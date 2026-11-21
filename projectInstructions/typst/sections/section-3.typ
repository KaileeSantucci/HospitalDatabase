#import "../styles.typ": report-table, as-cell, sum-values

// Use the raw-source manifest for source metadata and the Task 1 profile for counts.
#let manifest = json("../../../database/synthetic_raw/manifest.json")
#let profile = json("../../../database/synthetic_profiles/initial_profile.json")
#let source-ids = ("A", "B", "C", "D")

= Section 3 — Required Data Sources

== Source Overview

#let overview-rows = source-ids.enumerate().map(pair => {
  let id = pair.at(1)
  let source = manifest.sources.at(id)
  (
    as-cell(id),
    as-cell(source.continent),
    as-cell(source.format),
    as-cell(profile.at(id).record_count),
  )
})
#let raw-total = sum-values(source-ids.map(id => profile.at(id).record_count))
#let overview-rows = overview-rows + ((
  text("Total", weight: "bold"),
  as-cell("Four continents"),
  text(""),
  text(str(raw-total), weight: "bold"),
),)
#report-table(
  ("Source Identifier", "Continent", "File Format", "Raw Record Count"),
  overview-rows,
  "Section 3 — Source Overview",
  columns: (1.1fr, 1.8fr, 1fr, 1.3fr),
)

== Source File Organization

// The manifest does not include file counts; these are the observed layouts described by the generation specifications and raw source folders.
#let file-layouts = (
  (count: 13, layout: "One TXT file per entity; header followed by pipe-delimited records."),
  (count: 13, layout: "One CSV file per entity; header followed by CSV records."),
  (count: 14, layout: "reference_and_patients.xml plus 13 admission XML chunks with nested entities."),
  (count: 15, layout: "Separate patient and dictionary JSON files plus 13 admission chunks with nested entities."),
)
#let organization-rows = source-ids.enumerate().map(pair => {
  let index = pair.at(0)
  let id = pair.at(1)
  let source = manifest.sources.at(id)
  let entity-names = profile.at(id).entities.keys().sorted()
  (
    as-cell(id),
    as-cell(source.format),
    as-cell(file-layouts.at(index).count),
    as-cell(file-layouts.at(index).layout),
    as-cell(entity-names.join(", ")),
  )
})
#report-table(
  ("Source", "File Format", "Number of Source Files", "File Organization", "Entity Types Represented"),
  organization-rows,
  "Section 3 — Source File Organization",
  columns: (0.65fr, 0.75fr, 0.9fr, 2.1fr, 2.6fr),
)
#text(size: 8pt, style: "italic")[The manifest does not contain file counts; counts and layout descriptions use the existing generation documentation and source folders.]

== Record Counts by Source and Entity

#let entity-names = profile.at("A").entities.keys().sorted()
#let entity-count-rows = entity-names.map(entity => {
  let counts = source-ids.map(id => profile.at(id).entities.at(entity).record_count)
  (
    as-cell(entity),
    as-cell(counts.at(0)),
    as-cell(counts.at(1)),
    as-cell(counts.at(2)),
    as-cell(counts.at(3)),
    as-cell(sum-values(counts)),
  )
})
#let source-totals = source-ids.map(id => profile.at(id).record_count)
#let totals-row = (
  text("Total", weight: "bold"),
  text(str(source-totals.at(0)), weight: "bold"),
  text(str(source-totals.at(1)), weight: "bold"),
  text(str(source-totals.at(2)), weight: "bold"),
  text(str(source-totals.at(3)), weight: "bold"),
  text(str(sum-values(source-totals)), weight: "bold"),
)
#let entity-count-rows = entity-count-rows + (totals-row,)
#report-table(
  ("Entity", "Source A", "Source B", "Source C", "Source D", "Total"),
  entity-count-rows,
  "Section 3 — Record Counts by Source and Entity",
  columns: (2fr, 1fr, 1fr, 1fr, 1fr, 1fr),
)

== Record Reconciliation

#let reconciliation-rows = source-ids.map(id => (
  as-cell("Source " + id),
  as-cell(profile.at(id).record_count),
  text(""),
  text(""),
  text(""),
  text(""),
))
#let reconciliation-rows = reconciliation-rows + ((
  text("Total", weight: "bold"),
  text(str(raw-total), weight: "bold"),
  text(""),
  text(""),
  text(""),
  text(""),
),)
#report-table(
  ("Source", "Original Raw Record Count", "Duplicate Records Removed", "Rejected or Quarantined Records", "Other Count Adjustments", "Final Integrated Record Count"),
  reconciliation-rows,
  "Section 3 — Record Reconciliation (Complete After Cleaning and Integration)",
  columns: (0.9fr, 1.2fr, 1.2fr, 1.5fr, 1.2fr, 1.5fr),
)
