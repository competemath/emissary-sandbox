import Mathlib.Data.Nat.Defs

/-! Plain module: builds clean in every configuration. -/

theorem canary_clean (n : Nat) : n + 0 = n := by simp
