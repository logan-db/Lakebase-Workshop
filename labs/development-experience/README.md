# Development Experience

Explore Lakebase's developer-focused features: Git-like database branching and autoscaling serverless compute.

## Labs

| Order | Lab | What You'll Learn |
|-------|-----|-------------------|
| 1 | `Branches_and_Environments` | Create isolated dev branches, verify schema isolation, set branch TTLs |
| 2 | `Autoscaling_and_Compute` | Inspect CU ranges, resize endpoints, understand scale-to-zero |

## Prerequisites

- Complete **`00_Setup_Lakebase_Project`** (foundation)

## Key Concepts

- **Copy-on-write branching** — Instant, isolated database clones for dev/test/CI
- **Autoscaling compute** — 0.5–112 CU, scales automatically based on load
- **Scale-to-zero** — Non-production branches suspend when idle (no cost)
- **Branch TTL** — Auto-expire dev branches after a configurable duration

## Documentation

- [Branches](https://docs.databricks.com/aws/en/oltp/projects/branches)
- [Manage branches](https://docs.databricks.com/aws/en/oltp/projects/manage-branches)
- [Autoscaling](https://docs.databricks.com/aws/en/oltp/projects/autoscaling)
- [Scale to zero](https://docs.databricks.com/aws/en/oltp/projects/scale-to-zero)
- [Manage computes](https://docs.databricks.com/aws/en/oltp/projects/manage-computes)
