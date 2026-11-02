To integrate the dynamic WhiteHax Tests (Scan) script with GitLab, the approach mirrors GitHub, but 
you will output GitLab's native DAST JSON report schema instead of SARIF.
GitLab natively parses files assigned to the artifacts:reports:dast block and 
maps those vulnerabilities straight to your project's Vulnerability Report and Merge Request security widgets.

This configuration below uses an independent pipeline structure. It triggers whenever 
an environment is successfully deployed, fetches your custom Python execution script, 
and securely provisions the system environment keys.

### YAML Code below - save it in .gitlab-ci.yml in your repository:

stages:
  - security-verification

whitehax_dast_scan:
  stage: security-verification
  image: python:3.11-slim
  rules:
    # Triggers only when a deployment pipeline finishes successfully
    # Note: Ensure your deployment job explicitly defines an "environment" block
    - if: $CI_PIPIELINE_SOURCE == "trigger" || $CI_ENVIRONMENT_URL != null
  
  before_script:
    - pip install --upgrade pip
    # Install requests or any other needed utility frameworks if they exist
    - if [ -f whitehax_scans/requirements.txt ]; then pip install -r whitehax_scans/requirements.txt; fi

  script:
    - echo "Initializing WhiteHax DAST against AWS runtime environment..."
    - echo "Target URL is $CI_ENVIRONMENT_URL"
    
    # Executes the python blueprint script
    - python whitehax_scans/whitehax_tests.py

  artifacts:
    name: "whitehax-dast-findings"
    when: always # Ensures report is captured even if vulnerabilities are found
    reports:
      # CRITICAL: GitLab maps this exact key to the native Vulnerability Report
      dast: gl-dast-report.json 


