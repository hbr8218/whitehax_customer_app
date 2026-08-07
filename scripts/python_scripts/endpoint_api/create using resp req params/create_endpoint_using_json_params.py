import requests
import json

API_KEY = ""  # Required
SESSION_KEY = ""  # Required
ENDPOINT_NAME = ""  # Required
ENDPOINT_DESCRIPTION = ""  # Optional
ENDPOINT_TYPE = ""  # Required; must be one of: api_endpoint, llm_model_endpoint, mcp_endpoint
ENDPOINT_PARAMS = {  # Required
    "url": "",  # Required; must be a valid url
    "selection": "json_parameters",  # Required; must be "json_parameters"
}
JSON_PARAMETERS = {  # Required
    "request": {},  # Required; must be a valid json object (can be {})
    "response": {},  # Required; must be a valid json object (can be {})
}

url = f"https://demo.whitehax.com/api/endpoint-config/create/"

payload = {
    "endpoint_name": ENDPOINT_NAME,
    "endpoint_description": ENDPOINT_DESCRIPTION,
    "endpoint_type": ENDPOINT_TYPE,
    "endpoint_params": json.dumps(ENDPOINT_PARAMS),
    "json_parameters": json.dumps(JSON_PARAMETERS),
}
headers = {"Authorization": API_KEY, "X-Session-Key": SESSION_KEY}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
