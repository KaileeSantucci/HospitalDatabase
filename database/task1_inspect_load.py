import csv
import json
import logging
from collections import Counter
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

# Locate the input and output folders.
SCRIPT_FOLDER = Path(__file__).resolve().parent
RAW_FOLDER = SCRIPT_FOLDER / "synthetic_raw"
PROFILE_FOLDER = SCRIPT_FOLDER / "synthetic_profiles"
PROFILE_FILE = PROFILE_FOLDER / "initial_profile.json"
ERROR_FILE = PROFILE_FOLDER / "read_errors.log"

#Tell the program which file format belongs to each source.
SOURCE_FORMATS = {"A": "txt", "B": "csv", "C": "xml", "D": "json"}

#This is a dictionary which is responsible for storing the tag/key names that
#tell the XML and JSON loaders which tags represents actual entity records, Check if the field/current key 
#is recognized
XML_RECORDS = { #which XML tages represent records
    "patient": "patients",
    "entry": "icd9_dictionary",
    "admission": "admissions",
    "diagnosis": "diagnoses",
    "triage_assessment": "triage_assessments",
    "unit_stay": "unit_stays",
    "diagnostic_order": "diagnostic_orders",
    "examination": "diagnostic_examinations",
    "radiology_examination": "radiology_examinations",
    "radiology_report": "radiology_reports",
    "clinical_note": "clinical_notes",
    "surgical_procedure": "surgical_procedures",
    "discharge_record": "discharge_records",
}
JSON_RECORDS = { #which JSON keys represent records
    "patients": "patients",
    "icd9_dictionary": "icd9_dictionary",
    "admissions": "admissions",
    "diagnoses": "diagnoses",
    "triage_assessments": "triage_assessments",
    "unit_stays": "unit_stays",
    "diagnostic_orders": "diagnostic_orders",
    "examinations": "diagnostic_examinations",
    "radiology_examinations": "radiology_examinations",
    "report": "radiology_reports",
    "clinical_notes": "clinical_notes",
    "surgical_procedures": "surgical_procedures",
    "discharge_record": "discharge_records",
}
XML_CONTAINERS = {
    "diagnoses", "patients", "unit_stays", "diagnostic_orders",
    "examinations", "radiology_examinations", "clinical_notes",
    "surgical_procedures", "triage_assessments",
}

def report_error(file_path, place, reason):
    """Write a problem to the log so the record is not silently lost."""
    logging.error("%s | %s | %s", file_path, place, reason)


#Loading the TXT files. A pipe ( | ) separates each field
def load_txt(file_path):
    rows = []
    with file_path.open(encoding="utf-8") as file:
        header = file.readline().rstrip("\r\n").split("|")
        if not header or header == [""]:
            report_error(file_path, "header", "Missing header")
            return rows

        for line_number, line in enumerate(file, start=2):
            values = line.rstrip("\r\n").split("|")
            if len(values) != len(header):
                report_error(file_path, f"line {line_number}", "Wrong number of fields")
                continue
            rows.append(dict(zip(header, values)))
    return rows


#Loading the CSV files
def load_csv(file_path):
    rows = []
    with file_path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            report_error(file_path, "header", "Missing header")
            return rows

        for line_number, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                report_error(file_path, f"line {line_number}", "Wrong number of CSV fields")
                continue
            rows.append(row)
    return rows


#Loading the XML files
#Extracting the actual info, receives an element that has already been identified by as record and extracts its fields.
def load_xml_record(element):
    row = {} #create an empty dictionary
    for child in element: #iterate through the children
        if len(child) == 0 and child.tag not in XML_CONTAINERS:  #check if the element is a leaf element, or nested
            row[child.tag] = child.text or "" #stores the fiedl and the value
    return row #returns the extracted record

#this is function is for finding records
def visit_xml(element, records):
    #determine if the element is a record, using the dictionary created from the load_xml function.
    #distinguish between entitiy records and other XML elements
    if element.tag in XML_RECORDS:
        entity = XML_RECORDS[element.tag] #retrieves the name of the entity
        records.setdefault(entity, []).append(load_xml_record(element)) #stores the record
        #.setdefault(): retrieves the list associated with the entity
        #.load_xml_record(): extracts the fiedl from the current XML record and returns them as a dictionary
        #.append(): adds the record to the list of record that belong to that entity

    #Keep visiting children because records can be nested inside admissions/orders
    #Rescursion
    for child in element:
        visit_xml(child, records)

#file_path is the location of the XML file and records is the dictionary data
#structure where the extracted records will be loaded/stored
def load_xml(file_path, records):
    try:
        root = ET.parse(file_path).getroot() #parses the XML file, ET is the element tree used for XML files in a python library
        visit_xml(root, records)
    except (ET.ParseError, OSError, UnicodeError) as error:
        report_error(file_path, "document", error)


#Loading the JSON files
#value is the current json file/list/value being examined, records is the dictionary containing the extracted records
#entit is the entity type of the current record, place is current location within the JSON hierarchy, nd the file path is the location of original JSON file
def visit_json(value, records, entity=None, place="$", file_path=""):
    if isinstance(value, dict):
        #Starting to extract individual records, we check if the entity had been identified, then
        #we find the key, iterate through every key-value pair and exclude dictionaries or lists.
        if entity:
            row = {key: item for key, item in value.items()
                   if key not in JSON_RECORDS and not isinstance(item, (dict, list))}
            records.setdefault(entity, []).append(row) #allows us to store the extracted records

        #explore the nested information
        for key, child in value.items():
            child_entity = JSON_RECORDS.get(key)
            child_place = f"{place}.{key}"
            if child_entity and isinstance(child, list): #recognized entity contains a list
                for index, item in enumerate(child):
                    if isinstance(item, dict):
                        visit_json(item, records, child_entity,
                                   f"{child_place}[{index}]", file_path)
                    else:
                        report_error(file_path, f"{child_place}[{index}]", "Expected a record object")
            elif child_entity and isinstance(child, dict): #recognized entity contains a dictionary
                visit_json(child, records, child_entity, child_place, file_path)
            elif child_entity and child is not None: #recognized entity contains an unexpected value
                report_error(file_path, child_place, "Expected a record object or list")
            elif isinstance(child, (dict, list)): #unrecognized container
                visit_json(child, records, place=child_place, file_path=file_path)

    elif isinstance(value, list): #checks if the individual list iem has the expected format/dictionary structure before continuing
        for index, item in enumerate(value):
            visit_json(item, records, entity, f"{place}[{index}]", file_path)

def load_json(file_path, records):
    try:
        document = json.loads(file_path.read_text(encoding="utf-8"))
        visit_json(document, records, file_path=str(file_path))
    except (json.JSONDecodeError, OSError, UnicodeError) as error:
        report_error(file_path, "document", error)


#Now we need to pick the right loader for each file and gather records by
#entity type. example of entity types: (patient, diagnosis, tirage assesment,etc.)
def load_source(source):
    file_format = SOURCE_FORMATS[source]
    source_folder = RAW_FOLDER / source
    records = {}

    for file_path in sorted(source_folder.glob(f"*.{file_format}")):
        if file_format in {"txt", "csv"}:
            entity = file_path.stem
            try:
                if file_format == "txt":
                    rows = load_txt(file_path)
                else:
                    rows = load_csv(file_path)
                records.setdefault(entity, []).extend(rows)
            except (OSError, UnicodeError, csv.Error) as error:
                report_error(file_path, "file", error)

        elif file_format == "xml":
            load_xml(file_path, records)

        else:  # JSON
            load_json(file_path, records)

    return records


#try to determine the kind of information a value represents WITHOUT changing it
def value_type(value):
    if isinstance(value, bool):
        return "boolean" #have to check boolean first
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"

    #check if a string is representing a number
    text = str(value)
    try:
        float(text)
        return "number"
    except ValueError:
        pass

    #check if a string is representing a date
    for date_format in ("%Y-%m-%d", "%d/%m/%Y", "%Y%m%d",
                        "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            datetime.strptime(text, date_format)
            return "date/time"
        except ValueError:
            pass
    try:
        datetime.fromisoformat(text)
        return "date/time"
    except ValueError:
        return "string"


#count missing values, duplicates, and collect examples for one entity
def profile_entity(rows):
    #goes thorugh every record and collects unique field names, then sorts then alphabetically
    fields = sorted({field for row in rows for field in row})
    #initialize empty dictionaries
    missing = {}
    data_types = {}
    examples = {}
    invalid = {}

    #counting the missing values, examines one field at a time across all records for that entity
    for field in fields:
        values = [row.get(field) for row in rows]
        present = [value for value in values if value not in (None, "", r"\N")]
        missing[field] = len(values) - len(present) #missing-value counts is explicity require in assignemtn

        #field type inference, we want to determine the type of the entire field, not just one value
        if not present:
            data_types[field] = "unknown"
        else:
            if "code" in field.lower():
                data_types[field] = "string"
            else:
                types = Counter(value_type(value) for value in present)
                data_types[field] = types.most_common(1)[0][0]

        spellings = {}
        for value in present:
            text = str(value)
            spellings.setdefault(text.strip().casefold(), set()).add(text)
        formatting_examples = [text for variants in spellings.values() if len(variants) > 1
                               for text in sorted(variants)]
        formatting_examples += [str(value) for value in present
                                if str(value) != str(value).strip()]
        if formatting_examples:
            examples[field] = list(dict.fromkeys(formatting_examples))[:3]

        # Values that do not match the most common inferred type are examples to review.
        most_common_type = data_types[field]
        invalid_values = [str(value) for value in present
                          if most_common_type not in {"unknown", "string"}
                          and value_type(value) != most_common_type]
        if invalid_values:
            invalid[field] = list(dict.fromkeys(invalid_values))[:3]

    # An exact duplicate has the same field values.
    rows_as_text = [json.dumps(row, sort_keys=True, ensure_ascii=False, default=str) for row in rows]
    exact_counts = Counter(rows_as_text)
    exact_duplicates = sum(count - 1 for count in exact_counts.values())

    sample_values = {
        field: list(dict.fromkeys(str(row.get(field)) for row in rows
                                  if row.get(field) not in (None, "", r"\N")))[:3]
        for field in fields
    }
    return {
        "record_count": len(rows),
        "field_names": fields,
        "inferred_types": data_types,
        "missing_value_counts": missing,
        "exact_duplicate_count": exact_duplicates,
        "sample_values": sample_values,
        "formatting_examples": examples,
        "invalid_value_examples": invalid,
    }


#Load and profile every source continent, then save results in one readable JSON report.
def main():
    PROFILE_FOLDER.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=ERROR_FILE, level=logging.ERROR,
                        format="%(levelname)s %(message)s", filemode="w")

    #loop through all 4 sources, and profile them
    all_sources = {}
    for source, file_format in SOURCE_FORMATS.items():
        records = load_source(source)
        entities = {}
        for entity, rows in sorted(records.items()):
            entities[entity] = profile_entity(rows)
        all_sources[source] = {
            "format": file_format.upper(),
            "record_count": sum(item["record_count"] for item in entities.values()),
            "entities": entities,
        }

    PROFILE_FILE.write_text(json.dumps(all_sources, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Finished. Profile: {PROFILE_FILE}")
    print(f"Input problems, if any: {ERROR_FILE}")


if __name__ == "__main__":
    main()
