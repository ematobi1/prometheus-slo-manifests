# Error budget policy

Applies to every SLO in [`slos/`](../slos). Budget remaining is
`slo:period_error_budget_remaining:ratio` over the rolling 30-day window, shown on the
[SLO overview dashboard](../dashboards/slo-overview.json).

| Budget remaining | Action |
|---|---|
| More than 50% | Normal release cadence. |
| 25% to 50% | Releases need a tested rollback plan. Reliability work gets prioritized in the next sprint. |
| 0% to 25% | Only fixes and reliability changes ship. The owning team reviews open postmortem action items. |
| Exhausted (0% or below) | Feature freeze until the budget recovers above 0%, except security fixes. Service owner and engineering manager sign off on any exception. |

Any single incident that consumes more than 20% of the budget requires a postmortem
using the [postmortem template](postmortem-template.md), even if it did not page.

TODO: get this policy signed off by the service owners and engineering leadership.
