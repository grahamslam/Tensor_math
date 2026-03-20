"""
Multi-edge trap breaker for Graph 41.

Remove edge (11,28) to break the K5 extension trap, then search for
1-2 additional edge flips among the conflict knot vertices {5,6,8,11,12,28}
and their neighbors to compensate for the 2 I5 violations created.

If any combination yields a clean n=42 base, test extension to n=43.
"""
import numpy as np
import networkx as nx
import time
import sys
import json
from itertools import combinations

sys.stdout.reconfigure(line_buffering=True)

RESULTS_FILE = "results.json"


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


def count_new_vertex_violations(adj, conn, n):
    neighbors = [j for j in range(n) if conn[j] == 1]
    non_neighbors = [j for j in range(n) if conn[j] == 0]
    k5 = sum(1 for c in combinations(neighbors, 4)
             if all(adj[c[a], c[b]] == 1 for a in range(4) for b in range(a+1, 4)))
    i5 = sum(1 for c in combinations(non_neighbors, 4)
             if all(adj[c[a], c[b]] == 0 for a in range(4) for b in range(a+1, 4)))
    return k5, i5


def sa_extension(adj, n, num_restarts=15, steps=30000):
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


def save_result(n, adj, method, elapsed=0):
    from datetime import datetime
    results = []
    if __import__('os').path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r') as f:
            results = json.load(f)
    degs = adj.sum(axis=1)
    edges = int(adj.sum()) // 2
    total = n * (n - 1) // 2
    entry = {
        'n': n, 'r': 5, 's': 5, 'verified': True, 'method': method,
        'timestamp': datetime.now().isoformat(),
        'edges': edges, 'total_possible_edges': total,
        'density': round(edges / total, 4),
        'degree_min': int(degs.min()), 'degree_max': int(degs.max()),
        'degree_mean': round(float(degs.mean()), 2),
        'elapsed_seconds': round(elapsed, 1),
        'npy_file': f'r55_n{n}_verified.npy',
        'adjacency': adj.tolist(),
    }
    results = [r for r in results if r['n'] != n]
    results.append(entry)
    results.sort(key=lambda r: r['n'])
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    np.save(f'r55_n{n}_verified.npy', adj)
    print(f"  Saved to {RESULTS_FILE} and r55_n{n}_verified.npy")


if __name__ == '__main__':
    print("R(5,5) Multi-Edge Trap Breaker")
    print("=" * 60)

    with open('r55_42some.g6') as f:
        g6_lines = [l.strip() for l in f if l.strip()]

    adj_orig = graph6_to_adj(g6_lines[41])
    n = 42

    # Conflict knot vertices
    knot = {5, 6, 8, 11, 12, 28}

    # Collect candidate edges: any edge touching a knot vertex
    candidates = set()
    for v in knot:
        for u in range(n):
            if u != v:
                candidates.add((min(u, v), max(u, v)))
    # Also add edges between knot neighbors (one hop out)
    knot_neighbors = set()
    for v in knot:
        for u in range(n):
            if adj_orig[v, u] == 1:
                knot_neighbors.add(u)
    knot_neighbors -= knot
    for v in knot_neighbors:
        for u in knot:
            candidates.add((min(u, v), max(u, v)))

    candidates = sorted(candidates)
    print(f"Candidate edges: {len(candidates)} (touching knot vertices + neighbors)")

    # Primary flip: remove (11,28)
    primary = (11, 28)
    t0 = time.time()
    tested = 0
    found_clean = []

    # ===== PHASE 1: Primary + 1 additional flip =====
    print(f"\nPhase 1: Remove (11,28) + 1 additional flip ({len(candidates)} candidates)")

    for u, v in candidates:
        if (u, v) == primary:
            continue

        adj = adj_orig.copy()
        # Remove primary
        adj[primary[0], primary[1]] = 0
        adj[primary[1], primary[0]] = 0
        # Flip candidate
        adj[u, v] = 1 - adj[u, v]
        adj[v, u] = adj[u, v]

        k5, i5 = full_energy(adj, n)
        tested += 1

        if k5 + i5 == 0:
            found_clean.append(('1flip', primary, (u, v), adj.copy()))
            print(f"  ** CLEAN: remove (11,28) + flip ({u},{v}) -> K5={k5} I5={i5} **")
        elif k5 + i5 <= 2:
            print(f"  Near: flip ({u},{v}) -> K5={k5} I5={i5} total={k5+i5}")

        if tested % 50 == 0:
            elapsed = time.time() - t0
            rate = tested / elapsed
            print(f"  {tested}/{len(candidates)} [{elapsed:.0f}s, {rate:.1f}/s]", flush=True)

    elapsed = time.time() - t0
    print(f"Phase 1 done: {tested} tested, {len(found_clean)} clean [{elapsed:.1f}s]")

    # ===== PHASE 2: Primary + 2 additional flips (if Phase 1 found nothing) =====
    if not found_clean:
        # Narrow to most promising candidates (those that got close in Phase 1)
        print(f"\nPhase 2: Remove (11,28) + 2 additional flips")
        print(f"  Narrowing to edges touching knot vertices only")

        knot_edges = [(min(u, v), max(u, v)) for u in knot for v in knot if u < v]
        # Add edges from knot to their immediate neighbors
        for v in knot:
            for u in range(n):
                if u not in knot and (adj_orig[v, u] == 1 or u in knot_neighbors):
                    knot_edges.append((min(u, v), max(u, v)))
        knot_edges = sorted(set(knot_edges))
        # Remove primary from candidates
        knot_edges = [e for e in knot_edges if e != primary]
        print(f"  Candidate edges for 2-flip: {len(knot_edges)}")
        print(f"  Pairs to test: {len(knot_edges) * (len(knot_edges)-1) // 2}")

        tested2 = 0
        for i, (u1, v1) in enumerate(knot_edges):
            for u2, v2 in knot_edges[i+1:]:
                adj = adj_orig.copy()
                adj[primary[0], primary[1]] = 0
                adj[primary[1], primary[0]] = 0
                adj[u1, v1] = 1 - adj[u1, v1]
                adj[v1, u1] = adj[u1, v1]
                adj[u2, v2] = 1 - adj[u2, v2]
                adj[v2, u2] = adj[u2, v2]

                k5, i5 = full_energy(adj, n)
                tested2 += 1

                if k5 + i5 == 0:
                    found_clean.append(('2flip', primary, (u1, v1), (u2, v2), adj.copy()))
                    print(f"  ** CLEAN: remove (11,28) + flip ({u1},{v1}) + flip ({u2},{v2}) **")
                elif k5 + i5 <= 1:
                    print(f"  Near: ({u1},{v1})+({u2},{v2}) -> K5={k5} I5={i5}")

                if tested2 % 200 == 0:
                    elapsed = time.time() - t0
                    total_pairs = len(knot_edges) * (len(knot_edges)-1) // 2
                    rate = tested2 / max(elapsed - (time.time() - t0 - elapsed), 0.1) if tested2 > 0 else 0
                    print(f"  {tested2}/{total_pairs} [{elapsed:.0f}s]", flush=True)

        print(f"Phase 2 done: {tested2} tested, {len(found_clean)} clean")

    # ===== TEST EXTENSION FOR CLEAN BASES =====
    if found_clean:
        print(f"\n{'='*60}")
        print(f"TESTING EXTENSIONS for {len(found_clean)} clean modified bases")
        print(f"{'='*60}")

        for entry in found_clean:
            desc = f"remove {entry[1]} + flip {entry[2]}"
            if entry[0] == '2flip':
                desc += f" + flip {entry[3]}"
                adj = entry[4]
            else:
                adj = entry[3]

            print(f"\n  Testing: {desc}")
            ext_E, ext_conn = sa_extension(adj, n, num_restarts=20, steps=30000)
            print(f"  Extension result: E={ext_E}")

            if ext_E == 0:
                print(f"\n  *** R(5,5) AVOIDER AT n=43 FOUND!! ***")
                adj43 = np.zeros((43, 43), dtype=np.int8)
                adj43[:42, :42] = adj
                for j in range(42):
                    adj43[42, j] = adj43[j, 42] = ext_conn[j]
                k5f, i5f = full_energy(adj43, 43)
                print(f"  Full n=43 verification: K5={k5f} I5={i5f}")
                if k5f + i5f == 0:
                    print(f"  **** VERIFIED! R(5,5) > 43! ****")
                    save_result(43, adj43, f"graph41_modified({desc})+extension",
                               time.time() - t0)
                    sys.exit(0)
            elif ext_E <= 3:
                print(f"  Close! E={ext_E}")
    else:
        print(f"\nNo clean modified base found.")

    elapsed = time.time() - t0
    print(f"\nTotal time: {elapsed:.1f}s")
    print("Done.")
