#!/usr/bin/env python3
"""judge.py — compare what a campaign OBSERVED with what it must observe, by capability.

An emissary-archangel change is checked by running its tooling on the canary library (canary/lib) in this repository. What the run did is written down by observe.py as an observation
(module states, what was vendored, what was kept out, which declarations were removed, what the lint repair took out). This file decides whether that is acceptable. It is trusted code: it runs
in a job of its own, from this repository's main, and never executes anything from the change under test.

The expectation (canary/expected.json) is a set of CAPABILITIES. Each names the file that gives emissary that ability and what the canary must look like when it works:

  - a capability whose file is present in the change is ENFORCED: every expectation of it must hold exactly;
  - a capability listed in `required_capabilities` whose file is MISSING fails the verdict ("a capability was removed"): tooling may only gain abilities, never lose them silently;
  - any other capability whose file is missing is SKIPPED (the change is based on a version of emissary from before it existed) and reported as skipped.

`required_capabilities` and the expectations change only through a commit to this repository, which is the human step: a pull request cannot make its own regression acceptable.

  judge.py --observation obs.json --expected canary/expected.json --files files.json --out verdict.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def judge(observation: dict, expected: dict, files: set[str]) -> dict:
    failures: list[str] = []
    enforced: list[str] = []
    skipped: list[str] = []
    caps = expected.get("capabilities", {})
    required = set(expected.get("required_capabilities", []))
    for name in sorted(required - set(caps)):
        failures.append(f"{name}: required but not defined in the expectation")
    for name, cap in sorted(caps.items()):
        needed = cap.get("requires_file")
        if needed and needed not in files:
            if name in required:
                failures.append(f"{name}: capability removed ({needed} is missing from the change)")
            else:
                skipped.append(name)
            continue
        enforced.append(name)
        exp = cap.get("expect", {})
        for key, want in sorted(exp.items()):
            got = observation.get(key)
            if key == "states":
                for module, state in sorted(want.items()):
                    have = (got or {}).get(module)
                    if have != state:
                        failures.append(f"{name}: module {module} is {have!r}, expected {state!r}")
            elif isinstance(want, list):
                if sorted(got or []) != sorted(want):
                    failures.append(f"{name}: {key} is {sorted(got or [])}, expected {sorted(want)}")
            else:
                if got != want:
                    failures.append(f"{name}: {key} is {got!r}, expected {want!r}")
    return {"ok": not failures, "failures": failures, "enforced": enforced, "skipped": skipped}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--observation", required=True)
    ap.add_argument("--expected", required=True)
    ap.add_argument("--files", required=True, help="JSON list of the emissary paths that exist in the change")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    v = judge(json.loads(Path(a.observation).read_text()), json.loads(Path(a.expected).read_text()), set(json.loads(Path(a.files).read_text())))
    Path(a.out).write_text(json.dumps(v, indent=1, sort_keys=True))
    print(json.dumps(v, indent=1, sort_keys=True))
    return 0 if v["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
