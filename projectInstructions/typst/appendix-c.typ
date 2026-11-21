#import "styles.typ": report-table, as-cell

// Typst reads CSV cells as strings; the ICD-9 codes are not converted to numbers.
#let reference = csv("../../projectInstructions/icd9_reference.csv")
#let entries = reference.slice(1)

= Appendix C — ICD-9 Reference Data

The rows below reproduce the supplied ICD-9 reference CSV. Codes, titles, descriptions, and categories are imported as text.

#let make-reference-rows(rows) = rows.map(row => (
  as-cell(row.at(0)),
  as-cell(row.at(1)),
  as-cell(row.at(2)),
  as-cell(row.at(3)),
))
#report-table(
  ("Code", "Official Title", "Description", "Disease Category"),
  make-reference-rows(entries.slice(0, 25)),
  "Appendix C — Supplied ICD-9 Reference Entries (1–25)",
  columns: (0.75fr, 2fr, 3.1fr, 1.75fr),
  font-size: 8pt,
  cell-inset: (x: 4pt, y: 2pt),
)

#pagebreak()
#report-table(
  ("Code", "Official Title", "Description", "Disease Category"),
  make-reference-rows(entries.slice(25)),
  "Appendix C — Supplied ICD-9 Reference Entries (26–50)",
  columns: (0.75fr, 2fr, 3.1fr, 1.75fr),
  font-size: 8pt,
  cell-inset: (x: 4pt, y: 2pt),
)
