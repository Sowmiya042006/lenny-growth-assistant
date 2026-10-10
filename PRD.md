# Product Requirements Document
## The Lenny Growth Assistant

Status: Initial plan. Features below are requirements, not completed work.

## 1. User and Problem

Primary users are product managers and growth professionals.

They need practical advice from Lenny's Podcast, but searching and
reading long transcripts takes time. They also need to turn useful
advice into reusable essays, checklists, and documents.

The assistant will help users find source-backed answers and create
content without needing to write complex prompts.

## 2. Success Metrics

Targets to evaluate before submission:

- At least 8 of 10 prepared, answerable questions receive answers
  supported by the cited transcript passages, checked manually.
- All 5 prepared unsupported questions receive a clear explanation
  that the available transcripts do not support an answer.
- Two separate chat sessions retain their own history after an
  application restart, without mixing messages.
- A fresh setup succeeds using the documented startup instructions.

We will record actual results rather than assume these targets are met.

## 3. Assumptions

- The first version is a local, single-user evaluation application.
- Internet access is available for initial setup and transcript downloads.
- Ollama will provide the local model used in the demo.
- A cloud provider requires the evaluator's own API key.
- Model quality and speed depend on the laptop and selected model.
- We will check the transcript repository's usage terms before deciding
  whether to redistribute data or download it during setup.

## 4. Included Scope

- React chat interface and FastAPI backend.
- PostgreSQL storage for sessions, messages, timestamps, and minimal
  user metadata.
- Integration with one required agent framework:
  Claude Agent SDK or Pi Coding Agent.
- Transcript ingestion, indexing, source tracking, and refresh command.
- Retrieval-based answers with sources and follow-up support.
- Independent chat sessions and a New Chat action.
- A reusable Ship 30 for 30 writing skill targeting 1,250 words.
- Markdown and HTML/CSS artifacts displayed beside the chat.
- Configurable local and cloud models, with the active model visible.
- Validation, structured errors, health checks, and diagnostic logs.
- Reproducible startup, automated tests, and operational documentation.

## 5. Excluded Scope

- Production login, team permissions, and billing.
- General web search and answers based on unrelated sources.
- Model training or fine-tuning.
- JavaScript execution inside generated artifacts.

These exclusions keep the first version achievable within the deadline.
The application will be documented as a local demo, not a secure
multi-user production service.

## 6. Main User Flow

1. Open the application and see the active model.
2. Start a chat and ask a product or growth question.
3. Receive an answer with relevant transcript sources.
4. Ask a follow-up question using the same session.
5. Request an essay or artifact based on the discussion.
6. View the formatted artifact beside the conversation.
7. Return to a saved conversation later.

## 7. Acceptance Criteria

- Answers use retrieved transcript evidence.
- Citations identify real sources and can be inspected.
- Insufficient evidence produces an honest limitation message.
- Follow-ups use the current session's context.
- New chats do not inherit another session's context.
- Conversations survive application restarts.
- Essays target 1,125–1,375 words and include a hook, headings,
  selective emphasis, a useful takeaway, and grounded claims.
- Generated HTML is isolated in a sandboxed viewer, with scripts
  and external network requests blocked.
- Markdown rendering does not execute embedded HTML.
- Missing keys, unavailable Ollama, timeouts, empty retrieval,
  and database failures produce understandable errors.
- Local failures never silently send conversation data to a
  cloud provider.

## 8. Risks and Trade-offs

- Hallucination: use evidence, citations, and unsupported-answer tests.
  Citations alone do not guarantee correctness.
- Local model quality: test a small model on representative tasks.
- Latency: limit retrieved context and measure response times.
- Cloud cost and privacy: require explicit provider selection.
- Unsafe artifacts: isolate previews and restrict allowed content.
- Data leakage: separate sessions and avoid logging secrets or
  complete conversations by default.
- Limited time: prioritize working required flows before visual polish.

## 9. Implementation Plan

1. Confirm model and agent-framework compatibility.
2. Build a basic frontend-to-backend connection.
3. Add PostgreSQL persistence and session handling.
4. Load transcripts and implement retrieval with source tracking.
5. Connect the agent layer and local/cloud model configuration.
6. Add the essay skill and artifact viewer.
7. Test critical behavior and failure cases.
8. Complete documentation and verify a fresh installation.
9. Record the demo and prepare the submission.