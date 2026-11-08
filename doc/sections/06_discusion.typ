= Discusión

== Interpretación física de los resultados

Los barridos paramétricos muestran que el modelo reproduce las tendencias
cualitativas esperadas: la ROS aumenta con el viento y la pendiente, disminuye
con la humedad y se anula en un umbral efectivo. La dependencia del viento es
casi lineal para $U < 4$ m/s y se acelera ligeramente después, consistente con
la forma potencial de $phi_w$. La pendiente produce un crecimiento más que
lineal, porque $phi_s$ depende de $tan^2 phi$. La humedad, en cambio, reduce la
ROS de forma no lineal y desplaza el umbral de extinción por debajo de $M_x$
debido al tiempo de residencia finito. Este último resultado es
físicamente plausible: en un frente real, la celda vecina debe recibir
suficiente calor antes de que el combustible del frente se consuma; si la
humedad es alta, la tasa de liberación de calor no alcanza para completar el
cruce.

La relación largo/ancho es un indicador sensible a la anisotropía del modelo.
Con viento nulo, la huella es casi circular ($L/A approx 1$); con $8$ m/s,
$L/A approx 4.4$. La saturación alrededor de $4.4$ se debe a que el kernel
angular y la resolución de la malla limitan la concentración del frente. En
comparación, la fórmula de Anderson @anderson1983 predice relaciones mayores
para vientos fuertes; sin embargo, esa fórmula se calibró para incendios de
alta intensidad y no para un AC con resolución de $5$ m. La tendencia es
consistente, aunque la magnitud no debe interpretarse como una validación
cuantitativa.

El experimento de percolación es, quizás, el resultado más contundente. Los
umbrales estimados, $0.5907$ y $0.4084$, coinciden con los valores teóricos
$0.5927$ y $0.4073$ dentro de $0.002$. Esto valida no solo la implementación
del AC, sino también la interpretación del paisaje como una red de sitios
conectados. La diferencia entre ambas vecindades es enorme: con Moore, el fuego
percola con una ocupación del $41$%; con von Neumann, necesita el $59$%. En
términos de gestión, esto implica que la conectividad diagonal es un factor de
primer orden: fragmentar el combustible en una retícula que elimine los
contactos diagonales puede aumentar sustancialmente el umbral de propagación.

== El efecto de la incertidumbre

La comparación determinista--estocástica muestra una diferencia sistemática: el
ensemble produce un área $2.4$ veces mayor a $t=600$ s, con un coeficiente de
variación del $3.1$%. Esta diferencia no es ruido estadístico; es un sesgo
producido por la percolación de primer paso. El área crece sobre todo por
ensanchamiento e igniciones tempranas en los flancos: la ROS axial estimada
por el ajuste global es $35.3$ m/min en el ensemble y $42.2$ m/min en el
determinista, mientras la relación largo/ancho baja de $1.87$ a $1.34$. En el
modelo determinista, la
celda se enciende cuando la exposición acumulada alcanza uno; en el modelo
probabilístico, la ignición es un proceso de Poisson y algunas celdas se
encienden antes del tiempo medio. En una retícula 2D, el frente puede elegir
entre muchos caminos; el tiempo de llegada es el mínimo de una colección de
variables aleatorias, y el mínimo tiene esperanza menor que el mínimo de las
esperanzas. Este mecanismo es conocido en la teoría de percolación de primer
paso y en los modelos de crecimiento de interfaces.

El resultado tiene dos implicaciones. Primero, los modelos deterministas
pueden subestimar el área quemada cuando la incertidumbre local es alta; esto
es relevante para la gestión del riesgo, porque las decisiones se toman sobre
escenarios medios. Segundo, la dispersión del ensemble es pequeña para dominios
grandes, pero el sesgo persiste; no basta con aumentar el número de
realizaciones para corregirlo, porque el sesgo es una propiedad del modelo, no
del muestreo. Para reducir la diferencia sería necesario calibrar el umbral
determinista con el tiempo medio de ignición del modelo estocástico, o usar un
modelo de umbral aleatorio con una distribución estrecha en lugar de una
exponencial.

La disminución de la relación largo/ancho en el ensemble ($1.87 arrow.r 1.34$) y el
aumento de la dimensión fractal ($1.79 arrow.r 1.82$) indican que el ruido hace el
frente más redondeado y más ramificado. Esto es contraintuitivo: se esperaría
que el ruido aumentara la elongación al permitir igniciones tempranas en la
dirección del viento; sin embargo, también permite igniciones laterales, que
ensanchan la huella. El balance neto depende del cociente entre la tasa de
ignición lateral y la de cabeza. En nuestros resultados, el ensanchamiento
domina, probablemente porque el kernel angular es estrecho y la probabilidad
lateral, aunque pequeña, se acumula durante $600$ s.

== Comparación con el estado del arte

Los modelos de AC revisados por Karakonstantis y Xylomenos
@karakonstantis2026a suelen reportar validaciones con eventos reales, pero
rara vez incluyen un análisis de percolación o una comparación
determinista--estocástica con el mismo terreno. Nuestro trabajo llena ese vacío
al proporcionar un marco reproducible que combina ambos. La coincidencia de los
umbrales de percolación con la teoría es un argumento fuerte a favor de la
implementación; la diferencia sistemática entre regímenes es un recordatorio de
que la elección del modelo de ignición no es neutral.

En comparación con los modelos acoplados fuego--atmósfera @mandel2011, nuestro
modelo es mucho más económico, pero no resuelve la retroalimentación del fuego
sobre el viento. En comparación con los modelos de aprendizaje automático
@andrianarivony2024, nuestro modelo es interpretable y no requiere
datos de entrenamiento, pero no captura patrones empíricos que no estén
codificados en Rothermel. La combinación de ambos enfoques ---un AC físico como
prior y un emulador de aprendizaje para corregir sesgos--- es una línea
prometedora.

== Aplicación a eventos reales

Los dos casos muestran que el simulador puede alimentarse con datos reales,
pero también revelan la brecha entre un modelo de investigación y una
herramienta operativa. En Acos, el área oficial se reproduce con un error del
$3.6$%, lo que valida la escala de la parametrización; sin embargo, la ausencia
de perímetro impide evaluar la forma, y la elipse usada como referencia no es
una cicatriz observada. En Little Giant, el perímetro WFIGS permite calcular un
IoU de $0.62$ y un error de área del $38.2$% en una subventana; la
sobreestimación es consistente con un modelo que simula cuatro días con
combustible asignado por reglas altitudinales, mientras el perímetro oficial
corresponde al estado final tras varios meses.

La lección metodológica es que la calidad del caso depende menos del modelo
que de los datos de entrada. Para el Perú, el siguiente paso es construir
perímetros oficiales o derivados de Sentinel-2 y mapas de combustible locales;
para eventos internacionales, usar LANDFIRE, RAWS y perímetros diarios. Sin
esos insumos, el modelo puede reproducir el orden de magnitud del área, pero no
la geometría ni la cronología del frente.

== Limitaciones

#enum(
  [*Parametrización semiempírica.* La ROS se calcula con Rothermel y un factor
    de eficiencia del viento calibrado ($f_w=0.30$). No se realizó una
    calibración formal con datos de campo; los valores de ROS deben
    interpretarse como órdenes de magnitud, no como predicciones operativas.],
  [*Viento uniforme.* El viento es constante en espacio y tiempo. En un
    incendio real, la interacción con la topografía y la columna convectiva
    genera campos de viento no uniformes que pueden cambiar la dirección del
    frente.],
  [*Sin spotting.* Las pavesas se estudian como un problema de verificación,
    pero no se incorporan a las simulaciones principales. El spotting puede
    iniciar focos secundarios a cientos de metros y dominar la propagación en
    condiciones extremas.],
  [*Terreno sintético.* La elevación, la vegetación y la humedad son campos
    generados, no derivados de datos satelitales o de inventarios forestales.
    La heterogeneidad es realista en sentido estadístico, pero no corresponde a
    un paisaje específico.],
  [*Modelo estocástico.* La hipótesis de intentos de Bernoulli independientes
    es una simplificación. En un frente real, la ignición es un proceso
    continuo con memoria térmica; un modelo de umbral aleatorio o un proceso
    de Hawkes podrían representar mejor la correlación temporal.],
  [*Escala.* El dominio máximo es de $512 times 512$ celdas ($2.56$ km con
    $Delta x=5$ m). Los incendios reales abarcan decenas de kilómetros; la
    extrapolación requiere simulaciones de mayor escala y paralelización.],
)

== Implicaciones para la enseñanza y la práctica

Desde el punto de vista formativo, el trabajo muestra cómo las herramientas de
un curso de Física Computacional se articulan en un problema real. La
propagación de errores no es un tema abstracto: el número de condición de
Rothermel cerca de la extinción explica por qué las predicciones son inciertas.
Los métodos de raíces permiten encontrar umbrales de humedad y viento. Los
integradores de EDO aparecen en el transporte de pavesas y en la verificación
de la conservación de energía. Las EDE y el análisis de MSD proporcionan el
lenguaje para interpretar la dispersión del frente. Y los autómatas celulares
---regla 184, Nagel--Schreckenberg, Juego de la Vida--- ofrecen un banco de
pruebas para validar el motor antes de aplicarlo al fuego.

Desde el punto de vista práctico, el simulador puede usarse para explorar
escenarios: ¿qué pasa si la humedad aumenta un $20$%?, ¿cuánto se reduce el
área quemada si se crea un cortafuegos?, ¿cómo cambia el riesgo al pasar de
viento de $2$ a $6$ m/s? Las respuestas son cualitativas, pero permiten
comparar alternativas y comunicar la importancia relativa de los factores. Con
datos reales y una calibración adecuada, el mismo marco podría convertirse en
una herramienta de apoyo a la decisión.
