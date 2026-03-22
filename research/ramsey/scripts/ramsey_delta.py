"""
R(5,5) Delta-Energy SA -- exact energy updates in O(n^3) per step.

When flipping edge (u,v), only 5-cliques containing BOTH u and v can change.
(A clique through u but not v is unaffected by the u-v edge.)
So we only need to check (n-2 choose 3) = C(37,3) = 7770 subsets per step
instead of 2 * C(38,4) = 147K. That's ~19x faster.

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


def count_cliques_through_pair(A, u, v, k, n):
    """Count k-cliques containing BOTH u and v.
    Only need to find (k-2)-cliques among common structure."""
    if A[u, v] == 0:
        return 0  # u,v not connected, can't be in same clique
    others = [w for w in range(n) if w != u and w != v]
    count = 0
    for combo in combinations(others, k - 2):
        # Check all vertices connect to u and v
        all_ok = True
        for w in combo:
            if A[u, w] == 0 or A[v, w] == 0:
                all_ok = False
                break
        if not all_ok:
            continue
        # Check combo is a clique among themselves
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


def log_progress(data):
    with open(PROGRESS_FILE, 'a') as f:
        f.write(json.dumps(data) + '\n')


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


if __name__ == '__main__':
    print("R(5,5) Delta-Energy SA -- O(n^3) exact pair-delta updates")
    print("=" * 60)

    # Clear progress
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

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

        rng = np.random.RandomState()
        n = target_n
        max_steps = n * n * 500
        recount_interval = 5000
        trials = 5

        best_global_adj = None
        best_global_E = float('inf')

        for trial in range(trials):
            t_start = time.time()

            # Initialize
            if seed is not None and trial == 0:
                old_n = seed.shape[0]
                adj = np.zeros((n, n), dtype=np.int8)
                adj[:old_n, :old_n] = seed
                for i in range(old_n, n):
                    for j in range(i):
                        if rng.random() < 0.5:
                            adj[i, j] = adj[j, i] = 1
                init = f"ext({old_n}->{n})"
            else:
                is_prime = n >= 5 and all(n % d != 0 for d in range(2, int(n**0.5) + 1))
                if is_prime and n % 4 == 1 and trial == 0:
                    adj = paley(n)
                    init = "Paley"
                else:
                    adj = np.zeros((n, n), dtype=np.int8)
                    for i in range(n):
                        for j in range(i + 1, n):
                            if rng.random() < 0.5:
                                adj[i, j] = adj[j, i] = 1
                    init = "random"

            # Maintain complement
            comp = 1 - adj.copy()
            np.fill_diagonal(comp, 0)

            # Full initial energy
            E = full_count(adj, 5, n) + full_count(comp, 5, n)
            print(f"  Trial {trial+1}: init={init} E={E}", flush=True)

            if E == 0:
                print(f"    CLEAN! [{time.time()-t_start:.1f}s]")
                best_global_adj = adj.copy()
                best_global_E = 0
                break

            best_adj = adj.copy()
            best_E = E
            T = 2.0
            cooling = 1.0 - 4.0 / max_steps
            last_report = time.time()
            last_log = time.time()
            accept_count = 0
            step_count = 0

            for step in range(max_steps):
                u = rng.randint(0, n)
                v = rng.randint(0, n)
                if u == v:
                    continue
                if u > v:
                    u, v = v, u

                # Count 5-cliques through (u,v) pair BEFORE flip
                before_G = count_cliques_through_pair(adj, u, v, 5, n)
                before_C = count_cliques_through_pair(comp, u, v, 5, n)

                # Flip edge in both adj and complement
                adj[u, v] = 1 - adj[u, v]
                adj[v, u] = adj[u, v]
                comp[u, v] = 1 - comp[u, v]
                comp[v, u] = comp[u, v]

                # Count 5-cliques through (u,v) pair AFTER flip
                after_G = count_cliques_through_pair(adj, u, v, 5, n)
                after_C = count_cliques_through_pair(comp, u, v, 5, n)

                dE = (after_G + after_C) - (before_G + before_C)
                newE = E + dE
                step_count += 1

                if dE <= 0 or rng.random() < np.exp(-dE / max(T, 0.01)):
                    E = newE
                    accept_count += 1
                    if E <= 0:
                        # Verify with full count
                        real_E = full_count(adj, 5, n) + full_count(comp, 5, n)
                        if real_E == 0:
                            elapsed = time.time() - t_start
                            print(f"    FOUND at step {step}! E=0 [{elapsed:.1f}s]")
                            best_adj = adj.copy()
                            best_E = 0
                            break
                        else:
                            E = real_E
                    elif E < best_E:
                        best_E = E
                        best_adj = adj.copy()
                else:
                    # Undo flip in both
                    adj[u, v] = 1 - adj[u, v]
                    adj[v, u] = adj[u, v]
                    comp[u, v] = 1 - comp[u, v]
                    comp[v, u] = comp[u, v]

                T *= cooling

                # Periodic full recount to correct any drift
                if step > 0 and step % recount_interval == 0:
                    real_E = full_count(adj, 5, n) + full_count(comp, 5, n)
                    if real_E != E:
                        E = real_E

                # Log progress
                now = time.time()
                if now - last_log >= 2.0:
                    degs = adj.sum(axis=1).astype(float)
                    acc_rate = accept_count / max(step_count, 1)
                    log_progress({
                        'time': round(now - t_start, 1),
                        'wall': round(now, 1),
                        'n': n,
                        'trial': trial + 1,
                        'step': step,
                        'max_steps': max_steps,
                        'pct': round(step / max_steps * 100, 1),
                        'E': E,
                        'best_E': best_E,
                        'T': round(T, 6),
                        'accept_rate': round(acc_rate, 3),
                        'deg_var': round(float(np.var(degs)), 2),
                        'tri_G': 0, 'tri_C': 0,
                        'k5': E, 'i5': 0,
                        'k4': 0, 'i4': 0,
                        'violation': E,
                        'near_viol': 0,
                        'regularity': 0, 'balance': 0,
                    })
                    last_log = now

                if now - last_report > 20:
                    elapsed = now - t_start
                    rate = step / max(elapsed, 0.1)
                    acc_rate = accept_count / max(step_count, 1)
                    print(f"    step {step}/{max_steps} E={E} best={best_E} T={T:.4f} "
                          f"acc={acc_rate:.1%} {rate:.0f}st/s [{elapsed:.0f}s]", flush=True)
                    last_report = now

            elapsed = time.time() - t_start
            print(f"    final E={best_E} [{elapsed:.1f}s]", flush=True)

            if best_E < best_global_E:
                best_global_E = best_E
                best_global_adj = best_adj.copy()

            if best_E == 0:
                break

        if best_global_E == 0:
            print(f"\n  ** VERIFIED R(5,5) avoider at n={target_n}! **")
            edges = int(best_global_adj.sum()) // 2
            total_e = target_n * (target_n - 1) // 2
            degs = best_global_adj.sum(axis=1)
            print(f"  Edges: {edges}/{total_e} ({edges/total_e*100:.1f}%)")
            print(f"  Degree: {int(degs.min())}-{int(degs.max())} (mean={degs.mean():.1f})")
            np.save(f'r55_n{target_n}_verified.npy', best_global_adj)
            print(f"  Saved to r55_n{target_n}_verified.npy")
            seed = best_global_adj
        else:
            print(f"\n  Best E={best_global_E} at n={target_n}")
            if best_global_E > 100:
                print(f"  Too many violations, stopping.")
                break

    print("\nDone.")
