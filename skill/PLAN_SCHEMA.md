# Plan Schema Reference

Data structure reference for `plan.json` — the execution plan DAG.

## Storage

**Location:** `{workspace}/.autoresearch/plan.json`

This file is the source of truth. It should be:
- Updated after every node completes
- Read by every new worker to avoid repeating mistakes
- Preserved across sessions for resumable research
- Backed up before each update to `plan.backup.json`

## Full Schema

```json
{
  "metadata": {
    "goal": "Find viable Polymarket arbitrage strategy",
    "goal_type": "hybrid",
    "success_criteria": "Identify at least one strategy with positive expected value",
    "constraints": ["No real money trading", "Must be automatable"],
    "time_budget_minutes": 120,
    "created_at": "2026-03-23T12:00:00Z",
    "updated_at": "2026-03-23T13:30:00Z"
  },
  "nodes": {
    "[node_id]": { ... }
  },
  "statistics": {
    "total_nodes": 12,
    "completed_count": 7,
    "pending_count": 3,
    "running_count": 1,
    "error_count": 1,
    "elapsed_minutes": 45
  }
}
```

## Node Types

### Research Node

```json
{
  "id": "RES_01",
  "type": "research",
  "parent_ids": ["RES_00"],
  "status": "answered",
  "question": "What is Polymarket's fee structure?",
  "approach": "Read official docs and API documentation",
  "deliverable": "Fee structure summary",
  "finding": {
    "summary": "Trading fee is 2% on profit, no fee on loss",
    "evidence": ["https://docs.polymarket.com/fees"],
    "artifacts": [],
    "confidence": "verified",
    "verifiable": false,
    "verification_plan": null,
    "new_questions": []
  },
  "children_ids": [],
  "created_at": "2026-03-23T12:05:00Z",
  "started_at": "2026-03-23T12:10:00Z",
  "completed_at": "2026-03-23T12:15:00Z"
}
```

### Experiment Node

```json
{
  "id": "EXP_01",
  "type": "experiment",
  "parent_ids": ["baseline"],
  "status": "completed",
  "hypothesis": "Playwright has higher success rate than Puppeteer",
  "setup": "Install both, prepare target URL list",
  "run": "python benchmark.py --tool playwright --runs 100",
  "metric": "success_rate",
  "pass_condition": "playwright_rate > puppeteer_rate + 10%",
  "result": {
    "metric_value": 0.94,
    "delta": 0.21,
    "verification_command": "python benchmark.py --tool playwright --runs 100",
    "duration_seconds": 325
  },
  "insights": ["Playwright handles dynamic content better"],
  "children_ids": ["EXP_03"],
  "created_at": "...",
  "started_at": "...",
  "completed_at": "..."
}
```

### Verification Node

```json
{
  "id": "RES_02_verify",
  "type": "verification",
  "parent_ids": ["RES_02"],
  "status": "pass",
  "question": "Verify: Price gaps >2% occur 3-5 times daily",
  "approach": "Run price monitor for 7 days",
  "metric": "daily_gap_count",
  "pass_condition": "average daily count between 2 and 8",
  "result": {
    "metric_value": 4.2,
    "verification_command": "python monitor.py --days 7 --threshold 0.02",
    "duration_seconds": 604800
  },
  "children_ids": [],
  "created_at": "...",
  "started_at": "...",
  "completed_at": "..."
}
```

### Synthesis Node

```json
{
  "id": "SYN_01",
  "type": "synthesis",
  "parent_ids": ["RES_01", "RES_02", "EXP_01"],
  "status": "answered",
  "question": "What is the overall arbitrage feasibility?",
  "approach": "Combine all findings",
  "finding": {
    "summary": "Arbitrage is feasible but margin is thin (3-5% after fees)",
    "details": "Full analysis...",
    "recommendations": ["Focus on high-volume events", "..."],
    "confidence_breakdown": {
      "verified_claims": ["Price gaps exist (verified by EXP_01)"],
      "theoretical_claims": ["Market makers may act as competition"],
      "refuted_claims": []
    }
  },
  "children_ids": [],
  "created_at": "...",
  "started_at": "...",
  "completed_at": "..."
}
```

## Node Status Values

| Status | Used by | Meaning |
|--------|---------|---------|
| `pending` | all | Not started, waiting for parents |
| `running` | all | Worker executing |
| `answered` | research, synthesis | Question answered with evidence |
| `partial` | research | Partially answered, needs follow-up |
| `unanswerable` | research | Cannot be answered (data unavailable etc.) |
| `completed` | experiment | Experiment ran successfully |
| `failed` | experiment | Experiment ran but hypothesis not supported |
| `pass` | verification | Finding experimentally confirmed |
| `fail` | verification | Finding experimentally disproven |
| `error` | all | Technical failure (spawn fail, timeout, etc.) |
| `verified` | (confidence) | Research finding confirmed by experiment |
| `theoretical` | (confidence) | Research finding not experimentally testable |
| `refuted` | (confidence) | Research finding disproven by experiment |
| `superseded` | all | Skipped because parent was refuted |

## Operations

### Get Ready Nodes

```python
def get_ready_nodes(plan):
    terminal = {"answered", "partial", "unanswerable", "completed",
                "failed", "pass", "fail", "error", "verified",
                "theoretical", "refuted", "superseded"}
    ready = []
    for node_id, node in plan["nodes"].items():
        if node["status"] != "pending":
            continue
        parents_done = all(
            plan["nodes"][pid]["status"] in terminal
            for pid in node["parent_ids"]
        )
        if parents_done:
            ready.append(node_id)
    return ready
```

## Visualization

```bash
python scripts/visualize_evolution.py .autoresearch/plan.json
# Creates .autoresearch/plan_graph.html
```

Node shapes by type:
- Research: rectangle
- Experiment: circle
- Verification: diamond
- Synthesis: hexagon

Colors by confidence:
- Verified: bright green
- Theoretical: yellow
- Refuted: red
- Pending: gray
