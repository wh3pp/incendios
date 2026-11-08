# fireca — Propagación de incendios forestales con autómatas celulares

Paquete de simulación, análisis numérico y reproducibilidad del Trabajo de
Investigación Formativa (TIF) del curso de Física Computacional, Escuela
Profesional de Ciencia de la Computación, Universidad Nacional de San Agustín
de Arequipa.

## Requisitos

- [uv](https://docs.astral.sh/uv/) (gestión de entorno y dependencias)
- Python >= 3.11 (gestionado por uv)

## Instalación

```bash
uv sync
```

## Pruebas

```bash
uv run pytest
```

## Reproducir todos los resultados del documento

```bash
uv run python scripts/run_all.py
uv run python scripts/check_dois.py
uv run python scripts/check_open_access.py
```

Los resultados se escriben en `results/`:

- `results/tables/*.csv` — tablas numéricas.
- `results/figures/*.pdf` — figuras vectoriales usadas por Typst.
- `results/summary.json` — métricas globales de la campaña.

## Uso de la CLI

```bash
uv run fireca run --size 256 --wind 6 --moisture 0.08 --seed 42 --out results/demo
uv run fireca sweep --variable wind --size 128 --members 20
```

Los casos reales se regeneran con:

```bash
uv run python scripts/fetch_real_cases.py
uv run python scripts/run_all.py --only casos
```

Requieren los DEM cacheados en `data/real_cases/` y el perímetro WFIGS en
`data/real_cases/little_giant.geojson`.

## Estructura

```
src/fireca/
  fuels.py        Modelos de combustible y ecuación de Rothermel
  terrain.py      Generación de terreno, vegetación, humedad y viento
  dem.py          Descarga/cacheo de DEM real (Terrarium/Mapzen)
  real_cases.py   Casos Acos 2025 y Little Giant 2026
  ca.py           Autómatas celulares determinista, estocástico y MTT
  metrics.py      Área quemada, ROS, forma, dimensión fractal
  numerics.py     Experimentos de las sesiones 1–6 del curso
  experiments.py  Campañas paramétricas y Monte Carlo
  plotting.py     Figuras del documento
  cli.py          Interfaz de línea de comandos
```

## Documento

```bash
typst compile doc/main.typ doc/main.pdf
```

El PDF compilado se encuentra en `doc/main.pdf`.
