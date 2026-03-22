"""
Break the {11,13,28} triangle trap in Graph 41.

Strategy: remove one edge from the triangle, check if the modified
42-vertex graph is still R(5,5)-avoiding, then try extending to n=43.

If removing one edge creates violations in the base graph, try flipping
other edges to compensate (targeted SA on the base graph with the
constraint that the triangle edge stays removed).
"""
import numpy as np
import networkx as nx
import time
import sys
import json
from itertools import combinations

sys.stdout.reconfigure(line_buffering=True)


def graph6_to_adj(g6):
    return nx.to_numpy_array(nx.from_graph6_bytes(g6.encode()), dtype=np.int8)


def full_energy(adj, n):
    C = 1 - adj.copy()
    np.fill_diagonal(C, 0)
    k5 = i5 = 0
    for combo in combinations(range(n), 5):
        if all(adj[combo[a], combo[b]] == 1 for a in range(5) for b in range(a+1, 5)):
            k5 += 1
        if all(C[combo[a], combo[b]] == 1 for a in range(5) for b in range(a+1, 5)):
            i5 += 1
    return k5, i5


def find_violations(adj, n):
    C = 1 - adj.copy()
    np.fill_diagonal(C, 0)
    k5s = []
    i5s = []
    for combo in combinations(range(n), 5):
        if all(adj[combo[a], combo[b]] == 1 for a in range(5) for b in range(a+1, 5)):
            k5s.append(combo)
        if all(C[combo[a], combo[b]] == 1 for a in range(5) for b in range(a+1, 5)):
            i5s.append(combo)
    return k5s, i5s


def count_new_vertex_violations(adj, conn, n):
    neighbors = [j for j in range(n) if conn[j] == 1]
    non_neighbors = [j for j in range(n) if conn[j] == 0]
    k5 = sum(1 for c in combinations(neighbors, 4)
             if all(adj[c[a], c[b]] == 1 for a in range(4) for b in range(a+1, 4)))
    i5 = sum(1 for c in combinations(non_neighbors, 4)
             if all(adj[c[a], c[b]] == 0 for a in range(4) for b in range(a+1, 4)))
    return k5, i5


def sa_extension(adj, n, num_restarts=10, steps=20000):
    rng = np.random.RandomState()
    best_E = 999
    best_conn = None
    for restart in range(num_restarts):
        conn = np.random.randint(0, 2, n, dtype=np.int8)
        k5, i5 = count_new_vertex_violations(adj, conn, n)
        E = k5 + i5
        T = 1.0
        cooling = 1.0 - 5.0 / steps
        for step in range(steps):
            j = rng.randint(0, n)
            conn[j] = 1 - conn[j]
            nk5, ni5 = count_new_vertex_violations(adj, conn, n)
            nE = nk5 + ni5
            if nE - E <= 0 or rng.random() < np.exp(-(nE - E) / max(T, 0.005)):
                E = nE
                if E < best_E:
                    best_E = E
                    best_conn = conn.copy()
                if E == 0:
                    return 0, best_conn
            else:
                conn[j] = 1 - conn[j]
            T *= cooling
    return best_E, best_conn


def targeted_base_sa(adj_orig, n, forbidden_edge, max_steps=500000):
    """SA on the base graph: flip edges to restore R(5,5) avoidance
    while keeping forbidden_edge removed."""
    rng = np.random.RandomState()
    adj = adj_orig.copy()
    u_f, v_f = forbidden_edge

    # Ensure forbidden edge is removed
    adj[u_f, v_f] = 0
    adj[v_f, u_f] = 0

    k5s, i5s = find_violations(adj, n)
    E = len(k5s) + len(i5s)
    best_E = E
    best_adj = adj.copy()

    print(f"    Base SA start: E={E} (K5={len(k5s)} I5={len(i5s)})")

    T = 0.5
    cooling = 1.0 - 5.0 / max_steps

    for step in range(max_steps):
        u = rng.randint(0, n)
        v = rng.randint(0, n)
        if u == v:
            continue
        if u > v:
            u, v = v, u
        # Don't flip the forbidden edge back
        if (u, v) == (min(u_f, v_f), max(u_f, v_f)):
            continue

        adj[u, v] = 1 - adj[u, v]
        adj[v, u] = adj[u, v]

        nk5s, ni5s = find_violations(adj, n)
        nE = len(nk5s) + len(ni5s)
        dE = nE - E

        if dE <= 0 or rng.random() < np.exp(-dE / max(T, 0.005)):
            E = nE
            if E < best_E:
                best_E = E
                best_adj = adj.copy()
            if E == 0:
                print(f"    Base SA CLEAN at step {step}!")
                return adj, 0
        else:
            adj[u, v] = 1 - adj[u, v]
            adj[v, u] = adj[u, v]

        T *= cooling

        if step % 50000 == 0 and step > 0:
            print(f"    step {step}/{max_steps} E={E} best={best_E} T={T:.4f}", flush=True)

    return best_adj, best_E


if __name__ == '__main__':
    print("R(5,5) Trap Breaker — Modify Graph 41 base to enable extension")
    print("=" * 60)

    with open('r55_42some.g6') as f:
        g6_lines = [l.strip() for l in f if l.strip()]

    adj41 = graph6_to_adj(g6_lines[41])
    n = 42

    # The trap triangle
    trap_edges = [(11, 13), (11, 28), (13, 28)]

    # Also try edges involving the non-shared vertices (10, 18)
    extra_edges = [(10, 11), (10, 13), (10, 28), (18, 11), (18, 13), (18, 28)]

    print(f"\nOriginal Graph 41:")
    k5, i5 = full_energy(adj41, n)
    print(f"  Base: K5={k5} I5={i5} (should be 0,0)")

    t0 = time.time()

    for u, v in trap_edges + extra_edges:
        print(f"\n{'='*60}")
        print(f"Removing edge ({u},{v})  [was {'present' if adj41[u,v]==1 else 'absent'}]")
        print(f"{'='*60}")

        if adj41[u, v] == 0:
            print(f"  Edge not present, trying ADD instead")
            test_adj = adj41.copy()
            test_adj[u, v] = 1
            test_adj[v, u] = 1
        else:
            test_adj = adj41.copy()
            test_adj[u, v] = 0
            test_adj[v, u] = 0

        k5, i5 = full_energy(test_adj, n)
        print(f"  After modification: K5={k5} I5={i5} total={k5+i5}")

        if k5 + i5 == 0:
            print(f"  ** STILL R(5,5)-AVOIDING! Testing extension... **")
            ext_E, ext_conn = sa_extension(test_adj, n, num_restarts=10, steps=20000)
            print(f"  Extension result: E={ext_E}")
            if ext_E == 0:
                print(f"\n  *** R(5,5) AVOIDER AT n=43 FOUND! ***")
                # Build and verify full 43-vertex graph
                adj43 = np.zeros((43, 43), dtype=np.int8)
                adj43[:42, :42] = test_adj
                for j in range(42):
                    adj43[42, j] = adj43[j, 42] = ext_conn[j]
                k5f, i5f = full_energy(adj43, 43)
                print(f"  Full verification: K5={k5f} I5={i5f}")
        elif k5 + i5 <= 5:
            print(f"  Only {k5+i5} violations. Trying targeted SA to fix base...")
            fixed_adj, fixed_E = targeted_base_sa(test_adj, n,
                                                   (u, v) if adj41[u,v]==1 else (-1,-1),
                                                   max_steps=200000)
            print(f"  SA result: E={fixed_E}")
            if fixed_E == 0:
                print(f"  ** Fixed! Testing extension... **")
                ext_E, ext_conn = sa_extension(fixed_adj, n, num_restarts=10, steps=20000)
                print(f"  Extension result: E={ext_E}")
                if ext_E == 0:
                    print(f"\n  *** R(5,5) AVOIDER AT n=43 FOUND! ***")
        else:
            print(f"  Too many violations ({k5+i5}), skipping")

    elapsed = time.time() - t0
    print(f"\nTotal time: {elapsed:.1f}s")
    print("Done.")
