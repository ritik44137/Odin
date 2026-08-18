# Odyssey task draft

Copy each section **body** (not the `##` heading) into the matching field on the
Odyssey form. Use only keyboard-accessible ASCII (`->`, `^2`, `--`, `<=`,
straight quotes). The Notes section is local scratch and has no form counterpart.

## Title

Repair evaluation pipeline for fine-tuned classifier and recover held-out F1

## Working slug

repair-classifier-eval-pipeline-f1

## Collection family

ML engineering

## Task family

debugging

## Verifier family

ml_artifact

## Objective

Repair an existing training and evaluation pipeline for a fine-tuned text classifier so the produced model artifact and evaluation outputs achieve the required held-out F1 score without corrupting the training protocol. The agent must identify and fix the pipeline defects, preserve reproducibility, and generate the artifact expected by the verifier. Done means the repaired pipeline completes successfully in the provided environment and the resulting artifact clears the verifier's hidden quality threshold on held-out evaluation data.

## Motivation

This task reflects real ML engineering work where the challenge is not inventing a model from scratch but repairing a broken training or evaluation path so a system once again produces trustworthy metrics and usable artifacts.

## Difficulty explanation

The difficulty lies in finding the real source of metric failure inside a multi-step ML pipeline. A weak model may blame the data, overfit visible metrics, or patch only surface-level scripts while leaving leakage, label handling, evaluation mismatch, or artifact packaging bugs unresolved. The hidden verifier can detect shallow fixes because it evaluates the actual produced artifact and held-out performance, not just whether training ran.

## Expert time estimate (hours)

8

## Environment summary

The sandbox contains a Python ML project in /app with local training data, validation data, a broken training/evaluation pipeline, and the necessary libraries preinstalled in the image. GPU is not required. The task is fully offline and all model assets and datasets are bundled locally.

## Resource estimate

cpuMillis: 6000
memoryMb: 8192
storageMb: 8192
gpuCount: 0
agentTimeoutSec: 10800
verifierTimeoutSec: 3600

## Network requirements

mode: none
justification: All datasets, dependencies, and model components are provided locally for deterministic execution.
hosts: (none)

## Oracle strategy

The reference solution identifies the pipeline defects, corrects preprocessing and evaluation alignment, retrains or re-runs the pipeline as needed, and produces the model artifact and outputs expected by the verifier. The solved pipeline is reproducible and reaches the held-out threshold reliably within the declared resource budget.

## Verification strategy

The verifier runs the training and evaluation pipeline through tests/test.sh, validates that the expected artifact is produced, checks reproducibility-sensitive outputs, and evaluates the final model on hidden held-out data. Visible checks expose the expected artifact shape and representative metric reporting. Hidden checks verify the decisive held-out F1 threshold, guard against leakage and output spoofing, and ensure the task is solved by producing a valid model artifact rather than by printing fabricated metrics.

## Binary success condition

The task passes only if the repaired pipeline produces the required model artifact and clears the hidden held-out F1 threshold under the verifier.

## Partial score strategy

Partial credit is awarded for producing a valid artifact and improving held-out performance toward the target, with higher weight on genuine metric recovery than on superficial pipeline cleanup. Fabricated or non-reproducible metric outputs receive no credit.

## Anticipated exploits

The agent may try to print expected metrics, bypass true evaluation, leak labels into the pipeline, or emit a placeholder artifact. The verifier defeats these by rerunning evaluation on held-out data, checking artifact structure and behavior, and validating that reported metrics correspond to the actual produced model.
