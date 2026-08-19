# Odyssey task draft

Copy each section **body** (not the `##` heading) into the matching field on the
Odyssey form. Use only keyboard-accessible ASCII (`->`, `^2`, `--`, `<=`,
straight quotes). The Notes section is local scratch and has no form counterpart.

## Title

Train a molecular GNN under a 32 MB checkpoint cap

## Working slug

molecular-gnn-checkpoint-cap

## Collection family

ML engineering

## Task family

performance

## Verifier family

ml_artifact

## Objective

Train a graph neural net for molecular property prediction under the protocol in /app/docs/train.md: a 32 MB compressed-checkpoint cap, a frozen featurizer, and a held-out eval harness across 20 local datasets covering classification and regression. Done means the produced checkpoint loads under the cap, the training recipe is reproducible from /app, and held-out metrics clear the documented thresholds. This is training-under-cap plus a multi-dataset harness, not repairing a broken classifier eval script to recover F1.

## Motivation

ML engineering in this collection is standing up a real training and eval system with a hard resource cap, the way a lab would ship a constrained artifact. Debugging one pipeline flag is not that job.

## Difficulty explanation

The remaining work is data plumbing, model capacity under the byte cap, training schedule, and an eval harness that must not leak. The first-attempt trap is overfitting the visible dataset or emitting a checkpoint that reports metrics without fitting under 32 MB after the verifier's compressor. Hidden datasets and a reseal of the checkpoint catch that. Frontier-model struggle on a tiny eval-repair ticket would not make that ticket long-horizon.

## Expert time estimate (hours)

60

## Environment summary

The image has local datasets, a pinned ML stack, the training protocol, a skeleton trainer, and a dummy baseline that misses the cap or the metric. GPU is optional per the draft envelope. Runtime is sealed. Held-out eval data used by the grader is not in /app.

## Resource estimate

cpuMillis: 8000
memoryMb: 32768
storageMb: 20480
gpuCount: 0
agentTimeoutSec: 28800
verifierTimeoutSec: 3600

## Network requirements

mode: none
justification: All datasets, dependencies, and model components are provided locally for deterministic execution.
hosts: (none)

## Oracle strategy

The reference solution trains a model that fits the cap, writes the checkpoint to the required path, and records the recipe. It does not copy held-out scores into the artifact.

## Verification strategy

Visible checks confirm a loadable checkpoint and metric reporting on a public split. Hidden checks evaluate the resealed checkpoint on held-out datasets and enforce the 32 MB cap after the verifier's compressor. Visible weight is a minority.

## Binary success condition

The task passes only if the checkpoint is under the cap and clears hidden held-out thresholds on the harness.

## Partial score strategy

Partial credit for a valid artifact and for metric progress toward the threshold. Fabricated metrics receive no credit.

## Anticipated exploits

The agent may print expected metrics, leak labels, or ship an oversized checkpoint. The verifier reseals the file, reruns eval on held-out data, and measures compressed size.
