# Family-Specific Guidance

Use this document when a raw task idea is still underspecified and needs to be shaped into a stronger Odyssey task.

## Library clone

Best for tasks centered on implementing or repairing a focused library, parser, SDK component, adapter, or module with clear behavioral semantics.

Strong signals:

- precise input/output behavior
- conformance-style verification
- edge cases and invariants matter more than UI polish
- hidden tests can vary inputs broadly without changing the core objective

Weak patterns to avoid:

- trivial CRUD wrappers with no semantic depth
- tasks that are really product slices disguised as a library

## Product clone

Best for tasks that recreate a meaningful slice of a real application or workflow and require integrating several components coherently.

Strong signals:

- multiple moving parts across application layers
- user-visible behavior or business workflow correctness matters
- verification can inspect outputs, state changes, and realistic end-to-end behavior

Weak patterns to avoid:

- toy UI scaffolds without meaningful backend or state logic
- single-function tasks mislabeled as product work

## ML engineering

Best for tasks that train, tune, evaluate, wire up, or operationalize a model against a meaningful metric.

Strong signals:

- model artifacts or evaluation outputs are central
- data handling, training loops, metrics, or inference integration are part of the work
- verification checks true metric or artifact quality, not only file existence

Weak patterns to avoid:

- fake ML tasks where the model is irrelevant to success
- tasks that require open-ended internet retrieval to function

## Algorithmic optimization

Best for tasks where correctness already exists or can be specified clearly, and the challenge is to improve performance, memory use, or efficiency without violating semantics.

Strong signals:

- measurable baseline and measurable improvement target
- correctness must be preserved under hidden cases
- performance wins require real reasoning rather than toggling an obvious flag

Weak patterns to avoid:

- unverifiable claims of speedup
- optimization tasks without stable measurement conditions

## Cross-family question

Before locking classification, ask: what is the central thing being graded?

- behavior against a library-like spec -> likely Library clone
- application workflow slice -> likely Product clone
- metric-driven model or artifact -> likely ML engineering
- preserved correctness plus efficiency improvement -> likely Algorithmic optimization