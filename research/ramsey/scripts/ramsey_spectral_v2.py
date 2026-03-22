"""
R(5,5) Hybrid SA -- O(n^3) spectral + sampled clique detection.

Strategy: Instead of full O(n^5) clique counting OR loose Hoffman bound,
use a hybrid energy:
  1. Degree regularity penalty (O(n)) -- Ramsey avoiders are near-regular
  2. Triangle imbalance (O(n^3)) -- fast proxy for higher clique structure
  3. Sampled 4-clique/4-indep count (O(samples * n)) -- targeted probe

Writes progress to progress.jsonl for live dashboard.
"""
import numpy as np
import time
import sys
import json
import os
from itertools import combinations

sys.stdout.reconfigure(line_buffering=True)

PROGRESS_FILE = "progress.jsonl"


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


def count_triangles(A, n):
    """Count triangles via matrix multiplication. O(n^3) but fast with numpy."""
    A2 = A.astype(np.float32)
    A3_trace = np.trace(A2 @ A2 @ A2)
    return int(A3_trace) // 6


def count_triangles_complement(A, n):
    """Count triangles in complement."""
    C = (1 - A).astype(np.float32)
    np.fill_diagonal(C, 0)
    C3_trace = np.trace(C @ C @ C)
    return int(C3_trace) // 6


def sample_k_cliques(A, n, k, num_samples, rng):
    """Sample random k-subsets, count how many are cliques. Fast probe."""
    if n < k:
        return 0, num_samples
    found = 0
    for _ in range(num_samples):
        verts = rng.choice(n, k, replace=False)
        is_clique = True
        for a in range(k):
            for b in range(a + 1, k):
                if A[verts[a], verts[b]] == 0:
                    is_clique = False
                    break
            if not is_clique:
                break
        if is_clique:
            found += 1
    return found, num_samples


def full_count(A, k, n):
    """Full k-clique count for verification."""
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


def hybrid_energy(A, n, rng, sample_size=200):
    """Hybrid energy -- degree regularity + sampled clique detection.

    Components (no triangle counting -- saves ~60% time):
    1. Degree variance -- want near-regular (Ramsey avoiders are near-regular)
    2. Sampled 5-cliques in G -- want 0 (hard penalty)
    3. Sampled 5-independent-sets (5-cliques in complement) -- want 0
    4. Sampled 4-clique density -- want low (soft gradient toward fewer near-violations)
    """
    C = 1 - A
    np.fill_diagonal(C, 0)

    # 1. Degree regularity O(n)
    degs = A.sum(axis=1).astype(float)
    target_deg = (n - 1) / 2.0
    deg_var = float(np.var(degs))
    deg_penalty = deg_var / max(target_deg, 1)

    # 2. Sampled 5-cliques and 5-indep-sets
    k5_found, k5_total = sample_k_cliques(A, n, 5, sample_size, rng)
    i5_found, i5_total = sample_k_cliques(C.astype(np.int8), n, 5, sample_size, rng)

    # 3. Sampled 4-clique density (near-violation indicator)
    k4_found, k4_total = sample_k_cliques(A, n, 4, sample_size, rng)
    i4_found, i4_total = sample_k_cliques(C.astype(np.int8), n, 4, sample_size, rng)

    # Weighted combination
    violation_penalty = (k5_found + i5_found) * 100.0  # hard penalty for actual violations
    near_violation = (k4_found + i4_found) * 0.5       # soft penalty for 4-clique density
    regularity = deg_penalty * 2.0

    total = violation_penalty + near_violation + regularity

    details = {
        'deg_var': round(deg_var, 2),
        'tri_G': 0,
        'tri_C': 0,
        'k5': k5_found,
        'i5': i5_found,
        'k4': k4_found,
        'i4': i4_found,
        'violation': round(violation_penalty, 2),
        'near_viol': round(near_violation, 2),
        'regularity': round(regularity, 4),
        'balance': 0,
    }
    return total, details


def log_progress(data):
    """Append a JSON line to progress file."""
    with open(PROGRESS_FILE, 'a') as f:
        f.write(json.dumps(data) + '\n')


def hybrid_sa(n, trials=3, max_steps=None, seed_adj=None):
    """SA with hybrid energy. Writes progress for live dashboard."""
    rng = np.random.RandomState()
    if max_steps is None:
        max_steps = n * n * 3000

    best_adj = None
    best_E = float('inf')
    sample_size = min(500, max(100, n * 5))

    for trial in range(trials):
        t_start = time.time()

        # Initialize
        if seed_adj is not None and trial == 0:
            if seed_adj.shape[0] == n:
                adj = seed_adj.copy()
                init_method = "seed"
            elif seed_adj.shape[0] < n:
                old_n = seed_adj.shape[0]
                adj = np.zeros((n, n), dtype=np.int8)
                adj[:old_n, :old_n] = seed_adj
                for i in range(old_n, n):
                    for j in range(i):
                        if rng.random() < 0.5:
                            adj[i, j] = adj[j, i] = 1
                init_method = f"ext({old_n}->{n})"
            else:
                adj = seed_adj[:n, :n].copy()
                init_method = f"trunc->{n}"
        else:
            is_prime = n >= 5 and all(n % d != 0 for d in range(2, int(n**0.5) + 1))
            if is_prime and n % 4 == 1 and trial == 0:
                adj = paley(n)
                init_method = "Paley"
            else:
                adj = np.zeros((n, n), dtype=np.int8)
                for i in range(n):
                    for j in range(i + 1, n):
                        if rng.random() < 0.5:
                            adj[i, j] = adj[j, i] = 1
                init_method = "random"

        E, details = hybrid_energy(adj, n, rng, sample_size)
        print(f"  Trial {trial+1}: init={init_method} E={E:.2f} k5={details['k5']} i5={details['i5']}", flush=True)

        if E < best_E:
            best_E = E
            best_adj = adj.copy()

        T = 2.0
        cooling = 1.0 - 3.0 / max_steps
        last_report = time.time()
        last_log = time.time()
        no_improve = 0
        local_best_E = E
        step_count = 0
        accept_count = 0

        for step in range(max_steps):
            u = rng.randint(0, n)
            v = rng.randint(0, n)
            if u == v:
                continue
            if u > v:
                u, v = v, u

            adj[u, v] = 1 - adj[u, v]
            adj[v, u] = adj[u, v]

            newE, new_details = hybrid_energy(adj, n, rng, sample_size)
            dE = newE - E
            step_count += 1

            if dE <= 0 or rng.random() < np.exp(-dE / max(T, 0.001)):
                E = newE
                details = new_details
                accept_count += 1
                if E < local_best_E:
                    local_best_E = E
                    no_improve = 0
                else:
                    no_improve += 1
                if E < best_E:
                    best_E = E
                    best_adj = adj.copy()
            else:
                adj[u, v] = 1 - adj[u, v]
                adj[v, u] = adj[u, v]
                no_improve += 1

            T *= cooling

            # Reheat if stuck
            if no_improve > n * n * 100:
                T = max(T, 0.8)
                no_improve = 0

            # Log progress every 2 seconds
            now = time.time()
            if now - last_log >= 2.0:
                log_progress({
                    'time': round(now - t_start, 1),
                    'wall': round(now, 1),
                    'n': n,
                    'trial': trial + 1,
                    'step': step,
                    'max_steps': max_steps,
                    'pct': round(step / max_steps * 100, 1),
                    'E': round(E, 3),
                    'best_E': round(best_E, 3),
                    'T': round(T, 6),
                    'accept_rate': round(accept_count / max(step_count, 1), 3),
                    **details
                })
                last_log = now

            if now - last_report > 20:
                elapsed = now - t_start
                pct = step / max_steps * 100
                rate = step_count / elapsed
                print(f"    E={E:.2f} best={best_E:.2f} k5={details['k5']} i5={details['i5']} "
                      f"k4={details['k4']} i4={details['i4']} "
                      f"T={T:.4f} {pct:.0f}% {rate:.0f}st/s", flush=True)
                last_report = now

        elapsed = time.time() - t_start
        print(f"    final E={E:.2f} best={best_E:.2f} [{elapsed:.1f}s]", flush=True)

    return best_adj, best_E, trials


if __name__ == '__main__':
    print("R(5,5) Hybrid SA -- Spectral + Sampled Clique Energy")
    print("=" * 60)

    # Clear progress file
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

    # Load seed
    seed = None
    for npy in ['r55_n38.npy', 'r55_n37.npy']:
        try:
            seed = np.load(npy)
            print(f"Loaded seed: {npy} (n={seed.shape[0]})")
            break
        except FileNotFoundError:
            continue

    for target_n in range(39, 44):
        print(f"\n{'='*60}")
        print(f"Target: n={target_n}")
        print(f"{'='*60}")

        t0 = time.time()
        adj, E, trial = hybrid_sa(target_n, trials=3,
                                   max_steps=target_n * target_n * 3000,
                                   seed_adj=seed)

        # When sampled energy is low, verify with full count
        if E < 5.0:
            print(f"\n  Low energy ({E:.2f}), running full verification...")
            C = 1 - adj; np.fill_diagonal(C, 0)
            kr = full_count(adj, 5, target_n)
            is_ = full_count(C, 5, target_n)
            edges = int(adj.sum()) // 2
            total = target_n * (target_n - 1) // 2
            print(f"  K5={kr} I5={is_} edges={edges}/{total} ({edges/total*100:.1f}%)")

            if kr + is_ == 0:
                print(f"  ** VERIFIED R(5,5) avoider at n={target_n}! **")
                np.save(f"r55_n{target_n}.npy", adj)
                print(f"  Saved to r55_n{target_n}.npy")
                seed = adj
                continue
            else:
                print(f"  Sampled energy was low but full count found {kr+is_} violations")
                print(f"  (Need more SA steps or better sampling)")

        print(f"  Best energy: {E:.2f}")
        print(f"  Total time: {time.time()-t0:.1f}s")

        if E > 50:
            print(f"  Energy too high, stopping.")
            break

    print("\nDone.")
