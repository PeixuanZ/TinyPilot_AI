"""
Week 2: Memory Agent
Retrieves relevant memories from SQLite + ChromaDB based on natural language queries
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from memory.database import get_events, get_events_by_date_range
from memory.vector_store import search_memory
from datetime import datetime, timedelta, timezone
import json


# ── Tool functions the LLM can call ──────────────────────────

def tool_search_semantic(query: str, n_results: int = 5) -> list:
    """
    Semantic search over all memories using ChromaDB.
    Use for: open-ended questions like 'what has baby eaten', 'any milestones'
    """
    results = search_memory(query, n_results=n_results)
    return results


def tool_get_recent_events(event_type: str, days: int = 7) -> list:
    """
    Get recent events of a specific type from SQLite.
    Use for: 'show me sleep records this week', 'recent feedings'
    event_type: feeding, sleep, growth, milestone, medical, note
    """
    start = datetime.now(timezone.utc) - timedelta(days=days)
    end   = datetime.now(timezone.utc)
    return get_events_by_date_range(start, end, event_type=event_type)


def tool_get_all_events(event_type: str, limit: int = 20) -> list:
    """
    Get all events of a specific type.
    Use for: 'all growth records', 'every milestone'
    """
    return get_events(event_type=event_type, limit=limit)


# ── Memory Agent ─────────────────────────────────────────────

class MemoryAgent:
    """
    Retrieves relevant memories based on a user query.
    Combines semantic search (ChromaDB) with structured retrieval (SQLite).
    """

    TOOLS = {
        "search_semantic":  tool_search_semantic,
        "get_recent_events": tool_get_recent_events,
        "get_all_events":   tool_get_all_events,
    }

    def __init__(self, llm_client=None):
        self.llm = llm_client  # will be Ollama client in Week 4

    def _classify_query(self, query: str) -> dict:
        """
        Rule-based query classifier (no LLM needed for Week 2).
        Week 4 will replace this with actual LLM tool calling.
        """
        query_lower = query.lower()

        # Detect event type
        event_type = None
        if any(w in query_lower for w in ["eat", "food", "feed", "meal", "drink"]):
            event_type = "feeding"
        elif any(w in query_lower for w in ["sleep", "nap", "wake", "night"]):
            event_type = "sleep"
        elif any(w in query_lower for w in ["weight", "height", "grow", "size"]):
            event_type = "growth"
        elif any(w in query_lower for w in ["milestone", "first", "walk", "talk", "crawl"]):
            event_type = "milestone"
        elif any(w in query_lower for w in ["doctor", "vaccine", "medical", "sick"]):
            event_type = "medical"

        # Detect time range
        days = 7  # default
        if any(w in query_lower for w in ["today", "tonight"]):
            days = 1
        elif any(w in query_lower for w in ["week", "7 day"]):
            days = 7
        elif any(w in query_lower for w in ["month", "30 day"]):
            days = 30
        elif any(w in query_lower for w in ["ever", "all", "history", "always"]):
            days = 999

        # Decide retrieval strategy
        if event_type and days < 999:
            strategy = "get_recent_events"
        elif event_type and days == 999:
            strategy = "get_all_events"
        else:
            strategy = "search_semantic"

        return {
            "strategy":   strategy,
            "event_type": event_type,
            "days":       days
        }

    def retrieve(self, query: str) -> dict:
        """
        Main retrieval method.
        Returns relevant memories for the given query.
        """
        plan = self._classify_query(query)
        results = []

        if plan["strategy"] == "get_recent_events" and plan["event_type"]:
            results = tool_get_recent_events(plan["event_type"], days=plan["days"])
        elif plan["strategy"] == "get_all_events" and plan["event_type"]:
            results = tool_get_all_events(plan["event_type"])
        else:
            # Fallback to semantic search
            semantic = tool_search_semantic(query)
            results  = [{"text": r["text"], "metadata": r["metadata"]}
                        for r in semantic]

        return {
            "query":    query,
            "plan":     plan,
            "results":  results,
            "n_found":  len(results)
        }

    def format_results(self, retrieval: dict) -> str:
        """Format retrieval results as readable text for the LLM."""
        if not retrieval["results"]:
            return "No relevant memories found."

        lines = [f"Found {retrieval['n_found']} relevant records:\n"]
        for i, r in enumerate(retrieval["results"], 1):
            if "event_type" in r:
                # SQLite result
                lines.append(
                    f"{i}. [{r['event_type'].upper()}] "
                    f"{r['date'][:10]} — {json.dumps(r['data'], ensure_ascii=False)}"
                )
            else:
                # ChromaDB result
                lines.append(f"{i}. {r.get('text', str(r))}")

        return "\n".join(lines)


if __name__ == "__main__":
    agent = MemoryAgent()

    test_queries = [
        "What did baby eat this week?",
        "How has baby been sleeping?",
        "Any milestones recently?",
        "Show me all growth records",
        "What foods has baby tried?",
    ]

    print("=== Memory Agent Test ===\n")
    for query in test_queries:
        print(f"Query: {query}")
        result = agent.retrieve(query)
        print(f"Strategy: {result['plan']['strategy']} "
              f"(type={result['plan']['event_type']}, "
              f"days={result['plan']['days']})")
        print(agent.format_results(result))
        print()