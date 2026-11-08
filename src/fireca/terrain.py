"""Generación de terrenos forestales heterogéneos.

El terreno se construye mediante síntesis espectral de ruido fractal
(fracional Brownian motion, fBm) para la elevación y la cobertura vegetal.
Sobre esa base se definen:

* el mapa de tipos de combustible (pasto, matorral, hojarasca, bosque),
* la humedad del combustible muerto,
* la densidad de vegetación,
* los gradientes de pendiente,
* las celdas incombustibles (lagos, roca expuesta, ríos).

La heterogeneidad espacial es un ingrediente central del modelo: los
autómatas celulares homogéneos producen frentes demasiado regulares y no
permiten estudiar efectos de percolación ni de conectividad del paisaje.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import numpy as np
from numpy.typing import NDArray
from scipy.ndimage import gaussian_filter

from .fuels import STANDARD_FUELS, FuelModel

# Umbrales de cobertura para asignar modelos de combustible.
COVER_THRESHOLDS: Final[tuple[float, float, float]] = (0.28, 0.55, 0.78)


@dataclass
class Terrain:
    """Representación rasterizada de un paisaje forestal.

    Attributes
    ----------
    elevation:
        Elevación [m], forma ``(H, W)``.
    fuel_type:
        Índice del modelo de combustible; ``-1`` indica celda incombustible.
    moisture:
        Humedad del combustible muerto [fracción].
    veg_density:
        Densidad relativa de vegetación en ``[0, 1]``.
    load_factor:
        Multiplicador espacial de la carga de combustible.
    cell_size:
        Tamaño de celda [m].
    wind_speed:
        Velocidad del viento [m/s].
    wind_direction:
        Dirección hacia la que sopla el viento [rad].
    grad_x, grad_y:
        Gradientes de elevación [m/m] en coordenadas físicas.
    """

    elevation: NDArray[np.float64]
    fuel_type: NDArray[np.int8]
    moisture: NDArray[np.float64]
    veg_density: NDArray[np.float64]
    load_factor: NDArray[np.float64]
    cell_size: float
    wind_speed: float
    wind_direction: float
    grad_x: NDArray[np.float64]
    grad_y: NDArray[np.float64]
    seed: int = 0

    @property
    def shape(self) -> tuple[int, int]:
        return self.elevation.shape

    @property
    def slope(self) -> NDArray[np.float64]:
        """Magnitud de la pendiente (tan phi)."""
        return np.hypot(self.grad_x, self.grad_y)

    @property
    def burnable(self) -> NDArray[np.bool_]:
        return self.fuel_type >= 0

    def fuel_models(self) -> dict[str, FuelModel]:
        return STANDARD_FUELS

    def summary(self) -> dict[str, float]:
        """Estadísticos descriptivos del terreno."""
        burnable = self.burnable
        return {
            "size": float(self.shape[0]),
            "cell_size_m": self.cell_size,
            "domain_m": float(self.shape[1] * self.cell_size),
            "elevation_min_m": float(np.min(self.elevation)),
            "elevation_max_m": float(np.max(self.elevation)),
            "elevation_mean_m": float(np.mean(self.elevation)),
            "slope_mean": float(np.mean(self.slope[burnable])) if burnable.any() else 0.0,
            "slope_max": float(np.max(self.slope[burnable])) if burnable.any() else 0.0,
            "burnable_fraction": float(np.mean(burnable)),
            "moisture_mean": float(np.mean(self.moisture[burnable])) if burnable.any() else 0.0,
            "moisture_min": float(np.min(self.moisture[burnable])) if burnable.any() else 0.0,
            "moisture_max": float(np.max(self.moisture[burnable])) if burnable.any() else 0.0,
            "veg_density_mean": float(np.mean(self.veg_density)),
            "wind_speed_m_s": float(self.wind_speed),
            "wind_direction_deg": float(np.degrees(self.wind_direction) % 360.0),
        }


def spectral_fbm(
    shape: tuple[int, int],
    rng: np.random.Generator,
    beta: float = 2.8,
    f_min: float = 0.0,
) -> NDArray[np.float64]:
    """Ruido fractal gaussiano periódico mediante síntesis espectral.

    Se genera un campo cuya densidad espectral de potencia sigue
    ``S(k) ~ |k|^{-beta}``. Para ``beta = 2.8`` se obtiene un paisaje con
    estructura multiescala realista. El campo resultante se normaliza a
    media cero y desviación estándar uno.
    """
    h, w = shape
    ky = np.fft.fftfreq(h)[:, None]
    kx = np.fft.fftfreq(w)[None, :]
    k = np.hypot(kx, ky)
    k[0, 0] = 1.0
    amplitude = k ** (-beta / 2.0)
    amplitude[0, 0] = 0.0
    if f_min > 0.0:
        amplitude[k < f_min] = 0.0
    noise = rng.normal(size=(h, w)) + 1j * rng.normal(size=(h, w))
    field = np.fft.ifft2(amplitude * noise).real
    field -= field.mean()
    std = field.std()
    if std > 0.0:
        field /= std
    return field


def _normalize(field: NDArray[np.float64]) -> NDArray[np.float64]:
    lo, hi = float(np.min(field)), float(np.max(field))
    if hi - lo < 1e-12:
        return np.zeros_like(field)
    return (field - lo) / (hi - lo)


def generate_terrain(
    size: int = 256,
    cell_size: float = 5.0,
    seed: int = 42,
    vegetation: float = 0.70,
    moisture: float = 0.08,
    wind_speed: float = 6.0,
    wind_direction: float = 0.0,
    relief: float = 80.0,
    base_slope: float = 0.0,
    beta: float = 2.8,
    river: bool = False,
    lake: bool = True,
    moisture_gradient: float = 0.06,
    moisture_noise: float = 0.015,
) -> Terrain:
    """Genera un terreno forestal sintético y heterogéneo.

    Parameters
    ----------
    size:
        Número de filas y columnas de la malla cuadrada.
    cell_size:
        Tamaño de celda [m].
    vegetation:
        Cobertura vegetal media en ``[0, 1]``.
    moisture:
        Humedad media del combustible muerto.
    wind_speed:
        Velocidad del viento [m/s].
    wind_direction:
        Dirección hacia la que sopla el viento [rad].
    relief:
        Amplitud vertical del relieve [m].
    base_slope:
        Pendiente media impuesta en la dirección +x (m/m).
    river:
        Si es ``True``, añade un río sinusoidal incombustible.
    lake:
        Si es ``True``, las zonas más bajas se consideran lago.
    """
    if size < 16:
        raise ValueError("size debe ser >= 16")
    if cell_size <= 0:
        raise ValueError("cell_size debe ser positivo")
    if not 0.0 <= vegetation <= 1.0:
        raise ValueError("vegetation debe estar en [0, 1]")

    rng = np.random.default_rng(seed)
    shape = (size, size)

    elev_field = spectral_fbm(shape, rng, beta=beta)
    elev_field = _normalize(elev_field)
    # Suavizado leve para que los gradientes sean físicamente interpretables.
    elev_field = gaussian_filter(elev_field, sigma=1.5, mode="wrap")
    elev_field = _normalize(elev_field)
    yy, xx = np.mgrid[0:size, 0:size]
    elevation = relief * (0.15 + 0.70 * elev_field) + base_slope * xx * cell_size

    cover_field = _normalize(spectral_fbm(shape, rng, beta=2.3))
    cover_field = gaussian_filter(cover_field, sigma=2.0, mode="wrap")
    cover_field = _normalize(cover_field)

    # Densidad de vegetación: cobertura media + estructura espacial.
    veg = vegetation * (0.55 + 0.75 * cover_field) + 0.10 * (1.0 - elev_field)
    veg = np.clip(veg, 0.0, 1.0)

    fuel_type = np.full(shape, -1, dtype=np.int8)
    active = cover_field > 0.18
    fuel_type[active & (cover_field < COVER_THRESHOLDS[0])] = 0  # FM1
    fuel_type[
        active & (cover_field >= COVER_THRESHOLDS[0]) & (cover_field < COVER_THRESHOLDS[1])
    ] = 1
    fuel_type[
        active & (cover_field >= COVER_THRESHOLDS[1]) & (cover_field < COVER_THRESHOLDS[2])
    ] = 2
    fuel_type[active & (cover_field >= COVER_THRESHOLDS[2])] = 3

    # Lagos en las zonas topográficamente más bajas.
    if lake:
        threshold = np.quantile(elevation, 0.035)
        fuel_type[elevation <= threshold] = -1

    # Río sinusoidal de 2 celdas de ancho.
    if river:
        center = size / 2.0 + 0.12 * size * np.sin(2.0 * np.pi * yy[:, 0] / (0.45 * size))
        river_mask = np.abs(xx - center[:, None]) < 1.5
        fuel_type[river_mask] = -1

    # Roca expuesta en pendientes extremas.
    grad_row, grad_col = np.gradient(elevation, cell_size)
    grad_x = grad_col
    grad_y = -grad_row
    slope = np.hypot(grad_x, grad_y)
    fuel_type[slope > 1.35] = -1

    # La humedad disminuye con la elevación y aumenta en zonas sombreadas
    # (baja densidad de vegetación, dosel cerrado).
    moisture_field = (
        moisture
        + moisture_gradient * (1.0 - cover_field)
        + moisture_noise * rng.normal(size=shape)
        - 1.5e-4 * (elevation - elevation.mean())
    )
    # Cada celda no puede superar el 95 % de su humedad de extinción.
    mx = np.zeros(shape)
    for idx, model in enumerate(STANDARD_FUELS.values()):
        mx[fuel_type == idx] = model.mx
    moisture_field = np.where(mx > 0.0, np.minimum(moisture_field, 0.95 * mx), moisture_field)
    moisture_field = np.clip(moisture_field, 0.02, 0.60)

    load_factor = np.clip(0.55 + 0.90 * veg, 0.35, 1.45)
    load_factor[fuel_type < 0] = 0.0

    return Terrain(
        elevation=elevation,
        fuel_type=fuel_type,
        moisture=moisture_field,
        veg_density=veg,
        load_factor=load_factor,
        cell_size=cell_size,
        wind_speed=float(wind_speed),
        wind_direction=float(wind_direction),
        grad_x=grad_x,
        grad_y=grad_y,
        seed=seed,
    )


def binary_forest(
    size: int,
    occupancy: float,
    cell_size: float = 1.0,
    seed: int = 0,
    fuel_code: str = "FM1",
    moisture: float = 0.07,
) -> Terrain:
    """Bosque binario para experimentos de percolación.

    Cada celda es combustible con probabilidad ``occupancy`` e incombustible
    en caso contrario. No hay pendiente ni viento; el objetivo es aislar el
    efecto de la conectividad del paisaje.
    """
    if not 0.0 <= occupancy <= 1.0:
        raise ValueError("occupancy debe estar en [0, 1]")
    rng = np.random.default_rng(seed)
    shape = (size, size)
    present = rng.random(shape) < occupancy
    code_to_idx = {code: i for i, code in enumerate(STANDARD_FUELS)}
    if fuel_code not in code_to_idx:
        raise ValueError(f"fuel_code desconocido: {fuel_code}")
    fuel_type = np.full(shape, -1, dtype=np.int8)
    fuel_type[present] = code_to_idx[fuel_code]
    model = STANDARD_FUELS[fuel_code]
    moisture_field = np.full(shape, min(moisture, 0.95 * model.mx))
    return Terrain(
        elevation=np.zeros(shape),
        fuel_type=fuel_type,
        moisture=moisture_field,
        veg_density=present.astype(float),
        load_factor=present.astype(float),
        cell_size=cell_size,
        wind_speed=0.0,
        wind_direction=0.0,
        grad_x=np.zeros(shape),
        grad_y=np.zeros(shape),
        seed=seed,
    )


def ignition_mask(
    shape: tuple[int, int],
    mode: str = "center",
    radius: int = 1,
) -> NDArray[np.bool_]:
    """Máscara booleana con la(s) celda(s) de ignición.

    Modos disponibles: ``"center"``, ``"left"``, ``"line_left"``,
    ``"corner"``.
    """
    h, w = shape
    mask = np.zeros(shape, dtype=bool)
    if mode == "center":
        r0, c0 = h // 2, w // 2
        mask[
            max(0, r0 - radius) : min(h, r0 + radius + 1),
            max(0, c0 - radius) : min(w, c0 + radius + 1),
        ] = True
    elif mode == "left":
        r0 = h // 2
        mask[max(0, r0 - radius) : min(h, r0 + radius + 1), 0 : radius + 1] = True
    elif mode == "line_left":
        mask[:, 0 : radius + 1] = True
    elif mode == "corner":
        mask[0 : radius + 1, 0 : radius + 1] = True
    else:
        raise ValueError(f"modo de ignición desconocido: {mode}")
    return mask
