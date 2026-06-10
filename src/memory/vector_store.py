"""
Week 1: Vector store for semantic memory retrieval
"""
import chromadb
from pathlib import Path
import json

ROOT_DIR   = Path(__file__).parent.parent.parent
CHROMA_DIR = ROOT_DIR / "data" / "vectors"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

client     = chromadb.PersistentClient(path=str(CHROMA_DIR))
collection = client.get_or_create_collection(
    name="tinypilot_memories",
    metadata={"hnsw:space": "cosine"}
)


def add_memory(event_id: str, text: str, metadata: dict):
    """Add an event to the vector store."""
    collection.add(
        documents=[text],
        metadatas=[metadata],
        ids=[event_id]
    )


def search_memory(query: str, n_results: int = 5) -> list:
    """Semantic search over all memories."""
    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, collection.count())
    )
    if not results["documents"][0]:
        return []

    return [
        {
            "text":     results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i]
        }
        for i in range(len(results["documents"][0]))
    ]


def get_memory_count() -> int:
    return collection.count()


if __name__ == "__main__":
    # test
    add_memory(
        "test-001",
        "Baby ate salmon for the first time today, seemed to enjoy it",
        {"event_type": "feeding", "date": "2026-06-01"}
    )
    add_memory(
        "test-002",
        "Baby slept 10 hours with only one night waking",
        {"event_type": "sleep", "date": "2026-06-02"}
    )
    add_memory(
        "test-003",
        "Baby took first steps today, 11 months old",
        {"event_type": "milestone", "date": "2026-06-03"}
    )

    print(f"Total memories: {get_memory_count()}")

    results = search_memory("what did baby eat")
    print("\nSearch: 'what did baby eat'")
    for r in results:
        print(f"  [{r['metadata']['event_type']}] {r['text'][:60]}")