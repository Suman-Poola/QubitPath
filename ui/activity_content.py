"""Hands-on activities for every lesson in app.py's CURRICULUM.

Each lesson id maps to an activity: a ``title`` and a list of ``parts``. The
lesson's own one-line ``activity`` text (in CURRICULUM) is shown as the intro.
A part is a dict with ``title``, an optional ``prompt`` (Markdown) and a
``kind``, rendered by ui/activities.py:

* ``"sort"``: put each of ``items`` (``text``, ``answer``, ``why``) into one of
  ``categories``.
* ``"order"``: arrange ``steps`` (listed here in the correct order).
* ``"check"``: one multiple-choice question (``question``, ``options``,
  ``answer``, ``why``), as in a walkthrough step.
* ``"widget"``: a custom experiment ``name``d in ui/activity_widgets.py.

Activities practise what the lesson's walkthrough taught (and cites), so the
facts here come from the same sources. tests/test_activities.py re-checks every
answer with Qiskit: which recipes give which results, which vectors are valid
states, and what each error does to the repetition code.
"""

from __future__ import annotations

from typing import Any

import numpy as np

_S = 1 / np.sqrt(2)
_ONE_QUBIT_KID_MENU = {"(empty)": None, "X": ("x", 0), "H": ("h", 0)}
_ONE_QUBIT_MENU = {"(empty)": None, "X": ("x", 0), "H": ("h", 0), "Z": ("z", 0)}
_TWO_QUBIT_MENU = {
    "(empty)": None,
    "H on qubit 0": ("h", 0),
    "H on qubit 1": ("h", 1),
    "X on qubit 0": ("x", 0),
    "X on qubit 1": ("x", 1),
    "CX: control 0, target 1": ("cx", 0, 1),
}
_SWITCH_RECIPES = {
    "Flip": [("x", 0)],
    "Maybe": [("h", 0)],
    "Flip → Flip": [("x", 0), ("x", 0)],
    "Maybe → Maybe": [("h", 0), ("h", 0)],
    "Flip → Maybe": [("x", 0), ("h", 0)],
}

ACTIVITIES: dict[str, dict[str, Any]] = {
    # =====================================================================
    # Elementary (ages 7-10)
    # =====================================================================
    "EL1": {
        "title": "Bit hunt",
        "kid": True,
        "parts": [
            {
                "kind": "sort",
                "title": "Which ones work like a bit?",
                "prompt": "A bit has exactly **two** ways to be, like a light switch: off (0) or on (1). Sort each thing.",
                "categories": ["Works like a bit", "Not a bit"],
                "items": [
                    {"text": "\U0001F4A1 A light switch: on or off", "answer": 0, "why": "Only two ways to be: off is 0, on is 1."},
                    {"text": "\U0001F6AA A door: open or closed", "answer": 0, "why": "Two ways: closed could be 0 and open could be 1."},
                    {"text": "\U0001F50A A volume knob that turns to lots of levels", "answer": 1, "why": "It has lots of levels, not just two."},
                    {"text": "\U0001F58D️ A box of 24 crayons", "answer": 1, "why": "24 colors is way more than two choices."},
                    {"text": "\U0001FA99 A coin lying on the table: heads or tails", "answer": 0, "why": "Heads or tails: exactly two ways, just like 0 and 1."},
                    {"text": "\U0001F321️ A thermometer", "answer": 1, "why": "A temperature can be lots of different numbers."},
                ],
            },
            {
                "kind": "widget",
                "name": "room_bits",
                "title": "Bit hunt in your room",
                "prompt": "Now look around your room. Find three things that are only ever one of two ways, and type them in.",
            },
        ],
    },
    "EL2": {
        "title": "Coin race",
        "kid": True,
        "parts": [
            {
                "kind": "widget",
                "name": "coin_race",
                "title": "Your coin vs. the magic coin",
                "prompt": (
                    "Flip a real coin 10 times and type in how many heads and tails you got. (No coin? Use the pretend one.) "
                    "Then spin the magic coin the same number of times and compare."
                ),
            },
            {
                "kind": "check",
                "title": "What did you notice?",
                "question": "When you flip or spin lots and lots of times, what happens?",
                "options": [
                    "Both coins land on heads about half the time",
                    "The magic coin always lands on heads",
                    "The real coin always lands on tails",
                ],
                "answer": 0,
                "why": "Both are random, and over many tries each side comes up about half the time. The magic coin is a (simulated) qubit!",
            },
        ],
    },
    "EL3": {
        "title": "Switch matching game",
        "kid": True,
        "parts": [
            {
                "kind": "sort",
                "title": "Match each recipe to its trick",
                "prompt": "You always start at **0**. Match each switch recipe to what it does.",
                "categories": ["1 every time", "Spinning coin: half 0, half 1", "Back to 0 every time"],
                "items": [
                    {"text": "Flip", "answer": 0, "why": "The Flip switch (X) turns 0 into 1."},
                    {"text": "Maybe", "answer": 1, "why": "The Maybe switch (H) makes a spinning magic coin."},
                    {"text": "Flip → Flip", "answer": 2, "why": "The second Flip undoes the first: 0 → 1 → 0."},
                    {"text": "Maybe → Maybe", "answer": 2, "why": "Surprise! The second Maybe undoes the first, so you get 0 every time."},
                    {"text": "Flip → Maybe", "answer": 1, "why": "Flip makes 1, then Maybe turns it into a spinning coin."},
                ],
            },
            {
                "kind": "widget",
                "name": "recipe_proof",
                "title": "Prove it on the simulator",
                "prompt": "Run every recipe on a (simulated) qubit and check your matches.",
                "recipes": _SWITCH_RECIPES,
            },
        ],
    },
    "EL4": {
        "title": "The partner-coin game",
        "kid": True,
        "parts": [
            {
                "kind": "widget",
                "name": "partner_game",
                "rounds": 5,
                "title": "Guess your friend's coin",
                "prompt": (
                    "Make a pair of coins and peek at **your** coin. Guess what your friend's coin shows, then reveal it. "
                    "Play 5 rounds with partner coins, then try ordinary coins and see the difference."
                ),
            },
        ],
    },
    # =====================================================================
    # Proficient (ages 11-13)
    # =====================================================================
    "MS1": {
        "title": "Bit, qubit, or both?",
        "parts": [
            {
                "kind": "sort",
                "title": "Sort the statements",
                "prompt": "Is each statement true of a classical bit, of a qubit, or of both?",
                "categories": ["Classical bit", "Qubit", "Both"],
                "items": [
                    {"text": "It is always exactly 0 or exactly 1, even when we don't know which", "answer": 0,
                     "why": "A classical bit really is in one of its two states; probabilities only describe what we know."},
                    {"text": "It can be in a superposition such as |+⟩", "answer": 1,
                     "why": "Only a qubit has states like |+⟩ = (1/√2)|0⟩ + (1/√2)|1⟩."},
                    {"text": "Reading (measuring) it gives a 0 or a 1", "answer": 2,
                     "why": "Measuring a qubit shows a classical state, 0 or 1, just like reading a bit."},
                    {"text": "It stores the photos and games on your phone", "answer": 0,
                     "why": "Phones are classical computers: they store everything in bits."},
                    {"text": "IBM's Heron processors are built from these", "answer": 1,
                     "why": "Heron is a family of IBM quantum processors, and those are built from qubits."},
                ],
            },
        ],
    },
    "MS2": {
        "title": "Percent challenge",
        "parts": [
            {
                "kind": "widget",
                "name": "percent_challenge",
                "title": "Turn counts into percents",
                "prompt": (
                    "Run each circuit, then work out the percent of shots that came out **1**: "
                    "(number of 1s ÷ shots) × 100. Type your answer (one decimal place is plenty)."
                ),
            },
        ],
    },
    "MS3": {
        "title": "Circuit builder",
        "parts": [
            {
                "kind": "widget",
                "name": "circuit_builder",
                "title": "Build, predict, run",
                "prompt": (
                    "Put up to three gates on the wire (they happen left to right), predict the result, then run 1000 shots. "
                    "Solve all three challenges."
                ),
                "qubits": 1,
                "slots": 3,
                "menu": _ONE_QUBIT_KID_MENU,
                "challenges": [
                    {"label": "Get 1 every time", "probs": {"1": 1.0}},
                    {"label": "Make a 50/50 coin", "probs": {"0": 0.5, "1": 0.5}},
                    {"label": "Use at least two gates and still get 0 every time", "probs": {"0": 1.0}, "min_gates": 2},
                ],
            },
        ],
    },
    "MS4": {
        "title": "Build the spooky pair yourself",
        "parts": [
            {
                "kind": "widget",
                "name": "circuit_builder",
                "title": "Two-qubit builder",
                "prompt": (
                    "Pick up to three gates (they happen left to right; qubit 0 is the right-hand digit of each result). "
                    "Predict which results will appear, then run."
                ),
                "qubits": 2,
                "slots": 3,
                "menu": _TWO_QUBIT_MENU,
                "challenges": [
                    {"label": "Bell pair: only 00 and 11, half each", "probs": {"00": 0.5, "11": 0.5}},
                    {"label": "Opposite partners: only 01 and 10, half each", "probs": {"01": 0.5, "10": 0.5}},
                ],
            },
            {
                "kind": "check",
                "title": "Confirm it",
                "question": "In your Bell-pair runs, how often did 01 or 10 show up?",
                "options": ["Never", "About half the time", "About a quarter of the time"],
                "answer": 0,
                "why": "The Bell pair (1/√2)|00⟩ + (1/√2)|11⟩ has no |01⟩ or |10⟩ part, so those results can't appear.",
            },
        ],
    },
    # =====================================================================
    # Erudite (ages 14-18)
    # =====================================================================
    "HF1": {
        "title": "State or not? Quantum or not?",
        "parts": [
            {
                "kind": "sort",
                "title": "Valid qubit states",
                "prompt": r"A qubit state vector $\alpha|0\rangle + \beta|1\rangle$ needs $|\alpha|^2 + |\beta|^2 = 1$. Which vectors are valid?",
                "categories": ["Valid state", "Not valid"],
                "items": [
                    {"text": r"$\tfrac{1}{\sqrt2}|0\rangle + \tfrac{1}{\sqrt2}|1\rangle$", "answer": 0, "vector": [_S, _S],
                     "why": r"$\tfrac12 + \tfrac12 = 1$."},
                    {"text": r"$\tfrac12|0\rangle + \tfrac12|1\rangle$", "answer": 1, "vector": [0.5, 0.5],
                     "why": r"$\tfrac14 + \tfrac14 = \tfrac12$, not 1."},
                    {"text": r"$\tfrac35|0\rangle - \tfrac{4i}{5}|1\rangle$", "answer": 0, "vector": [3 / 5, -4j / 5],
                     "why": r"$\tfrac{9}{25} + \tfrac{16}{25} = 1$: complex entries are fine."},
                    {"text": r"$|0\rangle + |1\rangle$", "answer": 1, "vector": [1, 1],
                     "why": r"$1 + 1 = 2$. Dividing both amplitudes by $\sqrt2$ would fix it."},
                    {"text": r"$\tfrac12|0\rangle + \tfrac{\sqrt3}{2}i|1\rangle$", "answer": 0, "vector": [0.5, np.sqrt(3) / 2 * 1j],
                     "why": r"$\tfrac14 + \tfrac34 = 1$."},
                    {"text": r"$-|1\rangle$", "answer": 0, "vector": [0, -1],
                     "why": r"$|-1|^2 = 1$: negative entries are allowed."},
                ],
            },
            {
                "kind": "sort",
                "title": "Realistic use cases",
                "prompt": "IBM notes that quantum computing is of particular interest for chemistry and materials science. Sort each task.",
                "categories": ["Classical computers already do this well", "A research target for quantum computers"],
                "items": [
                    {"text": "Sending a text message", "answer": 0, "why": "Everyday communication runs well on classical bits."},
                    {"text": "Simulating how molecules behave, for chemistry research", "answer": 1,
                     "why": "IBM: quantum computing is “of particular interest for chemistry and material science applications.”"},
                    {"text": "Editing a video", "answer": 0, "why": "Media editing is a classical workload."},
                    {"text": "Modeling a new material atom by atom", "answer": 1,
                     "why": "Modeling physical systems is where IBM says quantum computers have “certain advantages.”"},
                    {"text": "Adding up a shopping list", "answer": 0, "why": "Simple arithmetic is trivial for a classical computer."},
                ],
            },
        ],
    },
    "HF2": {
        "title": "Born-rule drill",
        "parts": [
            {
                "kind": "widget",
                "name": "born_rule_drill",
                "needed": 3,
                "title": "Predict, then sample",
                "prompt": r"Pick a state, predict $\Pr(1) = |\beta|^2$, then sample it and compare. Get three right.",
            },
        ],
    },
    "HF3": {
        "title": "Gate puzzles",
        "parts": [
            {
                "kind": "widget",
                "name": "circuit_builder",
                "title": "Single-qubit puzzles",
                "prompt": (
                    "Build circuits from X, Z and H (applied left to right to $|0\\rangle$). After each run the page shows "
                    "the statevector, so you can check states that measurement alone can't tell apart."
                ),
                "qubits": 1,
                "slots": 3,
                "menu": _ONE_QUBIT_MENU,
                "show_state": True,
                "challenges": [
                    {"label": "Always measure 1, using only H and Z", "probs": {"1": 1.0}, "only": ["H", "Z"]},
                    {"label": "Prepare |−⟩ (up to a global phase)", "state": [_S, -_S]},
                    {"label": "End in |0⟩ using at least three gates", "state": [1, 0], "min_gates": 3},
                ],
            },
        ],
    },
    "HF4": {
        "title": "Assemble your first program",
        "parts": [
            {
                "kind": "widget",
                "name": "circuit_builder",
                "title": "Write the Bell program",
                "prompt": "Choose the two gate lines of the program. The page shows the full Qiskit program and runs exactly that.",
                "qubits": 2,
                "slots": 2,
                "show_code": True,
                "menu": {
                    "(empty)": None,
                    "qc.h(0)": ("h", 0),
                    "qc.h(1)": ("h", 1),
                    "qc.x(0)": ("x", 0),
                    "qc.cx(0, 1)": ("cx", 0, 1),
                    "qc.cx(1, 0)": ("cx", 1, 0),
                },
                "challenges": [{"label": "Make the Bell state: only 00 and 11, half each", "probs": {"00": 0.5, "11": 0.5}}],
            },
            {
                "kind": "check",
                "title": "Explain the zeros",
                "question": "Why do 01 and 10 never appear in the ideal simulator?",
                "options": [
                    "Their amplitudes are exactly 0, so the Born rule gives them probability 0",
                    "The simulator throws away unlikely results to save time",
                    "They do appear, but the chart rounds them down to 0",
                ],
                "answer": 0,
                "why": r"The state is $\tfrac{1}{\sqrt2}|00\rangle + \tfrac{1}{\sqrt2}|11\rangle$: zero amplitude means zero probability. Noisy hardware can still show them.",
            },
        ],
    },
    "HA1": {
        "title": "Basis states and product states",
        "parts": [
            {
                "kind": "widget",
                "name": "basis_list",
                "qubits": 3,
                "title": "List the basis",
                "prompt": "Type all eight standard basis states of a three-qubit register.",
            },
            {
                "kind": "widget",
                "name": "product_state_predict",
                "title": "Predict a product state",
                "prompt": (
                    "Choose a state for each qubit (qubit 2 is the leftmost factor). Before checking, select every basis state "
                    "whose amplitude will be nonzero. Use at least one |+⟩ or |−⟩."
                ),
            },
        ],
    },
    "HA2": {
        "title": "Bell-state statistics lab",
        "parts": [
            {
                "kind": "widget",
                "name": "bell_statistics",
                "title": "Run it many times",
                "prompt": "Pick a Bell state and run it five times at each shot count. Watch how much the results wobble from run to run.",
            },
            {
                "kind": "check",
                "title": "Read the spread",
                "question": "How did the run-to-run spread change from 10 to 1000 shots?",
                "options": [
                    "It shrank, roughly 10× (statistical spread scales like 1/√shots)",
                    "It stayed about the same",
                    "It grew, because more shots means more randomness",
                ],
                "answer": 0,
                "why": "100× more shots shrinks the fluctuations by about √100 = 10×. Which outcomes can appear never changes.",
            },
        ],
    },
    "HA3": {
        "title": "Map the information flow",
        "parts": [
            {
                "kind": "widget",
                "name": "teleport_flow",
                "title": "Label the channels",
                "prompt": "Label each arrow in the teleportation diagram as a quantum or a classical channel.",
            },
            {
                "kind": "order",
                "title": "Put teleportation in order",
                "steps": [
                    "Alice and Bob share an e-bit: Alice holds A, Bob holds B",
                    "Alice applies a CNOT (Q control, A target), then a Hadamard on Q",
                    "Alice measures A and Q, getting the bits a and b",
                    "Alice sends a and b to Bob over a classical channel",
                    "Bob applies X to B if a = 1, then Z if b = 1",
                ],
                "why": "Bob can't finish until Alice's two bits arrive.",
            },
            {
                "kind": "check",
                "title": "Now superdense coding",
                "question": "In superdense coding, what does Alice send to Bob?",
                "options": [
                    "One qubit (A), which carries two classical bits",
                    "Two classical bits, over an ordinary channel",
                    "One qubit plus two classical bits",
                ],
                "answer": 0,
                "why": "Alice encodes c and d by applying Z and/or X to A and sends A: one qubit plus the shared e-bit carries two bits.",
            },
        ],
    },
    "HA4": {
        "title": "Trace a Grover iteration",
        "parts": [
            {
                "kind": "widget",
                "name": "grover_trace",
                "title": "N = 4, one marked item",
                "prompt": (
                    r"Pick the marked item, then predict its amplitude before each stage: the initial Hadamards, then one "
                    r"Grover iteration $G = H Z_{\mathrm{OR}} H Z_f$."
                ),
            },
        ],
    },
    "HR1": {
        "title": "Noise detective",
        "parts": [
            {
                "kind": "widget",
                "name": "noise_detective",
                "title": "What does the noise erase?",
                "prompt": (
                    "For each case, look at the ideal density matrix and predict what the channel does. "
                    "A correct answer reveals the noisy matrix, computed with Qiskit's DensityMatrix."
                ),
            },
        ],
    },
    "HR2": {
        "title": "VQE workflow and failure lab",
        "parts": [
            {
                "kind": "order",
                "title": "Sketch the loop",
                "steps": [
                    "Choose the Hamiltonian H and a parameterized ansatz",
                    "Pick initial parameters θ₀",
                    "Quantum step: prepare the ansatz state and estimate ⟨H⟩ with the Estimator",
                    "Classical step: the optimizer chooses the next parameters",
                    "Repeat the last two steps until the energy stops improving",
                ],
            },
            {
                "kind": "widget",
                "name": "vqe_failure_lab",
                "title": "Find the failure",
                "prompt": "Run three VQE setups on the same toy Hamiltonian, then diagnose each one.",
            },
        ],
    },
    "HR3": {
        "title": "Encode your own Max-Cut",
        "parts": [
            {
                "kind": "widget",
                "name": "maxcut_builder",
                "title": "Graph → Hamiltonian → QAOA → answer",
                "prompt": "Design a graph, read off its cost Hamiltonian, predict its maximum cut, then let p = 1 QAOA find one.",
            },
        ],
    },
    "HR4": {
        "title": "Break the repetition code",
        "parts": [
            {
                "kind": "widget",
                "name": "break_the_code",
                "title": "Inject errors",
                "prompt": "Encode a state, inject up to two errors, and watch the syndrome and the recovery.",
            },
            {
                "kind": "sort",
                "title": "Name the limitations",
                "prompt": "Based on your experiments, what does the 3-qubit repetition code do with each error?",
                "categories": ["Detected and corrected", "Detected, but the wrong qubit gets “corrected”", "Not detected at all"],
                "items": [
                    {"text": "One bit flip (X on any single qubit)", "answer": 0, "errors": [("x", 1)],
                     "why": "The syndrome points at the flipped qubit, and flipping it back restores the state."},
                    {"text": "Two bit flips (X on qubits 0 and 1)", "answer": 1, "errors": [("x", 0), ("x", 1)],
                     "why": "The syndrome blames qubit 2; flipping it leaves 111 in place of 000, a logical bit flip."},
                    {"text": "Three bit flips (X on every qubit)", "answer": 2, "errors": [("x", 0), ("x", 1), ("x", 2)],
                     "why": "000 becomes 111, another codeword, so every parity check passes."},
                    {"text": "One phase flip (Z on qubit 1)", "answer": 2, "errors": [("z", 1)],
                     "why": "Z doesn't change any parity, so the syndrome is 00, yet the logical state picks up a phase flip."},
                ],
            },
        ],
    },
}
