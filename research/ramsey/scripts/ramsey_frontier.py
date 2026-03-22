"""
R(5,5) Frontier Push — optimized SA with neighborhood-restricted energy.
For each edge flip (u,v), only recount cliques/independent-sets that
could be affected — those involving u or v.
"""
import numpy as np
import time
import sys
from itertools import combinations

sys.stdout.reconfigure(line_buffering=True)


def count_cliques_through_vertex(A, v, k, n):
    """Count k-cliques containing vertex v. O(n^(k-1)) worst case."""
    count = 0
    sub = [v]

    def go(start, depth):
        nonlocal count
        if depth == k:
            # Check all pairs
            for a in range(k):
                for b in range(a + 1, k):
                    if A[sub[a], sub[b]] == 0:
                        return
            count += 1
            return
        for w in range(start, n):
            if w == v:
                continue
            sub.append(w)
            go(w + 1, depth + 1)
            sub.pop()

    go(0, 1)
    return count


def full_count(A, k, n):
    """Full k-clique count."""
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


def fast_sa(n, r, s, trials=5, max_steps=None, verbose=True):
    """SA with periodic full recount to avoid drift."""
    rng = np.random.RandomState()
    if max_steps is None:
        max_steps = n * n * 400

    best_adj = None
    best_E = float('inf')

    for trial in range(trials):
        t_start = time.time()

        # Initialize
        is_prime = n >= 5 and all(n % d != 0 for d in range(2, int(n**0.5) + 1))
        if is_prime and n % 4 == 1 and trial == 0:
            qr = set()
            for x in range(1, n):
                qr.add((x * x) % n)
            adj = np.zeros((n, n), dtype=np.int8)
            for i in range(n):
                for j in range(n):
                    if i != j and (j - i) % n in qr:
                        adj[i, j] = 1
            init_method = "Paley"
        else:
            adj = np.zeros((n, n), dtype=np.int8)
            for i in range(n):
                for j in range(i + 1, n):
                    if rng.random() < 0.5:
                        adj[i, j] = adj[j, i] = 1
            init_method = "random"

        # Full initial energy
        C = 1 - adj.copy()
        np.fill_diagonal(C, 0)
        kr = full_count(adj, r, n)
        is_ = full_count(C, s, n)
        E = kr + is_

        if verbose:
            print(f"  Trial {trial+1}: init={init_method} E={E} (K{r}={kr} I{s}={is_})", end="", flush=True)

        if E == 0:
            if verbose:
                print(f" FOUND in {time.time()-t_start:.1f}s")
            return adj, 0, trial + 1

        T = 2.0
        cooling = 1.0 - 4.0 / max_steps
        recount_interval = max(1000, n * 50)  # full recount periodically
        last_report = time.time()

        for step in range(max_steps):
            u = rng.randint(0, n)
            v = rng.randint(0, n)
            if u == v:
                continue
            if u > v:
                u, v = v, u

            # Count cliques through u and v BEFORE flip
            kr_uv_before = count_cliques_through_vertex(adj, u, r, n) + count_cliques_through_vertex(adj, v, r, n)
            C = 1 - adj; np.fill_diagonal(C, 0)
            is_uv_before = count_cliques_through_vertex(C, u, s, n) + count_cliques_through_vertex(C, v, s, n)

            # Flip
            adj[u, v] = 1 - adj[u, v]
            adj[v, u] = adj[u, v]

            # Count cliques through u and v AFTER flip
            kr_uv_after = count_cliques_through_vertex(adj, u, r, n) + count_cliques_through_vertex(adj, v, r, n)
            C = 1 - adj; np.fill_diagonal(C, 0)
            is_uv_after = count_cliques_through_vertex(C, u, s, n) + count_cliques_through_vertex(C, v, s, n)

            # Delta (cliques through u,v changed; others unchanged)
            dE = (kr_uv_after - kr_uv_before) + (is_uv_after - is_uv_before)
            newE = E + dE

            if dE <= 0 or rng.random() < np.exp(-dE / max(T, 0.01)):
                E = newE
                if E <= 0:
                    # Verify with full count
                    C = 1 - adj; np.fill_diagonal(C, 0)
                    real_E = full_count(adj, r, n) + full_count(C, s, n)
                    if real_E == 0:
                        if verbose:
                            print(f" FOUND at step {step} [{time.time()-t_start:.1f}s]")
                        return adj, 0, trial + 1
                    else:
                        E = real_E  # correct drift
            else:
                adj[u, v] = 1 - adj[u, v]
                adj[v, u] = adj[u, v]

            T *= cooling

            # Periodic full recount to correct accumulated errors
            if step > 0 and step % recount_interval == 0:
                C = 1 - adj; np.fill_diagonal(C, 0)
                real_E = full_count(adj, r, n) + full_count(C, s, n)
                if abs(real_E - E) > 0:
                    E = real_E

            if verbose and time.time() - last_report > 30:
                elapsed = time.time() - t_start
                pct = step / max_steps * 100
                print(f" E={E}({pct:.0f}%)", end="", flush=True)
                last_report = time.time()

        if verbose:
            C = 1 - adj; np.fill_diagonal(C, 0)
            real_E = full_count(adj, r, n) + full_count(C, s, n)
            print(f" final E={real_E} [{time.time()-t_start:.1f}s]")
            E = real_E

        if E < best_E:
            best_E = E
            best_adj = adj.copy()

    return best_adj, best_E, trials


if __name__ == '__main__':
    print("R(5,5) Frontier Push")
    print("=" * 60)

    for n in [37, 38, 39, 40, 41, 42]:
        print(f"\n--- n={n} ---")
        t0 = time.time()
        adj, E, trial = fast_sa(n, 5, 5, trials=2, max_steps=n*n*300)
        if E == 0:
            # Verify
            C = 1 - adj; np.fill_diagonal(C, 0)
            k5 = full_count(adj, 5, n)
            i5 = full_count(C, 5, n)
            edges = int(adj.sum()) // 2
            total = n * (n-1) // 2
            print(f"  VERIFIED: K5={k5} I5={i5} edges={edges}/{total} ({edges/total*100:.1f}%)")
            np.save(f"r55_n{n}.npy", adj)
        print(f"  Total time: {time.time()-t0:.1f}s")
