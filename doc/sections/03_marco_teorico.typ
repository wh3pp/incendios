= Marco teórico

== Física de la propagación

=== El triángulo del fuego y la tasa de liberación de calor

La combustión requiere combustible, oxígeno y calor. En un incendio forestal,
el combustible es la materia vegetal seca; el oxígeno proviene del aire; y el
calor se transfiere por radiación, convección y contacto directo. La velocidad
a la que el frente avanza depende del balance entre el calor liberado por la
combustión y el calor necesario para elevar el combustible vecino hasta su
temperatura de ignición @rothermel1972. Byram introdujo la intensidad de línea
de fuego,
$ I_B = H w R, $
donde $H$ es el calor de combustión, $w$ la carga de combustible consumida por
unidad de área y $R$ la velocidad de propagación. Esta cantidad controla la
longitud de llama y la probabilidad de transición a fuego de copa.

=== Modelo de Rothermel

El modelo de Rothermel @rothermel1972 expresa la velocidad de propagación
superficial como
$ R = frac(I_R xi (1 + phi_w + phi_s), rho_b epsilon Q_"ig"), $
donde $I_R$ es la intensidad de reacción, $xi$ el factor de propagación,
$phi_w$ y $phi_s$ los factores de viento y pendiente, $rho_b$ la densidad
aparente del lecho, $epsilon$ la fracción de calor que se propaga y $Q_"ig"$ el
calor de preignición. La intensidad de reacción se calcula como
$ I_R = Gamma w_n h eta_M eta_S, $
con $Gamma$ la tasa de reacción óptima, $w_n$ la carga neta, $h$ el calor de
combustión, $eta_M$ el amortiguamiento por humedad y $eta_S$ el
amortiguamiento mineral. La tasa de reacción depende de la relación de
empaquetamiento $beta = rho_b/rho_p$ y de la relación óptima
$beta_{op} = 3.348 sigma^{-0.8189}$:
$ Gamma = Gamma_"max" (frac(beta, beta_{op}))^A exp(A(1 - frac(beta, beta_{op}))), $
donde $sigma$ es la relación superficie--volumen y
$A = 133 sigma^{-0.7913}$. El factor de propagación y la fracción de calor
son
$ xi = frac(exp((0.792 + 0.681 sqrt(sigma))(beta + 0.1)), 192 + 0.2595 sigma), quad epsilon = exp(-138/sigma). $
El calor de preignición se aproxima por $Q_"ig" = 250 + 1116 M$, con $M$ la
humedad del combustible. El amortiguamiento por humedad es el polinomio
$ eta_M = 1 - 2.59 r + 5.11 r^2 - 3.52 r^3, quad r = M/M_x, $
que se anula cuando $M = M_x$ (humedad de extinción). El amortiguamiento
mineral es $eta_S = 0.174 S_e^{-0.19}$, con $S_e = 0.01$.

Los factores de viento y pendiente son
$ phi_w = C U^B (frac(beta, beta_{op}))^{-E}, quad
  phi_s = 5.275 beta^{-0.3} tan^2 phi, $
donde $U$ es la velocidad del viento en ft/min, $phi$ el ángulo de la
pendiente y
$ C = 7.47 exp(-0.133 sigma^{0.55}), quad
  B = 0.02526 sigma^{0.54}, quad
  E = 0.715 exp(-3.59 times 10^{-4} sigma). $
En este trabajo las ecuaciones se evalúan internamente en el sistema
imperial original y el resultado se convierte a m/s. La Tabla
@tab:combustibles resume los cuatro modelos de combustible utilizados, basados
en la estandarización de Scott y Burgan @scott2005.

#figure(
  table(
    columns: (auto, auto, auto, auto, auto, auto, auto),
    align: center,
    stroke: 0.4pt,
    inset: 3.5pt,
    table.header(
      [Código], [Nombre], [$w_0$ (kg/m²)], [$sigma$ (1/m)], [$delta$ (m)], [$M_x$], [$tau_"res"$ (s)],
    ),
    [FM1], [Pasto corto], [0.166], [11483], [0.305], [0.12], [120],
    [FM4], [Matorral], [3.140], [6562], [1.829], [0.20], [300],
    [FM8], [Hojarasca], [1.680], [6562], [0.061], [0.30], [600],
    [FM10], [Bosque], [2.240], [6562], [0.305], [0.25], [600],
  ),
  caption: [Modelos de combustible estándar adaptados a un lecho único.],
) <tab:combustibles>

=== Correcciones direccionales y forma del frente

Rothermel calcula la velocidad en la dirección de máxima propagación. Para un
AC bidimensional se necesita la velocidad hacia cada vecino. En este trabajo se
adopta un kernel angular que combina la proyección del viento con una
reducción de la componente de espalda:
$ R(theta) = R_0 [1 + phi_w cos^8(theta - theta_w)] (1 + phi_s(theta)), $
donde $theta_w$ es la dirección del viento y $phi_s(theta)$ es el factor de
pendiente en la dirección $theta$. El exponente ocho produce un frente
alargado y reduce la propagación lateral excesiva que aparece con un kernel
cosenoidal simple. La componente de espalda se limita a una fracción
$f_b = 0.05$ de $R_0$. Este tipo de corrección es consistente con los modelos
elípticos de crecimiento de frentes y con las curvas de relación largo/ancho
de Anderson @anderson1983, aunque el exponente se calibró para
reproducir la morfología observada en el AC y no para un evento particular.

== Autómatas celulares

=== Definición formal

Un autómata celular es una tupla $(cal(L), S, cal(N), f)$ donde
$cal(L)$ es una retícula de celdas, $S$ un conjunto finito de estados,
$cal(N)$ una vecindad y $f$ una regla local de transición. En una retícula cuadrada bidimensional, la vecindad de von
Neumann está formada por los cuatro vecinos ortogonales, y la de Moore por los
ocho vecinos. La actualización puede ser sincrónica (todas las celdas se
actualizan con el estado del paso anterior) o asincrónica. La actualización
sincrónica es la más adecuada para la paralelización y para evitar sesgos de
orden.

En este trabajo cada celda $i$ tiene un estado
$ s_i in {0, 1, 2, 3}, $
que representa no quemado, combustionando, quemado e incombustible,
respectivamente. La regla de transición depende del estado de los vecinos, de
la velocidad direccional $R_{i arrow.r j}$ y de un umbral de ignición. La
actualización se realiza con doble búfer, de modo que el estado nuevo no
depende del orden de recorrido.

=== Regla 184 y modelo de Nagel--Schreckenberg

La regla 184 es un autómata elemental que modela partículas que avanzan si la
celda siguiente está vacía. Su regla booleana es
$ n_i(t+1) = n_{i-1}(t)[1 - n_i(t)] + n_i(t) n_{i+1}(t), $
y su diagrama fundamental es $J = min(rho, 1-rho)$. El modelo de
Nagel--Schreckenberg generaliza la idea para el tráfico: cada
vehículo acelera, respeta la distancia de seguridad y frena con probabilidad
$p$. A pesar de su simplicidad, reproduce transiciones de fase entre flujo
libre y congestionado. Estos dos modelos se usan en este trabajo como pruebas
de verificación del motor de AC: si el motor reproduce sus diagramas
fundamentales, la implementación de la vecindad y de la actualización
sincrónica es correcta.

=== Juego de la Vida

Las reglas elementales pueden generar comportamientos computacionalmente
complejos a partir de instrucciones muy simples. El Juego de la Vida de Conway
es un AC bidimensional con dos estados y vecindad de Moore. Una célula viva sobrevive si tiene dos o tres
vecinos vivos; una célula muerta nace si tiene exactamente tres vecinos vivos.
El glider es una estructura que se desplaza diagonalmente y se usa como prueba
de estabilidad y de propagación de patrones. En este trabajo se emplea como
prueba de regresión del motor bidimensional.

=== Autómatas celulares probabilísticos

En un AC probabilístico, la transición es una variable aleatoria. Para el
fuego se adopta
$ P("ignición"_i) = 1 - exp(-h_i), quad
  h_i = sum_{j in cal(N)(i)} frac(R_{j arrow.r i} Delta t, d_{j arrow.r i}), $
donde $d_{j arrow.r i}$ es la distancia entre centros de celdas y $R_{j arrow.r i}$ la
velocidad desde $j$ hacia $i$. La forma exponencial garantiza que $P in [0,1]$
y que, para $h$ pequeño, $P approx h$. En el modelo determinista se acumula la
exposición
$ H_i(t+Delta t) = H_i(t) e^{-Delta t/tau_c} + h_i(t), $
y se enciende la celda cuando $H_i >= 1$. El tiempo $tau_c$ es una escala de
enfriamiento; en la práctica se toma grande para que el modelo represente el
límite de exposición acumulada sin pérdidas. La comparación entre ambos
regímenes es el objeto de la sección de resultados.

== Percolación y conectividad

La percolación de sitio describe la formación de un cúmulo conexo que atraviesa
una red cuando cada sitio está ocupado con probabilidad $p$. Para la red
cuadrada, el umbral de percolación es $p_c approx 0.5927$ con vecindad de von
Neumann y $p_c approx 0.4073$ con vecindad de Moore @newman2000. Cerca del umbral, la probabilidad de que exista un cúmulo
atravesante sigue una curva sigmoidea cuya anchura escala como
$ L^{-1/nu}$, donde $L$ es el tamaño del sistema y $nu$ el exponente de
correlación. La longitud de correlación divergente hace que los sistemas
finitos muestren una transición suave, pero el punto de cruce converge a $p_c$
al aumentar $L$.

En un paisaje forestal, la ocupación $p$ representa la fracción de celdas con
combustible. Si $p < p_c$, el fuego queda confinado a cúmulos finitos; si
$p > p_c$, existe un camino conectado que permite que el incendio atraviese el
dominio. Este mecanismo explica por qué la fragmentación del hábitat puede
reducir la probabilidad de grandes incendios y por qué los modelos
de percolación son útiles para interpretar la respuesta del paisaje a la
sequía y a las prácticas de gestión.

== Herramientas numéricas

=== Aritmética de punto flotante

Los números reales se representan en precisión doble IEEE 754 con 52 bits de
mantisa y 11 bits de exponente. El redondeo introduce un error
relativo máximo $u = epsilon/2$, donde $epsilon approx 2.22 times 10^{-16}$ es
el épsilon de máquina. Para una operación $op in {+,-,times,div}$,
$ "fl"(a "op" b) = (a op b)(1 + delta), quad |delta| <= u. $
La cancelación catastrófica ocurre cuando se restan números casi iguales: el
error absoluto se conserva, pero el error relativo crece. Un ejemplo clásico es $(1-cos x)/x^2$ para $x$
pequeño, que puede reescribirse de forma estable como
$2 sin^2(x/2)/x^2$. El número de condición de una función $f$ en $x$ es
$ kappa_f(x) = | frac(x f'(x), f(x)) |, $
y mide cuánto se amplifica un error relativo en la entrada. En el modelo de
Rothermel, $kappa$ crece cuando $M arrow.r M_x$ porque $eta_M arrow.r 0$; esto hace que
las predicciones cerca de la extinción sean intrínsecamente sensibles a la
humedad.

=== Ecuaciones no lineales

Un ejemplo canónico de ecuación no lineal es la ecuación de van der Waals,
$ P = frac(R T, V-b) - frac(a, V^2), $
que corrige la ley de los gases ideales con un término de volumen excluido
$b$ y una atracción intermolecular $a$. En el punto crítico se
anulan la primera y la segunda derivada de la presión respecto del volumen,
$ frac(partial P, partial V) = 0, quad frac(partial^2 P, partial V^2) = 0, $
lo que permite obtener $V_c = 3b$, $P_c = a/(27b^2)$ y
$T_c = 8a/(27 R b)$. Este problema ilustra por qué los métodos de raíces son
necesarios: la ecuación es cúbica en $V$ y no tiene una solución algebraica
simple para todos los regímenes. Los umbrales de humedad y de viento del
modelo de fuego son, en el mismo sentido, raíces de ecuaciones no lineales. El
método de bisección mantiene un intervalo con cambio de signo y reduce el error
a la mitad en cada iteración:
$ |e_n| <= frac(b-a, 2^n). $
El método de falsa posición interpola linealmente y suele converger más rápido,
aunque puede estancarse; la variante de Illinois corrige ese problema. El
método de Newton--Raphson usa la derivada y, cerca de una raíz simple, converge
cuadráticamente:
$ e_{n+1} approx frac(f''(x^*), 2 f'(x^*)) e_n^2. $
El método de la secante aproxima la derivada con una diferencia dividida y
converge con orden $phi = (1+sqrt(5))/2 approx 1.618$.

=== Integradores de EDO

Para una ecuación $y' = f(t,y)$, el método de Euler explícito es
$ y_{n+1} = y_n + Delta t f(t_n, y_n), $
con error local $O(Delta t^2)$ y global $O(Delta t)$. El método de Runge--Kutta
de segundo orden (punto medio) y el de cuarto orden (RK4) combinan evaluaciones
intermedias para alcanzar órdenes globales dos y cuatro, respectivamente.
Para sistemas de segundo orden, como el péndulo o un oscilador,
el método de Euler-Cromer actualiza primero la velocidad y luego la posición
con la velocidad nueva:
$ v_{n+1} = v_n + Delta t a(x_n, v_n), quad x_{n+1} = x_n + Delta t v_{n+1}. $
Este esquema es simpléctico y evita la deriva sistemática de energía del Euler
explícito, a un costo computacional similar. RK4 es el estándar de facto para
problemas no rígidos por su buena relación precisión/costo. En el problema de
N cuerpos, la conservación de la energía es un indicador de calidad: un
integrador simpléctico conserva mejor la energía a largo plazo, pero RK4 con
paso pequeño mantiene una deriva aceptable para tiempos cortos.

=== Ecuaciones diferenciales estocásticas

Una EDE de Itô se escribe
$ d X_t = a(t,X_t) d t + b(t,X_t) d W_t, $
donde $W_t$ es un movimiento browniano. El esquema de Euler--Maruyama es
$ X_{n+1} = X_n + a(t_n,X_n) Delta t + b(t_n,X_n) sqrt(Delta t) Z_n, $
con $Z_n ~ cal(N)(0,1)$. Tiene orden fuerte $1/2$ y orden
débil $1$. Para el movimiento browniano libre, $d X = sigma d W$, la solución es
$X_t ~ cal(N)(0, sigma^2 t)$ y el desplazamiento cuadrático medio es
$ "MSD"(t) = ⟨ (X_t-X_0)^2 ⟩ = sigma^2 t. $
El movimiento browniano fue explicado por Einstein en 1905 como consecuencia
del movimiento térmico de las moléculas @einstein1905. La densidad de
probabilidad satisface la ecuación de Fokker--Planck
$ frac(partial p, partial t) = -frac(partial, partial x)(a p) + frac(1,2) frac(partial^2, partial x^2)(b^2 p), $
cuya solución fundamental para deriva y difusión constantes es una gaussiana.
En este trabajo se usa esta solución para verificar el generador
de trayectorias y, por analogía, para interpretar la dispersión del frente de
fuego como un proceso de difusión con deriva.

=== Monte Carlo y propagación de incertidumbre

Un ensemble Monte Carlo consiste en $N$ realizaciones independientes del modelo,
cada una con una semilla distinta. La media y la desviación estándar de una
salida $Y$ se estiman como
$ hat{mu} = frac(1,N) sum_{k=1}^N Y_k, quad
  hat{sigma} = sqrt(frac(1,N-1) sum_{k=1}^N (Y_k - hat{mu})^2). $
El error estándar de la media decrece como $hat{sigma}/sqrt(N)$, de modo que
cuadruplicar el número de realizaciones reduce a la mitad la incertidumbre
estadística. El coeficiente de variación $"CV" = hat{sigma}/hat{mu}$ permite
comparar la dispersión entre escenarios con medias distintas.

== Análisis dimensional y números adimensionales

La propagación de un frente está controlada por la competencia entre la
flotabilidad, la inercia y la transferencia de calor. El número de Froude
$"Fr" = U/sqrt(g L)$ compara la velocidad del viento con la velocidad de las
ondas de gravedad; el número de Reynolds $"Re" = U L/nu$ compara la inercia con
la viscosidad; y la intensidad de Byram $I_B$ caracteriza la potencia por
unidad de longitud del frente. En modelos de fuego, la longitud de llama
$L_f$ se correlaciona con $I_B$ mediante leyes de potencia, y la relación
$L_f/H$ controla la transición a fuego de copa. Aunque este trabajo no resuelve
la dinámica de la llama, estas magnitudes permiten interpretar los órdenes de
magnitud y comparar los resultados con la literatura @sullivan2009a.
