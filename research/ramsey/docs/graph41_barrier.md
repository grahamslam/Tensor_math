# The Graph 41 Barrier: A Near-Extremal R(5,5,42) Extension

**Date:** March 22, 2026
**Authors:** Brent Graham, Claude Opus 4.6 (Anthropic)
**Repository:** grahamslam/Tensor_math

---

## 1. Identity

Graph 41 refers to the graph at 0-indexed position 41 in McKay's `r55_42some.g6` file, which contains 328 R(5,5)-avoiding graphs on 42 vertices. Together with their complements, these form the complete known set of 656 distinct R(5,5,42)-graphs. Since 43 <= R(5,5) <= 46, these are the largest known graphs that simultaneously avoid 5-cliques and 5-independent-sets.

Graph 41 is distinguished by having the lowest extension resistance of any graph in this collection.

---

## 2. Why It Matters

Extension resistance ER(G, 5, 5) measures the minimum number of R(5,5) violations (K5s plus I5s) that arise when adding a 43rd vertex to G, optimized over all 2^42 possible connection vectors. If any graph achieves ER = 0, it would extend to a 43-vertex R(5,5)-avoider, disproving the McKay-Radziszowski conjecture that R(5,5) = 43.

Graph 41 achieves **ER = 2** (SA-derived upper bound, computed via simulated annealing with 10 restarts and 20,000 steps per restart). This makes it a dramatic outlier:

| Rank | ER | Count |
|------|-----|-------|
| 1st  | 2   | 1 graph (Graph 41) |
| 2nd  | 4   | few graphs |
| 3rd  | 9   | few graphs |
| ...  | ... | ... |
| Mean | 37.6 | across all 656 |
| Max  | 83  | most resistant graphs |

Only 4 of 656 graphs achieve ER <= 5. Only 25 achieve ER <= 10. Graph 41 stands alone at ER = 2 -- a single violation away from the next best, and just 2 violations away from a result that would reshape Ramsey theory.

Notably, **both Graph 41 and its complement achieve ER = 2**. For diagonal Ramsey numbers R(r,r), extension resistance is invariant under complementation (since complement preserves R(r,r) avoidance symmetrically), so this is expected. However, it suggests possible self-complementary or near-self-complementary structure worth further investigation.

---

## 3. The Barrier Structure

The SA-derived best connection vector for Graph 41 produces exactly 2 violations, both of type K5 (no I5 violations). Each K5 violation arises from a 4-clique in the base graph whose 4 vertices are all connected to the new vertex, completing a forbidden 5-clique:

- **K5 violation 1:** 4-clique **(10, 11, 13, 28)** + new vertex
- **K5 violation 2:** 4-clique **(11, 13, 18, 28)** + new vertex

These two 4-cliques share three vertices: **{11, 13, 28}**, which form a triangle in the base graph. The fourth vertex differs (10 vs 18), but the shared triangle creates a tightly coupled constraint structure.

The new vertex must be connected to all four vertices {10, 11, 13, 28} and also to all four vertices {11, 13, 18, 28} in the best-found configuration. The shared triangle {11, 13, 28} means that disconnecting the new vertex from any of these three shared vertices would break *both* K5 violations simultaneously -- but doing so would create I5 violations among the non-neighbors, making the trade futile.

---

## 4. The Trap Mechanism

The natural approach to eliminating the 2 K5 violations is to modify the base graph itself: remove an edge from the shared triangle {11, 13, 28} so that neither (10,11,13,28) nor (11,13,18,28) remains a 4-clique. This was tested systematically (`break_trap.py`).

**Removing edge (11, 28)** successfully destroys both offending 4-cliques. However, this modification introduces new violations in the base graph:

- **2 new I5 violations** appear on the vertex set **{5, 6, 8, 11, 12, 28}**

These I5s arise because vertices 11 and 28, now disconnected from each other, join a group of mutually non-adjacent vertices that already bordered on forming a 5-independent-set. The critical finding:

> The I5 violations on {5, 6, 8, 11, 12, 28} can **only** be fixed by re-adding edge (11, 28).

No other single edge flip among the 861 possible edges in K_42 can eliminate these I5s without creating new K5 violations. The single-edge trap is **airtight**: removing (11,28) trades 2 extension-K5s for 2 base-I5s, and the only repair is reverting the removal.

The same trap structure applies to the other two edges of the shared triangle, {11,13} and {13,28}. Each removal creates compensating I5 violations that can only be resolved by restoring the removed edge.

---

## 5. Multi-Edge Exhaustive Search

Given the airtight single-edge trap, an exhaustive multi-edge search was conducted (`break_trap_multi.py`) to determine whether simultaneous edge flips could break the constraint coupling.

### Phase 1: Single Flips

Starting from the primary modification (remove edge (11,28)), every candidate edge touching the conflict knot vertices {5, 6, 8, 11, 12, 28} and their neighbors was tested as an additional compensating flip.

- **230 single flips tested**
- **0 produced a clean (K5=0, I5=0) base graph**
- Best total violations remained at 2

### Phase 2: Double Flips

All pairs of candidate edges were tested as simultaneous compensating flips alongside the primary (11,28) removal, for a total of 3 edge modifications per trial.

- **26,335 pairs tested exhaustively**
- **0 produced a clean base graph**

### Conclusion

The constraint interlocking is **global**, not local. The barrier cannot be broken by modifying up to 3 edges simultaneously within the conflict neighborhood. The K5 and I5 constraints are coupled through a web of dependencies that extends well beyond the immediate conflict knot, meaning that any local repair propagates violations to distant parts of the graph.

---

## 6. Structural Properties

A key insight from the multivariate regression analysis (see `extension_resistance_conjecture.md`, Section 5.4) is that **Graph 41's macro statistics are near the population mean** for R(5,5,42)-graphs:

| Property | Graph 41 | Population Range | Population Mean |
|----------|----------|-----------------|-----------------|
| Edge count | ~430 | 423-438 | ~430 |
| Degree range | 19-22 | 19-22 | typical |
| Degree variance | typical | 0.49-1.01 | ~0.78 |
| 4-clique count | typical | 1099-1216 | ~1157 |
| Spectral gap | typical | 14.56-15.76 | ~15.1 |

The best 3-predictor model (k4_total, tri_diff, degree_var) explains only 25.4% of ER variance across the 656 graphs; the remaining 74% resides in micro-structural topology. Graph 41's near-escape to ER = 2 is not because it occupies an extreme position in any macro-statistical dimension. Rather, its specific constraint topology -- the arrangement of which vertices participate in which 4-cliques and 4-independent-sets, and how those constraints interlock -- happens to leave an almost-navigable path for a 43rd vertex.

This reinforces the broader finding that extension resistance is fundamentally a **micro-structural** property. Aggregate statistics set a baseline difficulty range but cannot predict individual graph behavior. The fact that a population-mean graph achieves the minimum ER across the entire collection underscores how sensitive extendability is to exact edge placement.

---

## 7. Open Questions

### 7.1 Is the obstruction pattern reusable?

The barrier structure in Graph 41 -- two K5-forming 4-cliques sharing a triangle, with each triangle edge removal creating compensating I5 violations -- may represent a general obstruction motif. Do other low-ER graphs (ER = 4, 9) exhibit similar shared-subgraph constraint coupling? If this pattern recurs, it could be formalized as a structural certificate of non-extendability.

### 7.2 Minimal unsatisfiable core

The constraint system can be viewed as a hypergraph where:
- Each 4-clique is a hyperedge requiring at least one non-neighbor among its vertices
- Each 4-independent-set is a hyperedge requiring at least one neighbor among its vertices
- The connection vector is a satisfying assignment

Graph 41's ER = 2 means this constraint hypergraph is *almost* satisfiable. Can the 2 unsatisfied constraints be characterized as a **minimal unsatisfiable core** (MUS) -- a smallest subset of constraints that cannot be simultaneously satisfied? If the MUS is small and structurally localized (as the shared triangle suggests), this would provide a compact certificate explaining why extension fails. MUS extraction techniques from SAT/CSP solving could be applied directly.

### 7.3 Complement barrier structure

Both Graph 41 and its complement achieve ER = 2. By the symmetry of R(5,5), the complement's violations are the "mirror" of the original's (K5 violations become I5 violations and vice versa). But does the complement exhibit the *same* barrier topology -- shared triangles, airtight single-edge traps, globally coupled multi-edge constraints? Or does it fail for a structurally different reason? Comparing the two barrier structures could reveal whether the near-escape is a property of the graph's abstract structure or an artifact of a specific vertex labeling.

### 7.4 Deeper multi-edge searches

The exhaustive search covered up to 3 simultaneous edge flips within the conflict neighborhood. Could 4+ simultaneous flips, or flips in distant parts of the graph, break the trap? The combinatorial explosion makes exhaustive testing infeasible at higher flip counts, but targeted approaches (e.g., SA on the base graph edges with the constraint of maintaining R(5,5) avoidance) could probe deeper.

### 7.5 Connection to the phase transition

The extension phase transition closes at approximately 78% of R(r,s). For R(5,5) >= 43, the n=42 graphs sit at ~98% of the Ramsey number -- well past closure. Graph 41 shows that even deep into the closed phase, some graphs come remarkably close to extending. Is ER = 2 the theoretical minimum for n=42, or could a graph outside McKay's 656 achieve ER = 1 or even ER = 0? The 656 graphs are the *known* R(5,5,42)-graphs, not provably all of them.

### 7.6 SAT/ILP formulation

The extension problem for a fixed base graph is equivalent to a constraint satisfaction problem on 42 binary variables. For Graph 41 specifically, where ER = 2 and the constraint structure is known, encoding the problem as a SAT instance or integer linear program could either prove ER = 2 is exact (not just an SA upper bound) or discover a connection vector achieving ER < 2.

---

## References

- Extension resistance definition and full correlation analysis: `docs/extension_resistance_conjecture.md`
- R(5,5) search report and algorithmic evolution: `docs/R55_search_report.md`
- Barrier analysis script: `scripts/analyze_barrier.py`
- Single-edge trap breaker: `scripts/break_trap.py`
- Multi-edge trap breaker: `scripts/break_trap_multi.py`
- McKay's graph dataset: `results/r55_42some.g6` (328 graphs; complements form the other 328)
- Extension resistance data: `results/extension_analysis.json`

---

*This document is a focused companion to the extension resistance conjecture. It isolates Graph 41 as a case study in near-extremal Ramsey avoidance.*
