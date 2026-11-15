# FHIR Bundle Parser

A Python script that reads a FHIR Bundle (the HL7 standard for exchanging healthcare data) and turns its deeply nested JSON into clean pandas tables, then flags abnormal vital signs.

## How it works
- Parses a Bundle containing two kinds of resources: **Patient** and **Observation**
- **Patients:** builds a full name from the nested `given` and `family` fields, calculates age from the birth date, and reads the city if an address exists
- **Observations:** extracts the patient ID from the `subject` reference (`"Patient/P001"`), the measurement code and name, the value, and the unit
- Handles **multi-component observations**: one blood pressure observation becomes two rows, systolic and diastolic
- Handles **missing results**: an observation with no value (marked "not-performed") is kept and flagged as `MISSING`, not dropped
- Joins observations to patients with a left merge, then flags each result using simple rules per measurement code

## Example results (sample data)
| Patient | Age | Measure | Value | Flag |
|---------|-----|---------|-------|------|
| Maria Clara Silva | 38 | Heart rate | 72 | normal |
| Maria Clara Silva | 38 | Glucose | 105 | normal |
| John Carter | 61 | Heart rate | 110 | HIGH |
| John Carter | 61 | Systolic blood pressure | 150 | HIGH |
| John Carter | 61 | Diastolic blood pressure | 95 | HIGH |
| John Carter | 61 | Glucose | none | MISSING |

5 observations become 6 rows, because the blood pressure panel is split into two measurements.

## How to run
```bash
python fhir_parser.py
```

## What I learned
- What a FHIR Bundle is, and how resources are organized inside its `entry` list
- Navigating deeply nested JSON: lists inside dictionaries inside lists
- Using `.get()` with defaults for optional fields, so patients without an address or phone don't crash the script
- Turning one nested record into several flat rows (multi-component observations)
- Splitting a reference string like `"Patient/P001"` to get an ID
- Calculating age correctly, including the check for whether the birthday has happened yet this year
- Keeping missing results visible with a `MISSING` flag instead of silently dropping them
- Writing small helper functions (`parse_patient`, `parse_observation`, `make_row`, `flag`) so each one has a single job

## Limitations
- **Educational only, not medical advice.** The thresholds (heart rate above 100, blood pressure at or above 140/90, glucose above 125) are simplified illustrations, not clinical rules.
- Age is calculated as of a fixed date (2024-01-15) so the output is reproducible. A real system would use the date of each observation.
- Only two resource types are handled. Real FHIR bundles contain many more.
- All data is fictional. Real patient data is protected by privacy laws such as HIPAA and GDPR and must never be committed to a public repository.

## Dependencies
Requires pandas:
```bash
pip install pandas
```
