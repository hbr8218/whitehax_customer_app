import requests

API_KEY = ""  # Required
SESSION_KEY = ""  # Required
PROFILE_ID = ""  # Required

url = f"https://demo.whitehax.com/api/test-files/download/{PROFILE_ID}"

headers = {"Authorization": API_KEY, "X-Session-Key": SESSION_KEY}

response = requests.request("GET", url, headers=headers)
response.raise_for_status()

output_path = f"profile_{PROFILE_ID}_test_files.zip"
with open(output_path, "wb") as f:
    f.write(response.content)
