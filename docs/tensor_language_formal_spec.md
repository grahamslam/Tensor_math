# Tensor Language Specification (TLS)

## Version

**TLS 0.1 Draft**

## Status

Exploratory formal specification for a tensor-native symbolic mathematics language.

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

- coefficient field or ring
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

- `space`
- `field`
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

### 4.3 Literals
TLS 0.1 supports the following literal classes:

- integer literals
- decimal literals
- vector literals
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

#### Field Declaration
```tls
field R
```

#### Space Declaration
```tls
space V over R dim 3
space W over R dim 2
```

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
```

---

## 6. Type System

### 6.1 Type Components
Each type contains:

- scalar domain
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
Numeric literals SHALL be promoted to rank-0 tensor type over the current default field.

Example:

```tls
1 : Tensor<>
```

### 6.4 Addition Rule
Addition is valid iff both operands have identical tensor type.

```tls
Gamma |- A : X
Gamma |- B : X
-----------------
Gamma |- A + B : X
```

### 6.5 Tensor Product Rule
If `A` and `B` are tensors, then `A * B` denotes tensor product unless one operand is scalar.

```tls
Gamma |- A : Tensor<S1...Sn>
Gamma |- B : Tensor<T1...Tm>
---------------------------------
Gamma |- A * B : Tensor<S1...Sn,T1...Tm>
```

If either side is rank-0, multiplication denotes scalar scaling.

### 6.6 Contraction Rule
Contraction is valid only when:

- one slot is contravariant
- one slot is covariant
- both belong to compatible spaces
- contraction does not violate declared symmetry structure

```tls
Gamma |- T : Tensor<...,V+,...,V-,...>
--------------------------------------
Gamma |- contract(T, i, j) : Tensor<...remaining slots...>
```

### 6.7 Indexed Contraction Rule
If repeated index labels appear in a valid expression with opposite variance and matching space, an implementation MAY permit explicit indexed contraction under a strict mode flag.

Example:

```tls
T[a+, b-] * v[b+]
```

In strict TLS 0.1, this SHOULD remain non-contracted unless wrapped by `contract(...)`.

### 6.8 Raising and Lowering
Raising and lowering are valid only when a compatible nondegenerate bilinear form is declared.

```tls
Gamma |- g : Tensor<V-,V->
Gamma |- v : Tensor<V+>
------------------------
Gamma |- lower(v,g) : Tensor<V->
```

### 6.9 Symmetrization
```tls
Gamma |- T : Tensor<slots>
--------------------------
Gamma |- sym(T, i, j) : Tensor<slots>{sym(i,j)}
```

### 6.10 Antisymmetrization
```tls
Gamma |- T : Tensor<slots>
--------------------------
Gamma |- antisym(T, i, j) : Tensor<slots>{antisym(i,j)}
```

---

## 7. Operator Semantics

### 7.1 `+`
Tensor addition. Requires exact type identity.

### 7.2 `*`
Tensor product by default. Scalar scaling when one operand is rank 0.

### 7.3 `@`
Reserved shorthand contraction operator. In TLS 0.1, `@` SHALL denote the principal contraction between the rightmost compatible slot of the left operand and the leftmost compatible slot of the right operand, if unique. Otherwise it MUST raise a type ambiguity error.

### 7.4 `contract(...)`
Explicit contraction. Preferred in formal derivations.

### 7.5 `raise(...)`
Raises one compatible covariant slot using a declared inverse metric or pairing.

### 7.6 `lower(...)`
Lowers one compatible contravariant slot using a declared metric or pairing.

### 7.7 `sym(...)`
Projects to the symmetric component.

### 7.8 `antisym(...)`
Projects to the antisymmetric component.

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

TLS 0.1 reserves syntax for connections but does not fully define covariant derivative semantics.

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

---

## 11. Error Classes

TLS implementations SHOULD expose the following error classes:

### 11.1 ParseError
Invalid syntax.

### 11.2 TypeError
Operator applied to incompatible tensor types.

### 11.3 VarianceError
Illegal contraction or raise/lower mismatch.

### 11.4 SpaceError
Incompatible spaces used in one operation.

### 11.5 StructureError
Missing metric, pairing, basis, or connection.

### 11.6 AmbiguityError
An operation admits multiple incompatible interpretations.

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

### 12.3 Scalar Multiplication
```tls
2 * 3
```

Interpretation:

- rank-0 tensor product
- equivalent to scalar multiplication in the coefficient field

Thus ordinary arithmetic is a conservative sublanguage of TLS.

---

## 13. Minimal Standard Library

TLS 0.1 SHOULD provide these built-ins:

- `contract`
- `raise`
- `lower`
- `sym`
- `antisym`
- `rank`
- `type_of`
- `spaces_of`
- `variances_of`
- `is_scalar`
- `is_symmetric`
- `trace` (only where defined)
- `transpose` (for declared compatible rank-2 forms)

---

## 14. Sample Programs

### 14.1 Scalar Arithmetic
```tls
field R
let x = 1
let y = 2
assert type_of(x + y) == Tensor<>
```

### 14.2 Vector and Covector Contraction
```tls
field R
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
field R
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
field R
space V over R dim 3
metric g : Tensor<V-,V-> {sym(1,2), nondegenerate}
let v = v(1,2,3)
let omega = lower(v,g)
```

---

## 15. Compliance Levels

### TLS-Core
Required:

- scalar promotion
- tensor addition
- tensor product
- explicit contraction
- rank/type introspection
- parser for typed tensor expressions

### TLS-Geom
Adds:

- metrics
- raising/lowering
- symmetry annotations
- basis declarations

### TLS-Calc
Adds:

- differential operators
- connections
- tensor fields over manifolds
- covariant differentiation

---

## 16. Formalization Direction

A future version SHOULD define:

- full grammar in EBNF
- denotational semantics
- operational semantics for evaluation
- canonical type equivalence rules
- rewrite rules for tensor identities
- proof obligations for invariant-preserving transformations

---

## 17. Proposed EBNF Sketch

```ebnf
program        = { declaration | statement } ;
declaration    = field_decl | space_decl | tensor_decl | metric_decl | type_decl ;
statement      = let_stmt | assert_stmt | expr ;
field_decl     = "field" identifier ;
space_decl     = "space" identifier "over" identifier [ "dim" number ] ;
tensor_decl    = "tensor" identifier ":" tensor_type ;
metric_decl    = "metric" identifier ":" tensor_type ;
type_decl      = "type" identifier "=" tensor_type ;
let_stmt       = "let" identifier "=" expr ;
assert_stmt    = "assert" expr ;
expr           = additive_expr ;
additive_expr  = multiplicative_expr { "+" multiplicative_expr } ;
multiplicative_expr = primary_expr { ("*" | "@") primary_expr } ;
primary_expr   = literal | identifier | indexed_expr | function_call | "(" expr ")" ;
indexed_expr   = identifier "[" index_slot { "," index_slot } "]" ;
index_slot     = identifier ("+" | "-") ;
function_call  = identifier "(" [ expr { "," expr } ] ")" ;
literal        = number | vector_literal | covector_literal | matrix_literal ;
vector_literal = "v" "(" number { "," number } ")" ;
covector_literal = "cv" "(" number { "," number } ")" ;
matrix_literal = "m" "(" number { "," number } ";" number { "," number } { ";" number { "," number } } ")" ;
tensor_type    = "Tensor" "<" [ slot_type { "," slot_type } ] ">" [ structure_block ] ;
slot_type      = identifier ("+" | "-") ;
structure_block = "{" identifier [ "(" number { "," number } ")" ] { "," identifier [ "(" number { "," number } ")" ] } "}" ;
```

---

## 18. Foundational Summary

TLS defines a tensor-native mathematical language where:

- scalars are rank-0 tensors
- ordinary arithmetic is a sublanguage
- tensor interaction is explicit
- type safety is structural
- indices are typed and variance-aware
- geometry requires declared structure
- representation does not replace identity

This makes TLS suitable as the first formal step toward a generalized tensor-standard mathematics system.

