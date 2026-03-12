# ClaraMed Appointment Booking System

> A production-ready patient appointment booking application built with Python/Flask, deployed on AWS Elastic Beanstalk, with a fully automated 7-stage CI/CD pipeline using AWS CodePipeline — demonstrating both Continuous Deployment and Continuous Delivery patterns.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat&logo=flask&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-Elastic%20Beanstalk-FF9900?style=flat&logo=amazonaws&logoColor=white)
![Region](https://img.shields.io/badge/Region-ca--central--1-232F3E?style=flat&logo=amazonaws&logoColor=white)
![CI/CD](https://img.shields.io/badge/CI%2FCD-CodePipeline-FF9900?style=flat&logo=amazonaws&logoColor=white)

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Solution](#solution)
- [Why These AWS Services](#why-these-aws-services)
- [Expected Impact](#expected-impact)
- [Architecture](#architecture)
- [CI/CD Pipeline](#cicd-pipeline)
- [Tech Stack](#tech-stack)
- [Application Features](#application-features)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)
- [Running Locally](#running-locally)
- [Running Tests](#running-tests)
- [Deploying to Elastic Beanstalk](#deploying-to-elastic-beanstalk)

---

## Problem Statement

**ClaraMed Clinic Network** is a fast-growing Canadian healthcare company operating **12 clinics across Ontario and Quebec**, serving over **47,000 patients annually**. As of 2024, their appointment booking process ran entirely on phone calls and manually maintained spreadsheets — a system visibly breaking under growth pressure.

### Operational Pain Points

| Problem | Measured Impact |
|---|---|
| ~340 booking calls handled per day across all clinics | Front desk staff spending 60–70% of their shift on the phone |
| Average 8 minutes per booking call | High operational cost per appointment |
| 12% of appointments had scheduling conflicts | Direct result of manual, error-prone data entry |
| 23% patient no-show rate | No automated confirmations or reminders |
| ~$180 CAD revenue lost per missed appointment | **~$1.5M CAD lost annually** across the network |

### Engineering Pain Points

Beyond the operational problems, ClaraMed's 4-person engineering team had no standardized release process:

- Developers pushed code **directly to production** with no automated testing gate
- No staging environment — bugs were caught by patients, not engineers
- A bad deployment in **November 2023** caused a **4-hour outage across 3 clinics**, directly impacting patient care
- The ClaraMed Medical Director had **no visibility or control** over when software changes went live
- No audit trail of deployments — no way to answer "what changed and who approved it?"

The root cause was not a lack of engineering skill — it was a lack of **process and tooling**. The team needed infrastructure that enforced good practices automatically, without requiring them to manage servers.

---

## Solution

This project delivers two things simultaneously:

**1. A web-based appointment booking system** — patients and clinic staff can book, view, and cancel appointments through a browser instead of a phone call, backed by a REST API that integrates with future systems (EHR, SMS reminders, billing).

**2. A production-grade CI/CD pipeline** — every code change is automatically tested, deployed to staging, validated, and held at a manual approval gate before the ClaraMed Medical Director authorises a production release. No code reaches patients without being tested and signed off.

---

## Why These AWS Services

Each service was chosen for a specific technical and business reason.

### AWS Elastic Beanstalk — Application Hosting

**The problem it solves:** ClaraMed's engineers are application developers, not infrastructure engineers. Provisioning EC2 instances, configuring Auto Scaling groups, setting up ALBs, patching OS packages — none of that delivers patient value.

**Why Beanstalk specifically:**
- Handles provisioning, load balancing, auto-scaling, and health monitoring automatically
- Supports multiple named environments (`claramed-staging`, `claramed-preprod`, `claramed-production`) — essential for the multi-stage pipeline
- Zero-downtime rolling deployments — critical for a patient-facing healthcare application
- Still gives full access to underlying EC2 and VPC configuration when needed, unlike fully serverless options
- Native integration with CodePipeline — no custom deployment scripts required

**Why not ECS or Lambda:** ECS requires managing task definitions, clusters, and container networking — unnecessary overhead for a team of 4. Lambda would require significant architectural changes to the Flask app and introduces cold-start latency unacceptable for a booking UI.

---

### AWS CodePipeline — CI/CD Orchestration

**The problem it solves:** Developers were deploying manually with no consistent process. CodePipeline enforces a repeatable, auditable release workflow — every deployment follows the same stages in the same order, every time.

**Why CodePipeline specifically:**
- Native integration with GitHub, CodeBuild, Elastic Beanstalk, and SNS — no glue code or third-party plugins
- Visual pipeline view gives non-technical stakeholders (ClaraMed Medical Director) real-time visibility into release status
- Built-in manual approval actions with SNS notifications — exactly what the hierarchy-approval requirement needs
- Full execution history provides an audit trail: every deployment, who approved it, and when
- IAM-native — no third-party credentials or secrets to rotate

**Why not GitHub Actions or Jenkins:** GitHub Actions requires managing cross-service IAM integration manually. Jenkins requires provisioning and maintaining a build server — contrary to the no-infrastructure-management requirement.

---

### AWS CodeBuild — Build and Test Runner

**The problem it solves:** Before this project, code was never tested before deployment. CodeBuild runs the full `pytest` suite on every push — if any test fails, the pipeline stops and nothing deploys.

**Why CodeBuild specifically:**
- Fully managed — no build server to maintain or scale
- Build config lives in `buildspec.yml`, committed to the repo — infrastructure as code
- Native CodePipeline integration means zero configuration to wire the two together
- Execution logs streamed to CloudWatch for debugging failed builds

---

### AWS SNS — Hierarchy Approval Notifications

**The problem it solves:** The ClaraMed Medical Director needs to approve production releases but should not need to log into the AWS console.

**Why SNS specifically:**
- CodePipeline's manual approval action natively publishes to an SNS topic
- The ClaraMed Medical Director receives an email with a direct approve/reject link — no AWS account required
- SNS can deliver to email, SMS, or HTTP endpoints — notification channel can change without modifying the pipeline
- Creates a hard architectural gate: production deployment is **impossible** without explicit approval — it is not just a convention or a policy

---

### Amazon S3 — Artifact Storage

**The problem it solves:** Pipeline stages need to reliably pass the same build artifact (the packaged application zip) between them without transformation.

**Why S3:** CodePipeline uses S3 natively as its artifact store. Versioned, durable, and IAM-controlled — the exact zip that CodeBuild produces is what Elastic Beanstalk receives. No intermediate storage to manage.

---

### Amazon CloudWatch — Observability *(planned)*

**The problem it solves:** The November 2023 outage went undetected for 20 minutes because there were no automated health checks or alerting.

**Planned implementation:**
- Application logs streamed from Elastic Beanstalk to CloudWatch Logs
- Alarms on HTTP 5xx error rate — threshold: >1% over 5 minutes triggers PagerDuty alert
- Deployment health alarm triggered automatically after each production CodePipeline execution
- 90-day log retention for PIPEDA compliance

---

### Route 53 + ACM — Custom Domain and TLS *(planned)*

**Why needed:** `appointments.claramed.ca` with valid TLS is a baseline requirement for any patient-facing healthcare application — for trust, usability, and regulatory optics under PIPEDA (Canada's federal privacy law).

ACM certificates are free and auto-renewing, integrating directly with the Elastic Beanstalk ALB. Route 53 enables weighted routing between environments for blue/green deployments in a future iteration.

---

### Amazon CloudFront — CDN *(planned)*

**Why needed:** ClaraMed's clinics span from Windsor to Montreal. Without a CDN, all static assets are served from a single `ca-central-1` origin. CloudFront caches at Canadian PoPs, reducing latency for clinic staff, and absorbs traffic spikes during high-demand periods (flu season, Monday mornings).

---

## Expected Impact

### Operational Impact

| Metric | Before | After (Projected) |
|---|---|---|
| Booking method | Phone only | Web self-serve + phone |
| Staff time per online booking | 8 min | ~0 min |
| Scheduling conflict rate | 12% | < 1% (system-enforced validation) |
| Patient no-show rate | 23% | ~10% (automated confirmations) |
| Annual revenue lost to no-shows | ~$1.5M CAD | ~$650K CAD |
| **Net annual saving** | — | **~$850K CAD** |

### Engineering Impact

| Metric | Before | After |
|---|---|---|
| Deployment process | Manual, ad hoc | Automated 7-stage pipeline |
| Test coverage enforced on deploy | 0% | 100% — pipeline blocked if tests fail |
| Mean time to detect production outage | 20+ min (user reports) | < 5 min (CloudWatch alarm) |
| Mean time to recover from bad deploy | 4+ hours | < 10 min (Beanstalk environment rollback) |
| Unauthorised production releases | Possible | Architecturally prevented by SNS gate |
| Deployment audit trail | None | Full history in CodePipeline console |

---

## Architecture

```
User / Browser
      |
   Route 53              (planned — custom domain: appointments.claramed.ca)
      |
  CloudFront             (planned — CDN, Canadian PoPs)
      |
     ALB                 (managed automatically by Elastic Beanstalk)
      |
      +─────────────────────────────+
      |                             |
Elastic Beanstalk             Elastic Beanstalk
claramed-staging               claramed-production
claramed-preprod
      |                             |
      +─────────────────────────────+
                    |
             (Future) RDS MySQL     (persistent storage, replacing in-memory store)
                    |
            AWS Secrets Manager     (DB credentials, injected at runtime via IAM)


CI/CD Pipeline (AWS CodePipeline)
──────────────────────────────────────────────────────────────
GitHub push to main
  → [1] Source          GitHub — pipeline triggered on push
  → [2] Build           CodeBuild — pip install, pytest, zip artifact
  → [3] Deploy Staging  Beanstalk claramed-staging             ← Continuous Deployment
  → [4] Smoke Test      CodeBuild — tests against live staging URL
  → [5] Pre-Production  Beanstalk claramed-preprod             ← Continuous Delivery
  → [6] Approval        SNS email to ClaraMed Medical Director — approve or reject
  → [7] Production      Beanstalk claramed-production (only if approved)
```

---

## CI/CD Pipeline

This project deliberately demonstrates the distinction between **Continuous Deployment** and **Continuous Delivery** — a distinction that matters in regulated environments like healthcare.

### Stages 1–3: Continuous Integration + Continuous Deployment

Code is automatically tested and deployed to staging on every push — no human involved.

| Stage | Tool | Description |
|---|---|---|
| 1 — Source | GitHub | Push to `main` triggers the pipeline automatically |
| 2 — Build | CodeBuild | Installs deps, runs `pytest`, packages app as zip artifact |
| 3 — Deploy Staging | Elastic Beanstalk | Auto-deploys to `claramed-staging` if all tests pass |

### Stages 4–7: Continuous Integration + Continuous Delivery

Production requires human sign-off — the ClaraMed Medical Director controls the final gate.

| Stage | Tool | Description |
|---|---|---|
| 4 — Test Staging | CodeBuild | Smoke tests run against the live staging endpoint |
| 5 — Pre-Production | Elastic Beanstalk | Deploys to `claramed-preprod` for final validation |
| 6 — Approval | SNS | Email sent to ClaraMed Medical Director — one-click approve or reject |
| 7 — Production | Elastic Beanstalk | Deploys to `claramed-production` only after approval |

> **Why the distinction matters:** In healthcare, deploying untested code to production without oversight is a liability — technical and regulatory. Stages 1–3 give engineers fast feedback loops. Stages 4–7 give the organisation control and an audit trail. Both are necessary.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Framework | Flask 3.0 |
| Web Server | Gunicorn (3 workers) |
| Hosting | AWS Elastic Beanstalk |
| CI/CD Orchestration | AWS CodePipeline |
| Build and Test | AWS CodeBuild + pytest |
| Approval Gate | AWS SNS |
| Artifact Storage | AWS S3 |
| Source Control | GitHub |
| Region | ca-central-1 |

---

## Application Features

- Book patient appointments with available doctors
- View all appointments in a live table
- Cancel appointments
- REST API for future integrations (EHR, SMS reminders, billing)
- `/api/health` endpoint for Elastic Beanstalk ALB health checks
- Environment and version banner on the UI — useful for confirming which environment you are on during pipeline validation

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Web UI |
| GET | `/api/health` | Health check — polled by ALB |
| GET | `/api/doctors` | List all available doctors |
| GET | `/api/appointments` | List all appointments |
| POST | `/api/appointments` | Book a new appointment |
| GET | `/api/appointments/<id>` | Get a single appointment by ID |
| DELETE | `/api/appointments/<id>` | Cancel an appointment |

### POST `/api/appointments` — Request Body

```json
{
  "patient_name": "John Smith",
  "doctor_id": "D001",
  "appointment_date": "2025-09-15T10:00",
  "reason": "Annual checkup"
}
```

### Response `201 Created`

```json
{
  "message": "Appointment booked",
  "appointment": {
    "id": "e3b0c442-98fb-1c55-ad53-6c9ef8292a1f",
    "patient_name": "John Smith",
    "doctor_name": "Dr. Sarah Tremblay",
    "specialty": "General Practice",
    "appointment_date": "2025-09-15T10:00",
    "status": "confirmed",
    "created_at": "2025-09-01T14:32:00Z"
  }
}
```

---

## Project Structure

```
claramed-appointments/
├── app.py                    # Flask app — all API routes + HTML UI
├── requirements.txt          # Python dependencies
├── Procfile                  # Tells Beanstalk to use Gunicorn, not Flask dev server
├── buildspec.yml             # CodeBuild: install → test → package artifact
├── .ebextensions/
│   └── python.config         # WSGI entry point, env vars, static file mapping
└── tests/
    └── test_app.py           # 10 pytest unit tests covering all endpoints
```

---

## Running Locally

```bash
# Clone the repo
git clone https://github.com/njamutoh/From-Code-to-Production-CI-CD-Pipeline-with-AWS-Elasticbeanstalk-and-CodePipeline-Containerized-Application-on-AWS.git
cd claramed-appointments

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Visit `http://localhost:5000`

---

## Running Tests

```bash
pytest tests/ -v
```

Expected output:

```
tests/test_app.py::test_health_check                        PASSED
tests/test_app.py::test_get_doctors                         PASSED
tests/test_app.py::test_create_appointment                  PASSED
tests/test_app.py::test_create_appointment_missing_patient  PASSED
tests/test_app.py::test_create_appointment_invalid_doctor   PASSED
tests/test_app.py::test_get_appointments_empty              PASSED
tests/test_app.py::test_get_appointments_after_create       PASSED
tests/test_app.py::test_cancel_appointment                  PASSED
tests/test_app.py::test_cancel_nonexistent_appointment      PASSED
tests/test_app.py::test_ui_loads                            PASSED

10 passed in 0.42s
```

---

## Deploying to Elastic Beanstalk

### Prerequisites

- AWS CLI configured (`aws configure`)
- EB CLI installed (`pip install awsebcli`)

### Steps

```bash
# Initialise Elastic Beanstalk application
eb init claramed-appointments --region ca-central-1 --platform python-3.11

# Create the three environments
eb create claramed-staging
eb create claramed-preprod
eb create claramed-production

# Manual deploy (CodePipeline handles this automatically once the pipeline is set up)
eb deploy claramed-production
```

---

## Author

**njamutoh** — [GitHub](https://github.com/njamutoh) | [LinkedIn](#)

> Region: `ca-central-1` &nbsp;|&nbsp; Python 3.11 + Flask &nbsp;|&nbsp; AWS Elastic Beanstalk + CodePipeline
