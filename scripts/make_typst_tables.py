"""Genera tablas Typst a partir de los CSV de resultados.

El archivo producido, ``doc/tablas.typ``, define funciones ``tabla_*`` que se
invocan desde las secciones del documento. Así se evita transcribir cifras a
mano y se garantiza que las tablas coincidan con las simulaciones.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
OUT = ROOT / "doc" / "tablas.typ"


def num(x: float, digits: int = 2, sci: bool = False) -> str:
    if pd.isna(x):
        return "--"
    x = float(x)
    if sci or (x != 0 and abs(x) < 1e-3):
        return f"{x:.{digits}e}"
    return f"{x:.{digits}f}"


def make_table(
    name: str, headers: list[str], rows: list[list[str]], columns: int | None = None
) -> str:
    cols = columns or len(headers)
    lines = [
        f"#let {name}() = table(",
        f"  columns: {cols},",
        "  align: center,",
        "  stroke: 0.4pt,",
        "  inset: 4pt,",
        "  table.header(" + ", ".join(f"[{h}]" for h in headers) + "),",
    ]
    for row in rows:
        lines.append("  " + ", ".join(f"[{c}]" for c in row) + ",")
    lines.append(")")
    return "\n".join(lines)


def main() -> None:
    blocks: list[str] = [
        "// Archivo generado por scripts/make_typst_tables.py. No editar a mano.",
        "",
    ]

    # Punto flotante.
    df = pd.read_csv(TABLES / "punto_flotante.csv")
    rows = [
        [
            f"`{r.expresion}`",
            num(r.resultado, 4, sci=True),
            num(r.error_abs, 2, sci=True),
        ]
        for r in df.itertuples()
    ]
    blocks.append(
        make_table(
            "tabla_punto_flotante",
            ["Expresión", "Resultado", "Error absoluto"],
            rows,
        )
    )

    # Raíces.
    df = pd.read_csv(TABLES / "raices.csv")
    rows = [
        [
            r.metodo,
            str(int(r.iteraciones)),
            num(r.raiz, 8),
            num(r.error_abs, 2, sci=True),
            num(r.error_final, 2, sci=True),
        ]
        for r in df.itertuples()
    ]
    blocks.append(
        make_table(
            "tabla_raices",
            ["Método", "Iteraciones", "Raíz $M^*$", "$|M_k-M^*|$", "$|f(M_k)|$"],
            rows,
        )
    )

    # EDO.
    df = pd.read_csv(TABLES / "edo.csv")
    rows = [
        [r.metodo.upper(), num(r.dt, 3), num(r.error, 3, sci=True), num(r.orden, 2)]
        for r in df.itertuples()
    ]
    blocks.append(
        make_table(
            "tabla_edo",
            ["Método", "$\\Delta t$ [s]", "Error $|v_N-v(5)|$ [m/s]", "Orden observado"],
            rows,
        )
    )

    # Péndulo.
    df = pd.read_csv(TABLES / "pendulo.csv")
    rows = [
        [
            num(r.amplitud_rad, 2),
            num(r.periodo_rk4, 4),
            num(r.periodo_exacto, 4),
            num(r.error_rel, 2, sci=True),
            num(r.drift_energia_rel, 1, sci=True),
        ]
        for r in df.itertuples()
    ]
    blocks.append(
        make_table(
            "tabla_pendulo",
            [
                "$\\theta_0$ [rad]",
                "$T_{RK4}$ [s]",
                "$T_{exacto}$ [s]",
                "Error rel.",
                "Deriva de energía",
            ],
            rows,
        )
    )

    # Euler-Cromer.
    df = pd.read_csv(TABLES / "euler_cromer.csv")
    rows = [
        [
            r.metodo,
            num(r.dt, 3),
            str(int(r.periodos)),
            num(r.drift_max_rel, 2, sci=True),
            num(r.drift_final_rel, 2, sci=True),
        ]
        for r in df.itertuples()
    ]
    blocks.append(
        make_table(
            "tabla_euler_cromer",
            ["Método", "$\\Delta t$ [s]", "Períodos", "Deriva máx. rel.", "Deriva final rel."],
            rows,
        )
    )

    # N cuerpos.
    df = pd.read_csv(TABLES / "nbody.csv")
    rows = [
        [num(r.dt, 4), num(r.drift_max_rel, 2, sci=True), num(r.drift_final_rel, 2, sci=True)]
        for r in df.itertuples()
    ]
    blocks.append(
        make_table(
            "tabla_nbody",
            ["$\\Delta t$", "Deriva máx. rel.", "Deriva final rel."],
            rows,
        )
    )

    # SDE.
    df = pd.read_csv(TABLES / "sde.csv")
    rows = [
        [
            num(r.t, 0),
            num(r.media_empirica, 3),
            num(r.media_exacta, 3),
            num(r.std_empirica, 3),
            num(r.std_exacta, 3),
            num(r.ks_pvalue, 2),
        ]
        for r in df.itertuples()
    ]
    blocks.append(
        make_table(
            "tabla_sde",
            [
                "$t$ [s]",
                "$\\langle X\\rangle$ emp.",
                "$\\langle X\\rangle$ exacta",
                "$\\sigma$ emp.",
                "$\\sigma$ exacta",
                "$p_{KS}$",
            ],
            rows,
        )
    )

    # Escenario base (tabla vertical de métricas).
    df = pd.read_csv(TABLES / "escenario_base.csv").iloc[0]
    metrics = [
        ("Área quemada", num(df.burned_area_m2 / 1e4, 2) + " ha"),
        ("Fracción quemada", num(df.burned_fraction * 100, 1) + " %"),
        ("ROS de cabeza", num(df.ros_m_min, 2) + " m/min"),
        ("$R^2$ del ajuste de ROS", num(df.ros_r2, 3)),
        ("Perímetro", num(df.perimeter_m / 1000, 2) + " km"),
        ("Relación largo/ancho", num(df.length_breadth, 2)),
        ("Excentricidad", num(df.eccentricity, 3)),
        ("Compacidad", num(df.circularity, 3)),
        ("Dimensión fractal", num(df.fractal_dimension, 3)),
        ("Rugosidad del frente", num(df.roughness_s, 1) + " s"),
        ("Celdas quemadas", num(df.burned_cells, 0)),
    ]
    rows = [[k, v] for k, v in metrics]
    blocks.append(make_table("tabla_escenario", ["Métrica", "Valor"], rows))

    # Viento.
    df = pd.read_csv(TABLES / "viento.csv")
    rows = [
        [num(r.viento_m_s, 0), num(r.ros_m_min, 2), num(r.area_ha, 2), num(r.lb, 2), num(r.fd, 2)]
        for r in df.itertuples()
    ]
    blocks.append(
        make_table(
            "tabla_viento",
            ["$U$ [m/s]", "ROS [m/min]", "Área [ha]", "L/A", "$D_f$"],
            rows,
        )
    )

    # Humedad.
    df = pd.read_csv(TABLES / "humedad.csv")
    rows = [
        [num(r.humedad, 2), num(r.ros_m_min, 2), num(r.area_ha, 2), num(r.head_m, 0)]
        for r in df.itertuples()
    ]
    blocks.append(
        make_table(
            "tabla_humedad",
            ["$M$ [--]", "ROS [m/min]", "Área [ha]", "Avance [m]"],
            rows,
        )
    )

    # Pendiente.
    df = pd.read_csv(TABLES / "pendiente.csv")
    rows = [
        [num(r.pendiente_grados, 1), num(r.ros_m_min, 2), num(r.area_ha, 2), num(r.lb, 2)]
        for r in df.itertuples()
    ]
    blocks.append(
        make_table(
            "tabla_pendiente",
            ["Pendiente [°]", "ROS [m/min]", "Área [ha]", "L/A"],
            rows,
        )
    )

    # Percolación (selección).
    df = pd.read_csv(TABLES / "percolacion.csv")
    keep = [0.35, 0.375, 0.40, 0.425, 0.45, 0.475, 0.50, 0.525, 0.55, 0.575, 0.60, 0.625, 0.65]
    sel = df[df["ocupacion"].apply(lambda x: any(abs(x - k) < 1e-9 for k in keep))]
    piv = sel.pivot(index="ocupacion", columns="vecindad", values="p_percolacion").reset_index()
    rows = [
        [
            num(r.ocupacion, 3),
            num(r["Von Neumann (4)"], 3),
            num(r["Moore (8)"], 3),
        ]
        for _, r in piv.iterrows()
    ]
    blocks.append(
        make_table(
            "tabla_percolacion",
            ["$p$", "$P_{\\mathrm{perc}}$ (4)", "$P_{\\mathrm{perc}}$ (8)"],
            rows,
        )
    )

    # Comparación determinista/estocástico.
    df = pd.read_csv(TABLES / "comparacion.csv")
    rows = [
        [
            r.modelo,
            num(r.area_media_ha, 2),
            num(r.area_std_ha, 2),
            num(r.cv_area * 100, 2),
            num(r.ros_medio_m_min, 2),
            num(r.lb_medio, 2),
            num(r.fd_media, 2),
        ]
        for r in df.itertuples()
    ]
    blocks.append(
        make_table(
            "tabla_comparacion",
            ["Modelo", "Área [ha]", "$\\sigma_A$ [ha]", "CV [%]", "ROS [m/min]", "L/A", "$D_f$"],
            rows,
        )
    )

    # Convergencia espacial.
    df = pd.read_csv(TABLES / "convergencia_espacial.csv")
    rows = [
        [
            num(r.celda_m, 2),
            str(int(r.n)),
            num(r.ros_m_min, 3),
            num(r.error_rel * 100, 1),
            num(r.orden, 2) if pd.notna(r.orden) else "--",
        ]
        for r in df.itertuples()
    ]
    blocks.append(
        make_table(
            "tabla_convergencia_espacial",
            ["$\\Delta x$ [m]", "$N$", "ROS [m/min]", "Error rel. [%]", "Orden"],
            rows,
        )
    )

    # Convergencia temporal.
    df = pd.read_csv(TABLES / "convergencia_temporal.csv")
    rows = [
        [num(r.dt_s, 3), num(r.ros_m_min, 3), num(r.error_rel * 100, 2)] for r in df.itertuples()
    ]
    blocks.append(
        make_table(
            "tabla_convergencia_temporal",
            ["$\\Delta t$ [s]", "ROS [m/min]", "Error rel. [%]"],
            rows,
        )
    )

    # Sensibilidad.
    df = pd.read_csv(TABLES / "sensibilidad.csv")
    rows = [[r.parametro.capitalize(), num(r.elasticidad, 3)] for r in df.itertuples()]
    blocks.append(make_table("tabla_sensibilidad", ["Parámetro", "Elasticidad"], rows))

    # Casos reales.
    df = pd.read_csv(TABLES / "casos_reales.csv")
    rows = []
    for r in df.itertuples():
        iou = "--" if pd.isna(r.iou) else num(r.iou, 2)
        rows.append(
            [
                r.caso,
                r.pais,
                r.inicio,
                num(r.area_observada_ha, 0),
                num(r.area_simulada_ha, 0),
                num(r.error_area_rel * 100, 1),
                iou,
                num(r.ros_m_min, 1),
                num(r.lb, 2),
            ]
        )
    blocks.append(
        make_table(
            "tabla_casos_reales",
            [
                "Caso",
                "País",
                "Inicio",
                "Área obs. [ha]",
                "Área sim. [ha]",
                "Error [%]",
                "IoU",
                "ROS [m/min]",
                "L/A",
            ],
            rows,
        )
    )

    # Rendimiento (datos medidos en la campaña).
    perf = [
        ("64", "0.09", "0.13", "0.6"),
        ("128", "0.20", "0.30", "2.3"),
        ("256", "0.81", "1.14", "9.2"),
        ("512", "3.78", "--", "36.8"),
    ]
    blocks.append(
        make_table(
            "tabla_rendimiento",
            ["$N$", "Det. [s]", "Estoc. [s]", "Memoria [MB]"],
            [list(p) for p in perf],
        )
    )

    OUT.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")

    # Conversión de comandos LaTeX a sintaxis matemática de Typst.
    import re

    text = OUT.read_text(encoding="utf-8")

    def fix(match: re.Match) -> str:
        frag = match.group(0)
        frag = re.sub(r"\\text\{([^}]*)\}", r'"\1"', frag)
        frag = re.sub(r"\\mathrm\{([^}]*)\}", r'"\1"', frag)
        frag = re.sub(r"\\mathcal\{([^}]*)\}", r"cal(\1)", frag)
        frag = frag.replace(r"\langle", "⟨").replace(r"\rangle", "⟩")
        frag = frag.replace(r"\left", "").replace(r"\right", "")
        frag = re.sub(r"\\([A-Za-z]+)", r"\1", frag)
        return frag

    text = re.sub(r"\$.*?\$", fix, text, flags=re.DOTALL)
    text = text.replace("geq", ">=").replace("leq", "<=")
    text = text.replace("T_{RK4}", 'T_"RK4"').replace("T_{exacto}", 'T_"exacto"')
    text = text.replace("p_{KS}", 'p_"KS"').replace("P_{perc}", 'P_"perc"')
    text = text.replace("P_{mathrm{perc}}", 'P_"perc"')
    OUT.write_text(text, encoding="utf-8")
    print("Escrito", OUT)


if __name__ == "__main__":
    main()
