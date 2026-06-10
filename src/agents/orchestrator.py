"""
Week 4: Updated Orchestrator with LLM integration
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from agents.memory_agent    import MemoryAgent
from agents.analytics_agent import AnalyticsAgent
from agents.planning_agent  import PlanningAgent
from llm.ollama_client      import classify_intent, generate_response, parse_log_entry
from memory.database        import add_event
from datetime               import datetime, timezone
import json


class Orchestrator:

    def __init__(self):
        self.memory_agent         = MemoryAgent()
        self.analytics_agent      = AnalyticsAgent()
        self.planning_agent       = PlanningAgent()
        self.conversation_history = []

    def _handle_log(self, query: str) -> str:
        """Parse natural language and save to database."""
        parsed = parse_log_entry(query)
        if parsed and "event_type" in parsed:
            event_id = add_event(
                event_type=parsed["event_type"],
                data=parsed["data"]
            )
            return (f"Got it! I've logged this {parsed['event_type']} record:\n"
                    f"{json.dumps(parsed['data'], ensure_ascii=False)}")
        return "I couldn't parse that entry. Could you rephrase it?"

    def _handle_recall(self, query: str) -> str:
        retrieval = self.memory_agent.retrieve(query)
        context   = self.memory_agent.format_results(retrieval)
        return generate_response(query, context, self.conversation_history)

    def _handle_analyze(self, query: str) -> str:
        q = query.lower()
        parts = []

        if any(w in q for w in ["sleep", "nap", "wake"]):
            r = self.analytics_agent.analyze_sleep()
            parts.append(r.get("insight", ""))
        if any(w in q for w in ["eat", "food", "feed"]):
            r = self.analytics_agent.analyze_feeding()
            parts.append(r.get("insight", ""))
        if any(w in q for w in ["weight", "height", "grow"]):
            r = self.analytics_agent.analyze_growth()
            parts.append(r.get("insight", ""))
        if not parts:
            full  = self.analytics_agent.run_full_analysis()
            parts = [v.get("insight", "") for v in full.values()]

        context = "\n".join(parts)
        return generate_response(query, context, self.conversation_history)

    def _handle_plan(self, query: str) -> str:
        sleep_data   = self.analytics_agent.analyze_sleep()
        feeding_data = self.analytics_agent.analyze_feeding()
        plan = self.planning_agent.generate_weekly_plan(
            sleep_data, feeding_data, age_months=11
        )
        context = "\n".join([
            f"- {r['message']} → {r['action']}"
            for r in plan["top_priorities"]
        ])
        return generate_response(query, context, self.conversation_history)

    def chat(self, user_message: str) -> str:
        """Main entry point for Streamlit UI."""
        self.conversation_history.append({
            "role": "user", "content": user_message
        })

        # LLM-based intent classification
        intent   = classify_intent(user_message)
        handlers = {
            "log":     self._handle_log,
            "recall":  self._handle_recall,
            "analyze": self._handle_analyze,
            "plan":    self._handle_plan,
        }
        response = handlers.get(intent, self._handle_recall)(user_message)

        self.conversation_history.append({
            "role": "assistant", "content": response
        })
        return response


if __name__ == "__main__":
    orc = Orchestrator()
    print("=== Orchestrator + LLM Test ===\n")

    queries = [
        "Baby ate mashed sweet potato, about 60ml just now",
        "What has baby been eating this week?",
        "How has sleep been going lately?",
        "What should I focus on this week?",
    ]

    for q in queries:
        print(f"Parent: {q}")
        r = orc.chat(q)
        print(f"TinyPilot: {r}\n")

"""
Week 3: Orchestrator
Routes user queries to the right agents and aggregates responses
"""
'''
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from agents.memory_agent    import MemoryAgent
from agents.analytics_agent import AnalyticsAgent
from agents.planning_agent  import PlanningAgent
from memory.database        import add_event
from datetime               import datetime, timezone
import json


class Orchestrator:
    """
    Central coordinator for TinyPilot.
    Interprets user intent, delegates to agents, returns unified response.
    """

    def __init__(self):
        self.memory_agent    = MemoryAgent()
        self.analytics_agent = AnalyticsAgent()
        self.planning_agent  = PlanningAgent()
        self.conversation_history = []

    def _classify_intent(self, query: str) -> str:
        """
        Classify user query into one of 4 intents.
        Week 4 will use LLM for this — for now rule-based.
        """
        q = query.lower()

        # Log intent: adding new data
        if any(w in q for w in ["log", "add", "record", "just", "had", "ate",
                                  "slept", "weighed", "new", "today"]):
            return "log"

        # Analyze intent: trends and patterns
        if any(w in q for w in ["trend", "pattern", "analysis", "compare",
                                  "change", "progress", "better", "worse",
                                  "how has", "over"]):
            return "analyze"

        # Plan intent: recommendations and reminders
        if any(w in q for w in ["recommend", "suggest", "should", "plan",
                                  "remind", "next", "upcoming", "what to do",
                                  "advice", "tip"]):
            return "plan"

        # Recall intent: retrieving specific memories
        return "recall"

    def _handle_log(self, query: str) -> str:
        """Parse and log a new event from natural language."""
        q = query.lower()

        # Simple extraction (Week 4 will use LLM for this)
        if "slept" in q or "sleep" in q:
            return ("To log sleep, please use the format:\n"
                    "'Baby slept X hours with Y night wakings'")
        elif "ate" in q or "eat" in q or "fed" in q:
            return ("To log feeding, please use the format:\n"
                    "'Baby ate [food] — [amount]ml'")
        else:
            return "To log an event, please describe what happened and I'll save it."

    def _handle_recall(self, query: str) -> str:
        """Retrieve relevant memories."""
        retrieval = self.memory_agent.retrieve(query)
        formatted = self.memory_agent.format_results(retrieval)
        return formatted

    def _handle_analyze(self, query: str) -> str:
        """Run analytics and return insights."""
        q = query.lower()
        parts = []

        if any(w in q for w in ["sleep", "nap", "wake"]):
            result = self.analytics_agent.analyze_sleep()
            parts.append(f"Sleep analysis:\n{result.get('insight', '')}")

        if any(w in q for w in ["eat", "food", "feed", "meal"]):
            result = self.analytics_agent.analyze_feeding()
            parts.append(f"Feeding analysis:\n{result.get('insight', '')}")

        if any(w in q for w in ["weight", "height", "grow"]):
            result = self.analytics_agent.analyze_growth()
            parts.append(f"Growth analysis:\n{result.get('insight', '')}")

        if not parts:
            # Run full analysis
            full = self.analytics_agent.run_full_analysis()
            parts = [
                f"Sleep: {full['sleep'].get('insight', 'No data')}",
                f"Feeding: {full['feeding'].get('insight', 'No data')}",
                f"Growth: {full['growth'].get('insight', 'No data')}",
            ]

        return "\n\n".join(parts)

    def _handle_plan(self, query: str) -> str:
        """Generate recommendations and reminders."""
        sleep_data   = self.analytics_agent.analyze_sleep()
        feeding_data = self.analytics_agent.analyze_feeding()
        plan = self.planning_agent.generate_weekly_plan(
            sleep_data, feeding_data, age_months=11
        )

        lines = ["Here are my recommendations:\n"]
        for i, rec in enumerate(plan["top_priorities"], 1):
            lines.append(f"{i}. {rec['message']}")
            lines.append(f"   → {rec['action']}\n")

        if plan["reminders"]:
            lines.append("Upcoming reminders:")
            for r in plan["reminders"]:
                lines.append(f"• {r['message']}")
                lines.append(f"  → {r['action']}")

        return "\n".join(lines)

    def chat(self, user_message: str) -> str:
        """
        Main entry point. Takes a user message, returns a response.
        This is what the Streamlit UI will call.
        """
        # Add to conversation history
        self.conversation_history.append({
            "role":    "user",
            "content": user_message,
            "time":    datetime.now(timezone.utc).isoformat()
        })

        # Classify intent
        intent = self._classify_intent(user_message)

        # Route to appropriate handler
        if intent == "log":
            response = self._handle_log(user_message)
        elif intent == "analyze":
            response = self._handle_analyze(user_message)
        elif intent == "plan":
            response = self._handle_plan(user_message)
        else:
            response = self._handle_recall(user_message)

        # Add response to history
        self.conversation_history.append({
            "role":    "assistant",
            "content": response,
            "time":    datetime.now(timezone.utc).isoformat()
        })

        return response

    def get_history(self) -> list:
        return self.conversation_history


if __name__ == "__main__":
    orchestrator = Orchestrator()

    print("=== Orchestrator Test ===\n")
    print("TinyPilot is ready. Type your questions.\n")

    test_queries = [
        "What did baby eat this week?",
        "How has baby's sleep changed over time?",
        "What should I focus on this week?",
        "Any milestones coming up?",
        "Show me all feeding records",
    ]

    for query in test_queries:
        print(f"Parent: {query}")
        response = orchestrator.chat(query)
        print(f"TinyPilot: {response}")
        print()
'''    