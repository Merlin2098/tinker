# Tinker Architecture

## LLM-Friendly Specification

------------------------------------------------------------------------

## System Overview

Tinker is a deterministic orchestration layer governing AI agent
execution through:

-   Explicit task contracts
-   Kernel operational modes
-   Deterministic trigger evaluation
-   Lazy-loaded skills
-   Model-family instruction overrides

------------------------------------------------------------------------

## Execution Flow

Task.yaml ↓ Kernel Resolution ↓ Trigger Engine ↓ Instruction Layer ↓
Skill Activation ↓ Agent Execution

------------------------------------------------------------------------

## Kernel Contract

Defines:

-   mode
-   model_family
-   risk_tolerance
-   execution_scope
-   modification_permissions

Kernel must be explicit and inspectable.

------------------------------------------------------------------------

## Determinism Principles

-   Minimal context activation
-   No uncontrolled exploration
-   No redesign without explicit permission
-   Strict separation of intent and execution

------------------------------------------------------------------------

**Architecture version generated:** 2026-02-12

