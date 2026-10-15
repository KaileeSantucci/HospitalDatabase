CREATE TABLE Patients (
	patient_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	first_name VARCHAR(40) NOT NULL,
	last_name VARCHAR(40) NOT NULL,
	date_of_birth DATE NOT NULL,
	gender VARCHAR(20),
	address VARCHAR(60) NOT NULL,
	telephone_number VARCHAR(15) NOT NULL,
	health_insurance_number VARCHAR(12) NOT NULL UNIQUE,
	emergency_contact_name VARCHAR(40),
	emergency_contact_phone VARCHAR(15),
	life_status VARCHAR(12) NOT NULL
		CHECK (life_status IN ('Alive', 'Deceased')),
	death_datetime TIMESTAMP,

	CHECK((life_status = 'Alive' AND death_datetime IS NULL)
			OR (life_status = 'Deceased'))
);

CREATE TABLE Admissions (
	admission_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	patient_id INTEGER NOT NULL,
	admission_datetime TIMESTAMP NOT NULL,
	admission_type VARCHAR(20) NOT NULL
		CHECK (admission_type IN ('emergency', 'urgent', 'elective', 'outpatient', 'newborn', 'other')),
	admission_source VARCHAR(60),
	reason_for_admission VARCHAR(120),
	insurance_info VARCHAR(100),
	condition_on_admission TEXT,
	admitting_professional VARCHAR(60),
	discharge_datetime TIMESTAMP,
	final_status VARCHAR(20)
		CHECK (final_status IN ('Discharged', 'Deceased', 'Transferred', 'Other')),

	FOREIGN KEY (patient_id) REFERENCES Patients(patient_id),

	CHECK (discharge_datetime IS NULL
			OR discharge_datetime >= admission_datetime),
	CHECK ((final_status IS NULL AND discharge_datetime IS NULL)
			OR (final_status IS NOT NULL AND discharge_datetime IS NOT NULL))
);

CREATE TABLE ICD9Dictionary (
	icd9_code VARCHAR(10) PRIMARY KEY,
	official_title VARCHAR(150) NOT NULL,
	description TEXT,
	disease_category VARCHAR(100)
);

CREATE TABLE Diagnosis (
	diagnosis_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	patient_id INTEGER NOT NULL,
	admission_id INTEGER NOT NULL,
	icd9_code VARCHAR(10) NOT NULL,
	diagnosis_datetime TIMESTAMP NOT NULL,
	diagnosis_type VARCHAR(40) NOT NULL
		CHECK (diagnosis_type IN ('Primary', 'Secondary', 'Preliminary')),
	diagnosing_physician VARCHAR(40) NOT NULL,

	FOREIGN KEY (patient_id) REFERENCES Patients(patient_id),
	FOREIGN KEY (admission_id) REFERENCES Admissions(admission_id),
	FOREIGN KEY (icd9_code) REFERENCES ICD9Dictionary(icd9_code)
);

CREATE TABLE TriageAssessments (
	triage_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	admission_id INTEGER NOT NULL,
	assessment_datetime TIMESTAMP NOT NULL,
	triage_nurse VARCHAR(60) NOT NULL,
	blood_pressure VARCHAR(10),
	heart_rate SMALLINT,
	respiratory_rate SMALLINT,
	body_temperature NUMERIC(4,1),
	oxygen_saturation NUMERIC(5,2),
	pain_level SMALLINT
		CHECK (pain_level BETWEEN 0 AND 10),
	reported_symptoms TEXT,
	known_allergies TEXT,
	current_medications TEXT,
	priority_level VARCHAR(20) NOT NULL
		CHECK (priority_level IN ('High', 'Moderate', 'Low')),

	FOREIGN KEY (admission_id) REFERENCES Admissions(admission_id)
);

CREATE TABLE ClinicalNotes (
	note_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	admission_id INTEGER NOT NULL,
	note_datetime TIMESTAMP NOT NULL,
	author_physician VARCHAR(60) NOT NULL,
	note_type VARCHAR(20) NOT NULL
		CHECK(note_type IN ('Admission', 'Progress', 'Consultation', 'Discharge Summary', 'Other')),
	note_content TEXT,
	symptoms TEXT,
	physical_examination TEXT,
	clinical_findings TEXT,
	suspected_condition VARCHAR(100),
	planned_examinations TEXT,
	treatment_plan TEXT,

	FOREIGN KEY (admission_id) REFERENCES Admissions(admission_id)
);

CREATE TABLE UnitStays (
	unit_stay_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	admission_id INTEGER NOT NULL,
	unit_type VARCHAR(40) NOT NULL
		CHECK (unit_type IN (
			'Emergency Department',
			'General Medical Ward',
			'ICU',
			'CCU',
			'MICU',
			'SICU',
			'Surgical Ward',
			'Other')),
	ward VARCHAR(40),
	room VARCHAR(10),
	bed_number VARCHAR(10),
	entry_datetime TIMESTAMP NOT NULL,
	exit_datetime TIMESTAMP,
	responsible_physician VARCHAR(60) NOT NULL,
	transfer_reason VARCHAR(60),

	FOREIGN KEY (admission_id) REFERENCES Admissions(admission_id),

	CHECK(exit_datetime IS NULL OR exit_datetime >= entry_datetime)
);

CREATE TABLE DiagnosticOrders (
	order_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	admission_id INTEGER NOT NULL,
	requesting_physician VARCHAR(40) NOT NULL,
	requested_examination VARCHAR(100) NOT NULL,
	request_datetime TIMESTAMP NOT NULL,
	clinical_reason TEXT,
	priority VARCHAR(20) NOT NULL
		CHECK (priority IN ('High', 'Medium', 'Low')),
	order_status VARCHAR(40) NOT NULL
		CHECK (order_status IN ('Completed', 'Awaiting Results', 'Pending', 'Cancelled', 'Other')),

	FOREIGN KEY (admission_id) REFERENCES Admissions(admission_id)
);

CREATE TABLE DiagnosticExaminations (
	exam_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	order_id INTEGER NOT NULL,
	exam_type VARCHAR(100) NOT NULL,
	exam_datetime TIMESTAMP,
	performed_by VARCHAR(40) NOT NULL,
	exam_result TEXT,
	exam_status VARCHAR(40) NOT NULL
		CHECK (exam_status IN ('Completed', 'Awaiting Results', 'Pending', 'Cancelled', 'Other')),

	FOREIGN KEY (order_id) REFERENCES DiagnosticOrders(order_id)
);

CREATE TABLE RadiologyExaminations (
	radiology_exam_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	admission_id INTEGER NOT NULL,
	order_id INTEGER NOT NULL,
	exam_type VARCHAR(60) NOT NULL,
	exam_datetime TIMESTAMP NOT NULL,
	body_area VARCHAR(60) NOT NULL,
	referring_physician VARCHAR(40) NOT NULL,
	radiology_technician VARCHAR(40) NOT NULL,
	exam_status VARCHAR(40) NOT NULL
		CHECK (exam_status IN ('Completed', 'Awaiting Results', 'Other')),
	image_link TEXT,

	FOREIGN KEY (admission_id) REFERENCES Admissions(admission_id),
	FOREIGN KEY (order_id) REFERENCES DiagnosticOrders(order_id)
);

CREATE TABLE RadiologyReports (
	report_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	radiology_exam_id INTEGER NOT NULL UNIQUE,
	radiologist VARCHAR(40) NOT NULL,
	report_datetime TIMESTAMP NOT NULL,
	findings TEXT,
	interpretations TEXT,
	clinical_conclusion TEXT,

	FOREIGN KEY (radiology_exam_id) REFERENCES RadiologyExaminations(radiology_exam_id)
);

CREATE TABLE SurgicalProcedures (
	procedure_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, 
	admission_id INTEGER NOT NULL,
	procedure_name VARCHAR(60) NOT NULL,
	procedure_datetime TIMESTAMP NOT NULL,
	surgeon VARCHAR(40) NOT NULL,
	operating_room VARCHAR(10),
	outcome_notes TEXT,

	FOREIGN KEY (admission_id) REFERENCES Admissions(admission_id)
);

CREATE TABLE DischargeRecords (
	discharge_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	admission_id INTEGER NOT NULL UNIQUE,
	discharge_datetime TIMESTAMP NOT NULL,
	discharge_destination VARCHAR(60),
	condition_at_discharge TEXT,
	prescribed_medications TEXT,
	follow_up_instructions TEXT,
	follow_up_appointments TEXT,
	responsible_physician VARCHAR(40) NOT NULL,
	discharge_summary TEXT,

	FOREIGN KEY (admission_id) REFERENCES Admissions(admission_id)
);
