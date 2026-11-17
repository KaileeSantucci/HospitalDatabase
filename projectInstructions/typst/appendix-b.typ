#import "styles.typ": report-table, as-cell, sum-values

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

// Read the current profile so field tables update when the JSON changes.
#let profile = json("../../database/synthetic_profiles/initial_profile.json")
#let sources = (
  (id: "A", place: "North America", format: "TXT"),
  (id: "B", place: "Europe", format: "CSV"),
  (id: "C", place: "Asia", format: "XML"),
  (id: "D", place: "Oceania", format: "JSON"),
)

= Appendix B — Field-Level Profiles

This appendix lists the field names, inferred data types, and raw missing-value counts from the initial profile. Source-specific names and reported types are preserved.

#for (index, source) in sources.enumerate() {
  if index > 0 { pagebreak() }
  let data = profile.at(source.id)
  let entity-names = data.entities.keys().sorted()

  [
  == B.#(index + 1) Source #source.id — #source.place (#source.format)

  #let field-counts = entity-names.map(entity => data.entities.at(entity).field_names.len())
  #let entity-starts = field-counts.enumerate().map(pair =>
    sum-values(field-counts.slice(0, pair.at(0)))
  )
  #let field-rows = entity-names.map(entity => {
    let details = data.entities.at(entity)
    details.field_names.enumerate().map(pair => {
      let field-index = pair.at(0)
      let field = pair.at(1)
      (
        as-cell(if field-index == 0 { entity } else { "" }),
        as-cell(field),
        as-cell(details.inferred_types.at(field)),
        as-cell(details.missing_value_counts.at(field, default: 0)),
      )
    })
  }).flatten()
  #report-table(
    ("Entity", "Field Name", "Inferred Data Type", "Missing-Value Count"),
    field-rows,
    "Appendix B." + str(index + 1) + " — Source " + source.id + " Field-Level Profile",
    columns: (1.5fr, 2.2fr, 1.5fr, 1.2fr),
    group-starts: entity-starts,
  )
  ]
}
