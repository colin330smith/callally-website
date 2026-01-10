"""
Authentication Router - Signup, Login, User Info
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4

from database.connection import get_db
from database.models import User, Business
from services.auth_service import AuthService
from middleware.auth_middleware import get_current_user
from schemas.auth import (
    SignupRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    UserWithBusinessesResponse,
    BusinessSummary
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/signup", response_model=TokenResponse)
async def signup(request: SignupRequest, db: AsyncSession = Depends(get_db)):
    """
    Create a new user account and business.
    Returns JWT token and business_id.
    """
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == request.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    user = User(
        id=uuid4(),
        email=request.email,
        password_hash=AuthService.hash_password(request.password)
    )
    db.add(user)
    await db.flush()

    # Create business
    business = Business(
        id=uuid4(),
        user_id=user.id,
        name=request.business_name,
        notification_email=request.email,
        onboarding_step=1
    )
    db.add(business)
    await db.commit()

    # Generate token
    token = AuthService.create_access_token(str(user.id))

    return TokenResponse(
        access_token=token,
        business_id=business.id
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    """
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user or not AuthService.verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    # Get first business for convenience
    result = await db.execute(
        select(Business).where(Business.user_id == user.id).limit(1)
    )
    business = result.scalar_one_or_none()

    token = AuthService.create_access_token(str(user.id))

    return TokenResponse(
        access_token=token,
        business_id=business.id if business else None
    )


@router.get("/me", response_model=UserWithBusinessesResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user info with their businesses.
    """
    result = await db.execute(
        select(Business).where(Business.user_id == current_user.id)
    )
    businesses = result.scalars().all()

    return UserWithBusinessesResponse(
        user=UserResponse.model_validate(current_user),
        businesses=[BusinessSummary.model_validate(b) for b in businesses]
    )


@router.post("/logout")
async def logout():
    """
    Logout endpoint (client should discard token).
    JWT tokens are stateless, so we just return success.
    """
    return {"message": "Logged out successfully"}
