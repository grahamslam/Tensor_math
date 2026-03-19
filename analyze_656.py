"""
Phase 1: Characterize all 656 R(5,5,42)-graphs.
Loads 328 from McKay's g6 file + 328 complements.
Computes structural properties for each.
"""
import numpy as np
import networkx as nx
import time
import sys
import json
from itertools import combinations
from collections import Counter

sys.stdout.reconfigure(line_buffering=True)


def graph6_to_adj(g6_string):
    """Convert graph6 string to numpy adjacency matrix via networkx."""
    G = nx.from_graph6_bytes(g6_string.encode())
    return nx.to_numpy_array(G, dtype=np.int8)


def count_k_cliques(A, k, n):
    """Count k-cliques."""
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


def analyze_graph(adj, n, idx):
    """Compute structural properties of a single graph."""
    degs = adj.sum(axis=1).astype(int)
    edges = int(adj.sum()) // 2
    total = n * (n - 1) // 2

    # Complement
    C = 1 - adj.copy()
    np.fill_diagonal(C, 0)

    # Triangle count via matrix trace
    A2 = adj.astype(np.float32)
    tri = int(np.trace(A2 @ A2 @ A2)) // 6

    C2 = C.astype(np.float32)
    tri_comp = int(np.trace(C2 @ C2 @ C2)) // 6

    # 4-cliques (needed for extension analysis)
    k4 = count_k_cliques(adj, 4, n)
    i4 = count_k_cliques(C, 4, n)

    # Eigenvalues
    eigs = np.sort(np.linalg.eigvalsh(adj.astype(float)))[::-1]

    # Automorphism group size (via networkx)
    G = nx.from_numpy_array(adj)

    # Degree sequence
    deg_seq = sorted(degs.tolist())

    # Check if circulant (all rows are cyclic shifts)
    is_circulant = True
    first_row = adj[0].tolist()
    for i in range(1, n):
        shifted = first_row[-i:] + first_row[:-i]
        if adj[i].tolist() != shifted:
            is_circulant = False
            break

    return {
        'idx': idx,
        'n': n,
        'edges': edges,
        'density': round(edges / total, 4),
        'degree_min': int(degs.min()),
        'degree_max': int(degs.max()),
        'degree_mean': round(float(degs.mean()), 2),
        'degree_var': round(float(np.var(degs)), 2),
        'degree_seq': deg_seq,
        'triangles': tri,
        'triangles_comp': tri_comp,
        'tri_balance': round(abs(tri - tri_comp) / max(tri + tri_comp, 1), 4),
        'k4_cliques': k4,
        'i4_indep': i4,
        'k4_balance': round(abs(k4 - i4) / max(k4 + i4, 1), 4),
        'spectral_gap': round(float(eigs[0] - eigs[1]), 4),
        'lambda_max': round(float(eigs[0]), 4),
        'lambda_min': round(float(eigs[-1]), 4),
        'is_circulant': is_circulant,
    }


if __name__ == '__main__':
    print("Phase 1: Characterizing 656 R(5,5,42)-graphs")
    print("=" * 60)

    # Load graph6 file
    with open('r55_42some.g6', 'r') as f:
        g6_lines = [line.strip() for line in f if line.strip()]
    print(f"Loaded {len(g6_lines)} graphs from g6 file")

    n = 42
    all_stats = []
    t0 = time.time()

    for i, g6 in enumerate(g6_lines):
        adj = graph6_to_adj(g6)
        assert adj.shape == (n, n), f"Graph {i} has shape {adj.shape}"

        # Analyze original
        stats = analyze_graph(adj, n, i)
        stats['source'] = 'original'
        all_stats.append(stats)

        # Analyze complement
        C = 1 - adj.copy()
        np.fill_diagonal(C, 0)
        stats_c = analyze_graph(C, n, i + 328)
        stats_c['source'] = 'complement'
        all_stats.append(stats_c)

        if (i + 1) % 20 == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (len(g6_lines) - i - 1) / rate
            print(f"  {i+1}/{len(g6_lines)} [{elapsed:.0f}s, ETA {eta:.0f}s]", flush=True)

    elapsed = time.time() - t0
    print(f"\nAnalyzed {len(all_stats)} graphs in {elapsed:.1f}s")

    # ===== SUMMARY STATISTICS =====
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    edges_list = [s['edges'] for s in all_stats]
    print(f"\nEdge counts: min={min(edges_list)} max={max(edges_list)} mean={np.mean(edges_list):.1f}")

    deg_vars = [s['degree_var'] for s in all_stats]
    print(f"Degree variance: min={min(deg_vars):.2f} max={max(deg_vars):.2f} mean={np.mean(deg_vars):.2f}")

    # Degree sequence distribution
    deg_seqs = Counter([tuple(s['degree_seq']) for s in all_stats])
    print(f"\nDistinct degree sequences: {len(deg_seqs)}")
    for seq, count in deg_seqs.most_common(10):
        print(f"  {count}x: {list(seq)[:10]}...{list(seq)[-3:]}")

    # Circulant check
    circulant_count = sum(1 for s in all_stats if s['is_circulant'])
    print(f"\nCirculant graphs: {circulant_count}/{len(all_stats)}")

    # K4 / I4 distribution
    k4_list = [s['k4_cliques'] for s in all_stats]
    i4_list = [s['i4_indep'] for s in all_stats]
    print(f"\n4-cliques: min={min(k4_list)} max={max(k4_list)} mean={np.mean(k4_list):.1f}")
    print(f"4-indep:   min={min(i4_list)} max={max(i4_list)} mean={np.mean(i4_list):.1f}")

    # K4 balance
    balances = [s['k4_balance'] for s in all_stats]
    print(f"K4 balance (|k4-i4|/(k4+i4)): min={min(balances):.4f} max={max(balances):.4f} mean={np.mean(balances):.4f}")

    # Triangle stats
    tri_list = [s['triangles'] for s in all_stats]
    tri_c_list = [s['triangles_comp'] for s in all_stats]
    print(f"\nTriangles(G): min={min(tri_list)} max={max(tri_list)} mean={np.mean(tri_list):.1f}")
    print(f"Triangles(C): min={min(tri_c_list)} max={max(tri_c_list)} mean={np.mean(tri_c_list):.1f}")

    # Spectral stats
    gaps = [s['spectral_gap'] for s in all_stats]
    lmax = [s['lambda_max'] for s in all_stats]
    lmin = [s['lambda_min'] for s in all_stats]
    print(f"\nSpectral gap: min={min(gaps):.4f} max={max(gaps):.4f} mean={np.mean(gaps):.4f}")
    print(f"Lambda_max:   min={min(lmax):.4f} max={max(lmax):.4f} mean={np.mean(lmax):.4f}")
    print(f"Lambda_min:   min={min(lmin):.4f} max={max(lmin):.4f} mean={np.mean(lmin):.4f}")

    # Hoffman bound check
    hoffman = [n * (-s['lambda_min']) / (s['lambda_max'] - s['lambda_min']) for s in all_stats]
    print(f"Hoffman bound: min={min(hoffman):.2f} max={max(hoffman):.2f} mean={np.mean(hoffman):.2f}")

    # Save full analysis
    with open('analysis_656.json', 'w') as f:
        json.dump(all_stats, f, indent=2)
    print(f"\nSaved to analysis_656.json")
