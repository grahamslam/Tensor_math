"""Quick verification of the current best graph from the running SA."""
import numpy as np
import time
import sys
import json
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


# The SA saves its best adjacency matrix whenever best_E improves.
# But we didn't add that save yet -- so let's reconstruct from the seed
# and run the SA just long enough to hit the best_E=0.143 state.
# Actually, easier: modify the running SA to dump its best. But we can't
# interrupt it. So let's run a fresh short SA from the same seed and
# verify whatever it finds quickly.

# Better approach: the SA script already triggers verification at E < 5.0
# at the END of all trials. But we want it NOW.

# Simplest: run a very short SA, grab first E~0 candidate, verify it.

print("R(5,5) Quick Verify -- short SA from n=38 seed, verify first candidate")
print("=" * 60)

seed = np.load('r55_n38.npy')
print(f"Loaded seed n={seed.shape[0]}")

n = 39
rng = np.random.RandomState(42)

# Extend seed
adj = np.zeros((n, n), dtype=np.int8)
adj[:38, :38] = seed
for i in range(38, n):
    for j in range(i):
        if rng.random() < 0.5:
            adj[i, j] = adj[j, i] = 1

# Quick SA -- just enough to clear any 5-violations
print(f"\nRunning short SA at n={n}...")
t0 = time.time()

C = 1 - adj.copy()
np.fill_diagonal(C, 0)
kr = full_count(adj, 5, n)
is_ = full_count(C, 5, n)
E = kr + is_
print(f"  Initial: K5={kr} I5={is_} E={E}")

if E == 0:
    print(f"  Already clean! No SA needed.")
else:
    best_adj = adj.copy()
    best_E = E
    T = 2.0
    max_steps = n * n * 500
    cooling = 1.0 - 5.0 / max_steps

    for step in range(max_steps):
        u, v = rng.randint(0, n, 2)
        if u == v:
            continue
        if u > v:
            u, v = v, u

        adj[u, v] = 1 - adj[u, v]
        adj[v, u] = adj[u, v]

        C = 1 - adj
        np.fill_diagonal(C, 0)
        newE = full_count(adj, 5, n) + full_count(C, 5, n)

        if newE <= E or rng.random() < np.exp(-(newE - E) / max(T, 0.01)):
            E = newE
            if E < best_E:
                best_E = E
                best_adj = adj.copy()
            if E == 0:
                print(f"  Hit E=0 at step {step}! [{time.time()-t0:.1f}s]")
                break
        else:
            adj[u, v] = 1 - adj[u, v]
            adj[v, u] = adj[u, v]

        T *= cooling

        if step % 10000 == 0 and step > 0:
            print(f"  step {step}/{max_steps} E={E} best={best_E} T={T:.4f}", flush=True)

    adj = best_adj
    E = best_E

print(f"\n{'='*60}")
print(f"FULL VERIFICATION at n={n}")
print(f"{'='*60}")

t1 = time.time()
C = 1 - adj
np.fill_diagonal(C, 0)
kr = full_count(adj, 5, n)
print(f"  K5 (5-cliques): {kr}  [{time.time()-t1:.1f}s]")
t2 = time.time()
is_ = full_count(C, 5, n)
print(f"  I5 (5-indep):   {is_}  [{time.time()-t2:.1f}s]")

edges = int(adj.sum()) // 2
total = n * (n - 1) // 2
degs = adj.sum(axis=1)
print(f"  Edges: {edges}/{total} ({edges/total*100:.1f}%)")
print(f"  Degree range: {degs.min()}-{degs.max()} (mean={degs.mean():.1f}, var={np.var(degs):.1f})")

if kr + is_ == 0:
    print(f"\n  ** VERIFIED: n={n} is an R(5,5) avoider! **")
    np.save(f'r55_n{n}_verified.npy', adj)
    print(f"  Saved to r55_n{n}_verified.npy")
else:
    print(f"\n  Not an avoider: {kr + is_} violations")

print(f"\nTotal time: {time.time()-t0:.1f}s")
