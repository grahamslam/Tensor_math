"""
R(5,5) Smart Search — extension-guided growth from Paley(37).

Strategy:
1. Start from Paley(37) (known R(5,5) avoider)
2. Find valid extensions to n=38 via extend_analysis
3. Pick the best extension (lowest degree variance → best spectral properties)
4. Light SA on the 38-vertex graph to clean up any violations
5. Repeat: extend to 39, 40, 41, 42
"""
import numpy as np
import time
import sys
from itertools import combinations

sys.stdout.reconfigure(line_buffering=True)


def paley(p):
    qr = set()
    for x in range(1, p):
        qr.add((x * x) % p)
    A = np.zeros((p, p), dtype=np.int8)
    for i in range(p):
        for j in range(p):
            if i != j and (j - i) % p in qr:
                A[i, j] = 1
    return A


def complement(A):
    n = A.shape[0]
    C = 1 - A.copy()
    np.fill_diagonal(C, 0)
    return C.astype(np.int8)


def full_count(A, k, n):
    count = 0
    for combo in combinations(range(n), k):
        ok = True
        for a in range(k):
            for b in range(a + 1, k):
                if A[combo[a], combo[b]] == 0:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            count += 1
    return count


def energy(A, r, s):
    n = A.shape[0]
    C = complement(A)
    return full_count(A, r, n) + full_count(C, s, n)


def degree_variance(A):
    degs = A.sum(axis=1).astype(float)
    return float(np.var(degs))


def find_valid_extensions(A, r, s, max_check=None):
    """Find all valid connection patterns for adding one vertex."""
    n = A.shape[0]
    C = complement(A)

    # Find (r-1)-cliques and (s-1)-independent-sets
    r1_cliques = []
    for combo in combinations(range(n), r - 1):
        if all(A[combo[a], combo[b]] == 1 for a in range(r-1) for b in range(a+1, r-1)):
            r1_cliques.append(combo)

    s1_indeps = []
    for combo in combinations(range(n), s - 1):
        if all(C[combo[a], combo[b]] == 1 for a in range(s-1) for b in range(a+1, s-1)):
            s1_indeps.append(combo)

    print(f"    {len(r1_cliques)} existing {r-1}-cliques, {len(s1_indeps)} existing {s-1}-indep-sets")

    total = 1 << n
    if max_check is not None and total > max_check:
        # Too many patterns — sample randomly
        return find_valid_extensions_sampled(A, r, s, r1_cliques, s1_indeps, max_check)

    valid_patterns = []
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

        if not creates_clique and not creates_indep:
            valid_patterns.append(pattern)

    return valid_patterns


def find_valid_extensions_sampled(A, r, s, r1_cliques, s1_indeps, num_samples):
    """Sample random connection patterns and test validity."""
    n = A.shape[0]
    rng = np.random.RandomState()
    valid = []
    target_deg = n // 2  # aim for ~50% density

    for _ in range(num_samples):
        # Biased random: target degree near n/2
        pattern = 0
        for bit in range(n):
            if rng.random() < target_deg / n:
                pattern |= (1 << bit)

        creates_clique = False
        creates_indep = False

        for clique in r1_cliques:
            if all((pattern >> bit) & 1 for bit in clique):
                creates_clique = True
                break

        for indep in s1_indeps:
            if not any((pattern >> bit) & 1 for bit in indep):
                creates_indep = True
                break

        if not creates_clique and not creates_indep:
            valid.append(pattern)

    return valid


def extend_graph(A, pattern):
    """Add a vertex to graph A with the given connection pattern."""
    n = A.shape[0]
    new_A = np.zeros((n + 1, n + 1), dtype=np.int8)
    new_A[:n, :n] = A
    for j in range(n):
        if (pattern >> j) & 1:
            new_A[n, j] = 1
            new_A[j, n] = 1
    return new_A


def pick_best_extension(A, valid_patterns, r, s, top_k=20):
    """Pick the extension with lowest degree variance (most regular)."""
    n = A.shape[0]
    target_deg = n // 2

    scored = []
    for pattern in valid_patterns[:min(len(valid_patterns), 1000)]:
        deg = bin(pattern).count('1')
        # Score: prefer degree close to n/2, minimize variance
        deg_diff = abs(deg - target_deg)
        scored.append((deg_diff, pattern))

    scored.sort()

    # Among top candidates, pick the one with lowest degree variance after extension
    best_var = float('inf')
    best_pattern = scored[0][1]

    for _, pattern in scored[:top_k]:
        new_A = extend_graph(A, pattern)
        var = degree_variance(new_A)
        if var < best_var:
            best_var = var
            best_pattern = pattern

    return best_pattern, best_var


def light_sa(A, r, s, max_steps=None):
    """Light simulated annealing to clean up any violations."""
    n = A.shape[0]
    adj = A.copy()
    if max_steps is None:
        max_steps = n * n * 100

    rng = np.random.RandomState()
    E = energy(adj, r, s)

    if E == 0:
        return adj, 0

    T = 1.0
    cooling = 1.0 - 5.0 / max_steps

    for step in range(max_steps):
        u, v = rng.randint(0, n, 2)
        if u == v:
            continue
        if u > v:
            u, v = v, u

        adj[u, v] = 1 - adj[u, v]
        adj[v, u] = adj[u, v]

        newE = energy(adj, r, s)
        dE = newE - E

        if dE <= 0 or rng.random() < np.exp(-dE / max(T, 0.01)):
            E = newE
            if E == 0:
                return adj, 0
        else:
            adj[u, v] = 1 - adj[u, v]
            adj[v, u] = adj[u, v]

        T *= cooling

    return adj, E


def circulant_search(n, r, s, max_trials=50000):
    """Search circulant graphs on n vertices for R(r,s) avoidance."""
    half = n // 2
    best_adj = None
    best_E = float('inf')
    rng = np.random.RandomState()

    for trial in range(max_trials):
        # Random difference set targeting ~50% density
        S = set()
        target = half // 2 + rng.randint(-2, 3)
        diffs = rng.choice(range(1, half + 1), size=min(target, half), replace=False)
        for d in diffs:
            S.add(d)
            S.add(n - d)

        adj = np.zeros((n, n), dtype=np.int8)
        for i in range(n):
            for j in range(n):
                if i != j and (j - i) % n in S:
                    adj[i, j] = 1

        E = energy(adj, r, s)
        if E < best_E:
            best_E = E
            best_adj = adj.copy()
            if E == 0:
                return best_adj, 0, trial + 1

        if trial % 10000 == 0 and trial > 0:
            print(f"      circulant trial {trial}: best E={best_E}")

    return best_adj, best_E, max_trials


if __name__ == '__main__':
    print("R(5,5) Smart Search — Extension-Guided Growth")
    print("=" * 60)
    r, s = 5, 5

    # Start from Paley(37)
    A = paley(37)
    print(f"\nBase: Paley(37), E={energy(A, r, s)}, alpha={37}")
    print(f"  edges={int(A.sum())//2}/{37*36//2} density=50.0%")

    current = A

    for target_n in range(38, 43):
        n = current.shape[0]
        print(f"\n{'='*60}")
        print(f"Extending n={n} -> n={target_n}")
        print(f"{'='*60}")

        t0 = time.time()

        # Strategy 1: Try extension analysis (if feasible)
        if n <= 22:
            print(f"  Strategy 1: Exhaustive extension analysis")
            valid = find_valid_extensions(current, r, s)
            print(f"    Found {len(valid)} valid extensions")
        else:
            print(f"  Strategy 1: Sampled extension analysis (n={n} too large for exhaustive)")
            # Find cliques/indeps for sampling
            C = complement(current)
            r1_cliques = []
            for combo in combinations(range(n), r - 1):
                if all(current[combo[a], combo[b]] == 1 for a in range(r-1) for b in range(a+1, r-1)):
                    r1_cliques.append(combo)
            s1_indeps = []
            for combo in combinations(range(n), s - 1):
                if all(C[combo[a], combo[b]] == 1 for a in range(s-1) for b in range(a+1, s-1)):
                    s1_indeps.append(combo)
            print(f"    {len(r1_cliques)} 4-cliques, {len(s1_indeps)} 4-indep-sets")

            valid = find_valid_extensions_sampled(current, r, s, r1_cliques, s1_indeps, 500000)
            print(f"    Found {len(valid)} valid extensions in 500K samples")

        if len(valid) > 0:
            pattern, var = pick_best_extension(current, valid, r, s)
            new_A = extend_graph(current, pattern)
            E = energy(new_A, r, s)
            deg = bin(pattern).count('1')
            print(f"    Best extension: degree={deg}, variance={var:.2f}, E={E}")

            if E == 0:
                print(f"    CLEAN EXTENSION to n={target_n}!")
                current = new_A
            else:
                print(f"    Extension has E={E}, applying light SA...")
                cleaned, final_E = light_sa(new_A, r, s, max_steps=target_n*target_n*200)
                print(f"    After SA: E={final_E}")
                if final_E == 0:
                    print(f"    SUCCESS at n={target_n}!")
                    current = cleaned
                else:
                    print(f"    SA didn't reach E=0, trying Strategy 2...")
                    # Fall through to circulant
                    valid = []

        if len(valid) == 0:
            print(f"  Strategy 2: Circulant search at n={target_n}")
            circ, circ_E, trials = circulant_search(target_n, r, s, max_trials=100000)
            print(f"    Best circulant: E={circ_E} (after {trials} trials)")

            if circ_E == 0:
                print(f"    CIRCULANT FOUND at n={target_n}!")
                current = circ
            elif circ_E < 10:
                print(f"    Near-miss circulant (E={circ_E}), applying SA...")
                cleaned, final_E = light_sa(circ, r, s, max_steps=target_n*target_n*300)
                print(f"    After SA: E={final_E}")
                if final_E == 0:
                    print(f"    SUCCESS at n={target_n}!")
                    current = cleaned
                else:
                    print(f"    Could not reach n={target_n}")
                    break
            else:
                print(f"    Could not reach n={target_n}")
                break

        elapsed = time.time() - t0
        print(f"  Time: {elapsed:.1f}s")

        # Verify and save
        final_E = energy(current, r, s)
        if final_E == 0:
            alpha_val = None
            # Quick alpha check
            C = complement(current)
            for k in range(5, 0, -1):
                if full_count(C, k, current.shape[0]) > 0:
                    alpha_val = k
                    break
            edges = int(current.sum()) // 2
            total = current.shape[0] * (current.shape[0] - 1) // 2
            print(f"\n  VERIFIED n={target_n}: E=0, alpha<={alpha_val}, edges={edges}/{total} ({edges/total*100:.1f}%)")
            np.save(f"r55_n{target_n}.npy", current)
            print(f"  Saved to r55_n{target_n}.npy")
        else:
            print(f"\n  FAILED at n={target_n}: E={final_E}")
            break

    print("\n" + "=" * 60)
    print(f"Reached n={current.shape[0]}")
    if current.shape[0] >= 43:
        print("MATCHED KNOWN R(5,5) LOWER BOUND!")
    elif current.shape[0] >= 38:
        print(f"Exceeded Paley frontier (37) by {current.shape[0]-37} vertices")
