import json

from chunker import chunk_transcript
from transcript_reader import (
    PROJECT_ROOT,
    TRANSCRIPT_ROOT,
    read_transcript,
)


def main():
    files = sorted(
        (TRANSCRIPT_ROOT / "episodes").glob("*/transcript.md")
    )

    if not files:
        raise SystemExit("No transcript files found.")

    output_path = PROJECT_ROOT / "data" / "chunks.jsonl"
    temporary_path = output_path.with_suffix(".jsonl.tmp")

    transcript_count = 0
    chunk_count = 0
    failures = []

    with temporary_path.open("w", encoding="utf-8") as output:
        for path in files:
            try:
                transcript = read_transcript(path)
                chunks = chunk_transcript(transcript)

                if not chunks:
                    raise ValueError("Transcript produced no chunks.")

            except Exception as exc:
                failures.append({
                    "file": str(path.relative_to(TRANSCRIPT_ROOT)),
                    "error": str(exc),
                })
                continue

            for chunk in chunks:
                output.write(
                    json.dumps(chunk, ensure_ascii=False) + "\n"
                )

            transcript_count += 1
            chunk_count += len(chunks)

    if failures:
        temporary_path.unlink(missing_ok=True)

        print("Ingestion stopped. Existing chunks were not replaced.")
        print(json.dumps(failures, indent=2, ensure_ascii=False))

        raise SystemExit(1)

    temporary_path.replace(output_path)

    print(f"Transcripts processed: {transcript_count}")
    print(f"Chunks created: {chunk_count}")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()