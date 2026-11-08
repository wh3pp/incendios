#set text(size: 9.5pt)
#set par(leading: 0.56em)

#align(center)[
  #text(size: 13pt, weight: "bold")[Resumen]
]

#align(center)[
  #text(size: 9pt, style: "italic")[
    Avance de investigación (65 %): estado del arte, marco teórico y metodología
  ]
]

Los incendios forestales son fenómenos complejos en los que interactúan la
vegetación, la humedad, el viento y la topografía. Su propagación sobre
terrenos heterogéneos presenta frentes irregulares, umbrales de conectividad y
una sensibilidad considerable a las condiciones locales. Este trabajo desarrolla
un simulador bidimensional basado en autómatas celulares que representa el
terreno como una malla de celdas con estado, propiedades de combustible y
condiciones meteorológicas. La velocidad de propagación se calcula con una
versión vectorizada del modelo de Rothermel, corregida por viento y pendiente,
y se transfiere a los ocho vecinos de Moore mediante un kernel angular
calibrado. Se implementan dos variantes: un AC determinista por acumulación de
exposición térmica y un AC probabilístico de Bernoulli, este último evaluado con
ensembles Monte Carlo.

En esta entrega se presentan la introducción, el estado del arte, el marco
teórico y la metodología completa: formulación del modelo, generación del
terreno, reglas de propagación, algoritmos determinista y probabilístico,
métricas, diseño experimental y estrategia de validación. Los resultados
numéricos, la comparación sistemática de escenarios y la aplicación a eventos
reales se desarrollan en la etapa final del trabajo.

#v(0.6em)
*Palabras clave:* autómatas celulares, incendios forestales, Rothermel,
percolación, Monte Carlo, análisis numérico, física computacional.

// Restaurar el tamaño y el interlineado del cuerpo principal.
#set text(size: 10.5pt)
#set par(leading: 0.62em)
