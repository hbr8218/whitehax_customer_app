import requests

API_KEY = ""  # Required
SESSION_KEY = ""  # Required
ENDPOINT_CONFIG_ID = ""  # Required

url = f"https://demo.whitehax.com/api/endpoint-config/getEndpointConfigById/{ENDPOINT_CONFIG_ID}"

headers = {"Authorization": API_KEY, "X-Session-Key": SESSION_KEY}

response = requests.request("GET", url, headers=headers)

print(response.text)
