import CanaryLib.Shim

/-! Imports the shim module: it must build once the shim is gone. -/

theorem canary_after_shim (n : Nat) : 0 + n = n := canary_shim_user n
