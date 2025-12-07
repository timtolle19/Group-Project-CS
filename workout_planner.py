# workout_calendar.py
# This Streamlit app shows a 3-month workout calendar (current month + previous 2).
# Users can click a day in the calendar, and then log the workout duration and type.
# Data is stored in Streamlit's session_state, so it persists while the app is running.
import calendar          # Standard library: used to generate month layouts (weeks/days).
import datetime          # Standard library: used to handle dates (today, formatting, etc.).
import streamlit as st   # Third-party library: used to build the web UI.
from streamlit import session_state as state  # Short alias for st.session_state.
# Primary theme color for some UI elements (e.g., "Selected" text).
PRIMARY_COLOR = "#007A3D"
# Weekday names + matching Python datetime.weekday() indices.
# datetime.date.weekday() returns:
#   Monday=0, Tuesday=1, ..., Sunday=6
WEEKDAYS = [
    ("Monday", 0),
    ("Tuesday", 1),
    ("Wednesday", 2),
    ("Thursday", 3),
    ("Friday", 4),
    ("Saturday", 5),
    ("Sunday", 6),
]
# Workout categories that the user can choose from in the dropdown.
WORKOUT_TYPES = [
    "Push day",
    "Pull day",
    "Leg day",
    "Full body",
    "Lower body",
    "Cardio",
]
def _init_state():
    """
    Initialize Streamlit session_state keys used by the app.
    Streamlit's session_state is like a small in-memory database that
    persists across user interactions (button clicks, etc.).
    This function ensures that required keys exist with default values.
    """
    # If this is the first time the app runs, "workout_logs" won't exist yet.
    # We create it and initialize it as an empty dict.
    # It will store workout data keyed by date string "YYYY-MM-DD", e.g.:
    #  state.workout_logs["2025-12-02"] = {"minutes": 45, "type": "Push day"}
    if "workout_logs" not in state:
        state.workout_logs = {}
    # Store the currently selected date in the calendar.
    # If it doesn't exist yet, initialize it to today's date.
    if "selected_date" not in state:
        state.selected_date = datetime.date.today()
def _render_month(year: int, month: int):
    """
    Render a single month of the calendar, with clickable days.
    Args:
        year (int): Year of the calendar (e.g. 2025).
        month (int): Month of the calendar (1–12).
    Behavior:
        - Displays a month header (e.g. "December 2025").
        - Shows weekday names in the header row (Mo, Tu, ...).
        - For each day in the month:
            * Shows a button with the day number (1..31).
            * Clicking the button sets that day as the "selected_date".
            * If a workout is logged on that day, shows a small summary underneath.
    """
    # Create a Calendar instance that starts the week on Monday (0).
    # This matches our WEEKDAYS definition.
    cal = calendar.Calendar(firstweekday=0)
    # Get the month name (e.g., "December") from the calendar module.
    month_name = calendar.month_name[month]
    # Display month heading in Streamlit (level 4 markdown).
    st.markdown(f"#### {month_name} {year}")
    # Display the weekday headers ("Mo", "Tu", etc.) in 7 equal columns.
    header_cols = st.columns(7)
    for col, (name, _) in zip(header_cols, WEEKDAYS):
        # Use minimal HTML styling to center and style the weekday labels.
        col.markdown(
            f"<div style='text-align:center; font-size:13px; "
            f"color:#555; font-weight:600;'>{name[:2]}</div>",
            unsafe_allow_html=True,
        )
    # Iterate week by week for the given month.
    # cal.monthdatescalendar(year, month) returns a list of weeks,
    # and each week is a list of 7 datetime.date objects.
    for week in cal.monthdatescalendar(year, month):
        # Create a new row of 7 columns for each week.
        cols = st.columns(7)
        # Combine each column with its corresponding date object.
        for col, date_obj in zip(cols, week):
            # Some of the dates returned can be from previous or next month
            # to fill out the full weeks. We hide those cells.
            if date_obj.month != month:
                with col:
                    # Empty placeholder so the grid alignment remains intact.
                    st.write("")
                # Move on to the next date.
                continue
            # Convert the date to ISO format string "YYYY-MM-DD".
            date_str = date_obj.isoformat()
            # Try to retrieve a previously saved workout log for this day.
            log = state.workout_logs.get(date_str)
            # Check if this day is currently selected.
            is_selected = (state.selected_date == date_obj)
            # Day number as string (e.g., "1", "2", ..., "31").
            day_label = str(date_obj.day)
            # All UI elements for this day go inside this column.
            with col:
                # If this day is the selected one, show a little "Selected" marker above.
                if is_selected:
                    st.markdown(
                        f"<div style='text-align:center; font-size:11px; "
                        f"color:{PRIMARY_COLOR};'>Selected</div>",
                        unsafe_allow_html=True,
                    )
                # Main button: shows the day number.
                # Clicking this button will update the session_state.selected_date.
                if st.button(
                    day_label,
                    key=f"day-btn-{date_str}",  # unique key per day
                    use_container_width=True,  # button fills the column width
                ):
                    # Update currently selected day in the global session state.
                    state.selected_date = date_obj
                # If we have a workout log for this day, show a small summary below the button.
                if log:
                    minutes = log.get("minutes")
                    wtype = log.get("type")
                    summary = f"{minutes} min – {wtype}"
                    st.caption(summary)


def main():
    """
    Main function that builds the entire Streamlit UI.
    It:
      1. Initializes state.
      2. Shows page title and instructions.
      3. Renders calendars for current month + previous 2 months.
      4. Shows a panel to log / edit a workout for the selected day.
      5. Optionally lists up to 10 most recent logged workouts.
    """
    # 1. Make sure session_state contains all required keys.
    _init_state()

    # 2. Page title and description.
    st.subheader("Workout log calendar")
    st.caption(
        "Log your past workouts in a calendar view. "
        "Click on a date to add or edit the workout for that day."
    )
    st.info(
        "You always see the current month plus the previous two months (3 months of past workouts)."
    )
    # Visual separator line.
    st.divider()

    # 3. Determine which months to show.
    # Get today's date (e.g., 2025-12-07).
    today = datetime.date.today()
    # Convert today's year and month into a single linear "month index".
    # Example: January of year Y => Y * 12 + 0, February => Y * 12 + 1, etc.
    # This is a handy way to go backwards or forwards by a fixed number of months.
    base_index = today.year * 12 + (today.month - 1)
    # We want to show exactly 3 months: current month + previous 2.
    months_to_show = 3
    # Loop over 0,1,2 to show 3 months in total.
    for offset in range(months_to_show):
        # For offset=0: current month, offset=1: previous month, offset=2: two months ago.
        idx = base_index - offset
        # Reconstruct year and month from the linear index.
        year = idx // 12                # integer division -> year
        month = (idx % 12) + 1          # remainder -> month in range [1..12]
        # Render the calendar for that (year, month).
        _render_month(year, month)
        # Add some vertical space between months.
        st.write("")
    # Divider between the calendars and the logging panel.
    st.divider()

    # 4. Workout logging panel for the selected date.
    # Get the currently selected date object (datetime.date).
    selected_date: datetime.date = state.selected_date
    # Create a human-readable string like "Monday, 01 December 2025".
    selected_str = selected_date.strftime("%A, %d %B %Y")
    # Display a header reflecting which date the user is logging for.
    st.markdown(f"### Log workout for {selected_str}")
    # This is the key under which we'll store the log in session_state.workout_logs.
    date_key = selected_date.isoformat()  # "YYYY-MM-DD"
    # Try to load an existing log for this date; default to {} if none is found.
    existing_log = state.workout_logs.get(date_key, {})
    # Pre-fill the minutes input with existing value if present, otherwise use 0.
    existing_minutes = existing_log.get("minutes", 0)
    # Pre-fill the workout type with existing value if present; otherwise first option.
    existing_type = existing_log.get("type", WORKOUT_TYPES[0])
    # Create two equal columns:
    #   left: numerical input for minutes,
    #   right: selectbox for workout type.
    col_minutes, col_type = st.columns([1, 1])

    # Minutes input column
    with col_minutes:
        # Number input for workout length.
        minutes = st.number_input(
            "Workout length (minutes)",
            min_value=0,           # no negative minutes
            max_value=600,         # upper limit (10 hours)
            step=5,                # step size when using the arrows
            value=int(existing_minutes),  # default value
            help="How long did you train on this day?",
            key="minutes_input",   # unique key for Streamlit
        )

    # Workout type selectbox column
    with col_type:
        # Just in case the list of WORKOUT_TYPES changes in the future and
        # an old saved type no longer exists, reset to first item.
        if existing_type not in WORKOUT_TYPES:
            existing_type = WORKOUT_TYPES[0]
        # Dropdown selector for workout category.
        workout_type = st.selectbox(
            "Workout type",
            options=WORKOUT_TYPES,                      # list of possible types
            index=WORKOUT_TYPES.index(existing_type),   # preselect existing type
            help="What kind of workout did you do?",
            key="workout_type_select",                  # unique key
        )

    # 5. Save button: when clicked, we store/update the workout log for that date.
    # This button will run its callback logic whenever clicked.
    if st.button("Save workout", type="primary"):
        # Create/update the entry in the workout_logs dictionary
        # under the key for this specific date.
        state.workout_logs[date_key] = {
            "minutes": int(minutes),   # ensure minutes is an int
            "type": workout_type,      # selected workout type
        }
        # Give user visual confirmation that their workout was saved.
        st.success(f"Saved workout for {selected_str}.")

    # 6. Optional: show up to 10 most recent logged workouts as a simple list.
    # Only show this section if there is at least one log.
    if state.workout_logs:
        st.markdown("#### Recent logged workouts")
        # state.workout_logs is a dict with keys like "YYYY-MM-DD".
        # sorted(..., reverse=True) sorts by key descending, so newest dates come first.
        items = sorted(state.workout_logs.items(), key=lambda x: x[0], reverse=True)
        # Iterate over the first 10 items to show a short history.
        for d_str, log in items[:10]:
            # Convert the date string back into a datetime.date object.
            d_obj = datetime.date.fromisoformat(d_str)
            # Format the date for display, e.g. "07 Dec 2025 (Sun)".
            label = d_obj.strftime("%d %b %Y (%a)")
            # Write a bullet point with date, minutes, and type.
            st.write(f"- **{label}**: {log['minutes']} min – {log['type']}")
