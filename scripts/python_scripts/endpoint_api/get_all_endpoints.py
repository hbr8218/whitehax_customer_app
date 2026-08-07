import requests

API_KEY = ""  # Required
SESSION_KEY = ""  # Required

url = f"https://demo.whitehax.com/api/endpoint-config/getAllEndpointConfigs/"

headers = {"Authorization": API_KEY, "X-Session-Key": SESSION_KEY}

response = requests.request("GET", url, headers=headers)

print(response.text)
