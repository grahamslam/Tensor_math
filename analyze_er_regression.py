"""
Phase 2: Multivariate Regression for Extension Resistance

Fit models predicting ER from combinations of structural properties.
Test linear, polynomial, and feature-interaction models.
"""
import json
import numpy as np
from scipy import stats
from itertools import combinations
import sys

sys.stdout.reconfigure(line_buffering=True)


def load_data():
    with open('analysis_656.json') as f:
        structural = json.load(f)
    with open('extension_analysis.json') as f:
        extension = json.load(f)

    er_map = {r['idx']: r['best_E'] for r in extension}

    matched = []
    for s in structural:
        if s['idx'] in er_map:
            entry = dict(s)
            entry['ER'] = er_map[s['idx']]
            matched.append(entry)
    return matched


def extract_features(data):
    """Extract feature matrix and target vector."""
    n = len(data)
    er = np.array([d['ER'] for d in data], dtype=float)

    features = {}
    features['edges'] = np.array([d['edges'] for d in data], dtype=float)
    features['degree_var'] = np.array([d['degree_var'] for d in data], dtype=float)
    features['triangles'] = np.array([d['triangles'] for d in data], dtype=float)
    features['triangles_comp'] = np.array([d['triangles_comp'] for d in data], dtype=float)
    features['tri_balance'] = np.array([d['tri_balance'] for d in data], dtype=float)
    features['k4_cliques'] = np.array([d['k4_cliques'] for d in data], dtype=float)
    features['i4_indep'] = np.array([d['i4_indep'] for d in data], dtype=float)
    features['k4_balance'] = np.array([d['k4_balance'] for d in data], dtype=float)
    features['spectral_gap'] = np.array([d['spectral_gap'] for d in data], dtype=float)
    features['lambda_max'] = np.array([d['lambda_max'] for d in data], dtype=float)
    features['lambda_min'] = np.array([d['lambda_min'] for d in data], dtype=float)

    # Derived
    features['k4_total'] = features['k4_cliques'] + features['i4_indep']
    features['k4_diff'] = np.abs(features['k4_cliques'] - features['i4_indep'])
    features['tri_total'] = features['triangles'] + features['triangles_comp']
    features['tri_diff'] = np.abs(features['triangles'] - features['triangles_comp'])

    return features, er


def standardize(x):
    """Z-score standardize."""
    mu, sigma = x.mean(), x.std()
    if sigma < 1e-10:
        return np.zeros_like(x), mu, sigma
    return (x - mu) / sigma, mu, sigma


def linear_regression(X, y):
    """OLS regression. Returns coefficients, R^2, adjusted R^2, residuals."""
    n, p = X.shape
    # Add intercept
    X_int = np.column_stack([np.ones(n), X])
    # Solve normal equations
    try:
        beta = np.linalg.lstsq(X_int, y, rcond=None)[0]
    except np.linalg.LinAlgError:
        return None, 0, 0, y

    y_pred = X_int @ beta
    residuals = y - y_pred
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot
    adj_r2 = 1 - (1 - r2) * (n - 1) / (n - p - 1)

    return beta, r2, adj_r2, residuals


if __name__ == '__main__':
    print("Phase 2: Extension Resistance Multivariate Regression")
    print("=" * 60)

    data = load_data()
    features, er = extract_features(data)
    n = len(er)
    print(f"Records: {n}")

    # Top predictors from Phase 1
    top_features = ['k4_total', 'tri_balance', 'tri_diff', 'k4_diff',
                    'k4_balance', 'degree_var', 'tri_total']

    # ===== MODEL 1: Single best predictor =====
    print(f"\n{'='*60}")
    print("MODEL 1: Single predictor regressions")
    print(f"{'='*60}")

    for name in top_features:
        X = features[name].reshape(-1, 1)
        beta, r2, adj_r2, _ = linear_regression(X, er)
        print(f"  {name:<20s}  R2={r2:.4f}  adj_R2={adj_r2:.4f}")

    # ===== MODEL 2: Top 2 predictors =====
    print(f"\n{'='*60}")
    print("MODEL 2: Best 2-predictor combinations")
    print(f"{'='*60}")

    best_2 = []
    for f1, f2 in combinations(top_features, 2):
        X = np.column_stack([features[f1], features[f2]])
        beta, r2, adj_r2, _ = linear_regression(X, er)
        best_2.append((f1, f2, r2, adj_r2))

    best_2.sort(key=lambda x: -x[3])
    for f1, f2, r2, adj_r2 in best_2[:10]:
        print(f"  {f1} + {f2}")
        print(f"    R2={r2:.4f}  adj_R2={adj_r2:.4f}")

    # ===== MODEL 3: Top 3 predictors =====
    print(f"\n{'='*60}")
    print("MODEL 3: Best 3-predictor combinations")
    print(f"{'='*60}")

    best_3 = []
    for f1, f2, f3 in combinations(top_features, 3):
        X = np.column_stack([features[f1], features[f2], features[f3]])
        beta, r2, adj_r2, _ = linear_regression(X, er)
        best_3.append((f1, f2, f3, r2, adj_r2))

    best_3.sort(key=lambda x: -x[4])
    for f1, f2, f3, r2, adj_r2 in best_3[:5]:
        print(f"  {f1} + {f2} + {f3}")
        print(f"    R2={r2:.4f}  adj_R2={adj_r2:.4f}")

    # ===== MODEL 4: All top predictors =====
    print(f"\n{'='*60}")
    print("MODEL 4: All top predictors combined")
    print(f"{'='*60}")

    X_all = np.column_stack([features[f] for f in top_features])
    beta, r2, adj_r2, residuals = linear_regression(X_all, er)
    print(f"  Features: {', '.join(top_features)}")
    print(f"  R2={r2:.4f}  adj_R2={adj_r2:.4f}")
    print(f"  Coefficients (standardized):")

    # Standardized coefficients
    X_std = np.column_stack([standardize(features[f])[0] for f in top_features])
    beta_std, _, _, _ = linear_regression(X_std, er)
    for i, name in enumerate(top_features):
        print(f"    {name:<20s}: {beta_std[i+1]:>+8.2f}")

    # ===== MODEL 5: Polynomial (quadratic) on top 2 =====
    print(f"\n{'='*60}")
    print("MODEL 5: Quadratic model on top 2 predictors")
    print(f"{'='*60}")

    f1_name, f2_name = best_2[0][0], best_2[0][1]
    f1 = features[f1_name]
    f2 = features[f2_name]
    X_quad = np.column_stack([f1, f2, f1**2, f2**2, f1*f2])
    beta, r2, adj_r2, _ = linear_regression(X_quad, er)
    print(f"  {f1_name} + {f2_name} + squares + interaction")
    print(f"  R2={r2:.4f}  adj_R2={adj_r2:.4f}")

    # ===== MODEL 6: All features including interactions =====
    print(f"\n{'='*60}")
    print("MODEL 6: Top 4 with all pairwise interactions")
    print(f"{'='*60}")

    top4 = ['k4_total', 'tri_balance', 'k4_diff', 'degree_var']
    base = [features[f] for f in top4]
    interactions = []
    interaction_names = list(top4)

    for i in range(len(top4)):
        for j in range(i+1, len(top4)):
            interactions.append(base[i] * base[j])
            interaction_names.append(f"{top4[i]}*{top4[j]}")

    X_int = np.column_stack(base + interactions)
    beta, r2, adj_r2, residuals = linear_regression(X_int, er)
    print(f"  Features: {', '.join(interaction_names)}")
    print(f"  R2={r2:.4f}  adj_R2={adj_r2:.4f}")

    # ===== SUMMARY =====
    print(f"\n{'='*60}")
    print("SUMMARY: Model comparison")
    print(f"{'='*60}")
    print(f"  {'Model':<50s} {'R2':>8s} {'adj_R2':>8s}")
    print(f"  {'-'*66}")
    print(f"  {'Best single predictor (k4_total)':<50s} {'':>8s} {'':>8s}")

    X_single = features['k4_total'].reshape(-1, 1)
    _, r2_s, adj_s, _ = linear_regression(X_single, er)
    print(f"  {'  k4_total only':<50s} {r2_s:>8.4f} {adj_s:>8.4f}")

    print(f"  {'Best 2 predictors':<50s} {best_2[0][2]:>8.4f} {best_2[0][3]:>8.4f}")
    print(f"    ({best_2[0][0]} + {best_2[0][1]})")
    print(f"  {'Best 3 predictors':<50s} {best_3[0][3]:>8.4f} {best_3[0][4]:>8.4f}")
    print(f"    ({best_3[0][0]} + {best_3[0][1]} + {best_3[0][2]})")

    X_all = np.column_stack([features[f] for f in top_features])
    _, r2_all, adj_all, _ = linear_regression(X_all, er)
    print(f"  {'All 7 top predictors':<50s} {r2_all:>8.4f} {adj_all:>8.4f}")
    print(f"  {'Quadratic (top 2 + squares + interaction)':<50s} {':>8s'} {':>8s'}")

    X_quad = np.column_stack([features[best_2[0][0]], features[best_2[0][1]],
                               features[best_2[0][0]]**2, features[best_2[0][1]]**2,
                               features[best_2[0][0]]*features[best_2[0][1]]])
    _, r2_q, adj_q, _ = linear_regression(X_quad, er)
    print(f"  {'  quadratic':<50s} {r2_q:>8.4f} {adj_q:>8.4f}")
    print(f"  {'Top 4 + pairwise interactions':<50s} {r2:>8.4f} {adj_r2:>8.4f}")

    # Residual analysis
    X_best = np.column_stack([features[f] for f in top4])
    _, _, _, res_best = linear_regression(X_best, er)
    print(f"\n  Residuals (best linear model, top 4):")
    print(f"    Mean: {res_best.mean():.2f}")
    print(f"    Std:  {res_best.std():.2f}")
    print(f"    Max absolute: {np.max(np.abs(res_best)):.1f}")
    print(f"    Unexplained variance: {100*(1-r2):.1f}%")

    # Save results
    output = {
        'best_single': {'feature': 'k4_total', 'R2': round(r2_s, 4)},
        'best_pair': {'features': [best_2[0][0], best_2[0][1]], 'R2': round(best_2[0][2], 4)},
        'best_triple': {'features': [best_3[0][0], best_3[0][1], best_3[0][2]], 'R2': round(best_3[0][3], 4)},
        'all_top': {'features': top_features, 'R2': round(r2_all, 4)},
        'quadratic': {'R2': round(r2_q, 4)},
        'interactions': {'R2': round(r2, 4)},
    }
    with open('er_regression.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved to er_regression.json")
    print("Done.")
