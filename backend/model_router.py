import os
from dataclasses import dataclass

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    TextBlock,
    query,
)

from ollama_client import (
    OLLAMA_MODEL,
    ask_ollama,
)


LLM_PROVIDER = os.getenv(
    "LLM_PROVIDER",
    "ollama",
).strip().lower()

CLAUDE_MODEL = os.getenv(
    "CLAUDE_MODEL",
    "sonnet",
).strip()


@dataclass
class ModelResult:
    answer: str
    provider: str
    model: str


async def ask_claude_agent(prompt: str) -> str:
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "Claude is selected, but ANTHROPIC_API_KEY "
            "is not configured."
        )

    options = ClaudeAgentOptions(
        model=CLAUDE_MODEL,
        max_turns=1,
        system_prompt=(
            "You are a source-grounded product and growth "
            "assistant. Follow the supplied evidence and citation "
            "rules exactly. Do not use outside knowledge."
        ),

        # The web application only needs text generation.
        # Block Claude Code filesystem, shell, network, and
        # sub-agent tools.
        disallowed_tools=[
            "Bash",
            "Read",
            "Write",
            "Edit",
            "Glob",
            "Grep",
            "WebFetch",
            "WebSearch",
            "Task",
            "NotebookEdit",
        ],
    )

    text_parts = []

    try:
        async for sdk_message in query(
            prompt=prompt,
            options=options,
        ):
            if not isinstance(
                sdk_message,
                AssistantMessage,
            ):
                continue

            for block in sdk_message.content:
                if isinstance(block, TextBlock):
                    text_parts.append(block.text)

    except Exception as exc:
        raise RuntimeError(
            "Claude Agent SDK request failed. "
            "Check the API key, model, and network connection."
        ) from exc

    answer = "\n".join(text_parts).strip()

    if not answer:
        raise RuntimeError(
            "Claude Agent SDK returned an empty answer."
        )

    return answer


async def ask_configured_model(
    prompt: str,
) -> ModelResult:
    if LLM_PROVIDER == "ollama":
        answer = await ask_ollama(prompt)

        return ModelResult(
            answer=answer,
            provider="ollama",
            model=OLLAMA_MODEL,
        )

    if LLM_PROVIDER == "claude":
        answer = await ask_claude_agent(prompt)

        return ModelResult(
            answer=answer,
            provider="claude-agent-sdk",
            model=CLAUDE_MODEL,
        )

    raise RuntimeError(
        "Unsupported LLM_PROVIDER. "
        "Use 'ollama' or 'claude'."
    )


def provider_status() -> dict:
    return {
        "provider": LLM_PROVIDER,
        "model": (
            OLLAMA_MODEL
            if LLM_PROVIDER == "ollama"
            else CLAUDE_MODEL
        ),
        "cloud_configured": bool(
            os.getenv("ANTHROPIC_API_KEY")
        ),
        "fallback": "disabled",
    }