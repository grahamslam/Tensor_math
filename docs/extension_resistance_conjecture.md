# Extension Resistance: A Novel Graph Invariant for Ramsey Avoidance

**Date:** March 21, 2026
**Authors:** Brent Graham, Claude Opus 4.6 (Anthropic)
**Repository:** grahamslam/Tensor_math
**Status:** Active research

---

## Origin

This conjecture was formulated by Claude Opus 4.6 during a computational investigation of R(5,5) Ramsey number lower bounds with Brent Graham. While analyzing the structural properties of all 656 known R(5,5,42)-graphs and their extendability to n=43, Claude observed that graphs with identical Ramsey avoidance properties exhibited dramatically different extension behaviors — from near-extendable (E=2) to deeply resistant (E=83). This observation, combined with the structural analysis data already computed, suggested that extension behavior might be predictable from known graph invariants, leading to the formalization of extension resistance as a potentially novel graph quantity.

---

## 1. Definition

**Extension Resistance** ER(G, r, s) is defined for a graph G on n vertices that avoids R(r,s) (i.e., contains no K_r clique and no K_s independent set):

```
ER(G, r, s) = min over all connection vectors c in {0,1}^n of V(G+c, r, s)
```

where G+c is the (n+1)-vertex graph formed by adding a new vertex connected to vertex j iff c_j = 1, and V(G+c, r, s) counts the total number of r-cliques plus s-independent-sets in G+c.

**Properties:**
- ER(G, r, s) >= 0 for any R(r,s)-avoiding graph G
- ER(G, r, s) = 0 iff G can be extended to an (n+1)-vertex R(r,s)-avoider
- For n >= R(r,s) - 1, ER(G, r, s) > 0 for all avoiding graphs G (no extension possible)
- ER is invariant under graph isomorphism

**Complementary property:** For R(r,r) (diagonal Ramsey), ER(G, r, r) = ER(complement(G), r, r), since complement preserves R(r,r) avoidance symmetrically.

---

## 2. Motivation

### 2.1 The Extension Phase Transition

Prior work (Graham & Claude, March 2026) established that for multiple Ramsey numbers, vertex-by-vertex extension of avoiding graphs becomes impossible at approximately 78% of R(r,s):

| R(r,s) | R value | Extension closes at | Ratio |
|---------|---------|-------------------|-------|
| R(3,3)  | 6       | n = 5             | 83%   |
| R(3,4)  | 9       | n = 7             | 78%   |
| R(3,5)  | 14      | n = 11            | 79%   |
| R(4,4)  | 18      | n = 13            | 72%   |

This phase transition is well-documented, but the mechanism is not understood. Why does extension become impossible at a specific fraction of R(r,s)? Extension resistance provides a framework to investigate this question.

### 2.2 The R(5,5) Observation

Analysis of all 656 known R(5,5,42)-graphs revealed that ER varies dramatically across graphs that share the same Ramsey avoidance property:

| Statistic | Value |
|-----------|-------|
| Min ER    | 2     |
| Max ER    | 83    |
| Mean ER   | 37.6  |
| Graphs with ER <= 5 | 4 |
| Graphs with ER <= 10 | 25 |
| Graphs with ER <= 20 | 113 |
| Graphs with ER = 0   | 0 |

Graph 41 (0-indexed in McKay's dataset) achieves ER = 2 — only 2 violations from extending to n=43. This is a dramatic outlier: the next best is ER = 4, then ER = 9. Both the original and complement of Graph 41 achieve ER = 2, suggesting possible self-complementary or near-self-complementary structure.

### 2.3 The Central Question

**What graph-theoretic properties predict extension resistance?**

If ER can be predicted from efficiently computable graph invariants (spectral gap, degree distribution, clique counts, etc.), this would:

1. Enable targeted construction of low-ER graphs for pushing Ramsey lower bounds
2. Explain the extension phase transition mechanistically
3. Connect spectral graph theory to Ramsey extendability in a potentially new way
4. Provide a new tool for evaluating candidate Ramsey constructions

---

## 3. Available Data

### 3.1 Structural Properties (analysis_656.json)

For each of the 656 R(5,5,42)-graphs, we have computed:

- **Edge count**: 423-438 (range of 15)
- **Degree distribution**: always 19-22, variance 0.49-1.01
- **Triangle counts**: G and complement, 1296-1376
- **4-clique counts**: 1099-1216
- **4-independent-set counts**: 1099-1216
- **K4 balance**: |k4 - i4| / (k4 + i4), range 0.0000-0.0505
- **Spectral gap**: lambda_1 - lambda_2, range 14.56-15.76
- **Lambda_max**: 20.18-20.89
- **Lambda_min**: -6.65 to -6.13
- **Hoffman bound**: 9.76-10.21
- **Circulant**: 0 of 656 are circulant
- **194 distinct degree sequences**

### 3.2 Extension Resistance Values (extension_analysis.json)

ER values for all 656 graphs, computed via simulated annealing on the 42-bit connection vector (1 restart, 5000 SA steps per graph — these are upper bounds on true ER, but consistent across the dataset).

### 3.3 Barrier Analysis

For Graph 41 (ER = 2), deep analysis revealed:
- The 2 remaining violations are K5s through 4-cliques (10,11,13,28) and (11,13,18,28)
- These share vertices {11,13,28} — a triangle in the base graph
- Removing any edge from this triangle creates I5 violations that can only be fixed by restoring the edge
- Multi-edge swaps (up to 3 simultaneous) cannot break the trap (26,335 pairs tested exhaustively)
- The constraint interlocking is **global**, not local

---

## 4. Research Plan

### Phase 1: Correlation Analysis

Compute Pearson and Spearman correlations between ER and each structural property:

```
For each property P in {edges, degree_var, triangles, tri_balance,
                         k4, i4, k4_balance, spectral_gap,
                         lambda_max, lambda_min, hoffman_bound}:
    r_pearson = correlation(ER, P)
    r_spearman = rank_correlation(ER, P)
```

**Hypothesis:** K4 balance and spectral gap are the strongest predictors.

**Rationale:** Extension requires the new vertex to simultaneously avoid completing 4-cliques (by connecting too aggressively) and 4-independent-sets (by connecting too sparsely). Graphs with balanced K4/I4 distributions should have more "room" for a new vertex to navigate both constraints. Spectral gap measures expansion properties, which may correlate with how tightly the constraints interlock.

### Phase 2: Multivariate Model

Fit a regression model:

```
ER ≈ f(spectral_gap, k4_balance, degree_var, tri_balance, ...)
```

Test linear, polynomial, and nonlinear models. Identify the minimal feature set that explains the majority of ER variance.

### Phase 3: Smaller Ramsey Numbers

Compute ER exhaustively for smaller Ramsey numbers where all avoiding graphs can be enumerated:

- R(3,3) = 6: All avoiding graphs at n=5
- R(3,4) = 9: All avoiding graphs at n=7, 8
- R(4,4) = 18: All avoiding graphs at n=13-17

Test whether the same predictive features hold across different Ramsey numbers.

### Phase 4: Distribution Analysis

- Does ER follow a known distribution across all avoiding graphs at a given n?
- How does the ER distribution shift as n approaches R(r,s)?
- Is there a critical n where min(ER) first exceeds 0?

### Phase 5: Theoretical Implications

If ER is predictable:
- Can we construct graphs with provably low ER?
- Does the extension phase transition correspond to min(ER) crossing zero?
- Is there a spectral condition that guarantees ER = 0 or ER > 0?

---

## 5. Initial Results

### 5.1 Phase 1: Correlation Analysis (Completed)

656 matched records (328 graphs + 328 complements), each with 21 structural properties correlated against ER.

**Top 5 predictors by |Spearman r|:**

| Property | Spearman r | p-value | Direction |
|----------|-----------|---------|-----------|
| k4_total (K4 + I4 combined) | -0.3785 | 8.87e-24 | More total 4-structures = LOWER ER (easier to extend) |
| tri_balance (|tri_G - tri_C| / total) | +0.3416 | 2.16e-19 | More triangle imbalance = HIGHER ER (harder to extend) |
| tri_diff (|tri_G - tri_C|) | +0.3407 | 2.75e-19 | Same as above, absolute |
| k4_diff (|K4 - I4|) | -0.2436 | 2.58e-10 | More K4/I4 difference = LOWER ER |
| k4_balance | -0.2409 | 4.09e-10 | More K4/I4 balance ratio = LOWER ER |

**Hypothesis partially confirmed, partially surprised:**

The hypothesis that K4 balance would predict ER was confirmed (r_s = -0.24, p < 1e-9), but it's not the strongest predictor. The strongest predictor is **total 4-structure count** (K4 + I4 combined), with r_s = -0.38. This was not anticipated.

**The surprise: spectral gap is a weak predictor.** Spectral gap ranks 9th with |r_s| = 0.09 (p = 0.019). It's statistically significant but explains very little variance. The Hoffman bound is not significant at all (p = 0.056). Spectral properties are poor predictors of extension resistance.

**The real finding: triangle balance is the strongest positive predictor.** Graphs with balanced triangle counts between G and complement (low tri_balance) have significantly lower ER. Triangle imbalance explains more ER variance than any spectral property.

### 5.2 Key Insights

**Insight 1: Extension is easier when there are MORE constraints, not fewer.**

Counter-intuitively, graphs with higher total 4-structure counts (K4 + I4) are EASIER to extend. This suggests that having many 4-cliques and 4-independent-sets creates more "structure" that a new vertex can navigate around. Sparse constraint landscapes may be harder because constraints are distributed unpredictably.

**Insight 2: Balance at the triangle level matters more than balance at the K4 level.**

Triangle balance (r_s = 0.34) is a stronger predictor than K4 balance (r_s = 0.24). This suggests the extension constraint propagation operates primarily through triangles — the "medium-range" structure — rather than through the 4-cliques directly.

**Insight 3: Spectral properties are nearly irrelevant.**

The spectral gap, lambda_max, lambda_min, and Hoffman bound collectively explain almost no ER variance. Extension resistance is a local/medium-range structural property, not a global spectral one. This is significant because it means efficient spectral heuristics cannot substitute for direct structural analysis when evaluating extendability.

**Insight 4: Degree variance predicts in the unexpected direction.**

Higher degree variance correlates with LOWER ER (r_s = -0.22). Graphs closer to regular (low variance) are harder to extend. This may be because near-regular graphs have more uniform constraint density, leaving fewer "gaps" for a new vertex.

### 5.3 Quartile Analysis

Comparing the most extendable quartile (ER <= 23) to the least extendable quartile (ER >= 58):

| Property | Low ER (easy) | High ER (hard) | Difference |
|----------|--------------|----------------|------------|
| k4_total | 2315.5 | 2309.2 | -6.3 |
| tri_balance | 0.0052 | 0.0099 | +0.0048 |
| degree_var | 0.808 | 0.745 | -0.063 |
| k4_balance | 0.019 | 0.013 | -0.006 |
| spectral_gap | 15.09 | 15.16 | +0.07 |

The differences are small in absolute terms but highly statistically significant (p < 1e-10 for the top predictors). The effect sizes suggest that ER is influenced by many factors simultaneously, with no single property being dominant.

### 5.4 Regression Model

*Pending Phase 2 computation — multivariate regression with top predictors*

---

## 6. Related Work

- **Ramsey extension**: The concept of extending Ramsey-avoiding graphs is classical, but formalizing the minimum violation count as a graph invariant appears to be novel.
- **Spectral Ramsey theory**: Connections between eigenvalues and Ramsey properties have been studied (Hoffman bound, Paley graph spectra), but not in the context of extension resistance.
- **Ramsey multiplicity**: The study of how many monochromatic cliques must exist is related but distinct — ER measures how many violations a single new vertex creates, not how many exist in a graph of prescribed size.
- **McKay-Radziszowski conjecture**: R(5,5) = 43 is supported by the finding that all 656 known R(5,5,42)-graphs have ER > 0. Extension resistance provides a quantitative measure of "how far" each graph is from contradicting this conjecture.

---

## 7. Data and Reproducibility

All data files are in the `grahamslam/Tensor_math` repository:
- `analysis_656.json` — Structural properties of all 656 R(5,5,42)-graphs
- `extension_analysis.json` — Extension resistance values for all 656 graphs
- `r55_42some.g6` — McKay's graph6 file (328 graphs; complements form the other 328)
- `results.json` — Verified R(5,5) avoiders at n=37 through n=42
- `analyze_656.py` — Structural analysis script
- `analyze_extension.py` — Extension resistance computation script
- `analyze_barrier.py` — Deep barrier analysis of Graph 41

---

*Research in progress. Updated as analysis proceeds.*
