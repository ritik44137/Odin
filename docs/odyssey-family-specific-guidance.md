# Family-Specific Guidance

Use this document when a raw task idea is still underspecified and needs to be shaped into a stronger Odyssey task.

Horizon first: each family is a **complete system**, not a ticket. Collection
bar: `docs/odyssey-long-horizon.md`. Trap design:
`docs/odyssey-difficulty-design.md`.

## Library clone

Best for reproducing a complete real library, compiler, decoder, interpreter,
LSP, runtime, or control plane against a frozen spec or RFC.

Strong signals:

- remaining work is the whole stack (codec + session + planner, or
  preprocessor + IR + codegen), not one operator
- conformance-style verification over generated inputs
- edge cases and invariants matter more than UI polish

Weak patterns to avoid:

- add/fix a feature in an existing parser
- implement a small greenfield module of a few public functions
- trivial CRUD wrappers with no semantic depth
- tasks that are really product slices disguised as a library

## Product clone

Best for cloning a real application: APIs, persistence, auth, jobs, and the
product surface (UI or SDK).

Strong signals:

- multiple application layers that only succeed together
- user-visible behavior and backend workflow correctness
- verification inspects API, durable state, and the product surface

Weak patterns to avoid:

- one workflow slice (offline queue, invoice retry) in an existing app
- toy UI scaffolds without meaningful backend or state logic
- single-function tasks mislabeled as product work

## ML engineering

Best for training, post-training, porting, or kernel-optimizing a real model
under a hard cap, or for a multi-dataset eval harness.

Strong signals:

- model artifacts or evaluation outputs are central
- a resource cap (checkpoint bytes, latency, one-GPU budget) that a dummy
  file cannot fake
- held-out eval the agent cannot rewrite

Weak patterns to avoid:

- repair a broken eval script to recover F1
- fake ML tasks where the model is irrelevant to success
- tasks that require open-ended internet retrieval to function

## Algorithmic optimization

Best for beating a tight cycle, conflict, or quality target on a substantial
solver or custom-ISA kernel without breaking semantics.

Strong signals:

- measurable baseline and measurable improvement target
- correctness (and proofs, if the domain has them) preserved on hidden cases
- performance wins require real reasoning rather than toggling an obvious flag

Weak patterns to avoid:

- reduce peak memory in an already-correct helper
- unverifiable claims of speedup
- optimization tasks without stable measurement conditions

## Family shape must match the label

Instruction, `/app` starting state, and tests must all look like the declared
collection family. A library-clone draft whose `/app` is a fleet rollout script
and whose tests grep syslog is misclassified, not clever. The same is true in
the other direction: do not relabel a parser bug as Product clone to look more
novel. Honesty of family is part of review, and the corpus is balanced across
the four families.

Difficulty must live where that family is actually hard, not in a copied
pipeline. Horizon must live where that family is actually long, not in a
padded timeout. See `docs/odyssey-difficulty-design.md` and
`docs/odyssey-long-horizon.md`.

## Cross-family question

Before locking classification, ask: what is the central thing being graded?

- behavior against a complete library/protocol spec -> likely Library clone
- full application clone -> likely Product clone
- metric-driven model or artifact under a cap -> likely ML engineering
- preserved correctness plus efficiency improvement on a substantial kernel -> likely Algorithmic optimization
