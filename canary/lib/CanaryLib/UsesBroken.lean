import CanaryLib.Broken

/-! A module behind one with an error in a declaration: the tolerant build still builds it. -/

theorem canary_uses_broken : True := canary_fine_after_broken
