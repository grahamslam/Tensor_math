"""
Phase 2: Extension analysis -- for each of the 656 R(5,5,42)-graphs,
how close can we get to extending to n=43?

For each graph, run SA on the 42-bit connection vector for the new vertex.
Report minimum new-vertex violations achievable.
"""
import numpy as np
import networkx as nx
import time
import sys
import json
from itertools import combinations

sys.stdout.reconfigure(line_buffering=True)


def graph6_to_adj(g6_string):
    G = nx.from_graph6_bytes(g6_string.encode())
    return nx.to_numpy_array(G, dtype=np.int8)


def count_new_vertex_violations(adj_base, conn, n_base):
    """Count K5s and I5s involving the new vertex."""
    neighbors = [j for j in range(n_base) if conn[j] == 1]
    non_neighbors = [j for j in range(n_base) if conn[j] == 0]

    k5 = 0
    for combo in combinations(neighbors, 4):
        if all(adj_base[combo[a], combo[b]] == 1 for a in range(4) for b in range(a + 1, 4)):
            k5 += 1

    i5 = 0
    for combo in combinations(non_neighbors, 4):
        if all(adj_base[combo[a], combo[b]] == 0 for a in range(4) for b in range(a + 1, 4)):
            i5 += 1

    return k5, i5


def sa_extension(adj_base, n_base, num_restarts=5, steps=50000):
    """SA to find best connection vector for new vertex."""
    rng = np.random.RandomState()
    best_E = float('inf')
    best_conn = None
    best_k5 = 0
    best_i5 = 0

    for restart in range(num_restarts):
        conn = np.zeros(n_base, dtype=np.int8)
        for j in range(n_base):
            if rng.random() < 0.5:
                conn[j] = 1

        k5, i5 = count_new_vertex_violations(adj_base, conn, n_base)
        E = k5 + i5
        T = 1.0
        cooling = 1.0 - 5.0 / steps

        for step in range(steps):
            j = rng.randint(0, n_base)
            conn[j] = 1 - conn[j]
            nk5, ni5 = count_new_vertex_violations(adj_base, conn, n_base)
            nE = nk5 + ni5
            dE = nE - E
            if dE <= 0 or rng.random() < np.exp(-dE / max(T, 0.005)):
                E = nE
                k5, i5 = nk5, ni5
                if E < best_E:
                    best_E = E
                    best_conn = conn.copy()
                    best_k5 = k5
                    best_i5 = i5
                if E == 0:
                    return 0, 0, 0, best_conn
            else:
                conn[j] = 1 - conn[j]
            T *= cooling

    return best_E, best_k5, best_i5, best_conn


if __name__ == '__main__':
    print("Phase 2: Extension Analysis -- Can any R(5,5,42)-graph extend to n=43?")
    print("=" * 60)

    with open('r55_42some.g6', 'r') as f:
        g6_lines = [line.strip() for line in f if line.strip()]
    print(f"Loaded {len(g6_lines)} graphs")

    n_base = 42
    results = []
    t0 = time.time()

    for i, g6 in enumerate(g6_lines):
        adj = graph6_to_adj(g6)

        # Try original
        E, k5, i5, conn = sa_extension(adj, n_base, num_restarts=1, steps=5000)
        results.append({
            'idx': i, 'source': 'original',
            'best_E': E, 'k5': k5, 'i5': i5,
            'conn_degree': int(conn.sum()) if conn is not None else 0,
        })

        # Try complement
        C = 1 - adj.copy()
        np.fill_diagonal(C, 0)
        Ec, k5c, i5c, connc = sa_extension(C, n_base, num_restarts=1, steps=5000)
        results.append({
            'idx': i + 328, 'source': 'complement',
            'best_E': Ec, 'k5': k5c, 'i5': i5c,
            'conn_degree': int(connc.sum()) if connc is not None else 0,
        })

        if (i + 1) % 10 == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (len(g6_lines) - i - 1) / rate
            best_so_far = min(r['best_E'] for r in results)
            print(f"  {i+1}/{len(g6_lines)} best_ext={best_so_far} [{elapsed:.0f}s, ETA {eta:.0f}s]",
                  flush=True)

        if E == 0 or Ec == 0:
            print(f"\n  *** GRAPH {i} EXTENDS TO n=43! E={min(E,Ec)} ***")
            break

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s")

    # Summary
    ext_energies = [r['best_E'] for r in results]
    print(f"\n{'='*60}")
    print("EXTENSION SUMMARY")
    print(f"{'='*60}")
    print(f"Graphs analyzed: {len(results)}")
    print(f"Min extension violations: {min(ext_energies)}")
    print(f"Max extension violations: {max(ext_energies)}")
    print(f"Mean extension violations: {np.mean(ext_energies):.1f}")
    print(f"Graphs with E <= 5: {sum(1 for e in ext_energies if e <= 5)}")
    print(f"Graphs with E <= 10: {sum(1 for e in ext_energies if e <= 10)}")
    print(f"Graphs with E <= 20: {sum(1 for e in ext_energies if e <= 20)}")
    print(f"Graphs with E = 0: {sum(1 for e in ext_energies if e == 0)}")

    # Distribution
    from collections import Counter
    dist = Counter(ext_energies)
    print(f"\nViolation distribution (top 15):")
    for E, count in sorted(dist.items())[:15]:
        bar = '#' * count
        print(f"  E={E:3d}: {count:3d} {bar}")

    # Save
    with open('extension_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved to extension_analysis.json")
