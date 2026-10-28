/-! A dependency package of the canary library: ordinary, safe code. -/

namespace CanaryDep

def double (n : Nat) : Nat := n + n

theorem double_eq (n : Nat) : double n = 2 * n := by
  unfold double
  omega

end CanaryDep
