-- SOEN363 Phase 1 synthetic dataset checks.

SELECT 'orphan admissions' AS check_name, (SELECT COUNT(*) FROM Admissions a LEFT JOIN Patients p ON p.patient_id=a.patient_id WHERE p.patient_id IS NULL) AS violation_count;
SELECT 'diagnosis patient/admission mismatch' AS check_name, (SELECT COUNT(*) FROM Diagnosis d JOIN Admissions a ON a.admission_id=d.admission_id WHERE d.patient_id<>a.patient_id) AS violation_count;
SELECT 'missing primary diagnosis for completed admissions' AS check_name, (SELECT COUNT(*) FROM Admissions a WHERE a.discharge_datetime IS NOT NULL AND NOT EXISTS (SELECT 1 FROM Diagnosis d WHERE d.admission_id=a.admission_id AND d.diagnosis_type='Primary')) AS violation_count;
SELECT 'discharge timestamp mismatch' AS check_name, (SELECT COUNT(*) FROM DischargeRecords d JOIN Admissions a ON a.admission_id=d.admission_id WHERE d.discharge_datetime<>a.discharge_datetime) AS violation_count;
SELECT 'discharge before admission' AS check_name, (SELECT COUNT(*) FROM Admissions WHERE discharge_datetime<admission_datetime) AS violation_count;
SELECT 'unit exit before entry' AS check_name, (SELECT COUNT(*) FROM UnitStays WHERE exit_datetime<entry_datetime) AS violation_count;
SELECT 'radiology order/admission mismatch' AS check_name, (SELECT COUNT(*) FROM RadiologyExaminations r JOIN DiagnosticOrders o ON o.order_id=r.order_id WHERE r.admission_id<>o.admission_id) AS violation_count;
SELECT 'radiology outside admission' AS check_name, (SELECT COUNT(*) FROM RadiologyExaminations r JOIN Admissions a ON a.admission_id=r.admission_id WHERE r.exam_datetime<a.admission_datetime OR (a.discharge_datetime IS NOT NULL AND r.exam_datetime>a.discharge_datetime)) AS violation_count;
SELECT 'surgery outside admission' AS check_name, (SELECT COUNT(*) FROM SurgicalProcedures s JOIN Admissions a ON a.admission_id=s.admission_id WHERE s.procedure_datetime<a.admission_datetime OR (a.discharge_datetime IS NOT NULL AND s.procedure_datetime>a.discharge_datetime)) AS violation_count;
SELECT 'deceased patient missing date' AS check_name, (SELECT COUNT(*) FROM Patients WHERE life_status='Deceased' AND death_datetime IS NULL) AS violation_count;

-- Number of rows per table:
SELECT 'Patients' AS table_name, COUNT(*) AS row_count FROM Patients;
SELECT 'Admissions' AS table_name, COUNT(*) AS row_count FROM Admissions;
SELECT 'ICD9Dictionary' AS table_name, COUNT(*) AS row_count FROM ICD9Dictionary;
SELECT 'Diagnosis' AS table_name, COUNT(*) AS row_count FROM Diagnosis;
SELECT 'TriageAssessments' AS table_name, COUNT(*) AS row_count FROM TriageAssessments;
SELECT 'ClinicalNotes' AS table_name, COUNT(*) AS row_count FROM ClinicalNotes;
SELECT 'UnitStays' AS table_name, COUNT(*) AS row_count FROM UnitStays;
SELECT 'DiagnosticOrders' AS table_name, COUNT(*) AS row_count FROM DiagnosticOrders;
SELECT 'DiagnosticExaminations' AS table_name, COUNT(*) AS row_count FROM DiagnosticExaminations;
SELECT 'RadiologyExaminations' AS table_name, COUNT(*) AS row_count FROM RadiologyExaminations;
SELECT 'RadiologyReports' AS table_name, COUNT(*) AS row_count FROM RadiologyReports;
SELECT 'SurgicalProcedures' AS table_name, COUNT(*) AS row_count FROM SurgicalProcedures;
SELECT 'DischargeRecords' AS table_name, COUNT(*) AS row_count FROM DischargeRecords;

-- Scenario coverage for all 20 assignment questions (each count should be > 0).
SELECT 'Q01 high-priority emergency' AS scenario, (SELECT COUNT(*) FROM Admissions a JOIN TriageAssessments t USING(admission_id) WHERE a.admission_type='emergency' AND t.priority_level='High') AS matching_records;
SELECT 'Q02 patients with >3 admissions' AS scenario, (SELECT COUNT(*) FROM (SELECT patient_id FROM Admissions GROUP BY patient_id HAVING COUNT(*)>3) q) AS matching_records;
SELECT 'Q03 discharged without surgery' AS scenario, (SELECT COUNT(*) FROM Admissions a WHERE a.final_status='Discharged' AND NOT EXISTS (SELECT 1 FROM SurgicalProcedures s WHERE s.admission_id=a.admission_id)) AS matching_records;
SELECT 'Q04 radiology and surgery' AS scenario, (SELECT COUNT(DISTINCT s.admission_id) FROM SurgicalProcedures s JOIN RadiologyExaminations r USING(admission_id)) AS matching_records;
SELECT 'Q05 ICU or CCU >7 days' AS scenario, (SELECT COUNT(*) FROM UnitStays WHERE unit_type IN ('ICU','CCU') AND exit_datetime-entry_datetime>INTERVAL '7 days') AS matching_records;
SELECT 'Q06 patients with zero admissions' AS scenario, (SELECT COUNT(*) FROM Patients p WHERE NOT EXISTS (SELECT 1 FROM Admissions a WHERE a.patient_id=p.patient_id)) AS matching_records;
SELECT 'Q07 emergency to ICU/CCU' AS scenario, (SELECT COUNT(DISTINCT a.admission_id) FROM Admissions a JOIN UnitStays u USING(admission_id) WHERE a.admission_source='Emergency Department' AND u.unit_type IN ('ICU','CCU')) AS matching_records;
SELECT 'Q08 repeated primary ICD-9 in ICU/CCU' AS scenario, (SELECT COALESCE(MAX(n),0) FROM (SELECT d.icd9_code,COUNT(*) n FROM Diagnosis d WHERE d.diagnosis_type='Primary' AND EXISTS(SELECT 1 FROM UnitStays u WHERE u.admission_id=d.admission_id AND u.unit_type IN ('ICU','CCU')) GROUP BY d.icd9_code) q) AS matching_records;
SELECT 'Q09 MICU SICU ICU CCU' AS scenario, (SELECT COUNT(DISTINCT unit_type) FROM UnitStays WHERE unit_type IN ('MICU','SICU','ICU','CCU')) AS matching_records;
SELECT 'Q10 surgery before ICU/CCU' AS scenario, (SELECT COUNT(*) FROM SurgicalProcedures s JOIN UnitStays u USING(admission_id) WHERE u.unit_type IN ('ICU','CCU') AND s.procedure_datetime<u.entry_datetime) AS matching_records;
SELECT 'Q11 patients without radiology' AS scenario, (SELECT COUNT(*) FROM Patients p WHERE NOT EXISTS(SELECT 1 FROM Admissions a JOIN RadiologyExaminations r USING(admission_id) WHERE a.patient_id=p.patient_id)) AS matching_records;
SELECT 'Q12 discharge summary recovery' AS scenario, (SELECT COUNT(*) FROM ClinicalNotes WHERE note_type='Discharge Summary' AND note_content ILIKE '%recovery%') AS matching_records;
SELECT 'Q13 radiology without ICU/CCU' AS scenario, (SELECT COUNT(DISTINCT r.admission_id) FROM RadiologyExaminations r WHERE NOT EXISTS(SELECT 1 FROM UnitStays u WHERE u.admission_id=r.admission_id AND u.unit_type IN ('ICU','CCU'))) AS matching_records;
SELECT 'Q14 completed admissions' AS scenario, (SELECT COUNT(*) FROM Admissions WHERE discharge_datetime IS NOT NULL) AS matching_records;
SELECT 'Q15 patients with transfers' AS scenario, (SELECT COUNT(*) FROM (SELECT admission_id FROM UnitStays GROUP BY admission_id HAVING COUNT(*)>1) q) AS matching_records;
SELECT 'Q16 multiple critical care types' AS scenario, (SELECT COUNT(*) FROM (SELECT admission_id FROM UnitStays WHERE unit_type IN ('ICU','CCU','MICU','SICU') GROUP BY admission_id HAVING COUNT(DISTINCT unit_type)>1) q) AS matching_records;
SELECT 'Q17 multiple ICD9 codes' AS scenario, (SELECT COUNT(*) FROM (SELECT admission_id FROM Diagnosis GROUP BY admission_id HAVING COUNT(DISTINCT icd9_code)>1) q) AS matching_records;
SELECT 'Q18 patients with notes' AS scenario, (SELECT COUNT(DISTINCT a.patient_id) FROM Admissions a JOIN ClinicalNotes n USING(admission_id)) AS matching_records;
SELECT 'Q19 deaths during admission' AS scenario, (SELECT COUNT(*) FROM Admissions a JOIN Patients p USING(patient_id) WHERE a.final_status='Deceased' AND p.death_datetime BETWEEN a.admission_datetime AND a.discharge_datetime) AS matching_records;
SELECT 'Q20 surgery and radiology same day' AS scenario, (SELECT COUNT(*) FROM SurgicalProcedures s JOIN RadiologyExaminations r USING(admission_id) WHERE s.procedure_datetime::date=r.exam_datetime::date) AS matching_records;

SELECT
    (SELECT COUNT(*) FROM Patients) AS patients,
    (SELECT COUNT(*) FROM Admissions) AS admissions,
    (SELECT COUNT(*) FROM Diagnosis) AS diagnoses,
    (SELECT COUNT(*) FROM ClinicalNotes) AS clinical_notes,
    (SELECT COUNT(*) FROM DischargeRecords) AS discharge_records;
