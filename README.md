# WhiteHaX Customer App — GitHub CI/CD scaffold

Template repository for attaching **WhiteHaX DAST verification** to a customer application’s GitHub Actions pipeline.

This is **not** the WhiteHaX tester engine (`WHFTCLI.py` / `cli_main`). That still runs on the WhiteHaX platform. This repo is the **customer-side remote control**: after deploy → call WhiteHaX API → upload SARIF to GitHub Code Scanning.

```
Customer deploy succeeds
        ↓
GitHub deployment_status (environment_url)
        ↓
.github/workflows/whitehax-dast.yml
        ↓
whitehax_scans/whitehax_tests.py  →  WhiteHaX REST API
        ↓
whitehax_results.sarif
        ↓
GitHub Code Scanning alerts
```

## Layout

```
WhiteHaX_customer_app/
├── .github/workflows/whitehax-dast.yml   # CI trigger + SARIF upload
├── whitehax_scans/
│   ├── whitehax_tests.py                 # API bridge + SARIF writer
│   └── requirements.txt
└── README.md
```

## Setup

### 1. Create a new GitHub repository

Copy this folder into a new empty repo (or use it as the repo root).

### 2. Add repository secrets

| Secret | Purpose |
|--------|---------|
| `WHITEHAX_URL` | Base URL of the WhiteHaX API (e.g. `https://demo.whitehax.com`) |
| `WHITEHAX_API_KEY` | External API key (`Authorization` header) |
| `WHITEHAX_PROFILE_ID` | Profile whose endpoint/tests the job should run |

GitHub → **Settings → Secrets and variables → Actions**.

### 3. Enable Code Scanning

The repo must allow Code Scanning so `upload-sarif` can publish alerts (**Security → Code scanning**).

### 4. Confirm deployments publish `environment_url`

The workflow only runs when:

- `deployment_status.state == success`
- `environment_url` is non-empty

Your deploy system must create GitHub `deployment_status` events with a reachable URL.

### 5. Adapter behavior (already implemented)

`run_whitehax_scan()` now:

1. `POST /api/external/jobs/` with `profile_id` + report name  
2. Polls `GET /api/external/jobs/{job_id}/status/` until completed/failed  
3. `GET /api/external/readiness-score/getReportById/{report_id}`  
4. Maps `score_json` `failed_tests` / `detailed_results` / `security_findings` into SARIF findings  

**Note:** The jobs API is **profile-based**. `TARGET_URL` is used for SARIF location URIs and logging. The profile’s configured endpoint should already point at the deployed app (or match that URL).

Optional env overrides:

| Variable | Purpose |
|----------|---------|
| `WHITEHAX_JOB_ID` | Skip start; poll an existing job |
| `WHITEHAX_REPORT_ID` | Skip start+poll; fetch one report only |
| `WHITEHAX_REPORT_NAME` | Report label (default `github-actions-whitehax`) |
| `WHITEHAX_POLL_INTERVAL_SEC` | Poll interval (default `15`) |
| `WHITEHAX_POLL_TIMEOUT_SEC` | Max wait (default `3600`) |

## Local dry-run

```bash
cd WhiteHaX_customer_app
pip install -r whitehax_scans/requirements.txt

set WHITEHAX_URL=https://demo.whitehax.com
set WHITEHAX_API_KEY=your-key
set WHITEHAX_PROFILE_ID=418
set TARGET_URL=https://staging.example.com
set WHITEHAX_FAIL_ON_ERROR=false

python whitehax_scans/whitehax_tests.py
```

On Windows PowerShell use `$env:WHITEHAX_URL = "..."`.

To convert an existing report without starting a job:

```bash
set WHITEHAX_REPORT_ID=123
python whitehax_scans/whitehax_tests.py
```

## How this relates to Django / WHFTCLI

| Path | Who starts the scan | What runs the tests |
|------|---------------------|---------------------|
| Product UI / Django | View with `profile_id`, `user_id`, `job_id` | `python WHFTCLI.py --profile_id …` on the server |
| This GitHub scaffold | Actions with `TARGET_URL` + API key | Same platform eventually — CI only calls REST |

Same engine underneath; different front door.

## Fail mode

| `WHITEHAX_FAIL_ON_ERROR` | Behavior |
|--------------------------|----------|
| `false` (default) | Always write SARIF; workflow can stay green (report-only) |
| `true` | Exit non-zero if the scan/adapter fails (blocking) |

## Notes

- Do not print API keys in logs.
- `localhost` on a GitHub-hosted runner is the runner itself, not your laptop. Use a public staging URL, self-hosted runner, or tunnel for private targets.
- For production, validate SARIF upload in a staging repo before enabling blocking mode.
