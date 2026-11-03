"""Step-by-step walkthrough content for every lesson in app.py's CURRICULUM.

Each lesson id maps to a list of steps. A step is a dict with:

* ``title`` and ``body`` (Markdown; ``$...$`` renders as math).
* ``sources``: keys into SOURCES. Every fact in a step comes from one of these
  official pages (IBM Quantum Learning, Qiskit documentation, IBM, or the Nobel
  Prize site). Quoted phrases are copied word for word from the source.
* ``checked``: optional note for claims that are demonstrated by the step's live
  experiment or by plain arithmetic rather than quoted from a page.
* ``analogy``: True when the step uses a picture (coins, switches) to explain an
  idea. The page labels these so learners know it's a comparison, not physics.
* ``try``: optional interactive element, rendered by ui/walkthroughs.py:
  ``{"kind": "check", ...}`` (a quick question), ``{"kind": "circuit", ...}``
  (a circuit built from ``ops`` and run on Qiskit's StatevectorSampler), or
  ``{"kind": "widget", "name": ...}`` (a custom experiment in
  ui/walkthrough_widgets.py).

tests/test_walkthroughs.py re-checks every circuit result, quiz answer and
numeric claim with Qiskit, and that every step cites an official source.
"""

from __future__ import annotations

from typing import Any

_LEARN = "https://quantum.cloud.ibm.com/learning/en/courses/"
_DOCS = "https://quantum.cloud.ibm.com/docs/en/"
_BOQI = "IBM Quantum Learning \u00b7 Basics of Quantum Information"
_FOQA = "IBM Quantum Learning \u00b7 Fundamentals of Quantum Algorithms"
_GFQI = "IBM Quantum Learning \u00b7 General Formulation of Quantum Information"
_QEC = "IBM Quantum Learning \u00b7 Foundations of Quantum Error Correction"
_VAD = "IBM Quantum Learning \u00b7 Variational Algorithm Design"

# key: (title, url). Only official pages: IBM / IBM Quantum / Qiskit docs / nobelprize.org.
SOURCES: dict[str, tuple[str, str]] = {
    "ibm-qc": ("IBM Think: What is quantum computing?", "https://www.ibm.com/think/topics/quantum-computing"),
    "nobel-2022": ("The Nobel Prize in Physics 2022: popular science background", "https://www.nobelprize.org/prizes/physics/2022/popular-information/"),
    "nobel-2022-press": ("The Nobel Prize in Physics 2022: press release", "https://www.nobelprize.org/prizes/physics/2022/press-release/"),
    "boqi-classical": (f"{_BOQI}: Classical information", _LEARN + "basics-of-quantum-information/single-systems/classical-information"),
    "boqi-quantum": (f"{_BOQI}: Quantum information", _LEARN + "basics-of-quantum-information/single-systems/quantum-information"),
    "boqi-qiskit": (f"{_BOQI}: Qiskit implementation (single systems)", _LEARN + "basics-of-quantum-information/single-systems/qiskit-implementation"),
    "boqi-multi-classical": (f"{_BOQI}: Multiple systems, classical information", _LEARN + "basics-of-quantum-information/multiple-systems/classical-information"),
    "boqi-multi-quantum": (f"{_BOQI}: Multiple systems, quantum information", _LEARN + "basics-of-quantum-information/multiple-systems/quantum-information"),
    "boqi-multi-qiskit": (f"{_BOQI}: Qiskit implementation (multiple systems)", _LEARN + "basics-of-quantum-information/multiple-systems/qiskit-implementation"),
    "boqi-circuits": (f"{_BOQI}: Circuits", _LEARN + "basics-of-quantum-information/quantum-circuits/circuits"),
    "boqi-limitations": (f"{_BOQI}: Limitations on quantum information", _LEARN + "basics-of-quantum-information/quantum-circuits/limitations-on-quantum-information"),
    "boqi-eia": (f"{_BOQI}: Entanglement in action", _LEARN + "basics-of-quantum-information/entanglement-in-action/introduction"),
    "boqi-teleport": (f"{_BOQI}: Quantum teleportation", _LEARN + "basics-of-quantum-information/entanglement-in-action/quantum-teleportation"),
    "boqi-superdense": (f"{_BOQI}: Superdense coding", _LEARN + "basics-of-quantum-information/entanglement-in-action/superdense-coding"),
    "foqa-query": (f"{_FOQA}: The query model of computation", _LEARN + "fundamentals-of-quantum-algorithms/quantum-query-algorithms/query-model-of-computation"),
    "foqa-dj": (f"{_FOQA}: Deutsch-Jozsa algorithm", _LEARN + "fundamentals-of-quantum-algorithms/quantum-query-algorithms/deutsch-jozsa-algorithm"),
    "foqa-grover-search": (f"{_FOQA}: Unstructured search", _LEARN + "fundamentals-of-quantum-algorithms/grover-algorithm/unstructured-search"),
    "foqa-grover-analysis": (f"{_FOQA}: Analysis (Grover's algorithm)", _LEARN + "fundamentals-of-quantum-algorithms/grover-algorithm/analysis"),
    "foqa-grover-iterations": (f"{_FOQA}: Choosing the number of iterations", _LEARN + "fundamentals-of-quantum-algorithms/grover-algorithm/number-of-iterations"),
    "foqa-grover-remarks": (f"{_FOQA}: Concluding remarks (Grover's algorithm)", _LEARN + "fundamentals-of-quantum-algorithms/grover-algorithm/concluding-remarks"),
    "gfqi-density": (f"{_GFQI}: Density matrix basics", _LEARN + "general-formulation-of-quantum-information/density-matrices/density-matrix-basics"),
    "gfqi-convex": (f"{_GFQI}: Convex combinations of density matrices", _LEARN + "general-formulation-of-quantum-information/density-matrices/convex-combinations"),
    "gfqi-bloch": (f"{_GFQI}: The Bloch sphere", _LEARN + "general-formulation-of-quantum-information/density-matrices/bloch-sphere"),
    "gfqi-channels": (f"{_GFQI}: Quantum channel basics", _LEARN + "general-formulation-of-quantum-information/quantum-channels/quantum-channel-basics"),
    "gfqi-kraus": (f"{_GFQI}: Representations of channels", _LEARN + "general-formulation-of-quantum-information/quantum-channels/representations-of-channels"),
    "qec-repetition": (f"{_QEC}: Repetition codes", _LEARN + "foundations-of-quantum-error-correction/correcting-quantum-errors/repetition-codes"),
    "qec-shor": (f"{_QEC}: The 9-qubit Shor code", _LEARN + "foundations-of-quantum-error-correction/correcting-quantum-errors/shor-code"),
    "qec-threshold": (f"{_QEC}: Threshold theorem", _LEARN + "foundations-of-quantum-error-correction/fault-tolerant-quantum-computing/threshold-theorem"),
    "vad-intro": (f"{_VAD}: Variational algorithms", _LEARN + "variational-algorithm-design/variational-algorithms"),
    "vad-ansatz": (f"{_VAD}: Ans\u00e4tze and variational forms", _LEARN + "variational-algorithm-design/ansaetze-and-variational-forms"),
    "vad-cost": (f"{_VAD}: Cost functions", _LEARN + "variational-algorithm-design/cost-functions"),
    "vad-optim": (f"{_VAD}: Optimization loops", _LEARN + "variational-algorithm-design/optimization-loops"),
    "qiskit-hello": ("Qiskit docs: Hello world", _DOCS + "guides/hello-world"),
    "qiskit-bits": ("Qiskit docs: Bit-ordering in the Qiskit SDK", _DOCS + "guides/bit-ordering"),
    "qiskit-processors": ("IBM Quantum docs: Processor types", _DOCS + "guides/processor-types"),
    "qiskit-qaoa": ("Qiskit tutorial: Quantum approximate optimization algorithm", _DOCS + "tutorials/quantum-approximate-optimization-algorithm"),
    "api-h": ("Qiskit API: HGate", _DOCS + "api/qiskit/qiskit.circuit.library.HGate"),
    "api-cx": ("Qiskit API: CXGate", _DOCS + "api/qiskit/qiskit.circuit.library.CXGate"),
    "api-ry": ("Qiskit API: RYGate", _DOCS + "api/qiskit/qiskit.circuit.library.RYGate"),
    "api-sampler": ("Qiskit API: StatevectorSampler", _DOCS + "api/qiskit/qiskit.primitives.StatevectorSampler"),
    "api-estimator": ("Qiskit API: StatevectorEstimator", _DOCS + "api/qiskit/qiskit.primitives.StatevectorEstimator"),
    "api-statevector": ("Qiskit API: Statevector", _DOCS + "api/qiskit/qiskit.quantum_info.Statevector"),
    "api-densitymatrix": ("Qiskit API: DensityMatrix", _DOCS + "api/qiskit/qiskit.quantum_info.DensityMatrix"),
    "api-qaoa-ansatz": ("Qiskit API: qaoa_ansatz", _DOCS + "api/qiskit/qiskit.circuit.library.qaoa_ansatz"),
    "api-real-amplitudes": ("Qiskit API: real_amplitudes", _DOCS + "api/qiskit/qiskit.circuit.library.real_amplitudes"),
}

# Reusable circuit recipes. Ops are (gate, *qubits); see ui/walkthroughs.py for the allowed gates.
_BELL = [("h", 0), ("cx", 0, 1)]
_ONE_QUBIT_PREDICT = ["Always 0", "Always 1", "About half 0, half 1"]

WALKTHROUGHS: dict[str, list[dict[str, Any]]] = {
    # =====================================================================
    # Elementary (ages 7-10)
    # =====================================================================
    "EL1": [
        {
            "title": "Computers speak in 0s and 1s",
            "body": (
                "Every game, photo and song on a computer is stored as lots of tiny pieces of information "
                "called **bits**. A bit can only ever be one of two things: **0** or **1**.\n\n"
                "IBM puts it like this: classical computers \u201crely on bits (zeros and ones) to store and process data.\u201d"
            ),
            "sources": ["ibm-qc"],
        },
        {
            "title": "A bit is like a light switch",
            "body": (
                "A light switch is a good way to picture a bit. It is either **off** or **on**, never halfway. "
                "Let's call off **0** and on **1**. Flip the switch below and watch the bit change."
            ),
            "analogy": True,
            "sources": ["ibm-qc"],
            "try": {"kind": "widget", "name": "bit_switches", "switches": 1},
        },
        {
            "title": "More switches, more patterns",
            "body": (
                "With **1** switch there are 2 patterns: 0 and 1. With **2** switches there are 4: "
                "00, 01, 10 and 11. Every extra switch **doubles** the number of patterns, so 3 switches make 8.\n\n"
                "Flip the three switches to make different patterns. Computers also read a pattern as a number "
                "(this way of writing numbers is called *binary*)."
            ),
            "analogy": True,
            "sources": ["boqi-multi-classical"],
            "checked": "The pattern counts (2, 4, 8) and binary numbers are worked out live by the switches.",
            "try": {"kind": "widget", "name": "bit_switches", "switches": 3},
        },
        {
            "title": "Find bits around you",
            "body": (
                "Now look around your room for things that are only ever **one of two ways**: a door is open or "
                "closed, a lamp is on or off. Those work like bits!"
            ),
            "sources": ["ibm-qc"],
            "try": {
                "kind": "check",
                "question": "Which one works like a bit?",
                "options": ["A light switch: only ON or OFF", "A volume knob that turns to lots of levels", "A box of 24 crayons"],
                "answer": 0,
                "why": "A bit has exactly two choices. The switch has two; the knob and the crayons have many.",
            },
        },
        {
            "title": "Next up: the qubit",
            "body": (
                "Quantum computers use **qubits** instead of bits. IBM says a qubit \u201ccan act like a bit, storing "
                "either a zero or a one, but it can also exist as a weighted combination of both simultaneously.\u201d\n\n"
                "You'll see what that means in the next lesson, *The Magic Spinning Coin*."
            ),
            "sources": ["ibm-qc"],
        },
    ],
    "EL2": [
        {
            "title": "A regular coin flip",
            "body": (
                "When you flip a regular coin, you can't know ahead of time whether it lands heads or tails. "
                "But if you flip it **many** times, about half of the flips come up heads.\n\n"
                "Try it: flip a pretend coin 10 times, then 100 times."
            ),
            "sources": [],
            "checked": "The flips are random numbers made live on this page, so you can see the result yourself.",
            "try": {"kind": "widget", "name": "coin_flips"},
        },
        {
            "title": "The magic coin: a qubit",
            "body": (
                "A qubit is like a magic coin that is **still spinning**: it isn't heads or tails yet. IBM says a "
                "qubit can be \u201ca weighted combination\u201d of 0 and 1 at the same time. Scientists call this "
                "**superposition**."
            ),
            "analogy": True,
            "sources": ["ibm-qc"],
        },
        {
            "title": "Looking means measuring",
            "body": (
                "When scientists look at a qubit, they call it **measuring**. A measurement always gives just "
                "**one** answer: 0 or 1. IBM explains that when a quantum system is measured, it ends up as "
                "\u201ceither a zero or a one.\u201d"
            ),
            "sources": ["ibm-qc"],
        },
        {
            "title": "Spin the magic coin",
            "body": (
                "Here a gate called **H** sets a real (simulated) qubit spinning, and then we measure it. "
                "Each time you get 0 or 1, and each one has an equal chance. Run it 10 times, then 100 times."
            ),
            "sources": ["api-h", "boqi-quantum"],
            "checked": "Results come from Qiskit's simulator each time you press Run.",
            "try": {
                "kind": "circuit", "qubits": 1, "recipes": {"Magic coin": [("h", 0)]},
                "shots": [10, 100], "kid": True,
            },
        },
        {
            "title": "Quick check",
            "body": "Let's see what you've learned about the magic coin.",
            "sources": ["boqi-quantum"],
            "try": {
                "kind": "check",
                "question": "You spin the magic coin and measure it 100 times. About how many times will you get 0?",
                "options": ["About 0 times", "About 50 times", "Exactly 100 times"],
                "answer": 1,
                "why": "0 and 1 each have an equal chance, so you get about 50 zeros. The exact number changes a little every time, just like real coin flips.",
            },
        },
    ],
    "EL3": [
        {
            "title": "Recipes for qubits",
            "body": (
                "A quantum program is like a recipe. Each step is called a **gate**, and gates change qubits. "
                "In a circuit picture, each line is a qubit and you read the steps **from left to right**."
            ),
            "sources": ["boqi-circuits"],
        },
        {
            "title": "The Flip switch (X gate)",
            "body": (
                "The **Flip switch** swaps 0 and 1. Its real name is the **X gate** (scientists also call it a "
                "*bit flip* or *NOT*). Start at 0, flip once, and you get 1 every single time. Try it!"
            ),
            "sources": ["boqi-quantum"],
            "try": {"kind": "circuit", "qubits": 1, "recipes": {"Flip": [("x", 0)]}, "shots": [10, 100], "kid": True},
        },
        {
            "title": "The Maybe switch (H gate)",
            "body": (
                "The **Maybe switch** turns a plain 0 into a spinning magic coin: half the time you get 0, half "
                "the time 1. Its real name is the **Hadamard gate**, or **H**."
            ),
            "sources": ["api-h", "boqi-quantum"],
            "try": {"kind": "circuit", "qubits": 1, "recipes": {"Maybe": [("h", 0)]}, "shots": [10, 100], "kid": True},
        },
        {
            "title": "Two-switch recipes",
            "body": (
                "Now put two switches in a row. Pick a recipe, guess what will happen, then run it.\n\n"
                "Here's a surprise: **two Maybe switches in a row give 0 every time.** The second one undoes the "
                "first! A regular spinning coin can't do that, which is one way qubits are different."
            ),
            "sources": ["boqi-limitations"],
            "checked": "Every recipe is run on Qiskit's simulator; the Maybe \u2192 Maybe result is 0 every time.",
            "try": {
                "kind": "circuit", "qubits": 1, "kid": True, "shots": [10, 100], "predict": _ONE_QUBIT_PREDICT,
                "recipes": {
                    "Flip \u2192 Flip": [("x", 0), ("x", 0)],
                    "Flip \u2192 Maybe": [("x", 0), ("h", 0)],
                    "Maybe \u2192 Maybe": [("h", 0), ("h", 0)],
                },
            },
        },
        {
            "title": "Quick check",
            "body": "Read the recipe in order, left to right.",
            "sources": ["boqi-quantum"],
            "try": {
                "kind": "check",
                "question": "Recipe: Flip, then Flip again. You start at 0. What do you get?",
                "options": ["0 every time", "1 every time", "Half 0, half 1"],
                "answer": 0,
                "why": "The first Flip turns 0 into 1, and the second Flip turns 1 back into 0.",
            },
        },
    ],
    "EL4": [
        {
            "title": "Partner coins",
            "body": (
                "Scientists can link two qubits so that their answers are connected. This is called "
                "**entanglement**. IBM says: \u201cEntanglement is the ability of qubits to correlate their state "
                "with other qubits.\u201d"
            ),
            "analogy": True,
            "sources": ["ibm-qc"],
        },
        {
            "title": "Make partner coins",
            "body": (
                "Recipe: a Maybe switch (H) on the first coin, then a special two-coin gate called **CNOT**. "
                "Run it and look at both coins: you'll see **00** or **11**, but never 01 or 10."
            ),
            "sources": ["boqi-multi-quantum", "qiskit-hello"],
            "try": {"kind": "circuit", "qubits": 2, "recipes": {"Partner coins": _BELL}, "shots": [10, 100], "kid": True},
        },
        {
            "title": "Nobody picks the answer",
            "body": (
                "Run the partner coins again a few times. Sometimes both are 0 and sometimes both are 1. "
                "Nobody can choose which one comes out. It's random, but the two coins **always match**."
            ),
            "sources": ["ibm-qc"],
            "checked": "You can see this in the results of the previous step: only 00 and 11 appear.",
        },
        {
            "title": "Far apart, still linked",
            "body": (
                "Entangled particles stay linked \u201cregardless of how far apart they are.\u201d That seemed so strange "
                "that Albert Einstein talked about \u201cspooky action at a distance.\u201d\n\n"
                "In 2022, three scientists (Alain Aspect, John Clauser and Anton Zeilinger) won the Nobel Prize in "
                "Physics for experiments with entangled particles of light, called **photons**."
            ),
            "sources": ["nobel-2022", "nobel-2022-press"],
        },
        {
            "title": "Quick check",
            "body": "Think about the partner-coin recipe you ran.",
            "sources": ["boqi-multi-quantum"],
            "try": {
                "kind": "check",
                "question": "You make partner coins with this recipe. The first coin shows 1. What does the second coin show?",
                "options": ["0", "1", "It could be either"],
                "answer": 1,
                "why": "This recipe only ever gives 00 or 11, so if one coin is 1, the other is 1 too.",
            },
        },
    ],
    # =====================================================================
    # Proficient (ages 11-13)
    # =====================================================================
    "MS1": [
        {
            "title": "Classical bits",
            "body": (
                "A classical bit is always in one of two states, **0** or **1**. Even when we don't know which, it "
                "really is one of them. We can describe our uncertainty with probabilities, such as "
                "0 with probability 3/4 and 1 with probability 1/4."
            ),
            "sources": ["boqi-classical"],
        },
        {
            "title": "Ket notation: |0\u27e9 and |1\u27e9",
            "body": (
                "Quantum scientists write states inside a **ket**, the |\u00a0\u27e9 symbol. |0\u27e9 and |1\u27e9 are the "
                "two basic states of a qubit. You can put any name inside a ket: |+\u27e9 is called the "
                "**plus state** and |\u2212\u27e9 the **minus state**."
            ),
            "sources": ["boqi-quantum"],
        },
        {
            "title": "Superposition",
            "body": (
                "A qubit's state can be a combination of |0\u27e9 and |1\u27e9, for example\n\n"
                "|+\u27e9 = (1/\u221a2)|0\u27e9 + (1/\u221a2)|1\u27e9.\n\n"
                "IBM's course notes that for quantum states, \u201csuperposition and linear combination are "
                "essentially synonymous.\u201d Prepare |0\u27e9, |1\u27e9 or |+\u27e9 below and measure each one."
            ),
            "sources": ["boqi-quantum"],
            "try": {
                "kind": "circuit", "qubits": 1, "shots": [10, 100, 1000],
                "recipes": {"|0\u27e9 (no gate)": [], "|1\u27e9 (X gate)": [("x", 0)], "|+\u27e9 (H gate)": [("h", 0)]},
            },
        },
        {
            "title": "Measuring gives a plain bit",
            "body": (
                "When you measure a qubit, you never see the whole state. IBM's course says the observer "
                "\u201cwon't see a quantum state vector, but rather will see some classical state\u201d: just 0 or 1."
            ),
            "sources": ["boqi-quantum"],
        },
        {
            "title": "Qubits are real today",
            "body": (
                "Real quantum processors already exist. IBM groups its processors into **families**; for example, "
                "the **Heron** family. Qiskit's *Hello world* guide shows how to build a circuit and run it on an "
                "IBM quantum computer."
            ),
            "sources": ["qiskit-processors", "qiskit-hello"],
        },
        {
            "title": "Quick check",
            "body": "Pick the true statement.",
            "sources": ["boqi-quantum"],
            "try": {
                "kind": "check",
                "question": "Which statement is true?",
                "options": [
                    "Measuring a qubit always gives a result of 0 or 1",
                    "You can see a qubit's whole state just by measuring it once",
                    "A classical bit can be 0 and 1 at the same time",
                ],
                "answer": 0,
                "why": "A measurement shows a classical state (0 or 1), not the quantum state itself.",
            },
        },
    ],
    "MS2": [
        {
            "title": "From amplitudes to chances",
            "body": (
                "Each part of a superposition has a number in front of it, called an **amplitude**. To get the "
                "chance of a result, take the amplitude's size and **square it**.\n\n"
                "For |+\u27e9 = (1/\u221a2)|0\u27e9 + (1/\u221a2)|1\u27e9: (1/\u221a2)\u00b2 = 1/2, so there's a **50%** chance of 0 and "
                "a **50%** chance of 1."
            ),
            "sources": ["boqi-quantum"],
        },
        {
            "title": "Counts \u2192 percent",
            "body": (
                "We run a circuit many times; each run is called a **shot**. To turn counts into a percentage:\n\n"
                "**percent of 1s = (number of 1s \u00f7 shots) \u00d7 100**\n\n"
                "Run the H-gate circuit and check the percentage the page shows against your own math."
            ),
            "sources": ["api-sampler"],
            "try": {"kind": "circuit", "qubits": 1, "recipes": {"H gate": [("h", 0)]}, "shots": [10, 100, 1000]},
        },
        {
            "title": "More shots, steadier percents",
            "body": (
                "With only 10 shots the percentage jumps around (you might see 30% or 70%). With 1000 shots it "
                "usually lands close to 50%. Compare five small runs with five big runs."
            ),
            "sources": ["api-sampler"],
            "checked": "Both sets of runs are sampled live on Qiskit's simulator.",
            "try": {"kind": "widget", "name": "shot_spread"},
        },
        {
            "title": "Not every superposition is 50/50",
            "body": (
                "The **RY** gate turns a qubit by an angle \u03b8. Qiskit's documentation gives its matrix; starting "
                "from |0\u27e9 it makes cos(\u03b8/2)|0\u27e9 + sin(\u03b8/2)|1\u27e9, so the chance of measuring 1 is "
                "**sin\u00b2(\u03b8/2)**. Move the slider and test the prediction."
            ),
            "sources": ["api-ry", "boqi-quantum"],
            "try": {"kind": "widget", "name": "ry_slider"},
        },
        {
            "title": "Quick check",
            "body": "Use the counts-to-percent rule.",
            "sources": ["api-sampler"],
            "try": {
                "kind": "check",
                "question": "You ran 200 shots and got 1 fifty times. What percent of the shots were 1?",
                "options": ["25%", "50%", "40%"],
                "answer": 0,
                "why": "50 \u00f7 200 = 0.25, and 0.25 \u00d7 100 = 25%.",
            },
        },
    ],
    "MS3": [
        {
            "title": "Reading a circuit diagram",
            "body": (
                "In a circuit diagram each horizontal line (a **wire**) is a qubit, and boxes on the wires are "
                "**gates**. The flow goes **from left to right**, so the leftmost gate happens first. In Qiskit's "
                "drawings, qubit 0 is the top wire. The meter symbol at the end is a **measurement**."
            ),
            "sources": ["boqi-circuits", "qiskit-bits"],
            "try": {"kind": "circuit", "qubits": 1, "recipes": {"H then measure": [("h", 0)]}, "shots": [100], "diagram_only": True},
        },
        {
            "title": "Gate 1: X flips",
            "body": (
                "The **X gate** swaps the two basic states: X|0\u27e9 = |1\u27e9 and X|1\u27e9 = |0\u27e9. That's why it's also "
                "called a *bit flip* or a *NOT* operation."
            ),
            "sources": ["boqi-quantum"],
        },
        {
            "title": "Gate 2: H makes an equal superposition",
            "body": (
                "The **H gate** (Hadamard) changes |0\u27e9 into |+\u27e9 and |1\u27e9 into |\u2212\u27e9. Both of those are equal "
                "mixes: measuring gives 0 or 1 with a 50% chance each."
            ),
            "sources": ["api-h", "boqi-quantum"],
        },
        {
            "title": "Predict, then run",
            "body": "Choose a one-gate circuit, write down your prediction, then run it to see if you were right.",
            "sources": ["boqi-quantum"],
            "try": {
                "kind": "circuit", "qubits": 1, "shots": [10, 100, 1000], "predict": _ONE_QUBIT_PREDICT,
                "recipes": {"No gate": [], "X gate": [("x", 0)], "H gate": [("h", 0)]},
            },
        },
        {
            "title": "The same circuit in Qiskit code",
            "body": (
                "Here is the Qiskit code for the H-gate circuit. It builds a `QuantumCircuit`, adds the gate and a "
                "measurement, and samples it with Qiskit's `StatevectorSampler`. Pressing Run below runs exactly "
                "this program."
            ),
            "sources": ["qiskit-hello", "api-sampler"],
            "try": {"kind": "circuit", "qubits": 1, "recipes": {"H gate": [("h", 0)]}, "shots": [100, 1000], "show_code": True},
        },
        {
            "title": "Quick check",
            "body": "One more about reading diagrams.",
            "sources": ["boqi-circuits"],
            "try": {
                "kind": "check",
                "question": "In a circuit diagram, in which order do the gates happen?",
                "options": ["Left to right", "Right to left", "All at the same time"],
                "answer": 0,
                "why": "In circuit diagrams the flow of information goes from left to right.",
            },
        },
    ],
    "MS4": [
        {
            "title": "A two-qubit gate: CNOT",
            "body": (
                "The **controlled-NOT** (CX) gate uses one qubit as the **control** and one as the **target**. If the "
                "control is 1, it flips the target; if the control is 0, nothing happens. Compare the two recipes "
                "(qubit 0 is the control and is the right-hand digit of each result)."
            ),
            "sources": ["api-cx", "qiskit-bits"],
            "try": {
                "kind": "circuit", "qubits": 2, "shots": [100],
                "recipes": {"Control 0: CX only": [("cx", 0, 1)], "Control 1: X, then CX": [("x", 0), ("cx", 0, 1)]},
            },
        },
        {
            "title": "Make a Bell pair",
            "body": (
                "Put an H gate on qubit 0, then a CX from qubit 0 to qubit 1. This makes the Bell state "
                "|\u03a6\u207a\u27e9 = (1/\u221a2)|00\u27e9 + (1/\u221a2)|11\u27e9, the same circuit Qiskit's *Hello world* guide builds. "
                "Run it: only **00** and **11** appear."
            ),
            "sources": ["boqi-multi-quantum", "qiskit-hello"],
            "try": {"kind": "circuit", "qubits": 2, "recipes": {"Bell pair": _BELL}, "shots": [10, 100, 1000]},
        },
        {
            "title": "Each qubit alone looks random",
            "body": (
                "Look at just one qubit in your results: it's 0 about half the time and 1 about half the time. "
                "But the two qubits **always agree**. The pair is **entangled**: it is not just two separate qubits "
                "each doing their own thing."
            ),
            "sources": ["boqi-multi-quantum"],
            "checked": "The 50/50 split for each qubit can be read off the results above.",
        },
        {
            "title": "Why Einstein called it spooky",
            "body": (
                "IBM explains that when one entangled qubit is measured, the computer \u201ccan immediately determine "
                "information about other qubits.\u201d Albert Einstein talked about \u201cspooky action at a distance,\u201d "
                "and in 1935 he, Boris Podolsky and Nathan Rosen argued that quantum mechanics seemed incomplete "
                "(the *EPR paradox*).\n\n"
                "Experiments with entangled photons, \u201cestablishing the violation of Bell inequalities,\u201d won the "
                "2022 Nobel Prize in Physics."
            ),
            "sources": ["ibm-qc", "nobel-2022", "nobel-2022-press"],
        },
        {
            "title": "Entanglement at work",
            "body": (
                "Scientists treat entanglement as a **resource**. One shared Bell pair is called an **e-bit**. With "
                "one e-bit plus two ordinary bits of communication, *quantum teleportation* sends a qubit's state "
                "from one person to another. You'll meet it in the Erudite pathway."
            ),
            "sources": ["boqi-eia", "boqi-teleport"],
        },
        {
            "title": "Quick check",
            "body": "Think about the Bell pair results.",
            "sources": ["boqi-multi-quantum"],
            "try": {
                "kind": "check",
                "question": "You measure a Bell pair made with H then CX. Which results can appear?",
                "options": ["00 and 11 only", "01 and 10 only", "All four, equally often"],
                "answer": 0,
                "why": "|\u03a6\u207a\u27e9 only has the parts |00\u27e9 and |11\u27e9, so those are the only possible results.",
            },
        },
    ],
    # =====================================================================
    # Erudite (ages 14-18)
    # =====================================================================
    "HF1": [
        {
            "title": "Classical and probabilistic states",
            "body": (
                "A bit has two classical states, 0 and 1. When we're uncertain, a **probabilistic state** is a "
                "column vector of probabilities: nonnegative real numbers that sum to 1, such as "
                r"$\begin{pmatrix} 3/4 \\ 1/4 \end{pmatrix}$" " for 0 with probability 3/4 and 1 with probability 1/4."
            ),
            "sources": ["boqi-classical"],
        },
        {
            "title": "Quantum state vectors",
            "body": (
                "A qubit's quantum state is a column vector of **complex** numbers whose absolute values squared "
                "sum to 1; in other words, a unit vector in the Euclidean norm. Entries may be negative or "
                r"complex. The standard basis is $|0\rangle = \begin{pmatrix}1\\0\end{pmatrix}$, "
                r"$|1\rangle = \begin{pmatrix}0\\1\end{pmatrix}$."
                "\n\nIBM's course stresses the quantum mindset: any speedup from a quantum computer \u201cis ultimately "
                "derived from these simple mathematical changes.\u201d"
            ),
            "sources": ["boqi-quantum"],
        },
        {
            "title": "Ket notation, checked in Qiskit",
            "body": (
                r"Kets name vectors: $|\psi\rangle$ is any state, and the plus and minus states are "
                r"$|\pm\rangle = \tfrac{1}{\sqrt 2}|0\rangle \pm \tfrac{1}{\sqrt 2}|1\rangle$. "
                "The course's Qiskit lesson builds three vectors and tests them with `Statevector.is_valid()`. "
                "Pick one to check it."
            ),
            "sources": ["boqi-quantum", "boqi-qiskit"],
            "try": {"kind": "widget", "name": "statevector_check"},
        },
        {
            "title": "Standard basis measurement",
            "body": (
                r"Measuring $|\psi\rangle$ in the standard basis gives outcome $k$ with probability "
                r"$|\langle k|\psi\rangle|^2$. You see a classical state, never the vector itself. For "
                r"$\tfrac{1+2i}{3}|0\rangle - \tfrac{2}{3}|1\rangle$ the course computes "
                r"$\Pr(0) = 5/9$ and $\Pr(1) = 4/9$."
            ),
            "sources": ["boqi-quantum"],
        },
        {
            "title": "Realistic use cases",
            "body": (
                "IBM notes that a computer that uses quantum mechanical principles \u201chas certain advantages in "
                "modeling physical systems,\u201d so quantum computing is \u201cof particular interest for chemistry and "
                "material science applications.\u201d\n\n"
                "A realistic mindset also means knowing the limits: IBM's algorithms course says Grover's search "
                "algorithm \u201cmay not lead to a practical quantum advantage for searching any time soon,\u201d even "
                "though it is a fundamentally important idea."
            ),
            "sources": ["ibm-qc", "foqa-grover-remarks"],
        },
        {
            "title": "Quick check",
            "body": "Apply the unit-norm rule.",
            "sources": ["boqi-qiskit"],
            "try": {
                "kind": "check",
                "question": "Which vector is a valid qubit state?",
                "options": [r"$(1/3,\ 2/3)$", r"$\left(\tfrac{1+2i}{3},\ -\tfrac{2}{3}\right)$", r"$(1,\ 1)$"],
                "answer": 1,
                "why": r"$|1+2i|^2/9 + 4/9 = 5/9 + 4/9 = 1$. The others have squared norms $5/9$ and $2$.",
            },
        },
    ],
    "HF2": [
        {
            "title": "Superposition is linear combination",
            "body": (
                r"A general qubit state is $\alpha|0\rangle + \beta|1\rangle$ with complex amplitudes $\alpha, \beta$. "
                "In the course's words, \u201csuperposition and linear combination are essentially synonymous.\u201d"
            ),
            "sources": ["boqi-quantum"],
        },
        {
            "title": "The Born rule and normalization",
            "body": (
                r"Outcome probabilities are $|\alpha|^2$ and $|\beta|^2$. They sum to 1 exactly because a quantum "
                "state vector has Euclidean norm 1. Enter any amplitudes below: the page normalizes them and "
                "applies the rule."
            ),
            "sources": ["boqi-quantum"],
            "try": {"kind": "widget", "name": "normalize"},
        },
        {
            "title": "Same statistics, different states",
            "body": (
                r"$|+\rangle$ and $|-\rangle$ both give 0 and 1 with probability 1/2, so " "\u201cas far as standard basis "
                "measurements are concerned, the plus and minus states are no different.\u201d But apply H before "
                r"measuring and $|+\rangle$ always gives 0 while $|-\rangle$ always gives 1, so they can be "
                r"discriminated perfectly. (Here $|-\rangle$ is made as $H X|0\rangle$.)"
            ),
            "sources": ["boqi-quantum", "boqi-limitations"],
            "try": {
                "kind": "circuit", "qubits": 1, "shots": [100, 1000],
                "recipes": {
                    "|+\u27e9, measure": [("h", 0)],
                    "|\u2212\u27e9, measure": [("x", 0), ("h", 0)],
                    "|+\u27e9, H, measure": [("h", 0), ("h", 0)],
                    "|\u2212\u27e9, H, measure": [("x", 0), ("h", 0), ("h", 0)],
                },
            },
        },
        {
            "title": "Interpreting repeated measurements",
            "body": (
                "Each shot prepares and measures the state again. Counts fluctuate from run to run, and the "
                "observed frequencies get closer to the Born-rule probabilities as the number of shots grows."
            ),
            "sources": ["api-sampler"],
            "checked": "Compare the spread of five 10-shot runs with five 1000-shot runs, sampled live.",
            "try": {"kind": "widget", "name": "shot_spread"},
        },
        {
            "title": "Quick check",
            "body": "Use the Born rule.",
            "sources": ["boqi-quantum"],
            "try": {
                "kind": "check",
                "question": r"$|\psi\rangle = \tfrac{3}{5}|0\rangle + \tfrac{4i}{5}|1\rangle$. What is $\Pr(1)$?",
                "options": [r"$4/5$", r"$16/25$", r"$-16/25$"],
                "answer": 1,
                "why": r"$|4i/5|^2 = 16/25$. Probabilities are absolute values squared, never negative.",
            },
        },
    ],
    "HF3": [
        {
            "title": "Gates are unitary matrices",
            "body": (
                r"Operations on quantum state vectors are **unitary** matrices: $UU^\dagger = U^\dagger U = \mathbb{I}$. "
                r"So every gate can be undone: applying $U^\dagger$ after $U$ gives back the original state."
            ),
            "sources": ["boqi-quantum"],
        },
        {
            "title": "X, Z and H",
            "body": (
                r"$X = \begin{pmatrix}0&1\\1&0\end{pmatrix}$ is a *bit flip* or NOT. "
                r"$Z = \begin{pmatrix}1&0\\0&-1\end{pmatrix}$ is a *phase flip*: $Z|0\rangle = |0\rangle$, "
                r"$Z|1\rangle = -|1\rangle$. "
                r"$H = \tfrac{1}{\sqrt2}\begin{pmatrix}1&1\\1&-1\end{pmatrix}$ is the Hadamard operation."
            ),
            "sources": ["boqi-quantum", "api-h"],
        },
        {
            "title": "Rotation gates",
            "body": (
                r"Qiskit defines $RY(\theta) = \exp(-i\tfrac{\theta}{2}Y) = "
                r"\begin{pmatrix}\cos\frac{\theta}{2} & -\sin\frac{\theta}{2}\\ \sin\frac{\theta}{2} & \cos\frac{\theta}{2}\end{pmatrix}$, "
                r"so $RY(\theta)|0\rangle$ is measured as 1 with probability $\sin^2(\theta/2)$. Test it."
            ),
            "sources": ["api-ry", "boqi-quantum"],
            "try": {"kind": "widget", "name": "ry_slider"},
        },
        {
            "title": "Z is invisible, until you sandwich it",
            "body": (
                r"Z only changes the sign of the $|1\rangle$ amplitude, so on its own it never changes "
                r"standard-basis statistics. Between two Hadamards, though, $HZH = X$: the circuit H, Z, H "
                "always outputs 1, while H, H outputs 0."
            ),
            "sources": ["boqi-quantum"],
            "checked": r"$HZH = X$ is checked as a matrix identity in the test suite and by the runs below.",
            "try": {
                "kind": "circuit", "qubits": 1, "shots": [100], "predict": _ONE_QUBIT_PREDICT,
                "recipes": {"H, Z, H": [("h", 0), ("z", 0), ("h", 0)], "H, H": [("h", 0), ("h", 0)], "Z only": [("z", 0)]},
            },
        },
        {
            "title": "Qiskit's ordering conventions",
            "body": (
                "Read circuits left to right. In Qiskit diagrams \u201cqubit 0 is the topmost qubit,\u201d and in result "
                "strings \u201cbit 0 is the rightmost bit.\u201d So `qc.x(1)` on two qubits gives the result `10`, as in "
                "Qiskit's bit-ordering guide."
            ),
            "sources": ["qiskit-bits", "boqi-circuits"],
            "try": {"kind": "circuit", "qubits": 2, "shots": [100], "show_code": True, "recipes": {"x on qubit 1": [("x", 1)]}},
        },
        {
            "title": "Quick check",
            "body": "Apply the ordering rule.",
            "sources": ["qiskit-bits"],
            "try": {
                "kind": "check",
                "question": "A 2-qubit circuit has only `qc.x(0)`, then measurement. What result string appears?",
                "options": ["01", "10", "00"],
                "answer": 0,
                "why": "Qubit 0 is the rightmost bit of the result string, so flipping it gives 01.",
            },
        },
    ],
    "HF4": [
        {
            "title": "Build the circuit",
            "body": (
                "Qiskit's *Hello world* guide starts with a two-qubit circuit: a Hadamard on qubit 0, then a "
                "controlled-X with qubit 0 as control and qubit 1 as target.\n\n"
                "```python\nfrom qiskit import QuantumCircuit\n\nqc = QuantumCircuit(2)\nqc.h(0)\nqc.cx(0, 1)\n```"
            ),
            "sources": ["qiskit-hello"],
            "try": {"kind": "circuit", "qubits": 2, "recipes": {"Bell circuit": _BELL}, "shots": [100], "diagram_only": True, "measure": False},
        },
        {
            "title": "Inspect the statevector",
            "body": (
                "`Statevector.from_instruction(qc)` starts every qubit in $|0\\rangle$ and applies the circuit. "
                r"For this circuit the result is $\tfrac{1}{\sqrt2}|00\rangle + \tfrac{1}{\sqrt2}|11\rangle$."
            ),
            "sources": ["api-statevector", "boqi-multi-quantum"],
            "try": {"kind": "widget", "name": "statevector_view"},
        },
        {
            "title": "Sample counts with a primitive",
            "body": (
                "To get measurement counts, add `qc.measure_all()` and run the circuit with a **Sampler** primitive. "
                "`StatevectorSampler` is Qiskit's built-in, full state-vector simulation of the Sampler. The code "
                "below is what this page runs when you press Run."
            ),
            "sources": ["api-sampler", "qiskit-bits"],
            "try": {"kind": "circuit", "qubits": 2, "recipes": {"Bell circuit": _BELL}, "shots": [100, 1000], "show_code": True},
        },
        {
            "title": "Why 01 and 10 never appear",
            "body": (
                r"The ideal state has zero amplitude on $|01\rangle$ and $|10\rangle$, so the ideal simulator never "
                "returns them. Real hardware is different: IBM explains that quantum processors are kept "
                "extremely cold \u201cto minimize noise and avoid decoherence,\u201d and noise can make results "
                "imperfect."
            ),
            "sources": ["boqi-multi-quantum", "ibm-qc"],
        },
        {
            "title": "Quick check",
            "body": "Name the Qiskit call.",
            "sources": ["qiskit-bits"],
            "try": {
                "kind": "check",
                "question": "Which line adds a measurement to every qubit of `qc`?",
                "options": ["`qc.measure_all()`", "`qc.h(0)`", "`Statevector.from_instruction(qc)`"],
                "answer": 0,
                "why": "`measure_all()` measures every qubit into a classical register named `meas`, which is why the counts are read from `data.meas`.",
            },
        },
    ],
    "HA1": [
        {
            "title": "Classical states multiply",
            "body": (
                "Two bits have the classical states 00, 01, 10, 11, the Cartesian product of {0, 1} with itself. "
                "Each extra bit doubles the count, so n bits have $2^n$ classical states, and an n-qubit state "
                "vector has $2^n$ entries. Slide to see the basis grow."
            ),
            "sources": ["boqi-multi-classical", "boqi-multi-quantum"],
            "try": {"kind": "widget", "name": "basis_states"},
        },
        {
            "title": "Tensor products",
            "body": (
                r"Independent states combine by the tensor product: $|\phi\rangle \otimes |\psi\rangle$. For example "
                r"$|0\rangle \otimes |+\rangle = \tfrac{1}{\sqrt2}|00\rangle + \tfrac{1}{\sqrt2}|01\rangle$. "
                "States that can be written this way are **product states**. In Qiskit, `a.tensor(b)` puts `b` on "
                "the right."
            ),
            "sources": ["boqi-multi-quantum", "boqi-multi-qiskit"],
            "try": {"kind": "widget", "name": "tensor_product"},
        },
        {
            "title": "Basis ordering",
            "body": (
                r"The course writes an n-qubit system as $(\mathsf{X}_{n-1}, \ldots, \mathsf{X}_0)$, the same "
                "convention Qiskit uses: qubit 0 is the rightmost symbol in a ket or result string. Flip one qubit "
                "of three and read off the string."
            ),
            "sources": ["boqi-multi-quantum", "qiskit-bits"],
            "try": {
                "kind": "circuit", "qubits": 3, "shots": [100],
                "recipes": {"X on qubit 0": [("x", 0)], "X on qubit 1": [("x", 1)], "X on qubit 2": [("x", 2)]},
            },
        },
        {
            "title": "Quick check",
            "body": "Scale it up.",
            "sources": ["boqi-multi-quantum"],
            "try": {
                "kind": "check",
                "question": "How many entries does the state vector of 5 qubits have?",
                "options": ["10", "25", "32"],
                "answer": 2,
                "why": r"$2^5 = 32$.",
            },
        },
    ],
    "HA2": [
        {
            "title": "Product versus entangled",
            "body": (
                "A state is **entangled** if it is not a product state. The course shows that "
                r"$\tfrac{1}{\sqrt2}|00\rangle + \tfrac{1}{\sqrt2}|11\rangle$ is not a product state: a product "
                r"$|\phi\rangle\otimes|\psi\rangle$ with nonzero $|00\rangle$ and $|11\rangle$ amplitudes would also "
                r"need nonzero $|01\rangle$ and $|10\rangle$ amplitudes, but those are zero here."
            ),
            "sources": ["boqi-multi-quantum"],
        },
        {
            "title": "The four Bell states",
            "body": (
                r"$|\phi^\pm\rangle = \tfrac{1}{\sqrt2}|00\rangle \pm \tfrac{1}{\sqrt2}|11\rangle$ and "
                r"$|\psi^\pm\rangle = \tfrac{1}{\sqrt2}|01\rangle \pm \tfrac{1}{\sqrt2}|10\rangle$. Starting from "
                r"$|\phi^+\rangle$, a Z on qubit 0 gives $|\phi^-\rangle$, an X gives $|\psi^+\rangle$, and Z then X "
                r"gives $|\psi^-\rangle$. Run each and compare the statistics across shot counts."
            ),
            "sources": ["boqi-multi-quantum", "boqi-superdense"],
            "try": {
                "kind": "circuit", "qubits": 2, "shots": [10, 100, 1000],
                "recipes": {
                    "\u03c6\u207a": _BELL,
                    "\u03c6\u207b": _BELL + [("z", 0)],
                    "\u03c8\u207a": _BELL + [("x", 0)],
                    "\u03c8\u207b": _BELL + [("z", 0), ("x", 0)],
                },
            },
        },
        {
            "title": "Correlation is not entanglement",
            "body": (
                r"A classically correlated pair (00 or 11 with probability 1/2 each) gives the same standard-basis "
                r"statistics as $|\phi^+\rangle$. The difference shows up after a Hadamard on both qubits: "
                r"$|\phi^+\rangle$ stays perfectly correlated while the classical pair becomes uniform. The course "
                "notes that entanglement can do things that \u201ccannot be done with any classically correlated state.\u201d"
            ),
            "sources": ["boqi-eia", "gfqi-convex"],
            "checked": "Both cases are computed exactly with Qiskit's DensityMatrix class.",
            "try": {"kind": "widget", "name": "correlation_vs_entanglement"},
        },
        {
            "title": "Entanglement as a resource",
            "body": (
                r"In quantum information, $|\phi^+\rangle$ is treated as one unit of entanglement, an **e-bit** "
                "(\u201cthe \u2018e\u2019 stands for \u2018entangled\u2019\u201d). Teleportation and superdense coding, in the next "
                "lesson, each use one e-bit."
            ),
            "sources": ["boqi-eia"],
        },
        {
            "title": "Quick check",
            "body": "Use the product-state test.",
            "sources": ["boqi-multi-quantum"],
            "try": {
                "kind": "check",
                "question": "Which state is entangled?",
                "options": [r"$|0\rangle\otimes|+\rangle$", r"$\tfrac{3}{5}|00\rangle + \tfrac{4}{5}|11\rangle$", r"$|11\rangle$"],
                "answer": 1,
                "why": r"The course uses $\tfrac35|00\rangle + \tfrac45|11\rangle$ as an example: the same argument shows it is not a product state.",
            },
        },
    ],
    "HA3": [
        {
            "title": "The setup",
            "body": (
                r"Alice and Bob share an e-bit: Alice holds qubit $\mathsf{A}$, Bob holds $\mathsf{B}$, in state "
                r"$|\phi^+\rangle$. Alice also has a qubit $\mathsf{Q}$ in an unknown state "
                r"$\alpha|0\rangle + \beta|1\rangle$ that she wants Bob to have."
            ),
            "sources": ["boqi-teleport"],
        },
        {
            "title": "The protocol",
            "body": (
                r"1. Alice applies a CNOT with $\mathsf{Q}$ as control and $\mathsf{A}$ as target, then a Hadamard on $\mathsf{Q}$.\n"
                r"2. She measures $\mathsf{A}$ (outcome $a$) and $\mathsf{Q}$ (outcome $b$) and sends both bits to Bob.\n"
                r"3. If $a = 1$ Bob applies X to $\mathsf{B}$; if $b = 1$ he applies Z."
            ),
            "sources": ["boqi-teleport"],
        },
        {
            "title": "Teleport a state",
            "body": (
                r"Choose a state for $\mathsf{Q}$. The page runs the protocol in Qiskit, with Bob's corrections "
                "written as controlled gates (the same operations, applied after the measurements are known), and "
                r"compares Bob's qubit with the original. Each outcome $ab$ occurs with probability 1/4."
            ),
            "sources": ["boqi-teleport"],
            "checked": "Fidelity is computed with Qiskit's quantum_info module for the state you choose.",
            "try": {"kind": "widget", "name": "teleport"},
        },
        {
            "title": "What moves, and what doesn't",
            "body": (
                "As the course puts it, \u201cmatter is not teleported in quantum teleportation \u2014 what is actually "
                "teleported is quantum information.\u201d " r"Alice's $\mathsf{Q}$ ends up in $|b\rangle$, so no copy is left behind, consistent with "
                "the no-cloning theorem. The e-bit is used up, and Bob can't finish until Alice's two classical bits "
                "reach him; the Nobel committee's background notes that \u201ca signal cannot travel faster than light.\u201d"
            ),
            "sources": ["boqi-teleport", "boqi-limitations", "nobel-2022"],
        },
        {
            "title": "Superdense coding",
            "body": (
                r"The reverse trade: one qubit plus one shared e-bit carries **two** classical bits $c, d$. Alice applies "
                r"Z if $d = 1$ and X if $c = 1$, then sends $\mathsf{A}$. Bob applies a CNOT ($\mathsf{A}$ control, "
                r"$\mathsf{B}$ target) and a Hadamard on $\mathsf{A}$, then measures $\mathsf{B}$ to get $c$ and "
                r"$\mathsf{A}$ to get $d$."
            ),
            "sources": ["boqi-superdense"],
            "try": {"kind": "widget", "name": "superdense"},
        },
        {
            "title": "Quick check",
            "body": "Count the resources.",
            "sources": ["boqi-teleport"],
            "try": {
                "kind": "check",
                "question": "What does teleporting one qubit use up?",
                "options": ["One e-bit and two classical bits", "Two qubits sent from Alice to Bob", "Nothing; it happens instantly"],
                "answer": 0,
                "why": "The protocol uses one shared e-bit plus two bits of classical communication.",
            },
        },
    ],
    "HA4": [
        {
            "title": "The query model",
            "body": (
                "In the query model the input is a function hidden in an **oracle** or **black box**: \u201cthe only "
                "way to access it being to ask questions.\u201d An algorithm's cost is the number of queries it makes."
            ),
            "sources": ["foqa-query"],
        },
        {
            "title": "Deutsch\u2013Jozsa",
            "body": (
                r"Promise: $f:\{0,1\}^n \to \{0,1\}$ is either constant or balanced. " "The Deutsch\u2013Jozsa algorithm "
                r"makes **one** query: if every measured bit is 0, $f$ is constant; otherwise it is balanced. Any "
                r"deterministic classical algorithm needs $2^{n-1}+1$ queries in the worst case. The catch: "
                "\u201cprobabilistic classical algorithms can solve the Deutsch-Jozsa problem with very high "
                "probability using just a few queries.\u201d"
            ),
            "sources": ["foqa-dj"],
            "try": {"kind": "widget", "name": "deutsch_jozsa"},
        },
        {
            "title": "Unstructured search",
            "body": (
                r"Grover's algorithm finds an input with $f(x) = 1$ among $N = 2^n$ possibilities using "
                r"$O(\sqrt N)$ queries; classical search needs $O(N)$. Within the query model this is "
                "asymptotically optimal, a quadratic advantage."
            ),
            "sources": ["foqa-grover-search", "foqa-grover-remarks"],
        },
        {
            "title": "Amplitude amplification, iteration by iteration",
            "body": (
                r"With $s$ solutions, let $\theta = \sin^{-1}\sqrt{s/N}$. After $t$ Grover iterations the success "
                r"probability is $\sin^2((2t+1)\theta)$. It rises, then oscillates, so the course recommends "
                r"$t = \lfloor \pi / (4\theta) \rfloor$. For $N = 4$ with one solution, a single iteration finds "
                "it with certainty. Try different sizes and iteration counts."
            ),
            "sources": ["foqa-grover-analysis", "foqa-grover-iterations"],
            "try": {"kind": "widget", "name": "grover"},
        },
        {
            "title": "Quick check",
            "body": "Compare query counts.",
            "sources": ["foqa-dj"],
            "try": {
                "kind": "check",
                "question": "For n = 3, how many queries does a deterministic classical algorithm need in the worst case for Deutsch\u2013Jozsa?",
                "options": ["1", "5", "8"],
                "answer": 1,
                "why": r"$2^{n-1} + 1 = 2^2 + 1 = 5$. The quantum algorithm needs 1.",
            },
        },
    ],
    "HR1": [
        {
            "title": "Density matrices",
            "body": (
                r"A density matrix $\rho$ has unit trace, $\operatorname{Tr}(\rho) = 1$, and is positive "
                r"semidefinite, $\rho \geq 0$. States of the form $\rho = |\psi\rangle\langle\psi|$ are **pure**; "
                "they have one eigenvalue equal to 1 and all others 0."
            ),
            "sources": ["gfqi-density"],
        },
        {
            "title": "Mixed states and the Bloch ball",
            "body": (
                r"Randomly preparing $|0\rangle$ or $|1\rangle$ with probability 1/2 each gives "
                r"$\tfrac12|0\rangle\langle0| + \tfrac12|1\rangle\langle1| = \mathbb{I}/2$, the **completely mixed "
                "state**. Pure qubit states sit on the Bloch sphere; convex combinations give \u201cpoints inside of "
                "the Bloch sphere, which represent density matrices of states that are not pure.\u201d"
            ),
            "sources": ["gfqi-convex", "gfqi-bloch"],
        },
        {
            "title": "Purity",
            "body": (
                r"Qiskit's `DensityMatrix.purity()` returns the purity of a state, $\operatorname{Tr}(\rho^2)$. It is 1 "
                r"for pure states and smaller for mixed ones; for a qubit it bottoms out at 1/2 for $\mathbb{I}/2$. "
                "The noise lab below reports it."
            ),
            "sources": ["api-densitymatrix", "gfqi-density"],
            "checked": r"The test suite checks that `purity()` equals $\operatorname{Tr}(\rho^2)$ and the values 1 and 1/2.",
        },
        {
            "title": "Quantum channels",
            "body": (
                "A channel must be **trace-preserving** and **completely positive**. A Kraus representation writes it "
                r"as $\Phi(\rho) = \sum_k A_k \rho A_k^\dagger$ with $\sum_k A_k^\dagger A_k = \mathbb{I}$. Two examples "
                r"from the course: the completely dephasing channel $\Delta$ zeros the off-diagonal entries, and the "
                r"completely depolarizing channel $\Omega(\rho) = \operatorname{Tr}(\rho)\,\mathbb{I}/2$ outputs the "
                "completely mixed state."
            ),
            "sources": ["gfqi-channels", "gfqi-kraus"],
        },
        {
            "title": "Noise lab",
            "body": (
                r"Here the noise channel acts with probability $p$ (otherwise nothing happens). Watch which "
                r"information disappears: dephasing erases the off-diagonal entries (so $|+\rangle$ loses its "
                "X-basis certainty) but keeps standard-basis statistics; depolarizing pushes every state toward "
                r"$\mathbb{I}/2$."
            ),
            "sources": ["gfqi-channels", "api-densitymatrix"],
            "checked": "Every matrix, purity and probability is computed with Qiskit's DensityMatrix.",
            "try": {"kind": "widget", "name": "noise"},
        },
        {
            "title": "Quick check",
            "body": "Use the purity definition.",
            "sources": ["gfqi-convex"],
            "try": {
                "kind": "check",
                "question": r"What is the purity $\operatorname{Tr}(\rho^2)$ of the completely mixed qubit state $\mathbb{I}/2$?",
                "options": ["0", "1/2", "1"],
                "answer": 1,
                "why": r"$(\mathbb{I}/2)^2 = \mathbb{I}/4$, whose trace is $2 \times 1/4 = 1/2$.",
            },
        },
    ],
    "HR2": [
        {
            "title": "The variational theorem",
            "body": (
                r"For any parameterized state, $\langle\psi(\vec\theta)|\hat{\mathcal H}|\psi(\vec\theta)\rangle \geq \lambda_0$, "
                "the lowest eigenvalue (ground-state energy). So minimizing the energy over the parameters gives an "
                "upper estimate of the ground-state energy that improves as the minimum is approached."
            ),
            "sources": ["vad-intro", "vad-cost"],
        },
        {
            "title": "The hybrid loop",
            "body": (
                "A variational algorithm combines a **cost function**, an **ansatz** (the parameterized search "
                "space) and an **optimizer**. The quantum computer evaluates the cost, an expectation value that "
                "can be estimated with the Estimator primitive. Then \u201ca classical optimizer analyzes them and "
                "chooses the next set of values for the variational parameters.\u201d"
            ),
            "sources": ["vad-intro", "vad-cost"],
        },
        {
            "title": "Ans\u00e4tze",
            "body": (
                "An ansatz combines a reference state with a **variational form**, a parameterized circuit whose "
                "gate parameters the optimizer tunes. Qiskit's circuit library includes ready-made forms such as "
                "`real_amplitudes` and `efficient_su2`."
            ),
            "sources": ["vad-ansatz", "api-real-amplitudes"],
        },
        {
            "title": "Run a mini VQE",
            "body": (
                r"This demo minimizes $\langle H\rangle$ for a small **toy** Hamiltonian chosen for this page "
                r"($H = Z\!Z + 0.5\,X\!I + 0.5\,I\!X$, not a molecule), using a `real_amplitudes` ansatz, "
                "Qiskit's `StatevectorEstimator`, and SciPy's COBYLA optimizer, the same optimizer used in the "
                "course. The exact ground energy is computed separately so you can compare."
            ),
            "sources": ["vad-optim", "api-estimator", "api-real-amplitudes"],
            "checked": "The test suite runs this optimization and checks it reaches the exact ground energy.",
            "try": {"kind": "widget", "name": "vqe"},
        },
        {
            "title": "What can go wrong",
            "body": (
                "Local optimizers are fast but \u201ccan be heavily dependent on the initial point\u201d and can get "
                "stuck in **local minima**. If the cost landscape is relatively flat, it is hard to find a direction "
                "to search, which is called a **barren plateau**. Gradient-free methods cost more evaluations in "
                "high-dimensional search spaces."
            ),
            "sources": ["vad-optim"],
        },
        {
            "title": "Quick check",
            "body": "Who does what in the loop?",
            "sources": ["vad-intro"],
            "try": {
                "kind": "check",
                "question": "In VQE, which part runs on a classical computer?",
                "options": ["Preparing the ansatz state", "Choosing the next parameters (the optimizer)", "Measuring the qubits"],
                "answer": 1,
                "why": "The quantum computer evaluates the cost; a classical optimizer chooses the next parameters.",
            },
        },
    ],
    "HR3": [
        {
            "title": "Max-cut",
            "body": (
                "Given a graph, split its nodes into two sets so that as many edges as possible cross between the "
                "sets. Qiskit's QAOA tutorial calls max-cut \u201can NP-hard optimization problem with applications in "
                "clustering, network science, and statistical physics.\u201d"
            ),
            "sources": ["qiskit-qaoa"],
        },
        {
            "title": "From cost function to Hamiltonian",
            "body": (
                r"Each edge $(i, j)$ becomes a term $\tfrac12 Z_iZ_j$ in the cost Hamiltonian $H_C$, plus a constant "
                r"offset, and the cut value of a bitstring is $-(\langle H_C\rangle + \text{offset})$. For a single "
                r"bitstring, $Z_iZ_j = -1$ exactly when nodes $i$ and $j$ are on opposite sides."
            ),
            "sources": ["qiskit-qaoa"],
            "checked": "The cut values in the demo below are computed both ways and must agree (tested).",
        },
        {
            "title": "Alternating operators",
            "body": (
                r"QAOA starts from $H^{\otimes n}|0\rangle$ and applies alternating layers of the cost operator "
                r"$e^{-i\gamma_k H_C}$ and a mixer $e^{-i\beta_k H_m}$; a classical optimizer tunes the angles. "
                "Qiskit's `qaoa_ansatz` function builds this circuit (the tutorial uses the older `QAOAAnsatz` class, "
                "deprecated since Qiskit 2.1). By default it starts with a layer of Hadamard gates and uses global "
                "Pauli-X rotations as the mixer."
            ),
            "sources": ["qiskit-qaoa", "api-qaoa-ansatz"],
        },
        {
            "title": "Try p = 1 on a 4-node ring",
            "body": (
                "The ring 0\u20131\u20132\u20133\u20130 has a maximum cut of 4 (alternate the sides: 0101). " r"Adjust $\gamma$ and "
                r"$\beta$, or let COBYLA optimize them, and watch the expected cut. The **approximation ratio** shown "
                "is expected cut \u00f7 maximum cut."
            ),
            "sources": ["qiskit-qaoa", "api-qaoa-ansatz"],
            "checked": "Expected cuts are computed exactly from the qaoa_ansatz statevector.",
            "try": {"kind": "widget", "name": "qaoa"},
        },
        {
            "title": "From samples to a solution",
            "body": (
                "Finally, sample the optimized circuit and post-process: the tutorial extracts \u201cthe most likely "
                "bitstring from the sampled distribution,\u201d which represents the best cut found. The demo above "
                "lists the most likely bitstrings with their cut values."
            ),
            "sources": ["qiskit-qaoa"],
        },
        {
            "title": "Quick check",
            "body": "Map the edges.",
            "sources": ["qiskit-qaoa"],
            "try": {
                "kind": "check",
                "question": r"For a bitstring where nodes $i$ and $j$ are on opposite sides, what is $Z_iZ_j$?",
                "options": ["+1", "\u22121", "0"],
                "answer": 1,
                "why": r"$Z$ has eigenvalues $+1$ for 0 and $-1$ for 1, so opposite bits multiply to $-1$, and that edge counts toward the cut.",
            },
        },
    ],
    "HR4": [
        {
            "title": "Logical and physical qubits",
            "body": (
                "Error correction encodes one **logical** qubit into several **physical** qubits. The 3-bit "
                r"repetition code repeats a bit three times ($0 \mapsto 000$, $1 \mapsto 111$); for a qubit, "
                r"$\alpha|0\rangle + \beta|1\rangle$ becomes $\alpha|000\rangle + \beta|111\rangle$."
            ),
            "sources": ["qec-repetition"],
        },
        {
            "title": "Syndrome measurement",
            "body": (
                "Measuring the qubits directly would destroy the superposition. Instead, ancilla qubits measure the "
                "**parity** of qubits (0, 1) and (1, 2) without collapsing the encoded state. The outcomes are the "
                "**syndrome**: 00 means no correction, 01 means flip qubit 0, 11 qubit 1, and 10 qubit 2."
            ),
            "sources": ["qec-repetition"],
        },
        {
            "title": "Try the repetition code",
            "body": (
                "Encode a state, inject an error, extract the syndrome, correct, and decode. The page reports the "
                "syndrome and the fidelity between your original and recovered state."
            ),
            "sources": ["qec-repetition"],
            "checked": "Simulated with Qiskit; the tests check every syndrome against the course's table.",
            "try": {"kind": "widget", "name": "repetition_code"},
        },
        {
            "title": "The phase-flip problem",
            "body": (
                "In the course's words, \u201cthe 3-bit repetition code doesn't protect against phase-flips at all\u201d: " r"a Z error turns "
                r"$\alpha|000\rangle + \beta|111\rangle$ into $\alpha|000\rangle - \beta|111\rangle$, which the "
                "syndrome can't see (try the Z option above). The **9-qubit Shor code** combines repetition codes to "
                "handle both, and correcting bit flips and phase flips on a qubit is enough to correct an arbitrary "
                "single-qubit error."
            ),
            "sources": ["qec-repetition", "qec-shor"],
        },
        {
            "title": "Fault tolerance and the threshold theorem",
            "body": (
                "The threshold theorem, informally: a quantum circuit of size N \u201ccan be implemented with high "
                "accuracy by a noisy quantum circuit, provided that the probability of error at each location in "
                "the noisy circuit is below a fixed, nonzero threshold value,\u201d with only polylogarithmic overhead, "
                r"$O(N \log^c N)$."
            ),
            "sources": ["qec-threshold"],
        },
        {
            "title": "Quick check",
            "body": "Read the syndrome table.",
            "sources": ["qec-repetition"],
            "try": {
                "kind": "check",
                "question": "The syndrome is 11. Which correction do you apply?",
                "options": ["X on qubit 0", "X on qubit 1 (the middle qubit)", "X on qubit 2"],
                "answer": 1,
                "why": "Both parity checks involve qubit 1, so both flag it: syndrome 11 \u2192 flip qubit 1.",
            },
        },
    ],
}
