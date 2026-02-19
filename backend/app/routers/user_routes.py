"""
Router de User
Responsabilidade: receber requests HTTP e chamar services
NÃO contém lógica de negócio nem queries SQL
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.services.user_service import UserService
from app.schemas.user_schema import UserCreate, UserUpdate, UserResponse
from app.security.password import hash_password
from app.security.deps import get_db


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=dict)
def list_users(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """Lista usuários com paginação"""
    service = UserService(db)
    result = service.list_users(page=page, page_size=page_size)
    
    # Converte para response schema
    return {
        "items": [UserResponse.model_validate(user) for user in result["items"]],
        "page": result["page"],
        "page_size": result["page_size"],
        "total": result["total"]
    }


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    """Busca usuário por ID"""
    service = UserService(db)
    user = service.get_user_by_id(user_id)
    return UserResponse.model_validate(user)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Cria novo usuário"""
    service = UserService(db)
    
    # Hash da senha (security layer)
    password_hash = hash_password(user_data.password)
    
    user = service.create_user(user_data, password_hash)
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: UUID, user_data: UserUpdate, db: Session = Depends(get_db)):
    """Atualiza usuário"""
    service = UserService(db)
    user = service.update_user(user_id, user_data)
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: UUID, db: Session = Depends(get_db)):
    """Deleta usuário"""
    service = UserService(db)
    service.delete_user(user_id)
    return None
