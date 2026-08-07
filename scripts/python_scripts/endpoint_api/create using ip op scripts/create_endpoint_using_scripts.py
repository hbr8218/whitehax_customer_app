import requests
import json


API_KEY = ""  # Required
SESSION_KEY = ""  # Required
ENDPOINT_NAME = ""  # Required
ENDPOINT_TYPE = ""  # Required; must be one of: api_endpoint, llm_model_endpoint, mcp_endpoint
ENDPOINT_PARAMS = {  # Required
    "url": "",  # Required; must be a valid url
    "selection": "scripts",  # Required; must be "scripts"
    "input_script_prompt_processing": "" # Required; must be one of: single, multi
}
ENDPOINT_DESCRIPTION = ""  # Optional

url = f"https://demo.whitehax.com/api/endpoint-config/create/"

payload = {
    "endpoint_name": ENDPOINT_NAME,
    "endpoint_type": ENDPOINT_TYPE,
    "endpoint_params": json.dumps(ENDPOINT_PARAMS),
    "endpoint_description": ENDPOINT_DESCRIPTION,
}
files = [ # Either inputScript or inputScriptFile is required
    (
        "inputScript",
        (
            "input_script.py",
            open("input_script.py", "rb"),
            "application/octet-stream",
        ),
    ),
    (
        "outputScript",
        (
            "output_script.py",
            open("output_script.py", "rb"),
            "application/octet-stream",
        ),
    ),
]
headers = {"Authorization": API_KEY, "X-Session-Key": SESSION_KEY}

response = requests.request("POST", url, headers=headers, data=payload, files=files)

print(response.text)
