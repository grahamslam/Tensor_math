"""
R(5,5) Circulant Search -- inspired by AlphaEvolve (Algorithm 5).

Key insight: restrict search to circulant graphs defined by a difference set S.
Edge (u,v) exists iff |u-v| mod n is in S.

Advantages:
- Search space: 2^(n/2) difference sets vs 2^(n*(n-1)/2) general graphs
- Vertex-transitive: only need to check clique/indep-set constraints at vertex 0
- K5-free iff no K4 in subgraph induced by neighborhood S
- I5-free iff no I4 in subgraph induced by non-neighborhood

For n=43: search space = 2^21 = ~2M vs 2^903 general. Exhaustive is feasible!

Writes progress to progress.jsonl for dashboard.
"""
import numpy as np
import time
import sys
import json
import os
from itertools import combinations

sys.stdout.reconfigure(line_buffering=True)

PROGRESS_FILE = "progress.jsonl"
RESULTS_FILE = "results.json"


def save_result(n, adj, method, diff_set=None, elapsed=0, phases=None):
    """Save a verified R(5,5) avoider with full metadata."""
    from datetime import datetime

    # Load existing results
    results = []
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r') as f:
            results = json.load(f)

    degs = adj.sum(axis=1)
    edges = int(adj.sum()) // 2
    total = n * (n - 1) // 2

    entry = {
        'n': n,
        'r': 5,
        's': 5,
        'verified': True,
        'method': method,
        'timestamp': datetime.now().isoformat(),
        'edges': edges,
        'total_possible_edges': total,
        'density': round(edges / total, 4),
        'degree_min': int(degs.min()),
        'degree_max': int(degs.max()),
        'degree_mean': round(float(degs.mean()), 2),
        'degree_variance': round(float(np.var(degs)), 2),
        'elapsed_seconds': round(elapsed, 1),
        'phases': phases or {},
        'npy_file': f'r55_n{n}_verified.npy',
    }

    if diff_set is not None:
        base_diffs = sorted([d for d in diff_set if d <= n // 2])
        entry['difference_set'] = base_diffs
        entry['is_circulant'] = True
    else:
        entry['is_circulant'] = False

    # Store adjacency as list-of-lists for portability
    entry['adjacency'] = adj.tolist()

    # Check if we already have this n, replace if so
    results = [r for r in results if r['n'] != n]
    results.append(entry)
    results.sort(key=lambda r: r['n'])

    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2)

    np.save(f'r55_n{n}_verified.npy', adj)
    print(f"  Saved to {RESULTS_FILE} and r55_n{n}_verified.npy")


def log_progress(data):
    with open(PROGRESS_FILE, 'a') as f:
        f.write(json.dumps(data) + '\n')


def make_circulant(n, diff_set):
    """Build circulant graph from difference set."""
    A = np.zeros((n, n), dtype=np.int8)
    for i in range(n):
        for d in diff_set:
            j = (i + d) % n
            if j != i:
                A[i, j] = 1
                A[j, i] = 1
    return A


def count_cliques_through_pair(A, u, v, k, n):
    """Count k-cliques containing BOTH u and v."""
    if A[u, v] == 0:
        return 0
    others = [w for w in range(n) if w != u and w != v]
    count = 0
    for combo in combinations(others, k - 2):
        all_ok = True
        for w in combo:
            if A[u, w] == 0 or A[v, w] == 0:
                all_ok = False
                break
        if not all_ok:
            continue
        is_clique = True
        for a in range(k - 2):
            for b in range(a + 1, k - 2):
                if A[combo[a], combo[b]] == 0:
                    is_clique = False
                    break
            if not is_clique:
                break
        if is_clique:
            count += 1
    return count


def check_clique_at_vertex(A, v, k, n):
    """Check if vertex v participates in a k-clique. Returns count."""
    neighbors = [w for w in range(n) if A[v, w] == 1]
    count = 0
    for combo in combinations(neighbors, k - 1):
        is_clique = True
        for a in range(k - 1):
            for b in range(a + 1, k - 1):
                if A[combo[a], combo[b]] == 0:
                    is_clique = False
                    break
            if not is_clique:
                break
        if is_clique:
            count += 1
    return count


def check_indep_at_vertex(A, v, k, n):
    """Check if vertex v participates in a k-independent-set. Returns count."""
    non_neighbors = [w for w in range(n) if w != v and A[v, w] == 0]
    count = 0
    for combo in combinations(non_neighbors, k - 1):
        is_indep = True
        for a in range(k - 1):
            for b in range(a + 1, k - 1):
                if A[combo[a], combo[b]] == 1:
                    is_indep = False
                    break
            if not is_indep:
                break
        if is_indep:
            count += 1
    return count


def vertex_transitive_energy(n, diff_set):
    """For circulant graphs, check constraints at vertex 0 only.
    K5-free iff no K4 among neighbors of 0.
    I5-free iff no I4 among non-neighbors of 0.
    Returns (k5_count_at_0, i5_count_at_0) -- multiply by n/k for total."""
    A = make_circulant(n, diff_set)
    k5 = check_clique_at_vertex(A, 0, 5, n)
    i5 = check_indep_at_vertex(A, 0, 5, n)
    return k5, i5, A


def full_count(A, k, n):
    """Count k-cliques in graph A."""
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


def full_verify(A, n):
    """Full verification across all vertices."""
    from itertools import combinations
    k5 = 0
    for combo in combinations(range(n), 5):
        ok = True
        for a in range(5):
            for b in range(a + 1, 5):
                if A[combo[a], combo[b]] == 0:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            k5 += 1

    C = 1 - A.copy()
    np.fill_diagonal(C, 0)
    i5 = 0
    for combo in combinations(range(n), 5):
        ok = True
        for a in range(5):
            for b in range(a + 1, 5):
                if C[combo[a], combo[b]] == 0:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            i5 += 1

    return k5, i5


def orbit_search(n, r, s, max_trials=500000):
    """Search over difference sets using orbit-based SA.

    Difference set S must be symmetric: if d in S, then n-d in S.
    So we only choose from {1, 2, ..., n//2} and auto-include n-d.
    For odd n, d=n//2 doesn't exist, so half = (n-1)//2 choices.
    Search space: 2^half.
    """
    half = n // 2
    rng = np.random.RandomState()

    best_E = float('inf')
    best_diff = None
    best_adj = None

    # Target degree: ~(n-1)/2 for balanced graph
    target_size = half // 2  # number of base differences (each adds ~2 to degree)

    t0 = time.time()
    last_log = time.time()
    last_report = time.time()

    # Phase 1: Random sampling to find good starting point
    print(f"  Phase 1: Random sampling (n={n}, half={half}, 2^{half} = {2**half:.0e} space)")

    for trial in range(min(max_trials, 200000)):
        # Random difference set with target density
        num_diffs = target_size + rng.randint(-3, 4)
        num_diffs = max(3, min(num_diffs, half))
        base_diffs = rng.choice(range(1, half + 1), size=num_diffs, replace=False)

        diff_set = set()
        for d in base_diffs:
            diff_set.add(int(d))
            diff_set.add(int(n - d))

        k5, i5, A = vertex_transitive_energy(n, diff_set)
        E = k5 + i5

        if E < best_E:
            best_E = E
            best_diff = diff_set.copy()
            best_adj = A.copy()
            if E == 0:
                print(f"    FOUND at trial {trial}! E=0")
                return best_adj, best_diff, 0, trial

        now = time.time()
        if now - last_log >= 2.0:
            log_progress({
                'time': round(now - t0, 1),
                'wall': round(now, 1),
                'n': n,
                'trial': 1,
                'step': trial,
                'max_steps': max_trials,
                'pct': round(trial / max_trials * 100, 1),
                'E': E,
                'best_E': best_E,
                'T': 0,
                'accept_rate': 0,
                'deg_var': 0,
                'tri_G': 0, 'tri_C': 0,
                'k5': k5, 'i5': i5,
                'k4': 0, 'i4': 0,
                'violation': E,
                'near_viol': 0,
                'regularity': 0, 'balance': 0,
            })
            last_log = now

        if now - last_report > 15:
            rate = trial / max(now - t0, 0.1)
            print(f"    trial {trial} best_E={best_E} {rate:.0f} trials/s", flush=True)
            last_report = now

    elapsed = time.time() - t0
    print(f"  Phase 1 done: best_E={best_E} [{elapsed:.1f}s]")

    if best_E == 0:
        return best_adj, best_diff, 0, max_trials

    # Phase 2: SA on difference set (flip individual differences in/out)
    print(f"\n  Phase 2: SA on difference set (best_E={best_E})")

    # Convert best_diff to a bit vector over {1..half}
    bits = np.zeros(half + 1, dtype=np.int8)  # bits[d] = 1 if d is in base set
    for d in best_diff:
        if d <= half:
            bits[d] = 1

    max_sa_steps = half * 5000
    T = 1.5
    cooling = 1.0 - 4.0 / max_sa_steps
    t0_sa = time.time()
    sa_best_E = best_E

    for step in range(max_sa_steps):
        # Flip a random base difference
        d = rng.randint(1, half + 1)
        bits[d] = 1 - bits[d]

        # Reconstruct difference set
        diff_set = set()
        for dd in range(1, half + 1):
            if bits[dd]:
                diff_set.add(dd)
                diff_set.add(n - dd)

        if len(diff_set) < 6 or len(diff_set) > n - 6:
            bits[d] = 1 - bits[d]  # undo -- too sparse/dense
            continue

        k5, i5, A = vertex_transitive_energy(n, diff_set)
        E_new = k5 + i5
        dE = E_new - best_E

        if dE <= 0 or rng.random() < np.exp(-dE / max(T, 0.01)):
            best_E = E_new
            if E_new < sa_best_E:
                sa_best_E = E_new
                best_diff = diff_set.copy()
                best_adj = A.copy()
            if E_new == 0:
                print(f"    SA FOUND at step {step}! E=0")
                return best_adj, best_diff, 0, step
        else:
            bits[d] = 1 - bits[d]  # undo

        T *= cooling

        now = time.time()
        if now - last_log >= 2.0:
            log_progress({
                'time': round(now - t0, 1),
                'wall': round(now, 1),
                'n': n,
                'trial': 2,
                'step': step,
                'max_steps': max_sa_steps,
                'pct': round(step / max_sa_steps * 100, 1),
                'E': E_new,
                'best_E': sa_best_E,
                'T': round(T, 6),
                'accept_rate': 0,
                'deg_var': 0,
                'tri_G': 0, 'tri_C': 0,
                'k5': k5, 'i5': i5,
                'k4': 0, 'i4': 0,
                'violation': E_new,
                'near_viol': 0,
                'regularity': 0, 'balance': 0,
            })
            last_log = now

        if now - last_report > 15:
            rate = step / max(now - t0_sa, 0.1)
            print(f"    SA step {step}/{max_sa_steps} E={best_E} best={sa_best_E} "
                  f"T={T:.4f} {rate:.0f}st/s", flush=True)
            last_report = now

    elapsed = time.time() - t0
    print(f"  Phase 2 done: best_E={sa_best_E} [{time.time()-t0_sa:.1f}s]")

    if sa_best_E == 0:
        return best_adj, best_diff, 0, max_trials

    # Phase 3: Break symmetry -- multi-restart edge SA from best circulant
    # LOW temperature (we're close), fresh restart each time from circulant seed
    print(f"\n  Phase 3: Multi-restart edge SA (seed E_vt={sa_best_E})")

    circulant_seed = best_adj.copy()
    comp_seed = 1 - circulant_seed.copy()
    np.fill_diagonal(comp_seed, 0)
    seed_full_E = full_count(circulant_seed, 5, n) + full_count(comp_seed, 5, n)
    print(f"    Full energy of circulant seed: E={seed_full_E}")

    phase3_best_E = seed_full_E
    phase3_best_adj = circulant_seed.copy()
    t0_p3 = time.time()

    num_restarts = 15
    steps_per_restart = n * n * 200

    for restart in range(num_restarts):
        adj = circulant_seed.copy()
        comp = 1 - adj.copy()
        np.fill_diagonal(comp, 0)
        E = seed_full_E

        # Low temp -- don't scramble, just nudge
        T = 0.3
        cooling = 1.0 - 6.0 / steps_per_restart

        for step in range(steps_per_restart):
            u = rng.randint(0, n)
            v = rng.randint(0, n)
            if u == v:
                continue
            if u > v:
                u, v = v, u

            before_G = count_cliques_through_pair(adj, u, v, 5, n) if adj[u, v] == 1 else 0
            before_C = count_cliques_through_pair(comp, u, v, 5, n) if comp[u, v] == 1 else 0

            adj[u, v] = 1 - adj[u, v]
            adj[v, u] = adj[u, v]
            comp[u, v] = 1 - comp[u, v]
            comp[v, u] = comp[u, v]

            after_G = count_cliques_through_pair(adj, u, v, 5, n) if adj[u, v] == 1 else 0
            after_C = count_cliques_through_pair(comp, u, v, 5, n) if comp[u, v] == 1 else 0

            dE = (after_G + after_C) - (before_G + before_C)
            newE = E + dE

            if dE <= 0 or rng.random() < np.exp(-dE / max(T, 0.005)):
                E = newE
                if E <= 0:
                    real_E = full_count(adj, 5, n) + full_count(comp, 5, n)
                    if real_E == 0:
                        print(f"    FOUND! restart={restart} step={step} [{time.time()-t0_p3:.1f}s]")
                        return adj, None, 0, step
                    else:
                        E = real_E
                elif E < phase3_best_E:
                    phase3_best_E = E
                    phase3_best_adj = adj.copy()
            else:
                adj[u, v] = 1 - adj[u, v]
                adj[v, u] = adj[u, v]
                comp[u, v] = 1 - comp[u, v]
                comp[v, u] = comp[u, v]

            T *= cooling

            if step > 0 and step % 5000 == 0:
                real_E = full_count(adj, 5, n) + full_count(comp, 5, n)
                if real_E != E:
                    E = real_E

            now = time.time()
            if now - last_log >= 2.0:
                global_step = restart * steps_per_restart + step
                total_steps = num_restarts * steps_per_restart
                log_progress({
                    'time': round(now - t0, 1), 'wall': round(now, 1),
                    'n': n, 'trial': 3,
                    'step': global_step, 'max_steps': total_steps,
                    'pct': round(global_step / total_steps * 100, 1),
                    'E': E, 'best_E': phase3_best_E,
                    'T': round(T, 6), 'accept_rate': 0, 'deg_var': 0,
                    'tri_G': 0, 'tri_C': 0,
                    'k5': E, 'i5': 0, 'k4': 0, 'i4': 0,
                    'violation': E, 'near_viol': 0,
                    'regularity': 0, 'balance': 0,
                })
                last_log = now

            if now - last_report > 20:
                rate = step / max(now - t0_p3, 0.1) if restart == 0 else (restart * steps_per_restart + step) / max(now - t0_p3, 0.1)
                print(f"    R{restart} step {step}/{steps_per_restart} E={E} best={phase3_best_E} "
                      f"T={T:.4f} {rate:.0f}st/s", flush=True)
                last_report = now

        print(f"    Restart {restart}: final E={E} best_overall={phase3_best_E}", flush=True)

    print(f"  Phase 3 done: best_E={phase3_best_E} [{time.time()-t0_p3:.1f}s]")

    if phase3_best_E < sa_best_E:
        return phase3_best_adj, None, phase3_best_E, max_trials
    return best_adj, best_diff, sa_best_E, max_trials


if __name__ == '__main__':
    print("R(5,5) Circulant Search -- AlphaEvolve-inspired")
    print("=" * 60)

    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

    # First verify Paley(37) as circulant
    print("\nVerifying Paley(37) as circulant baseline...")
    qr37 = set()
    for x in range(1, 37):
        qr37.add((x * x) % 37)
    k5, i5, A37 = vertex_transitive_energy(37, qr37)
    print(f"  Paley(37): K5_at_0={k5} I5_at_0={i5} -> {'CLEAN' if k5+i5==0 else 'VIOLATIONS'}")

    for target_n in range(39, 44):
        print(f"\n{'='*60}")
        print(f"Target: n={target_n} (search space: 2^{target_n//2})")
        print(f"{'='*60}")

        t0 = time.time()
        adj, diff, E, iters = orbit_search(target_n, 5, 5)

        if E == 0:
            # Vertex-transitive check passed, now full verify
            print(f"\n  Vertex-transitive check passed! Full verification...")
            kr, is_ = full_verify(adj, target_n)
            edges = int(adj.sum()) // 2
            total = target_n * (target_n - 1) // 2
            degs = adj.sum(axis=1)
            print(f"  Full: K5={kr} I5={is_} edges={edges}/{total} ({edges/total*100:.1f}%)")
            print(f"  Degree: {int(degs.min())}-{int(degs.max())} (uniform={int(degs[0])})")

            if kr + is_ == 0:
                print(f"\n  ** VERIFIED R(5,5) avoider at n={target_n}! **")
                method = "circulant" if diff is not None else "hybrid(circulant+edge_SA)"
                if diff:
                    base_diffs = sorted([d for d in diff if d <= target_n // 2])
                    print(f"  Difference set: {base_diffs}")
                save_result(target_n, adj, method=method, diff_set=diff,
                           elapsed=time.time() - t0,
                           phases={'phase1_trials': iters})
            else:
                print(f"  VT check was wrong -- full count found violations")
        else:
            print(f"\n  Best circulant E={E} at n={target_n}")
            if E > 50:
                print(f"  Too many violations, trying next n anyway...")

        print(f"  Time: {time.time()-t0:.1f}s")

    print("\nDone.")
