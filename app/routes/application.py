from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.db_client import DBClient
from app.core.database import get_session
from app.core.security import get_current_user
from app.models.application import ApplicationStatus
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["Application"], dependencies=[Depends(get_current_user)])


@router.patch("/{application_id}", response_model=Dict[str, Any])
async def update_application_status(
    application_id: UUID,
    application_status: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Update an application by ID.

    :param application_id: ID of the application.
    :param application_status: New status of the application.
    :return: Updated application data.
    """
    db = DBClient(session)
    # Validate the application status with the ApplicationStatus enum
    if application_status not in ApplicationStatus._value2member_map_:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid application status: {application_status}"
        )

    updated = await db.update_table_entry(
        "applications",
        identifier={"id": str(application_id)},
        update_data={"status": application_status}
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found or update failed"
        )
    return updated