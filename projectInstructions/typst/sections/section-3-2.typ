#import "../styles.typ": report-table, as-cell, raw-example, sum-values

#let manifest = json("../../../database/synthetic_raw/manifest.json")
#let profile = json("../../../database/synthetic_profiles/initial_profile.json")
#let source-ids = ("A", "B", "C", "D")
#let raw-total = sum-values(source-ids.map(id => profile.at(id).record_count))

== Section 3.2 — Differences and Data-Quality Problems

=== Differences Between Sources

The entries below are taken from the existing generation specifications and source manifest.

#let timezone-values = source-ids.map(id => manifest.sources.at(id).timezone)
#let comparison-rows = (
  (
    as-cell("File structure"),
    as-cell("13 entity-specific TXT files"),
    as-cell("13 entity-specific CSV files"),
    as-cell("One reference/patient file and 13 XML admission chunks; nested entities"),
    as-cell("Separate patient and dictionary files and 13 JSON admission chunks; nested entities"),
  ),
  (
    as-cell("Field naming conventions"),
    as-cell("Logical field names"),
    as-cell("Source-specific header aliases"),
    as-cell("Logical field names as XML elements"),
    as-cell("Logical field names as JSON properties"),
  ),
  (
    as-cell("Date formats"),
    as-cell("YYYY-MM-DD"),
    as-cell("DD/MM/YYYY"),
    as-cell("YYYYMMDD"),
    as-cell("YYYY-MM-DD"),
  ),
  (
    as-cell("Timestamp formats"),
    as-cell("YYYY-MM-DD HH:MM:SS; no explicit offset"),
    as-cell("DD/MM/YYYY HH:MM; no explicit offset"),
    as-cell("ISO 8601 with +08:00 offset"),
    as-cell("ISO 8601 with +10:00 offset"),
  ),
  (
    as-cell("Time zones in manifest"),
    as-cell(timezone-values.at(0)),
    as-cell(timezone-values.at(1)),
    as-cell(timezone-values.at(2)),
    as-cell(timezone-values.at(3)),
  ),
  (
    as-cell("Admission category labels"),
    as-cell("emergency; urgent; elective; outpatient"),
    as-cell("emergency; urgent admission; routine; outpatient"),
    as-cell("Emergency; Urgent Care; Planned; Ambulatory"),
    as-cell("ER; urgent; scheduled; clinic"),
  ),
  (
    as-cell("Triage priority labels"),
    as-cell("High; Moderate; Low"),
    as-cell("critical; urgent; routine"),
    as-cell("P1; P2; P3"),
    as-cell("immediate; urgent; routine"),
  ),
  (
    as-cell("Hospital unit labels"),
    as-cell("Emergency Department; General Medical Ward; ICU; CCU; MICU; SICU; Surgical Ward; Other"),
    as-cell("A&E; ward; Critical Care; Cardiac Care; Medical Intensive Care; Surgical Intensive Care; surgical ward; other"),
    as-cell("ED; Medical Ward; Intensive Care; Cardiac Care; Medical ICU; Surgical ICU; Surgery Ward; Other"),
    as-cell("ER; General Ward; ICU-Adult; Cardiac ICU; ICU-Medical; ICU-Surgical; Surgical Ward; Other"),
  ),
  (
    as-cell("Admission status labels"),
    as-cell("Discharged; Deceased; missing for unfinished admissions"),
    as-cell("Discharged; Deceased; missing for unfinished admissions"),
    as-cell("Discharged; Deceased; missing for unfinished admissions"),
    as-cell("Discharged; Deceased; missing for unfinished admissions"),
  ),
  (
    as-cell("Order and examination status labels"),
    as-cell("Orders: Completed, Pending, Awaiting Results; examinations: Completed"),
    as-cell("Orders: Completed, Pending, Awaiting Results; examinations: Completed"),
    as-cell("Orders: Completed, Pending, Awaiting Results; examinations: Completed"),
    as-cell("Orders: Completed, Pending, Awaiting Results; examinations: Completed"),
  ),
  (
    as-cell("Temperature units"),
    as-cell("Celsius"),
    as-cell("Celsius"),
    as-cell("Celsius"),
    as-cell("Fahrenheit"),
  ),
  (
    as-cell("Missing-value representations"),
    as-cell("\\N"),
    as-cell("Empty CSV field"),
    as-cell("Null optional element omitted"),
    as-cell("JSON null or absent optional property"),
  ),
  (
    as-cell("Local identifier conventions"),
    as-cell("Entity prefix + five digits; source-local"),
    as-cell("Entity prefix + five digits; source-local"),
    as-cell("Entity prefix + five digits; source-local"),
    as-cell("Entity prefix + five digits; source-local"),
  ),
)
#report-table(
  ("Characteristic", "Source A", "Source B", "Source C", "Source D"),
  comparison-rows,
  "Section 3.2 — Generation-Specified Source Differences",
  columns: (1.25fr, 1.7fr, 1.7fr, 1.7fr, 1.7fr),
)

=== Intentional Data-Quality Problems

#let issue-count(source-id, issue-name) = manifest.sources.at(source-id).issue_ledger.filter(item => item.issue == issue-name).len()
#let issue-row(label, issue-name) = {
  let counts = source-ids.map(id => issue-count(id, issue-name))
  let total = sum-values(counts)
  (
    as-cell(label),
    as-cell(counts.at(0)),
    as-cell(counts.at(1)),
    as-cell(counts.at(2)),
    as-cell(counts.at(3)),
    as-cell(total),
    as-cell(str(total) + " / " + str(raw-total) + " raw entity instances (" + str(total * 100 / raw-total) + "%)"),
  )
}
#let required-counts = source-ids.map(id => issue-count(id, "missing required value"))
#let optional-counts = source-ids.map(id => issue-count(id, "missing optional value"))
#let seeded-missing-total = sum-values(required-counts) + sum-values(optional-counts)
#let missing-row = (
  as-cell("Missing required and optional values (required; optional)"),
  as-cell("" + str(required-counts.at(0)) + "; " + str(optional-counts.at(0))),
  as-cell("" + str(required-counts.at(1)) + "; " + str(optional-counts.at(1))),
  as-cell("" + str(required-counts.at(2)) + "; " + str(optional-counts.at(2))),
  as-cell("" + str(required-counts.at(3)) + "; " + str(optional-counts.at(3))),
  as-cell("Required " + str(sum-values(required-counts)) + "; optional " + str(sum-values(optional-counts))),
  as-cell(str(seeded-missing-total) + " / " + str(raw-total) + " raw entity instances (" + str(seeded-missing-total * 100 / raw-total) + "%)"),
)
#let no-id-count-row = (
  as-cell("Repeated local identifiers across different sources"),
  text(""), text(""), text(""), text(""), text(""), text(""),
)
#let anomaly-rows = (
  issue-row("Duplicate records", "exact duplicate"),
  missing-row,
  issue-row("Inconsistent capitalization and whitespace", "whitespace/case variation"),
  issue-row("Invalid or ambiguous dates (manifest issue: invalid timestamp)", "invalid timestamp"),
  issue-row("Invalid numeric values", "invalid numeric value"),
  issue-row("Broken references between related records", "broken admission reference"),
  issue-row("Chronologically inconsistent hospital events", "chronological inconsistency"),
  no-id-count-row,
)
#report-table(
  ("Data-Quality Problem", "Source A", "Source B", "Source C", "Source D", "Total", "Frequency / Percentage"),
  anomaly-rows,
  "Section 3.2 — Intentional Issue-Ledger Counts",
  columns: (2.1fr, 0.7fr, 0.7fr, 0.7fr, 0.7fr, 0.8fr, 2fr),
)
#text(size: 8pt, style: "italic")[Counts above are issue-ledger entries from the generation manifest, not unique affected-record counts. Percentages use the combined raw entity-instance count as the denominator; one instance may carry multiple issues. The invalid-timestamp count does not separately identify ambiguous-date cases. The manifest does not record a frequency for repeated local identifiers. Task 1 reports observed profile counts separately. Profile missing-value counts include ordinary optional absences and are not the same as intentionally seeded missing-value entries.]

=== Representative Examples

The generation manifest records issue labels and affected local identifiers, but not the altered field values. Those identifiers are included below; raw-value cells remain blank when the manifest has no value example. The table also includes representative raw formatting, invalid-value, and repeated-identifier examples already present in the Task 1 profile. Explanation cells remain blank.

#let ledger-issue-examples = (
  (issue: "exact duplicate", label: "Duplicate record"),
  (issue: "missing required value", label: "Missing required value"),
  (issue: "missing optional value", label: "Missing optional value"),
  (issue: "whitespace/case variation", label: "Inconsistent capitalization and whitespace"),
  (issue: "invalid timestamp", label: "Invalid timestamp"),
  (issue: "invalid numeric value", label: "Invalid numeric value"),
  (issue: "broken admission reference", label: "Broken admission reference"),
  (issue: "chronological inconsistency", label: "Chronological inconsistency"),
)
#let ledger-example-rows = source-ids.map(source-id => {
  let ledger = manifest.sources.at(source-id).issue_ledger
  ledger-issue-examples.map(example => {
    let item = ledger.filter(record => record.issue == example.issue).at(0)
    (
      as-cell(source-id),
      as-cell(item.entity),
      as-cell("Manifest record ID: " + item.id),
      as-cell(example.label),
      text(""),
      text(""),
    )
  })
}).flatten().flatten()

#let example-rows = source-ids.map(source-id => {
  let source = profile.at(source-id)
  let note-entity = source.entities.at("clinical_notes")
  let note-format-field = note-entity.formatting_examples.keys().sorted().at(0)
  let note-format-values = note-entity.formatting_examples.at(note-format-field).map(value => "⟦" + value + "⟧").join(", ")
  let note-invalid-field = note-entity.invalid_value_examples.keys().sorted().at(0)
  let note-invalid-value = note-entity.invalid_value_examples.at(note-invalid-field).at(0)
  let triage = source.entities.at("triage_assessments")
  let triage-invalid-field = triage.invalid_value_examples.keys().sorted().at(0)
  let triage-invalid-value = triage.invalid_value_examples.at(triage-invalid-field).at(0)
  let patient-samples = source.entities.at("patients").sample_values
  let patient-id-field = if patient-samples.keys().contains("patient_id") { "patient_id" } else { "person_ref" }
  let patient-id-example = patient-samples.at(patient-id-field).at(0)
  (
    (
      as-cell(source-id), as-cell("clinical_notes"), as-cell(note-format-field),
      as-cell("Formatting example from Task 1 profile"), raw(note-format-values), text(""),
    ),
    (
      as-cell(source-id), as-cell("clinical_notes"), as-cell(note-invalid-field),
      as-cell("Invalid-value example from Task 1 profile"), raw-example(note-invalid-value), text(""),
    ),
    (
      as-cell(source-id), as-cell("triage_assessments"), as-cell(triage-invalid-field),
      as-cell("Invalid-value example from Task 1 profile"), raw-example(triage-invalid-value), text(""),
    ),
    (
      as-cell(source-id), as-cell("patients"), as-cell(patient-id-field),
      as-cell("Repeated source-local identifier example"), raw-example(patient-id-example), text(""),
    ),
  )
}).flatten()
#let example-rows = ledger-example-rows + example-rows
#report-table(
  ("Source", "Entity", "Field or Affected Relationship", "Data-Quality Problem", "Original Raw Example", "Explanation"),
  example-rows,
  "Section 3.2 — Representative Existing Examples",
  columns: (0.65fr, 1.2fr, 1.35fr, 1.55fr, 1.45fr, 1.7fr),
)

=== Preservation of Raw Datasets

#let preservation-rows = ((as-cell("How the original source files are preserved unchanged"), text("")),)
#report-table(
  ("Item to document", "Your documentation"),
  preservation-rows,
  "Section 3.2 — Raw Dataset Preservation Placeholder",
  columns: (2.5fr, 3.5fr),
)
