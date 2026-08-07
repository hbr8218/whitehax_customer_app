import requests

API_KEY = ""  # Required
SESSION_KEY = ""  # Required
ENDPOINT_CONFIG_ID = ""  # Required

url = f"https://demo.whitehax.com/api/endpoint-config/{ENDPOINT_CONFIG_ID}/delete/"

headers = {"Authorization": API_KEY, "X-Session-Key": SESSION_KEY}

response = requests.request("DELETE", url, headers=headers)

print(response.text)
