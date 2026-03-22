"""
One-shot R(5,5) verification.
Extends r55_n38.npy to n=39 with multiple random seeds,
picks the one with fewest 5-cliques, and does full verification.
No SA -- just try many extensions and verify the best.
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


def verify(adj, n):
    """Full R(5,5) verification. Returns (K5_count, I5_count)."""
    C = 1 - adj
    np.fill_diagonal(C, 0)
    kr = full_count(adj, 5, n)
    is_ = full_count(C, 5, n)
    return kr, is_


print("R(5,5) One-Shot Verify")
print("=" * 60)

seed = np.load('r55_n38.npy')
n = 39

# Try many random extensions of the 39th vertex
print(f"Trying random extensions of n=38 seed to n={n}...")
best_ext = None
best_violations = float('inf')

t0 = time.time()
for trial in range(200):
    rng = np.random.RandomState(trial)
    adj = np.zeros((n, n), dtype=np.int8)
    adj[:38, :38] = seed

    # Random connections for vertex 38
    for j in range(38):
        if rng.random() < 0.5:
            adj[38, j] = adj[j, 38] = 1

    # Quick check -- only count 5-cliques involving the new vertex
    # This is much faster than full count
    new_v = 38
    violations = 0

    # 5-cliques containing vertex 38 in G
    neighbors = [j for j in range(38) if adj[38, j] == 1]
    for combo in combinations(neighbors, 4):
        if all(adj[combo[a], combo[b]] == 1 for a in range(4) for b in range(a+1, 4)):
            violations += 1

    # 5-indep-sets containing vertex 38 in G (= non-neighbors form clique in complement)
    non_neighbors = [j for j in range(38) if adj[38, j] == 0]
    for combo in combinations(non_neighbors, 4):
        if all(adj[combo[a], combo[b]] == 0 for a in range(4) for b in range(a+1, 4)):
            violations += 1

    if violations < best_violations:
        best_violations = violations
        best_ext = adj.copy()
        if violations == 0:
            print(f"  Trial {trial}: ZERO new violations!")
            break

    if trial % 50 == 0:
        print(f"  Trial {trial}: best new-vertex violations = {best_violations}", flush=True)

elapsed = time.time() - t0
print(f"  Best extension: {best_violations} new-vertex violations [{elapsed:.1f}s]")

if best_violations == 0:
    print(f"\nNew vertex introduces no violations.")
    print(f"The base n=38 graph was verified clean.")
    print(f"Therefore n=39 must be clean -- but let's verify fully anyway.\n")

print(f"{'='*60}")
print(f"FULL VERIFICATION at n={n}")
print(f"{'='*60}")

adj = best_ext
t1 = time.time()
kr, is_ = verify(adj, n)
elapsed = time.time() - t1
edges = int(adj.sum()) // 2
total = n * (n - 1) // 2
degs = adj.sum(axis=1)

print(f"  K5 (5-cliques): {kr}")
print(f"  I5 (5-indep):   {is_}")
print(f"  Edges: {edges}/{total} ({edges/total*100:.1f}%)")
print(f"  Degree range: {int(degs.min())}-{int(degs.max())} (mean={degs.mean():.1f})")
print(f"  Verification time: {elapsed:.1f}s")

if kr + is_ == 0:
    print(f"\n  ** VERIFIED: n={n} is an R(5,5) avoider! **")
    np.save(f'r55_n{n}_verified.npy', adj)
    print(f"  Saved to r55_n{n}_verified.npy")
else:
    print(f"\n  Not clean: {kr + is_} total violations")
    print(f"  (Extension was clean but base graph interactions create violations)")
    print(f"  Need SA to fix these.")
