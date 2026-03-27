# Tensor Standard Math Calculator

A self-contained tensor algebra calculator that treats every value — from plain integers to Ramsey colorings to Christoffel symbols — as a typed tensor object. Built on the **Tensor Language Specification (TLS) v0.2**.

[![Launch Calculator](https://img.shields.io/badge/Launch_Calculator-▶-blue?style=for-the-badge)](https://grahamslam.github.io/Tensor_math/)

No build step, no dependencies.

## What it does

| Input | Output | What's happening |
|-------|--------|-----------------|
| `1 + 2` | `3 (scalar)` | Rank-0 tensor addition |
| `cv(1,2) @ v(3,4)` | `11 (scalar)` | Covector contracts with vector |
| `m(1,2;3,4) @ v(5,6)` | `[17, 39] (vector)` | Matrix-vector contraction |
| `contract(T[a+,b-], v[b+])` | `[17, 39][a+]` | Index-aware contraction by label |
| `einsum('a+b-,b+c- -> a+c-', A, B)` | `[[19,22],[43,50]]` | Einstein summation convention |
| `christoffel(g, dg)` | `{T^0_{11}=...}` | Christoffel symbols from metric |
| `riemann(g, dg, ddg)` | Riemann, Ricci, R, K | Full curvature pipeline |
| `paley(13)` | `13x13 matrix` | Paley graph (quadratic residues) |
| `ramsey_check(paley(13), 4, 4)` | `false` | Paley(13) avoids R(4,4) |
| `ramsey_anneal(8, 3, 4)` | `8x8 matrix` | Simulated annealing Ramsey search |

## Features

**Core algebra**
- Scalars, vectors (`v`), covectors (`cv`), matrices (`m`), rank-3 tensors (`t3`)
- Addition `+`, subtraction `-`, tensor product `*`, contraction `@`
- Variance tracking (contravariant/covariant) on every operation
- Dimension and space compatibility checking

**Linear algebra**
- `trace`, `det`, `inv`, `transpose`, `norm`, `eigenvalues`
- `sym()` / `antisym()` — symmetry projection with propagation tracking
- `raise(v, g)` / `lower(w, g)` — variance change via metric tensor

**Differential geometry (TLS-Calc)**
- `christoffel(g, dg)` — Christoffel symbols from metric + first derivatives
- `riemann(g, dg, ddg)` — Riemann tensor, Ricci tensor, scalar curvature, Gaussian curvature (2D)
- `covariantD(mu, T, gamma, partialT)` — covariant derivative with Christoffel corrections
- `revar(T, '--')` — relabel index variance without changing components

**Graph theory & Ramsey theory (TLS-Graph)**

*Graph construction:*
- `adjacency(n)` — complete graph K_n as adjacency matrix
- `paley(p)` — Paley graph on prime p vertices (quadratic residues mod p, requires p ≡ 1 mod 4)
- `circulant(n, v(d1,d2,...))` — circulant graph with specified difference set
- `complement(A)` — flip edge colors (0↔1, diagonal stays 0)

*Graph analysis:*
- `degree(A)` — degree sequence as vector
- `triangles(A)` — count triangles via trace(A³)/6
- `cliques(A, k)` — count complete k-subgraphs (exhaustive)
- `independent_set(A, k)` — count independent sets of size k
- `chromatic(A)` — edge color counts (red/blue)
- `hadamard(A, B)` — element-wise (Hadamard) product

*Ramsey theory:*
- `ramsey_check(A, s, t)` — check if 2-coloring contains monochromatic K_s (red) or K_t (blue)
- `ramsey_search(n, s, t)` — random search for R(s,t)-avoiding colorings of K_n
- `ramsey_energy(A, r, s)` — compute Ramsey energy: count(K_r) + count(I_s), goal is 0
- `ramsey_anneal(n, r, s [, trials])` — simulated annealing search for R(r,s)-avoiding coloring

**Indexed notation (TLS-native)**
- `T[a+, b-]` — attach typed index labels to any tensor
- `contract(T[a+, b-], v[b+])` — contract by matching index labels
- `contract(A[a+, a-])` — self-contraction (trace) by repeated label
- Free/bound index tracking with variance and space validation

**Einstein summation convention**
- `einsum('a+b-, b+c- -> a+c-', A, B)` — variance-aware with automatic contraction
- Output index order controlled by the `->` clause
- Validates rank match, variance compatibility, and dimension agreement

**Environment**
- REPL tab with persistent declarations: `ring`, `space`, `tensor`, `metric`, `basis`
- `where` clauses for inline local bindings
- Strict and Educational evaluation modes
- Full TLS v0.2 specification embedded in the Specification tab

## Ramsey theory examples

```
# === Algebraic graph constructions ===

# Paley graph on 13 vertices — self-complementary, vertex-transitive
paley(13)
ramsey_check(paley(13), 4, 4)
# => false — Paley(13) avoids R(4,4)! (R(4,4)=18)

# Check its structure
cliques(paley(13), 3)         # 26 triangles
independent_set(paley(13), 4) # 0 independent 4-sets
chromatic(paley(13))          # red=39, blue=39 (self-complementary)

# Circulant graph — edges defined by difference set mod n
circulant(9, v(1,2,4))
# => 9-vertex graph where (u,v) connected iff |u-v| mod 9 in {1,2,4,5,7,8}

# === Ramsey energy and annealing ===

# Energy function: E(G) = count(K_r) + count(I_s)
# Goal: find coloring with E = 0
ramsey_energy(paley(13), 3, 4)
# => 26 (K_3=26, I_4=0) — not R(3,4)-free, but R(4,4)-free

# Simulated annealing search (inspired by AlphaEvolve)
ramsey_anneal(8, 3, 4)
# => 8x8 adjacency matrix with E=0 (R(3,4)=9, so K_8 has avoiding colorings)

ramsey_anneal(9, 3, 4)
# => best effort — may not reach E=0 since R(3,4)=9

# === Classical Ramsey verification ===

# R(3,3) = 6: every 2-coloring of K_6 has a monochromatic triangle
ramsey_search(5, 3, 3)   # finds avoiding coloring (possible)
ramsey_search(6, 3, 3)   # none found (impossible — R(3,3)=6)

# Tensor operations on graph adjacency matrices
let K = adjacency(6)
trace(K @ K)       # 30 = sum of squared degrees
trace(K @ K @ K)   # 120 = 6 * triangles(K) = 6 * 20
degree(K)          # [5,5,5,5,5,5] — regular graph
```

## Comparison with AlphaEvolve (Google DeepMind, March 2026)

The [AlphaEvolve Ramsey paper](https://arxiv.org/abs/2603.09172) improved lower bounds for R(3,13), R(3,18), R(4,13), R(4,14), and R(4,15) using LLM-evolved search algorithms. Our calculator implements the same building blocks their algorithms use:

| AlphaEvolve Technique | Our Calculator |
|----------------------|----------------|
| Paley graph seeding | `paley(p)` |
| Circulant/cyclic graphs | `circulant(n, S)` |
| Energy function E = K_r + I_s | `ramsey_energy(A, r, s)` |
| Simulated annealing | `ramsey_anneal(n, r, s)` |
| Clique counting | `cliques(A, k)` |
| Independent set counting | `independent_set(A, k)` |
| Graph complement | `complement(A)` |
| Ramsey validation | `ramsey_check(A, s, t)` |
| Spectral analysis | `eigenvalues(A)` |

AlphaEvolve is a meta-algorithm that *discovers* search algorithms. Our calculator provides the *tensor primitives* those algorithms build on — plus the ability to verify results, explore algebraic constructions, and analyze graph structure through tensor operations (contraction, trace, spectral decomposition).

## GR example: unit sphere curvature

```
christoffel(m(1,0;0,0.75), t3(0,0;0,0.866|0,0;0,0))
# => Christoffel symbols

riemann(m(1,0;0,0.75), t3(0,0;0,0.866|0,0;0,0), t3(0,0;0,-1|0,0;0,0|0,0;0,0|0,0;0,0))
# => R=2, K=1 (unit sphere)
```

## Python Research Engine

For large-scale Ramsey research beyond browser limits:

```bash
python engine.py                                    # Paley survey + extension landscapes
python research/ramsey/scripts/ramsey_research.py    # extension window analysis
python research/ramsey/scripts/ramsey_circulant.py   # circulant-seeded R(5,5) search
python research/ramsey/scripts/ramsey_targeted.py    # targeted SA for R(5,5) frontier
```

The Python engine provides the same TLS-Graph operations backed by NumPy, with ~100x speedup over the browser calculator. Handles n=50+ graphs and 5-clique counting in sub-second time.

```python
from engine import *

P = paley(37)
print(ramsey_check(P, 5, 5))          # False — avoids R(5,5)
print(independence_number(P))          # 4
print(hoffman_bound(P))               # 6

# Extension analysis: can P be grown by one vertex?
ext = extend_analysis(P, 5, 5)
print(ext['valid'], '/', ext['total_patterns'])

# Full extension landscape for R(4,4)
results = extension_landscape(4, 4, 18)
print_landscape(results)
```

## Research Findings

See `docs/spectral_ramsey_findings.md` for documented research results, including:

1. **Spectral proofs of Ramsey avoidance** — O(n³) via Hoffman bound vs O(n^k) enumeration
2. **Paley threshold formula** — first R(k,k) failure at p ≈ 1.6k²
3. **Family-specific Ramsey profiles** — Paley for R(k,k), cubic residue for R(3,s)
4. **Exact independence numbers** — α/√p ≈ 0.75 for Paley graphs
5. **Paley extension trap** — no Paley graph can be extended while maintaining avoidance
6. **Extension phase transition** — window closes at ~78% of R(r,s), a structural property
7. **The extension funnel** — transition zone where extendable and non-extendable graphs coexist
8. **R(5,5) extension landscape** — window stays open dramatically longer for larger Ramsey numbers
9. **R(5,5) avoiders verified through n=41** — Paley-seeded graphs verified with adjacency matrices stored

See also `research/ramsey/docs/` for detailed methodology, the extension resistance conjecture, and R(5,5) search reports.

## Project structure

```
index.html                              Browser calculator (HTML/CSS/JS)
engine.py                               Python research engine (NumPy)
er_small_ramsey.json                    Extension resistance data (Phase 3)
docs/
  tensor_language_formal_spec.md        TLS v0.1 draft
  tensor_language_formal_spec_v0.2.md   TLS v0.2 (current, includes TLS-Graph)
  TLS_paper_draft.md                    Academic paper draft
  spectral_ramsey_findings.md           Research findings & data
research/ramsey/
  scripts/                              19 analysis & search scripts
    ramsey_research.py                  Extension window analysis
    ramsey_circulant.py                 Circulant-seeded R(5,5) search
    ramsey_targeted.py                  Targeted SA for R(5,5) frontier
    analyze_er_*.py                     Extension resistance analysis
    verify_*.py                         Graph verification tools
    break_trap*.py                      Paley trap breaking experiments
  docs/                                 Research documents
    extension_resistance_conjecture.md  ER conjecture formalization
    METHODOLOGY.md                      Research methodology
    R55_search_report.md                R(5,5) search progress
  results/                              Verified adjacency matrices (.npy, .json)
  dashboard/                            Live SA monitoring (Chart.js)
```

## TLS compliance

The calculator implements most of **TLS-Core** and **TLS-Geom**:

- Scalar promotion, tensor addition, tensor product, explicit contraction
- Variance and space tracking on all operations
- Metric declarations with raise/lower
- Symmetry detection and propagation
- Dimension well-formedness constraints

It also reaches into **TLS-Calc** territory with Christoffel symbols and Riemann curvature, and into **TLS-Graph** territory with algebraic graph constructions, Ramsey theory, and simulated annealing search.

Not yet implemented: change-of-basis transformations, LLM-guided evolutionary search.

## License

MIT
