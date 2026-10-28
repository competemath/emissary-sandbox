import Mathlib.Data.Nat.Defs

/-! One declaration that really does not hold: an honest error that no repair may hide. -/

theorem canary_broken : (1 : Nat) = 2 := by simp

theorem canary_fine_after_broken : True := trivial
