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
- The Medical Director had **no visibility or control** over when software changes went live
- No audit trail of deployments — no way to answer "what changed and who approved it?"

The root cause was not a lack of engineering skill — it was a lack of **process and tooling**. The team needed infrastructure that enforced good practices automatically, without requiring them to manage servers.

---

## Solution

This project delivers two things simultaneously:

**1. A web-based appointment booking system** — patients and clinic staff can book, view, and cancel appointments through a browser instead of a phone call, backed by a REST API that can integrate with future systems (EHR, SMS reminders, billing).

**2. A production-grade CI/CD pipeline** — every code push to GitHub automatically triggers a pipeline that deploys to staging first, then holds at a manual SNS approval gate before the Medical Director authorises a production release. No code reaches patients without explicit sign-off.

---

## Why These AWS Services

Each service was chosen for a specific technical and business reason.

### AWS Elastic Beanstalk — Application Hosting

**The problem it solves:** ClaraMed's engineers are application developers, not infrastructure engineers. Provisioning EC2 instances, patching OS packages, configuring networking — none of that delivers patient value.

**Why Beanstalk specifically:**
- Handles provisioning, health monitoring, and deployment automatically
- Supports multiple named environments (`claramed-staging-env`, `claramed-preprod-env`, `claramedapp-env`) — essential for the multi-stage pipeline
- Native integration with CodePipeline — no custom deployment scripts required
- Still gives full access to underlying EC2 and VPC configuration when needed, unlike fully serverless options

**Why not ECS or Lambda:** ECS requires managing task definitions, clusters, and container networking — unnecessary overhead for a team of 4. Lambda would require significant architectural changes to the Flask app and introduces cold-start latency unacceptable for a booking UI.

---

### AWS CodePipeline — CI/CD Orchestration

**The problem it solves:** Developers were deploying manually with no consistent process. CodePipeline enforces a repeatable, auditable release workflow — every deployment follows the same stages in the same order, every time.

**Why CodePipeline specifically:**
- Native integration with GitHub, Elastic Beanstalk, and SNS — no glue code or third-party plugins
- Visual pipeline view gives non-technical stakeholders (Medical Director) real-time visibility into release status
- Built-in manual approval actions with SNS notifications — exactly what the hierarchy-approval requirement needs
- Full execution history provides an audit trail: every deployment, who approved it, and when
- IAM-native — no third-party credentials or secrets to rotate

**Why not GitHub Actions or Jenkins:** GitHub Actions requires managing cross-service IAM integration manually. Jenkins requires provisioning and maintaining a build server — contrary to the no-infrastructure-management requirement.

---

### AWS SNS — Hierarchy Approval Notifications

**The problem it solves:** The Medical Director needs to approve production releases but should not need to log into the AWS console.

**Why SNS specifically:**
- CodePipeline's manual approval action natively publishes to an SNS topic
- The Medical Director receives an email with a direct approve/reject link — no AWS account required
- Creates a hard architectural gate: production deployment is **impossible** without explicit approval — not just a convention or policy

---

### Amazon S3 — Artifact Storage

**The problem it solves:** Pipeline stages need to reliably pass the same application package between them.

**Why S3:** CodePipeline uses S3 natively as its artifact store between stages. Versioned, durable, and IAM-controlled — no intermediate storage to manage.

---

### Amazon CloudFront — CDN and HTTPS Termination

**Why used:** Since the Beanstalk environment runs as a single instance without a load balancer, CloudFront serves two purposes:
- **HTTPS termination** — ACM certificate attached to the CloudFront distribution provides SSL without needing a load balancer
- **CDN** — caches static assets at edge locations, reducing latency for clinic staff across geographies

CloudFront sits in front of the Beanstalk origin (HTTP), terminating HTTPS at the edge and forwarding traffic over HTTP to the origin — a common and cost-effective pattern for single-instance deployments.

---

### AWS ACM — TLS Certificate

**Why used:** Free, auto-renewing SSL certificate provisioned in `us-east-1` (required by CloudFront) and attached to the CloudFront distribution. Enables `https://appointments.nbertcloudwizard.org` with a valid certificate — a baseline requirement for any patient-facing application.

---

### Amazon Route 53 — DNS

**Why used:** Routes `appointments.nbertcloudwizard.org` to the CloudFront distribution via a CNAME record, providing a clean custom domain instead of a raw Beanstalk or CloudFront URL.

---

### Amazon CloudWatch — Observability *(planned)*

**Planned implementation:**
- Application logs streamed from Elastic Beanstalk to CloudWatch Logs
- Alarms on HTTP 5xx error rate — threshold: >1% over 5 minutes
- Deployment health monitoring after each production pipeline execution
- 90-day log retention for compliance

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
| Deployment process | Manual, ad hoc | Automated pipeline |
| Staging environment | None | Dedicated staging env on Beanstalk |
| Mean time to recover from bad deploy | 4+ hours | < 10 min (Beanstalk rollback) |
| Unauthorised production releases | Possible | Architecturally prevented by SNS gate |
| Deployment audit trail | None | Full history in CodePipeline console |

---

## Architecture

```
User / Browser
      |
   Route 53
   (CNAME: appointments.nbertcloudwizard.org → CloudFront)
      |
  CloudFront
  (HTTPS termination — ACM cert us-east-1, origin: Beanstalk HTTP)
      |
      +─────────────────────────────────+
      |                                 |
Elastic Beanstalk                 Elastic Beanstalk
claramed-staging-env    claramed-preprod-env    claramedapp-env
(auto-deployed by pipeline)       (deployed after SNS approval)


CI/CD Pipeline (AWS CodePipeline)
──────────────────────────────────────────────────────
GitHub push to main
  → [1] Source          GitHub — pipeline triggered on push
  → [2] Deploy Staging  Beanstalk claramed-staging-env      ← Continuous Deployment
  → [3] Deploy Pre-Prod  Beanstalk claramed-preprod-env
  → [4] Approval        SNS email to Medical Director
  → [4] Production      Beanstalk claramedapp-env   ← Continuous Delivery
```

---

## CI/CD Pipeline

This project deliberately demonstrates the distinction between **Continuous Deployment** and **Continuous Delivery** — a distinction that matters in regulated environments like healthcare.

### Continuous Deployment (Stages 1–2)

Code is automatically deployed to staging on every push — no human involved.

| Stage | Tool | Description |
|---|---|---|
| 1 — Source | GitHub | Push to `main` triggers the pipeline automatically |
| 2 — Deploy Staging | Elastic Beanstalk | Auto-deploys to `claramed-staging-env` |

### Continuous Delivery (Stages 3–4)

Production requires human sign-off — the Medical Director controls the final gate.

| Stage | Tool | Description |
|---|---|---|
| 3 — Pre-Production | Elastic Beanstalk | Deploys to `claramed-preprod-env` for final validation |
| 4 — Approval | SNS | Email sent to Medical Director — one-click approve or reject |
| 5 — Production | Elastic Beanstalk | Deploys to `claramedapp-env` only after approval |

> **Why the distinction matters:** In healthcare, deploying untested code to production without oversight is a liability — technical and regulatory. The SNS gate makes approval architecturally enforced, not just a policy. Staging gives engineers fast feedback. Production requires explicit sign-off.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Framework | Flask 3.0 |
| Web Server | Gunicorn |
| Hosting | AWS Elastic Beanstalk |
| CI/CD Orchestration | AWS CodePipeline |
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
- Environment and version banner on the UI — useful for confirming which environment you are on during pipeline validation

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
├── buildspec.yml             # CodeBuild config (optional — for future test automation)
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
eb create claramed-preprod-env
eb create claramedapp-env

# Manual deploy (CodePipeline handles this automatically)
eb deploy claramedapp-env
```

---

## Author

**njamutoh** — [GitHub](https://github.com/njamutoh) | [LinkedIn](#)

> Region: `us-east-1` &nbsp;|&nbsp; Python 3.11 + Flask &nbsp;|&nbsp; AWS Elastic Beanstalk · CodePipeline · CloudFront · Route 53
