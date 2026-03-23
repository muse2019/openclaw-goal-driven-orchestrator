# Planning Guide

Phase 1 of the Goal-Driven Orchestrator. Generate a structured execution
plan (DAG) based on the goal_spec from brainstorming.

## Purpose

Transform the goal_spec into a concrete, executable plan. The plan is a
DAG of typed nodes that Phase 2 (Execution) will process.

**Announce at start:** "I'm using the planning skill to create the execution plan."

## Input

Read `.autoresearch/goal_spec.md` from brainstorming output.
Required fields: goal, type, success_criteria, constraints, time_budget.

## Plan Generation

### Step 1: Design the DAG

Based on `goal_type`, use the matching template:

---

#### Template: `experiment`

For goals where the answer comes from running code and measuring results.

```
baseline: Run unmodified/current state to establish ground truth
├── EXP_01: [Test approach A]
├── EXP_02: [Test approach B]
├── EXP_03: [Test approach C]  (optional)
└── SYN_01: Compare results, recommend best
```

Each experiment node must define:
- `hypothesis`: what we expect
- `setup`: preparation steps
- `run`: exact command(s) to execute
- `metric`: what to measure
- `pass_condition`: what counts as success

---

#### Template: `research`

For goals where the answer comes from gathering and analyzing information.

```
RES_00: Foundational research (context, landscape, basics)
├── RES_01: [Sub-question 1]
├── RES_02: [Sub-question 2]
├── RES_03: [Sub-question 3]
└── SYN_01: Synthesize findings into answer
```

Each research node must define:
- `question`: what we're investigating
- `approach`: how to investigate (search, read docs, analyze code, etc.)
- `deliverable`: expected output (summary doc, data file, etc.)

---

#### Template: `hybrid`

For goals requiring both investigation and experimental validation.

```
RES_00: Foundational research
├── RES_01: [Investigate aspect 1]
│   └── (EXP_XX: may be auto-generated during execution if finding is verifiable)
├── RES_02: [Investigate aspect 2]
│   └── (EXP_XX: may be auto-generated during execution if finding is verifiable)
├── RES_03: [Investigate aspect 3]
└── SYN_01: Synthesize all findings + experimental results
```

Hybrid plans start with research nodes. Experiment nodes are added
dynamically during execution when a research finding is verifiable.

---

### Step 2: Present for Approval

Show the DAG to the user:

```
Here's the execution plan:

[Show DAG structure with node descriptions]

Total nodes: [N]
Estimated time: [X] minutes

Should I proceed, or would you like to modify the plan?
```

### Step 3: Initialize Working Directory

After approval, create:

```
{workspace}/.autoresearch/
├── goal_spec.md          # From brainstorming (already exists)
├── plan.json             # The execution plan
├── plan_initial.json     # Backup of initial plan
├── findings_log.md       # Human-readable log (starts empty)
├── findings/             # Research finding files
├── results/              # Experiment result files
└── prototypes/           # Code artifacts from workers
```

## plan.json Structure

See `PLAN_SCHEMA.md` for the full schema. Abbreviated:

```json
{
  "metadata": {
    "goal": "...",
    "goal_type": "experiment | research | hybrid",
    "success_criteria": "...",
    "constraints": [],
    "time_budget_minutes": 60,
    "created_at": "...",
    "updated_at": "..."
  },
  "nodes": {
    "RES_01": {
      "id": "RES_01",
      "type": "research",
      "parent_ids": ["RES_00"],
      "question": "...",
      "approach": "...",
      "deliverable": "...",
      "status": "pending",
      "finding": null,
      "children_ids": []
    },
    "EXP_01": {
      "id": "EXP_01",
      "type": "experiment",
      "parent_ids": ["baseline"],
      "hypothesis": "...",
      "setup": "...",
      "run": "...",
      "metric": "...",
      "pass_condition": "...",
      "status": "pending",
      "result": null,
      "children_ids": []
    }
  },
  "statistics": {
    "total_nodes": 0,
    "completed_count": 0,
    "pending_count": 0
  }
}
```

## After Approval

Invoke the execution phase. Read `EXECUTION.md` and follow it.

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Create huge plans upfront | Start with 3-7 nodes, let execution evolve |
| Mix node types without reason | Match node type to what the goal actually needs |
| Skip user approval | Always get explicit sign-off before executing |
| Forget the baseline | Experiment plans must start with a baseline node |
