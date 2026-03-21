---
name: autoresearch-goal-driven
description: >
  Autonomous research orchestrator that combines brainstorming with goal-driven
  execution. Generates an evolving experiment DAG, spawns isolated workers,
  verifies results independently, and records the full research evolution.
  Use when running autonomous experiments, overnight research tasks, or
  any scenario requiring systematic trial-and-error with memory.
---

# Autoresearch Goal-Driven Orchestrator

A master orchestrator for autonomous research that combines:
1. **Brainstorming Phase** — Understand goals, design experiment strategy
2. **Goal-Driven Execution** — Spawn workers, verify results, record evolution
3. **Dynamic DAG Evolution** — Prune dead ends, extend new branches, merge successes

## Core Rules

- Do **not** implement solutions yourself — delegate to workers
- Treat worker results as untrusted until independently verified
- Keep complete experiment history in `.autoresearch/evolution_dag.json`
- Every new worker must read prior experiment history
- Stop when: time budget exhausted, max experiments reached, or all paths dead

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `time_budget_minutes` | 60 | Total research time budget |
| `max_experiments` | 100 | Maximum experiments before stopping |
| `worker_timeout_seconds` | 360 | Per-worker timeout |
| `parallel_workers` | 1 | Concurrent workers (future) |
| `evolution_strategy` | `dynamic` | `static` or `dynamic` |

## Workflow

Follow this process exactly.

### Phase 1: Brainstorming

**Step 1: Understand Context**

Read in order:
1. Project README / documentation
2. Key source files for the task
3. Prior experiment logs if they exist
4. Recent commits to understand what's been tried

**Step 2: Clarify the Goal**

Ask one question at a time:
- **Goal**: What metric should we optimize, and what's the target value?
- **Constraints**: What must we respect? (files not to modify, time limits, etc.)
- **Budget**: What's our total time budget for this session?
- **Risk Tolerance**: Conservative incremental or bold experiments?

**Step 3: Design Initial DAG**

Generate 2-5 initial experiments as a DAG:

```json
{
  "nodes": [
    {
      "id": "baseline",
      "parent_ids": [],
      "hypothesis": "Establish baseline performance",
      "action": "Run unmodified code"
    },
    {
      "id": "exp_001",
      "parent_ids": ["baseline"],
      "hypothesis": "Higher learning rate accelerates convergence",
      "action": "Increase LR from 0.01 to 0.03"
    }
  ]
}
```

**Step 4: Get User Approval**

Present the DAG and ask:
> "This is my initial experiment plan. Should I proceed, or modify?"

**Step 5: Initialize Storage**

Create the working directory and save initial state:
```
{workspace}/.autoresearch/
├── evolution_dag.json
├── initial_dag.json
└── experiments_log.md
```

### Phase 2: Goal-Driven Execution

**Main Loop:**

1. **Select next node** — pick pending node with all parents resolved
2. **Spawn worker** — isolated execution with timeout
3. **Verify independently** — run verification commands yourself
4. **Update node** — record result, mark success/dead_end
5. **Evolve DAG** — add new nodes based on insights
6. **Check termination** — time budget? max experiments? all paths dead?

**Worker Prompt Template:**

```
Your task is to achieve: [node.hypothesis]

Action: [node.action]

Success criteria:
- [success_criteria from DAG]

Read .autoresearch/experiments_log.md for prior attempts.
Work only on the implementation.
Run verification before reporting back.
Report ONLY when done or blocked with concrete evidence.
```

**Verification Standards:**

- If criteria mention tests, run those tests
- If criteria mention a script, run that script
- If criteria mention output shape, inspect the artifact
- Never accept "done" at face value — verify yourself

### Phase 3: DAG Evolution

**When a worker succeeds:**

1. Parse the result and insights
2. Generate child experiments:
   - **Exploit**: Double down on what worked
   - **Explore**: Try orthogonal direction
   - **Combine**: Merge with another successful path
3. Add new nodes to DAG

**When a worker fails:**

1. Mark node as `dead_end`
2. Record exact failure reason
3. Do NOT spawn children from dead ends

**Node Status Transitions:**

```
pending → running → success | dead_end
                ↑________|
                 (retry with different approach)
```

## DAG Schema

```json
{
  "metadata": {
    "workspace": "/path/to/project",
    "goal": "Minimize val_bpb",
    "success_criteria": "val_bpb < 0.95",
    "time_budget_minutes": 60,
    "created_at": "2026-03-21T12:00:00Z",
    "updated_at": "2026-03-21T13:30:00Z"
  },
  "nodes": {
    "baseline": {
      "id": "baseline",
      "parent_ids": [],
      "status": "success",
      "hypothesis": "Establish baseline",
      "action": "Run unmodified train.py",
      "result": {
        "metric": 0.9979,
        "commit": "a1b2c3d",
        "duration_seconds": 320
      },
      "insights": ["Baseline performance established"],
      "children_ids": ["exp_001", "exp_002"]
    }
  },
  "best_node_id": "exp_042",
  "statistics": {
    "total_nodes": 47,
    "success_count": 18,
    "dead_end_count": 12,
    "pending_count": 3
  }
}
```

## Output

### Progress Updates

When updating the user:
- Report verified status only, not worker claims
- Mention current experiment number
- Show the verification command(s) run
- Be explicit about pass/fail

### Final Report

```
=== Autoresearch Complete ===

Goal: [goal]
Time: [X] minutes
Experiments: [N]

Best result: [node_id]
  - Metric: [value] (improved [delta] from baseline)
  - Commit: [hash]
  - Path: baseline → exp_003 → ... → [best]

Evolution summary:
  - [N] dead ends pruned
  - [N] new branches discovered
  - [N] branches merged

See .autoresearch/evolution_dag.json for full history.
```

## Boundaries

- Do NOT claim success based only on worker narration
- Do NOT skip verification because worker sounds confident
- Do NOT spawn children from dead_end nodes
- Do NOT exceed time_budget or max_experiments without user escalation
- Do NOT modify files outside the allowed scope
