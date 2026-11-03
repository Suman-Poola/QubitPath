"""Checks every lesson's hands-on activity: its answers hold in Qiskit, and a learner can complete it.

Run from the repo root:  python -m unittest discover tests
"""

from __future__ import annotations

import itertools
import re
import sys
import unittest
from pathlib import Path

import numpy as np
from qiskit.quantum_info import DensityMatrix, Statevector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ui import activity_widgets as aw  # noqa: E402
from ui import walkthrough_widgets as ww  # noqa: E402
from ui.activity_content import ACTIVITIES  # noqa: E402
from ui.walkthroughs import ideal_probabilities  # noqa: E402

APP_SOURCE = (ROOT / "app.py").read_text(encoding="utf-8")
LESSON_IDS = re.findall(r'"id": "([A-Z]{2}\d)"', APP_SOURCE)


def parts(kind: str | None = None, name: str | None = None):
    for lesson_id, activity in ACTIVITIES.items():
        for index, part in enumerate(activity["parts"]):
            if (kind is None or part["kind"] == kind) and (name is None or part.get("name") == name):
                yield lesson_id, index, part


def builder_solution(part: dict, challenge: dict) -> list[str] | None:
    """Some gate choice for every slot that solves ``challenge`` (fewest gates first), or None."""
    menu = part["menu"]
    for picks in sorted(itertools.product(menu, repeat=part["slots"]), key=lambda p: sum(bool(menu[x]) for x in p)):
        if aw.challenge_problem(challenge, part["qubits"], menu, picks) is None:
            return list(picks)
    return None


class TestStructure(unittest.TestCase):
    def test_every_lesson_has_an_activity(self):
        self.assertEqual(len(LESSON_IDS), 20)
        self.assertEqual(sorted(LESSON_IDS), sorted(ACTIVITIES))
        for lesson_id, activity in ACTIVITIES.items():
            with self.subTest(lesson=lesson_id):
                self.assertTrue(activity["title"])
                self.assertGreaterEqual(len(activity["parts"]), 1)

    def test_every_lesson_describes_its_activity(self):
        self.assertEqual(len(re.findall(r'"activity": "[^"]{20,}"', APP_SOURCE)), 20)

    def test_parts_are_valid(self):
        for lesson_id, index, part in parts():
            with self.subTest(lesson=lesson_id, part=index):
                self.assertTrue(part["title"])
                if part["kind"] == "widget":
                    self.assertIn(part["name"], aw.WIDGETS)
                else:
                    self.assertIn(part["kind"], aw.KINDS)
                if part["kind"] == "sort":
                    self.assertGreaterEqual(len(part["categories"]), 2)
                    self.assertGreaterEqual(len(part["items"]), 2)
                    for item in part["items"]:
                        self.assertIn(item["answer"], range(len(part["categories"])))
                        self.assertTrue(item["text"] and item["why"])
                    # Every category except possibly one should be used, or the sort is a giveaway.
                    self.assertGreaterEqual(len({item["answer"] for item in part["items"]}), 2)
                elif part["kind"] == "order":
                    self.assertGreaterEqual(len(part["steps"]), 3)
                    self.assertEqual(len(set(part["steps"])), len(part["steps"]))
                elif part["kind"] == "check":
                    self.assertIn(part["answer"], range(len(part["options"])))
                    self.assertTrue(part["why"])

    def test_no_literal_unicode_escapes(self):
        # A "’" inside an r-string would show up as backslash-u text on the page.
        def strings(value):
            if isinstance(value, str):
                yield value
            elif isinstance(value, dict):
                for v in value.values():
                    yield from strings(v)
            elif isinstance(value, (list, tuple)):
                for v in value:
                    yield from strings(v)

        for lesson_id, index, part in parts():
            with self.subTest(lesson=lesson_id, part=index):
                for text in strings(part):
                    self.assertNotIn(chr(92) + "u", text)

    def test_shuffled_steps_are_stable_and_never_already_solved(self):
        for lesson_id, index, part in parts("order"):
            key = f"act_{lesson_id}_{index}"
            shuffled = aw.shuffled_steps(key, part["steps"])
            self.assertEqual(shuffled, aw.shuffled_steps(key, part["steps"]))
            self.assertNotEqual(shuffled, part["steps"])
            self.assertEqual(sorted(shuffled), sorted(part["steps"]))


class TestAnswers(unittest.TestCase):
    def test_switch_recipes_match_their_tricks(self):  # EL3
        sort, proof = ACTIVITIES["EL3"]["parts"]
        trick = {(("1", 1.0),): 0, (("0", 0.5), ("1", 0.5)): 1, (("0", 1.0),): 2}
        for item in sort["items"]:
            probs = tuple((o, round(p, 9)) for o, p in ideal_probabilities(1, proof["recipes"][item["text"]]).items() if p > 1e-9)
            self.assertEqual(trick[probs], item["answer"], item["text"])

    def test_magic_and_partner_coins(self):  # EL2, EL4
        heads, tails = aw.magic_coin_spins(1000, seed=3)
        self.assertEqual(heads + tails, 1000)
        self.assertTrue(400 < heads < 600)
        partner = [aw.coin_pair(aw.PARTNER, seed=s) for s in range(60)]
        self.assertTrue(all(mine == friend for mine, friend in partner))
        self.assertEqual({mine for mine, _ in partner}, {"0", "1"})
        ordinary = [aw.coin_pair("Ordinary coins (not linked)", seed=s) for s in range(60)]
        self.assertTrue(any(mine != friend for mine, friend in ordinary))

    def test_percent_rounds(self):  # MS2
        theory = [ww.ry_probability_of_one(r["theta"]) for r in aw.PERCENT_ROUNDS]
        self.assertAlmostEqual(theory[0], 0.5)
        self.assertAlmostEqual(theory[1], 0.25)
        fraction = ww.ones_fraction(aw.percent_circuit(np.pi / 3), 4000, 1, seed=2)[0]
        self.assertAlmostEqual(fraction, 0.25, delta=0.03)

    def test_builder_challenges_are_solvable_and_not_trivial(self):  # MS3, MS4, HF3, HF4
        for lesson_id, index, part in parts("widget", "circuit_builder"):
            empty = [next(iter(part["menu"]))] * part["slots"]
            for challenge in part["challenges"]:
                with self.subTest(lesson=lesson_id, challenge=challenge["label"]):
                    self.assertIsNotNone(builder_solution(part, challenge))
                    self.assertIsNotNone(aw.challenge_problem(challenge, part["qubits"], part["menu"], empty))

    def test_builder_known_solutions(self):
        def solves(lesson_id, challenge_index, picks):
            part = ACTIVITIES[lesson_id]["parts"][0]
            return aw.challenge_problem(part["challenges"][challenge_index], part["qubits"], part["menu"], picks) is None

        self.assertTrue(solves("MS3", 0, ["X", "(empty)", "(empty)"]))
        self.assertTrue(solves("MS3", 2, ["H", "H", "(empty)"]))
        self.assertFalse(solves("MS3", 2, ["(empty)", "(empty)", "(empty)"]))  # needs two gates
        self.assertTrue(solves("MS4", 0, ["H on qubit 0", "CX: control 0, target 1", "(empty)"]))
        self.assertTrue(solves("MS4", 1, ["H on qubit 0", "CX: control 0, target 1", "X on qubit 0"]))
        self.assertTrue(solves("HF3", 0, ["H", "Z", "H"]))  # HZH = X
        self.assertFalse(solves("HF3", 0, ["X", "(empty)", "(empty)"]))  # only H and Z allowed
        self.assertTrue(solves("HF3", 1, ["X", "H", "(empty)"]))  # H|1> = |->
        self.assertTrue(solves("HF3", 1, ["H", "Z", "(empty)"]))  # Z|+> = |->
        self.assertFalse(solves("HF3", 1, ["H", "(empty)", "(empty)"]))  # |+> has the same statistics, not the same state
        self.assertTrue(solves("HF3", 2, ["X", "Z", "X"]))  # -|0>: equal up to global phase
        self.assertTrue(solves("HF4", 0, ["qc.h(0)", "qc.cx(0, 1)"]))
        self.assertTrue(solves("HF4", 0, ["qc.h(1)", "qc.cx(1, 0)"]))

    def test_valid_state_answers(self):  # HF1
        sort = ACTIVITIES["HF1"]["parts"][0]
        for item in sort["items"]:
            with self.subTest(item=item["text"]):
                self.assertEqual(Statevector(item["vector"]).is_valid(), item["answer"] == 0)

    def test_born_states(self):  # HF2
        expected = [1 / 4, 1 / 2, 9 / 25, 8 / 9, 1 / 2]
        for (label, amplitudes), p1 in zip(aw.BORN_STATES.items(), expected):
            with self.subTest(state=label):
                self.assertTrue(Statevector(amplitudes).is_valid())
                self.assertAlmostEqual(aw.born_probability_of_one(amplitudes), p1)
        self.assertGreaterEqual(len(aw.BORN_STATES), ACTIVITIES["HF2"]["parts"][0]["needed"])

    def test_basis_parsing_and_product_support(self):  # HA1
        self.assertEqual(aw.basis_tokens("|000⟩, 001; 010> 011|100 101 110 111"), aw.outcomes(3))
        self.assertEqual(aw.basis_tokens("0012"), ["001"])
        self.assertEqual(aw.product_support("0+0"), ["000", "010"])  # qubit 1 in |+>
        self.assertEqual(aw.product_support("1-+"), ["100", "101", "110", "111"])
        self.assertEqual(aw.product_support("110"), ["110"])
        state = Statevector.from_label("1-+")
        self.assertAlmostEqual(state.data[int("110", 2)].real, -0.5)  # |->: the qubit-1 = 1 terms are negative

    def test_bell_statistics(self):  # HA2
        for name, ops in aw.BELL_RECIPES.items():
            support = [o for o, p in ideal_probabilities(2, ops).items() if p > 1e-9]
            with self.subTest(state=name):
                self.assertEqual(len(support), 2)
                for counts in aw.bell_runs(ops, 100, 5, seed=4):
                    self.assertEqual(sum(counts.values()), 100)
                    self.assertEqual(sum(counts[o] for o in support), 100)
        ops = aw.BELL_RECIPES["φ⁺"]
        spread = {s: np.std([r["00"] / s for r in aw.bell_runs(ops, s, 400, seed=9)]) for s in (10, 1000)}
        self.assertAlmostEqual(spread[10] / spread[1000], 10, delta=2.5)  # the HA2 check's "about 10x"

    def test_teleport_flow(self):  # HA3
        self.assertEqual(set(aw.FLOW_ANSWERS), set(aw.FLOW_ARROWS))
        self.assertTrue(set(aw.FLOW_ANSWERS.values()) <= set(aw.CHANNELS))
        dot = aw.teleport_flow_dot(aw.FLOW_ANSWERS)
        self.assertIn("quantum channel", dot)
        self.assertIn("classical channel", dot)
        self.assertIn("(?)", aw.teleport_flow_dot({"ebit": None, "bits": None}))
        steps = ACTIVITIES["HA3"]["parts"][1]["steps"]
        self.assertTrue(steps[0].startswith("Alice and Bob share an e-bit") and steps[-1].startswith("Bob applies"))
        for c in (0, 1):  # superdense coding: one qubit carries two bits
            for d in (0, 1):
                self.assertEqual(list(ww.superdense_result(c, d)), [f"{c}{d}"])

    def test_grover_trace(self):  # HA4
        for marked in aw.outcomes(2):
            with self.subTest(marked=marked):
                states = aw.grover_trace_states(marked)
                self.assertEqual(aw.grover_stage_answers(marked), [0, 1, 2])  # +1/2, -1/2, +1
                self.assertAlmostEqual(states[-1].probabilities_dict()[marked], 1.0)
                self.assertAlmostEqual(states[-1].probabilities_dict()[marked], ww.grover_success(2, marked, 1))
                self.assertAlmostEqual(float(np.mean(np.real(states[2].data))), 0.25)  # the average the diffusion reflects about

    def test_noise_challenges(self):  # HR1
        dephased_plus, dephased_zero, depolarized_one, half_dephased = (aw.noisy_state(c) for c in aw.NOISE_CHALLENGES)
        plus = DensityMatrix.from_label("+")
        self.assertTrue(np.allclose(np.diag(dephased_plus.data), np.diag(plus.data)))  # Z statistics kept
        self.assertAlmostEqual(abs(dephased_plus.data[0, 1]), 0.0)  # coherence erased
        self.assertTrue(np.allclose(dephased_zero.data, DensityMatrix.from_label("0").data))  # nothing lost
        self.assertTrue(np.allclose(depolarized_one.data, np.eye(2) / 2))
        self.assertAlmostEqual(half_dephased.purity().real, 0.625)
        self.assertEqual([c["answer"] for c in aw.NOISE_CHALLENGES], [1, 2, 1, 1])

    def test_vqe_setups_fail_as_diagnosed(self):  # HR2
        exact = ww.vqe_exact_ground_energy()
        gaps = [aw.run_vqe_setup(label)[1] - exact for label in aw.VQE_SETUPS]
        self.assertTrue(all(g > -1e-9 for g in gaps))  # variational theorem
        self.assertLess(gaps[0], 1e-3)  # A: reaches the ground energy
        self.assertGreater(gaps[1], 0.05)  # B: stopped too early
        self.assertAlmostEqual(gaps[2] + exact, -np.sqrt(1.25), places=3)  # C: best one-RY energy is -sqrt(1 + 0.5^2)
        _, b_more = ww.run_vqe(maxiter=300)
        self.assertLess(b_more - exact, 1e-3)  # B's ansatz is fine; more iterations fix it
        self.assertEqual(aw.VQE_VERDICT_ANSWERS, [0, 1, 2])

    def test_maxcut_for_every_graph(self):  # HR3
        for size in range(1, len(aw.MAXCUT_EDGES) + 1):
            for edges in itertools.combinations(aw.MAXCUT_EDGES, size):
                hamiltonian, offset = ww.qaoa_cost_hamiltonian(edges)
                diagonal = np.real(np.diag(hamiltonian.to_matrix()))
                best, strings = aw.max_cut(edges)
                for i in range(16):
                    self.assertAlmostEqual(-(diagonal[i] + offset), ww.cut_value(format(i, "04b"), edges))
                self.assertTrue(all(ww.cut_value(s, edges) == best for s in strings))
        default = tuple(e for e in aw.MAXCUT_EDGES if e in aw.MAXCUT_DEFAULT)
        self.assertEqual(aw.max_cut(default)[0], 3)
        gamma, beta = ww.optimize_qaoa(edges=default)
        probs = ww.qaoa_state(gamma, beta, default).probabilities_dict()
        expected = sum(p * ww.cut_value(k, default) for k, p in probs.items())
        self.assertAlmostEqual(expected, ww.qaoa_expected_cut(gamma, beta, default))
        self.assertGreater(expected / 3, 0.6)
        self.assertEqual(ww.qaoa_cost_hamiltonian()[1], -2.0)  # the walkthrough's ring is unchanged

    def test_repetition_code_limitations(self):  # HR4
        sort = ACTIVITIES["HR4"]["parts"][1]
        for item in sort["items"]:
            syndrome, fix, _ = ww.run_repetition_errors(1.2, item["errors"])
            logical = any(aw.logical_effect(item["errors"], fix))
            category = 0 if not logical else (2 if syndrome == "00" else 1)
            self.assertEqual(category, item["answer"], item["text"])

    def test_logical_effect_matches_fidelity(self):
        theta = 1.2  # a generic state: any logical X or Z changes it
        for first, second in itertools.product(aw.CODE_ERRORS.values(), repeat=2):
            errors = [e for e in (first, second) if e]
            with self.subTest(errors=errors):
                _, fix, fidelity = ww.run_repetition_errors(theta, errors)
                self.assertEqual(any(aw.logical_effect(errors, fix)), fidelity < 1 - 1e-9)
        self.assertEqual(aw.code_scenario([("x", 0), ("x", 0)]), None)  # two flips on one qubit cancel
        self.assertEqual(aw.code_scenario([("x", 0), ("x", 2)]), "two bit flips")
        self.assertEqual(aw.code_scenario([("z", 2)]), "a phase flip")


# ---------------------------------------------------------------------------
# Rendering and completion in Streamlit's test runner
# ---------------------------------------------------------------------------

HARNESS = (
    "import sys\n"
    f"sys.path.insert(0, {str(ROOT)!r})\n"
    "import streamlit as st\n"
    "from ui.activities import render_activity\n"
    "st.session_state.setdefault('xp', 0)\n"
    "render_activity({'id': st.session_state['lesson_id'], 'activity': 'Intro text.'})\n"
)


def complete_part(at, key: str, part: dict) -> None:  # noqa: C901 - one branch per part type
    """Drive one activity part to completion the way a learner would."""
    kind, name = part["kind"], part.get("name")
    if kind == "sort":
        for i, item in enumerate(part["items"]):
            at.radio(key=f"{key}_item{i}").set_value(item["answer"])
        at.button(key=f"{key}_check").click().run()
    elif kind == "order":
        for i, step in enumerate(part["steps"]):
            at.selectbox(key=f"{key}_pos{i}").set_value(step)
        at.button(key=f"{key}_check").click().run()
    elif kind == "check":
        at.radio(key=f"{key}_choice").set_value(part["answer"]).run()
    elif name == "room_bits":
        for i, thing in enumerate(["lamp", "door", "fan"]):
            at.text_input(key=f"{key}_{i}").set_value(thing)
        at.run()
    elif name == "coin_race":
        at.button(key=f"{key}_pretend").click().run()
        at.button(key=f"{key}_spin").click().run()
    elif name == "recipe_proof":
        at.button(key=f"{key}_run").click().run()
    elif name == "partner_game":
        for n in range(part["rounds"]):
            at.button(key=f"{key}_new").click().run()
            at.radio(key=f"{key}_guess{n}").set_value("0").run()
            at.button(key=f"{key}_reveal").click().run()
    elif name == "percent_challenge":
        for r, rnd in enumerate(aw.PERCENT_ROUNDS):
            at.button(key=f"{key}_run{r}").click().run()
            ones = at.session_state[f"{key}_ones{r}"]
            at.number_input(key=f"{key}_answer{r}").set_value(round(100 * ones / rnd["shots"], 1)).run()
    elif name == "circuit_builder":
        for c, challenge in enumerate(part["challenges"]):
            if len(part["challenges"]) > 1:
                at.radio(key=f"{key}_challenge").set_value(c)
            for s, pick in enumerate(builder_solution(part, challenge)):
                at.selectbox(key=f"{key}_slot{s}").set_value(pick)
            at.run()
            at.button(key=f"{key}_run").click().run()
    elif name == "born_rule_drill":
        labels = list(aw.BORN_STATES)
        for i in range(part["needed"]):
            at.radio(key=f"{key}_state").set_value(labels[i]).run()
            at.number_input(key=f"{key}_guess{i}").set_value(round(aw.born_probability_of_one(aw.BORN_STATES[labels[i]]), 3)).run()
    elif name == "basis_list":
        at.text_input(key=f"{key}_text").set_value(" ".join(aw.outcomes(part["qubits"]))).run()
    elif name == "product_state_predict":
        at.multiselect(key=f"{key}_predict0+0").set_value(aw.product_support("0+0"))
        at.button(key=f"{key}_check").click().run()
    elif name == "bell_statistics":
        at.button(key=f"{key}_run").click().run()
    elif name == "teleport_flow":
        for arrow, channel in aw.FLOW_ANSWERS.items():
            at.selectbox(key=f"{key}_{arrow}").set_value(channel)
        at.run()
    elif name == "grover_trace":
        for stage, answer in enumerate(aw.grover_stage_answers("00")):
            at.radio(key=f"{key}_guess_00_{stage}").set_value(answer).run()
            at.button(key=f"{key}_apply").click().run()
    elif name == "noise_detective":
        for i, challenge in enumerate(aw.NOISE_CHALLENGES):
            at.radio(key=f"{key}_case").set_value(i).run()
            at.radio(key=f"{key}_answer{i}").set_value(challenge["answer"]).run()
    elif name == "vqe_failure_lab":
        at.button(key=f"{key}_run").click().run()
        complete_part(at, f"{key}_diagnose", {"kind": "sort", "items": [{"answer": a} for a in aw.VQE_VERDICT_ANSWERS]})
    elif name == "maxcut_builder":
        signature = "".join(f"{i}{j}" for i, j in aw.MAXCUT_EDGES if (i, j) in aw.MAXCUT_DEFAULT)
        at.number_input(key=f"{key}_predict{signature}").set_value(3).run()
        at.button(key=f"{key}_run").click().run()
    elif name == "break_the_code":
        at.selectbox(key=f"{key}_err2").set_value("X on qubit 1").run()  # error 1 defaults to X on qubit 0
        at.selectbox(key=f"{key}_err1").set_value("Z on qubit 1")
        at.selectbox(key=f"{key}_err2").set_value("None").run()
    else:
        raise AssertionError(f"No test driver for part {kind}/{name}")


class TestRendering(unittest.TestCase):
    def new_app(self, lesson_id: str):
        from streamlit.testing.v1 import AppTest

        at = AppTest.from_string(HARNESS, default_timeout=120)
        at.session_state["lesson_id"] = lesson_id
        at.run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        return at

    def test_every_activity_renders(self):
        for lesson_id, activity in ACTIVITIES.items():
            with self.subTest(lesson=lesson_id):
                at = self.new_app(lesson_id)
                self.assertTrue(any(activity["title"] in m.value for m in at.markdown))
                self.assertFalse(at.session_state[f"act_{lesson_id}_done"] if f"act_{lesson_id}_done" in at.session_state else False)

    def test_every_activity_can_be_completed(self):
        for lesson_id, activity in ACTIVITIES.items():
            with self.subTest(lesson=lesson_id):
                at = self.new_app(lesson_id)
                for index, part in enumerate(activity["parts"]):
                    complete_part(at, f"act_{lesson_id}_{index}", part)
                    self.assertFalse(at.exception, [e.value for e in at.exception])
                    self.assertTrue(at.session_state[f"act_{lesson_id}_{index}_done"], f"part {index} ({part['title']})")
                self.assertTrue(at.session_state[f"act_{lesson_id}_done"])
                self.assertEqual(at.session_state["xp"], 20)
                at.run()  # the XP is awarded once
                self.assertEqual(at.session_state["xp"], 20)
                self.assertTrue(any("Activity complete" in s.value for s in at.success))

    def test_wrong_answers_do_not_complete(self):
        at = self.new_app("EL1")
        sort = ACTIVITIES["EL1"]["parts"][0]
        for i, item in enumerate(sort["items"]):
            at.radio(key=f"act_EL1_0_item{i}").set_value(1 - item["answer"])
        at.button(key="act_EL1_0_check").click().run()
        self.assertNotIn("act_EL1_0_done", at.session_state)
        self.assertTrue(any("0 of 6 right" in i.value for i in at.info))

        at = self.new_app("HR2")
        steps = ACTIVITIES["HR2"]["parts"][0]["steps"]
        for i, step in enumerate(reversed(steps)):
            at.selectbox(key=f"act_HR2_0_pos{i}").set_value(step)
        at.button(key="act_HR2_0_check").click().run()
        self.assertNotIn("act_HR2_0_done", at.session_state)

        at = self.new_app("HF3")
        at.selectbox(key="act_HF3_0_slot0").set_value("X").run()  # X alone breaks the "only H and Z" rule
        at.button(key="act_HF3_0_run").click().run()
        self.assertTrue(any("use only H and Z" in i.value for i in at.info))
        self.assertEqual(at.session_state["act_HF3_0_solved"], set())


if __name__ == "__main__":
    unittest.main()
