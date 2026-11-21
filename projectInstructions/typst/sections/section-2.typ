#import "../styles.typ": report-table, as-cell

= Section 2 — Generative AI Use

Complete the documentation fields below. The explanation cells are intentionally blank.

#let ai-rows = (
  (as-cell("AI tool used"), text("")),
  (as-cell("Original prompts used for dataset generation"), text("")),
  (as-cell("Required fictional-data and educational-purpose disclaimer"), text("")),
  (as-cell("Personal review and verification of generated datasets"), text("")),
)
#report-table(
  ("Item to document", "Your documentation"),
  ai-rows,
  "Section 2 — Generative AI Use Documentation",
  columns: (2fr, 4fr),
)
