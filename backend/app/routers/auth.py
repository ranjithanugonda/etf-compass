"""POST /api/auth/login — returns JWT token."""

from fastapi import APIRouter, HTTPException, status

from backend.app.auth import authenticate
from backend.app.schemas.admin import LoginRequest, LoginResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest) -> LoginResponse:
    token = authenticate(body.username, body.password)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    return LoginResponse(access_token=token)
