import requests

API_KEY = ""  # Required
SESSION_KEY = ""  # Required
ENDPOINT_ID = ""  # Required

url = f"https://demo.whitehax.com/api/endpoint-files/download/{ENDPOINT_ID}"

headers = {"Authorization": API_KEY, "X-Session-Key": SESSION_KEY}

response = requests.request("GET", url, headers=headers)

response.raise_for_status()

output_path = f"endpoint_files_{ENDPOINT_ID}.zip"
with open(output_path, "wb") as f:
    f.write(response.content)
