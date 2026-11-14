from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserRead
from app.api.deps import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("", response_model=List[UserRead])
async def list_users(
    search: Optional[str] = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(User).where(User.is_active == True)
    if search:
        stmt = stmt.where(
            or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
        )
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    users = result.scalars().all()
    return [UserRead.model_validate(u) for u in users]
