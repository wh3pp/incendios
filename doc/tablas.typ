// Archivo generado por scripts/make_typst_tables.py. No editar a mano.



#let tabla_punto_flotante() = table(
  columns: 3,
  align: center,
  stroke: 0.4pt,
  inset: 4pt,
  table.header([Expresión], [Resultado], [Error absoluto]),
  [`0.1 + 0.2`], [3.0000e-01], [5.55e-17],
  [`(0.1 + 0.2) - 0.3`], [5.5511e-17], [5.55e-17],
  [`1e16 + 1 - 1e16`], [0.0000e+00], [1.00e+00],
  [`(1 - cos(1e-8)) / 1e-16`], [0.0000e+00], [5.00e-01],
  [`épsilon de máquina`], [2.2204e-16], [0.00e+00],
)

#let tabla_raices() = table(
  columns: 5,
  align: center,
  stroke: 0.4pt,
  inset: 4pt,
  table.header([Método], [Iteraciones], [Raíz $M^*$], [$|M_k-M^*|$], [$|f(M_k)|$]),
  [Bisección], [39], [0.17616184], [2.26e-13], [2.22e-14],
  [Falsa posición], [7], [0.17616184], [3.41e-15], [1.72e-16],
  [Newton-Raphson], [5], [0.17616184], [1.75e-15], [1.04e-17],
  [Secante], [6], [0.17616184], [1.70e-13], [1.67e-14],
)

#let tabla_edo() = table(
  columns: 4,
  align: center,
  stroke: 0.4pt,
  inset: 4pt,
  table.header([Método], [$Delta t$ [s]], [Error $|v_N-v(5)|$ [m/s]], [Orden observado]),
  [EULER], [0.200], [2.905e-01], [--],
  [EULER], [0.100], [1.446e-01], [1.01],
  [EULER], [0.050], [7.212e-02], [1.00],
  [EULER], [0.025], [3.602e-02], [1.00],
  [RK2], [0.200], [7.530e-03], [--],
  [RK2], [0.100], [1.818e-03], [2.05],
  [RK2], [0.050], [4.467e-04], [2.02],
  [RK2], [0.025], [1.107e-04], [2.01],
  [RK4], [0.200], [6.954e-06], [--],
  [RK4], [0.100], [4.188e-07], [4.05],
  [RK4], [0.050], [2.569e-08], [4.03],
  [RK4], [0.025], [1.591e-09], [4.01],
)

#let tabla_pendulo() = table(
  columns: 5,
  align: center,
  stroke: 0.4pt,
  inset: 4pt,
  table.header([$theta_0$ [rad]], [$T_"RK4"$ [s]], [$T_"exacto"$ [s]], [Error rel.], [Deriva de energía]),
  [0.05], [2.0070], [2.0064], [3.09e-04], [7.3e-14],
  [0.50], [2.0380], [2.0379], [6.48e-05], [9.7e-14],
  [1.00], [2.1390], [2.1391], [6.43e-05], [2.2e-13],
  [1.50], [2.3310], [2.3310], [5.67e-06], [3.6e-13],
  [2.50], [3.2960], [3.2959], [2.06e-05], [5.7e-13],
)

#let tabla_euler_cromer() = table(
  columns: 5,
  align: center,
  stroke: 0.4pt,
  inset: 4pt,
  table.header([Método], [$Delta t$ [s]], [Períodos], [Deriva máx. rel.], [Deriva final rel.]),
  [EULER], [0.010], [20], [4.90e+00], [4.87e+00],
  [EULER-CROMER], [0.010], [20], [1.50e-02], [1.37e-04],
  [RK4], [0.010], [20], [4.20e-08], [4.04e-08],
)

#let tabla_nbody() = table(
  columns: 3,
  align: center,
  stroke: 0.4pt,
  inset: 4pt,
  table.header([$Delta t$], [Deriva máx. rel.], [Deriva final rel.]),
  [0.0200], [7.48e-08], [7.48e-08],
  [0.0100], [2.22e-09], [2.12e-09],
  [0.0050], [8.64e-11], [5.29e-11],
  [0.0025], [5.61e-12], [8.15e-13],
)

#let tabla_sde() = table(
  columns: 6,
  align: center,
  stroke: 0.4pt,
  inset: 4pt,
  table.header([$t$ [s]], [$⟨ X⟩$ emp.], [$⟨ X⟩$ exacta], [$sigma$ emp.], [$sigma$ exacta], [$p_"KS"$]),
  [1], [0.503], [0.500], [0.201], [0.200], [0.26],
  [2], [1.004], [1.000], [0.283], [0.283], [0.51],
  [5], [2.504], [2.500], [0.447], [0.447], [0.93],
)

#let tabla_escenario() = table(
  columns: 2,
  align: center,
  stroke: 0.4pt,
  inset: 4pt,
  table.header([Métrica], [Valor]),
  [Área quemada], [21.13 ha],
  [Fracción quemada], [12.9 %],
  [ROS de cabeza], [64.78 m/min],
  [$R^2$ del ajuste de ROS], [0.958],
  [Perímetro], [5.29 km],
  [Relación largo/ancho], [1.85],
  [Excentricidad], [0.840],
  [Compacidad], [0.095],
  [Dimensión fractal], [1.819],
  [Rugosidad del frente], [218.2 s],
  [Celdas quemadas], [8452],
)

#let tabla_viento() = table(
  columns: 5,
  align: center,
  stroke: 0.4pt,
  inset: 4pt,
  table.header([$U$ [m/s]], [ROS [m/min]], [Área [ha]], [L/A], [$D_f$]),
  [0], [2.40], [0.48], [1.00], [1.79],
  [1], [3.68], [0.64], [1.18], [1.77],
  [2], [6.10], [0.96], [1.50], [1.82],
  [3], [9.27], [1.36], [2.03], [1.83],
  [4], [12.98], [1.98], [2.40], [1.88],
  [5], [17.08], [2.61], [2.97], [1.90],
  [6], [21.80], [3.49], [3.39], [1.87],
  [7], [27.22], [4.42], [3.90], [1.90],
  [8], [31.98], [5.48], [4.38], [1.93],
)

#let tabla_humedad() = table(
  columns: 4,
  align: center,
  stroke: 0.4pt,
  inset: 4pt,
  table.header([$M$ [--]], [ROS [m/min]], [Área [ha]], [Avance [m]]),
  [0.03], [3.81], [2.02], [75],
  [0.05], [2.95], [1.26], [60],
  [0.07], [2.40], [0.85], [50],
  [0.09], [2.04], [0.60], [40],
  [0.11], [1.80], [0.48], [35],
  [0.13], [1.61], [0.38], [35],
  [0.15], [1.42], [0.32], [30],
  [0.18], [1.03], [0.17], [20],
  [0.21], [5.85e-17], [0.02], [5],
  [0.24], [5.85e-17], [0.02], [5],
)

#let tabla_pendiente() = table(
  columns: 4,
  align: center,
  stroke: 0.4pt,
  inset: 4pt,
  table.header([Pendiente [°]], [ROS [m/min]], [Área [ha]], [L/A]),
  [0.0], [2.40], [0.48], [1.00],
  [5.7], [2.79], [0.54], [1.02],
  [11.3], [3.97], [0.71], [1.15],
  [16.7], [5.92], [1.08], [1.22],
  [21.8], [8.61], [1.69], [1.35],
  [26.6], [12.04], [2.59], [1.47],
  [31.0], [16.35], [3.94], [1.58],
)

#let tabla_percolacion() = table(
  columns: 3,
  align: center,
  stroke: 0.4pt,
  inset: 4pt,
  table.header([$p$], [$P_{"perc"}$ (4)], [$P_{"perc"}$ (8)]),
  [0.350], [0.000], [0.000],
  [0.375], [0.000], [0.062],
  [0.400], [0.000], [0.350],
  [0.425], [0.000], [0.775],
  [0.450], [0.000], [0.975],
  [0.475], [0.000], [1.000],
  [0.500], [0.000], [1.000],
  [0.525], [0.000], [1.000],
  [0.550], [0.013], [1.000],
  [0.575], [0.212], [1.000],
  [0.600], [0.700], [1.000],
  [0.625], [0.900], [1.000],
  [0.650], [1.000], [1.000],
)

#let tabla_comparacion() = table(
  columns: 7,
  align: center,
  stroke: 0.4pt,
  inset: 4pt,
  table.header([Modelo], [Área [ha]], [$sigma_A$ [ha]], [CV [%]], [ROS [m/min]], [L/A], [$D_f$]),
  [Determinista], [10.28], [0.00], [0.00], [42.24], [1.87], [1.79],
  [Estocástico (ensemble)], [24.89], [0.77], [3.08], [35.34], [1.34], [1.82],
)

#let tabla_convergencia_espacial() = table(
  columns: 5,
  align: center,
  stroke: 0.4pt,
  inset: 4pt,
  table.header([$Delta x$ [m]], [$N$], [ROS [m/min]], [Error rel. [%]], [Orden]),
  [10.00], [64], [12.500], [8.3], [--],
  [5.00], [128], [13.043], [4.3], [0.94],
  [2.50], [256], [13.043], [4.3], [4.48e-15],
  [1.25], [512], [13.636], [0.0], [--],
)

#let tabla_convergencia_temporal() = table(
  columns: 3,
  align: center,
  stroke: 0.4pt,
  inset: 4pt,
  table.header([$Delta t$ [s]], [ROS [m/min]], [Error rel. [%]]),
  [2.000], [12.500], [5.21],
  [1.000], [13.043], [1.09],
  [0.500], [13.043], [1.09],
  [0.250], [13.187], [0.00],
  [0.125], [13.187], [0.00],
)

#let tabla_sensibilidad() = table(
  columns: 2,
  align: center,
  stroke: 0.4pt,
  inset: 4pt,
  table.header([Parámetro], [Elasticidad]),
  [Carga], [-0.195],
  [Humedad], [-0.480],
  [Pendiente], [0.774],
  [Viento], [1.218],
)

#let tabla_casos_reales() = table(
  columns: 9,
  align: center,
  stroke: 0.4pt,
  inset: 4pt,
  table.header([Caso], [País], [Inicio], [Área obs. [ha]], [Área sim. [ha]], [Error [%]], [IoU], [ROS [m/min]], [L/A]),
  [Incendio forestal de Acos (Mayuhuilca)], [Perú], [2025-09-11 12:24], [297], [308], [3.6], [--], [10.4], [1.36],
  [Little Giant Fire], [Estados Unidos], [2026-07-15 00:00], [1253], [1731], [38.2], [0.62], [0.1], [1.11],
)

#let tabla_rendimiento() = table(
  columns: 4,
  align: center,
  stroke: 0.4pt,
  inset: 4pt,
  table.header([$N$], [Det. [s]], [Estoc. [s]], [Memoria [MB]]),
  [64], [0.09], [0.13], [0.6],
  [128], [0.20], [0.30], [2.3],
  [256], [0.81], [1.14], [9.2],
  [512], [3.78], [--], [36.8],
)
