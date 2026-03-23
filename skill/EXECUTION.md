# Execution Protocol

Phase 2 of the Goal-Driven Orchestrator. Execute the plan by driving
workers through nodes, verifying results independently, and evolving
the DAG based on findings.

## Purpose

Take the approved `plan.json` and systematically work through every node,
using the right protocol for each node type.

**Announce at start:** "I'm using the execution skill to run the plan."

## Main Loop

```
STEP 1: Select next node
STEP 2: Spawn worker (typed prompt)
STEP 3: Verify result
STEP 4: Record + Evolve
STEP 5: Terminate or continue
     ↑                    │
     └── not done ────────┘
```

---

## STEP 1: Select Next Node

```
ENTER: Loop start or previous node complete
DO:
  1. Read .autoresearch/plan.json
  2. Find nodes where:
     - status = "pending"
     - all parent_ids have status in [completed, answered, verified,
       failed, refuted, unanswerable, theoretical]
  3. Priority (pick first match):
     a. type="synthesis" with all inputs ready
     b. type="verification" (validate previous findings quickly)
     c. type="experiment" (produce concrete results)
     d. type="research" (gather information)
     e. Tie-break: shallower depth first, then ID order
EXIT: selected_node determined
ERROR:
  - No pending nodes → go to STEP 5 (termination)
  - Plan file missing → notify user
```

---

## STEP 2: Spawn Worker

Construct the prompt based on `node.type`, then spawn.

### Experiment Node Prompt

```
## Your Task

**Hypothesis**: {node.hypothesis}
**Setup**: {node.setup}
**Run**: {node.run}

## Success Criteria

Metric: {node.metric}
Pass condition: {node.pass_condition}

## Constraints

{metadata.constraints}
Timeout: {worker_timeout_seconds} seconds

## Prior Results (read first)

Read .autoresearch/findings_log.md for prior attempts.
Known dead ends: {dead_end_summaries}
Current best: {best_result}

## Output

Create file: .autoresearch/results/{node.id}.json

{
  "node_id": "{node.id}",
  "status": "completed" | "failed" | "error",
  "metric_value": <number or null>,
  "changes_made": ["file:lines", ...],
  "verification_command": "<command to reproduce>",
  "insights": ["..."],
  "error": null | "description"
}

Do NOT edit plan.json or findings_log.md.
```

### Research Node Prompt

```
## Your Task

**Question**: {node.question}
**Approach**: {node.approach}
**Expected deliverable**: {node.deliverable}

## Research Goal

{metadata.goal}

## Prior Findings (read first)

Read .autoresearch/findings_log.md
Already answered: {answered_summaries}
Already ruled out: {unanswerable_summaries}

## Output

Create file: .autoresearch/findings/{node.id}.json

{
  "node_id": "{node.id}",
  "question": "{node.question}",
  "status": "answered" | "partial" | "unanswerable",
  "summary": "One sentence answer",
  "evidence": ["source/proof 1", "source/proof 2"],
  "artifacts": ["paths to files created"],
  "confidence": "high" | "medium" | "low",
  "verifiable": true | false,
  "verification_plan": {
    "method": "How to verify experimentally",
    "metric": "What to measure",
    "pass_condition": "What counts as pass"
  } | null,
  "new_questions": ["Questions discovered during research"]
}

Rules for verifiable:
- Set true if this finding CAN be tested by running code
- Set false if it requires real-world action, future prediction, or
  information that is not programmatically accessible
- If true, you MUST provide verification_plan

Do NOT edit plan.json or findings_log.md.
```

### Verification Node Prompt

```
## Your Task

Experimentally verify the following claim:

**Claim**: {parent_finding.summary}
**Method**: {node.approach}
**Metric**: {node.metric}
**Pass condition**: {node.pass_condition}

## Output

Create file: .autoresearch/results/{node.id}.json

{
  "node_id": "{node.id}",
  "parent_id": "{parent_node.id}",
  "status": "pass" | "fail",
  "metric_value": <number>,
  "verification_command": "<exact command to reproduce>",
  "details": "Explanation of result"
}

You MUST actually run the code. Theoretical analysis is NOT acceptable
for verification nodes.

Do NOT edit plan.json or findings_log.md.
```

### Synthesis Node Prompt

```
## Your Task

Synthesize the following findings into a coherent answer:

**Goal**: {metadata.goal}

**Input findings**:
{for each parent: summary + status + evidence}

## Output

Create file: .autoresearch/findings/{node.id}.json

{
  "node_id": "{node.id}",
  "status": "answered",
  "summary": "Comprehensive answer",
  "details": "Full analysis with references to input findings",
  "recommendations": ["Actionable next step 1", ...],
  "confidence_breakdown": {
    "verified_claims": ["claims backed by experiments"],
    "theoretical_claims": ["claims without experimental validation"],
    "refuted_claims": ["claims disproven by experiments"]
  }
}

Do NOT edit plan.json or findings_log.md.
```

### Spawn Command (OpenClaw)

Use `sessions_spawn` to create worker subagents:

```
DO:
  1. Construct prompt based on node type (see above)
  2. sessions_spawn(
       label="worker-{node.id}",
       task=prompt,
       mode="run",
       runtime="subagent",
       model="default",
       runTimeoutSeconds={worker_timeout_seconds}
     )
  3. Update node: status = "running", started_at = now()
  4. Save plan.json

ERROR:
  Spawn fails → retry once → if still fails, mark node as "error" with reason "spawn_failed"

### Worker Result Retrieval

Workers save results to `.autoresearch/results/` or `.autoresearch/findings/`.
After spawn completes, read the result file to verify.
```

---

## STEP 3: Verify Result

Independent verification. Never trust worker claims.

### For Experiment / Verification Nodes

```
DO:
  1. Check .autoresearch/results/{node.id}.json exists
  2. Validate JSON format and required fields
  3. Run the verification_command yourself
  4. Compare your metric_value vs worker's metric_value
  5. Check pass_condition against YOUR measurement

  Judgment:
  - Your result matches + pass_condition met    → "completed" / "pass"
  - Your result matches + pass_condition not met → "failed" / "fail"
  - Your result differs from worker's claim      → "failed", note discrepancy
  - Command fails to run                        → "error"
  - No result file                              → "error"
```

### For Research Nodes

```
DO:
  1. Check .autoresearch/findings/{node.id}.json exists
  2. Validate JSON format and required fields
  3. Quality checklist:
     □ Has summary
     □ Has evidence (at least 1 item)
     □ Has confidence level
     □ Evidence is traceable (URLs, file paths, commands)
     □ Summary does not overclaim beyond evidence
     □ If verifiable=true, verification_plan is provided
  4. For prototype artifacts: run the code, check it works

  Judgment:
  - All checks pass → accept worker's status
  - Evidence weak but direction right → downgrade to "partial"
  - No evidence or fabricated → "unanswerable", log reason
```

### For Synthesis Nodes

```
DO:
  1. Check finding file exists
  2. Verify it references ALL input nodes
  3. Verify conclusions don't contradict verified findings
  4. Check recommendations are actionable

  Judgment:
  - Comprehensive and consistent → "answered"
  - Missing inputs → ask worker to redo
```

---

## STEP 4: Record + Evolve

### 4a: Update the Node

```
DO:
  1. Update node status based on verification
  2. Record result/finding data on the node
  3. Set completed_at = now()
  4. Update statistics (completed_count, pending_count)
  5. Backup: copy plan.json → plan.backup.json
  6. Save plan.json
  7. Append to findings_log.md:

     ### {node.id} [{node.type}]: {question or hypothesis}
     - **Status**: {status}
     - **Finding/Result**: {summary or metric}
     - **Evidence**: {evidence list}
     - **Confidence**: {confidence or pass/fail}
```

### 4b: Evolve the DAG

Based on the result, add new nodes:

**Research node answered + verifiable=true:**

```
Generate a verification child node:
{
  "id": "{node.id}_verify",
  "type": "verification",
  "parent_ids": ["{node.id}"],
  "question": "Verify: {finding.summary}",
  "approach": "{finding.verification_plan.method}",
  "metric": "{finding.verification_plan.metric}",
  "pass_condition": "{finding.verification_plan.pass_condition}",
  "status": "pending"
}
```

**Research node answered + has new_questions:**

```
For each new question, generate a research child node.
Limit: max 3 new questions per node.
```

**Verification node pass:**

```
Update parent node: confidence = "verified"
```

**Verification node fail:**

```
Update parent node: confidence = "refuted"
Mark parent's new_questions-spawned children as "superseded"
(don't execute research based on a refuted finding)
```

**Experiment completed + meaningful result:**

```
If result suggests a refinement, generate 1 follow-up experiment.
If budget < 20% remaining, do NOT generate new experiments.
```

**Any node partial:**

```
Generate 1 more focused child node to complete the answer.
```

**DAG Limits:**

```
- Total pending nodes: max 10
- DAG depth: max 5 levels
- Children per node: max 3
```

---

## STEP 5: Terminate or Continue

```
DO:
  Check conditions in order:

  1. GOAL ACHIEVED:
     Success criteria from goal_spec are met.
     → Generate final report, notify user.

  2. TIME EXHAUSTED:
     elapsed >= time_budget_minutes
     → Generate report with current findings, notify user.

  3. NODE LIMIT:
     total_nodes >= max_nodes
     → Generate report, notify user.

  4. ALL PATHS DEAD:
     No pending nodes, goal not achieved.
     → Notify user: "All paths explored, goal not fully met.
       Options: add new directions, relax criteria, or stop."

  5. CONSECUTIVE FAILURES:
     Last 5 nodes all failed/unanswerable/refuted.
     → Notify user: "Research may be stuck. Adjust direction?"

  NONE triggered → return to STEP 1.
```

---

## Final Report

When terminating, generate `.autoresearch/report.md`:

```markdown
# Research Report: {goal}

## Summary
[One paragraph answer to the original goal]

## Verified Findings
(Backed by experimental evidence)
- [finding with metric/proof]

## Theoretical Findings
(Supported by evidence but not experimentally verified)
- [finding with sources]

## Refuted Hypotheses
(Initially promising but disproven by experiments)
- [what was tried and why it failed]

## Unanswered Questions
- [questions that remain open]

## Recommendations
1. [Actionable next step]
2. ...

## Research Path
[DAG summary: what was asked → what was found → what it led to]

## Appendix
- Full plan: .autoresearch/plan.json
- Visualization: .autoresearch/plan_graph.html
- All findings: .autoresearch/findings/
- All results: .autoresearch/results/
- Prototypes: .autoresearch/prototypes/
```

---

## User Notification Points

Only notify user in these situations:

| Situation | Action |
|-----------|--------|
| Goal achieved | Report success + final report |
| Time/node budget exhausted | Report best findings so far |
| All paths dead | Ask for new directions |
| 5 consecutive failures | Ask if direction is wrong |
| Verification refutes key finding | Alert: previous conclusions may be invalid |
