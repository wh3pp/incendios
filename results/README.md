# Resultados

Este directorio se regenera con:

```bash
uv run python scripts/run_all.py
```

## Contenido

- `tables/`: tablas CSV de la campaña experimental.
- `figures/`: figuras en PDF (vectoriales) y PNG (previsualización).
- `data/`: arreglos NPZ con estados, tiempos de llegada, ensembles y
  trayectorias.
- `summary.json`: resumen global de la campaña.
- `data/caso_*.npz`: DEM, máscaras y resultados de los casos Acos y Little Giant.
- `tables/casos_reales.csv`: métricas de los dos casos reales.

Las figuras usadas por el documento se copian automáticamente a
`doc/assets/figures/` al final de `run_all.py`.
