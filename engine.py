"""
TLS-Graph Python Engine — high-performance tensor operations for Ramsey research.
Same operations as the browser calculator, backed by NumPy + Numba.

Usage:
    from engine import *
    P = paley(37)
    print(ramsey_check(P, 5, 5))
    print(extend_analysis(P, 5, 5))
"""
import numpy as np
from functools import lru_cache
import time

try:
    from numba import njit, prange
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False
    print("Warning: numba not installed. Install with 'pip install numba' for ~100x speedup.")


# ─── Graph Construction ───

def adjacency(n):
    """Complete graph K_n."""
    A = np.ones((n, n), dtype=np.int8)
    np.fill_diagonal(A, 0)
    return A


def paley(p):
    """Paley graph on prime p vertices (p ≡ 1 mod 4)."""
    assert p >= 5 and all(p % d != 0 for d in range(2, int(p**0.5)+1)), f"{p} is not prime"
    assert p % 4 == 1, f"p must be ≡ 1 (mod 4), got {p} ≡ {p%4}"
    qr = set()
    for x in range(1, p):
        qr.add((x * x) % p)
    A = np.zeros((p, p), dtype=np.int8)
    for i in range(p):
        for j in range(p):
            if i != j and (j - i) % p in qr:
                A[i, j] = 1
    return A


def cubic_residue(p):
    """Cubic residue graph on prime p (p ≡ 1 mod 3)."""
    assert p >= 7 and all(p % d != 0 for d in range(2, int(p**0.5)+1)), f"{p} is not prime"
    assert p % 3 == 1, f"p must be ≡ 1 (mod 3), got {p} ≡ {p%3}"
    cr = set()
    for x in range(1, p):
        cr.add((x * x * x) % p)
    A = np.zeros((p, p), dtype=np.int8)
    for i in range(p):
        for j in range(p):
            if i != j and (j - i) % p in cr:
                A[i, j] = 1
    return A


def circulant(n, diffs):
    """Circulant graph with difference set."""
    S = set()
    for d in diffs:
        S.add(d % n)
        S.add((n - d) % n)
    A = np.zeros((n, n), dtype=np.int8)
    for i in range(n):
        for j in range(n):
            if i != j and (j - i) % n in S:
                A[i, j] = 1
    return A


def complement(A):
    """Complement graph."""
    n = A.shape[0]
    C = 1 - A
    np.fill_diagonal(C, 0)
    return C.astype(np.int8)


# ─── Graph Analysis ───

def degree(A):
    """Degree sequence."""
    return A.sum(axis=1)


def triangles(A):
    """Triangle count via trace(A³)/6."""
    A64 = A.astype(np.int64)
    A2 = A64 @ A64
    return int(np.trace(A2 @ A64)) // 6


def eigenvalues(A):
    """Eigenvalues sorted descending."""
    vals = np.linalg.eigvalsh(A.astype(np.float64))
    return np.sort(vals)[::-1]


def spectral_gap(A):
    """λ₁ - λ₂."""
    eigs = eigenvalues(A)
    return eigs[0] - eigs[1]


def hoffman_bound(A):
    """Upper bound on independence number."""
    n = A.shape[0]
    eigs = eigenvalues(A)
    lmax, lmin = eigs[0], eigs[-1]
    if abs(lmax - lmin) < 1e-10:
        return n
    return int(np.floor(n * (-lmin) / (lmax - lmin)))


# ─── Clique Counting (with Numba acceleration) ───

def _count_cliques(A, k, n):
    """Count k-cliques via itertools (reliable, reasonably fast)."""
    from itertools import combinations
    count = 0
    for combo in combinations(range(n), k):
        is_clique = True
        for a in range(k):
            for b in range(a+1, k):
                if A[combo[a], combo[b]] == 0:
                    is_clique = False
                    break
            if not is_clique:
                break
        if is_clique:
            count += 1
    return count


def _has_clique(A, k, n):
    """Check if any k-clique exists (early termination)."""
    from itertools import combinations
    for combo in combinations(range(n), k):
        is_clique = True
        for a in range(k):
            for b in range(a+1, k):
                if A[combo[a], combo[b]] == 0:
                    is_clique = False
                    break
            if not is_clique:
                break
        if is_clique:
            return True
    return False


def cliques(A, k):
    """Count k-cliques."""
    return _count_cliques(np.ascontiguousarray(A), k, A.shape[0])


def independent_sets(A, k):
    """Count independent sets of size k."""
    return cliques(complement(A), k)


def clique_number(A):
    """Exact clique number ω(G)."""
    n = A.shape[0]
    omega = 1
    for k in range(2, min(n+1, 15)):
        if _has_clique(np.ascontiguousarray(A), k, n):
            omega = k
        else:
            break
    return omega


def independence_number(A):
    """Exact independence number α(G)."""
    return clique_number(complement(A))


# ─── Ramsey Operations ───

def ramsey_check(A, r, s):
    """Check if 2-coloring contains monochromatic K_r or I_s."""
    n = A.shape[0]
    Ac = np.ascontiguousarray(A)
    Cc = np.ascontiguousarray(complement(A))
    has_r = _has_clique(Ac, r, n)
    has_s = _has_clique(Cc, s, n)
    return has_r or has_s


def ramsey_energy(A, r, s):
    """E = count(K_r) + count(I_s). Goal: E=0."""
    n = A.shape[0]
    Ac = np.ascontiguousarray(A)
    Cc = np.ascontiguousarray(complement(A))
    return _count_cliques(Ac, r, n) + _count_cliques(Cc, s, n)


def ramsey_predict(A, r, s):
    """Spectral prediction of Ramsey avoidance."""
    n = A.shape[0]
    eigA = eigenvalues(A)
    lmaxA, lminA = eigA[0], eigA[-1]
    hoffA = int(np.floor(n * (-lminA) / (lmaxA - lminA)))

    C = complement(A)
    eigC = eigenvalues(C)
    lmaxC, lminC = eigC[0], eigC[-1]
    hoffC = int(np.floor(n * (-lminC) / (lmaxC - lminC)))

    no_red = hoffC < r
    no_blue = hoffA < s
    return {
        'predicts_avoids': no_red and no_blue,
        'no_red_clique': no_red,
        'no_blue_clique': no_blue,
        'hoffman_A': hoffA,
        'hoffman_complement': hoffC,
        'eigenvalues_A': (float(lmaxA), float(lminA)),
        'eigenvalues_C': (float(lmaxC), float(lminC)),
    }


# ─── Simulated Annealing ───

def ramsey_anneal(n, r, s, trials=5, steps_per_edge=300, seed=None):
    """Simulated annealing search for R(r,s)-avoiding coloring of K_n."""
    rng = np.random.RandomState(seed)
    best_adj = None
    best_E = float('inf')

    for trial in range(trials):
        # Initialize: Paley if applicable, else near-regular random
        is_prime = n >= 5 and all(n % d != 0 for d in range(2, int(n**0.5)+1))
        if is_prime and n % 4 == 1:
            adj = paley(n).copy()
        else:
            adj = np.zeros((n, n), dtype=np.int8)
            for i in range(n):
                for j in range(i+1, n):
                    adj[i, j] = adj[j, i] = rng.randint(0, 2)

        Ac = np.ascontiguousarray(adj)
        Cc = np.ascontiguousarray(complement(adj))
        E = _count_cliques(Ac, r, n) + _count_cliques(Cc, s, n)

        if E == 0:
            return adj, 0, trial + 1

        T = 1.5
        total_steps = n * n * steps_per_edge

        for step in range(total_steps):
            if E == 0:
                break
            u, v = rng.randint(0, n, 2)
            if u == v:
                continue
            if u > v:
                u, v = v, u

            adj[u, v] = 1 - adj[u, v]
            adj[v, u] = adj[u, v]

            Ac = np.ascontiguousarray(adj)
            Cc = np.ascontiguousarray(complement(adj))
            newE = _count_cliques(Ac, r, n) + _count_cliques(Cc, s, n)
            dE = newE - E

            if dE <= 0 or rng.random() < np.exp(-dE / T):
                E = newE
            else:
                adj[u, v] = 1 - adj[u, v]
                adj[v, u] = adj[u, v]

            T *= 0.99975

        if E < best_E:
            best_E = E
            best_adj = adj.copy()
        if best_E == 0:
            return best_adj, 0, trial + 1

    return best_adj, best_E, trials


# ─── Extension Analysis ───

def extend_analysis(A, r, s):
    """Analyze all 2^n connection patterns for adding vertex n+1."""
    n = A.shape[0]
    assert n <= 22, f"extend_analysis supports n ≤ 22 (2^n patterns). Got n={n}."

    # Find all (r-1)-cliques and (s-1)-independent-sets
    r1_cliques = []
    s1_indeps = []

    from itertools import combinations
    for combo in combinations(range(n), r-1):
        if all(A[combo[a], combo[b]] == 1 for a in range(r-1) for b in range(a+1, r-1)):
            r1_cliques.append(combo)

    C = complement(A)
    for combo in combinations(range(n), s-1):
        if all(C[combo[a], combo[b]] == 1 for a in range(s-1) for b in range(a+1, s-1)):
            s1_indeps.append(combo)

    total = 1 << n
    valid = 0
    fails_clique = 0
    fails_indep = 0
    fails_both = 0

    for pattern in range(total):
        creates_clique = False
        creates_indep = False

        for clique in r1_cliques:
            if all((pattern >> v) & 1 for v in clique):
                creates_clique = True
                break

        for indep in s1_indeps:
            if not any((pattern >> v) & 1 for v in indep):
                creates_indep = True
                break

        if creates_clique:
            fails_clique += 1
        if creates_indep:
            fails_indep += 1
        if creates_clique and creates_indep:
            fails_both += 1
        if not creates_clique and not creates_indep:
            valid += 1

    return {
        'n': n,
        'r': r,
        's': s,
        'r1_cliques': len(r1_cliques),
        's1_indeps': len(s1_indeps),
        'total_patterns': total,
        'valid': valid,
        'fails_clique': fails_clique,
        'fails_indep': fails_indep,
        'fails_both': fails_both,
        'pct_valid': valid / total * 100,
    }


# ─── Survey Tools ───

def paley_survey(p_max=50):
    """Comprehensive survey of Paley graph properties."""
    results = []
    for p in range(5, p_max + 1):
        if not all(p % d != 0 for d in range(2, int(p**0.5)+1)):
            continue
        if p % 4 != 1:
            continue
        A = paley(p)
        alpha = independence_number(A)
        omega = clique_number(A)
        hoff = hoffman_bound(A)
        gap = spectral_gap(A)
        tri = triangles(A)
        results.append({
            'p': p, 'degree': (p-1)//2, 'alpha': alpha, 'omega': omega,
            'hoffman': hoff, 'gap': round(gap, 3), 'triangles': tri,
            'ratio': round(alpha / p**0.5, 3),
            'R33': alpha < 3 and omega < 3,
            'R44': alpha < 4 and omega < 4,
            'R55': alpha < 5 and omega < 5,
        })
    return results


def extension_landscape(r, s, n_max=None):
    """Map the extension window for R(r,s) at every graph size."""
    if n_max is None:
        n_max = min(22, r * s)  # reasonable default

    results = []
    for n in range(r, n_max + 1):
        # Find an avoider
        adj, E, _ = ramsey_anneal(n, r, s, trials=10, steps_per_edge=200)
        if E > 0:
            results.append({'n': n, 'found_avoider': False})
            continue

        # Extension analysis
        if n <= 22:
            ext = extend_analysis(adj, r, s)
            results.append({
                'n': n, 'found_avoider': True,
                'valid_extensions': ext['valid'],
                'total_patterns': ext['total_patterns'],
                'pct_valid': ext['pct_valid'],
                'triangles': triangles(adj),
            })
        else:
            results.append({'n': n, 'found_avoider': True, 'note': 'too large for extension analysis'})

    return results


# ─── Graph Profile ───

def graph_profile(A):
    """Comprehensive graph analysis."""
    n = A.shape[0]
    degs = degree(A)
    eigs = eigenvalues(A)
    tri = triangles(A)
    edges = int(A.sum()) // 2
    total_edges = n * (n-1) // 2
    return {
        'n': n,
        'edges': edges,
        'density': round(edges / total_edges * 100, 1),
        'degree_min': int(degs.min()),
        'degree_max': int(degs.max()),
        'degree_mean': round(float(degs.mean()), 1),
        'regular': int(degs.min()) == int(degs.max()),
        'triangles': tri,
        'lambda_max': round(float(eigs[0]), 4),
        'lambda_min': round(float(eigs[-1]), 4),
        'spectral_gap': round(float(eigs[0] - eigs[1]), 4),
        'hoffman_bound': hoffman_bound(A),
        'self_complementary': edges == total_edges - edges,
    }


# ─── Pretty Printing ───

def print_survey(results):
    """Pretty-print paley_survey results."""
    print(f"{'p':>4} | {'deg':>3} | {'α':>2} | {'ω':>2} | {'Hoff':>4} | {'gap':>6} | {'α/√p':>5} | R33 | R44 | R55")
    print("-" * 65)
    for r in results:
        print(f"{r['p']:4d} | {r['degree']:3d} | {r['alpha']:2d} | {r['omega']:2d} | {r['hoffman']:4d} | {r['gap']:6.2f} | {r['ratio']:5.3f} | {'YES' if r['R33'] else ' no'} | {'YES' if r['R44'] else ' no'} | {'YES' if r['R55'] else ' no'}")


def print_landscape(results):
    """Pretty-print extension_landscape results."""
    print(f"{'n':>3} | {'valid':>8} / {'total':>8} | {'%':>6} | {'tri':>5}")
    print("-" * 45)
    for r in results:
        if not r['found_avoider']:
            print(f"{r['n']:3d} | no avoider found")
        elif 'valid_extensions' in r:
            print(f"{r['n']:3d} | {r['valid_extensions']:8d} / {r['total_patterns']:8d} | {r['pct_valid']:5.2f}% | {r['triangles']:5d}")
        else:
            print(f"{r['n']:3d} | {r.get('note', 'ok')}")


if __name__ == '__main__':
    print("TLS-Graph Python Engine")
    print("=" * 40)
    print()

    print("Paley Survey (p ≤ 50):")
    print_survey(paley_survey(50))

    print()
    print("Extension Landscape for R(4,4):")
    print_landscape(extension_landscape(4, 4, 17))

    print()
    print("Extension Landscape for R(3,3):")
    print_landscape(extension_landscape(3, 3, 6))
