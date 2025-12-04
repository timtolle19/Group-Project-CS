# workout_calendar.py

import calendar
import datetime

import streamlit as st
from streamlit import session_state as state

PRIMARY_COLOR = "#007A3D"


WEEKDAYS = [
    ("Monday", 0),
    ("Tuesday", 1),
    ("Wednesday", 2),
    ("Thursday", 3),
    ("Friday", 4),
    ("Saturday", 5),
    ("Sunday", 6),
]


WORKOUT_TYPES = [
    "Push day",
    "Pull day",
    "Leg day",
    "Full body",
    "Lower body",
    "Cardio",
]


def _init_state():
    """Ensure default values in session_state for the workout calendar."""
    if "workout_logs" not in state:
        # dict: { "YYYY-MM-DD": {"minutes": int, "type": str} }
        state.workout_logs = {}

    if "selected_date" not in state:
        state.selected_date = datetime.date.today()


def _render_month(year: int, month: int):
    """
    Render a simple month grid for logging past workouts.

    Each day is a button; clicking it sets `state.selected_date`.
    If a workout log exists for that date, a small summary is shown.
    """
    cal = calendar.Calendar(firstweekday=0)  # Monday

    month_name = calendar.month_name[month]
    st.markdown(f"#### {month_name} {year}")

    # weekday header
    header_cols = st.columns(7)
    for col, (name, _idx) in zip(header_cols, WEEKDAYS):
        col.markdown(
            f"<div style='text-align:center; font-size:13px; color:#555; font-weight:600;'>{name[:2]}</div>",
            unsafe_allow_html=True,
        )

    # weeks
    for week in cal.monthdatescalendar(year, month):
        cols = st.columns(7)
        for col, date_obj in zip(cols, week):
            # Only show days belonging to this month
            if date_obj.month != month:
                with col:
                    st.write("")  # empty cell
                continue

            date_str = date_obj.isoformat()
            log = state.workout_logs.get(date_str)
            is_selected = (state.selected_date == date_obj)

            # Build label & simple style indicator
            day_label = str(date_obj.day)

            with col:
                # Slight visual hint for selected date (just text around button)
                if is_selected:
                    st.markdown(
                        f"<div style='text-align:center; font-size:11px; color:{PRIMARY_COLOR};'>Selected</div>",
                        unsafe_allow_html=True,
                    )

                if st.button(
                    day_label,
                    key=f"day-btn-{date_str}",
                    use_container_width=True,
                ):
                    state.selected_date = date_obj

                # Show a brief log summary under the button if exists
                if log:
                    minutes = log.get("minutes")
                    wtype = log.get("type")
                    summary = f"{minutes} min – {wtype}"
                    st.caption(summary)


def main():
    """Render the workout log calendar tab (used by app.py)."""
    _init_state()

    st.subheader("Workout log calendar")
    st.caption(
        "Log your past workouts in a calendar view. "
        "Click on a date to add or edit the workout for that day."
    )

    st.info(
        "You always see the current month plus the previous two months (3 months of past workouts)."
    )

    st.divider()

    # ----- render the last 3 months (current month + previous 2) -----
    today = datetime.date.today()
    base_index = today.year * 12 + (today.month - 1)  # e.g. 2025-12 -> 2025*12 + 11

    months_to_show = 3  # always 3 months into the past (including current month)

    for offset in range(months_to_show):
        idx = base_index - offset
        year = idx // 12
        month = (idx % 12) + 1
        _render_month(year, month)
        st.write("")  # spacing between months

    st.divider()

    # ----- detail panel for selected date -----
    selected_date: datetime.date = state.selected_date
    selected_str = selected_date.strftime("%A, %d %B %Y")
    st.markdown(f"### Log workout for {selected_str}")

    date_key = selected_date.isoformat()
    existing_log = state.workout_logs.get(date_key, {})

    # Pre-fill with existing values if available
    existing_minutes = existing_log.get("minutes", 0)
    existing_type = existing_log.get("type", WORKOUT_TYPES[0])

    col_minutes, col_type = st.columns([1, 1])

    with col_minutes:
        minutes = st.number_input(
            "Workout length (minutes)",
            min_value=0,
            max_value=600,
            step=5,
            value=int(existing_minutes),
            help="How long did you train on this day?",
            key="minutes_input",
        )

    with col_type:
        # ensure existing_type is in WORKOUT_TYPES
        if existing_type not in WORKOUT_TYPES:
            existing_type = WORKOUT_TYPES[0]

        workout_type = st.selectbox(
            "Workout type",
            options=WORKOUT_TYPES,
            index=WORKOUT_TYPES.index(existing_type),
            help="What kind of workout did you do?",
            key="workout_type_select",
        )

    if st.button("Save workout", type="primary"):
        state.workout_logs[date_key] = {
            "minutes": int(minutes),
            "type": workout_type,
        }
        st.success(f"Saved workout for {selected_str}.")

    # Optionally show the last few logged days as a quick summary
    if state.workout_logs:
        st.markdown("#### Recent logged workouts")
        # sort by date, descending
        items = sorted(state.workout_logs.items(), key=lambda x: x[0], reverse=True)
        for d_str, log in items[:10]:
            d_obj = datetime.date.fromisoformat(d_str)
            label = d_obj.strftime("%d %b %Y (%a)")
            st.write(f"- **{label}**: {log['minutes']} min – {log['type']}")
