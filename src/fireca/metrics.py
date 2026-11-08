"""Métricas de propagación, forma del frente y estadística de ensembles."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import curve_fit
from scipy.special import expit

from .ca import SimulationResult


@dataclass
class ShapeMetrics:
    """Descriptores geométricos de la huella de un incendio."""

    area_m2: float
    perimeter_m: float
    length_breadth: float
    eccentricity: float
    orientation_deg: float
    circularity: float
    fractal_dimension: float


def pca_shape(mask: NDArray[np.bool_], cell_size: float = 1.0) -> tuple[float, float, float, float]:
    """Valores propios, excentricidad y orientación de la nube de celdas quemadas.

    Returns
    -------
    major, minor, eccentricity, orientation_rad
    """
    rows, cols = np.nonzero(mask)
    if rows.size < 3:
        return 0.0, 0.0, 0.0, 0.0
    x = cols * cell_size
    y = -rows * cell_size
    coords = np.column_stack([x - x.mean(), y - y.mean()])
    cov = np.cov(coords, rowvar=False)
    eigvals, eigvecs = np.linalg.eigh(cov)
    order = np.argsort(eigvals)[::-1]
    eigvals = np.maximum(eigvals[order], 0.0)
    major = float(np.sqrt(eigvals[0]))
    minor = float(np.sqrt(eigvals[1]))
    eccentricity = float(np.sqrt(max(0.0, 1.0 - (minor / major) ** 2))) if major > 0 else 0.0
    v = eigvecs[:, order[0]]
    orientation = float(np.arctan2(v[1], v[0]))
    return major, minor, eccentricity, orientation


def length_breadth(mask: NDArray[np.bool_]) -> float:
    """Relación largo/ancho de la elipse equivalente."""
    major, minor, _, _ = pca_shape(mask)
    if minor <= 0.0:
        return 0.0
    return float(major / minor)


def perimeter(mask: NDArray[np.bool_], cell_size: float = 1.0) -> float:
    """Perímetro de la huella quemada, contando aristas de frontera."""
    if not np.any(mask):
        return 0.0
    padded = np.pad(mask, 1, mode="constant", constant_values=False)
    horizontal = np.count_nonzero(padded[1:, :] != padded[:-1, :])
    vertical = np.count_nonzero(padded[:, 1:] != padded[:, :-1])
    return float((horizontal + vertical) * cell_size)


def circularity(mask: NDArray[np.bool_], cell_size: float = 1.0) -> float:
    """Compacidad ``4 pi A / P^2`` (1 para un círculo)."""
    p = perimeter(mask, cell_size)
    if p <= 0.0:
        return 0.0
    area = float(np.count_nonzero(mask)) * cell_size**2
    return float(4.0 * np.pi * area / p**2)


def box_counting_dimension(
    mask: NDArray[np.bool_], min_box: int = 1, max_box: int | None = None
) -> float:
    """Dimensión fractal por conteo de cajas.

    Se ajusta ``log N(s) = -D log s + c`` para tamaños de caja ``s`` potencia
    de dos. Un frente compacto da ``D ~ 2``; un frente dendrítico, valores
    intermedios entre 1 y 2.
    """
    if not np.any(mask):
        return 0.0
    rows, cols = np.nonzero(mask)
    # Se recorta al rectángulo envolvente para eliminar el sesgo de
    # alineación de la retícula de cajas.
    mask = mask[rows.min() : rows.max() + 1, cols.min() : cols.max() + 1]
    h, w = mask.shape
    rows, cols = np.nonzero(mask)
    obj_h = int(rows.max() - rows.min() + 1)
    obj_w = int(cols.max() - cols.min() + 1)
    if max_box is None:
        # Se evita el régimen de cajas mayores que el objeto, donde el
        # conteo está dominado por el tamaño finito de la huella.
        max_box = max(2, min(obj_h, obj_w) // 4)
    sizes = []
    s = min_box
    while s <= max_box:
        sizes.append(s)
        s *= 2
    if len(sizes) < 2:
        return 0.0
    counts = []
    for s in sizes:
        n_r = int(np.ceil(h / s))
        n_c = int(np.ceil(w / s))
        padded = np.zeros((n_r * s, n_c * s), dtype=bool)
        padded[:h, :w] = mask
        blocks = padded.reshape(n_r, s, n_c, s).any(axis=(1, 3))
        counts.append(int(np.count_nonzero(blocks)))
    log_s = np.log(np.asarray(sizes, dtype=float))
    log_n = np.log(np.asarray(counts, dtype=float))
    slope, _ = np.polyfit(log_s, log_n, 1)
    return float(-slope)


def shape_metrics(mask: NDArray[np.bool_], cell_size: float = 1.0) -> ShapeMetrics:
    """Calcula todos los descriptores geométricos de una huella."""
    area = float(np.count_nonzero(mask)) * cell_size**2
    return ShapeMetrics(
        area_m2=area,
        perimeter_m=perimeter(mask, cell_size),
        length_breadth=length_breadth(mask),
        eccentricity=pca_shape(mask, cell_size)[2],
        orientation_deg=float(np.degrees(pca_shape(mask, cell_size)[3])),
        circularity=circularity(mask, cell_size),
        fractal_dimension=box_counting_dimension(mask),
    )


def rate_of_spread(
    times: NDArray[np.float64],
    head_distance: NDArray[np.float64],
    t_start: float | None = None,
) -> tuple[float, float]:
    """Velocidad media de avance del frente [m/s] y coeficiente ``R^2``.

    Se ajusta una recta a la distancia de cabeza en función del tiempo. El
    tramo inicial se descarta para evitar el transitorio de ignición.
    """
    if times.size < 2:
        return 0.0, 0.0
    t0 = times[0] if t_start is None else t_start
    mask = times >= t0
    if np.count_nonzero(mask) < 2:
        mask = np.ones_like(times, dtype=bool)
    t = times[mask]
    d = head_distance[mask]
    slope, intercept = np.polyfit(t, d, 1)
    pred = slope * t + intercept
    ss_res = float(np.sum((d - pred) ** 2))
    ss_tot = float(np.sum((d - d.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return float(slope), float(r2)


def head_ros_from_arrival(
    arrival: NDArray[np.float64],
    cell_size: float,
    wind_direction: float = 0.0,
    half_width_cells: float = 2.5,
) -> tuple[float, float]:
    """ROS de cabeza estimada a partir del mapa de tiempos de llegada.

    Se seleccionan las celdas cercanas al eje del viento y se ajusta
    ``t = a + s / R``. Es más robusto que derivar el área cuando el frente
    alcanza un borde del dominio.
    """
    finite = np.isfinite(arrival)
    if np.count_nonzero(finite) < 5:
        return 0.0, 0.0
    rows, cols = np.nonzero(finite)
    times = arrival[rows, cols]
    # Origen: centroide de las celdas con menor tiempo de llegada.
    t_min = float(np.min(times))
    seed = times <= t_min + 1e-6
    r0 = float(np.mean(rows[seed]))
    c0 = float(np.mean(cols[seed]))
    x = (cols - c0) * cell_size
    y = -(rows - r0) * cell_size
    s = x * np.cos(wind_direction) + y * np.sin(wind_direction)
    p = -x * np.sin(wind_direction) + y * np.cos(wind_direction)
    select = (np.abs(p) <= half_width_cells * cell_size) & (s >= 2.0 * cell_size)
    if np.count_nonzero(select) < 5:
        return 0.0, 0.0
    slope, intercept = np.polyfit(s[select], times[select], 1)
    if slope <= 0.0:
        return 0.0, 0.0
    pred = slope * s[select] + intercept
    ss_res = float(np.sum((times[select] - pred) ** 2))
    ss_tot = float(np.sum((times[select] - times[select].mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return float(1.0 / slope), float(r2)


def arrival_roughness(arrival: NDArray[np.float64], mask: NDArray[np.bool_]) -> float:
    """Desviación estándar de los tiempos de llegada en la frontera [s].

    La frontera se aproxima como las celdas quemadas que tienen al menos un
    vecino no quemado. Un frente perfectamente liso tiene rugosidad cero;
    un frente dendrítico, alta dispersión.
    """
    if not np.any(mask):
        return 0.0
    padded = np.pad(mask, 1, mode="constant", constant_values=False)
    interior = (
        padded[1:-1, 1:-1]
        & padded[:-2, 1:-1]
        & padded[2:, 1:-1]
        & padded[1:-1, :-2]
        & padded[1:-1, 2:]
    )
    boundary = mask & ~interior
    values = arrival[boundary & np.isfinite(arrival)]
    return float(np.std(values)) if values.size > 1 else 0.0


def interpolate_area(result: SimulationResult, times: NDArray[np.float64]) -> NDArray[np.float64]:
    """Interpola el área quemada en una malla temporal común."""
    return np.interp(
        times, result.times, result.burned_area, left=0.0, right=result.burned_area[-1]
    )


def ensemble_statistics(
    results: Sequence[SimulationResult],
    times: NDArray[np.float64],
    cell_area: float = 1.0,
) -> dict[str, NDArray[np.float64]]:
    """Estadísticos de área y probabilidad de quema de un ensemble.

    Returns
    -------
    dict con ``mean_area``, ``std_area``, ``cv_area``, ``p_burn`` y
    ``mean_arrival``.
    """
    areas = np.vstack([interpolate_area(r, times) for r in results]) * cell_area
    mean_area = areas.mean(axis=0)
    std_area = areas.std(axis=0, ddof=1) if areas.shape[0] > 1 else np.zeros_like(mean_area)
    cv = np.divide(std_area, mean_area, out=np.zeros_like(std_area), where=mean_area > 0)
    burn_counts = np.mean(np.stack([(r.state == 1) | (r.state == 2) for r in results]), axis=0)
    arrivals = np.stack([r.arrival for r in results])
    finite = np.isfinite(arrivals)
    counts = finite.sum(axis=0)
    sums = np.where(finite, arrivals, 0.0).sum(axis=0)
    mean_arrival = np.full(arrivals.shape[1:], np.inf)
    np.divide(sums, counts, out=mean_arrival, where=counts > 0)
    return {
        "mean_area": mean_area,
        "std_area": std_area,
        "cv_area": cv,
        "p_burn": burn_counts,
        "mean_arrival": mean_arrival,
    }


def spanning_probability(results: Iterable[SimulationResult], edge: str = "right") -> float:
    """Fracción de realizaciones que alcanzan el borde opuesto."""
    total = 0
    spanned = 0
    for result in results:
        total += 1
        mask = (result.state == 1) | (result.state == 2)
        if edge == "right":
            spanned += int(np.any(mask[:, -1]))
        elif edge == "left":
            spanned += int(np.any(mask[:, 0]))
        elif edge == "top":
            spanned += int(np.any(mask[0, :]))
        elif edge == "bottom":
            spanned += int(np.any(mask[-1, :]))
        else:
            raise ValueError(f"borde desconocido: {edge}")
    return spanned / total if total else 0.0


def logistic_threshold(x: NDArray[np.float64], y: NDArray[np.float64]) -> tuple[float, float]:
    """Ajusta ``y = sigmoid(k (x - x_c))`` y devuelve ``(x_c, k)``."""

    def model(xv: NDArray[np.float64], xc: float, k: float) -> NDArray[np.float64]:
        return expit(k * (xv - xc))

    p0 = (float(np.median(x)), 10.0)
    try:
        popt, _ = curve_fit(model, x, y, p0=p0, maxfev=20000)
        return float(popt[0]), float(abs(popt[1]))
    except (RuntimeError, ValueError):
        # Interpolación lineal como respaldo.
        idx = np.argsort(x)
        xs, ys = x[idx], y[idx]
        xc = float(np.interp(0.5, ys, xs))
        return xc, 0.0


def summarize(result: SimulationResult, cell_size: float) -> dict[str, float]:
    """Resumen numérico de una simulación."""
    from .metrics import rate_of_spread, shape_metrics  # local para evitar ciclos

    ros_fit, r2_fit = rate_of_spread(result.times, result.head_distance)
    ros_arrival, r2_arrival = head_ros_from_arrival(result.arrival, cell_size)
    # El ajuste sobre el mapa de llegada es preciso en frentes homogéneos,
    # pero puede ser engañoso en terrenos muy heterogéneos (pocas celdas
    # sobre el eje y llegadas tempranas aisladas). Se exige un R^2 alto.
    if ros_arrival > 0.0 and r2_arrival >= 0.80 and ros_arrival <= 3.0:
        ros, r2 = ros_arrival, r2_arrival
    else:
        ros, r2 = ros_fit, r2_fit
    ros = max(ros, 0.0)
    shape = shape_metrics(result.burned_mask, cell_size)
    return {
        "burned_cells": float(np.count_nonzero(result.burned_mask)),
        "burned_area_m2": shape.area_m2,
        "burned_fraction": result.final_burned_fraction,
        "ros_m_s": ros,
        "ros_m_min": ros * 60.0,
        "ros_r2": r2,
        "ros_fit_m_s": ros_fit,
        "ros_fit_r2": r2_fit,
        "perimeter_m": shape.perimeter_m,
        "length_breadth": shape.length_breadth,
        "eccentricity": shape.eccentricity,
        "circularity": shape.circularity,
        "fractal_dimension": shape.fractal_dimension,
        "roughness_s": arrival_roughness(result.arrival, result.burned_mask),
    }
