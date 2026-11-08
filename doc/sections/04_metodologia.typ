= Metodología

== Diseño general del modelo

El simulador representa un paisaje forestal como una retícula cuadrada de
$N times N$ celdas de lado $Delta x$. Cada celda $i$ almacena un estado
$s_i in {0,1,2,3}$ (no quemado, combustionando, quemado, incombustible), un
tipo de combustible, una humedad $M_i$, una carga de combustible $w_i$, una
pendiente local $(partial z/partial x, partial z/partial y)$ y un tiempo de
residencia $tau_i$. La vecindad es de Moore (ocho vecinos), lo que permite
representar direcciones diagonales y reduce la anisotropía de la retícula
cuadrada en comparación con la vecindad de von Neumann.

La actualización es sincrónica y utiliza doble búfer: el estado nuevo se
calcula a partir del estado del paso anterior, de modo que el resultado no
depende del orden de recorrido. El paso temporal $Delta t$ se elige para
satisfacer una condición de tipo CFL,
$ frac(R_"max" Delta t, Delta x) <= 1, $
donde $R_"max"$ es la velocidad máxima permitida. En la práctica se usa
$Delta t = 1$ s, $Delta x = 5$ m y $R_"max" = 2.5$ m/s, lo que deja un margen
amplio. La ignición inicial es un bloque de $3 times 3$ celdas en el centro
del dominio, o una línea en el borde izquierdo para los experimentos de
convergencia y percolación.

== Generación del terreno heterogéneo

=== Ruido fractal espectral

La elevación y la cobertura vegetal se generan mediante síntesis espectral de
ruido fractal gaussiano. Se construye un campo complejo aleatorio
$hat{eta}(bold(k))$ y se filtra con una ley de potencia
$ S(k) prop |bold(k)|^{-beta}, $
de modo que el campo resultante tenga estructura en múltiples escalas. Para la
elevación se usa $beta = 2.8$; para la cobertura, $beta = 2.3$. El campo se
normaliza, se suaviza con un filtro gaussiano y se escala a un rango de
elevación de $0$ a $80$ m. La componente de pendiente se obtiene de los
gradientes centrales:
$ frac(partial z, partial x) = frac(z_{i,j+1}-z_{i,j-1},2 Delta x), quad
  frac(partial z, partial y) = -frac(z_{i+1,j}-z_{i-1,j},2 Delta x), $
donde el signo negativo de la segunda expresión corrige la orientación de las
filas de la imagen.

=== Modelos de combustible y humedad

La cobertura vegetal se discretiza en cuatro clases mediante umbrales de
cuantiles: pasto (FM1), matorral (FM4), hojarasca (FM8) y bosque (FM10). Las
propiedades de cada clase se resumen en la @tab:combustibles. La carga
local se modula por un factor $f_w = 0.55 + 0.90, rho_v$, donde $rho_v$ es la
densidad de vegetación, y se recorta a $[0.35, 1.45]$. La humedad se genera
como
$ M_i = M_0 + 0.06(1 - rho_{v,i}) + 0.015, epsilon_i - 1.5 times 10^{-4}(z_i - bar{z}), $
donde $epsilon_i$ es ruido gaussiano y $bar{z}$ la elevación media. La humedad
se recorta al $95$% de la humedad de extinción de cada celda, de modo que
ninguna celda combustible tenga $M_i >= M_{x,i}$. Las celdas con elevación
inferior al cuantil $3.5$% se consideran lago; las pendientes superiores a
$1.35$ se consideran roca expuesta; y, opcionalmente, se añade un río
sinusoidal incombustible.

=== Viento y condiciones de contorno

El viento se prescribe como un vector uniforme $(U, theta_w)$. En los
experimentos de barrido se varía $U$ de $0$ a $8$ m/s y se mantiene
$theta_w = 0$ (dirección $+x$). Las condiciones de contorno son abiertas: el
fuego puede abandonar el dominio, pero no se reinyecta. Las celdas
incombustibles actúan como barreras; el fuego puede rodearlas, pero no
atravesarlas. No se modela el acoplamiento con la atmósfera ni la turbulencia;
el viento es un forzamiento externo.

== Velocidad de propagación direccional

La velocidad base $R_0$ se calcula con las ecuaciones de Rothermel
(Sec. 3.1.2) para cada celda, usando su carga, su relación superficie--volumen,
su profundidad, su humedad y su humedad de extinción. Luego se calcula la
velocidad hacia los ocho vecinos como
$ R_{i arrow.r j} = R_{0,i} [1 + f_w phi_w(U) cos^8(theta_{i j}-theta_w)] [1 + phi_s(theta_{i j})], $
donde $f_w = 0.30$ es un factor de eficiencia del viento calibrado para
reproducir ROS plausibles, y $phi_s$ se evalúa con la componente de pendiente
en la dirección del vecino. La velocidad se recorta a $R_"max" = 2.5$ m/s. La
componente de espalda se limita a $0.05 R_0$ para evitar que el fuego avance
aguas arriba a la misma velocidad que en ausencia de viento.

La elección del exponente ocho merece una justificación. Un kernel
cosenoidal simple produce frentes demasiado anchos, porque la proyección del
viento sobre las diagonales sigue siendo grande. El exponente ocho concentra
la ganancia de velocidad en un cono estrecho alrededor de la dirección del
viento, lo que reproduce cualitativamente la forma elíptica observada en
incendios impulsados por viento @anderson1983. El valor se
seleccionó por prueba y error sobre simulaciones homogéneas, comparando la
relación largo/ancho con los rangos reportados por Anderson @anderson1983. No
se realizó una calibración formal con datos de campo; esta es una limitación
explícita del modelo.

== Modelo determinista

El modelo determinista acumula una exposición térmica $H_i$ en cada celda no
quemada. En cada paso,
$ H_i(t+Delta t) = H_i(t) e^{-Delta t/tau_c} + sum_{j in cal(N)(i)} frac(R_{j arrow.r i} Delta t, d_{j arrow.r i}), $
donde $tau_c$ es una escala de enfriamiento. Una celda se enciende cuando
$H_i >= 1$. El término de enfriamiento representa la pérdida de calor por
radiación y convección; en las simulaciones principales se toma
$tau_c = 10^9$ s para que el modelo sea el límite de exposición acumulada sin
pérdidas, y así compararlo de forma justa con el modelo estocástico. El
algoritmo se resume en el @alg:det.

#figure(
  raw(
    block: true,
    lang: "text",
    "ALGORITMO 1: AC determinista
Entrada: terreno, ignición, Δt, t_fin
1: estado ← no_quemado para celdas combustibles; incombustible en el resto
2: H ← 0; t ← 0; estado[ignición] ← combustionando
3: mientras t < t_fin:
4:   para cada dirección k ∈ {E, NE, N, NW, W, SW, S, SE}:
5:     H ← H + desplazar(R_k · Δt / d_k · [estado = combustionando])
6:   H ← H · exp(−Δt/τ_c)
7:   para cada celda i con estado = no_quemado:
8:     si H_i ≥ 1: estado_i ← combustionando; H_i ← 0
9:   para cada celda i con estado = combustionando:
10:    edad_i ← edad_i + Δt
11:    si edad_i ≥ τ_res,i: estado_i ← quemado
12:  t ← t + Δt
13: devolver estado, tiempos de llegada, área quemada",
  ),
  caption: [Pseudocódigo del autómata celular determinista.],
) <alg:det>

== Modelo probabilístico

El modelo probabilístico reemplaza el umbral determinista por una prueba de
Bernoulli. En cada paso, para cada celda no quemada,
$ P("ignición"_i) = 1 - exp(-h_i), quad
  h_i = sum_{j in cal(N)(i)} frac(R_{j arrow.r i} Delta t, d_{j arrow.r i}). $
Si $h_i$ es pequeño, $P approx h_i$; la forma exponencial garantiza
$P in [0,1]$ y evita la acumulación artificial de probabilidad. Tras la
prueba, $h_i$ se reinicia a cero, de modo que el proceso es memoryless y
equivalente a un proceso de Poisson con tasa variable. El algoritmo se resume
en el @alg:stoch.

#figure(
  raw(
    block: true,
    lang: "text",
    "ALGORITMO 2: AC probabilístico (una realización)
Entrada: terreno, ignición, Δt, t_fin, semilla
1: estado ← no_quemado; t ← 0; estado[ignición] ← combustionando
2: mientras t < t_fin:
3:   h ← 0
4:   para cada dirección k:
5:     h ← h + desplazar(R_k · Δt / d_k · [estado = combustionando])
6:   para cada celda i con estado = no_quemado:
7:     u ← Uniforme(0,1)
8:     si u < 1 − exp(−h_i): estado_i ← combustionando
9:   actualizar edades y tiempos de residencia
10:  t ← t + Δt
11: devolver estado, tiempos de llegada, área quemada",
  ),
  caption: [Pseudocódigo del autómata celular probabilístico.],
) <alg:stoch>

El ensemble Monte Carlo consiste en repetir el @alg:stoch con
semillas $s_k = s_0 + k$, $k = 0, dots, N-1$. Para cada realización se
registran el área quemada, el tiempo de llegada por celda y la máscara final.
La media y la desviación estándar se calculan sobre el conjunto. El número de
realizaciones se elige para que el error estándar de la media sea inferior al
$5$% de la media; en la práctica, $N = 32$ es suficiente para las métricas
globales, mientras que los mapas de probabilidad requieren $N >= 100$ para
resolver bien la frontera.

== Tiempo de residencia y extinción

Cada celda combustionando permanece en ese estado durante un tiempo
$tau_"res"$ que depende del combustible: $120$ s para pasto, $300$ s para
matorral y $600$ s para hojarasca y bosque. Este tiempo controla cuánto
contribuye una celda a la ignición de sus vecinos y, por tanto, la velocidad
efectiva del frente. Si una celda no logra acumular suficiente exposición
antes de que sus vecinos se apaguen, el fuego se detiene localmente. Esto
explica por qué la propagación se extingue para humedades cercanas a
$M approx 0.20$ aunque la humedad de extinción del modelo sea $M_x = 0.25$:
la combinación de baja ROS y tiempo de residencia finito impide completar el
cruce de la celda.

== Métricas de propagación y forma

=== Área quemada y velocidad de propagación

El área quemada se cuenta como el número de celdas con estado combustionando
o quemado, multiplicado por $Delta x^2$. La velocidad de propagación de cabeza
se estima de dos formas. La primera ajusta una recta a la distancia máxima
proyectada sobre la dirección del viento en función del tiempo:
$ d_h(t) = max_{i in "quemado"} (bold(r)_i dot hat{bold(u)}_w) - d_0, quad
  R = frac(d d_h, d t). $
La segunda ajusta el mapa de tiempos de llegada a lo largo del eje del viento,
$ t_i = a + frac(s_i, R), quad s_i = bold(r)_i dot hat{bold(u)}_w, $
y devuelve $R = 1/b$. El segundo método es más local y preciso en frentes
homogéneos, pero puede ser engañoso en terrenos muy heterogéneos; por ello se
exige $R^2 >= 0.80$ y se usa el primer método como respaldo.

=== Forma del frente

La forma se caracteriza mediante el análisis de componentes principales de la
nube de celdas quemadas. Si $lambda_1 >= lambda_2$ son los valores propios de
la matriz de covarianza, la relación largo/ancho se define como
$ L/A = sqrt(lambda_1/lambda_2), $
la excentricidad como $e = sqrt(1 - lambda_2/lambda_1)$ y la orientación como
el ángulo del primer vector propio. La compacidad es $4 pi A/P^2$, donde $A$
es el área y $P$ el perímetro contado por aristas de frontera. La dimensión
fractal se estima por conteo de cajas,
$ D_f = -frac(d log N(s), d log s), $
con cajas de tamaño $s = 1, 2, 4, dots$ hasta un cuarto del tamaño del objeto.
Un frente compacto da $D_f approx 2$; un frente dendrítico, valores entre
$1$ y $2$. La rugosidad del frente se define como la desviación estándar de
los tiempos de llegada en las celdas de frontera.

=== Percolación

Para el experimento de percolación se genera un bosque binario: cada celda es
combustible con probabilidad $p$ e incombustible con $1-p$. Se enciende la
columna izquierda y se resuelve el tiempo mínimo de llegada con el algoritmo de
Dijkstra sobre el grafo de vecinos (Sec. 4.7). Se define percolación como la
existencia de al menos una celda alcanzada en la columna derecha. Para cada
$p$ se realizan $80$ realizaciones y se estima la probabilidad de percolación.
El umbral se obtiene ajustando una sigmoide
$ P_"perc"(p) = frac(1,1+exp(-k(p-p_c))) $
y comparando $p_c$ con los valores teóricos de la red cuadrada.

=== Tiempo mínimo de llegada

El algoritmo de Dijkstra se usa como verificación independiente del AC
determinista. Se construye un grafo con un nodo por celda y aristas hacia los
ocho vecinos, con peso $d_{i j}/R_{i arrow.r j}$. El tiempo de llegada es la
distancia mínima desde las celdas de ignición. Esta solución es determinista y
proporciona una cota inferior del tiempo de llegada del AC, porque permite
elegir el camino más rápido entre todos los posibles. La comparación entre
ambos métodos se reporta en la sección de resultados.

== Implementación computacional y reproducibilidad

El modelo se implementó en Python con NumPy y SciPy, con componentes
independientes para las propiedades del combustible, la generación del
terreno, la actualización del autómata, las métricas y el análisis numérico.
La actualización de las celdas está vectorizada: las ocho direcciones de Moore
se procesan como desplazamientos de arreglos, lo que evita bucles explícitos
sobre la malla y mantiene el costo proporcional a $N^2$. Las pruebas
automatizadas verifican las propiedades del modelo de combustible, la
reproducibilidad de las semillas y los órdenes de convergencia de los métodos
numéricos.

El entorno computacional se gestiona con `uv`, que fija las versiones de las
dependencias y permite reconstruir el entorno de ejecución. Cada simulación
recibe una semilla explícita y produce tablas y figuras reproducibles. Los
detalles de instalación y ejecución se presentan en el anexo de
disponibilidad. El código no se transcribe en el documento; se remite al
repositorio del proyecto.

== Diseño experimental

La @tab:experimentos resume las campañas. Se distingue entre
experimentos de verificación numérica (E1--E3), experimentos de propagación
(E4--E8) y experimentos de sensibilidad y convergencia (E9--E10). Todos los
experimentos usan el mismo motor de cálculo, de modo que las diferencias entre
escenarios se deben a los parámetros y no a cambios de implementación.

#figure(
  table(
    columns: (0.55fr, 2.3fr, 2.1fr, 2.2fr),
    align: (center, left, left, left),
    stroke: 0.4pt,
    inset: 4pt,
    table.header([ID], [Objetivo], [Configuración], [Salida]),
    [E1], [Verificación de punto flotante y acondicionamiento], [Épsilon, cancelación, $kappa$ de Rothermel], [Tabla],
    [E2], [Métodos de raíces], [FM10, umbral de humedad], [Tabla y figura],
    [E3], [Integradores y EDE], [Caída con arrastre, péndulo, N cuerpos, Langevin], [Tablas y figura],
    [E4], [Escenario base], [$256^2$, $Delta x=5$ m, $U=4$ m/s, $M=0.07$, $t=900$ s], [Figuras y tabla],
    [E5], [Barrido de viento], [$192^2$, FM10, $U=0$--$8$ m/s], [Tabla y figura],
    [E6], [Barrido de humedad], [$160^2$, FM10, $M=0.03$--$0.24$], [Tabla y figura],
    [E7], [Barrido de pendiente], [$160^2$, FM10, $0$--$31$°], [Tabla y figura],
    [E8], [Percolación], [$64^2$, $p=0.25$--$0.75$, 80 realizaciones], [Tabla y figura],
    [E9], [Determinista vs. estocástico], [$160^2$, $U=4$ m/s, 32 miembros], [Tabla y figura],
    [E10], [Convergencia y sensibilidad], [$Delta x=1.25$--$10$ m, $Delta t=0.125$--$2$ s, OAT], [Tablas y figuras],
  ),
  caption: [Diseño experimental del estudio.],
) <tab:experimentos>

== Estrategia de validación

La validación se organiza en tres niveles. El primero es la _verificación
numérica_: se comprueba que los métodos reproduce los órdenes de convergencia y
las leyes de escala conocidas (Euler orden 1, RK2 orden 2, RK4 orden 4,
$"MSD" prop t$, regla 184, Nagel--Schreckenberg). El segundo es la
_validación interna_: se comprueba que el AC reproduce los umbrales de
percolación de la red cuadrada y que la ROS es monótona con el viento y la
pendiente. El tercero es la _comparación con la literatura_: se contrastan los
rangos de ROS y de relación largo/ancho con los reportados por Sullivan
@sullivan2009a, Andrews @andrews2018 y Anderson @anderson1983; los estudios
numéricos de viento y pendiente @hayajneh2025 complementan la comparación. No
se realiza una calibración formal con un incendio real, lo que
se discute como limitación.
