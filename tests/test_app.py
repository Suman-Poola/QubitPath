"""End-to-end checks of app.py in Streamlit's test runner.

Every page renders for every level, every lesson shows its walkthrough and
hands-on activity, and the main features (landing buttons, lesson checkpoint,
quizzes, lab, Professor Qubit, tutoring, analytics) work. These run the whole
app on every interaction, so they take a couple of minutes.

Run from the repo root:  python -m unittest discover tests
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ui.activity_content import ACTIVITIES  # noqa: E402

LEVELS = ["Elementary", "Proficient", "Erudite"]
PAGES = ["Home", "Recorded Learning", "Live Tutoring", "Quantum Lab", "Quiz & Games", "AI Professor", "Analytics", "Responsible AI"]


class AppTestCase(unittest.TestCase):
    def app(self, page: str = "Welcome", level: str | None = None):
        from streamlit.testing.v1 import AppTest

        at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=180)
        at.session_state["page"] = page
        if level:
            at.session_state["learner_level_select"] = level
        return self.run_ok(at)

    def run_ok(self, at):
        at.run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        return at

    @staticmethod
    def button(at, label: str):
        return next(b for b in at.button if b.label == label)


class TestPages(AppTestCase):
    def test_every_page_renders_for_every_level(self):
        self.app()
        for level in LEVELS:
            for page in PAGES:
                with self.subTest(level=level, page=page):
                    self.app(page, level)

    def test_landing_buttons_open_the_pathway(self):
        for level in LEVELS:
            for key in (f"pick_{level.lower()}", f"landing_begin_{level.lower()}"):
                with self.subTest(button=key):
                    at = self.app()
                    at.button(key=key).click()
                    self.run_ok(at)
                    self.assertEqual(at.session_state["page"], "Recorded Learning")
                    self.assertEqual(at.session_state["learner_level_select"], level)
                    at.button(key="nav_back_to_landing").click()
                    self.run_ok(at)
                    self.assertEqual(at.session_state["page"], "Welcome")

    def test_sidebar_settings_survive_the_landing_page(self):
        at = self.app("Home", "Proficient")
        at.sidebar.text_input(key="learner_name").set_value("Ada")
        at.sidebar.slider(key="weekly_hours").set_value(7.5)
        self.run_ok(at)
        at.button(key="nav_back_to_landing").click()
        self.run_ok(at)
        at.button(key="pick_proficient").click()
        self.run_ok(at)
        self.assertEqual(at.sidebar.text_input(key="learner_name").value, "Ada")
        self.assertEqual(at.sidebar.slider(key="weekly_hours").value, 7.5)


class TestLessons(AppTestCase):
    def test_every_lesson_shows_its_walkthrough_and_activity(self):
        tracks = {"HF": "Foundations", "HA": "Entanglement & Algorithms", "HR": "Advanced Research"}
        for level in LEVELS:
            at = self.app("Recorded Learning", level)
            select = at.selectbox(key=f"lesson_select_{level}")
            for lesson_id, activity in ACTIVITIES.items():
                option = next((o for o in select.options if o.startswith(lesson_id)), None)
                if option is None and level == "Erudite" and lesson_id[:2] in tracks:
                    at.radio(key="erudite_track_select").set_value(tracks[lesson_id[:2]])
                    self.run_ok(at)
                    select = at.selectbox(key=f"lesson_select_{level}")
                    option = next(o for o in select.options if o.startswith(lesson_id))
                if option is None:
                    continue  # another level's lesson
                with self.subTest(lesson=lesson_id):
                    select.set_value(option)
                    self.run_ok(at)
                    text = [m.value for m in at.markdown]
                    self.assertIn("#### \U0001F9ED Guided walkthrough", text)
                    self.assertIn(f"#### \U0001F6E0️ Hands-on activity: {activity['title']}", text)
                    select = at.selectbox(key=f"lesson_select_{level}")

    def test_checkpoint_tracks_walkthrough_activity_and_completion(self):
        at = self.app("Recorded Learning", "Elementary")
        self.assertTrue(any("⬜ Finish the guided walkthrough" in m.value for m in at.markdown))
        at.session_state["wt_EL1_done"] = True
        at.session_state["act_EL1_done"] = True
        self.run_ok(at)
        checklist = next(m.value for m in at.markdown if "Finish the guided walkthrough" in m.value)
        self.assertIn("✅ Finish the guided walkthrough", checklist)
        self.assertIn("✅ Complete the hands-on activity", checklist)
        xp = at.session_state["xp"]
        at.button(key="complete_EL1").click()
        self.run_ok(at)
        self.assertEqual(at.session_state["completed_lessons"], ["EL1"])
        self.assertEqual(at.session_state["xp"], xp + 40)


class TestFeatures(AppTestCase):
    def test_quizzes_need_every_answer_and_score_correctly(self):
        import ast

        # app.py runs Streamlit on import, so read the QUIZZES literal from its source instead.
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        quizzes = ast.literal_eval(source.split("QUIZZES: dict[str, Any] = ", 1)[1].split("\n\nKNOWLEDGE_BASE", 1)[0])
        for level in LEVELS:
            at = self.app("Quiz & Games", level)
            items, quiz_key = quizzes[level], level
            if level == "Erudite":
                items, quiz_key = quizzes["Erudite"]["Foundations"], "Erudite_Foundations"
            with self.subTest(level=level, answers="none"):
                self.button(at, "Submit quiz").click()
                self.run_ok(at)
                self.assertEqual(at.session_state["quiz_history"], [])
                self.assertTrue(any("Answer all 4 questions" in w.value for w in at.warning))
            with self.subTest(level=level, answers="all correct"):
                for idx, item in enumerate(items, start=1):
                    at.radio(key=f"{quiz_key}_{idx}").set_value(item["options"][item["answer"]])
                self.button(at, "Submit quiz").click()
                self.run_ok(at)
                self.assertEqual([m.value for m in at.metric if m.label == "Quiz score"], ["4/4"])
                self.assertEqual(at.session_state["quiz_history"][-1]["score_pct"], 100)
            with self.subTest(level=level, page="Analytics"):
                self.button(at, "Submit quiz").click()  # a second attempt in the same minute
                self.run_ok(at)
                at.session_state["page"] = "Analytics"
                self.run_ok(at)

    def test_quantum_lab(self):
        at = self.app("Quantum Lab", "Elementary")
        at.button(key="spin_coin_btn").click()
        self.run_ok(at)
        self.assertEqual(sum(int(m.value) for m in at.metric), 20)
        for level, experiments in [("Proficient", ["Quantum coin (H gate)", "Bell entanglement"]),
                                   ("Erudite", ["Quantum coin (H gate)", "Bell entanglement", "Three-qubit GHZ", "Custom Ry rotation"])]:
            at = self.app("Quantum Lab", level)
            for experiment in experiments:
                with self.subTest(level=level, experiment=experiment):
                    at.selectbox[0].set_value(experiment)
                    self.run_ok(at)
                    sliders = [s.label for s in at.slider]
                    self.assertEqual("Rotation angle θ" in sliders, experiment == "Custom Ry rotation")
                    self.button(at, "Run quantum experiment").click()
                    self.run_ok(at)
                    self.assertEqual(len(at.get("plotly_chart")), 1)

    def test_professor_qubit(self):
        at = self.app("AI Professor", "Elementary")
        at.chat_input[0].set_value("hi")
        self.run_ok(at)
        self.assertIn("Try asking about one of these topics", at.chat_message[-1].markdown[0].value)
        at.chat_input[0].set_value("what is entanglement?")
        self.run_ok(at)
        self.assertIn("Core idea — Entanglement", at.chat_message[-1].markdown[0].value)
        at.button(key="fb_helpful").click()
        self.run_ok(at)
        self.assertEqual(sum(at.session_state["bandit_counts"].values()), 1)

    def test_tutoring_booking(self):
        at = self.app("Live Tutoring", "Proficient")
        xp = at.session_state["xp"]
        self.button(at, "Book demo session").click()
        self.run_ok(at)
        self.assertEqual(len(at.session_state["bookings"]), 1)
        self.assertEqual(at.session_state["xp"], xp + 15)


if __name__ == "__main__":
    unittest.main()
