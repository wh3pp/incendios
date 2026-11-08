"""Interfaz de línea de comandos de ``fireca``.

Ejemplos:
    uv run fireca run --size 256 --wind 6 --moisture 0.08 --seed 42
    uv run fireca sweep --variable wind --size 128 --members 8
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from . import __version__
from .ca import DeterministicCA, StochasticCA
from .experiments import homogeneous_terrain
from .metrics import summarize
from .terrain import generate_terrain


def _cmd_run(args: argparse.Namespace) -> int:
    if args.homogeneous:
        terrain = homogeneous_terrain(
            size=args.size,
            fuel_code=args.fuel,
            moisture=args.moisture,
            wind_speed=args.wind,
            cell_size=args.cell_size,
        )
    else:
        terrain = generate_terrain(
            size=args.size,
            cell_size=args.cell_size,
            seed=args.seed,
            moisture=args.moisture,
            wind_speed=args.wind,
        )
    model = DeterministicCA(terrain, dt=args.dt)
    result = model.run(args.t_end, record_every=args.record_every)
    summary = summarize(result, terrain.cell_size)
    summary.update(
        {
            "seed": args.seed,
            "wind_m_s": args.wind,
            "moisture": args.moisture,
            "fuel": args.fuel,
            "homogeneous": args.homogeneous,
            "t_end_s": args.t_end,
        }
    )
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out / "result.npz",
        times=result.times,
        burned_area=result.burned_area,
        head_distance=result.head_distance,
        arrival=result.arrival,
        state=result.state,
    )
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


def _cmd_sweep(args: argparse.Namespace) -> int:
    values = np.linspace(args.min, args.max, args.points)
    rows = []
    for value in values:
        terrain = homogeneous_terrain(
            size=args.size,
            fuel_code=args.fuel,
            moisture=args.moisture if args.variable != "moisture" else float(value),
            wind_speed=args.wind if args.variable != "wind" else float(value),
            cell_size=args.cell_size,
        )
        if args.members <= 1:
            result = DeterministicCA(terrain, dt=args.dt).run(args.t_end, record_every=args.t_end)
            summary = summarize(result, terrain.cell_size)
            area = summary["burned_area_m2"]
            ros = summary["ros_m_min"]
            rows.append(
                {
                    args.variable: float(value),
                    "area_ha": area / 1e4,
                    "ros_m_min": ros,
                }
            )
        else:
            areas = []
            for k in range(args.members):
                result = StochasticCA(terrain, dt=args.dt, seed=args.seed + k).run(
                    args.t_end, record_every=args.t_end
                )
                areas.append(result.final_burned_area)
            rows.append(
                {
                    args.variable: float(value),
                    "area_ha": float(np.mean(areas)) * terrain.cell_size**2 / 1e4,
                    "area_std_ha": float(np.std(areas, ddof=1)) * terrain.cell_size**2 / 1e4,
                }
            )
        print(rows[-1])
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    import pandas as pd

    pd.DataFrame(rows).to_csv(out, index=False, float_format="%.8g")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fireca", description=__doc__)
    parser.add_argument("--version", action="version", version=f"fireca {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Ejecuta una simulación puntual.")
    run.add_argument("--size", type=int, default=256)
    run.add_argument("--cell-size", type=float, default=5.0)
    run.add_argument("--wind", type=float, default=4.0)
    run.add_argument("--moisture", type=float, default=0.07)
    run.add_argument("--fuel", default="FM10")
    run.add_argument("--seed", type=int, default=42)
    run.add_argument("--t-end", type=float, default=600.0)
    run.add_argument("--dt", type=float, default=1.0)
    run.add_argument("--record-every", type=float, default=10.0)
    run.add_argument("--homogeneous", action="store_true")
    run.add_argument("--out", default="results/run")
    run.set_defaults(func=_cmd_run)

    sweep = sub.add_parser("sweep", help="Barrido paramétrico.")
    sweep.add_argument("--variable", choices=("wind", "moisture"), default="wind")
    sweep.add_argument("--min", type=float, default=0.0)
    sweep.add_argument("--max", type=float, default=8.0)
    sweep.add_argument("--points", type=int, default=9)
    sweep.add_argument("--size", type=int, default=128)
    sweep.add_argument("--cell-size", type=float, default=5.0)
    sweep.add_argument("--wind", type=float, default=4.0)
    sweep.add_argument("--moisture", type=float, default=0.07)
    sweep.add_argument("--fuel", default="FM10")
    sweep.add_argument("--t-end", type=float, default=600.0)
    sweep.add_argument("--dt", type=float, default=1.0)
    sweep.add_argument("--members", type=int, default=1)
    sweep.add_argument("--seed", type=int, default=0)
    sweep.add_argument("--out", default="results/sweep.csv")
    sweep.set_defaults(func=_cmd_sweep)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
