"""
R(5,5) Barrier Analysis — what makes Graph 41 almost-extendable?

Investigate:
1. What are the EXACT 2 remaining violations?
2. Do they share vertices? (conflict structure)
3. What's the constraint overlap (vertices in both 4-cliques and 4-indep-sets)?
4. Compare structural properties of E<=5 graphs vs E>=50 graphs
5. What does the best connection vector look like?
"""
import numpy as np
import networkx as nx
import json
import time
import sys
from itertools import combinations
from collections import Counter

sys.stdout.reconfigure(line_buffering=True)


def graph6_to_adj(g6):
    return nx.to_numpy_array(nx.from_graph6_bytes(g6.encode()), dtype=np.int8)


def find_4_cliques(A, n):
    cliques = []
    for combo in combinations(range(n), 4):
        if all(A[combo[a], combo[b]] == 1 for a in range(4) for b in range(a+1, 4)):
            cliques.append(combo)
    return cliques


def find_4_indeps(A, n):
    indeps = []
    for combo in combinations(range(n), 4):
        if all(A[combo[a], combo[b]] == 0 for a in range(4) for b in range(a+1, 4)):
            indeps.append(combo)
    return indeps


def find_best_connection(adj, n, num_restarts=10, steps=20000):
    """Find best connection vector with more effort."""
    rng = np.random.RandomState()
    best_E = 999
    best_conn = None
    best_k5 = 0
    best_i5 = 0

    for restart in range(num_restarts):
        conn = np.zeros(n, dtype=np.int8)
        for j in range(n):
            if rng.random() < 0.5:
                conn[j] = 1

        neighbors = [j for j in range(n) if conn[j] == 1]
        non_neighbors = [j for j in range(n) if conn[j] == 0]

        k5 = sum(1 for c in combinations(neighbors, 4)
                 if all(adj[c[a], c[b]] == 1 for a in range(4) for b in range(a+1, 4)))
        i5 = sum(1 for c in combinations(non_neighbors, 4)
                 if all(adj[c[a], c[b]] == 0 for a in range(4) for b in range(a+1, 4)))
        E = k5 + i5

        T = 1.0
        cooling = 1.0 - 5.0 / steps
        for step in range(steps):
            j = rng.randint(0, n)
            conn[j] = 1 - conn[j]

            nb = [x for x in range(n) if conn[x] == 1]
            nnb = [x for x in range(n) if conn[x] == 0]
            nk5 = sum(1 for c in combinations(nb, 4)
                      if all(adj[c[a], c[b]] == 1 for a in range(4) for b in range(a+1, 4)))
            ni5 = sum(1 for c in combinations(nnb, 4)
                      if all(adj[c[a], c[b]] == 0 for a in range(4) for b in range(a+1, 4)))
            nE = nk5 + ni5

            if nE - E <= 0 or rng.random() < np.exp(-(nE - E) / max(T, 0.005)):
                E = nE
                k5, i5 = nk5, ni5
                if E < best_E:
                    best_E = E
                    best_conn = conn.copy()
                    best_k5 = k5
                    best_i5 = i5
                if E == 0:
                    return best_E, best_conn, best_k5, best_i5
            else:
                conn[j] = 1 - conn[j]
            T *= cooling

    return best_E, best_conn, best_k5, best_i5


def analyze_violations(adj, conn, n):
    """Find the EXACT violations for a given connection vector."""
    neighbors = [j for j in range(n) if conn[j] == 1]
    non_neighbors = [j for j in range(n) if conn[j] == 0]

    k5_violations = []
    for c in combinations(neighbors, 4):
        if all(adj[c[a], c[b]] == 1 for a in range(4) for b in range(a+1, 4)):
            k5_violations.append(c)

    i5_violations = []
    for c in combinations(non_neighbors, 4):
        if all(adj[c[a], c[b]] == 0 for a in range(4) for b in range(a+1, 4)):
            i5_violations.append(c)

    return k5_violations, i5_violations


def vertex_conflict_score(v, cliques4, indeps4):
    """How many 4-cliques AND 4-indep-sets does vertex v appear in?
    High conflict = connecting to v helps one side but hurts the other."""
    in_cliques = sum(1 for c in cliques4 if v in c)
    in_indeps = sum(1 for c in indeps4 if v in c)
    return in_cliques, in_indeps, min(in_cliques, in_indeps)


if __name__ == '__main__':
    print("R(5,5) Barrier Analysis")
    print("=" * 60)

    with open('r55_42some.g6') as f:
        g6_lines = [l.strip() for l in f if l.strip()]

    # Load extension results to identify top graphs
    with open('extension_analysis.json') as f:
        ext_results = json.load(f)

    # Sort by best_E
    sorted_results = sorted(ext_results, key=lambda r: r['best_E'])
    print("\nTop 10 most extendable graphs:")
    for r in sorted_results[:10]:
        print(f"  idx={r['idx']:3d} ({r['source']:10s}) E={r['best_E']:2d} "
              f"k5={r['k5']} i5={r['i5']} deg={r['conn_degree']}")

    n = 42

    # ===== DEEP ANALYSIS OF GRAPH 41 =====
    print(f"\n{'='*60}")
    print("DEEP ANALYSIS: Graph 41")
    print(f"{'='*60}")

    adj41 = graph6_to_adj(g6_lines[41])
    degs = adj41.sum(axis=1).astype(int)
    edges = int(adj41.sum()) // 2
    print(f"\nBasic stats:")
    print(f"  Edges: {edges}/861 ({edges/861*100:.1f}%)")
    print(f"  Degree sequence: {sorted(degs.tolist())}")
    print(f"  Degree variance: {np.var(degs):.4f}")

    # Eigenvalues
    eigs = np.sort(np.linalg.eigvalsh(adj41.astype(float)))[::-1]
    print(f"  Lambda_max: {eigs[0]:.4f}")
    print(f"  Lambda_min: {eigs[-1]:.4f}")
    print(f"  Spectral gap: {eigs[0]-eigs[1]:.4f}")

    # 4-cliques and 4-indep-sets
    print(f"\nCounting 4-structures...")
    t0 = time.time()
    cliques4 = find_4_cliques(adj41, n)
    C41 = 1 - adj41.copy()
    np.fill_diagonal(C41, 0)
    indeps4 = find_4_indeps(adj41, n)
    print(f"  {len(cliques4)} 4-cliques, {len(indeps4)} 4-independent-sets [{time.time()-t0:.1f}s]")

    # Vertex conflict analysis
    print(f"\nVertex conflict analysis:")
    print(f"  (vertex: in_cliques, in_indeps, conflict=min(c,i))")
    conflicts = []
    for v in range(n):
        ic, ii, conf = vertex_conflict_score(v, cliques4, indeps4)
        conflicts.append((v, ic, ii, conf))

    conflicts.sort(key=lambda x: -x[3])
    print(f"  Highest conflict vertices:")
    for v, ic, ii, conf in conflicts[:10]:
        print(f"    v={v:2d}: in {ic:3d} 4-cliques, {ii:3d} 4-indeps, conflict={conf:3d}")
    print(f"  Lowest conflict vertices:")
    for v, ic, ii, conf in conflicts[-5:]:
        print(f"    v={v:2d}: in {ic:3d} 4-cliques, {ii:3d} 4-indeps, conflict={conf:3d}")

    total_conflict = sum(c[3] for c in conflicts)
    print(f"  Total conflict score: {total_conflict}")

    # Find best connection with more effort
    print(f"\nFinding best connection vector (10 restarts, 20K steps)...")
    t0 = time.time()
    best_E, best_conn, best_k5, best_i5 = find_best_connection(adj41, n, num_restarts=10, steps=20000)
    print(f"  Best: E={best_E} (K5={best_k5} I5={best_i5}) [{time.time()-t0:.1f}s]")
    print(f"  Connection degree: {int(best_conn.sum())}/{n}")
    print(f"  Connected to: {[j for j in range(n) if best_conn[j]==1]}")
    print(f"  NOT connected to: {[j for j in range(n) if best_conn[j]==0]}")

    # What are the EXACT violations?
    print(f"\nExact violations:")
    k5v, i5v = analyze_violations(adj41, best_conn, n)
    print(f"  K5 violations ({len(k5v)}):")
    for v in k5v:
        print(f"    4-clique {v} + new vertex -> K5")
        # Check if any vertex in this clique has low conflict
        for u in v:
            ic, ii, conf = vertex_conflict_score(u, cliques4, indeps4)
            print(f"      v={u}: conflict={conf} (in {ic} cliques, {ii} indeps)")
    print(f"  I5 violations ({len(i5v)}):")
    for v in i5v:
        print(f"    4-indep {v} + new vertex -> I5")
        for u in v:
            ic, ii, conf = vertex_conflict_score(u, cliques4, indeps4)
            print(f"      v={u}: conflict={conf} (in {ic} cliques, {ii} indeps)")

    # Check if violations share vertices
    if k5v and i5v:
        k5_verts = set()
        for v in k5v:
            k5_verts.update(v)
        i5_verts = set()
        for v in i5v:
            i5_verts.update(v)
        shared = k5_verts & i5_verts
        print(f"\n  K5 violation vertices: {sorted(k5_verts)}")
        print(f"  I5 violation vertices: {sorted(i5_verts)}")
        print(f"  Shared vertices: {sorted(shared)}")
        if shared:
            print(f"  ** CONFLICT: {len(shared)} vertices appear in both K5 and I5 violations **")
            print(f"  These vertices are the crux -- connecting to them creates K5, disconnecting creates I5")

    # ===== COMPARE TOP vs BOTTOM GRAPHS =====
    print(f"\n{'='*60}")
    print("COMPARISON: Top 4 (E<=5) vs Bottom 4 (E>=75)")
    print(f"{'='*60}")

    top_indices = [r['idx'] for r in sorted_results[:4] if r['idx'] < 328]
    bottom_results = [r for r in sorted_results if r['idx'] < 328]
    bottom_indices = [r['idx'] for r in bottom_results[-4:]]

    for label, indices in [("TOP (E<=5)", top_indices), ("BOTTOM (E>=75)", bottom_indices)]:
        print(f"\n  {label}:")
        for idx in indices:
            adj = graph6_to_adj(g6_lines[idx])
            d = adj.sum(axis=1).astype(int)
            e = int(adj.sum()) // 2
            eig = np.sort(np.linalg.eigvalsh(adj.astype(float)))[::-1]

            C = 1 - adj.copy()
            np.fill_diagonal(C, 0)
            c4 = len(find_4_cliques(adj, n))
            i4 = len(find_4_indeps(adj, n))

            ext_e = next((r['best_E'] for r in ext_results if r['idx'] == idx), '?')

            print(f"    Graph {idx}: E_ext={ext_e} edges={e} deg={min(d)}-{max(d)} "
                  f"var={np.var(d):.3f} gap={eig[0]-eig[1]:.3f} "
                  f"k4={c4} i4={i4} balance={abs(c4-i4)/(c4+i4):.4f}")

    print(f"\n{'='*60}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*60}")
