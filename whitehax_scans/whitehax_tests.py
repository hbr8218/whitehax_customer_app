#!/usr/bin/env python3
"""
WhiteHax GitHub Actions SARIF bridge.

Calls the WhiteHaX external REST API to start a profile job, poll until
complete, fetch the report, and map findings into SARIF for Code Scanning.

This is NOT a replacement for WHFTCLI.py — the platform still runs the tester.
"""

from __future__ import annotations

import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests


OUTPUT_FILE = Path("whitehax_results.sarif")
SARIF_LEVELS = {
    "critical": "error",
    "high": "error",
    "error": "error",
    "medium": "warning",
    "warning": "warning",
    "low": "note",
    "info": "note",
    "informational": "note",
    "none": "none",
}

# Terminal job statuses returned by the WhiteHaX jobs API / status tracker.
SUCCESS_STATUSES = {"completed", "success", "succeeded", "done"}
FAILURE_STATUSES = {"failed", "error", "cancelled", "canceled", "aborted"}


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def sarif_level(severity: Any) -> str:
    return SARIF_LEVELS.get(str(severity or "").strip().lower(), "warning")


def normalize_finding(raw: dict) -> dict:
    """Map one WhiteHax API finding into the small internal shape below."""
    return {
        "id": str(raw.get("id") or raw.get("rule_id") or "WHX-GENERIC"),
        "title": str(raw.get("title") or raw.get("name") or "WhiteHax finding"),
        "description": str(raw.get("description") or raw.get("message") or ""),
        "severity": sarif_level(raw.get("severity") or raw.get("risk_level")),
        "uri": str(raw.get("uri") or raw.get("path") or ""),
    }


def auth_headers(api_key: str) -> dict:
    return {"Authorization": api_key}


def api_base(whitehax_url: str) -> str:
    return whitehax_url.rstrip("/")


def _unwrap_payload(payload: Any) -> Any:
    """Unwrap common WhiteHaX envelopes like {\"data\": ...} or {\"error\": false, \"data\": ...}."""
    if not isinstance(payload, dict):
        return payload
    if "data" in payload and isinstance(payload["data"], (dict, list)):
        return payload["data"]
    return payload


def _request_json(
    method: str,
    url: str,
    api_key: str,
    *,
    data: dict | None = None,
    timeout: int = 60,
) -> Any:
    response = requests.request(
        method,
        url,
        headers=auth_headers(api_key),
        data=data,
        timeout=timeout,
    )
    if response.status_code >= 400:
        raise RuntimeError(
            f"WhiteHaX API {method} {url} failed with HTTP {response.status_code}: "
            f"{response.text[:500]}"
        )
    if not response.text.strip():
        return {}
    try:
        return response.json()
    except ValueError as exc:
        raise RuntimeError(f"WhiteHaX API returned non-JSON from {url}: {response.text[:300]}") from exc


def start_job(whitehax_url: str, api_key: str, profile_id: str, report_name: str) -> str:
    """POST /api/external/jobs/ and return the new job id."""
    url = f"{api_base(whitehax_url)}/api/external/jobs/"
    payload = _request_json(
        "POST",
        url,
        api_key,
        data={"profile_id": profile_id, "report_name": report_name},
    )
    body = _unwrap_payload(payload)
    if not isinstance(body, dict):
        body = payload if isinstance(payload, dict) else {}

    for key in ("job_id", "id", "JobId", "jobId"):
        if body.get(key) is not None:
            return str(body[key])
        if isinstance(payload, dict) and payload.get(key) is not None:
            return str(payload[key])

    raise RuntimeError(
        "Could not find job_id in start-job response. "
        f"Keys seen: {sorted(body.keys()) if isinstance(body, dict) else type(body)}"
    )


def _extract_status_and_report_id(payload: Any) -> tuple[str, str | None]:
    """Parse job status + optional report_id from varied API shapes."""
    body = _unwrap_payload(payload)
    candidates: list[dict] = []
    if isinstance(body, dict):
        candidates.append(body)
        overall = body.get("overall")
        if isinstance(overall, dict):
            candidates.append(overall)
    if isinstance(payload, dict) and payload is not body:
        candidates.append(payload)

    status = ""
    report_id = None
    for item in candidates:
        for key in ("status", "job_status", "state"):
            if item.get(key):
                status = str(item[key]).strip().lower()
                break
        if status:
            break

    for item in candidates:
        for key in ("report_id", "reportId", "result_id"):
            if item.get(key) not in (None, "", 0, "0"):
                report_id = str(item[key])
                break
        if report_id:
            break

    return status, report_id


def poll_job(
    whitehax_url: str,
    api_key: str,
    job_id: str,
    *,
    poll_interval: int,
    poll_timeout: int,
) -> str:
    """Poll GET /api/external/jobs/{job_id}/status/ until complete; return report_id."""
    url = f"{api_base(whitehax_url)}/api/external/jobs/{job_id}/status/"
    deadline = time.time() + poll_timeout
    last_status = ""

    while time.time() < deadline:
        payload = _request_json("GET", url, api_key)
        status, report_id = _extract_status_and_report_id(payload)
        last_status = status or last_status or "unknown"
        print(f"[INFO] Job {job_id} status={last_status} report_id={report_id or '-'}")

        if status in SUCCESS_STATUSES:
            if not report_id:
                raise RuntimeError(
                    f"Job {job_id} completed but no report_id was returned in status payload."
                )
            return report_id

        if status in FAILURE_STATUSES:
            raise RuntimeError(f"Job {job_id} ended with status '{status}'.")

        time.sleep(poll_interval)

    raise TimeoutError(
        f"Timed out after {poll_timeout}s waiting for job {job_id} "
        f"(last status: {last_status or 'unknown'})."
    )


def fetch_report(whitehax_url: str, api_key: str, report_id: str) -> dict:
    """GET readiness-score/getReportById/{report_id} and return normalized report dict."""
    url = f"{api_base(whitehax_url)}/api/external/readiness-score/getReportById/{report_id}"
    payload = _request_json("GET", url, api_key)
    body = _unwrap_payload(payload)
    if not isinstance(body, dict):
        raise RuntimeError(f"Unexpected report payload type: {type(body)}")

    score_json = body.get("score_json", body)
    if isinstance(score_json, str):
        score_json = json.loads(score_json)
    if not isinstance(score_json, dict):
        raise RuntimeError("Report did not contain a score_json object.")

    return {
        "report_id": str(body.get("id") or report_id),
        "profile_id": body.get("profile_id"),
        "score_json": score_json,
    }


def _textify(value: Any, limit: int = 1200) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        text = value
    else:
        try:
            text = json.dumps(value, ensure_ascii=False)
        except TypeError:
            text = str(value)
    return " ".join(text.split())[:limit]


def findings_from_score_json(score_json: dict, target_url: str) -> list[dict]:
    """Extract failed tests / detailed results / security findings from score_json."""
    findings: list[dict] = []

    data = score_json.get("data") if isinstance(score_json.get("data"), dict) else {}
    for tester, block in data.items():
        if not isinstance(block, dict):
            continue
        failed_tests = block.get("failed_tests")
        if not isinstance(failed_tests, dict):
            continue
        for subcategory, failures in failed_tests.items():
            if isinstance(failures, dict):
                failures = [failures]
            if not isinstance(failures, list):
                continue
            for index, failure in enumerate(failures):
                if not isinstance(failure, dict):
                    failure = {"payload": failure}
                test_id = failure.get("test_id") or f"{tester}-{subcategory}-{index}"
                findings.append(
                    {
                        "id": f"WH-TEST-{tester}-{subcategory}",
                        "title": f"{tester}: {subcategory}",
                        "description": _textify(
                            failure.get("payload")
                            or failure.get("details")
                            or f"{subcategory} failed"
                        ),
                        "severity": failure.get("risk_level") or "high",
                        "uri": target_url,
                        "rule_id": f"WH-TEST-{tester}-{subcategory}",
                        "name": f"{tester}: {subcategory}",
                        "message": _textify(failure.get("payload") or failure.get("details")),
                        "path": target_url,
                        "test_id": test_id,
                    }
                )

    for section_key in ("mcp_agent_simulation", "dos_simulation"):
        section = score_json.get(section_key)
        if not isinstance(section, dict):
            continue

        detailed = section.get("detailed_results")
        if isinstance(detailed, list):
            for index, item in enumerate(detailed):
                if not isinstance(item, dict):
                    continue
                passed = item.get("passed")
                risk = str(item.get("risk_level") or item.get("severity") or "").lower()
                if passed is True and risk not in {"critical", "high"}:
                    continue
                attack = item.get("attack_type") or item.get("category") or "detailed-result"
                findings.append(
                    {
                        "id": f"WH-DETAIL-{attack}",
                        "title": str(attack),
                        "description": _textify(
                            item.get("details") or item.get("payload") or item.get("description") or attack
                        ),
                        "severity": item.get("risk_level") or item.get("severity") or "medium",
                        "uri": target_url,
                    }
                )

        sec_findings = section.get("security_findings")
        if isinstance(sec_findings, list):
            for item in sec_findings:
                if not isinstance(item, dict):
                    continue
                title = item.get("finding") or item.get("title") or item.get("attack_type") or "security finding"
                findings.append(
                    {
                        "id": f"WH-FINDING-{title}",
                        "title": str(title),
                        "description": _textify(
                            item.get("description")
                            or item.get("details")
                            or item.get("security_impact")
                            or title
                        ),
                        "severity": item.get("risk_level") or item.get("severity") or "medium",
                        "uri": target_url,
                    }
                )

    return findings


def run_whitehax_scan(whitehax_url: str, api_key: str, target_url: str) -> list:
    """
    Start (or resume) a WhiteHaX profile job, wait for completion, and return findings.

    Required env:
      WHITEHAX_PROFILE_ID   — profile whose endpoint/tests should run
                              (platform jobs API is profile-based; TARGET_URL is used
                              for SARIF locations / logging, not job creation)

    Optional env:
      WHITEHAX_REPORT_NAME  — report label (default: github-actions-whitehax)
      WHITEHAX_JOB_ID       — skip start; poll an existing job
      WHITEHAX_REPORT_ID    — skip start+poll; fetch this report only
      WHITEHAX_POLL_INTERVAL_SEC  — default 5
      WHITEHAX_POLL_TIMEOUT_SEC   — default 360
    """
    profile_id = "418" #os.environ.get("WHITEHAX_PROFILE_ID", "").strip()
    report_name = "customer-app" # os.environ.get("WHITEHAX_REPORT_NAME", "github-actions-whitehax").strip()
    existing_job_id = "0" # os.environ.get("WHITEHAX_JOB_ID", "").strip()
    existing_report_id = os.environ.get("WHITEHAX_REPORT_ID", "").strip()
    poll_interval = env_int("WHITEHAX_POLL_INTERVAL_SEC", 3)
    poll_timeout = env_int("WHITEHAX_POLL_TIMEOUT_SEC", 360)

    print(f"[INFO] WhiteHaX URL: {api_base(whitehax_url)}")
    print(f"[INFO] Target URL (SARIF locations): {target_url}")
    if profile_id:
        print(f"[INFO] Profile ID: {profile_id}")

    if existing_report_id:
        report_id = existing_report_id
        print(f"[INFO] Using existing report_id={report_id}")
    else:
        if existing_job_id:
            job_id = existing_job_id
            print(f"[INFO] Resuming existing job_id={job_id}")
        else:
            if not profile_id:
                raise RuntimeError(
                    "WHITEHAX_PROFILE_ID is required to start a job "
                    "(or set WHITEHAX_JOB_ID / WHITEHAX_REPORT_ID to resume)."
                )
            print(f"[INFO] Starting WhiteHaX job for profile_id={profile_id}")
            job_id = start_job(whitehax_url, api_key, profile_id, report_name)
            print(f"[INFO] Started job_id={job_id}")

        report_id = poll_job(
            whitehax_url,
            api_key,
            job_id,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
        )
        print(f"[INFO] Job finished with report_id={report_id}")

    report = fetch_report(whitehax_url, api_key, report_id)
    findings = findings_from_score_json(report["score_json"], target_url)
    print(f"[INFO] Extracted {len(findings)} finding(s) from report {report_id}")
    return findings


def build_sarif(findings: list, target_url: str, execution_error: str | None = None) -> dict:
    run = {
        "tool": {
            "driver": {
                "name": "WhiteHax DAST",
                "informationUri": "https://whitehax.com",
                "rules": [],
            }
        },
        "results": [],
        "invocations": [
            {
                "executionSuccessful": execution_error is None,
                "endTimeUtc": datetime.now(timezone.utc).isoformat(),
            }
        ],
    }

    rules = {}
    for raw in findings:
        finding = normalize_finding(raw)
        if finding["id"] not in rules:
            rules[finding["id"]] = {
                "id": finding["id"],
                "name": finding["title"],
                "shortDescription": {"text": finding["title"]},
                "fullDescription": {"text": finding["description"] or finding["title"]},
                "defaultConfiguration": {"level": finding["severity"]},
            }

        location_uri = urljoin(target_url.rstrip("/") + "/", finding["uri"].lstrip("/")) if finding["uri"] else target_url
        if finding["uri"].startswith("http://") or finding["uri"].startswith("https://"):
            location_uri = finding["uri"]

        run["results"].append(
            {
                "ruleId": finding["id"],
                "level": finding["severity"],
                "message": {"text": finding["description"] or finding["title"]},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": location_uri or target_url or "about:blank"}
                        }
                    }
                ],
            }
        )

    if execution_error:
        rules["WHX-SCAN-ERROR"] = {
            "id": "WHX-SCAN-ERROR",
            "name": "WhiteHax scan execution error",
            "shortDescription": {"text": "WhiteHax scan execution error"},
            "defaultConfiguration": {"level": "warning"},
        }
        run["results"].append(
            {
                "ruleId": "WHX-SCAN-ERROR",
                "level": "warning",
                "message": {"text": execution_error[:4000]},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": target_url or "about:blank"}
                        }
                    }
                ],
            }
        )

    run["tool"]["driver"]["rules"] = list(rules.values())
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [run],
    }


def write_sarif(payload: dict) -> None:
    OUTPUT_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[INFO] Wrote SARIF results to {OUTPUT_FILE}")


def main() -> int:
    target_url = os.environ.get("TARGET_URL", "")
    try:
        whitehax_url = "https://demo.whitehax.com" #require_env("WHITEHAX_URL")
        api_key = "" #require_env("WHITEHAX_API_KEY")
        target_url = "" #require_env("TARGET_URL")

        findings = run_whitehax_scan(whitehax_url, api_key, target_url)
        write_sarif(build_sarif(findings, target_url))
    except Exception as exc:
        print("[ERROR] WhiteHax scan failed:", exc, file=sys.stderr)
        traceback.print_exc()
        write_sarif(build_sarif([], target_url or "about:blank", str(exc)))
        if os.environ.get("WHITEHAX_FAIL_ON_ERROR", "false").lower() == "true":
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
