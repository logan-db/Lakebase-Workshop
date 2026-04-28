# Authentication & Permissions

Understand Lakebase's two-layer security model: workspace-level IAM and database-level PostgreSQL roles.

## Labs

| Lab | What You'll Learn |
|-----|-------------------|
| `Authentication_and_Permissions` | Generate OAuth tokens, inspect JWT claims, manage role grants, connect external tools |

## Prerequisites

- Complete **`00_Setup_Lakebase_Project`** (foundation)

## Key Concepts

- **Two-layer permissions** — Workspace IAM (who can access the project) + PostgreSQL roles (what they can do inside the database)
- **OAuth tokens** — 1-hour TTL, no static passwords, automatic rotation via the SDK
- **Role mapping** — Databricks identities map to PostgreSQL roles automatically

## Documentation

- [Authentication](https://docs.databricks.com/aws/en/oltp/projects/authentication)
- [Manage Postgres roles](https://docs.databricks.com/aws/en/oltp/projects/postgres-roles)
- [Manage permissions](https://docs.databricks.com/aws/en/oltp/projects/manage-roles-permissions)
- [Roles and permissions](https://docs.databricks.com/aws/en/oltp/projects/roles-permissions)
