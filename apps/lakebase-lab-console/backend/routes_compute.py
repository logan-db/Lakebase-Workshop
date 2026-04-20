"""Compute / autoscaling management routes."""

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.postgres import Endpoint, EndpointSpec, FieldMask

router = APIRouter(prefix="/api/compute", tags=["compute"])


def _get_project_id() -> str:
    pid = os.getenv("LAKEBASE_PROJECT_ID")
    if not pid:
        raise HTTPException(500, "LAKEBASE_PROJECT_ID not configured")
    return pid


class EndpointInfo(BaseModel):
    name: str
    branch_id: str
    endpoint_type: str | None = None
    state: str | None = None
    host: str | None = None
    min_cu: float | None = None
    max_cu: float | None = None
    scale_to_zero_seconds: int | None = None


class UpdateComputeRequest(BaseModel):
    min_cu: float = Field(..., ge=0.5, le=32)
    max_cu: float = Field(..., ge=0.5, le=32)


@router.get("/{branch_id}", response_model=list[EndpointInfo])
def list_endpoints(branch_id: str):
    """List compute endpoints for a branch."""
    w = WorkspaceClient()
    project_id = _get_project_id()
    endpoints = list(
        w.postgres.list_endpoints(
            parent=f"projects/{project_id}/branches/{branch_id}"
        )
    )

    result = []
    for ep in endpoints:
        detail = w.postgres.get_endpoint(name=ep.name)
        s = detail.status
        result.append(EndpointInfo(
            name=detail.name,
            branch_id=branch_id,
            endpoint_type=str(getattr(s, "endpoint_type", "")) if s else None,
            state=str(getattr(s, "current_state", "")) if s else None,
            host=getattr(s.hosts, "host", None) if s and s.hosts else None,
            min_cu=getattr(s, "autoscaling_limit_min_cu", None) if s else None,
            max_cu=getattr(s, "autoscaling_limit_max_cu", None) if s else None,
        ))
    return result


@router.patch("/{branch_id}/{endpoint_id}", response_model=EndpointInfo)
def update_compute(branch_id: str, endpoint_id: str, req: UpdateComputeRequest):
    """Update autoscaling limits for a compute endpoint."""
    if req.max_cu - req.min_cu > 8:
        raise HTTPException(
            400,
            f"Autoscaling range too wide: {req.max_cu - req.min_cu} CU "
            f"(max spread is 8 CU)"
        )

    w = WorkspaceClient()
    project_id = _get_project_id()
    ep_name = f"projects/{project_id}/branches/{branch_id}/endpoints/{endpoint_id}"

    try:
        w.postgres.update_endpoint(
            name=ep_name,
            endpoint=Endpoint(
                name=ep_name,
                spec=EndpointSpec(
                    autoscaling_limit_min_cu=req.min_cu,
                    autoscaling_limit_max_cu=req.max_cu,
                ),
            ),
            update_mask=FieldMask(
                field_mask=[
                    "spec.autoscaling_limit_min_cu",
                    "spec.autoscaling_limit_max_cu",
                ]
            ),
        ).wait()
    except Exception as e:
        raise HTTPException(400, str(e))

    detail = w.postgres.get_endpoint(name=ep_name)
    s = detail.status
    return EndpointInfo(
        name=detail.name,
        branch_id=branch_id,
        endpoint_type=str(getattr(s, "endpoint_type", "")) if s else None,
        state=str(getattr(s, "current_state", "")) if s else None,
        host=getattr(s.hosts, "host", None) if s and s.hosts else None,
        min_cu=getattr(s, "autoscaling_limit_min_cu", None) if s else None,
        max_cu=getattr(s, "autoscaling_limit_max_cu", None) if s else None,
    )
