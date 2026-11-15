import json
from datetime import date
import pandas as pd

bundle_json = '''
{
  "resourceType": "Bundle",
  "type": "collection",
  "entry": [
    {"resource": {
      "resourceType": "Patient", "id": "P001",
      "name": [{"use": "official", "family": "Silva", "given": ["Maria", "Clara"]}],
      "gender": "female", "birthDate": "1985-03-12",
      "telecom": [{"system": "phone", "value": "555-0101"}],
      "address": [{"city": "Sao Paulo", "country": "BR"}]
    }},
    {"resource": {
      "resourceType": "Patient", "id": "P002",
      "name": [{"use": "official", "family": "Carter", "given": ["John"]}],
      "gender": "male", "birthDate": "1962-11-02"
    }},
    {"resource": {
      "resourceType": "Observation", "id": "O1", "status": "final",
      "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4", "display": "Heart rate"}]},
      "subject": {"reference": "Patient/P001"},
      "effectiveDateTime": "2024-01-15T08:30:00Z",
      "valueQuantity": {"value": 72, "unit": "beats/minute"}
    }},
    {"resource": {
      "resourceType": "Observation", "id": "O2", "status": "final",
      "code": {"coding": [{"system": "http://loinc.org", "code": "2339-0", "display": "Glucose"}]},
      "subject": {"reference": "Patient/P001"},
      "effectiveDateTime": "2024-01-15T08:35:00Z",
      "valueQuantity": {"value": 105, "unit": "mg/dL"}
    }},
    {"resource": {
      "resourceType": "Observation", "id": "O3", "status": "final",
      "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4", "display": "Heart rate"}]},
      "subject": {"reference": "Patient/P002"},
      "effectiveDateTime": "2024-01-15T09:00:00Z",
      "valueQuantity": {"value": 110, "unit": "beats/minute"}
    }},
    {"resource": {
      "resourceType": "Observation", "id": "O4", "status": "final",
      "code": {"coding": [{"system": "http://loinc.org", "code": "85354-9", "display": "Blood pressure panel"}]},
      "subject": {"reference": "Patient/P002"},
      "effectiveDateTime": "2024-01-15T09:05:00Z",
      "component": [
        {"code": {"coding": [{"code": "8480-6", "display": "Systolic blood pressure"}]},
         "valueQuantity": {"value": 150, "unit": "mmHg"}},
        {"code": {"coding": [{"code": "8462-4", "display": "Diastolic blood pressure"}]},
         "valueQuantity": {"value": 95, "unit": "mmHg"}}
      ]
    }},
    {"resource": {
      "resourceType": "Observation", "id": "O5", "status": "final",
      "code": {"coding": [{"system": "http://loinc.org", "code": "2339-0", "display": "Glucose"}]},
      "subject": {"reference": "Patient/P002"},
      "effectiveDateTime": "2024-01-15T09:10:00Z",
      "dataAbsentReason": {"coding": [{"code": "not-performed"}]}
    }}
  ]
}
'''

bundle = json.loads(bundle_json)


def calculate_age(birth_text, today):
    birth = date.fromisoformat(birth_text)
    age = today.year - birth.year
    if (today.month, today.day) < (birth.month, birth.day):
        age -= 1
    return age


def parse_patient(p):
    names = p.get("name", [])
    if len(names) > 0:
        given = " ".join(names[0].get("given", []))
        family = names[0].get("family", "")
        full_name = (given + " " + family).strip()
    else:
        full_name = None

    addresses = p.get("address", [])
    if len(addresses) > 0:
        city = addresses[0].get("city")
    else:
        city = None

    return {
        "patient_id": p["id"],
        "name": full_name,
        "gender": p.get("gender"),
        "age": calculate_age(p["birthDate"], date(2024, 1, 15)),
        "city": city,
    }


def make_row(obs_id, patient_id, timestamp, coding, quantity):
    return {
        "obs_id": obs_id,
        "patient_id": patient_id,
        "timestamp": timestamp,
        "code": coding["code"],
        "measure": coding["display"],
        "value": quantity.get("value"),
        "unit": quantity.get("unit"),
    }


def parse_observation(o):
    patient_id = o["subject"]["reference"].split("/")[1]
    timestamp = o.get("effectiveDateTime")
    rows = []

    if "component" in o:
        for comp in o["component"]:
            coding = comp["code"]["coding"][0]
            quantity = comp.get("valueQuantity", {})
            rows.append(make_row(o["id"], patient_id, timestamp, coding, quantity))
    else:
        coding = o["code"]["coding"][0]
        quantity = o.get("valueQuantity", {})
        rows.append(make_row(o["id"], patient_id, timestamp, coding, quantity))

    return rows


def flag(row):
    if pd.isnull(row["value"]):
        return "MISSING"
    if row["code"] == "8867-4" and row["value"] > 100:
        return "HIGH"
    if row["code"] == "8480-6" and row["value"] >= 140:
        return "HIGH"
    if row["code"] == "8462-4" and row["value"] >= 90:
        return "HIGH"
    if row["code"] == "2339-0" and row["value"] > 125:
        return "HIGH"
    return "normal"


# Split the bundle by resource type
patient_rows = []
obs_rows = []

for entry in bundle["entry"]:
    resource = entry["resource"]

    if resource["resourceType"] == "Patient":
        patient_rows.append(parse_patient(resource))
    elif resource["resourceType"] == "Observation":
        obs_rows.extend(parse_observation(resource))

patients_df = pd.DataFrame(patient_rows)
obs_df = pd.DataFrame(obs_rows)
obs_df["timestamp"] = pd.to_datetime(obs_df["timestamp"])

# Join and flag
full = pd.merge(obs_df, patients_df[["patient_id", "name", "age"]], on="patient_id", how="left")
full["flag"] = full.apply(flag, axis=1)

print(patients_df)
print()
print(full[["name", "age", "measure", "value", "unit", "flag"]])