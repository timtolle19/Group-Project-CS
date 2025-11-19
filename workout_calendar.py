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


def _init_state():
    """Ensure default values in session_state for the calendar."""
    if "calendar_training_days" not in state:
        # default training days: Monday / Wednesday / Friday
        state.calendar_training_days = [0, 2, 4]
    if "calendar_start_date" not in state:
        state.calendar_start_date = datetime.date.today()


def _render_month(year: int, month: int, training_days: list[int]):
    """Render a simple month grid with highlighted training days."""
    cal = calendar.Calendar(firstweekday=0)  # Monday

    month_name = calendar.month_name[month]
    st.markdown(f"#### {month_name} {year}")

    # build HTML table
    html = [
        "<table style='border-collapse:collapse; width:100%;'>",
        "<thead><tr>",
    ]
    for name, _idx in WEEKDAYS:
        html.append(
            f"<th style='padding:6px; border-bottom:1px solid #ddd; "
            f"text-align:center; font-size:13px; color:#555;'>{name[:2]}</th>"
        )
    html.append("</tr></thead><tbody>")

    for week in cal.monthdayscalendar(year, month):
        html.append("<tr>")
        for i, day in enumerate(week):
            if day == 0:
                html.append(
                    "<td style='padding:8px; border-bottom:1px solid #eee;'></td>"
                )
                continue

            date_obj = datetime.date(year, month, day)
            weekday = date_obj.weekday()
            is_training = weekday in training_days

            if is_training:
                bg = "#E6F4EA"
                border = f"1px solid {PRIMARY_COLOR}"
                label = "<div style='font-size:11px;'>Training</div>"
            else:
                bg = "#ffffff"
                border = "1px solid #f0f0f0"
                label = ""

            cell_html = (
                f"<td style='padding:6px; border:{border}; background:{bg}; "
                "text-align:center; font-size:13px;'>"
                f"<div style='font-weight:600; color:{PRIMARY_COLOR};'>{day}</div>"
                f"{label}"
                "</td>"
            )
            html.append(cell_html)
        html.append("</tr>")
    html.append("</tbody></table>")

    st.markdown("".join(html), unsafe_allow_html=True)


def main():
    """Render the training calendar tab (used by app.py)."""
    _init_state()

    st.subheader("Training calendar")
    st.caption(
        "See your training days in a simple calendar view. "
        "You can adjust which weekdays you normally train."
    )

    col_left, col_right = st.columns([1, 1])

    # ----- left: settings -----
    with col_left:
        start_date = st.date_input(
            "Start date",
            value=state.calendar_start_date,
            help="The calendar starts from the month of this date.",
        )
        state.calendar_start_date = start_date

        day_labels = [name for name, _idx in WEEKDAYS]
        current_indices = state.calendar_training_days
        current_labels = [name for name, idx in WEEKDAYS if idx in current_indices]

        selected_labels = st.multiselect(
            "Weekly training days",
            options=day_labels,
            default=current_labels,
            help="These days will be highlighted as training days.",
        )

        training_days = [idx for name, idx in WEEKDAYS if name in selected_labels]
        state.calendar_training_days = training_days

        st.info(
            "Tip: Use this overview together with the **Workout builder** tab "
            "to decide which sessions you do on each training day."
        )

    # ----- right: how many months -----
    with col_right:
        months_to_show = st.selectbox(
            "Show calendar for",
            options=[1, 2, 3],
            format_func=lambda x: f"{x} month{'s' if x > 1 else ''}",
            index=1,
        )

    st.divider()

    # ----- render months -----
    year = state.calendar_start_date.year
    month = state.calendar_start_date.month

    for offset in range(months_to_show):
        # roll over year/month
        m = ((month - 1 + offset) % 12) + 1
        y = year + ((month - 1 + offset) // 12)
        _render_month(y, m, state.calendar_training_days)
        st.write("")  # spacing between months
