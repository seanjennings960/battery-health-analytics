# Numerical comparison: FVM-style weighted midpoint, plain midpoint (Newton–Cotes),
# Gauss–Jacobi quadrature, and Adaptive Simpson for ∫_0^1 r^2 sin(π r) dr.

import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def f(r):
    return math.sin(math.pi * r)

def g(r):
    return (r**2) * math.sin(math.pi * r)

# Exact integral: ∫_0^1 r^2 sin(π r) dr = 1/π − 4/π^3
I_exact = 1/math.pi - 4/(math.pi**3)

def midpoint_uniform(n):
    """Plain midpoint (Newton–Cotes) for ∫ g(r) dr on [0,1] with n cells."""
    h = 1.0 / n
    total = 0.0
    for i in range(n):
        r_mid = (i + 0.5) * h
        total += g(r_mid)
    return total * h, n  # value, function evaluations of g

def fvm_midpoint_weighted(n):
    """FVM-style midpoint: approximate ∫_0^1 r^2 f(r) dr by summing f(mid) * ∫cell r^2 dr.
       This integrates the geometry factor r^2 exactly per cell.
    """
    total = 0.0
    evals = 0
    for i in range(n):
        r_left = i / n
        r_right = (i + 1) / n
        r_mid = 0.5 * (r_left + r_right)
        # exact integral of r^2 over the cell
        weight_cell = (r_right**3 - r_left**3) / 3.0
        total += f(r_mid) * weight_cell
        evals += 1  # one f-eval per cell
    return total, evals

def gauss_jacobi_nodes_weights(n, alpha, beta):
    """Golub–Welsch algorithm for Gauss–Jacobi on [-1,1] with weight (1-x)^alpha (1+x)^beta.
       Returns nodes x (in [-1,1]) and weights w for ∫_{-1}^1 (1-x)^α (1+x)^β φ(x) dx.
    """
    k = np.arange(n, dtype=float)
    # diagonal a_k
    ab = (beta**2 - alpha**2)
    den = (2*k + alpha + beta) * (2*k + alpha + beta + 2)
    a = np.where(den != 0, ab / den, 0.0)

    # subdiagonal b_k (for k>=1)
    kk = np.arange(1, n, dtype=float)
    num = 4*kk*(kk+alpha)*(kk+beta)*(kk+alpha+beta)
    den = (2*kk + alpha + beta)**2 * (2*kk + alpha + beta + 1) * (2*kk + alpha + beta - 1)
    b = np.sqrt(num / den)

    # symmetric tridiagonal Jacobi matrix
    J = np.diag(a) + np.diag(b, 1) + np.diag(b, -1)

    # eigen-decomposition
    vals, vecs = np.linalg.eigh(J)
    x = vals  # nodes in [-1,1]

    # weights
    from math import gamma
    c = (2**(alpha+beta+1)) * gamma(alpha+1) * gamma(beta+1) / gamma(alpha+beta+2)
    w = c * (vecs[0, :]**2)
    return x, w

def gauss_jacobi_integrate_on_0_1(n, alpha=0.0, beta=2.0):
    """Compute ∫_0^1 r^2 f(r) dr using Gauss–Jacobi with (alpha=0, beta=2).
       We compute nodes/weights on [-1,1], map to [0,1], and scale weights accordingly.
    """
    x, w = gauss_jacobi_nodes_weights(n, alpha, beta)  # on [-1,1]
    # map to [0,1]: r = (x+1)/2
    r = 0.5 * (x + 1.0)
    # scaling for the change of variables:
    # ∫_0^1 r^β (1-r)^α φ(r) dr = 1/2^{α+β+1} ∫_{-1}^1 (1-x)^α (1+x)^β φ((x+1)/2) dx
    scale = 1.0 / (2.0**(alpha + beta + 1.0))
    val = np.sum(w * np.vectorize(f)(r)) * scale
    evals = n  # number of f evaluations
    return float(val), evals

def adaptive_simpson(fh, a, b, tol=1e-8, max_depth=20):
    """Adaptive Simpson's rule for ∫_a^b fh(x) dx with error ~ tol.
       Returns (value, eval_count).
    """
    eval_count = 0

    def simpson(fa, fm, fb, a, b):
        return (b - a) * (fa + 4*fm + fb) / 6.0

    def recurse(a, b, fa, fm, fb, S, depth):
        nonlocal eval_count
        m = 0.5 * (a + b)
        lm = 0.5 * (a + m)
        rm = 0.5 * (m + b)
        flm = fh(lm); frm = fh(rm)
        eval_count += 2
        S_left = simpson(fa, flm, fm, a, m)
        S_right = simpson(fm, frm, fb, m, b)
        if depth <= 0:
            return S_left + S_right
        if abs(S_left + S_right - S) < 15 * tol:
            return S_left + S_right + (S_left + S_right - S) / 15.0
        return recurse(a, m, fa, flm, fm, S_left, depth - 1) + \
               recurse(m, b, fm, frm, fb, S_right, depth - 1)

    fa = fh(a); fb = fh(b); m = 0.5*(a+b); fm = fh(m)
    eval_count += 3
    S0 = simpson(fa, fm, fb, a, b)
    val = recurse(a, b, fa, fm, fb, S0, max_depth)
    return val, eval_count

def run_experiment():
    Ns = [2, 4, 8, 16, 32, 64, 128, 256]
    Gs = [2, 3, 4, 5, 6, 8, 10, 12, 16]
    tols = [1e-4, 1e-6, 1e-8]

    rows = []

    # Midpoint (plain) and FVM-weighted
    for n in Ns:
        val_plain, evals_plain = midpoint_uniform(n)
        err_plain = abs(val_plain - I_exact)
        rows.append(dict(Method="Midpoint (Newton–Cotes)", N=n, Evals=evals_plain, Value=val_plain, AbsError=err_plain))

        val_fvm, evals_fvm = fvm_midpoint_weighted(n)
        err_fvm = abs(val_fvm - I_exact)
        rows.append(dict(Method="FVM-style weighted midpoint", N=n, Evals=evals_fvm, Value=val_fvm, AbsError=err_fvm))

    # Gauss–Jacobi
    for n in Gs:
        val_gj, evals_gj = gauss_jacobi_integrate_on_0_1(n, alpha=0.0, beta=2.0)
        err_gj = abs(val_gj - I_exact)
        rows.append(dict(Method="Gauss–Jacobi (α=0, β=2)", N=n, Evals=evals_gj, Value=val_gj, AbsError=err_gj))

    # Adaptive Simpson
    for tol in tols:
        val_ad, evals_ad = adaptive_simpson(g, 0.0, 1.0, tol=tol, max_depth=30)
        err_ad = abs(val_ad - I_exact)
        rows.append(dict(Method=f"Adaptive Simpson tol={tol}", N=float('nan'), Evals=evals_ad, Value=val_ad, AbsError=err_ad))

    df = pd.DataFrame(rows)
    print(df.to_string(index=False))

    # Plot: error vs # of function evaluations
    plt.figure()
    for meth in ["Midpoint (Newton–Cotes)", "FVM-style weighted midpoint", "Gauss–Jacobi (α=0, β=2)"]:
        sub = df[df["Method"] == meth].sort_values("Evals")
        plt.loglog(sub["Evals"], sub["AbsError"], marker='o', label=meth)
    sub_ad = df[df["Method"].str.startswith("Adaptive Simpson")].sort_values("Evals")
    plt.loglog(sub_ad["Evals"], sub_ad["AbsError"], marker='x', linestyle='none', label="Adaptive Simpson (var. tol)")
    plt.xlabel("Function evaluations")
    plt.ylabel("Absolute error")
    plt.title("Error vs. function evaluations for ∫_0^1 r^2 sin(π r) dr")
    plt.legend()
    plt.tight_layout()
    plt.show()

    print("Exact integral I = 1/π − 4/π^3 ≈", I_exact)

if __name__ == "__main__":
    run_experiment()
