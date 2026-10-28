"""judge.py: the verdict of a campaign. Invariants, with mutants (the same culture as emissary-archangel's scripts/bump/tests/CLASSES.md).

  * a capability whose file is present is enforced EXACTLY (a missing or different observation fails it);
  * a capability whose file is missing fails the verdict when it is required (tooling may only gain abilities) and is merely skipped otherwise;
  * an observation the expectation does not mention never fails;
  * the verdict is a function of its three inputs only (deterministic, order independent);
  * a regression cannot be made acceptable by the change under test: the expectation is an input of the trusted job, not of the run.
"""

from __future__ import annotations

import json
import random
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import judge as j  # noqa: E402
import observe as o  # noqa: E402

EXP = {
    "required_capabilities": ["baseline"],
    "capabilities": {
        "baseline": {"requires_file": "scripts/bump/tolerant_build.py", "expect": {"states": {"A": "clean", "B": "errors"}}},
        "vendor": {"requires_file": "scripts/bump/vendor_deps.py", "expect": {"vendored": ["Dep.X"], "unsafe": ["Dep.U"], "states": {"C": "clean"}}},
    },
}
OBS = {"states": {"A": "clean", "B": "errors", "C": "clean", "Z": "whatever"}, "vendored": ["Dep.X"], "unsafe": ["Dep.U"]}
FILES = {"scripts/bump/tolerant_build.py", "scripts/bump/vendor_deps.py"}


class Verdict(unittest.TestCase):
    def test_everything_as_expected_passes_and_names_what_it_enforced(self):
        v = j.judge(OBS, EXP, FILES)
        self.assertTrue(v["ok"], v)
        self.assertEqual((v["enforced"], v["skipped"]), (["baseline", "vendor"], []))

    def test_a_different_state_a_missing_module_and_a_different_list_all_fail(self):
        bad = json.loads(json.dumps(OBS))
        bad["states"]["C"] = "bad_import"
        self.assertFalse(j.judge(bad, EXP, FILES)["ok"])
        bad = json.loads(json.dumps(OBS))
        del bad["states"]["A"]
        self.assertFalse(j.judge(bad, EXP, FILES)["ok"])
        bad = json.loads(json.dumps(OBS))
        bad["vendored"] = ["Dep.X", "Dep.Extra"]
        self.assertFalse(j.judge(bad, EXP, FILES)["ok"])
        bad = json.loads(json.dumps(OBS))
        bad["unsafe"] = []
        self.assertFalse(j.judge(bad, EXP, FILES)["ok"])

    def test_a_required_capability_whose_file_is_gone_fails_and_an_optional_one_is_skipped(self):
        v = j.judge(OBS, EXP, FILES - {"scripts/bump/tolerant_build.py"})
        self.assertFalse(v["ok"])
        self.assertTrue(any("capability removed" in f for f in v["failures"]))
        v = j.judge(OBS, EXP, FILES - {"scripts/bump/vendor_deps.py"})
        self.assertTrue(v["ok"])
        self.assertEqual(v["skipped"], ["vendor"])

    def test_observations_the_expectation_does_not_mention_never_fail(self):
        extra = dict(OBS, brand_new_thing=[1, 2, 3])
        extra["states"] = dict(OBS["states"], Another="errors")
        self.assertTrue(j.judge(extra, EXP, FILES)["ok"])

    def test_a_required_capability_that_the_expectation_does_not_define_fails(self):
        exp = dict(EXP, required_capabilities=["baseline", "ghost"])
        self.assertFalse(j.judge(OBS, exp, FILES)["ok"])

    def test_the_verdict_depends_on_nothing_but_its_inputs(self):
        rng = random.Random(3)
        for _ in range(200):
            files = {f for f in FILES if rng.random() < 0.8}
            obs = {"states": {m: rng.choice(["clean", "errors", "bad_import"]) for m in "ABC"}, "vendored": rng.choice([["Dep.X"], []]), "unsafe": rng.choice([["Dep.U"], []])}
            a = j.judge(obs, EXP, files)
            b = j.judge(json.loads(json.dumps(obs)), json.loads(json.dumps(EXP)), set(sorted(files, reverse=True)))
            self.assertEqual(a, b)
            # and it is exactly "every enforced expectation holds"
            want_ok = ("scripts/bump/tolerant_build.py" in files and obs["states"]["A"] == "clean" and obs["states"]["B"] == "errors") and (
                "scripts/bump/vendor_deps.py" not in files or (obs["vendored"] == ["Dep.X"] and obs["unsafe"] == ["Dep.U"] and obs["states"]["C"] == "clean")
            )
            self.assertEqual(a["ok"], want_ok, (obs, files))


class Observe(unittest.TestCase):
    def test_what_the_raw_files_say_and_nothing_when_a_file_is_absent(self):
        import tempfile

        with tempfile.TemporaryDirectory() as t:
            raw = Path(t)
            self.assertEqual(o.observe(raw), {})
            (raw / "tb-final.json").write_text(json.dumps({"status": {"M": {"state": "clean"}, "N": {"state": "errors"}}}))
            (raw / "vendored.json").write_text(json.dumps({"vendored": [{"module": "Dep.X"}], "unsafe": [{"module": "Dep.U"}], "unresolved": ["Dep.U"]}))
            (raw / "repair-1.json").write_text(json.dumps({"removed_declarations": [{"name": "Nat.zero_add"}]}))
            (raw / "lint.json").write_text(json.dumps({"removed": [{"kind": "#print"}], "violations": []}))
            obs = o.observe(raw)
            self.assertEqual(obs["states"], {"M": "clean", "N": "errors"})
            self.assertEqual((obs["vendored"], obs["unsafe"], obs["removed_declarations"], obs["lint_removed_kinds"]), (["Dep.X"], ["Dep.U"], ["Nat.zero_add"], ["#print"]))


class TheExpectationItself(unittest.TestCase):
    """canary/expected.json is data a person edits; it must be well formed and say things the observer can produce."""

    def setUp(self):
        self.exp = json.loads((HERE.parent.parent / "canary" / "expected.json").read_text())

    def test_it_is_well_formed(self):
        self.assertTrue(set(self.exp["required_capabilities"]) <= set(self.exp["capabilities"]))
        for name, cap in self.exp["capabilities"].items():
            self.assertTrue(cap["requires_file"].startswith("scripts/"), name)
            self.assertTrue(cap["expect"], name)

    def test_every_key_it_expects_is_one_the_observer_produces(self):
        produced = {"states", "vendored", "unsafe", "unresolved", "removed_declarations", "lint_removed_kinds", "lint_violations_after"}
        for name, cap in self.exp["capabilities"].items():
            self.assertTrue(set(cap["expect"]) <= produced, (name, set(cap["expect"]) - produced))

    def test_every_module_it_names_exists_in_the_canary(self):
        lib = HERE.parent.parent / "canary" / "lib"
        dep = HERE.parent.parent / "canary" / "dep"
        for cap in self.exp["capabilities"].values():
            for mod in cap["expect"].get("states", {}):
                base = lib if mod.startswith("CanaryLib") else dep
                self.assertTrue((base / (mod.replace(".", "/") + ".lean")).exists() or mod == "CanaryLib", mod)


class Mutants(unittest.TestCase):
    """Break the judge the way the shortcut would; the tests above must notice."""

    def noticed(self, fn):
        suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(Verdict)])
        result = unittest.TestResult()
        saved = j.judge
        try:
            j.judge = fn(saved)
            suite.run(result)
        finally:
            j.judge = saved
        return bool(result.failures or result.errors)

    def test_a_judge_that_always_passes_is_noticed(self):
        self.assertTrue(self.noticed(lambda orig: lambda obs, exp, files: {"ok": True, "failures": [], "enforced": [], "skipped": []}))

    def test_a_judge_that_ignores_removed_capabilities_is_noticed(self):
        def mutant(orig):
            def m(obs, exp, files):
                exp = json.loads(json.dumps(exp))
                exp["required_capabilities"] = []
                return orig(obs, exp, files)

            return m

        self.assertTrue(self.noticed(mutant))

    def test_a_judge_that_does_not_look_at_states_is_noticed(self):
        def mutant(orig):
            def m(obs, exp, files):
                exp = json.loads(json.dumps(exp))
                for c in exp["capabilities"].values():
                    c["expect"].pop("states", None)
                return orig(obs, exp, files)

            return m

        self.assertTrue(self.noticed(mutant))

    def test_the_unmutated_judge_is_not_noticed(self):
        self.assertFalse(self.noticed(lambda orig: orig))


if __name__ == "__main__":
    unittest.main()
