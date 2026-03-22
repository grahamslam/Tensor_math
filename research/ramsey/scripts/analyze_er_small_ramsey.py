"""
Phase 3: Extension Resistance across smaller Ramsey numbers.

For R(3,3)=6, R(3,4)=9, R(3,5)=14, R(4,4)=18:
- Enumerate all avoiding graphs at sizes near R(r,s)
- Compute ER for each
- Compute structural properties
- Test whether k4_total, tri_balance, degree_var predict ER

Uses exhaustive search for small n, SA for larger n.
"""
import numpy as np
from itertools import combinations
from scipy import stats
import time
import sys
import json

sys.stdout.reconfigure(line_buffering=True)


def generate_all_graphs(n):
    """Generate all non-isomorphic graphs on n vertices (brute force for small n)."""
    edges = list(combinations(range(n), 2))
    num_edges = len(edges)
    graphs = []
    for mask in range(1 << num_edges):
        adj = np.zeros((n, n), dtype=np.int8)
        for i, (u, v) in enumerate(edges):
            if (mask >> i) & 1:
                adj[u, v] = adj[v, u] = 1
        graphs.append(adj)
    return graphs


def has_clique(adj, k, n):
    """Check if graph has a k-clique."""
    for combo in combinations(range(n), k):
        if all(adj[combo[a], combo[b]] == 1 for a in range(k) for b in range(a+1, k)):
            return True
    return False


def count_cliques(adj, k, n):
    """Count k-cliques."""
    count = 0
    for combo in combinations(range(n), k):
        if all(adj[combo[a], combo[b]] == 1 for a in range(k) for b in range(a+1, k)):
            count += 1
    return count


def is_ramsey_avoiding(adj, r, s, n):
    """Check if graph avoids R(r,s)."""
    if has_clique(adj, r, n):
        return False
    C = 1 - adj.copy()
    np.fill_diagonal(C, 0)
    if has_clique(C, s, n):
        return False
    return True


def compute_er(adj, r, s, n, method='exhaustive', sa_restarts=3, sa_steps=5000):
    """Compute extension resistance."""
    best_E = float('inf')

    if method == 'exhaustive':
        for mask in range(1 << n):
            conn = np.array([(mask >> j) & 1 for j in range(n)], dtype=np.int8)
            violations = count_new_violations(adj, conn, r, s, n)
            if violations < best_E:
                best_E = violations
                if best_E == 0:
                    return 0
    else:
        rng = np.random.RandomState()
        for restart in range(sa_restarts):
            conn = np.random.randint(0, 2, n, dtype=np.int8)
            violations = count_new_violations(adj, conn, r, s, n)
            E = violations
            T = 1.0
            cooling = 1.0 - 5.0 / sa_steps
            for step in range(sa_steps):
                j = rng.randint(0, n)
                conn[j] = 1 - conn[j]
                new_v = count_new_violations(adj, conn, r, s, n)
                if new_v <= E or rng.random() < np.exp(-(new_v - E) / max(T, 0.005)):
                    E = new_v
                    if E < best_E:
                        best_E = E
                    if E == 0:
                        return 0
                else:
                    conn[j] = 1 - conn[j]
                T *= cooling

    return best_E


def count_new_violations(adj, conn, r, s, n):
    """Count violations involving the new vertex."""
    neighbors = [j for j in range(n) if conn[j] == 1]
    non_neighbors = [j for j in range(n) if conn[j] == 0]

    kr = 0
    if len(neighbors) >= r - 1:
        for combo in combinations(neighbors, r - 1):
            if all(adj[combo[a], combo[b]] == 1 for a in range(r-1) for b in range(a+1, r-1)):
                kr += 1

    is_ = 0
    if len(non_neighbors) >= s - 1:
        for combo in combinations(non_neighbors, s - 1):
            if all(adj[combo[a], combo[b]] == 0 for a in range(s-1) for b in range(a+1, s-1)):
                is_ += 1

    return kr + is_


def compute_properties(adj, n):
    """Compute structural properties of a graph."""
    C = 1 - adj.copy()
    np.fill_diagonal(C, 0)

    degs = adj.sum(axis=1).astype(float)
    edges = int(adj.sum()) // 2

    # Triangles
    A2 = adj.astype(np.float32)
    tri = int(np.trace(A2 @ A2 @ A2)) // 6
    C2 = C.astype(np.float32)
    tri_c = int(np.trace(C2 @ C2 @ C2)) // 6
    tri_balance = abs(tri - tri_c) / max(tri + tri_c, 1)

    # K3 counts (= triangles for r=3 problems)
    k3 = tri
    i3 = tri_c

    # Eigenvalues
    eigs = np.sort(np.linalg.eigvalsh(adj.astype(float)))[::-1]
    spectral_gap = float(eigs[0] - eigs[1]) if len(eigs) > 1 else 0

    return {
        'edges': edges,
        'degree_var': round(float(np.var(degs)), 4),
        'triangles': tri,
        'triangles_comp': tri_c,
        'tri_balance': round(tri_balance, 4),
        'tri_diff': abs(tri - tri_c),
        'k3_total': tri + tri_c,
        'spectral_gap': round(spectral_gap, 4),
        'lambda_max': round(float(eigs[0]), 4),
        'lambda_min': round(float(eigs[-1]), 4),
    }


def count_violations(adj, r, s, n):
    """Count total r-cliques + s-independent-sets."""
    kr = count_cliques(adj, r, n)
    C = 1 - adj.copy()
    np.fill_diagonal(C, 0)
    is_ = count_cliques(C, s, n)
    return kr + is_


def find_avoiding_graphs_sa(n, r, s, max_graphs=500, restarts=2000, steps=5000):
    """Find avoiding graphs using simulated annealing to minimize violations."""
    rng = np.random.RandomState(42)
    graphs = []
    seen = set()
    edges = list(combinations(range(n), 2))

    for restart in range(restarts):
        # Random initial graph
        adj = np.zeros((n, n), dtype=np.int8)
        for i, j in edges:
            if rng.random() < 0.5:
                adj[i, j] = adj[j, i] = 1

        E = count_violations(adj, r, s, n)
        if E == 0:
            key = adj.tobytes()
            if key not in seen:
                seen.add(key)
                graphs.append(adj.copy())
                if len(graphs) >= max_graphs:
                    break
            continue

        T = 2.0
        cooling = (0.01 / 2.0) ** (1.0 / steps)
        for step in range(steps):
            u, v = edges[rng.randint(0, len(edges))]
            adj[u, v] = adj[v, u] = 1 - adj[u, v]
            new_E = count_violations(adj, r, s, n)
            if new_E <= E or rng.random() < np.exp(-(new_E - E) / max(T, 0.001)):
                E = new_E
                if E == 0:
                    key = adj.tobytes()
                    if key not in seen:
                        seen.add(key)
                        graphs.append(adj.copy())
                    break
            else:
                adj[u, v] = adj[v, u] = 1 - adj[u, v]
            T *= cooling

        if len(graphs) >= max_graphs:
            break

        if (restart + 1) % 200 == 0:
            print(f"      SA restart {restart+1}/{restarts}, found {len(graphs)} so far", flush=True)

    return graphs


if __name__ == '__main__':
    print("Phase 3: Extension Resistance across Ramsey Numbers")
    print("=" * 60)

    results_all = {}

    # Define test cases: (r, s, R_value, test_sizes, method)
    test_cases = [
        (3, 3, 6, [4, 5], 'exhaustive'),
        (3, 4, 9, [6, 7, 8], 'exhaustive'),
        (3, 5, 14, [10, 11, 12, 13], 'sample'),
        (4, 4, 18, [14, 15, 16, 17], 'sample'),
    ]

    for r, s, R_val, test_sizes, method in test_cases:
        print(f"\n{'='*60}")
        print(f"R({r},{s}) = {R_val}")
        print(f"{'='*60}")

        for n in test_sizes:
            t0 = time.time()
            print(f"\n  n={n} (R({r},{s})={R_val}, ratio={n/R_val:.2f})")

            # Find avoiding graphs
            if method == 'exhaustive' and n <= 7:
                print(f"    Enumerating all graphs on n={n}...")
                all_graphs = generate_all_graphs(n)
                avoiding = [g for g in all_graphs if is_ramsey_avoiding(g, r, s, n)]
                print(f"    Total graphs: {len(all_graphs)}, avoiding: {len(avoiding)}")
            else:
                print(f"    SA-constructing avoiding graphs on n={n}...")
                avoiding = find_avoiding_graphs_sa(n, r, s, max_graphs=500, restarts=3000, steps=8000)
                print(f"    Found: {len(avoiding)} avoiding graphs")

            if len(avoiding) == 0:
                print(f"    No avoiding graphs found at n={n}")
                continue

            # Compute ER and properties for each
            er_method = 'exhaustive' if n <= 16 else 'sa'
            data_points = []

            for i, adj in enumerate(avoiding):
                er = compute_er(adj, r, s, n, method=er_method)
                props = compute_properties(adj, n)
                props['ER'] = er
                data_points.append(props)

                if (i + 1) % 50 == 0 or i == len(avoiding) - 1:
                    elapsed = time.time() - t0
                    print(f"    {i+1}/{len(avoiding)} [{elapsed:.1f}s]", flush=True)

            # Analyze
            ers = np.array([d['ER'] for d in data_points])
            print(f"\n    ER distribution: min={ers.min()} max={ers.max()} "
                  f"mean={ers.mean():.1f} median={np.median(ers):.1f}")
            print(f"    ER=0: {np.sum(ers == 0)} graphs ({100*np.sum(ers==0)/len(ers):.1f}%)")

            # Correlations with available properties
            if len(data_points) >= 10 and np.std(ers) > 0:
                print(f"\n    Correlations with ER:")
                corr_results = []
                for prop_name in ['tri_balance', 'tri_diff', 'k3_total', 'degree_var',
                                  'spectral_gap', 'edges']:
                    vals = np.array([d[prop_name] for d in data_points])
                    if np.std(vals) > 1e-10:
                        r_s, p_s = stats.spearmanr(ers, vals)
                        sig = "***" if p_s < 0.001 else "**" if p_s < 0.01 else "*" if p_s < 0.05 else ""
                        corr_results.append((prop_name, r_s, p_s))
                        print(f"      {prop_name:<16s} r_s={r_s:>+.4f} p={p_s:.2e} {sig}")

            results_all[f"R({r},{s})_n{n}"] = {
                'r': r, 's': s, 'R_value': R_val, 'n': n,
                'ratio': round(n / R_val, 3),
                'num_avoiding': len(avoiding),
                'er_min': int(ers.min()), 'er_max': int(ers.max()),
                'er_mean': round(float(ers.mean()), 2),
                'er_zero_count': int(np.sum(ers == 0)),
                'er_zero_pct': round(100 * np.sum(ers == 0) / len(ers), 1),
            }

            elapsed = time.time() - t0
            print(f"    Time: {elapsed:.1f}s")

    # Summary
    print(f"\n{'='*60}")
    print("CROSS-RAMSEY SUMMARY")
    print(f"{'='*60}")
    print(f"{'Case':<16s} {'n':>3s} {'ratio':>6s} {'#avoid':>7s} {'ER min':>7s} {'ER max':>7s} {'ER=0%':>7s}")
    print("-" * 60)
    for key, v in sorted(results_all.items()):
        print(f"{key:<16s} {v['n']:>3d} {v['ratio']:>6.3f} {v['num_avoiding']:>7d} "
              f"{v['er_min']:>7d} {v['er_max']:>7d} {v['er_zero_pct']:>6.1f}%")

    with open('er_small_ramsey.json', 'w') as f:
        json.dump(results_all, f, indent=2)
    print(f"\nSaved to er_small_ramsey.json")
    print("Done.")
