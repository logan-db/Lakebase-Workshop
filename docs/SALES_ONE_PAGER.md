# Lakebase Workshop

**Production Postgres, inside the Lakehouse — proven by your team in a single afternoon.**

A facilitator-led, hands-on workshop where your technical team stands up a real Databricks Lakebase Autoscaling database in their own workspace, then completes role-based labs that exercise every capability that matters for production: branching, autoscaling, reverse ETL, online feature serving, agent memory, OAuth-only auth, point-in-time recovery, and a deployed full-stack app.

By the end, your team has a working reference architecture and a defensible point of view on whether Lakebase replaces the operational Postgres infrastructure they manage today.

---

## What it is

A **2.5-hour facilitated workshop** (90- and 60-minute variants available) delivered by a Databricks Solutions Architect. Each participant provisions their own Lakebase project from a setup notebook, then works through 9 self-contained labs grouped into three role-based tracks. All labs are available two ways — as Databricks notebooks for engineers who want code, and as pages inside a deployed Lab Console web app for engineers who prefer a visual workbench. Participants can switch between them at any time.

Everything runs inside the customer's own Databricks workspace. No external services, no separate accounts, no data leaves the workspace.

---

## Why it matters

| Today                                                                     | With Lakebase                                                                |
| ------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Self-managed Postgres for apps, agents, and ML serving                    | Fully-managed Postgres provisioned in minutes, inside the workspace          |
| Brittle, hand-built reverse-ETL pipelines from the Lakehouse to OLTP      | Native synced tables from Delta Lake with Change Data Feed                   |
| A separate online feature store with its own infra and SLAs               | Online feature store **is** Lakebase — one engine, one bill                  |
| Static passwords, manual rotation, no Unity Catalog governance            | OAuth-only credentials, 1-hour TTL, Unity Catalog-governed identities        |
| Heavy dev/test environments cloned by hand, paid for 24/7                 | Git-like branches with copy-on-write and scale-to-zero — dev costs nothing idle |
| Custom backup orchestration and hours-long restores                       | Always-on PITR with 35-day window; restore by branching from a snapshot     |
| Bespoke agent memory store, separate from the rest of the platform        | Persistent agent memory using the same Lakebase your app already uses        |

The workshop is structured to let your team prove each of these claims on their own data, in their own workspace, in a single session.

---

## Who it's for

**Buyers (this document):** VPs of Data, CTOs, Heads of Platform, and Heads of AI Engineering evaluating whether to consolidate operational Postgres onto Databricks. You decide whether to run this with your team.

**Participants in the room (5–30 engineers):**

| Track                     | Role                                                | What they care about                                              |
| ------------------------- | --------------------------------------------------- | ----------------------------------------------------------------- |
| **Application Builders**  | App developers, AI engineers                        | CRUD, JSONB, transactions, agent memory, deploying a real app    |
| **Data & ML Engineers**   | Data engineers, ML platform teams                   | Delta → Postgres sync, online feature serving, observability     |
| **Platform Architects**   | Central IT, infrastructure, security, FinOps        | Branching, autoscaling, OAuth, backup/restore, cost control      |

Tracks are facilitation guides, not silos — every lab is independent and participants can mix and match.

---

## What they leave with

1. **A working Lakebase project** in their own workspace, with seeded sample data, ready to keep using after the session.
2. **Hands-on muscle memory** across CRUD + JSONB, branching + autoscaling, reverse ETL, online features, agent memory, OAuth, observability, and PITR — the full surface area of Lakebase.
3. **A deployed full-stack reference app** (React + FastAPI + Lakebase, on Databricks Apps) that demonstrates the production pattern: shared app, per-user routing, Service Principal auth, postgres OAuth scope.
4. **A defensible evaluation point of view** — enough hands-on experience to credibly answer *"can Lakebase replace what we run today?"* without a follow-up POC cycle.
5. **A repo and runbook** they can re-run on their own to onboard the next team.

---

## Logistics

| Item                  | Detail                                                                                          |
| --------------------- | ----------------------------------------------------------------------------------------------- |
| **Duration**          | 2.5 hours (multi-track) — 90-min and 60-min variants also supported                             |
| **Format**            | Facilitator-led, in person or virtual. Self-paced after the session.                            |
| **Capacity**          | 5–30 engineers per session; scales freely since each participant has their own isolated DB     |
| **Facilitator**       | Databricks Solutions Architect (or trained customer champion using the included Facilitator Guide) |
| **Prerequisites (customer)** | Databricks workspace with Lakebase Autoscaling enabled; participants on Python 3.11+ laptops |
| **Prep time**         | Facilitator: ~30 min to clone the repo and deploy the Lab Console once. Participants: zero before the day |
| **Cost (Databricks)** | Each Lakebase project runs at minimum CU during the session. Branches scale to zero between exercises. Typical workshop spend per participant is negligible. |
| **Data**              | All workshop data is synthetic and seeded by the setup notebook. No customer data required.    |
| **Cleanup**           | A single cell in the setup notebook deletes each participant's project. Branches with TTLs auto-expire. |

---

## Agenda — 2.5 hour multi-track session

| Time          | Activity                                                                                    |
| ------------- | ------------------------------------------------------------------------------------------- |
| 0:00 – 0:15   | **Introduction** — what is Lakebase, where it fits in the Lakehouse, architecture overview |
| 0:15 – 0:30   | **Setup** — clone repo, run `setup.sh`, authenticate, deploy bundle                         |
| 0:30 – 0:45   | **Foundation** — every participant runs `00_Setup_Lakebase_Project` to create their project |
| 0:45 – 1:45   | **Track Time** — participants follow their role-based track (3 labs each)                  |
| 1:45 – 2:15   | **Cross-Track Exploration** — try a lab from another track                                  |
| 2:15 – 2:30   | **Wrap-up** — App Deployment overview, Q&A, next steps                                      |

90-minute and 60-minute variants are available in the Facilitator Guide for tighter sessions.

---

## What the 9 labs cover

| Lab                          | Track    | What participants prove                                                                            |
| ---------------------------- | -------- | -------------------------------------------------------------------------------------------------- |
| Data Operations              | App      | Full Postgres semantics — JSONB, arrays, triggers, transactions, audit logs                        |
| Agentic Memory               | App      | Persistent short- and long-term memory for AI agents on the same Lakebase as the app               |
| App Deployment *(capstone)*  | App      | A shared React + FastAPI app on Databricks Apps, with per-user routing and SP-based DB credentials |
| Reverse ETL                  | Data/ML  | Native Delta → Lakebase sync with CDF, in snapshot / triggered / continuous modes                  |
| Online Feature Store         | Data/ML  | A Databricks online feature store that *is* a Lakebase Autoscaling instance — one engine for ML serving |
| Observability                | Data/ML  | `pg_stat_*`, index usage, connection inspection, workspace monitoring UI                           |
| Development Experience       | Platform | Git-like database branching with TTLs; autoscaling 0.5–112 CU; scale-to-zero for non-prod branches |
| Authentication               | Platform | OAuth tokens with 1-hour TTL, decoded JWTs, two-layer permission model, no static passwords        |
| Backup & Recovery            | Platform | Snapshot branches, point-in-time recovery, instant restore via branching from any past moment     |

---

## Business outcomes for the buyer

- **Consolidation.** Operational Postgres, online feature store, and agent memory collapse into one managed service governed by Unity Catalog — fewer vendors, fewer integrations, one bill.
- **Faster app delivery.** Developers stop waiting on DBA-provisioned environments. Branches are instant; dev costs nothing when idle.
- **Lower TCO on dev/test.** Copy-on-write branches and scale-to-zero replace the typical 24/7 spend on non-prod replicas.
- **Stronger security posture.** OAuth-only access with short-lived tokens, identities governed by the same Unity Catalog policies as the rest of the Lakehouse.
- **Faster RPO/RTO.** Always-on PITR and instant branch-based recovery replace hours-long restore workflows.
- **Confident decisions.** Your team validates Lakebase against the workloads they actually run, in a single session, without sales pressure.

---

## Why this workshop, not a slide deck

The labs are intentionally adversarial: they walk participants through the things that *would* break a less-mature managed Postgres — sync semantics, JWT rotation, scale-to-zero cold starts, recovery RTO, CU sizing — and prove they don't. By the end of the session, your team has done the work, not watched it.

---

## Next steps

1. **Pick a date and audience.** A typical engagement is 8–20 engineers from the app, data, and platform teams.
2. **Confirm the workspace.** Your Databricks Solutions Architect will validate that Lakebase Autoscaling is enabled and that participants have the right permissions.
3. **Run it.** The facilitator handles all prep. Your team shows up on the day with laptops.

To schedule, contact your Databricks Account Team or Solutions Architect.

---

*Workshop repo: `Lakebase-Workshop` · Facilitator Guide: [docs/WORKSHOP_FACILITATOR.md](WORKSHOP_FACILITATOR.md) · Permissions model: [docs/PERMISSIONS.md](PERMISSIONS.md)*
