#import "../styles.typ": report-table, as-cell
#let profile = json("../../../database/synthetic_profiles/initial_profile.json")
#let source-ids = ("A", "B", "C", "D")

== Section 3.1 — Required Hospital Content

=== Entity Coverage

#let entity-names = profile.at("A").entities.keys().sorted()
#let coverage-rows = entity-names.map(entity => (
  as-cell(entity),
  as-cell(if profile.at("A").entities.keys().contains(entity) { "Yes" } else { "No" }),
  as-cell(if profile.at("B").entities.keys().contains(entity) { "Yes" } else { "No" }),
  as-cell(if profile.at("C").entities.keys().contains(entity) { "Yes" } else { "No" }),
  as-cell(if profile.at("D").entities.keys().contains(entity) { "Yes" } else { "No" }),
))
#report-table(
  ("Entity", "Source A", "Source B", "Source C", "Source D"),
  coverage-rows,
  "Section 3.1 — Entity Coverage by Source",
  columns: (2.2fr, 1fr, 1fr, 1fr, 1fr),
)

=== Hospital Workflows and Relationships

#let workflow-topics = (
  "Patient and admission relationships",
  "Diagnoses",
  "Triage assessments",
  "Hospital unit stays and transfers",
  "Diagnostic orders and examinations",
  "Radiology examinations and reports",
  "Surgical procedures",
  "Clinical notes",
  "Discharge records",
  "Healthcare professional information",
  "Variation supporting the Phase 1 queries",
)
#let workflow-rows = workflow-topics.map(topic => (as-cell(topic), text("")))
#report-table(
  ("Topic", "Explanation to complete"),
  workflow-rows,
  "Section 3.1 — Hospital Workflow Documentation Placeholders",
  columns: (2fr, 4fr),
)

=== ICD-9 Dictionary

The source dictionaries include ICD-9 entries. The reference rows supplied for the project appear in Appendix C.

#let verification-rows = (
  (as-cell("Reference source"), text("")),
  (as-cell("Verification method"), text("")),
  (as-cell("Personal verification results"), text("")),
)
#report-table(
  ("Item to document", "Your documentation"),
  verification-rows,
  "Section 3.1 — ICD-9 Documentation Placeholders",
  columns: (2fr, 4fr),
)
