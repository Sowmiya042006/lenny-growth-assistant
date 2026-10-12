import asyncio
import re
from contextlib import asynccontextmanager
from uuid import UUID

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from chat_store import (
    create_session,
    delete_session,
    get_messages,
    get_session,
    list_sessions,
    save_exchange,
)
from grounding import (
    INSUFFICIENT_EVIDENCE,
    build_grounded_prompt,
)
from model_router import (
    ask_configured_model,
    provider_status,
)
from retrieval import TranscriptSearch
from essay_skill import build_essay_prompt

# Load the transcript search index once at startup.
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.search = await asyncio.to_thread(
        TranscriptSearch
    )
    yield


app = FastAPI(
    title="The Lenny Growth Assistant",
    lifespan=lifespan,
)


# Allow requests from the local React frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=[
        "GET",
        "POST",
        "DELETE",
    ],
    allow_headers=["Content-Type"],
)


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=4000,
    )
    session_id: UUID | None = None

    @field_validator("message")
    @classmethod
    def reject_blank_message(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Message cannot be blank.")

        return value


class Source(BaseModel):
    citation: str
    transcript_id: str
    chunk_id: str
    source_url: str
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    provider: str
    model: str
    grounded: bool
    sources: list[Source]
    grounding_status: str
    session_id: UUID | None = None


class SessionRequest(BaseModel):
    title: str = Field(
        default="New chat",
        min_length=1,
        max_length=120,
    )

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        value = value.strip()

        if not value:
            return "New chat"

        return value

class EssayRequest(BaseModel):
    topic: str = Field(
        min_length=3,
        max_length=500,
    )

    @field_validator("topic")
    @classmethod
    def clean_topic(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Essay topic cannot be blank.")

        return value


class ArtifactResponse(BaseModel):
    title: str
    artifact_type: str
    content: str
    provider: str
    model: str
    sources: list[Source]
# Run database operations without blocking other API requests.
async def run_database(function, *args):
    try:
        return await asyncio.to_thread(
            function,
            *args,
        )

    except (psycopg.Error, RuntimeError) as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "DATABASE_UNAVAILABLE",
                "message": (
                    "Cannot access the database. "
                    "Check that PostgreSQL is running "
                    "and the database configuration is correct."
                ),
            },
        ) from exc


def is_referential_follow_up(message: str) -> bool:
    """
    Detect short questions referring to an earlier response.

    Examples:
    - Explain the second point.
    - Can you explain that?
    - Tell me more about it.
    """
    if len(message.split()) > 12:
        return False

    message_lower = message.lower()

    word_reference = re.search(
        r"\b(that|this|it|previous|above)\b",
        message_lower,
    )

    phrase_references = (
        "first point",
        "second point",
        "third point",
        "last point",
        "explain more",
        "explain clearly",
        "tell me more",
        "what does that mean",
    )

    phrase_reference = any(
        phrase in message_lower
        for phrase in phrase_references
    )

    return bool(word_reference or phrase_reference)


def get_previous_sources(
    history: list[dict],
) -> list[dict]:
    """
    Convert the latest assistant message's saved sources
    into the passage format used by grounding.py.
    """
    for message in reversed(history):
        if message.get("role") != "assistant":
            continue

        stored_sources = message.get("sources") or []

        if not stored_sources:
            continue

        passages = []

        for source in stored_sources:
            excerpt = source.get("excerpt")

            if not excerpt:
                continue

            passages.append(
                {
                    "transcript_id": source.get(
                        "transcript_id",
                        "",
                    ),
                    "chunk_id": source.get(
                        "chunk_id",
                        "",
                    ),
                    "source_url": source.get(
                        "source_url",
                        "",
                    ),
                    "text": excerpt,
                }
            )

        if passages:
            return passages

    return []


async def retrieve_passages(
    request: ChatRequest,
    history: list[dict],
) -> list[dict]:
    """
    Retrieve new evidence or reuse the previous answer's
    evidence for a referential follow-up question.
    """
    referential_follow_up = is_referential_follow_up(
        request.message
    )

    if referential_follow_up:
        previous_sources = get_previous_sources(history)

        if previous_sources:
            return previous_sources

    search_query = request.message

    # If a referential follow-up has no saved evidence,
    # include the previous question in the search query.
    if referential_follow_up:
        previous_questions = [
            message.get("content", "")
            for message in history
            if (
                message.get("role") == "user"
                and message.get("content")
            )
        ]

        if previous_questions:
            search_query = (
                previous_questions[-1][:500]
                + "\n"
                + request.message
            )

    return await asyncio.to_thread(
        app.state.search.search,
        search_query,
    )


# Generate an answer from transcript evidence.
async def generate_answer(
    request: ChatRequest,
    history: list[dict],
) -> ChatResponse:
    active_model = provider_status()

    passages = await retrieve_passages(
        request,
        history,
    )

    if not passages:
        return ChatResponse(
            answer=INSUFFICIENT_EVIDENCE,
            provider=active_model["provider"],
            model=active_model["model"],
            grounded=False,
            sources=[],
            grounding_status="no_matches",
        )

    prompt = build_grounded_prompt(
        request.message,
        passages,
        history=history,
    )

    try:
        model_result = await ask_configured_model(prompt)
        answer = model_result.answer

    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "MODEL_UNAVAILABLE",
                "message": str(exc),
            },
        ) from exc

    if INSUFFICIENT_EVIDENCE.lower() in answer.lower():
        return ChatResponse(
            answer=INSUFFICIENT_EVIDENCE,
            provider=model_result.provider,
            model=model_result.model,
            grounded=False,
            sources=[],
            grounding_status="insufficient_evidence",
        )

    # Accept citation formats such as [1], [2], and [1, 2].
    citation_groups = re.findall(
        r"\[([0-9,\s]+)\]",
        answer,
    )

    cited_numbers = {
        int(number)
        for group in citation_groups
        for number in re.findall(r"\d+", group)
    }

    valid_numbers = set(
        range(1, len(passages) + 1)
    )

    # Confirm that citations refer to supplied passages.
    if (
        not cited_numbers
        or not cited_numbers.issubset(valid_numbers)
    ):
        return ChatResponse(
            answer=(
                "I couldn't produce an answer with valid transcript "
                "citations. Please try a more specific question."
            ),
            provider=model_result.provider,
            model=model_result.model,
            grounded=False,
            sources=[],
            grounding_status="citation_check_failed",
        )

    sources = []

    for number in sorted(cited_numbers):
        passage = passages[number - 1]

        sources.append(
            Source(
                citation=f"[{number}]",
                transcript_id=passage["transcript_id"],
                chunk_id=passage["chunk_id"],
                source_url=passage["source_url"],
                excerpt=passage["text"],
            )
        )

    return ChatResponse(
        answer=answer,
        provider=model_result.provider,
        model=model_result.model,
        grounded=False,
        sources=sources,
        grounding_status=(
            "citations_valid_support_unverified"
        ),
    )


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "lenny-growth-assistant",
        "llm": provider_status(),
    }


@app.get("/config")
def read_configuration():
    return provider_status()


@app.post("/sessions", status_code=201)
async def start_session(request: SessionRequest):
    return await run_database(
        create_session,
        request.title,
        {"client": "local-web"},
    )


@app.get("/sessions")
async def read_sessions():
    sessions = await run_database(
        list_sessions
    )

    return {
        "sessions": sessions,
    }


@app.get("/sessions/{session_id}/messages")
async def read_session_messages(session_id: UUID):
    session = await run_database(
        get_session,
        session_id,
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "SESSION_NOT_FOUND",
                "message": (
                    "This chat session does not exist."
                ),
            },
        )

    messages = await run_database(
        get_messages,
        session_id,
    )

    return {
        "session": session,
        "messages": messages,
    }


@app.delete("/sessions/{session_id}")
async def remove_session(session_id: UUID):
    deleted = await run_database(
        delete_session,
        session_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "SESSION_NOT_FOUND",
                "message": (
                    "This chat session does not exist."
                ),
            },
        )

    return {
        "deleted": True,
        "session_id": session_id,
    }

@app.post(
    "/artifacts/essay",
    response_model=ArtifactResponse,
)
async def create_essay_artifact(
    request: EssayRequest,
):
    passages = await asyncio.to_thread(
        app.state.search.search,
        request.topic,
    )

    # Use only the four strongest results for faster generation.
    passages = passages[:4]

    if not passages:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NO_TRANSCRIPT_EVIDENCE",
                "message": (
                    "No transcript evidence was found "
                    "for this essay topic."
                ),
            },
        )

    prompt = build_essay_prompt(
        request.topic,
        passages,
    )
    try:
        model_result = await ask_configured_model(
            prompt
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "MODEL_UNAVAILABLE",
                "message": str(exc),
            },
        ) from exc

    # This assignment must occur after the try/except.
    content = model_result.answer

    def extract_citations(text: str) -> set[int]:
        citation_groups = re.findall(
            r"\[([0-9,\s]+)\]",
            text,
        )

        return {
            int(number)
            for group in citation_groups
            for number in re.findall(r"\d+", group)
        }

    valid_numbers = set(
        range(1, len(passages) + 1)
    )

    cited_numbers = extract_citations(content)

    citations_are_valid = (
        bool(cited_numbers)
        and cited_numbers.issubset(valid_numbers)
    )

    # Give the local model one opportunity to fix citations.
    if not citations_are_valid:
        correction_prompt = f"""
Rewrite the essay below.

Mandatory rules:
- Preserve the main meaning and Markdown structure.
- Add transcript citations in square brackets.
- Use only citation numbers 1 through {len(passages)}.
- Valid examples: [1], [2], [1, 2].
- Every factual paragraph must end with a citation.
- Do not use any other citation format.
- Return only the corrected essay.

Essay to correct:

{content}
""".strip()

        try:
            corrected_result = await ask_configured_model(
                correction_prompt
            )

        except RuntimeError as exc:
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "MODEL_UNAVAILABLE",
                    "message": str(exc),
                },
            ) from exc

        content = corrected_result.answer
        model_result = corrected_result
        cited_numbers = extract_citations(content)

        citations_are_valid = (
            bool(cited_numbers)
            and cited_numbers.issubset(valid_numbers)
        )

    if not citations_are_valid:
        raise HTTPException(
            status_code=502,
            detail={
                "code": "ESSAY_CITATION_CHECK_FAILED",
                "message": (
                    "The model could not produce an essay "
                    "with valid transcript citations after "
                    "one correction attempt."
                ),
            },
        )

    sources = []

    for number in sorted(cited_numbers):
        passage = passages[number - 1]

        sources.append(
            Source(
                citation=f"[{number}]",
                transcript_id=passage["transcript_id"],
                chunk_id=passage["chunk_id"],
                source_url=passage["source_url"],
                excerpt=passage["text"],
            )
        )

    return ArtifactResponse(
        title=f"Ship 30 for 30: {request.topic}",
        artifact_type="markdown",
        content=content,
        provider=model_result.provider,
        model=model_result.model,
        sources=sources,
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if request.session_id is None:
        session = await run_database(
            create_session,
            "New chat",
            {"client": "local-web"},
        )

        session_id = session["id"]

    else:
        session_id = request.session_id

        session = await run_database(
            get_session,
            session_id,
        )

        if session is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "SESSION_NOT_FOUND",
                    "message": (
                        "This chat session does not exist."
                    ),
                },
            )

    # Load only messages belonging to the current session.
    history = await run_database(
        get_messages,
        session_id,
    )

    result = await generate_answer(
        request,
        history,
    )

    try:
        await run_database(
            save_exchange,
            session_id,
            request.message,
            result.answer,
            result.model,
            [
                source.model_dump()
                for source in result.sources
            ],
            result.grounding_status,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "SESSION_NOT_FOUND",
                "message": (
                    "This chat session no longer exists."
                ),
            },
        ) from exc

    result.session_id = session_id

    return result