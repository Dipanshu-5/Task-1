# AI-First CRM HCP Module – Log Interaction Screen

This repository contains a complete, submission-ready implementation of an AI-First Customer Relationship Management (CRM) healthcare professional (HCP) interaction logger. The application consists of a responsive React + Redux frontend, a Python FastAPI backend, and an AI Agent workflow powered by **LangGraph** and **Groq (gemma2-9b-it)**.

---

## 1. Project Overview & Problem Statement

In life-sciences and pharmaceutical field operations, representatives spend significant time logging doctor interactions manually into complex CRM forms. This manual entry often leads to missing details, low summary quality, and promotional compliance risks.

**The Solution:** An AI-First CRM screen that bridges manually structured entries and conversational AI:
1. **Left - Structured Interaction Form:** Allows manual input with validation, pickers, and counters.
2. **Right - AI Assistant Panel:** Allows representatives to describe meetings in natural language.
3. **Synchronization:** Conversational inputs are extracted by the AI, verified for regulatory compliance, previewed in the UI, and synchronized to the Redux form state upon human confirmation.

---

## 2. Architecture & Data Flow

```
React UI (Left Form & Right Chat)
   ⇅ [Redux Toolkit State]
Vite Axios Clients
   ⇅ [FastAPI JSON Endpoints]
FastAPI Router
   ⇅ [LangGraph Workflow Agent] ⇄ [Groq API: gemma2-9b-it]
SQLAlchemy ORM
   ⇅
PostgreSQL / SQLite Database
```

---

## 3. Database Schema

The database is built on SQLAlchemy and is compatible with PostgreSQL, MySQL, and SQLite.

### HCP (Healthcare Professional)
* `id` (Integer, Primary Key) - Auto-incrementing identifier
* `full_name` (String) - Dr's full name (seeded for match lookups)
* `specialty` (String) - Specialty field (e.g. Cardiology, Oncology)
* `organization` (String) - Associated clinic or hospital name
* `email` (String, Optional) - Dr's email reference
* `created_at` / `updated_at` (DateTime) - Audit timestamps

### Interaction
* `id` (Integer, Primary Key) - Log identifier
* `hcp_id` (Integer, Foreign Key) - Associated HCP
* `interaction_type` (String) - In-Person, Virtual, Email, or Phone
* `interaction_date` / `interaction_time` - Meeting details
* `attendees` (Text) - JSON-serialized list of attendees
* `topics_discussed` (Text) - JSON-serialized list of topics
* `materials_shared` (Text) - JSON-serialized list of shared documents
* `samples_distributed` (Text) - JSON-serialized product sample logs
* `sentiment` (String) - Positive, Neutral, or Negative sentiment
* `outcomes` (Text) - Free text outcome notes
* `follow_up_actions` (Text) - Task descriptions
* `follow_up_date` (Date) - Action deadline date
* `original_notes` (Text) - Raw chat or dictation text
* `ai_summary` (Text) - Brief AI-generated compliant summary
* `created_by` / `status` (String) - Submitted/Draft status
* `created_at` / `updated_at` (DateTime) - Timestamps

### InteractionAudit
* `id` (Integer, Primary Key) - Audit record ID
* `interaction_id` (Integer, Foreign Key) - Link to target interaction
* `action` (String) - Action performed (e.g. "CREATE", "UPDATE")
* `changed_fields` (Text) - JSON-serialized list of modified columns
* `previous_values` (Text) - JSON-serialized map of old values
* `new_values` (Text) - JSON-serialized map of new values
* `timestamp` (DateTime) - Audit log timestamp

---

## 4. LangGraph Workflow & Tool Definitions

The AI Assistant routes all chat inputs through a state-driven LangGraph workflow:

```
[Start] ➔ Intent Detection ➔ Extract & Compliance ➔ Validation & Missing Fields Check
                                                       │
                                      (Conditional Edge: Route Action)
                                                       ├➔ [Wait for Human Confirmation]
                                                       ├➔ [Execute Agent Tools]
                                                       └➔ [Generate Response & End]
```

### Core Nodes:
1. **Intent Detection:** Parses message to detect intents (`log_interaction`, `edit_interaction`, `retrieve_history`, `suggest_follow_up`, `confirm`, `cancel`).
2. **Extraction:** Parses entities (materials, samples, outcomes) from notes.
3. **Validation & Missing-Field Detection:** Verifies dates, flags missing mandatory fields (HCP, Topic, Type), and marks state for confirmation.
4. **Tool Execution:** Invokes database transaction tools.
5. **Response Generation:** Formulates natural-language responses and instructions.

### Implemented Tools (app/tools/crm_tools.py):
1. **Log Interaction Tool:** Persists confirmed details in database with summary, preventing duplication on the same day.
2. **Edit Interaction Tool:** Patches existing logs with partial updates and writes column diffs to audit database.
3. **Retrieve Interaction History Tool:** Queries SQLite/PostgreSQL to return a timeline of past meetings for the selected HCP.
4. **Generate Follow-Up Suggestions Tool:** Analyzes notes to output compliant next-action recommendations and follow-up timeline targets.
5. **Summarize and Extract Interaction Tool:** Calls Groq LLM to convert raw text notes into structured JSON schema and scan for promotional compliance issues.

---

## 5. Setup & Running Instructions

### Prerequisites
* Python 3.11+
* Node.js 18+
* Groq API Key (If calling live Groq. If not configured, the app automatically runs in a Mocked-LLM environment for test suites and offline demos.)

---

### Local Setup (No Docker)

#### 1. Backend Setup
1. Open a terminal in `./backend`.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate # macOS/Linux
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy environment files and configure variables:
   ```bash
   copy .env.example .env
   ```
   *Edit `.env` and paste your `GROQ_API_KEY` (optional).*
5. Run the initialization and seeding script:
   ```bash
   python app/database/init_db.py
   ```
6. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

#### 2. Frontend Setup
1. Open a terminal in `./frontend`.
2. Install packages:
   ```bash
   npm install
   ```
3. Copy environment template:
   ```bash
   copy .env.example .env
   ```
4. Start the Vite React development server:
   ```bash
   npm run dev
   ```
5. Open your browser to `http://localhost:5173`.

---

### Setup with Docker Compose
If Docker is installed:
1. From the project root, run:
   ```bash
   docker-compose up --build
   ```
2. The services will spin up:
   * **Frontend UI:** `http://localhost:5173`
   * **FastAPI Backend:** `http://localhost:8000`
   * **PostgreSQL DB:** `http://localhost:5432`

---

## 6. How to Run Unit Tests

All backend and frontend tests run fully mocked, requiring no external API keys or live database configurations.

### Backend Tests (pytest)
From `./backend`:
```bash
.\venv\Scripts\pytest
```

### Frontend Tests (vitest)
From `./frontend`:
```bash
npm run test
```

---

## 7. 10–15 Minute Video Demonstration Script

This plan is optimized to showcase all 5 tools and requirements within a 12-minute window:

### [0:00 - 1:30] Introduction & Architecture
* **Visual:** Browser showing `http://localhost:5173` with split layout.
* **Talk:** Explain the objective: AI-First CRM screen for logging HCP interactions. Walk through the split screen structure: left manual entry, right chat assistant panel.
* **Database Check:** Briefly show pgAdmin or the CLI demonstrating the seeded fictional HCPs (Dr. Priya Sharma, Dr. Alan Grant).

### [1:30 - 3:30] Structured Form Workflow
* **Action:** Select "Dr. Alan Grant", set type to "Virtual", select topic "Clinical Trial Data", set sentiment to "Neutral". Press "Save Log".
* **Visual:** Form resets, toast notification slides in showing success.
* **Timeline Update:** Look at the "HCP Timeline History" card at the bottom right. Dr. Alan Grant's timeline updates instantly with the new log item.

### [3:30 - 6:00] Conversational AI Log (Tool 1, 5)
* **Action:** In the Chat input, paste:
  `"Met Dr Priya Sharma today at Cardiology clinic. We discussed Product X efficacy. She showed positive sentiment, asked for a brochure, and requested a follow-up in two weeks."`
  Press Send.
* **AI Tool Invoked:**
  1. *Tool 5 (Extraction)* runs on the text.
  2. *Validation* checks that `HCP (Priya Sharma)`, `Type (In-Person)`, and `Topic (Product Efficacy)` are extracted.
  3. *State Transition:* It pauses, prompting the user for approval.
* **Visual:** Renders the "AI Extracted Details" Card. Shows "Dr. Priya Sharma" matched to DB ID 1, sentiment "Positive", topics, and Outcomes.
* **Action:** Click "Confirm & Save".
* **Redux Sync & Save (Tool 1):** The Redux form LEFT column updates with these values, and the record persists to the database.

### [6:00 - 7:30] conversational AI Edit (Tool 2)
* **Action:** In Chat input, type:
  `"Update the last interaction, change sentiment to Neutral and add Prescribing guidelines brochure to materials."`
  Press Send.
* **Visual:** The preview card renders with changed values highlighted. Click "Confirm & Save".
* **Verification:** Show that the database records have updated.

### [7:30 - 9:00] Retrieve History (Tool 3)
* **Action:** In Chat input, type:
  `"Retrieve recent history timeline for Priya Sharma"`
  Press Send.
* **Visual:** Assistant displays a formatted bulleted list of past interactions with dates, sentiments, and topics.

### [9:00 - 10:30] Follow-Up Suggestions (Tool 4)
* **Action:** In Chat input, type:
  `"Suggest follow-up tasks for Priya Sharma based on outcomes"`
  Press Send.
* **Visual:** Assistant responds with a bulleted list of compliant, AI-generated actions (e.g. scheduling virtual access discussion) and suggested dates.

### [10:30 - 12:00] Code Walkthrough, Testing & Wrap-up
* **Code Walkthrough:** Show `app/agents/graph.py` (nodes, routing), `app/tools/crm_tools.py` (database writes, auditing), and frontend slices (`interactionSlice.js` sync).
* **Test Verification:** Run `pytest` and `npm run test` in terminal. Wrap up.

---

## 8. AI Safety & Domain Compliance Rules

1. **Rep Ownership of DB Writes:** The AI Assistant will **never** perform direct database creation or edits without explicit human approval. All writes halt at the confirmation node waiting for a `Confirm & Save` click.
2. **Promotional Safeguards:** The parser returns warnings if unsupported promotional claims (e.g. "cures", "100% safe") are typed in the dictation notes.
3. **No Clinical Advice:** The assistant is restricted to operational CRM logging and does not generate medical diagnoses or treatment guidelines.
4. **Audit Trail Logging:** All updates trigger detailed diff logs storing previous and modified JSON values in `InteractionAudit`.

---

## 9. Requirement-to-File Mapping

| Requirement | File Location |
| :--- | :--- |
| **FastAPI Core Application** | [main.py](file:///C:/Users/ALOK/.gemini/antigravity/scratch/hcp-crm-assignment/backend/app/main.py) |
| **FastAPI Route Endpoints** | [endpoints.py](file:///C:/Users/ALOK/.gemini/antigravity/scratch/hcp-crm-assignment/backend/app/api/endpoints.py) |
| **SQLAlchemy Table Models** | [crm.py (Models)](file:///C:/Users/ALOK/.gemini/antigravity/scratch/hcp-crm-assignment/backend/app/models/crm.py) |
| **Pydantic Schemas** | [crm.py (Schemas)](file:///C:/Users/ALOK/.gemini/antigravity/scratch/hcp-crm-assignment/backend/app/schemas/crm.py) |
| **CRUD DB Services** | [crm.py (Services)](file:///C:/Users/ALOK/.gemini/antigravity/scratch/hcp-crm-assignment/backend/app/services/crm.py) |
| **LangGraph Workflow Graph** | [graph.py](file:///C:/Users/ALOK/.gemini/antigravity/scratch/hcp-crm-assignment/backend/app/agents/graph.py) |
| **Agent State TypedDict** | [state.py](file:///C:/Users/ALOK/.gemini/antigravity/scratch/hcp-crm-assignment/backend/app/agents/state.py) |
| **Compulsory & Optional Tools** | [crm_tools.py](file:///C:/Users/ALOK/.gemini/antigravity/scratch/hcp-crm-assignment/backend/app/tools/crm_tools.py) |
| **Vite Frontend Entrypoint** | [App.jsx](file:///C:/Users/ALOK/.gemini/antigravity/scratch/hcp-crm-assignment/frontend/src/App.jsx) |
| **Structured Form View** | [LogInteractionPage.jsx](file:///C:/Users/ALOK/.gemini/antigravity/scratch/hcp-crm-assignment/frontend/src/pages/LogInteractionPage.jsx) |
| **Redux Form Slice** | [interactionSlice.js](file:///C:/Users/ALOK/.gemini/antigravity/scratch/hcp-crm-assignment/frontend/src/features/interactionSlice.js) |
| **Redux Agent Slice** | [agentSlice.js](file:///C:/Users/ALOK/.gemini/antigravity/scratch/hcp-crm-assignment/frontend/src/features/agentSlice.js) |
| **CRM Color & Styling System** | [index.css](file:///C:/Users/ALOK/.gemini/antigravity/scratch/hcp-crm-assignment/frontend/src/styles/index.css) |
| **Backend Test Suite** | [test_api.py](file:///C:/Users/ALOK/.gemini/antigravity/scratch/hcp-crm-assignment/backend/tests/test_api.py), [test_agent.py](file:///C:/Users/ALOK/.gemini/antigravity/scratch/hcp-crm-assignment/backend/tests/test_agent.py) |
| **Frontend Test Suite** | [slices.test.js](file:///C:/Users/ALOK/.gemini/antigravity/scratch/hcp-crm-assignment/frontend/src/features/slices.test.js) |
| **Docker Compose** | [docker-compose.yml](file:///C:/Users/ALOK/.gemini/antigravity/scratch/hcp-crm-assignment/docker-compose.yml) |
