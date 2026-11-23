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





