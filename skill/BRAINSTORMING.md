# Brainstorming Guide

Phase 0 of the Goal-Driven Orchestrator. Transform a vague goal into a
structured goal specification with classified type.

## Purpose

Understand what the user wants before making any plan. This phase produces
a `goal_spec` that Phase 1 (Planning) consumes.

**Announce at start:** "I'm using the brainstorming skill to understand your goal."

## Process

### 1. Understand the Context

Read in order:
1. **Project documentation** — README, docs, CLAUDE.md
2. **Key source files** — files relevant to the goal
3. **Prior research** — `.autoresearch/` if exists from previous sessions
4. **Recent commits** — what's been tried recently

### 2. Clarify the Goal

Ask one question at a time. Wait for answer before next question.

**Goal Question:**
> "What specific outcome are you trying to achieve?"
>
> Examples:
> - "Find a viable Polymarket arbitrage strategy"
> - "Determine the most stable browser data scraping method"
> - "Compare Playwright vs Puppeteer performance"

**Constraints Question:**
> "What constraints must we respect?"
>
> Examples:
> - "Cannot spend real money for testing"
> - "Must work on Windows"
> - "Single machine only"

**Budget Question:**
> "How much time should I spend on this?"
>
> Example: "60 minutes" or "overnight (8 hours)"

**Depth Question:**
> "How deep should I go?"
>
> Options:
> - **Quick scan** — surface-level overview, fast results
> - **Thorough** — comprehensive investigation with evidence
> - **Exhaustive** — leave no stone unturned, verify everything

### 3. Explore Approaches

Propose 2-3 different approaches with trade-offs:

```
Approach A: [name]
  - How: [method]
  - Pros: [advantages]
  - Cons: [disadvantages]
  - Time estimate: [duration]

Approach B: [name]
  ...

Recommended: [which and why]
```

Wait for user to pick or suggest alternatives.

### 4. Classify Goal Type

Based on the conversation, determine the goal type. This is NOT a
separate step — it falls out naturally from understanding the goal.

**Classification rules:**

| If the goal is about... | Type | Signal words |
|------------------------|------|-------------|
| Running code to compare/measure | `experiment` | "test", "compare", "benchmark", "measure", "which is faster" |
| Gathering information to understand | `research` | "investigate", "analyze", "what is", "how does X work" |
| Finding a solution (needs both) | `hybrid` | "find a way to", "is X feasible", "how to achieve" |

If unclear, ask:
> "Would this be answered by running code and measuring results, by
> gathering and analyzing information, or a mix of both?"

### 5. Confirm the Goal Spec

Present the summary and ask for approval:

```
Here's what I understand:

Goal: [one sentence]
Type: [experiment / research / hybrid]
Success criteria: [what "done" looks like]
Constraints: [list]
Time budget: [X minutes]
Approach: [chosen approach]

Should I proceed to create the execution plan?
```

## Output

The goal_spec. Save to `.autoresearch/goal_spec.md`:

```markdown
# Goal Specification

## Goal
[one sentence]

## Type
[experiment / research / hybrid]

## Success Criteria
[what counts as success]

## Constraints
- [constraint 1]
- [constraint 2]

## Time Budget
[X] minutes

## Approach
[chosen approach and reasoning]

## Context
[relevant project info discovered in step 1]
```

## After Approval

Invoke the planning phase. Read `PLANNING.md` and follow it.

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Skip context reading | Always check existing project state first |
| Ask multiple questions at once | One question per message |
| Assume the goal type | Let it emerge from conversation |
| Jump to planning without approval | Always get explicit user sign-off |
| Over-complicate simple goals | Scale depth to match the actual need |
