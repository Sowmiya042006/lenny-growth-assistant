import json
import os

import httpx


OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://127.0.0.1:11434",
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5:3b",
)


SYSTEM_INSTRUCTION = """
You are a transcript-grounded product and growth assistant.

Follow the user prompt exactly.
Use only the supplied transcript evidence.
Do not add outside facts or unsupported assumptions.
Do not invent quotations, people, companies, or statistics.
Do not claim causation when evidence shows correlation.
Use only citation numbers supplied with the evidence.
Return only the requested answer or artifact.
""".strip()


async def ask_ollama(message: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_INSTRUCTION,
            },
            {
                "role": "user",
                "content": message,
            },
        ],
        "stream": True,
        "keep_alive": "10m",
        "options": {
            "temperature": 0.2,
            "num_ctx": 8192,
            "num_predict": 2200,
        },
    }

    timeout = httpx.Timeout(
    connect=10.0,
    read=600.0,
    write=60.0,
    pool=30.0,
)
    answer_parts = []

    try:
        async with httpx.AsyncClient(
            timeout=timeout
        ) as client:
            async with client.stream(
                "POST",
                (
                    f"{OLLAMA_BASE_URL.rstrip('/')}"
                    "/api/chat"
                ),
                json=payload,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise RuntimeError(
                            "Ollama returned invalid streaming data."
                        ) from exc

                    if chunk.get("error"):
                        raise RuntimeError(
                            str(chunk["error"])
                        )

                    content = (
                        chunk.get("message", {})
                        .get("content", "")
                    )

                    if content:
                        answer_parts.append(content)

                    if chunk.get("done"):
                        break

    except httpx.TimeoutException as exc:
        raise RuntimeError(
            "Ollama stopped responding during generation."
        ) from exc

    except httpx.RequestError as exc:
        raise RuntimeError(
            "Cannot reach Ollama. "
            "Check that Ollama is running."
        ) from exc

    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"Ollama returned HTTP "
            f"{exc.response.status_code}. "
            "Check that the configured model is installed."
        ) from exc

    answer = "".join(answer_parts).strip()

    if not answer:
        raise RuntimeError(
            "Ollama returned an empty answer."
        )

    return answer