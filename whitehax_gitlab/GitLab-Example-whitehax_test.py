"""
Here is the complete Python blueprint for whitehax_scans/whitehax_tests.py.
This Python script parses the target execution parameters natively supplied 
by GitLab's runner context (CI_ENVIRONMENT_URL) and builds a valid, 
compliant GitLab DAST Report JSON structure.

Core Structural Design Rules for GitLab DAST Ingestion:
* Ultimate Tier Requirement: Just like native GitLab SAST, parsing 
  the gl-dast-report.json to render inside dashboards or merge requests requires a GitLab Ultimate license.
* The Severity Keyword Constraint: GitLab's schema parser rejects generic lowercase strings 
  or custom titles. You must map your scanner's severity level directly to one of 
  these valid tokens: Info, Low, Medium, High, or Critical.
* Unique Ingestion Hashes: The id key inside every entry within the vulnerabilities array 
  must be completely unique per finding. If your script outputs duplicate IDs, 
  GitLab will overwrite the previous logs and only show a single vulnerability on your dashboard.

"""

#!/usr/bin/env python3
import os
import sys
import json
import time

def main():
    # 1. Fetch parameters passed by the GitLab CI/CD environment context
    whitehax_url = os.environ.get("WHITEHAX_URL")
    api_key = os.environ.get("WHITEHAX_API_KEY")
    # GitLab automatically defines the live target environment via this variable
    target_url = os.environ.get("CI_ENVIRONMENT_URL")

    # Guardrails: Ensure required environment credentials exist
    if not all([whitehax_url, api_key, target_url]):
        print("[ERROR] Missing required execution variables.", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Initializing scan for: {target_url}")

    # -------------------------------------------------------------------------
    # PLACEHOLDER: Insert actual WhiteHax API call logic here.
    # -------------------------------------------------------------------------
    time.sleep(1) # Simulates tool calculation delay

    # 2. Define mock vulnerabilities retrieved from the scanner execution
    detected_vulnerabilities = [
        {
            "id": "WHX-001", 
            "title": "Cross-Site Scripting (XSS)", 
            "description": "Reflected XSS located in search payload inputs.", 
            "severity": "High", # GitLab values: Info, Low, Medium, High, Critical
            "uri": "api/v1/users"
        },
        {
            "id": "WHX-002", 
            "title": "Missing Content-Security-Policy Header", 
            "description": "The server application does not enforce safe structural frame paths.", 
            "severity": "Medium", 
            "uri": ""
        }
    ]

    # 3. Assemble structural GitLab Secure Report Schema (DAST Format)
    gitlab_dast_report = {
        "version": "15.0.0", # Target schema specification level
        "vulnerabilities": [],
        "scan": {
            "analyzer": {
                "id": "whitehax-dast",
                "name": "WhiteHax DAST Plugin",
                "vendor": {"name": "WhiteHax Sec"},
                "version": "1.0.0"
            },
            "scanner": {
                "id": "whitehax_engine",
                "name": "WhiteHax Scan Core",
                "vendor": {"name": "WhiteHax Sec"},
                "version": "2.4.0"
            },
            "type": "dast",
            "start_time": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "end_time": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "status": "success"
        }
    }

    # 4. Map findings into correct GitLab structural keys
    for index, vuln in enumerate(detected_vulnerabilities):
        full_path = f"{target_url.rstrip('/')}/{vuln['uri'].lstrip('/')}" if vuln['uri'] else target_url
        
        # Unique identifier hash required by GitLab tracking engines
        vulnerability_id = f"whitehax-{vuln['id']}-{index}"

        vulnerability_entry = {
            "id": vulnerability_id,
            "category": "dast",
            "name": vuln["title"],
            "description": vuln["description"],
            "severity": vuln["severity"],
            "confidence": "Confirmed",
            "scanner": {"id": "whitehax_engine", "name": "WhiteHax Scan Core"},
            "identifiers": [
                {
                    "type": "whitehax_id",
                    "name": vuln["id"],
                    "value": vuln["id"]
                }
            ],
            "links": [{"url": full_path}],
            "location": {
                "hostname": target_url,
                "path": f"/{vuln['uri'].lstrip('/')}" if vuln['uri'] else "/"
            }
        }
        gitlab_dast_report["vulnerabilities"].append(vulnerability_entry)

    # 5. Commit output data strings matching the artifact reports signature
    output_filename = "gl-dast-report.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(gitlab_dast_report, f, indent=2)
    
    print(f"[SUCCESS] Security payload generated: {output_filename}")

if __name__ == "__main__":
    main()
