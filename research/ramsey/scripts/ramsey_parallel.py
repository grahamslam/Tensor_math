"""
R(5,5) Parallel Search — uses all CPU cores.
Strategy: parallel circulant search + parallel SA from multiple seeds.
"""
import numpy as np
import time
import sys
import os
from itertools import combinations
from multiprocessing import Pool, cpu_count

sys.stdout.reconfigure(line_buffering=True)

R, S = 5, 5


def energy_single(adj_flat_n):
    """Compute Ramsey energy from flattened adjacency matrix. Picklable for multiprocessing."""
    adj_flat, n = adj_flat_n
    A = adj_flat.reshape(n, n)
    kr = 0
    for combo in combinations(range(n), R):
        ok = True
        for a in range(R):
            for b in range(a+1, R):
                if A[combo[a], combo[b]] == 0:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            kr += 1

    # Independent sets = cliques in complement
    is_ = 0
    for combo in combinations(range(n), S):
        ok = True
        for a in range(S):
            for b in range(a+1, S):
                if A[combo[a], combo[b]] == 1:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            is_ += 1

    return kr + is_


def make_circulant(args):
    """Build and evaluate a circulant graph. Returns (energy, diff_set)."""
    n, seed = args
    rng = np.random.RandomState(seed)
    half = n // 2

    # Random difference set targeting ~50% density
    target = half // 2 + rng.randint(-3, 4)
    target = max(3, min(target, half))
    diffs = rng.choice(range(1, half + 1), size=target, replace=False)
    S = set()
    for d in diffs:
        S.add(int(d))
        S.add(int(n - d))

    adj = np.zeros((n, n), dtype=np.int8)
    for i in range(n):
        for j in range(n):
            if i != j and (j - i) % n in S:
                adj[i, j] = 1

    E = energy_single((adj.flatten(), n))
    return E, tuple(sorted(S)), adj.flatten()


def sa_worker(args):
    """Run SA from a seed. Returns (best_energy, best_adj_flat)."""
    n, seed, max_steps = args
    rng = np.random.RandomState(seed)

    # Random near-regular init
    adj = np.zeros((n, n), dtype=np.int8)
    for i in range(n):
        for j in range(i+1, n):
            if rng.random() < 0.5:
                adj[i, j] = adj[j, i] = 1

    E = energy_single((adj.flatten(), n))
    best_E = E
    best_adj = adj.copy()

    T = 2.0
    cooling = 1.0 - 5.0 / max_steps

    for step in range(max_steps):
        u, v = rng.randint(0, n, 2)
        if u == v:
            continue
        if u > v:
            u, v = v, u

        adj[u, v] = 1 - adj[u, v]
        adj[v, u] = adj[u, v]

        newE = energy_single((adj.flatten(), n))

        if newE <= E or rng.random() < np.exp(-(newE - E) / max(T, 0.01)):
            E = newE
            if E < best_E:
                best_E = E
                best_adj = adj.copy()
            if E == 0:
                return 0, best_adj.flatten()
        else:
            adj[u, v] = 1 - adj[u, v]
            adj[v, u] = adj[u, v]

        T *= cooling

    return best_E, best_adj.flatten()


if __name__ == '__main__':
    cores = min(cpu_count(), 8)  # cap at 8 to avoid memory exhaustion
    print(f"R(5,5) Parallel Search — {cores} workers (of {cpu_count()} cores)")
    print("=" * 60)

    for target_n in [38, 39, 40, 41, 42]:
        print(f"\n{'='*60}")
        print(f"Target: n={target_n}")
        print(f"{'='*60}")

        # Phase 1: Parallel circulant search
        print(f"\n  Phase 1: Circulant search ({cores} workers)")
        t0 = time.time()

        num_trials = 50000
        batch_size = cores * 10
        best_E = float('inf')
        best_adj = None
        found = False

        with Pool(cores) as pool:
            for batch_start in range(0, num_trials, batch_size):
                tasks = [(target_n, batch_start + i) for i in range(min(batch_size, num_trials - batch_start))]
                results = pool.map(make_circulant, tasks)

                for E, diffs, adj_flat in results:
                    if E < best_E:
                        best_E = E
                        best_adj = adj_flat.reshape(target_n, target_n).copy()
                        if E == 0:
                            found = True
                            break
                if found:
                    break

                elapsed = time.time() - t0
                rate = (batch_start + len(tasks)) / elapsed
                print(f"    {batch_start + len(tasks)}/{num_trials} circulants, best E={best_E}, {rate:.0f}/s", flush=True)

        elapsed = time.time() - t0
        print(f"  Circulant result: E={best_E} [{elapsed:.1f}s]")

        if best_E == 0:
            print(f"  CIRCULANT FOUND at n={target_n}!")
            np.save(f"r55_n{target_n}.npy", best_adj)
            print(f"  Saved to r55_n{target_n}.npy")
            continue

        # Phase 2: Parallel SA from best circulant + random seeds
        if best_E <= 20:
            print(f"\n  Phase 2: Parallel SA refinement ({cores} workers)")
            t0 = time.time()

            sa_steps = target_n * target_n * 100
            tasks = [(target_n, 1000 + i, sa_steps) for i in range(cores)]

            with Pool(cores) as pool:
                results = pool.map(sa_worker, tasks)

            for E, adj_flat in results:
                if E < best_E:
                    best_E = E
                    best_adj = adj_flat.reshape(target_n, target_n).copy()

            elapsed = time.time() - t0
            print(f"  SA result: best E={best_E} [{elapsed:.1f}s]")

            if best_E == 0:
                print(f"  SA FOUND at n={target_n}!")
                np.save(f"r55_n{target_n}.npy", best_adj)
                print(f"  Saved to r55_n{target_n}.npy")
                continue

        print(f"  Could not reach E=0 at n={target_n}. Best E={best_E}")
        if best_E > 50:
            print(f"  Stopping — energy too high to continue.")
            break

    print("\nDone.")
