---
name: goal-driven-orchestrator
description: >
  Goal-adaptive autonomous orchestrator. Understands your goal through
  brainstorming, classifies it (research/experiment/hybrid), generates
  a tailored execution plan as a DAG, then drives workers through the plan
  with independent verification. Use for autonomous research, systematic
  experiments, or any goal requiring structured trial-and-error with memory.
---

# Goal-Driven Orchestrator

An autonomous orchestrator that adapts its workflow to your goal.

## Core Rules

- Do **not** implement solutions yourself — delegate to workers
- Treat worker results as untrusted until independently verified
- Keep complete history in `.autoresearch/plan.json`
- Every new worker must read prior findings/results
- Stop when: time budget exhausted, goal achieved, or all paths dead

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `time_budget_minutes` | 60 | Total time budget |
| `max_nodes` | 50 | Maximum nodes before stopping |
| `worker_timeout_seconds` | 360 | Per-worker timeout |

## Three-Phase Workflow

Follow these phases in order. Each phase has its own instruction file.

### Phase 0: Brainstorm

**File:** `BRAINSTORMING.md`

Understand the goal through dialogue:
1. Read project context
2. Ask clarifying questions (one at a time)
3. Explore 2-3 approaches with trade-offs
4. Produce a `goal_spec` with goal_type classification

**Output:** `goal_spec` containing goal, constraints, budget, direction, and type.

### Phase 1: Plan

**File:** `PLANNING.md`

Generate the execution plan based on `goal_spec`:
1. Build a DAG matching the goal_type
2. Present plan to user for approval
3. Initialize `.autoresearch/` working directory

**Output:** `plan.json` — a structured DAG ready for execution.

### Phase 2: Execute

**File:** `EXECUTION.md`

Run the plan:
1. Pick next ready node from DAG
2. Route to the right protocol based on node type:
   - `experiment` → run code, compare metrics
   - `research` → gather info, verify evidence
   - `synthesis` → combine findings
3. Verify independently
4. Record results, evolve DAG
5. Check termination → loop or report

**Output:** `report.md` — final findings with verified/theoretical classification.

## Boundaries

- Do NOT claim success based only on worker narration
- Do NOT skip verification because worker sounds confident
- Do NOT exceed time_budget or max_nodes without user escalation
- Do NOT modify files outside the allowed scope
- Do NOT proceed to Phase 1 without completing Phase 0
- Do NOT proceed to Phase 2 without user approval of the plan
