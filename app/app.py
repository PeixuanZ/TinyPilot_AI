"""
Week 5: TinyPilot Streamlit UI
"""
import streamlit as st
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from agents.orchestrator import Orchestrator
from agents.analytics_agent import AnalyticsAgent
from memory.database import add_event, get_events
from datetime import datetime, timezone

st.set_page_config(
    page_title="TinyPilot",
    page_icon="👶",
    layout="wide"
)

# ── Initialize session state ──────────────────────────────────
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = Orchestrator()
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Sidebar ───────────────────────────────────────────────────
st.sidebar.title("👶 TinyPilot")
st.sidebar.caption("AI-powered infant care assistant")

page = st.sidebar.radio(
    "Navigation",
    ["💬 Chat", "📊 Dashboard", "📝 Log Event", "📅 Timeline"]
)

# ── Quick stats in sidebar ────────────────────────────────────
st.sidebar.divider()
st.sidebar.caption("Quick Stats")
analytics = AnalyticsAgent()
sleep_data   = analytics.analyze_sleep()
feeding_data = analytics.analyze_feeding()

if sleep_data.get("status") == "ok":
    st.sidebar.metric(
        "Last night's sleep",
        f"{sleep_data.get('avg_duration_hrs', 0)} hrs"
    )
if feeding_data.get("status") == "ok":
    st.sidebar.metric(
        "Foods tried",
        feeding_data.get("n_unique_foods", 0)
    )


# ══════════════════════════════════════════════════════════════
# Page 1: Chat
# ══════════════════════════════════════════════════════════════
if page == "💬 Chat":
    st.title("💬 Chat with TinyPilot")
    st.caption("Ask anything about your baby's development, sleep, feeding, or milestones.")

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"],
                             avatar="👨‍👩‍👦" if msg["role"] == "user" else "👶"):
            st.write(msg["content"])

    # Suggested prompts
    if not st.session_state.messages:
        st.markdown("**Try asking:**")
        cols = st.columns(2)
        prompts = [
            "What did baby eat this week?",
            "How has sleep been going?",
            "What should I focus on this week?",
            "Any milestones coming up?",
        ]
        for i, prompt in enumerate(prompts):
            if cols[i % 2].button(prompt, use_container_width=True):
                st.session_state.messages.append(
                    {"role": "user", "content": prompt}
                )
                with st.spinner("TinyPilot is thinking..."):
                    response = st.session_state.orchestrator.chat(prompt)
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )
                st.rerun()

    # Chat input
    if user_input := st.chat_input("Ask TinyPilot anything..."):
        st.session_state.messages.append(
            {"role": "user", "content": user_input}
        )
        with st.chat_message("user", avatar="👨‍👩‍👦"):
            st.write(user_input)

        with st.chat_message("assistant", avatar="👶"):
            with st.spinner("Thinking..."):
                response = st.session_state.orchestrator.chat(user_input)
            st.write(response)

        st.session_state.messages.append(
            {"role": "assistant", "content": response}
        )


# ══════════════════════════════════════════════════════════════
# Page 2: Dashboard
# ══════════════════════════════════════════════════════════════
elif page == "📊 Dashboard":
    st.title("📊 Baby Dashboard")

    # KPI row
    col1, col2, col3, col4 = st.columns(4)
    growth = analytics.analyze_growth()

    col1.metric("Avg sleep",
                f"{sleep_data.get('avg_duration_hrs', '--')} hrs")
    col2.metric("Night wakings",
                f"{sleep_data.get('avg_night_wakings', '--')}/night")
    col3.metric("Foods tried",
                feeding_data.get("n_unique_foods", "--"))
    col4.metric("Weight",
                f"{growth.get('latest_weight', {}).get('kg', '--')} kg"
                if growth.get("status") == "ok" else "--")

    st.divider()

    col_l, col_r = st.columns(2)

    # Sleep chart
    with col_l:
        st.subheader("Sleep history")
        import matplotlib.pyplot as plt
        sleep_events = get_events("sleep", limit=14)
        if sleep_events:
            dates = [e["date"][:10] for e in reversed(sleep_events)]
            hours = [e["data"].get("duration_hours", 0)
                     for e in reversed(sleep_events)]
            wakings = [e["data"].get("night_wakings", 0)
                       for e in reversed(sleep_events)]

            fig, ax1 = plt.subplots(figsize=(5, 3))
            ax1.bar(range(len(dates)), hours,
                    color="#1D9E75", alpha=0.7, label="Sleep hrs")
            ax1.axhline(10, color="#D85A30", linestyle="--",
                        linewidth=1, label="Recommended")
            ax1.set_xticks(range(len(dates)))
            ax1.set_xticklabels(
                [d[5:] for d in dates], rotation=45, fontsize=8
            )
            ax1.set_ylabel("Hours")
            ax1.legend(fontsize=8)
            st.pyplot(fig)
            plt.close()
        else:
            st.info("No sleep records yet.")

    # Feeding chart
    with col_r:
        st.subheader("Foods introduced")
        feeding_events = get_events("feeding", limit=20)
        if feeding_events:
            foods = [e["data"].get("food", "unknown")
                     for e in feeding_events]
            food_counts = {}
            for f in foods:
                food_counts[f] = food_counts.get(f, 0) + 1

            fig, ax = plt.subplots(figsize=(5, 3))
            ax.barh(list(food_counts.keys()),
                    list(food_counts.values()),
                    color="#7F77DD", alpha=0.8)
            ax.set_xlabel("Times recorded")
            st.pyplot(fig)
            plt.close()
        else:
            st.info("No feeding records yet.")

    # Insights
    st.divider()
    st.subheader("Today's insights")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"💤 **Sleep:** {sleep_data.get('insight', 'No data')}")
    with col2:
        st.info(f"🍼 **Feeding:** {feeding_data.get('insight', 'No data')}")


# ══════════════════════════════════════════════════════════════
# Page 3: Log Event
# ══════════════════════════════════════════════════════════════
elif page == "📝 Log Event":
    st.title("📝 Log an Event")
    st.caption("Record feeding, sleep, growth, or milestones.")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["🍼 Feeding", "💤 Sleep", "📏 Growth", "⭐ Milestone"]
    )

    with tab1:
        st.subheader("Log feeding")
        food    = st.text_input("Food", placeholder="e.g. banana, breast milk")
        amount  = st.number_input("Amount (ml)", min_value=0, max_value=500,
                                   value=100, step=10)
        notes   = st.text_area("Notes (optional)")
        if st.button("Save feeding", type="primary"):
            if food:
                add_event("feeding",
                          {"food": food, "amount_ml": amount},
                          notes=notes or None)
                st.success(f"✓ Logged: {food} ({amount}ml)")
            else:
                st.warning("Please enter a food name.")

    with tab2:
        st.subheader("Log sleep")
        duration = st.slider("Duration (hours)", 0.0, 16.0, 10.0, 0.5)
        wakings  = st.number_input("Night wakings", min_value=0,
                                    max_value=20, value=0)
        notes    = st.text_area("Notes (optional)", key="sleep_notes")
        if st.button("Save sleep", type="primary"):
            add_event("sleep",
                      {"duration_hours": duration,
                       "night_wakings": wakings},
                      notes=notes or None)
            st.success(f"✓ Logged: {duration}hrs, {wakings} wakings")

    with tab3:
        st.subheader("Log growth")
        weight = st.number_input("Weight (kg)", min_value=0.0,
                                  max_value=30.0, value=7.0, step=0.1)
        height = st.number_input("Height (cm)", min_value=0.0,
                                  max_value=120.0, value=68.0, step=0.5)
        if st.button("Save growth", type="primary"):
            add_event("growth",
                      {"weight_kg": weight, "height_cm": height})
            st.success(f"✓ Logged: {weight}kg, {height}cm")

    with tab4:
        st.subheader("Log milestone")
        milestone  = st.text_input("Milestone",
                                    placeholder="e.g. first steps, said mama")
        age_months = st.number_input("Age (months)", min_value=0,
                                      max_value=36, value=11)
        if st.button("Save milestone", type="primary"):
            if milestone:
                add_event("milestone",
                          {"milestone": milestone,
                           "age_months": age_months})
                st.success(f"✓ Logged: {milestone} at {age_months} months")
            else:
                st.warning("Please describe the milestone.")


# ══════════════════════════════════════════════════════════════
# Page 4: Timeline
# ══════════════════════════════════════════════════════════════
elif page == "📅 Timeline":
    st.title("📅 Event Timeline")

    event_type = st.selectbox(
        "Filter by type",
        ["All", "feeding", "sleep", "growth", "milestone", "note"]
    )
    limit = st.slider("Number of records", 10, 100, 20)

    events = get_events(
        event_type=None if event_type == "All" else event_type,
        limit=limit
    )

    if not events:
        st.info("No events found.")
    else:
        for e in events:
            icon = {"feeding": "🍼", "sleep": "💤", "growth": "📏",
                    "milestone": "⭐", "note": "📝"}.get(e["event_type"], "📌")
            with st.expander(
                f"{icon} {e['event_type'].upper()} — {e['date'][:10]}"
            ):
                st.json(e["data"])
                if e.get("notes"):
                    st.caption(f"Notes: {e['notes']}")