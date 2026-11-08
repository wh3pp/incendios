#import "lib.typ": proyecto, footnote_ref
#import "tablas.typ": *

#show: proyecto.with(
  title: "Simulación de la propagación de incendios forestales en terrenos heterogéneos mediante autómatas celulares bidimensionales",
  course: "FÍSICA COMPUTACIONAL",
  logo: "assets/cs_logo.png",
  teacher: "Apaza Veliz, Danny Giancarlo",
  members: (
    "Miramira Bellido Rimsky Augusto",
    "Espinoza Barrios David Alejandro",
    "Montañez Pacco Roni Ezequiel",
    "Calizaya Quispe Jose Luis",
    "Machacca Puma Yaquelin Liset",
  ),
)

#set page(
  paper: "a4",
  margin: (x: 2.4cm, y: 2.4cm),
  numbering: "1",
)

#set text(
  font: "Libertinus Serif",
  size: 10.5pt,
  lang: "es",
)

#set par(
  justify: true,
  leading: 0.62em,
)

#set heading(numbering: "1.1")
#set math.equation(numbering: "(1)")

// Estilo de tablas y figuras.
#show figure: set block(breakable: true)
#show figure.caption: set text(size: 9pt)
#show table: set text(size: 8.4pt)
#show raw.where(block: true): set text(size: 8pt)

#set list(marker: [--], indent: 0.5em)
#set enum(indent: 0.5em)

#outline(title: [Índice], indent: 2em)
#pagebreak()
#outline(title: [Índice de figuras y tablas], target: figure, indent: 1.5em)

#pagebreak()
#include "sections/01_introduccion.typ"
#include "sections/02_estado_arte.typ"
#include "sections/03_marco_teorico.typ"
#include "sections/04_metodologia.typ"

#pagebreak()
#bibliography("refs.bib", style: "ieee", title: [Referencias bibliográficas])
