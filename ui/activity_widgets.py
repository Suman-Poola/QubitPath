"""Interactive parts of the lesson activities (ui/activity_content.py).

Every part renderer is ``fn(key, spec) -> bool``: ``key`` is a unique prefix
for its Streamlit keys, ``spec`` the part's dict, and the return value says
whether the learner has completed the part on this run (ui/activities.py makes
completion sticky). ``KINDS`` holds the generic parts (sort, order, check);
``WIDGETS`` the custom experiments named by ``{"kind": "widget", "name": ...}``.

As in ui/walkthrough_widgets.py, the physics lives in small pure functions next
to each widget so tests/test_activities.py can check it, and Qiskit's qubit 0
is the rightmost bit of every result string.
"""

from __future__ import annotations

import random
import re
from collections.abc import Callable, Sequence
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.circuit.library import real_amplitudes
from qiskit.primitives import StatevectorSampler
from qiskit.quantum_info import DensityMatrix, Operator, Statevector

from ui import walkthrough_widgets as ww
from ui.walkthroughs import (
    build_circuit,
    circuit_code,
    counts_chart,
    ideal_probabilities,
    one_qubit_prediction,
    outcomes,
    percent,
    sample_counts,
)

ONE_QUBIT_PREDICT = ["Always 0", "Always 1", "About half 0, half 1"]
COIN_FACE = {"0": "\U0001F642 Heads (0)", "1": "\U0001F643 Tails (1)"}

# Graphviz colors matching ui/theme.py's PALETTE (the chart sits on the dark page background).
_DOT_STYLE = (
    'bgcolor="transparent"; fontname="IBM Plex Sans";'
    'node [style=filled, fillcolor="#151A3F", color="#A6A9D6", fontcolor="#F4F3FF", fontname="IBM Plex Sans"];'
    'edge [color="#A6A9D6", fontcolor="#C9C8F0", fontname="IBM Plex Sans"];'
)


_chart_layout = ww._chart_layout


def _set(key: str, value: Any) -> None:
    st.session_state[key] = value


# ---------------------------------------------------------------------------
# Generic parts
# ---------------------------------------------------------------------------

def sort_items(key: str, spec: dict[str, Any]) -> bool:
    """Put every item in one of ``spec["categories"]``. Feedback stays live after the first check."""
    categories, items = spec["categories"], spec["items"]
    checked = st.session_state.get(f"{key}_checked", False)
    choices = []
    for i, item in enumerate(items):
        choice = st.radio(item["text"], range(len(categories)), format_func=lambda c: categories[c],
                          index=None, horizontal=True, key=f"{key}_item{i}")
        choices.append(choice)
        if checked and choice is not None:
            st.caption(f"✅ {item['why']}" if choice == item["answer"] else "❌ Not quite. Think again and pick another answer.")
    st.button("Check my answers", key=f"{key}_check", on_click=_set, args=(f"{key}_checked", True))
    if not checked:
        return False
    right = sum(c == item["answer"] for c, item in zip(choices, items))
    if right == len(items):
        st.success(f"All {len(items)} right!")
        return True
    unanswered = choices.count(None)
    st.info(f"{right} of {len(items)} right so far." + (f" {unanswered} still need an answer." if unanswered else ""))
    return False


def shuffled_steps(key: str, steps: Sequence[str]) -> list[str]:
    """``steps`` in a fixed (per key) order that is never already the right one."""
    order = list(steps)
    rng = random.Random(key)
    while len(order) > 1 and order == list(steps):
        rng.shuffle(order)
    return order


def order_steps(key: str, spec: dict[str, Any]) -> bool:
    """Choose which step comes 1st, 2nd, ... ``spec["steps"]`` is the correct order."""
    steps = spec["steps"]
    options = shuffled_steps(key, steps)
    checked = st.session_state.get(f"{key}_checked", False)
    picks = []
    for i in range(len(steps)):
        pick = st.selectbox(f"Step {i + 1}", options, index=None, placeholder="Choose a step…", key=f"{key}_pos{i}")
        picks.append(pick)
        if checked and pick is not None and pick != steps[i]:
            st.caption("❌ Something else happens here.")
    st.button("Check the order", key=f"{key}_check", on_click=_set, args=(f"{key}_checked", True))
    if not checked:
        return False
    if picks == list(steps):
        st.success("That's the right order!" + (f" {spec['why']}" if spec.get("why") else ""))
        return True
    right = sum(p == s for p, s in zip(picks, steps))
    st.info(f"{right} of {len(steps)} steps are in the right place.")
    return False


def check(key: str, spec: dict[str, Any]) -> bool:
    """One multiple-choice question (same spec as a walkthrough ``check`` step)."""
    options = spec["options"]
    choice = st.radio(spec["question"], range(len(options)), format_func=lambda i: options[i], index=None, key=f"{key}_choice")
    if choice is None:
        return False
    if choice == spec["answer"]:
        st.success(f"Correct! {spec['why']}")
        return True
    st.warning("Not quite. Have another look and try a different answer.")
    return False


# ---------------------------------------------------------------------------
# Elementary
# ---------------------------------------------------------------------------

def room_bits(key: str, spec: dict[str, Any]) -> bool:
    found = [col.text_input(f"Bit #{i + 1}", key=f"{key}_{i}", placeholder="e.g. my lamp")
             for i, col in enumerate(st.columns(3))]
    filled = [f.strip() for f in found if f.strip()]
    if len(filled) < 3:
        st.caption(f"{len(filled)} of 3 found.")
        return False
    st.success(f"Great bit hunting! {', '.join(filled)}: each one has just two ways to be, like 0 and 1.")
    return True


def _pretend_flips(key: str) -> None:
    flips = ww.flip_coins(10)
    st.session_state[f"{key}_heads"] = flips.count("H")
    st.session_state[f"{key}_tails"] = flips.count("T")


def magic_coin_spins(spins: int, seed: int | None = None) -> tuple[int, int]:
    """(heads, tails) from ``spins`` shots of the H-gate qubit; heads is 0, as in the Magic Coin Machine."""
    counts = sample_counts(1, [("h", 0)], spins, seed=seed)
    return counts["0"], counts["1"]


def coin_race(key: str, spec: dict[str, Any]) -> bool:
    for side in ("heads", "tails"):
        st.session_state.setdefault(f"{key}_{side}", 0)
    a, b, c = st.columns([1, 1, 1.4], vertical_alignment="bottom")
    heads = a.number_input("\U0001F642 Heads", 0, 100, step=1, key=f"{key}_heads")
    tails = b.number_input("\U0001F643 Tails", 0, 100, step=1, key=f"{key}_tails")
    c.button("No coin? Flip a pretend one 10 times", key=f"{key}_pretend", on_click=_pretend_flips, args=(key,), width="stretch")
    total = int(heads + tails)
    if st.button(f"Spin the magic coin {total} times! \U0001FA99", key=f"{key}_spin", type="primary", disabled=total == 0):
        st.session_state[f"{key}_result"] = (total, *magic_coin_spins(total))
    result = st.session_state.get(f"{key}_result")
    if not result:
        st.caption("Type your coin's results (or use the pretend coin), then spin the magic coin.")
        return False
    spins, magic_heads, magic_tails = result
    fig = go.Figure([
        go.Bar(name="Your coin", x=["Heads", "Tails"], y=[heads, tails]),
        go.Bar(name="Magic coin (a qubit)", x=["Heads", "Tails"], y=[magic_heads, magic_tails]),
    ])
    fig.update_layout(barmode="group", yaxis_title="How many times")
    st.plotly_chart(_chart_layout(fig, f"Your coin vs. the magic coin ({spins} spins)"), width="stretch", key=f"{key}_chart")
    st.markdown(f"Magic coin: **{magic_heads}** heads and **{magic_tails}** tails out of {spins} spins.")
    return True


def recipe_proof(key: str, spec: dict[str, Any]) -> bool:
    recipes = spec["recipes"]
    if st.button("Test every recipe on the quantum simulator (20 tries each)", key=f"{key}_run", type="primary"):
        st.session_state[f"{key}_result"] = {name: sample_counts(1, ops, 20) for name, ops in recipes.items()}
    result = st.session_state.get(f"{key}_result")
    if not result:
        return False
    st.dataframe(
        pd.DataFrame({"Recipe": list(result), "Got 0": [c["0"] for c in result.values()], "Got 1": [c["1"] for c in result.values()]}),
        hide_index=True, width="stretch",
    )
    st.success("Those are real (simulated) qubit results. Do they match how you sorted the recipes?")
    return True


# Your coin is qubit 0 (the right-hand bit of each result), your friend's is qubit 1.
PARTNER_MODES = {
    "Partner coins (linked)": [("h", 0), ("cx", 0, 1)],
    "Ordinary coins (not linked)": [("h", 0), ("h", 1)],
}
PARTNER = next(iter(PARTNER_MODES))


def coin_pair(mode: str, seed: int | None = None) -> tuple[str, str]:
    """(your coin, your friend's coin) from one shot of the mode's circuit."""
    counts = sample_counts(2, PARTNER_MODES[mode], 1, seed=seed)
    outcome = next(o for o, c in counts.items() if c)
    return outcome[1], outcome[0]


def _new_pair(key: str, mode: str) -> None:
    st.session_state[f"{key}_pair"] = (mode, *coin_pair(mode))


def _reveal(key: str, guess: str) -> None:
    mode, mine, friend = st.session_state.pop(f"{key}_pair")
    st.session_state.setdefault(f"{key}_rounds", []).append({"mode": mode, "mine": mine, "friend": friend, "guess": guess})


def partner_game(key: str, spec: dict[str, Any]) -> bool:
    rounds = st.session_state.get(f"{key}_rounds", [])
    mode = st.radio("Which coins?", list(PARTNER_MODES), horizontal=True, key=f"{key}_mode")
    pair = st.session_state.get(f"{key}_pair")
    if pair is None or pair[0] != mode:
        if rounds:
            last = rounds[-1]
            verdict = "You guessed right! \U0001F389" if last["guess"] == last["friend"] else "Not this time."
            match = "The coins **matched**." if last["mine"] == last["friend"] else "The coins **didn't match**."
            st.markdown(f"Last round: your coin {COIN_FACE[last['mine']]}, your friend's coin {COIN_FACE[last['friend']]}. {match} {verdict}")
        st.button("\U0001FA99 Make a new pair and peek at YOUR coin", key=f"{key}_new", on_click=_new_pair, args=(key, mode), type="primary")
    else:
        st.markdown(f"Your coin: **{COIN_FACE[pair[1]]}**. Your friend's coin is still hidden. \U0001F92B")
        guess = st.radio("What will your friend's coin show?", ["0", "1"], format_func=COIN_FACE.get, index=None,
                         horizontal=True, key=f"{key}_guess{len(rounds)}")
        st.button("Reveal my friend's coin", key=f"{key}_reveal", on_click=_reveal, args=(key, guess), disabled=guess is None)

    if rounds:
        st.dataframe(
            pd.DataFrame([
                {"Coins": m, "Rounds": len(rs), "Coins matched": sum(r["mine"] == r["friend"] for r in rs),
                 "Your right guesses": sum(r["guess"] == r["friend"] for r in rs)}
                for m in PARTNER_MODES if (rs := [r for r in rounds if r["mode"] == m])
            ]),
            hide_index=True, width="stretch",
        )
    partner_rounds = [r for r in rounds if r["mode"] == PARTNER]
    needed = spec.get("rounds", 5)
    if len(partner_rounds) < needed:
        st.caption(f"Partner rounds played: {len(partner_rounds)} of {needed}.")
        return False
    st.success(f"Partner coins matched in all {len(partner_rounds)} rounds, so peeking at your coin tells you your friend's. "
               "That's entanglement! Ordinary coins only match about half the time.")
    return True


# ---------------------------------------------------------------------------
# Proficient
# ---------------------------------------------------------------------------

PERCENT_ROUNDS = [
    {"label": "Round 1: the H-gate coin, 100 shots", "theta": np.pi / 2, "shots": 100},
    {"label": "Round 2: a lopsided coin, RY(60°), 200 shots", "theta": np.pi / 3, "shots": 200},
]


def percent_circuit(theta: float) -> QuantumCircuit:
    """RY(theta) on |0>, measured; RY(90°) gives the same chances as the H gate."""
    qc = QuantumCircuit(1)
    qc.ry(theta, 0)
    qc.measure_all()
    return qc


def percent_challenge(key: str, spec: dict[str, Any]) -> bool:
    for r, rnd in enumerate(PERCENT_ROUNDS):
        solved_key = f"{key}_solved{r}"
        st.markdown(f"**{rnd['label']}**" + (" ✅" if st.session_state.get(solved_key) else ""))
        if st.button("Run it", key=f"{key}_run{r}"):
            shots = rnd["shots"]
            st.session_state[f"{key}_ones{r}"] = round(ww.ones_fraction(percent_circuit(rnd["theta"]), shots, 1)[0] * shots)
        ones = st.session_state.get(f"{key}_ones{r}")
        if ones is None:
            continue
        shots = rnd["shots"]
        st.markdown(f"Out of **{shots}** shots you got **{ones}** ones and **{shots - ones}** zeros.")
        answer = st.number_input("What percent of the shots were 1?", 0.0, 100.0, value=None, step=0.5, format="%.1f",
                                 key=f"{key}_answer{r}")
        if answer is None:
            continue
        exact = 100 * ones / shots
        if abs(answer - exact) <= 0.5:
            theory = percent(ww.ry_probability_of_one(rnd["theta"]))
            st.success(f"Right: {ones} ÷ {shots} × 100 = {percent(ones / shots)}. Theory predicts {theory}.")
            st.session_state[solved_key] = True
        else:
            st.warning("Not quite. Divide the number of 1s by the number of shots, then multiply by 100.")
    return all(st.session_state.get(f"{key}_solved{r}") for r in range(len(PERCENT_ROUNDS)))


def challenge_problem(challenge: dict[str, Any], qubits: int, menu: dict[str, Any], picks: Sequence[str]) -> str | None:
    """None if the circuit built from ``picks`` meets ``challenge``, otherwise a hint."""
    used = [p for p in picks if menu[p]]
    ops = [menu[p] for p in used]
    if challenge.get("only") and any(p not in challenge["only"] for p in used):
        return f"For this challenge, use only {' and '.join(challenge['only'])}."
    if len(used) < challenge.get("min_gates", 0):
        return f"Use at least {challenge['min_gates']} gates for this challenge."
    if "probs" in challenge:
        probs = ideal_probabilities(qubits, ops)
        if any(abs(p - challenge["probs"].get(o, 0.0)) > 1e-9 for o, p in probs.items()):
            target = ", ".join(f"{o} → {percent(p)}" for o, p in challenge["probs"].items())
            return f"Not yet. The target is {target}."
    if "state" in challenge:
        state = Statevector.from_instruction(build_circuit(qubits, ops, measure=False))
        if not state.equiv(Statevector(challenge["state"])):
            return "Not yet: the final state isn't the target state. Check the amplitudes below."
    return None


def _state_table(qubits: int, ops: Sequence[tuple[Any, ...]]) -> None:
    state = Statevector.from_instruction(build_circuit(qubits, ops, measure=False))
    st.dataframe(
        pd.DataFrame({
            "Basis state": [f"|{o}⟩" for o in outcomes(qubits)],
            "Amplitude": [f"{a.real:+.4f}" + (f"{a.imag:+.4f}i" if abs(a.imag) > 1e-9 else "") for a in state.data],
            "Probability": [f"{abs(a) ** 2:.4f}" for a in state.data],
        }),
        hide_index=True, width="stretch",
    )


def circuit_builder(key: str, spec: dict[str, Any]) -> bool:
    qubits, menu, challenges = spec["qubits"], spec["menu"], spec["challenges"]
    solved: set[int] = st.session_state.setdefault(f"{key}_solved", set())
    st.markdown("  \n".join(f"{'✅' if i in solved else '⬜'} {c['label']}" for i, c in enumerate(challenges)))
    current = 0
    if len(challenges) > 1:
        current = st.radio("Working on", range(len(challenges)), format_func=lambda i: challenges[i]["label"],
                           horizontal=True, key=f"{key}_challenge")

    picks = [col.selectbox(f"Gate {s + 1}", list(menu), key=f"{key}_slot{s}") for s, col in enumerate(st.columns(spec["slots"]))]
    ops = [menu[p] for p in picks if menu[p]]
    st.code(str(build_circuit(qubits, ops).draw(output="text")), language=None)
    if spec.get("show_code"):
        st.code(circuit_code(qubits, ops, 1000), language="python")

    probs = ideal_probabilities(qubits, ops)
    if qubits == 1:
        prediction = st.radio("Your prediction", range(len(ONE_QUBIT_PREDICT)), format_func=lambda i: ONE_QUBIT_PREDICT[i],
                              index=None, horizontal=True, key=f"{key}_predict")
    else:
        prediction = st.multiselect("Your prediction: which results will appear?", outcomes(qubits), key=f"{key}_predict")

    if st.button("Run 1000 shots", key=f"{key}_run", type="primary"):
        st.session_state[f"{key}_result"] = (tuple(picks), sample_counts(qubits, ops, 1000))
    result = st.session_state.get(f"{key}_result")
    if result and result[0] == tuple(picks):
        counts_chart(result[1], key=f"{key}_chart", title="Results from 1000 shots")
        if qubits == 1 and prediction is not None:
            expected = one_qubit_prediction(probs)
            st.markdown("✅ Your prediction matches the theory." if prediction == expected
                        else f"❌ Theory says **{ONE_QUBIT_PREDICT[expected]}**. Compare that with your results.")
        elif qubits > 1 and prediction:
            support = sorted(o for o, p in probs.items() if p > 1e-9)
            st.markdown("✅ Your prediction matches the theory." if sorted(prediction) == support
                        else f"❌ Theory says only **{', '.join(support)}** can appear.")
        if spec.get("show_state"):
            _state_table(qubits, ops)
        problem = challenge_problem(challenges[current], qubits, menu, picks)
        if problem is None:
            solved.add(current)
            st.success(f"Challenge solved: {challenges[current]['label']}!")
        else:
            st.info(problem)
    return len(solved) == len(challenges)


# ---------------------------------------------------------------------------
# Erudite: foundations
# ---------------------------------------------------------------------------

# label: amplitudes (alpha, beta). Pr(1) = |beta|^2.
BORN_STATES: dict[str, list[complex]] = {
    r"$\tfrac{\sqrt3}{2}|0\rangle + \tfrac12|1\rangle$": [np.sqrt(3) / 2, 1 / 2],
    r"$\tfrac{1}{\sqrt2}|0\rangle - \tfrac{i}{\sqrt2}|1\rangle$": [1 / np.sqrt(2), -1j / np.sqrt(2)],
    r"$\tfrac45|0\rangle - \tfrac{3i}{5}|1\rangle$": [4 / 5, -3j / 5],
    r"$\tfrac13|0\rangle + \tfrac{2\sqrt2}{3}|1\rangle$": [1 / 3, 2 * np.sqrt(2) / 3],
    r"$\tfrac{1+i}{2}|0\rangle + \tfrac{1}{\sqrt2}|1\rangle$": [(1 + 1j) / 2, 1 / np.sqrt(2)],
}


def born_probability_of_one(amplitudes: Sequence[complex]) -> float:
    return float(Statevector(amplitudes).probabilities_dict().get("1", 0.0))


def born_rule_drill(key: str, spec: dict[str, Any]) -> bool:
    labels = list(BORN_STATES)
    needed = spec.get("needed", 3)
    solved: set[str] = st.session_state.setdefault(f"{key}_solved", set())
    st.caption(f"Solved {min(len(solved), needed)} of {needed}.")
    label = st.radio("State", labels, key=f"{key}_state")
    exact = born_probability_of_one(BORN_STATES[label])
    guess = st.number_input(r"Your prediction for $\Pr(1)$", 0.0, 1.0, value=None, step=0.01, format="%.3f",
                            key=f"{key}_guess{labels.index(label)}")
    if guess is not None:
        if abs(guess - exact) <= 0.005:
            solved.add(label)
            st.success(f"Correct: $\\Pr(1) = |\\beta|^2 = {exact:.4f}$.")
        else:
            st.warning(r"Not quite. Take the absolute value of the $|1\rangle$ amplitude and square it.")

    shots = st.radio("Shots", [10, 100, 1000], horizontal=True, key=f"{key}_shots")
    if st.button("Sample it on the simulator", key=f"{key}_run"):
        counts = Statevector(BORN_STATES[label]).sample_counts(shots)
        st.session_state[f"{key}_result"] = (label, shots, int(counts.get("1", 0)))
    result = st.session_state.get(f"{key}_result")
    if result and result[0] == label:
        _, ran, ones = result
        st.markdown(f"Measured frequency of 1: **{ones / ran:.3f}** ({ones} of {ran} shots) · Born rule: **{exact:.3f}** · "
                    f"difference {abs(ones / ran - exact):.3f}")
    return len(solved) >= needed


def basis_tokens(text: str) -> list[str]:
    """Bitstrings typed in any format: '000, 001', '|010⟩ |011>', ..."""
    return re.findall(r"[01]+", text)


def basis_list(key: str, spec: dict[str, Any]) -> bool:
    n = spec["qubits"]
    expected = set(outcomes(n))
    text = st.text_input(f"All {2**n} basis states (separate them with spaces or commas)", key=f"{key}_text",
                         placeholder=", ".join(outcomes(n)[:2]) + ", …")
    tokens = basis_tokens(text)
    if not tokens:
        return False
    wrong = sorted({t for t in tokens if len(t) != n})
    good = {t for t in tokens if len(t) == n}
    repeats = len([t for t in tokens if len(t) == n]) - len(good)
    notes = []
    if wrong:
        notes.append(f"each state has exactly {n} bits, so {', '.join(wrong)} can't be one")
    if repeats:
        notes.append("some states are listed more than once")
    if len(good) < len(expected):
        notes.append(f"{len(expected) - len(good)} of the {len(expected)} are still missing")
    if notes:
        st.info("Almost: " + "; ".join(notes) + ".")
        return False
    st.success("All eight! In Qiskit's order the state vector entries are "
               + ", ".join(f"|{o}⟩ = entry {i}" for i, o in enumerate(outcomes(n))) + ".")
    return True


PRODUCT_FACTORS = ["0", "1", "+", "-"]


def product_support(labels: str) -> list[str]:
    """Basis states with nonzero amplitude in Statevector.from_label(labels) (leftmost label = highest qubit)."""
    state = Statevector.from_label(labels)
    return [format(i, f"0{len(labels)}b") for i, a in enumerate(state.data) if abs(a) > 1e-9]


def product_state_predict(key: str, spec: dict[str, Any]) -> bool:
    cols = st.columns(3)
    labels = "".join(
        col.selectbox(f"Qubit {q}", PRODUCT_FACTORS, index=(2 if q == 1 else 0), format_func=lambda s: f"|{s}⟩", key=f"{key}_q{q}")
        for col, q in zip(cols, (2, 1, 0))
    )
    st.latex(r"|%s\rangle \otimes |%s\rangle \otimes |%s\rangle" % tuple(labels))
    prediction = st.multiselect("Basis states with a nonzero amplitude", outcomes(3), format_func=lambda o: f"|{o}⟩",
                                key=f"{key}_predict{labels}")
    if not st.button("Check my prediction", key=f"{key}_check"):
        return False
    support = product_support(labels)
    if sorted(prediction) != support:
        st.warning("Not quite. Expand the product one qubit at a time: |+⟩ and |−⟩ each split into a |0⟩ part and a |1⟩ part.")
        return False
    st.success(f"Correct: {', '.join(f'|{o}⟩' for o in support)}. Here are the amplitudes from Qiskit's Statevector.")
    state = Statevector.from_label(labels)
    st.dataframe(pd.DataFrame({"Basis state": [f"|{o}⟩" for o in support],
                               "Amplitude": [f"{state.data[int(o, 2)].real:+.4f}" for o in support]}),
                 hide_index=True, width="stretch")
    if not any(s in "+-" for s in labels):
        st.info("Now try it with at least one |+⟩ or |−⟩ factor, so more than one basis state appears.")
        return False
    return True


# ---------------------------------------------------------------------------
# Erudite: entanglement and algorithms
# ---------------------------------------------------------------------------

BELL_RECIPES = {
    "φ⁺": [("h", 0), ("cx", 0, 1)],
    "φ⁻": [("h", 0), ("cx", 0, 1), ("z", 0)],
    "ψ⁺": [("h", 0), ("cx", 0, 1), ("x", 0)],
    "ψ⁻": [("h", 0), ("cx", 0, 1), ("z", 0), ("x", 0)],
}
BELL_SHOTS = [10, 100, 1000]


def bell_runs(ops: Sequence[tuple[Any, ...]], shots: int, runs: int, seed: int | None = None) -> list[dict[str, int]]:
    """Counts from ``runs`` independent runs (a Generator, because an int seed would repeat itself for every circuit)."""
    result = StatevectorSampler(seed=np.random.default_rng(seed)).run([build_circuit(2, ops)] * runs, shots=shots).result()
    return [{o: int(result[i].data.meas.get_counts().get(o, 0)) for o in outcomes(2)} for i in range(runs)]


def bell_statistics(key: str, spec: dict[str, Any]) -> bool:
    name = st.radio("Bell state", list(BELL_RECIPES), horizontal=True, key=f"{key}_state")
    ops = BELL_RECIPES[name]
    support = [o for o, p in ideal_probabilities(2, ops).items() if p > 1e-9]
    tracked = support[0]
    if st.button("Run 5 times each at 10, 100 and 1000 shots", key=f"{key}_run", type="primary"):
        st.session_state[f"{key}_result"] = (name, {s: bell_runs(ops, s, 5) for s in BELL_SHOTS})
    result = st.session_state.get(f"{key}_result")
    if not result or result[0] != name:
        return False
    runs = result[1]
    fractions = {s: [r[tracked] / s for r in runs[s]] for s in BELL_SHOTS}
    impossible = sum(r[o] for s in BELL_SHOTS for r in runs[s] for o in outcomes(2) if o not in support)
    fig = go.Figure([go.Scatter(x=[s] * 5, y=fractions[s], mode="markers", marker=dict(size=10), name=f"{s} shots") for s in BELL_SHOTS])
    fig.add_hline(y=0.5, line_dash="dot", annotation_text="theory 0.5")
    fig.update_layout(xaxis_type="log", xaxis_title="Shots per run", yaxis_title=f"Fraction of {tracked}", yaxis_range=[0, 1],
                      showlegend=False)
    st.plotly_chart(_chart_layout(fig, f"{name}: five runs at each shot count"), width="stretch", key=f"{key}_chart")
    st.dataframe(pd.DataFrame({
        "Shots": BELL_SHOTS,
        f"Fractions of {tracked} in the 5 runs": [", ".join(f"{f:.2f}" for f in fractions[s]) for s in BELL_SHOTS],
        "Spread (max − min)": [f"{max(fractions[s]) - min(fractions[s]):.3f}" for s in BELL_SHOTS],
    }), hide_index=True, width="stretch")
    total = 5 * sum(BELL_SHOTS)
    st.markdown(f"Outcomes outside {{{', '.join(support)}}} appeared **{impossible}** times in {total} shots.")
    return True


FLOW_ARROWS = {
    "ebit": "Before the protocol: qubits A and B of the e-bit are delivered to Alice and Bob",
    "bits": "After measuring: Alice's results a and b travel to Bob",
}
FLOW_ANSWERS = {"ebit": "Quantum channel", "bits": "Classical channel"}
CHANNELS = ["Quantum channel", "Classical channel"]


def teleport_flow_dot(labels: dict[str, str | None]) -> str:
    def style(arrow: str, text: str) -> str:
        channel = labels.get(arrow)
        if channel is None:
            return f'label="{text}  (?)", style=dotted'
        color = "#8B7FF5" if channel == CHANNELS[0] else "#1FBFB2"
        dash = "dashed" if channel == CHANNELS[0] else "solid"
        return f'label="{text}\\n{channel.lower()}", color="{color}", fontcolor="{color}", style={dash}, penwidth=2'

    return (
        "digraph { rankdir=LR; " + _DOT_STYLE
        + 'S [label="e-bit source", shape=ellipse]; '
        + 'Alice [label="Alice\\nQ (unknown state), A", shape=box]; Bob [label="Bob\\nB", shape=box]; '
        + f'S -> Alice [{style("ebit", "A")}]; S -> Bob [{style("ebit", "B")}]; '
        + f'Alice -> Bob [{style("bits", "a, b")}]; }}'
    )


def teleport_flow(key: str, spec: dict[str, Any]) -> bool:
    labels = {arrow: st.selectbox(text, CHANNELS, index=None, placeholder="Which channel?", key=f"{key}_{arrow}")
              for arrow, text in FLOW_ARROWS.items()}
    st.graphviz_chart(teleport_flow_dot(labels), width="stretch")
    if None in labels.values():
        return False
    if labels == FLOW_ANSWERS:
        st.success("Right. The e-bit's qubits must physically reach Alice and Bob, but the protocol itself only sends two "
                   "ordinary bits, so it can't go faster than light, and Q's state is never copied.")
        return True
    st.warning("Not quite. Which arrows carry qubits, and which carry ordinary bits?")
    return False


GROVER_STAGES = [
    "Hadamard on both qubits",
    r"Oracle $Z_f$: flip the sign of the marked item",
    r"Diffusion $H Z_{\mathrm{OR}} H$: reflect about the average",
]
GROVER_CHART_TITLES = ["Hadamards", "Oracle Z_f", "Diffusion H·Z_OR·H"]  # plain text: chart titles can't render LaTeX
GROVER_CHOICES = ["+1/2", "−1/2", "+1", "0"]
_GROVER_VALUES = [0.5, -0.5, 1.0, 0.0]


def grover_trace_states(marked: str) -> list[Statevector]:
    """|00>, then the state after each stage of one Grover iteration G = H Z_OR H Z_f (the course's form)."""
    n = len(marked)
    hadamards = Operator.from_label("H" * n)
    z_f = Operator(np.diag([-1.0 if format(i, f"0{n}b") == marked else 1.0 for i in range(2**n)]))
    z_or = Operator(np.diag([1.0] + [-1.0] * (2**n - 1)))
    start = Statevector.from_label("0" * n)
    after_h = start.evolve(hadamards)
    after_oracle = after_h.evolve(z_f)
    after_diffusion = after_oracle.evolve(hadamards).evolve(z_or).evolve(hadamards)
    return [start, after_h, after_oracle, after_diffusion]


def grover_stage_answers(marked: str) -> list[int]:
    """Index into GROVER_CHOICES of the marked item's amplitude after each stage."""
    amps = [float(np.real(s.data[int(marked, 2)])) for s in grover_trace_states(marked)[1:]]
    return [int(np.argmin([abs(a - v) for v in _GROVER_VALUES])) for a in amps]


def _grover_apply(key: str, guess: int, answer: int) -> None:
    st.session_state.setdefault(f"{key}_log", []).append(guess == answer)


def _grover_restart(key: str) -> None:
    st.session_state[f"{key}_log"] = []


def grover_trace(key: str, spec: dict[str, Any]) -> bool:
    marked = st.radio("Marked item", outcomes(2), horizontal=True, key=f"{key}_marked", on_change=_grover_restart, args=(key,))
    log: list[bool] = st.session_state.get(f"{key}_log", [])
    stage = len(log)
    states, answers = grover_trace_states(marked), grover_stage_answers(marked)
    amps = np.real(states[stage].data)
    fig = go.Figure(go.Bar(x=[f"|{o}⟩" for o in outcomes(2)], y=amps, text=[f"{a:+.2f}" for a in amps],
                           marker_color=["#FF8A65" if o == marked else "#8B7FF5" for o in outcomes(2)]))
    if stage == 2:
        fig.add_hline(y=float(np.mean(amps)), line_dash="dot", annotation_text="average amplitude")
    fig.update_layout(yaxis_range=[-1.1, 1.1], yaxis_title="Amplitude", xaxis_type="category")
    title = "Start: |00⟩" if stage == 0 else f"After stage {stage}: {GROVER_CHART_TITLES[stage - 1]}"
    st.plotly_chart(_chart_layout(fig, title), width="stretch", key=f"{key}_chart")
    for i, ok in enumerate(log):
        st.markdown(f"{'✅' if ok else '❌'} Stage {i + 1} ({GROVER_STAGES[i]}): amplitude of |{marked}⟩ = **{GROVER_CHOICES[answers[i]]}**")

    if stage < len(GROVER_STAGES):
        guess = st.radio(f"Next, stage {stage + 1}: {GROVER_STAGES[stage]}. What will the amplitude of |{marked}⟩ be?",
                         range(len(GROVER_CHOICES)), format_func=lambda i: GROVER_CHOICES[i], index=None, horizontal=True,
                         key=f"{key}_guess_{marked}_{stage}")
        st.button("Apply it", key=f"{key}_apply", type="primary", on_click=_grover_apply,
                  args=(key, guess, answers[stage]), disabled=guess is None)
        return False
    st.button("Trace again", key=f"{key}_restart", on_click=_grover_restart, args=(key,))
    if all(log):
        st.success(f"All three right. With N = 4, one iteration takes the probability of |{marked}⟩ from 1/4 to 1.")
        return True
    st.info("Some predictions missed. Look at how the bars moved, then trace again.")
    return False


# ---------------------------------------------------------------------------
# Erudite: advanced research
# ---------------------------------------------------------------------------

NOISE_CHALLENGES = [
    {
        "label": "|+⟩ through complete dephasing (p = 1)", "state": "|+⟩", "channel": "Dephasing", "p": 1.0,
        "question": "Which information does the channel erase?",
        "options": ["The standard-basis (Z) statistics", "The off-diagonal coherence, so the X-basis certainty", "Nothing"],
        "answer": 1,
        "why": "Dephasing zeros the off-diagonal entries. Pr(0) stays 1/2, but measuring after H no longer always gives 0.",
    },
    {
        "label": "|0⟩ through complete dephasing (p = 1)", "state": "|0⟩", "channel": "Dephasing", "p": 1.0,
        "question": "Which information does the channel erase?",
        "options": ["The standard-basis (Z) statistics", "The off-diagonal coherence", "Nothing: |0⟩⟨0| is already diagonal"],
        "answer": 2,
        "why": "|0⟩⟨0| has no off-diagonal entries, so dephasing leaves it exactly as it was.",
    },
    {
        "label": "|1⟩ through complete depolarizing (p = 1)", "state": "|1⟩", "channel": "Depolarizing", "p": 1.0,
        "question": "What comes out?",
        "options": ["|1⟩⟨1|, unchanged", "𝕀/2, the completely mixed state: everything about the input is lost", "|0⟩⟨0|"],
        "answer": 1,
        "why": "The completely depolarizing channel outputs 𝕀/2 for every input state.",
    },
    {
        "label": "|+⟩ through dephasing with p = 0.5", "state": "|+⟩", "channel": "Dephasing", "p": 0.5,
        "question": "What is the purity Tr(ρ²) of the output?",
        "options": ["1", "0.625", "0.5"],
        "answer": 1,
        "why": "The output is [[1/2, 1/4], [1/4, 1/2]], and Tr(ρ²) = 1/4 + 1/16 + 1/16 + 1/4 = 0.625.",
    },
]


def noisy_state(challenge: dict[str, Any]) -> DensityMatrix:
    rho = DensityMatrix.from_label(ww.NOISE_STATES[challenge["state"]])
    return ww.apply_noise(rho, challenge["channel"], challenge["p"])


def _latex_matrix(m: np.ndarray) -> str:
    def entry(z: complex) -> str:
        return f"{z.real:.3f}" if abs(z.imag) < 5e-4 else f"{z.real:.3f}{z.imag:+.3f}i"

    return r"\begin{pmatrix} %s & %s \\ %s & %s \end{pmatrix}" % (entry(m[0, 0]), entry(m[0, 1]), entry(m[1, 0]), entry(m[1, 1]))


def noise_detective(key: str, spec: dict[str, Any]) -> bool:
    solved: set[int] = st.session_state.setdefault(f"{key}_solved", set())
    st.markdown("  \n".join(f"{'✅' if i in solved else '⬜'} {c['label']}" for i, c in enumerate(NOISE_CHALLENGES)))
    i = st.radio("Case", range(len(NOISE_CHALLENGES)), format_func=lambda j: NOISE_CHALLENGES[j]["label"], key=f"{key}_case")
    challenge = NOISE_CHALLENGES[i]
    ideal = DensityMatrix.from_label(ww.NOISE_STATES[challenge["state"]])
    st.latex(r"\rho_{\text{in}} = " + _latex_matrix(ideal.data))
    choice = st.radio(challenge["question"], range(len(challenge["options"])), format_func=lambda j: challenge["options"][j],
                      index=None, key=f"{key}_answer{i}")
    if choice is None:
        return len(solved) == len(NOISE_CHALLENGES)
    if choice != challenge["answer"]:
        st.warning("Not quite. Think about which entries of ρ the channel changes.")
        return len(solved) == len(NOISE_CHALLENGES)
    solved.add(i)
    out = noisy_state(challenge)
    x, y, z = ww.bloch_vector(out)
    st.success(f"Correct! {challenge['why']}")
    st.latex(r"\rho_{\text{out}} = " + _latex_matrix(out.data))
    st.markdown(f"Purity: **{ideal.purity().real:.3f} → {out.purity().real:.3f}** · Bloch vector length "
                f"**{np.linalg.norm(ww.bloch_vector(ideal)):.2f} → {np.sqrt(x * x + y * y + z * z):.2f}**")
    return len(solved) == len(NOISE_CHALLENGES)


VQE_SETUPS = {
    "A · real_amplitudes ansatz (4 parameters), up to 300 COBYLA iterations": {"ansatz": "real_amplitudes", "maxiter": 300},
    "B · the same ansatz, but COBYLA stops after 10 iterations": {"ansatz": "real_amplitudes", "maxiter": 10},
    "C · a single RY on qubit 0 (1 parameter), up to 300 iterations": {"ansatz": "single_ry", "maxiter": 300},
}
VQE_VERDICTS = ["Reaches the ground energy", "The optimizer stopped too early", "The ansatz can't represent the ground state"]
VQE_VERDICT_ANSWERS = [0, 1, 2]  # one per setup, in order
VQE_VERDICT_WHY = [
    "Its energy matches the exact ground energy.",
    "The energy was still falling when the iterations ran out.",
    "Even fully optimized, one RY on qubit 0 never touches qubit 1, so its best energy stays above the ground energy.",
]


def vqe_ansatz(name: str) -> QuantumCircuit:
    if name == "single_ry":
        qc = QuantumCircuit(2)
        qc.ry(Parameter("θ"), 0)
        return qc
    return real_amplitudes(2, reps=1)


def run_vqe_setup(label: str) -> tuple[list[float], float]:
    setup = VQE_SETUPS[label]
    return ww.run_vqe(maxiter=setup["maxiter"], ansatz=vqe_ansatz(setup["ansatz"]))


def vqe_failure_lab(key: str, spec: dict[str, Any]) -> bool:
    st.markdown(r"All three minimize $\langle H\rangle$ for the walkthrough's toy Hamiltonian "
                r"$H = Z\!Z + 0.5\,X\!I + 0.5\,I\!X$ with Qiskit's `StatevectorEstimator` and SciPy's COBYLA.")
    if st.button("Run all three setups", key=f"{key}_run", type="primary"):
        st.session_state[f"{key}_result"] = {label: run_vqe_setup(label) for label in VQE_SETUPS}
    results = st.session_state.get(f"{key}_result")
    if not results:
        return False
    exact = ww.vqe_exact_ground_energy()
    fig = go.Figure([go.Scatter(y=history, mode="lines", name=label.split(" · ")[0]) for label, (history, _) in results.items()])
    fig.add_hline(y=exact, line_dash="dot", annotation_text="exact ground energy")
    fig.update_layout(xaxis_title="Cost evaluations", yaxis_title="Energy")
    st.plotly_chart(_chart_layout(fig, "Three VQE runs"), width="stretch", key=f"{key}_chart")
    st.dataframe(pd.DataFrame({
        "Setup": list(results),
        "Final energy": [f"{final:.4f}" for _, final in results.values()],
        "Gap to exact": [f"{final - exact:.4f}" for _, final in results.values()],
        "Evaluations": [len(history) for history, _ in results.values()],
    }), hide_index=True, width="stretch")
    st.markdown("**Diagnose each setup.**")
    return sort_items(f"{key}_diagnose", {
        "categories": VQE_VERDICTS,
        "items": [{"text": label, "answer": a, "why": why}
                  for label, a, why in zip(VQE_SETUPS, VQE_VERDICT_ANSWERS, VQE_VERDICT_WHY)],
    })


MAXCUT_EDGES = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
MAXCUT_DEFAULT = {(0, 1), (1, 2), (0, 2), (2, 3)}  # a triangle with a tail


def max_cut(edges: Sequence[tuple[int, int]]) -> tuple[int, list[str]]:
    """Brute force: the maximum cut and every bitstring that achieves it."""
    cuts = {format(i, f"0{ww.QAOA_NODES}b"): ww.cut_value(format(i, f"0{ww.QAOA_NODES}b"), edges) for i in range(2**ww.QAOA_NODES)}
    best = max(cuts.values())
    return best, [b for b, c in cuts.items() if c == best]


def maxcut_dot(edges: Sequence[tuple[int, int]], bitstring: str | None = None) -> str:
    def node(i: int) -> str:
        if bitstring is None:
            return f'{i} [label="{i}", shape=circle];'
        fill = "#FF8A65" if bitstring[-1 - i] == "1" else "#1FBFB2"
        return f'{i} [label="{i}", shape=circle, fillcolor="{fill}", fontcolor="#0E1330"];'

    def edge(i: int, j: int) -> str:
        cut = bitstring is not None and bitstring[-1 - i] != bitstring[-1 - j]
        return f"{i} -- {j}" + (' [color="#FF8A65", penwidth=2.5, style=dashed];' if cut else ";")

    return "graph { layout=circo; " + _DOT_STYLE + " ".join(node(i) for i in range(ww.QAOA_NODES)) + " " + " ".join(edge(i, j) for i, j in edges) + " }"


def _run_qaoa(key: str, edges: tuple[tuple[int, int], ...]) -> None:
    """Button callback: runs before the script, so the graph at the top can show the sampled partition."""
    gamma, beta = ww.optimize_qaoa(edges=edges)
    counts = ww.qaoa_state(gamma, beta, edges).sample_counts(1000)
    st.session_state[f"{key}_result"] = {"edges": edges, "gamma": gamma, "beta": beta, "counts": dict(counts),
                                         "top": max(counts, key=counts.get)}


def maxcut_builder(key: str, spec: dict[str, Any]) -> bool:
    st.markdown("**1. Pick the edges of your graph** (4 nodes).")
    cols = st.columns(3)
    edges = tuple(e for n, e in enumerate(MAXCUT_EDGES)
                  if cols[n % 3].checkbox(f"{e[0]} — {e[1]}", value=e in MAXCUT_DEFAULT, key=f"{key}_e{e[0]}{e[1]}"))
    if not edges:
        st.info("Pick at least one edge.")
        return False
    best, best_strings = max_cut(edges)
    result = st.session_state.get(f"{key}_result")
    sampled = result is not None and result["edges"] == edges
    st.graphviz_chart(maxcut_dot(edges, result["top"] if sampled else None))  # natural size: stretched, 4 nodes fill the screen

    st.markdown("**2. The cost Hamiltonian** (Qiskit labels put qubit 0 on the right):")
    hamiltonian, offset = ww.qaoa_cost_hamiltonian(edges)
    terms = ", ".join(f'("ZZ", [{i}, {j}], 0.5)' for i, j in edges)
    st.code(f"H_C = SparsePauliOp.from_sparse_list([{terms}], num_qubits=4)\n"
            f"# {hamiltonian.to_list()}\n# offset = {offset}   (cut = -(<H_C> + offset))", language="python")

    st.markdown("**3. Predict, then run QAOA.**")
    prediction = st.number_input("Your prediction: the maximum cut of this graph", 0, len(edges), value=None, step=1,
                                 key=f"{key}_predict{''.join(f'{i}{j}' for i, j in edges)}")
    predicted = prediction is not None and prediction == best
    if prediction is not None:
        if predicted:
            st.success(f"Correct: the maximum cut is {best}, achieved by {', '.join(best_strings)}.")
        else:
            st.warning("Not quite. Try splitting the nodes into two groups so that as many edges as possible join different groups.")
    st.button("Optimize γ and β with COBYLA, then sample 1000 shots", key=f"{key}_run", type="primary",
              on_click=_run_qaoa, args=(key, edges))
    if not sampled:
        return False
    expected = ww.qaoa_expected_cut(result["gamma"], result["beta"], edges)
    counts = result["counts"]
    ranked = sorted(counts.items(), key=lambda kv: -kv[1])[:6]
    st.markdown(f"γ = **{result['gamma']:.3f}**, β = **{result['beta']:.3f}** · expected cut **{expected:.3f}** of a maximum "
                f"**{best}** → approximation ratio **{expected / best:.3f}**")
    st.dataframe(pd.DataFrame({"Bitstring (node 3 … node 0)": [b for b, _ in ranked], "Count": [c for _, c in ranked],
                               "Cut value": [ww.cut_value(b, edges) for b, _ in ranked]}),
                 hide_index=True, width="stretch")
    top_cut = ww.cut_value(result["top"], edges)
    best_sampled = max(ww.cut_value(b, edges) for b in counts)
    st.markdown(f"**Post-processing:** the most likely bitstring **{result['top']}** cuts **{top_cut}** edges (colored in the "
                f"graph above); the best bitstring anywhere in the samples cuts **{best_sampled}**.")
    return predicted


CODE_ERRORS = {"None": None, **{f"{g.upper()} on qubit {q}": (g, q) for g in ("x", "z") for q in range(3)}}
CODE_LESSONS = {"one bit flip": "a single bit flip", "two bit flips": "two bit flips", "a phase flip": "a phase flip"}


def _net(errors: Sequence[tuple[str, int]], gate: str) -> set[int]:
    """Qubits hit by an odd number of ``gate`` errors (two X's on one qubit cancel)."""
    return {q for q in range(3) if sum(g == gate and p == q for g, p in errors) % 2}


def logical_effect(errors: Sequence[tuple[str, int]], fix: int | None) -> tuple[bool, bool]:
    """(logical X, logical Z) left on the code after correction. X errors plus the fix always form 000 or 111,
    and on the code space any single Z acts as a logical Z."""
    flipped = _net(errors, "x") ^ ({fix} if fix is not None else set())
    return flipped == {0, 1, 2}, len(_net(errors, "z")) % 2 == 1


def code_scenario(errors: Sequence[tuple[str, int]]) -> str | None:
    """Which CODE_LESSONS scenario ``errors`` is an example of."""
    x, z = len(_net(errors, "x")), len(_net(errors, "z"))
    if z and not x:
        return "a phase flip"
    if x == 1 and not z:
        return "one bit flip"
    if x == 2 and not z:
        return "two bit flips"
    return None


def break_the_code(key: str, spec: dict[str, Any]) -> bool:
    tried: set[str] = st.session_state.setdefault(f"{key}_tried", set())
    theta = st.slider("Logical state angle θ: cos(θ/2)|0⟩ + sin(θ/2)|1⟩", 0.0, float(np.pi), 1.2, step=0.05, key=f"{key}_theta")
    a, b = st.columns(2)
    first = a.selectbox("Error 1", list(CODE_ERRORS), index=1, key=f"{key}_err1")
    second = b.selectbox("Error 2", list(CODE_ERRORS), index=0, key=f"{key}_err2")
    errors = [CODE_ERRORS[e] for e in (first, second) if CODE_ERRORS[e]]
    st.code(str(ww.repetition_circuit(theta, errors).draw(output="text")), language=None)
    syndrome, fix, fidelity = ww.run_repetition_errors(theta, errors)
    logical_x, logical_z = logical_effect(errors, fix)
    action = "no correction" if fix is None else f"apply X to qubit {fix}"
    st.markdown(f"Syndrome **{syndrome}** → {action} · fidelity of the recovered logical qubit with the original: **{fidelity:.4f}**")
    if not (logical_x or logical_z):
        st.success("The logical qubit is back to its original state.")
    else:
        damage = " and ".join(n for n, hit in (("a logical X (bit flip)", logical_x), ("a logical Z (phase flip)", logical_z)) if hit)
        cause = "The syndrome didn't see the error" if syndrome == "00" else "The syndrome pointed at the wrong qubit"
        st.error(f"{cause}, so the code is left with {damage}.")
        if fidelity > 0.9999:
            st.caption("This particular θ happens to be unchanged by that logical error. Move the slider to see it.")
    scenario = code_scenario(errors)
    if scenario:
        tried.add(scenario)
    st.markdown("Try each of these: " + " · ".join(f"{'✅' if s in tried else '⬜'} {text}" for s, text in CODE_LESSONS.items()))
    return tried >= set(CODE_LESSONS)


KINDS: dict[str, Callable[[str, dict[str, Any]], bool]] = {
    "sort": sort_items,
    "order": order_steps,
    "check": check,
}

WIDGETS: dict[str, Callable[[str, dict[str, Any]], bool]] = {
    "room_bits": room_bits,
    "coin_race": coin_race,
    "recipe_proof": recipe_proof,
    "partner_game": partner_game,
    "percent_challenge": percent_challenge,
    "circuit_builder": circuit_builder,
    "born_rule_drill": born_rule_drill,
    "basis_list": basis_list,
    "product_state_predict": product_state_predict,
    "bell_statistics": bell_statistics,
    "teleport_flow": teleport_flow,
    "grover_trace": grover_trace,
    "noise_detective": noise_detective,
    "vqe_failure_lab": vqe_failure_lab,
    "maxcut_builder": maxcut_builder,
    "break_the_code": break_the_code,
}
