# emissary-sandbox

Public, **secret-free** place where changes to [competemath/emissary-archangel](https://github.com/competemath/emissary-archangel)'s tooling are run for real before they are trusted.

* `canary/lib`: a small Lean library that has, on purpose, the things that cost the factory real runs: a Lake dependency it imports (`canary/dep`, vendored), a dependency module that runs code at compile time (must be kept out), a compatibility shim for a name Mathlib/core already declares (must be removed), a `#print axioms` line (the content lint refuses it), a module with a genuine error (must stay an honest error) and modules behind it.
* `canary/expected.json`: what the canary must look like after the tooling has run, **by capability** (see `judge/judge.py`). Changing it is a commit here, never part of a pull request under test.
* `.github/workflows/campaign.yml`: `poll` finds the open emissary pull requests that touch the pipeline, `run` executes their tooling on the canary (read-only job, no secrets), `judge` (a separate, trusted job) compares and **attests** the result (GitHub artifact attestation, Sigstore).
* emissary's check `campaign-gate` verifies the attestation for the pull request's head commit: `gh attestation verify result.json --repo competemath/emissary-sandbox`.

What this does **not** see: a change that makes its own tooling lie about what it did. The result names the commit that produced it; that is for review.
