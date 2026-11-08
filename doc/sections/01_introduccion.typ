= Introducción

== Contexto y motivación

Los incendios forestales constituyen una de las perturbaciones naturales de
mayor impacto sobre los ecosistemas, la atmósfera y las sociedades. En las
últimas décadas, el aumento de las temperaturas medias, la prolongación de las
sequías y la expansión de la interfaz urbano--forestal han incrementado tanto
la frecuencia como la intensidad de los grandes incendios @morvan2022. La
predicción de su propagación es un problema científico y operativo: de ella
dependen la evacuación de poblaciones, la asignación de recursos de extinción y
la evaluación de riesgos. Sin embargo, el fuego es un fenómeno multiescala en el
que intervienen procesos de combustión, transferencia de calor, turbulencia,
transporte de pavesas y heterogeneidades del paisaje @sullivan2009a.

Desde la física computacional, el problema se aborda mediante modelos que
discretizan el espacio y el tiempo. Los modelos físicos resuelven las
ecuaciones de conservación de masa, momento y energía, pero su costo
computacional es elevado y requieren parámetros difíciles de medir
@morvan2022. Los modelos empíricos y semiempíricos, como el de Rothermel
@rothermel1972, son más económicos y constituyen la base de herramientas
operativas como FARSITE @finney1998 y de numerosos simuladores de propagación
@andrews2018. Los autómatas celulares (AC) ocupan un lugar intermedio: son
modelos de estados discretos, reglas locales y actualización paralela, capaces
de reproducir patrones complejos con un costo computacional moderado.

La motivación de este trabajo es construir un modelo de AC bidimensional que
integre, de forma transparente y reproducible, los principales controles
físicos de la propagación ---combustible, humedad, viento y pendiente--- y que
permita comparar un régimen determinista con uno probabilístico. El interés no
es solo reproducir una forma de fuego, sino entender cómo la incertidumbre en
las reglas locales modifica la velocidad, la forma del frente y el área
quemada. Esta pregunta conecta la física del fuego con herramientas numéricas
del curso: aritmética de punto flotante, ecuaciones no lineales, integradores de
EDO, ecuaciones diferenciales estocásticas y autómatas celulares.

== Planteamiento del problema

Un modelo de propagación de incendios debe responder, al menos, a tres
preguntas: ¿dónde está el frente en cada instante?, ¿a qué velocidad avanza? y
¿cómo cambia su forma? En terrenos heterogéneos, la respuesta depende de la
distribución espacial de la vegetación, de la humedad, de la pendiente y del
viento. Pequeñas variaciones en la conectividad del combustible pueden producir
cambios abruptos en la extensión del incendio, un comportamiento característico
de los fenómenos de percolación @newman2000.

Los modelos de AC existentes se han aplicado a incendios reales, a paisajes
heterogéneos y a tácticas de supresión; la revisión de @karakonstantis2026a
documenta estos desarrollos. No obstante, muchos trabajos presentan
tres limitaciones: (i) las reglas de transición se calibraron para un paisaje
particular y no se analiza su sensibilidad; (ii) la comparación entre modelos
deterministas y probabilísticos se reduce a una diferencia cualitativa; y
(iii) la verificación numérica del simulador ---orden de convergencia,
acondicionamiento, propagación de errores--- no suele reportarse. Este trabajo
aborda esas tres limitaciones en un marco unificado.

El problema central se formula así: _¿cómo afectan la heterogeneidad del
terreno, el viento, la humedad y la pendiente a la velocidad y forma del frente
de un incendio simulado con un autómata celular bidimensional, y qué diferencias
introduce la incorporación de incertidumbre en las reglas de propagación?_

== Preguntas de investigación

#enum(
  [¿Qué modelo de velocidad de propagación, basado en Rothermel y corregido por
    viento y pendiente, reproduce rangos físicamente plausibles para distintos
    tipos de combustible?],
  [¿Cómo cambian la velocidad de propagación, el área quemada y la relación
    largo/ancho al variar la velocidad del viento, la humedad y la pendiente?],
  [¿Existe un umbral de densidad de vegetación por debajo del cual el incendio
    no percola a través del paisaje? ¿Coincide con los umbrales teóricos de
    percolación de sitio?],
  [¿Qué diferencias produce un modelo probabilístico frente a uno determinista
    en el área media, la dispersión y la rugosidad del frente?],
  [¿Se satisfacen los órdenes de convergencia y las leyes de escala esperadas
    para los métodos numéricos empleados (RK4, Euler-Maruyama, Monte Carlo)?],
)

== Hipótesis

*H1.* La velocidad de propagación de cabeza aumenta de forma monótona con el
viento y la pendiente, y disminuye de forma no lineal con la humedad, anulándose
en un umbral efectivo cercano a la humedad de extinción del combustible.

*H2.* La conectividad del paisaje impone un umbral de percolación: para
ocupaciones inferiores a $p_c$, la probabilidad de que el fuego atraviese el
dominio cae abruptamente. Con vecindad de Moore, el umbral debe ser cercano a
$0.407$; con vecindad de von Neumann, cercano a $0.593$.

*H3.* La incorporación de ruido en las reglas de ignición aumenta la dispersión
del área quemada y modifica el valor medio, porque el frente aprovecha caminos
de ignición temprana (percolación de primer paso). El coeficiente de variación
del ensemble debe ser pequeño para dominios grandes, pero el sesgo respecto del
modelo determinista puede ser sistemático.

*H4.* Los integradores numéricos utilizados conservan las propiedades teóricas:
RK4 presenta orden cuatro, Euler-Maruyama reproduce la ley de difusión
$"MSD" prop t$ y el AC reproduce los diagramas fundamentales de la
regla 184 y del modelo de Nagel--Schreckenberg.

== Objetivos

=== Objetivo general

Desarrollar y validar un simulador de propagación de incendios forestales
basado en autómatas celulares bidimensionales, que incorpore heterogeneidad
espacial, viento, humedad y pendiente, y que permita comparar un modelo
determinista con uno probabilístico mediante técnicas de Monte Carlo y
herramientas de análisis numérico.

=== Objetivos específicos

#enum(
  [Formular un AC bidimensional con estados de celda, vecindad de Moore y
    reglas de transición basadas en la velocidad de propagación de Rothermel,
    corregida por viento y pendiente.],
  [Generar terrenos sintéticos heterogéneos mediante ruido fractal espectral y
    mapas de combustible, humedad, vegetación y pendiente.],
  [Implementar un modelo determinista por acumulación de exposición y un modelo
    probabilístico de Bernoulli, junto con un ensemble Monte Carlo reproducible.],
  [Verificar numéricamente el simulador mediante pruebas de punto flotante,
    acondicionamiento, métodos de raíces, integradores de EDO, EDE y autómatas
    clásicos.],
  [Cuantificar el efecto del viento, la humedad, la pendiente y la densidad de
    vegetación sobre la ROS, el área quemada y la forma del frente.],
  [Estimar los umbrales de percolación del paisaje y compararlos con los valores
    teóricos de la red cuadrada.],
  [Comparar el modelo determinista con el probabilístico en términos de área
    media, desviación estándar, coeficiente de variación y rugosidad del frente.],
  [Aplicar el simulador a dos eventos reales: el incendio de Acos (Cusco,
    2025) y el Little Giant Fire (Washington, 2026), usando DEM, área oficial
    y perímetro cuando esté disponible.],
  [Documentar el código, las semillas, las tablas y las figuras para garantizar
    la reproducibilidad total del estudio.],
)

== Justificación

La propagación de incendios forestales es un fenómeno complejo en el que
intervienen múltiples factores físicos y ambientales: las características de la
vegetación, la humedad, el viento y la topografía. La interacción entre estas
variables puede producir patrones difíciles de describir mediante modelos
analíticos simples, especialmente cuando el entorno es heterogéneo. Los AC
representan una alternativa adecuada porque discretizan el terreno en una malla
bidimensional y representan la evolución del incendio mediante reglas locales
de transición entre estados @karakonstantis2026a.

La comparación entre un modelo determinista y uno probabilístico permite
estudiar el efecto de incorporar incertidumbre en las reglas de propagación.
Mientras que el modelo determinista utiliza reglas de transición fijas, el
modelo probabilístico representa de manera simplificada la variabilidad
producida por las condiciones locales del terreno y del entorno. Esta
comparación es relevante porque los modelos operativos suelen ser deterministas,
pero las observaciones reales exhiben variabilidad e incertidumbre
@karakonstantis2026b.

Desde el punto de vista computacional, los AC presentan una estructura adecuada
para la ejecución paralela, debido a que la actualización de numerosas celdas
puede realizarse de manera concurrente a partir del estado del paso temporal
anterior. El simulador desarrollado es vectorizado con NumPy y puede extenderse
a GPU; la revisión de @andrianarivony2024 muestra que los AC diferenciables y
acelerados permiten asimilar datos satelitales y calibrar parámetros. Además,
la incorporación de técnicas de aprendizaje automático
@andrianarivony2024 y de asimilación de datos @mandel2011 constituye una línea
natural de trabajo futuro.

Finalmente, el trabajo tiene un valor formativo: integra los contenidos de las
seis sesiones del curso de Física Computacional ---propagación de errores,
ecuaciones no lineales, EDO, osciladores y N cuerpos, EDE y autómatas
celulares--- en un único problema de investigación. Cada herramienta numérica se
aplica a una pregunta concreta del modelo, y no como un ejercicio aislado.

== Alcances y limitaciones

*Alcances.* El modelo representa la propagación superficial en una malla
cuadrada de hasta $512 times 512$ celdas, con celdas de $1.25$ a $10$ m. Incluye
cuatro modelos de combustible estándar (pasto, matorral, hojarasca y bosque),
humedad variable, viento uniforme, pendiente derivada de un campo de elevación y
obstáculos incombustibles. Se implementan dos regímenes (determinista y
estocástico) y se analizan barridos paramétricos, percolación, convergencia y
sensibilidad.

*Limitaciones.* El modelo no resuelve la combustión en detalle ni la
turbulencia atmosférica; la velocidad de propagación se prescribe mediante una
parametrización semiempírica. El viento es uniforme y estacionario, y no se
modela el acoplamiento fuego--atmósfera. No se incluyen pavesas (spotting) en
las simulaciones principales, aunque se analiza su transporte como problema de
verificación. La humedad y la vegetación son campos sintéticos, no derivados de
datos satelitales. Finalmente, la comparación con incendios reales es
cualitativa: se contrastan rangos de ROS y relaciones largo/ancho reportados en
la literatura, pero no se realiza una calibración formal con un evento
específico.
