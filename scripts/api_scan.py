import json
import requests

API_URL = "https://jsonplaceholder.typicode.com/posts/1"

response = requests.get(API_URL, timeout=30)
data = response.json()

sarif = {
    "version": "2.1.0",
    "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
    "runs": [
        {
            "tool": {
                "driver": {
                    "name": "Public API Scanner",
                    "informationUri": "https://example.com",
                    "rules": [
                        {
                            "id": "API001",
                            "name": "Public API Response",
                            "shortDescription": {
                                "text": "Public API returned data"
                            }
                        }
                    ]
                }
            },
            "results": [
                {
                    "ruleId": "API001",
                    "level": "note",
                    "message": {
                        "text": json.dumps(data, indent=2)
                    },
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {
                                    "uri": "api_response.json"
                                },
                                "region": {
                                    "startLine": 1
                                }
                            }
                        }
                    ]
                }
            ]
        }
    ]
}

with open("output.sarif", "w") as f:
    json.dump(sarif, f, indent=2)

print("SARIF generated...")