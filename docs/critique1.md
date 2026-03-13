This is an excellent critique. You’re not just reacting to the surface — you’re pushing on exactly the places where a language either becomes real or stays poetic.

I agree with nearly all of it.

## My take on each point

### 1. `@` needs tighter semantics

Yes. Your proposed restriction is the right move.

The current wording is too permissive for a formal spec. “If unique” sounds helpful, but in practice it creates a gray zone. A spec should prefer fewer magical cases and more explicitness.

I would revise it to:

* `@` is only legal for a small set of canonical contractions:

  * covector @ vector
  * rank-2 mixed tensor @ vector
  * covector @ rank-2 mixed tensor
* all other contractions must use `contract(...)`

So:

```tls
cv(1,2) @ v(3,4)
m(1,2;3,4) @ v(5,6)
```

are fine, but:

```tls
T @ S
```

is illegal unless the implementation can prove it matches one of the canonical forms.

That gives `@` the role of a convenience operator, not a second contraction language.

---

### 2. Dimension tracking in the type system

Also yes.

I agree with your preferred solution: dimension should live on the **space**, not be duplicated in every tensor type.

So the type checker should validate both:

* symbolic tensor type compatibility
* component shape compatibility induced by declared spaces

That means:

* `Tensor<V+>` is still the correct type
* but if `space V over R dim 3`, then any concrete value assigned to `Tensor<V+>` must have length 3

So the missing rule is really a **well-formedness constraint**, not a type syntax change.

I’d add something like:

> For any tensor with slots over declared finite-dimensional spaces, each represented axis must conform to the declared dimension of its corresponding space.

That keeps the language elegant while still catching:

* `v(1,2)` in `V dim 3`
* malformed matrix dimensions
* invalid contractions due to mismatched realized shape

---

### 3. Tensor vs tensor field distinction

Completely right.

This becomes unavoidable the moment TLS-Calc grows teeth.

Right now the spec still lives mostly in multilinear algebra over fixed spaces. As soon as you introduce:

* manifolds
* connections
* curvature
* covariant derivatives

you must distinguish between:

* a tensor at a point
* a tensor field over a base space

I think your instinct is correct, though I’d slightly refine the naming.

Instead of overloading `field`, I’d rename coefficient declarations to something like:

```tls
scalar_domain R
```

or

```tls
ring R
```

Then reserve `field` for tensor fields later if desired.

For TLS-Calc I’d likely introduce:

```tls
manifold M dim 4
bundle TM over M
tensorfield g : TensorField<M, TM-, TM->
```

or, more uniformly:

```tls
tensor g : Field<M, Tensor<TM-, TM->>
```

The second is more compositional, but the first is easier to read.

So yes: this distinction belongs in the roadmap explicitly.

---

### 4. Symmetry propagation

Yes again. This is a real omission.

Right now symmetry is treated as metadata attached to a tensor, but the language doesn’t say when that metadata survives, combines, or is destroyed.

You’re right that this needs inference rules.

I’d formalize it conservatively:

* `sym + sym -> sym` if the symmetry annotations are identical
* `antisym + antisym -> antisym` if identical
* mixed symmetry classes under addition require either:

  * rejection
  * or result type downgraded to unspecialized tensor type

I would choose the second only if explicitly requested by the implementation mode. In formal mode, I’d rather reject ambiguous structural weakening.

For products:

* tensor product does not automatically preserve whole-object symmetry unless derivable on a specified slot subset

For contraction:

* the resulting symmetry must be recomputed based on surviving slots

That last part is subtle and important. Contraction can:

* preserve symmetry
* destroy symmetry
* induce new symmetry in reduced forms

So this needs a dedicated “symmetry inference” section, not just a sentence.

---

### 5. No negation or subtraction

Correct, and easy to fix.

Your formulation is exactly how I would do it:

* unary negation:

  * `-T ≡ (-1) * T`
* subtraction:

  * `A - B ≡ A + (-1) * B`

That keeps the language algebraically clean and avoids introducing a separate semantic primitive.

Grammar-wise, TLS should add:

* unary minus in expressions
* binary subtraction as syntactic sugar lowered during parsing

This is one of those fixes that is small syntactically but makes the language feel much more complete.

---

### 6. `where` is reserved but undefined

Good catch. That’s sloppy in a formal spec.

And your proposed use is strong. `where` is valuable because TLS otherwise risks becoming declaration-heavy for small expressions.

I’d define it as a **local typing and declaration scope**.

Example:

```tls
contract(T[a+, b-], v[b+]) where
  space V over R dim 3
  tensor T : Tensor<V+, V->
  tensor v : Tensor<V+>
```

Semantically:

* `where` introduces a temporary environment
* bindings exist only for the attached expression or statement
* inner declarations shadow outer ones if allowed by mode

That would make TLS much better for notebooks, calculators, and theorem-style derivations.

---

### 7. Missing `det`, `inv`, `eigenvalues`

Agreed, with one caution: these should be defined as **structured operations**, not generic tensor operations.

Because not every rank-2 tensor deserves determinant or inverse semantics automatically. Those operations need conditions:

* square endomorphism or bilinear form
* finite-dimensionality
* nondegeneracy for inverse
* field/domain support for spectral operations

So I would absolutely add them, but guarded:

* `det(T)` requires a square compatible rank-2 representation over a finite-dimensional space
* `inv(T)` requires nondegeneracy and a compatible interpretation
* `eigenvalues(T)` requires endomorphism interpretation over a supported scalar domain
* `norm(v, g)` absolutely belongs in TLS-Geom

This is exactly the kind of thing that should live in the standard library with preconditions.

---

### 8. Program delimiters in EBNF

Yes. The EBNF sketch is underspecified there.

Your proposal is sensible:

* newline-terminated statements
* optional `;` for same-line chaining

That fits both:

* file-based specs
* interactive calculator/notebook use

So the grammar should say that explicitly.

---

## The bigger picture

What I like most about your critique is that it separates three layers that the first draft blurred together:

### Layer 1: tensor algebra core

* type safety
* variance
* spaces
* contraction
* tensor product

### Layer 2: representation and computation

* dimensions
* component shapes
* determinant
* inverse
* spectral operations

### Layer 3: geometry and fields

* manifolds
* tensor fields
* connections
* covariant differentiation

That separation is exactly what will keep TLS coherent.

## What I would change in the spec now

If I were revising the spec from your notes, I would make these immediate edits:

* restrict `@` to canonical unambiguous contractions only
* add a dimension well-formedness rule tied to declared spaces
* explicitly reserve tensor fields for TLS-Calc
* add symmetry propagation rules
* add unary negation and subtraction as lowered syntax
* define `where` as local scoped declarations
* expand the standard library with guarded structured operations
* define statement delimiters in the grammar

## My only mild pushback

Only one place I’d be slightly careful: on `eigenvalues`.

Not because it shouldn’t exist, but because in a tensor-native language it should probably not be presented as universally natural for all rank-2 tensors. It is natural for:

* endomorphisms
* matrix representations relative to a chosen basis
* certain metric-induced identifications

So I’d include it, but with stricter semantics than `trace` or `det`.

## My verdict

Your critique improves the spec materially. These are not cosmetic notes. They are the kinds of corrections that turn a draft from “interesting concept” into “candidate formal language.”

The most important fixes, in order, are:

1. tighten `@`
2. add dimension well-formedness
3. distinguish tensor values from tensor fields
4. define symmetry propagation
5. define `where`

Those five would stabilize the foundation fast.

The next move I’d recommend is to write **TLS 0.2**, incorporating your changes as normative edits. That would be much stronger than just discussing them abstractly.
