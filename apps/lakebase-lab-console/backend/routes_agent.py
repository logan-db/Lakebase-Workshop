"""Agent memory lab routes: session & message CRUD."""

import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .db import execute_query, execute_write

router = APIRouter(prefix="/api/agent", tags=["agent"])


class CreateSessionRequest(BaseModel):
    agent_name: str = Field(default="lab-agent", min_length=1)
    metadata: dict = {}


class AppendMessageRequest(BaseModel):
    role: str = Field(..., pattern=r"^(user|assistant|system|tool)$")
    content: str = Field(..., min_length=1)
    metadata: dict = {}


class SessionInfo(BaseModel):
    session_id: str
    agent_name: str
    metadata: dict
    created_at: str
    message_count: int = 0


@router.get("/sessions", response_model=list[SessionInfo])
def list_sessions(limit: int = 20):
    """List recent agent sessions with message counts."""
    rows = execute_query(
        """
        SELECT s.session_id, s.agent_name, s.metadata, s.created_at::text as created_at,
               COALESCE(m.cnt, 0) as message_count
        FROM demo.agent_sessions s
        LEFT JOIN (
            SELECT session_id, count(*) as cnt
            FROM demo.agent_messages
            GROUP BY session_id
        ) m ON s.session_id = m.session_id
        ORDER BY s.created_at DESC
        LIMIT %s
        """,
        (limit,),
    )
    return [SessionInfo(**r) for r in rows]


@router.post("/sessions", response_model=SessionInfo)
def create_session(req: CreateSessionRequest):
    """Create a new agent session."""
    session_id = str(uuid.uuid4())[:12]
    import json

    execute_write(
        "INSERT INTO demo.agent_sessions (session_id, agent_name, metadata) VALUES (%s, %s, %s)",
        (session_id, req.agent_name, json.dumps(req.metadata)),
    )
    return SessionInfo(
        session_id=session_id,
        agent_name=req.agent_name,
        metadata=req.metadata,
        created_at="now",
        message_count=0,
    )


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    """Delete a session and all its messages (cascading)."""
    result = execute_write(
        "DELETE FROM demo.agent_sessions WHERE session_id = %s", (session_id,)
    )
    if result[0].get("rowcount", 0) == 0:
        raise HTTPException(404, "Session not found")
    return {"status": "deleted", "session_id": session_id}


@router.get("/sessions/{session_id}/messages")
def get_messages(session_id: str):
    """Get all messages in a session, ordered chronologically."""
    return execute_query(
        """
        SELECT message_id, session_id, role, content, metadata,
               created_at::text as created_at
        FROM demo.agent_messages
        WHERE session_id = %s
        ORDER BY created_at ASC
        """,
        (session_id,),
    )


@router.post("/sessions/{session_id}/messages")
def append_message(session_id: str, req: AppendMessageRequest):
    """Append a message to a session."""
    import json

    sessions = execute_query(
        "SELECT 1 FROM demo.agent_sessions WHERE session_id = %s", (session_id,)
    )
    if not sessions:
        raise HTTPException(404, "Session not found")

    result = execute_write(
        "INSERT INTO demo.agent_messages (session_id, role, content, metadata) "
        "VALUES (%s, %s, %s, %s) RETURNING *",
        (session_id, req.role, req.content, json.dumps(req.metadata)),
    )

    execute_write(
        "UPDATE demo.agent_sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = %s",
        (session_id,),
    )

    return result
