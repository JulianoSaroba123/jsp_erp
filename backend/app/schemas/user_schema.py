"""
Schemas Pydantic para User
NUNCA expor password_hash em ResponseSchema
"""
from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    """Schema para criação de usuário"""
    name: str
    email: EmailStr
    password: str  # Senha em texto plano (será hasheada no service)
    role: str = "user"  # Default: user


class UserUpdate(BaseModel):
    """Schema para atualização de usuário (todos campos opcionais)"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Schema de resposta de usuário (NUNCA retorna password_hash)"""
    id: UUID
    name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """Schema para login"""
    email: EmailStr
    password: str
