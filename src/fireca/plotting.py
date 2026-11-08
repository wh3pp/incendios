"""Figuras del documento Typst.

Todas las figuras se guardan en PDF (vectorial) y PNG (previsualización) en
``results/figures``. El estilo es sobrio, con tipografía serif y paletas
accesibles para daltonismo.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch

from .numerics import fokker_planck_gaussian

RESULTS = Path("results")
TABLES = RESULTS / "tables"
FIGURES = RESULTS / "figures"
DATA = RESULTS / "data"

PALETTE = {
    "blue": "#2b6cb0",
    "orange": "#dd6b20",
    "green": "#2f855a",
    "red": "#c53030",
    "purple": "#6b46c1",
    "gray": "#4a5568",
}

FUEL_COLORS = ["#d9d9d9", "#e6c34a", "#5aa05a", "#8a5a2b", "#1f5f2a"]
STATE_COLORS = ["#4caf50", "#ff3b30", "#2b2b2b", "#9ecae1"]


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Libertinus Serif", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "font.size": 9,
            "axes.labelsize": 9,
            "axes.titlesize": 10,
            "legend.fontsize": 8,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "axes.linewidth": 0.7,
            "lines.linewidth": 1.4,
            "figure.dpi": 150,
            "savefig.dpi": 300,
        }
    )


def _save(fig: plt.Figure, name: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / f"{name}.pdf", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(FIGURES / f"{name}.png", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def plot_terrain() -> None:
    _style()
    data = np.load(DATA / "terrain.npz")
    elevation = data["elevation"]
    fuel = data["fuel_type"]
    moisture = data["moisture"]
    veg = data["veg_density"]
    extent = (0, elevation.shape[1] * 5.0 / 1000.0, 0, elevation.shape[0] * 5.0 / 1000.0)
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.8), constrained_layout=True)
    im0 = axes[0, 0].imshow(elevation, cmap="terrain", extent=extent, origin="upper")
    axes[0, 0].set_title("(a) Elevación")
    fig.colorbar(im0, ax=axes[0, 0], label="m", shrink=0.85)
    cmap = ListedColormap(FUEL_COLORS)
    norm = BoundaryNorm([-1.5, -0.5, 0.5, 1.5, 2.5, 3.5], cmap.N)
    im1 = axes[0, 1].imshow(fuel, cmap=cmap, norm=norm, extent=extent, origin="upper")
    axes[0, 1].set_title("(b) Modelo de combustible")
    cbar = fig.colorbar(im1, ax=axes[0, 1], ticks=[-1, 0, 1, 2, 3], shrink=0.85)
    cbar.ax.set_yticklabels(["Sin combustible", "Pasto", "Matorral", "Hojarasca", "Bosque"])
    im2 = axes[1, 0].imshow(moisture, cmap="YlGnBu", extent=extent, origin="upper")
    axes[1, 0].set_title("(c) Humedad del combustible")
    fig.colorbar(im2, ax=axes[1, 0], label="fracción", shrink=0.85)
    im3 = axes[1, 1].imshow(veg, cmap="Greens", extent=extent, origin="upper", vmin=0, vmax=1)
    axes[1, 1].set_title("(d) Densidad de vegetación")
    fig.colorbar(im3, ax=axes[1, 1], label="índice", shrink=0.85)
    for ax in axes.flat:
        ax.set_xlabel("x [km]")
        ax.set_ylabel("y [km]")
    # Punto de ignición (centro del dominio).
    cx = extent[1] / 2.0
    cy = extent[3] / 2.0
    for ax in (axes[0, 0], axes[0, 1], axes[1, 0], axes[1, 1]):
        ax.plot(
            [cx],
            [cy],
            marker="*",
            color="#c53030",
            markersize=8,
            markeredgecolor="white",
            markeredgewidth=0.5,
        )
    _save(fig, "terreno")


def plot_baseline() -> None:
    _style()
    data = np.load(DATA / "baseline.npz")
    cmap = ListedColormap(STATE_COLORS)
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], cmap.N)
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.6), constrained_layout=True)
    for ax, t in zip(axes, (0, 300, 600), strict=False):
        state = data[f"snap_{t}"]
        ax.imshow(state, cmap=cmap, norm=norm, interpolation="nearest")
        ax.set_title(f"t = {t} s")
        ax.set_xticks([])
        ax.set_yticks([])
    axes[0].set_ylabel("y [celdas]")
    handles = [
        Patch(color=STATE_COLORS[0], label="No quemado"),
        Patch(color=STATE_COLORS[1], label="Combustionando"),
        Patch(color=STATE_COLORS[2], label="Quemado"),
        Patch(color=STATE_COLORS[3], label="Incombustible"),
    ]
    fig.legend(
        handles=handles, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.08)
    )
    _save(fig, "escenario_base")

    # Mapa de tiempos de llegada.
    fig, ax = plt.subplots(figsize=(3.6, 3.1), constrained_layout=True)
    arrival = data["arrival"]
    masked = np.ma.masked_invalid(arrival)
    im = ax.imshow(masked, cmap="magma_r", interpolation="nearest")
    ax.set_title("Tiempo de llegada del frente")
    ax.set_xticks([])
    ax.set_yticks([])
    fig.colorbar(im, ax=ax, label="t [s]", shrink=0.85)
    _save(fig, "tiempo_llegada")


def plot_wind_sweep() -> None:
    _style()
    df = pd.read_csv(TABLES / "viento.csv")
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.8), constrained_layout=True)
    ax = axes[0]
    ax.plot(df["viento_m_s"], df["ros_m_min"], "o-", color=PALETTE["red"], label="ROS de cabeza")
    ax.set_xlabel("Velocidad del viento [m s$^{-1}$]")
    ax.set_ylabel("ROS [m min$^{-1}$]")
    ax.set_title("(a) Velocidad de propagación")
    ax.grid(alpha=0.3)
    ax = axes[1]
    ax.plot(df["viento_m_s"], df["lb"], "s-", color=PALETTE["blue"])
    ax.set_xlabel("Velocidad del viento [m s$^{-1}$]")
    ax.set_ylabel("Relación largo/ancho")
    ax.set_title("(b) Elongación de la huella")
    ax.grid(alpha=0.3)
    _save(fig, "barrido_viento")


def plot_moisture() -> None:
    _style()
    df = pd.read_csv(TABLES / "humedad.csv")
    fig, ax1 = plt.subplots(figsize=(4.2, 2.9), constrained_layout=True)
    ax1.plot(df["humedad"], df["ros_m_min"], "o-", color=PALETTE["red"])
    ax1.set_xlabel("Humedad del combustible $M$ [fracción]")
    ax1.set_ylabel("ROS [m min$^{-1}$]", color=PALETTE["red"])
    ax1.tick_params(axis="y", colors=PALETTE["red"])
    ax1.axvline(0.25, ls="--", color=PALETTE["gray"], lw=1)
    ax1.annotate(
        "$M_x$ (FM10)",
        xy=(0.25, 0.9),
        xycoords=("data", "axes fraction"),
        xytext=(-4, 0),
        textcoords="offset points",
        ha="right",
        va="top",
        fontsize=8,
    )
    ax1.grid(alpha=0.3)
    _save(fig, "barrido_humedad")


def plot_slope() -> None:
    _style()
    df = pd.read_csv(TABLES / "pendiente.csv")
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.8), constrained_layout=True)
    axes[0].plot(df["pendiente_grados"], df["ros_m_min"], "o-", color=PALETTE["orange"])
    axes[0].set_xlabel("Pendiente [°]")
    axes[0].set_ylabel("ROS [m min$^{-1}$]")
    axes[0].set_title("(a) Propagación cuesta arriba")
    axes[0].grid(alpha=0.3)
    axes[1].plot(df["pendiente_grados"], df["lb"], "s-", color=PALETTE["purple"])
    axes[1].set_xlabel("Pendiente [°]")
    axes[1].set_ylabel("Relación largo/ancho")
    axes[1].set_title("(b) Elongación")
    axes[1].grid(alpha=0.3)
    _save(fig, "barrido_pendiente")


def plot_percolation() -> None:
    _style()
    df = pd.read_csv(TABLES / "percolacion.csv")
    fig, ax = plt.subplots(figsize=(4.4, 3.0), constrained_layout=True)
    for label, color in (("Von Neumann (4)", PALETTE["blue"]), ("Moore (8)", PALETTE["orange"])):
        sub = df[df["vecindad"] == label]
        ax.plot(sub["ocupacion"], sub["p_percolacion"], "o-", ms=3.5, color=color, label=label)
    ax.axvline(0.5927, ls=":", color=PALETTE["blue"], lw=1.2)
    ax.axvline(0.4073, ls=":", color=PALETTE["orange"], lw=1.2)
    ax.set_xlabel("Ocupación del paisaje $p$")
    ax.set_ylabel("Probabilidad de percolación")
    ax.set_ylim(-0.03, 1.03)
    ax.legend(frameon=False, loc="lower right")
    ax.grid(alpha=0.3)
    _save(fig, "percolacion")


def plot_det_vs_stoch() -> None:
    _style()
    data = np.load(DATA / "ensemble.npz")
    times = data["times"]
    mean = data["mean_area"] / 1e4
    std = data["std_area"] / 1e4
    fig, axes = plt.subplots(1, 3, figsize=(7.5, 2.7), constrained_layout=True)
    ax = axes[0]
    det_area = data["det_area"] / 1e4
    ax.plot(data["det_times"], det_area, color=PALETTE["gray"], ls="--", label="Determinista")
    ax.plot(times, mean, color=PALETTE["red"], label="Media del ensemble")
    ax.fill_between(
        times, mean - std, mean + std, color=PALETTE["red"], alpha=0.18, label="±1 desv. est."
    )
    ax.set_xlabel("t [s]")
    ax.set_ylabel("Área quemada [ha]")
    ax.set_title("(a) Área quemada")
    ax.legend(frameon=False, fontsize=7)
    ax.grid(alpha=0.3)
    ax = axes[1]
    p = data["p_burn_400"] if "p_burn_400" in data else data["p_burn"]
    im = ax.imshow(p, cmap="inferno", vmin=0, vmax=1, interpolation="nearest")
    ax.set_title("(b) $P$(quema) a $t=400$ s")
    ax.set_xticks([])
    ax.set_yticks([])
    fig.colorbar(im, ax=ax, shrink=0.85)
    ax = axes[2]
    areas = data["final_areas"] * 25.0 / 1e4
    ax.hist(areas, bins=10, color=PALETTE["blue"], alpha=0.75, edgecolor="white")
    ax.set_xlabel("Área final [ha]")
    ax.set_ylabel("Frecuencia")
    ax.set_title("(c) Distribución final")
    ax.grid(alpha=0.3)
    _save(fig, "det_vs_estocastico")


def plot_numerics() -> None:
    _style()
    hist = pd.read_csv(TABLES / "raices_historia.csv")
    edo = pd.read_csv(TABLES / "edo.csv")
    langevin = np.load(DATA / "langevin.npz")
    fp = np.load(DATA / "fokker_planck.npz")
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.6), constrained_layout=True)

    ax = axes[0, 0]
    for method, color in (
        ("Bisección", PALETTE["gray"]),
        ("Falsa posición", PALETTE["blue"]),
        ("Newton-Raphson", PALETTE["red"]),
        ("Secante", PALETTE["green"]),
    ):
        sub = hist[hist["metodo"] == method]
        ax.semilogy(
            sub["iteracion"],
            np.maximum(sub["error"], 1e-18),
            "o-",
            ms=2.5,
            color=color,
            label=method,
        )
    ax.set_xlabel("Iteración")
    ax.set_ylabel("$|x_k - x^*|$")
    ax.set_title("(a) Métodos de raíces")
    ax.legend(frameon=False, fontsize=7)
    ax.grid(alpha=0.3, which="both")

    ax = axes[0, 1]
    for method, color in (
        ("euler", PALETTE["gray"]),
        ("rk2", PALETTE["blue"]),
        ("rk4", PALETTE["red"]),
    ):
        sub = edo[edo["metodo"] == method]
        ax.loglog(sub["dt"], sub["error"], "o-", color=color, label=method.upper())
    ax.set_xlabel("$\\Delta t$ [s]")
    ax.set_ylabel("Error absoluto en $v(5)$ [m s$^{-1}$]")
    ax.set_title("(b) Convergencia de integradores")
    ax.legend(frameon=False)
    ax.grid(alpha=0.3, which="both")

    ax = axes[1, 0]
    ax.loglog(langevin["times"][1:], langevin["msd"][1:], color=PALETTE["purple"], label="MSD")
    ax.set_xlabel("t [s]")
    ax.set_ylabel("MSD [m$^2$]")
    ax.set_title("(c) Movimiento browniano")
    ax.grid(alpha=0.3, which="both")

    ax = axes[1, 1]
    sample = fp["sample"]
    t = float(fp["t"])
    v = float(fp["velocity"])
    sigma = float(fp["sigma"])
    ax.hist(
        sample,
        bins=40,
        density=True,
        color=PALETTE["orange"],
        alpha=0.55,
        edgecolor="white",
        label="Langevin",
    )
    x = np.linspace(sample.min(), sample.max(), 400)
    ax.plot(x, fokker_planck_gaussian(x, t, v, sigma), color=PALETTE["red"], label="Fokker-Planck")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("Densidad")
    ax.set_title("(d) PDF en $t=5$ s")
    ax.legend(frameon=False)
    ax.grid(alpha=0.3)
    _save(fig, "numericos")


def plot_ca() -> None:
    _style()
    fig, axes = plt.subplots(1, 3, figsize=(7.5, 2.5), constrained_layout=True)
    st = np.load(DATA / "regla184_espaciotiempo.npz")["frames"]
    axes[0].imshow(st, cmap="binary", aspect="auto", interpolation="nearest")
    axes[0].set_title("(a) Regla 184")
    axes[0].set_xlabel("posición")
    axes[0].set_ylabel("paso temporal")
    rule = pd.read_csv(TABLES / "regla184.csv")
    axes[1].plot(
        rule["densidad"], rule["flujo"], "o", ms=3, color=PALETTE["blue"], label="Simulación"
    )
    axes[1].plot(
        rule["densidad"],
        rule["flujo_teorico"],
        "-",
        color=PALETTE["red"],
        label="$\\min(\\rho,1-\\rho)$",
    )
    axes[1].set_xlabel("densidad $\\rho$")
    axes[1].set_ylabel("flujo $J$")
    axes[1].set_title("(b) Diagrama fundamental")
    axes[1].legend(frameon=False, fontsize=7)
    axes[1].grid(alpha=0.3)
    nasch = pd.read_csv(TABLES / "nasch.csv")
    for p_brake, color in (
        (0.0, PALETTE["green"]),
        (0.25, PALETTE["orange"]),
        (0.5, PALETTE["purple"]),
    ):
        sub = nasch[nasch["p_frenado"] == p_brake]
        axes[2].plot(
            sub["densidad"], sub["flujo"], "o-", ms=2.5, color=color, label=f"$p$={p_brake}"
        )
    axes[2].set_xlabel("densidad $\\rho$")
    axes[2].set_ylabel("flujo $J$")
    axes[2].set_title("(c) Nagel-Schreckenberg")
    axes[2].legend(frameon=False, fontsize=7)
    axes[2].grid(alpha=0.3)
    _save(fig, "automatas")

    gol = np.load(DATA / "game_of_life.npz")["frames"]
    fig, axes = plt.subplots(1, 4, figsize=(5.4, 1.6), constrained_layout=True)
    for ax, idx in zip(axes, (0, 2, 4, 8), strict=False):
        ax.imshow(gol[idx], cmap="binary", interpolation="nearest")
        ax.set_title(f"t = {idx}", fontsize=8)
        ax.set_xticks([])
        ax.set_yticks([])
    _save(fig, "game_of_life")


def plot_firebrand() -> None:
    _style()
    data = np.load(DATA / "firebrand.npz")
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.8), constrained_layout=True)
    for wind, color in (
        (0.0, PALETTE["gray"]),
        (4.0, PALETTE["blue"]),
        (8.0, PALETTE["orange"]),
        (12.0, PALETTE["red"]),
    ):
        key = f"{wind:.1f}"
        x = data[f"x_{key}"]
        y = data[f"y_{key}"]
        y = np.where(y >= 0.0, y, np.nan)
        axes[0].plot(x, y, color=color, label=f"{wind:.0f} m/s")
    axes[0].set_xlabel("x [m]")
    axes[0].set_ylabel("y [m]")
    axes[0].set_title("(a) Trayectorias de pavesas")
    axes[0].set_ylim(bottom=0)
    axes[0].legend(frameon=False, fontsize=7)
    axes[0].grid(alpha=0.3)
    winds, ranges = [], []
    for wind in (0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 16.0):
        from .numerics import firebrand_trajectory

        t, states = firebrand_trajectory(wind, k=0.05, v0=6.0, angle_deg=30.0, t_end=20.0, dt=0.01)
        ground = np.where(states[:, 1] <= 0.0)[0]
        ranges.append(float(states[ground[0], 0]) if ground.size else float(states[-1, 0]))
        winds.append(wind)
    axes[1].plot(winds, ranges, "o-", color=PALETTE["red"])
    axes[1].set_xlabel("Viento [m s$^{-1}$]")
    axes[1].set_ylabel("Alcance [m]")
    axes[1].set_title("(b) Distancia de transporte")
    axes[1].grid(alpha=0.3)
    _save(fig, "pavesas")


def plot_sensitivity() -> None:
    _style()
    df = pd.read_csv(TABLES / "sensibilidad.csv")
    fig, ax = plt.subplots(figsize=(4.2, 2.5), constrained_layout=True)
    order = df.sort_values("elasticidad")
    colors = [PALETTE["red"] if v < 0 else PALETTE["green"] for v in order["elasticidad"]]
    ax.barh(order["parametro"], order["elasticidad"], color=colors, alpha=0.8)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_xlabel("Elasticidad de la ROS")
    ax.grid(alpha=0.3, axis="x")
    _save(fig, "sensibilidad")


def plot_grid_convergence() -> None:
    _style()
    df = pd.read_csv(TABLES / "convergencia_espacial.csv")
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.7), constrained_layout=True)
    axes[0].plot(df["celda_m"], df["ros_m_min"], "o-", color=PALETTE["blue"])
    axes[0].set_xlabel("Tamaño de celda [m]")
    axes[0].set_ylabel("ROS [m min$^{-1}$]")
    axes[0].set_title("(a) Convergencia espacial")
    axes[0].set_xticks(df["celda_m"])
    axes[0].grid(alpha=0.3)
    sub = df[df["error_rel"] > 0]
    axes[1].semilogy(sub["celda_m"], sub["error_rel"], "o-", color=PALETTE["red"])
    axes[1].set_xlabel("Tamaño de celda [m]")
    axes[1].set_ylabel("Error relativo")
    axes[1].set_title("(b) Error frente a la malla fina")
    axes[1].set_xticks(sub["celda_m"])
    axes[1].set_xticklabels([f"{x:g}" for x in sub["celda_m"]])
    axes[1].grid(alpha=0.3, which="both")
    _save(fig, "convergencia_espacial")


def _plot_case(case_key: str, title: str, name: str, show_observed: bool = True) -> None:
    """Figura de un caso real: DEM, máscara observada, simulación y área."""
    data = np.load(DATA / f"caso_{case_key}.npz")
    dem = data["elevation"]
    observed = data["observed"]
    burned = data["burned_mask"]
    cell = float(data["cell_size"])
    bbox = data["bbox"]
    lon_min, lat_min, lon_max, lat_max = bbox
    width_km = (lon_max - lon_min) * 111.32 * np.cos(np.radians(0.5 * (lat_min + lat_max)))
    height_km = (lat_max - lat_min) * 110.54
    extent = (0.0, width_km, 0.0, height_km)

    fig, axes = plt.subplots(1, 3, figsize=(7.6, 2.7), constrained_layout=True)
    ax = axes[0]
    im = ax.imshow(dem, cmap="terrain", extent=extent, origin="upper")
    ax.contour(
        observed.astype(float),
        levels=[0.5],
        colors=[PALETTE["red"]],
        linewidths=0.9,
        extent=extent,
        origin="upper",
    )
    ax.set_title("(a) DEM y área observada")
    ax.set_xlabel("x [km]")
    ax.set_ylabel("y [km]")
    fig.colorbar(im, ax=ax, label="m", shrink=0.85)

    ax = axes[1]
    ax.imshow(dem, cmap="gray", extent=extent, origin="upper", alpha=0.45)
    ax.imshow(
        np.ma.masked_where(~burned, burned),
        cmap="autumn",
        extent=extent,
        origin="upper",
        alpha=0.75,
    )
    if show_observed:
        ax.contour(
            observed.astype(float),
            levels=[0.5],
            colors=[PALETTE["blue"]],
            linewidths=0.9,
            extent=extent,
            origin="upper",
        )
    ax.set_title("(b) Simulación vs. observado" if show_observed else "(b) Área simulada")
    ax.set_xlabel("x [km]")
    ax.set_yticks([])

    ax = axes[2]
    t_days = data["times"] / 86400.0
    area_ha = data["burned_area"] * cell**2 / 1e4
    ax.plot(t_days, area_ha, color=PALETTE["red"], label="Simulado")
    ax.axhline(
        float(np.count_nonzero(observed) * cell**2 / 1e4),
        color=PALETTE["blue"],
        ls="--",
        label="Observado",
    )
    ax.set_xlabel("t [días]")
    ax.set_ylabel("Área [ha]")
    ax.set_title("(c) Área quemada")
    ax.legend(frameon=False, fontsize=7)
    ax.grid(alpha=0.3)
    fig.suptitle(title, fontsize=9.5)
    _save(fig, name)


def plot_real_cases() -> None:
    _style()
    _plot_case(
        "acos",
        "Acos (Cusco, Perú), 11–15 sep 2025",
        "caso_acos",
        show_observed=False,
    )
    _plot_case(
        "little_giant",
        "Little Giant (Washington, EE. UU.), jul 2026",
        "caso_little_giant",
    )
