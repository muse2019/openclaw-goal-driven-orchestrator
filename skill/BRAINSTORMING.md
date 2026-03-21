# Experiment Brainstorming Guide

Guide for brainstorming experiment strategies before goal-driven execution.

## Purpose

Transform a research goal into a structured experiment DAG that the orchestrator
can execute. This phase happens ONCE, before execution begins.

## Process

### 1. Understand the Research Context

Read in order:
1. **Project documentation** — README, docs, CLAUDE.md
2. **Key source files** — the file(s) that will be modified
3. **Prior experiment logs** — `.autoresearch/experiments_log.md` if exists
4. **Recent commits** — understand what's been tried recently

### 2. Clarify the Goal

Ask one question at a time. Wait for answer before next question.

**Goal Question:**
> "What metric should we optimize, and what's the target value?"
>
> Example answer: "Minimize val_bpb, target is under 0.95"

**Constraints Question:**
> "What constraints must we respect?"
>
> Examples:
> - "Cannot modify prepare.py"
> - "Training must complete in 5 minutes"
> - "Single GPU only"

**Budget Question:**
> "What's our total time budget for this research session?"
>
> Example: "60 minutes" or "overnight (8 hours)"

**Risk Tolerance Question:**
> "Should we prefer conservative incremental changes or bold experiments?"
>
> Options:
> - **Conservative** — small changes, each experiment builds on last success
> - **Aggressive** — try radical changes, accept higher failure rate
> - **Balanced** — mix of both

### 3. Design the Initial DAG

Based on domain knowledge and the goal, propose 2-5 initial experiments.

**Template for each experiment:**

```
ID: [unique identifier, e.g., baseline, exp_001]
Parent IDs: [node IDs this depends on, or [] for root]
Hypothesis: [what we're testing, one sentence]
Action: [concrete change to make]
Expected: [predicted outcome, optional]
```

**DAG Design Principles:**

1. **Always start with baseline** — unmodified code run to establish ground truth
2. **Create parallel branches** for independent hypotheses
3. **Create sequential chains** for incremental improvements
4. **Balance exploration vs exploitation** based on risk tolerance

**Example DAG:**

```
baseline (run unmodified)
├── exp_001: increase LR (parallel)
└── exp_002: change architecture (parallel)
    └── exp_003: combine with LR change (sequential)
```

### 4. Present DAG for Approval

Show the DAG structure and ask:
> "This is my initial experiment plan:
>
> [Show DAG structure]
>
> Should I proceed, or would you like to modify any experiments?"

### 5. Iterate Until Approved

Incorporate user feedback, regenerate DAG, repeat approval step.

## Output

Once approved, initialize the working directory:

```
{workspace}/.autoresearch/
├── evolution_dag.json    # Full DAG (starts with initial nodes)
├── initial_dag.json      # Initial plan (preserved for reference)
└── experiments_log.md    # Human-readable log
```

**evolution_dag.json structure:**

```json
{
  "metadata": {
    "workspace": "{workspace}",
    "goal": "[goal from user]",
    "success_criteria": "[criteria from user]",
    "time_budget_minutes": [budget],
    "created_at": "[timestamp]",
    "updated_at": "[timestamp]"
  },
  "nodes": {
    "baseline": {
      "id": "baseline",
      "parent_ids": [],
      "status": "pending",
      "hypothesis": "Establish baseline performance",
      "action": "Run unmodified code",
      "children_ids": []
    },
    "exp_001": {
      "id": "exp_001",
      "parent_ids": ["baseline"],
      "status": "pending",
      "hypothesis": "Higher learning rate accelerates convergence",
      "action": "Increase LR from 0.01 to 0.03",
      "children_ids": []
    }
  },
  "best_node_id": null,
  "statistics": {
    "total_nodes": 2,
    "success_count": 0,
    "dead_end_count": 0,
    "pending_count": 2
  }
}
```

**experiments_log.md template:**

```markdown
# Experiments Log

## Goal
[goal]

## Success Criteria
[criteria]

## Constraints
- [constraint 1]
- [constraint 2]

## Time Budget
[budget] minutes

---

## Experiments

### baseline
- **Hypothesis**: Establish baseline performance
- **Action**: Run unmodified code
- **Status**: pending
- **Result**: (to be filled)

### exp_001
- **Hypothesis**: Higher learning rate accelerates convergence
- **Action**: Increase LR from 0.01 to 0.03
- **Parent**: baseline
- **Status**: pending
- **Result**: (to be filled)
```

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Skip the baseline | Always run unmodified code first |
| Create huge DAGs upfront | Start small, let it evolve |
| Assume all experiments succeed | Design experiments that fail informatively |
| Ask multiple questions at once | One question per message |
| Proceed without approval | Always get explicit user buy-in |
