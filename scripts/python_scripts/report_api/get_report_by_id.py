import requests

API_KEY = ""  # Required
SESSION_KEY = ""  # Required
REPORT_ID = ""  # Required

url = f"https://demo.whitehax.com/api/readiness-score/getReportById/{REPORT_ID}"

headers = {"Authorization": API_KEY, "X-Session-Key": SESSION_KEY}

response = requests.request("GET", url, headers=headers)

print(response.text)
