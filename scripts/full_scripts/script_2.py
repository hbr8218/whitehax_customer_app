# Use API Key for all requests
# Load inputs from input_2.json
# 1. Get session key using email and password - use this for subsequent requests
# 2. Start test, get test id
# 3. Poll test status until error or completed, get report id
# 4. Get test report

import json
import sys
from pathlib import Path
import time
import requests

INPUTS_FILE = Path(__file__).with_name("input_2.json")
BASE_URL = "https://demo.whitehax.com"

def get_session_key(email, password, api_key):
    url = f"{BASE_URL}/api/auth/session/"
    payload = {"email": email, "password": password}
    headers = {"Authorization": api_key}

    response = requests.request("POST", url, headers=headers, data=payload, timeout=10)
    if response.status_code != 200:
        raise ValueError(response.json().get("message", response.text))
    return response.json()["session_key"]

def start_test(api_key, session_key, profile_id, report_name):
    url = f"{BASE_URL}/api/jobs/"
    payload = {"profile_id": profile_id, "report_name": report_name}
    headers = {"Authorization": api_key, "X-Session-Key": session_key}
    response = requests.request("POST", url, headers=headers, data=payload, timeout=10)
    if response.status_code != 201:
        raise ValueError(response.json().get("message", response.text))
    return response.json()["job_id"]

def get_test_status(api_key, session_key, test_id):
    url = f"{BASE_URL}/api/jobs/{test_id}/status/"
    headers = {"Authorization": api_key, "X-Session-Key": session_key}
    while True:
        response = requests.request("GET", url, headers=headers, timeout=10)
        if response.status_code != 200:
            raise ValueError(response.json().get("message", response.text))
        data = response.json().get("data", {})
        overall = data.get("overall")
        if overall and overall["status"] == "completed":
            return data["report_id"]
        if overall and overall["status"] == "failed":
            raise ValueError(overall.get("error_msg") or "Test failed")
        print("Test in progress! Completion: ", data.get("completion_pct", 0), "%")
        time.sleep(5)

def get_test_report(api_key, session_key, report_id):
    url = f"{BASE_URL}/api/readiness-score/getReportById/{report_id}"
    headers = {"Authorization": api_key, "X-Session-Key": session_key}
    response = requests.request("GET", url, headers=headers, timeout=10)
    if response.status_code != 200:
        raise ValueError(response.json().get("message", response.text))
    with open("report.json", "w") as f:
        json.dump(response.json(), f)
    print("Report saved to report.json")

def main():
    try:
        inputs = json.loads(INPUTS_FILE.read_text())
        api_key = inputs["api_key"]
        session_key = get_session_key(inputs["email"], inputs["password"], api_key)
        print("Authentication successful! Session key: ", session_key)
        test_id = start_test(
            api_key, session_key, inputs["profile_info"]["id"], inputs["report_info"]["name"]
        )
        print("Test started successfully! Test ID: ", test_id)
        report_id = get_test_status(api_key, session_key, test_id)
        print("Test completed successfully! Report ID: ", report_id)
        get_test_report(api_key, session_key, report_id)
    except Exception as e:
        sys.exit(f"Error: {e}")

if __name__ == "__main__":
    main()