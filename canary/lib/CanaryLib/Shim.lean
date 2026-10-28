import Mathlib.Data.Nat.Defs

/-! A compatibility shim for a name the target already declares: "already been declared" without the repair. -/

namespace Nat

/-- Compatibility spelling. -/
protected theorem zero_add (n : Nat) : 0 + n = n := by omega

end Nat

theorem canary_shim_user (n : Nat) : 0 + n = n := Nat.zero_add n
