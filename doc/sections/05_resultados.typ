#import "../tablas.typ": *

= Resultados

== Verificación numérica

Antes de interpretar las simulaciones de fuego, se verificó que las
herramientas numéricas utilizadas reproducen los comportamientos teóricos
esperados. Esta sección responde a la pregunta de investigación 5 y
proporciona la base de confianza para las secciones siguientes.

=== Punto flotante y acondicionamiento

La @tab:punto_flotante muestra experimentos elementales de aritmética
IEEE 754. El épsilon de máquina obtenido por bisección es
$2.220446049250313 times 10^{-16}$, idéntico al valor de `numpy.finfo(float).eps`.
La suma $0.1+0.2$ produce $0.30000000000000004$, un error absoluto de
$5.55 times 10^{-17}$; la resta posterior $(0.1+0.2)-0.3$ deja un residuo del
mismo orden. El caso $10^{16}+1-10^{16}$ devuelve $0$ en lugar de $1$: la
unidad es menor que la mitad del espaciado de la representación en esa escala,
por lo que se pierde por completo. El ejemplo de cancelación
$(1-cos x)/x^2$ con $x=10^{-8}$ devuelve $0$ en la forma ingenua, mientras que
la forma estable $2 sin^2(x/2)/x^2$ devuelve $0.5$; el error relativo es del
$100$%.

#figure(tabla_punto_flotante(), caption: [Experimentos de aritmética de punto flotante en doble precisión.]) <tab:punto_flotante>

El número de condición del modelo de Rothermel respecto de la humedad se
muestra en la @tab:condicionamiento. Lejos de la extinción,
$kappa approx 0.45$; al acercarse a $M_x$, $kappa$ crece hasta $47.7$ en
$M=0.245$. Esto significa que un error relativo del $1$% en la humedad se
amplifica a un error del $48$% en la ROS. Cerca de la extinción, el modelo es
intrínsecamente mal condicionado, y las predicciones deben interpretarse con
cautela. Este resultado justifica el uso de métodos robustos de raíces y de
tolerancias explícitas en la calibración.

#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: center,
    stroke: 0.4pt,
    inset: 4pt,
    table.header([$M$], [$eta_M$], [$kappa_{eta}$], [$kappa_R$]),
    [0.050], [0.658], [0.294], [0.477],
    [0.100], [0.556], [0.138], [0.446],
    [0.150], [0.525], [0.297], [0.698],
    [0.200], [0.396], [2.368], [2.839],
    [0.230], [0.201], [9.713], [10.220],
    [0.240], [0.109], [22.174], [22.691],
    [0.245], [0.056], [47.157], [47.679],
  ),
  caption: [Número de condición del amortiguamiento por humedad y de la ROS base para FM10 ($M_x=0.25$).],
) <tab:condicionamiento>

=== Ecuaciones no lineales

El problema aplicado consiste en encontrar la humedad $M^*$ tal que la ROS
base sea la mitad de la ROS a $M=0.05$. La raíz de referencia es
$M^* = 0.17616184$. La @tab:raices compara los cuatro métodos. La
bisección requiere $39$ iteraciones para alcanzar un error de
$2.3 times 10^{-13}$; la falsa posición con corrección de Illinois converge en
$7$ iteraciones; Newton--Raphson en $5$; y la secante en $6$. La @fig:numericos(a) muestra la historia de convergencia: Newton y la secante
caen abruptamente, mientras la bisección lo hace de forma lineal. El orden
observado de la secante, $1.57$, es consistente con el valor teórico
$1.618$; el de Newton no se estima de forma fiable porque alcanza la precisión
de máquina en pocas iteraciones. En términos prácticos, Newton--Raphson es el
método más eficiente cuando se dispone de la derivada; la falsa posición es una
buena alternativa si solo se dispone de evaluaciones de la función.

#figure(tabla_raices(), caption: [Comparación de métodos de raíces para el umbral de humedad de FM10.]) <tab:raices>

=== Integradores de EDO y transporte de pavesas

La @tab:edo y la @fig:numericos(b) muestran la convergencia de
Euler, RK2 y RK4 en la caída vertical con arrastre cuadrático, cuya solución
analítica es $v(t) = v_t tanh(g t/v_t)$ con $v_t = sqrt(g/k)$. Los órdenes
observados son $1.00$, $2.01$ y $4.01$, respectivamente, en excelente acuerdo
con la teoría. Para $Delta t = 0.025$ s, el error de Euler es
$3.6 times 10^{-2}$ m/s, el de RK2 $1.1 times 10^{-4}$ m/s y el de RK4
$1.6 times 10^{-9}$ m/s: RK4 es aproximadamente siete órdenes de magnitud más
preciso que Euler con el mismo paso.

#figure(tabla_edo(), caption: [Error y orden observado de los integradores en la caída con arrastre cuadrático.]) <tab:edo>

Para el proyectil bidimensional se usó RK4, ya que la comparación de métodos
se realizó en la caída vertical, donde se dispone de solución analítica. El
mismo integrador RK4 se aplicó al transporte de pavesas (firebrands) con
arrastre cuadrático y viento. La @fig:pavesas muestra que, para una
partícula lanzada desde $60$ m de altura con velocidad inicial $6$ m/s y
ángulo $30$°, el alcance pasa de $11$ m sin viento a $71$ m con $16$ m/s. La
trayectoria se curva gradualmente y el alcance crece de forma casi lineal con
el viento en el rango estudiado. Este resultado es una verificación cualitativa
del integrador y, al mismo tiempo, una estimación del orden de magnitud del
transporte de pavesas; no reemplaza un modelo de spotting con combustión y
turbulencia.

#figure(
  image("../assets/figures/pavesas.pdf", width: 100%),
  caption: [Trayectorias de pavesas con arrastre cuadrático (a) y distancia de transporte en función del viento (b).],
) <fig:pavesas>

=== Péndulo no lineal y problema de N cuerpos

La @tab:pendulo compara el período numérico del péndulo simple con el
período exacto obtenido de la integral elíptica. Para amplitudes de $0.05$ a
$2.5$ rad, el error relativo es inferior a $3 times 10^{-4}$ y la deriva
máxima de energía es del orden de $10^{-13}$. La @tab:nbody muestra la
deriva relativa de energía del problema de tres cuerpos en figura ocho: con
$Delta t = 0.02$ es $7.5 times 10^{-8}$, y con $Delta t = 0.0025$ baja a
$5.6 times 10^{-12}$. La reducción es consistente con el orden cuatro de RK4.
Estos resultados confirman que el integrador es adecuado para los términos de
transporte y para las verificaciones de conservación.

#figure(tabla_pendulo(), caption: [Período del péndulo no lineal: RK4 frente a la solución exacta.]) <tab:pendulo>

La comparación entre Euler explícito, Euler-Cromer y RK4 se muestra en la
@tab:euler_cromer para $20$ períodos de un péndulo con amplitud $1$ rad
y $Delta t=0.01$ s. El Euler explícito pierde la estabilidad energética: la
deriva máxima es del $490$%. Euler-Cromer, al actualizar la posición con la
velocidad nueva, mantiene la deriva en $1.5$% y el error final en
$1.4 times 10^{-4}$; RK4, con el mismo paso, la reduce a $4.2 times 10^{-8}$.
Este resultado justifica el uso de integradores simplécticos o de alto orden
para osciladores y para el transporte de pavesas.

#figure(tabla_euler_cromer(), caption: [Deriva de energía del péndulo no lineal con Euler, Euler-Cromer y RK4 ($20$ períodos).]) <tab:euler_cromer>

#figure(tabla_nbody(), caption: [Deriva relativa de energía en el problema de tres cuerpos en figura ocho con RK4.]) <tab:nbody>

=== Ecuaciones diferenciales estocásticas

La @tab:sde compara la media y la desviación estándar de $5000$
trayectorias de Langevin con la solución exacta de Fokker--Planck en $t=1,2,5$
s. Las medias empíricas son $0.503$, $1.004$ y $2.504$ frente a $0.5$, $1.0$ y
$2.5$; las desviaciones son $0.201$, $0.283$ y $0.447$ frente a $0.200$,
$0.283$ y $0.447$. Los valores $p$ de Kolmogorov--Smirnov son $0.26$, $0.51$ y
$0.93$, todos superiores a $0.05$, por lo que no se rechaza la hipótesis de que
las muestras provienen de la distribución gaussiana exacta. La @fig:numericos(c) muestra que el MSD crece linealmente con el tiempo; el
exponente ajustado es $1.011$, consistente con la difusión normal. La @fig:numericos(d) superpone el histograma de Langevin y la densidad de
Fokker--Planck en $t=5$ s.

#figure(tabla_sde(), caption: [Comparación entre la simulación de Langevin y la solución de Fokker--Planck.]) <tab:sde>

=== Autómatas celulares clásicos

La @fig:automatas muestra la verificación del motor de AC. La regla 184
reproduce el diagrama fundamental $J = min(rho,1-rho)$ con un error máximo
del orden de $0.03$ en el rango
$rho in [0.05,0.95]$. El modelo de Nagel--Schreckenberg reproduce la transición
de flujo libre a congestionado: para $p=0$ el flujo máximo es $0.77$ a
$rho approx 0.25$; para $p=0.25$ baja a $0.52$; y para $p=0.5$ a $0.30$. El
Juego de la Vida reproduce el movimiento del glider sin cambios de forma. Estos
resultados confirman que la vecindad, la actualización sincrónica y el manejo de
bordes del motor son correctos.

#figure(
  image("../assets/figures/automatas.pdf", width: 100%),
  caption: [Verificación del motor de autómatas: (a) diagrama espacio-temporal de la regla 184; (b) diagrama fundamental; (c) diagramas fundamentales de Nagel--Schreckenberg.],
) <fig:automatas>

#figure(
  image("../assets/figures/game_of_life.pdf", width: 72%),
  caption: [Evolución del glider del Juego de la Vida en una malla de $24 times 24$; se muestran cuatro instantes.],
) <fig:life>

#figure(
  image("../assets/figures/numericos.pdf", width: 100%),
  caption: [Verificación numérica: (a) convergencia de los métodos de raíces; (b) convergencia de Euler, RK2 y RK4; (c) MSD del movimiento browniano; (d) densidad de Fokker--Planck frente al histograma de Langevin.],
) <fig:numericos>

== Escenario base

La @fig:terreno muestra el terreno sintético de $256 times 256$ celdas
($1.28$ km de lado) utilizado como escenario base. La elevación varía entre
$12$ y $68$ m, con una pendiente media de $0.25$ ($14$°); la fracción
combustible es $95.2$%; la humedad media es $0.097$ y la densidad de
vegetación media $0.713$. El paisaje contiene lagos y parches de roca expuesta
que actúan como barreras locales.

#figure(
  image("../assets/figures/terreno.pdf", width: 100%),
  caption: [Terreno sintético del escenario base: (a) elevación; (b) modelos de combustible; (c) humedad; (d) densidad de vegetación.],
) <fig:terreno>

La @fig:base muestra la evolución del incendio para $t=0$, $300$ y $600$ s,
y la @fig:llegada muestra el tiempo de llegada del frente. El fuego se
inicia en el centro y se propaga preferentemente hacia la derecha, con
ramificaciones laterales asociadas a parches de matorral y a la pendiente. A
$t=900$ s, el área quemada es de $21.13$ ha, el $12.9$% del dominio; la ROS de
cabeza es $64.8$ m/min ($1.08$ m/s), la relación largo/ancho $1.85$, la
dimensión fractal $1.82$ y la rugosidad del frente $218$ s. La diferencia entre
la ROS de llegada ($64.8$ m/min) y la ROS del ajuste global ($36.4$ m/min)
refleja la heterogeneidad: el frente local avanza más rápido que el promedio
del área quemada.

#figure(
  image("../assets/figures/escenario_base.pdf", width: 100%),
  caption: [Estados del autómata determinista en el escenario base para $t=0$, $300$ y $600$ s.],
) <fig:base>

#figure(
  image("../assets/figures/tiempo_llegada.pdf", width: 72%),
  caption: [Tiempo de llegada del frente en el escenario base.],
) <fig:llegada>

#figure(tabla_escenario(), caption: [Métricas del escenario base a $t=900$ s.]) <tab:escenario>

== Efecto del viento

La @fig:viento y la @tab:viento muestran el barrido de viento sobre
un terreno homogéneo de FM10, con humedad $0.07$ y $t=900$ s. La ROS de cabeza
crece de $2.40$ m/min sin viento a $31.98$ m/min con $8$ m/s, un factor de
$13.3$. La relación largo/ancho crece de $1.00$ a $4.38$; el área quemada pasa
de $0.48$ a $5.48$ ha. El crecimiento de la ROS es aproximadamente lineal para
$U < 4$ m/s y se acelera ligeramente a partir de ahí, consistente con el
carácter no lineal de $phi_w$. La relación largo/ancho satura alrededor de
$4.4$, un valor inferior al que predice la fórmula de Anderson para vientos
fuertes; esto se debe al kernel angular y a la resolución finita de la malla.

#figure(
  image("../assets/figures/barrido_viento.pdf", width: 100%),
  caption: [Efecto del viento sobre la ROS de cabeza (a) y la relación largo/ancho (b) en FM10.],
) <fig:viento>

#figure(tabla_viento(), caption: [Barrido de viento en FM10: ROS, área quemada, relación largo/ancho y dimensión fractal.]) <tab:viento>

== Efecto de la humedad

La @fig:humedad y la @tab:humedad muestran la ROS en función de la
humedad para FM10 sin viento. La ROS disminuye de $3.81$ m/min a $M=0.03$ hasta
$1.03$ m/min a $M=0.18$; para $M=0.21$ y $M=0.24$ el fuego no se propaga más
allá de la ignición. La transición es abrupta entre $0.18$ y $0.21$, aunque la
humedad de extinción del modelo es $M_x=0.25$. Este adelantamiento del umbral
efectivo se debe a la competencia entre la baja ROS y el tiempo de residencia
finito: si la celda no alcanza la exposición crítica antes de que sus vecinos
se apaguen, el frente se detiene. El resultado es consistente con la reducción
no lineal de la ROS observada en la literatura y con la extinción anticipada
respecto de $M_x$.

#figure(
  image("../assets/figures/barrido_humedad.pdf", width: 72%),
  caption: [ROS de cabeza en función de la humedad para FM10 sin viento. La línea vertical indica $M_x=0.25$.],
) <fig:humedad>

#figure(tabla_humedad(), caption: [Barrido de humedad en FM10: ROS, área quemada y avance del frente.]) <tab:humedad>

== Efecto de la pendiente

La @fig:pendiente y la @tab:pendiente muestran el efecto de una
pendiente uniforme en la dirección $+x$, sin viento. La ROS crece de
$2.40$ m/min en terreno plano a $16.35$ m/min con $31$° de pendiente, un factor
de $6.8$. La relación largo/ancho crece de $1.00$ a $1.58$. El crecimiento es
más que lineal: al duplicar la pendiente de $15$° a $31$°, la ROS se
multiplica por $2.8$. Este comportamiento es consistente con la dependencia
cuadrática de $phi_s$ en $tan phi$ y con los estudios numéricos de viento y
pendiente @hayajneh2025.

#figure(
  image("../assets/figures/barrido_pendiente.pdf", width: 100%),
  caption: [Efecto de la pendiente sobre la ROS de cabeza (a) y la relación largo/ancho (b) en FM10 sin viento.],
) <fig:pendiente>

#figure(tabla_pendiente(), caption: [Barrido de pendiente en FM10: ROS, área quemada y relación largo/ancho.]) <tab:pendiente>

== Conectividad y percolación

La @fig:percolacion y la @tab:percolacion muestran la probabilidad de
percolación en función de la ocupación del paisaje para las vecindades de von
Neumann y Moore. Con vecindad de von Neumann, la transición ocurre entre
$p=0.55$ y $p=0.65$, con un umbral ajustado de $p_c = 0.5907$; con vecindad de
Moore, entre $p=0.35$ y $p=0.45$, con $p_c = 0.4084$. Los valores teóricos son
$0.5927$ y $0.4073$, respectivamente @newman2000. Las
diferencias son de $0.002$ y $0.001$, del orden de la incertidumbre estadística
para $80$ realizaciones y $L=64$. Este resultado es una validación fuerte del
motor de propagación y de la implementación de la vecindad.

#figure(
  image("../assets/figures/percolacion.pdf", width: 78%),
  caption: [Probabilidad de percolación en función de la ocupación para las vecindades de von Neumann (4) y Moore (8). Las líneas punteadas indican los umbrales teóricos.],
) <fig:percolacion>

#figure(tabla_percolacion(), caption: [Probabilidad de percolación para ocupaciones seleccionadas.]) <tab:percolacion>

== Comparación determinista--estocástica

La @fig:comparacion y la @tab:comparacion comparan el modelo
determinista con un ensemble de $32$ realizaciones del modelo probabilístico en
el mismo terreno, con $U=4$ m/s y $t=600$ s. El área media del ensemble es
$24.89$ ha, frente a $10.28$ ha del modelo determinista; el cociente es $2.42$.
La ROS media estimada con el ajuste global es $35.3$ m/min en el ensemble y
$42.2$ m/min en el determinista; por tanto, el aumento de área no proviene de
una mayor velocidad axial, sino de un frente más ancho y de igniciones
tempranas en los flancos. El coeficiente de variación del área es $3.1$%. La
relación largo/ancho baja de $1.87$ a $1.34$, y la dimensión fractal sube
ligeramente de $1.79$ a $1.82$; la rugosidad del frente disminuye de $136$ a
$124$ s.

#figure(
  image("../assets/figures/det_vs_estocastico.pdf", width: 100%),
  caption: [Comparación determinista--estocástica: (a) área quemada en función del tiempo; (b) probabilidad de quema a $t=400$ s; (c) distribución del área final del ensemble.],
) <fig:comparacion>

#figure(tabla_comparacion(), caption: [Comparación de métricas globales entre el modelo determinista y el ensemble estocástico.]) <tab:comparacion>

#figure(
  table(
    columns: (auto, auto, auto, auto, auto),
    align: center,
    stroke: 0.4pt,
    inset: 4pt,
    table.header([$U$ (m/s)], [Área det. (celdas)], [Área estoc. (celdas)], [$sigma$ (celdas)], [Cociente]),
    [0], [638], [1296.5], [194.0], [2.03],
    [1], [677], [1408.9], [221.6], [2.08],
    [2], [698], [1636.3], [242.2], [2.34],
    [3], [710], [1752.5], [245.7], [2.47],
    [4], [727], [1847.0], [237.7], [2.54],
  ),
  caption: [Cociente entre el área media del ensemble y el área determinista en función del viento (8 realizaciones, $t=600$ s).],
) <tab:mejora>

La diferencia sistemática merece una explicación. En el modelo determinista, una
celda se enciende cuando la exposición acumulada alcanza exactamente uno; en el
modelo probabilístico, la ignición es un proceso de Poisson con tasa $h_i$, de
modo que algunas celdas se encienden antes del tiempo medio. En una retícula
bidimensional, el frente puede aprovechar muchos caminos alternativos; el
tiempo de llegada es el mínimo sobre un conjunto exponencial de caminos, y
$E[min_k T_k] < min_k E[T_k]$ por la desigualdad de Jensen. Este efecto de
_percolación de primer paso_ explica por qué el ensemble se adelanta y por qué
la diferencia crece con el viento: a mayor viento, mayor contraste entre la
cabeza y los flancos, y mayor es el número de caminos que compiten. En un
experimento auxiliar con $U=0,1,2,3,4$ m/s (@tab:mejora), el cociente de
áreas creció de $2.03$ a $2.54$, lo que confirma que el efecto se intensifica
con la anisotropía del frente.

El coeficiente de variación del $3.1$% indica que, para un dominio de
$800 times 800$ m y $32$ realizaciones, la dispersión del área global es
pequeña; la incertidumbre se concentra en la posición del frente, como muestra
el mapa de probabilidad de la @fig:comparacion(b). Este resultado es
consistente con ensembles previos, donde la dispersión aumenta con la
variabilidad del viento y de la humedad, pero se reduce al promediar dominios
grandes.

== Convergencia y sensibilidad

La @fig:convergencia y las tablas correspondientes (@tab:conv_esp y @tab:conv_temp) muestran
la convergencia espacial y temporal. Al refinar la malla de $10$ a $1.25$ m, la
ROS converge de $12.50$ a $13.64$ m/min; el error relativo respecto de la malla
más fina baja de $8.3$% a $4.3$% y luego a cero. El orden observado es
aproximadamente uno, consistente con un esquema de primer orden en el
tratamiento de la interfaz. Al refinar el paso temporal de $2$ a $0.125$ s, la
ROS converge de $12.50$ a $13.19$ m/min, con un error que baja de $5.2$% a
$1.1$% y luego a cero. La convergencia temporal es más rápida que la espacial,
lo que sugiere que el error dominante es la discretización espacial.

#figure(
  image("../assets/figures/convergencia_espacial.pdf", width: 100%),
  caption: [Convergencia espacial de la ROS (a) y error relativo frente a la malla más fina (b).],
) <fig:convergencia>

#figure(tabla_convergencia_espacial(), caption: [Convergencia espacial de la ROS con ignición de línea.]) <tab:conv_esp>

#figure(tabla_convergencia_temporal(), caption: [Convergencia temporal de la ROS con $Delta x = 5$ m.]) <tab:conv_temp>

La @fig:sensibilidad y la @tab:sensibilidad muestran las
elasticidades locales de la ROS respecto de cuatro parámetros, obtenidas con un
diseño OAT (one-at-a-time) y un ajuste log--log. El viento es el parámetro más
influyente ($epsilon = 1.22$), seguido de la pendiente ($0.77$), la humedad
($-0.48$) y la carga de combustible ($-0.19$). El signo negativo de la carga
puede sorprender: en el modelo de Rothermel, aumentar la carga sin cambiar la
profundidad incrementa la relación de empaquetamiento y reduce la tasa de
reacción, un efecto que domina sobre el aumento de combustible disponible. Este
resultado es coherente con la formulación y sugiere que la carga y la
profundidad del lecho deben calibrarse conjuntamente.

#figure(
  image("../assets/figures/sensibilidad.pdf", width: 62%),
  caption: [Elasticidad de la ROS respecto del viento, la pendiente, la humedad y la carga de combustible.],
) <fig:sensibilidad>

#figure(tabla_sensibilidad(), caption: [Elasticidades locales de la ROS.]) <tab:sensibilidad>

== Comparación con la literatura

La @tab:validacion contrasta los resultados del modelo con rangos
reportados en la literatura. La ROS de pasto y matorral cae dentro de los
rangos observados para incendios de superficie; la ROS de hojarasca es algo
elevada con vientos fuertes, pero del mismo orden. La relación largo/ancho
sigue la tendencia de Anderson @anderson1983, aunque satura antes. Los umbrales
de percolación coinciden con los valores teóricos. El alcance de las pavesas es
del orden de decenas de metros, en el extremo inferior de los rangos reportados
para spotting, lo que refleja la ausencia de una columna convectiva y de un
modelo de combustión de la pavesa.

#figure(
  table(
    columns: (1.2fr, 1.6fr, 1.5fr, 1.4fr),
    align: (left, left, left, left),
    stroke: 0.4pt,
    inset: 4pt,
    table.header([Variable], [Literatura], [Este modelo], [Fuente]),
    [ROS pasto], [$0.1$--$3$ m/s], [$0.5$--$1.0$ m/s (4--8 m/s)], [@sullivan2009a],
    [ROS hojarasca], [$0.01$--$0.1$ m/s], [$0.04$--$0.53$ m/s], [@andrews2018],
    [Relación largo/ancho], [$1$--$5$], [$1.0$--$4.4$], [@anderson1983],
    [Percolación 4N], [$0.5927$], [$0.5907$], [@newman2000],
    [Percolación 8N], [$0.4073$], [$0.4084$], [@newman2000],
    [Intensidad de Byram], [depende del combustible], [no calculada], [@sullivan2009a],
  ),
  caption: [Comparación cualitativa con rangos de la literatura.],
) <tab:validacion>

== Rendimiento computacional

La @tab:rendimiento muestra el tiempo de pared por cada $100$ pasos
temporales en una CPU de escritorio, para el modelo determinista y el
estocástico. El costo escala aproximadamente como $N^2$, como es de esperar
para una actualización de vecindad sobre una malla cuadrada. Para $N=512$, el
modelo determinista tarda $3.78$ s por $100$ pasos, de modo que una simulación
de $1800$ s ($1800$ pasos) requiere alrededor de $68$ s. El modelo estocástico
es más costoso porque debe generar números aleatorios y procesar solo las
celdas activas; para $N=256$ tarda $1.14$ s por $100$ pasos. La vectorización
con NumPy y el uso de listas activas mantienen el costo dentro de límites
razonables para una campaña de decenas de simulaciones; una implementación en
GPU permitiría reducir el tiempo en uno o dos órdenes de magnitud.

#figure(tabla_rendimiento(), caption: [Tiempo de pared por $100$ pasos y memoria de trabajo estimada.]) <tab:rendimiento>
