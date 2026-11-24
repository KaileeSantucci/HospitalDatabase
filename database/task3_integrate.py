#task 3: combinning the 4 cleaned sources into 1 database
#1. loading the cleaned data from task 2 (1 folder per source)
#ids and ICD-9 code4s stay text 
#dtype=str keeps every value as text the way task 2 has it saved
import pandas as pd

table_names = ["patients", "admissions", "icd9_dictionary", "diagnoses", "triage_assessments",
               "clinical_notes", "unit_stays", "diagnostic_orders", "diagnostic_examinations",
               "radiology_examinations", "radiology_reports", "surgical_procedures", "discharge_records"]

data = {}
for source in ["A", "B", "C", "D"]:
    data[source] = {}
    for table in table_names:
        data[source][table] = pd.read_csv("synthetic_clean_data/Source_" + source + "/" + table + ".csv", dtype = str)

#checking the num of records loaded for each source
for source in ["A", "B", "C", "D"]:
    records_loaded = 0
    for table in table_names:
        records_loaded = records_loaded + len(data[source][table])
    print("Source", source, "records loaded:",records_loaded)

#2: one shared ICD-9 dictionary
#ICD-9 codes are standard, so a code means the same thing in every hospital
#the 4 sources each have their own copy of the dictionary (put together into 1 table)

all_dictionaries = pd.concat([data["A"]["icd9_dictionary"], data["B"]["icd9_dictionary"], data["C"]["icd9_dictionary"], data["D"]["icd9_dictionary"]])
print("ICD-9 rows before removing duplicates:", len(all_dictionaries))

icd9_dictionary = all_dictionaries.drop_duplicates() #same copies of the same code are only kept 1
print("ICD-9 codes after removing the duplicates:", len(icd9_dictionary))

#checking if code is still repeated (this would mean 2 sources give it different titles)
repeated_codes = len(icd9_dictionary) - len(set(icd9_dictionary["icd9_code"]))
if repeated_codes > 0:
    print(repeated_codes, "ICD-9 codes have more than one title")
print("ICD-9 check done")

#3: checking if the same patient is shown in more than 1 source
# my rule: 2 patient records are the same person only if they have the same health insurance number
# 1 insurance num = 1 person
# same full name & date of birth with a different insurance number = uncertain match which will not be merged but it will be counted 

all_patients = pd.concat([data["A"]["patients"], data["B"]["patients"],
                          data["C"]["patients"], data["D"]["patients"]])
print("Patients in all 4 sources:", len(all_patients))

#same health insurance num = same person
same_insurance = len(all_patients) - len(set(all_patients["health_insurance_number"]))
print("Same person (same insurance number):", same_insurance)

#same full name and date of brithday = uncertain match 
#not merged 
full_name_and_birth = all_patients["first_name"] + "" + all_patients["last_name"]
same_name_and_birth = len(all_patients) - len(set(full_name_and_birth))
print("Uncertain matches (same full name and date of birth):", same_name_and_birth)

#only the first name and date of birth (close to being the same person but is not)
first_name_and_birth = all_patients["first_name"] + "" + all_patients["date_of_birth"]
look_alike = len(all_patients) - len(set(first_name_and_birth))
print("Look-alikes (only same first name and date of birth):", look_alike)

#4: new ids for every record (surrogate keys)
# A's P00001 and B's P00001 are different patients so they can't keep the same id
#every record gets a new number 
#orginal id and source code is kept so that it can always trace a record back to where it came from (surrogate key + natural key)

tables_with_ids = ["patients", "admissions", "diagnoses", "triage_assessments", "clinical_notes",
                   "unit_stays", "diagnostic_orders", "diagnostic_examinations",
                   "radiology_examinations", "radiology_reports", "surgical_procedures", "discharge_records"]

#icd9_dictionary is not in the list: its codes are standard, they don't change
for table in tables_with_ids:
    new_ids = 1 #the new ids of each table start at 1
    for source in ["A", "B", "C", "D"]:
        df = data[source][table]
        id_column = df.columns[0] #first column is the record ids 
        df["source_code"] = source #which source the record comes from 
        df["source_record_id"] = df[id_column] #the original id 
        df[id_column] = list(range(new_ids, new_ids + len(df))) #the new ids
        new_ids = new_ids + len(df)
        data[source][table] = df
    print(table, "new ids: 1 to", new_ids -1)
print("Example of sources A and B of patient P00001:")
for source in ["A", "B", "C", "D"]:
    patients = data[source]["patients"]
    first_patient = patients[patients["source_record_id"] == "P00001"]
    print("Source", source, "P00001 = ", list(first_patient["patient_id"]))

#5: updating the links(foreign keys) to the new ids
#source B's admission still says patient_id = P00001 but now that patient is 801
#for each look up of the patient new id using its original id (source_record_id) with merge
#has to be done per source bc the same old id exists in every source and means a different patient in each one.
#(child table, column that points to the parent, parent table)

foreign_keys = [("admissions", "patient_id", "patients"),
                ("diagnoses", "patient_id", "patients"),
                ("diagnoses", "admission_id", "admissions"),
                ("triage_assessments", "admission_id", "admissions"),
                ("clinical_notes", "admission_id", "admissions"),
                ("unit_stays", "admission_id", "admissions"),
                ("diagnostic_orders", "admission_id", "admissions"),
                ("diagnostic_examinations", "order_id", "diagnostic_orders"),
                ("radiology_examinations", "admission_id", "admissions"),
                ("radiology_examinations", "order_id", "diagnostic_orders"),
                ("radiology_reports", "radiology_exam_id", "radiology_examinations"),
                ("surgical_procedures", "admission_id", "admissions"),
                ("discharge_records", "admission_id", "admissions")]

foreign_keys_updated = 0
foreign_keys_not_found = 0
for source in ["A", "B", "C", "D"]:
    for child, column, parent in foreign_keys:
        child_table = data[source][child]
        parent_table = data[source][parent]
        parent_id_column = parent_table.columns[0]
        old_and_new_ids = parent_table[["source_record_id", parent_id_column]] #old id = new id for the parent table
        old_and_new_ids = old_and_new_ids.rename(columns = {"source_record_id": column, parent_id_column:"new_id"})
        merged = pd.merge(child_table, old_and_new_ids, on=column, how="left")

        foreign_keys_not_found = foreign_keys_not_found + merged["new_id"].isna().sum()
        merged[column] = merged["new_id"]
        merged = merged.drop("new_id", axis=1)
        data[source][child] = merged

        foreign_keys_updated = foreign_keys_updated + len(merged)
print("Foreign keys whose parent was not found:", foreign_keys_not_found)
print("Foreign keys updated to the new ids:", foreign_keys_updated)

#6 combinning the four sources into 1 table each 
integrate = {}
for table in tables_with_ids:
    integrate[table] = pd.concat([data["A"][table], data["B"][table], data["C"][table], data["D"][table]])
    print(table, "rows after combinning the 4 sources:", len(integrate[table]))

#already did the icd-9 dictionary combined
integrate["icd9_dictionary"] = icd9_dictionary
print("icd9_dictionary rows:", len(integrate["icd9_dictionary"]))

#7. save the integrated data
import os
os.makedirs("synthetic_integrated_data", exist_ok=True)

#(13 integrated tables) 
for table in integrate:
    integrate[table].to_csv("synthetic_integrated_data/" + table + ".csv", index=False)
    print("Saved", table, "with", len(integrate[table]), "rows")

#new table where each source comes from
sources = pd.DataFrame({"source_code":["A", "B", "C", "D"], "city": ["Toronto", "Paris", "Singapore", "Brisbane"],
                        "continent": ["North America", "Europe", "Asia", "Oceania"], "file_format": ["TXT", "CSV", "XML", "JSON"],
                        "time_difference_hours": [-4,2,8,10]})
sources.to_csv("synthetic_integrated_data/sources.csv", index=False)
print("Saved sources with", len(sources), "rows")

#new table of original patient id in each source = new patient id
patients = integrate["patients"]
patient_source_mapping = pd.DataFrame({"mapping_id": list(range(1, len(patients)+1)),
                                       "source_code": list(patients["source_code"]), "source_patient_id": list(patients["source_record_id"]),
                                       "patient_id": list(patients["patient_id"])})
patient_source_mapping.to_csv("synthetic_integrated_data/patient_source_mapping.csv", index=False)
print("Saved patient_source_mapping with", len(patient_source_mapping), "rows")

#uncertain matches (same full name and data of birth, separately, not merged)
full_name_and_birth = patients["first_name"] + " " + patients["last_name"] + " " + patients["date_of_birth"]
uncertain_matches = patients[full_name_and_birth.duplicated(keep=False)]
uncertain_matches = uncertain_matches[["patient_id", "source_code", "source_record_id", "first_name", "last_name", "date_of_birth", "health_insurance_number"]]
uncertain_matches.to_csv("synthetic_integrated_data/uncertain_patient_matches.csv", index=False)
print("saved uncertain_patient_matches with", len(uncertain_matches), "rows")



