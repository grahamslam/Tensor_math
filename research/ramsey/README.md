# Ramsey Number Research

Computational investigation of Ramsey numbers using graph theory, spectral analysis, and simulated annealing. Built on the TLS-Graph extension of the Tensor Language Specification.

## Key Results

- **R(5,5) avoiders verified** through n=42 (complete chain n=37-42)
- **Extension Resistance (ER)** formalized as a novel graph invariant
- **Extension phase transition** confirmed across R(3,3), R(3,4), R(3,5), R(4,4), R(5,5)
- **Graph 41** in McKay's dataset achieves ER=2 at n=42 (nearest miss to disproving R(5,5)=43)
- 8 spectral/structural findings documented

## Structure

```
scripts/       — Python scripts for search, analysis, and verification
results/       — Adjacency matrices (.npy), structural data (.json), graph6 files
docs/          — Research reports, conjectures, and findings
dashboard/     — Live Chart.js dashboard for SA monitoring
```

## Key Documents

- `docs/extension_resistance_conjecture.md` — ER invariant definition, 5-phase research plan, cross-Ramsey validation
- `docs/R55_search_report.md` — Full R(5,5) computational search writeup
- `docs/spectral_ramsey_findings.md` — 8 spectral/structural findings
- `results/ramseyGoogle.pdf` — AlphaEvolve reference (Nagda et al., 2026)

## Script Categories

**R(5,5) search pipeline:**
- `ramsey_circulant.py` — 3-phase: circulant search + diff-set SA + edge SA
- `ramsey_targeted.py` — incremental violation tracking + targeted flips
- `ramsey_greedy.py` — greedy descent + chained SA
- `ramsey_extend42.py` — extend n=41 avoider to n=42

**Extension Resistance analysis:**
- `analyze_extension.py` — ER computation for R(5,5,42)-graphs
- `analyze_er_correlations.py` — Phase 1: correlation analysis
- `analyze_er_regression.py` — Phase 2: multivariate regression
- `analyze_er_small_ramsey.py` — Phase 3: cross-Ramsey validation (R(3,3) through R(4,4))
- `analyze_barrier.py` — Deep trap analysis of Graph 41
- `break_trap.py` / `break_trap_multi.py` — Multi-edge trap breaking attempts

**Structural analysis:**
- `analyze_656.py` — Properties of all 656 R(5,5,42)-graphs

**Verification:**
- `verify_best.py` / `verify_once.py` / `grab_and_verify.py` — Avoider verification
