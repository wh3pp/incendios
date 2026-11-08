"""Campañas experimentales y generación de tablas del TIF.

Cada función devuelve un ``pandas.DataFrame`` y, cuando corresponde, guarda
los arreglos necesarios para las figuras en ``results/``. El diseño prioriza
la reproducibilidad: todas las semillas son explícitas y los experimentos
pueden ejecutarse de forma independiente desde ``scripts/run_all.py``.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd

from .ca import (
    DeterministicCA,
    MinimumTravelTime,
    SimulationResult,
    StochasticCA,
    run_ensemble,
)
from .fuels import STANDARD_FUELS
from .metrics import (
    ensemble_statistics,
    logistic_threshold,
    rate_of_spread,
    summarize,
)
from .numerics import (
    convergence_table,
    floating_point_table,
    fokker_planck_table,
    game_of_life_step,
    glider,
    langevin_paths,
    msd_curve,
    nagel_schreckenberg_density_flow,
    nbody_table,
    pendulum_integrator_table,
    pendulum_table,
    root_methods_table,
    rule184_density_flow,
    rule184_step,
    solve_moisture_threshold,
)
from .real_cases import ACOS, LITTLE_GIANT, run_case
from .terrain import Terrain, binary_forest, generate_terrain, ignition_mask

RESULTS = Path("results")
TABLES = RESULTS / "tables"
FIGURES = RESULTS / "figures"
DATA = RESULTS / "data"


def ensure_dirs() -> None:
    for path in (TABLES, FIGURES, DATA):
        path.mkdir(parents=True, exist_ok=True)


def homogeneous_terrain(
    size: int,
    fuel_code: str,
    moisture: float,
    wind_speed: float,
    cell_size: float = 5.0,
    slope: float = 0.0,
    seed: int = 0,
) -> Terrain:
    """Terreno plano (o con pendiente uniforme) de un solo combustible."""
    terrain = generate_terrain(
        size=size,
        cell_size=cell_size,
        seed=seed,
        relief=0.0,
        vegetation=0.8,
        moisture=moisture,
        wind_speed=wind_speed,
        wind_direction=0.0,
        lake=False,
    )
    code_to_idx = {code: i for i, code in enumerate(STANDARD_FUELS)}
    idx = code_to_idx[fuel_code]
    terrain.fuel_type[:] = idx
    terrain.load_factor[:] = 1.0
    terrain.moisture[:] = moisture
    if slope != 0.0:
        yy, xx = np.mgrid[0:size, 0:size]
        terrain.elevation = slope * xx * cell_size
        terrain.grad_x[:] = slope
        terrain.grad_y[:] = 0.0
    else:
        terrain.elevation[:] = 0.0
        terrain.grad_x[:] = 0.0
        terrain.grad_y[:] = 0.0
    return terrain


def _save_result_arrays(result: SimulationResult, path: Path) -> None:
    np.savez_compressed(
        path,
        times=result.times,
        burned_area=result.burned_area,
        active_cells=result.active_cells,
        head_distance=result.head_distance,
        arrival=result.arrival,
        state=result.state,
        burned_mask=result.burned_mask,
    )


# ---------------------------------------------------------------------------
# Escenario base y comparación determinista / estocástico
# ---------------------------------------------------------------------------
def baseline_experiment(
    size: int = 256,
    cell_size: float = 5.0,
    seed: int = 42,
    moisture: float = 0.07,
    wind_speed: float = 4.0,
    t_end: float = 900.0,
    dt: float = 1.0,
) -> tuple[Terrain, SimulationResult, dict[str, float]]:
    """Escenario heterogéneo de referencia."""
    terrain = generate_terrain(
        size=size,
        cell_size=cell_size,
        seed=seed,
        relief=80.0,
        vegetation=0.70,
        moisture=moisture,
        wind_speed=wind_speed,
        wind_direction=0.0,
        lake=True,
    )
    model = DeterministicCA(terrain, dt=dt)
    initial = model.state.copy()
    result = model.run(t_end, snapshot_times=(300.0, 600.0, 900.0), record_every=10.0)
    result.snapshots[0.0] = initial
    summary = summarize(result, cell_size)
    summary.update(terrain.summary())
    np.savez_compressed(
        DATA / "baseline.npz",
        times=result.times,
        burned_area=result.burned_area,
        active_cells=result.active_cells,
        head_distance=result.head_distance,
        arrival=result.arrival,
        state=result.state,
        burned_mask=result.burned_mask,
        **{f"snap_{int(t)}": snap for t, snap in result.snapshots.items()},
    )
    np.savez_compressed(
        DATA / "terrain.npz",
        elevation=terrain.elevation,
        fuel_type=terrain.fuel_type,
        moisture=terrain.moisture,
        veg_density=terrain.veg_density,
        load_factor=terrain.load_factor,
        grad_x=terrain.grad_x,
        grad_y=terrain.grad_y,
    )
    return terrain, result, summary


def ensemble_experiment(
    size: int = 160,
    cell_size: float = 5.0,
    seed: int = 7,
    moisture: float = 0.07,
    wind_speed: float = 4.0,
    t_end: float = 600.0,
    n_members: int = 32,
    dt: float = 1.0,
) -> tuple[Terrain, list[SimulationResult], dict[str, np.ndarray]]:
    """Ensemble Monte Carlo del autómata probabilístico."""
    terrain = generate_terrain(
        size=size,
        cell_size=cell_size,
        seed=seed,
        relief=60.0,
        vegetation=0.70,
        moisture=moisture,
        wind_speed=wind_speed,
        wind_direction=0.0,
        lake=True,
    )
    members = run_ensemble(
        terrain,
        n_members=n_members,
        t_end=t_end,
        dt=dt,
        seed=seed * 1000,
        snapshot_times=(200.0, 400.0, 600.0),
        record_every=10.0,
    )
    det_model = DeterministicCA(terrain, dt=dt)
    det_result = det_model.run(t_end, record_every=10.0)
    times = np.arange(0.0, t_end + 1e-9, 10.0)
    stats = ensemble_statistics(members, times, cell_area=cell_size**2)
    stats["det_area"] = (
        np.interp(times, det_result.times, det_result.burned_area, left=0.0) * cell_size**2
    )
    # Probabilidad de quema en los tiempos de snapshot.
    p_snapshots = {}
    for t in (200.0, 400.0, 600.0):
        stack = []
        for m in members:
            snapshot = m.snapshots.get(t)
            if snapshot is not None:
                stack.append((snapshot == 1) | (snapshot == 2))
        if stack:
            p_snapshots[t] = np.mean(np.stack(stack), axis=0)
    stats["times"] = times
    stats["p_snapshots"] = p_snapshots  # type: ignore[assignment]
    np.savez_compressed(
        DATA / "ensemble.npz",
        times=times,
        mean_area=stats["mean_area"],
        std_area=stats["std_area"],
        cv_area=stats["cv_area"],
        p_burn=stats["p_burn"],
        mean_arrival=stats["mean_arrival"],
        **{f"p_burn_{int(t)}": arr for t, arr in p_snapshots.items()},
        final_areas=np.array(
            [np.count_nonzero((m.state == 1) | (m.state == 2)) for m in members], dtype=float
        ),
        det_area=stats["det_area"],
        det_times=times,
        det_state=det_result.state,
    )
    return terrain, members, stats


def comparison_table(
    det: SimulationResult,
    ensemble: Sequence[SimulationResult],
    cell_size: float,
) -> pd.DataFrame:
    """Tabla comparativa determinista vs estocástico."""
    det_summary = summarize(det, cell_size)
    det_ros, _ = rate_of_spread(det.times, det.head_distance)
    rows = [
        {
            "modelo": "Determinista",
            "area_media_ha": det_summary["burned_area_m2"] / 1e4,
            "area_std_ha": 0.0,
            "cv_area": 0.0,
            "ros_medio_m_min": det_ros * 60.0,
            "ros_std_m_min": 0.0,
            "lb_medio": det_summary["length_breadth"],
            "fd_media": det_summary["fractal_dimension"],
            "rugosidad_s": det_summary["roughness_s"],
        }
    ]
    summaries = [summarize(r, cell_size) for r in ensemble]
    areas = np.array([s["burned_area_m2"] / 1e4 for s in summaries])
    ros = np.array([rate_of_spread(r.times, r.head_distance)[0] * 60.0 for r in ensemble])
    lb = np.array([s["length_breadth"] for s in summaries])
    fd = np.array([s["fractal_dimension"] for s in summaries])
    rough = np.array([s["roughness_s"] for s in summaries])
    rows.append(
        {
            "modelo": "Estocástico (ensemble)",
            "area_media_ha": float(areas.mean()),
            "area_std_ha": float(areas.std(ddof=1)),
            "cv_area": float(areas.std(ddof=1) / areas.mean()) if areas.mean() else 0.0,
            "ros_medio_m_min": float(ros.mean()),
            "ros_std_m_min": float(ros.std(ddof=1)),
            "lb_medio": float(lb.mean()),
            "fd_media": float(fd.mean()),
            "rugosidad_s": float(rough.mean()),
        }
    )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Barridos paramétricos
# ---------------------------------------------------------------------------
def wind_sweep(
    winds: Sequence[float] = (0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0),
    size: int = 192,
    t_end: float = 900.0,
    fuel_code: str = "FM10",
    moisture: float = 0.07,
    cell_size: float = 5.0,
    dt: float = 1.0,
) -> pd.DataFrame:
    rows = []
    for wind in winds:
        terrain = homogeneous_terrain(size, fuel_code, moisture, wind, cell_size)
        model = DeterministicCA(terrain, dt=dt)
        result = model.run(t_end, record_every=30.0)
        s = summarize(result, cell_size)
        ros_fit, r2_fit = rate_of_spread(result.times, result.head_distance)
        rows.append(
            {
                "viento_m_s": wind,
                "ros_m_min": s["ros_m_min"],
                "ros_m_s": s["ros_m_s"],
                "ros_r2": s["ros_r2"],
                "ros_ajuste_m_min": ros_fit * 60.0,
                "area_ha": s["burned_area_m2"] / 1e4,
                "lb": s["length_breadth"],
                "fd": s["fractal_dimension"],
                "head_m": float(result.head_distance[-1]),
            }
        )
    return pd.DataFrame(rows)


def moisture_sweep(
    moistures: Sequence[float] = (0.03, 0.05, 0.07, 0.09, 0.11, 0.13, 0.15, 0.18, 0.21, 0.24),
    size: int = 160,
    t_end: float = 1200.0,
    fuel_code: str = "FM10",
    wind_speed: float = 0.0,
    cell_size: float = 5.0,
    dt: float = 1.0,
) -> pd.DataFrame:
    rows = []
    for moisture in moistures:
        terrain = homogeneous_terrain(size, fuel_code, moisture, wind_speed, cell_size)
        model = DeterministicCA(terrain, dt=dt)
        result = model.run(t_end, record_every=30.0)
        s = summarize(result, cell_size)
        rows.append(
            {
                "humedad": moisture,
                "ros_m_min": s["ros_m_min"],
                "area_ha": s["burned_area_m2"] / 1e4,
                "lb": s["length_breadth"],
                "head_m": float(result.head_distance[-1]),
            }
        )
    return pd.DataFrame(rows)


def slope_sweep(
    slopes: Sequence[float] = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6),
    size: int = 160,
    t_end: float = 900.0,
    fuel_code: str = "FM10",
    moisture: float = 0.07,
    cell_size: float = 5.0,
    dt: float = 1.0,
) -> pd.DataFrame:
    rows = []
    for slope in slopes:
        terrain = homogeneous_terrain(size, fuel_code, moisture, 0.0, cell_size, slope=slope)
        model = DeterministicCA(terrain, dt=dt)
        result = model.run(t_end, record_every=30.0)
        s = summarize(result, cell_size)
        rows.append(
            {
                "pendiente": slope,
                "pendiente_grados": float(np.degrees(np.arctan(slope))),
                "ros_m_min": s["ros_m_min"],
                "area_ha": s["burned_area_m2"] / 1e4,
                "lb": s["length_breadth"],
                "head_m": float(result.head_distance[-1]),
            }
        )
    return pd.DataFrame(rows)


def percolation_experiment(
    occupancies: Sequence[float] = tuple(np.linspace(0.25, 0.75, 21)),
    size: int = 64,
    realizations: int = 80,
    seed: int = 123,
) -> tuple[pd.DataFrame, dict[str, float]]:
    """Probabilidad de percolación en función de la ocupación del paisaje."""
    rows = []
    thresholds = {}
    for neighborhood in ("vonneumann", "moore"):
        for p in occupancies:
            spanned = 0
            for k in range(realizations):
                terrain = binary_forest(
                    size, p, seed=seed + 1000 * k, fuel_code="FM1", moisture=0.05
                )
                ignition = np.zeros((size, size), dtype=bool)
                ignition[:, 0] = True
                mtt = MinimumTravelTime(
                    terrain,
                    ignition=ignition,
                    neighborhood=neighborhood,
                )
                if np.any(np.isfinite(mtt.arrival[:, -1])):
                    spanned += 1
            rows.append(
                {
                    "vecindad": "Von Neumann (4)" if neighborhood == "vonneumann" else "Moore (8)",
                    "ocupacion": float(p),
                    "p_percolacion": spanned / realizations,
                    "realizaciones": realizations,
                }
            )
    df = pd.DataFrame(rows)
    for neighborhood in ("Von Neumann (4)", "Moore (8)"):
        sub = df[df["vecindad"] == neighborhood]
        xc, k = logistic_threshold(sub["ocupacion"].to_numpy(), sub["p_percolacion"].to_numpy())
        thresholds[neighborhood] = float(xc)
    return df, thresholds


def grid_convergence(
    cell_sizes: Sequence[float] = (10.0, 5.0, 2.5, 1.25),
    domain: float = 640.0,
    t_end: float = 600.0,
    fuel_code: str = "FM10",
    moisture: float = 0.07,
    wind_speed: float = 4.0,
    dt: float = 0.5,
) -> pd.DataFrame:
    rows = []
    for cell_size in cell_sizes:
        size = int(round(domain / cell_size))
        terrain = homogeneous_terrain(size, fuel_code, moisture, wind_speed, cell_size)
        model = DeterministicCA(terrain, dt=dt, ignition=ignition_mask(terrain.shape, "line_left"))
        result = model.run(t_end, record_every=30.0)
        s = summarize(result, cell_size)
        rows.append(
            {
                "celda_m": cell_size,
                "n": size,
                "ros_m_min": s["ros_m_min"],
                "area_ha": s["burned_area_m2"] / 1e4,
                "lb": s["length_breadth"],
            }
        )
    df = pd.DataFrame(rows)
    ref = df["ros_m_min"].iloc[-1]
    df["error_rel"] = (df["ros_m_min"] - ref).abs() / ref
    orders = []
    for i in range(1, len(df)):
        e0, e1 = df["error_rel"].iloc[i - 1], df["error_rel"].iloc[i]
        ratio = df["celda_m"].iloc[i - 1] / df["celda_m"].iloc[i]
        orders.append(np.log(e0 / e1) / np.log(ratio) if e1 > 0 and e0 > 0 else np.nan)
    df["orden"] = [np.nan] + orders
    return df


def timestep_convergence(
    dts: Sequence[float] = (2.0, 1.0, 0.5, 0.25, 0.125),
    size: int = 128,
    t_end: float = 600.0,
    fuel_code: str = "FM10",
    moisture: float = 0.07,
    wind_speed: float = 4.0,
) -> pd.DataFrame:
    rows = []
    for dt in dts:
        terrain = homogeneous_terrain(size, fuel_code, moisture, wind_speed, 5.0)
        model = DeterministicCA(terrain, dt=dt, ignition=ignition_mask(terrain.shape, "line_left"))
        result = model.run(t_end, record_every=30.0)
        s = summarize(result, 5.0)
        rows.append(
            {
                "dt_s": dt,
                "ros_m_min": s["ros_m_min"],
                "area_ha": s["burned_area_m2"] / 1e4,
                "lb": s["length_breadth"],
            }
        )
    df = pd.DataFrame(rows)
    ref = df["ros_m_min"].iloc[-1]
    df["error_rel"] = (df["ros_m_min"] - ref).abs() / ref
    return df


def sensitivity_experiment(
    size: int = 128,
    t_end: float = 600.0,
    seed: int = 11,
    moisture: float = 0.07,
    wind_speed: float = 4.0,
    variations: Sequence[float] = (0.7, 0.85, 1.0, 1.15, 1.3),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Sensibilidad local (OAT) de la ROS a cuatro parámetros."""
    rows = []
    for parameter in ("viento", "humedad", "carga", "pendiente"):
        for factor in variations:
            # Se usa un terreno homogéneo para aislar la elasticidad local de
            # cada parámetro; la heterogeneidad se estudia por separado.
            terrain = homogeneous_terrain(
                size=size,
                fuel_code="FM10",
                moisture=moisture,
                wind_speed=wind_speed,
                cell_size=5.0,
                slope=0.0,
            )
            if parameter == "viento":
                terrain.wind_speed = wind_speed * factor
            elif parameter == "humedad":
                terrain.moisture = np.clip(terrain.moisture * factor, 0.02, 0.24)
            elif parameter == "carga":
                terrain.load_factor = terrain.load_factor * factor
            elif parameter == "pendiente":
                slope = 0.2 * factor
                yy, xx = np.mgrid[0:size, 0:size]
                terrain.elevation = slope * xx * terrain.cell_size
                terrain.grad_x = np.full(terrain.shape, slope)
                terrain.grad_y = np.zeros(terrain.shape)
            model = DeterministicCA(terrain, dt=1.0)
            result = model.run(t_end, record_every=30.0)
            s = summarize(result, terrain.cell_size)
            rows.append(
                {
                    "parametro": parameter,
                    "factor": factor,
                    "ros_m_min": s["ros_m_min"],
                    "area_ha": s["burned_area_m2"] / 1e4,
                }
            )
    df = pd.DataFrame(rows)
    sens = []
    for parameter, group in df.groupby("parametro"):
        group = group.sort_values("factor")
        x = np.log(group["factor"].to_numpy())
        y = np.log(np.maximum(group["ros_m_min"].to_numpy(), 1e-9))
        slope = np.polyfit(x, y, 1)[0]
        sens.append({"parametro": parameter, "elasticidad": float(slope)})
    return df, pd.DataFrame(sens)


# ---------------------------------------------------------------------------
# Experimentos numéricos de las sesiones 1–6
# ---------------------------------------------------------------------------
def numerics_experiments() -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    out["punto_flotante"] = pd.DataFrame(floating_point_table())
    out["raices"] = pd.DataFrame(root_methods_table(STANDARD_FUELS["FM10"]))
    out["edo"] = pd.DataFrame(convergence_table())
    out["pendulo"] = pd.DataFrame(pendulum_table())
    out["euler_cromer"] = pd.DataFrame(pendulum_integrator_table())
    out["nbody"] = pd.DataFrame(nbody_table())
    out["sde"] = pd.DataFrame(fokker_planck_table())

    # Trayectorias de error de los métodos de raíces para la figura.
    model = STANDARD_FUELS["FM10"]
    root, target = solve_moisture_threshold(model, 0.5, 0.05)

    def f(m: float) -> float:
        from .fuels import base_rate_of_spread

        return float(base_rate_of_spread(model.load, model.sav, model.depth, m, model.mx)) - target

    from .numerics import bisection, false_position, newton_raphson, secant

    def df(m: float) -> float:
        h = 1e-7
        return (f(m + h) - f(m - h)) / (2.0 * h)

    methods = [
        bisection(f, 1e-4, 0.98 * model.mx),
        false_position(f, 1e-4, 0.98 * model.mx),
        newton_raphson(f, df, 0.5 * 0.98 * model.mx),
        secant(f, 1e-4, 0.98 * model.mx),
    ]
    hist = []
    for res in methods:
        for i, x in enumerate(res.roots):
            hist.append(
                {
                    "metodo": res.method,
                    "iteracion": i,
                    "error": abs(f(x)),
                    "error_x": abs(x - root),
                }
            )
    out["raices_historia"] = pd.DataFrame(hist)

    # MSD de Langevin.
    times, paths = langevin_paths(
        velocity=0.5, sigma=0.2, t_end=10.0, dt=0.01, n_paths=4000, seed=123
    )
    t_msd, msd, slope = msd_curve(times, paths)
    np.savez_compressed(DATA / "langevin.npz", times=t_msd, msd=msd, paths=paths[:, ::50, 0])
    out["langevin"] = pd.DataFrame(
        [{"pendiente_msd": slope, "msd_t10": float(msd[-1]), "teorica_t10": 0.04 * 10.0}]
    )

    # PDF de Fokker-Planck en t = 5.
    idx = int(round(5.0 / 0.01))
    sample = paths[:, idx, 0]
    np.savez_compressed(DATA / "fokker_planck.npz", sample=sample, t=5.0, velocity=0.5, sigma=0.2)

    # Autómatas celulares clásicos.
    rule_rows = []
    for rho in np.linspace(0.05, 0.95, 19):
        flows = [rule184_density_flow(float(rho), size=400, steps=300, seed=s)[0] for s in range(3)]
        rule_rows.append(
            {
                "densidad": float(rho),
                "flujo": float(np.mean(flows)),
                "flujo_std": float(np.std(flows, ddof=1)),
                "flujo_teorico": min(float(rho), 1.0 - float(rho)),
            }
        )
    out["regla184"] = pd.DataFrame(rule_rows)

    nasch_rows = []
    for p_brake in (0.0, 0.25, 0.5):
        for rho in np.linspace(0.05, 0.95, 10):
            flows = [
                nagel_schreckenberg_density_flow(
                    float(rho), size=250, steps=400, p_brake=p_brake, seed=s
                )[0]
                for s in range(2)
            ]
            nasch_rows.append(
                {
                    "densidad": float(rho),
                    "flujo": float(np.mean(flows)),
                    "p_frenado": p_brake,
                }
            )
    out["nasch"] = pd.DataFrame(nasch_rows)

    # Diagramas espacio-temporales.
    rng = np.random.default_rng(3)
    road = (rng.random(200) < 0.35).astype(np.int8)
    frames = [road.copy()]
    for _ in range(120):
        road = rule184_step(road)
        frames.append(road.copy())
    np.savez_compressed(DATA / "regla184_espaciotiempo.npz", frames=np.vstack(frames))

    gol = [glider((24, 24))]
    state = gol[0].copy()
    for _ in range(12):
        state = game_of_life_step(state)
        gol.append(state.copy())
    np.savez_compressed(DATA / "game_of_life.npz", frames=np.stack(gol))

    # Pavesas: trayectorias y alcance.
    from .numerics import firebrand_trajectory

    traj = {}
    for wind in (0.0, 4.0, 8.0, 12.0):
        t, states = firebrand_trajectory(wind, k=0.05, v0=6.0, angle_deg=30.0, t_end=12.0, dt=0.01)
        traj[str(wind)] = (t, states)
    np.savez_compressed(
        DATA / "firebrand.npz",
        **{f"t_{k}": v[0] for k, v in traj.items()},
        **{f"x_{k}": v[1][:, 0] for k, v in traj.items()},
        **{f"y_{k}": v[1][:, 1] for k, v in traj.items()},
    )
    return out


def save_all_tables(tables: dict[str, pd.DataFrame]) -> None:
    ensure_dirs()
    for name, df in tables.items():
        df.to_csv(TABLES / f"{name}.csv", index=False, float_format="%.8g")


def save_summary(summary: dict[str, object], path: Path | None = None) -> None:
    ensure_dirs()
    path = path or (RESULTS / "summary.json")
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


def stochastic_enhancement(
    winds: Sequence[float] = (0.0, 1.0, 2.0, 3.0, 4.0),
    size: int = 160,
    t_end: float = 600.0,
    n_members: int = 8,
    seed: int = 5,
) -> pd.DataFrame:
    """Cociente entre el área media estocástica y la determinista.

    Permite cuantificar cómo crece la ventaja del ensemble (percolación de
    primer paso) al aumentar la anisotropía del frente.
    """
    rows = []
    for wind in winds:
        terrain = generate_terrain(
            size=size,
            seed=seed,
            relief=60.0,
            vegetation=0.70,
            moisture=0.07,
            wind_speed=wind,
            lake=True,
        )
        det = DeterministicCA(terrain, dt=1.0).run(t_end, record_every=10.0)
        areas = []
        for k in range(n_members):
            stoch = StochasticCA(terrain, dt=1.0, seed=seed * 1000 + k)
            result = stoch.run(t_end, record_every=10.0)
            areas.append(result.final_burned_area)
        mean_area = float(np.mean(areas))
        rows.append(
            {
                "viento_m_s": wind,
                "area_det_celdas": float(det.final_burned_area),
                "area_estoc_celdas": mean_area,
                "area_estoc_std_celdas": float(np.std(areas, ddof=1)),
                "cociente": mean_area / max(float(det.final_burned_area), 1.0),
            }
        )
    return pd.DataFrame(rows)


def real_cases_experiment(
    size: int = 160,
    dt: float = 20.0,
    t_end: float = 4.0 * 24.0 * 3600.0,
) -> pd.DataFrame:
    """Ejecuta los dos casos reales y guarda arreglos para las figuras."""
    rows = []
    for case in (ACOS, LITTLE_GIANT):
        terrain, result, observed, metrics = run_case(case, size=size, dt=dt, t_end=t_end)
        np.savez_compressed(
            DATA / f"caso_{case.key}.npz",
            elevation=terrain.elevation,
            fuel_type=terrain.fuel_type,
            moisture=terrain.moisture,
            grad_x=terrain.grad_x,
            grad_y=terrain.grad_y,
            state=result.state,
            arrival=result.arrival,
            burned_mask=result.burned_mask,
            observed=observed,
            times=result.times,
            burned_area=result.burned_area,
            head_distance=result.head_distance,
            cell_size=terrain.cell_size,
            lat=case.latitude,
            lon=case.longitude,
            bbox=np.asarray(case.bbox),
        )
        rows.append(
            {
                "caso": case.name,
                "pais": case.country,
                "inicio": case.start.strftime("%Y-%m-%d %H:%M"),
                "area_observada_ha": metrics["observed_area_ha"],
                "area_oficial_ha": metrics["observed_area_official_ha"],
                "area_simulada_ha": metrics["simulated_area_ha"],
                "error_area_rel": metrics["area_error_rel"],
                "iou": metrics["iou"],
                "ros_m_min": metrics["ros_m_min"],
                "lb": metrics["length_breadth"],
                "fd": metrics["fractal_dimension"],
                "celda_m": terrain.cell_size,
                "dt_s": dt,
                "t_end_dias": t_end / 86400.0,
                "fuente": case.source,
            }
        )
    return pd.DataFrame(rows)
