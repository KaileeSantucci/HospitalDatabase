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


--query 5
--here need 2 joins since UnitStays doesn't link to Patients directly it goes through admissions which then goes to patients 
SELECT p.first_name, p.last_name, u.unit_type, u.entry_datetime, u.exit_datetime, u.exit_datetime - u.entry_datetime AS total_staytime -- columns i want in the result table which also includes the total stay time (exit time - entry time ) 
FROM UnitStays u --starts from the Unit stays table  
JOIN Admissions a ON a.admission_id = u.admission_id --joins admissions and matches a stay to an admission when they have the same admission ID num
JOIN Patients p ON p.patient_id = a.patient_id --then admission stores the patient_id so it reaches the patient and their name
WHERE u.unit_type IN ('ICU', 'CCU') --filtering to have only ICU and CCU stays
	AND u.exit_datetime - u.entry_datetime > INTERVAL '7 days'; --follows the conditon that the stay must be longer than 7 days 

--query 6
--using Left Join
SELECT p.patient_id, p.first_name, p.last_name, COUNT(a.admission_id) AS admission_count --columns i want in the result 
FROM Patients p --starts from the patients table, keeping every row of 'p'
LEFT JOIN Admissions a ON a.patient_id = p.patient_id --joins each patient's admission by matching it with patient_id. 'Left Join' because patients with no admissions will be kept as only 1 row with NULL in admissions 
GROUP BY p.patient_id, p.first_name, p.last_name; -- takes all of a patient's rows into 1 row per patient, so counts within each patient

--query 7
--using 3 joins, self join on unit stays
SELECT DISTINCT p.patient_id, p.first_name, p.last_name --columns needed for the resulting table
FROM UnitStays ed --starts from the UnitStays and ed for 'emergency department' for the first time
JOIN UnitStays c ON c.admission_id = ed.admission_id -- then second time which is c that stands for 'ICU/CCU stay', matching admission_id pairs with stays from the same admission
JOIN Admissions a ON a.admission_id = ed.admission_id -- the stay only knows its admission number, so look up the admission to get the patient_id
JOIN Patients p ON p.patient_id = a.patient_id -- look up the patient to get their names
WHERE ed.unit_type = 'Emergency Department' -- copy of 'ed' must be an Emergency department stay 
	AND c.unit_type IN ('ICU', 'CCU') -- copy 'c' must be an ICU or CCU stay 
	AND c.entry_datetime > ed.entry_datetime; -- ICU/CCU stay must have started after Emergency department stay


--query 8
--using IN to find admissions with an ICU/CCU stay 
SELECT i.icd9_code, i.official_title, COUNT(*) AS diagnosis_count  -- columns needed for the resulting table including how many times it was assigned 
FROM Diagnosis d -- start from all Diagnosis 
JOIN ICD9Dictionary i ON i.icd9_code = d.icd9_code -- looking up each code in the dictionary to get its official title 
WHERE d.diagnosis_type = 'Primary'  -- keeping only 'Primary' diagnosis
	AND d.admission_id IN( -- and only if the admission is in the list below
	SELECT admission_id -- list of admissions that had an ICU or CCU stay 
	FROM UnitStays
	WHERE unit_type IN ('ICU', 'CCU') -- using IN instead of JOIN because the admission with 2 ICU/CCU stays will not be counted twice  
	)
GROUP BY i.icd9_code, i.official_title -- putting every row with the same code into the same pile
ORDER BY diagnosis_count DESC -- go by the highest count
LIMIT 1; -- keeping the most frequent one 'Retrieving the most frequently assigned primary ICD-9 diagnosis'