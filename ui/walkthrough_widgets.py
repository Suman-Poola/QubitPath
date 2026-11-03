"""Custom experiments used by the lesson walkthroughs (ui/walkthrough_content.py).

Each widget is ``fn(key, spec)``: ``key`` is a unique prefix for its Streamlit
keys, ``spec`` the step's ``try`` dict. The physics lives in small pure
functions next to each widget so tests/test_walkthroughs.py can check it.
Circuits follow the official course conventions cited in the content file;
Qiskit's qubit 0 is the rightmost bit of every result string.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from functools import lru_cache
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from qiskit import QuantumCircuit
from qiskit.circuit.library import qaoa_ansatz, real_amplitudes
from qiskit.primitives import StatevectorEstimator, StatevectorSampler
from qiskit.quantum_info import DensityMatrix, SparsePauliOp, Statevector, partial_trace, state_fidelity
from scipy.optimize import minimize


def _pct(value: float) -> str:
    return f"{100 * value:.1f}".rstrip("0").rstrip(".") + "%"


def _chart_layout(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(title=title, height=280, margin=dict(l=10, r=10, t=40, b=10))
    return fig


# ---------------------------------------------------------------------------
# Elementary
# ---------------------------------------------------------------------------

def bit_switches(key: str, spec: dict[str, Any]) -> None:
    n = spec["switches"]
    bits = []
    for col, i in zip(st.columns(n), range(n)):
        with col:
            on = st.toggle(f"Switch {i + 1}", key=f"{key}_sw{i}")
            bulb = "\U0001F4A1" if on else "⚫"
            st.markdown(f"<div style='font-size:2rem;text-align:center'>{bulb} {int(on)}</div>", unsafe_allow_html=True)
            bits.append("1" if on else "0")
    pattern = "".join(bits)
    if n == 1:
        st.markdown(f"The switch is **{'on' if pattern == '1' else 'off'}**, so the bit is **{pattern}**.")
        return
    st.markdown(f"Your pattern is **{pattern}**. As a binary number that's **{int(pattern, 2)}**.")
    all_patterns = [format(i, f"0{n}b") for i in range(2**n)]
    st.markdown(f"With {n} switches there are **{len(all_patterns)}** patterns: "
                + " ".join(f"**`{p}`**" if p == pattern else f"`{p}`" for p in all_patterns))


def flip_coins(n: int, rng: np.random.Generator | None = None) -> list[str]:
    rng = rng or np.random.default_rng()
    return ["H" if r else "T" for r in rng.integers(0, 2, n)]


def coin_flips(key: str, spec: dict[str, Any]) -> None:
    a, b = st.columns(2)
    if a.button("Flip 10 times", key=f"{key}_flip10", width="stretch"):
        st.session_state[f"{key}_flips"] = flip_coins(10)
    if b.button("Flip 100 times", key=f"{key}_flip100", width="stretch"):
        st.session_state[f"{key}_flips"] = flip_coins(100)
    flips = st.session_state.get(f"{key}_flips")
    if flips:
        heads = flips.count("H")
        st.code(" ".join(flips), language=None)
        st.markdown(f"**Heads:** {heads} · **Tails:** {len(flips) - heads} · heads were **{_pct(heads / len(flips))}** of the flips.")


# ---------------------------------------------------------------------------
# Shots and single-qubit rotations
# ---------------------------------------------------------------------------

def ones_fraction(qc: QuantumCircuit, shots: int, runs: int, seed: int | None = None) -> list[float]:
    """Fraction of '1' results in each of ``runs`` independent runs of a 1-qubit circuit."""
    sampler = StatevectorSampler(seed=np.random.default_rng(seed))  # an int seed would make every run identical
    result = sampler.run([qc] * runs, shots=shots).result()
    return [result[i].data.meas.get_counts().get("1", 0) / shots for i in range(runs)]


def shot_spread(key: str, spec: dict[str, Any]) -> None:
    qc = QuantumCircuit(1)
    qc.h(0)
    qc.measure_all()
    if st.button("Run the H-gate circuit 5 times with 10 shots and 5 times with 1000 shots", key=f"{key}_run", type="primary"):
        st.session_state[f"{key}_data"] = (ones_fraction(qc, 10, 5), ones_fraction(qc, 1000, 5))
    data = st.session_state.get(f"{key}_data")
    if data:
        small, big = data
        st.dataframe(
            pd.DataFrame({"Run": range(1, 6), "% of 1s with 10 shots": [_pct(x) for x in small],
                          "% of 1s with 1000 shots": [_pct(x) for x in big]}),
            hide_index=True, width="stretch",
        )
        st.markdown(f"Spread (highest − lowest): **{_pct(max(small) - min(small))}** with 10 shots vs. "
                    f"**{_pct(max(big) - min(big))}** with 1000 shots. Theory: 50%.")


def ry_probability_of_one(theta: float) -> float:
    return float(np.sin(theta / 2) ** 2)


def ry_slider(key: str, spec: dict[str, Any]) -> None:
    degrees = st.slider("Angle θ (degrees)", 0, 180, 60, step=5, key=f"{key}_theta")
    theta = np.radians(degrees)
    predicted = ry_probability_of_one(theta)
    st.markdown(f"θ = {degrees}° = {theta:.3f} rad → predicted chance of 1 = sin²(θ/2) = **{_pct(predicted)}**")
    st.code(f"qc = QuantumCircuit(1)\nqc.ry({theta:.4f}, 0)\nqc.measure_all()", language="python")
    if st.button("Run 1000 shots", key=f"{key}_run", type="primary"):
        qc = QuantumCircuit(1)
        qc.ry(theta, 0)
        qc.measure_all()
        st.session_state[f"{key}_result"] = (degrees, ones_fraction(qc, 1000, 1)[0])
    result = st.session_state.get(f"{key}_result")
    if result and result[0] == degrees:
        st.markdown(f"Measured: **{_pct(result[1])}** of shots were 1 (predicted {_pct(predicted)}).")


# ---------------------------------------------------------------------------
# State vectors
# ---------------------------------------------------------------------------

# The three vectors from the course's Qiskit lesson (u, v, w), with the code that builds them.
COURSE_VECTORS = {
    "u = [1/sqrt(2), 1/sqrt(2)]": [1 / np.sqrt(2), 1 / np.sqrt(2)],
    "v = [(1 + 2.0j) / 3, -2 / 3]": [(1 + 2.0j) / 3, -2 / 3],
    "w = [1 / 3, 2 / 3]": [1 / 3, 2 / 3],
}


def statevector_check(key: str, spec: dict[str, Any]) -> None:
    label = st.radio("Vector", list(COURSE_VECTORS), key=f"{key}_vec")
    name, expr = label.split(" = ")
    vector = Statevector(COURSE_VECTORS[label])
    st.code(f"from qiskit.quantum_info import Statevector\nfrom numpy import sqrt\n\n{name} = Statevector({expr})\n{name}.is_valid()",
            language="python")
    norm_sq = float(np.sum(np.abs(vector.data) ** 2))
    if vector.is_valid():
        probs = vector.probabilities_dict()
        st.success(f"`is_valid()` → **True** (sum of |entries|² = {norm_sq:.4f}). "
                   f"Measurement probabilities: 0 → {probs.get('0', 0):.4f}, 1 → {probs.get('1', 0):.4f}.")
    else:
        st.error(f"`is_valid()` → **False**: the sum of |entries|² is {norm_sq:.4f}, not 1.")


def normalized(alpha: complex, beta: complex) -> tuple[complex, complex] | None:
    norm = np.sqrt(abs(alpha) ** 2 + abs(beta) ** 2)
    if norm < 1e-12:
        return None
    return alpha / norm, beta / norm


def normalize(key: str, spec: dict[str, Any]) -> None:
    cols = st.columns(4)
    values = [
        col.number_input(label, value=default, step=0.5, key=f"{key}_{i}")
        for i, (col, label, default) in enumerate(zip(cols, ["Re α", "Im α", "Re β", "Im β"], [1.0, 0.0, 1.0, 1.0]))
    ]
    alpha, beta = complex(values[0], values[1]), complex(values[2], values[3])
    result = normalized(alpha, beta)
    if result is None:
        st.warning("At least one amplitude must be nonzero.")
        return
    a, b = result
    state = Statevector([a, b])
    probs = state.probabilities_dict()
    st.markdown(
        f"|α|² + |β|² before normalizing = **{abs(alpha) ** 2 + abs(beta) ** 2:.4f}**. "
        f"Normalized: α = {a:.4f}, β = {b:.4f} (`Statevector.is_valid()` → {state.is_valid()}).  \n"
        f"Pr(0) = |α|² = **{probs.get('0', 0):.4f}**, Pr(1) = |β|² = **{probs.get('1', 0):.4f}**, sum = {sum(probs.values()):.4f}."
    )


def bell_circuit() -> QuantumCircuit:
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    return qc


def statevector_view(key: str, spec: dict[str, Any]) -> None:
    st.code("from qiskit.quantum_info import Statevector\n\nstate = Statevector.from_instruction(qc)\nprint(state.probabilities_dict())",
            language="python")
    state = Statevector.from_instruction(bell_circuit())
    probs = state.probabilities_dict()
    st.dataframe(
        pd.DataFrame({
            "Basis state": [f"|{o}⟩" for o in ("00", "01", "10", "11")],
            "Amplitude": [f"{state.data[int(o, 2)].real:+.4f}" for o in ("00", "01", "10", "11")],
            "Probability": [f"{probs.get(o, 0):.4f}" for o in ("00", "01", "10", "11")],
        }),
        hide_index=True, width="stretch",
    )


# ---------------------------------------------------------------------------
# Multiple qubits and entanglement
# ---------------------------------------------------------------------------

def basis_states(key: str, spec: dict[str, Any]) -> None:
    n = st.slider("Number of qubits n", 1, 6, 3, key=f"{key}_n")
    states = [format(i, f"0{n}b") for i in range(2**n)]
    st.markdown(f"**2^{n} = {len(states)}** classical states / state-vector entries:")
    st.code(" ".join(states), language=None)


SINGLE_QUBIT_LABELS = ["0", "1", "+", "-"]


def tensor_product(key: str, spec: dict[str, Any]) -> None:
    left_col, right_col = st.columns(2)
    left = left_col.selectbox("Left factor (qubit 1)", SINGLE_QUBIT_LABELS, index=0, format_func=lambda s: f"|{s}⟩", key=f"{key}_l")
    right = right_col.selectbox("Right factor (qubit 0)", SINGLE_QUBIT_LABELS, index=2, format_func=lambda s: f"|{s}⟩", key=f"{key}_r")
    product = Statevector.from_label(left).tensor(Statevector.from_label(right))
    st.code(f'Statevector.from_label("{left}").tensor(Statevector.from_label("{right}"))', language="python")
    terms = [f"({product.data[i].real:+.4f})|{format(i, '02b')}⟩" for i in range(4) if abs(product.data[i]) > 1e-12]
    st.markdown("Result: " + " ".join(terms) + f"  \nSame as `Statevector.from_label(\"{left}{right}\")`: "
                f"**{product.equiv(Statevector.from_label(left + right))}**")


def correlation_probabilities(hadamard_first: bool) -> tuple[dict[str, float], dict[str, float]]:
    """Outcome probabilities for |phi+> and for the classical 50/50 mixture of 00 and 11."""
    entangled = DensityMatrix(bell_circuit())
    classical = 0.5 * DensityMatrix.from_label("00") + 0.5 * DensityMatrix.from_label("11")
    if hadamard_first:
        hh = QuantumCircuit(2)
        hh.h([0, 1])
        entangled, classical = entangled.evolve(hh), classical.evolve(hh)
    keys = ("00", "01", "10", "11")
    pe, pc = entangled.probabilities_dict(), classical.probabilities_dict()
    return {k: float(pe.get(k, 0)) for k in keys}, {k: float(pc.get(k, 0)) for k in keys}


def correlation_vs_entanglement(key: str, spec: dict[str, Any]) -> None:
    basis = st.radio("Measure", ["Directly (standard basis)", "After a Hadamard on both qubits"], horizontal=True, key=f"{key}_basis")
    entangled, classical = correlation_probabilities(basis.startswith("After"))
    fig = go.Figure([
        go.Bar(name="Entangled |φ⁺⟩", x=list(entangled), y=list(entangled.values())),
        go.Bar(name="Classical 00-or-11 pair", x=list(classical), y=list(classical.values())),
    ])
    fig.update_layout(barmode="group", yaxis_range=[0, 1], xaxis_type="category", yaxis_title="Probability")
    st.plotly_chart(_chart_layout(fig, "Exact outcome probabilities"), width="stretch", key=f"{key}_chart")


# ---------------------------------------------------------------------------
# Teleportation and superdense coding
# ---------------------------------------------------------------------------

def qubit_state(theta: float, phi: float) -> Statevector:
    return Statevector([np.cos(theta / 2), np.exp(1j * phi) * np.sin(theta / 2)])


def teleportation_circuit(theta: float, phi: float) -> QuantumCircuit:
    """Qubits: 0 = Q (Alice's state), 1 = A (Alice's half of the e-bit), 2 = B (Bob's half).

    Bob's classically controlled X (if a = 1) and Z (if b = 1) are written as controlled gates
    from A and Q, which gives the same result as measuring first (deferred measurement).
    """
    qc = QuantumCircuit(3)
    qc.ry(theta, 0)
    qc.p(phi, 0)
    qc.barrier()
    qc.h(1)
    qc.cx(1, 2)  # e-bit shared by A and B
    qc.barrier()
    qc.cx(0, 1)  # Alice: CNOT, Q control, A target
    qc.h(0)  # Alice: Hadamard on Q
    qc.barrier()
    qc.cx(1, 2)  # Bob: X if a = 1
    qc.cz(0, 2)  # Bob: Z if b = 1
    return qc


def teleport_results(theta: float, phi: float) -> tuple[dict[str, float], float]:
    """Alice's outcome probabilities (keys 'ab') and the fidelity of Bob's qubit with the input."""
    final = Statevector.from_instruction(teleportation_circuit(theta, phi))
    probs = final.probabilities_dict(qargs=[0, 1])  # key = (A, Q) = (a, b)
    bob = partial_trace(final, [0, 1])
    return {k: float(probs.get(k, 0)) for k in ("00", "01", "10", "11")}, float(state_fidelity(bob, qubit_state(theta, phi)))


def teleport(key: str, spec: dict[str, Any]) -> None:
    a, b = st.columns(2)
    theta = a.slider("θ (polar angle)", 0.0, float(np.pi), 1.1, step=0.05, key=f"{key}_theta")
    phi = b.slider("φ (phase)", 0.0, float(2 * np.pi), 0.7, step=0.05, key=f"{key}_phi")
    psi = qubit_state(theta, phi).data
    st.markdown(f"Q starts in {psi[0].real:.3f}|0⟩ + ({psi[1]:.3f})|1⟩.")
    st.code(str(teleportation_circuit(theta, phi).draw(output="text")), language=None)
    probs, fidelity = teleport_results(theta, phi)
    corrections = {"00": "nothing", "01": "Z", "10": "X", "11": "X then Z"}
    st.dataframe(
        pd.DataFrame({"Alice's bits ab": list(probs), "Probability": [f"{p:.4f}" for p in probs.values()],
                      "Bob applies": [corrections[k] for k in probs]}),
        hide_index=True, width="stretch",
    )
    st.success(f"Fidelity between Bob's qubit and the original state: **{fidelity:.6f}** (1 means identical).")


def superdense_circuit(c: int, d: int) -> QuantumCircuit:
    """Qubits: 0 = A (Alice), 1 = B (Bob). Result string is 'BA' = 'cd'."""
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)  # shared e-bit
    qc.barrier()
    if d:
        qc.z(0)
    if c:
        qc.x(0)
    qc.barrier()
    qc.cx(0, 1)  # Bob: CNOT, A control, B target
    qc.h(0)  # Bob: Hadamard on A
    return qc


def superdense_result(c: int, d: int) -> dict[str, float]:
    probs = Statevector.from_instruction(superdense_circuit(c, d)).probabilities_dict()
    return {k: float(v) for k, v in probs.items() if v > 1e-9}


def superdense(key: str, spec: dict[str, Any]) -> None:
    a, b = st.columns(2)
    c = a.radio("Bit c", [0, 1], horizontal=True, key=f"{key}_c")
    d = b.radio("Bit d", [0, 1], horizontal=True, key=f"{key}_d")
    st.code(str(superdense_circuit(c, d).draw(output="text")), language=None)
    result = superdense_result(c, d)
    st.markdown("Bob measures B then A and reads: " + ", ".join(f"**{k}** with probability {v:.4f}" for k, v in result.items())
                + f". He sent for **{c}{d}**.")


# ---------------------------------------------------------------------------
# Query algorithms
# ---------------------------------------------------------------------------

DJ_N = 3
# label: (constant value or None, input bits XORed together for balanced functions)
DJ_FUNCTIONS: dict[str, tuple[int | None, tuple[int, ...]]] = {
    "Constant: f(x) = 0": (0, ()),
    "Constant: f(x) = 1": (1, ()),
    "Balanced: f(x) = x₀": (None, (0,)),
    "Balanced: f(x) = x₁ ⊕ x₂": (None, (1, 2)),
    "Balanced: f(x) = x₀ ⊕ x₁ ⊕ x₂": (None, (0, 1, 2)),
}


def dj_truth_table(label: str) -> dict[str, int]:
    constant, bits = DJ_FUNCTIONS[label]
    table = {}
    for i in range(2**DJ_N):
        x = format(i, f"0{DJ_N}b")  # x[-1] is x0
        table[x] = constant if constant is not None else sum(int(x[-1 - b]) for b in bits) % 2
    return table


def dj_circuit(label: str) -> QuantumCircuit:
    """Inputs on qubits 0..n-1, the query gate's output qubit on qubit n (prepared in |->)."""
    constant, bits = DJ_FUNCTIONS[label]
    qc = QuantumCircuit(DJ_N + 1)
    qc.x(DJ_N)
    qc.h(range(DJ_N + 1))
    qc.barrier()
    if constant == 1:
        qc.x(DJ_N)
    for b in bits:
        qc.cx(b, DJ_N)
    qc.barrier()
    qc.h(range(DJ_N))
    return qc


def dj_probability_all_zero(label: str) -> float:
    probs = Statevector.from_instruction(dj_circuit(label)).probabilities_dict(qargs=list(range(DJ_N)))
    return float(probs.get("0" * DJ_N, 0.0))


def deutsch_jozsa(key: str, spec: dict[str, Any]) -> None:
    label = st.selectbox("Hidden function (n = 3)", list(DJ_FUNCTIONS), key=f"{key}_f")
    table = dj_truth_table(label)
    ones = sum(table.values())
    st.caption("Truth table: " + " · ".join(f"f({x}) = {v}" for x, v in table.items())
               + f"  → {ones} ones and {len(table) - ones} zeros")
    st.code(str(dj_circuit(label).draw(output="text")), language=None)
    p0 = dj_probability_all_zero(label)
    verdict = "constant" if p0 > 0.999 else "balanced"
    st.markdown(f"Probability that every measured bit is 0: **{p0:.4f}** → the algorithm answers **{verdict}** after one query.")


def grover_circuit(n: int, marked: str, iterations: int) -> QuantumCircuit:
    """Grover search for one marked bitstring (Qiskit order: marked[-1] is qubit 0)."""
    qc = QuantumCircuit(n)
    qc.h(range(n))
    zeros = [q for q in range(n) if marked[n - 1 - q] == "0"]

    def flip_all_ones() -> None:  # phase -1 on |1...1>
        qc.h(n - 1)
        qc.mcx(list(range(n - 1)), n - 1)
        qc.h(n - 1)

    for _ in range(iterations):
        if zeros:
            qc.x(zeros)
        flip_all_ones()  # oracle: phase -1 on the marked string
        if zeros:
            qc.x(zeros)
        qc.h(range(n))
        qc.x(range(n))
        flip_all_ones()  # diffusion: reflect about the uniform superposition (up to a global phase)
        qc.x(range(n))
        qc.h(range(n))
    return qc


@lru_cache(maxsize=256)
def grover_success(n: int, marked: str, iterations: int) -> float:
    return float(Statevector.from_instruction(grover_circuit(n, marked, iterations)).probabilities_dict().get(marked, 0.0))


def grover_theory(n: int, iterations: int, solutions: int = 1) -> float:
    theta = np.arcsin(np.sqrt(solutions / 2**n))
    return float(np.sin((2 * iterations + 1) * theta) ** 2)


def grover_recommended(n: int, solutions: int = 1) -> int:
    return int(np.floor(np.pi / (4 * np.arcsin(np.sqrt(solutions / 2**n)))))


def grover(key: str, spec: dict[str, Any]) -> None:
    a, b = st.columns(2)
    n = a.select_slider("Qubits n (N = 2ⁿ items)", [2, 3, 4, 5], value=3, key=f"{key}_n")
    marked = b.selectbox("Marked item", [format(i, f"0{n}b") for i in range(2**n)], index=2**n - 1, key=f"{key}_m{n}")
    recommended = grover_recommended(n)
    max_t = 2 * recommended + 2
    t = st.slider("Grover iterations t", 0, max_t, recommended, key=f"{key}_t{n}")
    sim = [grover_success(n, marked, k) for k in range(max_t + 1)]
    fig = go.Figure([
        go.Scatter(x=list(range(max_t + 1)), y=[grover_theory(n, k) for k in range(max_t + 1)], mode="lines", name="sin²((2t+1)θ)"),
        go.Scatter(x=list(range(max_t + 1)), y=sim, mode="markers", name="Qiskit simulation", marker=dict(size=9)),
    ])
    fig.add_vline(x=t, line_dash="dot")
    fig.update_layout(xaxis_title="Iterations t", yaxis_title="Probability of the marked item", yaxis_range=[0, 1.05])
    st.plotly_chart(_chart_layout(fig, f"N = {2**n}, recommended t = ⌊π/(4θ)⌋ = {recommended}"),
                    width="stretch", key=f"{key}_chart")
    st.markdown(f"After **{t}** iteration(s), measuring gives **{marked}** with probability **{sim[t]:.4f}** "
                f"(each iteration makes one query).")


# ---------------------------------------------------------------------------
# Density matrices and noise
# ---------------------------------------------------------------------------

NOISE_STATES = {"|0⟩": "0", "|1⟩": "1", "|+⟩": "+", "|−⟩": "-"}


def apply_noise(rho: DensityMatrix, channel: str, p: float) -> DensityMatrix:
    """With probability p apply the completely dephasing or completely depolarizing channel."""
    if channel == "Dephasing":
        noisy = DensityMatrix(np.diag(np.diag(rho.data)))
    else:
        noisy = DensityMatrix(np.trace(rho.data) * np.eye(2) / 2)
    return DensityMatrix((1 - p) * rho.data + p * noisy.data)


def bloch_vector(rho: DensityMatrix) -> tuple[float, float, float]:
    return tuple(float(np.real(rho.expectation_value(SparsePauliOp(p)))) for p in "XYZ")


def noise(key: str, spec: dict[str, Any]) -> None:
    a, b, c = st.columns(3)
    label = a.selectbox("Input state", list(NOISE_STATES), index=2, key=f"{key}_state")
    channel = b.selectbox("Channel", ["Dephasing", "Depolarizing"], key=f"{key}_channel")
    p = c.slider("Probability p", 0.0, 1.0, 0.5, step=0.05, key=f"{key}_p")
    out = apply_noise(DensityMatrix.from_label(NOISE_STATES[label]), channel, p)
    m = out.data
    st.latex(r"\rho_{\text{out}} = \begin{pmatrix} %.3f & %.3f%+.3fi \\ %.3f%+.3fi & %.3f \end{pmatrix}"
             % (m[0, 0].real, m[0, 1].real, m[0, 1].imag, m[1, 0].real, m[1, 0].imag, m[1, 1].real))
    hadamard = QuantumCircuit(1)
    hadamard.h(0)
    z_probs, x_probs = out.probabilities_dict(), out.evolve(hadamard).probabilities_dict()
    x, y, z = bloch_vector(out)
    st.markdown(
        f"Purity Tr(ρ²) = **{out.purity().real:.3f}** · Bloch vector ({x:.2f}, {y:.2f}, {z:.2f}), length "
        f"{np.sqrt(x * x + y * y + z * z):.2f}  \nStandard-basis Pr(0) = **{z_probs.get('0', 0):.3f}** · "
        f"after H (X basis) Pr(0) = **{x_probs.get('0', 0):.3f}**"
    )


# ---------------------------------------------------------------------------
# Variational algorithms
# ---------------------------------------------------------------------------

VQE_HAMILTONIAN = SparsePauliOp.from_list([("ZZ", 1.0), ("XI", 0.5), ("IX", 0.5)])  # toy example, not a molecule


def vqe_exact_ground_energy() -> float:
    return float(np.min(np.linalg.eigvalsh(VQE_HAMILTONIAN.to_matrix())))


def run_vqe(x0: Sequence[float] | None = None, maxiter: int = 300,
            ansatz: QuantumCircuit | None = None) -> tuple[list[float], float]:
    """Minimize <H> over an ansatz (default real_amplitudes) with COBYLA; returns (energy history, final energy)."""
    ansatz = real_amplitudes(2, reps=1) if ansatz is None else ansatz
    estimator = StatevectorEstimator()
    history: list[float] = []

    def cost(params: np.ndarray) -> float:
        energy = float(estimator.run([(ansatz, VQE_HAMILTONIAN, params)]).result()[0].data.evs)
        history.append(energy)
        return energy

    start = np.ones(ansatz.num_parameters) if x0 is None else np.asarray(x0, dtype=float)
    result = minimize(cost, start, method="COBYLA", options={"maxiter": maxiter})
    return history, float(result.fun)


def vqe(key: str, spec: dict[str, Any]) -> None:
    st.code(
        "from qiskit.circuit.library import real_amplitudes\nfrom qiskit.primitives import StatevectorEstimator\n"
        "from qiskit.quantum_info import SparsePauliOp\nfrom scipy.optimize import minimize\nimport numpy as np\n\n"
        'H = SparsePauliOp.from_list([("ZZ", 1.0), ("XI", 0.5), ("IX", 0.5)])\n'
        "ansatz = real_amplitudes(2, reps=1)\nestimator = StatevectorEstimator()\n\n"
        "def cost(params):\n    return estimator.run([(ansatz, H, params)]).result()[0].data.evs\n\n"
        'result = minimize(cost, np.ones(ansatz.num_parameters), method="COBYLA")',
        language="python",
    )
    if st.button("Run VQE", key=f"{key}_run", type="primary"):
        st.session_state[f"{key}_result"] = run_vqe()
    result = st.session_state.get(f"{key}_result")
    if result:
        history, final = result
        exact = vqe_exact_ground_energy()
        fig = go.Figure([go.Scatter(y=history, mode="lines", name="⟨H⟩ at each evaluation")])
        fig.add_hline(y=exact, line_dash="dot", annotation_text="exact ground energy")
        fig.update_layout(xaxis_title="Cost evaluations", yaxis_title="Energy")
        st.plotly_chart(_chart_layout(fig, "VQE convergence"), width="stretch", key=f"{key}_chart")
        st.markdown(f"VQE energy **{final:.5f}** · exact ground energy **{exact:.5f}** (smallest eigenvalue of H) "
                    f"· difference {final - exact:.2e}, never below the exact value, as the variational theorem requires.")


QAOA_EDGES = [(0, 1), (1, 2), (2, 3), (3, 0)]
QAOA_NODES = 4


def qaoa_cost_hamiltonian(edges: Sequence[tuple[int, int]] = QAOA_EDGES) -> tuple[SparsePauliOp, float]:
    """1/2 Z_i Z_j per edge, with the offset that makes cut = -(<H_C> + offset), as in the Qiskit tutorial."""
    terms = [("ZZ", [i, j], 0.5) for i, j in edges]
    return SparsePauliOp.from_sparse_list(terms, num_qubits=QAOA_NODES), -len(edges) / 2


def cut_value(bitstring: str, edges: Sequence[tuple[int, int]] = QAOA_EDGES) -> int:
    """Edges crossing the partition (Qiskit order: bitstring[-1] is node 0)."""
    side = [int(bitstring[-1 - i]) for i in range(QAOA_NODES)]
    return sum(side[i] != side[j] for i, j in edges)


def qaoa_state(gamma: float, beta: float, edges: Sequence[tuple[int, int]] = QAOA_EDGES) -> Statevector:
    hamiltonian, _ = qaoa_cost_hamiltonian(edges)
    ansatz = qaoa_ansatz(hamiltonian, reps=1)
    values = {p: (beta if p.name.startswith("β") else gamma) for p in ansatz.parameters}
    return Statevector(ansatz.assign_parameters(values))


def qaoa_expected_cut(gamma: float, beta: float, edges: Sequence[tuple[int, int]] = QAOA_EDGES) -> float:
    hamiltonian, offset = qaoa_cost_hamiltonian(edges)
    return float(-(np.real(qaoa_state(gamma, beta, edges).expectation_value(hamiltonian)) + offset))


def optimize_qaoa(start: tuple[float, float] = (0.5, 0.5),
                  edges: Sequence[tuple[int, int]] = QAOA_EDGES) -> tuple[float, float]:
    """COBYLA over gamma, beta in [0, pi] (the sliders' range), maximizing the expected cut."""
    result = minimize(lambda x: -qaoa_expected_cut(x[0], x[1], edges), np.array(start), method="COBYLA",
                      bounds=[(0.0, np.pi)] * 2)
    gamma, beta = np.clip(result.x, 0.0, np.pi)
    return float(gamma), float(beta)


def _qaoa_optimize_callback(key: str) -> None:
    gamma, beta = optimize_qaoa((st.session_state[f"{key}_gamma"], st.session_state[f"{key}_beta"]))
    st.session_state[f"{key}_gamma"] = gamma
    st.session_state[f"{key}_beta"] = beta


def qaoa(key: str, spec: dict[str, Any]) -> None:
    st.session_state.setdefault(f"{key}_gamma", 0.5)
    st.session_state.setdefault(f"{key}_beta", 0.5)
    a, b = st.columns(2)
    gamma = a.slider("γ (cost angle)", 0.0, float(np.pi), step=0.01, key=f"{key}_gamma")
    beta = b.slider("β (mixer angle)", 0.0, float(np.pi), step=0.01, key=f"{key}_beta")
    st.button("Optimize γ and β with COBYLA", key=f"{key}_opt", on_click=_qaoa_optimize_callback, args=(key,))
    expected = qaoa_expected_cut(gamma, beta)
    best = max(cut_value(format(i, f"0{QAOA_NODES}b")) for i in range(2**QAOA_NODES))
    st.markdown(f"Expected cut **{expected:.3f}** of a maximum **{best}** → approximation ratio **{expected / best:.3f}**")
    probs = qaoa_state(gamma, beta).probabilities_dict()
    top = sorted(probs.items(), key=lambda kv: -kv[1])[:6]
    st.dataframe(
        pd.DataFrame({"Bitstring (node 3 … node 0)": [k for k, _ in top], "Probability": [f"{v:.3f}" for _, v in top],
                      "Cut value": [cut_value(k) for k, _ in top]}),
        hide_index=True, width="stretch",
    )


# ---------------------------------------------------------------------------
# Error correction
# ---------------------------------------------------------------------------

REPETITION_ERRORS = {
    "No error": None,
    "Bit flip (X) on qubit 0": ("x", 0),
    "Bit flip (X) on qubit 1": ("x", 1),
    "Bit flip (X) on qubit 2": ("x", 2),
    "Phase flip (Z) on qubit 1": ("z", 1),
}
# Syndrome string (ancilla 4 = parity of qubits 1,2; ancilla 3 = parity of qubits 0,1) -> qubit to flip.
SYNDROME_CORRECTION = {"00": None, "01": 0, "11": 1, "10": 2}


def _error_list(error: str) -> list[tuple[str, int]]:
    return [REPETITION_ERRORS[error]] if REPETITION_ERRORS[error] else []


def repetition_circuit(theta: float, errors: Sequence[tuple[str, int]]) -> QuantumCircuit:
    """Data qubits 0-2, ancillas 3 (parity of 0,1) and 4 (parity of 1,2); ``errors`` are (gate, qubit) pairs."""
    qc = QuantumCircuit(5)
    qc.ry(theta, 0)
    qc.cx(0, 1)
    qc.cx(0, 2)  # encode a|0> + b|1> as a|000> + b|111>
    qc.barrier()
    for gate, qubit in errors:
        getattr(qc, gate)(qubit)
    qc.barrier()
    qc.cx(0, 3)
    qc.cx(1, 3)
    qc.cx(1, 4)
    qc.cx(2, 4)
    return qc


def repetition_syndrome_circuit(theta: float, error: str) -> QuantumCircuit:
    return repetition_circuit(theta, _error_list(error))


def run_repetition_code(theta: float, error: str) -> tuple[str, int | None, float]:
    """Returns (syndrome, corrected qubit, fidelity of the decoded logical qubit with the original)."""
    return run_repetition_errors(theta, _error_list(error))


def run_repetition_errors(theta: float, errors: Sequence[tuple[str, int]]) -> tuple[str, int | None, float]:
    """``run_repetition_code`` for any list of X/Z errors."""
    state = Statevector.from_instruction(repetition_circuit(theta, errors))
    syndrome_probs = state.probabilities_dict(qargs=[3, 4])
    syndrome = max(syndrome_probs, key=syndrome_probs.get)  # deterministic: X/Z errors keep a definite parity
    fix = SYNDROME_CORRECTION[syndrome]
    tail = QuantumCircuit(5)
    if fix is not None:
        tail.x(fix)
    tail.cx(0, 2)
    tail.cx(0, 1)  # decode
    decoded = partial_trace(state.evolve(tail), [1, 2, 3, 4])
    original = Statevector([np.cos(theta / 2), np.sin(theta / 2)])
    return syndrome, fix, float(state_fidelity(decoded, original))


def repetition_code(key: str, spec: dict[str, Any]) -> None:
    a, b = st.columns(2)
    theta = a.slider("Logical state angle θ: cos(θ/2)|0⟩ + sin(θ/2)|1⟩", 0.0, float(np.pi), 1.2, step=0.05, key=f"{key}_theta")
    error = b.selectbox("Error", list(REPETITION_ERRORS), index=2, key=f"{key}_error")
    st.code(str(repetition_syndrome_circuit(theta, error).draw(output="text")), language=None)
    syndrome, fix, fidelity = run_repetition_code(theta, error)
    action = "no correction" if fix is None else f"apply X to qubit {fix}"
    st.markdown(f"Syndrome **{syndrome}** → {action}. Fidelity of the recovered logical qubit with the original: **{fidelity:.4f}**")
    if fidelity < 0.9999:
        st.warning("The code didn't recover the state: the 3-bit repetition code can't detect phase flips.")


WIDGETS: dict[str, Callable[[str, dict[str, Any]], None]] = {
    "bit_switches": bit_switches,
    "coin_flips": coin_flips,
    "shot_spread": shot_spread,
    "ry_slider": ry_slider,
    "statevector_check": statevector_check,
    "normalize": normalize,
    "statevector_view": statevector_view,
    "basis_states": basis_states,
    "tensor_product": tensor_product,
    "correlation_vs_entanglement": correlation_vs_entanglement,
    "teleport": teleport,
    "superdense": superdense,
    "deutsch_jozsa": deutsch_jozsa,
    "grover": grover,
    "noise": noise,
    "vqe": vqe,
    "qaoa": qaoa,
    "repetition_code": repetition_code,
}
