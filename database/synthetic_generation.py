#!/usr/bin/env python3
"""Generate the four fictional hospital source datasets for Section 3.

Run from the repository root:
    python3 database/synthetic_generation.py \
      --icd9-reference projectInstructions/icd9_reference.csv

The generator writes to database/synthetic_raw/ by default and refuses to
overwrite a non-empty output directory. All generated patient identities and
clinical scenarios are fictional and for education only.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import xml.etree.ElementTree as ET
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
RAW_ROOT = ROOT / "synthetic_raw"
SOURCE_INFO = {
    "A": ("North America", "TXT", 314159, "America/Toronto"),
    "B": ("Europe", "CSV", 271828, "Europe/Paris"),
    "C": ("Asia", "XML", 161803, "Asia/Singapore"),
    "D": ("Oceania", "JSON", 141421, "Australia/Brisbane"),
}
COUNTS = {
    "patients": 800,
    "admissions": 1300,
    "diagnoses": 1500,
    "triage_assessments": 700,
    "unit_stays": 700,
    "diagnostic_orders": 450,
    "diagnostic_examinations": 250,
    "radiology_examinations": 150,
    "radiology_reports": 150,
    "surgical_procedures": 100,
    "clinical_notes": 500,
    "discharge_records": 350,
    "icd9_dictionary": 50,
}
FIELD_ORDER = {
    "patients": "patient_id first_name last_name date_of_birth gender address telephone_number health_insurance_number emergency_contact_name emergency_contact_phone life_status death_datetime",
    "admissions": "admission_id patient_id admission_datetime admission_type admission_source reason_for_admission insurance_info condition_on_admission admitting_professional discharge_datetime final_status",
    "icd9_dictionary": "icd9_code official_title description disease_category",
    "diagnoses": "diagnosis_id patient_id admission_id icd9_code diagnosis_datetime diagnosis_type diagnosing_physician",
    "triage_assessments": "triage_id admission_id assessment_datetime triage_nurse blood_pressure heart_rate respiratory_rate body_temperature oxygen_saturation pain_level reported_symptoms known_allergies current_medications priority_level",
    "clinical_notes": "note_id admission_id note_datetime author_physician note_type note_content symptoms physical_examination clinical_findings suspected_condition planned_examinations treatment_plan",
    "unit_stays": "unit_stay_id admission_id unit_type ward room bed_number entry_datetime exit_datetime responsible_physician transfer_reason",
    "diagnostic_orders": "order_id admission_id requesting_physician requested_examination request_datetime clinical_reason priority order_status",
    "diagnostic_examinations": "exam_id order_id exam_type exam_datetime performed_by exam_result exam_status",
    "radiology_examinations": "radiology_exam_id admission_id order_id exam_type exam_datetime body_area referring_physician radiology_technician exam_status image_link",
    "radiology_reports": "report_id radiology_exam_id radiologist report_datetime findings interpretations clinical_conclusion",
    "surgical_procedures": "procedure_id admission_id procedure_name procedure_datetime surgeon operating_room outcome_notes",
    "discharge_records": "discharge_id admission_id discharge_datetime discharge_destination condition_at_discharge prescribed_medications follow_up_instructions follow_up_appointments responsible_physician discharge_summary",
}
FIELDS = {entity: value.split() for entity, value in FIELD_ORDER.items()}
ID_FIELDS = {
    "patients": "patient_id",
    "admissions": "admission_id",
    "diagnoses": "diagnosis_id",
    "triage_assessments": "triage_id",
    "clinical_notes": "note_id",
    "unit_stays": "unit_stay_id",
    "diagnostic_orders": "order_id",
    "diagnostic_examinations": "exam_id",
    "radiology_examinations": "radiology_exam_id",
    "radiology_reports": "report_id",
    "surgical_procedures": "procedure_id",
    "discharge_records": "discharge_id",
}
PREFIX = {
    "patients": "P", "admissions": "A", "diagnoses": "D",
    "triage_assessments": "T", "clinical_notes": "N", "unit_stays": "U",
    "diagnostic_orders": "O", "diagnostic_examinations": "E",
    "radiology_examinations": "R", "radiology_reports": "RR",
    "surgical_procedures": "S", "discharge_records": "DC",
}
STATUS = ("Completed", "Pending", "Awaiting Results", "Cancelled")

# Source B aliases are positional and map to the canonical FIELD_ORDER.
ALIASES_B = {
    "patients": "person_ref given_name family_name birth_date sex home_address phone coverage_id emergency_name emergency_phone vital_status death_time",
    "admissions": "visit_ref person_ref admitted_at visit_class origin presenting_reason payer_details admission_condition responsible_clinician released_at exit_status",
    "icd9_dictionary": "code official_name long_description category",
    "diagnoses": "diagnosis_ref person_ref visit_ref code recorded_at role clinician",
    "triage_assessments": "triage_ref visit_ref assessed_at nurse bp pulse_bpm respirations_min temperature_c oxygen_pct pain_score symptoms allergies medications acuity",
    "clinical_notes": "note_ref visit_ref authored_at author note_class text symptoms exam_findings clinical_findings suspected_diagnosis planned_tests plan",
    "unit_stays": "stay_ref visit_ref ward_class ward_name room_no bed_no arrived_at left_at attending_clinician transfer_reason",
    "diagnostic_orders": "request_ref visit_ref ordered_by test_requested ordered_at indication urgency request_state",
    "diagnostic_examinations": "test_ref request_ref test_class performed_at operator result_text test_state",
    "radiology_examinations": "image_exam_ref visit_ref request_ref modality performed_at anatomical_site referrer technologist image_state image_uri",
    "radiology_reports": "image_report_ref image_exam_ref reporting_radiologist reported_at observations interpretation conclusion",
    "surgical_procedures": "operation_ref visit_ref operation_name operated_at surgeon theatre outcome",
    "discharge_records": "release_ref visit_ref released_at destination condition_on_release medications_on_release followup_instructions followup_appointments responsible_clinician summary",
}


def local_id(source: str, entity: str, number: int) -> str:
    # IDs intentionally collide across systems; integration keys include source.
    del source
    return f"{PREFIX[entity]}{number:05d}"


def stamp(value: datetime, source: str) -> str:
    _, _, _, zone = SOURCE_INFO[source]
    offsets = {"America/Toronto": "-04:00", "Europe/Paris": "+02:00",
               "Asia/Singapore": "+08:00", "Australia/Brisbane": "+10:00"}
    if source == "A":
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if source == "B":
        return value.strftime("%d/%m/%Y %H:%M")
    if source == "C":
        return value.strftime("%Y-%m-%dT%H:%M:%S") + offsets[zone]
    return value.strftime("%Y-%m-%dT%H:%M:%S") + offsets[zone]


def date_string(value: datetime, source: str) -> str:
    if source == "B":
        return value.strftime("%d/%m/%Y")
    if source == "C":
        return value.strftime("%Y%m%d")
    return value.strftime("%Y-%m-%d")


def source_label(source: str, field: str, value: str) -> str:
    aliases = {
        "B": {
            "admission_type": {"emergency": "emergency", "urgent": "urgent admission",
                               "elective": "routine", "outpatient": "outpatient"},
            "priority_level": {"High": "critical", "Moderate": "urgent", "Low": "routine"},
            "unit_type": {
                "Emergency Department": "A&E", "General Medical Ward": "ward",
                "ICU": "Critical Care", "CCU": "Cardiac Care",
                "MICU": "Medical Intensive Care", "SICU": "Surgical Intensive Care",
                "Surgical Ward": "surgical ward", "Other": "other",
            },
        },
        "C": {
            "admission_type": {"emergency": "Emergency", "urgent": "Urgent Care",
                               "elective": "Planned", "outpatient": "Ambulatory"},
            "priority_level": {"High": "P1", "Moderate": "P2", "Low": "P3"},
            "unit_type": {
                "Emergency Department": "ED", "General Medical Ward": "Medical Ward",
                "ICU": "Intensive Care", "CCU": "Cardiac Care",
                "MICU": "Medical ICU", "SICU": "Surgical ICU",
                "Surgical Ward": "Surgery Ward", "Other": "Other",
            },
        },
        "D": {
            "admission_type": {"emergency": "ER", "urgent": "urgent", "elective": "scheduled", "outpatient": "clinic"},
            "priority_level": {"High": "immediate", "Moderate": "urgent", "Low": "routine"},
            "unit_type": {
                "Emergency Department": "ER", "General Medical Ward": "General Ward",
                "ICU": "ICU-Adult", "CCU": "Cardiac ICU",
                "MICU": "ICU-Medical", "SICU": "ICU-Surgical",
                "Surgical Ward": "Surgical Ward", "Other": "Other",
            },
        },
    }
    return aliases.get(source, {}).get(field, {}).get(value, value)


def load_icd9(path: Path) -> list[dict[str, str]]:
    required = ("code", "official_title", "description", "disease_category")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or any(name not in reader.fieldnames for name in required):
            raise ValueError(f"ICD-9 CSV must contain columns: {', '.join(required)}")
        rows = [{name: (row.get(name) or "").strip() for name in required}
                for row in reader]
    rows = [row for row in rows if row["code"] and row["official_title"]]
    if len(rows) < COUNTS["icd9_dictionary"]:
        raise ValueError("Provide at least 50 verified ICD-9 dictionary entries.")
    seen: set[str] = set()
    for row in rows:
        code = row["code"]
        if code in seen:
            raise ValueError(f"Duplicate ICD-9 code in reference input: {code}")
        seen.add(code)
    return [{
        "icd9_code": row["code"],
        "official_title": row["official_title"],
        "description": row["description"],
        "disease_category": row["disease_category"],
    } for row in rows[:COUNTS["icd9_dictionary"]]]


def make_source(source: str, icd: list[dict[str, str]]) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {entity: [] for entity in COUNTS}
    rows["icd9_dictionary"] = deepcopy(icd)
    for index in range(1, COUNTS["patients"] + 1):
        rows["patients"].append({
            "patient_id": local_id(source, "patients", index),
            "first_name": f"FictionalPerson{index:04d}",
            "last_name": f"Example{source}{index:04d}",
            "date_of_birth": date_string(datetime(1940, 1, 1) + timedelta(days=(index * 137) % 25000), source),
            "gender": ("Female", "Male", "Other")[index % 3],
            "address": f"Fictional Residence {source}-{index:04d}",
            "telephone_number": f"555-01{index % 100:02d}",
            "health_insurance_number": f"{source}{index:011d}"[:12],
            "emergency_contact_name": f"FictionalContact{index:04d}",
            "emergency_contact_phone": f"555-02{index % 100:02d}",
            "life_status": "Alive",
            "death_datetime": None,
        })

    def patient_number(admission_index: int) -> int:
        if 321 <= admission_index <= 340:
            return 700 + (admission_index - 321)
        if admission_index <= 400:
            return ((admission_index - 1) % 80) + 1
        return 81 + ((admission_index - 401) % 619)

    admissions: list[dict[str, Any]] = []
    admission_starts: list[datetime] = []
    admission_ends: list[datetime | None] = []
    admission_start = datetime(2022, 1, 1, 8)
    for index in range(1, COUNTS["admissions"] + 1):
        start = admission_start + timedelta(hours=index * 11)
        completed = index <= COUNTS["discharge_records"]
        if not completed:
            end = None
        elif 21 <= index <= 29:
            end = start + timedelta(days=10 + index % 3)
        elif index == 30:
            end = start + timedelta(days=16)
        else:
            end = start + timedelta(days=3, hours=(index * 7) % 24)
        admission_type = ("emergency", "urgent", "elective", "outpatient")[index % 4]
        patient_id = local_id(source, "patients", patient_number(index))
        is_deceased = 321 <= index <= 340
        admission = {
            "admission_id": local_id(source, "admissions", index),
            "patient_id": patient_id,
            "admission_datetime": stamp(start, source),
            "admission_type": source_label(source, "admission_type", admission_type),
            "admission_source": ("Emergency referral", "Clinic referral", "Transfer")[index % 3],
            "reason_for_admission": ("Fictional symptom review", "Planned fictional procedure", "Observation")[index % 3],
            "insurance_info": f"Synthetic plan {source}",
            "condition_on_admission": "Fictional educational scenario",
            "admitting_professional": f"FictionalClinician{index % 40:02d}",
            "discharge_datetime": stamp(end, source) if end else None,
            "final_status": ("Deceased" if is_deceased else "Discharged") if completed else None,
        }
        admissions.append(admission)
        admission_starts.append(start)
        admission_ends.append(end)
    rows["admissions"] = admissions

    for index in range(1, COUNTS["admissions"] + 1):
        admission_index = index
        admission = admissions[admission_index - 1]
        primary = admission_index <= COUNTS["discharge_records"]
        common_codes = {"A": "486", "B": "401.9", "C": "250.00", "D": "038.9"}
        common_code = common_codes[source]
        code = (common_code if primary and admission_index <= 100
                else icd[(admission_index - 1) % len(icd)]["icd9_code"])
        when = admission_starts[admission_index - 1] + timedelta(hours=3)
        rows["diagnoses"].append({
            "diagnosis_id": local_id(source, "diagnoses", index),
            "patient_id": admission["patient_id"],
            "admission_id": admission["admission_id"],
            "icd9_code": code,
            "diagnosis_datetime": stamp(when, source),
            "diagnosis_type": "Primary" if primary else ("Secondary" if index % 2 else "Preliminary"),
            "diagnosing_physician": f"FictionalClinician{index % 40:02d}",
        })
    for extra in range(1, COUNTS["diagnoses"] - COUNTS["admissions"] + 1):
        admission_index = extra
        admission = admissions[admission_index - 1]
        code = icd[(extra + 12) % len(icd)]["icd9_code"]
        rows["diagnoses"].append({
            "diagnosis_id": local_id(source, "diagnoses", COUNTS["admissions"] + extra),
            "patient_id": admission["patient_id"], "admission_id": admission["admission_id"],
            "icd9_code": code,
            "diagnosis_datetime": stamp(admission_starts[admission_index - 1] + timedelta(hours=5), source),
            "diagnosis_type": "Secondary",
            "diagnosing_physician": f"FictionalClinician{extra % 40:02d}",
        })

    for admission_index in range(321, 341):
        patient_index = patient_number(admission_index)
        rows["patients"][patient_index - 1]["life_status"] = "Deceased"
        rows["patients"][patient_index - 1]["death_datetime"] = admissions[admission_index - 1]["discharge_datetime"]

    for index in range(1, COUNTS["triage_assessments"] + 1):
        adm = admissions[index - 1]
        when = admission_starts[index - 1] + timedelta(hours=1)
        temperature = 36.5 + (index % 8) / 10
        if source == "D":
            temperature = round(temperature * 9 / 5 + 32, 1)
        rows["triage_assessments"].append({
            "triage_id": local_id(source, "triage_assessments", index),
            "admission_id": adm["admission_id"], "assessment_datetime": stamp(when, source),
            "triage_nurse": f"FictionalNurse{index % 30:02d}", "blood_pressure": "120/80",
            "heart_rate": 72 + index % 25, "respiratory_rate": 14 + index % 6,
            "body_temperature": temperature,
            "oxygen_saturation": 96 + index % 5, "pain_level": index % 11,
            "reported_symptoms": "Fictional symptom description", "known_allergies": None,
            "current_medications": None,
            "priority_level": source_label(source, "priority_level", ("High", "Moderate", "Low")[index % 3]),
        })

    unit_plan: list[tuple[int, str, timedelta, timedelta]] = []
    critical_units = ("ICU", "CCU", "MICU", "SICU")
    for admission_index in range(1, 201):
        if admission_index <= 20:
            sequence = [
                ("Emergency Department", 1, 6), ("ICU", 8, 18), ("CCU", 20, 44),
            ]
        elif 21 <= admission_index <= 30:
            sequence = [
                ("Emergency Department", 1, 6), ("General Medical Ward", 8, 24),
                ("ICU", 32, 24 * 9),
            ]
        elif 131 <= admission_index <= 150:
            sequence = [
                ("Emergency Department", 1, 6), ("General Medical Ward", 8, 19),
                ("Surgical Ward", 20, 36),
            ]
        else:
            unit = critical_units[admission_index % len(critical_units)]
            sequence = [
                ("Emergency Department", 1, 6), ("General Medical Ward", 8, 19),
                (unit, 20, 32),
            ]
        unit_plan.extend((admission_index, unit, timedelta(hours=entry), timedelta(hours=exit_))
                         for unit, entry, exit_ in sequence)
    for admission_index in range(201, 301):
        unit = critical_units[admission_index % len(critical_units)]
        unit_plan.append((admission_index, unit, timedelta(hours=3), timedelta(hours=15)))
    for index, (admission_index, unit, entry_offset, exit_offset) in enumerate(unit_plan, start=1):
        adm = admissions[admission_index - 1]
        entry = admission_starts[admission_index - 1] + entry_offset
        exit_time = admission_starts[admission_index - 1] + exit_offset
        rows["unit_stays"].append({
            "unit_stay_id": local_id(source, "unit_stays", index), "admission_id": adm["admission_id"],
            "unit_type": source_label(source, "unit_type", unit),
            "ward": f"Fictional Ward {index % 8:02d}", "room": f"{index % 60 + 1:02d}",
            "bed_number": f"{index % 4 + 1}", "entry_datetime": stamp(entry, source),
            "exit_datetime": stamp(exit_time, source),
            "responsible_physician": f"FictionalClinician{index % 40:02d}",
            "transfer_reason": ("Initial placement" if index % 3 == 1 else "Fictional unit transfer"),
        })

    orders: list[dict[str, Any]] = []
    for index in range(1, COUNTS["diagnostic_orders"] + 1):
        adm = admissions[index - 1]
        when = admission_starts[index - 1] + timedelta(hours=2)
        orders.append({
            "order_id": local_id(source, "diagnostic_orders", index),
            "admission_id": adm["admission_id"], "requesting_physician": f"FictionalClinician{index % 40:02d}",
            "requested_examination": ("Fictional blood panel", "Fictional imaging", "Fictional screening")[index % 3],
            "request_datetime": stamp(when, source), "clinical_reason": "Fictional educational indication",
            "priority": ("High", "Medium", "Low")[index % 3],
            "order_status": "Completed" if index <= 250 else ("Pending" if index % 2 else "Awaiting Results"),
        })
    rows["diagnostic_orders"] = orders

    for index in range(1, COUNTS["diagnostic_examinations"] + 1):
        order = orders[index - 1]
        when = admission_starts[index - 1] + timedelta(hours=4)
        rows["diagnostic_examinations"].append({
            "exam_id": local_id(source, "diagnostic_examinations", index), "order_id": order["order_id"],
            "exam_type": order["requested_examination"], "exam_datetime": stamp(when, source),
            "performed_by": f"FictionalTechnician{index % 20:02d}",
            "exam_result": "Fictional result for educational use", "exam_status": "Completed",
        })

    for index in range(1, COUNTS["radiology_examinations"] + 1):
        order = orders[index - 1]
        when = admission_starts[index - 1] + timedelta(hours=6)
        rows["radiology_examinations"].append({
            "radiology_exam_id": local_id(source, "radiology_examinations", index),
            "admission_id": order["admission_id"], "order_id": order["order_id"],
            "exam_type": "Fictional radiograph", "exam_datetime": stamp(when, source),
            "body_area": ("Chest", "Abdomen", "Extremity")[index % 3],
            "referring_physician": f"FictionalClinician{index % 40:02d}",
            "radiology_technician": f"FictionalTechnician{index % 20:02d}",
            "exam_status": "Completed", "image_link": None,
        })
        rows["radiology_reports"].append({
            "report_id": local_id(source, "radiology_reports", index),
            "radiology_exam_id": local_id(source, "radiology_examinations", index),
            "radiologist": f"FictionalRadiologist{index % 12:02d}",
            "report_datetime": stamp(when + timedelta(hours=1), source),
            "findings": "Fictional finding", "interpretations": "Fictional interpretation",
            "clinical_conclusion": "Fictional conclusion",
        })

    for index in range(1, COUNTS["surgical_procedures"] + 1):
        adm = admissions[index - 1]
        when = admission_starts[index - 1] + timedelta(hours=7)
        rows["surgical_procedures"].append({
            "procedure_id": local_id(source, "surgical_procedures", index),
            "admission_id": adm["admission_id"], "procedure_name": "Fictional procedure",
            "procedure_datetime": stamp(when, source), "surgeon": f"FictionalSurgeon{index % 15:02d}",
            "operating_room": f"F{index % 8 + 1}", "outcome_notes": "Fictional outcome",
        })

    for index in range(1, COUNTS["clinical_notes"] + 1):
        adm = admissions[index - 1]
        when = (admission_ends[index - 1] - timedelta(hours=1)
                if index <= 50 and admission_ends[index - 1]
                else admission_starts[index - 1] + timedelta(hours=5))
        note_type = ("Discharge Summary" if index <= 50
                     else ("Admission", "Progress", "Consultation")[index % 3])
        note_content = ("Fictional recovery discussion and follow-up plan."
                        if index <= 50 else "Entirely fictional educational note.")
        rows["clinical_notes"].append({
            "note_id": local_id(source, "clinical_notes", index), "admission_id": adm["admission_id"],
            "note_datetime": stamp(when, source), "author_physician": f"FictionalClinician{index % 40:02d}",
            "note_type": note_type,
            "note_content": note_content, "symptoms": "Fictional symptom",
            "physical_examination": "Fictional examination", "clinical_findings": "Fictional finding",
            "suspected_condition": "Fictional condition", "planned_examinations": "Fictional examination",
            "treatment_plan": "Fictional plan",
        })

    for index in range(1, COUNTS["discharge_records"] + 1):
        adm = admissions[index - 1]
        rows["discharge_records"].append({
            "discharge_id": local_id(source, "discharge_records", index),
            "admission_id": adm["admission_id"], "discharge_datetime": adm["discharge_datetime"],
            "discharge_destination": "Fictional residence", "condition_at_discharge": "Fictional stable condition",
            "prescribed_medications": None, "follow_up_instructions": "Fictional follow-up",
            "follow_up_appointments": None, "responsible_physician": adm["admitting_professional"],
            "discharge_summary": "Fictional discharge summary.",
        })
    return rows


def seed_issues(rows: dict[str, list[dict[str, Any]]], source: str) -> list[dict[str, str]]:
    """Apply controlled examples while retaining every planned entity count."""
    rng = random.Random(SOURCE_INFO[source][2] + 1)
    ledger: list[dict[str, str]] = []

    def alter(entity: str, count: int, field: str, value: Any, issue: str) -> None:
        choices = rng.sample(rows[entity], count)
        for row in choices:
            row[field] = value(row) if callable(value) else value
            ledger.append({"entity": entity, "id": str(row.get(ID_FIELDS.get(entity, ""), "")), "issue": issue})

    alter("clinical_notes", 18, "author_physician", None, "missing required value")
    alter("clinical_notes", 70, "note_type", lambda row: row["note_type"].upper() + " ", "whitespace/case variation")
    alter("clinical_notes", 35, "note_datetime", "not-a-date", "invalid timestamp")
    def break_ref(row: dict[str, Any]) -> str:
        row["_container_admission_id"] = row["admission_id"]
        return f"A99999"
    alter("clinical_notes", 35, "admission_id", break_ref, "broken admission reference")
    alter("clinical_notes", 35, "note_datetime",
          lambda row: stamp(datetime(2020, 1, 1, 0, 0, 0), source),
          "chronological inconsistency")
    alter("triage_assessments", 35, "heart_rate", "not-a-number", "invalid numeric value")
    alter("triage_assessments", 17, "triage_nurse", None, "missing required value")
    alter("triage_assessments", 70, "priority_level", lambda row: f" {row['priority_level'].lower()} ", "whitespace/case variation")
    alter("triage_assessments", 210, "known_allergies", None, "missing optional value")
    # Replace 35 note instances with exact copies after other mutations so they
    # remain byte-for-byte duplicate records in the serialized source.
    notes = rows["clinical_notes"]
    copies = deepcopy(notes[:35])
    rows["clinical_notes"] = notes[:465] + copies
    for row in copies:
        ledger.append({"entity": "clinical_notes", "id": row["note_id"], "issue": "exact duplicate"})
    return ledger


def source_b_row(entity: str, row: dict[str, Any]) -> dict[str, Any]:
    canonical = FIELDS[entity]
    aliases = ALIASES_B[entity].split()
    mapped = dict(zip(aliases, (row.get(field) for field in canonical)))
    for key, value in list(mapped.items()):
        if key.endswith("_at") or key in {"birth_date", "recorded_at", "reported_at", "performed_at", "arrived_at", "left_at", "operated_at", "released_at", "death_time"}:
            if value and isinstance(value, str) and len(value) == 19 and value[4] == "-":
                try:
                    dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                    mapped[key] = dt.strftime("%d/%m/%Y %H:%M")
                except ValueError:
                    # Preserve intentionally invalid values for the cleaning task.
                    pass
    # ICD codes remain strings even if they contain only digits.
    return mapped


def flatten_nested(rows: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Return ordered record buckets for nested XML/JSON serialization."""
    admissions = {r["admission_id"]: deepcopy(r) for r in rows["admissions"]}
    for entity in ("diagnoses", "triage_assessments", "unit_stays", "clinical_notes",
                   "surgical_procedures", "discharge_records"):
        key = "discharge_record" if entity == "discharge_records" else entity
        for admission in admissions.values():
            admission[key] = [] if entity != "discharge_records" else None
        for row in rows[entity]:
            parent_id = row.get("_container_admission_id", row["admission_id"])
            parent = admissions.get(parent_id)
            if parent is not None:
                item = {key: value for key, value in row.items() if not key.startswith("_")}
                if entity == "discharge_records":
                    parent[key] = deepcopy(item)
                else:
                    parent[key].append(deepcopy(item))
    for admission in admissions.values():
        admission["diagnostic_orders"] = []
    order_by_id = {}
    for row in rows["diagnostic_orders"]:
        item = deepcopy(row)
        item["examinations"] = []
        admissions[row["admission_id"]]["diagnostic_orders"].append(item)
        order_by_id[row["order_id"]] = item
    for row in rows["diagnostic_examinations"]:
        order_by_id[row["order_id"]]["examinations"].append(deepcopy(row))
    reports = {r["radiology_exam_id"]: deepcopy(r) for r in rows["radiology_reports"]}
    for row in rows["radiology_examinations"]:
        item = deepcopy(row)
        item["report"] = reports.get(row["radiology_exam_id"])
        order_by_id[row["order_id"]]["radiology_examinations"] = (
            order_by_id[row["order_id"]].get("radiology_examinations", []) + [item]
        )
    return list(admissions.values())


def write_a(rows: dict[str, list[dict[str, Any]]], folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for entity, records in rows.items():
        with (folder / f"{entity}.txt").open("w", encoding="utf-8", newline="") as stream:
            fields = FIELDS[entity]
            stream.write("|".join(fields) + "\n")
            for row in records:
                vals = []
                for field in fields:
                    value = row.get(field)
                    text = r"\N" if value is None else str(value)
                    if any(char in text for char in "|\r\n"):
                        raise ValueError(f"Unsafe delimiter/newline in {entity}.{field}")
                    vals.append(text)
                stream.write("|".join(vals) + "\n")


def write_b(rows: dict[str, list[dict[str, Any]]], folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for entity, records in rows.items():
        aliases = ALIASES_B[entity].split()
        with (folder / f"{entity}.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=aliases, extrasaction="ignore")
            writer.writeheader()
            for row in records:
                writer.writerow(source_b_row(entity, row))


def xml_value(parent: ET.Element, key: str, value: Any) -> None:
    if value is None:
        return
    if key == "report":
        key = "radiology_report"
    if isinstance(value, dict):
        child = ET.SubElement(parent, key)
        for subkey, subvalue in value.items():
            xml_value(child, subkey, subvalue)
    elif isinstance(value, list):
        container = ET.SubElement(parent, key)
        singular = {
            "diagnoses": "diagnosis", "patients": "patient", "unit_stays": "unit_stay",
            "diagnostic_orders": "diagnostic_order", "examinations": "examination",
            "radiology_examinations": "radiology_examination",
            "clinical_notes": "clinical_note", "surgical_procedures": "surgical_procedure",
        }.get(key, key[:-1] if key.endswith("s") else "item")
        for item in value:
            child = ET.SubElement(container, singular)
            if isinstance(item, dict):
                for subkey, subvalue in item.items():
                    xml_value(child, subkey, subvalue)
            else:
                child.text = "" if item is None else str(item)
    else:
        child = ET.SubElement(parent, key)
        child.text = "" if value is None else str(value)


def write_c(rows: dict[str, list[dict[str, Any]]], folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    # Separate well-formed chunks limit the impact of a damaged document.
    root = ET.Element("hospitalSystem", source="C")
    patients = ET.SubElement(root, "patients")
    for row in rows["patients"]:
        xml_value(patients, "patient", row)
    codes = ET.SubElement(root, "icd9Dictionary")
    for row in rows["icd9_dictionary"]:
        xml_value(codes, "entry", row)
    admissions = flatten_nested(rows)
    for chunk_start in range(0, len(admissions), 100):
        chunk_root = ET.Element("hospitalSystem", source="C")
        collection = ET.SubElement(chunk_root, "admissions")
        for admission in admissions[chunk_start:chunk_start + 100]:
            xml_value(collection, "admission", admission)
        tree = ET.ElementTree(chunk_root)
        ET.indent(tree, space="  ")
        tree.write(folder / f"admissions_{chunk_start // 100 + 1:02d}.xml",
                   encoding="utf-8", xml_declaration=True)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(folder / "reference_and_patients.xml", encoding="utf-8", xml_declaration=True)


def write_d(rows: dict[str, list[dict[str, Any]]], folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "patients.json").open("w", encoding="utf-8") as stream:
        json.dump({"system": {"source": "D"}, "patients": rows["patients"]},
                  stream, ensure_ascii=False, indent=2)
    with (folder / "icd9_dictionary.json").open("w", encoding="utf-8") as stream:
        json.dump({"system": {"source": "D"}, "icd9_dictionary": rows["icd9_dictionary"]},
                  stream, ensure_ascii=False, indent=2)
    admissions = flatten_nested(rows)
    for start in range(0, len(admissions), 100):
        path = folder / f"admissions_{start // 100 + 1:02d}.json"
        with path.open("w", encoding="utf-8") as stream:
            json.dump({"system": {"source": "D", "chunk": start // 100 + 1},
                       "admissions": admissions[start:start + 100]},
                      stream, ensure_ascii=False, indent=2)


def generate(reference: Path, root: Path = RAW_ROOT, seed_defects: bool = True) -> None:
    if root.exists() and any(root.iterdir()):
        raise ValueError(f"Output directory is not empty; preserving existing files: {root}")
    icd = load_icd9(reference)
    manifest: dict[str, Any] = {"synthetic_only": True, "tool": "Python standard library generator, authored with ChatGPT assistance",
                               "prompt_summary": "Entirely fictional educational hospital data; no real patients or personal information; fabricated identities and clinical scenarios; valid referenced ICD-9 data supplied separately.",
                               "icd9_reference_file": reference.name,
                               "record_count_rule": "entity instances; includes duplicates",
                               "sources": {}}
    for source, (continent, fmt, seed, timezone) in SOURCE_INFO.items():
        rows = make_source(source, icd)
        ledger = seed_issues(rows, source) if seed_defects else []
        folder = root / source
        if fmt == "TXT":
            write_a(rows, folder)
        elif fmt == "CSV":
            write_b(rows, folder)
        elif fmt == "XML":
            write_c(rows, folder)
        else:
            write_d(rows, folder)
        manifest["sources"][source] = {
            "continent": continent, "format": fmt, "seed": seed, "timezone": timezone,
            "entity_counts": {entity: len(records) for entity, records in rows.items()},
            "total_raw_entities": sum(map(len, rows.values())),
            "issue_ledger": ledger,
        }
    root.mkdir(parents=True, exist_ok=True)
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")




def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--icd9-reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=RAW_ROOT)
    parser.add_argument("--no-seeded-issues", action="store_true")
    args = parser.parse_args()
    try:
        generate(args.icd9_reference, args.output, not args.no_seeded_issues)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
