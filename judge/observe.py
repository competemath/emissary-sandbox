#!/usr/bin/env python3
"""observe.py — write down what a campaign run did, from the files it left. Runs in the run job (it is given the run's raw files); the VERDICT is made elsewhere, by judge.py.

  observe.py --raw DIR --out obs.json

DIR holds: tb-final.json (the tolerant build's module states), vendored.json (vendor_deps.py), repair-*.json (engine.py repair rounds), lint.json (lint_cli.py repair on a canary module), files.json.
A file that is absent means the capability did not run; its observations are simply absent.
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path


def load(p: Path):
    return json.loads(p.read_text()) if p.is_file() else None


def observe(raw: Path) -> dict:
    obs: dict = {}
    tb = load(raw / "tb-final.json")
    if tb:
        obs["states"] = {m: v.get("state") for m, v in (tb.get("status") or {}).items()}
    v = load(raw / "vendored.json")
    if v is not None:
        obs["vendored"] = sorted(x["module"] for x in v.get("vendored", []))
        obs["unsafe"] = sorted(x["module"] for x in v.get("unsafe", []))
        obs["unresolved"] = sorted(v.get("unresolved", []))
    removed: list[str] = []
    for f in sorted(glob.glob(str(raw / "repair-*.json"))):
        r = load(Path(f)) or {}
        removed += [d["name"] for d in r.get("removed_declarations", [])]
    if glob.glob(str(raw / "repair-*.json")):
        obs["removed_declarations"] = sorted(removed)
    lint = load(raw / "lint.json")
    if lint is not None:
        obs["lint_removed_kinds"] = sorted({r["kind"] for r in lint.get("removed", [])})
        obs["lint_violations_after"] = lint.get("violations", [])
    return obs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    Path(a.out).write_text(json.dumps(observe(Path(a.raw)), indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
