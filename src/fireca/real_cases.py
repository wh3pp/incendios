"""Casos de estudio reales: Acos (Cusco, 2025) y Little Giant (WA, 2026).

El módulo construye un ``Terrain`` a partir de un DEM real descargado de
Terrarium/Mapzen, asigna modelos de combustible mediante reglas altitudinales
y de pendiente, y define máscaras observadas para la validación.

Limitaciones explícitas:

* Para Acos no existe un perímetro oficial; se usa el área oficial de INDECI
  (300 ha) y una elipse equivalente solo para comparar el área y la escala.
* Para Little Giant se dispone del perímetro oficial WFIGS; se rasteriza sobre
  la subventana de simulación.
* El combustible no proviene de un inventario local: se asigna con reglas
  altitudinales. Es una aproximación documentada, no un mapa LANDFIRE o
  MapBiomas.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
from matplotlib.path import Path as MplPath
from numpy.typing import NDArray

from .ca import DeterministicCA, SimulationResult, run_ensemble
from .fuels import STANDARD_FUELS
from .metrics import summarize
from .terrain import Terrain

DATA = Path("data")
REAL = DATA / "real_cases"


@dataclass(frozen=True)
class CaseDefinition:
    """Metadatos y configuración de un incendio real."""

    key: str
    name: str
    country: str
    latitude: float
    longitude: float
    bbox: tuple[float, float, float, float]
    start: datetime
    observed_area_ha: float
    fuel_profile: str
    wind_speed: float
    wind_direction_deg: float
    moisture: float
    source: str
    perimeter_file: str | None = None
    residence_scale: float = 3.0
    notes: str = ""

    @property
    def bbox_width_m(self) -> float:
        lon_min, lat_min, lon_max, lat_max = self.bbox
        return (lon_max - lon_min) * 111_320.0 * np.cos(np.radians(self.latitude))

    @property
    def bbox_height_m(self) -> float:
        lat_min, lat_max = self.bbox[1], self.bbox[3]
        return (lat_max - lat_min) * 110_540.0

    @property
    def cell_size_m(self) -> float:
        return 0.5 * (self.bbox_width_m + self.bbox_height_m)


ACOS = CaseDefinition(
    key="acos",
    name="Incendio forestal de Acos (Mayuhuilca)",
    country="Perú",
    latitude=-13.95128,
    longitude=-71.73823,
    bbox=(-71.758, -13.969, -71.718, -13.933),
    start=datetime(2025, 9, 11, 12, 24),
    observed_area_ha=300.0,
    fuel_profile="andes",
    wind_speed=3.0,
    wind_direction_deg=0.0,
    moisture=0.11,
    source="INDECI, Reporte Complementario N.º 9686 (15/09/2025)",
    notes=(
        "Sector Mayuhuilca, distrito de Acos, provincia de Acomayo, Cusco. "
        "Área oficial destruida: 300 ha. Sin perímetro oficial."
    ),
)

LITTLE_GIANT = CaseDefinition(
    key="little_giant",
    name="Little Giant Fire",
    country="Estados Unidos",
    latitude=47.982755,
    longitude=-120.834068,
    bbox=(-120.864, 47.963, -120.804, 48.003),
    start=datetime(2026, 7, 15, 0, 0),
    observed_area_ha=172_912 * 0.40468564224,
    fuel_profile="cascades",
    wind_speed=8.0,
    wind_direction_deg=90.0,
    moisture=0.08,
    residence_scale=1.5,
    source="WFIGS/NIFC, perímetro oficial 2026",
    perimeter_file="data/real_cases/little_giant.geojson",
    notes=(
        "Condado de Chelan, Washington. 172 912 acres (~69 970 ha). "
        "Se simula una subventana de 4 km alrededor de la ignición; el evento "
        "completo excede la escala del modelo."
    ),
)

CASES = {ACOS.key: ACOS, LITTLE_GIANT.key: LITTLE_GIANT}


def _fuel_map(elevation: NDArray[np.float64], profile: str) -> NDArray[np.int8]:
    code_to_idx = {code: i for i, code in enumerate(STANDARD_FUELS)}
    fuel = np.full(elevation.shape, code_to_idx["FM10"], dtype=np.int8)
    if profile == "andes":
        fuel[elevation < 3300.0] = code_to_idx["FM1"]
        fuel[(elevation >= 3300.0) & (elevation < 3550.0)] = code_to_idx["FM4"]
        fuel[elevation >= 3550.0] = code_to_idx["FM8"]
    elif profile == "cascades":
        fuel[elevation < 900.0] = code_to_idx["FM1"]
        fuel[(elevation >= 900.0) & (elevation < 1300.0)] = code_to_idx["FM4"]
        fuel[(elevation >= 1300.0) & (elevation < 1700.0)] = code_to_idx["FM8"]
        fuel[elevation >= 1700.0] = code_to_idx["FM10"]
    else:
        raise ValueError(f"perfil de combustible desconocido: {profile}")
    return fuel


def build_case_terrain(
    case: CaseDefinition,
    size: int = 128,
    dem_path: str | Path | None = None,
) -> Terrain:
    """Construye un ``Terrain`` a partir del DEM real y reglas de combustible."""
    if dem_path is None:
        dem_path = REAL / f"{case.key}_dem.npy"
    dem = np.load(dem_path)
    if dem.shape != (size, size):
        from PIL import Image

        dem = np.asarray(
            Image.fromarray(dem.astype(np.float32)).resize((size, size), resample=Image.BILINEAR),
            dtype=np.float64,
        )
    cell_size = 0.5 * (case.bbox_width_m + case.bbox_height_m) / size
    grad_row, grad_col = np.gradient(dem, cell_size)
    grad_x = grad_col
    grad_y = -grad_row
    slope = np.hypot(grad_x, grad_y)

    fuel_type = _fuel_map(dem, case.fuel_profile)
    fuel_type[slope > 1.35] = -1

    moisture = case.moisture + 0.01 * np.random.default_rng(0).normal(size=dem.shape)
    moisture = np.clip(moisture, 0.02, 0.30)
    # Clip por modelo de combustible.
    for idx, model in enumerate(STANDARD_FUELS.values()):
        mask = fuel_type == idx
        moisture[mask] = np.minimum(moisture[mask], 0.95 * model.mx)

    return Terrain(
        elevation=dem,
        fuel_type=fuel_type,
        moisture=moisture,
        veg_density=np.clip(
            0.5 + 0.5 * (dem - dem.min()) / (dem.max() - dem.min() + 1e-9), 0.2, 1.0
        ),
        load_factor=np.ones_like(dem),
        cell_size=cell_size,
        wind_speed=case.wind_speed,
        wind_direction=np.radians(case.wind_direction_deg),
        grad_x=grad_x,
        grad_y=grad_y,
        seed=0,
    )


def ignition_cell(case: CaseDefinition, shape: tuple[int, int]) -> NDArray[np.bool_]:
    """Máscara de ignición de 3x3 celdas en la coordenada del evento."""
    lon_min, lat_min, lon_max, lat_max = case.bbox
    h, w = shape
    col = int(round((case.longitude - lon_min) / (lon_max - lon_min) * (w - 1)))
    row = int(round((lat_max - case.latitude) / (lat_max - lat_min) * (h - 1)))
    mask = np.zeros(shape, dtype=bool)
    mask[max(0, row - 1) : min(h, row + 2), max(0, col - 1) : min(w, col + 2)] = True
    return mask


def _polygon_mask(
    geometry: dict, bbox: tuple[float, float, float, float], shape: tuple[int, int]
) -> NDArray[np.bool_]:
    """Rasteriza un GeoJSON Polygon/MultiPolygon sobre centros de celda."""
    lon_min, lat_min, lon_max, lat_max = bbox
    h, w = shape
    xs = np.linspace(lon_min, lon_max, w)
    ys = np.linspace(lat_max, lat_min, h)
    xx, yy = np.meshgrid(xs, ys)
    points = np.column_stack([xx.ravel(), yy.ravel()])
    inside = np.zeros(points.shape[0], dtype=bool)
    polygons = (
        [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
    )
    for polygon in polygons:
        if not polygon:
            continue
        ring = np.asarray(polygon[0], dtype=float)
        path = MplPath(ring)
        inside |= path.contains_points(points)
    return inside.reshape(h, w)


def observed_mask(case: CaseDefinition, shape: tuple[int, int]) -> NDArray[np.bool_]:
    """Máscara observada.

    Para Little Giant se rasteriza el perímetro WFIGS. Para Acos, al no existir
    perímetro, se construye una elipse de área igual al área oficial.
    """
    if case.perimeter_file:
        path = Path(case.perimeter_file)
        data = json.loads(path.read_text(encoding="utf-8"))
        geometry = data["features"][0]["geometry"]
        return _polygon_mask(geometry, case.bbox, shape)

    # Elipse equivalente para Acos.
    h, w = shape
    area_m2 = case.observed_area_ha * 10_000.0
    ratio = 1.8
    a = np.sqrt(area_m2 * ratio / np.pi)
    b = np.sqrt(area_m2 / (np.pi * ratio))
    lon_min, lat_min, lon_max, lat_max = case.bbox
    xs = np.linspace(lon_min, lon_max, w)
    ys = np.linspace(lat_max, lat_min, h)
    xx, yy = np.meshgrid(xs, ys)
    xm = (xx - case.longitude) * 111_320.0 * np.cos(np.radians(case.latitude))
    ym = (yy - case.latitude) * 110_540.0
    # Elipse alineada con el viento (eje x).
    mask = (xm / a) ** 2 + (ym / b) ** 2 <= 1.0
    return mask


def run_case(
    case: CaseDefinition,
    size: int = 128,
    dt: float = 30.0,
    t_end: float | None = None,
    stochastic_members: int = 0,
) -> tuple[Terrain, SimulationResult, NDArray[np.bool_], dict[str, float]]:
    """Simula un caso real y devuelve terreno, resultado y máscara observada."""
    terrain = build_case_terrain(case, size=size)
    ignition = ignition_cell(case, terrain.shape)
    if t_end is None:
        t_end = 4.0 * 24.0 * 3600.0
    model = DeterministicCA(
        terrain,
        ignition=ignition,
        dt=dt,
        max_rate=1.0,
        wind_efficiency=0.30,
        cooling_time=1e9,
    )
    # En celdas gruesas, el tiempo de residencia nominal (600 s) es menor que
    # el tiempo de cruce d/R. Se escala para que el frente pueda propagarse;
    # el factor se reporta como parámetro numérico del caso.
    model.residence = np.where(model.residence > 0, model.residence * case.residence_scale, 0.0)
    result = model.run(t_end, record_every=max(60.0, t_end / 40.0))
    observed = observed_mask(case, terrain.shape)
    metrics = summarize(result, terrain.cell_size)
    metrics.update(
        {
            "observed_area_ha": float(np.count_nonzero(observed) * terrain.cell_size**2 / 1e4),
            "observed_area_official_ha": case.observed_area_ha,
            "simulated_area_ha": metrics["burned_area_m2"] / 1e4,
            "area_error_rel": abs(
                metrics["burned_area_m2"] / 1e4
                - float(np.count_nonzero(observed) * terrain.cell_size**2 / 1e4)
            )
            / max(float(np.count_nonzero(observed) * terrain.cell_size**2 / 1e4), 1.0),
            "iou": float("nan")
            if case.key == "acos"
            else float(
                np.count_nonzero(result.burned_mask & observed)
                / max(np.count_nonzero(result.burned_mask | observed), 1)
            ),
            "cell_size_m": terrain.cell_size,
            "dt_s": dt,
            "t_end_s": t_end,
        }
    )
    if stochastic_members:
        # El ensemble se deja preparado para análisis de incertidumbre.
        _ = run_ensemble(
            terrain,
            n_members=stochastic_members,
            t_end=t_end,
            dt=dt,
            seed=123,
            ignition=ignition,
        )
    return terrain, result, observed, metrics


def case_table() -> list[dict[str, str | float]]:
    """Tabla resumen de los dos casos."""
    rows = []
    for case in (ACOS, LITTLE_GIANT):
        rows.append(
            {
                "caso": case.name,
                "pais": case.country,
                "inicio": case.start.strftime("%Y-%m-%d %H:%M"),
                "area_ha": case.observed_area_ha,
                "fuel": case.fuel_profile,
                "viento_m_s": case.wind_speed,
                "humedad": case.moisture,
                "fuente": case.source,
            }
        )
    return rows
