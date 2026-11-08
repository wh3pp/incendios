"""Experimentos numéricos de las sesiones 1 a 6 del curso.

Cada bloque conecta una herramienta numérica del curso con el modelo de
incendios:

* Sesión 1: aritmética IEEE 754, épsilon de máquina, cancelación y número de
  condición del modelo de Rothermel.
* Sesión 2: ecuaciones no lineales (bisección, falsa posición, Newton-Raphson
  y secante) aplicadas a umbrales de humedad y viento.
* Sesión 3: integradores de EDO (Euler, Euler-Cromer, RK2, RK4) y transporte
  de pavesas con arrastre cuadrático.
* Sesión 4: oscilador no lineal (péndulo) y problema de N cuerpos como
  verificación del integrador RK4.
* Sesión 5: ecuaciones diferenciales estocásticas (Langevin,
  Euler-Maruyama, Fokker-Planck y MSD).
* Sesión 6: autómatas celulares clásicos (regla 184, Nagel-Schreckenberg y
  Juego de la Vida).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.special import erf

from .fuels import FuelModel, base_rate_of_spread, wind_factor

Array = NDArray[np.float64]
ScalarFunction = Callable[[float], float]


# ---------------------------------------------------------------------------
# Sesión 1: punto flotante y acondicionamiento
# ---------------------------------------------------------------------------
def machine_epsilon() -> float:
    """Épsilon de máquina de doble precisión por bisección."""
    eps = 1.0
    while 1.0 + eps / 2.0 != 1.0:
        eps /= 2.0
    return eps


def cancellation_demo(x: float) -> tuple[float, float]:
    """Compara ``(1-cos x)/x^2`` con la forma estable ``2 sin^2(x/2)/x^2``.

    Devuelve ``(valor_ingenuo, valor_estable)``. Para ``x`` pequeño, la
    primera expresión sufre cancelación catastrófica.
    """
    naive = (1.0 - np.cos(x)) / (x * x)
    stable = 2.0 * np.sin(x / 2.0) ** 2 / (x * x)
    return float(naive), float(stable)


def vdw_pressure(v: float, temperature: float, a: float = 0.3640, b: float = 4.267e-5) -> float:
    """Presión de van der Waals [Pa] para CO2 (a, b en unidades SI)."""
    r = 8.314462618
    return r * temperature / (v - b) - a / v**2


def moisture_sensitivity(moisture: float, mx: float) -> tuple[float, float]:
    """Valor y derivada de ``eta_M`` respecto de la humedad.

    Returns
    -------
    eta, d eta / d M
    """
    r = np.clip(moisture / mx, 0.0, 1.0)
    eta = 1.0 - 2.59 * r + 5.11 * r**2 - 3.52 * r**3
    deta = (-2.59 + 2.0 * 5.11 * r - 3.0 * 3.52 * r**2) / mx
    return float(eta), float(deta)


def condition_number_moisture(moisture: float, mx: float) -> float:
    """Número de condición ``kappa = |(M/eta) d eta/dM|``."""
    eta, deta = moisture_sensitivity(moisture, mx)
    if eta <= 1e-14:
        return float("inf")
    return float(abs(moisture * deta / eta))


def condition_number_ros(moisture: float, model: FuelModel, relative_step: float = 1e-5) -> float:
    """Número de condición de la ROS base respecto de la humedad.

    Se usa una diferencia central con paso relativo; el objetivo es mostrar
    el crecimiento de ``kappa`` cuando ``M -> M_x``.
    """
    h = max(moisture * relative_step, 1e-9)
    lo = max(moisture - h, 1e-8)
    hi = min(moisture + h, 0.999 * model.mx)
    if hi <= lo:
        return float("inf")
    r_lo = float(base_rate_of_spread(model.load, model.sav, model.depth, lo, model.mx))
    r_hi = float(base_rate_of_spread(model.load, model.sav, model.depth, hi, model.mx))
    r = float(base_rate_of_spread(model.load, model.sav, model.depth, moisture, model.mx))
    derivative = (r_hi - r_lo) / (hi - lo)
    if r <= 1e-30:
        return float("inf")
    return float(abs(moisture * derivative / r))


def floating_point_table() -> list[dict[str, float | str]]:
    """Tabla de experimentos elementales de punto flotante."""
    eps = machine_epsilon()
    naive, stable = cancellation_demo(1e-8)
    rows: list[dict[str, float | str]] = [
        {
            "expresion": "0.1 + 0.2",
            "resultado": repr(0.1 + 0.2),
            "error_abs": abs(0.1 + 0.2 - 0.3),
        },
        {
            "expresion": "(0.1 + 0.2) - 0.3",
            "resultado": repr((0.1 + 0.2) - 0.3),
            "error_abs": abs((0.1 + 0.2) - 0.3),
        },
        {
            "expresion": "1e16 + 1 - 1e16",
            "resultado": repr(1e16 + 1 - 1e16),
            "error_abs": abs((1e16 + 1 - 1e16) - 1.0),
        },
        {
            "expresion": "(1 - cos(1e-8)) / 1e-16",
            "resultado": repr(naive),
            "error_abs": abs(naive - stable),
        },
        {
            "expresion": "épsilon de máquina",
            "resultado": repr(eps),
            "error_abs": abs(eps - np.finfo(float).eps),
        },
    ]
    return rows


# ---------------------------------------------------------------------------
# Sesión 2: raíces de ecuaciones no lineales
# ---------------------------------------------------------------------------
@dataclass
class RootResult:
    """Resultado de un método iterativo de búsqueda de raíces."""

    method: str
    root: float
    iterations: int
    errors: list[float]
    converged: bool
    roots: list[float] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.roots is None:
            self.roots = []

    @property
    def final_error(self) -> float:
        return self.errors[-1] if self.errors else float("nan")

    def observed_order(self) -> float:
        """Orden de convergencia estimado a partir de tres errores."""
        e = [x for x in self.errors if x > 0.0]
        if len(e) < 3:
            return float("nan")
        return float(np.log(e[-1] / e[-2]) / np.log(e[-2] / e[-3]))


def bisection(
    f: ScalarFunction, a: float, b: float, tol: float = 1e-12, max_iter: int = 200
) -> RootResult:
    """Método de bisección clásico."""
    fa, fb = f(a), f(b)
    if fa * fb > 0:
        raise ValueError("la función no cambia de signo en [a, b]")
    errors: list[float] = []
    roots: list[float] = []
    root = 0.5 * (a + b)
    for k in range(max_iter):
        root = 0.5 * (a + b)
        fr = f(root)
        errors.append(abs(fr))
        roots.append(root)
        if abs(b - a) < tol or fr == 0.0:
            return RootResult("Bisección", root, k + 1, errors, True, roots)
        if fa * fr < 0:
            b, fb = root, fr
        else:
            a, fa = root, fr
    return RootResult("Bisección", root, max_iter, errors, False, roots)


def false_position(
    f: ScalarFunction, a: float, b: float, tol: float = 1e-12, max_iter: int = 200
) -> RootResult:
    """Regula falsi con corrección de Illinois (convergencia garantizada)."""
    fa, fb = f(a), f(b)
    if fa * fb > 0:
        raise ValueError("la función no cambia de signo en [a, b]")
    errors: list[float] = []
    roots: list[float] = []
    root = a
    side = 0
    for k in range(max_iter):
        root = (a * fb - b * fa) / (fb - fa)
        fr = f(root)
        errors.append(abs(fr))
        roots.append(root)
        if abs(fr) < tol or abs(b - a) < tol:
            return RootResult("Falsa posición", root, k + 1, errors, True, roots)
        if fa * fr < 0:
            b, fb = root, fr
            if side == -1:
                fa *= 0.5
            side = -1
        else:
            a, fa = root, fr
            if side == 1:
                fb *= 0.5
            side = 1
    return RootResult("Falsa posición", root, max_iter, errors, False, roots)


def newton_raphson(
    f: ScalarFunction,
    df: ScalarFunction,
    x0: float,
    tol: float = 1e-12,
    max_iter: int = 100,
) -> RootResult:
    """Método de Newton-Raphson."""
    x = float(x0)
    errors: list[float] = []
    roots: list[float] = []
    for k in range(max_iter):
        fx = f(x)
        errors.append(abs(fx))
        roots.append(x)
        if abs(fx) < tol:
            return RootResult("Newton-Raphson", x, k, errors, True, roots)
        dfx = df(x)
        if dfx == 0.0:
            break
        x_new = x - fx / dfx
        if not np.isfinite(x_new):
            break
        x = x_new
    return RootResult("Newton-Raphson", x, max_iter, errors, False, roots)


def secant(
    f: ScalarFunction, x0: float, x1: float, tol: float = 1e-12, max_iter: int = 100
) -> RootResult:
    """Método de la secante."""
    x_prev, x = float(x0), float(x1)
    f_prev, f_x = f(x_prev), f(x)
    errors: list[float] = []
    roots: list[float] = []
    for k in range(max_iter):
        errors.append(abs(f_x))
        roots.append(x)
        if abs(f_x) < tol:
            return RootResult("Secante", x, k, errors, True, roots)
        denom = f_x - f_prev
        if denom == 0.0:
            break
        x_new = x - f_x * (x - x_prev) / denom
        if not np.isfinite(x_new):
            break
        x_prev, f_prev = x, f_x
        x = x_new
        f_x = f(x)
    return RootResult("Secante", x, max_iter, errors, False, roots)


def solve_moisture_threshold(
    model: FuelModel, target_fraction: float = 0.5, reference_moisture: float = 0.05
) -> tuple[float, float]:
    """Humedad ``M`` tal que ``R0(M) = target_fraction * R0(M_ref)``.

    Devuelve ``(M_objetivo, R_objetivo)``. Es el problema no lineal aplicado
    del capítulo de métodos numéricos: la ROS decae de forma no lineal y se
    anula en la humedad de extinción.
    """
    r_ref = float(
        base_rate_of_spread(model.load, model.sav, model.depth, reference_moisture, model.mx)
    )
    target = target_fraction * r_ref

    def f(m: float) -> float:
        return float(base_rate_of_spread(model.load, model.sav, model.depth, m, model.mx)) - target

    a, b = 1e-4, 0.98 * model.mx
    if f(a) * f(b) > 0:
        # Si el objetivo no está en el rango, se devuelve el extremo.
        return (a if abs(f(a)) < abs(f(b)) else b), target
    # Referencia de alta precisión con bisección fina.
    ref = bisection(f, a, b, tol=1e-14, max_iter=200)
    return ref.root, target


def solve_critical_wind(
    model: FuelModel, moisture: float, target_ros: float, wind_efficiency: float = 0.30
) -> tuple[float, float]:
    """Velocidad de viento ``U`` que produce una ROS de cabeza objetivo."""
    r0 = float(base_rate_of_spread(model.load, model.sav, model.depth, moisture, model.mx))

    def f(u: float) -> float:
        phi = wind_efficiency * float(wind_factor(model.sav, model.load, model.depth, u))
        return r0 * (1.0 + phi) - target_ros

    a, b = 1e-6, 30.0
    if f(a) * f(b) > 0:
        return b, target_ros
    ref = bisection(f, a, b, tol=1e-12, max_iter=200)
    return ref.root, target_ros


def root_methods_table(
    model: FuelModel,
) -> list[dict[str, float | str]]:
    """Compara los cuatro métodos en el umbral de humedad del modelo."""
    root, target = solve_moisture_threshold(model, 0.5, 0.05)

    def f(m: float) -> float:
        return float(base_rate_of_spread(model.load, model.sav, model.depth, m, model.mx)) - target

    def df(m: float) -> float:
        h = 1e-7
        return (f(m + h) - f(m - h)) / (2.0 * h)

    a, b = 1e-4, 0.98 * model.mx
    results = [
        bisection(f, a, b),
        false_position(f, a, b),
        newton_raphson(f, df, 0.5 * (a + b)),
        secant(f, a, b),
    ]
    rows: list[dict[str, float | str]] = []
    for res in results:
        errs = [abs(x - root) for x in res.roots]
        order = float("nan")
        positive = [e for e in errs if e > 0.0]
        if len(positive) >= 3:
            order = float(np.log(positive[-1] / positive[-2]) / np.log(positive[-2] / positive[-3]))
        rows.append(
            {
                "metodo": res.method,
                "iteraciones": res.iterations,
                "raiz": res.root,
                "error_abs": abs(res.root - root),
                "error_final": res.final_error,
                "orden_observado": order,
                "convergio": res.converged,
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Sesión 3: integradores de EDO y transporte de pavesas
# ---------------------------------------------------------------------------
def euler_step(f: Callable[[float, Array], Array], t: float, y: Array, dt: float) -> Array:
    return y + dt * f(t, y)


def euler_cromer_step(
    accel: Callable[[Array], float], position: float, velocity: float, dt: float
) -> tuple[float, float]:
    """Paso de Euler-Cromer para un oscilador de segundo orden.

    La velocidad se actualiza primero y la posición usa la velocidad nueva.
    El esquema es simpléctico y evita la deriva sistemática de energía del
    Euler explícito en osciladores.
    """
    velocity_new = velocity + dt * accel(np.array([position, velocity]))
    position_new = position + dt * velocity_new
    return position_new, velocity_new


def rk2_step(f: Callable[[float, Array], Array], t: float, y: Array, dt: float) -> Array:
    k1 = f(t, y)
    k2 = f(t + dt / 2.0, y + dt * k1 / 2.0)
    return y + dt * k2


def rk4_step(f: Callable[[float, Array], Array], t: float, y: Array, dt: float) -> Array:
    k1 = f(t, y)
    k2 = f(t + dt / 2.0, y + dt * k1 / 2.0)
    k3 = f(t + dt / 2.0, y + dt * k2 / 2.0)
    k4 = f(t + dt, y + dt * k3)
    return y + dt * (k1 + 2.0 * k2 + 2.0 * k3 + k4) / 6.0


def integrate(
    f: Callable[[float, Array], Array],
    y0: Sequence[float],
    t_end: float,
    dt: float,
    method: str = "rk4",
) -> tuple[Array, Array]:
    """Integra un sistema de EDO con paso fijo.

    Returns
    -------
    times, states (``states[k]`` es el vector de estado en ``times[k]``).
    """
    n = int(round(t_end / dt))
    times = np.linspace(0.0, n * dt, n + 1)
    states = np.empty((n + 1, len(y0)), dtype=float)
    states[0] = np.asarray(y0, dtype=float)
    step = {"euler": euler_step, "rk2": rk2_step, "rk4": rk4_step}[method]
    for k in range(n):
        states[k + 1] = step(f, times[k], states[k], dt)
    return times, states


def drag_vertical_deriv(t: float, state: Array, g: float = 9.81, k: float = 0.01) -> Array:
    """Caída vertical con arrastre cuadrático: ``dv/dt = g - k v^2``."""
    v = state[0]
    return np.array([g - k * v * abs(v)])


def drag_vertical_exact(
    t: NDArray[np.float64], g: float = 9.81, k: float = 0.01
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Solución analítica de ``v' = g - k v^2`` con ``v(0)=0``."""
    vt = np.sqrt(g / k)
    v = vt * np.tanh(g * t / vt)
    x = (vt**2 / g) * np.log(np.cosh(g * t / vt))
    return v, x


def convergence_table(
    g: float = 9.81, k: float = 0.01, t_end: float = 5.0
) -> list[dict[str, float | str]]:
    """Error y orden observado de Euler, RK2 y RK4 en la caída con arrastre."""
    v_exact, _ = drag_vertical_exact(np.array([t_end]), g, k)
    rows: list[dict[str, float | str]] = []
    for method in ("euler", "rk2", "rk4"):
        previous_error = None
        for dt in (0.2, 0.1, 0.05, 0.025):
            n = int(round(t_end / dt))
            times = np.linspace(0.0, n * dt, n + 1)
            states = np.empty((n + 1, 1))
            states[0, 0] = 0.0
            step = {"euler": euler_step, "rk2": rk2_step, "rk4": rk4_step}[method]
            for i in range(n):
                states[i + 1] = step(drag_vertical_deriv, times[i], states[i], dt)
            error = abs(states[-1, 0] - v_exact[0])
            order = (
                np.log(previous_error / error) / np.log(2.0)
                if previous_error and error > 0
                else np.nan
            )
            rows.append(
                {
                    "metodo": method,
                    "dt": dt,
                    "error": error,
                    "orden": float(order) if np.isfinite(order) else np.nan,
                }
            )
            previous_error = error
    return rows


def projectile_deriv(t: float, state: Array, k: float, g: float, wind: Array) -> Array:
    """Proyectil 2D con arrastre cuadrático y viento.

    ``state = [x, y, vx, vy]``; la fuerza de arrastre es
    ``-k |v - w| (v - w)``.
    """
    x, y, vx, vy = state
    rx, ry = vx - wind[0], vy - wind[1]
    speed = np.hypot(rx, ry)
    ax = -k * speed * rx
    ay = -g - k * speed * ry
    return np.array([vx, vy, ax, ay])


def firebrand_trajectory(
    wind_speed: float,
    k: float = 0.05,
    v0: float = 6.0,
    angle_deg: float = 30.0,
    t_end: float = 12.0,
    dt: float = 0.01,
    height: float = 60.0,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Trayectoria de una pavesa (firebrand) lanzada desde una copa.

    El arrastre es cuadrático y el viento sopla en +x. La pavesa se lanza
    desde una altura ``height`` con velocidad inicial ``v0`` y ángulo
    ``angle_deg``. El coeficiente ``k`` controla el acoplamiento con el aire:
    valores mayores representan partículas más ligeras.
    """
    theta = np.radians(angle_deg)
    y0 = [0.0, height, v0 * np.cos(theta), v0 * np.sin(theta)]
    wind = np.array([wind_speed, 0.0])
    times, states = integrate(
        lambda t, y: projectile_deriv(t, y, k, 9.81, wind),
        y0,
        t_end,
        dt,
        "rk4",
    )
    return times, states


# ---------------------------------------------------------------------------
# Sesión 4: péndulo no lineal y N cuerpos
# ---------------------------------------------------------------------------
def pendulum_deriv(t: float, state: Array, g: float = 9.81, length: float = 1.0) -> Array:
    theta, omega = state
    return np.array([omega, -(g / length) * np.sin(theta)])


def pendulum_energy(state: Array, g: float = 9.81, length: float = 1.0) -> float:
    theta, omega = state
    return float(0.5 * length**2 * omega**2 + g * length * (1.0 - np.cos(theta)))


def pendulum_period(amplitude: float, length: float = 1.0, g: float = 9.81) -> float:
    """Período exacto del péndulo simple mediante la integral elíptica."""
    from scipy.special import ellipk

    k = np.sin(amplitude / 2.0)
    return float(4.0 * np.sqrt(length / g) * ellipk(k**2))


def pendulum_table(
    amplitudes: Sequence[float] = (0.05, 0.5, 1.0, 1.5, 2.5),
    dt: float = 1e-3,
) -> list[dict[str, float]]:
    """Período numérico (RK4) frente al período exacto y energía."""
    rows: list[dict[str, float]] = []
    for amp in amplitudes:
        y0 = [amp, 0.0]
        t_end = 2.0 * pendulum_period(amp) + 0.2
        times, states = integrate(pendulum_deriv, y0, t_end, dt, "rk4")
        energy0 = pendulum_energy(np.array(y0))
        energy = np.array([pendulum_energy(s) for s in states])
        # Cruces por cero con velocidad positiva.
        crossings = []
        for i in range(1, len(states)):
            if states[i - 1, 0] <= 0.0 < states[i, 0]:
                crossings.append(times[i])
        period = np.mean(np.diff(crossings)) if len(crossings) >= 2 else np.nan
        rows.append(
            {
                "amplitud_rad": amp,
                "periodo_rk4": float(period),
                "periodo_exacto": pendulum_period(amp),
                "error_rel": abs(period - pendulum_period(amp)) / pendulum_period(amp),
                "drift_energia_rel": float(np.max(np.abs(energy - energy0)) / energy0),
            }
        )
    return rows


def pendulum_integrator_table(
    amplitude: float = 1.0,
    dt: float = 0.01,
    periods: int = 20,
) -> list[dict[str, float | str]]:
    """Deriva de energía del péndulo con Euler, Euler-Cromer y RK4."""
    period = pendulum_period(amplitude)
    t_end = periods * period
    n = int(round(t_end / dt))
    times = np.linspace(0.0, n * dt, n + 1)
    rows: list[dict[str, float | str]] = []
    for method in ("euler", "euler-cromer", "rk4"):
        state = np.array([amplitude, 0.0])
        energy0 = pendulum_energy(state)
        energies = [energy0]
        for k in range(n):
            if method == "euler-cromer":
                theta, omega = euler_cromer_step(
                    lambda y, _t=times[k]: pendulum_deriv(_t, y)[1], state[0], state[1], dt
                )
                state = np.array([theta, omega])
            else:
                step = euler_step if method == "euler" else rk4_step
                state = step(pendulum_deriv, times[k], state, dt)
            energies.append(pendulum_energy(state))
        energies_arr = np.asarray(energies)
        rows.append(
            {
                "metodo": method.upper(),
                "dt": dt,
                "periodos": periods,
                "drift_max_rel": float(np.max(np.abs(energies_arr - energy0)) / abs(energy0)),
                "drift_final_rel": float(abs(energies_arr[-1] - energy0) / abs(energy0)),
            }
        )
    return rows


def nbody_deriv(t: float, state: Array, masses: Array, soft: float = 1e-6) -> Array:
    """Derivadas del problema gravitatorio de N cuerpos.

    ``state = [r_1, ..., r_N, v_1, ..., v_N]`` con ``r_i = (x_i, y_i)``.
    """
    n = len(masses)
    pos = state[: 2 * n].reshape(n, 2)
    vel = state[2 * n :].reshape(n, 2)
    acc = np.zeros_like(pos)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            r = pos[j] - pos[i]
            dist2 = np.dot(r, r) + soft
            acc[i] += masses[j] * r / dist2**1.5
    return np.concatenate([vel.ravel(), acc.ravel()])


def nbody_energy(state: Array, masses: Array, soft: float = 1e-6) -> float:
    n = len(masses)
    pos = state[: 2 * n].reshape(n, 2)
    vel = state[2 * n :].reshape(n, 2)
    kinetic = 0.5 * np.sum(masses[:, None] * vel**2)
    potential = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            r = np.linalg.norm(pos[j] - pos[i])
            potential -= masses[i] * masses[j] / np.sqrt(r**2 + soft)
    return float(kinetic + potential)


def figure_eight_initial() -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Condiciones iniciales del problema de tres cuerpos en figura ocho."""
    masses = np.array([1.0, 1.0, 1.0])
    state = np.array(
        [
            -0.97000436,
            0.24308753,
            0.97000436,
            -0.24308753,
            0.0,
            0.0,
            -0.466203685,
            -0.43236573,
            -0.466203685,
            -0.43236573,
            0.93240737,
            0.86473146,
        ]
    )
    return masses, state


def nbody_table(dt_values: Sequence[float] = (0.02, 0.01, 0.005, 0.0025)) -> list[dict[str, float]]:
    """Deriva relativa de energía del problema de figura ocho con RK4."""
    masses, y0 = figure_eight_initial()
    e0 = nbody_energy(y0, masses)
    rows = []
    for dt in dt_values:
        times, states = integrate(lambda t, y: nbody_deriv(t, y, masses), y0, 6.0, dt, "rk4")
        energies = np.array([nbody_energy(s, masses) for s in states])
        rows.append(
            {
                "dt": dt,
                "drift_max_rel": float(np.max(np.abs(energies - e0)) / abs(e0)),
                "drift_final_rel": float(abs(energies[-1] - e0) / abs(e0)),
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Sesión 5: EDE, Langevin, Fokker-Planck y MSD
# ---------------------------------------------------------------------------
def euler_maruyama(
    drift: Callable[[float, Array], Array],
    diffusion: Callable[[float, Array], Array],
    x0: Sequence[float],
    t_end: float,
    dt: float,
    n_paths: int = 1000,
    seed: int = 0,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Integra ``dX = a(t,X) dt + b(t,X) dW`` con Euler-Maruyama.

    Returns
    -------
    times, paths de forma ``(n_paths, n_times, dim)``.
    """
    rng = np.random.default_rng(seed)
    n = int(round(t_end / dt))
    times = np.linspace(0.0, n * dt, n + 1)
    x = np.tile(np.asarray(x0, dtype=float), (n_paths, 1))
    dim = x.shape[1]
    paths = np.empty((n_paths, n + 1, dim))
    paths[:, 0, :] = x
    sqrt_dt = np.sqrt(dt)
    for k in range(n):
        t = times[k]
        a = np.array([drift(t, xi) for xi in x])
        b = np.array([diffusion(t, xi) for xi in x])
        noise = rng.normal(size=(n_paths, dim))
        x = x + a * dt + b * sqrt_dt * noise
        paths[:, k + 1, :] = x
    return times, paths


def langevin_paths(
    velocity: float = 0.5,
    sigma: float = 0.2,
    t_end: float = 10.0,
    dt: float = 0.01,
    n_paths: int = 2000,
    seed: int = 0,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Movimiento de un frente con deriva constante y ruido blanco.

    ``dX = v dt + sigma dW``. La solución exacta es
    ``X(t) ~ N(v t, sigma^2 t)``.
    """
    return euler_maruyama(
        lambda t, x: np.array([velocity]),
        lambda t, x: np.array([sigma]),
        [0.0],
        t_end,
        dt,
        n_paths,
        seed,
    )


def msd_curve(
    times: NDArray[np.float64], paths: NDArray[np.float64]
) -> tuple[NDArray[np.float64], NDArray[np.float64], float]:
    """MSD y exponente de difusión ajustado ``MSD ~ t^alpha``."""
    x = paths[:, :, 0]
    # Se usa la varianza respecto de la media del ensemble para eliminar la
    # contribución balística de la deriva y aislar la difusión.
    msd = np.mean((x - x.mean(axis=0, keepdims=True)) ** 2, axis=0)
    mask = (times > 0) & (msd > 0)
    slope, _ = np.polyfit(np.log(times[mask]), np.log(msd[mask]), 1)
    return times, msd, float(slope)


def fokker_planck_gaussian(
    x: NDArray[np.float64], t: float, velocity: float, sigma: float
) -> NDArray[np.float64]:
    """Solución fundamental de la ecuación de Fokker-Planck con deriva."""
    if t <= 0.0:
        raise ValueError("t debe ser positivo")
    mean = velocity * t
    std = sigma * np.sqrt(t)
    return np.exp(-0.5 * ((x - mean) / std) ** 2) / (std * np.sqrt(2.0 * np.pi))


def fokker_planck_table(
    velocity: float = 0.5,
    sigma: float = 0.2,
    times: Sequence[float] = (1.0, 2.0, 5.0),
    n_paths: int = 5000,
    dt: float = 0.01,
    seed: int = 0,
) -> list[dict[str, float]]:
    """Compara la PDF empírica de Langevin con la solución de Fokker-Planck."""
    t_end = max(times)
    sim_times, paths = langevin_paths(velocity, sigma, t_end, dt, n_paths, seed)
    rows = []
    for t in times:
        idx = int(round(t / dt))
        sample = paths[:, idx, 0]
        # Distancia de Kolmogorov-Smirnov entre la muestra y la PDF exacta.
        from scipy.stats import kstest

        def cdf(z: float, _t: float = t) -> float:
            return 0.5 * (1.0 + erf((z - velocity * _t) / (sigma * np.sqrt(2.0 * _t))))

        ks = kstest(sample, cdf)
        rows.append(
            {
                "t": t,
                "media_empirica": float(np.mean(sample)),
                "media_exacta": velocity * t,
                "std_empirica": float(np.std(sample)),
                "std_exacta": sigma * np.sqrt(t),
                "ks_pvalue": float(ks.pvalue),
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Sesión 6: autómatas celulares clásicos
# ---------------------------------------------------------------------------
def rule184_step(road: NDArray[np.integer]) -> NDArray[np.int8]:
    """Paso de la regla 184: partículas que avanzan si la celda está libre.

    La regla se implementa con la actualización paralela estándar:
    ``n_i(t+1) = n_{i-1}(t) (1 - n_i(t)) + n_i(t) n_{i+1}(t)``.
    """
    n = np.asarray(road, dtype=np.int8)
    left = np.roll(n, 1)
    right = np.roll(n, -1)
    return ((left * (1 - n)) + (n * right)).astype(np.int8)


def rule184_density_flow(
    density: float, size: int = 512, steps: int = 400, seed: int = 0
) -> tuple[float, float]:
    """Flujo estacionario de la regla 184 para una densidad dada."""
    rng = np.random.default_rng(seed)
    road = (rng.random(size) < density).astype(np.int8)
    for _ in range(steps):
        road = rule184_step(road)
    flow = float(np.mean(road * np.roll(1 - road, -1)))
    return flow, float(np.mean(road))


def nagel_schreckenberg_step(
    road: NDArray[np.integer],
    speeds: NDArray[np.integer],
    v_max: int = 5,
    p_brake: float = 0.25,
    rng: np.random.Generator | None = None,
) -> tuple[NDArray[np.int8], NDArray[np.int8]]:
    """Paso del modelo de Nagel-Schreckenberg.

    ``road`` contiene 1 si hay vehículo y 0 si no; ``speeds`` es la velocidad
    de cada vehículo (0 en celdas vacías).
    """
    rng = rng or np.random.default_rng()
    n = len(road)
    new_speeds = speeds.copy()
    positions = np.flatnonzero(road)
    for pos in positions:
        v = int(speeds[pos])
        # Distancia al vehículo siguiente (con condiciones periódicas).
        gap = 1
        while gap < n and road[(pos + gap) % n] == 0:
            gap += 1
        gap -= 1
        v = min(v + 1, v_max, gap)
        if rng.random() < p_brake:
            v = max(v - 1, 0)
        new_speeds[pos] = v
    new_road = np.zeros_like(road, dtype=np.int8)
    moved_speeds = np.zeros_like(speeds, dtype=np.int8)
    for pos in positions:
        target = (pos + new_speeds[pos]) % n
        new_road[target] = 1
        moved_speeds[target] = new_speeds[pos]
    return new_road, moved_speeds


def nagel_schreckenberg_density_flow(
    density: float,
    size: int = 300,
    steps: int = 600,
    v_max: int = 5,
    p_brake: float = 0.25,
    seed: int = 0,
) -> tuple[float, float]:
    """Flujo estacionario del modelo NaSch para una densidad dada."""
    rng = np.random.default_rng(seed)
    road = (rng.random(size) < density).astype(np.int8)
    speeds = np.where(road > 0, rng.integers(0, v_max + 1, size=size), 0).astype(np.int8)
    for _ in range(steps):
        road, speeds = nagel_schreckenberg_step(road, speeds, v_max, p_brake, rng)
    flow = float(np.sum(speeds) / size)
    return flow, float(np.mean(road))


def game_of_life_step(grid: NDArray[np.integer]) -> NDArray[np.int8]:
    """Paso del Juego de la Vida de Conway (vecindad de Moore)."""
    g = np.asarray(grid, dtype=np.int8)
    neighbors = sum(
        np.roll(np.roll(g, dr, axis=0), dc, axis=1)
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if not (dr == 0 and dc == 0)
    )
    alive = (g == 1) & ((neighbors == 2) | (neighbors == 3))
    born = (g == 0) & (neighbors == 3)
    return (alive | born).astype(np.int8)


def glider(shape: tuple[int, int] = (20, 20)) -> NDArray[np.int8]:
    """Glider clásico centrado en una malla."""
    grid = np.zeros(shape, dtype=np.int8)
    pattern = np.array([[0, 1, 0], [0, 0, 1], [1, 1, 1]], dtype=np.int8)
    r0 = shape[0] // 2 - 1
    c0 = shape[1] // 2 - 1
    grid[r0 : r0 + 3, c0 : c0 + 3] = pattern
    return grid


def spacetime(initial: NDArray[np.integer], steps: int, rule: str = "rule184") -> NDArray[np.int8]:
    """Diagrama espacio-temporal de un autómata unidimensional."""
    frames = [np.asarray(initial, dtype=np.int8)]
    state = frames[0].copy()
    for _ in range(steps):
        if rule == "rule184":
            state = rule184_step(state)
        elif rule == "nasch":
            raise ValueError("use nagel_schreckenberg_step para NaSch")
        else:
            raise ValueError(f"regla desconocida: {rule}")
        frames.append(state.copy())
    return np.vstack(frames)
