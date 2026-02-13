# Invoker

## Deterministic Capability Orchestration for AI Agents

![Status](https://img.shields.io/badge/status-active-blue)
![Architecture](https://img.shields.io/badge/architecture-deterministic-green)
![Design](https://img.shields.io/badge/design-model--agnostic-orange)

Invoker is a **portable governance layer + structural template** for
orchestrating AI agents with control, predictability, and token
efficiency.

It is not a runtime.\
It is not an SDK.\
It is not a plug-and-play framework.

------------------------------------------------------------------------

## Why Invoker Exists

LLMs tend to:

-   Overconsume tokens
-   Redesign unnecessarily
-   Hallucinate without explicit contracts
-   Blur intention and execution

Invoker enforces:

-   Determinism over creativity
-   Explicit task contracts
-   Selective capability activation
-   Operational kernel modes
-   Separation of intention and execution

------------------------------------------------------------------------

## Quickstart

### Install

``` bash
python install_invoker.py
```

### Select Kernel

``` bash
invoker use standard
invoker status
```

### Create Task

``` bash
invoker task template
# or
invoker task build
```

Edit:

    agent/user_task.yaml

### Execution Flow

Task → Kernel → Triggers → Instructions → Skills → Agent Action

------------------------------------------------------------------------

## Core Concepts

### Kernel

Defines operational mode, limits, and permissions.

### Task.yaml

Explicit contract:

``` yaml
Objective:
Files:
Config:
Constraints:
Risk Tolerance:
```

### Triggers

Deterministic selection engine.

### Instructions

Model-family overrides extending base instructions.

### Skills

Governed procedural units (meta.yaml + body.md).

------------------------------------------------------------------------

## Documentation

See `architecture.md` for full system specification.

------------------------------------------------------------------------

**Last updated:** 2026-02-12
