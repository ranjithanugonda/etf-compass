"""Pydantic models for admin endpoints."""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class StrategyParamUpdate(BaseModel):
    param_value: object


class SystemStatusUpdate(BaseModel):
    status: str  # "running" | "paused"
