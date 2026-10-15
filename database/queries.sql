--query 1
SELECT DISTINCT p.last_name, p.first_name, a.admission_datetime
FROM Admissions a
JOIN Patients p ON p.patient_id = a.patient_id
JOIN TriageAssessments t ON t.admission_id = a.admission_id
WHERE t.priority_level = 'High'
		AND a.admission_type = 'emergency';

--query 2
SELECT DISTINCT p.patient_id, p.last_name, p.first_name, COUNT(*)
FROM Admissions a
JOIN Patients p on p.patient_id = a.patient_id
GROUP BY p.patient_id, p.last_name, p.first_name
HAVING COUNT(*) >3;

--query 3
SELECT p.last_name, p.first_name, a.admission_datetime, a.discharge_datetime
FROM Admissions a
JOIN Patients p ON p.patient_id = a.patient_id
WHERE a.final_status = 'Discharged'
    AND NOT EXISTS (
        SELECT 1
        FROM SurgicalProcedures s
        WHERE s.admission_id = a.admission_id
    );

--query 4
SELECT DISTINCT p.patient_id, p.last_name, p.first_name
FROM Admissions a
JOIN Patients p ON p.patient_id = a.patient_id
WHERE EXISTS (
        SELECT 1
        FROM SurgicalProcedures s
        WHERE s.admission_id = a.admission_id
    )
    AND EXISTS (
        SELECT 1
        FROM RadiologyExaminations re
        WHERE re.admission_id = a.admission_id
            AND re.exam_status = 'Completed'
    );
