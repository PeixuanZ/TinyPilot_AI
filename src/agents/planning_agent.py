"""
Week 3: Planning Agent
Generates actionable recommendations based on analytics results
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from memory.database import get_events, add_event
from datetime import datetime, timezone, timedelta


class PlanningAgent:
    """
    Generates recommendations, reminders, and action plans
    based on baby's current data and developmental stage.
    """

    # Developmental milestones by age (months)
    MILESTONES_EXPECTED = {
        6:  ["sits without support", "responds to name", "babbling"],
        9:  ["crawling", "pincer grasp", "stranger anxiety"],
        12: ["first words", "standing with support", "first steps"],
        18: ["walking independently", "10+ words", "stacking blocks"],
        24: ["50+ words", "two-word phrases", "running"],
    }

    # WHO sleep recommendations by age (months)
    SLEEP_RECOMMENDATIONS = {
        (0, 3):   (14, 17),
        (4, 11):  (12, 16),
        (12, 23): (11, 14),
        (24, 36): (10, 13),
    }

    def recommend_from_sleep(self, sleep_analysis: dict) -> list:
        """Generate sleep recommendations."""
        recommendations = []

        if sleep_analysis.get("status") == "no_data":
            recommendations.append({
                "type":     "reminder",
                "priority": "low",
                "message":  "Start tracking sleep to get personalized insights.",
                "action":   "Log tonight's sleep duration and any night wakings."
            })
            return recommendations

        avg_dur  = sleep_analysis.get("avg_duration_hrs", 0)
        avg_wake = sleep_analysis.get("avg_night_wakings", 0)
        trend    = sleep_analysis.get("duration_trend", "")

        if avg_dur < 10:
            recommendations.append({
                "type":     "suggestion",
                "priority": "high",
                "message":  f"Sleep duration ({avg_dur}hrs) is below the recommended 10-12hrs.",
                "action":   "Try moving bedtime 30 minutes earlier for the next 3 nights."
            })

        if avg_wake > 2:
            recommendations.append({
                "type":     "suggestion",
                "priority": "high",
                "message":  f"Frequent night wakings ({avg_wake:.1f}/night) detected.",
                "action":   "Consider a consistent wind-down routine: bath → feed → song → sleep."
            })

        if trend == "declining":
            recommendations.append({
                "type":     "alert",
                "priority": "medium",
                "message":  "Sleep duration has been decreasing recently.",
                "action":   "Check for teething, growth spurt, or schedule changes."
            })

        if not recommendations:
            recommendations.append({
                "type":     "positive",
                "priority": "low",
                "message":  f"Sleep looks great! {avg_dur}hrs average with {avg_wake:.1f} wakings/night.",
                "action":   "Keep the current routine going."
            })

        return recommendations

    def recommend_from_feeding(self, feeding_analysis: dict) -> list:
        """Generate feeding recommendations."""
        recommendations = []

        if feeding_analysis.get("status") == "no_data":
            recommendations.append({
                "type":     "reminder",
                "priority": "medium",
                "message":  "No feeding records found.",
                "action":   "Start logging meals to track food diversity."
            })
            return recommendations

        n_foods = feeding_analysis.get("n_unique_foods", 0)
        foods   = feeding_analysis.get("unique_foods", [])

        if n_foods < 5:
            recommendations.append({
                "type":     "suggestion",
                "priority": "medium",
                "message":  f"Baby has tried only {n_foods} different foods.",
                "action":   "Introduce one new food every 3-4 days. Try sweet potato or avocado next."
            })
        elif n_foods >= 10:
            recommendations.append({
                "type":     "positive",
                "priority": "low",
                "message":  f"Great food diversity! Baby has tried {n_foods} different foods.",
                "action":   "Continue introducing new textures and flavors."
            })

        # Check for allergen exposure
        allergens = ["egg", "peanut", "fish", "wheat", "dairy", "soy"]
        tried_allergens = [a for a in allergens
                           if any(a in f.lower() for f in foods)]
        if len(tried_allergens) < 3:
            recommendations.append({
                "type":     "suggestion",
                "priority": "medium",
                "message":  "Early allergen introduction is recommended.",
                "action":   f"Consider introducing: {', '.join([a for a in allergens if a not in tried_allergens][:3])}."
            })

        return recommendations

    def get_upcoming_reminders(self, age_months: int = 11) -> list:
        """Generate upcoming appointment and milestone reminders."""
        reminders = []

        # Vaccine schedule (simplified)
        vaccine_schedule = {6: "6-month vaccines", 9: "9-month checkup",
                            12: "12-month vaccines", 15: "15-month vaccines",
                            18: "18-month checkup"}
        for month, vaccine in vaccine_schedule.items():
            if age_months <= month <= age_months + 2:
                reminders.append({
                    "type":    "appointment",
                    "message": f"Upcoming: {vaccine} (around {month} months)",
                    "action":  "Schedule pediatrician appointment."
                })

        # Upcoming milestones
        for month, milestones in self.MILESTONES_EXPECTED.items():
            if age_months < month <= age_months + 3:
                reminders.append({
                    "type":    "milestone",
                    "message": f"Expected milestones around {month} months:",
                    "action":  f"Watch for: {', '.join(milestones)}."
                })

        return reminders

    def generate_weekly_plan(self,
                              sleep_analysis: dict,
                              feeding_analysis: dict,
                              age_months: int = 11) -> dict:
        """Generate a complete weekly action plan."""
        sleep_recs   = self.recommend_from_sleep(sleep_analysis)
        feeding_recs = self.recommend_from_feeding(feeding_analysis)
        reminders    = self.get_upcoming_reminders(age_months)

        # Sort by priority
        all_recs = sleep_recs + feeding_recs + reminders
        priority_order = {"high": 0, "medium": 1, "low": 2, "appointment": 0}
        all_recs.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 2))

        return {
            "generated_at":      datetime.now(timezone.utc).isoformat(),
            "age_months":        age_months,
            "sleep_recommendations":   sleep_recs,
            "feeding_recommendations": feeding_recs,
            "reminders":              reminders,
            "top_priorities":          all_recs[:3],
        }


if __name__ == "__main__":
    from analytics_agent import AnalyticsAgent

    analytics = AnalyticsAgent()
    planning  = PlanningAgent()

    sleep_data   = analytics.analyze_sleep()
    feeding_data = analytics.analyze_feeding()

    plan = planning.generate_weekly_plan(sleep_data, feeding_data, age_months=11)

    print("=== Planning Agent Test ===\n")
    print("── Top Priorities ──")
    for i, rec in enumerate(plan["top_priorities"], 1):
        print(f"{i}. [{rec['type'].upper()}] {rec['message']}")
        print(f"   → {rec['action']}\n")

    print("── Upcoming Reminders ──")
    for r in plan["reminders"]:
        print(f"• {r['message']}")
        print(f"  → {r['action']}\n")