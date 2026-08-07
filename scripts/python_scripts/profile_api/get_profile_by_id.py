import requests

API_KEY = ""  # Required
SESSION_KEY = ""  # Required
PROFILE_ID = ""  # Required

url = f"https://demo.whitehax.com/api/profiles-config/getProfileById/{PROFILE_ID}"

headers = {"Authorization": API_KEY, "X-Session-Key": SESSION_KEY}

response = requests.request("GET", url, headers=headers)

print(response.text)
