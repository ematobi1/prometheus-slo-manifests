# Postmortem: <incident title>

Blameless. Focus on systems and processes, not people.

| Field | Value |
|---|---|
| Date | YYYY-MM-DD |
| Authors | |
| Status | Draft / In review / Final |
| Services | |
| Severity | page / ticket |
| Duration | start (UTC) to end (UTC) |
| Error budget consumed | % of 30-day budget: failed requests during the incident divided by (error budget ratio x total requests over 30 days). Do not subtract budget-remaining readings; the rolling window also drops old errors. |

## Summary

Two or three sentences: what happened, who was affected, how it was resolved.

## Impact

Users and requests affected, failed request count, revenue or contractual impact.

## Timeline (UTC)

| Time | Event |
|---|---|
| | Trigger |
| | Alert fired |
| | Acknowledged |
| | Mitigated |
| | Resolved |

## Root cause

## Detection

Did the SLO alert fire? How long after impact started? Was it the right severity?

## Resolution and mitigation

## What went well

## What went poorly

## Action items

| Action | Type (prevent / detect / mitigate) | Owner | Issue | Due |
|---|---|---|---|---|
| | | | | |

File each action item as a GitHub issue in this repo or the owning service's repo.
