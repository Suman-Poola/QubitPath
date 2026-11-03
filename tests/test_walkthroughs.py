"""Checks that every lesson walkthrough is sourced and that its claims hold in Qiskit.

Run from the repo root:  python -m unittest discover tests
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import qaoa_ansatz
from qiskit.quantum_info import DensityMatrix, Operator, Statevector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ui import walkthrough_widgets as w  # noqa: E402
from ui.walkthrough_content import SOURCES, WALKTHROUGHS  # noqa: E402
from ui.walkthroughs import build_circuit, circuit_code, ideal_probabilities, sample_counts  # noqa: E402

OFFICIAL_HOSTS = {"quantum.cloud.ibm.com", "www.ibm.com", "www.nobelprize.org"}
LESSON_IDS = re.findall(r'"id": "([A-Z]{2}\d)"', (ROOT / "app.py").read_text(encoding="utf-8"))


def steps(kind: str | None = None):
    for lesson_id, lesson_steps in WALKTHROUGHS.items():
        for index, step in enumerate(lesson_steps):
            spec = step.get("try")
            if kind is None or (spec and spec["kind"] == kind):
                yield lesson_id, index, step


def recipe(lesson_id: str, title: str, name: str):
    step = next(s for s in WALKTHROUGHS[lesson_id] if s["title"] == title)
    return step["try"]["qubits"], step["try"]["recipes"][name]


def probs_of(lesson_id: str, title: str, name: str) -> dict[str, float]:
    qubits, ops = recipe(lesson_id, title, name)
    return {k: round(v, 9) for k, v in ideal_probabilities(qubits, ops).items() if v > 1e-9}


class TestStructureAndSources(unittest.TestCase):
    def test_every_lesson_has_a_walkthrough(self):
        self.assertEqual(len(LESSON_IDS), 20)
        self.assertEqual(sorted(LESSON_IDS), sorted(WALKTHROUGHS))
        for lesson_id in LESSON_IDS:
            self.assertGreaterEqual(len(WALKTHROUGHS[lesson_id]), 4, lesson_id)

    def test_every_step_is_sourced_or_checked(self):
        for lesson_id, index, step in steps():
            with self.subTest(lesson=lesson_id, step=index):
                self.assertTrue(step["title"] and step["body"])
                self.assertTrue(step.get("sources") or step.get("checked"))
                for key in step.get("sources", []):
                    self.assertIn(key, SOURCES)

    def test_sources_are_official_https_pages(self):
        for key, (title, url) in SOURCES.items():
            with self.subTest(source=key):
                parsed = urlparse(url)
                self.assertEqual(parsed.scheme, "https")
                self.assertIn(parsed.netloc, OFFICIAL_HOSTS)
                self.assertTrue(title)

    def test_every_source_is_used(self):
        used = {k for _, _, step in steps() for k in step.get("sources", [])}
        self.assertEqual(used, set(SOURCES))

    def test_no_literal_unicode_escapes(self):
        # A "’" inside an r-string would show up as backslash-u text on the page.
        needle = chr(92) + "u"
        for lesson_id, index, step in steps():
            with self.subTest(lesson=lesson_id, step=index):
                self.assertNotIn(needle, repr([step["title"], step["body"], step.get("try", {})]).replace("\\\\u", needle))

    def test_interactive_specs_are_valid(self):
        for lesson_id, index, step in steps():
            spec = step.get("try")
            if not spec:
                continue
            with self.subTest(lesson=lesson_id, step=index):
                if spec["kind"] == "check":
                    self.assertGreaterEqual(len(spec["options"]), 2)
                    self.assertIn(spec["answer"], range(len(spec["options"])))
                    self.assertTrue(spec["why"])
                elif spec["kind"] == "widget":
                    self.assertIn(spec["name"], w.WIDGETS)
                else:
                    self.assertEqual(spec["kind"], "circuit")
                    for ops in spec["recipes"].values():
                        build_circuit(spec["qubits"], ops)


class TestCircuitSteps(unittest.TestCase):
    def test_displayed_code_runs_and_matches_theory(self):
        for lesson_id, index, step in steps("circuit"):
            spec = step["try"]
            for name, ops in spec["recipes"].items():
                with self.subTest(lesson=lesson_id, step=index, recipe=name):
                    namespace: dict = {}
                    exec(circuit_code(spec["qubits"], ops, 2000).replace("print(", "counts = ("), namespace)  # noqa: S102
                    counts = namespace["counts"]
                    probs = ideal_probabilities(spec["qubits"], ops)
                    self.assertEqual(sum(counts.values()), 2000)
                    for outcome, count in counts.items():
                        self.assertGreater(probs[outcome], 0, f"{outcome} should be impossible")
                        self.assertAlmostEqual(count / 2000, probs[outcome], delta=0.06)
                    sampled = sample_counts(spec["qubits"], ops, 500, seed=11)
                    self.assertEqual(sum(sampled.values()), 500)

    def test_elementary_and_proficient_results(self):
        self.assertEqual(probs_of("EL2", "Spin the magic coin", "Magic coin"), {"0": 0.5, "1": 0.5})
        self.assertEqual(probs_of("EL3", "The Flip switch (X gate)", "Flip"), {"1": 1.0})
        self.assertEqual(probs_of("EL3", "Two-switch recipes", "Flip → Flip"), {"0": 1.0})
        self.assertEqual(probs_of("EL3", "Two-switch recipes", "Flip → Maybe"), {"0": 0.5, "1": 0.5})
        self.assertEqual(probs_of("EL3", "Two-switch recipes", "Maybe → Maybe"), {"0": 1.0})
        self.assertEqual(probs_of("EL4", "Make partner coins", "Partner coins"), {"00": 0.5, "11": 0.5})
        self.assertEqual(probs_of("MS4", "A two-qubit gate: CNOT", "Control 0: CX only"), {"00": 1.0})
        self.assertEqual(probs_of("MS4", "A two-qubit gate: CNOT", "Control 1: X, then CX"), {"11": 1.0})

    def test_plus_minus_discrimination(self):
        title = "Same statistics, different states"
        self.assertEqual(probs_of("HF2", title, "|+⟩, measure"), {"0": 0.5, "1": 0.5})
        self.assertEqual(probs_of("HF2", title, "|−⟩, measure"), {"0": 0.5, "1": 0.5})
        self.assertEqual(probs_of("HF2", title, "|+⟩, H, measure"), {"0": 1.0})
        self.assertEqual(probs_of("HF2", title, "|−⟩, H, measure"), {"1": 1.0})
        minus = Statevector.from_instruction(build_circuit(1, [("x", 0), ("h", 0)], measure=False))
        self.assertTrue(minus.equiv(Statevector([1, -1]) / np.sqrt(2)))

    def test_gate_identities(self):
        hzh = QuantumCircuit(1)
        hzh.h(0)
        hzh.z(0)
        hzh.h(0)
        x = QuantumCircuit(1)
        x.x(0)
        self.assertTrue(Operator(hzh).equiv(Operator(x)))
        self.assertEqual(probs_of("HF3", "Z is invisible, until you sandwich it", "H, Z, H"), {"1": 1.0})
        self.assertEqual(probs_of("HF3", "Z is invisible, until you sandwich it", "Z only"), {"0": 1.0})
        self.assertTrue(np.allclose(Operator(build_circuit(1, [("h", 0)], measure=False)).data, np.array([[1, 1], [1, -1]]) / np.sqrt(2)))
        z = Operator(build_circuit(1, [("z", 0)], measure=False)).data
        self.assertTrue(np.allclose(z, np.diag([1, -1])))
        for theta in np.linspace(0, np.pi, 7):
            qc = QuantumCircuit(1)
            qc.ry(theta, 0)
            expected = np.array([[np.cos(theta / 2), -np.sin(theta / 2)], [np.sin(theta / 2), np.cos(theta / 2)]])
            self.assertTrue(np.allclose(Operator(qc).data, expected))
            self.assertAlmostEqual(Statevector(qc).probabilities_dict().get("1", 0.0), w.ry_probability_of_one(theta))

    def test_qiskit_ordering(self):
        self.assertEqual(probs_of("HF3", "Qiskit's ordering conventions", "x on qubit 1"), {"10": 1.0})
        self.assertEqual(probs_of("HA1", "Basis ordering", "X on qubit 0"), {"001": 1.0})
        self.assertEqual(probs_of("HA1", "Basis ordering", "X on qubit 1"), {"010": 1.0})
        self.assertEqual(probs_of("HA1", "Basis ordering", "X on qubit 2"), {"100": 1.0})
        self.assertEqual(ideal_probabilities(2, [("x", 0)])["01"], 1.0)  # HF3 quick check
        self.assertEqual([c.name for c in build_circuit(2, []).cregs], ["meas"])  # HF4 quick check

    def test_bell_states_match_course_definitions(self):
        s = 1 / np.sqrt(2)
        expected = {
            "φ⁺": [s, 0, 0, s], "φ⁻": [s, 0, 0, -s],
            "ψ⁺": [0, s, s, 0], "ψ⁻": [0, s, -s, 0],  # index = int('ba'): |01> is index 1
        }
        for name, vector in expected.items():
            qubits, ops = recipe("HA2", "The four Bell states", name)
            state = Statevector.from_instruction(build_circuit(qubits, ops, measure=False))
            self.assertTrue(np.allclose(state.data, vector), name)


class TestWidgetPhysics(unittest.TestCase):
    def test_course_vectors(self):
        u, v, ww = (Statevector(x) for x in w.COURSE_VECTORS.values())
        self.assertTrue(u.is_valid())
        self.assertTrue(v.is_valid())
        self.assertFalse(ww.is_valid())
        probs = v.probabilities_dict()
        self.assertAlmostEqual(probs["0"], 5 / 9)
        self.assertAlmostEqual(probs["1"], 4 / 9)
        self.assertAlmostEqual(abs(4j / 5) ** 2, 16 / 25)  # HF2 quick check

    def test_normalize(self):
        a, b = w.normalized(1 + 0j, 1 + 1j)
        self.assertAlmostEqual(abs(a) ** 2 + abs(b) ** 2, 1.0)
        self.assertAlmostEqual(abs(a) ** 2, 1 / 3)
        self.assertIsNone(w.normalized(0j, 0j))

    def test_tensor_product_example(self):
        product = Statevector.from_label("0").tensor(Statevector.from_label("+"))
        self.assertTrue(np.allclose(product.data, [1 / np.sqrt(2), 1 / np.sqrt(2), 0, 0]))  # |00> and |01>
        self.assertTrue(product.equiv(Statevector.from_label("0+")))
        self.assertEqual(len(Statevector.from_label("0" * 5).data), 32)  # HA1 quick check

    def test_correlation_vs_entanglement(self):
        entangled, classical = w.correlation_probabilities(hadamard_first=False)
        rounded = {k: round(v, 9) for k, v in entangled.items()}
        self.assertEqual(rounded, {"00": 0.5, "01": 0, "10": 0, "11": 0.5})
        self.assertEqual(rounded, {k: round(v, 9) for k, v in classical.items()})
        entangled, classical = w.correlation_probabilities(hadamard_first=True)
        self.assertAlmostEqual(entangled["00"], 0.5)
        self.assertAlmostEqual(entangled["11"], 0.5)
        for value in classical.values():
            self.assertAlmostEqual(value, 0.25)

    def test_entangled_quick_check(self):
        def is_product(vector):  # a 2-qubit pure state is a product state iff its 2x2 coefficient matrix has rank 1
            return np.linalg.matrix_rank(np.asarray(vector).reshape(2, 2), tol=1e-9) == 1
        self.assertTrue(is_product(Statevector.from_label("0+").data))
        self.assertFalse(is_product([3 / 5, 0, 0, 4 / 5]))
        self.assertTrue(is_product(Statevector.from_label("11").data))

    def test_teleportation(self):
        rng = np.random.default_rng(3)
        for theta, phi in [(0.0, 0.0), (np.pi, 0.0), (1.1, 0.7), *rng.uniform(0, [np.pi, 2 * np.pi], (6, 2))]:
            probs, fidelity = w.teleport_results(theta, phi)
            for value in probs.values():
                self.assertAlmostEqual(value, 0.25)
            self.assertAlmostEqual(fidelity, 1.0, places=9)

    def test_superdense_coding(self):
        for c in (0, 1):
            for d in (0, 1):
                result = w.superdense_result(c, d)
                self.assertEqual(list(result), [f"{c}{d}"])
                self.assertAlmostEqual(result[f"{c}{d}"], 1.0)

    def test_deutsch_jozsa(self):
        for label in w.DJ_FUNCTIONS:
            with self.subTest(function=label):
                values = list(w.dj_truth_table(label).values())
                constant = len(set(values)) == 1
                self.assertTrue(constant or values.count(1) == len(values) // 2)
                self.assertEqual(label.startswith("Constant"), constant)
                self.assertAlmostEqual(w.dj_probability_all_zero(label), 1.0 if constant else 0.0)
        self.assertEqual(2 ** (3 - 1) + 1, 5)  # HA4 quick check

    def test_grover(self):
        self.assertAlmostEqual(w.grover_success(2, "10", 1), 1.0)  # N = 4: certainty after one iteration
        for n in (2, 3, 4, 5):
            for marked in (format(0, f"0{n}b"), format(2**n - 1, f"0{n}b"), format(5 % 2**n, f"0{n}b")):
                for t in range(2 * w.grover_recommended(n) + 3):
                    with self.subTest(n=n, marked=marked, t=t):
                        self.assertAlmostEqual(w.grover_success(n, marked, t), w.grover_theory(n, t), places=9)
        self.assertEqual(w.grover_recommended(2), 1)

    def test_density_matrices_and_noise(self):
        plus = DensityMatrix.from_label("+")
        self.assertAlmostEqual(plus.purity().real, 1.0)
        mixed = DensityMatrix(np.eye(2) / 2)
        self.assertAlmostEqual(mixed.purity().real, 0.5)  # HR1 quick check
        for rho in (plus, mixed, w.apply_noise(plus, "Dephasing", 0.3)):
            self.assertAlmostEqual(rho.purity().real, np.trace(rho.data @ rho.data).real)
        dephased = w.apply_noise(plus, "Dephasing", 1.0)
        self.assertTrue(np.allclose(dephased.data, np.eye(2) / 2))
        # The completely dephasing channel matches its Kraus form {|0><0|, |1><1|}.
        kraus = [np.diag([1, 0]), np.diag([0, 1])]
        self.assertTrue(np.allclose(sum(k.conj().T @ k for k in kraus), np.eye(2)))
        self.assertTrue(np.allclose(sum(k @ plus.data @ k.conj().T for k in kraus), dephased.data))
        for label in ("0", "1", "+", "-"):
            rho = DensityMatrix.from_label(label)
            self.assertTrue(np.allclose(w.apply_noise(rho, "Depolarizing", 1.0).data, np.eye(2) / 2))
            self.assertAlmostEqual(w.apply_noise(rho, "Dephasing", 0.7).probabilities_dict().get("0", 0),
                                   rho.probabilities_dict().get("0", 0))
        x, y, z = w.bloch_vector(plus)
        self.assertAlmostEqual(x, 1.0)
        self.assertAlmostEqual(np.linalg.norm(w.bloch_vector(w.apply_noise(plus, "Depolarizing", 0.5))), 0.5)

    def test_vqe_respects_variational_theorem_and_converges(self):
        history, final = w.run_vqe()
        exact = w.vqe_exact_ground_energy()
        self.assertGreaterEqual(min(history), exact - 1e-9)
        self.assertAlmostEqual(final, exact, delta=1e-3)

    def test_qaoa(self):
        hamiltonian, offset = w.qaoa_cost_hamiltonian()
        diagonal = np.real(np.diag(hamiltonian.to_matrix()))
        for i in range(2**w.QAOA_NODES):
            bits = format(i, f"0{w.QAOA_NODES}b")
            self.assertAlmostEqual(-(diagonal[i] + offset), w.cut_value(bits))
        self.assertEqual(max(w.cut_value(format(i, "04b")) for i in range(16)), 4)
        self.assertEqual(w.cut_value("0101"), 4)
        for gamma, beta in [(0.5, 0.5), (1.2, 0.3)]:
            probs = w.qaoa_state(gamma, beta).probabilities_dict()
            self.assertAlmostEqual(sum(p * w.cut_value(k) for k, p in probs.items()), w.qaoa_expected_cut(gamma, beta))
        gamma, beta = w.optimize_qaoa()
        self.assertTrue(0 <= gamma <= np.pi and 0 <= beta <= np.pi)
        self.assertGreaterEqual(w.qaoa_expected_cut(gamma, beta) / 4, 0.74)
        names = sorted(p.name[0] for p in qaoa_ansatz(hamiltonian, reps=1).parameters)
        self.assertEqual(names, ["β", "γ"])
        self.assertEqual(np.real(np.diag(np.kron(np.diag([1, -1]), np.diag([1, -1]))))[1], -1)  # HR3 quick check

    def test_repetition_code_matches_course_table(self):
        expected = {
            "No error": ("00", None), "Bit flip (X) on qubit 0": ("01", 0),
            "Bit flip (X) on qubit 1": ("11", 1), "Bit flip (X) on qubit 2": ("10", 2),
        }
        for theta in (0.0, 1.2, np.pi / 2, np.pi):
            for error, (syndrome, fix) in expected.items():
                with self.subTest(theta=theta, error=error):
                    got_syndrome, got_fix, fidelity = w.run_repetition_code(theta, error)
                    self.assertEqual((got_syndrome, got_fix), (syndrome, fix))
                    self.assertAlmostEqual(fidelity, 1.0, places=9)
            syndrome, fix, fidelity = w.run_repetition_code(theta, "Phase flip (Z) on qubit 1")
            self.assertEqual((syndrome, fix), ("00", None))
            self.assertAlmostEqual(fidelity, np.cos(theta) ** 2, places=9)  # |a|^2 - |b|^2, squared
        self.assertEqual(w.SYNDROME_CORRECTION["11"], 1)  # HR4 quick check

    def test_phase_flip_on_any_qubit_gives_the_same_state(self):
        states = []
        for qubit in range(3):
            qc = QuantumCircuit(3)
            qc.ry(1.2, 0)
            qc.cx(0, 1)
            qc.cx(0, 2)
            qc.z(qubit)
            states.append(Statevector(qc))
        self.assertTrue(all(s.equiv(states[0]) for s in states))

    def test_shot_helpers(self):
        qc = build_circuit(1, [("h", 0)])
        fractions = w.ones_fraction(qc, 1000, 5, seed=5)
        self.assertEqual(len(fractions), 5)
        self.assertTrue(all(0.4 < f < 0.6 for f in fractions))
        flips = w.flip_coins(100, np.random.default_rng(1))
        self.assertEqual(len(flips), 100)
        self.assertTrue(set(flips) <= {"H", "T"})
        self.assertEqual(50 / 200 * 100, 25)  # MS2 quick check


class TestRendering(unittest.TestCase):
    """Render every step of every walkthrough in Streamlit's test runner."""

    def test_every_step_renders(self):
        from streamlit.testing.v1 import AppTest

        script = (
            "import sys\n"
            f"sys.path.insert(0, {str(ROOT)!r})\n"
            "import streamlit as st\n"
            "from ui.walkthroughs import render_walkthrough\n"
            "render_walkthrough({'id': st.session_state['lesson_id']})\n"
        )
        for lesson_id, index, _ in steps():
            with self.subTest(lesson=lesson_id, step=index):
                at = AppTest.from_string(script, default_timeout=60)
                at.session_state["lesson_id"] = lesson_id
                at.session_state[f"wt_{lesson_id}_step"] = index
                at.run()
                self.assertFalse(at.exception, [e.value for e in at.exception])
                self.assertIn(f"Step {index + 1} of {len(WALKTHROUGHS[lesson_id])}", [p.proto.text for p in at.get("progress")])


if __name__ == "__main__":
    unittest.main()
