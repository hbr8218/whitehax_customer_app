# Create an endpoint, then create a profile using that endpoint_config_id.
# Fill in the params below, then run: python create_endpoint_and_profile.py

import json
import sys
import requests

BASE_URL = "https://demo.whitehax.com"

# --- Auth ---
API_KEY = "70UyXkl-T7U3IxSaVhA4AW4gzCP4ipjIn0AO2OCjRhI"  # Required
EMAIL = "hbr@ironsdn.com    "  # Required
PASSWORD = "hbr123"  # Required

# --- Endpoint ---
ENDPOINT_NAME = "Test Endpoint github"  # Required
ENDPOINT_DESCRIPTION = "Test Endpoint Description"  # Optional
ENDPOINT_TYPE = "api_endpoint"  # Required; must be one of: api_endpoint, llm_model_endpoint, mcp_endpoint
ENDPOINT_PARAMS = {  # Required
    "url": "http://54.177.207.48:8000/chat",  # Required; must be a valid url
    "selection": "json_parameters",  # Required; must be "json_parameters"
}
JSON_PARAMETERS = {  # Required
    "request": {
                "headers": {
                    "Authorization": "Bearer xxx",
                    "Content-Type": "application/json"
                },
                "request_template": {
                    "message":"{{PROMPT}}"
                },
                "prompt_path":"message"
                }
,  # Required; must be a valid json object (can be {})
    "response": {
        "response": "{{RESP}}",
        "status": "ok"
        }
,  # Required; must be a valid json object (can be {})
}

# --- Profile ---
PROFILE_NAME = "github profile api endpoint"  # Required
PROFILE_DESCRIPTION = "github profile api endpoint description"  # Optional
PROFILE_TYPE = "prompts_docs_llm"  # Required; must be one of: mcp_tester, dos_tester, rto, prompts_docs_llm, ai_model_attack_surface, regulation_compliance
RETRY_ATTEMPTS = 0  # Optional
PROFILE_CONFIG = {
  "profile_type": PROFILE_TYPE,
  "prompts_testing": {
    "enabled": True
  },
  "test_file_paths": {
    "dos": [
      
    ],
    "llm": [
      
    ],
    "mcp": [
      
    ],
    "rto": [
      
    ],
    "docs": [
      
    ],
    "frame": [
      
    ],
    "prompts": [
      {
        "file_name": "h_gen_test_100.csv",
        "file_path": "/home/ubuntu/projects/wh_internal_api/wh_tester_api/media_root/user_files/user_4/user_generated_files/malicious_prompts/h_gen_test_100.csv",
        "file_creation_method": "generated"
      }
    ],
    "rc_prompts": [
      
    ],
    "custom_decision_tree": [
      
    ]
  },
  "adv_multi_attacks": {
    "sub": {
      "ama_backdoor": {
        "enabled": False
      },
      "ama_collusion": {
        "enabled": False
      },
      "ama_jb_classic": {
        "enabled": False
      },
      "ama_jb_reverse": {
        "enabled": False
      },
      "ama_crisis_manip": {
        "enabled": False
      },
      "ama_tool_exploit": {
        "enabled": False
      },
      "ama_jb_contextual": {
        "enabled": False
      },
      "ama_safe_boundary": {
        "enabled": False
      },
      "ama_jb_token_manip": {
        "enabled": False
      },
      "ama_info_extraction": {
        "enabled": False
      },
      "ama_decision_fatigue": {
        "enabled": False
      },
      "ama_jb_sophisticated": {
        "enabled": False
      },
      "ama_resource_exhaustion": {
        "enabled": False
      }
    },
    "enabled": False
  },
  "malicious_doc_uploads": {
    "enabled": False
  }
}


def get_session_key(email, password, api_key):
    url = f"{BASE_URL}/api/auth/session/"
    payload = {"email": email, "password": password}
    headers = {"Authorization": api_key}
    response = requests.request("POST", url, headers=headers, data=payload, timeout=10)
    if response.status_code != 200:
        raise ValueError(response.json().get("message", response.text))
    return response.json()["session_key"]


def create_endpoint(api_key, session_key):
    url = f"{BASE_URL}/api/endpoint-config/create/"
    payload = {
        "endpoint_name": ENDPOINT_NAME,
        "endpoint_description": ENDPOINT_DESCRIPTION,
        "endpoint_type": ENDPOINT_TYPE,
        "endpoint_params": json.dumps(ENDPOINT_PARAMS),
        "json_parameters": json.dumps(JSON_PARAMETERS),
    }
    headers = {"Authorization": api_key, "X-Session-Key": session_key}
    response = requests.request("POST", url, headers=headers, data=payload, timeout=10)
    if response.status_code != 201:
        raise ValueError(response.json().get("message", response.text))
    result = response.json()
    endpoint_id = (result.get("data") or {}).get("id") or result.get("id")
    if endpoint_id is None:
        raise ValueError(f"Endpoint create response missing id: {result}")
    return endpoint_id


def create_profile(api_key, session_key, endpoint_config_id):
    url = f"{BASE_URL}/api/profiles-config/create/"
    payload = {
        "profile_name": PROFILE_NAME,
        "profile_description": PROFILE_DESCRIPTION,
        "profile_type": PROFILE_TYPE,
        "endpoint_config_id": endpoint_config_id,
        "config": json.dumps(PROFILE_CONFIG),
        "retry_attempts": RETRY_ATTEMPTS,
    }
    headers = {"Authorization": api_key, "X-Session-Key": session_key}
    response = requests.request("POST", url, headers=headers, data=payload, timeout=10)
    if response.status_code != 201:
        raise ValueError(response.json().get("message", response.text))
    result = response.json()
    profile_id = result.get("id")
    if profile_id is None:
        raise ValueError(f"Profile create response missing id: {result}")
    return profile_id


def main():
    try:
        session_key = get_session_key(EMAIL, PASSWORD, API_KEY)
        print("session_key:", session_key)
        endpoint_config_id = create_endpoint(API_KEY, session_key)
        print("endpoint_config_id:", endpoint_config_id)
        profile_id = create_profile(API_KEY, session_key, endpoint_config_id)
        print("profile_id:", profile_id)
    except Exception as e:
        sys.exit(f"Error: {e}")


if __name__ == "__main__":
    main()
