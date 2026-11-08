"""Modelos de combustible y ecuación de propagación de Rothermel (1972).

El módulo implementa una versión vectorizada del modelo de propagación
superficial de Rothermel en unidades SI. Internamente las ecuaciones se
evalúan en el sistema imperial original (lb, ft, min, BTU) y el resultado se
convierte a m/s, que es la unidad utilizada por el autómata celular.

Referencias
----------
Rothermel, R. C. (1972). A mathematical model for predicting fire spread in
wildland fuels. USDA Forest Service, INT-RP-115.
https://doi.org/10.2737/INT-RP-115

Andrews, P. L. (2018). The Rothermel surface fire spread model and associated
developments: A comprehensive explanation. RMRS-GTR-371.
https://doi.org/10.2737/RMRS-GTR-371
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

import numpy as np
from numpy.typing import ArrayLike, NDArray

# Factores de conversión al sistema imperial utilizado por Rothermel.
KG_M2_TO_LB_FT2: Final = 1.0 / 4.882427636
M_TO_FT: Final = 1.0 / 0.3048
M_INV_TO_FT_INV: Final = 0.3048
FT_MIN_TO_M_S: Final = 0.3048 / 60.0
BTU_LB_TO_J_KG: Final = 2326.0  # 1 BTU/lb = 2326 J/kg (calor de combustión)
LB_FT3_TO_KG_M3: Final = 16.018463

# Constantes físicas del modelo.
PARTICLE_DENSITY_LB_FT3: Final = 32.0
HEAT_CONTENT_BTU_LB: Final = 8000.0
TOTAL_MINERAL_CONTENT: Final = 0.0555
EFFECTIVE_MINERAL_CONTENT: Final = 0.01


@dataclass(frozen=True)
class FuelModel:
    """Propiedades de un modelo de combustible superficial.

    Attributes
    ----------
    code:
        Identificador corto (por ejemplo ``"FM1"``).
    name:
        Nombre descriptivo.
    load:
        Carga de combustible seca [kg m^-2].
    sav:
        Relación superficie-volumen [m^-1].
    depth:
        Profundidad del lecho [m].
    mx:
        Humedad de extinción [fracción].
    residence_time:
        Tiempo de residencia de la llama [s].
    color:
        Color RGB para las figuras.
    """

    code: str
    name: str
    load: float
    sav: float
    depth: float
    mx: float
    residence_time: float = 300.0
    heat: float = HEAT_CONTENT_BTU_LB
    particle_density: float = PARTICLE_DENSITY_LB_FT3
    total_mineral: float = TOTAL_MINERAL_CONTENT
    effective_mineral: float = EFFECTIVE_MINERAL_CONTENT
    color: tuple[float, float, float] = field(default=(0.2, 0.5, 0.2))


# Modelos estándar de Scott & Burgan (2005), adaptados a un único lecho.
# La carga total se obtiene sumando los combustibles de 1 h, 10 h y 100 h.
STANDARD_FUELS: Final[dict[str, FuelModel]] = {
    "FM1": FuelModel(
        code="FM1",
        name="Pasto corto (short grass)",
        load=0.166,
        sav=11483.0,
        depth=0.3048,
        mx=0.12,
        residence_time=120.0,
        color=(0.85, 0.75, 0.25),
    ),
    "FM4": FuelModel(
        code="FM4",
        name="Matorral denso (chaparral)",
        load=3.14,
        sav=6562.0,
        depth=1.829,
        mx=0.20,
        residence_time=300.0,
        color=(0.35, 0.55, 0.20),
    ),
    "FM8": FuelModel(
        code="FM8",
        name="Hojarasca de bosque cerrado (closed timber litter)",
        load=1.68,
        sav=6562.0,
        depth=0.061,
        mx=0.30,
        residence_time=600.0,
        color=(0.45, 0.35, 0.20),
    ),
    "FM10": FuelModel(
        code="FM10",
        name="Hojarasca y sotobosque (timber litter and understory)",
        load=2.24,
        sav=6562.0,
        depth=0.3048,
        mx=0.25,
        residence_time=600.0,
        color=(0.25, 0.40, 0.15),
    ),
}


def _as_array(x: ArrayLike | float) -> NDArray[np.float64]:
    return np.asarray(x, dtype=float)


def packing_ratio(
    load: ArrayLike, depth: ArrayLike, particle_density: float = PARTICLE_DENSITY_LB_FT3
) -> NDArray[np.float64]:
    """Relación de empaquetamiento ``beta = rho_b / rho_p`` (adimensional)."""
    load_i = _as_array(load) * KG_M2_TO_LB_FT2
    depth_i = _as_array(depth) * M_TO_FT
    depth_safe = np.where(depth_i > 0.0, depth_i, 1.0)
    return np.where(depth_i > 0.0, load_i / depth_safe, 0.0) / particle_density


def optimal_packing_ratio(sav: ArrayLike) -> NDArray[np.float64]:
    """Relación de empaquetamiento óptima ``beta_op`` de Rothermel."""
    sigma_i = _as_array(sav) * M_INV_TO_FT_INV
    sigma_safe = np.where(sigma_i > 0.0, sigma_i, 1.0)
    return np.where(sigma_i > 0.0, 3.348 * sigma_safe**-0.8189, 0.0)


def moisture_damping(moisture: ArrayLike, mx: ArrayLike) -> NDArray[np.float64]:
    """Factor de amortiguamiento por humedad ``eta_M``.

    Se anula cuando ``M >= M_x`` (humedad de extinción). La expresión es un
    polinomio cúbico que puede volverse negativo si se evalúa fuera del rango
    físico; por ello se recorta a ``[0, 1]``.
    """
    m = _as_array(moisture)
    mx_a = _as_array(mx)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where(mx_a > 0.0, m / mx_a, 0.0)
    r = np.clip(r, 0.0, 1.0)
    eta = 1.0 - 2.59 * r + 5.11 * r**2 - 3.52 * r**3
    return np.clip(eta, 0.0, 1.0)


def mineral_damping(effective_mineral: float = EFFECTIVE_MINERAL_CONTENT) -> float:
    """Factor de amortiguamiento mineral ``eta_S``."""
    return float(0.174 * effective_mineral**-0.19)


def wind_factor(
    sav: ArrayLike,
    load: ArrayLike,
    depth: ArrayLike,
    wind_speed: ArrayLike,
    particle_density: float = PARTICLE_DENSITY_LB_FT3,
) -> NDArray[np.float64]:
    """Factor de viento ``phi_w`` para viento en la dirección de propagación.

    ``wind_speed`` se expresa en m/s y se convierte internamente a ft/min.
    """
    sigma_i = _as_array(sav) * M_INV_TO_FT_INV
    sigma_safe = np.where(sigma_i > 0.0, sigma_i, 1.0)
    u_ft_min = np.maximum(_as_array(wind_speed), 0.0) * M_TO_FT * 60.0
    beta = packing_ratio(load, depth, particle_density)
    beta_op = optimal_packing_ratio(sav)
    c = 7.47 * np.exp(-0.133 * sigma_safe**0.55)
    b = 0.02526 * sigma_safe**0.54
    e = 0.715 * np.exp(-3.59e-4 * sigma_safe)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(beta_op > 0.0, beta / beta_op, 0.0)
        phi = np.where(
            (u_ft_min > 0.0) & (ratio > 0.0),
            c * u_ft_min**b * ratio ** (-e),
            0.0,
        )
    return np.clip(phi, 0.0, 1.0e4)


def slope_factor(
    load: ArrayLike,
    depth: ArrayLike,
    tan_slope: ArrayLike,
    particle_density: float = PARTICLE_DENSITY_LB_FT3,
) -> NDArray[np.float64]:
    """Factor de pendiente ``phi_s`` para una pendiente ``tan(phi)``."""
    beta = packing_ratio(load, depth, particle_density)
    s = np.maximum(_as_array(tan_slope), 0.0)
    beta_safe = np.where(beta > 0.0, beta, 1.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        phi = 5.275 * np.where(beta > 0.0, beta_safe**-0.3, 0.0) * s**2
    return np.clip(phi, 0.0, 1.0e4)


def rothermel_components(
    load: ArrayLike,
    sav: ArrayLike,
    depth: ArrayLike,
    moisture: ArrayLike,
    mx: ArrayLike,
    heat: float = HEAT_CONTENT_BTU_LB,
    particle_density: float = PARTICLE_DENSITY_LB_FT3,
    total_mineral: float = TOTAL_MINERAL_CONTENT,
    effective_mineral: float = EFFECTIVE_MINERAL_CONTENT,
) -> dict[str, NDArray[np.float64] | float]:
    """Calcula los componentes intermedios del modelo de Rothermel.

    Todos los argumentos aceptan escalares o arreglos de NumPy y se
    transmiten (broadcasting) de forma elemental. Devuelve un diccionario con
    las magnitudes adimensionales y la velocidad base ``r0`` en m/s.
    """
    load_i = _as_array(load) * KG_M2_TO_LB_FT2
    depth_i = _as_array(depth) * M_TO_FT
    sigma_i = _as_array(sav) * M_INV_TO_FT_INV
    valid = (load_i > 0.0) & (depth_i > 0.0) & (sigma_i > 0.0)
    depth_safe = np.where(depth_i > 0.0, depth_i, 1.0)
    sigma_safe = np.where(sigma_i > 0.0, sigma_i, 1.0)
    rho_b = np.where(valid, load_i / depth_safe, 0.0)
    beta = rho_b / particle_density
    beta_op = 3.348 * sigma_safe**-0.8189
    a = 133.0 * sigma_safe**-0.7913
    gamma_max = sigma_safe**1.5 / (495.0 + 0.0594 * sigma_safe**1.5)
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        ratio = np.where(beta_op > 0.0, beta / beta_op, 0.0)
        gamma = np.where(
            (ratio > 0.0) & valid,
            gamma_max * ratio**a * np.exp(a * (1.0 - ratio)),
            0.0,
        )
        xi = np.exp((0.792 + 0.681 * np.sqrt(sigma_safe)) * (beta + 0.1)) / (
            192.0 + 0.2595 * sigma_safe
        )
    eps = np.exp(-138.0 / sigma_safe)
    q_ig = 250.0 + 1116.0 * _as_array(moisture)
    eta_m = moisture_damping(moisture, mx)
    eta_s = mineral_damping(effective_mineral)
    net_load = load_i * (1.0 - total_mineral)
    i_r = gamma * net_load * heat * eta_m * eta_s
    with np.errstate(divide="ignore", invalid="ignore"):
        r0_ft_min = np.where(
            (rho_b > 0.0) & (eps > 0.0) & (q_ig > 0.0),
            i_r * xi / (rho_b * eps * q_ig),
            0.0,
        )
    r0 = np.maximum(r0_ft_min, 0.0) * FT_MIN_TO_M_S
    return {
        "beta": beta,
        "beta_op": beta_op,
        "gamma": gamma,
        "xi": xi,
        "eps": eps,
        "q_ig": q_ig,
        "eta_m": eta_m,
        "eta_s": eta_s,
        "i_r": i_r,
        "r0": r0,
    }


def base_rate_of_spread(
    load: ArrayLike,
    sav: ArrayLike,
    depth: ArrayLike,
    moisture: ArrayLike,
    mx: ArrayLike,
    **kwargs: float,
) -> NDArray[np.float64]:
    """Velocidad de propagación sin viento ni pendiente [m/s]."""
    return np.asarray(rothermel_components(load, sav, depth, moisture, mx, **kwargs)["r0"])


@dataclass(frozen=True)
class DirectionalRates:
    """Velocidades direccionales de propagación para los 8 vecinos.

    Attributes
    ----------
    rates:
        Arreglo de forma ``(8, H, W)`` con la velocidad [m/s] desde cada celda
        hacia cada uno de los ocho vecinos de Moore.
    offsets:
        Desplazamientos ``(dr, dc)`` en orden E, NE, N, NW, W, SW, S, SE.
    angles:
        Ángulo polar de cada dirección [rad].
    distances:
        Distancia física entre centros de celdas vecinas [m].
    """

    rates: NDArray[np.float64]
    offsets: tuple[tuple[int, int], ...]
    angles: NDArray[np.float64]
    distances: NDArray[np.float64]


# Orden: E, NE, N, NW, W, SW, S, SE. ``dr`` positivo hacia abajo (filas).
VON_NEUMANN_OFFSETS: Final[tuple[tuple[int, int], ...]] = (
    (0, 1),
    (-1, 0),
    (0, -1),
    (1, 0),
)

MOORE_OFFSETS: Final[tuple[tuple[int, int], ...]] = (
    (0, 1),
    (-1, 1),
    (-1, 0),
    (-1, -1),
    (0, -1),
    (1, -1),
    (1, 0),
    (1, 1),
)


def directional_rates(
    load: ArrayLike,
    sav: ArrayLike,
    depth: ArrayLike,
    moisture: ArrayLike,
    mx: ArrayLike,
    wind_speed: float,
    wind_direction: float,
    grad_x: ArrayLike,
    grad_y: ArrayLike,
    cell_size: float,
    max_rate: float = 2.5,
    wind_efficiency: float = 0.30,
    offsets: tuple[tuple[int, int], ...] = MOORE_OFFSETS,
) -> DirectionalRates:
    """Calcula la ROS hacia los ocho vecinos de Moore.

    Parameters
    ----------
    wind_speed:
        Velocidad del viento [m/s].
    wind_direction:
        Dirección hacia la que sopla el viento [rad], medida desde +x.
    grad_x, grad_y:
        Gradientes de elevación [m/m] en las direcciones +x (columnas) y
        +y (filas).
    cell_size:
        Tamaño de celda [m].
    max_rate:
        Cota superior de seguridad para la ROS [m/s].
    """
    base = base_rate_of_spread(load, sav, depth, moisture, mx)
    valid = (_as_array(load) > 0.0) & (_as_array(sav) > 0.0) & (_as_array(depth) > 0.0)
    n = len(offsets)
    offsets_arr = np.asarray(offsets, dtype=float)
    angles = np.arctan2(-offsets_arr[:, 0], offsets_arr[:, 1])
    distances = cell_size * np.hypot(offsets_arr[:, 0], offsets_arr[:, 1])

    # Factor de viento calculado con la velocidad total y proyectado sobre
    # cada dirección. La componente de espalda se limita a una fracción
    # ``backing_floor`` de la velocidad base, de modo que el fuego no avance
    # Aguas arriba a la misma velocidad que sin viento.
    phi_w_full = wind_efficiency * wind_factor(sav, load, depth, wind_speed)
    backing_floor = 0.05
    rates = np.empty((n,) + base.shape, dtype=float)
    for k in range(n):
        cos_d = np.cos(angles[k] - wind_direction)
        # Kernel angular estrecho: el factor de viento decae como cos^4,
        # consistente con la forma alargada de los incendios impulsados por
        # viento. La componente de espalda se limita a backing_floor.
        cos_pos = max(float(cos_d), 0.0)
        factor_w = np.clip(
            1.0 + phi_w_full * cos_pos**8,
            backing_floor,
            1.0 + phi_w_full,
        )
        # Componente de la pendiente en la dirección de propagación.
        s_dir = grad_x * np.cos(angles[k]) + grad_y * np.sin(angles[k])
        phi_s = slope_factor(load, depth, np.maximum(s_dir, 0.0))
        rates[k] = np.where(valid, np.minimum(base * factor_w * (1.0 + phi_s), max_rate), 0.0)
    return DirectionalRates(
        rates=rates,
        offsets=offsets,
        angles=angles,
        distances=distances,
    )


def fuel_property_maps(
    fuel_type: NDArray[np.integer],
    models: dict[str, FuelModel] | None = None,
) -> dict[str, NDArray[np.float64]]:
    """Convierte un mapa de tipos de combustible en mapas de propiedades.

    El valor ``-1`` del mapa se interpreta como celda incombustible; sus
    propiedades se fuerzan a cero.
    """
    models = models or STANDARD_FUELS
    codes = list(models)
    shape = fuel_type.shape
    load = np.zeros(shape)
    sav = np.zeros(shape)
    depth = np.zeros(shape)
    mx = np.zeros(shape)
    residence = np.zeros(shape)
    for idx, code in enumerate(codes):
        model = models[code]
        mask = fuel_type == idx
        load[mask] = model.load
        sav[mask] = model.sav
        depth[mask] = model.depth
        mx[mask] = model.mx
        residence[mask] = model.residence_time
    valid = fuel_type >= 0
    load[~valid] = 0.0
    depth[~valid] = 0.0
    mx[~valid] = 0.0
    return {
        "load": load,
        "sav": sav,
        "depth": depth,
        "mx": mx,
        "residence_time": residence,
        "valid": valid.astype(float),
    }
