# Tensor Language Specification (TLS)

## Version

**TLS 0.2**

## Status

Formal specification for a tensor-native symbolic mathematics language.

---

## Changelog from TLS 0.1

| # | Change | Sections affected |
|---|--------|-------------------|
| 1 | `@` operator restricted to three canonical contraction forms; all others require `contract(...)` | 7.3, 6.7, 11.6 |
| 2 | Dimension well-formedness rule: dimension lives on the space, tensors must conform | 6.11 (new) |
| 3 | `field` keyword renamed to `ring`; `field` reserved for tensor fields in TLS-Calc | 4.2, 5.1, all examples |
| 4 | Tensor field roadmap section added for TLS-Calc with reserved syntax | 16 (new) |
| 5 | Symmetry propagation rules: addition, product, contraction | 6.12 (new) |
| 6 | Negation and subtraction defined as syntactic sugar | 6.13 (new), 7.9-7.10 (new), EBNF |
| 7 | `where` clause defined as local scoped declarations | 5.7 (new), EBNF |
| 8 | Standard library expanded with `det`, `inv`, `norm`, `eigenvalues` (guarded) | 13 |
| 9 | Statement delimiters defined: newline-terminated, optional `;` | EBNF |
| 10 | Conformance test section added with normative expected outputs | 15 (new) |

---

## 1. Purpose

Tensor Language Specification (TLS) defines a mathematical language in which the primitive semantic object is a **typed tensor**. Scalars, vectors, covectors, matrices, linear maps, and higher-order multilinear objects are all treated as specializations of tensor objects rather than separate foundational categories.

TLS is designed to support:

- symbolic tensor manipulation
- tensor-safe arithmetic
- explicit type checking
- basis-aware and basis-independent reasoning
- conversion of ordinary arithmetic into tensor-standard form
- extensibility toward calculus, geometry, and physics

---

## 2. Design Principles

### 2.1 Tensor-First Semantics
Every value denotes a tensor object, including rank-0 values.

### 2.2 Typed Indices
Every tensor index belongs to a declared space and carries declared variance.

### 2.3 Structure Before Representation
A tensor is not identical to its component array. Components are one representation of a tensor under a chosen basis.

### 2.4 Explicit Interaction
Tensor contraction must be explicit unless a declared operator introduces a standard contraction rule.

### 2.5 Validity by Type
An expression is well-formed only if all tensor operations satisfy index, space, and variance constraints.

### 2.6 Extra Structure Is Never Implicit
Metrics, symplectic forms, orientations, volume forms, and connections must be declared before they are used.

---

## 3. Core Semantic Model

### 3.1 Primitive Semantic Object
A tensor object is defined as:

- an ordered index signature
- a value domain
- a transformation law
- optional symmetry constraints
- optional representation data

### 3.2 Index Signature
An index signature is an ordered list of typed index slots.

Each index slot contains:

- **label**: symbolic identifier
- **space**: declared space name
- **variance**: contravariant (`+`) or covariant (`-`)
- **role**: free or bound

### 3.3 Tensor Type
A tensor type is determined by:

- coefficient ring
- ordered list of spaces
- ordered list of variances
- symmetry annotations
- optional declared interpretation

Examples:

- scalar: `Tensor<>`
- vector in `V`: `Tensor<V+>`
- covector in `V`: `Tensor<V->`
- mixed rank-2 tensor: `Tensor<V+,V->`
- symmetric rank-2 covariant tensor on `V`: `Tensor<V-,V->{sym(1,2)}`

### 3.4 Scalars
A scalar is a tensor of rank 0 with empty index signature.

### 3.5 Rank
The rank of a tensor is the number of free index slots in its type.

### 3.6 Equality
Two tensor expressions are type-equal only if they share the same tensor type.
Two tensors are semantically equal only if they denote the same tensor object under the declared structure.

---

## 4. Lexical Elements

### 4.1 Identifiers
Identifiers SHALL begin with a letter or underscore and MAY contain letters, digits, and underscores.

Examples:

- `T`
- `g`
- `velocity`
- `_tmp1`

### 4.2 Reserved Keywords
The following keywords are reserved:

- `ring`
- `space`
- `tensor`
- `metric`
- `connection`
- `sym`
- `antisym`
- `let`
- `type`
- `contract`
- `raise`
- `lower`
- `basis`
- `invariant`
- `where`
- `assert`
- `det`
- `inv`
- `norm`
- `eigenvalues`

The following keywords are reserved for future use and SHALL NOT be used as identifiers:

- `field` (reserved for tensor fields in TLS-Calc)
- `manifold`
- `bundle`
- `tensorfield`

### 4.3 Literals
TLS 0.2 supports the following literal classes:

- integer literals
- decimal literals
- vector literals
- covector literals
- matrix literals
- tensor constructor literals

Examples:

- `1`
- `2.5`
- `v(1,2,3)`
- `cv(4,5,6)`
- `m(1,2;3,4)`

### 4.4 Comments
Line comments begin with `#`.

---

## 5. Syntactic Forms

### 5.1 Declarations

#### Ring Declaration
```tls
ring R
```

Declares a coefficient ring. All spaces and tensors inherit their scalar domain from a declared ring.

#### Space Declaration
```tls
space V over R dim 3
space W over R dim 2
```

The `dim` clause declares the finite dimension of the space. Dimension is a property of the space, not of individual tensor types. See Section 6.11 for the well-formedness rule this induces.

#### Tensor Declaration
```tls
tensor T : Tensor<V+,V->
tensor g : Tensor<V-,V-> {sym(1,2)}
```

#### Metric Declaration
```tls
metric g : Tensor<V-,V-> {sym(1,2), nondegenerate}
```

#### Connection Declaration
```tls
connection nabla on V compatible g
```

### 5.2 Binding
```tls
let x = 3
let v = v(1,2,3)
let A = m(1,2;3,4)
```

### 5.3 Type Alias
```tls
type EndV = Tensor<V+,V->
```

### 5.4 Indexed Form
Indexed notation is a core syntax.

```tls
T[a+, b-]
g[a-, b-]
v[a+]
omega[a-]
```

Interpretation rules:

- index labels are symbolic placeholders
- `+` denotes contravariant slot
- `-` denotes covariant slot
- labels with identical names MAY become eligible for contraction when one is upper and one is lower in a compatible context

### 5.5 Grouping
```tls
(T[a+, b-] * v[c+])
```

### 5.6 Function-Style Tensor Operators
```tls
contract(T[a+, b-], v[b+])
raise(omega[a-], g)
lower(v[a+], g)
sym(T[a-, b-])
antisym(F[a-, b-])
det(A)
inv(A)
```

### 5.7 Where Clause

The `where` keyword introduces a local declaration scope attached to a single expression or statement. Bindings introduced by `where` exist only for the evaluation of the attached expression.

Syntax:

```tls
<expression> where
  <declaration>
  <declaration>
  ...
```

Example:

```tls
contract(T[a+, b-], v[b+]) where
  space V over R dim 3
  tensor T : Tensor<V+, V->
  tensor v : Tensor<V+>
```

Semantics:

- `where` introduces a temporary typing environment.
- All declarations within the `where` block are visible only to the attached expression.
- Inner declarations shadow outer declarations of the same name.
- `where` blocks MAY be nested.
- A `where` block SHALL NOT contain statements (e.g., `let` bindings that persist beyond the expression are not permitted; use `let` inside `where` only as local temporaries).

---

## 6. Type System

### 6.1 Type Components
Each type contains:

- scalar domain (the declared ring)
- ordered slots
- slot variances
- slot spaces
- optional symmetry markers
- optional structure dependencies

### 6.2 Type Judgment
A judgment has the form:

```tls
Gamma |- expr : Type
```

where `Gamma` is the typing environment.

### 6.3 Scalar Promotion
Numeric literals SHALL be promoted to rank-0 tensor type over the current default ring.

Example:

```tls
1 : Tensor<>
```

### 6.4 Addition Rule
Addition is valid iff both operands have identical tensor type (same ring, same slots, same variances, same spaces).

```
Gamma |- A : X
Gamma |- B : X
-----------------
Gamma |- A + B : X
```

See Section 6.12 for symmetry propagation under addition.

### 6.5 Tensor Product Rule
If `A` and `B` are tensors, then `A * B` denotes tensor product unless one operand is scalar.

```
Gamma |- A : Tensor<S1...Sn>
Gamma |- B : Tensor<T1...Tm>
---------------------------------
Gamma |- A * B : Tensor<S1...Sn,T1...Tm>
```

If either side is rank-0, multiplication denotes scalar scaling.

See Section 6.12 for symmetry propagation under tensor product.

### 6.6 Contraction Rule
Contraction is valid only when:

- one slot is contravariant
- one slot is covariant
- both belong to compatible spaces
- contraction does not violate declared symmetry structure

```
Gamma |- T : Tensor<...,V+,...,V-,...>
--------------------------------------
Gamma |- contract(T, i, j) : Tensor<...remaining slots...>
```

See Section 6.12 for symmetry propagation under contraction.

### 6.7 Canonical Contraction via `@`

The `@` operator is legal ONLY for the following canonical contraction forms:

**Form 1: Covector @ Vector -> Scalar**
```
Gamma |- omega : Tensor<V->
Gamma |- v : Tensor<V+>
----------------------------
Gamma |- omega @ v : Tensor<>
```

**Form 2: Rank-2 Mixed Tensor @ Vector -> Vector**
```
Gamma |- T : Tensor<V+, V->
Gamma |- v : Tensor<V+>
-----------------------------
Gamma |- T @ v : Tensor<V+>
```

The contraction pairs the rightmost covariant slot of `T` with the contravariant slot of `v`.

**Form 3: Covector @ Rank-2 Mixed Tensor -> Covector**
```
Gamma |- omega : Tensor<V->
Gamma |- T : Tensor<V+, V->
------------------------------
Gamma |- omega @ T : Tensor<V->
```

The contraction pairs the covariant slot of `omega` with the leftmost contravariant slot of `T`.

**All other uses of `@` SHALL raise an AmbiguityError.** In particular:

- rank-2 @ rank-2 is NOT permitted via `@`
- rank-3 or higher tensors are NOT permitted with `@`
- same-variance pairings are NOT permitted with `@`

These cases MUST use `contract(...)` with explicit slot specification.

### 6.8 Indexed Contraction Rule
If repeated index labels appear in a valid expression with opposite variance and matching space, an implementation MAY permit explicit indexed contraction under a strict mode flag.

Example:

```tls
T[a+, b-] * v[b+]
```

In strict TLS 0.2, this SHOULD remain non-contracted unless wrapped by `contract(...)`.

### 6.9 Raising and Lowering
Raising and lowering are valid only when a compatible nondegenerate bilinear form is declared.

```
Gamma |- g : Tensor<V-,V->
Gamma |- v : Tensor<V+>
------------------------
Gamma |- lower(v,g) : Tensor<V->
```

```
Gamma |- g : Tensor<V-,V-> {nondegenerate}
Gamma |- omega : Tensor<V->
---------------------------------------------
Gamma |- raise(omega,g) : Tensor<V+>
```

### 6.10 Symmetrization and Antisymmetrization
```
Gamma |- T : Tensor<slots>
--------------------------
Gamma |- sym(T, i, j) : Tensor<slots>{sym(i,j)}
```

```
Gamma |- T : Tensor<slots>
--------------------------
Gamma |- antisym(T, i, j) : Tensor<slots>{antisym(i,j)}
```

### 6.11 Dimension Well-Formedness

**Rule.** For any tensor with slots over declared finite-dimensional spaces, each represented axis MUST conform to the declared dimension of its corresponding space.

Formally: if `space V over R dim n` is declared, then any concrete value assigned to a tensor type containing slot `V+` or `V-` MUST have exactly `n` components along that axis.

This rule catches:

- **Component count mismatch**: `v(1,2)` assigned to `Tensor<V+>` where `space V over R dim 3` is a well-formedness violation.
- **Matrix shape mismatch**: `m(1,2,3;4,5,6)` assigned to `Tensor<V+,V->` where `space V over R dim 3` requires a 3x3 matrix, not 2x3.
- **Cross-space shape mismatch**: `m(1,2;3,4)` assigned to `Tensor<V+,W->` requires the row count to match `dim V` and the column count to match `dim W`.
- **Contraction shape consistency**: any contraction between slots over the same space is guaranteed to be dimensionally consistent because both slots inherit the same dimension from the space declaration.

Dimension is a property of the space, not of the tensor type. The tensor type `Tensor<V+>` does not carry an independent dimension annotation; it derives its concrete dimension from the declaration of `V`.

Implementations SHALL raise a TypeError or SpaceError when a concrete tensor value violates the dimension well-formedness rule.

### 6.12 Symmetry Propagation Rules

This section defines how symmetry annotations propagate through tensor operations. Unless stated otherwise, symmetry annotations refer to slot-pair symmetry markers of the form `{sym(i,j)}` or `{antisym(i,j)}`.

#### 6.12.1 Addition

- If both operands carry identical symmetry annotations, the result carries those same annotations.
  ```
  sym{S} + sym{S} -> sym{S}
  antisym{S} + antisym{S} -> antisym{S}
  ```
- If operands carry different symmetry annotations (including one symmetric and one antisymmetric, or different slot groupings):
  - **Strict mode**: the addition SHALL be rejected as a SymmetryError.
  - **Relaxed mode**: the result is downgraded to an unspecialized tensor (all symmetry annotations are dropped).
- Implementations MUST document which mode they use. TLS-Core conformance requires at least relaxed mode.

#### 6.12.2 Tensor Product

Tensor product does NOT automatically preserve whole-object symmetry.

If `A : Tensor<V-,V->{sym(1,2)}` and `B : Tensor<W->`, then `A * B : Tensor<V-,V-,W->`. The symmetry annotation `{sym(1,2)}` MAY be preserved on the first two slots of the result if the implementation tracks per-slot-group symmetry. Whole-object symmetry of the product is NOT implied.

Implementations that track slot-group symmetry SHOULD propagate compatible sub-annotations. Implementations that do not track slot-group symmetry SHALL drop all symmetry annotations on tensor product results.

#### 6.12.3 Contraction

When a contraction eliminates two slots, the symmetry of the result MUST be recomputed based on the surviving slots.

- If the contracted slots are not involved in any symmetry annotation, surviving annotations are preserved with adjusted slot indices.
- If a contracted slot participates in a symmetry annotation, that annotation is destroyed.
- Contraction MAY induce new symmetry in the result (e.g., contracting a pair of slots from a tensor with higher symmetry). However, implementations are NOT required to detect induced symmetry; they MAY conservatively drop annotations.

**Note.** Contraction can preserve, destroy, or induce symmetry. A fully general symmetry inference engine is outside the scope of TLS-Core but MAY be provided by implementations.

#### 6.12.4 Scalar Multiplication

Scalar multiplication preserves all symmetry annotations:
```
s * T{annotations} -> (s*T){annotations}
```

#### 6.12.5 Raising and Lowering

Raising or lowering a slot changes its variance. Symmetry annotations involving that slot MUST be re-evaluated. If a symmetric pair `{sym(i,j)}` has one slot raised, the annotation is destroyed because the two slots now have different variance and occupy different spaces (V+ vs V-).

### 6.13 Negation and Subtraction

#### 6.13.1 Unary Negation

Unary negation is defined as scalar multiplication by the additive inverse of the ring identity:

```
-T  ===  (-1) * T
```

The result type of `-T` is identical to the type of `T`, including all symmetry annotations.

#### 6.13.2 Binary Subtraction

Binary subtraction is syntactic sugar:

```
A - B  ===  A + (-1) * B
```

Subtraction is lowered to addition and scalar multiplication during parsing. All type-checking rules for addition (Section 6.4) apply to the desugared form.

---

## 7. Operator Semantics

### 7.1 `+`
Tensor addition. Requires exact type identity. See Section 6.12.1 for symmetry propagation.

### 7.2 `*`
Tensor product by default. Scalar scaling when one operand is rank 0. See Section 6.12.2 for symmetry behavior.

### 7.3 `@`
Canonical contraction operator. Legal ONLY for the three forms defined in Section 6.7:

1. covector @ vector -> scalar
2. rank-2 mixed tensor @ vector -> vector
3. covector @ rank-2 mixed tensor -> covector

All other uses SHALL raise an AmbiguityError.

### 7.4 `contract(...)`
Explicit contraction. The preferred and general-purpose contraction mechanism. Required for all contractions not covered by `@`.

### 7.5 `raise(...)`
Raises one compatible covariant slot using a declared inverse metric or pairing.

### 7.6 `lower(...)`
Lowers one compatible contravariant slot using a declared metric or pairing.

### 7.7 `sym(...)`
Projects to the symmetric component.

### 7.8 `antisym(...)`
Projects to the antisymmetric component.

### 7.9 Unary `-`
Negation. Equivalent to `(-1) * operand`. See Section 6.13.1.

### 7.10 Binary `-`
Subtraction. Syntactic sugar for `A + (-1) * B`. See Section 6.13.2.

---

## 8. Structural Objects

### 8.1 Metric
A metric declaration introduces:

- a symmetric covariant rank-2 tensor
- nondegeneracy requirement
- induced raising/lowering maps
- optional norm and trace operations

### 8.2 Connection
A connection introduces tensor-aware differentiation on declared bundles or spaces.

TLS 0.2 reserves syntax for connections but does not fully define covariant derivative semantics. See Section 16 for the TLS-Calc roadmap.

### 8.3 Basis
A basis declaration binds a coordinate representation to a space.

```tls
basis e for V
```

A basis MAY be used to expose component arrays. Basis data SHALL NOT alter tensor identity.

---

## 9. Representation Model

### 9.1 Coordinate Representation
A tensor MAY have components relative to a basis.

Example:

```tls
let v = components(e) [1,2,3]
```

### 9.2 Representation Safety
Operations on component arrays are legal only when basis compatibility is established.

### 9.3 Transformation Law
Implementations SHALL preserve tensorial transformation laws when changing basis.

---

## 10. Validity Rules

An expression is valid iff all of the following hold:

1. every identifier is declared or bound
2. every tensor slot has declared space compatibility
3. every addition has identical operand types
4. every contraction pairs compatible opposite-variance slots
5. every raising/lowering references declared structure
6. every symmetry projection references valid slot indices
7. no operator introduces hidden non-tensorial dependence unless explicitly declared
8. every concrete tensor value conforms to the dimension well-formedness rule (Section 6.11)
9. every use of `@` matches one of the three canonical forms (Section 6.7)
10. every `where` block contains only declarations, not persistent bindings

---

## 11. Error Classes

TLS implementations SHOULD expose the following error classes:

### 11.1 ParseError
Invalid syntax.

### 11.2 TypeError
Operator applied to incompatible tensor types, or concrete value violates dimension well-formedness.

### 11.3 VarianceError
Illegal contraction or raise/lower mismatch.

### 11.4 SpaceError
Incompatible spaces used in one operation, or dimension mismatch between a concrete value and its declared space.

### 11.5 StructureError
Missing metric, pairing, basis, or connection.

### 11.6 AmbiguityError
An operation admits multiple incompatible interpretations. In particular, use of `@` on operands that do not match one of the three canonical forms (Section 6.7) SHALL raise this error.

### 11.7 SymmetryError
In strict mode, addition of tensors with incompatible symmetry annotations. See Section 6.12.1.

### 11.8 PreconditionError
A standard library operation was invoked on an operand that does not satisfy the operation's preconditions (e.g., `inv` on a degenerate tensor, `eigenvalues` on a non-endomorphism).

---

## 12. Ordinary Arithmetic Embedding

TLS embeds ordinary arithmetic as a rank-0 tensor fragment.

### 12.1 Numerals
```tls
1 : Tensor<>
2 : Tensor<>
```

### 12.2 Scalar Addition
```tls
1 + 2
```

Interpretation:

```tls
Tensor<> + Tensor<> -> Tensor<>
```

### 12.3 Scalar Subtraction
```tls
5 - 3
```

Interpretation:

```tls
5 + (-1) * 3 -> Tensor<>
```

### 12.4 Scalar Multiplication
```tls
2 * 3
```

Interpretation:

- rank-0 tensor product
- equivalent to scalar multiplication in the coefficient ring

### 12.5 Scalar Negation
```tls
-7
```

Interpretation:

```tls
(-1) * 7 -> Tensor<>
```

Thus ordinary arithmetic is a conservative sublanguage of TLS.

---

## 13. Standard Library

TLS 0.2 provides the following built-in operations. Each operation specifies its preconditions; failure to satisfy a precondition SHALL raise a PreconditionError.

### 13.1 Core Operations (TLS-Core)

| Operation | Signature | Preconditions |
|-----------|-----------|---------------|
| `contract(T, i, j)` | Removes two slots, returns reduced tensor | Slots `i`,`j` have opposite variance over compatible spaces |
| `raise(T, g)` | Returns tensor with one covariant slot raised | `g` is a declared nondegenerate metric compatible with the target slot |
| `lower(T, g)` | Returns tensor with one contravariant slot lowered | `g` is a declared nondegenerate metric compatible with the target slot |
| `sym(T, i, j)` | Projects to symmetric part in slots `i`,`j` | Slots `i`,`j` have same variance and same space |
| `antisym(T, i, j)` | Projects to antisymmetric part in slots `i`,`j` | Slots `i`,`j` have same variance and same space |
| `rank(T)` | Returns integer rank | None |
| `type_of(T)` | Returns tensor type | None |
| `spaces_of(T)` | Returns list of spaces | None |
| `variances_of(T)` | Returns list of variances | None |
| `is_scalar(T)` | Returns boolean | None |
| `is_symmetric(T)` | Returns boolean | None |
| `trace(T)` | Contracts the canonical pair of opposite-variance slots | `T` has exactly one contravariant and one covariant slot over the same space, OR explicit slot indices are provided |
| `transpose(T)` | Swaps two slots of a rank-2 tensor | `T` is rank 2 |

### 13.2 Structured Operations (TLS-Core, guarded)

| Operation | Signature | Preconditions | Returns |
|-----------|-----------|---------------|---------|
| `det(T)` | `det : Tensor<V+,V-> -> Tensor<>` | `T` is rank-2 with one contravariant and one covariant slot over the same finite-dimensional space (endomorphism interpretation), OR `T` is a rank-2 covariant/contravariant tensor over a single finite-dimensional space with a declared metric for index raising | Scalar (element of the ring) |
| `inv(T)` | `inv : Tensor<V+,V-> -> Tensor<V-,V+>` | Same as `det`, plus nondegeneracy (`det(T) != 0`). The result type has swapped variance relative to the input. | Tensor with swapped variance |
| `eigenvalues(T)` | `eigenvalues : Tensor<V+,V-> -> List<Tensor<>>` | `T` must admit an endomorphism interpretation: rank-2 with one contravariant and one covariant slot over the same finite-dimensional space. The ring must support the characteristic polynomial (algebraically closed or extension thereof). Stricter than `det` or `trace`: this operation depends on the specific basis-independent spectral structure. | Ordered list of scalars |

### 13.3 Geometric Operations (TLS-Geom)

| Operation | Signature | Preconditions | Returns |
|-----------|-----------|---------------|---------|
| `norm(v, g)` | `norm : (Tensor<V+>, Tensor<V-,V->) -> Tensor<>` | `v` is a vector, `g` is a declared nondegenerate symmetric metric over the same space. The ring must support a square root operation or the result is `norm_squared`. | Scalar. If the ring supports square roots, returns `sqrt(contract(lower(v,g), v))`. Otherwise, implementations MAY return the squared norm and document this behavior. |

---

## 14. Sample Programs

### 14.1 Scalar Arithmetic
```tls
ring R
let x = 1
let y = 2
assert type_of(x + y) == Tensor<>
```

### 14.2 Vector and Covector Contraction
```tls
ring R
space V over R dim 2
let v = v(3,4)
let w = cv(1,2)
let s = w @ v
```

Expected type:

```tls
s : Tensor<>
```

### 14.3 Tensor Product
```tls
ring R
space V over R dim 2
let v = v(2,1)
let w = cv(5,7)
let A = v * w
```

Expected type:

```tls
A : Tensor<V+,V->
```

### 14.4 Metric Use
```tls
ring R
space V over R dim 3
metric g : Tensor<V-,V-> {sym(1,2), nondegenerate}
let v = v(1,2,3)
let omega = lower(v, g)
```

Expected type:

```tls
omega : Tensor<V->
```

### 14.5 Negation and Subtraction
```tls
ring R
space V over R dim 2
let a = v(3,4)
let b = v(1,1)
let c = a - b
let d = -a
```

Expected types:

```tls
c : Tensor<V+>
d : Tensor<V+>
```

### 14.6 Where Clause
```tls
ring R
let result = contract(T[a+, b-], v[b+]) where
  space V over R dim 3
  tensor T : Tensor<V+, V->
  tensor v : Tensor<V+>
```

Expected type:

```tls
result : Tensor<V+>
```

### 14.7 Ambiguity Error on `@`
```tls
ring R
space V over R dim 2
tensor A : Tensor<V+, V->
tensor B : Tensor<V+, V->
# The following is ILLEGAL and must raise AmbiguityError:
# let C = A @ B
# Correct form:
let C = contract(A[a+, b-], B[b+, c-])
```

### 14.8 Dimension Well-Formedness Error
```tls
ring R
space V over R dim 3
# The following is ILLEGAL — v(1,2) has 2 components but V has dim 3:
# let v = v(1,2)
# Correct:
let v = v(1,2,3)
```

### 14.9 Symmetry Propagation
```tls
ring R
space V over R dim 3
tensor A : Tensor<V-, V-> {sym(1,2)}
tensor B : Tensor<V-, V-> {sym(1,2)}
let C = A + B
# C : Tensor<V-, V-> {sym(1,2)}

tensor D : Tensor<V-, V-> {antisym(1,2)}
# In strict mode, A + D is a SymmetryError
# In relaxed mode, A + D : Tensor<V-, V-> (no symmetry annotation)
```

---

## 15. Conformance Tests

This section defines normative conformance tests. A conforming TLS 0.2 implementation MUST produce the specified results for each test. Tests are organized by compliance level.

### 15.1 TLS-Core Conformance

#### Test C01: Scalar promotion
```tls
ring R
let x = 42
assert type_of(x) == Tensor<>
```
**Expected**: PASS. `x` is a rank-0 tensor.

#### Test C02: Scalar arithmetic
```tls
ring R
let x = 3
let y = 4
let z = x + y
assert is_scalar(z)
assert z == 7
```
**Expected**: PASS. Both assertions hold.

#### Test C03: Scalar negation
```tls
ring R
let x = 5
let y = -x
assert y == -5
assert type_of(y) == Tensor<>
```
**Expected**: PASS.

#### Test C04: Scalar subtraction
```tls
ring R
let x = 10
let y = 3
let z = x - y
assert z == 7
```
**Expected**: PASS.

#### Test C05: Vector type
```tls
ring R
space V over R dim 3
let v = v(1,2,3)
assert type_of(v) == Tensor<V+>
assert rank(v) == 1
```
**Expected**: PASS.

#### Test C06: Covector-vector contraction via `@`
```tls
ring R
space V over R dim 2
let w = cv(1,2)
let v = v(3,4)
let s = w @ v
assert type_of(s) == Tensor<>
assert s == 11
```
**Expected**: PASS. `s = 1*3 + 2*4 = 11`.

#### Test C07: Tensor product type
```tls
ring R
space V over R dim 2
let u = v(1,0)
let w = cv(0,1)
let T = u * w
assert type_of(T) == Tensor<V+, V->
assert rank(T) == 2
```
**Expected**: PASS.

#### Test C08: Mixed tensor @ vector
```tls
ring R
space V over R dim 2
tensor T : Tensor<V+, V->
let T = m(1,0;0,2)
let v = v(3,4)
let w = T @ v
assert type_of(w) == Tensor<V+>
```
**Expected**: PASS. `w` is a vector.

#### Test C09: `@` on rank-2 @ rank-2 raises AmbiguityError
```tls
ring R
space V over R dim 2
tensor A : Tensor<V+, V->
tensor B : Tensor<V+, V->
let A = m(1,0;0,1)
let B = m(2,0;0,2)
let C = A @ B
```
**Expected**: AmbiguityError.

#### Test C10: Dimension well-formedness violation
```tls
ring R
space V over R dim 3
let v = v(1,2)
```
**Expected**: TypeError or SpaceError. `v(1,2)` has 2 components but `V` has dimension 3.

#### Test C11: Addition type mismatch
```tls
ring R
space V over R dim 2
space W over R dim 3
let v = v(1,2)
let w = v(1,2,3)
let z = v + w
```
**Expected**: TypeError. `Tensor<V+>` cannot be added to `Tensor<W+>`.

#### Test C12: Explicit contraction
```tls
ring R
space V over R dim 2
tensor T : Tensor<V+, V->
let T = m(1,2;3,4)
assert trace(T) == 5
```
**Expected**: PASS. Trace = 1 + 4 = 5.

#### Test C13: Symmetry preservation under addition
```tls
ring R
space V over R dim 2
tensor A : Tensor<V-, V-> {sym(1,2)}
tensor B : Tensor<V-, V-> {sym(1,2)}
let C = A + B
assert is_symmetric(C)
```
**Expected**: PASS.

#### Test C14: Symmetry destruction under mixed addition (strict mode)
```tls
ring R
space V over R dim 2
tensor A : Tensor<V-, V-> {sym(1,2)}
tensor B : Tensor<V-, V-> {antisym(1,2)}
let C = A + B
```
**Expected**: SymmetryError in strict mode. In relaxed mode: PASS with `is_symmetric(C) == false`.

#### Test C15: Where clause scoping
```tls
ring R
space V over R dim 2
let s = contract(T[a+, b-], w[b+]) where
  tensor T : Tensor<V+, V->
  let T = m(1,0;0,1)
  tensor w : Tensor<V+>
  let w = v(5,6)
assert type_of(s) == Tensor<V+>
# T and w from the where block are not visible here
```
**Expected**: PASS. `s` has type `Tensor<V+>`. Names `T` and `w` are not bound outside the `where` block.

#### Test C16: det of identity
```tls
ring R
space V over R dim 2
tensor I : Tensor<V+, V->
let I = m(1,0;0,1)
assert det(I) == 1
```
**Expected**: PASS.

#### Test C17: inv type
```tls
ring R
space V over R dim 2
tensor T : Tensor<V+, V->
let T = m(1,2;3,4)
let S = inv(T)
assert type_of(S) == Tensor<V-, V+>
```
**Expected**: PASS. Inverse swaps variance.

#### Test C18: inv of degenerate matrix
```tls
ring R
space V over R dim 2
tensor T : Tensor<V+, V->
let T = m(1,2;2,4)
let S = inv(T)
```
**Expected**: PreconditionError. `det(T) = 0`.

### 15.2 TLS-Geom Conformance

#### Test G01: Lowering with metric
```tls
ring R
space V over R dim 2
metric g : Tensor<V-, V-> {sym(1,2), nondegenerate}
let g = m(1,0;0,1)
let v = v(3,4)
let omega = lower(v, g)
assert type_of(omega) == Tensor<V->
```
**Expected**: PASS.

#### Test G02: Lowering without metric raises StructureError
```tls
ring R
space V over R dim 2
let v = v(3,4)
let omega = lower(v, g)
```
**Expected**: StructureError. `g` is not declared.

#### Test G03: Raise then lower is identity (with Euclidean metric)
```tls
ring R
space V over R dim 2
metric g : Tensor<V-, V-> {sym(1,2), nondegenerate}
let g = m(1,0;0,1)
let v = v(3,4)
let omega = lower(v, g)
let v2 = raise(omega, g)
assert v2 == v
```
**Expected**: PASS (for Euclidean metric, raise and lower are mutual inverses).

---

## 16. Tensor Field Roadmap (TLS-Calc)

This section describes planned syntax and semantics for tensor fields over manifolds. The constructs described here are **reserved but not yet normative**. Implementations SHALL NOT reject these keywords but are not required to implement their semantics until TLS-Calc is finalized.

### 16.1 Planned Declarations

#### Manifold Declaration
```tls
manifold M dim 4
```

Declares a smooth manifold with the given dimension.

#### Bundle Declaration
```tls
bundle TM over M
```

Declares a vector bundle over a manifold.

#### Tensor Field Declaration (Option A: dedicated keyword)
```tls
tensorfield g : TensorField<M, TM-, TM->
```

#### Tensor Field Declaration (Option B: compositional type)
```tls
tensor g : Field<M, Tensor<TM-, TM->>
```

Option A is more readable. Option B is more compositional and consistent with the existing type system. A future TLS-Calc specification will select one form or support both.

### 16.2 Semantic Distinction

A **tensor** (as defined in TLS-Core and TLS-Geom) is a multilinear map at a single point — an element of a tensor product of vector spaces.

A **tensor field** is a smooth assignment of a tensor to each point of a manifold — a section of a tensor bundle.

This distinction is critical for:

- **Covariant derivatives**: only meaningful for tensor fields, not pointwise tensors.
- **Lie derivatives**: require a vector field, not just a vector.
- **Curvature**: a tensor field derived from a connection on a bundle.
- **Integration**: requires tensor densities or forms over a manifold.

### 16.3 Reserved Keywords

The following keywords are reserved for TLS-Calc and SHALL NOT be used as identifiers in any TLS compliance level:

- `field` (tensor fields, NOT coefficient rings — use `ring` for coefficient domains)
- `manifold`
- `bundle`
- `tensorfield`

---

## 17. Compliance Levels

### TLS-Core
Required:

- scalar promotion
- tensor addition (with symmetry propagation per Section 6.12)
- negation and subtraction (Section 6.13)
- tensor product
- explicit contraction via `contract(...)`
- canonical contraction via `@` (Section 6.7) with AmbiguityError enforcement
- dimension well-formedness checking (Section 6.11)
- `where` clause (Section 5.7)
- rank/type introspection
- standard library: core operations and structured operations (Section 13.1, 13.2)
- parser for typed tensor expressions with statement delimiters
- all TLS-Core conformance tests (Section 15.1) MUST pass

### TLS-Geom
Adds:

- metrics
- raising/lowering
- symmetry annotations
- basis declarations
- geometric standard library operations (Section 13.3)
- all TLS-Geom conformance tests (Section 15.2) MUST pass

### TLS-Calc
Adds:

- differential operators
- connections
- tensor fields over manifolds (Section 16)
- covariant differentiation
- Lie derivatives

### TLS-Graph
Adds graph theory and Ramsey theory operations on adjacency tensors:

#### 17.4.1 Graph Construction

| Operation | Signature | Preconditions | Returns |
|-----------|-----------|---------------|---------|
| `adjacency(n)` | `adjacency : Tensor<> -> Tensor<V+,V->` | `n` is a positive integer scalar, 2 ≤ n ≤ 50 | Adjacency matrix of K_n (complete graph): all 1s with 0 diagonal |
| `paley(p)` | `paley : Tensor<> -> Tensor<V+,V->` | `p` is prime, p ≥ 5, p ≡ 1 (mod 4) | Paley graph: vertices = Z_p, edge iff (u-v) is a quadratic residue mod p. Self-complementary, vertex-transitive. |
| `circulant(n, S)` | `circulant : (Tensor<>, Tensor<V+>) -> Tensor<V+,V->` | `n` is a positive integer, `S` is a vector of integer differences | Circulant graph: edge (u,v) iff \|u-v\| mod n is in S (symmetric closure applied automatically) |
| `complement(A)` | `complement : Tensor<V+,V-> -> Tensor<V+,V->` | `A` is a square rank-2 tensor with 0/1 entries | Complement graph: off-diagonal entries flipped (0↔1) |

#### 17.4.2 Graph Analysis

| Operation | Signature | Preconditions | Returns |
|-----------|-----------|---------------|---------|
| `degree(A)` | `degree : Tensor<V+,V-> -> Tensor<V+>` | `A` is a square rank-2 tensor | Vector of row sums (degree sequence) |
| `triangles(A)` | `triangles : Tensor<V+,V-> -> Tensor<>` | `A` is a square rank-2 tensor | Number of triangles via trace(A³)/6 |
| `cliques(A, k)` | `cliques : (Tensor<V+,V->, Tensor<>) -> Tensor<>` | `A` is square rank-2, `k` is integer scalar 2 ≤ k ≤ 10 | Number of complete k-subgraphs (exhaustive enumeration) |
| `independent_set(A, k)` | `independent_set : (Tensor<V+,V->, Tensor<>) -> Tensor<>` | `A` is square rank-2, `k` is integer scalar 1 ≤ k ≤ 15 | Number of independent sets of size k (no edges between any pair) |
| `chromatic(A)` | `chromatic : Tensor<V+,V-> -> Tensor<>` | `A` is a square rank-2 tensor with 0/1 entries | Edge color counts: red (1) and blue (0) with totals |
| `hadamard(A, B)` | `hadamard : (Tensor<V+,V->, Tensor<V+,V->) -> Tensor<V+,V->` | Same dimensions | Element-wise (Hadamard) product |

#### 17.4.3 Ramsey Theory

| Operation | Signature | Preconditions | Returns |
|-----------|-----------|---------------|---------|
| `ramsey_check(A, s, t)` | `ramsey_check : (Tensor<V+,V->, Tensor<>, Tensor<>) -> Tensor<>` | `A` is square rank-2 with 0/1 entries, `s` and `t` are positive integer scalars | 1 if coloring contains monochromatic red K_s or blue K_t, 0 if Ramsey-avoiding. Explanation includes which clique was found. |
| `ramsey_search(n, s, t)` | `ramsey_search : (Tensor<>, Tensor<>, Tensor<>) -> Tensor<V+,V->` | All scalars, 2 ≤ n ≤ 20 | Random search for R(s,t)-avoiding coloring of K_n. Returns adjacency matrix if found, 0 if no avoiding coloring found in up to 10,000 trials. |
| `ramsey_energy(A, r, s)` | `ramsey_energy : (Tensor<V+,V->, Tensor<>, Tensor<>) -> Tensor<>` | `A` is square rank-2, `r` and `s` are positive integer scalars | Ramsey energy E = count(K_r in A) + count(I_s in complement(A)). An energy of 0 means the coloring is R(r,s)-avoiding. |
| `ramsey_anneal(n, r, s [, trials])` | `ramsey_anneal : (Tensor<>, Tensor<>, Tensor<> [, Tensor<>]) -> Tensor<V+,V->` | All scalars, 3 ≤ n ≤ 30, optional trials (default 3, max 20) | Simulated annealing search for R(r,s)-avoiding coloring of K_n. Minimizes ramsey_energy via Metropolis criterion with geometric cooling. Returns best coloring found. |

#### 17.4.4 Tensor–Graph Connection

Graphs are encoded as rank-2 tensors (adjacency matrices) with natural tensor operations:

- **Contraction** (`A @ A`): Matrix power A² counts paths of length 2 between vertices
- **Trace** (`trace(A @ A @ A) / 6`): Triangle count via closed walks
- **Eigenvalues** (`eigenvalues(A)`): Graph spectrum — algebraic connectivity, spectral gap
- **Hadamard product**: Mask operations for subgraph extraction and color filtering
- **Complement**: Edge-color inversion for Ramsey 2-coloring analysis

This connection enables applying the full TLS tensor algebra (contraction, decomposition, spectral analysis) to combinatorial graph problems.

#### 17.4.5 Algebraic Graph Constructions

Paley graphs and circulant graphs are the two dominant initialization strategies in computational Ramsey theory (see Nagda et al., "Reinforced Generation of Combinatorial Structures: Ramsey Numbers," arXiv:2603.09172, March 2026). TLS-Graph provides both as first-class tensor constructors:

- **Paley graphs** (`paley(p)`): Vertices are elements of the finite field Z_p. Edges connect vertices whose difference is a quadratic residue mod p. Self-complementary and vertex-transitive — optimal starting points for symmetric Ramsey constructions.
- **Circulant graphs** (`circulant(n, S)`): Edges defined by a difference set S, where (u,v) is an edge iff |u-v| mod n is in S. Captures cyclic symmetry, enabling orbit-based search space reduction.
- **Simulated annealing** (`ramsey_anneal(n, r, s)`): Stochastic local search minimizing the Ramsey energy function E(G) = count(K_r) + count(I_s) via Metropolis criterion. The fundamental search primitive used by virtually all computational Ramsey results.

---

## 18. EBNF Grammar

```ebnf
(* TLS 0.2 Formal Grammar *)

program          = { (declaration | statement) terminator } ;
terminator       = NEWLINE | ";" ;

declaration      = ring_decl
                 | space_decl
                 | tensor_decl
                 | metric_decl
                 | connection_decl
                 | type_decl
                 | basis_decl ;

statement        = let_stmt | assert_stmt | expr ;

(* --- Declarations --- *)

ring_decl        = "ring" identifier ;
space_decl       = "space" identifier "over" identifier [ "dim" integer ] ;
tensor_decl      = "tensor" identifier ":" tensor_type ;
metric_decl      = "metric" identifier ":" tensor_type ;
connection_decl  = "connection" identifier "on" identifier "compatible" identifier ;
type_decl        = "type" identifier "=" tensor_type ;
basis_decl       = "basis" identifier "for" identifier ;

(* --- Statements --- *)

let_stmt         = "let" identifier "=" expr ;
assert_stmt      = "assert" expr ;

(* --- Expressions --- *)

expr             = where_expr ;
where_expr       = additive_expr [ "where" NEWLINE INDENT { declaration terminator } DEDENT ] ;
additive_expr    = multiplicative_expr { ("+" | "-") multiplicative_expr } ;
multiplicative_expr = unary_expr { ("*" | "@") unary_expr } ;
unary_expr       = [ "-" ] primary_expr ;
primary_expr     = literal
                 | identifier
                 | indexed_expr
                 | function_call
                 | "(" expr ")" ;

indexed_expr     = identifier "[" index_slot { "," index_slot } "]" ;
index_slot       = identifier ("+" | "-") ;

function_call    = identifier "(" [ expr { "," expr } ] ")" ;

(* --- Literals --- *)

literal          = number
                 | vector_literal
                 | covector_literal
                 | matrix_literal ;

number           = integer | decimal ;
integer          = digit { digit } ;
decimal          = digit { digit } "." digit { digit } ;
vector_literal   = "v" "(" number { "," number } ")" ;
covector_literal = "cv" "(" number { "," number } ")" ;
matrix_literal   = "m" "(" row { ";" row } ")" ;
row              = number { "," number } ;

(* --- Types --- *)

tensor_type      = "Tensor" "<" [ slot_type { "," slot_type } ] ">" [ structure_block ] ;
slot_type        = identifier ("+" | "-") ;
structure_block  = "{" annotation { "," annotation } "}" ;
annotation       = identifier [ "(" integer { "," integer } ")" ] ;

(* --- Lexical --- *)

identifier       = ( letter | "_" ) { letter | digit | "_" } ;
letter           = "A" | ... | "Z" | "a" | ... | "z" ;
digit            = "0" | ... | "9" ;

NEWLINE          = (* platform newline character(s) *) ;
INDENT           = (* increase in indentation level *) ;
DEDENT           = (* decrease in indentation level *) ;
```

**Notes on delimiters:**

- Statements and declarations are terminated by NEWLINE.
- The `;` character MAY be used to chain multiple statements on a single line.
- The `where` clause uses indentation-sensitive parsing: the declarations within a `where` block MUST be indented relative to the `where` keyword.
- Implementations MAY accept `{` ... `}` as an alternative to INDENT/DEDENT for `where` blocks.

---

## 19. Formalization Direction

A future version SHOULD define:

- denotational semantics
- operational semantics for evaluation
- canonical type equivalence rules
- rewrite rules for tensor identities
- proof obligations for invariant-preserving transformations
- formal symmetry inference algorithms
- TLS-Calc normative semantics (tensor fields, connections, curvature)

---

## 20. Foundational Summary

TLS defines a tensor-native mathematical language where:

- scalars are rank-0 tensors
- ordinary arithmetic is a sublanguage
- tensor interaction is explicit
- type safety is structural
- indices are typed and variance-aware
- geometry requires declared structure
- representation does not replace identity
- dimension is a property of spaces, not tensor types
- symmetry propagation is governed by explicit rules
- convenience operators (`@`, `-`) have precise, restricted semantics
- the coefficient domain is declared as a `ring`, with `field` reserved for tensor fields

This makes TLS suitable as a formal foundation for a generalized tensor-standard mathematics system.
