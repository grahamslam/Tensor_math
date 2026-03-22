# Related Work Map for Ramsey Research

This note maps adjacent research to the current Ramsey program in this repository, especially the work on one-vertex extension, Extension Resistance (ER), Graph 41, exact/heuristic calibration, and search methodology.

## Purpose

The goal of this note is not just to collect references. It is to connect each research direction to specific questions in this project:

- Can this help compute exact ER on small instances?
- Can this explain Graph 41-like extension barriers?
- Can this reduce duplicate search across isomorphic candidates?
- Can this improve verification, calibration, or search efficiency?
- Can this provide a stronger theoretical framing for ER-like quantities?

---

## 1. Exact extension and verification

### 1.1 One-vertex extension and counterexample checking
**Most directly relevant**

A 2024 paper, **“Ramsey Number Counterexample Checking and One Vertex Extension”**, appears to be the closest existing algorithmic neighbor to the current Extension Resistance program.

Why it matters here:
- ER asks how far a graph is from being extendable by one new vertex.
- This paper focuses directly on one-vertex extension and counterexample checking.
- It reportedly validates emptiness results for `R(4,6,36)` and `R(5,5,43)` relative to the currently known lower-order graph sets.

Potential contribution to this repo:
- Benchmark ER against exact one-vertex extension algorithms.
- Separate:
  - exact extension feasibility,
  - exact minimum violation count on smaller cases,
  - heuristic ER upper bounds on larger cases.
- Use as a calibration target for simulated annealing and local-search extension scoring.

Project questions:
- Can their extension framework be adapted to compute exact ER on smaller Ramsey instances?
- Can it certify that a graph with estimated `ER > 0` truly has positive ER?
- Can it help characterize “almost extendable” graphs more rigorously?

Reference:
- <https://arxiv.org/html/2411.04267v3>

---

### 1.2 Standard small-Ramsey data and reference surveys
**Baseline comparison literature**

Two essential background resources are:

- Brendan McKay’s Ramsey graph data page
- Stanisław Radziszowski’s survey on small Ramsey numbers

Why they matter here:
- They provide the canonical ecosystem for claims involving `R(5,5,42)` graphs.
- The 656 `R(5,5,42)` graphs are part of the standard baseline against which this project should compare any structural claims.

Potential contribution to this repo:
- External validation of the graph sets being studied.
- Standard framing for near-extremal and lower-bound claims.
- A comparison point for Graph 41 and any proposed ER-based structure classifications.

Project questions:
- Are Graph 41-like motifs already visible in known catalogs?
- Can ER be computed or estimated across standard known datasets for comparison?
- Can the repo’s claims be tied more explicitly to canonical reference sets?

References:
- <https://users.cecs.anu.edu.au/~bdm/data/ramsey.html>
- <https://www.cs.rit.edu/~spr/ElJC/eline.html>

---

## 2. Extremal structure and invariants

### 2.1 Uniquely \(K_r\)-saturated graphs
**Best conceptual analog for extension barriers**

This literature studies graphs with no \(K_r\), but where adding any missing edge creates a unique \(K_r\).

Why it matters here:
- It is not the same as ER, but it is conceptually close.
- Both settings study fragile extremality and “on the edge” forbidden-structure creation.
- This may give a vocabulary for Graph 41-like obstruction phenomena.

Potential contribution to this repo:
- A conceptual framework for “extension traps.”
- Possible analogies for classifying near-extremal graphs.
- Candidates for structural motifs that create rigid obstruction patterns.

Project questions:
- Is Graph 41 exhibiting a one-vertex analog of unique saturation behavior?
- Can ER-positive graphs be grouped into obstruction families similar to saturation classes?
- Are there minimal unsatisfiable extension cores analogous to unique saturation constraints?

Reference:
- <https://arxiv.org/pdf/1203.1084>

---

### 2.2 Supersaturation and forbidden-subgraph count theory
**Natural theoretical neighbor to ER**

Supersaturation studies how many forbidden subgraphs must appear once a graph crosses certain density or structure thresholds.

Why it matters here:
- ER is a minimum residual forbidden-count quantity after the best one-vertex extension.
- That makes ER feel like a localized or conditional supersaturation-style invariant.

Potential contribution to this repo:
- A theoretical language for interpreting ER as more than a heuristic score.
- Possible lower bounds or monotonicity principles for extension difficulty.
- Bridges between ER predictors and counts of medium-sized motifs.

Project questions:
- Can ER be bounded below using clique/independent-set supersaturation ideas?
- Do low-ER graphs occupy a sharp boundary region in motif-count space?
- Are the strongest empirical ER predictors really proxies for local supersaturation pressure?

Reference:
- <https://arxiv.org/pdf/2312.08265>

---

### 2.3 Flag algebras
**Promising for asymptotic structure, less direct for exact search**

Flag algebra methods provide asymptotic inequalities in extremal graph theory and can sometimes help classify extremal configurations.

Why it matters here:
- If ER is real and meaningful, the next step after empirical study may be proving structural constraints on low-ER graphs.
- Flag algebras may help formalize statements about densities of local substructures or motif balances.

Potential contribution to this repo:
- A possible route toward provable structural restrictions.
- A bridge from empirical motif correlations to mathematical inequalities.
- A way to move from “observed pattern” to “necessary condition.”

Project questions:
- Can flag algebra inequalities explain why certain medium-range motifs predict ER?
- Can Graph 41-like near-extremal behavior be constrained asymptotically?
- Are there density inequalities separating extendable from non-extendable regimes?

Reference:
- <https://arxiv.org/pdf/2601.12741>

---

## 3. Search acceleration and exact search methodology

### 3.1 Canonical augmentation and isomorph-free generation
**One of the best practical upgrades for this repo**

Canonical augmentation and nauty-style symmetry reduction are standard tools for avoiding duplicate exploration of isomorphic search states.

Why it matters here:
- Ramsey search is highly redundant under isomorphism.
- Extension studies can easily overcount “distinct” candidate barriers that are actually the same graph class.
- This is especially important if the repo moves toward exact enumeration, exact ER calibration, or cataloging barrier motifs.

Potential contribution to this repo:
- Reduce duplicate search effort.
- Improve exact enumeration workflows.
- Support classification of Graph 41-like barrier patterns at the isomorphism-class level.

Project questions:
- Can isomorph-free generation be integrated into the extension pipeline?
- Can near-extremal candidates be canonicalized before analysis?
- Does the Graph 41 motif appear across multiple isomorphism classes or only a tiny handful?

Reference:
- <https://arxiv.org/pdf/1706.08325>

---

### 3.2 SAT / SMT approaches for Ramsey-type search
**Strong candidate for an exact-search side stack**

Recent SAT-based Ramsey work shows that specialized SAT encodings and parallel search can improve bounds and exact checking in Ramsey-like problems.

Why it matters here:
- Extension feasibility is a constrained combinatorial decision problem.
- ER on small cases could potentially be computed exactly through satisfiability or optimization encodings.
- SAT/SMT may be a better exact baseline than brute force once the structure is encoded correctly.

Potential contribution to this repo:
- Exact extension feasibility checks.
- Exact ER computation on small instances.
- Cross-verification of heuristic search results.

Project questions:
- Can one-vertex extension be encoded as SAT or MaxSAT?
- Can exact ER be formulated as a minimization problem over extension violations?
- Would a SAT layer be a useful validation backend for the current heuristics?

Reference:
- <https://arxiv.org/pdf/2312.01159>

---

## 4. Learning-guided search

### 4.1 RamseyRL and related reinforcement-learning work
**Interesting for prioritization, lower priority than exact calibration**

RamseyRL and related work use learning-guided search or best-first strategies to discover Ramsey counterexamples or candidate extremal graphs.

Why it matters here:
- If ER becomes a central score, learned methods could help prioritize moves, perturbations, or candidate extension vectors.
- This may be useful after the exact-vs-heuristic foundations are stronger.

Potential contribution to this repo:
- Learned move selection during local search or annealing.
- ER prediction or ranking models.
- Better candidate prioritization for expensive extension analysis.

Project questions:
- Can a model predict which vertex-attachment patterns are most promising?
- Can ER upper bounds be learned well enough to guide search?
- Can RL help navigate barrier-rich landscapes like the Graph 41 neighborhood?

Reference:
- <https://arxiv.org/abs/2308.11943>

---

### 4.2 Graph neural networks for extremal / Ramsey search
**Potentially useful for ranking, not a substitute for proof**

Graph neural networks may help identify structure in candidate near-extremal graphs that is hard to capture with hand-designed features.

Why it matters here:
- The current program already studies structural predictors of ER.
- A GNN could be tested as a stronger nonlinear predictor of estimated or exact ER.

Potential contribution to this repo:
- Predictive ranking of candidate graphs.
- Feature discovery beyond triangle imbalance / motif counts.
- Search guidance for which graphs or neighborhoods to explore next.

Project questions:
- Can a GNN outperform hand-designed structural predictors for ER?
- Does it discover motifs similar to the Graph 41 barrier?
- Can it be used only for ranking while keeping all final claims exact or verifiable?

References:
- <https://arxiv.org/abs/2308.11943>
- <https://arxiv.org/html/2602.17276>

---

## 5. Recommended priority order

If the goal is to strengthen the current Ramsey research in the most direct and scientifically useful way, the priority order should be:

1. **One-vertex extension / counterexample-checking paper**
   - Closest conceptual match to ER.
   - Highest immediate value for calibration and exact extension analysis.

2. **McKay / Radziszowski baseline references**
   - Essential for framing claims about `R(5,5,42)` and near-extremal structure.

3. **Canonical augmentation / isomorph-free generation**
   - Best practical upgrade for exact or semi-exact exploration.

4. **SAT / SMT exact-search approaches**
   - Strong candidate for computing exact ER on small cases.

5. **Uniquely \(K_r\)-saturated graphs**
   - Best conceptual analog for Graph 41-like fragile barriers.

6. **Supersaturation / flag algebra directions**
   - Best theoretical path if ER is to become a rigorous invariant with provable structure.

7. **RL / GNN methods**
   - Useful for search acceleration, but less urgent than calibration, exactness, and structural understanding.

---

## 6. Suggested immediate actions for this repository

### Action A — Exact-vs-heuristic ER calibration
Use exact one-vertex extension or SAT/MaxSAT on smaller Ramsey instances to measure:
- how often heuristic ER equals exact ER,
- whether the ranking induced by estimated ER is stable,
- whether the same predictors remain important.

### Action B — Graph 41 barrier formalization
Build a dedicated note on the Graph 41 obstruction:
- local motif structure,
- conflict hypergraph,
- candidate minimal unsatisfiable cores,
- whether the pattern appears elsewhere.

### Action C — Isomorphism-aware barrier catalog
Canonicalize near-extremal graphs and extension barriers so the repo can answer:
- how many genuinely distinct barrier types exist,
- whether Graph 41 is unique or representative,
- whether ER clusters by isomorphism class or motif family.

### Action D — ER theory note
Write a theory note treating ER as a proposed invariant:
- exact definition,
- isomorphism invariance,
- monotonicity questions,
- relationship to extension feasibility,
- possible supersaturation analogies.

---

## 7. Bottom-line recommendation

The single paper to read first is:

**Ramsey Number Counterexample Checking and One Vertex Extension**  
<https://arxiv.org/html/2411.04267v3>

It appears to be the closest existing work to the project’s current Extension Resistance direction, and it is the most likely to improve both the methodology and the framing of the Ramsey folder quickly.

After that, the strongest practical upgrade is to bring in:
- canonical augmentation / symmetry reduction,
- then an exact-search or SAT-backed calibration path,
- while separately deepening the conceptual side through unique saturation and supersaturation-style theory.

This combination would give the project:
- stronger exactness,
- stronger reproducibility,
- better structural understanding,
- and a more persuasive research narrative.
