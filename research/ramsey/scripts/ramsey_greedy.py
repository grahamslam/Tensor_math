"""
R(5,5) Greedy + Targeted SA -- two-phase approach.

Phase A: GREEDY -- for each step, evaluate ALL possible edge flips,
         pick the one that reduces violations the most. No randomness.
         Runs until no improving flip exists (local minimum).

Phase B: TARGETED SA -- from the greedy local minimum, use SA with
         targeted violation-aware moves to escape and continue.
         Chains restarts from best-so-far instead of original seed.

With incremental violation tracking, greedy can evaluate ~860 edges
per step at n=42, each in O(neighbors) time.
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


def find_all_violations(adj, n):
    """Find all 5-cliques in G and 5-independent-sets (= cliques in complement)."""
    C = 1 - adj.copy()
    np.fill_diagonal(C, 0)
    k5 = set()
    i5 = set()
    for combo in combinations(range(n), 5):
        ok = True
        for a in range(5):
            for b in range(a + 1, 5):
                if adj[combo[a], combo[b]] == 0:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            k5.add(frozenset(combo))

        ok = True
        for a in range(5):
            for b in range(a + 1, 5):
                if C[combo[a], combo[b]] == 0:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            i5.add(frozenset(combo))
    return k5, i5


def count_violations_through_edge(u, v, adj_uv, k5_set, i5_set):
    """Count how many violations edge (u,v) participates in."""
    count = 0
    if adj_uv == 1:
        for c in k5_set:
            if u in c and v in c:
                count += 1
    else:
        for c in i5_set:
            if u in c and v in c:
                count += 1
    return count


def flip_and_update(adj, u, v, k5_set, i5_set, n):
    """Flip edge (u,v) and update violation sets. Returns (removed, added)."""
    adj[u, v] = 1 - adj[u, v]
    adj[v, u] = adj[u, v]

    if adj[u, v] == 1:
        # Edge ADDED -- remove broken I5s, check for new K5s
        to_remove = {s for s in i5_set if u in s and v in s}
        i5_set -= to_remove

        added = 0
        cn = [w for w in range(n) if w != u and w != v
              and adj[u, w] == 1 and adj[v, w] == 1]
        for combo in combinations(cn, 3):
            if (adj[combo[0], combo[1]] == 1 and
                adj[combo[0], combo[2]] == 1 and
                adj[combo[1], combo[2]] == 1):
                new_c = frozenset([u, v, combo[0], combo[1], combo[2]])
                if new_c not in k5_set:
                    k5_set.add(new_c)
                    added += 1
        return len(to_remove), added
    else:
        # Edge REMOVED -- remove broken K5s, check for new I5s
        to_remove = {s for s in k5_set if u in s and v in s}
        k5_set -= to_remove

        added = 0
        cnn = [w for w in range(n) if w != u and w != v
               and adj[u, w] == 0 and adj[v, w] == 0]
        for combo in combinations(cnn, 3):
            if (adj[combo[0], combo[1]] == 0 and
                adj[combo[0], combo[2]] == 0 and
                adj[combo[1], combo[2]] == 0):
                new_c = frozenset([u, v, combo[0], combo[1], combo[2]])
                if new_c not in i5_set:
                    i5_set.add(new_c)
                    added += 1
        return len(to_remove), added


def evaluate_flip(adj, u, v, k5_set, i5_set, n):
    """Evaluate what flipping (u,v) would do WITHOUT actually doing it.
    Returns delta_E (negative = improvement)."""
    # How many violations does this edge currently participate in?
    destroys = count_violations_through_edge(u, v, adj[u, v], k5_set, i5_set)

    # Temporarily flip to count what would be created
    adj[u, v] = 1 - adj[u, v]
    adj[v, u] = adj[u, v]

    creates = 0
    if adj[u, v] == 1:
        # Now edge exists -- count new K5s
        cn = [w for w in range(n) if w != u and w != v
              and adj[u, w] == 1 and adj[v, w] == 1]
        for combo in combinations(cn, 3):
            if (adj[combo[0], combo[1]] == 1 and
                adj[combo[0], combo[2]] == 1 and
                adj[combo[1], combo[2]] == 1):
                c = frozenset([u, v, combo[0], combo[1], combo[2]])
                if c not in k5_set:
                    creates += 1
    else:
        # Now edge absent -- count new I5s
        cnn = [w for w in range(n) if w != u and w != v
               and adj[u, w] == 0 and adj[v, w] == 0]
        for combo in combinations(cnn, 3):
            if (adj[combo[0], combo[1]] == 0 and
                adj[combo[0], combo[2]] == 0 and
                adj[combo[1], combo[2]] == 0):
                c = frozenset([u, v, combo[0], combo[1], combo[2]])
                if c not in i5_set:
                    creates += 1

    # Undo
    adj[u, v] = 1 - adj[u, v]
    adj[v, u] = adj[u, v]

    return creates - destroys


def log_progress(data):
    with open(PROGRESS_FILE, 'a') as f:
        f.write(json.dumps(data) + '\n')


def save_result(n, adj, method, elapsed=0):
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


if __name__ == '__main__':
    n = 42
    print(f"R(5,5) Greedy + Targeted SA at n={n}")
    print("=" * 60)

    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

    t0 = time.time()

    # Seed
    diffs = [3, 7, 8, 10, 11, 12, 14, 16, 18, 19]
    diff_set = set()
    for d in diffs:
        diff_set.add(d)
        diff_set.add(n - d)
    seed = make_circulant(n, diff_set)

    # ===== PHASE A: GREEDY =====
    print(f"\nPhase A: Greedy descent")
    adj = seed.copy()
    k5_set, i5_set = find_all_violations(adj, n)
    E = len(k5_set) + len(i5_set)
    print(f"  Start: {len(k5_set)} K5 + {len(i5_set)} I5 = {E}")

    greedy_step = 0
    last_log = time.time()
    while E > 0:
        # Find the best flip among ALL edges involved in violations
        # First, collect all vertices in violations
        viol_vertices = set()
        for c in k5_set:
            viol_vertices.update(c)
        for c in i5_set:
            viol_vertices.update(c)

        if not viol_vertices:
            break

        # Evaluate flips for edges touching violation vertices
        best_delta = 0
        best_flip = None
        candidates_checked = 0

        for u in sorted(viol_vertices):
            for v in range(u + 1, n):
                # Only evaluate if this edge is in a violation
                in_viol = count_violations_through_edge(u, v, adj[u, v], k5_set, i5_set)
                if in_viol == 0:
                    continue

                delta = evaluate_flip(adj, u, v, k5_set, i5_set, n)
                candidates_checked += 1
                if delta < best_delta:
                    best_delta = delta
                    best_flip = (u, v)

        if best_flip is None or best_delta >= 0:
            print(f"  Greedy stuck at E={E} (no improving flip among {candidates_checked} candidates)")
            break

        u, v = best_flip
        old_k5 = k5_set.copy()
        old_i5 = i5_set.copy()
        flip_and_update(adj, u, v, k5_set, i5_set, n)
        E = len(k5_set) + len(i5_set)
        greedy_step += 1

        now = time.time()
        if now - last_log >= 2.0:
            log_progress({
                'time': round(now - t0, 1), 'wall': round(now, 1),
                'n': n, 'trial': 0,
                'step': greedy_step, 'max_steps': 1000,
                'pct': 0,
                'E': E, 'best_E': E,
                'T': 0, 'accept_rate': 1.0, 'deg_var': 0,
                'tri_G': 0, 'tri_C': 0,
                'k5': len(k5_set), 'i5': len(i5_set),
                'k4': 0, 'i4': 0,
                'violation': E, 'near_viol': 0,
                'regularity': 0, 'balance': 0,
            })
            last_log = now

        print(f"    Step {greedy_step}: flip ({u},{v}) dE={best_delta} -> "
              f"E={E} (K5={len(k5_set)} I5={len(i5_set)}) "
              f"[checked {candidates_checked}]", flush=True)

        if E == 0:
            elapsed = time.time() - t0
            print(f"\n  GREEDY SOLVED IT! E=0 in {greedy_step} steps [{elapsed:.1f}s]")
            print(f"\n  ** VERIFIED R(5,5) avoider at n={n}! **")
            save_result(n, adj, "greedy(circulant_seed)", elapsed)
            sys.exit(0)

    greedy_E = E
    greedy_elapsed = time.time() - t0
    print(f"\nPhase A done: E={greedy_E} in {greedy_step} steps [{greedy_elapsed:.1f}s]")

    # ===== PHASE B: TARGETED SA from greedy local minimum =====
    print(f"\nPhase B: Targeted SA from greedy minimum (E={greedy_E})")

    best_adj = adj.copy()
    best_k5 = k5_set.copy()
    best_i5 = i5_set.copy()
    global_best_E = greedy_E

    rng = np.random.RandomState()
    num_restarts = 50
    steps_per_restart = n * n * 200

    for restart in range(num_restarts):
        # Chain from best-so-far, not original seed
        adj = best_adj.copy()
        k5_set, i5_set = find_all_violations(adj, n)
        E = len(k5_set) + len(i5_set)

        T = 0.5
        cooling = 1.0 - 5.0 / steps_per_restart
        restart_best = E

        for step in range(steps_per_restart):
            # 70% targeted, 30% random
            if rng.random() < 0.7 and E > 0:
                all_viols = list(k5_set) + list(i5_set)
                viol = list(all_viols[rng.randint(0, len(all_viols))])
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

            old_k5 = k5_set.copy()
            old_i5 = i5_set.copy()

            flip_and_update(adj, u, v, k5_set, i5_set, n)
            newE = len(k5_set) + len(i5_set)
            dE = newE - E

            if dE <= 0 or rng.random() < np.exp(-dE / max(T, 0.005)):
                E = newE
                if E < restart_best:
                    restart_best = E
                if E < global_best_E:
                    global_best_E = E
                    best_adj = adj.copy()
                    best_k5 = k5_set.copy()
                    best_i5 = i5_set.copy()
                if E == 0:
                    elapsed = time.time() - t0
                    print(f"  FOUND! restart={restart} step={step} [{elapsed:.1f}s]")
                    print(f"\n  ** VERIFIED R(5,5) avoider at n={n}! **")
                    save_result(n, adj, "greedy+targeted_SA", elapsed)
                    sys.exit(0)
            else:
                adj[u, v] = 1 - adj[u, v]
                adj[v, u] = adj[u, v]
                k5_set.clear()
                k5_set.update(old_k5)
                i5_set.clear()
                i5_set.update(old_i5)

            T *= cooling

            now = time.time()
            if now - last_log >= 2.0:
                gs = restart * steps_per_restart + step
                total_steps = num_restarts * steps_per_restart
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

        print(f"  R{restart}: this={restart_best} best={global_best_E} "
              f"K5={len(k5_set)} I5={len(i5_set)} [{time.time()-t0:.0f}s]", flush=True)

    elapsed = time.time() - t0
    print(f"\nBest E={global_best_E} at n={n} [{elapsed:.1f}s]")
    print("Done.")
