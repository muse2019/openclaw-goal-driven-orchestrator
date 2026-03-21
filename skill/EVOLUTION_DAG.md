# Evolution DAG Management

Management system for the dynamic experiment evolution graph.

## Overview

The Evolution DAG is the central data structure that tracks:
- All experiments (nodes) and their relationships (edges)
- Experiment results, insights, and status
- The best result found so far and the path to it
- Statistics about the research session

## Storage

**Location:** `{workspace}/.autoresearch/evolution_dag.json`

This file is the source of truth for the orchestrator and should be:
- Updated after every experiment completes
- Read by every new worker to avoid repeating mistakes
- Preserved across sessions for resumable research

## Data Structure

### Full Schema

```json
{
  "metadata": {
    "workspace": "/path/to/project",
    "goal": "Minimize val_bpb",
    "success_criteria": "val_bpb < 0.95",
    "constraints": ["Cannot modify prepare.py", "Single GPU only"],
    "time_budget_minutes": 60,
    "created_at": "2026-03-21T12:00:00Z",
    "updated_at": "2026-03-21T13:30:00Z"
  },
  "nodes": {
    "[node_id]": {
      "id": "exp_001",
      "parent_ids": ["baseline"],
      "status": "success",
      "hypothesis": "Higher learning rate accelerates convergence",
      "action": "Increase LR from 0.01 to 0.03",
      "result": {
        "metric": 0.9932,
        "delta": -0.0047,
        "commit": "b2c3d4e",
        "duration_seconds": 325
      },
      "insights": ["LR=0.03 works well with this architecture"],
      "children_ids": ["exp_005", "exp_006"],
      "created_at": "2026-03-21T12:05:00Z",
      "started_at": "2026-03-21T12:10:00Z",
      "completed_at": "2026-03-21T12:15:25Z"
    }
  },
  "best_node_id": "exp_042",
  "statistics": {
    "total_nodes": 47,
    "success_count": 18,
    "dead_end_count": 12,
    "pending_count": 3,
    "running_count": 1,
    "total_time_minutes": 58
  }
}
```

### Node Status Values

| Status | Description |
|--------|-------------|
| `pending` | Not yet started, waiting for parents |
| `running` | Worker currently executing |
| `success` | Completed successfully, metric improved |
| `dead_end` | Failed or made things worse |

### Node Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier |
| `parent_ids` | string[] | IDs of parent nodes (empty for root) |
| `status` | enum | pending/running/success/dead_end |
| `hypothesis` | string | What we're testing |
| `action` | string | Concrete change made |
| `result` | object | Metric, commit, duration |
| `insights` | string[] | What we learned |
| `children_ids` | string[] | IDs of child nodes spawned |
| `timestamps` | object | created_at, started_at, completed_at |

## Operations

### Add Node

When spawning a new experiment:

1. Generate unique ID (e.g., `exp_048`)
2. Set parent_ids based on which node spawned it
3. Initialize status as `pending`
4. Add to nodes dict
5. Update parent's children_ids
6. Update statistics.total_nodes

### Update Node Status

When a worker completes:

1. Set status to `success` or `dead_end`
2. Record result (metric, commit, duration)
3. Record insights from worker output
4. Update statistics (success_count/dead_end_count)
5. Check if this is new best, update best_node_id if so
6. Update metadata.updated_at

### Query Ready Nodes

Get nodes ready to run (all parents resolved, status=pending):

```python
def get_ready_nodes(dag):
    ready = []
    for node_id, node in dag["nodes"].items():
        if node["status"] != "pending":
            continue
        parents_resolved = all(
            dag["nodes"][pid]["status"] in ["success", "dead_end"]
            for pid in node["parent_ids"]
        )
        if parents_resolved:
            ready.append(node_id)
    return ready
```

### Query Best Path

Get the path from root to best node:

```python
def get_best_path(dag):
    if not dag["best_node_id"]:
        return []

    path = []
    current = dag["best_node_id"]
    while current:
        path.append(current)
        parents = dag["nodes"][current]["parent_ids"]
        current = parents[0] if parents else None

    return list(reversed(path))
```

## Dynamic Evolution

### Adding Child Nodes

When a node succeeds:

1. Parse worker insights
2. Generate 1-3 child experiments:
   - **Exploit**: "What if we push this direction further?"
   - **Explore**: "What's an orthogonal direction to try?"
   - **Combine**: "Can we merge this with another success?"

**Example:**

```json
// Parent succeeded with LR=0.03
{
  "id": "exp_001",
  "status": "success",
  "insights": ["LR=0.03 works well"],
  "children_ids": ["exp_005", "exp_006"]
}

// Generated children
{
  "exp_005": {
    "id": "exp_005",
    "parent_ids": ["exp_001"],
    "hypothesis": "Even higher LR might work",
    "action": "Increase LR to 0.05",
    "status": "pending"
  },
  "exp_006": {
    "id": "exp_006",
    "parent_ids": ["exp_001"],
    "hypothesis": "Combine good LR with architecture change",
    "action": "LR=0.03 + increase depth",
    "status": "pending"
  }
}
```

### Marking Dead Ends

When a node fails:

1. Set status to `dead_end`
2. Record failure reason in result.error
3. Do NOT spawn children
4. Record insight about what NOT to try

**Example:**

```json
{
  "id": "exp_007",
  "status": "dead_end",
  "result": {
    "error": "Training diverged, NaN loss at step 42"
  },
  "insights": ["LR=0.1 is too high for this architecture"]
}
```

## Visualization

Generate an interactive HTML visualization:

```bash
python scripts/visualize_evolution.py .autoresearch/evolution_dag.json
# Creates .autoresearch/evolution_graph.html
```

**Visualization Features:**
- DAG layout with nodes as circles
- Color coding: green=success, red=dead_end, gray=pending, blue=running
- Click node to see details panel
- Show metric evolution over time
- Highlight best path
- Filter by status

## Backup and Resume

### Backup

The DAG is automatically saved after each update. For additional safety:

```bash
cp .autoresearch/evolution_dag.json .autoresearch/evolution_dag.backup.json
```

### Resume

If resuming an interrupted session:

1. Read existing `evolution_dag.json`
2. Find nodes with status `running` (interrupted)
3. Reset them to `pending`
4. Continue with ready nodes

## Integration with Orchestrator

The orchestrator should:

1. **Before each experiment:** Read DAG, select ready node
2. **During experiment:** Update node status to `running`
3. **After experiment:** Update result, insights, status
4. **Evolve:** Add new nodes based on insights
5. **Save:** Write DAG to disk after each update
