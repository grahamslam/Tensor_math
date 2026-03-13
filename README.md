# Tensor Standard Math Calculator

A self-contained tensor algebra calculator that treats every value — from plain integers to Christoffel symbols — as a typed tensor object. Built on the **Tensor Language Specification (TLS) v0.2**.

Open `index.html` in a browser. No build step, no dependencies.

## What it does

| Input | Output | What's happening |
|-------|--------|-----------------|
| `1 + 2` | `3 (scalar)` | Rank-0 tensor addition |
| `cv(1,2) @ v(3,4)` | `11 (scalar)` | Covector contracts with vector |
| `m(1,2;3,4) @ v(5,6)` | `[17, 39] (vector)` | Matrix-vector contraction |
| `m(1,2;3,4) @ m(5,6;7,8)` | `[[19,22],[43,50]]` | Matrix multiplication |
| `christoffel(g, dg)` | `{T^0_{11}=...}` | Christoffel symbols from metric |
| `riemann(g, dg, ddg)` | Riemann, Ricci, R, K | Full curvature pipeline |

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

**Differential geometry**
- `t3(a,b;c,d|e,f;g,h)` — rank-3 tensor literals (pipe-separated slabs)
- `christoffel(g, dg)` — Christoffel symbols from metric + first derivatives
- `riemann(g, dg, ddg)` — Riemann tensor, Ricci tensor, scalar curvature, Gaussian curvature (2D)

**Environment**
- REPL tab with persistent declarations: `ring`, `space`, `tensor`, `metric`
- `where` clauses for inline local bindings
- Strict and Educational evaluation modes
- Full TLS v0.2 specification embedded in the Specification tab

## Tensor literal syntax

```
42              scalar (rank 0)
v(1,2,3)        vector (rank 1, contravariant)
cv(4,5,6)       covector (rank 1, covariant)
m(1,2;3,4)      matrix (rank 2, rows separated by ;)
t3(a,b;c,d|e,f;g,h)   rank-3 tensor (slabs separated by |)
```

## GR example: unit sphere curvature

```
# Sphere at theta = pi/3
# g = diag(1, sin^2(pi/3)) = diag(1, 0.75)
# dg[theta] = [[0,0],[0,sin(2pi/3)]], dg[phi] = [[0,0],[0,0]]
# ddg[theta,theta] = [[0,0],[0,2cos(2pi/3)]] = [[0,0],[0,-1]]

christoffel(m(1,0;0,0.75), t3(0,0;0,0.866|0,0;0,0))
# => {T^0_{11}=-0.433, T^1_{01}=0.577, T^1_{10}=0.577}

riemann(m(1,0;0,0.75), t3(0,0;0,0.866|0,0;0,0), t3(0,0;0,-1|0,0;0,0|0,0;0,0|0,0;0,0))
# => R=2, K=1 (unit sphere)
```

## Project structure

```
index.html                              Single-file calculator (HTML/CSS/JS)
docs/
  tensor_language_formal_spec.md        TLS v0.1 draft
  tensor_language_formal_spec_v0.2.md   TLS v0.2 (current)
```

## TLS compliance

The calculator implements most of **TLS-Core** and **TLS-Geom**:

- Scalar promotion, tensor addition, tensor product, explicit contraction
- Variance and space tracking on all operations
- Metric declarations with raise/lower
- Symmetry detection and propagation
- Dimension well-formedness constraints

It also reaches into **TLS-Calc** territory with Christoffel symbols and Riemann curvature.

Not yet implemented: indexed notation `T[a+,b-]`, basis declarations, Einstein summation convention, covariant derivatives.

## License

MIT
