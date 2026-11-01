"""Extra landing-page sections: intro + Bloch sphere, three steps, pathway overview, footer.

Everything shown to visitors is in the constants at the top of this file; edit
any line marked ``# EDIT ME``. Lesson counts, times and titles are read from
app.py's CURRICULUM, so they stay correct when lessons change.

Styling for these sections lives in ui/theme.py (look for "landing sections").
"""

from __future__ import annotations

import html
from collections.abc import Sequence
from typing import Any

import streamlit as st

from ui.navigation import start_pathway

# ---------------------------------------------------------------------------
# Copy shown on the landing page
# ---------------------------------------------------------------------------

PRODUCT_NAME = "Qubit Path AI"  # EDIT ME (the hero wordmark in app.py says "QubitPath")
GITHUB_URL = "https://github.com/Suman-Poola/QubitPath"  # EDIT ME if the repo moves
AUTHOR_CREDIT = "Suman"  # EDIT ME (e.g. full name)
MENTOR_CREDIT = "Qingyang"  # EDIT ME (e.g. full name / title)

ABOUT_TEXT = (  # EDIT ME
    f"{PRODUCT_NAME} takes students from “what is a bit?” all the way to quantum error "
    "correction. Pick the pathway that fits your age and experience, work through short lessons "
    "with hands-on activities, run real circuits on a Qiskit simulator, and ask Professor Qubit, "
    "the built-in AI tutor, whenever something doesn’t click."
)

BLOCH_CAPTION = (  # EDIT ME
    "This is a Bloch sphere: how physicists picture one qubit. The top is |0⟩, the bottom "
    "is |1⟩, and anywhere in between is a superposition."
)

# (icon, title, text). "{levels}" is replaced with the level names, e.g. "Elementary, Proficient, or Erudite".
STEPS = [  # EDIT ME
    ("\U0001F9ED", "Choose your level", "Pick {levels}. You can switch pathways any time from the sidebar."),
    ("\U0001F3AC", "Learn", "Open a lesson for its goals, notes and a hands-on activity, then mark it complete to earn XP."),
    ("\U0001F916", "Practice & ask the AI", "Run experiments in the lab, take quick quizzes, and ask Professor Qubit when you get stuck."),
]

# One or two sentences per level. A level missing here falls back to its LEVEL_META blurb.
PATHWAY_COVERS = {  # EDIT ME
    "Elementary": "Bits, magic spinning coins, flip-and-maybe switches, and partner coins: big quantum ideas told through stories and games, no math needed.",
    "Proficient": "Bits vs. qubits, superposition as percent chances, your first circuit diagram, and entanglement, with the real vocabulary.",
    "Erudite": "Three tracks, from your first Qiskit program through entanglement and algorithms to VQE, QAOA, and error correction.",
}

FOOTER_NOTE = "Alpha preview · An educational prototype. Feedback is very welcome!"  # EDIT ME


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------

def _spacer(rem: float) -> None:
    st.markdown(f"<div style='height:{rem}rem'></div>", unsafe_allow_html=True)


def bloch_sphere() -> str:
    """A Bloch sphere drawn in SVG: shell, equator, |0>/|1> poles and one state vector."""
    return (
        f'<div class="qp-bloch"><svg viewBox="0 0 240 240" role="img" aria-label="{html.escape(BLOCH_CAPTION)}">'
        '<circle cx="120" cy="120" r="84" class="qp-bloch-shell"/>'
        '<path d="M36,120 A84,24 0 0,1 204,120" class="qp-bloch-back"/>'
        '<line x1="120" y1="36" x2="120" y2="204" class="qp-bloch-axis"/>'
        '<path d="M36,120 A84,24 0 0,0 204,120" class="qp-bloch-front"/>'
        '<line x1="120" y1="120" x2="168" y2="134" class="qp-bloch-drop"/>'
        '<line x1="168" y1="62" x2="168" y2="134" class="qp-bloch-drop"/>'
        '<circle cx="120" cy="36" r="3.5" class="qp-bloch-pole"/>'
        '<circle cx="120" cy="204" r="3.5" class="qp-bloch-pole"/>'
        '<line x1="120" y1="120" x2="168" y2="62" class="qp-bloch-state"/>'
        '<circle cx="168" cy="62" r="13" class="qp-bloch-halo"/>'
        '<circle cx="168" cy="62" r="7" class="qp-bloch-tip"/>'
        '<text x="120" y="24" class="qp-bloch-label">|0⟩</text>'
        '<text x="120" y="228" class="qp-bloch-label">|1⟩</text>'
        '<text x="192" y="56" class="qp-bloch-label">|ψ⟩</text>'
        f'</svg><p class="qp-bloch-caption">{BLOCH_CAPTION}</p></div>'
    )


def render_about_section(levels: Sequence[str], curriculum: dict[str, list[dict[str, Any]]]) -> None:
    """'What is Qubit Path AI?' intro, a few stats, and the Bloch-sphere figure."""
    lesson_count = sum(len(curriculum[level]) for level in levels)
    stats = [(str(len(levels)), "learning pathways"), (str(lesson_count), "lessons"), ("1", "AI tutor")]

    _spacer(2.4)
    text_col, figure_col = st.columns([1.5, 1], gap="large", vertical_alignment="center")
    with text_col:
        st.markdown(f"### What is {PRODUCT_NAME}?")
        st.markdown(f'<p class="qp-section-lead">{ABOUT_TEXT}</p>', unsafe_allow_html=True)
        st.markdown(
            '<div class="qp-stats">'
            + "".join(f'<div class="qp-stat"><b>{n}</b><span>{label}</span></div>' for n, label in stats)
            + "</div>",
            unsafe_allow_html=True,
        )
    with figure_col:
        st.markdown(bloch_sphere(), unsafe_allow_html=True)


def _duration(minutes: int) -> str:
    return f"{minutes} min" if minutes < 120 else f"about {round(minutes / 60)} hrs"


def render_get_started_section(
    levels: Sequence[str],
    level_meta: dict[str, dict[str, Any]],
    curriculum: dict[str, list[dict[str, Any]]],
) -> None:
    """Three-step 'how it works' row, then one card per pathway with a Begin button."""
    level_list = ", ".join(levels[:-1]) + f", or {levels[-1]}" if len(levels) > 1 else levels[0]

    _spacer(2.4)
    st.markdown("### Get started in three steps")
    for col, (number, (icon, title, text)) in zip(st.columns(len(STEPS)), enumerate(STEPS, start=1)):
        with col:
            st.markdown(
                f'<div class="qp-step"><span class="qp-step-num">{number}</span><span class="qp-step-icon">{icon}</span>'
                f"<h4>{title}</h4><p>{text.format(levels=level_list)}</p></div>",
                unsafe_allow_html=True,
            )

    _spacer(2.4)
    st.markdown("### Inside each pathway")
    for col, level in zip(st.columns(len(levels)), levels):
        meta, lessons = level_meta[level], curriculum[level]
        titles = "".join(f"<li>{html.escape(lesson['title'])}</li>" for lesson in lessons[:3])
        if len(lessons) > 3:
            titles += f'<li class="qp-inside-more">+ {len(lessons) - 3} more</li>'
        with col:
            st.markdown(
                f'<div class="qp-pathcard qp-inside"><span class="qp-path-icon">{meta["icon"]}</span>'
                f'<h3>{level}</h3><p class="qp-path-age">{meta["age_range"]}</p>'
                f'<p>{PATHWAY_COVERS.get(level, meta["blurb"])}</p>'
                f'<p class="qp-inside-meta">{len(lessons)} lessons · {_duration(sum(l["duration"] for l in lessons))}</p>'
                f"<ul>{titles}</ul></div>",
                unsafe_allow_html=True,
            )
            st.button(
                f"Begin {level}",
                key=f"landing_begin_{level.lower()}",
                on_click=start_pathway,
                args=(level,),
                type="primary",
                width="stretch",
            )


def render_footer() -> None:
    st.markdown(
        '<div class="qp-footer">'
        f'<p class="qp-footer-brand">⚛ {PRODUCT_NAME}</p>'
        f"<p>Created by <b>{AUTHOR_CREDIT}</b> (author) · Mentored by <b>{MENTOR_CREDIT}</b> (mentor)</p>"
        f'<p><a href="{GITHUB_URL}" target="_blank" rel="noopener noreferrer">View the project on GitHub</a></p>'
        f'<p class="qp-footer-note">{FOOTER_NOTE}</p>'
        "</div>",
        unsafe_allow_html=True,
    )
