"""
Replicate the hybrid SA's best state and verify it.
Uses the same seed (rng state 0) and extension logic, then runs
a quick SA with the FAST sampled energy to find a low-E state,
then verifies with full count.

Since full verification is only 0.5s at n=39, we can check frequently.
"""
import numpy as np
import time
import sys
from itertools import combinations

sys.stdout.reconfigure(line_buffering=True)


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


def sample_k_cliques(A, n, k, num_samples, rng):
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
    return found


def fast_energy(A, n, rng, sample_size=200):
    """Sampled energy -- no triangles."""
    C = 1 - A
    np.fill_diagonal(C, 0)
    k5 = sample_k_cliques(A, n, 5, sample_size, rng)
    i5 = sample_k_cliques(C.astype(np.int8), n, 5, sample_size, rng)
    k4 = sample_k_cliques(A, n, 4, sample_size, rng)
    i4 = sample_k_cliques(C.astype(np.int8), n, 4, sample_size, rng)
    degs = A.sum(axis=1).astype(float)
    deg_var = float(np.var(degs))
    target_deg = (n - 1) / 2.0
    return (k5 + i5) * 100 + (k4 + i4) * 0.5 + (deg_var / max(target_deg, 1)) * 2, k5, i5


print("R(5,5) Fast SA + Frequent Full Verification")
print("=" * 60)

seed = np.load('r55_n38.npy')
n = 39
rng = np.random.RandomState()

# Extend seed
adj = np.zeros((n, n), dtype=np.int8)
adj[:38, :38] = seed
for i in range(38, n):
    for j in range(i):
        if rng.random() < 0.5:
            adj[i, j] = adj[j, i] = 1

E, k5, i5 = fast_energy(adj, n, rng)
print(f"Initial sampled E={E:.2f} k5={k5} i5={i5}")

best_adj = adj.copy()
best_E = E
T = 2.0
max_steps = 5000000
cooling = 1.0 - 3.0 / max_steps
verify_interval = 50000  # full verify every 50K steps
last_report = time.time()
t0 = time.time()
verified_count = 0

for step in range(max_steps):
    u = rng.randint(0, n)
    v = rng.randint(0, n)
    if u == v:
        continue
    if u > v:
        u, v = v, u

    adj[u, v] = 1 - adj[u, v]
    adj[v, u] = adj[u, v]

    newE, nk5, ni5 = fast_energy(adj, n, rng)
    dE = newE - E

    if dE <= 0 or rng.random() < np.exp(-dE / max(T, 0.001)):
        E = newE
        if E < best_E:
            best_E = E
            best_adj = adj.copy()
    else:
        adj[u, v] = 1 - adj[u, v]
        adj[v, u] = adj[u, v]

    T *= cooling

    # Full verification on best graph periodically
    if step > 0 and step % verify_interval == 0:
        C = 1 - best_adj
        np.fill_diagonal(C, 0)
        kr = full_count(best_adj, 5, n)
        is_ = full_count(C, 5, n)
        verified_count += 1
        elapsed = time.time() - t0
        rate = step / elapsed

        print(f"  [{step/1000:.0f}K steps, {elapsed:.0f}s, {rate:.0f}st/s] "
              f"sampled bestE={best_E:.3f} | FULL: K5={kr} I5={is_} total={kr+is_} T={T:.4f}",
              flush=True)

        if kr + is_ == 0:
            print(f"\n  ** VERIFIED R(5,5) AVOIDER AT n={n}! **")
            edges = int(best_adj.sum()) // 2
            total_e = n * (n - 1) // 2
            degs = best_adj.sum(axis=1)
            print(f"  Edges: {edges}/{total_e} ({edges/total_e*100:.1f}%)")
            print(f"  Degree range: {int(degs.min())}-{int(degs.max())}")
            np.save(f'r55_n{n}_verified.npy', best_adj)
            print(f"  Saved to r55_n{n}_verified.npy")
            print(f"  Total time: {time.time()-t0:.1f}s, {verified_count} verifications")
            sys.exit(0)

print(f"\nDid not find clean graph in {max_steps} steps.")
C = 1 - best_adj
np.fill_diagonal(C, 0)
kr = full_count(best_adj, 5, n)
is_ = full_count(C, 5, n)
print(f"Final best: K5={kr} I5={is_}")
