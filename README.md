# SkillAblate

**Measure what an Agent Skill actually changes.**

SkillAblate is an open-source evaluation tool for comparing an AI agent **with and without a `SKILL.md`**.

The idea is simple:

```text
same task
same agent
same tools
same environment

WITHOUT SKILL
      vs.
WITH SKILL

      ↓

measured outcome
```

Instead of deciding that a skill is good because its instructions look sophisticated, SkillAblate measures whether the skill changes observable performance.

> **Don't benchmark the description. Ablate the skill.**

## Why SkillAblate?

Agent Skills package reusable instructions, workflows, scripts, references, and other resources for AI agents.

But publishing a skill does not prove that it improves an agent.

A skill could:

* improve task completion
* improve instruction compliance
* reduce errors
* improve tool use
* have no measurable effect
* make performance worse

SkillAblate is designed to make those differences measurable.

## Core experiment

SkillAblate treats the skill as the experimental variable.

```text
                    TASK
                     │
           ┌─────────┴─────────┐
           │                   │
      BASELINE RUN         SKILL RUN
           │                   │
      no SKILL.md          + SKILL.md
           │                   │
           └─────────┬─────────┘
                     │
                  GRADERS
                     │
                     ▼
               SKILL DELTA
```

Where possible, both conditions should use the same:

* model
* agent harness
* task
* tools
* environment
* limits
* grader
* number of trials

The important difference is the presence of the skill.

## Skill Delta

The primary metric is intentionally simple.

```text
Skill Delta = Skill Score - Baseline Score
```

Example:

```text
Baseline     0.60
With Skill   0.85

Skill Delta +0.25
```

That means the skill improved measured performance by **25 percentage points on that benchmark**.

It does not mean the skill makes every agent 25% better.

Results belong to the exact model, harness, tasks, environment, skill version, and graders that produced them.

## Quick start

Requires Python 3.11 or newer.

Clone the repository:

```bash
git clone https://github.com/bybaochaule/skillablate.git
cd skillablate
```

Install:

```bash
python -m pip install -e .
```

Run the included deterministic smoke test:

```bash
skillablate run \
  examples/incident-triage/benchmark.yaml \
  --skill examples/incident-triage \
  --command "python examples/incident-triage/mock_agent.py" \
  --trials 3
```

SkillAblate will run every task in two conditions:

```text
baseline
skill
```

and print a comparison report.

## Why a command adapter first?

SkillAblate v0.1 deliberately does not depend on one model provider.

Any agent, CLI, wrapper, or test harness can participate if it can:

1. accept the task prompt from standard input
2. return its final answer through standard output
3. read `SKILLABLATE_SKILL_DIR` when a skill is enabled

For a baseline run:

```text
SKILLABLATE_SKILL_DIR=""
```

For a skill run:

```text
SKILLABLATE_SKILL_DIR="/path/to/skill"
```

This keeps the evaluation protocol separate from vendor-specific SDKs.

## Benchmark format

Example:

```yaml
schema_version: "0.1"

suite:
  id: incident-triage
  version: "0.1.0"
  description: >
    Tests classification under a fictional incident policy.

tasks:
  - id: checkout-outage

    prompt: |
      Classify this incident and return JSON.

      The production checkout database is unreachable.
      All customer purchases are failing.

    graders:
      - type: json_equals
        path: severity
        expected: P0
        weight: 1.0
```

## Supported graders

### `json_equals`

Checks a value inside a JSON response.

```yaml
- type: json_equals
  path: severity
  expected: P0
  weight: 1.0
```

### `regex`

Checks whether output matches a regular expression.

```yaml
- type: regex
  pattern: "P[0-3]"
  weight: 1.0
```

### `exact`

Checks the complete stripped output.

```yaml
- type: exact
  expected: PASS
  weight: 1.0
```

## Multiple graders

Tasks may use weighted graders.

```yaml
graders:
  - type: json_equals
    path: severity
    expected: P0
    weight: 0.8

  - type: regex
    pattern: "database|checkout"
    weight: 0.2
```

Task score:

```text
Σ(score × weight)
─────────────────
Σ(weight)
```

Each grader returns a score between `0` and `1`.

## Trials

AI agents are often non-deterministic.

SkillAblate therefore supports repeated trials:

```bash
skillablate run benchmark.yaml \
  --skill ./my-skill \
  --command "./run-agent" \
  --trials 5
```

Scores are aggregated across trials.

The deterministic example agent exists only to test SkillAblate itself.

It is not presented as evidence about any real AI model.

## Evidence

Each run can be saved as JSON:

```bash
skillablate run \
  examples/incident-triage/benchmark.yaml \
  --skill examples/incident-triage \
  --command "python examples/incident-triage/mock_agent.py" \
  --trials 3 \
  --output result.json
```

The output records:

```text
suite
task
condition
trial
raw response
grader scores
task score
errors
skill path
command
```

Future versions will add richer run manifests including model identifiers, tool events, token usage, latency, environment fingerprints, and skill hashes.

## What SkillAblate does not claim

SkillAblate does not certify that a skill is universally good.

It does not create a universal "Skill Quality Score."

It does not rank model providers.

It does not treat an agent's statement that it succeeded as proof of success.

It does not hide negative results.

A skill that produces no improvement is still a useful experimental result.

## Current status

**Pre-alpha — v0.1 measurement core**

The first goal is to make the experiment understandable and reproducible.

Current scope:

```text
✓ SKILL.md treatment condition
✓ baseline condition
✓ YAML benchmark suites
✓ repeated trials
✓ deterministic graders
✓ generic command adapter
✓ JSON evidence
✓ comparison reports
✓ automated tests
```

Not yet implemented:

```text
○ OpenAI/Codex adapter
○ Claude/Claude Code adapter
○ Gemini adapter
○ tool-event normalization
○ confidence intervals
○ regression thresholds
○ GitHub PR reporting
○ public benchmark packs
```

## Roadmap

### v0.1 — Core protocol

Stable benchmark format, paired experiments, deterministic graders, evidence output, tests.

### v0.2 — Agent adapters

Reference integrations for major agent environments.

### v0.3 — Statistical evaluation

Variance, confidence intervals, repeated-run analysis, and regression detection.

### v0.4 — CI integration

Run skill evaluations automatically when skills or agent systems change.

### v0.5 — Community benchmark packs

Reusable public test suites for common Agent Skill capabilities.

## Research integrity

SkillAblate should make it harder—not easier—to exaggerate AI evaluation results.

Contributors should:

* publish the tested conditions
* preserve failures
* avoid cherry-picking successful trials
* disclose model and harness versions
* use deterministic graders where possible
* disclose model-based graders when used
* separate measured evidence from interpretation

Sponsor funding must never buy favorable benchmark results.

## Contributing

Contributions are welcome.

Useful contributions include:

```text
benchmark tasks
graders
agent adapters
reproducibility improvements
failure analysis
statistics
documentation
tests
security review
```

Opening a small issue with a reproducible example is valuable even if you do not have a pull request.

## Long-term goal

Agent Skills are becoming reusable infrastructure.

SkillAblate's goal is to help the ecosystem answer a basic engineering question:

> **Did this skill actually improve the agent?**

If the answer can be measured reproducibly, skills can evolve from interesting instruction files into tested software artifacts.

## License

Apache License 2.0
