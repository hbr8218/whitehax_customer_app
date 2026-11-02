GitHub Actions:

```
gh workflow run whitehax-dast.yml -f target_url="http://54.177.207.48:8000/chat" -f profile_id="729"
```

GitLab CI (Run pipeline, pipelines API, or a trigger). Store `WHITEHAX_URL`, `WHITEHAX_API_KEY`, `WHITEHAX_EMAIL`, and `WHITEHAX_PASSWORD` as masked CI/CD variables. Pass the runtime URL as `WHITEHAX_TARGET_URL` when the pipeline starts. Optional pipeline variables: `WHITEHAX_PROFILE_ID`, `WHITEHAX_REPORT_ID`, `WHITEHAX_FAIL_ON_ERROR`. The job writes `gl-dast-report.json` and publishes it with `artifacts:reports:dast`.

```
curl --request POST \
  --header "PRIVATE-TOKEN: <token>" \
  --form "ref=main" \
  --form "variables[WHITEHAX_TARGET_URL]=http://54.177.207.48:8000/chat" \
  --form "variables[WHITEHAX_PROFILE_ID]=729" \
  "https://gitlab.example.com/api/v4/projects/<id>/pipeline"
```