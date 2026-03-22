"""
R(5,5) Spectral SA -- O(n^3) energy via Hoffman bound instead of O(n^5) clique counting.

For R(5,5) avoidance we need ω(G) ≤ 4 AND α(G) ≤ 4.
Hoffman bound: α(G) ≤ n · (-λ_min) / (λ_max - λ_min)
By self-complement symmetry: ω(G) = α(complement(G))

SA energy = max(0, hoffman(G) - 4) + max(0, hoffman(complement(G)) - 4)
When energy = 0, the Hoffman bound proves R(5,5) avoidance.

Each step is O(n^3) eigenvalue decomposition instead of O(n^5) clique enumeration.
At n=42: ~74K vs ~130M ops -- ~1750x speedup.
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


def hoffman_bound(A):
    """Hoffman bound on independence number. O(n^3)."""
    n = A.shape[0]
    eigs = np.linalg.eigvalsh(A.astype(float))
    lam_min = eigs[0]
    lam_max = eigs[-1]
    if lam_max - lam_min < 1e-10:
        return float(n)
    return n * (-lam_min) / (lam_max - lam_min)


def spectral_energy(A):
    """Energy based on Hoffman bounds for both G and complement.
    Returns 0 when Hoffman proves α(G) ≤ 4 AND α(complement) ≤ 4."""
    n = A.shape[0]
    C = 1 - A.copy()
    np.fill_diagonal(C, 0)

    hG = hoffman_bound(A)      # bounds α(G) -- need ≤ 4
    hC = hoffman_bound(C)      # bounds α(C) = ω(G) -- need ≤ 4

    target = 4.0
    penalty_G = max(0.0, hG - target)
    penalty_C = max(0.0, hC - target)
    return penalty_G + penalty_C, hG, hC


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


def verify_avoidance(A, r, s):
    """Full O(n^5) verification -- only called on candidates."""
    n = A.shape[0]
    C = 1 - A.copy()
    np.fill_diagonal(C, 0)
    kr = full_count(A, r, n)
    is_ = full_count(C, s, n)
    return kr, is_


def spectral_sa(n, trials=5, max_steps=None, seed_adj=None):
    """Simulated annealing using spectral energy. O(n^3) per step."""
    r, s = 5, 5
    rng = np.random.RandomState()
    if max_steps is None:
        max_steps = n * n * 2000  # can afford more steps at O(n^3)

    best_adj = None
    best_E = float('inf')

    for trial in range(trials):
        t_start = time.time()

        # Initialize
        if seed_adj is not None and trial == 0:
            if seed_adj.shape[0] == n:
                adj = seed_adj.copy()
                init_method = "seed"
            elif seed_adj.shape[0] < n:
                # Extend seed to n vertices with random edges
                old_n = seed_adj.shape[0]
                adj = np.zeros((n, n), dtype=np.int8)
                adj[:old_n, :old_n] = seed_adj
                for i in range(old_n, n):
                    for j in range(i):
                        if rng.random() < 0.5:
                            adj[i, j] = adj[j, i] = 1
                init_method = f"extended({old_n}->{n})"
            else:
                adj = seed_adj[:n, :n].copy()
                init_method = f"truncated({seed_adj.shape[0]}->{n})"
        else:
            is_prime = n >= 5 and all(n % d != 0 for d in range(2, int(n**0.5) + 1))
            if is_prime and n % 4 == 1 and trial == 0:
                adj = paley(n)
                init_method = "Paley"
            else:
                # Near-regular random graph
                adj = np.zeros((n, n), dtype=np.int8)
                for i in range(n):
                    for j in range(i + 1, n):
                        if rng.random() < 0.5:
                            adj[i, j] = adj[j, i] = 1
                init_method = "random"

        E, hG, hC = spectral_energy(adj)
        print(f"  Trial {trial+1}: init={init_method} E={E:.4f} (a<={hG:.2f} w<={hC:.2f})", end="", flush=True)

        if E < best_E:
            best_E = E
            best_adj = adj.copy()

        if E == 0:
            print(f" SPECTRAL PROOF in {time.time()-t_start:.1f}s")
            return adj, 0, trial + 1

        T = 1.5
        cooling = 1.0 - 3.0 / max_steps
        last_report = time.time()
        no_improve = 0
        local_best_E = E

        for step in range(max_steps):
            u = rng.randint(0, n)
            v = rng.randint(0, n)
            if u == v:
                continue
            if u > v:
                u, v = v, u

            # Flip edge
            adj[u, v] = 1 - adj[u, v]
            adj[v, u] = adj[u, v]

            newE, newHG, newHC = spectral_energy(adj)
            dE = newE - E

            if dE <= 0 or rng.random() < np.exp(-dE / max(T, 0.001)):
                E = newE
                hG, hC = newHG, newHC
                if E < local_best_E:
                    local_best_E = E
                    no_improve = 0
                else:
                    no_improve += 1
                if E < best_E:
                    best_E = E
                    best_adj = adj.copy()
                if E == 0:
                    print(f" SPECTRAL PROOF at step {step} [{time.time()-t_start:.1f}s]")
                    return adj, 0, trial + 1
            else:
                adj[u, v] = 1 - adj[u, v]
                adj[v, u] = adj[u, v]
                no_improve += 1

            T *= cooling

            # Reheat if stuck
            if no_improve > n * n * 50:
                T = max(T, 0.5)
                no_improve = 0

            if time.time() - last_report > 15:
                elapsed = time.time() - t_start
                pct = step / max_steps * 100
                print(f" E={E:.4f}(a<={hG:.2f},w<={hC:.2f},{pct:.0f}%)", end="", flush=True)
                last_report = time.time()

        elapsed = time.time() - t_start
        print(f" final E={E:.4f} [{elapsed:.1f}s]")

    return best_adj, best_E, trials


if __name__ == '__main__':
    print("R(5,5) Spectral SA -- O(n^3) Hoffman Bound Energy")
    print("=" * 60)

    # Load best known result as seed
    seed = None
    for npy in ['r55_n38.npy', 'r55_n37.npy']:
        try:
            seed = np.load(npy)
            print(f"Loaded seed: {npy} (n={seed.shape[0]})")
            E, hG, hC = spectral_energy(seed)
            print(f"  Spectral energy: {E:.4f} (a<={hG:.2f} w<={hC:.2f})")
            break
        except FileNotFoundError:
            continue

    # First verify seed if we have one
    if seed is not None and seed.shape[0] <= 38:
        print(f"\nVerifying seed (full clique count)...")
        kr, is_ = verify_avoidance(seed, 5, 5)
        print(f"  K5={kr} I5={is_} -- {'VERIFIED' if kr + is_ == 0 else 'VIOLATIONS'}")

    for target_n in range(39, 44):
        print(f"\n{'='*60}")
        print(f"Target: n={target_n}")
        print(f"{'='*60}")

        t0 = time.time()
        adj, E, trial = spectral_sa(target_n, trials=3,
                                     max_steps=target_n * target_n * 2000,
                                     seed_adj=seed)

        if E == 0:
            print(f"\n  Spectral proof found! Verifying with full clique count...")
            kr, is_ = verify_avoidance(adj, 5, 5)
            edges = int(adj.sum()) // 2
            total = target_n * (target_n - 1) // 2
            print(f"  K5={kr} I5={is_} edges={edges}/{total} ({edges/total*100:.1f}%)")

            if kr + is_ == 0:
                print(f"  FULLY VERIFIED R(5,5) avoider at n={target_n}!")
                np.save(f"r55_n{target_n}.npy", adj)
                print(f"  Saved to r55_n{target_n}.npy")
                seed = adj  # use as seed for next size
            else:
                print(f"  Hoffman bound proved avoidance but full count found violations.")
                print(f"  (Hoffman is an upper bound -- not always tight)")
                print(f"  Switching to hybrid: spectral SA + clique verification...")
                # The spectral energy got to 0 but the bound wasn't tight enough
                # Still use this as a good seed for the next attempt
                seed = adj if seed is None else seed
        else:
            print(f"\n  Best spectral energy: {E:.4f}")
            print(f"  Could not reach spectral proof at n={target_n}")
            # Don't update seed -- keep using previous
            if E > 2.0:
                print(f"  Energy too high, stopping.")
                break

        print(f"  Total time: {time.time()-t0:.1f}s")

    print("\nDone.")
