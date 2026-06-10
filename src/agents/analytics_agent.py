"""
Week 2: Analytics Agent
Detects trends and patterns from historical records
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from memory.database import get_events
from datetime import datetime, timezone
import statistics


class AnalyticsAgent:
    """
    Analyzes trends in baby's feeding, sleep, and growth records.
    Returns structured insights that can be passed to the LLM for explanation.
    """

    def analyze_sleep(self, days: int = 14) -> dict:
        """
        Analyze sleep trends over the past N days.
        Detects: duration trend, night waking trend, best/worst nights.
        """
        events = get_events(event_type="sleep", limit=days)
        if not events:
            return {"status": "no_data", "message": "No sleep records found"}

        durations   = [e["data"].get("duration_hours", 0) for e in events]
        wakings     = [e["data"].get("night_wakings", 0) for e in events]
        dates       = [e["date"][:10] for e in events]

        # Split into first half and second half for trend detection
        mid = len(durations) // 2
        recent_dur  = durations[:mid] if mid > 0 else durations
        older_dur   = durations[mid:] if mid > 0 else durations
        recent_wake = wakings[:mid] if mid > 0 else wakings
        older_wake  = wakings[mid:] if mid > 0 else wakings

        dur_mean_recent  = statistics.mean(recent_dur)
        dur_mean_older   = statistics.mean(older_dur)
        wake_mean_recent = statistics.mean(recent_wake)
        wake_mean_older  = statistics.mean(older_wake)

        dur_trend  = "improving" if dur_mean_recent > dur_mean_older else "declining"
        wake_trend = "improving" if wake_mean_recent < wake_mean_older else "worsening"

        return {
            "status":          "ok",
            "n_records":       len(events),
            "avg_duration_hrs": round(statistics.mean(durations), 1),
            "avg_night_wakings": round(statistics.mean(wakings), 1),
            "best_night":      {"date": dates[durations.index(max(durations))],
                                "hours": max(durations)},
            "worst_night":     {"date": dates[durations.index(min(durations))],
                                "hours": min(durations)},
            "duration_trend":  dur_trend,
            "waking_trend":    wake_trend,
            "insight":         self._sleep_insight(
                                   statistics.mean(durations),
                                   statistics.mean(wakings),
                                   dur_trend, wake_trend
                               )
        }

    def _sleep_insight(self, avg_dur: float, avg_wake: float,
                       dur_trend: str, wake_trend: str) -> str:
        parts = []
        if avg_dur >= 10:
            parts.append(f"Sleep duration is healthy at {avg_dur:.1f} hrs/night on average.")
        elif avg_dur >= 8:
            parts.append(f"Sleep duration is adequate at {avg_dur:.1f} hrs/night.")
        else:
            parts.append(f"Sleep duration is low at {avg_dur:.1f} hrs/night — consider adjusting bedtime routine.")

        if avg_wake == 0:
            parts.append("Baby is sleeping through the night.")
        elif avg_wake <= 1:
            parts.append(f"Night wakings are minimal ({avg_wake:.1f}/night).")
        else:
            parts.append(f"Night wakings are frequent ({avg_wake:.1f}/night) — may indicate sleep regression.")

        parts.append(f"Trend: sleep duration is {dur_trend}, "
                     f"night wakings are {wake_trend}.")
        return " ".join(parts)

    def analyze_feeding(self) -> dict:
        """
        Analyze feeding diversity and patterns.
        """
        events = get_events(event_type="feeding", limit=50)
        if not events:
            return {"status": "no_data", "message": "No feeding records found"}

        foods   = [e["data"].get("food", "") for e in events if e["data"].get("food")]
        amounts = [e["data"].get("amount_ml", 0) for e in events
                   if e["data"].get("amount_ml", 0) > 0]
        unique_foods = list(set(foods))

        return {
            "status":          "ok",
            "n_records":       len(events),
            "unique_foods":    unique_foods,
            "n_unique_foods":  len(unique_foods),
            "avg_amount_ml":   round(statistics.mean(amounts), 1) if amounts else 0,
            "most_recent_food": foods[0] if foods else None,
            "insight":         (
                f"Baby has tried {len(unique_foods)} different foods: "
                f"{', '.join(unique_foods[:5])}{'...' if len(unique_foods) > 5 else ''}. "
                f"Average intake is {round(statistics.mean(amounts), 1) if amounts else 0}ml per feeding."
            )
        }

    def analyze_growth(self) -> dict:
        """
        Analyze growth trajectory.
        """
        events = get_events(event_type="growth", limit=20)
        if not events:
            return {"status": "no_data", "message": "No growth records found"}

        weights = [(e["date"][:10], e["data"].get("weight_kg"))
                   for e in events if e["data"].get("weight_kg")]
        heights = [(e["date"][:10], e["data"].get("height_cm"))
                   for e in events if e["data"].get("height_cm")]

        result = {"status": "ok", "n_records": len(events)}

        if weights:
            result["latest_weight"] = {"date": weights[0][0], "kg": weights[0][1]}
            if len(weights) > 1:
                gain = weights[0][1] - weights[-1][1]
                result["weight_gain_kg"] = round(gain, 2)
                result["weight_trend"]   = "gaining" if gain > 0 else "losing"

        if heights:
            result["latest_height"] = {"date": heights[0][0], "cm": heights[0][1]}

        result["insight"] = (
            f"Latest weight: {weights[0][1]}kg ({weights[0][0]}). "
            f"Latest height: {heights[0][1]}cm ({heights[0][0]})."
            if weights and heights else "Incomplete growth data."
        )
        return result

    def run_full_analysis(self) -> dict:
        """Run all analyses and return combined report."""
        return {
            "sleep":   self.analyze_sleep(),
            "feeding": self.analyze_feeding(),
            "growth":  self.analyze_growth(),
        }


if __name__ == "__main__":
    agent = AnalyticsAgent()

    print("=== Analytics Agent Test ===\n")

    print("── Sleep Analysis ──")
    sleep = agent.analyze_sleep()
    print(f"Records: {sleep.get('n_records')}")
    print(f"Avg duration: {sleep.get('avg_duration_hrs')} hrs")
    print(f"Avg wakings: {sleep.get('avg_night_wakings')}/night")
    print(f"Trend: {sleep.get('duration_trend')}")
    print(f"Insight: {sleep.get('insight')}\n")

    print("── Feeding Analysis ──")
    feeding = agent.analyze_feeding()
    print(f"Unique foods: {feeding.get('unique_foods')}")
    print(f"Insight: {feeding.get('insight')}\n")

    print("── Growth Analysis ──")
    growth = agent.analyze_growth()
    print(f"Insight: {growth.get('insight')}\n")