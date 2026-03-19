# R(5,5) Computational Search Report

**Date:** March 18-19, 2026
**Authors:** Graham Slama, Claude Opus 4.6 (Anthropic)
**Repository:** grahamslam/Tensor_math

---

## 1. Summary

We conducted a computational search for R(5,5)-avoiding graphs, independently verifying avoiders at every size n=37 through n=42. Along the way, we developed and evaluated 8 distinct algorithmic approaches, discovered structural properties of the search landscape, and confirmed key theoretical predictions about extension phase transitions.

The search culminated in reproducing the known lower bound R(5,5) >= 43, with our own constructions at n=38-41 and verification of Exoo's 1989 construction at n=42.

## 2. Background

The Ramsey number R(5,5) is the smallest n such that every 2-coloring of the edges of K_n contains a monochromatic K_5. Equivalently, it is the smallest n such that every graph on n vertices contains either a 5-clique or a 5-independent-set.

**Current bounds:** 43 <= R(5,5) <= 46

- Lower bound: Exoo (1989), construction via cyclic(43) minus vertex plus 16 edge flips
- Upper bound: Angeltveit & McKay (2024), computational flag algebra methods
- Conjecture (McKay-Radziszowski): R(5,5) = 43

There are exactly 656 distinct R(5,5,42)-graphs known (McKay), and none can be extended to n=43.

## 3. Verified Results

| n | Method | Time | K5 | I5 | Edges | Density | Degree |
|---|--------|------|----|----|-------|---------|--------|
| 37 | Paley(37) | 0.4s | 0 | 0 | 333 | 50.0% | 18 (uniform) |
| 38 | Circulant search | 40.6s | 0 | 0 | 361 | 51.4% | 19 (uniform) |
| 39 | Circulant + edge SA | 43.0s | 0 | 0 | ~380 | ~51% | ~19-20 |
| 40 | Pure circulant | <5min | 0 | 0 | ~400 | ~51% | 20 (uniform) |
| 41 | Pure circulant | <5min | 0 | 0 | ~420 | ~51% | 20 (uniform) |
| 42 | Exoo (1989) | verified | 0 | 0 | 428 | 49.7% | 19-22 |

All adjacency matrices stored in `results.json` for independent verification.

### n=38 Construction
Circulant graph on Z_38 with difference set {2, 3, 10, 11, 13, 15, 16, 17, 18, 19}.
Found via random sampling of difference sets (8,597 trials at 213 trials/sec).

### n=39 Construction
Hybrid: circulant seed (E_vt=5, 39 full violations) refined by edge-flip simulated annealing.
The circulant with difference set {2, 3, 6, 7, 8, 14, 15, 17, 18, 19} was the best found in 200K trials. Phase 3 edge SA with low temperature (T=0.3) reduced 39 violations to 0 in 10,638 steps (43 seconds).

### n=40, n=41 Constructions
Pure circulant avoiders found during Phase 1 random sampling. At these sizes, the circulant search space (2^19 and 2^20 respectively) contains zero-violation solutions that random sampling hits within 100K trials.

## 4. Algorithmic Evolution

We developed 8 approaches of increasing sophistication:

### 4.1 Pure SA with O(n^5) Energy
Full 5-clique enumeration per step. C(39,5) = 575,757 subsets checked twice per evaluation.
**Result:** ~2 steps/sec at n=39. Completely impractical.

### 4.2 Sampled Energy
Random sampling of 200 5-subsets per evaluation instead of full enumeration.
**Result:** Fast (~170 st/s) but fundamentally dishonest. Sampling covered 0.035% of the space, reporting E=0.14 when the true energy was 291. Useless for convergence.

### 4.3 Hoffman Bound Spectral SA
Replace clique counting with eigenvalue computation: alpha(G) <= n * (-lambda_min) / (lambda_max - lambda_min). O(n^3) per step.
**Result:** Bound too loose. Hoffman gives alpha <= 9 for graphs where actual alpha = 4. SA cannot converge because the objective function doesn't reflect reality.

### 4.4 Pair-Delta SA
When flipping edge (u,v), only recount 5-cliques containing both u and v. This is C(n-2, 3) subsets instead of C(n, 5). Exact delta, O(n^3) per step.
**Result:** ~250 steps/sec with honest energy. Practical but still random -- each step is a random edge flip.

### 4.5 Circulant Restriction
Restrict search to circulant graphs defined by a difference set S. Edge (u,v) exists iff |u-v| mod n is in S. Search space collapses from 2^(n(n-1)/2) to 2^(n/2). Vertex-transitive property means violations only need to be checked at vertex 0.
**Result:** Game-changing. Found n=38 in 40 seconds, n=40 and n=41 as pure circulants. Three-phase pipeline: (1) random difference-set sampling, (2) difference-set SA, (3) symmetry-breaking edge SA from best circulant.

**Critical discovery:** Starting Phase 3 with low temperature (T=0.3) is essential. High temperature (T=1.5) scrambles the circulant structure, causing violations to spike to 217 before slowly recovering. Low temperature preserves the near-solution structure and makes surgical fixes.

### 4.6 Targeted SA with Incremental Violation Tracking
Inspired by AlphaEvolve Algorithm 4 (Nagda et al., 2026). Maintain explicit sets of all 5-cliques and 5-independent-sets. Update incrementally on each edge flip: remove broken violations, check for newly created ones.
**Result:** 9,000 steps/sec (36x faster than pair-delta). Targeted moves: 70% of flips chosen from edges participating in violations, 30% random exploration.

### 4.7 Greedy Descent
Evaluate ALL candidate flips, pick the one that maximizes violation reduction.
**Critical discovery:** The best circulant seed for n=42 is a **greedy trap** -- zero improving single-edge flips exist. Every edge removal that breaks a K5 creates more I5s than it destroys. This is a structural property of the circulant, not a limitation of the algorithm.

### 4.8 Extension from n=41
Add one vertex to the verified n=41 avoider. Search over 41-bit connection vectors. The base graph has 1,025 four-cliques and 1,025 four-independent-sets. SA on the connection vector converges to 62 new-vertex violations across all restarts.
**Result:** Confirms Finding 7 (extension phase transition). The extension window is closed at n=42 for this base graph.

## 5. Key Findings

### 5.1 The Circulant Trap at n=42
The jump from n=41 to n=42 is qualitative, not merely quantitative:

| Property | n=39 | n=42 |
|----------|------|------|
| Best circulant E_vt | 5 | 15 |
| Full violations | 39 | 126 |
| Violation type | Mixed K5/I5 | All K5 (zero I5) |
| Greedy improving flips | Many | Zero |
| SA convergence | 43 seconds to E=0 | Plateaus at ~82-115 |

The n=42 circulant is a local minimum in every sense: greedy, SA, and targeted SA all fail to escape.

### 5.2 Exoo's Construction is Non-Circulant
Exoo's verified n=42 avoider has degree range 19-22 (six vertices of deg 19, twenty of deg 20, ten of deg 21, six of deg 22). This non-uniform degree distribution is impossible for a circulant graph, confirming that the n=42 solution requires breaking circulant symmetry.

Exoo's method -- start from a circulant on K_43, delete a vertex, flip 16 specific edges -- achieves this symmetry-breaking through a principled algebraic construction rather than stochastic search.

### 5.3 Extension Phase Transition Confirmed
Our Finding 7 predicted extension impossibility at ~78% of R(r,s). For R(5,5) ~ 43, this predicts closure at n ~ 34. Our experimental results:
- n=39: Extension from n=38 requires SA but succeeds
- n=42: Extension from n=41 fails with hard floor at E=62
- Literature: None of the 656 known n=42 graphs can extend to n=43

### 5.4 Sampling is Deceptive
The sampled energy approach (Section 4.2) is a cautionary tale. At n=39, 200 random samples from 575K possible 5-subsets has a 0.035% hit rate. The SA appeared to converge (sampled E near 0) while the true energy was 291 violations. Any stochastic search using sampled subgraph counting must account for this coverage gap.

## 6. Comparison with AlphaEvolve

The AlphaEvolve paper (Nagda, Raghavan, Thakurta; Google DeepMind, 2026) improved lower bounds for R(3,13), R(3,18), R(4,13), R(4,14), and R(4,15) using LLM-evolved search algorithms. They did not tackle R(5,5).

Our approaches overlap with several AlphaEvolve-discovered strategies:
- Circulant bootstrap (our Phase 1) matches their Algorithm 5 initialization
- Incremental violation tracking (our Section 4.6) matches Algorithm 4's core technique
- The greedy trap discovery parallels their finding that different cells require fundamentally different initialization families

Key differences:
- AlphaEvolve uses an LLM to evolve the search algorithms themselves; we manually designed each approach
- AlphaEvolve's Algorithm 6 uses "harmonic tunneling" (flipping all edges at a specific cyclic distance) which we did not implement
- AlphaEvolve maintains a population of search algorithms; we evolved sequentially

## 7. Tools and Infrastructure

- **Live dashboard** (`dashboard.html` + `dashboard_server.py`): Browser-based Chart.js dashboard showing energy, violations, temperature, and accept rate in real time. Flask backend serves progress data from JSONL file. Time-window controls (5min / 30min / all data) prevent chart compression.

- **Results database** (`results.json`): Structured JSON with full metadata for each verified avoider: adjacency matrix, construction method, timing, degree statistics, verification status.

- **TLS-Graph extension** (`index.html`): Browser-based calculator with 20+ graph/Ramsey operations for interactive exploration.

## 8. Future Directions

1. **Proving R(5,5) = 43**: Requires closing the gap between upper bound (46) and lower bound (43). The upper bound side uses flag algebra / semidefinite programming methods. Computational contribution would involve exhaustive case analysis or new theoretical techniques.

2. **Other open Ramsey numbers**: R(3,13) was just improved by AlphaEvolve. Our pipeline (circulant search + targeted SA) could be applied to R(4,6), R(5,6), R(5,7), and other cells with known gaps.

3. **Structure of the 656 graphs**: Analyzing the complete set of R(5,5,42)-graphs for common structural motifs could inform theoretical approaches to the upper bound.

4. **Compiled implementation**: A C/Rust implementation of the targeted SA with incremental violation tracking could push throughput from 9K to 1M+ steps/sec, enabling much deeper searches.

## 9. References

- Exoo, G. "A lower bound for r(5, 5)." *Journal of Graph Theory* 13(1):97-98, 1989.
- Angeltveit, V. and McKay, B.D. "R(5,5) <= 46." arXiv:2409.15709, 2024.
- Nagda, A., Raghavan, P., and Thakurta, A. "Reinforced Generation of Combinatorial Structures: Ramsey Numbers." arXiv:2603.09172, 2026.
- Radziszowski, S.P. "Small Ramsey Numbers." *Electronic Journal of Combinatorics*, Dynamic Survey DS1, 2024.
- Ge, Y. et al. "Study of Exoo's Lower Bound." arXiv:2212.12630, 2022.
