---
name: incident-triage
description: Classifies operational incidents using the fictional SkillAblate severity policy. Use when asked to assign P0, P1, P2, or P3 severity to an operational incident.
license: Apache-2.0
metadata:
  version: "0.1.0"
  purpose: "skillablate-smoke-test"
---

# Incident Triage

Classify operational incidents using this fictional
severity policy.

## Severity policy

Use **P0** when a production incident prevents the primary
customer transaction for most or all customers.

Use **P1** when a production incident creates major
customer impact but the primary transaction remains
available to some customers.

Use **P2** when customer-facing functionality is degraded
but customers have a practical workaround.

Use **P3** when the impact is minor, internal-only,
informational, or does not materially prevent customers
from completing their work.

## Decision process

Identify the affected system.

Determine whether the impact is customer-facing.

Determine whether the primary customer transaction is:

1. unavailable,
2. partially available,
3. degraded with a practical workaround, or
4. unaffected.

Choose exactly one severity.

Do not increase severity merely because the incident
sounds urgent.

## Output

Return valid JSON:

```json
{
  "severity": "P0",
  "rationale": "Brief explanation."
}
