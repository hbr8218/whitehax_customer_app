import requests
import json

API_KEY = ""  # Required
SESSION_KEY = ""  # Required
PROFILE_NAME = ""  # Required
PROFILE_DESCRIPTION = ""  # Optional
ENDPOINT_CONFIG_ID = ""  # Required
PROFILE_TYPE = ""  # Required; must be one of: mcp_tester, dos_tester, rto, prompts_docs_llm, ai_model_attack_surface, regulation_compliance
PROFILE_CONFIG_FILE = ""  # Required; name of any one of the six profile json files
RETRY_ATTEMPTS = 0  # Optional

url = f"https://demo.whitehax.com/api/profiles-config/create/"

with open(PROFILE_CONFIG_FILE) as f:
    CONFIG = json.load(f)

payload = {
    "profile_name": PROFILE_NAME,
    "profile_description": PROFILE_DESCRIPTION,
    "endpoint_config_id": ENDPOINT_CONFIG_ID,
    "profile_type": PROFILE_TYPE,
    "retry_attempts": RETRY_ATTEMPTS,
    "config": json.dumps(CONFIG),
}


headers = {"Authorization": API_KEY, "X-Session-Key": SESSION_KEY}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
