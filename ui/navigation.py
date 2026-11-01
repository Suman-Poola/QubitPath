"""Routing helpers shared by the landing page and the course pages.

app.py routes with ``st.session_state["page"]`` (the sidebar radio's key) and
keeps the chosen level in ``st.session_state["learner_level_select"]`` (the
sidebar pathway selectbox's key). These helpers only write those two keys, so
they work alongside the existing sidebar navigation instead of replacing it.

Use ``start_pathway`` / ``back_to_landing`` as ``on_click`` callbacks. Streamlit
runs callbacks before the script reruns, which is the only point where a
widget's session-state value (like the sidebar radio's) may be changed.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

import streamlit as st

PAGE_KEY = "page"
LEVEL_KEY = "learner_level_select"
LANDING_PAGE = "Welcome"
# Where "Start <Level>" / "Begin <Level>" lands: the lesson library, opened on that level's tab.
PATHWAY_PAGE = "Recorded Learning"

_NAV_PILLS_KEY = "course_nav_pills"


def start_pathway(level: str, page: str = PATHWAY_PAGE) -> None:
    """Select ``level`` and open its course pathway."""
    st.session_state[LEVEL_KEY] = level
    st.session_state[PAGE_KEY] = page


def back_to_landing() -> None:
    st.session_state[PAGE_KEY] = LANDING_PAGE


def _follow_nav_pills() -> None:
    choice = st.session_state.get(_NAV_PILLS_KEY)
    if choice:
        st.session_state[PAGE_KEY] = choice


def render_course_nav(
    pages: Sequence[str],
    current_page: str,
    format_page: Callable[[str], str],
    pathway_label: str,
) -> None:
    """Top bar for course pages: back to the landing page, current pathway, and page links.

    The page links mirror the sidebar radio so every page is reachable even
    while the sidebar is collapsed (the default on phones).
    """
    # Mirror the sidebar's choice; safe because the pills widget isn't created yet this run.
    st.session_state[_NAV_PILLS_KEY] = current_page

    back_col, label_col = st.columns([1, 3], vertical_alignment="center")
    with back_col:
        st.button("← Back to landing", key="nav_back_to_landing", on_click=back_to_landing, width="stretch")
    with label_col:
        st.markdown(f'<span class="qp-pill">{pathway_label}</span>', unsafe_allow_html=True)
    st.pills(
        "Go to page",
        pages,
        key=_NAV_PILLS_KEY,
        format_func=format_page,
        required=True,
        on_change=_follow_nav_pills,
        label_visibility="collapsed",
    )
