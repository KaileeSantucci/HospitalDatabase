
# Import Task 3 CSV files into the Phase 2 PostgreSQL database.
# Run from the repository root using the Python virtual environment.

# Reruns are insert-only: identical records are skipped, new records are inserted.
# Conflicting records cause a transaction rollback.
# Existing records are never updated or deleted.

import csv
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import psycopg
from psycopg import sql


# Define the target PostgreSQL database.
DATABASE = "hospital_phase2_db"

# Locate the integrated CSV files using a relative path.
DATA_DIR = Path(__file__).resolve().parent / "synthetic_integrated_data"

# Map each CSV filename to its corresponding PostgreSQL table.
# Parent tables must also be imported before dependent tables.
TABLES = [
    ("sources", "sources"),
    ("icd9_dictionary", "icd9dictionary"),
    ("patients", "patients"),
    ("patient_source_mapping", "patientsourcemapping"),
    ("admissions", "admissions"),
    ("diagnoses", "diagnosis"),
    ("triage_assessments", "triageassessments"),
    ("clinical_notes", "clinicalnotes"),
    ("unit_stays", "unitstays"),
    ("diagnostic_orders", "diagnosticorders"),
    ("surgical_procedures", "surgicalprocedures"),
    ("discharge_records", "dischargerecords"),
    ("diagnostic_examinations", "diagnosticexaminations"),
    ("radiology_examinations", "radiologyexaminations"),
    ("radiology_reports", "radiologyreports"),
]

# Define the primary key of each PostgreSQL table.
PRIMARY_KEYS = {
    "sources": "source_code",
    "icd9dictionary": "icd9_code",
    "patients": "patient_id",
    "patientsourcemapping": "mapping_id",
    "admissions": "admission_id",
    "diagnosis": "diagnosis_id",
    "triageassessments": "triage_id",
    "clinicalnotes": "note_id",
    "unitstays": "unit_stay_id",
    "diagnosticorders": "order_id",
    "surgicalprocedures": "procedure_id",
    "dischargerecords": "discharge_id",
    "diagnosticexaminations": "exam_id",
    "radiologyexaminations": "radiology_exam_id",
    "radiologyreports": "report_id",
}

# Identify columns that must be converted to integers.
INTEGER_COLUMNS = {
    "time_difference_hours",
    "patient_id",
    "mapping_id",
    "admission_id",
    "diagnosis_id",
    "triage_id",
    "note_id",
    "unit_stay_id",
    "order_id",
    "procedure_id",
    "discharge_id",
    "exam_id",
    "radiology_exam_id",
    "report_id",
    "respiratory_rate",
    "pain_level",
}

# Identify columns that require decimal values
DECIMAL_COLUMNS = {
    "heart_rate",
    "body_temperature",
    "oxygen_saturation",
}

# Convert CSV values to appropriate Python data types
def convert_value(column, value):

    # Convert empty fields to PostgreSQL NULL values
    if value == "":
        return None

    # Convert integer columns from strings to integers
    if column in INTEGER_COLUMNS:
        return int(value)

    # Convert decimal columns while preserving numeric precision
    if column in DECIMAL_COLUMNS:
        return Decimal(value)

    # Convert the date of birth to a date object
    if column == "date_of_birth":
        return date.fromisoformat(value)

    # Convert timestamp columns to datetime objects
    if column.endswith("_datetime"):
        return datetime.fromisoformat(value)

    # Keep all remaining values as strings.
    return value


# Import records from one CSV file into its corresponding table
def import_table(cursor, csv_name, table_name):

    # Locate the CSV file and get the table's primary key.
    file_path = DATA_DIR / f"{csv_name}.csv"
    primary_key = PRIMARY_KEYS[table_name]

    # Initialize counters for the inserted and skipped records
    inserted = 0
    skipped = 0

    # Open the CSV file and read each row as a dictionary
    with file_path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        # Retrieve column names from the CSV header
        columns = reader.fieldnames

        # Ensure the CSV contains headers as well as the required primary key
        if not columns or primary_key not in columns:
            raise ValueError(f"Invalid CSV headers in {csv_name}.csv")

        # Construct the list of SQL column names
        column_list = sql.SQL(", ").join(
            sql.Identifier(column) for column in columns
        )

        # Create a parameter placeholder for each column
        placeholders = sql.SQL(", ").join(
            sql.Placeholder() for column in columns
        )

        # Create a parameterized INSERT query to prevent duplicate primary keys
        insert_query = sql.SQL(
            "INSERT INTO {} ({}) VALUES ({}) "
            "ON CONFLICT ({}) DO NOTHING"
        ).format(
            sql.Identifier("public", table_name),
            column_list,
            placeholders,
            sql.Identifier(primary_key),
        )

        # Create a SELECT query to retrieve an existing record
        select_query = sql.SQL(
            "SELECT {} FROM {} WHERE {} = %s"
        ).format(
            column_list,
            sql.Identifier("public", table_name),
            sql.Identifier(primary_key),
        )

        # Process each record in the CSV file
        for row in reader:
            try:
                # Check that the row contains the correct number of fields
                if None in row or any(value is None for value in row.values()):
                    raise ValueError("Incorrect number of CSV fields")

                # Convert each field to its appropriate data type
                values = tuple(
                    convert_value(column, row[column])
                    for column in columns
                )

                # Insert the record using parameterized SQL
                cursor.execute(insert_query, values)

                # If a new record was insrted, increase the counter
                if cursor.rowcount == 1:
                    inserted += 1

                else:
                    # Retrieve the primary key of the existing record
                    key_value = convert_value(
                        primary_key, row[primary_key]
                    )

                    # Retrieve the existing record from the database
                    cursor.execute(select_query, (key_value,))
                    existing = cursor.fetchone()

                    # Skip the record if its values are identical
                    if existing == values:
                        skipped += 1
                    else:
                        # Reject records with the same key but different values
                        raise ValueError(
                            f"Conflicting record: {primary_key}={key_value}"
                        )

            except Exception as error:
                # Report the filename and line number where the error occurred
                raise ValueError(
                    f"{csv_name}.csv, line {reader.line_num}: {error}"
                ) from error

    # Return the total inserted and skipped records for this table
    return inserted, skipped

# Synchronize identity columns after importing explicit IDs
def sync_identity(cursor, table_name):

    # Retrieve the primary key of the current table
    primary_key = PRIMARY_KEYS[table_name]

    # Skip tables that do not use generated identity columns
    if table_name in ("sources", "icd9dictionary"):
        return

    # Finds the highest primary key currently stored in the table
    cursor.execute(
        sql.SQL("SELECT MAX({}) FROM {}").format(
            sql.Identifier(primary_key),
            sql.Identifier("public", table_name),
        )
    )

    # Retrieve the maximum ID from the query result
    maximum_id = cursor.fetchone()[0]

    # Only restart the identity sequence if the table contains records
    if maximum_id is not None:

        # Set the next generated ID to the maximum existing ID plus one
        cursor.execute(
            sql.SQL(
                "ALTER TABLE {} ALTER COLUMN {} RESTART WITH {}"
            ).format(
                sql.Identifier("public", table_name),
                sql.Identifier(primary_key),
                sql.Literal(maximum_id + 1),
            )
        )


# Execute the complete import within one transaction
def main():

    # Store the import results for each table
    results = []

    try:
        # Establish a connection to the Phase 2 database
        with psycopg.connect(dbname=DATABASE) as connection:

            # Create a cursor to execute SQL statements
            with connection.cursor() as cursor:

                # Import tables in dependency order to preserve foreign keys
                for csv_name, table_name in TABLES:
                    inserted, skipped = import_table(
                        cursor, csv_name, table_name
                    )

                    # Store the number of inserted and skipped records
                    results.append((table_name, inserted, skipped))

                # Synchronize identity sequences after all records are imported
                for csv_name, table_name in TABLES:
                    sync_identity(cursor, table_name)

        # Commit the transaction automatically when the connection block ends

    except Exception as error:

        # Roll back the transaction automatically if an error occurs
        print("Import failed. All changes have been rolled back.")

        # Display the error message
        print(error)

        # Return a nonzero exit code to indicate failure
        return 1

    # Display the results after a successful import.
    print("\nImport completed successfully.\n")

    # Print the column headers for the import summary
    print(f"{'Table':25} {'Imported':>10} {'Skipped':>10}")
    print("-" * 47)

    # Display the import statistics for each table
    for table_name, inserted, skipped in results:
        print(f"{table_name:25} {inserted:10} {skipped:10}")

    # Calculate the total number of inserted records
    total_inserted = sum(result[1] for result in results)

    # Calculate the total number of skipped records
    total_skipped = sum(result[2] for result in results)

    # Display the overall import totals
    print("-" * 47)
    print(f"{'Total':25} {total_inserted:10} {total_skipped:10}")

    # Return zero to indicate successful execution
    return 0


# Run the main function when the script is executed directly
if __name__ == "__main__":
    raise SystemExit(main())
