= Estado del arte

== Modelos físicos y semiempíricos de propagación

El estudio cuantitativo de la propagación de incendios forestales se remonta a
los trabajos de Rothermel, quien formuló un modelo unidimensional de
propagación superficial basado en el balance de energía en la zona de
precalentamiento @rothermel1972. Su ecuación relaciona la velocidad de
propagación con la intensidad de reacción, la carga de combustible, la relación
superficie--volumen, la humedad y los factores de viento y pendiente. A pesar de
sus simplificaciones, el modelo sigue siendo la base de sistemas operativos
como BEHAVE y FARSITE @andrews2018, @finney1998. La revisión de Andrews
@andrews2018 detalla las correcciones y los límites de validez, mientras que
Scott y Burgan @scott2005 estandarizaron los modelos de combustible usados en
la práctica.

Los modelos físicos y cuasifísicos resuelven las ecuaciones de conservación y
la transferencia de calor por radiación y convección. Trabajos recientes
acoplan la atmósfera y el fuego, como WRF-SFIRE @mandel2011, y revisan medio
siglo de progreso hacia modelos CFD completamente físicos @morvan2022. Estos modelos
capturan la interacción fuego--atmósfera y la formación de columnas
convectivas, pero su costo computacional y la incertidumbre de los parámetros
limitan su uso en simulaciones de largo plazo o en ensembles grandes.

En el extremo opuesto, los modelos empíricos y cuasiempíricos relacionan la
velocidad de propagación con variables ambientales mediante regresiones. La
revisión de Sullivan @sullivan2009a clasifica estos modelos y discute su
dependencia del tipo de combustible y de las condiciones meteorológicas. La
corrección por viento y pendiente, y el efecto de la humedad, se discuten en
las revisiones de Sullivan y en estudios numéricos recientes @hayajneh2025.
En conjunto, la literatura muestra que
ningún modelo es universal: la elección depende del régimen de fuego, de la
escala espacial y de los datos disponibles @sullivan2009a.

== Modelos de autómatas celulares

Los autómatas celulares son sistemas dinámicos discretos definidos por una
retícula, un conjunto finito de estados, una vecindad y una regla de transición
local. Su atractivo para el fuego radica en que reproducen frentes
complejos a partir de reglas simples y permiten incorporar heterogeneidad
espacial de forma natural. Karafyllidis y Thanailakis @karafyllidis1997
propusieron uno de los modelos pioneros: cada celda almacena combustible,
estado de ignición y tiempo de residencia, y la propagación depende de la
velocidad del viento y de la pendiente. Alexandridis et al. @alexandridis2008
extendieron el enfoque con una regla probabilística y validaron la huella
simulada del incendio de Spetses (1990) contra la observada. Variantes
posteriores incorporaron retículas hexagonales y fuentes locales aleatorizadas
para representar la ignición por pavesas.

En el ámbito del control, Hayakawa @hayakawa2011 formuló AC estocásticos con
umbrales de percolación y estrategias de supresión. Sus resultados sugieren que
la probabilidad de propagación a gran escala está controlada por la
conectividad del combustible, y que la supresión puede modelarse como una
reducción local de la probabilidad de ignición. La combinación de AC con
técnicas de aprendizaje automático es una línea reciente que anticipa el uso
actual de emuladores y modelos diferenciables. La revisión de Karakonstantis y
Xylomenos @karakonstantis2026a describe estos desarrollos y señala que la
validación con eventos reales sigue siendo heterogénea.

La revisión más reciente de Karakonstantis y Xylomenos @karakonstantis2026a
analiza los modelos bidimensionales de AC para incendios y señala tres
deficiencias recurrentes: la falta de validación sistemática, la escasa
atención a la incertidumbre de los datos de entrada y la dependencia de
calibraciones ad hoc. El mismo grupo cuantifica el efecto de la incertidumbre
de los datos de entrada en la simulación @karakonstantis2026b, y concluye que
la propagación de la incertidumbre debe evaluarse con ensembles. Nuestro
trabajo responde a esa recomendación.

== Modelos estocásticos, percolación y ensembles

La percolación es el marco natural para estudiar la conectividad del paisaje.
En una red cuadrada, la percolación de sitio presenta un umbral bien definido:
$p_c approx 0.5927$ para vecindad de von Neumann y $p_c approx 0.4073$ para
vecindad de Moore @newman2000. Los umbrales de conectividad forestal dependen
de las condiciones meteorológicas, y la pérdida de conectividad puede reducir
abruptamente la probabilidad de grandes incendios. Los modelos de fuego
autoorganizado muestran que la competencia entre crecimiento de vegetación e
incendios puede llevar a un estado crítico, con una distribución de tamaños de
incendio en ley de potencias.

En el plano operativo, los ensembles Monte Carlo se usan para propagar la
incertidumbre de los parámetros y de las condiciones iniciales. La dispersión
de las predicciones depende de la variabilidad del viento y de la humedad, y
debe evaluarse con ensembles. Los AC probabilísticos son una
alternativa computacionalmente económica a los ensembles de modelos físicos,
pero su relación con el límite determinista no siempre se analiza. En este
trabajo se comparan ambos regímenes con el mismo terreno, la misma
parametrización y el mismo esquema de ignición, de modo que las diferencias
sean atribuibles únicamente al ruido en las reglas.

== Modelos acoplados, GPU y aprendizaje automático

Los modelos acoplados fuego--atmósfera, como WRF-SFIRE @mandel2011, resuelven
la interacción entre el campo de viento y la liberación de calor. Su costo es
varios órdenes de magnitud mayor que el de un AC, pero permiten estudiar
fenómenos como la formación de remolinos de fuego y la modificación local del
viento. En paralelo, la aceleración por GPU y los AC diferenciables han abierto
la posibilidad de calibrar y asimilar datos en tiempo casi real. Los AC
diferenciables en GPU se acoplan a modelos de aprendizaje profundo para
predecir la propagación; la revisión de Andrianarivony y Akhloufi
@andrianarivony2024 sistematiza los avances en aprendizaje automático para
incendios.

Estas líneas de trabajo son complementarias a nuestro enfoque. Un AC
diferenciable podría calibrar los parámetros de Rothermel con datos
satelitales; un modelo acoplado podría reemplazar el viento uniforme por un
campo de viento resuelto; y un modelo de aprendizaje podría sustituir la regla
de transición local por un emulador. Sin embargo, la transparencia y el bajo
costo de un AC clásico siguen siendo valiosos para la docencia, el análisis de
sensibilidad y la exploración de escenarios.

== Síntesis y vacíos de investigación

La @tab:estado_arte resume las familias de modelos revisadas. Se observa
un compromiso entre fidelidad física y costo computacional: los modelos CFD
resuelven la física, pero no permiten explorar grandes ensembles; los AC son
económicos, pero dependen de parametrizaciones y de la calidad de los datos. El
vacío que aborda este trabajo es la falta de estudios que integren, en un mismo
marco reproducible, (i) una parametrización física transparente, (ii) un
análisis de percolación, (iii) una comparación determinista--estocástica y
(iv) una verificación numérica explícita de los métodos empleados.

#figure(
  table(
    columns: (1.25fr, 1.45fr, 1.55fr, 1.55fr, 1.55fr),
    align: (left, left, left, left, left),
    stroke: 0.4pt,
    inset: 4pt,
    table.header(
      [Modelo],
      [Enfoque],
      [Variables],
      [Fortalezas],
      [Limitaciones],
    ),
    [Rothermel @rothermel1972],
    [Semiempírico 1D],
    [Combustible, humedad, viento, pendiente],
    [Base operativa, bajo costo, interpretable],
    [No resuelve 2D ni turbulencia],
    [FARSITE @finney1998],
    [Tiempo mínimo de llegada],
    [Combustible, viento, pendiente],
    [Frentes 2D, amplia validación],
    [Determinista, sensible a la parametrización],
    [AC bidimensional @karakonstantis2026a],
    [Autómata celular],
    [Vegetación, viento, pendiente, supresión],
    [Reglas locales, heterogeneidad, bajo costo],
    [Calibración específica, poca incertidumbre],
    [WRF-SFIRE @mandel2011],
    [CFD acoplado],
    [Atmósfera, fuego, viento],
    [Física detallada, interacción fuego--atmósfera],
    [Costo muy alto, parámetros inciertos],
    [Aprendizaje automático @andrianarivony2024],
    [Emuladores y modelos diferenciables],
    [Datos, imágenes, variables ambientales],
    [Rápido, calibrable, asimilación],
    [Caja negra, requiere datos],
    [Este trabajo],
    [AC 2D determinista y estocástico],
    [Vegetación, humedad, viento, pendiente, percolación],
    [Reproducible, verificado, ensemble],
    [Viento uniforme, sin acoplamiento atmosférico],
  ),
  caption: [Comparación de familias de modelos de propagación de incendios forestales.],
) <tab:estado_arte>
