"""
Service para User - lógica de negócio
"""
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Dict

from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user_schema import UserCreate, UserUpdate
from app.exceptions.errors import NotFoundError, ConflictError


class UserService:
    """Service com regras de negócio para User"""
    
    def __init__(self, db: Session):
        self.repo = UserRepository(db)
    
    def get_user_by_id(self, user_id: UUID) -> User:
        """Busca usuário por ID (lança exceção se não encontrado)"""
        user = self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"Usuário com ID {user_id} não encontrado")
        return user
    
    def get_user_by_email(self, email: str) -> User:
        """Busca usuário por email"""
        user = self.repo.get_by_email(email)
        if not user:
            raise NotFoundError(f"Usuário com email {email} não encontrado")
        return user
    
    def list_users(self, page: int = 1, page_size: int = 20) -> Dict:
        """
        Lista usuários com paginação
        Retorna dict com items, page, page_size, total
        """
        skip = (page - 1) * page_size
        users = self.repo.get_all(skip=skip, limit=page_size)
        total = self.repo.count()
        
        return {
            "items": users,
            "page": page,
            "page_size": page_size,
            "total": total
        }
    
    def create_user(self, user_data: UserCreate, password_hash: str) -> User:
        """
        Cria novo usuário
        Valida se email já existe (conflito)
        password_hash: já deve vir hasheado do security layer
        """
        # Validação: email único
        existing_user = self.repo.get_by_email(user_data.email)
        if existing_user:
            raise ConflictError(f"Email {user_data.email} já está em uso")
        
        # Cria entidade
        user = User(
            name=user_data.name,
            email=user_data.email,
            password_hash=password_hash,  # Já vem hasheado
            role=user_data.role
        )
        
        return self.repo.create(user)
    
    def update_user(self, user_id: UUID, user_data: UserUpdate) -> User:
        """Atualiza usuário existente"""
        user = self.get_user_by_id(user_id)
        
        # Validação: se alterou email, verificar se novo email já existe
        if user_data.email and user_data.email != user.email:
            existing = self.repo.get_by_email(user_data.email)
            if existing:
                raise ConflictError(f"Email {user_data.email} já está em uso")
        
        # Atualiza apenas campos fornecidos
        if user_data.name is not None:
            user.name = user_data.name
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.role is not None:
            user.role = user_data.role
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        
        return self.repo.update(user)
    
    def delete_user(self, user_id: UUID) -> None:
        """Deleta usuário"""
        user = self.get_user_by_id(user_id)
        self.repo.delete(user)
