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


-- Query 9: Calculate the average length of stay for each critical care unit type
-- Uses `AVG()` to calculate the average stay duration, `GROUP BY` to separate unit types, and `WHERE` to filter critical care units and incomplete stays.

SELECT
    unit_type, -- display the critical care unit type
    JUSTIFY_HOURS(AVG(exit_datetime - entry_datetime)) AS average_length_of_stay -- calculates and formats the average length of the stay
FROM UnitStays -- retrieves unit stay records
WHERE unit_type IN ('MICU', 'SICU', 'ICU', 'CCU') -- includes only critical care units (MICU, SICU, ICU, CCU)
    AND exit_datetime IS NOT NULL -- excludes any stays that have not yet ended
GROUP BY unit_type -- calculates a seperate ADD
ORDER BY unit_type; -- displays the results in alphabetical order by unit type


-- Query 10: Patients who have underwent surgey before entering the ICU/CCU unit
-- Uses `JOIN` to connect patients, admissions, surgeries and unit stays, and `WHERE` to filter surgeries performed before ICU/CCU entry

SELECT
    p.first_name, -- display patient's first name
    p.last_name, -- display patient's last name
    s.procedure_datetime, -- display surgery date and time
    u.unit_type, -- display critical care unit type
    u.entry_datetime AS unit_entry_time -- display unit entry time
FROM Patients p -- retrieve patient information
JOIN Admissions a ON p.patient_id = a.patient_id -- matches patients to admissions
JOIN SurgicalProcedures s ON a.admission_id = s.admission_id -- to find surgeries during admission
JOIN UnitStays u ON a.admission_id = u.admission_id -- find unit stays during the same admission
WHERE u.unit_type IN ('ICU', 'CCU') -- include only ICU and CCU
    AND s.procedure_datetime < u.entry_datetime -- ensure surgery occurred before unit entry
ORDER BY p.last_name, p.first_name, s.procedure_datetime; -- sort by patient and surgery date

-- Query 11: Count the radiology examinations performed for each patient across all admissions
-- Uses `LEFT JOIN` to include all patients and `COUNT()` with `GROUP BY` to total radiology examinations per patient

SELECT
    p.first_name, -- display patient's first name
    p.last_name, -- display patient's last name
    COUNT(r.radiology_exam_id) AS total_examinations -- count radiology exams, including zero
FROM Patients p -- start with all patients
LEFT JOIN Admissions a ON p.patient_id = a.patient_id -- include patients without admissions
LEFT JOIN RadiologyExaminations r ON a.admission_id = r.admission_id -- include admissions without radiology exams
GROUP BY p.patient_id, p.first_name, p.last_name -- calculate one total per patient
ORDER BY p.last_name, p.first_name; -- sort results alphabetically

-- Query 12: Find all patients whose discharge-summary clinical note contains the keyword 'recovery'
-- Uses `JOIN` to connect patients to clinical notes, `WHERE` with `ILIKE` to find discharge summaries containing “recovery” for case-insensitive matching
-- and `DISTINCT` to avoid duplicates

SELECT DISTINCT
    p.first_name, -- display patient's first name
    p.last_name -- display patient's last name
FROM Patients p -- retrieve patient information
JOIN Admissions a ON p.patient_id = a.patient_id -- match patients to admissions
JOIN ClinicalNotes n ON a.admission_id = n.admission_id -- retrieve clinical notes for each admission
WHERE n.note_type = 'Discharge Summary' -- include only discharge-summary notes
    AND n.note_content ILIKE '%recovery%' -- search for "recovery" regardless of capitalization
ORDER BY p.last_name, p.first_name; -- sort patients alphabetically

-- Query 13: List all admissions with at least one radiology examination but no recorded ICU or CCU stay
-- Uses `EXISTS` to keep admissions with a radiology exam and `NOT EXISTS` to exclude admissions with an ICU or CCU stay, so each admission appears only once

SELECT
    a.admission_id, -- display the admission number
    p.first_name, -- display patient's first name
    p.last_name, -- display patient's last name
    a.admission_datetime, -- display when the admission started
    a.admission_type -- display the type of admission
FROM Admissions a -- start from all admissions
JOIN Patients p ON p.patient_id = a.patient_id -- look up the patient to get their name
WHERE EXISTS ( -- keep the admission only if it had at least one radiology exam
        SELECT 1
        FROM RadiologyExaminations r
        WHERE r.admission_id = a.admission_id
    )
    AND NOT EXISTS ( -- and only if no ICU or CCU stay was recorded for that same admission
        SELECT 1
        FROM UnitStays u
        WHERE u.admission_id = a.admission_id
            AND u.unit_type IN ('ICU', 'CCU')
    )
ORDER BY a.admission_id; -- sort by admission number

-- Query 14: Retrieve the patient(s) with the longest completed hospital stay, from admission time to discharge time
-- Uses a subquery with `MAX()` to find the longest completed stay and `WHERE` to return every admission equal to it, so ties are all displayed

SELECT
    p.patient_id, -- display patient's id
    p.first_name, -- display patient's first name
    p.last_name, -- display patient's last name
    a.admission_datetime, -- display admission time
    a.discharge_datetime, -- display discharge time
    a.discharge_datetime - a.admission_datetime AS length_of_stay -- calculate how long the stay lasted
FROM Admissions a -- start from all admissions
JOIN Patients p ON p.patient_id = a.patient_id -- look up the patient to get their name
WHERE a.discharge_datetime IS NOT NULL -- only completed stays
    AND a.discharge_datetime - a.admission_datetime = ( -- keep the stay only if its length equals the maximum
        SELECT MAX(discharge_datetime - admission_datetime) -- longest completed stay in the whole table
        FROM Admissions
        WHERE discharge_datetime IS NOT NULL
    )
ORDER BY p.last_name, p.first_name; -- sort alphabetically if there is a tie

-- Query 15: Count the total number of transfers between hospital units for each patient
-- Uses a subquery with `COUNT(*) - 1` to get transfers per admission (the first unit placement is not a transfer), then `SUM()` with `GROUP BY` to total them per patient

SELECT
    p.patient_id, -- display patient's id
    p.first_name, -- display patient's first name
    p.last_name, -- display patient's last name
    COALESCE(SUM(t.transfers), 0) AS total_transfers -- sum the transfers of every admission, 0 if there are none
FROM Patients p -- start from all patients
LEFT JOIN Admissions a ON a.patient_id = p.patient_id -- match each patient to their admissions
LEFT JOIN ( -- transfers per admission
        SELECT
            admission_id,
            COUNT(*) - 1 AS transfers -- every stay after the first one is a transfer
        FROM UnitStays
        GROUP BY admission_id -- one row per admission
    ) t ON t.admission_id = a.admission_id -- attach the transfer count to its admission
GROUP BY p.patient_id, p.first_name, p.last_name -- one total per patient
ORDER BY total_transfers DESC, p.last_name, p.first_name; -- most transfers first

-- Query 16: List all patients who stayed in more than one type of critical care unit during the same admission
-- Uses `GROUP BY` with `HAVING COUNT(DISTINCT unit_type) > 1` to find admissions with at least two different critical care units (ICU, CCU, MICU, SICU) and `DISTINCT` to list each patient once

SELECT DISTINCT
    p.patient_id, -- display patient's id
    p.first_name, -- display patient's first name
    p.last_name -- display patient's last name
FROM Patients p -- start from all patients
JOIN Admissions a ON a.patient_id = p.patient_id -- match patients to their admissions
WHERE a.admission_id IN ( -- keep only admissions from the list below
        SELECT admission_id
        FROM UnitStays
        WHERE unit_type IN ('ICU', 'CCU', 'MICU', 'SICU') -- only critical care stays
        GROUP BY admission_id -- one group per admission
        HAVING COUNT(DISTINCT unit_type) > 1 -- at least two different critical care unit types
    )
ORDER BY p.last_name, p.first_name; -- sort patients alphabetically

-- Query 17: Find all admissions which the patient has recieved more than one distinct ICD-9 diagnosis
SELECT
    p.first_name,
    p.last_name,
    d.admission_id,
    COUNT(DISTINCT d.icd9_code) AS number_of_icd9_codes -- Count unique ICD-9 codes for each admission
FROM Patients p
JOIN Diagnosis d ON p.patient_id = d.patient_id -- Match patients to their diagnoses
GROUP BY p.patient_id, p.first_name, p.last_name, d.admission_id -- Group diagnoses by patient and admission
HAVING COUNT(DISTINCT d.icd9_code) > 1 -- Include only admissions with more than one distinct diagnosis
ORDER BY p.first_name, p.last_name; -- Sort patients alphabetically

-- Query 18: Retrieve the latest clinical note for each patient
-- Retrieve the most recent clinical note for each patient.
-- Display the patient's name, note type, creation date and time, and note contents.

SELECT DISTINCT ON (p.patient_id) -- Return only one note per patient
    p.first_name,
    p.last_name,
    c.note_type,
    c.note_datetime,
    c.note_content
FROM Patients p
JOIN Admissions a ON p.patient_id = a.patient_id -- Match patients to their admissions
JOIN ClinicalNotes c ON a.admission_id = c.admission_id -- Retrieve clinical notes for each admission
ORDER BY p.patient_id, c.note_datetime DESC, c.note_id DESC; -- Select the most recent note for each patient and order by note ID to break ties if multiple notes have the same datetime.

-- Query 19
-- Find all admissions where the patient died during their hospital stay.
-- Display the patient's name, admission date, date of death and primary ICD-9 diagnosis.
SELECT
    table1.first_name,
    table1.last_name,
    table2.admission_datetime,
    table1.death_datetime,
    table2.icd9_code
FROM patients table1
INNER JOIN (
    -- Retrieve admissions with a primary diagnosis
    SELECT
        a.admission_id,
        a.patient_id,
        a.admission_datetime,
        a.final_status,
        d.icd9_code
    FROM admissions a
    INNER JOIN diagnosis d
        ON a.admission_id = d.admission_id
        AND d.diagnosis_type = 'Primary' -- Include only primary diagnoses
    WHERE a.final_status = 'Deceased' -- Include only admissions where the patient died
) table2
    ON table1.patient_id = table2.patient_id; -- Match deceased admissions to their patients

-- query 20
-- list the patient's name, the admission identifier, the procedure name, the examination type and the datetime 
SELECT p.first_name, p.last_name, table1.admission_id, table1.procedure_type, table1.exam_type, table1.datetime
FROM patients p
INNER JOIN 
(
	SELECT a.admission_id, a.patient_id, temp_table.procedure_type, temp_table.exam_type, temp_table.datetime
	FROM admissions a
	INNER JOIN (
		-- select the admission identifier, the procedure name, the examination type and the datetime in the specified format 
		SELECT s.admission_id, s.procedure_name AS procedure_type, r.exam_type, TO_CHAR(s.procedure_datetime, 'YYYY-MM-DD') AS datetime
		FROM surgicalprocedures s
		INNER JOIN radiologyexaminations r
		ON s.admission_id = r.admission_id AND TO_CHAR(s.procedure_datetime, 'YYYY-MM-DD') = TO_CHAR(r.exam_datetime, 'YYYY-MM-DD') -- include all matching admission identifiers and datetime
	) temp_table 
	ON a.admission_id = temp_table.admission_id -- find all matching admission identifiers in the admissions table 
) table1
ON p.patient_id = table1.patient_id; -- find all corresponding patients 
