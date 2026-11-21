# Section 3: Synthetic Source Data Record

## Source selection and size

Each source represents an independent fictional hospital system on a different continent. The generator produced 7,000 raw entity instances per source, meeting the required 5,000–10,000 range and totaling 28,000 records.

| Source | Geographic origin | Required format | Raw entity records |
|---|---|---|---:|
| A | North America | Delimited TXT | 7,000 |
| B | Europe | CSV | 7,000 |
| C | Asia | XML | 7,000 |
| D | Oceania | JSON | 7,000 |
| **Total** | **Four continents** |  | **28,000** |

The exact entity counts are recorded in `database/synthetic_raw/manifest.json`. Each source contains the same allocation:

| Entity type | Records per source |
|---|---:|
| Patients | 800 |
| Admissions | 1,300 |
| Diagnoses | 1,500 |
| Triage assessments | 700 |
| Unit stays | 700 |
| Diagnostic orders | 450 |
| Diagnostic examinations | 250 |
| Radiology examinations | 150 |
| Radiology reports | 150 |
| Surgical procedures | 100 |
| Clinical notes | 500 |
| Discharge records | 350 |
| ICD-9 dictionary entries | 50 |
| **Total** | **7,000** |

These are raw source-record counts. Repeated and deliberately defective entity instances still count. XML and JSON nested entities are each counted once; collection containers, metadata, tags, attributes, and fields are not records.

## Files and record layouts

- **A (TXT):** one UTF-8 pipe-delimited file per entity, with a header row and one entity per subsequent line. `\\N` denotes a missing value. Field order and logical record layout are defined by the generator and its entity field definitions.
- **B (CSV):** one UTF-8 CSV file per entity, with a header row and one entity per row. Standard CSV quoting is used; empty values represent missing data. Source-specific header aliases differ from A.
- **C (XML):** `reference_and_patients.xml` stores patients and dictionary entries; admission documents are divided into 13 XML chunks. Admissions contain nested event entities, each with its own identifier.
- **D (JSON):** patient and dictionary files are separate; admissions are divided into 13 JSON chunks. Admission objects contain nested event arrays and objects, each representing an entity instance.

The TXT delimiter and row structure are documented here for Section 3; the loader implementation and parsing/profile evidence belong to Task 1.

## Hospital content and workflow variation

All sources contain related patients, admissions, and diagnoses, plus triage assessments, professionals, units and stays, diagnostic orders and examinations, radiology exams and reports, procedures, clinical notes, discharge records, and ICD-9 dictionary records. Source-local IDs connect related entities. Repeated admissions per patient and multi-diagnosis admissions are represented. Generated cases vary in admission type, triage priority, unit pathways, completed/deceased status, admission duration, clinical activity, and diagnosis distribution to support workflow analysis and the Phase 1 query set.

## Source differences and controlled data-quality examples

The sources use different field names and representations, including differing date and timestamp formats, source time zones, admission and triage labels, unit labels, temperature units, whitespace/capitalization, and missing-value encodings. Planned fictional time zones are `America/Toronto` (A), `Europe/Paris` (B), `Asia/Singapore` (C), and `Australia/Brisbane` (D). Source D temperatures use Fahrenheit; the other sources use Celsius.

The generator seeds controlled examples of exact duplicates, missing required and optional values, capitalization/whitespace variation, invalid and ambiguous dates, invalid numeric values, broken references, inconsistent event chronology, and local identifiers repeated across independent sources. The manifest's per-source issue ledger records the seeded issue type and affected entity identifier. A single record can have multiple issues. Seeded defects are intentional; most generated records remain usable. No missing clinical facts are filled in as part of generation.

## ICD-9 reference and synthetic-data declaration

ICD-9 codes are represented as strings so punctuation and leading zeros are preserved. The shared 50-entry dictionary is included in each source's 7,000-record total. Codes and official titles were selected from the CMS FY 2015 ICD-9-CM code-description reference; the checked subset is stored in `projectInstructions/icd9_reference.csv`. Category labels are derived from the ICD-9 chapter ranges for this dataset.

All patient identities, contact details, and clinical scenarios are entirely fictional, created exclusively for educational and learning purposes; they do not describe real patients or include real personal information. ChatGPT was used to help plan and author the generator; Python's standard library deterministically generates the records from fixed per-source seeds. Individual patient rows were not supplied by or copied from an AI output. Review included checking source counts and issue ledgers against the manifest, checking that the source-specific formats and relationships are generated by code, and checking the ICD-9 subset against the CMS reference.

CMS reference: [2015 ICD-9-CM diagnosis code descriptions](https://www.cms.gov/medicare/coding-billing/icd-10-codes).

## Preservation

The generated originals are preserved under `database/synthetic_raw/`. The manifest is part of the source record and documents source origins, formats, time zones, counts, generation seeds, and seeded issues. Cleaning should produce separate outputs so the raw files remain unchanged.
