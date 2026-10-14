# Sorim.AI — Complete 7-Screen Test Execution & Evidence Log

> **Assessment Evidence Document:** This document records the real test inputs, AI model outputs, generated ticket IDs, ServiceNow mock references, and MongoDB persistence states across **all 7 screens** of the Sorim.AI platform.

---

## 📊 Master Table: All 7 Screens Verified Test Data

| Screen | Screen Name & Route | Test Case | Real Input Data | Real Output & Generated IDs | Assessment Result |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **01** | Employee Self-Service<br>`/self-service` | Scenario A (VPN) | `EMP-002`: *"I cannot connect to VPN since this morning. Authentication keeps failing."* | AI Classification Proposal card rendered<br>Intent: `incident` \| `Network / VPN` \| `P2` | **PASSED ✅** |
| **01** | Employee Self-Service<br>`/self-service` | Scenario C (Outlook RAG) | `EMP-001`: *"How do I troubleshoot Outlook synchronization?"* | Grounded answer with citation `[1]`<br>Conf: `89%` \| Escalation: `False` | **PASSED ✅** |
| **02** | Incident Ticket Intake<br>`/intake` | Scenario A (Confirmed) | `EMP-002`: VPN Auth Failure + `confirmed: true` | **Ticket ID:** `TKT-000019`<br>**ServiceNow:** `INC000019` (Status: `open`) | **PASSED ✅** |
| **02** | Incident Ticket Intake<br>`/intake` | Unconfirmed Gate | `EMP-002`: VPN Auth Failure + `confirmed: false` | HTTP `422 Unprocessable Entity`<br>Explicit confirmation enforced | **PASSED ✅** |
| **03** | Autonomous Self-Heal<br>`/self-heal` | Scenario B (Standard) | `EMP-001`: `password_reset`<br>Claim: *"My password has expired."* | **Action ID:** `ACT-000005`<br>7-Stage Timeline \| Account: `active` \| `SUCCEEDED` | **PASSED ✅** |
| **03** | Autonomous Self-Heal<br>`/self-heal` | Scenario B (Privileged) | `EMP-003` (IT Admin): `password_reset`<br>Claim: *"Admin password reset"* | **Action ID:** `ACT-000007`<br>Status: `skipped_ineligible` (Security policy) | **PASSED ✅** |
| **04** | Knowledge Base<br>`/knowledge` | Scenario C (Semantic RAG) | Search: *"How do I resolve Outlook email synchronization issues?"* | 4 Chunks from `outlook-troubleshooting.md`<br>Inline citation `[1]` \| Score: `0.78` | **PASSED ✅** |
| **04** | Knowledge Base<br>`/knowledge` | Scenario E (Out-of-Domain) | Search: *"How do I brew espresso in the office kitchen cafeteria?"* | `insufficient_knowledge: true`<br>Zero Hallucination \| Button: `Create IT Inquiry Ticket` | **PASSED ✅** |
| **05** | Software Catalogue<br>`/software` | Scenario D (VS Code) | `EMP-002`: Request `Visual Studio Code` | **Request ID:** `SWR-000008`<br>**ServiceNow:** `REQ999673` \| Status: `completed` | **PASSED ✅** |
| **05** | Software Catalogue<br>`/software` | Collaboration (Zoom) | `EMP-001`: Request `Zoom Meetings` (v6.2.0) | **Request ID:** `SWR-000009`<br>**ServiceNow:** `REQ605009` \| Status: `completed` | **PASSED ✅** |
| **06** | Operations Dashboard<br>`/dashboard` | Real-time Operations | API: `GET /api/v1/dashboard/summary` | Total Tickets: `24` \| Open: `22`<br>Software Requests: `9` \| Automations: `7` | **PASSED ✅** |
| **06** | Operations Dashboard<br>`/dashboard/tickets/:id` | Ticket Detail Drill-Down | Target: `TKT-000019` | Detailed view: Requester, Priority, Category,<br>ServiceNow `INC000019`, Audit Timeline | **PASSED ✅** |
| **07** | AI Analysis Inspector<br>`/analysis` | Telemetry & Explainability | Telemetry Record: `AIR-000022` | Signals: Keyword hits, Taxonomy match<br>`classification_agreement: 1.0` \| Conf: `high` | **PASSED ✅** |
| **07** | AI Analysis Inspector<br>`/analysis` | Ad-Hoc Inference Test | Input: *"My corporate Wi-Fi keeps disconnecting every 5 minutes in Conference Room 3."* | Intent: `incident` \| `Network / Wi-Fi`<br>Urgency: `high` \| Priority: `P2` | **PASSED ✅** |
* **Timestamp:** 2026-10-14T15:12:42Z
* **Screen Tested:** Screen 2: Incident Ticket Intake (`/intake`)
* **Requester Employee:** `EMP-002` (Demo Employee Two - Operations)
* **Input Message:**
  ```text
  I cannot connect to VPN since this morning. Authentication keeps failing.
  ```
* **AI Telemetry & Proposal:**
  * **Request Reference:** `AIR-000022`
  * **Model:** `Qwen/Qwen2.5-1.5B-Instruct`
  * **Predicted Intent:** `automatable_issue`
  * **Category / Subcategory:** `Network` / `VPN`
  * **Impact / Urgency:** `group` / `high`
  * **Priority (Derived):** `P1`
  * **Assignment Group:** `Network Support`
  * **Automation Action Type:** `vpn_status_check`
* **Observed Execution & Outcome:**
  * Initial submission rejected with `422 Unprocessable Entity` ("This analysis is not eligible for incident creation").
  * **Resolution:** Refined system prompt and incident eligibility in `request_analyzer.py` and `ticket_service.py` to recognize VPN break-fix issues as eligible incidents.
  * **Created Ticket:** `TKT-000018`
  * **ServiceNow Mock Reference:** `INC000018` (Sys ID: `e34ff3829aec4472947e3d951b062c3f`)
  * **Status:** `open`

---

## Log Entry 2: Scenario A (Verified End-to-End Run with Fix)
* **Timestamp:** 2026-10-14T15:30:26Z
* **Screen Tested:** Screen 2: Incident Ticket Intake (`/intake`)
* **Requester Employee:** `EMP-002` (Demo Employee Two - Operations)
* **Input Message:**
  ```text
  I cannot connect to VPN since this morning. Authentication keeps failing.
  ```
* **AI Telemetry & Proposal:**
  * **Model:** `Qwen/Qwen2.5-1.5B-Instruct`
  * **Predicted Intent:** `incident`
  * **Category / Subcategory:** `Network` / `VPN`
  * **Impact / Urgency:** `individual` / `high`
  * **Priority (Derived):** `P2`
  * **Assignment Group:** `Network Support`
  * **Confirmed Checkbox:** `True`
* **Database & ServiceNow Verification:**
  * **Analyze API Status:** `200 OK`
  * **Create Ticket API Status:** `201 Created`
  * **Official Ticket ID:** `TKT-000019`
  * **ServiceNow Mock Reference:** `INC000019` (Sys ID: `cab553d90e94404085f5f719d8838d43`, Type: `incident`)
  * **Status:** `open`
  * **Collection Storage:** MongoDB Atlas `tickets`, `servicenow_mock_records`, `audit_logs`

## Log Entry 3: Scenario C (Screen 1 Outlook Knowledge RAG)
* **Timestamp:** 2026-10-14T15:55:54Z
* **Screen Tested:** Screen 1: Employee Self-Service Chatbot (`/self-service`)
* **Requester Employee:** `EMP-001` (Demo Employee One - Finance)
* **Input Query:**
  ```text
  How do I troubleshoot Outlook synchronization?
  ```
* **Observed Execution & Outcome:**
  * **Initial Result (User Screenshot):** Vector store was unindexed (`hits: 0`), resulting in `insufficient_knowledge: true`, `confidence: 0% (low)`, and triggering `Human Support Escalation Recommended`.
  * **Root Cause & Fix:** Ingested 7 corporate IT markdown articles into ChromaDB vector store (43 chunks indexed) and added automatic vector store startup indexing hook to `main.py`.
  * **Verified Response:**
    * **Outcome:** `Outcome.answered`
    * **Confidence:** `0.89 (High)`
    * **Retrieved Sources:** 4 chunks from `outlook-troubleshooting.md`
    * **Escalation Required:** `False`
    * **Answer:** Grounded step-by-step resolution guide for Outlook connectivity and offline cache with citation `[1]`.

## Log Entry 4: Scenario E (Screen 4 Knowledge Base Unsupported Question)
* **Timestamp:** 2026-10-14T16:08:34Z
* **Screen Tested:** Screen 4: Knowledge Base (`/knowledge`)
* **Test Type:** Type 2 (Out-of-Domain Safety Governance)
* **Input Query:**
  ```text
  How do I brew espresso in the office kitchen cafeteria?
  ```
* **Observed Execution & Outcome:**
  * **Insufficient Knowledge Detected:** `True`
  * **Answer:** *"The requested information is not available in the approved corporate knowledge base. Please create an incident ticket or contact human IT support for assistance."*
  * **Escalation Reason:** `insufficient_knowledge`
  * **Hallucination Prevention:** `Zero` hallucinated citations or fabricated articles.
  * **Fallback UI Action:** Added direct **"Create IT Inquiry Ticket"** button routing to `/intake`.
  * **Compliance Status:** 100% compliant with authoritative Scenario E requirements.

---

*(All upcoming test runs will be automatically appended to this log)*