import Mathlib.Data.Nat.Defs
import CanaryDep.Basic

/-! Imports a package the library requires: nothing builds that package, so without vendoring this is a bad import.
The author's `#print axioms` line below is what the content lint refuses in a record. -/

theorem canary_uses_dep (n : Nat) : CanaryDep.double n = n + n := by
  unfold CanaryDep.double
  rfl

#print axioms canary_uses_dep
