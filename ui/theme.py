"""Shared dark-blue theme for every QubitPath page.

The palette comes from the landing page (hero ink, path cards, wordmark) and
lives in two places that must stay in sync:

* ``.streamlit/config.toml`` themes Streamlit's own widgets (inputs, tabs,
  tables, charts, alerts).
* ``PALETTE`` below themes QubitPath's custom HTML (cards, page headers, pills).

app.py still injects ``BASE_CSS`` (fonts + the original light-page rules) and
``inject_level_theme()`` (the per-level accent). ``apply_theme()`` re-skins the
light parts of BASE_CSS for the dark background. Its selectors are prefixed
with ``body`` so each one outranks the BASE_CSS rule it replaces by exactly one
element, whatever order Streamlit inserts the two <style> blocks in, while
BASE_CSS's more specific class rules (e.g. ``.qp-pagehead h1``) still win.
"""

from __future__ import annotations

import streamlit as st

# Contrast ratios are WCAG 2.x against the page background "bg" unless noted;
# body text needs at least 4.5:1.
PALETTE: dict[str, str] = {
    "bg": "#0E1330",  # page background = landing hero ink
    "surface": "#151A3F",  # cards = landing path cards
    "surface-2": "#1A2050",  # inputs (= secondaryBackgroundColor in config.toml)
    "border": "rgba(255, 255, 255, 0.09)",
    "text": "#F4F3FF",  # 16.6:1 (14.0:1 on surface-2)
    "text-soft": "#C9C8F0",  # 11.3:1 (hero subtitle)
    "text-muted": "#A6A9D6",  # 8.0:1 (6.8:1 on surface-2); the old #6B7094 was 3.8:1
    "primary": "#8B7FF5",  # brand violet #7C6FF2 lightened: 4.7:1+ on every surface (was 4.0:1)
    "link": "#1FBFB2",  # cyan wordmark, 7.9:1
}
DEFAULT_ACCENT = "#6F4BF2"  # same as --qp-accent in BASE_CSS (used on the landing page)
_DARK_TEXT = "#0E1330"
_LIGHT_TEXT = "#FFFFFF"


def _relative_luminance(hex_color: str) -> float:
    channels = []
    for i in (1, 3, 5):
        c = int(hex_color[i:i + 2], 16) / 255
        channels.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = channels
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(color_a: str, color_b: str) -> float:
    """WCAG contrast ratio between two ``#RRGGBB`` colors (1.0 to 21.0)."""
    hi, lo = sorted((_relative_luminance(color_a), _relative_luminance(color_b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def readable_text_on(background: str) -> str:
    """Dark ink or white, whichever reads better on ``background``.

    Coral (#FF8A65) and cyan (#1FBFB2) only reach ~2.3:1 with white text but
    ~7.9:1 with dark ink; violet (#6F4BF2) is the other way round (5.3:1 white).
    """
    if contrast_ratio(_DARK_TEXT, background) >= contrast_ratio(_LIGHT_TEXT, background):
        return _DARK_TEXT
    return _LIGHT_TEXT


_DARK_CSS = """
/* ---- page + text ---- */
body .stApp { background: radial-gradient(circle at 12% 0%, var(--qp-surface-2) 0%, var(--qp-bg) 55%); }
body h1, body h2, body h3, body .qp-display { color: var(--qp-text); }
body p, body li, body label, body span { color: var(--qp-text); }
body .qp-muted,
body [data-testid="stCaptionContainer"],
body [data-testid="stCaptionContainer"] :is(p, span, li) { color: var(--qp-text-muted); }
/* Streamlit also fades captions to 60% opacity, which drops muted text to ~3.7:1. */
body [data-testid="stMain"] [data-testid="stCaptionContainer"] { opacity: 1; }

/* ---- surfaces BASE_CSS painted white ---- */
body .qp-card {
  background: var(--qp-surface);
  border: 1px solid var(--qp-border); border-top: 3px solid var(--qp-accent);
  box-shadow: 0 10px 26px rgba(0, 0, 0, 0.28);
}
body div[data-testid="stMetric"] { background: var(--qp-surface); border: 1px solid var(--qp-border); }
body .qp-professor { background: var(--qp-surface); border: 1px solid var(--qp-border); }
body .qp-pill {
  background: color-mix(in srgb, var(--qp-accent) 22%, var(--qp-surface));
  border: 1px solid color-mix(in srgb, var(--qp-accent) 45%, transparent);
  color: var(--qp-text);
}
body .success-box { background: color-mix(in srgb, #20A977 16%, var(--qp-bg)); }
body .info-box { background: color-mix(in srgb, #368BEA 16%, var(--qp-bg)); }
body .warning-box { background: color-mix(in srgb, #E4A11B 16%, var(--qp-bg)); }

/* Page headers: darken the accent so white titles stay >= 5.6:1 on every level
   (white on the raw coral/cyan accents was ~2.3:1). */
body .qp-pagehead {
  background: linear-gradient(120deg, color-mix(in srgb, var(--qp-accent) 55%, var(--qp-bg)) 0%, var(--qp-surface) 100%);
  border: 1px solid var(--qp-border); border-bottom: 3px solid var(--qp-accent);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.35);
}

/* Primary buttons use the level accent (BASE_CSS); pick a readable label color for it.
   Streamlit's own hover color (a dark violet) would otherwise replace the accent under the cursor. */
body button[kind="primary"],
body button[kind="primary"] :is(p, span) { color: var(--qp-on-accent); }
body button[kind="primary"]:is(:hover, :focus-visible, :active) {
  background: color-mix(in srgb, var(--qp-accent) 85%, #000000);
  border-color: color-mix(in srgb, var(--qp-accent) 85%, #000000);
  color: var(--qp-on-accent);
}

/* app.py's "Lesson checkpoint" opens a qp-card div in one st.markdown call and closes it in
   another; Streamlit can't wrap widgets that way, so it leaves an empty card. Hide it. */
body .qp-card:empty { display: none; }

/* Landing hero: Streamlit's paragraph margins cancel BASE_CSS's auto-centering of the subtitle. */
body .qp-hero-sub { margin-left: auto; margin-right: auto; }

/* ---- landing sections (ui/landing_sections.py) ---- */
.qp-section-lead { color: var(--qp-text-soft); font-size: 1.05rem; line-height: 1.6; }
.qp-stats { display: flex; flex-wrap: wrap; gap: .6rem; margin-top: .4rem; }
.qp-stat { background: var(--qp-surface); border: 1px solid var(--qp-border); border-radius: 14px; padding: .5rem .9rem; }
.qp-stat b { font-family: 'Space Grotesk', sans-serif; font-size: 1.35rem; color: var(--qp-cyan); margin-right: .4rem; }
.qp-stat span { color: var(--qp-text-soft); }

.qp-bloch { display: flex; flex-direction: column; align-items: center; }
.qp-bloch svg { width: 100%; max-width: 250px; height: auto; }
.qp-bloch-shell { fill: rgba(124, 111, 242, 0.08); stroke: rgba(201, 200, 240, 0.55); stroke-width: 1.4; }
.qp-bloch-back { fill: none; stroke: rgba(201, 200, 240, 0.3); stroke-width: 1.2; stroke-dasharray: 4 5; }
.qp-bloch-front { fill: none; stroke: var(--qp-cyan); stroke-width: 1.6; stroke-dasharray: 6 6; animation: qp-bloch-flow 5s linear infinite; }
.qp-bloch-axis { stroke: rgba(201, 200, 240, 0.45); stroke-width: 1.2; stroke-dasharray: 3 4; }
.qp-bloch-drop { stroke: rgba(255, 138, 101, 0.55); stroke-width: 1.2; stroke-dasharray: 3 3; }
.qp-bloch-state { stroke: var(--qp-coral); stroke-width: 3; stroke-linecap: round; }
.qp-bloch-tip { fill: var(--qp-coral); }
.qp-bloch-halo { fill: var(--qp-coral); transform-box: fill-box; transform-origin: center; animation: qp-bloch-pulse 2.8s ease-in-out infinite; }
.qp-bloch-pole { fill: var(--qp-text-soft); }
.qp-bloch-label { fill: var(--qp-text-soft); font-family: 'IBM Plex Mono', monospace; font-size: 15px; text-anchor: middle; }
.qp-bloch .qp-bloch-caption { color: var(--qp-text-muted); font-size: .85rem; text-align: center; max-width: 300px; margin: .4rem auto 0; }
@keyframes qp-bloch-flow { to { stroke-dashoffset: -120; } }
@keyframes qp-bloch-pulse { 0%, 100% { opacity: .12; transform: scale(.75); } 50% { opacity: .4; transform: scale(1.25); } }
@media (prefers-reduced-motion: reduce) { .qp-bloch-front, .qp-bloch-halo { animation: none; } }

.qp-step { background: var(--qp-surface); border: 1px solid var(--qp-border); border-radius: 18px; padding: 1.1rem 1.1rem 1rem; min-height: 170px; }
.qp-step .qp-step-num {
  display: inline-flex; width: 30px; height: 30px; border-radius: 50%; align-items: center; justify-content: center;
  background: var(--qp-primary); color: var(--qp-bg); font-family: 'Space Grotesk', sans-serif; font-weight: 700; margin-right: .5rem;
}
.qp-step .qp-step-icon { font-size: 1.3rem; vertical-align: middle; }
.qp-step h4 { margin: .6rem 0 .3rem; color: var(--qp-text); }
.qp-step p { color: var(--qp-text-soft); font-size: .93rem; line-height: 1.5; margin: 0; }

.qp-inside { min-height: 330px; }
.qp-inside .qp-inside-meta { color: var(--qp-cyan); font-family: 'IBM Plex Mono', monospace; font-size: .78rem; }
.qp-inside ul { margin: .5rem 0 0; padding-left: 1.1rem; }
.qp-inside li { color: var(--qp-text-soft); font-size: .88rem; line-height: 1.45; }
.qp-inside .qp-inside-more { list-style: none; margin-left: -1.1rem; color: var(--qp-text-muted); }

.qp-footer { margin-top: 3rem; padding: 1.4rem 0 .6rem; border-top: 1px solid var(--qp-border); text-align: center; }
.qp-footer p { color: var(--qp-text-soft); margin: .25rem 0; font-size: .92rem; }
.qp-footer b { color: var(--qp-text); }
.qp-footer .qp-footer-brand { font-family: 'Space Grotesk', sans-serif; color: var(--qp-cyan); font-weight: 600; font-size: 1.05rem; }
.qp-footer .qp-footer-note { color: var(--qp-text-muted); font-size: .85rem; }
.qp-footer a { color: var(--qp-link); }
"""


def apply_theme(accent: str | None = None) -> None:
    """Inject the shared dark theme. Call once per run, after BASE_CSS.

    ``accent`` is the current level's accent color (None on the landing page,
    which uses BASE_CSS's default accent).
    """
    tokens = "".join(f"--qp-{name}: {value};" for name, value in PALETTE.items())
    on_accent = readable_text_on(accent or DEFAULT_ACCENT)
    # st.html with only a <style> tag applies the CSS without adding an empty row to the page.
    # Its sanitizer drops the whole style block if the CSS contains "<" followed by a letter or
    # "/" (it looks like a tag), so keep HTML out of the CSS comments.
    st.html(f"<style>:root {{ {tokens} --qp-on-accent: {on_accent}; }}{_DARK_CSS}</style>")
