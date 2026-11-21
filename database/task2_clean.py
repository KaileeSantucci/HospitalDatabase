import pandas as pd
from task1_inspect_load import load_source 

#1: loading every source into the DataFrames
raw = {}
for source in ["A","B","C","D"]:
    entities = load_source(source) # loading {table name :list of records}
    raw[source] = {}
    for table in entities:
        raw[source][table] = pd.DataFrame(entities[table])
                   

#2: rename source B's columns to the common names, Source A, C, D use the phase 1 names 
#so only B changes

B_column_names = {
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

for table, new_names in B_column_names.items():
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
            print("Columns don't match in", source, table)
print("Column check finished.")

#3: Removing the extra spaces at the start and end of the text values
spaces_removed = 0 #starts the count at 0
for source in ["A", "B", "C","D"]: 
    for table in raw[source]:
        df = raw[source][table]
        for column in df.columns:
            before = df[column].fillna("") #fillna: so emty cells are not counted as changes/ spaces removed
            df[column] = df[column].apply(lambda x: x.strip() if isinstance(x, str) else x)
            after = df[column].fillna("")
            spaces_removed = spaces_removed + (before != after).sum()
print("Extra spaces removed:", spaces_removed)

#4: mapping each source's category labels to the values allowed by the pahse 1 schema
# dictionary says: label used by a source (in lowercase) value our schema allows

label_transitions = {
    ("admissions", "admission_type"): {
        "emergency": "emergency", "er": "emergency",
        "urgent": "urgent", "urgent admission": "urgent", "urgent care": "urgent",
        "elective": "elective", "routine": "elective", "planned": "elective", "scheduled": "elective",
        "outpatient": "outpatient", "ambulatory": "outpatient", "clinic": "outpatient",
    },
    ("triage_assessments", "priority_level"): {
        "high": "High", "critical": "High", "p1": "High", "immediate": "High",
        "moderate": "Moderate", "urgent": "Moderate", "p2": "Moderate",
        "low": "Low", "routine": "Low", "p3": "Low",
    },
    ("unit_stays", "unit_type"): {
        "emergency department": "Emergency Department", "a&e": "Emergency Department",
        "ed": "Emergency Department", "er": "Emergency Department",
        "general medical ward": "General Medical Ward", "ward": "General Medical Ward",
        "medical ward": "General Medical Ward", "general ward": "General Medical Ward",
        "icu": "ICU", "critical care": "ICU", "intensive care": "ICU", "icu-adult": "ICU",
        "ccu": "CCU", "cardiac care": "CCU", "cardiac icu": "CCU",
        "micu": "MICU", "medical intensive care": "MICU", "medical icu": "MICU", "icu-medical": "MICU",
        "sicu": "SICU", "surgical intensive care": "SICU", "surgical icu": "SICU", "icu-surgical": "SICU",
        "surgical ward": "Surgical Ward", "surgery ward": "Surgical Ward",
    },
    ("clinical_notes", "note_type"): {
        "admission": "Admission", "progress": "Progress",
        "consultation": "Consultation", "discharge summary": "Discharge Summary",
    },
}
labels_mapped = 0  #starts at count 0
for source in ["A","B","C", "D"]: #going through each hospital source
    for(table,column), mapping in label_transitions.items(): #each (table,column) and its dictionary
        df = raw[source][table] #the table we are currently cleaning 
        before = df[column].fillna("") #save the values before changing them, so you cna count the change
        df[column] = df[column].apply(lambda x: x.lower() if isinstance(x, str) else x) # lowercase first so 'P1' and 'p1' and spaces like ' p1 ' match the same dictionary key 
        df[column] = df[column].replace(mapping) #swaping each label for schema's value
        after = df[column].fillna("") #values after change
        labels_mapped = labels_mapped + (before != after).sum() #sum of the values changed

        #checking if any label not in the dictionary would still be lowercase and not allowed
        allowed = mapping.values() #the values that the schema allows are eg. High, Low , Moderate
        missing_labels = [] #the missing labels
        for value in df[column]: #looking at every value in the column 
            if isinstance(value, str) and value not in allowed and value not in missing_labels: #text that is not allowed value 
                missing_labels.append(value) #add it to the list 
        if len(missing_labels) > 0: #if something was found then print it once
            print("No translation for", missing_values, "in", source, table, column)
print("Category labels mapped:", labels_mapped) #total number of labels changed

#5: Missing values
#each source writes "empty" differently: A uses \N, B uses an empty string '', C and D use 'None'
#need to turn every missing marker into 1 real empty value "None" 

missing_values = ["\\N", ""]

missing_converted = 0 # start count at 0
for source in ["A","B","C", "D"]: #going through each hospital source
    for table in raw[source]:
        df = raw[source][table]
        for column in df.columns:
            before = df[column].isna().sum() #empty cells before 
            df[column] = df[column].apply(lambda x: None if isinstance(x,str) and x in missing_values else x) #if the value is text and is one of th emarkers, replace it with None
            after = df[column].isna().sum() #empty cells after 
            missing_converted = missing_converted + (after - before)

print("Missing values are converted into empty values:", missing_converted)

#decideing what to do wih each missing value
#needed columns (NOT NULL, plus the ids) the record is rejected 
#other column is optional -> the record keepts with an empty value

needed_columns ={

    "patients": ["patient_id", "first_name", "last_name", "date_of_birth", "address",
                 "telephone_number", "health_insurance_number", "life_status"],
    "admissions": ["admission_id", "patient_id", "admission_datetime", "admission_type"],
    "icd9_dictionary": ["icd9_code", "official_title"],
    "diagnoses": ["diagnosis_id", "patient_id", "admission_id", "icd9_code",
                  "diagnosis_datetime", "diagnosis_type", "diagnosing_physician"],
    "triage_assessments": ["triage_id", "admission_id", "assessment_datetime",
                           "triage_nurse", "priority_level"],
    "clinical_notes": ["note_id", "admission_id", "note_datetime", "author_physician", "note_type"],
    "unit_stays": ["unit_stay_id", "admission_id", "unit_type", "entry_datetime",
                   "responsible_physician"],
    "diagnostic_orders": ["order_id", "admission_id", "requesting_physician",
                          "requested_examination", "request_datetime", "priority", "order_status"],
    "diagnostic_examinations": ["exam_id", "order_id", "exam_type", "performed_by", "exam_status"],
    "radiology_examinations": ["radiology_exam_id", "admission_id", "order_id", "exam_type",
                               "exam_datetime", "body_area", "referring_physician",
                               "radiology_technician", "exam_status"],
    "radiology_reports": ["report_id", "radiology_exam_id", "radiologist", "report_datetime"],
    "surgical_procedures": ["procedure_id", "admission_id", "procedure_name",
                            "procedure_datetime", "surgeon"],
    "discharge_records": ["discharge_id", "admission_id", "discharge_datetime",
                          "responsible_physician"],

}

not_accepted = [] #every rejected and not accepted reccord goes in this array
for source in ["A", "B", "C", "D"]:
    for table, required in needed_columns.items():
        df = raw[source][table]
        id_column = df.columns[0] #the first column is in the records ID
        for column in required:
            missing_rows = df[df[column].isna()] #boolean filtering: rows where this column is empty
            for record_id in missing_rows[id_column]:
                not_accepted.append({"source": source,"table": table, "record_id": record_id,"reason":"missing needed value:"+column})
            df = df[df[column].notna()] #keep only the rows that have a value
        raw[source][table] = df
print("Records that were not accepted for a missing required value:", len(not_accepted))

#6: duplicates
#keep 1 copy and remove the others

removed_duplicates = 0
for source in ["A", "B", "C", "D"]:
    for table in raw[source]:
        df = raw[source][table]
        before = len(df)
        df= df.drop_duplicates() #removing duplicates
        removed_duplicates = removed_duplicates + (before - len(df))
        raw[source][table] = df
print("Duplicate Records removed:", removed_duplicates)

#after removing every duplicate then every id should appear only 1
# the id becomes the primary key, check while printing a warning if an id is still repeated 
#that means that 2 different records share an id

for source in ["A", "B", "C", "D"]:
    for table in raw[source]:
        df = raw[source][table]
        id_column = df.columns[0] #first column is the records ids
        repeated_ids = len(df) - len(set(df[id_column])) #rows - unique ids = repeated ids
        if repeated_ids > 0:
            print("Repeated ids of the source", source, table, ":", repeated_ids)
print("Id duplicates check is done.")

#7: numbers and units 
#triage measurements are stored as text and they are turned into real numbers 
#a value that is not a number or is not possible is flagged, the record is kept only that value is emptied

realistic_num_ranges = {
    "heart_rate": (20, 250),
    "respiratory_rate": (5, 60),
    "body_temperature": (30, 45),       # in degrees Celsius
    "oxygen_saturation": (50, 100),
    "pain_level": (0, 10),              # same as the CHECK in the schema
}

outlier = [] #values that are flagged and were emptied, with the original value and the reason

for source in ["A", "B", "C", "D"]:
   df = raw[source]["triage_assessments"]
   for column in realistic_num_ranges:
        original = df[column].copy() #keeping orginial values 
        df[column] = pd.to_numeric(df[column], errors = "coerce") #test to: num and not num: to empty

        #source D measures temp in F: convert to celsius
        if source == "D" and column == "body_temperature":
            df[column] = df[column].apply(lambda x: round((x-32)*5/9,1))

        lowest, highest = realistic_num_ranges[column]
        for record_id, old_value, new_value in zip(df["triage_id"], original, df[column]): #going through the rows: record ids, value before, value after 
            if pd.isna(new_value) and pd.notna(old_value): #if it had a value but it was not a number
                outlier.append({"source": source, "table": "triage_assessments", "record_id": record_id,
                                "column": column, "original_value": old_value,
                                "reason": "not a number"})
            if pd.notna(new_value) and (new_value < lowest or new_value > highest): #if it is a number, but outside the possible realistic range 
                outlier.append({"source": source, "table": "triage_assessments", "record_id": record_id,
                                "column": column, "original_value": old_value,
                                "reason": "outside the possible range"})
        df[column] = df[column].apply(lambda x: None if pd.notna(x) and (x < lowest or x > highest) else x)
   raw[source]["triage_assessments"] = df
print("Invalid numeric values that were flagged and emptied:", len(outlier))

#8: dates and the time zones
#every source writes dates differently and each source is in its own time zone:
#A(toronto): 2022-01-01 19:00:00            no time zone written in the file
#B(paris): 01/01/2022 19:00               day first, no time zone written in the
#C(singapore): 2022-01-01T19:00:00+08:00      time zone written at the end
#D(brisbane): 2022-01-01T19:00:00+10:00      time zone written at the end
#all the dates and times are converted to one format in UTC (the same clock for every source)

TimeStamps_format = { #how each source writes a date & time
    "A": "%Y-%m-%d %H:%M:%S",
    "B": "%d/%m/%Y %H:%M",
    "C": "%Y-%m-%dT%H:%M:%S", #%z = the time zone at the end 
    "D": "%Y-%m-%dT%H:%M:%S",
}

date_format = { #how each source writes a date only date of birth
    "A": "%Y-%m-%d",
    "B": "%d/%m/%Y",
    "C": "%Y%m%d",
    "D": "%Y-%m-%d",
}

time_difference = { #(UTC)how many hours each source is ahead of UTC
    "A": -4,
    "B": 2,
    "C": 8,
    "D": 10, 
}


dates_converted = 0
bad_dates = 0
for source in ["A","B","C","D"]:
    for table in raw[source]:
        df=raw[source][table]
        id_column = df.columns[0]
        for column in df.columns:
            if column.endswith("_datetime") or column == "date_of_birth": #taking only the data columns: names that end with _datetime and date_of_birth
                original = df[column].copy() #keep the original values 

                if column.endswith("_datetime"): #date + time columns
                    # C and D write the time zone at the end (+08:00): keep only the first 19 characters,
                    # the date and time, because the offset is already in UTC_OFFSET
                    if source in ["C", "D"]:
                        df[column] = df[column].apply(lambda x: x[:19] if isinstance(x,str)else x)
                    df[column] = pd.to_datetime(df[column], format = TimeStamps_format[source], errors = "coerce") #a value that is not a valid date becomes emtpy
                    df[column] = df[column]-pd.Timedelta(hours=time_difference[source]) #Timedelta : means the length of time, subtracts the source's time differnce 

                if column == "date_of_birth":#date only column : date of firth (no time = no time zone)
                    df[column] = pd.to_datetime(df[column], format = date_format[source], errors = 'coerce').dt.date 

                #finding the values that had a date before but are now empty (not a valid date)
                for record_id, old_value, new_value in zip(df[id_column], original, df[column]):
                    if pd.notna(old_value) and pd.isna(new_value):
                        bad_dates = bad_dates + 1 
                        if column in needed_columns[table]:
                            not_accepted.append({"source": source, "table": table, "record_id": record_id, "problem": "invalid date:" + column})
                        else:
                            outlier.append({"source": source, "table": table, "record_id": record_id, "column": column, "original_value": old_value, "problem": "invalid date"})
                dates_converted = dates_converted + df[column].notna().sum()

                #removing the records whose required date was invvalid
            for column in needed_columns[table]:
                df = df[df[column].notna()]
            raw[source][table] = df
print("The Dates converted to UTC:", dates_converted)
print("Invalid dates that were found:", bad_dates)

#9: chronology (events in the right order) and relationships (references that exist)

#chronology
#the event of an admission can't happen before the patient was admitted 
event_times = {
    "triage_assessments": "assessment_datetime",
    "clinical_notes": "note_datetime",
    "unit_stays": "entry_datetime",
    "diagnoses": "diagnosis_datetime",
    "diagnostic_orders": "request_datetime",
    "radiology_examinations": "exam_datetime",
    "surgical_procedures": "procedure_datetime",
    "discharge_records": "discharge_datetime",
}

wrong_order = 0
for source in ["A", "B", "C", "D"]:
    admissions = raw[source]["admissions"]

    #an admission can't be discharged before it started
    rejected_rows = admissions[admissions["discharge_datetime"] < admissions["admission_datetime"]]
    for record_id in rejected_rows["admission_id"]:
        not_accepted.append({"source": source, "table": "admissions", "record_id": record_id, "problem": "discharged before admission"})
        wrong_order = wrong_order + 1
    bad_ids = list(rejected_rows["admission_id"])
    admissions = admissions[admissions["admission_id"].apply(lambda x: x not in bad_ids)] #keeping the others
    raw[source]["admissions"] = admissions

    #a unit stay can't end before it started 
    stays = raw[source]["unit_stays"]
    rejected_rows = stays[stays["exit_datetime"] < stays["entry_datetime"]]
    for record_id in rejected_rows["unit_stay_id"]:
        not_accepted.append({"source": source, "table": "unit_stays", "record_id": record_id, "reason": "left the unit before entering it"})
        wrong_order = wrong_order + 1
    bad_ids = list(rejected_rows["unit_stay_id"])
    raw[source]["unit_stays"] = stays[stays["unit_stay_id"].apply(lambda x: x not in bad_ids)]

    #every event must happen at or after its admission
    for table, time_column in event_times.items():
        df = raw[source][table]
        id_column = df.columns[0]

        joined = pd.merge(df,admissions[["admission_id", "admission_datetime"]], on="admission_id", how="left") #merge (like when doing an SQL JOIN) add the admission time next to each event
        before_admissions = joined[joined[time_column] < joined["admission_datetime"]]
        for record_id in before_admissions[id_column]:
            not_accepted.append({"source": source, "table": table,"record_id": record_id, "problem": "happened before the admission: " + time_column})

            wrong_order = wrong_order + 1
        bad_ids = list(before_admissions[id_column])
        raw[source][table] = df[df[id_column].apply(lambda x: x not in bad_ids)]
print("Records removed (happened before admission):", wrong_order)


#Relationship
relationships = [
    ("admissions", "patient_id", "patients"),
    ("diagnoses", "admission_id", "admissions"),
    ("diagnoses", "patient_id", "patients"),
    ("diagnoses", "icd9_code", "icd9_dictionary"),
    ("triage_assessments", "admission_id", "admissions"),
    ("clinical_notes", "admission_id", "admissions"),
    ("unit_stays", "admission_id", "admissions"),
    ("diagnostic_orders", "admission_id", "admissions"),
    ("diagnostic_examinations", "order_id", "diagnostic_orders"),
    ("radiology_examinations", "admission_id", "admissions"),
    ("radiology_examinations", "order_id", "diagnostic_orders"),
    ("radiology_reports", "radiology_exam_id", "radiology_examinations"),
    ("surgical_procedures", "admission_id", "admissions"),
    ("discharge_records", "admission_id", "admissions"),
]

missing_parents = 0
for source in ["A", "B", "C", "D"]:
    for child, column, parent in relationships:
        df = raw[source][child]
        id_column = df.columns[0]
        parent_df = raw[source][parent]
        parent_ids = list(parent_df[parent_df.columns[0]]) #all the ids of the parent table

        #true if the value is one of the parent's ids
        found = df[column].apply(lambda x: x in parent_ids)
        for record_id in df[found == False][id_column]:
            not_accepted.append({"source": source, "table": child, "record_id": record_id, "problem": "points to a " + parent + " record that does not exist: " + column})

            missing_parents = missing_parents +1 
            raw[source][child] = df[found]
print("Records removed (parent doesn't exist):", missing_parents)

 

    

