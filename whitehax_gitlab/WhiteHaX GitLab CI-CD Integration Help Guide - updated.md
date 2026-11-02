WhiteHax GitLab CI/CD Integration Help Guide

Using GitLab CI/CD, post-deploy target URL handoff, WhiteHax REST API integration, and GitLab DAST report artifacts.

**Recommended use:**

1. Treat the workflow and SARIF bridge as reusable scaffolding. Fill in only the WhiteHax REST API adapter once the exact platform endpoint details are available.
2. File names, File paths and Variable names in this guide are only examples, you can save files (.yml & python script) and change variables in any names that are meaningful to you and the project.

Assumptions:

1. That you have an existing user account on WhiteHaX AI-ASM platform & retrieved REST API Key from the platform,
2. That either you will use a previously created AI Endpoint & Test profile for this or will create new using the WhiteHaX REST-API,

# 1. What This Integration Does

This guide describes how to run a WhiteHax DAST verification step after a GitLab deployment and publish the result as GitLab's native DAST security report artifact. GitLab ingests files declared under artifacts:reports:dast and can show findings in merge request security widgets, the pipeline Security tab, the project Vulnerability Report, and security dashboards when the required GitLab security tier is available.

**Note:** Deployment target note: AWS deployment status or AWS post-deploy checks apply only when the application runtime server is deployed in AWS. If the runtime target is local, on a developer workstation, or inside a private network, pass the target explicitly through WHITEHAX\_TARGET\_URL, TARGET\_URL, or CI\_ENVIRONMENT\_URL and make the Python script handle local/private target resolution. For shared GitLab runners, localhost means the runner container, not the developer machine; use a self-hosted runner, VPN-accessible endpoint, staging URL, or controlled tunnel when local/private runtime scanning is required.

- The deploy stage should pass the live runtime URL to the security-verification stage.
- The scan job should write gl-dast-report.json at the repository workspace root.
- The artifact must be declared under artifacts:reports:dast.
- The report should be locally schema-validated before treating it as production-ready.

## Process Flow: SAST to WhiteHax DAST Loop

![](images/image-001.png)

Figure 1. Recommended security loop for GitLab CI/CD: run SAST on code changes, fix and repeat, then run WhiteHax DAST after runtime deployment and feed fixes back to the next code update.

# 2. Important GitLab Difference

GitLab CI does not provide a direct equivalent to GitHub's deployment\_status event listener in this sample. The safer pattern is to run WhiteHax as a later stage after deployment, or trigger a separate pipeline and pass WHITEHAX\_TARGET\_URL explicitly. CI\_ENVIRONMENT\_URL is useful when the job has environment context, but a later independent job should not assume it is automatically available unless the pipeline passes it.

# 3. Repository Layout

.gitlab-ci.yml

whitehax\_scans/

whitehax\_tests.py

requirements.txt

requirements.txt should include requests and any WhiteHax SDK/client dependencies used by the real REST adapter.

# 4. Recommended .gitlab-ci.yml

Save the following example as .gitlab-ci.yml or merge the job into an existing pipeline. Replace deploy\_to\_aws with the repository's real deploy job. The dotenv handoff is included to make the runtime target URL explicit and reliable.

stages:

\- deploy

\- security-verification

\# Example: your real deploy job should set or publish the deployed runtime URL.

\# If the deploy job already defines environment:url, GitLab may expose CI\_ENVIRONMENT\_URL

\# inside that job. For a later job, pass the URL explicitly through dotenv or variables.

deploy\_to\_aws:

stage: deploy

script:

\- echo "Deploy application to AWS here"

\- echo "WHITEHAX\_TARGET\_URL=https://staging.example.com" > deploy.env

artifacts:

reports:

dotenv: deploy.env

whitehax\_dast\_scan:

stage: security-verification

image: python:3.11-slim

needs:

\- job: deploy\_to\_aws

artifacts: true

rules:

\- if: '$WHITEHAX\_TARGET\_URL != ""'

\- if: '$CI\_PIPELINE\_SOURCE == "trigger" && $WHITEHAX\_TARGET\_URL != ""'

\- when: never

variables:

TARGET\_URL: "$WHITEHAX\_TARGET\_URL"

WHITEHAX\_FAIL\_ON\_ERROR: "false"

before\_script:

\- python -m pip install --upgrade pip

\- |

if \[ -f whitehax\_scans/requirements.txt \]; then

pip install -r whitehax\_scans/requirements.txt

else

pip install requests

fi

script:

\- echo "Initializing WhiteHax DAST against runtime environment"

\- echo "Target URL is $TARGET\_URL"

\- python whitehax\_scans/whitehax\_tests.py

artifacts:

name: "whitehax-dast-findings"

when: always

paths:

\- gl-dast-report.json

reports:

dast: gl-dast-report.json

# 5. Recommended Python DAST Report Bridge

Save the following as whitehax\_scans/whitehax\_tests.py. The REST API call section is deliberately left as a TODO because the exact WhiteHax endpoint, request payload, polling behavior, and response fields are platform-specific.

#!/usr/bin/env python3

"""

WhiteHax GitLab DAST report bridge.

This sample keeps the WhiteHax REST API adapter as a placeholder and focuses on

stable GitLab CI behavior, report-shape hygiene, severity normalization, and

error-safe artifact generation.

"""

import hashlib

import json

import os

import sys

import traceback

from datetime import datetime, timezone

from pathlib import Path

from urllib.parse import urljoin, urlparse

import requests

OUTPUT\_FILE = Path("gl-dast-report.json")

GITLAB\_SEVERITIES = {

"critical": "Critical",

"high": "High",

"medium": "Medium",

"warning": "Medium",

"low": "Low",

"info": "Info",

"informational": "Info",

"unknown": "Unknown",

}

def now\_utc():

return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def require\_env(name):

value = os.environ.get(name)

if not value:

raise RuntimeError(f"Missing required environment variable: {name}")

return value

def normalize\_severity(value):

return GITLAB\_SEVERITIES.get(str(value or "").strip().lower(), "Unknown")

def stable\_finding\_id(finding, target\_url):

raw = "|".join(

\[

str(finding.get("id", "")),

str(finding.get("uri", "")),

str(finding.get("description", "")),

target\_url,

\]

)

return "whitehax-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()\[:32\]

def normalize\_finding(raw):

return {

"id": str(raw.get("id") or raw.get("rule\_id") or "WHX-GENERIC"),

"title": str(raw.get("title") or raw.get("name") or "WhiteHax finding"),

"description": str(raw.get("description") or raw.get("message") or ""),

"severity": normalize\_severity(raw.get("severity")),

"uri": str(raw.get("uri") or raw.get("path") or ""),

}

def run\_whitehax\_scan(whitehax\_url, api\_key, target\_url):

"""

TODO: Replace this placeholder with the real WhiteHax REST API workflow.

Expected behavior:

\- authenticate with WHITEHAX\_API\_KEY without printing it,

\- submit or trigger a scan for TARGET\_URL,

\- poll until the scan is complete or fails,

\- fetch findings from the completed scan, and

\- return a list of dictionaries that normalize\_finding() can consume.

"""

raise NotImplementedError("WhiteHax REST API adapter is project-specific.")

def build\_report(findings, target\_url, execution\_error=None):

start\_time = now\_utc()

vulnerabilities = \[\]

parsed\_target = urlparse(target\_url)

for raw in findings:

finding = normalize\_finding(raw)

path = "/" + finding\["uri"\].lstrip("/") if finding\["uri"\] else "/"

full\_url = urljoin(target\_url.rstrip("/") + "/", finding\["uri"\].lstrip("/"))

vulnerabilities.append(

{

"id": stable\_finding\_id(finding, target\_url),

"category": "dast",

"name": finding\["title"\],

"message": finding\["description"\] or finding\["title"\],

"description": finding\["description"\] or finding\["title"\],

"severity": finding\["severity"\],

"confidence": "Confirmed",

"scanner": {"id": "whitehax\_engine", "name": "WhiteHax Scan Core"},

"identifiers": \[

{

"type": "whitehax\_id",

"name": finding\["id"\],

"value": finding\["id"\],

}

\],

"links": \[{"url": full\_url}\],

"location": {

"hostname": parsed\_target.hostname or target\_url,

"path": path,

},

}

)

status = "success"

if execution\_error:

status = "failure"

vulnerabilities.append(

{

"id": stable\_finding\_id(

{

"id": "WHX-SCAN-ERROR",

"uri": "/",

"description": execution\_error,

},

target\_url,

),

"category": "dast",

"name": "WhiteHax scan execution error",

"message": execution\_error\[:4000\],

"description": execution\_error\[:4000\],

"severity": "Unknown",

"confidence": "Confirmed",

"scanner": {"id": "whitehax\_engine", "name": "WhiteHax Scan Core"},

"identifiers": \[

{

"type": "whitehax\_error",

"name": "WHX-SCAN-ERROR",

"value": "WHX-SCAN-ERROR",

}

\],

"location": {

"hostname": parsed\_target.hostname or target\_url,

"path": "/",

},

}

)

return {

"version": "15.0.0",

"scan": {

"analyzer": {

"id": "whitehax-dast",

"name": "WhiteHax DAST Plugin",

"vendor": {"name": "WhiteHax Sec"},

"version": "1.0.0",

},

"scanner": {

"id": "whitehax\_engine",

"name": "WhiteHax Scan Core",

"vendor": {"name": "WhiteHax Sec"},

"version": "1.0.0",

},

"type": "dast",

"start\_time": start\_time,

"end\_time": now\_utc(),

"status": status,

},

"vulnerabilities": vulnerabilities,

}

def write\_report(payload):

OUTPUT\_FILE.write\_text(json.dumps(payload, indent=2), encoding="utf-8")

print(f"\[INFO\] Wrote GitLab DAST report to {OUTPUT\_FILE}")

def main():

target\_url = os.environ.get("TARGET\_URL") or os.environ.get("CI\_ENVIRONMENT\_URL") or ""

try:

whitehax\_url = require\_env("WHITEHAX\_URL")

api\_key = require\_env("WHITEHAX\_API\_KEY")

target\_url = target\_url or require\_env("TARGET\_URL")

findings = run\_whitehax\_scan(whitehax\_url, api\_key, target\_url)

write\_report(build\_report(findings, target\_url))

except Exception as exc:

print("\[ERROR\] WhiteHax scan failed:", exc, file=sys.stderr)

traceback.print\_exc()

write\_report(build\_report(\[\], target\_url or "https://unknown-target.invalid", str(exc)))

if os.environ.get("WHITEHAX\_FAIL\_ON\_ERROR", "false").lower() == "true":

return 1

return 0

if \_\_name\_\_ == "\_\_main\_\_":

raise SystemExit(main())

# 6. Validation Notes

| **Area** | **Status** | **Recommended handling** |
| --- | --- | --- |
| Pipeline trigger | Needs correction | GitLab does not mirror GitHub deployment\_status. Use a later stage after deploy, dotenv handoff, or a triggered pipeline with WHITEHAX\_TARGET\_URL. |
| Rule condition | Bug fixed | Use CI\_PIPELINE\_SOURCE, not CI\_PIPIELINE\_SOURCE. Quote rules expressions in .gitlab-ci.yml. |
| DAST artifact | Valid | artifacts:reports:dast: gl-dast-report.json is the correct GitLab report hook. |
| Report visibility | Ultimate tier | DAST reports and vulnerability report integration require GitLab Ultimate for native security dashboards/widgets. |
| REST API adapter | Project-specific | Leave the WhiteHax API submit/poll/fetch flow as a placeholder until the endpoint contract is confirmed. |
| Report generation | Hardened | Use stable vulnerability IDs, normalized severity, hostname-only location, UTC timestamps, and error-safe artifact generation. |

# 7. Implementation Checklist

- Create CI/CD variables example WHITEHAX\_URL and WHITEHAX\_API\_KEY and mark them masked/protected where appropriate.
- Pass the deployed application URL as WHITEHAX\_TARGET\_URL, TARGET\_URL, or CI\_ENVIRONMENT\_URL.
- Replace run\_whitehax\_scan() with the real WhiteHax REST API submit, poll, and fetch-results flow.
- Normalize real WhiteHax findings into id, title, description, severity, and uri.
- Validate gl-dast-report.json against GitLab's security report schema before rollout.
- Decide whether WHITEHAX\_FAIL\_ON\_ERROR should remain false for report-only mode or true for blocking mode.

# 8. Common Pitfalls

- Do not use CI\_PIPIELINE\_SOURCE; the correct predefined variable is CI\_PIPELINE\_SOURCE.
- Do not assume a post-deploy job automatically inherits CI\_ENVIRONMENT\_URL without explicitly passing or defining it.
- Do not print WhiteHax API keys or authorization headers in GitLab job logs.
- Do not use unstable IDs such as loop indexes for long-term vulnerability tracking.
- Do not emit raw scanner severity values unless they map to GitLab's allowed severity vocabulary.
- Do not skip paths: if users need to browse the JSON artifact, include artifacts:paths in addition to artifacts:reports:dast.
