# Agentic Memory

Use Lakebase as persistent memory for AI agents — store conversation history, session state, and cross-session context.

## Labs

| Lab | What You'll Learn |
|-----|-------------------|
| `Agent_Memory` | Create sessions, store multi-turn conversations, query history, cross-session JSONB queries |

## Prerequisites

- Complete **`00_Setup_Lakebase_Project`** (foundation — seeds the `agent_sessions` and `agent_messages` tables)

## Key Concepts

- **Session/message pattern** — Relational schema for multi-turn agent conversations
- **JSONB metadata** — Store arbitrary context per session and message
- **Cross-session queries** — Find patterns across all agent conversations using SQL
- **No extra infrastructure** — Use the same Lakebase instance your app already connects to
