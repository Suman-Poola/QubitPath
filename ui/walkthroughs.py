"""Built-in lesson walkthroughs: one step at a time, with live Qiskit experiments.

``render_walkthrough(lesson)`` replaces the old "Recording panel" on the lesson
page. The steps themselves live in ui/walkthrough_content.py; the custom
experiments in ui/walkthrough_widgets.py.

Every widget key starts with ``wt_<lesson id>_`` because the lesson page renders
one lesson per level tab in the same run, and Streamlit keys must be unique.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler
from qiskit.quantum_info import Statevector

from ui.walkthrough_content import SOURCES, WALKTHROUGHS
from ui.walkthrough_widgets import WIDGETS

# Gates a "circuit" step may use, with the number of qubits each acts on.
GATES = {"h": 1, "x": 1, "z": 1, "cx": 2}
ANALOGY_NOTE = "\U0001F9E9 Picture idea: a comparison to help you imagine it, not exactly how the real thing works."


# ---------------------------------------------------------------------------
# Circuit helpers (also used by tests/test_walkthroughs.py)
# ---------------------------------------------------------------------------

def build_circuit(qubits: int, ops: Sequence[tuple[Any, ...]], measure: bool = True) -> QuantumCircuit:
    qc = QuantumCircuit(qubits)
    for name, *targets in ops:
        if GATES.get(name) != len(targets):
            raise ValueError(f"Unsupported gate {name}{tuple(targets)}")
        getattr(qc, name)(*targets)
    if measure:
        qc.measure_all()
    return qc


def circuit_code(qubits: int, ops: Sequence[tuple[Any, ...]], shots: int) -> str:
    """The Qiskit program equivalent to ``build_circuit`` + ``sample_counts``."""
    lines = [
        "from qiskit import QuantumCircuit",
        "from qiskit.primitives import StatevectorSampler",
        "",
        f"qc = QuantumCircuit({qubits})",
    ]
    lines += [f"qc.{name}({', '.join(str(t) for t in targets)})" for name, *targets in ops]
    lines += [
        "qc.measure_all()",
        "",
        f"result = StatevectorSampler().run([qc], shots={shots}).result()",
        "print(result[0].data.meas.get_counts())",
    ]
    return "\n".join(lines)


def outcomes(qubits: int) -> list[str]:
    return [format(i, f"0{qubits}b") for i in range(2**qubits)]


def ideal_probabilities(qubits: int, ops: Sequence[tuple[Any, ...]]) -> dict[str, float]:
    """Exact outcome probabilities for every bitstring (Qiskit order: qubit 0 is the rightmost bit)."""
    probs = Statevector.from_instruction(build_circuit(qubits, ops, measure=False)).probabilities_dict()
    return {o: float(probs.get(o, 0.0)) for o in outcomes(qubits)}


def sample_counts(qubits: int, ops: Sequence[tuple[Any, ...]], shots: int, seed: int | None = None) -> dict[str, int]:
    result = StatevectorSampler(seed=seed).run([build_circuit(qubits, ops)], shots=shots).result()
    counts = result[0].data.meas.get_counts()
    return {o: int(counts.get(o, 0)) for o in outcomes(qubits)}


def one_qubit_prediction(probs: dict[str, float]) -> int:
    """Index into the ["Always 0", "Always 1", "About half 0, half 1"] prediction options."""
    if probs["0"] > 0.999:
        return 0
    if probs["1"] > 0.999:
        return 1
    return 2


def counts_chart(counts: dict[str, int], key: str, title: str = "Results"):
    df = pd.DataFrame({"Result": list(counts), "Count": list(counts.values())})
    fig = px.bar(df, x="Result", y="Count", text="Count", title=title)
    fig.update_layout(height=260, margin=dict(l=10, r=10, t=40, b=10), xaxis_type="category")
    st.plotly_chart(fig, width="stretch", key=key)


def percent(value: float) -> str:
    return f"{100 * value:.1f}".rstrip("0").rstrip(".") + "%"


# ---------------------------------------------------------------------------
# Step elements
# ---------------------------------------------------------------------------

def _render_check(key: str, spec: dict[str, Any]) -> None:
    options = spec["options"]
    choice = st.radio(spec["question"], range(len(options)), format_func=lambda i: options[i], index=None, key=f"{key}_check")
    if choice is None:
        return
    if choice == spec["answer"]:
        st.success(f"Correct! {spec['why']}")
    else:
        st.warning("Not quite. Have another look and try a different answer.")


def _render_circuit(key: str, spec: dict[str, Any]) -> None:
    qubits, recipes, kid = spec["qubits"], spec["recipes"], spec.get("kid", False)
    names = list(recipes)
    name = names[0]
    if len(names) > 1:
        name = st.radio("Recipe" if kid else "Circuit", names, horizontal=True, key=f"{key}_recipe")
    ops = recipes[name]

    st.caption("Circuit picture (qubit 0 is the top line):" if kid else "Circuit (Qiskit text drawing):")
    st.code(str(build_circuit(qubits, ops, measure=spec.get("measure", True)).draw(output="text")), language=None)
    if spec.get("diagram_only"):
        return

    shot_options = spec.get("shots", [100])
    shots = shot_options[0]
    if len(shot_options) > 1:
        shots = st.radio(
            "How many times?" if kid else "Shots",
            shot_options,
            format_func=(lambda s: f"{s} times") if kid else str,
            horizontal=True,
            key=f"{key}_shots",
        )
    if spec.get("show_code"):
        st.code(circuit_code(qubits, ops, shots), language="python")

    probs = ideal_probabilities(qubits, ops)
    prediction = None
    if spec.get("predict"):
        prediction = st.radio("Your prediction", range(len(spec["predict"])), format_func=lambda i: spec["predict"][i],
                              index=None, horizontal=True, key=f"{key}_{name}_predict")

    result_key = f"{key}_result"
    if st.button("Run it!" if kid else "Run on the simulator", key=f"{key}_run", type="primary"):
        st.session_state[result_key] = (name, shots, sample_counts(qubits, ops, shots))
    result = st.session_state.get(result_key)
    if not result or result[0] != name:
        return

    _, ran_shots, counts = result
    counts_chart(counts, key=f"{key}_chart", title=f"Results from {ran_shots} {'tries' if kid else 'shots'}")
    seen = ", ".join(f"{o} → {c} ({percent(c / ran_shots)})" for o, c in counts.items() if c)
    theory = ", ".join(f"{o} → {percent(p)}" for o, p in probs.items() if p > 1e-9)
    st.markdown(f"**You got:** {seen}  \n**Theory predicts:** {theory}")
    if prediction is not None:
        expected = one_qubit_prediction(probs)
        if prediction == expected:
            st.success("Your prediction matches what theory says!")
        else:
            st.info(f"Theory says: **{spec['predict'][expected]}**. Compare that with your results.")


def _render_sources(step: dict[str, Any]) -> None:
    links = [f"[{SOURCES[k][0]}]({SOURCES[k][1]})" for k in step.get("sources", [])]
    lines = []
    if links:
        lines.append("\U0001F4DA **Source:** " + " · ".join(links))
    if step.get("checked"):
        lines.append(f"✅ **Checked:** {step['checked']}")
    if lines:
        st.caption("  \n".join(lines))


# ---------------------------------------------------------------------------
# Walkthrough
# ---------------------------------------------------------------------------

def _set_step(state_key: str, value: int) -> None:
    st.session_state[state_key] = value


def _finish(lesson_id: str) -> None:
    st.session_state[f"wt_{lesson_id}_done"] = True


def walkthrough_done(lesson_id: str) -> bool:
    return bool(st.session_state.get(f"wt_{lesson_id}_done"))


def _restart(lesson_id: str) -> None:
    st.session_state[f"wt_{lesson_id}_step"] = 0
    st.session_state[f"wt_{lesson_id}_done"] = False


def lesson_sources(lesson_id: str) -> list[str]:
    """Every source key cited by a lesson's walkthrough, in first-use order."""
    keys: list[str] = []
    for step in WALKTHROUGHS.get(lesson_id, []):
        keys += [k for k in step.get("sources", []) if k not in keys]
    return keys


def render_walkthrough(lesson: dict[str, Any]) -> None:
    """The step-by-step walkthrough for ``lesson`` (a CURRICULUM entry)."""
    lesson_id = lesson["id"]
    steps = WALKTHROUGHS.get(lesson_id)
    if not steps:
        return
    state_key = f"wt_{lesson_id}_step"
    index = min(st.session_state.setdefault(state_key, 0), len(steps) - 1)
    step = steps[index]
    key = f"wt_{lesson_id}_{index}"

    with st.container(border=True):
        st.markdown("#### \U0001F9ED Guided walkthrough")
        st.progress((index + 1) / len(steps), text=f"Step {index + 1} of {len(steps)}")
        st.markdown(f"##### {step['title']}")
        if step.get("analogy"):
            st.caption(ANALOGY_NOTE)
        st.markdown(step["body"])

        spec = step.get("try")
        if spec:
            if spec["kind"] == "check":
                _render_check(key, spec)
            elif spec["kind"] == "circuit":
                _render_circuit(key, spec)
            else:
                WIDGETS[spec["name"]](key, spec)
        _render_sources(step)

        back, _, forward = st.columns([1, 0.6, 1])
        back.button("← Back", key=f"{key}_back", on_click=_set_step, args=(state_key, index - 1),
                    disabled=index == 0, width="stretch")
        if index < len(steps) - 1:
            forward.button("Next →", key=f"{key}_next", on_click=_set_step, args=(state_key, index + 1),
                           type="primary", width="stretch")
        elif not st.session_state.get(f"wt_{lesson_id}_done"):
            forward.button("Finish ✓", key=f"{key}_finish", on_click=_finish, args=(lesson_id,),
                           type="primary", width="stretch")
        else:
            forward.button("Start over", key=f"{key}_restart", on_click=_restart, args=(lesson_id,), width="stretch")
        if index == len(steps) - 1 and st.session_state.get(f"wt_{lesson_id}_done"):
            st.success("Walkthrough complete! Do the hands-on activity below, then mark the lesson complete to earn XP.")

    with st.expander("Where this lesson's facts come from"):
        st.markdown(
            "Each step cites the official page it is based on (IBM Quantum Learning, the Qiskit documentation, "
            "IBM, or the Nobel Prize site). Experiment results are computed live with Qiskit.\n\n"
            + "\n".join(f"- [{SOURCES[k][0]}]({SOURCES[k][1]})" for k in lesson_sources(lesson_id))
        )
