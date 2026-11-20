import pandas as pd
from task1_inspect_load import load_source 

#1 loading every source into the DataFrames
raw = {}
for source in ["A","B","C","D"]:
    entities = load_source(source) # loading {table name :list of records}
    raw[source] = {}
    for table in entities:
        raw[source][table] = pd.DataFrame(entities[table])
                   

#2 rename source B's columns to the common names, Source A, C, D use the phase 1 names 
#so only B changes

B_COLUMN_NAMES = {
     "admissions": {
        "visit_ref": "admission_id", "person_ref": "patient_id",
        "admitted_at": "admission_datetime", "visit_class": "admission_type",
        "origin": "admission_source", "presenting_reason": "reason_for_admission",
        "payer_details": "insurance_info", "admission_condition": "condition_on_admission",
        "responsible_clinician": "admitting_professional",
        "released_at": "discharge_datetime", "exit_status": "final_status",
    },
    "clinical_notes": {
        "note_ref": "note_id", "visit_ref": "admission_id",
        "authored_at": "note_datetime", "author": "author_physician",
        "note_class": "note_type", "text": "note_content",
        "exam_findings": "physical_examination", "suspected_diagnosis": "suspected_condition",
        "planned_tests": "planned_examinations", "plan": "treatment_plan",
    },
    "diagnoses": {
        "diagnosis_ref": "diagnosis_id", "person_ref": "patient_id",
        "visit_ref": "admission_id", "code": "icd9_code",
        "recorded_at": "diagnosis_datetime", "role": "diagnosis_type",
        "clinician": "diagnosing_physician",
    },
    "diagnostic_examinations": {
        "test_ref": "exam_id", "request_ref": "order_id",
        "test_class": "exam_type", "performed_at": "exam_datetime",
        "operator": "performed_by", "result_text": "exam_result",
        "test_state": "exam_status",
    },
    "diagnostic_orders": {
        "request_ref": "order_id", "visit_ref": "admission_id",
        "ordered_by": "requesting_physician", "test_requested": "requested_examination",
        "ordered_at": "request_datetime", "indication": "clinical_reason",
        "urgency": "priority", "request_state": "order_status",
    },
    "discharge_records": {
        "release_ref": "discharge_id", "visit_ref": "admission_id",
        "released_at": "discharge_datetime", "destination": "discharge_destination",
        "condition_on_release": "condition_at_discharge",
        "medications_on_release": "prescribed_medications",
        "followup_instructions": "follow_up_instructions",
        "followup_appointments": "follow_up_appointments",
        "responsible_clinician": "responsible_physician", "summary": "discharge_summary",
    },
    "icd9_dictionary": {
        "code": "icd9_code", "official_name": "official_title",
        "long_description": "description", "category": "disease_category",
    },
    "patients": {
        "person_ref": "patient_id", "given_name": "first_name",
        "family_name": "last_name", "birth_date": "date_of_birth",
        "sex": "gender", "home_address": "address", "phone": "telephone_number",
        "coverage_id": "health_insurance_number",
        "emergency_name": "emergency_contact_name",
        "emergency_phone": "emergency_contact_phone",
        "vital_status": "life_status", "death_time": "death_datetime",
    },
    "radiology_examinations": {
        "image_exam_ref": "radiology_exam_id", "visit_ref": "admission_id",
        "request_ref": "order_id", "modality": "exam_type",
        "performed_at": "exam_datetime", "anatomical_site": "body_area",
        "referrer": "referring_physician", "technologist": "radiology_technician",
        "image_state": "exam_status", "image_uri": "image_link",
    },
    "radiology_reports": {
        "image_report_ref": "report_id", "image_exam_ref": "radiology_exam_id",
        "reporting_radiologist": "radiologist", "reported_at": "report_datetime",
        "observations": "findings", "interpretation": "interpretations",
        "conclusion": "clinical_conclusion",
    },
    "surgical_procedures": {
        "operation_ref": "procedure_id", "visit_ref": "admission_id",
        "operation_name": "procedure_name", "operated_at": "procedure_datetime",
        "theatre": "operating_room", "outcome": "outcome_notes",
    },
    "triage_assessments": {
        "triage_ref": "triage_id", "visit_ref": "admission_id",
        "assessed_at": "assessment_datetime", "nurse": "triage_nurse",
        "bp": "blood_pressure", "pulse_bpm": "heart_rate",
        "respirations_min": "respiratory_rate", "temperature_c": "body_temperature",
        "oxygen_pct": "oxygen_saturation", "pain_score": "pain_level",
        "symptoms": "reported_symptoms", "allergies": "known_allergies",
        "medications": "current_medications", "acuity": "priority_level",
    },
    "unit_stays": {
        "stay_ref": "unit_stay_id", "visit_ref": "admission_id",
        "ward_class": "unit_type", "ward_name": "ward", "room_no": "room",
        "bed_no": "bed_number", "arrived_at": "entry_datetime",
        "left_at": "exit_datetime", "attending_clinician": "responsible_physician",
    },
} 

for table, new_names in B_COLUMN_NAMES.items():
    raw["B"][table] = raw["B"][table].rename(columns = new_names)


#source c leaves out tags that are always empty, so some of its tables are missing columns
#adding each missing column back as an empty column then putting the colums in the same order as source A

for source in ["B","C", "D"]:
    for table in raw["A"]:
        df = raw[source][table]
        for column in raw["A"][table].columns:
            if column not in df.columns:
                df[column] = None #create the missing column (empty)

        raw[source][table] = df[list(raw["A"][table].columns)] #same column order as A

#checking every source should have exactly the same columns as A 
for table in raw["A"]:
    for source in ["B","C","D"]:
        if list(raw[source][table].columns) != list(raw["A"][table].columns):
            print("source",source, table, ": columns do not match")
print("Column check finished.")

