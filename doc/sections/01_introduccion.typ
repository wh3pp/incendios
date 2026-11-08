= Introducción

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
