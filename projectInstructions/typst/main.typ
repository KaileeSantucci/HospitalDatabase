#import "styles.typ": *

#set page(
  paper: "us-letter",
  margin: (x: 0.72in, y: 0.68in),
  footer: context [
    #align(center)[#counter(page).display()]
  ],
)
#set text(font: "Libertinus Serif", size: 10pt, lang: "en")
#set par(leading: 0.72em, spacing: 0.55em)
#show heading: set block(above: 1.0em, below: 0.4em)
#show figure: set block(breakable: true)
#show figure.caption: set text(size: 8.5pt, fill: rgb("#4B5563"))

#align(center)[
  #text(size: 19pt, weight: "bold")[SOEN 363 — Phase 2]
  #linebreak()
  #text(size: 14pt)[Hospital Database Project Documentation]
]
#v(1em)

#outline(title: [Table of Contents], depth: 3)

#pagebreak()
#include "sections/section-2.typ"
#pagebreak()
#include "sections/section-3.typ"
#pagebreak()
#include "sections/section-3-1.typ"
#pagebreak()
#include "sections/section-3-2.typ"
#pagebreak()
#include "sections/task-1.typ"
#pagebreak()
#include "sections/task-2.typ"
#pagebreak()
#include "sections/task-3.typ"
#pagebreak()
#include "sections/task-4.typ"
#pagebreak()
#include "sections/task-5.typ"
#pagebreak()
#include "sections/task-6.typ"
#pagebreak()
#include "appendix-a.typ"
#pagebreak()
#include "appendix-b.typ"
#pagebreak()
#include "appendix-c.typ"
