import hashlib
import re


def chunk_transcript(
    transcript: dict,
    chunk_words: int = 350,
    overlap_words: int = 60,
) -> list[dict]:
    if not 0 <= overlap_words < chunk_words:
        raise ValueError(
            "Overlap must be non-negative and smaller than chunk size."
        )

    text = transcript["text"]

    # Locate words while preserving the original text formatting.
    words = list(re.finditer(r"\S+", text))

    chunks = []
    step = chunk_words - overlap_words

    for start in range(0, len(words), step):
        end = min(start + chunk_words, len(words))

        passage = text[
            words[start].start():words[end - 1].end()
        ]

        fingerprint = (
            f"{transcript['id']}:{start}:{passage}"
        ).encode("utf-8")

        chunk_id = hashlib.sha256(fingerprint).hexdigest()[:24]

        chunks.append({
            "chunk_id": chunk_id,
            "transcript_id": transcript["id"],
            "title": transcript["title"],
            "guest": transcript["guest"],
            "source_url": transcript["source_url"],
            "youtube_url": transcript["youtube_url"],
            "word_start": start,
            "word_end": end,
            "text": passage,
        })

        if end == len(words):
            break

    return chunks