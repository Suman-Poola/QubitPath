from __future__ import annotations

import json
import math
import random
from datetime import date, datetime, timedelta
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# ============================================================================
# Constants
# ============================================================================

APP_TITLE = "QubitPath"
LEVELS = ["Elementary", "Proficient", "Erudite"]
LEVEL_TO_NUM = {"Elementary": 1, "Proficient": 2, "Erudite": 3}
IBM_COURSES_URL = "https://quantum.cloud.ibm.com/learning/en/courses"
QISKIT_DOCS_URL = "https://qiskit.qotlabs.org/docs/"

PAGE_KEYS = [
    "Home",
    "Recorded Learning",
    "Live Tutoring",
    "Quantum Lab",
    "Quiz & Games",
    "AI Professor",
    "Analytics",
    "Responsible AI",
]
NAV_ICONS = {
    "Home": "\U0001F3E0",
    "Recorded Learning": "\U0001F3AC",
    "Live Tutoring": "\U0001F9D1\u200D\U0001F3EB",
    "Quantum Lab": "\U0001F9EA",
    "Quiz & Games": "\U0001F3AE",
    "AI Professor": "\U0001F916",
    "Analytics": "\U0001F4CA",
    "Responsible AI": "\U0001F6E1\uFE0F",
}

LEVEL_META: dict[str, dict[str, Any]] = {
    "Elementary": {
        "age_range": "Ages 7\u201310",
        "tagline": "Big questions, playful experiments.",
        "icon": "\U0001F31F",
        "blurb": "Coins that are magic, switches that flip, and your first taste of quantum weirdness \u2014 no math required.",
        "accent": "#FF8A65",
        "accent2": "#7C6FF2",
        "radius": "26px",
        "goal_options": ["Have fun and get curious", "Understand the big ideas", "Try the mini-games", "Collect XP stars"],
        "nav_overrides": {
            "Quantum Lab": "Magic Coin Machine",
            "AI Professor": "Ask Professor Qubit",
            "Analytics": "My Progress",
            "Responsible AI": "For Grown-Ups",
        },
        "lab_name": "Magic Coin Machine",
        "resource_label": "Grown-up corner: browse IBM's course catalog",
    },
    "Proficient": {
        "age_range": "Ages 11\u201313",
        "tagline": "Real circuits, real vocabulary, real fun.",
        "icon": "\U0001F9ED",
        "blurb": "Real circuit diagrams, real vocabulary, and enough percentages to explain why quantum coins land the way they do.",
        "accent": "#1FBFB2",
        "accent2": "#7C6FF2",
        "radius": "16px",
        "goal_options": ["Understand the basics well", "Build my first circuit", "Get ready for a science fair", "Explore quantum careers"],
        "nav_overrides": {
            "Quantum Lab": "Circuit Playground",
            "AI Professor": "Ask Professor Qubit",
            "Analytics": "My Stats",
            "Responsible AI": "For Parents & Teachers",
        },
        "lab_name": "Circuit Playground",
        "resource_label": "Want to go further? Open the resource",
    },
    "Erudite": {
        "age_range": "Ages 14\u201318",
        "tagline": "From qubits to error correction, at research pace.",
        "icon": "\U0001F52C",
        "blurb": "Twelve lessons from your first Qiskit program to error correction, plus a real circuit simulator and research-style tools.",
        "accent": "#6F4BF2",
        "accent2": "#1FBFB2",
        "radius": "10px",
        "goal_options": ["Understand foundations", "Build Qiskit projects", "Prepare for research or competitions", "Explore quantum careers"],
        "nav_overrides": {},
        "lab_name": "Quantum Lab",
        "resource_label": "Open official learning resource",
    },
}


def nav_label(level: str, page_key: str) -> str:
    return LEVEL_META[level]["nav_overrides"].get(page_key, page_key)


st.set_page_config(
    page_title=f"{APP_TITLE} | Quantum Learning",
    page_icon="\u269B\uFE0F",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================================
# Base styling (level-independent: fonts, tokens, structural rules)
# ============================================================================

BASE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap');

:root {
  --qp-ink: #0E1330;
  --qp-ink-soft: #1A2050;
  --qp-violet: #7C6FF2;
  --qp-cyan: #1FBFB2;
  --qp-coral: #FF8A65;
  --qp-paper: #F7F6FB;
  --qp-slate: #232A4D;
  --qp-muted: #6B7094;
  --qp-accent: #6F4BF2;
  --qp-accent2: #1FBFB2;
  --qp-radius: 16px;
}

html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
.stApp { background: var(--qp-paper); }
.block-container { padding-top: 1.1rem; padding-bottom: 2rem; max-width: 100%; }
[data-testid="stHeader"] { background: transparent; }

h1, h2, h3, .qp-display { font-family: 'Space Grotesk', sans-serif; color: var(--qp-slate); letter-spacing: -0.01em; }
p, li, label, span { color: var(--qp-slate); }
.qp-mono, .qp-ket { font-family: 'IBM Plex Mono', monospace; }

/* ---- sidebar / mission-control rail ---- */
section[data-testid="stSidebar"] { background: linear-gradient(180deg, var(--qp-ink), var(--qp-ink-soft)); }
section[data-testid="stSidebar"] * { color: #F1F1FA !important; }
section[data-testid="stSidebar"] .qp-sidebar-title { font-family: 'Space Grotesk', sans-serif; font-size: 1.3rem; font-weight: 700; margin-bottom: 0; }

/* ---- generic content card ---- */
.qp-card {
  background: #FFFFFF; border: 1px solid rgba(35,42,77,0.08);
  border-top: 3px solid var(--qp-accent);
  padding: 1.05rem 1.2rem; border-radius: var(--qp-radius);
  box-shadow: 0 10px 26px rgba(30,38,90,0.07);
  min-height: 130px;
}
.qp-pill {
  display: inline-block; padding: .22rem .68rem; border-radius: 999px;
  background: color-mix(in srgb, var(--qp-accent) 14%, white);
  color: var(--qp-accent); font-weight: 600; font-size: .78rem; margin-right: .3rem;
}
.qp-muted { color: var(--qp-muted); font-size: .87rem; }
.success-box { background:#ECFFF7; border-left:5px solid #20A977; padding:.8rem 1rem; border-radius:12px; }
.info-box { background:#EEF8FF; border-left:5px solid #368BEA; padding:.8rem 1rem; border-radius:12px; }
.warning-box { background:#FFF8E7; border-left:5px solid #E4A11B; padding:.8rem 1rem; border-radius:12px; }
div[data-testid="stMetric"] { background:white; border:1px solid #ECEBF6; padding:.7rem; border-radius: var(--qp-radius); }

.qp-pagehead {
  padding: 1.3rem 1.5rem; border-radius: var(--qp-radius); color: white;
  background: linear-gradient(120deg, var(--qp-accent) 0%, var(--qp-ink) 120%);
  box-shadow: 0 16px 40px rgba(30,38,90,0.18); margin-bottom: 1rem;
}
.qp-pagehead h1 { color: white; margin: 0; font-size: 2.05rem; }
.qp-pagehead p { color: rgba(255,255,255,.92); margin: .4rem 0 0; font-size: 1.02rem; }

.qp-professor { display:flex; gap:1rem; align-items:center; background:white; padding:1rem; border-radius: var(--qp-radius); border:1px solid #E9E7F5; }
.qp-avatar { width:64px; height:64px; border-radius:50%; display:flex; align-items:center; justify-content:center;
  font-size:1.9rem; background: linear-gradient(135deg, var(--qp-accent), var(--qp-accent2)); color:white; flex-shrink:0; }

/* ---- landing hero ---- */
.qp-hero { background: radial-gradient(circle at 20% 0%, #262c66 0%, var(--qp-ink) 62%); border-radius: 28px;
  padding: 3rem 1.5rem 2rem; text-align:center; color:#F4F3FF; }
.qp-wordmark { font-family:'Space Grotesk',sans-serif; font-weight:600; letter-spacing:.02em; color: var(--qp-cyan); margin:0; font-size:1.05rem; }
.qp-hero h1 { color:#FBFAFF; font-size: 2.7rem; line-height:1.12; margin: .6rem auto 0; max-width: 640px; }
.qp-hero-sub { color:#C9C8F0; max-width: 560px; margin: 1rem auto 0; font-size:1.05rem; line-height:1.55; }

.qp-orbit-wrap { display:flex; justify-content:center; margin: 1.6rem 0 .2rem; }
.qp-orbit-svg { width: 168px; height: 168px; }
.qp-orbit-ring { fill:none; stroke-width:1.3; }
.qp-ring-a { stroke: rgba(124,111,242,.55); transform-origin:110px 110px; transform:rotate(-22deg) scaleY(.52); }
.qp-ring-b { stroke: rgba(31,191,178,.5); transform-origin:110px 110px; transform:rotate(58deg) scaleY(.52); }
.qp-orbit-core { fill:#FF8A65; }
.qp-orbit-spin { transform-origin:110px 110px; animation: qp-spin 9s linear infinite; }
.qp-orbit-axis { stroke:#FF8A65; stroke-width:2.6; stroke-linecap:round; }
.qp-orbit-tip { fill:#FF8A65; }
@keyframes qp-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .qp-orbit-spin { animation: none; } }

.qp-choose-label { color:#EDEBFF; font-family:'Space Grotesk',sans-serif; font-size:1.1rem; margin: 2rem 0 .9rem; }

.qp-pathcard { background:#151A3F; border:1px solid rgba(255,255,255,.09); border-radius:22px; padding:1.3rem 1.1rem 1rem;
  text-align:left; min-height: 210px; }
.qp-pathcard .qp-path-icon { font-size:1.7rem; }
.qp-pathcard h3 { color:#FBFAFF; margin:.4rem 0 0; font-family:'Space Grotesk',sans-serif; }
.qp-pathcard .qp-path-age { color: var(--qp-cyan); font-family:'IBM Plex Mono',monospace; font-size:.78rem; }
.qp-pathcard p { color:#C9C8E8; font-size:.92rem; line-height:1.45; margin:.5rem 0 0; }

.qp-howcard { text-align:center; padding: .4rem; }
.qp-howcard .qp-how-icon { font-size:1.6rem; }

/* keep native buttons legible against the dark hero and tidy elsewhere */
.stButton>button { border-radius: 999px; font-weight:600; }
button[kind="primary"] { background: var(--qp-accent); border-color: var(--qp-accent); }

/* dot-grid texture used only for the Proficient lab/card accents */
.qp-dotgrid { background-image: radial-gradient(rgba(31,191,178,.28) 1px, transparent 1px); background-size: 14px 14px; }
</style>
"""
st.markdown(BASE_CSS, unsafe_allow_html=True)


def inject_level_theme(level: str) -> None:
    meta = LEVEL_META[level]
    st.markdown(
        f"<style>:root {{ --qp-accent:{meta['accent']}; --qp-accent2:{meta['accent2']}; --qp-radius:{meta['radius']}; }}</style>",
        unsafe_allow_html=True,
    )


def orbit_mark() -> str:
    return (
        '<div class="qp-orbit-wrap" aria-hidden="true"><svg viewBox="0 0 220 220" class="qp-orbit-svg">'
        '<circle cx="110" cy="110" r="92" class="qp-orbit-ring qp-ring-a"/>'
        '<circle cx="110" cy="110" r="92" class="qp-orbit-ring qp-ring-b"/>'
        '<circle cx="110" cy="110" r="6" class="qp-orbit-core"/>'
        '<g class="qp-orbit-spin"><line x1="110" y1="110" x2="110" y2="18" class="qp-orbit-axis"/>'
        '<circle cx="110" cy="18" r="9" class="qp-orbit-tip"/></g></svg></div>'
    )


def header(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="qp-pagehead"><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


# ============================================================================
# Curriculum content
# ============================================================================

CURRICULUM: dict[str, list[dict[str, Any]]] = {
    "Elementary": [
        {
            "id": "EL1", "title": "What Makes a Computer Think?", "duration": 15, "difficulty": 1,
            "objectives": ["Explain that computers store everything as 0s and 1s", "Give two real-world on/off examples", "Say why a light switch is a good bit"],
            "summary": "Every regular computer, from a phone to a laptop, breaks information into tiny switches called bits. A bit is only ever one of two things: off (0) or on (1) \u2014 just like a light switch.",
            "activity": "Walk around your room and find three things that work like a bit: only ever one of two states.",
            "recording": "Recorded lesson: Meet the humble bit",
            "resource": IBM_COURSES_URL,
        },
        {
            "id": "EL2", "title": "The Magic Spinning Coin", "duration": 18, "difficulty": 1,
            "objectives": ["Describe a qubit using the spinning-coin idea", "Explain what \u201cmeasuring\u201d means", "Predict roughly how many heads vs. tails in many flips"],
            "summary": "A qubit is like a magic coin: while it's spinning in the air it isn't heads or tails yet, it's a mix of both. The moment you catch it and look \u2014 that's a measurement \u2014 it becomes just one answer.",
            "activity": "Flip a real coin 10 times and tally heads vs. tails, then compare with the Magic Coin Machine.",
            "recording": "Recorded lesson: Why quantum coins are weird",
            "resource": IBM_COURSES_URL,
        },
        {
            "id": "EL3", "title": "Flip It! Quantum Switches", "duration": 20, "difficulty": 1,
            "objectives": ["Use the Flip switch to turn 0 into 1", "Use the Maybe switch to make a spinning coin", "Read a two-switch recipe in order"],
            "summary": "Scientists build quantum programs out of tiny switches called gates. The one we call the Flip switch (real name: X) always swaps 0 and 1. The Maybe switch (real name: H) turns a plain 0 into a spinning magic coin.",
            "activity": "In the mini-game, match each switch to the trick it performs.",
            "recording": "Recorded lesson: Two switches, endless tricks",
            "resource": IBM_COURSES_URL,
        },
        {
            "id": "EL4", "title": "Partner Coins: A Quantum Magic Trick", "duration": 18, "difficulty": 1,
            "objectives": ["Describe entanglement as \u201clinked partner coins\u201d", "Say why this surprised even Einstein", "Recognize the word entanglement"],
            "summary": "Sometimes scientists link two magic coins so tightly that whatever one lands on, the other always matches \u2014 even from opposite sides of a room, or opposite sides of the planet. Real scientists call this entanglement, and it's one of the strangest true facts we know about nature.",
            "activity": "Play the partner-coin game with a friend: agree on a rule, then \u201cmeasure\u201d your coins at the same time and check the match.",
            "recording": "Recorded lesson: Coins that always agree",
            "resource": IBM_COURSES_URL,
        },
    ],
    "Proficient": [
        {
            "id": "MS1", "title": "Bits vs. Qubits", "duration": 25, "difficulty": 1,
            "objectives": ["Compare a classical bit with a qubit", "Read the labels |0\u27e9 and |1\u27e9", "List one real device that already uses qubits"],
            "summary": "A classical bit is always 0 or 1. A qubit can be a mix of both \u2014 scientists write the two options as |0\u27e9 and |1\u27e9, and a qubit's state can combine them until it's measured.",
            "activity": "Sort five devices (phone, quantum computer prototype, calculator, thermostat, qubit sensor) into classical vs. quantum.",
            "recording": "Recorded lesson: From bits to qubits",
            "resource": IBM_COURSES_URL,
        },
        {
            "id": "MS2", "title": "Superposition and Percent Chances", "duration": 28, "difficulty": 1,
            "objectives": ["Explain superposition in one sentence", "Turn a count of outcomes into a percentage", "Interpret a bar chart of measurement results"],
            "summary": "Superposition means a qubit is in a combination of |0\u27e9 and |1\u27e9 at once. You can't see the mix directly \u2014 you only see percentages after measuring many times, similar to how flipping one coin many times reveals it's \u201cabout 50/50.\u201d",
            "activity": "Run the Circuit Playground's coin experiment for 100 shots and calculate the percentage that landed on 1.",
            "recording": "Recorded lesson: Reading a results bar chart",
            "resource": QISKIT_DOCS_URL,
        },
        {
            "id": "MS3", "title": "Your First Circuit", "duration": 30, "difficulty": 2,
            "objectives": ["Read a circuit diagram left to right", "Name the X and H gates", "Predict a simple one-gate outcome"],
            "summary": "A quantum circuit is a recipe: a line for each qubit, with boxes (gates) placed left to right showing what happens to it over time. The X gate flips |0\u27e9 and |1\u27e9; the H gate creates an equal mix of both.",
            "activity": "Build a one-gate circuit in the Circuit Playground and check whether the result matches your prediction.",
            "recording": "Recorded lesson: Reading circuit diagrams",
            "resource": QISKIT_DOCS_URL,
        },
        {
            "id": "MS4", "title": "Spooky Pairs: Intro to Entanglement", "duration": 30, "difficulty": 2,
            "objectives": ["Define entanglement in your own words", "Explain why Einstein called it \u201cspooky\u201d", "Identify a Bell-pair result pattern (00 or 11 only)"],
            "summary": "A special two-qubit gate can link two qubits so tightly that measuring one instantly tells you the other's result \u2014 even though neither one had a fixed value before you looked. Albert Einstein famously called this \u201cspooky action at a distance,\u201d and it's now used in real quantum technology.",
            "activity": "Run the Bell-entanglement experiment in the Circuit Playground and confirm you only ever see 00 or 11.",
            "recording": "Recorded lesson: Meeting entanglement for real",
            "resource": IBM_COURSES_URL,
        },
    ],
    "Erudite": [
        {
            "id": "HF1", "track": "Foundations", "title": "Bits, Qubits, and the Quantum Mindset", "duration": 35, "difficulty": 1,
            "objectives": ["Compare a classical bit with a qubit", "Read ket notation", "Identify realistic quantum-computing use cases"],
            "summary": "A bit is either 0 or 1. A qubit is described by a normalized complex state vector and can be measured to produce a classical result.",
            "activity": "Classify five everyday problems as classical, quantum-inspired, or potentially quantum-relevant.",
            "recording": "Recorded lesson: From bits to qubits",
            "resource": "https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/single-systems/introduction",
        },
        {
            "id": "HF2", "track": "Foundations", "title": "Superposition and Measurement", "duration": 45, "difficulty": 1,
            "objectives": ["Explain amplitudes and probabilities", "Apply normalization", "Interpret repeated measurement counts"],
            "summary": "Superposition is a linear combination of basis states. Measurement converts amplitudes into outcome probabilities through the Born rule.",
            "activity": "Use the Quantum Coin mini-game to compare predicted and sampled outcomes.",
            "recording": "Recorded lesson: Why quantum measurement is probabilistic",
            "resource": "https://qiskit.qotlabs.org/learning/courses/basics-of-quantum-information/single-systems/quantum-information",
        },
        {
            "id": "HF3", "track": "Foundations", "title": "Quantum Gates and Circuit Diagrams", "duration": 50, "difficulty": 1,
            "objectives": ["Recognize X, H, Z, and rotation gates", "Read a circuit left to right", "Predict basic single-qubit outcomes"],
            "summary": "Quantum gates are reversible linear operations. The X gate flips basis states, while the H gate creates and removes equal superpositions.",
            "activity": "Build a single-qubit circuit and compare your prediction with Qiskit simulation.",
            "recording": "Recorded lesson: Gate-by-gate circuit reading",
            "resource": "https://qiskit.qotlabs.org/docs/guides/circuit-library",
        },
        {
            "id": "HF4", "track": "Foundations", "title": "Your First Qiskit Program", "duration": 55, "difficulty": 1,
            "objectives": ["Create a QuantumCircuit", "Simulate a statevector", "Sample measurement counts"],
            "summary": "Qiskit represents quantum programs as circuits. A local statevector simulator is ideal for learning before using real quantum hardware.",
            "activity": "Create a Bell state and explain why 01 and 10 should not appear in the ideal simulator.",
            "recording": "Recorded lab: Build and run a Bell circuit",
            "resource": "https://qiskit.qotlabs.org/docs/guides/quick-start",
        },
        {
            "id": "HA1", "track": "Entanglement & Algorithms", "title": "Multiple Qubits and Tensor Products", "duration": 60, "difficulty": 2,
            "objectives": ["Determine multi-qubit state dimensions", "Interpret basis ordering", "Construct product states"],
            "summary": "The state space grows as 2^n for n qubits. Tensor products combine individual systems into a joint mathematical description.",
            "activity": "Calculate the eight basis states for a three-qubit register.",
            "recording": "Recorded lesson: Scaling from one qubit to many",
            "resource": "https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/multiple-systems/introduction",
        },
        {
            "id": "HA2", "track": "Entanglement & Algorithms", "title": "Entanglement and Bell States", "duration": 65, "difficulty": 2,
            "objectives": ["Distinguish correlation from entanglement", "Prepare a Bell state", "Interpret joint measurements"],
            "summary": "Entangled states cannot be written as a product of independent subsystem states. Bell states are the standard two-qubit examples.",
            "activity": "Run the Bell-state lab for several shot counts and compare statistical variation.",
            "recording": "Recorded lesson: Entanglement without faster-than-light messaging",
            "resource": "https://qiskit.qotlabs.org/learning/courses/basics-of-quantum-information/entanglement-in-action/introduction",
        },
        {
            "id": "HA3", "track": "Entanglement & Algorithms", "title": "Teleportation and Superdense Coding", "duration": 75, "difficulty": 2,
            "objectives": ["Describe the role of shared entanglement", "Track classical communication", "Separate state transfer from matter transfer"],
            "summary": "Quantum teleportation transfers an unknown quantum state using shared entanglement plus two classical bits; it does not transmit matter or violate causality.",
            "activity": "Draw the information flow and label quantum versus classical channels.",
            "recording": "Recorded lesson: Quantum communication protocols",
            "resource": "https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/entanglement-in-action/quantum-teleportation",
        },
        {
            "id": "HA4", "track": "Entanglement & Algorithms", "title": "Quantum Algorithms: Deutsch\u2013Jozsa and Grover", "duration": 85, "difficulty": 2,
            "objectives": ["Explain oracle-based algorithms", "Describe amplitude amplification", "Compare query complexity"],
            "summary": "Early quantum algorithms reveal how interference can suppress wrong answers and amplify useful ones. Grover search gives a quadratic query improvement for unstructured search.",
            "activity": "Trace one Grover iteration for a two-qubit search space.",
            "recording": "Recorded lesson: Interference as an algorithmic resource",
            "resource": "https://quantum.cloud.ibm.com/learning/en/courses/fundamentals-of-quantum-algorithms",
        },
        {
            "id": "HR1", "track": "Advanced Research", "title": "Density Matrices, Noise, and Channels", "duration": 90, "difficulty": 3,
            "objectives": ["Represent mixed states", "Calculate purity conceptually", "Describe common noise channels"],
            "summary": "Density matrices describe pure and mixed states. Quantum channels model physically allowed transformations, including noise and decoherence.",
            "activity": "Compare ideal and noisy state descriptions and identify which information is lost.",
            "recording": "Recorded seminar: From statevectors to open systems",
            "resource": "https://quantum.cloud.ibm.com/learning/en/courses/general-formulation-of-quantum-information",
        },
        {
            "id": "HR2", "track": "Advanced Research", "title": "Variational Algorithms and VQE", "duration": 100, "difficulty": 3,
            "objectives": ["Describe hybrid quantum-classical loops", "Identify ansatz and optimizer roles", "Interpret expectation-value objectives"],
            "summary": "Variational algorithms use a parameterized quantum circuit and a classical optimizer. VQE estimates low-energy states of a Hamiltonian.",
            "activity": "Sketch a VQE workflow and identify possible sources of optimization failure.",
            "recording": "Recorded lab: Anatomy of a VQE experiment",
            "resource": "https://quantum.cloud.ibm.com/learning/en/courses/quantum-chem-with-vqe",
        },
        {
            "id": "HR3", "track": "Advanced Research", "title": "QAOA and Combinatorial Optimization", "duration": 100, "difficulty": 3,
            "objectives": ["Map a cost function to a Hamiltonian", "Explain alternating operators", "Evaluate approximation quality"],
            "summary": "QAOA alternates problem and mixer operators. It is a framework for experimenting with approximate solutions to combinatorial problems.",
            "activity": "Encode a small Max-Cut instance and discuss measurement-to-solution post-processing.",
            "recording": "Recorded workshop: Hybrid optimization with QAOA",
            "resource": "https://qiskit.qotlabs.org/learning/courses/variational-algorithm-design",
        },
        {
            "id": "HR4", "track": "Advanced Research", "title": "Quantum Error Correction and Fault Tolerance", "duration": 110, "difficulty": 3,
            "objectives": ["Explain logical versus physical qubits", "Describe syndrome measurement", "Identify the purpose of fault tolerance"],
            "summary": "Quantum error correction protects logical information by encoding it across many physical qubits and extracting error syndromes without directly reading the logical state.",
            "activity": "Work through a three-qubit repetition-code example and identify its limitations.",
            "recording": "Recorded seminar: Protecting fragile quantum information",
            "resource": "https://quantum.cloud.ibm.com/learning/en/courses/foundations-of-quantum-error-correction",
        },
    ],
}
LEVEL_LESSON_IDS: dict[str, set[str]] = {lvl: {l["id"] for l in CURRICULUM[lvl]} for lvl in LEVELS}
ERUDITE_TRACKS = ["Foundations", "Entanglement & Algorithms", "Advanced Research"]

QUIZZES: dict[str, Any] = {
    "Elementary": [
        {"q": "A regular computer bit can be\u2026", "options": ["Only ON or only OFF", "ON, OFF, or both at once", "Always spinning", "Always purple"], "answer": 0, "why": "A classical bit is always just one of two choices: off (0) or on (1)."},
        {"q": "While a magic coin is still spinning in the air, what is it?", "options": ["Only heads", "Only tails", "A mix of heads and tails", "Nothing at all"], "answer": 2, "why": "Before you look (measure), a spinning qubit-coin is a mix of both possibilities \u2014 that's superposition."},
        {"q": "What happens the moment you catch and look at the spinning coin?", "options": ["It keeps spinning forever", "It becomes just one result, heads or tails", "It turns into two coins", "It disappears"], "answer": 1, "why": "Measuring (looking) makes the qubit settle into one definite outcome."},
        {"q": "Two \u201cpartner coins\u201d are entangled. If one lands heads, the other one\u2026", "options": ["Always lands heads too (in this simple trick)", "Always lands tails no matter what", "Does something unrelated", "Stops working"], "answer": 0, "why": "Entangled partners are linked \u2014 what happens to one instantly tells you about the other, however far apart they are."},
    ],
    "Proficient": [
        {"q": "Which is the best description of a qubit before you measure it?", "options": ["It is secretly already 0 or 1, you just don't know which", "It can be a mix of |0\u27e9 and |1\u27e9 at the same time", "It stores two separate classical bits", "It is always exactly halfway between 0 and 1"], "answer": 1, "why": "A qubit's state is a combination of |0\u27e9 and |1\u27e9 until measurement, not a hidden classical value."},
        {"q": "If a fair qubit shows 1 about 50% of the time over many measurements, that's because\u2026", "options": ["The circuit is broken", "Outcomes are sampled from a probability distribution", "It alternates 0,1,0,1 on a timer", "Measurement always gives the same answer"], "answer": 1, "why": "Repeated measurements sample from a probability distribution \u2014 the split looks close to 50/50 over many tries, not a strict alternation."},
        {"q": "In a circuit diagram, what does the H gate do to a qubit that starts at |0\u27e9?", "options": ["Nothing changes", "Flips it straight to |1\u27e9", "Puts it into an equal mix of |0\u27e9 and |1\u27e9", "Deletes the qubit"], "answer": 2, "why": "The Hadamard (H) gate creates an equal superposition of |0\u27e9 and |1\u27e9."},
        {"q": "Two qubits are entangled. What's special about measuring them?", "options": ["Their results are totally unrelated", "Their results are linked, even far apart", "One qubit copies the other before measurement", "Entangled qubits can't be measured"], "answer": 1, "why": "Entangled qubits show correlated outcomes when measured \u2014 a link that can't be explained by treating them as independent."},
    ],
    "Erudite": {
        "Foundations": [
            {"q": "Which statement best describes a qubit before measurement?", "options": ["It is always secretly 0 or 1", "It can be represented by normalized complex amplitudes", "It stores two classical bits", "It violates probability rules"], "answer": 1, "why": "A pure qubit state is represented by two normalized complex amplitudes."},
            {"q": "What does an ideal Hadamard gate do to |0>?", "options": ["Creates an equal superposition of |0> and |1>", "Always produces |1>", "Measures the qubit", "Copies the qubit"], "answer": 0, "why": "H|0> = (|0> + |1>)/sqrt(2)."},
            {"q": "Why do repeated measurements of the same prepared superposition vary?", "options": ["The computer is broken", "Quantum outcomes are sampled from a probability distribution", "The circuit changes itself", "Qubits are classical random-number generators"], "answer": 1, "why": "Measurement samples outcomes according to the state's probability amplitudes."},
            {"q": "Which gate acts like a classical NOT on basis states?", "options": ["Z", "H", "X", "S"], "answer": 2, "why": "The Pauli-X gate maps |0> to |1> and |1> to |0>."},
        ],
        "Entanglement & Algorithms": [
            {"q": "How many computational basis states does a three-qubit register have?", "options": ["3", "6", "8", "9"], "answer": 2, "why": "An n-qubit system has 2^n basis states, so 2^3 = 8."},
            {"q": "An entangled two-qubit state can always be written as\u2026", "options": ["A product of two single-qubit states", "A classical probability table only", "A joint state that may not factor into subsystem states", "Two copied unknown qubits"], "answer": 2, "why": "Non-factorability is a defining feature of pure-state entanglement."},
            {"q": "Quantum teleportation requires shared entanglement and\u2026", "options": ["No communication", "Two classical bits", "Faster-than-light signaling", "A copy of the unknown state"], "answer": 1, "why": "The protocol requires two classical bits, preserving causality."},
            {"q": "Grover's algorithm is primarily associated with\u2026", "options": ["Unstructured search", "Sorting in constant time", "Copying quantum states", "Perfect error correction"], "answer": 0, "why": "Grover search provides quadratic query improvement for unstructured search."},
        ],
        "Advanced Research": [
            {"q": "A density matrix is especially useful for representing\u2026", "options": ["Only classical bits", "Mixed states and subsystems", "Only deterministic algorithms", "Copied unknown states"], "answer": 1, "why": "Density matrices represent both pure and mixed quantum states."},
            {"q": "In VQE, the classical optimizer updates\u2026", "options": ["Hardware temperature", "Parameters of an ansatz circuit", "The number of physical laws", "Measurement postulates"], "answer": 1, "why": "VQE iteratively adjusts parameterized circuit values to reduce an energy objective."},
            {"q": "The purpose of a quantum error syndrome is to\u2026", "options": ["Read the logical state directly", "Identify information about errors without revealing the logical data", "Eliminate all physical noise", "Clone the logical qubit"], "answer": 1, "why": "Syndromes reveal error information while preserving encoded logical information."},
            {"q": "A fault-tolerant protocol is designed so that\u2026", "options": ["One fault does not uncontrollably spread into many logical errors", "Every gate is noiseless", "No redundancy is needed", "Classical control is forbidden"], "answer": 0, "why": "Fault tolerance constrains error propagation and supports reliable logical operations."},
        ],
    },
}

KNOWLEDGE_BASE = [
    {"title": "Qubit", "text": "A qubit is a two-level quantum information unit. A pure state can be written alpha|0> + beta|1>, where alpha and beta are complex amplitudes and their squared magnitudes sum to one."},
    {"title": "Measurement", "text": "Computational-basis measurement returns 0 or 1. The probabilities are the squared magnitudes of the relevant amplitudes. Measurement also changes the post-measurement state."},
    {"title": "Hadamard gate", "text": "The Hadamard gate creates equal superpositions from computational-basis states and can also recombine amplitudes, making interference visible."},
    {"title": "No-cloning theorem", "text": "An arbitrary unknown quantum state cannot be perfectly copied by a universal physical operation. This is consistent with linear quantum evolution."},
    {"title": "Entanglement", "text": "Entanglement describes joint quantum states whose correlations cannot be explained by assigning independent pure states to each subsystem. It does not enable faster-than-light communication."},
    {"title": "Quantum teleportation", "text": "Teleportation transfers an unknown quantum state using one shared entangled pair, a joint measurement, and two classical bits. The sender's original state is not retained."},
    {"title": "Grover search", "text": "Grover's algorithm alternates an oracle phase operation and diffusion-like amplitude amplification. It uses on the order of the square root of N oracle queries for an unstructured search space of size N."},
    {"title": "Density matrix", "text": "A density matrix is positive semidefinite with trace one. It represents pure states, probabilistic mixtures, and reduced states of larger entangled systems."},
    {"title": "VQE", "text": "The variational quantum eigensolver evaluates expectation values from a parameterized ansatz and uses a classical optimizer to search for a low-energy parameter setting."},
    {"title": "Quantum error correction", "text": "Quantum error correction encodes logical information into a larger Hilbert space. Syndrome measurements identify error information while avoiding direct measurement of the logical state."},
    {"title": "QAOA", "text": "QAOA alternates parameterized cost and mixer unitaries, then samples candidate solutions. Performance depends on encoding, depth, parameter optimization, noise, and post-processing."},
]

TEACHING_ARMS = ["Visual analogy", "Worked example", "Guided practice", "Short knowledge check", "Tutor session"]


# ============================================================================
# Session state / cached models
# ============================================================================

def init_state() -> None:
    defaults = {
        "page": "Welcome",
        "completed_lessons": [],
        "quiz_history": [],
        "xp": 120,
        "streak": 4,
        "bookings": [],
        "chat_history": [
            {"role": "assistant", "content": "Welcome! I am Professor Qubit. Ask me about qubits, gates, entanglement, algorithms, noise, or error correction."}
        ],
        "bandit_values": {arm: 0.5 for arm in TEACHING_ARMS},
        "bandit_counts": {arm: 0 for arm in TEACHING_ARMS},
        "current_strategy": "Visual analogy",
        "last_lab_success": None,
        "coin_spins": None,
        "weekly_activity": pd.DataFrame(
            {
                "week": [f"W{i}" for i in range(1, 9)],
                "minutes": [70, 95, 80, 135, 120, 155, 145, 180],
                "quiz_accuracy": [55, 62, 65, 71, 74, 78, 80, 84],
            }
        ),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_resource
def train_ai_models() -> tuple[RandomForestRegressor, Pipeline, pd.DataFrame, float]:
    rng = np.random.default_rng(42)
    n = 2400
    df = pd.DataFrame(
        {
            "weekly_hours": rng.uniform(0.5, 12.0, n),
            "lessons_completed": rng.integers(0, 13, n),
            "quiz_average": rng.uniform(25, 100, n),
            "streak_days": rng.integers(0, 31, n),
            "positive_feedback": rng.uniform(0.25, 1.0, n),
            "math_comfort": rng.integers(1, 6, n),
            "live_sessions": rng.integers(0, 7, n),
            "difficulty_level": rng.integers(1, 4, n),
        }
    )
    raw_progress = (
        1.8 * df["weekly_hours"]
        + 2.6 * df["lessons_completed"]
        + 0.22 * df["quiz_average"]
        + 0.38 * df["streak_days"]
        + 8.0 * df["positive_feedback"]
        + 2.0 * df["math_comfort"]
        + 2.8 * df["live_sessions"]
        - 3.0 * df["difficulty_level"]
        + rng.normal(0, 5.5, n)
    )
    df["four_week_progress"] = np.clip(raw_progress, 3, 100)

    risk_score = (
        1.2
        - 0.22 * df["weekly_hours"]
        - 0.045 * df["quiz_average"]
        - 0.08 * df["streak_days"]
        - 0.7 * df["positive_feedback"]
        - 0.25 * df["live_sessions"]
        + 0.35 * df["difficulty_level"]
        + rng.normal(0, 0.6, n)
    )
    df["support_risk"] = (risk_score > -2.55).astype(int)

    features = [
        "weekly_hours", "lessons_completed", "quiz_average", "streak_days",
        "positive_feedback", "math_comfort", "live_sessions", "difficulty_level",
    ]
    progress_model = RandomForestRegressor(n_estimators=220, max_depth=10, min_samples_leaf=3, random_state=42, n_jobs=-1)
    progress_model.fit(df[features], df["four_week_progress"])

    risk_model = Pipeline(
        [
            ("scale", StandardScaler()),
            ("dnn", MLPClassifier(hidden_layer_sizes=(64, 32, 16), activation="relu", alpha=0.001, max_iter=500, random_state=42, early_stopping=True)),
        ]
    )
    risk_model.fit(df[features], df["support_risk"])
    training_accuracy = float(risk_model.score(df[features], df["support_risk"]))
    importance = pd.DataFrame({"feature": features, "importance": progress_model.feature_importances_}).sort_values("importance", ascending=False)
    return progress_model, risk_model, importance, training_accuracy


@st.cache_resource
def build_retriever() -> tuple[TfidfVectorizer, np.ndarray]:
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform([item["title"] + " " + item["text"] for item in KNOWLEDGE_BASE])
    return vectorizer, matrix


def get_quiz_average() -> float:
    if not st.session_state.quiz_history:
        return 65.0
    return float(np.mean([x["score_pct"] for x in st.session_state.quiz_history]))


def positive_feedback_rate() -> float:
    total = sum(st.session_state.bandit_counts.values())
    if total == 0:
        return 0.65
    weighted = sum(st.session_state.bandit_values[a] * st.session_state.bandit_counts[a] for a in TEACHING_ARMS)
    return float(weighted / total)


def learner_features(level: str, weekly_hours: float, math_comfort: int) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "weekly_hours": weekly_hours,
                "lessons_completed": len(st.session_state.completed_lessons),
                "quiz_average": get_quiz_average(),
                "streak_days": st.session_state.streak,
                "positive_feedback": positive_feedback_rate(),
                "math_comfort": math_comfort,
                "live_sessions": len(st.session_state.bookings),
                "difficulty_level": LEVEL_TO_NUM[level],
            }
        ]
    )


def choose_teaching_strategy(epsilon: float = 0.16) -> str:
    if random.random() < epsilon:
        return random.choice(TEACHING_ARMS)
    values = st.session_state.bandit_values
    max_value = max(values.values())
    best = [arm for arm, value in values.items() if math.isclose(value, max_value, rel_tol=1e-9)]
    return random.choice(best)


def update_bandit(arm: str, reward: int) -> None:
    st.session_state.bandit_counts[arm] += 1
    n = st.session_state.bandit_counts[arm]
    old = st.session_state.bandit_values[arm]
    st.session_state.bandit_values[arm] = old + (reward - old) / n
    st.session_state.current_strategy = choose_teaching_strategy()


CAVEAT_LOW = {
    "Elementary": "I'm not totally sure about this one \u2014 ask a grown-up, or try the lesson again to double-check!",
    "Proficient": "This is only a loose match in my notes, so double-check it against the lesson or ask a tutor.",
    "Erudite": "I found only a weak match in the built-in knowledge base, so treat this as a starting point and verify it with the linked course materials or a tutor.",
}
CAVEAT_OK = {
    "Elementary": "This answer comes from QubitPath's own lesson notes.",
    "Proficient": "This answer is grounded in QubitPath's curated lesson notes.",
    "Erudite": "This answer is grounded in the platform's curated concept notes.",
}
LEVEL_NOTE = {
    "Elementary": "I'll explain this with a simple, everyday comparison and skip the technical words where I can.",
    "Proficient": "I'll connect this to circuits and simple percentages, and introduce a bit of the real vocabulary.",
    "Erudite": "I'll connect this to formal representations, assumptions, and implementation tradeoffs.",
}


def professor_answer(question: str, learner_level: str, strategy: str) -> str:
    vectorizer, matrix = build_retriever()
    query_vec = vectorizer.transform([question])
    scores = cosine_similarity(query_vec, matrix).ravel()
    top_idx = scores.argsort()[::-1][:3]
    top = [KNOWLEDGE_BASE[i] for i in top_idx]
    confidence = float(scores[top_idx[0]]) if len(top_idx) else 0.0
    core = top[0]["text"]
    related = ", ".join(item["title"] for item in top[1:])

    strategy_text = {
        "Visual analogy": "Analogy: think of amplitudes as arrows whose direction matters; when arrows combine, they can reinforce or cancel.",
        "Worked example": "Worked example: start with |0>, apply one gate at a time, and write the state after each operation before predicting measurement outcomes.",
        "Guided practice": "Guided practice: first state the number of qubits, then list basis states, then identify gates, and only then calculate or simulate.",
        "Short knowledge check": "Knowledge check: what result would change if the final measurement were removed? Explain your answer in one sentence.",
        "Tutor session": "Tutor-session suggestion: bring one circuit and one specific point of confusion to a 25-minute live session for targeted feedback.",
    }[strategy]

    caveat = CAVEAT_LOW[learner_level] if confidence < 0.08 else CAVEAT_OK[learner_level]

    return (
        f"**Core idea \u2014 {top[0]['title']}**\n\n{core}\n\n"
        f"**Adaptive teaching move**\n\n{strategy_text}\n\n"
        f"**For your level**\n\n{LEVEL_NOTE[learner_level]}\n\n"
        f"**Related concepts:** {related}.\n\n"
        f"*{caveat}*"
    )


def find_recommended_lesson(level: str) -> dict[str, Any]:
    for lesson in CURRICULUM[level]:
        if lesson["id"] not in st.session_state.completed_lessons:
            return lesson
    for fallback in LEVELS:
        for lesson in CURRICULUM[fallback]:
            if lesson["id"] not in st.session_state.completed_lessons:
                return lesson
    return CURRICULUM["Erudite"][-1]


def make_circuit(experiment: str, theta: float) -> tuple[QuantumCircuit, str]:
    if experiment == "Quantum coin (H gate)":
        qc = QuantumCircuit(1)
        qc.h(0)
        expectation = "0 and 1 should be approximately balanced."
    elif experiment == "Bell entanglement":
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)
        expectation = "Only 00 and 11 should appear in the ideal simulator."
    elif experiment == "Three-qubit GHZ":
        qc = QuantumCircuit(3)
        qc.h(0)
        qc.cx(0, 1)
        qc.cx(1, 2)
        expectation = "Only 000 and 111 should appear in the ideal simulator."
    else:
        qc = QuantumCircuit(1)
        qc.ry(theta, 0)
        expectation = "The probability of 1 is sin\u00b2(theta/2)."
    return qc, expectation


def sample_statevector(qc: QuantumCircuit, shots: int, seed: int = 7) -> tuple[dict[str, int], Statevector]:
    state = Statevector.from_instruction(qc)
    state.seed(seed)
    counts = dict(state.sample_counts(shots=shots))
    return counts, state


def score_quiz(items: list[dict[str, Any]], selected: list[str]) -> tuple[int, list[dict[str, Any]]]:
    correct = 0
    details = []
    for item, answer_text in zip(items, selected):
        selected_idx = item["options"].index(answer_text)
        is_correct = selected_idx == item["answer"]
        correct += int(is_correct)
        details.append({"question": item["q"], "correct": is_correct, "explanation": item["why"]})
    return correct, details


# ============================================================================
# App shell: landing page, sidebar, routing
# ============================================================================

init_state()
progress_model, risk_model, feature_importance, dnn_training_accuracy = train_ai_models()

current_page = st.session_state["page"]

if current_page != "Welcome":
    with st.sidebar:
        st.markdown(f'<p class="qp-sidebar-title">\u269B\uFE0F {APP_TITLE}</p>', unsafe_allow_html=True)
        st.caption("Adaptive quantum-computing education prototype")
        learner_name = st.text_input("Learner display name", value="Quantum Explorer")
        learner_level = st.selectbox("Current pathway", LEVELS, key="learner_level_select")
        weekly_hours = st.slider("Planned study hours per week", 1.0, 12.0, 4.0, 0.5)
        math_comfort = st.slider("Math comfort", 1, 5, 3, help="1 = developing; 5 = very comfortable")
        learner_goal = st.selectbox("Primary goal", LEVEL_META[learner_level]["goal_options"])
        st.markdown("---")
        page = st.radio(
            "Navigate",
            PAGE_KEYS,
            key="page",
            format_func=lambda k: f"{NAV_ICONS[k]}  {nav_label(learner_level, k)}",
        )
        st.markdown("---")
        level_total = len(CURRICULUM[learner_level])
        level_done = len(LEVEL_LESSON_IDS[learner_level] & set(st.session_state.completed_lessons))
        level_pct = 100 * level_done / level_total if level_total else 0
        st.progress(level_pct / 100, text=f"{learner_level} pathway: {level_pct:.0f}%")
        st.caption(f"\U0001F525 {st.session_state.streak}-day streak \u00b7 \u2B50 {st.session_state.xp} XP")
    inject_level_theme(learner_level)
else:
    # Sensible fallbacks so the shared feature/recommendation code below
    # (which runs on every page, including Welcome) has values to work with.
    learner_name = "Quantum Explorer"
    learner_level = "Elementary"
    weekly_hours = 4.0
    math_comfort = 3
    learner_goal = LEVEL_META["Elementary"]["goal_options"][0]
    page = "Welcome"

features_row = learner_features(learner_level, weekly_hours, math_comfort)
predicted_progress = float(progress_model.predict(features_row)[0])
risk_probability = float(risk_model.predict_proba(features_row)[0, 1])
risk_label = "Needs support" if risk_probability >= 0.58 else "On track"
recommended = find_recommended_lesson(learner_level)


def go_to(level: str) -> None:
    st.session_state["learner_level_select"] = level
    st.session_state["page"] = "Home"
    st.rerun()


# ============================================================================
# Welcome / landing page
# ============================================================================

if page == "Welcome":
    st.markdown(
        '<div class="qp-hero"><p class="qp-wordmark">\u269B QubitPath</p>'
        "<h1>Quantum computing,<br>explained at your speed.</h1>"
        '<p class="qp-hero-sub">Lessons, live tutoring, a real Qiskit lab, and an AI guide that adapts to how '
        "you learn \u2014 for explorers from third grade through senior year.</p></div>",
        unsafe_allow_html=True,
    )
    st.markdown(orbit_mark(), unsafe_allow_html=True)
    st.markdown('<p class="qp-choose-label" style="text-align:center;">Choose your path</p>', unsafe_allow_html=True)

    cols = st.columns(3)
    button_keys = {"Elementary": "pick_elementary", "Proficient": "pick_proficient", "Erudite": "pick_erudite"}
    for col, level in zip(cols, LEVELS):
        meta = LEVEL_META[level]
        with col:
            st.markdown(
                f'<div class="qp-pathcard"><span class="qp-path-icon">{meta["icon"]}</span>'
                f'<h3>{level}</h3><p class="qp-path-age">{meta["age_range"]}</p>'
                f'<p>{meta["blurb"]}</p></div>',
                unsafe_allow_html=True,
            )
            if st.button(f"Start {level}", key=button_keys[level], width="stretch"):
                go_to(level)

    st.markdown("<div style='height:2.4rem'></div>", unsafe_allow_html=True)
    st.markdown("### How QubitPath works")
    how = [
        ("\U0001F3AC", "Recorded lessons", "Work through leveled lessons at your own pace, then mark them complete to earn XP."),
        ("\U0001F9D1\u200D\U0001F3EB", "Live tutoring", "Book time with a tutor over Zoom, Teams, or Google Meet when you get stuck."),
        ("\U0001F9EA", "A real quantum lab", "Build circuits and run them on an ideal Qiskit simulator \u2014 not just a picture of one."),
        ("\U0001F916", "An AI guide that adapts", "Ask Professor Qubit questions, then rate the answer \u2014 the platform learns which teaching style helps."),
    ]
    hcols = st.columns(4)
    for hcol, (icon, title, text) in zip(hcols, how):
        with hcol:
            st.markdown(f'<div class="qp-howcard"><div class="qp-how-icon">{icon}</div><h4>{title}</h4><p class="qp-muted">{text}</p></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
    r1, r2 = st.columns(2)
    r1.link_button("IBM Quantum Learning catalog", IBM_COURSES_URL, width="stretch")
    r2.link_button("Qiskit documentation", QISKIT_DOCS_URL, width="stretch")

elif page == "Home":
    header("Learn quantum computing with an adaptive guide", "Structured pathways, hands-on labs, live tutoring, and transparent AI recommendations.")
    st.markdown(f"### Welcome, {learner_name} \U0001F44B")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current pathway", learner_level)
    c2.metric("4-week progress forecast", f"{predicted_progress:.0f}%")
    c3.metric("Learning status", risk_label, f"{risk_probability:.0%} support probability")
    c4.metric("Experience points", st.session_state.xp)

    st.markdown("### Your next best action")
    left, right = st.columns([1.55, 1])
    with left:
        track_pill = f'<span class="qp-pill">{recommended["track"]}</span>' if "track" in recommended else ""
        st.markdown(
            f"""
            <div class="qp-card">
              <span class="qp-pill">{recommended['id']}</span>{track_pill}<span class="qp-pill">{learner_level}</span>
              <h3>{recommended['title']}</h3>
              <p>{recommended['summary']}</p>
              <p class="qp-muted">Estimated time: {recommended['duration']} minutes \u00b7 Goal: {learner_goal}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            f"""
            <div class="qp-card">
              <h3>\U0001F9E0 Adaptive strategy</h3>
              <p><b>{st.session_state.current_strategy}</b></p>
              <p class="qp-muted">The contextual bandit updates this recommendation when you rate Professor Qubit's help.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Explore the platform")
    cols = st.columns(4)
    cards = [
        ("\U0001F3AC", "Recorded learning", "Study leveled modules, lesson notes, activities, and official references."),
        ("\U0001F9D1\u200D\U0001F3EB", "Live tutoring", "Book a prototype Zoom, Teams, or Google Meet session with a tutor."),
        (LEVEL_META[learner_level]["icon"], LEVEL_META[learner_level]["lab_name"], "Build and simulate quantum circuits with sampled measurements."),
        ("\U0001F4CA", nav_label(learner_level, "Analytics"), "Review progress, skill coverage, quiz history, and AI forecasts."),
    ]
    for col, (icon, title, text) in zip(cols, cards):
        with col:
            st.markdown(f'<div class="qp-card"><h2>{icon}</h2><h3>{title}</h3><p>{text}</p></div>', unsafe_allow_html=True)

    st.markdown("### How the AI components work")
    st.info(
        "Machine learning forecasts progress; a multilayer neural network estimates whether additional support may be helpful; "
        "a transparent retrieval tutor answers from curated notes; and a bandit learns which teaching format receives positive feedback."
    )
    st.warning("All predictions are demonstrations trained on synthetic data. A human tutor should review any learner-support decision.")

elif page == "Recorded Learning":
    header("Recorded learning library", "Choose a pathway, open a lesson, complete its activity, and track your progress.")
    tabs = st.tabs(LEVELS)
    for tab, level in zip(tabs, LEVELS):
        with tab:
            st.markdown(f"### {level} pathway")
            lessons = CURRICULUM[level]
            if level == "Erudite":
                track = st.radio("Track", ERUDITE_TRACKS, horizontal=True, key="erudite_track_select")
                lessons = [l for l in lessons if l["track"] == track]
            selected_title = st.selectbox(
                f"Select a {level.lower()} lesson",
                [f"{x['id']} \u2014 {x['title']}" for x in lessons],
                key=f"lesson_select_{level}",
            )
            lesson = lessons[[f"{x['id']} \u2014 {x['title']}" for x in lessons].index(selected_title)]
            a, b = st.columns([1.6, 1])
            with a:
                st.subheader(lesson["title"])
                st.caption(f"{lesson['duration']} minutes \u00b7 Difficulty {lesson['difficulty']}/3")
                st.markdown("**Learning objectives**")
                for objective in lesson["objectives"]:
                    st.markdown(f"- {objective}")
                st.markdown("**Lesson notes**")
                st.write(lesson["summary"])
                st.markdown("**Hands-on activity**")
                st.write(lesson["activity"])
                st.markdown("**Recording panel**")
                st.info(f"\U0001F3AC {lesson['recording']} \u2014 prototype slot. Replace the external resource link with your own hosted recording when available.")
                st.link_button(LEVEL_META[level]["resource_label"], lesson["resource"], width="stretch")
            with b:
                completed = lesson["id"] in st.session_state.completed_lessons
                st.markdown('<div class="qp-card">', unsafe_allow_html=True)
                st.markdown("#### Lesson checkpoint")
                st.write("Explain the key concept in your own words, complete the activity, then mark the lesson complete.")
                if completed:
                    st.success("Completed \u2713")
                elif st.button("Mark lesson complete", key=f"complete_{lesson['id']}", width="stretch"):
                    st.session_state.completed_lessons.append(lesson["id"])
                    st.session_state.xp += 40
                    st.success("Lesson completed. +40 XP")
                    st.rerun()
                st.markdown("#### Keep exploring")
                if level == "Elementary":
                    st.markdown("- Ask a grown-up to try the lesson with you")
                    st.markdown("- Try the mini-game in Quiz & Games")
                    st.markdown("- Retell the idea to someone in one sentence")
                elif level == "Proficient":
                    st.markdown("- Try the matching Circuit Playground experiment")
                    st.markdown("- Take the Proficient quiz for this topic")
                    st.markdown(f"- {LEVEL_META[level]['resource_label']} above, when you're ready to go deeper")
                else:
                    st.markdown("- IBM Quantum Learning course catalog")
                    st.markdown("- Qiskit documentation and tutorials")
                    st.markdown("- *Quantum Computing for Everyone* \u2014 Chris Bernhardt")
                    st.markdown("- *Introduction to Classical and Quantum Computing* \u2014 Thomas Wong")
                st.markdown("</div>", unsafe_allow_html=True)

elif page == "Live Tutoring":
    header("Live tutoring studio", "Schedule guided practice with a tutor through Zoom, Microsoft Teams, or Google Meet.")
    today = date.today()
    schedule = pd.DataFrame(
        [
            {"Tutor": "Ms. Priya Nair", "Focus": "Elementary explorers: coins, switches, and wonder", "Date": today + timedelta(days=1), "Time": "4:00 PM", "Seats": 4},
            {"Tutor": "Dr. Maya Chen", "Focus": "Proficient-level circuits and first Qiskit steps", "Date": today + timedelta(days=1), "Time": "5:00 PM", "Seats": 3},
            {"Tutor": "Alex Rivera", "Focus": "Erudite-level entanglement and algorithms", "Date": today + timedelta(days=2), "Time": "7:00 PM", "Seats": 2},
            {"Tutor": "Dr. Samir Patel", "Focus": "Erudite-level VQE, QAOA, and research prep", "Date": today + timedelta(days=4), "Time": "6:30 PM", "Seats": 1},
        ]
    )
    st.dataframe(schedule, hide_index=True, width="stretch")

    st.markdown("### Book a prototype session")
    with st.form("booking_form"):
        c1, c2 = st.columns(2)
        tutor = c1.selectbox("Tutor", schedule["Tutor"].tolist())
        platform = c2.selectbox("Meeting platform", ["Zoom", "Microsoft Teams", "Google Meet"])
        session_date = c1.date_input("Preferred date", value=today + timedelta(days=2), min_value=today)
        session_time = c2.time_input("Preferred time", value=datetime.strptime("18:00", "%H:%M").time())
        topic = st.text_area("Topic or question you want help with", placeholder="Example: I understand H and CNOT separately, but I need help interpreting Bell-state measurement results.")
        submitted = st.form_submit_button("Book demo session", width="stretch")
    if submitted:
        booking = {
            "Tutor": tutor,
            "Platform": platform,
            "Date": str(session_date),
            "Time": session_time.strftime("%I:%M %p"),
            "Topic": topic or "General quantum-computing guidance",
            "Status": "Requested",
        }
        st.session_state.bookings.append(booking)
        st.session_state.xp += 15
        st.success("Session request saved in this browser session. +15 XP")

    if st.session_state.bookings:
        st.markdown("### Your session requests")
        st.dataframe(pd.DataFrame(st.session_state.bookings), hide_index=True, width="stretch")
    st.markdown(
        '<div class="warning-box"><b>Production note:</b> Real meeting creation requires OAuth and the provider APIs. '
        "Store credentials in a secret manager, collect the minimum data needed, and obtain consent before recording sessions.</div>",
        unsafe_allow_html=True,
    )

elif page == "Quantum Lab":
    lab_name = LEVEL_META[learner_level]["lab_name"]

    if learner_level == "Elementary":
        header("The Magic Coin Machine", "Flip a quantum coin and see how many times it lands on each side.")
        st.markdown(
            '<div class="qp-card qp-dotgrid" style="text-align:center;">'
            '<p style="font-size:3rem;margin:.2rem 0;">\U0001FA99</p>'
            "<p>This is the same trick from <b>The Magic Spinning Coin</b> lesson: while it's \u201cspinning,\u201d it's a mix of heads and tails. "
            "Press the button to spin it 20 times and see what happens!</p></div>",
            unsafe_allow_html=True,
        )
        if st.button("Spin the Magic Coin! \U0001FA99", key="spin_coin_btn", type="primary", width="stretch"):
            qc, _ = make_circuit("Quantum coin (H gate)", 0.0)
            counts, _ = sample_statevector(qc, shots=20, seed=random.randint(0, 10_000))
            heads = counts.get("0", 0)
            tails = counts.get("1", 0)
            st.session_state.coin_spins = (heads, tails)
            st.session_state.xp += 10

        if st.session_state.coin_spins:
            heads, tails = st.session_state.coin_spins
            m1, m2 = st.columns(2)
            m1.metric("\U0001F642 Heads (0)", heads)
            m2.metric("\U0001F643 Tails (1)", tails)
            st.markdown(
                '<div class="success-box">About half heads, about half tails \u2014 that\u2019s superposition! '
                "Spin again and the exact numbers will wiggle a little, just like flipping a real coin.</div>",
                unsafe_allow_html=True,
            )

    else:
        if learner_level == "Proficient":
            header("Circuit Playground", "Build a simple circuit and compare your prediction with the sampled measurement counts.")
            experiment_options = ["Quantum coin (H gate)", "Bell entanglement"]
        else:
            header("Qiskit quantum laboratory", "Create an ideal circuit, inspect its state, and compare your prediction with sampled measurement counts.")
            experiment_options = ["Quantum coin (H gate)", "Bell entanglement", "Three-qubit GHZ", "Custom Ry rotation"]

        left, right = st.columns([1, 1.25])
        with left:
            experiment = st.selectbox("Experiment", experiment_options)
            theta = st.slider("Rotation angle \u03b8", 0.0, float(2 * np.pi), float(np.pi / 2), 0.05, disabled=experiment != "Custom Ry rotation")
            shots = st.select_slider("Measurement shots", options=[100, 256, 512, 1024, 2048, 4096], value=1024)
            prediction_options = ["Mostly 0", "Mostly 1", "Balanced outcomes", "Only correlated all-zero/all-one outcomes"]
            prediction = st.selectbox("Predict the dominant ideal outcome pattern", prediction_options)
            run_lab = st.button("Run quantum experiment", type="primary", width="stretch")
            st.caption("The simulator is ideal and does not include hardware noise.")

        qc, expectation = make_circuit(experiment, theta)
        with right:
            st.markdown("#### Circuit")
            fig = qc.draw(output="mpl", fold=-1)
            st.pyplot(fig, clear_figure=True)
            plt.close(fig)

        if run_lab:
            counts, state = sample_statevector(qc, shots)
            probability_df = pd.DataFrame({"State": list(counts.keys()), "Counts": list(counts.values())}).sort_values("State")
            c1, c2 = st.columns([1.2, 1])
            with c1:
                bar = px.bar(probability_df, x="State", y="Counts", text="Counts", title="Sampled measurement counts")
                bar.update_layout(yaxis_title="Counts", xaxis_title="Computational basis state")
                st.plotly_chart(bar, width="stretch")
            with c2:
                n_qubits = qc.num_qubits
                if learner_level == "Erudite":
                    st.markdown("#### Statevector amplitudes")
                    amplitude_rows = []
                    for idx, amp in enumerate(state.data):
                        amplitude_rows.append(
                            {"basis": format(idx, f"0{n_qubits}b"), "real": float(np.real(amp)), "imag": float(np.imag(amp)), "probability": float(abs(amp) ** 2)}
                        )
                    st.dataframe(pd.DataFrame(amplitude_rows), hide_index=True, width="stretch")
                else:
                    st.markdown("#### Outcome probabilities")
                    probability_rows = [
                        {"basis": format(idx, f"0{n_qubits}b"), "probability": f"{float(abs(amp) ** 2):.0%}"}
                        for idx, amp in enumerate(state.data)
                    ]
                    st.dataframe(pd.DataFrame(probability_rows), hide_index=True, width="stretch")
                st.info(expectation)

            expected_prediction = {
                "Quantum coin (H gate)": "Balanced outcomes",
                "Bell entanglement": "Only correlated all-zero/all-one outcomes",
                "Three-qubit GHZ": "Only correlated all-zero/all-one outcomes",
                "Custom Ry rotation": "Mostly 0" if theta < np.pi / 2 or theta > 3 * np.pi / 2 else ("Mostly 1" if np.pi / 2 < theta < 3 * np.pi / 2 else "Balanced outcomes"),
            }[experiment]
            success = prediction == expected_prediction
            if success and st.session_state.last_lab_success != (experiment, prediction, round(theta, 2)):
                st.session_state.xp += 25
                st.session_state.last_lab_success = (experiment, prediction, round(theta, 2))
                st.success("Your prediction matched the ideal pattern. +25 XP")
            elif success:
                st.success("Your prediction matched the ideal pattern.")
            else:
                st.warning(f"Compare your prediction with this expectation: {expectation}")

elif page == "Quiz & Games":
    header("Quizzes and mini-games", "Check understanding immediately and turn practice into an active learning loop.")
    quiz_level = st.selectbox("Quiz level", LEVELS, index=LEVELS.index(learner_level))

    if quiz_level == "Erudite":
        quiz_track = st.radio("Quiz track", ERUDITE_TRACKS, horizontal=True, key="quiz_track_select")
        quiz_items = QUIZZES["Erudite"][quiz_track]
        quiz_key = f"Erudite_{quiz_track}"
    else:
        quiz_items = QUIZZES[quiz_level]
        quiz_key = quiz_level

    with st.form(f"quiz_{quiz_key}"):
        selected_answers = []
        for idx, item in enumerate(quiz_items, start=1):
            selected_answers.append(st.radio(f"{idx}. {item['q']}", item["options"], key=f"{quiz_key}_{idx}"))
        quiz_submit = st.form_submit_button("Submit quiz", width="stretch")
    if quiz_submit:
        correct, details = score_quiz(quiz_items, selected_answers)
        score_pct = 100 * correct / len(quiz_items)
        st.session_state.quiz_history.append({"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "level": quiz_level, "score_pct": score_pct})
        gained = int(10 * correct)
        st.session_state.xp += gained
        st.metric("Quiz score", f"{correct}/{len(quiz_items)}", f"+{gained} XP")
        for detail in details:
            if detail["correct"]:
                st.success(f"\u2713 {detail['question']} \u2014 {detail['explanation']}")
            else:
                st.error(f"Review: {detail['question']} \u2014 {detail['explanation']}")

    if quiz_level == "Elementary":
        st.markdown("### Spin-the-Qubit mini-game")
        st.write("Guess which side you think will win, then spin 10 magic coins and see who was right \u2014 you or chance!")
        guess = st.selectbox("Your guess: which side wins?", ["Heads", "Tails", "It'll be close!"])
        if st.button("Spin 10 coins", key="spin10_btn", width="stretch"):
            heads = sum(1 for _ in range(10) if random.random() < 0.5)
            tails = 10 - heads
            winner = "Heads" if heads > tails else ("Tails" if tails > heads else "It'll be close!")
            st.write(f"Result: \U0001F642 Heads {heads} \u2014 Tails {tails} \U0001F643")
            if guess == winner:
                st.success("Nice guess! Quantum coins are random, so that's a fun coincidence.")
            else:
                st.info("No match this time \u2014 that's expected, since each spin is random.")
    else:
        st.markdown("### Gate-matching mini-game")
        game_col1, game_col2 = st.columns(2)
        challenge = game_col1.selectbox("Target transformation", ["Turn |0> into |1>", "Create equal probabilities from |0>", "Add a phase flip to |1>"])
        chosen_gate = game_col2.selectbox("Choose a gate", ["X", "H", "Z"])
        solution = {"Turn |0> into |1>": "X", "Create equal probabilities from |0>": "H", "Add a phase flip to |1>": "Z"}[challenge]
        if st.button("Check gate", key="check_gate_btn", width="stretch"):
            if chosen_gate == solution:
                st.success("Correct. The selected gate matches the target transformation.")
            else:
                st.warning(f"Try again. The best match is the {solution} gate.")

elif page == "AI Professor":
    header("Professor Qubit", "A transparent AI tutor that retrieves curated concepts and adapts its teaching format from feedback.")
    st.markdown(
        '<div class="qp-professor"><div class="qp-avatar">\u269B\uFE0F</div><div><h3>Professor Qubit</h3>'
        "<p>Ask a quantum question. I will cite the closest built-in concept, tailor the depth to your pathway, and show the teaching strategy being tested.</p></div></div>",
        unsafe_allow_html=True,
    )
    st.caption(f"Current adaptive strategy: {st.session_state.current_strategy}")

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask Professor Qubit a question\u2026")
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        answer = professor_answer(prompt, learner_level, st.session_state.current_strategy)
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()

    if len(st.session_state.chat_history) > 1:
        st.markdown("#### Was the most recent teaching approach useful?")
        f1, f2, f3 = st.columns([1, 1, 3])
        if f1.button("\U0001F44D Helpful", key="fb_helpful", width="stretch"):
            update_bandit(st.session_state.current_strategy, 1)
            st.success("Feedback recorded. The adaptive policy has been updated.")
        if f2.button("\U0001F44E Not helpful", key="fb_not_helpful", width="stretch"):
            update_bandit(st.session_state.current_strategy, 0)
            st.info("Feedback recorded. The platform will explore another teaching format.")
        with f3:
            st.caption("This is an epsilon-greedy contextual-bandit demonstration, not autonomous self-evolution.")

    with st.expander("See the current bandit learning table"):
        bandit_df = pd.DataFrame(
            {
                "Teaching strategy": TEACHING_ARMS,
                "Estimated reward": [st.session_state.bandit_values[a] for a in TEACHING_ARMS],
                "Feedback count": [st.session_state.bandit_counts[a] for a in TEACHING_ARMS],
            }
        )
        st.dataframe(bandit_df, hide_index=True, width="stretch")

elif page == "Analytics":
    header(f"{nav_label(learner_level, 'Analytics')}: learning dashboard", "Review behavior, outcomes, forecasts, and model inputs without treating AI output as a final decision.")

    level_total = len(CURRICULUM[learner_level])
    level_done = len(LEVEL_LESSON_IDS[learner_level] & set(st.session_state.completed_lessons))
    all_total = sum(len(v) for v in CURRICULUM.values())

    m1, m2, m3, m4 = st.columns(4)
    m1.metric(f"{learner_level} lessons", f"{level_done}/{level_total}")
    m2.metric("Quiz average", f"{get_quiz_average():.0f}%")
    m3.metric("4-week forecast", f"{predicted_progress:.0f}%")
    m4.metric("Support status", risk_label, f"{risk_probability:.0%}")
    st.caption(f"Across all three pathways: {len(st.session_state.completed_lessons)}/{all_total} lessons completed.")

    c1, c2 = st.columns(2)
    with c1:
        activity_fig = px.line(st.session_state.weekly_activity, x="week", y=["minutes", "quiz_accuracy"], markers=True, title="Weekly activity and quiz accuracy")
        activity_fig.update_layout(legend_title_text="Metric")
        st.plotly_chart(activity_fig, width="stretch")
    with c2:
        forecast_weeks = np.arange(0, 5)
        current_completion = 100 * len(st.session_state.completed_lessons) / all_total
        projected = np.clip(current_completion + forecast_weeks * predicted_progress / 4.0, 0, 100)
        forecast_df = pd.DataFrame({"Week": forecast_weeks, "Projected curriculum completion": projected})
        forecast_fig = px.area(forecast_df, x="Week", y="Projected curriculum completion", title="Illustrative completion trajectory (all pathways)")
        forecast_fig.update_yaxes(range=[0, 100], ticksuffix="%")
        st.plotly_chart(forecast_fig, width="stretch")

    c3, c4 = st.columns(2)
    with c3:
        completed_set = set(st.session_state.completed_lessons)
        skill_scores = {
            "Foundations": min(100, 20 + 13 * len(completed_set & {"EL1", "EL2", "MS1", "MS2", "HF1", "HF2"})),
            "Circuits & gates": min(100, 20 + 20 * len(completed_set & {"EL3", "MS3", "HF3", "HF4"})),
            "Entanglement": min(100, 20 + 20 * len(completed_set & {"EL4", "MS4", "HA2", "HA3"})),
            "Algorithms": min(100, 15 + 28 * len(completed_set & {"HA4", "HR2", "HR3"})),
            "Quantum math": min(100, 15 + 28 * len(completed_set & {"HA1", "HR1", "HR4"})),
        }
        radar = go.Figure()
        radar.add_trace(go.Scatterpolar(r=list(skill_scores.values()), theta=list(skill_scores.keys()), fill="toself", name="Skill score"))
        radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, title="Skill coverage profile (all pathways)")
        st.plotly_chart(radar, width="stretch")
    with c4:
        if st.session_state.quiz_history:
            quiz_df = pd.DataFrame(st.session_state.quiz_history)
            quiz_fig = px.bar(quiz_df, x="date", y="score_pct", color="level", title="Quiz history", range_y=[0, 100])
            st.plotly_chart(quiz_fig, width="stretch")
        else:
            st.info("Complete a quiz to populate the quiz-history chart.")

    st.markdown("### Why the progress model made its forecast")
    importance_fig = px.bar(feature_importance.sort_values("importance"), x="importance", y="feature", orientation="h", title="Random-forest global feature importance on synthetic training data")
    st.plotly_chart(importance_fig, width="stretch")
    st.caption(f"The support-risk neural network uses hidden layers (64, 32, 16). Synthetic-data training accuracy: {dnn_training_accuracy:.1%}. This number does not validate real-world performance.")

    report = {
        "learner": learner_name,
        "pathway": learner_level,
        "goal": learner_goal,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "lessons_completed": st.session_state.completed_lessons,
        "quiz_average": get_quiz_average(),
        "xp": st.session_state.xp,
        "four_week_progress_forecast": predicted_progress,
        "support_risk_probability": risk_probability,
        "support_status": risk_label,
        "recommended_next_lesson": recommended["id"],
    }
    r1, r2 = st.columns(2)
    r1.download_button("Download learner report (JSON)", json.dumps(report, indent=2), file_name="qubitpath_learner_report.json", mime="application/json", width="stretch")
    csv_report = pd.DataFrame([report | {"lessons_completed": ",".join(report["lessons_completed"])}]).to_csv(index=False)
    r2.download_button("Download learner report (CSV)", csv_report, file_name="qubitpath_learner_report.csv", mime="text/csv", width="stretch")

else:  # Responsible AI
    if learner_level == "Erudite":
        header("Responsible AI and production roadmap", "Build learner trust through transparency, privacy, accessibility, evaluation, and human oversight.")
    else:
        header(nav_label(learner_level, "Responsible AI"), "What this prototype does with your family's data, and what a real product still needs to add.")

    st.markdown("### What this prototype does")
    st.markdown(
        """
        - Uses **synthetic data** to demonstrate progress forecasting and learner-support risk prediction.
        - Uses a **curated retrieval tutor** rather than pretending that a generic language model is always correct.
        - Uses a small **epsilon-greedy bandit** to learn which teaching format receives positive feedback.
        - Keeps all session data in Streamlit's temporary browser/server session state.
        """
    )
    st.markdown("### What a production platform still needs")
    roadmap = pd.DataFrame(
        [
            ["Identity and roles", "Student, tutor, parent/guardian, instructor, and administrator permissions", "High"],
            ["Persistent database", "Encrypted learner profiles, progress events, content, and audit logs", "High"],
            ["Live-session APIs", "OAuth integration for Zoom, Teams, or Google Meet", "High"],
            ["Content management", "Instructor upload, captioning, transcripts, versioning, and moderation", "High"],
            ["Model evaluation", "Real holdout data, subgroup analysis, calibration, drift monitoring, and tutor review", "High"],
            ["Accessibility", "Keyboard navigation, captions, transcripts, readable contrast, and screen-reader testing", "High"],
            ["Security", "Secret management, least privilege, rate limiting, backups, and incident response", "High"],
            ["Age-appropriate controls", "Parental consent, content filtering per pathway, and COPPA-aware data handling for younger learners", "High"],
            ["Optional LLM tutor", "Grounded generation, citation checks, refusal behavior, and age-appropriate controls", "Medium"],
            ["Real quantum hardware", "IBM Quantum credentials, job limits, cost controls, and queue feedback", "Medium"],
        ],
        columns=["Capability", "Production requirement", "Priority"],
    )
    st.dataframe(roadmap, hide_index=True, width="stretch")

    st.markdown("### Guardrails")
    g1, g2, g3 = st.columns(3)
    with g1:
        st.markdown('<div class="qp-card">\U0001F512 <b>Privacy</b><p>Minimize data collection, encrypt records, define retention limits, and obtain consent for recordings and, for younger learners, parental consent.</p></div>', unsafe_allow_html=True)
    with g2:
        st.markdown('<div class="qp-card">\U0001F9D1\u200D\U0001F3EB <b>Human oversight</b><p>Never use a risk score as an automatic grade or penalty. Let tutors review context and learner preferences.</p></div>', unsafe_allow_html=True)
    with g3:
        st.markdown('<div class="qp-card">\U0001F4D0 <b>Evaluation</b><p>Measure learning gains, calibration, false alerts, accessibility, and performance across every age pathway.</p></div>', unsafe_allow_html=True)

    st.markdown("### Official learning references")
    ref1, ref2 = st.columns(2)
    ref1.link_button("IBM Quantum Learning catalog", IBM_COURSES_URL, width="stretch")
    ref2.link_button("Qiskit documentation", QISKIT_DOCS_URL, width="stretch")
