# Tensor Language Specification: A Typed Algebra Unifying Computation from Scalars to Combinatorics

**Authors:** Graham Tidwell, Claude (Anthropic)
**Date:** March 2026
**Status:** Working Draft

---

## Abstract

Mathematical computation is fragmented across tools that do not share type systems. Array libraries treat tensors as untyped multidimensional arrays without variance or space tracking. Graph libraries operate on adjacency structures disconnected from the linear algebra governing their spectral properties. Symbolic algebra systems enforce some mathematical structure but typically lack computational evaluation. This paper presents the Tensor Language Specification (TLS), a formal language in which the primitive semantic object at every level — from integer arithmetic through differential geometry to graph combinatorics — is a typed tensor. We demonstrate that this unification is not merely aesthetic: the type system catches classes of mathematical errors at parse time that existing tools permit silently, and the framework enables cross-domain reasoning that siloed tools cannot express. We introduce TLS-Graph, an extension that encodes graphs as typed rank-2 tensors and reformulates classical graph operations — clique counting, spectral analysis, Ramsey verification — as tensor contractions and decompositions. We present a working implementation in a single dependency-free file and demonstrate its application across domains from physics to combinatorics.

---

## 1. Introduction

Consider three computations from different mathematical domains:

1. A physicist computes Christoffel symbols from a metric tensor and its derivatives, contracting indices with careful variance tracking.
2. A data scientist multiplies adjacency matrices to count paths in a network, using the same matrix multiplication the physicist uses for tensor contraction.
3. A combinatorialist counts triangles in a graph by computing trace(A³)/6 — a three-fold self-contraction of the adjacency tensor.

These computations share deep mathematical structure. All three are tensor contractions. All three require attention to index semantics. All three produce results whose correctness depends on dimensional compatibility and structural constraints.

Yet no existing computational framework treats them as instances of the same typed operation.

The physicist uses Cadabra or xTensor, which understands variance but cannot count graph cliques. The data scientist uses NumPy, which multiplies matrices efficiently but silently permits `v @ v` (contracting two vectors without checking whether an inner product exists). The combinatorialist uses NetworkX, which counts triangles but has no connection to the spectral theory that bounds the independence number.

The Tensor Language Specification (TLS) addresses this fragmentation by defining a mathematical language in which the primitive semantic object is a **typed tensor**. Scalars are rank-0 tensors. Vectors carry contravariant variance over a declared space. Adjacency matrices are rank-2 tensors mapping vertices to neighborhoods. Christoffel symbols are rank-3 tensors with mixed variance. Every operation — addition, contraction, eigenvalue decomposition, clique counting — is governed by structural rules on index signatures, and violations are caught before evaluation.

### 1.1 Contributions

1. **TLS-Core**: A formal specification for typed tensor arithmetic where every value is a tensor object with tracked variance, space membership, and dimensional well-formedness (Section 2).

2. **Graduated demonstration**: A single type system governs computation from scalar addition through Einstein summation to Riemannian curvature, with each level introducing constraints that catch errors undetectable in untyped frameworks (Section 3).

3. **TLS-Graph**: An extension encoding graphs as typed rank-2 tensors with algebraic constructors, combinatorial operations, and search tools, all within the same typed algebra (Section 4).

4. **Cross-domain applications**: Demonstrations spanning physics (curvature of surfaces), network science (spectral graph analysis), and combinatorics (Ramsey theory), all expressed in a unified notation (Section 5).

5. **Implementation**: A complete, dependency-free implementation in a single HTML file (Section 6).

---

## 2. The Tensor Language Specification

### 2.1 Design Philosophy

TLS is governed by six principles:

**Tensor-first semantics.** Every value denotes a tensor object, including rank-0 scalars. There is no separate "number" type — `42` is `Tensor<>` with empty index signature.

**Typed indices.** Every tensor index belongs to a declared space and carries declared variance (contravariant `+` or covariant `-`). This is not metadata; it is part of the tensor's type.

**Structure before representation.** A tensor is not identical to its component array. Components are one representation under a chosen basis. The tensor's identity is its type signature plus transformation law.

**Explicit interaction.** Contraction must be explicit unless a declared operator introduces a standard contraction rule. The `@` operator performs canonical contraction; all other contractions require the `contract()` function with specified index labels.

**Validity by type.** An expression is well-formed only if all tensor operations satisfy index, space, and variance constraints. This is checked structurally, not at runtime.

**Extra structure is never implicit.** Metrics, connections, and symmetries must be declared before use. There is no default inner product.

### 2.2 Index Signatures

A tensor's type is determined by its **index signature**: an ordered list of typed index slots, each containing:

- **Label**: a symbolic identifier (e.g., `a`, `mu`)
- **Space**: a declared vector space (e.g., `V`, `W`)
- **Variance**: contravariant (`+`) or covariant (`-`)
- **Role**: free or bound (determined by context)

Examples:
- Scalar: `Tensor<>` (empty signature)
- Vector in V: `Tensor<V+>` (one contravariant slot)
- Covector in V: `Tensor<V->` (one covariant slot)
- Linear map: `Tensor<V+, V->` (one up, one down)
- Metric: `Tensor<V-, V-> {sym(1,2)}` (symmetric covariant)
- Christoffel: `Tensor<V+, V-, V->` (mixed rank-3)

### 2.3 Contraction Rules

Contraction — the operation that generalizes dot products, matrix multiplication, and trace — requires:

1. Exactly two slots are identified for contraction.
2. The slots have **opposite variance** (one `+`, one `-`).
3. The slots belong to **compatible spaces**.
4. The dimension of the space is consistent across both tensors.

When these conditions are met, the contraction sums over the shared index and produces a tensor with rank reduced by 2. When they are not met, the system raises a structural error.

This is the core safety guarantee. In NumPy, `np.dot(v, v)` silently computes an inner product without checking whether an inner product is mathematically meaningful on the space in question. In TLS, `v @ v` where both are `Tensor<V+>` is rejected: two contravariant vectors cannot contract without a metric to lower one index.

### 2.4 Dimensional Well-formedness

Dimension is a property of **spaces**, not of individual tensors:

> If space `V` has been declared with `dim n`, then every tensor with an index slot over `V` must have exactly `n` components along that axis.

This catches errors that shape-checking alone misses: two 3-component vectors over different spaces `V` and `W` may not be added, even though their shapes match.

### 2.5 Symmetry Tracking

Tensors may carry symmetry constraints:
- `sym(i, j)`: components are invariant under exchange of slots `i` and `j`
- `antisym(i, j)`: components change sign under exchange

Symmetry propagates through operations: the sum of two symmetric tensors is symmetric; the contraction of a symmetric tensor with an antisymmetric one is zero. TLS tracks and propagates these properties automatically.

---

## 3. Graduated Examples

We demonstrate the type system at increasing complexity, showing at each level what TLS catches that untyped systems do not.

### 3.1 Arithmetic as Rank-0 Tensor Algebra

```
1 + 2
=> 3 (scalar)
```

The result is `Tensor<>` — a rank-0 tensor. This is not special-cased; it falls out of the general tensor addition rule (same rank, same spaces, same variances). Students see arithmetic as the simplest case of tensor algebra, not a separate system.

### 3.2 Linear Algebra with Variance

```
cv(1,2) @ v(3,4)
=> 11 (scalar)
```

A covector `Tensor<V->` contracts with a vector `Tensor<V+>`. Opposite variances, compatible spaces — yields a scalar. This is the mathematically correct evaluation: a linear functional applied to a vector.

```
v(1,2) @ v(3,4)
=> TYPE ERROR: Cannot contract — both slots are contravariant (+).
```

NumPy computes `np.dot([1,2], [3,4]) = 11` without complaint. But two vectors in a space without a declared metric have no canonical inner product. TLS makes the distinction explicit. With a metric: `lower(v1, g) @ v2` — the metric produces a covector, which contracts validly.

### 3.3 Einstein Summation

```
einsum('a+b-, b+c- -> a+c-', A, B)
=> [[19,22],[43,50]]
```

The `b+` and `b-` contract (matching labels, opposite variance). The `a+` and `c-` are free. TLS validates rank match, variance compatibility, and dimension agreement — constraints that NumPy's `np.einsum('ij,jk->ik', A, B)` does not enforce.

### 3.4 Differential Geometry

```
christoffel(m(1,0;0,0.75), t3(0,0;0,0.866|0,0;0,0))
=> {Γ^0_{11}=-0.433, Γ^1_{01}=0.577, Γ^1_{10}=0.577}

riemann(g, dg, ddg)
=> R=2, K=1 (unit sphere)
```

Christoffel symbols Γ^λ_{μν} are rank-3 tensors with typed variance `Tensor<V+, V-, V->`. The Riemann tensor, Ricci tensor, and scalar curvature are derived through validated contractions — each step checked for correct index pairing.

```
covariantD(0, revar(g, '--'), christoffel(g, dg), revar(dg_0, '--'))
=> [[0, 0], [0, 0]]    (metric compatibility: ∇g = 0)
```

The `revar` function marks the metric as covariant without changing components, ensuring Christoffel corrections target the right variance pattern. The zero result confirms metric compatibility — a fundamental identity of Riemannian geometry, verified computationally.

### 3.5 The Type Safety Progression

| Level | New constraint | Error caught |
|-------|---------------|-------------|
| Scalars | Ring compatibility | Adding incompatible quantities |
| Vectors | Variance tracking | Contracting two vectors without a metric |
| Indexed | Label matching | Summing over wrong index pairs |
| Geometry | Connection structure | Missing Christoffel corrections |

The same type system governs all four levels. Tensors are not a data structure for multidimensional arrays — they are a type system for mathematical computation.

---

## 4. TLS-Graph: Graphs as Typed Tensors

### 4.1 The Natural Encoding

An undirected graph on n vertices has a natural representation as a rank-2 tensor: its adjacency matrix A ∈ `Tensor<V+, V->`. This is not merely convenient. The adjacency matrix is a **linear map** on the vertex space: A sends each vertex to its neighborhood. The tensor type `Tensor<V+, V->` is precisely the type of a linear endomorphism.

Standard tensor operations acquire graph-theoretic meaning:

| Tensor operation | Expression | Graph interpretation |
|-----------------|------------|---------------------|
| Contraction | `A @ A` | Path counting: (A²)_{ij} = paths of length 2 from i to j |
| Trace | `trace(A @ A @ A) / 6` | Triangle count via closed walks |
| Eigenvalues | `eigenvalues(A)` | Graph spectrum; spectral gap determines expansion |
| Complement | `complement(A)` | Edge-color inversion for 2-coloring analysis |
| Hadamard product | `hadamard(A, B)` | Subgraph intersection; edge filtering |
| Degree sequence | `degree(A)` | Row contraction → vector of vertex degrees |

These identities are not analogies. They are direct consequences of the tensor contraction rules.

### 4.2 Algebraic Graph Constructors

TLS-Graph provides first-class constructors for structured graph families:

**Complete graphs:**
```
adjacency(n)    # K_n as rank-2 tensor
```

**Paley graphs:**
```
paley(p)        # p prime, p ≡ 1 (mod 4)
```
Vertices are Z_p; edge (u,v) exists iff u-v is a quadratic residue mod p. Self-complementary and vertex-transitive — properties that follow from number-theoretic structure and are preserved through tensor operations.

**Circulant graphs:**
```
circulant(n, v(d1, d2, ...))    # edges by difference set mod n
```
Edge (u,v) exists iff |u-v| mod n is in the difference set S. Inherits cyclic symmetry of Z_n. The automorphism group includes all cyclic rotations, reducing the effective search space from 2^(n choose 2) to 2^(n/2) when searching within the circulant family.

### 4.3 Combinatorial Operations

| Operation | Preconditions | Returns |
|-----------|---------------|---------|
| `cliques(A, k)` | Rank-2 tensor, scalar k | Count of complete k-subgraphs |
| `independent_set(A, k)` | Rank-2 tensor, scalar k | Count of k-independent-sets |
| `triangles(A)` | Rank-2 tensor | Triangle count via trace(A³)/6 |
| `chromatic(A)` | Rank-2 binary tensor | Edge counts by color class |
| `ramsey_check(A, s, t)` | Rank-2 binary tensor, scalars | Monochromatic clique detection |
| `ramsey_energy(A, r, s)` | Rank-2 binary tensor, scalars | E = count(K_r) + count(I_s) |
| `ramsey_anneal(n, r, s)` | Scalars | Simulated annealing search |

Each operation is typed — `cliques(v(1,2,3), 2)` is rejected because you cannot count cliques in a vector.

---

## 5. Cross-Domain Applications

### 5.1 Physics: Curvature of Surfaces

The Gaussian curvature of the unit sphere at θ = π/3:

```
let g = m(1,0;0,0.75)
let dg = t3(0,0;0,0.866|0,0;0,0)
let ddg = t3(0,0;0,-1|0,0;0,0|0,0;0,0|0,0;0,0)

christoffel(g, dg)
=> {Γ^0_{11}=-0.433, Γ^1_{01}=0.577, Γ^1_{10}=0.577}

riemann(g, dg, ddg)
=> R=2, K=1
```

The scalar curvature R=2 and Gaussian curvature K=1 confirm the unit sphere has constant positive curvature. The computation requires typed index tracking: the Ricci contraction R_{μν} = R^λ_{μλν} contracts the first and third indices of the Riemann tensor — and TLS validates that these have opposite variance.

### 5.2 Network Science: Spectral Graph Analysis

The spectrum of a graph reveals structural properties invisible to purely combinatorial analysis:

```
let K = adjacency(6)
eigenvalues(K)          # [5, -1, -1, -1, -1, -1]
trace(K @ K)            # 30 = sum of squared eigenvalues
```

The complete graph K_6 has eigenvalue 5 (multiplicity 1) and eigenvalue -1 (multiplicity 5). The spectral gap λ_1 - λ_2 = 6 indicates perfect expansion — every vertex connects to every other.

For the Petersen graph (a 3-regular graph on 10 vertices):
```
let P = circulant(5, v(1,2))  # approximation via circulant
degree(P)                      # degree sequence
trace(P @ P @ P) / 6          # triangle count
```

The Hoffman bound constrains the independence number using the spectral gap:

α(G) ≤ n · (-λ_min) / (λ_max - λ_min)

This bound is computable entirely through tensor operations: `eigenvalues(A)` gives the spectrum, and the bound follows from scalar arithmetic on the extremal eigenvalues.

### 5.3 Combinatorics: Algebraic Ramsey Constructions

Paley graphs provide a bridge between number theory and extremal graph theory:

```
let P = paley(13)
cliques(P, 3)                  # 26 triangles
cliques(P, 4)                  # 0 four-cliques
independent_set(P, 4)          # 0 four-independent-sets
chromatic(P)                   # red=39, blue=39 (self-complementary)
ramsey_check(P, 4, 4)          # false — avoids R(4,4)!
```

Paley(13) avoids R(4,4) because it has no 4-cliques and — by self-complementarity — no 4-independent-sets. The balanced edge distribution (39 red, 39 blue) is a structural consequence of the quadratic residue construction. This analysis, expressed as a sequence of typed tensor operations, reveals *why* the construction works: the number-theoretic structure of quadratic residues modulo a prime forces a balanced, clique-free graph.

Circulant constructions offer a complementary approach:

```
# Circulant graph on 8 vertices with difference set {1,4}
let C = circulant(8, v(1,4))
ramsey_check(C, 3, 4)           # check for R(3,4) avoidance
ramsey_energy(C, 3, 4)          # energy: how close to avoiding?
```

### 5.4 Combinatorial Search

For cases where algebraic constructions are insufficient, TLS-Graph provides stochastic search:

```
# Simulated annealing: minimize E = count(K_3) + count(I_4) on K_8
ramsey_anneal(8, 3, 4)
=> 8x8 adjacency matrix (E=0, R(3,4)-avoiding)
```

The annealing search uses the Metropolis criterion with geometric cooling, randomly flipping edges and accepting moves that reduce the Ramsey energy. Since R(3,4) = 9, an avoiding coloring of K_8 exists and the search typically finds one within a few trials.

```
# R(3,3) = 6: verify the classical result
ramsey_anneal(5, 3, 3)   # E=0 found (avoiding coloring exists)
ramsey_anneal(6, 3, 3)   # best E > 0 (no avoiding coloring — R(3,3)=6)
```

This computational approach mirrors the methods used in recent work on Ramsey lower bounds (Exoo and Tatarevic, 2015; Nagda et al., 2026), where simulated annealing initialized from algebraic graphs has been the dominant technique. TLS-Graph provides the same primitives — Paley seeding, circulant construction, energy computation, SA search — within a typed framework that ensures mathematical validity of the operations.

### 5.5 The Unifying Thread

These three applications — physics, networks, combinatorics — share no domain-specific code. They use the same tensor operations:

| Operation | Physics use | Network use | Combinatorics use |
|-----------|------------|-------------|-------------------|
| Contraction `@` | Index lowering | Path counting | Walk enumeration |
| `trace` | Scalar curvature | Degree sum | Triangle counting |
| `eigenvalues` | Stability analysis | Spectral gap | Hoffman bound |
| `det` | Volume element | Laplacian | Characteristic polynomial |
| `complement` | — | Bipartite check | Ramsey coloring |

The type system governs all of them. A variance error in a Christoffel computation is caught by the same rule that prevents contracting two graph adjacency matrices with incompatible vertex spaces.

---

## 6. Implementation

TLS is implemented as a self-contained calculator in a single HTML file (~5000 lines of JavaScript). The implementation includes:

- **Lexer**: tokenizes TLS expressions with tensor literals, indexed notation, and string-based einsum equations
- **Parser**: recursive descent producing an AST with `where` clauses, indexed forms, and multi-argument functions
- **Type checker**: validates index signatures, variance compatibility, space membership, and dimensional well-formedness at parse time
- **Evaluator**: computes tensor operations with full variance and symmetry tracking
- **REPL**: persistent declarations for rings, spaces, tensors, metrics, and bases

The implementation has no external dependencies. It runs in any modern browser without a build step, server, or package installation. The full TLS v0.2 specification is embedded in the implementation's Specification tab.

### 6.1 Performance

The calculator evaluates expressions in JavaScript with no GPU acceleration. Practical limits:

| Operation | Limit | Bottleneck |
|-----------|-------|-----------|
| Graph construction | n ≤ 50 vertices | Memory (n² matrix) |
| Clique counting | k ≤ 10, n ≤ 25 | Exhaustive enumeration O(n^k) |
| Simulated annealing | n ≤ 30 | Energy evaluation per step |
| Eigenvalues | n ≤ 10 | Characteristic polynomial |
| Differential geometry | dim ≤ 4 | Riemann tensor computation |

These limits are acceptable for exploration, verification, and education. A compiled implementation with GPU acceleration would remove them while preserving the type system.

---

## 7. Related Work

### 7.1 Tensor Computation

NumPy (Harris et al., 2020) and JAX (Bradbury et al., 2018) provide efficient array operations but treat tensors as untyped multidimensional arrays. TensorFlow and PyTorch optimize for neural networks rather than mathematical type safety. None track variance, space membership, or symmetry.

### 7.2 Computer Algebra

Cadabra (Peeters, 2007) provides tensor algebra for field theory with full index handling but operates symbolically. xAct/xTensor (Martin-Garcia, 2008) offers comprehensive tensor calculus within Mathematica. SageMath provides broad mathematical computation but treats tensors as secondary objects. None extend to graph combinatorics.

### 7.3 Formal Verification

Lean's Mathlib (The Mathlib Community, 2020) proves theorems about tensors but does not compute with them. The type-theoretic approach is philosophically aligned with TLS but operates at a different abstraction level.

### 7.4 Graph Computation

NetworkX (Hagberg et al., 2008) and igraph provide graph algorithms with no tensor connection. Neither links graph structure to the spectral theory governing expansion and independence numbers.

### 7.5 Computational Combinatorics

SAT solvers have been used to prove R(4,5) = 25 (Gauthier and Brown, 2024). Exoo and Tatarevic (2015) established many Ramsey lower bounds using simulated annealing on algebraic graphs. Nagda et al. (2026) used LLM-evolved search to improve five Ramsey bounds. Wagner (2021) used neural networks to find combinatorial counterexamples. These works develop search algorithms; TLS provides the typed algebraic framework in which such algorithms' operations can be expressed and verified.

### 7.6 Positioning

To our knowledge, no existing system unifies scalar arithmetic, differential geometry, and graph combinatorics under a single typed tensor algebra with formal variance and space tracking.

---

## 8. Discussion

### 8.1 What TLS Achieves

**Tensor typing is practical.** The full specification is implementable in ~5000 lines with no dependencies. Type checking adds negligible overhead and catches real mathematical errors.

**Unification is productive.** The same `trace` that computes scalar curvature from the Ricci tensor counts triangles in a graph. The same contraction rule that validates Christoffel corrections validates matrix power computations for path counting. This reflects the mathematical fact that these operations are all instances of tensor contraction — and TLS makes that fact computationally explicit.

**Cross-domain reasoning is enabled.** The Hoffman bound for independence number is naturally a constraint on adjacency tensor eigenvalues. Paley graph self-complementarity is a tensor decomposition identity. Ramsey energy is a combinatorial tensor norm. These connections exist in mathematics; TLS makes them computable in a single framework.

### 8.2 What TLS Does Not Achieve

TLS is not a replacement for high-performance numerical computing. Its JavaScript implementation cannot compete with BLAS-backed matrix multiplication or distributed search algorithms.

TLS does not discover new mathematics. It provides a framework for expressing, verifying, and exploring known mathematics with type safety.

TLS does not prove theorems. Unlike Lean, TLS does not produce machine-checkable proofs. It computes results and checks types, but does not verify that results hold universally.

---

## 9. Future Work

**TLS-Calc.** The specification reserves syntax for tensor fields over manifolds, covariant differentiation, and Lie derivatives. Implementation would enable geodesic computation and curvature flows within the same typed framework.

**Change-of-basis.** TLS declares bases but does not implement basis change. Adding this would complete the "structure before representation" principle.

**Proof assistant integration.** Connecting TLS to Lean would allow computed results to be lifted into machine-checkable proofs — for example, translating a `ramsey_check` computation into a formal proof that a specific coloring is Ramsey-avoiding.

**GPU-accelerated evaluation.** WebGPU or CUDA backends would enable large-scale graph operations and parallel simulated annealing, extending TLS from exploration to frontier computation.

**Broader graph families.** Cayley graphs, Kneser graphs, and random regular graphs are all expressible as typed tensors. Adding constructors for these families would expand TLS-Graph's utility for extremal combinatorics.

---

## 10. Conclusion

The Tensor Language Specification demonstrates that a single typed algebra can govern mathematical computation from integer addition through Riemannian curvature to graph combinatorics. The key insight is that tensors are not merely a data structure for multidimensional arrays — they are a **type system** for mathematical computation, with variance, space membership, and dimensional well-formedness as structural constraints.

TLS-Graph extends this framework to graph theory by recognizing that adjacency matrices are typed rank-2 tensors whose contraction, spectral decomposition, and complement operations have precise graph-theoretic interpretations. The same type system that prevents a physicist from contracting two vectors without a metric prevents a combinatorialist from computing cliques on a non-square tensor.

We do not claim that TLS will replace domain-specific tools. We claim that it provides the right abstraction for understanding what those tools share — and that recognizing mathematical operations as typed tensor operations catches errors, enables cross-domain reasoning, and reveals structural connections that siloed tools obscure.

Every value is a tensor. Every operation is typed. Everything follows from that.

---

## References

Bradbury, J., et al. (2018). JAX: Composable transformations of Python+NumPy programs.

Exoo, G. and Tatarevic, M. (2015). New lower bounds for 28 classical Ramsey numbers. *arXiv:1504.02403*.

Gauthier, T. and Brown, C. E. (2024). A formal proof of R(4,5) = 25. *arXiv:2404.01761*.

Hagberg, A., Swart, P., and Chult, D. (2008). Exploring network structure, dynamics, and function using NetworkX.

Harris, C. R., et al. (2020). Array programming with NumPy. *Nature*, 585, 357-362.

Martin-Garcia, J. M. (2008). xAct: Efficient tensor computer algebra for Mathematica.

Nagda, A., Raghavan, P., and Thakurta, A. (2026). Reinforced generation of combinatorial structures: Ramsey numbers. *arXiv:2603.09172*.

Novikov, A., et al. (2025). AlphaEvolve: A coding agent for scientific and algorithmic discovery. *arXiv:2506.13131*.

Peeters, K. (2007). Cadabra: A field-theory motivated approach to computer algebra. *Computer Physics Communications*, 176(8), 550-558.

Radziszowski, S. (2024). Small Ramsey numbers. *The Electronic Journal of Combinatorics*, DS1.

The Mathlib Community. (2020). The Lean mathematical library. *CPP 2020*.

Wagner, A. Z. (2021). Constructions in combinatorics via neural networks. *arXiv:2104.14516*.
