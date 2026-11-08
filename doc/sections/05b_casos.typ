#import "../tablas.typ": *

= Aplicación a eventos reales

== Selección y fuentes de datos

Se seleccionaron dos casos: uno peruano y uno internacional. El caso peruano
es el incendio de Acos (Cusco, septiembre de 2025), documentado por INDECI; el
caso internacional es el Little Giant Fire (Washington, Estados Unidos, julio
de 2026), con perímetro oficial WFIGS. La @tab:fuentes_casos resume las
fuentes. La elevación proviene de teselas Terrarium/Mapzen, que se descargan
sin clave de API y se cachean localmente; los perímetros y metadatos se
guardan en formatos geoespaciales y tabulares para que la simulación sea
reproducible.

#figure(
  table(
    columns: (1.2fr, 2.4fr, 2.2fr),
    align: (left, left, left),
    stroke: 0.4pt,
    inset: 4pt,
    table.header([Insumo], [Acos], [Little Giant]),
    [Fecha de inicio], [11/09/2025, 12:24], [15/07/2026],
    [Área observada], [300 ha (INDECI)], [172 912 acres ≈ 69 975 ha (WFIGS)],
    [Perímetro], [No oficial; elipse equivalente], [WFIGS, perímetro oficial],
    [DEM], [Terrarium/Mapzen, 128×128], [Terrarium/Mapzen, 128×128],
    [Combustible], [Reglas altitudinales andinas], [Reglas altitudinales Cascades],
    [Viento/humedad], [Parámetros efectivos calibrados], [Parámetros efectivos],
    [Fuente], [#link("https://portal.indeci.gob.pe/")[INDECI]], [#link("https://www.nifc.gov/")[NIFC/WFIGS]],
  ),
  caption: [Fuentes de datos de los dos casos reales.],
) <tab:fuentes_casos>

== Caso peruano: Acos, Cusco (2025)

El 11 de septiembre de 2025, a las 12:24 h, se registró un incendio forestal en
el sector Mayuhuilca, distrito de Acos, provincia de Acomayo, Cusco. INDECI
reportó 300 ha de cobertura natural destruida y su extinción el 15 de
septiembre de 2025. No se dispone de un perímetro oficial, por lo que la
validación se limita al área y a la escala; la elipse de la @fig:acos(a)
es una referencia de área, no una cicatriz observada.

La simulación usó una malla de $160 times 160$ celdas ($Delta x approx 25.9$ m),
$Delta t = 20$ s y cuatro días de evolución. El combustible se asignó por
altitud: pasto por debajo de 3300 m, matorral entre 3300 y 3550 m y hojarasca
por encima de 3550 m. El viento efectivo se calibró a 3 m/s y la humedad a
$0.11$; estos valores son parámetros efectivos, no una serie meteorológica.
El área simulada fue $307.6$ ha frente a $296.9$ ha de la máscara de
referencia ($300$ ha oficiales), un error del $3.6$%. La ROS de cabeza fue $10.4$ m/min, la relación largo/ancho $1.36$ y la
dimensión fractal $1.81$.

#figure(
  image("../assets/figures/caso_acos.pdf", width: 100%),
  caption: [Caso Acos: (a) DEM real y elipse de área oficial; (b) área simulada frente a la referencia de área; (c) evolución del área quemada.],
) <fig:acos>

== Caso internacional: Little Giant Fire (2026)

El Little Giant Fire se inició el 15 de julio de 2026 en el condado de Chelan,
Washington, por un rayo. WFIGS reporta $172\,912$ acres ($approx 69\,975$ ha)
y un perímetro oficial. El evento completo excede la escala del modelo, por lo
que se simuló una subventana de $4.4$ km alrededor de la ignición, con
$160 times 160$ celdas ($Delta x approx 27.8$ m), $Delta t = 20$ s y cuatro
días. El perímetro WFIGS se rasterizó sobre la subventana: el área observada
dentro de ella es $1252.7$ ha. El modelo produjo $1731.0$ ha, un error del
$38.2$%, con un IoU de $0.62$ respecto del perímetro oficial recortado.

#figure(
  image("../assets/figures/caso_little_giant.pdf", width: 100%),
  caption: [Caso Little Giant: (a) DEM real y perímetro WFIGS; (b) área simulada frente al perímetro observado; (c) evolución del área quemada en la subventana.],
) <fig:little_giant>

#figure(tabla_casos_reales(), caption: [Métricas de los dos casos reales. En Acos, el área observada es la máscara elíptica de referencia ($297$ ha; $300$ ha oficiales). En Little Giant, corresponde a la subventana de 4.4 km, no al total de 69 975 ha. El IoU de Acos no se reporta porque no existe perímetro oficial.]) <tab:casos_reales>

== Validación y limitaciones

La @tab:casos_reales resume los resultados. El caso Acos reproduce el
área de referencia con un error del $3.6$% ($2.5$% respecto de las $300$ ha
oficiales), pero no permite evaluar la forma porque no hay perímetro. El caso
Little Giant alcanza un IoU de $0.62$ con el perímetro observado en la
subventana, con una sobreestimación del área del $38.2$%; la
diferencia es esperable porque el modelo simula cuatro días con combustible
asignado por reglas altitudinales, mientras que el perímetro WFIGS corresponde
al estado final tras varios meses y el evento completo supera la escala del
dominio.

Las limitaciones principales son: (i) no existe un perímetro oficial para el
caso peruano; (ii) el combustible no proviene de un inventario local
(MapBiomas/LANDFIRE) sino de reglas altitudinales; (iii) el viento y la humedad
son parámetros efectivos calibrados, no series ERA5-Land; (iv) la resolución de
$25$--$28$ m es más gruesa que la de las simulaciones sintéticas ($5$ m); y
(v) el tiempo de residencia se escaló para que el frente pudiera cruzar celdas
gruesas. Estas limitaciones no invalidan la comparación de orden de magnitud,
pero impiden presentar los casos como predicciones operativas.

El valor del ejercicio es metodológico: demuestra que el simulador puede
alimentarse con un DEM real, una fecha y un área oficial, y que el pipeline de
validación funciona. La incorporación de Sentinel-2, MapBiomas, LANDFIRE y
ERA5-Land, junto con perímetros oficiales peruanos, queda como trabajo futuro
inmediato.
