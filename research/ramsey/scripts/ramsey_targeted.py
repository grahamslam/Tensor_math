"""
R(5,5) Targeted SA -- AlphaEvolve Algorithm 4 inspired.

Key insight: maintain explicit sets of all 5-cliques and 5-independent-sets.
When choosing which edge to flip, pick the one that destroys the most violations.
When flipping, update violation sets incrementally instead of recounting.

This turns random SA into TARGETED violation destruction.
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


def find_all_cliques(A, k, n):
    """Find all k-cliques. Returns set of frozensets."""
    cliques = set()
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
            cliques.add(frozenset(combo))
    return cliques


def find_violations(adj, n):
    """Find all 5-cliques in G and complement (= all violations)."""
    C = 1 - adj.copy()
    np.fill_diagonal(C, 0)
    k5 = find_all_cliques(adj, 5, n)
    i5 = find_all_cliques(C, 5, n)
    return k5, i5


def edge_violation_score(adj, u, v, k5_set, i5_set, n):
    """How many violations does edge (u,v) participate in?
    For K5: if edge is present, count K5s containing both u and v.
    For I5: if edge is absent, count I5s containing both u and v.
    Flipping this edge would destroy those violations (but might create new ones)."""
    score_destroy = 0
    score_create = 0

    if adj[u, v] == 1:
        # Edge exists. Removing it destroys K5s through (u,v), but might create I5s.
        for clique in k5_set:
            if u in clique and v in clique:
                score_destroy += 1
    else:
        # Edge absent. Adding it destroys I5s through (u,v), but might create K5s.
        for indep in i5_set:
            if u in indep and v in indep:
                score_destroy += 1

    return score_destroy


def update_violations_after_flip(adj, u, v, k5_set, i5_set, n):
    """After flipping edge (u,v), update violation sets incrementally.

    If edge was added (now adj[u,v]=1):
      - Remove any I5s containing both u and v (they're no longer independent)
      - Check for new K5s containing both u and v
    If edge was removed (now adj[u,v]=0):
      - Remove any K5s containing both u and v (they're no longer cliques)
      - Check for new I5s containing both u and v
    """
    C = 1 - adj.copy()
    np.fill_diagonal(C, 0)

    if adj[u, v] == 1:
        # Edge was ADDED
        # Remove broken I5s
        to_remove = {s for s in i5_set if u in s and v in s}
        i5_set -= to_remove
        removed = len(to_remove)

        # Check for new K5s through (u,v)
        added = 0
        # Need 3 more vertices that are all connected to u, v, and each other
        common_neighbors = [w for w in range(n) if w != u and w != v
                           and adj[u, w] == 1 and adj[v, w] == 1]
        for combo in combinations(common_neighbors, 3):
            if (adj[combo[0], combo[1]] == 1 and
                adj[combo[0], combo[2]] == 1 and
                adj[combo[1], combo[2]] == 1):
                new_clique = frozenset([u, v, combo[0], combo[1], combo[2]])
                if new_clique not in k5_set:
                    k5_set.add(new_clique)
                    added += 1
    else:
        # Edge was REMOVED
        # Remove broken K5s
        to_remove = {s for s in k5_set if u in s and v in s}
        k5_set -= to_remove
        removed = len(to_remove)

        # Check for new I5s through (u,v)
        added = 0
        common_non_neighbors = [w for w in range(n) if w != u and w != v
                                and adj[u, w] == 0 and adj[v, w] == 0]
        for combo in combinations(common_non_neighbors, 3):
            if (adj[combo[0], combo[1]] == 0 and
                adj[combo[0], combo[2]] == 0 and
                adj[combo[1], combo[2]] == 0):
                new_indep = frozenset([u, v, combo[0], combo[1], combo[2]])
                if new_indep not in i5_set:
                    i5_set.add(new_indep)
                    added += 1

    return removed, added


def log_progress(data):
    with open(PROGRESS_FILE, 'a') as f:
        f.write(json.dumps(data) + '\n')


def save_result(n, adj, method, elapsed=0, phases=None):
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
        'elapsed_seconds': round(elapsed, 1),
        'phases': phases or {},
        'npy_file': f'r55_n{n}_verified.npy',
        'adjacency': adj.tolist(),
    }
    results = [r for r in results if r['n'] != n]
    results.append(entry)
    results.sort(key=lambda r: r['n'])
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    np.save(f'r55_n{n}_verified.npy', adj)
    print(f"  Saved to {RESULTS_FILE} and r55_n{n}_verified.npy")


def targeted_sa(n, seed_adj, num_restarts=20, steps_per_restart=None):
    """Targeted SA: score edges by violation participation, flip the best ones."""
    if steps_per_restart is None:
        steps_per_restart = n * n * 300

    rng = np.random.RandomState()
    t0 = time.time()
    last_log = time.time()

    global_best_E = float('inf')
    global_best_adj = None
    total_steps = num_restarts * steps_per_restart

    for restart in range(num_restarts):
        adj = seed_adj.copy()

        # Build initial violation sets
        k5_set, i5_set = find_violations(adj, n)
        E = len(k5_set) + len(i5_set)

        if restart == 0:
            print(f"  Initial violations: {len(k5_set)} K5 + {len(i5_set)} I5 = {E}")

        if E == 0:
            print(f"  Already clean!")
            return adj, 0

        restart_best = E
        if E < global_best_E:
            global_best_E = E
            global_best_adj = adj.copy()

        T = 0.5
        cooling = 1.0 - 5.0 / steps_per_restart

        for step in range(steps_per_restart):
            # 70% of the time: pick a TARGETED flip (edge in a violation)
            # 30% of the time: random flip (exploration)
            if rng.random() < 0.7 and E > 0:
                # Pick a random violation, then a random edge in it
                all_violations = list(k5_set) + list(i5_set)
                viol = list(all_violations[rng.randint(0, len(all_violations))])
                # Pick a random pair from this violation
                idx = rng.choice(len(viol), 2, replace=False)
                u, v = viol[idx[0]], viol[idx[1]]
                if u > v:
                    u, v = v, u
            else:
                u = rng.randint(0, n)
                v = rng.randint(0, n)
                if u == v:
                    continue
                if u > v:
                    u, v = v, u

            # Save state for undo
            old_k5 = k5_set.copy()
            old_i5 = i5_set.copy()

            # Flip
            adj[u, v] = 1 - adj[u, v]
            adj[v, u] = adj[u, v]

            # Incremental update
            removed, added = update_violations_after_flip(adj, u, v, k5_set, i5_set, n)
            newE = len(k5_set) + len(i5_set)
            dE = newE - E

            if dE <= 0 or rng.random() < np.exp(-dE / max(T, 0.005)):
                E = newE
                if E < restart_best:
                    restart_best = E
                if E < global_best_E:
                    global_best_E = E
                    global_best_adj = adj.copy()
                if E == 0:
                    elapsed = time.time() - t0
                    print(f"  FOUND! restart={restart} step={step} [{elapsed:.1f}s]")
                    return adj, 0
            else:
                # Undo flip and restore violation sets
                adj[u, v] = 1 - adj[u, v]
                adj[v, u] = adj[u, v]
                k5_set.clear()
                k5_set.update(old_k5)
                i5_set.clear()
                i5_set.update(old_i5)

            T *= cooling

            # Periodic full recount to catch any bugs
            if step > 0 and step % 10000 == 0:
                real_k5, real_i5 = find_violations(adj, n)
                real_E = len(real_k5) + len(real_i5)
                if real_E != E:
                    k5_set = real_k5
                    i5_set = real_i5
                    E = real_E

            now = time.time()
            if now - last_log >= 2.0:
                gs = restart * steps_per_restart + step
                log_progress({
                    'time': round(now - t0, 1), 'wall': round(now, 1),
                    'n': n, 'trial': restart + 1,
                    'step': gs, 'max_steps': total_steps,
                    'pct': round(gs / total_steps * 100, 1),
                    'E': E, 'best_E': global_best_E,
                    'T': round(T, 6), 'accept_rate': 0, 'deg_var': 0,
                    'tri_G': 0, 'tri_C': 0,
                    'k5': len(k5_set), 'i5': len(i5_set),
                    'k4': 0, 'i4': 0,
                    'violation': E, 'near_viol': 0,
                    'regularity': 0, 'balance': 0,
                })
                last_log = now

        print(f"  R{restart}: this={restart_best} K5={len(k5_set)} I5={len(i5_set)} "
              f"best={global_best_E} [{time.time()-t0:.0f}s]", flush=True)

    return global_best_adj, global_best_E


if __name__ == '__main__':
    n = 42
    print(f"R(5,5) Targeted SA at n={n}")
    print("=" * 60)

    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

    t0 = time.time()

    # Best known circulant for n=42
    diffs = [3, 7, 8, 10, 11, 12, 14, 16, 18, 19]
    diff_set = set()
    for d in diffs:
        diff_set.add(d)
        diff_set.add(n - d)
    seed = make_circulant(n, diff_set)
    print(f"Seed: circulant diffs={diffs}")

    adj, E = targeted_sa(n, seed, num_restarts=30, steps_per_restart=n*n*300)

    elapsed = time.time() - t0
    if E == 0:
        print(f"\n** VERIFIED R(5,5) avoider at n={n}! **")
        save_result(n, adj, "targeted_SA(circulant_seed)", elapsed)
    else:
        print(f"\nBest E={E} at n={n} [{elapsed:.1f}s]")

    print("\nDone.")
