import requests

API_KEY = ""  # Required
USER_EMAIL = ""  # Required
USER_PASSWORD = ""  # Required

url = f"https://demo.whitehax.com/api/auth/session/"

payload = {"email": USER_EMAIL, "password": USER_PASSWORD}
headers = {"Authorization": API_KEY}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
