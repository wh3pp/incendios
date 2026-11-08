= Anexos

== Anexo A: disponibilidad y reproducibilidad

El código fuente, los datos de entrada, las semillas y las rutinas de análisis
están disponibles en el repositorio del proyecto. El entorno computacional se
gestiona con `uv`, que fija las versiones de las dependencias, y las pruebas
automatizadas permiten verificar la reproducibilidad de los resultados. La
campaña completa, las tablas y las figuras se regeneran mediante un comando
único; el documento se compila con Typst. Por tratarse de un trabajo de
investigación, el código no se transcribe en el texto: se remite al
repositorio y a su documentación.

Las referencias se seleccionaron entre fuentes con versión de acceso abierto
verificada (informes públicos, revistas de acceso abierto o preprints); no se
incluyen artículos que requieran pago.

Las semillas utilizadas son: escenario base $42$; ensemble $7$ con miembros
$7000, 7001, dots$; percolación $123$ con realizaciones $123 + 1000k$;
barridos $0$; convergencia $0$; sensibilidad $11$. Los resultados numéricos se
conservan en formatos tabulares y binarios para su auditoría.

== Anexo B: símbolos

#figure(
  table(
    columns: (auto, 3.4fr),
    align: (center, left),
    stroke: 0.4pt,
    inset: 4pt,
    table.header([Símbolo], [Significado]),
    [$R$], [Velocidad de propagación (ROS) [m/s].],
    [$R_0$], [ROS base sin viento ni pendiente [m/s].],
    [$R_"max"$], [Cota de seguridad de la ROS [m/s].],
    [$M$], [Humedad del combustible [fracción].],
    [$M_x$], [Humedad de extinción [fracción].],
    [$w_0$], [Carga de combustible [kg/m²].],
    [$sigma$], [Relación superficie--volumen [1/m].],
    [$delta$], [Profundidad del lecho [m].],
    [$beta$], [Relación de empaquetamiento.],
    [$eta_M$], [Amortiguamiento por humedad.],
    [$phi_w, phi_s$], [Factores de viento y pendiente.],
    [$Delta x$], [Tamaño de celda [m].],
    [$Delta t$], [Paso temporal [s].],
    [$tau_"res"$], [Tiempo de residencia [s].],
    [$tau_c$], [Escala de enfriamiento [s].],
    [$H_i$], [Exposición térmica acumulada.],
    [$h_i$], [Tasa de exposición por paso.],
    [$p_c$], [Umbral de percolación.],
    [$D_f$], [Dimensión fractal.],
    [$L/A$], [Relación largo/ancho.],
    [$kappa$], [Número de condición.],
    [$epsilon$], [Épsilon de máquina.],
  ),
  caption: [Símbolos principales.],
) <tab:simbolos>

== Anexo C: unidades y conversiones de Rothermel

El modelo se formula en unidades imperiales: carga en lb/ft², relación
superficie--volumen en ft⁻¹, profundidad en ft, velocidad en ft/min y calor de
combustión en BTU/lb. Las conversiones utilizadas son:
$ 1 " kg/m"^2 = 0.204816 " lb/ft"^2, quad
  1 " m"^{-1} = 0.3048 " ft"^{-1}, $
$ 1 " ft/min" = 0.00508 " m/s", quad
  1 " BTU/lb" = 2326 " J/kg". $
La densidad de partícula se toma como $32$ lb/ft³ y el calor de combustión como
$8000$ BTU/lb. La humedad de extinción y la humedad del combustible se
introducen como fracciones adimensionales. El calor de preignición se calcula
en BTU/lb y la intensidad de reacción en BTU/ft²/min. La conversión final
multiplica por $0.00508$ para obtener m/s.

== Anexo D: tabla completa de percolación

La @tab:perc_full reproduce la probabilidad de percolación para todas las
ocupaciones simuladas. Se observa que la transición de von Neumann es más
abrupta que la de Moore, como corresponde a una vecindad con menos conexiones.

#figure(
  table(
    columns: (auto, auto, auto, auto, auto),
    align: center,
    stroke: 0.4pt,
    inset: 3.5pt,
    table.header([$p$], [4N], [8N], [$p$], [4N / 8N]),
    [0.250], [0.000], [0.000], [0.500], [0.000 / 1.000],
    [0.275], [0.000], [0.000], [0.525], [0.000 / 1.000],
    [0.300], [0.000], [0.000], [0.550], [0.013 / 1.000],
    [0.325], [0.000], [0.000], [0.575], [0.213 / 1.000],
    [0.350], [0.000], [0.000], [0.600], [0.700 / 1.000],
    [0.375], [0.000], [0.063], [0.625], [0.900 / 1.000],
    [0.400], [0.000], [0.350], [0.650], [1.000 / 1.000],
    [0.425], [0.000], [0.775], [0.675], [1.000 / 1.000],
    [0.450], [0.000], [0.975], [0.700], [1.000 / 1.000],
    [0.475], [0.000], [1.000], [0.725], [1.000 / 1.000],
  ),
  caption: [Probabilidad de percolación completa para las dos vecindades.],
) <tab:perc_full>
