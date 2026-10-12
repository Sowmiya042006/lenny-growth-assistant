from pathlib import Path
from urllib.parse import quote

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TRANSCRIPT_ROOT = PROJECT_ROOT / "data" / "lennys-transcripts"


def read_transcript(path: Path) -> dict:
    # Read characters correctly, including Unicode.
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()

    if not lines or lines[0].strip() != "---":
        raise ValueError(f"Missing metadata section: {path}")

    # Find the closing metadata marker.
    closing_index = next(
        (
            index
            for index in range(1, len(lines))
            if lines[index].strip() == "---"
        ),
        None,
    )

    if closing_index is None:
        raise ValueError(f"Unclosed metadata section: {path}")

    metadata_text = "\n".join(lines[1:closing_index])
    metadata = yaml.safe_load(metadata_text)

    if not isinstance(metadata, dict):
        raise ValueError(f"Invalid metadata: {path}")

    # Use the actual transcript, excluding the description and keywords.
    body = "\n".join(lines[closing_index + 1:]).strip()

    if "## Transcript" in body:
        body = body.split("## Transcript", 1)[1].strip()

    if not body:
        raise ValueError(f"Empty transcript: {path}")

    relative_path = path.relative_to(TRANSCRIPT_ROOT).as_posix()

    return {
        "id": relative_path,
        "title": str(metadata.get("title") or path.parent.name),
        "guest": str(metadata.get("guest") or "Unknown"),
        "youtube_url": str(metadata.get("youtube_url") or ""),
        "source_url": (
            "https://github.com/ChatPRD/lennys-podcast-transcripts/"
            f"blob/main/{quote(relative_path, safe='/')}"
        ),
        "text": body,
    }


if __name__ == "__main__":
    files = sorted(
        (TRANSCRIPT_ROOT / "episodes").glob("*/transcript.md")
    )

    if not files:
        raise SystemExit("No transcripts found. Check the data folder.")

    sample = read_transcript(files[0])

    print(f"Transcript files: {len(files)}")
    print(f"Title: {sample['title']}")
    print(f"Guest: {sample['guest']}")
    print(f"Source: {sample['source_url']}")
    print(f"Transcript characters: {len(sample['text'])}")
    print("\nPreview:")
    print(sample["text"][:500])