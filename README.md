# 🚀 SwarmHive – Automated API Security & Broken Authorization Detection

SwarmHive is a **stateful automated API security testing platform** designed to detect **Broken Object Level Authorization (BOLA) / IDOR vulnerabilities** in modern APIs.

Traditional API scanners treat requests independently, which makes them ineffective at detecting **authorization flaws**.  
SwarmHive solves this problem by simulating **real attacker workflows**, including multi-user sessions, token reuse, and chained API interactions.

---

# 1. Project Overview

APIs are the backbone of modern applications such as:

- Financial systems
- E-commerce platforms
- Mobile applications
- Cloud services
- Enterprise software

However, **authorization vulnerabilities remain the most critical API security risk**.

The most common vulnerability is:

**Broken Object Level Authorization (BOLA)**

Example:

```
GET /api/user/1/profile
```

If a user changes it to:

```
GET /api/user/2/profile
```

and the API returns another user's data, the system is vulnerable.

SwarmHive automatically detects these types of issues.

---

# 2. Lab Overview & Architecture

<img width="872" height="564" alt="image" src="https://github.com/user-attachments/assets/173cb45d-fa08-4266-9dd6-db17007382c6" />


**Architecture Explanation:**

**1: Frontend (React) – Port 3000**

- User interface for uploading OpenAPI specifications
- Attack template selection and preview
- Results dashboard with expandable vulnerability details
- PDF report generation

**2: Backend (FastAPI) – Port 8000**

- OpenAPI parser and endpoint analyzer
- Session manager for multi-user token handling
- Attack engine executing YAML templates
- Reporting module with vulnerability evidence collection

**3: Target API (Test Environment)**

- Vulnerable API used for testing
- Contains intentionally weak authorization logic
- Allows demonstration of IDOR/BOLA exploitation

---

# 3. Key Features

### 🔎 OpenAPI-Driven Testing
Automatically parses **OpenAPI / Swagger specifications** to understand:

- API endpoints
- request parameters
- authentication methods
- request / response schemas

---

### 🔐 Stateful Attack Simulation

Maintains **session state across multiple requests**, enabling detection of vulnerabilities that traditional scanners miss.

Example attack chain:

```
Login → Create Resource → Switch User → Attempt Unauthorized Access
```

---

### 👥 Multi-User Authorization Testing

SwarmHive simulates **multiple users interacting with the API**.

Example workflow:

```
User A creates a resource
User B attempts to access or modify it
```

If access is allowed → **vulnerability detected**

---

### ⚙ YAML-Based Attack Templates

Attack logic is defined using **YAML templates**, making tests modular and extensible.

Example template snippet:

```yaml
method: GET
endpoint: /resource/{id}
user: attacker
```

This allows new attack scenarios to be added without modifying backend code.

---

### 📄 Automated Vulnerability Reporting

SwarmHive generates structured reports containing:

- endpoint tested
- request payload
- response body
- user identity used
- severity level
- reproduction steps

---

# 4. Technology Stack

**Backend**

- Python
- FastAPI
- HTTPX / Requests
- PyYAML

**Frontend**

- HTML
- CSS
- JavaScript
- React

**Other Technologies**

- OpenAPI / Swagger
- YAML attack templates

---

# 5. How SwarmHive Works

The testing workflow follows these steps:

**Step 1 – Upload OpenAPI Specification**

User uploads the API documentation file.

Supported formats:

```
openapi.yaml
openapi.json
```

---

**Step 2 – Parse API Structure**

SwarmHive extracts:

- endpoints
- HTTP methods
- parameters
- authentication schemes

---

**Step 3 – Authenticate Multiple Users**

The system logs in as different users and stores authentication tokens.

Example:

```
User A token
User B token
```

---

**Step 4 – Execute Attack Templates**

SwarmHive runs automated attack sequences such as:

```
Login → Create Resource → Access Resource With Different User
```

---

**Step 5 – Detect Authorization Flaws**

If the API allows unauthorized access, the endpoint is flagged as vulnerable.

---

**Step 6 – Generate Security Report**

The tool produces a report including:

- request details
- response details
- exploit steps
- vulnerability severity

---

# 6. System Requirements

**Minimum Requirements**

- Python 3.10+
- 4 GB RAM
- Dual-core CPU
- 10 GB Storage

**Supported Platforms**

- Linux
- Windows
- macOS
- Cloud environments

---

# 7. Project Structure

```
SwarmHive
│
├── backend
│   ├── main.py
│   ├── openapi_parser.py
│   ├── attack_engine.py
│   ├── session_manager.py
│
├── templates
│   ├── idor_read.yaml
│   ├── bola_modify.yaml
│
├── frontend
│   ├── index.html
│   ├── app.js
│
├── vulnerable_api
│
└── README.md
```

---

# 8. SwarmHive Dashboard & Usage

This section demonstrates the **core workflow of SwarmHive**, showing how a user interacts with the platform to perform automated API security testing.

---

## Figure 8.1 – SwarmHive Dashboard

<img width="872" height="564" alt="Screenshot 2026-03-10 180851" src="https://github.com/user-attachments/assets/586fb837-25ef-4f4c-965d-7d9d45a69068" />


The SwarmHive Dashboard provides the main interface for interacting with the system.

Key functionalities available on the dashboard include:

- Uploading **OpenAPI / Swagger specifications**
- Selecting predefined **attack templates**
- Initiating automated security scans
- Viewing **test results and vulnerability reports**

This interface is designed to simplify API security testing for both **security researchers and developers**.

---

## Figure 8.2 – SwarmHive Features

<img width="962" height="490" alt="image" src="https://github.com/user-attachments/assets/29993749-462e-47e6-aefb-71d8096747cb" />


This screen highlights the primary capabilities of the SwarmHive platform.

Major features include:

- **OpenAPI-driven endpoint discovery**
- **Automated BOLA / IDOR vulnerability testing**
- **Multi-user session simulation**
- **Stateful attack execution**
- **Structured vulnerability reporting**

These features enable SwarmHive to detect **authorization vulnerabilities that traditional scanners often miss**.

---

## Figure 8.3 – SwarmHive Test Result (Dry Run)

<img width="1041" height="810" alt="image" src="https://github.com/user-attachments/assets/279f9c74-becf-4856-aa11-240f3b69aca3" />


After executing an attack template, SwarmHive performs a **dry run of the security tests** against the target API.

The results panel displays:

- API endpoints tested
- Request methods used
- Authentication tokens applied
- Response status codes
- Indicators of potential vulnerabilities

This step helps analysts **verify the behavior of API endpoints before generating a final report**.

---

## Figure 8.4 – SwarmHive Test Result (Report Generation)

<img width="829" height="395" alt="image" src="https://github.com/user-attachments/assets/9e4b8916-d5ac-40fd-b2fa-084b6c068057" />

Once the test execution is completed, SwarmHive generates a **detailed vulnerability report**.

The report includes:

- Vulnerable endpoint information
- Attack request details
- Response evidence
- User session used during testing
- Recommended remediation steps

Reports can be exported as **PDF files**, making them suitable for **security documentation and vulnerability disclosure**.

---

# 9. Future Enhancements

Planned improvements include:

- GraphQL security testing
- gRPC API support
- AI-based attack path prediction
- CI/CD pipeline integration
- Advanced vulnerability dashboards
- OAuth2 and enterprise authentication support

---

# 10. Authors

**Chinmay Panda**  
**Deepthi V Naik**  
**Gehana Khameshara P**

Master of Computer Applications  
Specialization in Information Security  
Department of Computer Science and IT  
Jain (Deemed-to-be University)

---
