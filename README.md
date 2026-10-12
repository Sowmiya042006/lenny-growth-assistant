# The Lenny Growth Assistant

A transcript-grounded product and growth assistant built with FastAPI,
React, PostgreSQL, Ollama, and the Claude Agent SDK.

The application retrieves relevant passages from Lenny's Podcast
transcripts, generates answers with numbered citations, preserves
independent chat sessions, and creates long-form Markdown artifacts
using the "Ship 30 for 30" essay skill.

## Features

- Transcript-grounded question answering
- Numbered source citations
- Saved and independent chat sessions
- Follow-up question support
- PostgreSQL persistence
- Ollama local-model support
- Claude Agent SDK cloud-provider integration
- Explicit provider configuration with no silent fallback
- "Ship 30 for 30" long-form essay skill
- Safe Markdown artifact viewer
- Expandable transcript evidence
- Session deletion
- Health and provider-configuration endpoints

## Technology Stack

### Backend

- Python
- FastAPI
- PostgreSQL
- Psycopg 3
- HTTPX
- Claude Agent SDK
- Ollama
- Pydantic

### Frontend

- React
- Vite
- react-markdown

### Infrastructure

- Docker Compose for PostgreSQL
- Local Ollama runtime

## Project Structure

```text
LennyGrowthAssistant/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── chat_store.py
│   ├── retrieval.py
│   ├── grounding.py
│   ├── essay_skill.py
│   ├── model_router.py
│   ├── ollama_client.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
├── data/
├── docker-compose.yml
├── .env.example
├── PRD.md
├── design.md
├── architecture.md
└── README.md

Prerequisites

Install:

Python 3.11 or newer
Node.js and npm
Docker Desktop
Ollama
Git

Install the local model:

ollama pull qwen2.5:3b

Verify Ollama:

ollama list
Invoke-RestMethod http://127.0.0.1:11434/api/tags
Environment Configuration

Copy .env.example to .env and update the values when necessary.

The application supports these providers:

LLM_PROVIDER=ollama

or:

LLM_PROVIDER=claude
ANTHROPIC_API_KEY=your_key_here
CLAUDE_MODEL=sonnet

A real .env file must never be committed.

Start PostgreSQL

From the project root:

cd E:\LennyGrowthAssistant
docker compose up -d
docker ps

PostgreSQL should be available on:

127.0.0.1:5432
Start the Backend
cd E:\LennyGrowthAssistant\backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn main:app --reload

Backend:

http://127.0.0.1:8000

API documentation:

http://127.0.0.1:8000/docs
Start the Frontend

Open a second terminal:

cd E:\LennyGrowthAssistant\frontend
npm install
npm run dev

Frontend:

http://localhost:5173
API Endpoints
Method	Endpoint	Purpose
GET	/health	Backend and provider health
GET	/config	Active provider configuration
GET	/sessions	List saved sessions
POST	/sessions	Create a chat session
GET	/sessions/{id}/messages	Load session messages
DELETE	/sessions/{id}	Delete a session
POST	/chat	Generate a grounded answer
POST	/artifacts/essay	Generate a Markdown essay artifact
Example Chat Request
{
  "message": "How can activation improve customer retention?",
  "session_id": null
}
Example Essay Request
{
  "topic": "How activation improves customer retention"
}
Grounding and Citation Policy

The retrieval layer searches indexed transcript passages and supplies
the strongest matches to the configured model.

Generated answers must contain numbered citations such as [1] and
[2]. The backend verifies that every cited number refers to a supplied
passage.

This validation confirms citation references, but it does not
automatically prove that every generated claim is fully entailed by
the cited text. The interface clearly reports this limitation.

If relevant evidence is unavailable, the assistant returns an
insufficient-evidence response instead of relying on outside knowledge.

Provider Selection and Privacy

Provider selection is controlled by LLM_PROVIDER.

ollama: prompts remain on the local machine.
claude: prompts are sent through the Claude Agent SDK.
Automatic fallback is disabled.

The application never silently sends a local prompt to a cloud model.
A provider failure is returned to the user as an explicit error.

Artifact Safety

Essay artifacts are returned as Markdown.

The frontend renders them using react-markdown. Raw generated HTML
and JavaScript are not executed, reducing script-injection risk.

Known Limitations
Citation numbers are validated, but full claim-level entailment is
not automatically verified.
Local generation speed depends on the user's CPU, memory, and model.
Long essays can take several minutes with qwen2.5:3b.
Claude requires a separately configured Anthropic API key.
Provider changes currently require updating configuration and
restarting the backend.
Resilience
Database failures return structured 503 responses.
Model failures return structured 503 responses.
Invalid sessions return 404.
Invalid request bodies return 422.
Ollama responses use streaming to support long generation.
Essay citations receive one automatic correction attempt.
Transcript Source

The retrieval corpus is based on the publicly available Lenny's
Podcast transcript repository:

https://github.com/ChatPRD/lennys-podcast-transcripts

Demo Flow
Open the application.
Confirm the active provider is Ollama.
Create a new saved chat.
Ask a product-growth question.
Inspect cited transcript passages.
Ask a referential follow-up question.
Reload the saved conversation.
Generate a "Ship 30 for 30" essay.
Inspect the Markdown artifact and its sources.
Delete a test session.
Security Notes
Secrets are loaded from environment variables.
.env is excluded from Git.
Transcript links are restricted to the expected GitHub repository.
Markdown artifacts do not execute generated scripts.
Cloud fallback is explicitly disabled.
Author

Developed as a take-home engineering project.


