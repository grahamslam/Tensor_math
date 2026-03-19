"""
R(5,5) n=42 via extension from verified n=41 avoider.

AlphaEvolve Algorithm 2 strategy:
1. Load verified n=41 R(5,5) avoider
2. Find all 4-cliques and 4-independent-sets in base graph
3. For the new vertex 41: its neighborhood must "hit" every 4-indep-set
   (connect to at least one member) AND "miss" at least one vertex
   in every 4-clique (not connect to all members)
4. Use SA on the new vertex's connection vector (41 bits) -- much smaller search
5. If that fails, do targeted edge SA on the full n=42 graph

Key advantage: search space for new vertex is 2^41 vs 2^861 for full graph.
And we only need to check violations involving the new vertex.
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


def find_k_cliques(A, k, n):
    """Find all k-cliques."""
    cliques = []
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
            cliques.append(combo)
    return cliques


def count_new_vertex_violations(adj41, connection, n_base, r=5, s=5):
    """Count violations introduced by adding vertex n_base with given connections.
    Only checks 5-cliques and 5-indep-sets containing the new vertex."""
    new_v = n_base
    neighbors = [j for j in range(n_base) if connection[j] == 1]
    non_neighbors = [j for j in range(n_base) if connection[j] == 0]

    # K5s containing new vertex: need 4-clique among neighbors
    k5_new = 0
    for combo in combinations(neighbors, 4):
        ok = True
        for a in range(4):
            for b in range(a + 1, 4):
                if adj41[combo[a], combo[b]] == 0:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            k5_new += 1

    # I5s containing new vertex: need 4-indep-set among non-neighbors
    i5_new = 0
    for combo in combinations(non_neighbors, 4):
        ok = True
        for a in range(4):
            for b in range(a + 1, 4):
                if adj41[combo[a], combo[b]] == 1:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            i5_new += 1

    return k5_new, i5_new


def full_energy(adj, n):
    C = 1 - adj.copy()
    np.fill_diagonal(C, 0)
    k5 = 0
    i5 = 0
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
            k5 += 1

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
    print(f"R(5,5) Extension Attack: n=41 -> n={n}")
    print("=" * 60)

    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

    t0 = time.time()

    # Load n=41 avoider
    adj41 = np.load('r55_n41_verified.npy')
    n_base = 41
    print(f"Loaded verified n={n_base} avoider")

    # Count 4-cliques and 4-indep-sets in base graph
    print(f"Counting 4-cliques and 4-independent-sets in base graph...")
    t1 = time.time()
    cliques4 = find_k_cliques(adj41, 4, n_base)
    C41 = 1 - adj41.copy()
    np.fill_diagonal(C41, 0)
    indeps4 = find_k_cliques(C41, 4, n_base)
    print(f"  {len(cliques4)} 4-cliques, {len(indeps4)} 4-independent-sets [{time.time()-t1:.1f}s]")

    # ===== PHASE 1: SA on connection vector =====
    print(f"\nPhase 1: SA on new vertex connection vector (41 bits)")
    print(f"  Constraint: connect to >=1 in each 4-indep-set, miss >=1 in each 4-clique")

    rng = np.random.RandomState()
    last_log = time.time()

    global_best_E = float('inf')
    global_best_conn = None
    num_restarts = 100  # cheap -- only 41 bits to flip
    steps_per_restart = 200000

    for restart in range(num_restarts):
        # Random connection vector targeting ~50% degree
        conn = np.zeros(n_base, dtype=np.int8)
        for j in range(n_base):
            if rng.random() < 0.5:
                conn[j] = 1

        k5, i5 = count_new_vertex_violations(adj41, conn, n_base)
        E = k5 + i5

        T = 1.0
        cooling = 1.0 - 5.0 / steps_per_restart
        restart_best = E

        for step in range(steps_per_restart):
            # Flip one bit in connection vector
            j = rng.randint(0, n_base)
            conn[j] = 1 - conn[j]

            new_k5, new_i5 = count_new_vertex_violations(adj41, conn, n_base)
            newE = new_k5 + new_i5
            dE = newE - E

            if dE <= 0 or rng.random() < np.exp(-dE / max(T, 0.005)):
                E = newE
                if E < restart_best:
                    restart_best = E
                if E < global_best_E:
                    global_best_E = E
                    global_best_conn = conn.copy()
                if E == 0:
                    break
            else:
                conn[j] = 1 - conn[j]

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
                    'k5': new_k5 if 'new_k5' in dir() else k5,
                    'i5': new_i5 if 'new_i5' in dir() else i5,
                    'k4': 0, 'i4': 0,
                    'violation': E, 'near_viol': 0,
                    'regularity': 0, 'balance': 0,
                })
                last_log = now

        if restart % 10 == 0 or restart_best < global_best_E + 5:
            elapsed = time.time() - t0
            print(f"  R{restart}: this={restart_best} best={global_best_E} [{elapsed:.0f}s]", flush=True)

        if global_best_E == 0:
            break

    elapsed_p1 = time.time() - t0
    print(f"\nPhase 1 done: best E={global_best_E} [{elapsed_p1:.1f}s]")

    if global_best_E == 0:
        # Build full n=42 graph and verify
        adj42 = np.zeros((n, n), dtype=np.int8)
        adj42[:n_base, :n_base] = adj41
        for j in range(n_base):
            adj42[n_base, j] = adj42[j, n_base] = global_best_conn[j]

        print(f"\nFull verification...")
        k5_full, i5_full = full_energy(adj42, n)
        print(f"  K5={k5_full} I5={i5_full}")

        if k5_full + i5_full == 0:
            elapsed = time.time() - t0
            print(f"\n** VERIFIED R(5,5) avoider at n={n}! **")
            save_result(n, adj42, "extension(n41+vertex_SA)", elapsed)
        else:
            print(f"  New vertex is clean but base graph has violations?? Shouldn't happen.")
    else:
        print(f"\n  Could not find clean extension.")
        print(f"  Best new-vertex violations: {global_best_E}")
        conn = global_best_conn
        deg = int(conn.sum())
        print(f"  Best connection: degree={deg}/{n_base}")

    print(f"\nTotal time: {time.time()-t0:.1f}s")
    print("Done.")
