# Sorim.AI — Complete 7-Screen Test Execution & Evidence Log


## 📋 Detailed Verification Records by Screen

### 💻 Screen 1: Employee Self-Service Assistant (`/self-service`)
* **Test 1.1: Incident Proposal (Scenario A)**
  * **Input:** Employee `EMP-002` + *"I cannot connect to VPN since this morning. Authentication keeps failing."*
  * **AI Output:** Intent: `incident`, Category: `Network / VPN`, Priority: `P2` (high urgency / individual impact).
  * **UI Action:** Assistant renders an inline proposal card with a *"Confirm & Create Incident"* button.
* **Test 1.2: Knowledge Assistance (Scenario C)**
  * **Input:** Employee `EMP-001` + *"How do I troubleshoot Outlook synchronization?"*
  * **AI Output:** Intent: `knowledge_question`, Confidence: `89%`, 4 relevant passages retrieved from `outlook-troubleshooting.md`, grounded response with inline citation `[1]`. Escalation: `False`.

---

### 📋 Screen 2: Incident Ticket Intake & Explicit Confirmation (`/intake`)
* **Test 2.1: Explicitly Confirmed Incident Creation (Scenario A Benchmark)**
  * **Input:** Requester `EMP-002`, description *"I cannot connect to VPN since this morning. Authentication keeps failing."*, confirmation checkbox `[✔]`.
  * **Execution Result:**
    * **Ticket ID:** `TKT-000019`
    * **ServiceNow Incident:** `INC000019` (sys_id: `cab553d90e94404085f5f719d8838d43`, mode: `mock`)
    * **Category:** `Network` / `VPN`
    * **Priority:** `P2` | **Assignment Group:** `Network Support`
    * **Status:** `open`
* **Test 2.2: Mandatory Confirmation Protection Gate**
  * **Input:** Requester `EMP-002`, description provided, confirmation checkbox left `unchecked` (`confirmed: false`).
  * **Execution Result:** Backend rejects with HTTP `422 Unprocessable Entity` (*"Ticket creation must require explicit employee confirmation"*), preventing accidental ticket creation.

---

### ⚡ Screen 3: Autonomous Self-Heal Agent (`/self-heal`)
* **Test 3.1: Standard Employee Password Expiry Workflow (Scenario B)**
  * **Input:** Requester `EMP-001` (Finance user with `account_status: "password_expired"`), Action: `password_reset`, Claim: *"My password has expired."*
  * **Execution Result:**
    * **Action ID:** `ACT-000005`
    * **7 Stages Executed:** `Identify` ➔ `Diagnose` ➔ `Knowledge Search` ➔ `Determine Automation` ➔ `Execute` ➔ `Validate` ➔ `Update ServiceNow` (All completed).
    * **Postcondition Verification:** Employee `EMP-001` account status mutated in MongoDB `users` collection from `password_expired` to **`active`**.
    * **Audit Trail:** Success event written to `audit_logs` collection.
    * **Overall Status:** `SUCCEEDED` ✅
* **Test 3.2: Privileged User Safety Policy Guard**
  * **Input:** Requester `EMP-003` (IT Administrator with `privileged: true`), Action: `password_reset`.
  * **Execution Result:**
    * **Action ID:** `ACT-000007`
    * **Safety Decision:** Execution aborted at eligibility gate.
    * **Reason:** Administrative and privileged credentials cannot be reset via autonomous self-heal; human intervention required.
    * **Overall Status:** `SKIPPED_INELIGIBLE` ✅

---

### 📚 Screen 4: Knowledge Base Search & Documentation (`/knowledge`)
* **Test 4.1: Grounded Semantic RAG Pipeline (Scenario C)**
  * **Query:** *"How do I resolve Outlook email synchronization issues?"* (Mode: `answer`)
  * **Execution Result:**
    * ChromaDB vector retrieval returns 4 chunks from `outlook-troubleshooting.md` (top similarity score `0.7802`).
    * Answer synthesized with verified inline citation `[1]`.
    * Grounding score: `0.89` (High Confidence).
* **Test 4.2: Out-of-Domain Non-IT Question (Scenario E)**
  * **Query:** *"How do I brew espresso in the office kitchen cafeteria?"*
  * **Execution Result:**
    * Vector store similarity below threshold (`score < 0.20`).
    * Response: `insufficient_knowledge: true`.
    * Honest statement: *"The requested information is not available in the approved corporate knowledge base. Please create an incident ticket or contact human IT support for assistance."*
    * Zero fabricated citations or hallucinated documents.
    * Interactive UI fallback: Rendered **"Create IT Inquiry Ticket"** button routing to `/intake`.

---

### 📦 Screen 5: Software Catalogue & Automated Provisioning (`/software`)
* **Test 5.1: Developer Package Provisioning (Scenario D)**
  * **Input:** Employee `EMP-002`, Software: `Visual Studio Code` (Development, Version 1.94).
  * **Execution Result:**
    * **Request ID:** `SWR-000008`
    * **ServiceNow Mock Request:** `REQ999673` (Record type: `service_request`, Mode: `mock`)
    * **Lifecycle Progression:** `Requested` ➔ `Provisioning` ➔ `Completed`
    * **Postcondition Validation:** Mock installer verified package presence.
* **Test 5.2: Collaboration Tool Provisioning**
  * **Input:** Employee `EMP-001`, Software: `Zoom Meetings` (Version 6.2.0).
  * **Execution Result:**
    * **Request ID:** `SWR-000009`
    * **ServiceNow Mock Request:** `REQ605009`
    * **Status:** `Completed`

---

### 📊 Screen 6: ITSM Operations Dashboard (`/dashboard`)
* **Test 6.1: Live Aggregate Metrics Verification**
  * **Total Incidents:** `24`
  * **Open Incidents:** `22`
  * **Software Provisioning Requests:** `9` total (`9` completed, `0` failed)
  * **Autonomous Remediation Actions:** `7` total (`2` succeeded, `5` safely skipped)
  * **AI Telemetry Requests:** `15` total
* **Test 6.2: Public Incident Record Drill-Down (`/dashboard/tickets/TKT-000019`)**
  * **Public Ticket ID:** `TKT-000019`
  * **Linked ServiceNow Reference:** `INC000019`
  * **Requester:** Demo Employee Two (`EMP-002`, Operations)
  * **Classification:** Category `Network`, Subcategory `VPN`, Priority `P2`
  * **Audit Event Trail:** Timestamped lifecycle from intake analysis to mock dispatch.

---

### 🔬 Screen 7: AI Analysis Inspector (`/analysis`)
* **Test 7.1: Persisted AI Telemetry & Explainability Decomposition**
  * **Selected Telemetry Reference:** `AIR-000022`
  * **Model Used:** `Qwen/Qwen2.5-1.5B-Instruct`
  * **Explainability Signals:** Matched rules for `Network Support` assignment group.
  * **Heuristic Confidence Breakdown:**
    * `classification_agreement`: `1.0`
    * `confidence_level`: `high`
    * `method`: `heuristic_v1`
* **Test 7.2: Ad-Hoc Real-Time Classification Evaluation**
  * **Input:** *"My corporate Wi-Fi keeps disconnecting every 5 minutes in Conference Room 3."*
  * **Classification Result:** Category: `Network`, Subcategory: `Wi-Fi`, Assignment Group: `Network Support`, Urgency: `high`, Priority: `P2`.

---

## 🛡️ Assessment Criteria Compliance Summary

| Assessment Requirement | Verified Evidence | Status |
| :--- | :--- | :---: |
| **Scenario A (VPN Incident Intake & Confirmation)** | Verified on Screen 2 (`TKT-000019`, `INC000019`, P2 Priority, `Network/VPN`) | **PASSED ✅** |
| **Scenario B (Password Expiry Self-Heal)** | Verified on Screen 3 (`ACT-000005`, 7-stage timeline, mutated to `active`) | **PASSED ✅** |
| **Scenario B (Privileged Account Protection)** | Verified on Screen 3 (`ACT-000007`, `skipped_ineligible` for IT admin `EMP-003`) | **PASSED ✅** |
| **Scenario C (Outlook Troubleshooting RAG)** | Verified on Screen 4 & Screen 1 (ChromaDB 43 chunks, `[1]` citation, 89% conf) | **PASSED ✅** |
| **Scenario D (Software Request & Provisioning)** | Verified on Screen 5 (`SWR-000008`, `REQ999673`, VS Code status: `completed`) | **PASSED ✅** |
| **Scenario E (Unsupported Question & Zero Hallucination)**| Verified on Screen 4 (`insufficient_knowledge: true`, zero fake citations) | **PASSED ✅** |
| **Handling of Undefined Data** | Validated fallback texts, Pydantic 422 schemas, and explicit confirmation gates | **PASSED ✅** |

---
*Generated by Sorim.AI Helpdesk Automation Platform Test Harness.*
