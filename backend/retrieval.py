import json
import re
from pathlib import Path

from rank_bm25 import BM25Okapi


CHUNKS_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "chunks.jsonl"
)

STOP_WORDS = set(
    "a an the is are was were be been being "
    "i me my we our you your he she it they their "
    "and or but if of to in on at for from with "
    "this that these those "
    "do does did can could would should "
    "what which who how why when where "
    "please tell explain about".split()
)


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())

    return [
        word
        for word in words
        if word not in STOP_WORDS and len(word) > 1
    ]


class TranscriptSearch:
    def __init__(self, path: Path = CHUNKS_PATH):
        if not path.exists():
            raise FileNotFoundError(
                "Chunks file is missing. Run ingest.py first."
            )

        with path.open("r", encoding="utf-8") as file:
            self.chunks = [
                json.loads(line)
                for line in file
                if line.strip()
            ]

        if not self.chunks:
            raise ValueError("The chunks file is empty.")

        documents = [
            tokenize(chunk["text"])
            for chunk in self.chunks
        ]

        if not any(documents):
            raise ValueError("No searchable words found.")

        self.index = BM25Okapi(documents)

    def search(self, question: str, limit: int = 4) -> list[dict]:
        # Remove repeated query words while keeping their order.
        query = list(dict.fromkeys(tokenize(question)))

        if not query or limit <= 0:
            return []

        scores = self.index.get_scores(query)

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda index: float(scores[index]),
            reverse=True,
        )

        results = []
        episode_counts = {}

        for index in ranked_indices:
            score = float(scores[index])

            if score <= 0:
                break

            chunk = self.chunks[index]
            episode_id = chunk["transcript_id"]

            # Avoid filling every result with the same episode.
            if episode_counts.get(episode_id, 0) >= 2:
                continue

            results.append({
                **chunk,
                "score": round(score, 3),
            })

            episode_counts[episode_id] = (
                episode_counts.get(episode_id, 0) + 1
            )

            if len(results) >= limit:
                break

        return results


if __name__ == "__main__":
    search_engine = TranscriptSearch()

    question = "How can I improve customer retention?"
    results = search_engine.search(question)

    print(f"Question: {question}")
    print(f"Passages indexed: {len(search_engine.chunks)}")

    for number, result in enumerate(results, start=1):
        print(f"\n[{number}] {result['title']}")
        print(f"Score: {result['score']}")
        print(f"Source: {result['source_url']}")
        print(f"Preview: {result['text'][:700]}")