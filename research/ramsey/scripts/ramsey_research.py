"""
Ramsey Research — push the extension window analysis to R(3,3), R(4,4), R(5,5).
Test the 67% threshold hypothesis.

Usage:
    python ramsey_research.py
"""
from engine import *
import time


def research_extension_threshold():
    """Map extension windows for R(3,3), R(4,4), R(5,5) and test the 67% ratio."""
    print("=" * 70)
    print("EXTENSION WINDOW ANALYSIS")
    print("Testing hypothesis: extension closes at ~67% of R(k,k)")
    print("=" * 70)

    targets = [
        (3, 3, 6, 6),     # R(3,3)=6, scan up to 6
        (3, 4, 9, 9),     # R(3,4)=9, scan up to 9
        (4, 4, 18, 18),   # R(4,4)=18, scan up to 18
        (3, 5, 14, 14),   # R(3,5)=14, scan up to 14
    ]

    for r, s, ramsey, n_max in targets:
        print(f"\n{'-'*60}")
        print(f"R({r},{s}) = {ramsey}")
        print(f"{'-'*60}")

        t0 = time.time()
        results = extension_landscape(r, s, min(n_max, 20))
        elapsed = time.time() - t0

        print_landscape(results)

        # Find closure point
        closure = None
        for res in results:
            if res['found_avoider'] and 'valid_extensions' in res and res['valid_extensions'] == 0:
                closure = res['n']
                break

        if closure:
            ratio = closure / ramsey
            print(f"\nExtension window closes at n={closure}")
            print(f"R({r},{s}) = {ramsey}")
            print(f"Ratio: {closure}/{ramsey} = {ratio:.3f} ({ratio*100:.1f}%)")
        else:
            print(f"\nExtension window did not close in range tested")

        print(f"Time: {elapsed:.1f}s")


def research_r55_push():
    """Push R(5,5) analysis as far as Python can go."""
    print("\n" + "=" * 70)
    print("R(5,5) FRONTIER PUSH")
    print("Known: 43 ≤ R(5,5) ≤ 48")
    print("=" * 70)

    # First: Paley survey for R(5,5)
    print("\nPaley graphs and R(5,5):")
    primes_1mod4 = [p for p in range(5, 60)
                    if all(p % d != 0 for d in range(2, int(p**0.5)+1)) and p % 4 == 1]

    for p in primes_1mod4:
        t0 = time.time()
        A = paley(p)
        alpha = independence_number(A)
        omega = clique_number(A)
        avoids = alpha < 5 and omega < 5
        elapsed = time.time() - t0
        status = "AVOIDS R(5,5)" if avoids else f"FAILS (alpha={alpha}, omega={omega})"
        print(f"  Paley({p:2d}): alpha={alpha} omega={omega} {status} [{elapsed:.1f}s]")

    # SA search at frontier sizes
    print("\nSA search for R(5,5) avoiding graphs:")
    for n in [37, 38, 39, 40, 41, 42]:
        print(f"\n  n={n}: ", end="", flush=True)
        t0 = time.time()
        adj, E, trial = ramsey_anneal(n, 5, 5, trials=3, steps_per_edge=150)
        elapsed = time.time() - t0
        if E == 0:
            alpha = independence_number(adj)
            omega = clique_number(adj)
            print(f"FOUND E=0 (trial {trial}, alpha={alpha}, omega={omega}) [{elapsed:.1f}s]")
            prof = graph_profile(adj)
            print(f"         edges={prof['edges']} density={prof['density']}% tri={prof['triangles']} regular={prof['regular']}")
        else:
            print(f"best E={E} [{elapsed:.1f}s]")


def research_extension_r33():
    """Detailed extension analysis for R(3,3) — small enough to be exhaustive."""
    print("\n" + "=" * 70)
    print("R(3,3) DETAILED EXTENSION ANALYSIS")
    print("=" * 70)

    for n in range(3, 7):
        adj, E, _ = ramsey_anneal(n, 3, 3, trials=20, steps_per_edge=500)
        if E > 0:
            print(f"\nn={n}: No R(3,3)-avoiding graph found")
            continue

        ext = extend_analysis(adj, 3, 3)
        tri = triangles(adj)
        alpha = independence_number(adj)

        print(f"\nn={n}: alpha={alpha}, omega={clique_number(adj)}, triangles={tri}")
        print(f"  Extension: {ext['valid']}/{ext['total_patterns']} valid ({ext['pct_valid']:.1f}%)")
        print(f"  (r-1)-cliques: {ext['r1_cliques']}, (s-1)-indep-sets: {ext['s1_indeps']}")
        print(f"  Killed by clique: {ext['fails_clique']}, by indep: {ext['fails_indep']}, by both: {ext['fails_both']}")


def research_threshold_ratios():
    """Compute the extension closure ratio for multiple R(r,s)."""
    print("\n" + "=" * 70)
    print("EXTENSION CLOSURE RATIOS")
    print("Hypothesis: closure occurs at ~67% of R(r,s)")
    print("=" * 70)

    cases = [
        (3, 3, 6),
        (3, 4, 9),
        (3, 5, 14),
        (4, 4, 18),
    ]

    print(f"\n{'R(r,s)':>8} | {'R value':>7} | {'Closure':>7} | {'Ratio':>6}")
    print("-" * 40)

    for r, s, R in cases:
        results = extension_landscape(r, s, min(R, 20))
        closure = None
        for res in results:
            if res['found_avoider'] and 'valid_extensions' in res and res['valid_extensions'] == 0:
                closure = res['n']
                break
        if closure:
            ratio = closure / R
            print(f"R({r},{s})   | {R:7d} | {closure:7d} | {ratio:5.1%}")
        else:
            print(f"R({r},{s})   | {R:7d} |    open | {'N/A':>6}")


if __name__ == '__main__':
    print("TLS-Graph Ramsey Research Engine")
    print("Python + NumPy" + (" + Numba" if HAS_NUMBA else " (no Numba)"))
    print()

    research_extension_r33()
    research_threshold_ratios()
    research_extension_threshold()
    research_r55_push()
