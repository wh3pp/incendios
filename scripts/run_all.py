"""Ejecuta la campaña experimental completa y regenera las figuras.

Uso:
    uv run python scripts/run_all.py
    uv run python scripts/run_all.py --only numericos,base
"""

from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path

import pandas as pd

from fireca import experiments as ex
from fireca import plotting as pl

ROOT = Path(__file__).resolve().parents[1]


def timed(name: str, fn, *args, **kwargs):
    t0 = time.perf_counter()
    result = fn(*args, **kwargs)
    dt = time.perf_counter() - t0
    print(f"[{name}] {dt:.1f} s")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only",
        default="numericos,base,ensemble,barridos,percolacion,convergencia,sensibilidad,casos,figuras",
        help="Lista separada por comas de etapas a ejecutar.",
    )
    args = parser.parse_args()
    only = {s.strip() for s in args.only.split(",") if s.strip()}
    ex.ensure_dirs()
    summary: dict[str, object] = {}

    if "numericos" in only:
        tables = timed("numericos", ex.numerics_experiments)
        ex.save_all_tables(tables)
        summary["langevin"] = tables["langevin"].to_dict(orient="records")[0]

    if "base" in only:
        terrain, result, base_summary = timed("base", ex.baseline_experiment)
        pd.DataFrame([base_summary]).to_csv(
            ex.TABLES / "escenario_base.csv", index=False, float_format="%.8g"
        )
        summary["escenario_base"] = base_summary
        pl.plot_terrain()
        pl.plot_baseline()

    if "ensemble" in only:
        terrain, members, _ = timed("ensemble", ex.ensemble_experiment)
        det_model = ex.DeterministicCA(terrain, dt=1.0)
        comparison = ex.comparison_table(
            det_model.run(600.0, record_every=10.0),
            members,
            5.0,
        )
        comparison.to_csv(ex.TABLES / "comparacion.csv", index=False, float_format="%.8g")
        summary["comparacion"] = comparison.to_dict(orient="records")
        enhancement = timed("mejora_estocastica", ex.stochastic_enhancement)
        enhancement.to_csv(ex.TABLES / "mejora_estocastica.csv", index=False, float_format="%.8g")
        summary["mejora_estocastica"] = enhancement.to_dict(orient="records")
        pl.plot_det_vs_stoch()

    if "barridos" in only:
        wind = timed("viento", ex.wind_sweep)
        wind.to_csv(ex.TABLES / "viento.csv", index=False, float_format="%.8g")
        moisture = timed("humedad", ex.moisture_sweep)
        moisture.to_csv(ex.TABLES / "humedad.csv", index=False, float_format="%.8g")
        slope = timed("pendiente", ex.slope_sweep)
        slope.to_csv(ex.TABLES / "pendiente.csv", index=False, float_format="%.8g")
        summary["viento"] = wind.to_dict(orient="records")
        summary["humedad"] = moisture.to_dict(orient="records")
        summary["pendiente"] = slope.to_dict(orient="records")
        pl.plot_wind_sweep()
        pl.plot_moisture()
        pl.plot_slope()

    if "percolacion" in only:
        perc, thresholds = timed("percolacion", ex.percolation_experiment)
        perc.to_csv(ex.TABLES / "percolacion.csv", index=False, float_format="%.8g")
        summary["percolacion_umbrales"] = thresholds
        pl.plot_percolation()

    if "convergencia" in only:
        spatial = timed("convergencia_espacial", ex.grid_convergence)
        spatial.to_csv(ex.TABLES / "convergencia_espacial.csv", index=False, float_format="%.8g")
        temporal = timed("convergencia_temporal", ex.timestep_convergence)
        temporal.to_csv(ex.TABLES / "convergencia_temporal.csv", index=False, float_format="%.8g")
        summary["convergencia_espacial"] = spatial.to_dict(orient="records")
        summary["convergencia_temporal"] = temporal.to_dict(orient="records")
        pl.plot_grid_convergence()

    if "sensibilidad" in only:
        data, sens = timed("sensibilidad", ex.sensitivity_experiment)
        data.to_csv(ex.TABLES / "sensibilidad_datos.csv", index=False, float_format="%.8g")
        sens.to_csv(ex.TABLES / "sensibilidad.csv", index=False, float_format="%.8g")
        summary["sensibilidad"] = sens.to_dict(orient="records")
        pl.plot_sensitivity()

    if "casos" in only:
        required = Path("data/real_cases")
        if not (required / "acos_dem.npy").exists():
            print(
                "Casos reales omitidos: ejecute "
                "`uv run python scripts/fetch_real_cases.py`."
            )
        else:
            cases = timed("casos_reales", ex.real_cases_experiment)
            cases.to_csv(
                ex.TABLES / "casos_reales.csv", index=False, float_format="%.8g"
            )
            summary["casos_reales"] = json.loads(cases.to_json(orient="records"))
            pl.plot_real_cases()

    if "figuras" in only:
        timed("figuras_numericas", pl.plot_numerics)
        timed("figuras_ca", pl.plot_ca)
        timed("figuras_pavesas", pl.plot_firebrand)

    # Copia de figuras vectoriales al directorio que consume Typst.
    destination = ROOT / "doc" / "assets" / "figures"
    destination.mkdir(parents=True, exist_ok=True)
    for figure in ex.FIGURES.glob("*.pdf"):
        shutil.copy2(figure, destination / figure.name)

    ex.save_summary(summary)
    print("Listo. Resultados en", ROOT / "results")


if __name__ == "__main__":
    main()
