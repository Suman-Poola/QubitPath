"""Hands-on activities: the interactive module under every lesson's walkthrough.

``render_activity(lesson)`` draws the activity for a CURRICULUM entry. The
activities themselves live in ui/activity_content.py; their interactive parts
in ui/activity_widgets.py. A part counts as done once the learner has completed
it on any run (so re-running an experiment later never un-completes it), and
the activity is done when every part is. Finishing an activity earns XP once.

Every widget key starts with ``act_<lesson id>_`` because the lesson page
renders one lesson per level tab in the same run, and Streamlit keys must be unique.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from ui.activity_content import ACTIVITIES
from ui.activity_widgets import KINDS, WIDGETS

ACTIVITY_XP = 20


def activity_done(lesson_id: str) -> bool:
    return bool(st.session_state.get(f"act_{lesson_id}_done"))


def _renderer(part: dict[str, Any]):
    return WIDGETS[part["name"]] if part["kind"] == "widget" else KINDS[part["kind"]]


def render_activity(lesson: dict[str, Any]) -> None:
    """The hands-on activity for ``lesson`` (a CURRICULUM entry)."""
    lesson_id = lesson["id"]
    activity = ACTIVITIES.get(lesson_id)
    if not activity:
        return
    parts = activity["parts"]
    part_done = [f"act_{lesson_id}_{i}_done" for i in range(len(parts))]

    with st.container(border=True):
        st.markdown(f"#### \U0001F6E0️ Hands-on activity: {activity['title']}")
        if lesson.get("activity"):
            st.caption(lesson["activity"])
        for i, part in enumerate(parts):
            # The check mark reflects earlier runs. (Filling an st.empty() placeholder after the part instead
            # would collapse the heading during every rerun and shift the widgets below it under the cursor.)
            label = f"Part {i + 1} of {len(parts)}: {part['title']}" if len(parts) > 1 else part["title"]
            st.markdown(f"##### {'✅ ' if st.session_state.get(part_done[i]) else ''}{label}")
            if part.get("prompt"):
                st.markdown(part["prompt"])
            if _renderer(part)(f"act_{lesson_id}_{i}", part):
                st.session_state[part_done[i]] = True

        if all(st.session_state.get(k) for k in part_done) and not activity_done(lesson_id):
            st.session_state[f"act_{lesson_id}_done"] = True
            st.session_state["xp"] = st.session_state.get("xp", 0) + ACTIVITY_XP
            st.toast(f"Activity complete! +{ACTIVITY_XP} XP", icon="\U0001F389")
            if activity.get("kid"):
                st.balloons()
        if activity_done(lesson_id):
            st.success(f"Activity complete! (+{ACTIVITY_XP} XP) Mark the lesson complete when you're ready.")
