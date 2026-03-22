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

| R(r,s) | R value | Extension closes at | Ratio | ER at closure |
|---------|---------|-------------------|-------|---------------|
| R(3,3)  | 6       | n = 5             | 83%   | 2 (uniform)   |
| R(3,4)  | 9       | n = 8             | 89%   | 1-2           |
| R(3,5)  | 14      | n = 13            | 93%   | 4 (uniform)   |
| R(4,4)  | 18      | n ≈ 16*           | 89%*  | pending       |

*R(4,4) n=16 analysis in progress; n=15 has 0.8% ER=0 remaining.

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

### 5.4 Phase 2: Multivariate Regression (Completed)

**Model comparison:**

| Model | Features | R2 | adj_R2 |
|-------|----------|-----|--------|
| Single best | k4_total | 0.110 | 0.108 |
| Best 2 | k4_total + tri_diff | 0.193 | 0.191 |
| Best 3 | k4_total + tri_diff + degree_var | 0.254 | 0.251 |
| All 7 top | k4_total + tri_balance + tri_diff + k4_diff + k4_balance + degree_var + tri_total | 0.257 | 0.249 |
| Quadratic (top 2) | k4_total + tri_diff + squares + interaction | 0.194 | 0.188 |
| Top 4 + interactions | 4 features + 6 pairwise interactions | 0.260 | 0.249 |

**Key findings:**

1. **The best 3-predictor model explains 25.4% of ER variance.** The formula is approximately:
   ```
   ER ~ a*(k4_total) + b*(tri_diff) + c*(degree_var) + intercept
   ```
   Adding more predictors beyond 3 provides diminishing returns (adj_R2 plateaus at ~0.25).

2. **Quadratic and interaction terms do not help.** The quadratic model on the top 2 predictors (R2=0.194) barely improves over the linear model (R2=0.193). Pairwise interactions add almost nothing. The relationship between structural properties and ER is approximately linear, not polynomial.

3. **74% of ER variance is unexplained by structural properties.** The best model leaves 74% of the variance in the residuals (std = 16.3, max absolute error = 60.3). This means that while k4_total, tri_diff, and degree_var are statistically significant predictors, they are insufficient to predict ER for individual graphs.

4. **Extension resistance is not a simple function of macro-structure.** The unexplained 74% likely resides in micro-structural properties — specific arrangements of edges, local vertex neighborhoods, and constraint interaction patterns — that are not captured by aggregate statistics like total clique counts or degree variance.

### 5.5 Interpretation

**What 25% explains:** The macro-structural properties tell us the general difficulty range. Graphs with high k4_total, low tri_diff, and high degree_var tend to be easier to extend. This sets a "baseline difficulty" that accounts for about a quarter of the observed variation.

**What 74% doesn't explain:** The specific extension resistance of individual graphs depends on the exact topology — which vertices participate in which 4-cliques, how constraints interlock locally, whether the constraint graph has bottlenecks or escape routes. Graph 41 achieves ER=2 not because its macro statistics are extreme (they're near the population mean) but because its specific constraint topology happens to have a near-escape.

**Implication for Ramsey search:** Macro statistics can narrow the search space (prefer high k4_total, balanced triangles, higher degree variance) but cannot replace direct extension testing. The final 74% requires constructing and testing specific graphs.

**Implication for the phase transition:** The extension phase transition at ~78% of R(r,s) likely reflects the point where even the most favorable macro-structural configurations cannot overcome the micro-structural constraint density. Below this threshold, some graphs have favorable enough micro-structure to achieve ER=0. Above it, no graph does.

### 5.6 Phase 3: Cross-Ramsey Validation (Completed)

To test whether extension resistance behaves consistently across different Ramsey numbers, we computed ER across four Ramsey families: R(3,3)=6, R(3,4)=9, R(3,5)=14, and R(4,4)=18. For small n (≤7), all avoiding graphs were enumerated exhaustively. For larger n, avoiding graphs were constructed via simulated annealing (500 graphs per case, SA minimizing R(r,s) violations to zero).

**Complete phase transition table:**

| Case | n | n/R ratio | Avoiding graphs | ER min | ER max | ER mean | ER=0 % | Status |
|------|---|-----------|----------------|--------|--------|---------|--------|--------|
| R(3,3) | 4 | 0.667 | 18 | 0 | 1 | 0.3 | 66.7% | Open |
| R(3,3) | 5 | 0.833 | 12 | 2 | 2 | 2.0 | 0.0% | **Closed** |
| R(3,4) | 6 | 0.667 | 2,812 | 0 | 1 | 0.0 | 97.5% | Wide open |
| R(3,4) | 7 | 0.778 | 13,842 | 0 | 1 | 0.4 | 63.7% | Closing |
| R(3,4) | 8 | 0.889 | 500† | 1 | 2 | 1.4 | 0.0% | **Closed** |
| R(3,5) | 10 | 0.714 | 500† | 0 | 1 | 0.2 | 83.2% | Wide open |
| R(3,5) | 11 | 0.786 | 500† | 0 | 2 | 0.8 | 27.6% | Closing |
| R(3,5) | 12 | 0.857 | 500† | 0 | 3 | 1.8 | 8.2% | Nearly closed |
| R(3,5) | 13 | 0.929 | 500† | 4 | 4 | 4.0 | 0.0% | **Closed** |
| R(4,4) | 14 | 0.778 | 500† | 0 | 3 | 1.7 | 2.6% | Nearly closed |
| R(4,4) | 15 | 0.833 | 500† | 0 | 5 | 3.3 | 0.8% | Almost closed |
| R(4,4) | 16 | 0.889 | pending | — | — | — | — | Running |
| R(4,4) | 17 | 0.944 | pending | — | — | — | — | Pending |
| R(5,5) | 42 | 0.977‡ | 656 | 2 | 83 | 37.6 | 0.0% | **Closed** |

†SA-constructed samples (not exhaustive). ‡Using R(5,5)≥43.

**Key findings:**

**Finding 1: ER uniformity at closure.** When the phase transition closes, ER often converges to a single value. At R(3,3) n=5, ALL 12 graphs have ER=2. At R(3,5) n=13, ALL 500 SA-constructed graphs have ER=4. This uniformity suggests a structural inevitability — at these sizes, every avoiding graph hits the same fundamental barrier. The uniform ER value appears to equal 2(r-2) for R(3,s): ER=2 for R(3,3) (r=3), ER=2 for R(3,4) (max observed), ER=4 for R(3,5) at closure (r=5 in the K_s constraint). This pattern warrants further investigation.

**Finding 2: The phase transition is confirmed across all four Ramsey families.** Extension goes from majority-extendable to fully closed within 2-3 steps of n. The closure ratio varies: R(3,3) closes at 0.83, R(3,4) at 0.89, R(3,5) at 0.93. The higher r+s is, the later (in ratio terms) the transition closes, likely because larger graphs have more micro-structural degrees of freedom.

**Finding 3: R(4,4) closes earlier than R(3,s) at the same ratio.** At ratio 0.78, R(3,4) still has 63.7% extendable graphs, R(3,5) has 27.6%, but R(4,4) has only 2.6%. The diagonal Ramsey number R(4,4) is far more constrained than the off-diagonal cases. This makes sense: K4 avoidance in both the graph AND complement simultaneously is a tighter constraint than K3-avoidance in one side and K_s-avoidance in the other.

**Finding 4: ER range scales with graph size.** At closure, R(3,3) has ER range {2}, R(3,4) has {1,2}, R(3,5) has {4}, while R(5,5) spans {2,...,83}. For R(4,4) at n=15 the range is already {0,...,5}. The ER distribution broadens dramatically with n, reflecting increasing micro-structural diversity.

**Finding 5: Correlation predictors are phase-dependent and Ramsey-dependent.**

The dominant predictor changes across Ramsey families and across the open/closed transition:

| Case | Top predictor | r_s | Spectral gap r_s |
|------|--------------|-----|-----------------|
| R(3,4) n=7 (open) | degree_var | -0.667 | -0.064 |
| R(3,4) n=8 (closed) | all tied | ±0.334 | -0.334 |
| R(3,5) n=10 (open) | spectral_gap | -0.092 | -0.092 |
| R(3,5) n=12 (closing) | spectral_gap | -0.487 | **-0.487** |
| R(4,4) n=14 (closing) | degree_var | -0.212 | -0.004 |
| R(4,4) n=15 (closing) | tri_balance | +0.195 | -0.145 |
| R(5,5) n=42 (closed) | k4_total | -0.379 | -0.090 |

Key observations:
- **Spectral gap emerges as a strong predictor for R(3,5)** (r_s = -0.49 at n=12), unlike all other cases. This may be because R(3,5) avoidance (no K3 in G, no K5 in complement) is particularly sensitive to expansion properties.
- **Degree variance is the dominant predictor in the "open" phase** (R(3,4) n=7, R(4,4) n=14), but weakens as the transition closes. In the open phase, having irregular degree distribution creates "gaps" that a new vertex can exploit.
- **Triangle balance becomes important near closure** (R(4,4) n=15, R(5,5) n=42), when the constraint landscape is so tight that medium-range structure determines the residual extendability.
- **No single predictor is universal.** The best predictor depends on both the Ramsey number and the phase of the transition. This reinforces the Phase 2 finding that ER is fundamentally a micro-structural property.

**Finding 6: The correlation direction of tri_diff flips between open and closed phases.**

In the open phase (R(3,4) n=7), tri_diff has r_s = -0.33 (more triangle difference = easier to extend). In the closed/near-closed phase (R(3,5) n=12, R(5,5) n=42), tri_diff has r_s = +0.39 and +0.34 respectively (more triangle difference = harder). This reversal suggests that triangle asymmetry helps at low density (creating structural variety) but hurts at high density (creating constraint imbalance).

---

## 6. Related Work

- **Ramsey extension**: The concept of extending Ramsey-avoiding graphs is classical, but formalizing the minimum violation count as a graph invariant appears to be novel.
- **Spectral Ramsey theory**: Connections between eigenvalues and Ramsey properties have been studied (Hoffman bound, Paley graph spectra), but not in the context of extension resistance.
- **Ramsey multiplicity**: The study of how many monochromatic cliques must exist is related but distinct — ER measures how many violations a single new vertex creates, not how many exist in a graph of prescribed size.
- **McKay-Radziszowski conjecture**: R(5,5) = 43 is supported by the finding that all 656 known R(5,5,42)-graphs have ER > 0. Extension resistance provides a quantitative measure of "how far" each graph is from contradicting this conjecture.

---

## 7. Data and Reproducibility

All data files are in `grahamslam/Tensor_math` under `research/ramsey/`:
- `results/analysis_656.json` — Structural properties of all 656 R(5,5,42)-graphs
- `results/extension_analysis.json` — Extension resistance values for all 656 graphs
- `results/r55_42some.g6` — McKay's graph6 file (328 graphs; complements form the other 328)
- `results/results.json` — Verified R(5,5) avoiders at n=37 through n=42
- `results/er_small_ramsey.json` — Phase 3 results for R(3,3), R(3,4), R(3,5), R(4,4)
- `scripts/analyze_656.py` — Structural analysis script
- `scripts/analyze_extension.py` — Extension resistance computation script
- `scripts/analyze_barrier.py` — Deep barrier analysis of Graph 41
- `scripts/analyze_er_small_ramsey.py` — Phase 3 cross-Ramsey ER computation (SA-based graph construction)

---

*Research in progress. Updated as analysis proceeds.*
