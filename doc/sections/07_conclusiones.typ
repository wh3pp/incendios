= Conclusiones

El objetivo general se cumplió: se desarrolló y validó un simulador de
propagación de incendios forestales basado en autómatas celulares
bidimensionales, con heterogeneidad espacial, viento, humedad y pendiente, y se
compararon los regímenes determinista y probabilístico con herramientas de
análisis numérico. Las conclusiones específicas son las siguientes.

#enum(
  [*Modelo físico y numérico.* La combinación de Rothermel con un kernel
    angular $cos^8$ y una eficiencia de viento $f_w=0.30$ produce ROS
    plausibles para cuatro modelos de combustible. La ROS de FM10 varía de
    $2.40$ a $31.98$ m/min cuando el viento pasa de $0$ a $8$ m/s, y de
    $2.40$ a $16.35$ m/min cuando la pendiente pasa de $0$ a $31$°. Los
    órdenes de magnitud son consistentes con los rangos de la literatura
    @andrews2018, @sullivan2009a.],
  [*Efecto de la humedad.* La ROS disminuye de $3.81$ m/min a $M=0.03$ hasta
    $1.03$ m/min a $M=0.18$, y se anula para $M >= 0.21$. El umbral efectivo
    es inferior a la humedad de extinción $M_x=0.25$ porque el tiempo de
    residencia finito impide completar el cruce de la celda. Este resultado
    reproduce cualitativamente la no linealidad reportada en la literatura.],
  [*Percolación.* El modelo reproduce los umbrales teóricos de percolación de
    sitio de la red cuadrada: $p_c = 0.5907$ con vecindad de von Neumann
    (teórico $0.5927$) y $p_c = 0.4084$ con vecindad de Moore (teórico
    $0.4073$). La diferencia es del orden de $0.002$, dentro de la
    incertidumbre estadística. Esto valida el motor de propagación y confirma
    que la conectividad diagonal reduce drásticamente el umbral de propagación
    @newman2000.],
  [*Determinista vs. estocástico.* El ensemble de $32$ realizaciones produce
    un área media de $24.89$ ha frente a $10.28$ ha del modelo determinista a
    $t=600$ s, un cociente de $2.42$, con un coeficiente de variación del
    $3.1$%. La diferencia se atribuye a la percolación de primer paso: el
    mínimo de muchos caminos aleatorios tiene esperanza menor que el camino
    determinista. El efecto crece con el viento: el cociente pasa de $2.03$ a
    $2.54$ entre $U=0$ y $4$ m/s.],
  [*Verificación numérica.* Los integradores reproducen sus órdenes teóricos:
    Euler $1.00$, RK2 $2.01$, RK4 $4.01$. El MSD de Langevin crece con
    exponente $1.011$, y las distribuciones empíricas no se distinguen de la
    solución de Fokker--Planck ($p_"KS" > 0.26$). Euler-Cromer mantiene la
    energía del péndulo en $1.5$% frente al $490$% de Euler explícito, y RK4
    la reduce a $4.2 times 10^{-8}$. El péndulo y el problema de N cuerpos
    conservan la energía con derivas inferiores a $10^{-11}$ y $10^{-12}$,
    respectivamente. Los autómatas clásicos reproducen sus diagramas
    fundamentales.],
  [*Acondicionamiento.* El número de condición de la ROS respecto de la
    humedad crece de $0.45$ lejos de la extinción a $47.7$ en $M=0.245$. Cerca
    de $M_x$, un error del $1$% en la humedad puede amplificarse a un error
    del $48$% en la ROS. Las predicciones cercanas a la extinción deben
    reportarse con intervalos de incertidumbre.],
  [*Convergencia y sensibilidad.* La ROS converge con el refinamiento de malla
    ($8.3$% de error a $Delta x=10$ m, $4.3$% a $5$ m, $0$% a $1.25$ m) y con
    el paso temporal ($5.2$% a $Delta t=2$ s, $1.1$% a $1$ s). Las
    elasticidades locales son $1.22$ (viento), $0.77$ (pendiente), $-0.48$
    (humedad) y $-0.19$ (carga). El viento es el factor dominante, seguido de
    la pendiente.],
  [*Casos reales.* El simulador se aplicó a Acos (Cusco, 2025) y a Little
    Giant (Washington, 2026). En Acos, el área simulada fue $307.6$ ha frente a
    $296.9$ ha de la máscara de referencia ($300$ ha oficiales), un error del
    $3.6$%, aunque no hay perímetro para evaluar la forma. En Little Giant, la subventana de $4.4$ km produjo $1731$ ha frente
    a $1253$ ha observadas (error $38.2$%) y un IoU de $0.62$; el evento
    completo ($69\,975$ ha) excede la escala del modelo.],
  [*Reproducibilidad.* El código, las semillas, las tablas y las figuras se
    generan con `uv` y un único comando. Las pruebas unitarias cubren los
    módulos de combustible, terreno, AC, métricas y numerics. Todas las
    referencias incluyen DOI verificado y, cuando existe, versión de acceso
    abierto.],
)

La hipótesis H1 se confirma: la ROS es monótona con el viento y la pendiente y
no lineal con la humedad. H2 se confirma con alta precisión: los umbrales de
percolación coinciden con la teoría. H3 se confirma cualitativamente: el ruido
modifica el valor medio y la dispersión, y el efecto es sistemático. H4 se
confirma: los métodos numéricos reproducen sus órdenes y leyes de escala.

La principal contribución del trabajo es metodológica: un marco reproducible
que integra un modelo físico transparente, un análisis de percolación, una
comparación determinista--estocástica y una verificación numérica explícita. En
un contexto de creciente disponibilidad de datos y de herramientas de
aprendizaje automático, este tipo de modelo interpretable sigue siendo
necesario para formular hipótesis, diseñar experimentos y comunicar la
incertidumbre.

== Trabajo futuro

#enum(
  [*Paralelización y GPU.* El motor actual es vectorizado con NumPy, pero una
    implementación en GPU o con Numba permitiría simular dominios de decenas de
    kilómetros y ensembles de cientos de miembros en tiempos compatibles con la
    operación.],
  [*Asimilación de datos.* La combinación del AC con datos satelitales de
    temperatura y humedad, y con técnicas de filtro de partículas, permitiría
    calibrar la humedad y el viento en tiempo casi real @karakonstantis2026b.],
  [*Spotting y acoplamiento atmosférico.* Incorporar el transporte de pavesas
    como fuente secundaria de ignición y reemplazar el viento uniforme por un
    campo de viento resuelto o parametrizado por la topografía
    @mandel2011.],
  [*Modelos estocásticos más realistas.* Sustituir la hipótesis de Bernoulli
    independiente por un umbral aleatorio con correlación espacial o por un
    proceso de Hawkes, y comparar la estructura de los ensembles con
    observaciones.],
  [*Validación con eventos reales.* Aplicar el modelo a un incendio documentado
    (por ejemplo, Spetses 1990 o un evento peruano) con datos de combustible y
    meteorología, y evaluar la bondad de ajuste de la huella simulada.],
)
