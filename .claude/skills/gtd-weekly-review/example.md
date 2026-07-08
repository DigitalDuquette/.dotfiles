# Weekly Review Example

This example demonstrates the structure and tone of the weekly review
output. Adapt the content and length based on the actual daily notes.

The Team Update models the leadership-requested style: one-line
preamble, short fragment bullets (not sentences), theme-level
summaries. Bullet count is flexible; density per bullet is not.
Decisions, blockers, and upcoming focus are single bullets. Detail
lives in the linked notes and the Daily Note Review, not the update.

```md
# Week 27, 2026

## Team Update

Short holiday week, almost all of it on the inspection app image outage
— from "nobody can quantify it" to a shipped fix and numbers trending
down.

- 8 PRs merged across 4 repos, mostly inspection image outage
  ([[2-areas/reviews/dev-activity/DigitalDuquette/2026-W27|full PR list]])
- Audit dashboard now quantifies missing app images
- App fix 2.15.4 live Thursday — miss rate already dropping
- Production-tracking data drops fixed (orchestration moved to SQL
  Agent job)
- Scale touch screen API: stubs up, TCP weights reading, MVP endpoints
  on track for end of July
- Scheduled receiver rewrite staged — deploy next week
- AG5 vendor call: Advanced Analytics API confirmed deprecated, vendor
  committed to data fix + transition meeting
- Inspection reporting reconciliation started with Nate — greenfielding
  the queue business rules
- Decision: Container Vision AI is the Q3 AI project (Ernie + Bob)
- Next week: monitor image fix, scale API stubs, receiver rewrite
  deploy

---

## Private Notes

Vendor friction: documented two more SLG failures (scale config
mismatch, dead in-motion flag); the accountability file keeps growing
and feeds the larger vendor conversation.

Team: new hire ramping impressively fast; another team member got the
project-list-hygiene feedback again — watch whether it sticks. Unlike
the Team Update, this section stays as detailed as it needs to be.

---

## Action Items for Fresh

- [ ] Monitor missing-image count post-2.15.4; confirm inspectors are on
      the latest app version
- [ ] Deliver scale API stubs to Post Industria; core MVP endpoints by
      end of July
- [ ] Final testing + deploy of the scheduled receiver rewrite next week
- [ ] Review queued PRs (incl. the 18-file warehouse pipeline PR)

---

## Meeting Log

See [[2026-W27-meetings]] for the detailed meeting log.

---

## Daily Note Review

### Tuesday, June 30

- Worked the SR pipeline: making the vehicle-to-RIMAS record 1-to-1.
- Set up the inspection image audit dashboard showing missing images
  since the new inspection table started.

### Thursday, July 2

- Dashboarding to support the inspection outage; waiting to see whether
  the new app version fixes the issue.
- Completed more scheduled receiver rewrite work; staged and ready for
  final testing and deploy next week.

This section stays detailed — it is the searchable archive; only the
Team Update is length-capped.
```
