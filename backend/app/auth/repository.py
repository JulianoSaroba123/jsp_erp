"""
Repositório de dados para User.
Camada de acesso a dados (DAO) que encapsula queries SQLAlchemy.
"""
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user import User


class UserRepository:
    """
    Repositório estático para operações de banco de dados relacionadas a User.
    
    Segue o padrão Repository, isolando a lógica de acesso a dados
    da lógica de negócio (Service).
    """
    
    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        """
        Busca usuário por email.
        
        Args:
            db: Sessão do SQLAlchemy
            email: Email do usuário (case-insensitive)
            
        Returns:
            User ou None se não encontrado
            
        Example:
            >>> user = UserRepository.get_by_email(db, "admin@jsp.com")
        """
        stmt = select(User).where(User.email == email.lower().strip())
        return db.scalar(stmt)
    
    @staticmethod
    def get_by_id(db: Session, user_id: uuid.UUID) -> User | None:
        """
        Busca usuário por ID (UUID).
        
        Args:
            db: Sessão do SQLAlchemy
            user_id: UUID do usuário
            
        Returns:
            User ou None se não encontrado
            
        Example:
            >>> user = UserRepository.get_by_id(db, uuid.UUID("..."))
        """
        return db.get(User, user_id)
    
    @staticmethod
    def create(db: Session, user: User) -> User:
        """
        Cria um novo usuário no banco de dados.
        
        Args:
            db: Sessão do SQLAlchemy
            user: Instância de User a ser persistida
            
        Returns:
            User criado com ID gerado
            
        Example:
            >>> user = User(email="test@jsp.com", password_hash="...", name="Test")
            >>> created = UserRepository.create(db, user)
        """
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def get_all_active(db: Session) -> list[User]:
        """
        Retorna todos os usuários ativos.
        
        Args:
            db: Sessão do SQLAlchemy
            
        Returns:
            Lista de usuários ativos
        """
        stmt = select(User).where(User.is_active == True).order_by(User.created_at.desc())
        return list(db.scalars(stmt))
    
    @staticmethod
    def update(db: Session, user: User) -> User:
        """
        Atualiza um usuário existente.
        
        Args:
            db: Sessão do SQLAlchemy
            user: Instância de User com alterações
            
        Returns:
            User atualizado
        """
        db.commit()
        db.refresh(user)
        return user
