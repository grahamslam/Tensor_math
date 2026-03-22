"""
R(5,5) Phase 3 only -- multi-restart low-temp edge SA from known best circulants.

Skips Phase 1/2 (we already know the best circulant difference sets).
Goes straight to symmetry-breaking edge flips.
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


def make_circulant(n, diff_set):
    A = np.zeros((n, n), dtype=np.int8)
    for i in range(n):
        for d in diff_set:
            j = (i + d) % n
            if j != i:
                A[i, j] = 1
                A[j, i] = 1
    return A


def count_cliques_through_pair(A, u, v, k, n):
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


def full_energy(A, n):
    C = 1 - A.copy()
    np.fill_diagonal(C, 0)
    return full_count(A, 5, n) + full_count(C, 5, n)


def save_result(n, adj, method, diff_set=None, elapsed=0, phases=None):
    from datetime import datetime
    results = []
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r') as f:
            results = json.load(f)
    degs = adj.sum(axis=1)
    edges = int(adj.sum()) // 2
    total = n * (n - 1) // 2
    entry = {
        'n': n, 'r': 5, 's': 5, 'verified': True, 'method': method,
        'timestamp': datetime.now().isoformat(),
        'edges': edges, 'total_possible_edges': total,
        'density': round(edges / total, 4),
        'degree_min': int(degs.min()), 'degree_max': int(degs.max()),
        'degree_mean': round(float(degs.mean()), 2),
        'degree_variance': round(float(np.var(degs)), 2),
        'elapsed_seconds': round(elapsed, 1),
        'phases': phases or {},
        'npy_file': f'r55_n{n}_verified.npy',
        'is_circulant': diff_set is not None,
        'adjacency': adj.tolist(),
    }
    if diff_set is not None:
        entry['difference_set'] = sorted([d for d in diff_set if d <= n // 2])
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


def phase3_search(n, seed_adj, num_restarts=20, steps_per_restart=None):
    """Multi-restart low-temp edge SA from a seed graph."""
    if steps_per_restart is None:
        steps_per_restart = n * n * 200

    rng = np.random.RandomState()
    comp_seed = 1 - seed_adj.copy()
    np.fill_diagonal(comp_seed, 0)
    seed_E = full_count(seed_adj, 5, n) + full_count(comp_seed, 5, n)
    print(f"  Seed full energy: E={seed_E}")

    if seed_E == 0:
        print(f"  Already clean!")
        return seed_adj, 0

    best_E = seed_E
    best_adj = seed_adj.copy()
    t0 = time.time()
    last_log = time.time()
    last_report = time.time()
    total_steps = num_restarts * steps_per_restart

    for restart in range(num_restarts):
        adj = seed_adj.copy()
        comp = 1 - adj.copy()
        np.fill_diagonal(comp, 0)
        E = seed_E

        T = 0.3
        cooling = 1.0 - 6.0 / steps_per_restart
        restart_best = E

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
                    real_E = full_energy(adj, n)
                    if real_E == 0:
                        print(f"  FOUND! restart={restart} step={step} [{time.time()-t0:.1f}s]")
                        return adj, 0
                    else:
                        E = real_E
                elif E < restart_best:
                    restart_best = E
                if E < best_E:
                    best_E = E
                    best_adj = adj.copy()
            else:
                adj[u, v] = 1 - adj[u, v]
                adj[v, u] = adj[u, v]
                comp[u, v] = 1 - comp[u, v]
                comp[v, u] = comp[u, v]

            T *= cooling

            if step > 0 and step % 5000 == 0:
                real_E = full_energy(adj, n)
                if real_E != E:
                    E = real_E

            now = time.time()
            if now - last_log >= 2.0:
                gs = restart * steps_per_restart + step
                log_progress({
                    'time': round(now - t0, 1), 'wall': round(now, 1),
                    'n': n, 'trial': restart + 1,
                    'step': gs, 'max_steps': total_steps,
                    'pct': round(gs / total_steps * 100, 1),
                    'E': E, 'best_E': best_E,
                    'T': round(T, 6), 'accept_rate': 0, 'deg_var': 0,
                    'tri_G': 0, 'tri_C': 0,
                    'k5': E, 'i5': 0, 'k4': 0, 'i4': 0,
                    'violation': E, 'near_viol': 0,
                    'regularity': 0, 'balance': 0,
                })
                last_log = now

            if now - last_report > 20:
                gs = restart * steps_per_restart + step
                rate = gs / max(now - t0, 0.1)
                print(f"    R{restart} step {step}/{steps_per_restart} E={E} "
                      f"best={best_E} T={T:.4f} {rate:.0f}st/s", flush=True)
                last_report = now

        print(f"  Restart {restart}: this_best={restart_best} overall_best={best_E}", flush=True)

    print(f"  Phase 3 done: best_E={best_E} [{time.time()-t0:.1f}s]")
    return best_adj, best_E


# Known best circulant difference sets from Phase 1/2
KNOWN_CIRCULANTS = {
    39: [2, 3, 6, 7, 8, 14, 15, 17, 18, 19],  # E_vt=5, full E~39
}


if __name__ == '__main__':
    print("R(5,5) Phase 3 -- Multi-restart Edge SA from Known Circulants")
    print("=" * 60)

    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

    for target_n in [39, 40, 41, 42, 43]:
        print(f"\n{'='*60}")
        print(f"Target: n={target_n}")
        print(f"{'='*60}")

        t0 = time.time()

        if target_n in KNOWN_CIRCULANTS:
            base_diffs = KNOWN_CIRCULANTS[target_n]
            diff_set = set()
            for d in base_diffs:
                diff_set.add(d)
                diff_set.add(target_n - d)
            seed = make_circulant(target_n, diff_set)
            print(f"  Using known circulant: diffs={base_diffs}")
        else:
            # For sizes without known circulants, do a quick Phase 1
            print(f"  No known circulant -- running quick Phase 1...")
            half = target_n // 2
            rng_init = np.random.RandomState()
            best_seed_E = float('inf')
            seed = None
            from ramsey_circulant import check_clique_at_vertex, check_indep_at_vertex
            t0_p1 = time.time()
            last_log_p1 = time.time()
            for trial in range(100000):
                target_size = half // 2 + rng_init.randint(-3, 4)
                target_size = max(3, min(target_size, half))
                base_d = rng_init.choice(range(1, half + 1), size=target_size, replace=False)
                ds = set()
                for d in base_d:
                    ds.add(int(d))
                    ds.add(int(target_n - d))
                A = make_circulant(target_n, ds)
                k5 = check_clique_at_vertex(A, 0, 5, target_n)
                i5 = check_indep_at_vertex(A, 0, 5, target_n)
                E = k5 + i5
                if E < best_seed_E:
                    best_seed_E = E
                    seed = A.copy()
                    if E == 0:
                        break
                now = time.time()
                if now - last_log_p1 >= 2.0:
                    log_progress({
                        'time': round(now - t0, 1), 'wall': round(now, 1),
                        'n': target_n, 'trial': 0,
                        'step': trial, 'max_steps': 100000,
                        'pct': round(trial / 100000 * 100, 1),
                        'E': E, 'best_E': best_seed_E,
                        'T': 0, 'accept_rate': 0, 'deg_var': 0,
                        'tri_G': 0, 'tri_C': 0,
                        'k5': k5, 'i5': i5, 'k4': 0, 'i4': 0,
                        'violation': E, 'near_viol': 0,
                        'regularity': 0, 'balance': 0,
                    })
                    last_log_p1 = now
                if trial % 20000 == 0 and trial > 0:
                    print(f"    trial {trial} best_vt={best_seed_E}", flush=True)
            print(f"  Quick Phase 1: best_vt={best_seed_E}")

        adj, E = phase3_search(target_n, seed, num_restarts=20)
        elapsed = time.time() - t0

        if E == 0:
            print(f"\n  ** VERIFIED R(5,5) avoider at n={target_n}! **")
            save_result(target_n, adj, method="hybrid(circulant+edge_SA)", elapsed=elapsed)
        else:
            print(f"\n  Best E={E} at n={target_n} [{elapsed:.1f}s]")

    print("\nDone.")
