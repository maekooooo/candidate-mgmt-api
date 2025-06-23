from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_client import DBClient
from app.core.database import get_session
from app.core.security import get_current_user
from app.models.application import ApplicationStatus


router = APIRouter(tags=["Candidate"], dependencies=[Depends(get_current_user)])


@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_candidate(
    payload: Dict[str, Any],
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new candidate.
    """
    db = DBClient(session)
    created = await db.create_table_entry("candidates", payload)
    if not created:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create candidate"
        )
    return created


@router.get("/", response_model=List[Dict[str, Any]])
async def list_candidates(
    skill: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    session: AsyncSession = Depends(get_session),
):
    """
    List candidates, optionally filtered by skill.
    """
    db = DBClient(session)
    filters = {"skills": skill} if skill else None
    results = await db.query_table_data("candidates", filters=filters, limit=limit, offset=offset)
    return results


@router.get("/{candidate_id}", response_model=Dict[str, Any])
async def get_candidate_by_id(
    candidate_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Retrieve a single candidate by ID.
    """
    db = DBClient(session)
    result = await db.query_table_data(
        "candidates",
        filters={"id": str(candidate_id)},
        single_row=True
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    return result

@router.put("/{candidate_id}", response_model=Dict[str, Any])
async def update_candidate(
    candidate_id: UUID,
    payload:      Dict[str, Any],
    session: AsyncSession = Depends(get_session),
):
    """
    Update an existing candidate.
    """
    db = DBClient(session)
    updated = await db.update_table_entry(
        "candidates",
        identifier={"id": str(candidate_id)},
        update_data=payload
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found or update failed"
        )
    return updated


# -- Nested application routes ------------------------------------------------
@router.post("/{candidate_id}/applications", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_application(
    candidate_id: UUID,
    payload:      Dict[str, Any],
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new application for a candidate.
    """
    db = DBClient(session)
    # ensure the FK is set
    data = {**payload, "candidate_id": str(candidate_id)}
    created = await db.create_table_entry("applications", data)
    if not created:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create application"
        )
    return created

@router.get("/{candidate_id}/applications", response_model=List[Dict[str, Any]])
async def list_applications_for_candidate(
    candidate_id: UUID,
    status: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """
    List all applications for a given candidate.
    """
    db = DBClient(session)
    
    # Validate status if provided
    if status and status not in ApplicationStatus._value2member_map_:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid application status: {status}"
        )
    results = await db.query_table_data(
        "applications",
        filters={"candidate_id": str(candidate_id), "status": status} if status else {"candidate_id": str(candidate_id)}
    )
    return results
