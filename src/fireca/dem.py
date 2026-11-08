"""Descarga y recorte de modelos digitales de elevación (DEM).

Se usa el servicio público Terrarium de Mapzen/AWS, que sirve teselas PNG
codificadas con elevación en los canales RGB. No requiere clave de API. Las
teselas se cachean localmente para que las simulaciones sean reproducibles sin
conexión.

Codificación Terrarium:
    elevación [m] = R * 256 + G + B / 256 - 32768
"""

from __future__ import annotations

import math
import urllib.request
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from PIL import Image

TILE_URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
USER_AGENT = "fireca-TIF/1.0 (academic use)"


def deg2num(lat: float, lon: float, zoom: int) -> tuple[float, float]:
    """Coordenadas fraccionarias de tesela Web Mercator."""
    n = 2.0**zoom
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
    return x, y


def _download_tile(zoom: int, x: int, y: int, cache_dir: Path) -> NDArray[np.float64]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{zoom}_{x}_{y}.png"
    if not path.exists():
        request = urllib.request.Request(
            TILE_URL.format(z=zoom, x=x, y=y), headers={"User-Agent": USER_AGENT}
        )
        with urllib.request.urlopen(request, timeout=45) as response:
            path.write_bytes(response.read())
    rgb = np.asarray(Image.open(path).convert("RGB"), dtype=np.float64)
    return rgb[:, :, 0] * 256.0 + rgb[:, :, 1] + rgb[:, :, 2] / 256.0 - 32768.0


def fetch_dem(
    bbox: tuple[float, float, float, float],
    size: int = 128,
    zoom: int = 14,
    cache_dir: str | Path = "data/dem_cache",
) -> NDArray[np.float64]:
    """Descarga un DEM para ``bbox = (lon_min, lat_min, lon_max, lat_max)``.

    Devuelve un arreglo cuadrado de ``size x size`` en metros sobre el nivel
    del mar, remuestreado bilinealmente.
    """
    lon_min, lat_min, lon_max, lat_max = bbox
    if not (lon_min < lon_max and lat_min < lat_max):
        raise ValueError("bbox inválido")
    cache = Path(cache_dir)
    x0f, y0f = deg2num(lat_max, lon_min, zoom)
    x1f, y1f = deg2num(lat_min, lon_max, zoom)
    x0, y0 = int(math.floor(x0f)), int(math.floor(y0f))
    x1, y1 = int(math.floor(x1f)), int(math.floor(y1f))
    tiles = []
    for y in range(y0, y1 + 1):
        row = []
        for x in range(x0, x1 + 1):
            row.append(_download_tile(zoom, x, y, cache))
        tiles.append(np.concatenate(row, axis=1))
    mosaic = np.concatenate(tiles, axis=0)

    # Coordenadas de píxel dentro del mosaico.
    px0 = (x0f - x0) * 256.0
    px1 = (x1f - x0) * 256.0
    py0 = (y0f - y0) * 256.0
    py1 = (y1f - y0) * 256.0
    cropped = mosaic[
        int(math.floor(py0)) : int(math.ceil(py1)),
        int(math.floor(px0)) : int(math.ceil(px1)),
    ]
    image = Image.fromarray(cropped.astype(np.float32), mode="F").resize(
        (size, size), resample=Image.BILINEAR
    )
    return np.asarray(image, dtype=np.float64)


def load_or_fetch(
    path: str | Path,
    bbox: tuple[float, float, float, float],
    size: int = 128,
    zoom: int = 14,
) -> NDArray[np.float64]:
    """Carga un DEM cacheado o lo descarga si no existe."""
    path = Path(path)
    if path.exists():
        return np.load(path)
    dem = fetch_dem(bbox, size=size, zoom=zoom)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, dem)
    return dem
