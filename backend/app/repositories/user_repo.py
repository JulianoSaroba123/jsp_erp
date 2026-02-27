"""
Repository para User - acesso a dados (queries)
Camada de abstração do banco de dados
"""
from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from typing import Optional, List

from app.models.user import User
from app.models.role import Role


class UserRepository:
    """Repository para operações de banco com User"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Busca usuário por ID com roles e permissions carregadas (eager loading)"""
        return (
            self.db.query(User)
            .options(
                joinedload(User.roles).joinedload(Role.permissions)
            )
            .filter(User.id == user_id)
            .first()
        )
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Busca usuário por email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_all(self, skip: int = 0, limit: int = 20) -> List[User]:
        """Lista todos os usuários com paginação"""
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def count(self) -> int:
        """Conta total de usuários"""
        return self.db.query(User).count()
    
    def create(self, user: User) -> User:
        """Cria novo usuário"""
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update(self, user: User) -> User:
        """Atualiza usuário existente"""
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete(self, user: User) -> None:
        """Deleta usuário"""
        self.db.delete(user)
        self.db.commit()
