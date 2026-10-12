# Design Document

## Product Goal

The Lenny Growth Assistant helps users answer product and growth
questions using evidence from Lenny's Podcast transcripts.

The product prioritizes:

1. Grounded responses
2. Inspectable evidence
3. Independent saved conversations
4. Local-model privacy
5. Clear provider behavior
6. Safe artifact rendering

## Main User Flows

### Grounded Chat

1. The user creates or selects a chat session.
2. The user submits a product or growth question.
3. The backend retrieves relevant transcript passages.
4. The configured model generates a cited answer.
5. The backend validates citation numbers.
6. The question, answer, sources, and status are stored.
7. The frontend displays the answer and expandable sources.

### Follow-up Question

Short referential questions such as "Explain the second point" reuse
the previous answer's evidence. If saved evidence is unavailable, the
previous user question is added to the retrieval query.

### Essay Artifact

1. The user enters an essay topic.
2. The backend retrieves the four strongest passages.
3. The "Ship 30 for 30" skill requests a long-form Markdown essay.
4. The backend validates citations.
5. One correction attempt is made if citations are invalid.
6. The frontend safely renders the Markdown artifact and its sources.

## Interface Design

The application uses a two-column layout.

### Sidebar

- New Chat button
- Saved session list
- Selected-session highlight
- Delete Selected Chat button

### Main Area

- Application title and description
- Active provider and model
- Essay-generation form
- Markdown artifact viewer
- Conversation history
- Question input
- Loading and error messages

## Grounding Design

Retrieval results contain:

- Transcript ID
- Chunk ID
- GitHub source URL
- Transcript excerpt

Evidence is numbered before being included in the model prompt. The
model is instructed to cite only these numbers.

The backend verifies that:

- At least one citation exists.
- Every citation number refers to a supplied passage.

A valid number does not guarantee complete factual entailment.
Therefore, the response status is reported as:

```text
citations_valid_support_unverified

This limitation is also displayed in the frontend.

Session Design

PostgreSQL stores chat sessions and messages.

Each message is associated with exactly one session. Loading a session
returns only that session's messages, preventing conversation leakage
between independent chats.

When the first question is saved, the default "New chat" title is
replaced with a shortened version of that question.

Provider Design

The model router supports:

Ollama for local inference
Claude through the Claude Agent SDK

Provider selection uses the LLM_PROVIDER environment variable.

Automatic fallback is disabled. This avoids silently transferring a
prompt from a local provider to a cloud provider.

Artifact Safety

Artifacts are generated as Markdown instead of executable HTML.

The React frontend uses react-markdown without raw-HTML plugins.
Generated scripts and raw HTML are not executed.

External transcript links are accepted only when they:

Use HTTPS
Point to github.com
Match the expected transcript repository path
Error Handling

Structured API errors are used for:

Database unavailable
Model unavailable
Session not found
No transcript evidence
Citation validation failure
Request validation failure

The frontend displays human-readable messages and prevents duplicate
requests while generation is active.

Important Trade-offs
Citation Validation

The current implementation validates citation references but does not
perform semantic claim-level verification. This was chosen to keep the
local workflow lightweight.

Local Generation Speed

Ollama improves privacy but long-form generation may be slow on
CPU-only machines. Streaming is used so long generation does not fail
because of a fixed total timeout.

Provider Switching

Provider switching is configuration-based and requires a backend
restart. This keeps credential handling on the server and prevents API
keys from entering the browser.

Essay Evidence Limit

Essay generation uses the four strongest passages to reduce prompt
size and local-model processing time.

Future Improvements
Claim-level entailment checking
Streaming tokens to the browser
Stored essay artifacts
Provider switching through an authenticated admin interface
Hybrid lexical and embedding retrieval
Retrieval-quality evaluation
Background essay jobs with progress updates