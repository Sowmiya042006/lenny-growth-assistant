# Agent-Assisted Development Log

## Project

The Lenny Growth Assistant

## Development Approach

This project was developed with AI-assisted iteration. The developer
reviewed, copied, executed, tested, and corrected each proposed change
inside the local development environment.

## Major Implementation Steps

1. Created a FastAPI backend and React frontend.
2. Loaded and indexed Lenny's Podcast transcript passages.
3. Implemented transcript retrieval and grounded prompt construction.
4. Added Ollama local-model integration.
5. Added citation parsing for `[1]`, `[2]`, and `[1, 2]`.
6. Added PostgreSQL-backed sessions and messages.
7. Added independent session loading and deletion.
8. Added referential follow-up handling.
9. Added a saved-chat React interface.
10. Added source expansion and safe transcript links.
11. Installed and integrated the Claude Agent SDK.
12. Added configuration-based Ollama/Claude provider routing.
13. Disabled automatic provider fallback for privacy.
14. Added the "Ship 30 for 30" essay skill.
15. Added citation checking and one essay-correction attempt.
16. Changed Ollama to streamed response reading for long generation.
17. Added a safe Markdown artifact viewer with `react-markdown`.
18. Added README, design, architecture, environment, and security
    documentation.
19. Verified the frontend production build.
20. Verified Python source compilation.

## Important Problems and Resolutions

### PostgreSQL Was Unavailable

The backend returned `DATABASE_UNAVAILABLE`, and port 5432 was closed.

Resolution:

- Verified Docker installation.
- Started the PostgreSQL Docker Compose service.
- Confirmed the container was healthy and port 5432 was mapped.

### Invalid Citation Parsing

The original citation parser recognized `[1]` but did not correctly
handle grouped citations such as `[1, 2]`.

Resolution:

- Parsed citation groups first.
- Extracted all digits from each group.
- Checked the resulting numbers against the supplied passage range.

### Follow-up Retrieval Contamination

Every short question originally included the previous question, which
could mix unrelated topics.

Resolution:

- Added referential follow-up detection.
- Reused prior sources only for messages such as "explain that" or
  "explain the second point."

### Duplicate Sessions

Multiple sessions had similar automatically generated titles.

Resolution:

- Added a session deletion endpoint.
- Added a Delete Selected Chat button in the frontend.

### Essay Generation Timeout

Long essay responses exceeded the original non-streaming HTTP timeout.

Resolution:

- Enabled streaming in the Ollama client.
- Collected response chunks until generation completed.
- Limited essay retrieval to the four strongest passages.

### Unsafe Artifact Rendering Risk

Generated HTML could execute scripts if inserted directly into the DOM.

Resolution:

- Generated Markdown artifacts.
- Rendered them using `react-markdown`.
- Did not enable raw-HTML execution.

## Validation Performed

- PostgreSQL container health check
- Backend `/health` request
- Backend `/config` request
- Grounded `/chat` request
- Saved-session loading
- Session deletion
- Follow-up question test
- Ollama provider response test
- Essay artifact generation
- Citation failure and retry behavior
- React production build
- Python compilation check

## Human Review

AI-generated code and documentation were manually reviewed and tested
by the developer. Errors were diagnosed using PowerShell output,
FastAPI tracebacks, browser behavior, and API responses.