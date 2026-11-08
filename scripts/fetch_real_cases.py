"""Descarga los insumos de los casos reales (DEM y perímetro WFIGS).

Uso:
    uv run python scripts/fetch_real_cases.py

Genera:
    data/real_cases/acos_dem.npy
    data/real_cases/little_giant_dem.npy
    data/real_cases/little_giant.geojson
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

import numpy as np

from fireca.dem import fetch_dem
from fireca.real_cases import ACOS, LITTLE_GIANT, REAL

WFIGS = (
    "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/"
    "WFIGS_Interagency_Perimeters_YearToDate/FeatureServer/0/query"
)


def fetch_little_giant() -> None:
    params = {
        "where": "poly_IncidentName='Little Giant'",
        "outFields": "poly_IncidentName,poly_GISAcres,poly_PolygonDateTime",
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "geojson",
    }
    url = WFIGS + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "fireca-TIF/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    path = REAL / "little_giant.geojson"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    data = json.loads(payload)
    print(f"WFIGS: {len(data.get('features', []))} feature(s) -> {path}")


def main() -> None:
    REAL.mkdir(parents=True, exist_ok=True)
    for case in (ACOS, LITTLE_GIANT):
        path = REAL / f"{case.key}_dem.npy"
        if path.exists():
            print("DEM ya existe:", path)
            continue
        dem = fetch_dem(case.bbox, size=128, zoom=14)
        np.save(path, dem)
        print("DEM guardado:", path, dem.shape, float(dem.min()), float(dem.max()))
    perimeter = REAL / "little_giant.geojson"
    if perimeter.exists():
        print("Perímetro ya existe:", perimeter)
    else:
        fetch_little_giant()


if __name__ == "__main__":
    main()
