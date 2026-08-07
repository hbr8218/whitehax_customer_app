import requests

API_KEY = ""  # Required
SESSION_KEY = ""  # Required
PROFILE_ID = ""  # Required
REPORT_NAME = ""  # Optional

url = f"https://demo.whitehax.com/api/jobs/"

payload = {"profile_id": PROFILE_ID, "report_name": REPORT_NAME}

headers = {"Authorization": API_KEY, "X-Session-Key": SESSION_KEY}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
