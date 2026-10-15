-- 1. Ensure a diagnosis belongs to the patient admitted.
ALTER TABLE Admissions
ADD CONSTRAINT unique_admission_patient
UNIQUE (admission_id, patient_id);

ALTER TABLE Diagnosis
ADD CONSTRAINT fk_diagnosis_admission_patient
FOREIGN KEY (admission_id, patient_id)
REFERENCES Admissions(admission_id, patient_id);

-- 2. Ensure a radiology examination belongs to the same admission as its diagnostic order.
ALTER TABLE DiagnosticOrders
ADD CONSTRAINT unique_order_admission
UNIQUE (order_id, admission_id);

ALTER TABLE RadiologyExaminations
ADD CONSTRAINT fk_radiology_order_admission
FOREIGN KEY (order_id, admission_id)
REFERENCES DiagnosticOrders(order_id, admission_id);
