# ClaraMed Appointment Booking System

> A production-ready patient appointment booking application built with Python/Flask — automated from GitHub push to production on AWS Elastic Beanstalk using CodePipeline, with multi-environment staging and SNS-gated production approval, illustrating the difference between Continuous Deployment and Continuous Delivery.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat&logo=flask&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-Elastic%20Beanstalk-FF9900?style=flat&logo=amazonaws&logoColor=white)
![Region](https://img.shields.io/badge/Region-us--east--1-232F3E?style=flat&logo=amazonaws&logoColor=white)
![CI/CD](https://img.shields.io/badge/CI%2FCD-CodePipeline-FF9900?style=flat&logo=amazonaws&logoColor=white)
![CloudFront](https://img.shields.io/badge/CDN-CloudFront-FF9900?style=flat&logo=amazonaws&logoColor=white)

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Solution](#solution)
- [Architecture Overview](#architecture-overview)
- [Why These AWS Services](#why-these-aws-services)
- [Expected Impact](#expected-impact)
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
- The Head of IT had **no visibility or control** over when software changes went live
- No audit trail of deployments — no way to answer "what changed and who approved it?"

The root cause was not a lack of engineering skill — it was a lack of **process and tooling**. The team needed infrastructure that enforced good practices automatically, without requiring them to manage servers.

---

## Solution

This project delivers two things simultaneously:

**1. A web-based appointment booking system — patients and clinic staff can book, view, and cancel appointments through a browser instead of a phone call. The application exposes API endpoints that a future developer can extend to add features like SMS reminders, billing integration, or connection to an Electronic Health Records system.

**2. A production-grade CI/CD pipeline** — every code push to GitHub automatically triggers a pipeline that runs tests, deploys to staging, then holds at a manual SNS approval gate before the Head of IT authorises a production release. No code reaches production without passing tests and receiving explicit sign-off.

---

## Architecture Overview

```
APPLICATION TRAFFIC FLOW
─────────────────────────────────────────────────────────────
User / Browser
      |  HTTPS (appointments.nbertcloudwizard.org)
   Route 53
   (A Record — Alias → CloudFront distribution)
      |
  CloudFront
  (ACM cert attached — HTTPS termination | CDN)
      |  HTTP port 80
  Elastic Beanstalk — claramedapp-env
  (Python/Flask + Gunicorn | us-east-1 | single instance)


CI/CD PIPELINE — AWS CodePipeline
─────────────────────────────────────────────────────────────
GitHub (push to main)
      |
  [Stage 1] Source
      GitHub pulls latest code
      |
  [Stage 2] Build & Test                    ← CodeBuild
      pip install -r requirements.txt
      pip install pytest
      python -m pytest test_app.py -v
      Pipeline stops here if tests fail
      |
  [Stage 3] Deploy to Staging               ← Continuous Deployment
      Beanstalk: claramed-staging-env
      Automatic — no human involved
      |
  [Stage 4] Manual Approval                 ← Continuous Delivery gate
      SNS email sent to Head of IT
      Pipeline pauses — waits for approval
      One-click approve or reject
      No AWS console access needed
      |
  [Stage 5] Deploy to Production
      Beanstalk: claramedapp-env
      Same artifact from Stage 2 — no rebuild
      Live at appointments.nbertcloudwizard.org


SUPPORTING SERVICES
─────────────────────────────────────────────────────────────
ACM        — SSL/TLS certificate (us-east-1) attached to CloudFront
SNS        — approval email notifications to Head of IT
S3         — stores pipeline artifacts between stages
IAM        — CodePipeline service role and permissions
CloudWatch — logs and monitoring (planned)
```

---

## Why These AWS Services

### AWS Elastic Beanstalk — Application Hosting

**The problem it solves:** ClaraMed's engineers are application developers, not infrastructure engineers. Provisioning EC2 instances, patching OS packages, configuring networking — none of that delivers patient value.

**Why Beanstalk specifically:**
- Handles provisioning, health monitoring, and deployment automatically
- Supports multiple named environments (`claramed-staging-env`, `claramedapp-env`) — essential for the multi-stage pipeline
- Native integration with CodePipeline — no custom deployment scripts required
- Still gives full access to underlying EC2 and VPC configuration when needed, unlike fully serverless options

**Why not ECS or Lambda:** ECS requires managing task definitions, clusters, and container networking — unnecessary overhead for a team of 4. Lambda would require significant architectural changes to the Flask app and introduces cold-start latency unacceptable for a booking UI.

---

### AWS CodePipeline — CI/CD Orchestration

**The problem it solves:** Developers were deploying manually with no consistent process. CodePipeline enforces a repeatable, auditable release workflow — every deployment follows the same stages in the same order, every time.

**Why CodePipeline specifically:**
- Native integration with GitHub, CodeBuild, Elastic Beanstalk, and SNS — no glue code or third-party plugins
- Visual pipeline view gives the Head of IT real-time visibility into release status
- Built-in manual approval actions with SNS notifications — exactly what the hierarchy-approval requirement needs
- Full execution history provides an audit trail: every deployment, who approved it, and when
- IAM-native — no third-party credentials or secrets to rotate

**Why not GitHub Actions or Jenkins:** GitHub Actions requires managing cross-service IAM integration manually. Jenkins requires provisioning and maintaining a build server — contrary to the no-infrastructure-management requirement.

---

### AWS CodeBuild — Build and Test Runner

**The problem it solves:** Before this project, code was never tested before deployment. CodeBuild runs the full pytest suite on every push — if any test fails, the pipeline stops and nothing deploys.

**Why CodeBuild specifically:**
- Fully managed — no build server to maintain or scale
- Native CodePipeline integration — zero configuration to wire the two together
- If tests fail, the pipeline stops before staging is even touched
- Execution logs available in CloudWatch for debugging failed builds

---

### AWS SNS — Hierarchy Approval Notifications

**The problem it solves:** The Head of IT needs to approve production releases but should not need to log into the AWS console.

**Why SNS specifically:**
- CodePipeline's manual approval action natively publishes to an SNS topic
- The Head of IT receives an email with a direct approve/reject link — no AWS account required
- Creates a hard architectural gate: production deployment is **impossible** without explicit approval — not just a convention or policy
- Full approval history logged in CodePipeline execution details

---

### Amazon CloudFront — HTTPS Termination and CDN

**Why used:** The Beanstalk environment runs as a single instance without a load balancer. CloudFront serves two purposes:
- **HTTPS termination** — ACM certificate attached to CloudFront provides SSL without needing a load balancer
- **CDN** — caches static assets at edge locations, reducing latency for clinic staff

CloudFront sits in front of the Beanstalk origin (HTTP port 80), terminating HTTPS at the edge — a cost-effective pattern for single-instance deployments.

---

### AWS ACM — TLS Certificate

Free, auto-renewing SSL certificate provisioned in `us-east-1` (required by CloudFront) and attached to the CloudFront distribution. Enables `https://appointments.nbertcloudwizard.org` with a valid certificate — a baseline requirement for any patient-facing application.

---

### Amazon Route 53 — DNS

Routes `appointments.nbertcloudwizard.org` to the CloudFront distribution via an **A record with Alias**. Users never interact with the raw Beanstalk or CloudFront URL.

---

### Amazon S3 — Artifact Storage

CodePipeline uses S3 natively as its artifact store between stages. The exact zip that CodeBuild produces in Stage 2 is what both Staging and Production receive — same artifact, no rebuild, guaranteed consistency.

---

### Amazon CloudWatch — Observability *(planned)*

- Application logs streamed from Elastic Beanstalk
- Alarms on HTTP 5xx error rate
- Deployment health monitoring after each pipeline execution

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
| Deployment process | Manual, ad hoc | Automated 5-stage pipeline |
| Test coverage enforced on deploy | 0% | 100% — pipeline blocked if tests fail |
| Staging environment | None | Dedicated `claramed-staging-env` |
| Mean time to recover from bad deploy | 4+ hours | < 10 min (Beanstalk rollback) |
| Unauthorised production releases | Possible | Architecturally prevented by SNS gate |
| Deployment audit trail | None | Full history in CodePipeline console |

---

## CI/CD Pipeline

This project deliberately demonstrates the distinction between **Continuous Deployment** and **Continuous Delivery** — a distinction that matters in regulated environments like healthcare.

### Stages 1–3: Continuous Integration + Continuous Deployment

Code is automatically tested and deployed to staging on every push — no human involved.

| Stage | Tool | Description |
|---|---|---|
| 1 — Source | GitHub | Push to `main` triggers the pipeline automatically |
| 2 — Build & Test | CodeBuild | Runs `pytest` — pipeline stops if any test fails |
| 3 — Deploy Staging | Elastic Beanstalk | Auto-deploys to `claramed-staging-env` |

### Stages 4–5: Continuous Delivery

Production requires human sign-off — the Head of IT controls the final gate.

| Stage | Tool | Description |
|---|---|---|
| 4 — Approval | SNS | Email sent to Head of IT — one-click approve or reject |
| 5 — Deploy Production | Elastic Beanstalk | Deploys same artifact to `claramedapp-env` only after approval |

> **Why the distinction matters:** In healthcare, deploying untested code to production without oversight is a liability. Stages 1–3 give engineers fast feedback and a validated staging environment. Stages 4–5 give the organisation control and a full audit trail. The SNS gate makes approval architecturally enforced — not just a policy.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Framework | Flask 3.0 |
| Web Server | Gunicorn |
| Hosting | AWS Elastic Beanstalk |
| CI/CD Orchestration | AWS CodePipeline |
| Build and Test | AWS CodeBuild + pytest |
| Approval Gate | AWS SNS |
| Artifact Storage | AWS S3 |
| CDN + HTTPS | AWS CloudFront + ACM |
| DNS | AWS Route 53 |
| Source Control | GitHub |
| Region | us-east-1 |

---

## Application Features

- Book patient appointments with available doctors
- View all appointments in a live table
- Cancel appointments
- REST API for future integrations (EHR, SMS reminders, billing)
- `/api/health` endpoint for Beanstalk health checks
- Environment and version banner on the UI — confirms which environment you are on during pipeline validation

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Web UI |
| GET | `/api/health` | Health check |
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
├── buildspec.yml             # CodeBuild build and test instructions
├── .ebextensions/
│   └── python.config         # WSGI entry point and environment configuration
└── tests/
    └── test_app.py           # Pytest unit tests covering all endpoints
```

---

## Running Locally

```bash
# Clone the repo
git clone https://github.com/njamutoh/From-Code-to-Production-CI-CD-Pipeline-with-AWS-Elasticbeanstalk-and-CodePipeline.git
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
pip install pytest
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
eb init claramed-appointments --region us-east-1 --platform python-3.11

# Create environments
eb create claramed-staging-env
eb create claramedapp-env

# Manual deploy (CodePipeline handles this automatically)
eb deploy claramedapp-env
```

---

## Author

**njamutoh** — [GitHub](https://github.com/njamutoh) | [LinkedIn](#)

> Region: `us-east-1` &nbsp;|&nbsp; Python 3.11 + Flask &nbsp;|&nbsp; AWS Elastic Beanstalk · CodePipeline · CloudFront · Route 53
