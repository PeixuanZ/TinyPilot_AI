"""
Week 4: Ollama LLM client
Wraps Ollama API for use by all agents
"""
import requests
import json
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))


OLLAMA_HOST  = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"


def chat(messages: list, model: str = OLLAMA_MODEL,
         temperature: float = 0.7) -> str:
    """
    Send a conversation to Ollama and return the response text.
    messages = [{"role": "user/assistant/system", "content": "..."}]
    """
    response = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={
            "model":    model,
            "messages": messages,
            "stream":   False,
            "options":  {"temperature": temperature}
        },
        timeout=60
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


def classify_intent(query: str) -> str:
    """Use LLM to classify user intent."""
    prompt = f"""You are a routing classifier for a baby care assistant app.
Classify the user's message into exactly one of these intents:
- log: user wants to record/add new data (feeding, sleep, growth, milestone)
- recall: user wants to retrieve specific past records
- analyze: user wants trends, patterns, or comparisons over time
- plan: user wants recommendations, reminders, or advice

User message: "{query}"

Reply with only one word: log, recall, analyze, or plan."""

    result = chat(
        [{"role": "user", "content": prompt}],
        temperature=0.0  # deterministic
    )
    intent = result.strip().lower()
    if intent not in ["log", "recall", "analyze", "plan"]:
        return "recall"  # safe fallback
    return intent


def generate_response(
    user_query: str,
    context: str,
    conversation_history: list = None
) -> str:
    """
    Generate a natural language response given retrieved context.
    This is the core LLM call that makes TinyPilot conversational.
    """
    system_prompt = """You are TinyPilot, a warm and knowledgeable AI assistant
helping parents track and understand their baby's development.

Your personality:
- Warm, supportive, and encouraging
- Evidence-based but not clinical
- Concise — 2-4 sentences max unless asked for more
- Always end with one actionable suggestion when relevant

You have access to the baby's records provided in the context.
Only use information from the context — never make up data."""

    messages = [{"role": "system", "content": system_prompt}]

    # Add conversation history (last 4 turns for context)
    if conversation_history:
        for turn in conversation_history[-4:]:
            messages.append({
                "role":    turn["role"],
                "content": turn["content"]
            })

    # Add current query with context
    messages.append({
        "role": "user",
        "content": f"""Context from baby's records:
{context}

Parent's question: {user_query}

Please answer based on the context above."""
    })

    return chat(messages, temperature=0.7)


def parse_log_entry(user_message: str) -> dict:
    """
    Use LLM to extract structured data from a natural language log entry.
    e.g. "Baby ate banana and some rice, about 80ml" →
         {"event_type": "feeding", "data": {"food": "banana, rice", "amount_ml": 80}}
    """
    prompt = f"""Extract structured data from this baby care log entry.
Return ONLY valid JSON, no explanation.

Input: "{user_message}"

Return one of these formats:
- Feeding: {{"event_type": "feeding", "data": {{"food": "...", "amount_ml": 0}}}}
- Sleep:   {{"event_type": "sleep",   "data": {{"duration_hours": 0, "night_wakings": 0}}}}
- Growth:  {{"event_type": "growth",  "data": {{"weight_kg": 0, "height_cm": 0}}}}
- Milestone: {{"event_type": "milestone", "data": {{"milestone": "...", "age_months": 0}}}}
- Note:    {{"event_type": "note",    "data": {{"text": "..."}}}}

JSON only:"""

    result = chat([{"role": "user", "content": prompt}], temperature=0.0)

    # Clean and parse
    result = result.strip()
    if result.startswith("```"):
        result = result.split("```")[1]
        if result.startswith("json"):
            result = result[4:]
    try:
        return json.loads(result.strip())
    except json.JSONDecodeError:
        return {"event_type": "note", "data": {"text": user_message}}


if __name__ == "__main__":
    print("=== Ollama LLM Client Test ===\n")

    # Test intent classification
    test_queries = [
        "What did baby eat this week?",
        "Baby slept 9 hours last night with 2 wakings",
        "How has sleep changed over the past month?",
        "What should I introduce next for feeding?",
        "Any milestones coming up?",
    ]

    print("── Intent Classification ──")
    for q in test_queries:
        intent = classify_intent(q)
        print(f"  '{q[:45]}...' → {intent}" if len(q) > 45 else f"  '{q}' → {intent}")

    print("\n── Log Entry Parsing ──")
    log_entries = [
        "Baby ate mashed sweet potato, about 60ml",
        "Slept 10.5 hours last night, no wakings",
        "Weight check: 7.5kg at 11 months",
        "Baby said mama for the first time today!",
    ]
    for entry in log_entries:
        parsed = parse_log_entry(entry)
        print(f"  Input:  {entry}")
        print(f"  Parsed: {parsed}\n")

    print("── Natural Language Response ──")
    context = """Found 5 relevant records:
1. [FEEDING] 2026-06-10 — food: breast milk, amount: 120ml
2. [FEEDING] 2026-06-09 — food: oatmeal, amount: 80ml
3. [FEEDING] 2026-06-08 — food: banana, amount: 50ml
4. [FEEDING] 2026-06-07 — food: salmon, amount: 60ml
5. [FEEDING] 2026-06-06 — food: yogurt, amount: 90ml"""

    response = generate_response(
        "What has baby been eating this week?",
        context
    )
    print(f"  Response: {response}")