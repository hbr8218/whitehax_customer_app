import requests
import json

API_KEY = ""  # Required
SESSION_KEY = ""  # Required
PROFILE_ID = ""  # Required
OVERALL_READINESS = ""  # Required
SCORE_JSON_FILE = ""  # Required; name of the JSON file containing report data
REPORT_NAME = ""  # Optional
REPORT_TYPE = ""  # Optional; if provided, must be one of: individual, consolidated

with open(SCORE_JSON_FILE) as f:
    SCORE_JSON = json.load(f)

url = f"https://demo.whitehax.com/api/readiness-score/createReport/"

payload = {
    "profile_id": PROFILE_ID,
    "overall_readiness": OVERALL_READINESS,
    "score_json": json.dumps(SCORE_JSON),
    "report_type": REPORT_TYPE,
    "report_name": REPORT_NAME,
}

headers = {"Authorization": API_KEY, "X-Session-Key": SESSION_KEY}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
