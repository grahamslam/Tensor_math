"""
Phase 1: Extension Resistance Correlation Analysis

Correlate ER values against all structural properties of the 656 R(5,5,42)-graphs
to identify which graph invariants predict extension resistance.
"""
import json
import numpy as np
from scipy import stats
import sys

sys.stdout.reconfigure(line_buffering=True)


def load_data():
    with open('analysis_656.json') as f:
        structural = json.load(f)
    with open('extension_analysis.json') as f:
        extension = json.load(f)

    # Build lookup: idx -> ER
    er_map = {}
    for r in extension:
        er_map[r['idx']] = r['best_E']

    # Match structural properties to ER values
    matched = []
    for s in structural:
        idx = s['idx']
        if idx in er_map:
            entry = dict(s)
            entry['ER'] = er_map[idx]
            matched.append(entry)

    return matched


if __name__ == '__main__':
    print("Extension Resistance Correlation Analysis")
    print("=" * 60)

    data = load_data()
    print(f"Matched records: {len(data)}")

    # Extract arrays
    er = np.array([d['ER'] for d in data])

    properties = {
        'edges': np.array([d['edges'] for d in data]),
        'density': np.array([d['density'] for d in data]),
        'degree_min': np.array([d['degree_min'] for d in data]),
        'degree_max': np.array([d['degree_max'] for d in data]),
        'degree_mean': np.array([d['degree_mean'] for d in data]),
        'degree_var': np.array([d['degree_var'] for d in data]),
        'triangles': np.array([d['triangles'] for d in data]),
        'triangles_comp': np.array([d['triangles_comp'] for d in data]),
        'tri_balance': np.array([d['tri_balance'] for d in data]),
        'k4_cliques': np.array([d['k4_cliques'] for d in data]),
        'i4_indep': np.array([d['i4_indep'] for d in data]),
        'k4_balance': np.array([d['k4_balance'] for d in data]),
        'spectral_gap': np.array([d['spectral_gap'] for d in data]),
        'lambda_max': np.array([d['lambda_max'] for d in data]),
        'lambda_min': np.array([d['lambda_min'] for d in data]),
    }

    # Derived properties
    properties['k4_total'] = properties['k4_cliques'] + properties['i4_indep']
    properties['k4_diff'] = np.abs(properties['k4_cliques'] - properties['i4_indep'])
    properties['tri_total'] = properties['triangles'] + properties['triangles_comp']
    properties['tri_diff'] = np.abs(properties['triangles'] - properties['triangles_comp'])
    properties['hoffman'] = 42 * (-properties['lambda_min']) / (properties['lambda_max'] - properties['lambda_min'])
    properties['degree_range'] = properties['degree_max'] - properties['degree_min']

    # Compute correlations
    print(f"\n{'Property':<20s} {'Pearson r':>10s} {'p-value':>12s} {'Spearman r':>12s} {'p-value':>12s}")
    print("-" * 66)

    results = []
    for name, values in sorted(properties.items()):
        # Skip if constant
        if np.std(values) < 1e-10:
            print(f"{name:<20s} {'(constant)':>10s}")
            continue

        r_p, p_p = stats.pearsonr(er, values)
        r_s, p_s = stats.spearmanr(er, values)
        results.append((name, r_p, p_p, r_s, p_s, abs(r_s)))

        sig_p = "***" if p_p < 0.001 else "**" if p_p < 0.01 else "*" if p_p < 0.05 else ""
        sig_s = "***" if p_s < 0.001 else "**" if p_s < 0.01 else "*" if p_s < 0.05 else ""

        print(f"{name:<20s} {r_p:>10.4f} {p_p:>10.2e} {sig_p:>2s} {r_s:>10.4f} {p_s:>10.2e} {sig_s:>2s}")

    # Rank by absolute Spearman correlation
    results.sort(key=lambda x: -x[5])
    print(f"\n{'='*60}")
    print("TOP PREDICTORS (ranked by |Spearman r|)")
    print(f"{'='*60}")
    for name, r_p, p_p, r_s, p_s, abs_rs in results[:10]:
        direction = "higher = harder to extend" if r_s > 0 else "higher = easier to extend"
        print(f"  {name:<20s} |r_s|={abs_rs:.4f}  ({direction})")

    # Summary statistics
    print(f"\n{'='*60}")
    print("ER DISTRIBUTION")
    print(f"{'='*60}")
    print(f"  Min:    {er.min()}")
    print(f"  Max:    {er.max()}")
    print(f"  Mean:   {er.mean():.1f}")
    print(f"  Median: {np.median(er):.1f}")
    print(f"  Std:    {np.std(er):.1f}")

    # Quartile analysis
    q1 = np.percentile(er, 25)
    q3 = np.percentile(er, 75)
    low_er = [d for d in data if d['ER'] <= q1]
    high_er = [d for d in data if d['ER'] >= q3]

    print(f"\n{'='*60}")
    print(f"QUARTILE COMPARISON (Q1 <= {q1}, Q4 >= {q3})")
    print(f"{'='*60}")
    print(f"{'Property':<20s} {'Low ER (mean)':>14s} {'High ER (mean)':>14s} {'Difference':>12s}")
    print("-" * 60)

    for name in ['spectral_gap', 'k4_balance', 'degree_var', 'tri_balance', 'edges',
                  'k4_cliques', 'i4_indep', 'k4_total', 'lambda_max', 'lambda_min']:
        low_vals = [d.get(name, properties[name][data.index(d)]) for d in low_er]
        high_vals = [d.get(name, properties[name][data.index(d)]) for d in high_er]

        # Use the numpy arrays instead
        low_indices = [i for i, d in enumerate(data) if d['ER'] <= q1]
        high_indices = [i for i, d in enumerate(data) if d['ER'] >= q3]

        low_mean = properties[name][low_indices].mean()
        high_mean = properties[name][high_indices].mean()
        diff = high_mean - low_mean

        print(f"  {name:<20s} {low_mean:>14.4f} {high_mean:>14.4f} {diff:>+12.4f}")

    # Save results
    output = {
        'n_records': len(data),
        'er_stats': {
            'min': int(er.min()),
            'max': int(er.max()),
            'mean': round(float(er.mean()), 2),
            'median': round(float(np.median(er)), 2),
            'std': round(float(np.std(er)), 2),
        },
        'correlations': {
            name: {
                'pearson_r': round(float(r_p), 4),
                'pearson_p': float(p_p),
                'spearman_r': round(float(r_s), 4),
                'spearman_p': float(p_s),
            }
            for name, r_p, p_p, r_s, p_s, _ in results
        },
    }

    with open('er_correlations.json', 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved to er_correlations.json")
    print("Done.")
