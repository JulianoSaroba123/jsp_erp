"""
Serviço de autenticação.
Camada de lógica de negócio para registro, login e validações de usuário.
"""
from sqlalchemy.orm import Session

from app.models.user import User
from .repository import UserRepository
from .security import hash_password, verify_password


class AuthService:
    """
    Serviço estático para operações de autenticação.
    
    Contém toda a lógica de negócio relacionada a registro,
    login e validação de credenciais.
    """
    
    @staticmethod
    def register(
        db: Session, 
        email: str, 
        password: str, 
        name: str,
        role: str = "user"
    ) -> User:
        """
        Registra um novo usuário no sistema.
        
        Args:
            db: Sessão do SQLAlchemy
            email: Email do novo usuário (será normalizado para lowercase)
            password: Senha em texto plano (será hasheada com bcrypt)
            name: Nome completo do usuário
            role: Papel do usuário (default: "user")
            
        Returns:
            User criado
            
        Raises:
            ValueError: Se o email já estiver cadastrado ou senha for fraca
            
        Example:
            >>> user = AuthService.register(db, "novo@jsp.com", "senha123", "Novo Usuário")
        """
        # Validar email único
        email_normalized = email.lower().strip()
        if UserRepository.get_by_email(db, email_normalized):
            raise ValueError("E-mail já cadastrado.")
        
        # Validar senha (mínimo 6 caracteres)
        if len(password) < 6:
            raise ValueError("Senha deve ter no mínimo 6 caracteres.")
        
        # Validar nome
        if not name or len(name.strip()) < 3:
            raise ValueError("Nome deve ter no mínimo 3 caracteres.")
        
        # Validar role
        valid_roles = ["admin", "user", "technician", "finance"]
        if role not in valid_roles:
            raise ValueError(f"Role inválido. Use: {', '.join(valid_roles)}")
        
        # Criar usuário
        user = User(
            email=email_normalized,
            password_hash=hash_password(password),
            name=name.strip(),
            role=role,
            is_active=True
        )
        
        return UserRepository.create(db, user)
    
    @staticmethod
    def authenticate(db: Session, email: str, password: str) -> User:
        """
        Autentica um usuário com email e senha.
        
        Args:
            db: Sessão do SQLAlchemy
            email: Email do usuário
            password: Senha em texto plano
            
        Returns:
            User autenticado
            
        Raises:
            ValueError: Se credenciais forem inválidas ou usuário inativo
            
        Example:
            >>> user = AuthService.authenticate(db, "admin@jsp.com", "123456")
        """
        email_normalized = email.lower().strip()
        
        # Buscar usuário
        user = UserRepository.get_by_email(db, email_normalized)
        
        # Validar credenciais
        if not user:
            raise ValueError("Credenciais inválidas.")
        
        if not verify_password(password, user.password_hash):
            raise ValueError("Credenciais inválidas.")
        
        # Validar usuário ativo
        if not user.is_active:
            raise ValueError("Usuário inativo. Contate o administrador.")
        
        return user
    
    @staticmethod
    def change_password(
        db: Session, 
        user: User, 
        old_password: str, 
        new_password: str
    ) -> User:
        """
        Altera a senha de um usuário.
        
        Args:
            db: Sessão do SQLAlchemy
            user: Usuário que terá a senha alterada
            old_password: Senha atual (para validação)
            new_password: Nova senha
            
        Returns:
            User com senha atualizada
            
        Raises:
            ValueError: Se senha atual estiver incorreta ou nova senha for fraca
        """
        # Verificar senha atual
        if not verify_password(old_password, user.password_hash):
            raise ValueError("Senha atual incorreta.")
        
        # Validar nova senha
        if len(new_password) < 6:
            raise ValueError("Nova senha deve ter no mínimo 6 caracteres.")
        
        # Atualizar senha
        user.password_hash = hash_password(new_password)
        return UserRepository.update(db, user)
