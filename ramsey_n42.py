"""
R(5,5) focused attack on n=42 -- the frontier.

Strategy:
1. Exhaustive-ish circulant search (500K trials) to find best seed
2. Multi-restart edge SA with MEDIUM temp (0.8) and slow cooling
3. If that fails, try Paley(41) as alternate seed (41 is prime, 41 mod 4 = 1)
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


def check_at_vertex(A, v, k_clique, k_indep, n):
    neighbors = [w for w in range(n) if A[v, w] == 1]
    non_neighbors = [w for w in range(n) if w != v and A[v, w] == 0]
    k5 = 0
    for combo in combinations(neighbors, k_clique - 1):
        if all(A[combo[a], combo[b]] == 1 for a in range(k_clique-1) for b in range(a+1, k_clique-1)):
            k5 += 1
    i5 = 0
    for combo in combinations(non_neighbors, k_indep - 1):
        if all(A[combo[a], combo[b]] == 0 for a in range(k_indep-1) for b in range(a+1, k_indep-1)):
            i5 += 1
    return k5, i5


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


if __name__ == '__main__':
    n = 42
    print(f"R(5,5) Focused Attack on n={n}")
    print("=" * 60)

    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

    t0_total = time.time()
    rng = np.random.RandomState()
    half = n // 2

    # ===== PHASE 1: Deep circulant search =====
    print(f"\nPhase 1: Deep circulant search (500K trials, half={half})")
    best_vt = float('inf')
    best_seed = None
    best_diffs = None
    last_log = time.time()

    for trial in range(500000):
        target_size = half // 2 + rng.randint(-4, 5)
        target_size = max(3, min(target_size, half))
        base_d = rng.choice(range(1, half + 1), size=target_size, replace=False)
        ds = set()
        for d in base_d:
            ds.add(int(d))
            ds.add(int(n - d))
        A = make_circulant(n, ds)
        k5, i5 = check_at_vertex(A, 0, 5, 5, n)
        E = k5 + i5
        if E < best_vt:
            best_vt = E
            best_seed = A.copy()
            best_diffs = sorted([d for d in ds if d <= half])
            if E == 0:
                print(f"  CLEAN circulant at trial {trial}!")
                break

        now = time.time()
        if now - last_log >= 2.0:
            log_progress({
                'time': round(now - t0_total, 1), 'wall': round(now, 1),
                'n': n, 'trial': 0,
                'step': trial, 'max_steps': 500000,
                'pct': round(trial / 500000 * 100, 1),
                'E': E, 'best_E': best_vt,
                'T': 0, 'accept_rate': 0, 'deg_var': 0,
                'tri_G': 0, 'tri_C': 0,
                'k5': k5, 'i5': i5, 'k4': 0, 'i4': 0,
                'violation': E, 'near_viol': 0,
                'regularity': 0, 'balance': 0,
            })
            last_log = now

        if trial % 50000 == 0 and trial > 0:
            rate = trial / (time.time() - t0_total)
            print(f"  trial {trial} best_vt={best_vt} diffs={best_diffs} {rate:.0f}/s", flush=True)

    print(f"Phase 1 done: best_vt={best_vt} diffs={best_diffs} [{time.time()-t0_total:.1f}s]")

    if best_vt == 0:
        # Verify
        seed_E = full_energy(best_seed, n)
        if seed_E == 0:
            print(f"\n** VERIFIED pure circulant R(5,5) avoider at n={n}! **")
            save_result(n, best_seed, "circulant", time.time() - t0_total)
            sys.exit(0)

    # Also try Paley(41) extended to 42
    print(f"\nAlternate seed: Paley(41) extended to n={n}")
    p41 = paley(41)
    adj41 = np.zeros((n, n), dtype=np.int8)
    adj41[:41, :41] = p41
    for j in range(41):
        if rng.random() < 0.5:
            adj41[41, j] = adj41[j, 41] = 1
    paley_E = full_energy(adj41, n)
    print(f"  Paley(41)+1: full E={paley_E}")

    # Pick best seed
    circ_full_E = full_energy(best_seed, n)
    print(f"  Best circulant: full E={circ_full_E}")

    seeds = [(best_seed, circ_full_E, "circulant"), (adj41, paley_E, "paley41+1")]
    seeds.sort(key=lambda x: x[1])
    print(f"  Using: {seeds[0][2]} (E={seeds[0][1]})")

    # ===== PHASE 3: Multi-restart edge SA =====
    print(f"\nPhase 3: Multi-restart edge SA")

    num_restarts = 30
    steps_per_restart = n * n * 300
    total_steps = num_restarts * steps_per_restart

    global_best_E = float('inf')
    global_best_adj = None
    t0_p3 = time.time()

    for seed_adj, seed_E, seed_name in seeds[:2]:  # try both seeds
        print(f"\n  --- Seed: {seed_name} (E={seed_E}) ---")

        for restart in range(num_restarts):
            adj = seed_adj.copy()
            comp = 1 - adj.copy()
            np.fill_diagonal(comp, 0)
            E = seed_E

            # Medium temp -- allow exploration but don't scramble
            T = 0.8
            cooling = 1.0 - 5.0 / steps_per_restart
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
                            elapsed = time.time() - t0_total
                            print(f"\n  FOUND! seed={seed_name} restart={restart} step={step} [{elapsed:.1f}s]")
                            print(f"\n  ** VERIFIED R(5,5) avoider at n={n}! **")
                            save_result(n, adj, f"hybrid({seed_name}+edge_SA)", elapsed)
                            sys.exit(0)
                        else:
                            E = real_E
                    elif E < restart_best:
                        restart_best = E
                    if E < global_best_E:
                        global_best_E = E
                        global_best_adj = adj.copy()
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
                        'time': round(now - t0_total, 1), 'wall': round(now, 1),
                        'n': n, 'trial': restart + 1,
                        'step': gs, 'max_steps': total_steps,
                        'pct': round(gs / total_steps * 100, 1),
                        'E': E, 'best_E': global_best_E,
                        'T': round(T, 6), 'accept_rate': 0, 'deg_var': 0,
                        'tri_G': 0, 'tri_C': 0,
                        'k5': E, 'i5': 0, 'k4': 0, 'i4': 0,
                        'violation': E, 'near_viol': 0,
                        'regularity': 0, 'balance': 0,
                    })
                    last_log = now

                if now - last_report >= 20 if 'last_report' in dir() else True:
                    pass

            print(f"  R{restart}: this={restart_best} best={global_best_E} "
                  f"[{time.time()-t0_p3:.0f}s]", flush=True)

    elapsed = time.time() - t0_total
    print(f"\nBest E={global_best_E} at n={n} [{elapsed:.1f}s]")
