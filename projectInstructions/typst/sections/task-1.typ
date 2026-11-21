#import "../styles.typ": report-table, as-cell, raw-example, sum-values

// Read the current profile directly so reported values are not copied by hand.
#let profile = json("../../../database/synthetic_profiles/initial_profile.json")
#let sources = (
  (id: "A", place: "North America", format: "TXT"),
  (id: "B", place: "Europe", format: "CSV"),
  (id: "C", place: "Asia", format: "XML"),
  (id: "D", place: "Oceania", format: "JSON"),
)

= Task 1 — Initial Data Profiling

The field-level profiles are provided in Appendix B. The following source pages summarize record counts and selected raw-data quality examples.

#for (index, source) in sources.enumerate() {
  if index > 0 { pagebreak() }
  let data = profile.at(source.id)
  let entity-names = data.entities.keys().sorted()

  [
  == Source #source.id — #source.place (#source.format)

  === Entity-Level Profile

  #let entity-rows = entity-names.map(entity => {
    let details = data.entities.at(entity)
    (
      as-cell(entity),
      as-cell(details.record_count),
      as-cell(details.exact_duplicate_count),
    )
  })
  #let entity-total = sum-values(data.entities.values().map(item => item.record_count))
  #let duplicate-total = sum-values(data.entities.values().map(item => item.exact_duplicate_count))
  #let entity-rows = entity-rows + ((
    text("Total", weight: "bold"),
    text(str(entity-total), weight: "bold"),
    text(str(duplicate-total), weight: "bold"),
  ),)
  #report-table(
    ("Entity", "Record Count", "Exact Duplicate Count Before Cleaning"),
    entity-rows,
    "Source " + source.id + " — Entity-Level Profile",
    columns: (2fr, 1fr, 1.8fr),
  )

  === Summary Statistics

  #let missing-total = sum-values(data.entities.values().map(item =>
    sum-values(item.missing_value_counts.values())
  ))
  #let fields-with-missing = sum-values(data.entities.values().map(item =>
    item.missing_value_counts.values().filter(value => value > 0).len()
  ))
  #let summary-rows = (
    (as-cell("Total raw records"), as-cell(data.record_count)),
    (as-cell("Total exact duplicates"), as-cell(duplicate-total)),
    (as-cell("Total missing values"), as-cell(missing-total)),
    (as-cell("Fields containing missing values"), as-cell(fields-with-missing)),
  )
  #report-table(
    ("Statistic", "Value"),
    summary-rows,
    "Source " + source.id + " — Summary Statistics",
    columns: (3fr, 1fr),
  )

  === Formatting Differences

  #let formatting-rows = entity-names.map(entity => {
    let examples = data.entities.at(entity).formatting_examples
    examples.keys().map(field => {
      let raw-values = examples.at(field).map(value => "⟦" + value + "⟧").join(", ")
      (as-cell(entity), as-cell(field), raw(raw-values), text(""))
    })
  }).flatten()
  #report-table(
    ("Entity", "Field", "Raw Value Examples", "Formatting Issue"),
    formatting-rows,
    "Source " + source.id + " — Formatting Examples",
    columns: (1.5fr, 1.6fr, 3.5fr, 1.4fr),
  )

  === Invalid-Value Examples

  #let invalid-rows = entity-names.map(entity => {
    let examples = data.entities.at(entity).invalid_value_examples
    examples.keys().map(field => examples.at(field).map(value => (
      as-cell(entity),
      as-cell(field),
      raw-example(value),
      text(""),
    )))
  }).flatten().flatten()
  #report-table(
    ("Entity", "Field", "Raw Value", "Reason Invalid"),
    invalid-rows,
    "Source " + source.id + " — Invalid-Value Examples",
    columns: (1.5fr, 1.7fr, 2fr, 2.8fr),
  )
  #text(size: 8pt, style: "italic")[Formatting Issue and Reason Invalid are blank because the profile contains examples but no explanations. No new validation or explanations are generated here.]
  ]
}

#pagebreak()
== Task 1 — Manual Documentation Placeholders

=== TXT Source Documentation: Delimiter and Record Layout

[Placeholder — add the TXT delimiter and record-layout description here.]

=== Error Logging Results

[Placeholder — add observations from read_errors.log and the logging check here.]

=== Loading Limitations

[Placeholder — describe any observed loading limitations here.]

=== Personal Observations

[Placeholder — add your own observations here.]
