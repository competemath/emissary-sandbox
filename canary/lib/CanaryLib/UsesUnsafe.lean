import Mathlib.Data.Nat.Defs
import CanaryDep.Unsafe

/-! Imports the dependency module that runs code at compile time: the vendoring tool must keep it out, so this stays a bad import. -/

theorem canary_uses_unsafe : True := trivial
