"""
Testes para UserService - Sprint 1 Coverage
Objetivo: 31% → 85% coverage
"""
import pytest
from uuid import uuid4
from sqlalchemy.orm import Session

from app.services.user_service import UserService
from app.schemas.user_schema import UserCreate, UserUpdate
from app.exceptions.errors import NotFoundError, ConflictError
from app.models.user import User


class TestUserServiceGet:
    """Testes de busca (get_user_by_id, get_user_by_email)"""
    
    def test_get_user_by_id_success(self, db_session: Session, seed_user_admin):
        """Deve retornar usuário quando ID existe"""
        service = UserService(db_session)
        user = service.get_user_by_id(seed_user_admin.id)
        
        assert user is not None
        assert user.id == seed_user_admin.id
        assert user.email == seed_user_admin.email
    
    def test_get_user_by_id_not_found(self, db_session: Session):
        """Deve lançar NotFoundError quando ID não existe"""
        service = UserService(db_session)
        fake_id = uuid4()
        
        with pytest.raises(NotFoundError) as exc:
            service.get_user_by_id(fake_id)
        
        assert str(fake_id) in str(exc.value)
        assert "não encontrado" in str(exc.value)
    
    def test_get_user_by_email_success(self, db_session: Session, seed_user_admin):
        """Deve retornar usuário quando email existe"""
        service = UserService(db_session)
        user = service.get_user_by_email("admin@test.com")
        
        assert user is not None
        assert user.email == "admin@test.com"
        assert user.role == "admin"
    
    def test_get_user_by_email_not_found(self, db_session: Session):
        """Deve lançar NotFoundError quando email não existe"""
        service = UserService(db_session)
        
        with pytest.raises(NotFoundError) as exc:
            service.get_user_by_email("inexistente@test.com")
        
        assert "inexistente@test.com" in str(exc.value)


class TestUserServiceList:
    """Testes de listagem (list_users)"""
    
    def test_list_users_default_pagination(self, db_session: Session, seed_user_admin, seed_user_normal):
        """Deve listar usuários com paginação padrão"""
        service = UserService(db_session)
        result = service.list_users()
        
        assert "items" in result
        assert "page" in result
        assert "page_size" in result
        assert "total" in result
        assert result["page"] == 1
        assert result["page_size"] == 20
        assert result["total"] >= 2
        assert len(result["items"]) >= 2
    
    def test_list_users_custom_pagination(self, db_session: Session, seed_user_admin, seed_user_normal):
        """Deve respeitar parâmetros de paginação customizados"""
        service = UserService(db_session)
        result = service.list_users(page=1, page_size=1)
        
        assert result["page"] == 1
        assert result["page_size"] == 1
        assert len(result["items"]) == 1
        assert result["total"] >= 2
    
    def test_list_users_second_page(self, db_session: Session, seed_user_admin, seed_user_normal):
        """Deve retornar segunda página corretamente"""
        service = UserService(db_session)
        result = service.list_users(page=2, page_size=1)
        
        assert result["page"] == 2
        assert result["page_size"] == 1
        assert len(result["items"]) >= 1


class TestUserServiceCreate:
    """Testes de criação (create_user)"""
    
    def test_create_user_success(self, db_session: Session):
        """Deve criar usuário com dados válidos"""
        service = UserService(db_session)
        user_data = UserCreate(
            name="Novo Usuário",
            email="novo@test.com",
            password="senha123",  # Será ignorado, usamos hash direto
            role="user"
        )
        
        user = service.create_user(user_data, password_hash="$2b$12$hashedpassword")
        
        assert user.id is not None
        assert user.name == "Novo Usuário"
        assert user.email == "novo@test.com"
        assert user.role == "user"
        assert user.password_hash == "$2b$12$hashedpassword"
        assert user.is_active is True  # Default
    
    def test_create_user_duplicate_email(self, db_session: Session, seed_user_admin):
        """Deve lançar ConflictError quando email já existe"""
        service = UserService(db_session)
        user_data = UserCreate(
            name="Duplicado",
            email="admin@test.com",  # Email já existe
            password="senha123",
            role="user"
        )
        
        with pytest.raises(ConflictError) as exc:
            service.create_user(user_data, password_hash="$2b$12$hash")
        
        assert "admin@test.com" in str(exc.value)
        assert "já está em uso" in str(exc.value)
    
    def test_create_user_with_admin_role(self, db_session: Session):
        """Deve permitir criação de usuário admin"""
        service = UserService(db_session)
        user_data = UserCreate(
            name="Novo Admin",
            email="newadmin@test.com",
            password="senha123",
            role="admin"
        )
        
        user = service.create_user(user_data, password_hash="$2b$12$hash")
        
        assert user.role == "admin"


class TestUserServiceUpdate:
    """Testes de atualização (update_user)"""
    
    def test_update_user_name_only(self, db_session: Session, seed_user_normal):
        """Deve atualizar apenas o nome"""
        service = UserService(db_session)
        update_data = UserUpdate(name="Nome Atualizado")
        
        user = service.update_user(seed_user_normal.id, update_data)
        
        assert user.name == "Nome Atualizado"
        assert user.email == seed_user_normal.email  # Não mudou
        assert user.role == seed_user_normal.role  # Não mudou
    
    def test_update_user_email_valid(self, db_session: Session, seed_user_normal):
        """Deve atualizar email para um novo email válido"""
        service = UserService(db_session)
        update_data = UserUpdate(email="novoemail@test.com")
        
        user = service.update_user(seed_user_normal.id, update_data)
        
        assert user.email == "novoemail@test.com"
    
    def test_update_user_email_duplicate(self, db_session: Session, seed_user_admin, seed_user_normal):
        """Deve lançar ConflictError ao tentar email já existente"""
        service = UserService(db_session)
        update_data = UserUpdate(email="admin@test.com")  # Email do admin
        
        with pytest.raises(ConflictError) as exc:
            service.update_user(seed_user_normal.id, update_data)
        
        assert "admin@test.com" in str(exc.value)
    
    def test_update_user_role(self, db_session: Session, seed_user_normal):
        """Deve permitir mudança de role"""
        service = UserService(db_session)
        update_data = UserUpdate(role="admin")
        
        user = service.update_user(seed_user_normal.id, update_data)
        
        assert user.role == "admin"
    
    def test_update_user_is_active(self, db_session: Session, seed_user_normal):
        """Deve permitir desativar usuário"""
        service = UserService(db_session)
        update_data = UserUpdate(is_active=False)
        
        user = service.update_user(seed_user_normal.id, update_data)
        
        assert user.is_active is False
    
    def test_update_user_multiple_fields(self, db_session: Session, seed_user_normal):
        """Deve atualizar múltiplos campos simultaneamente"""
        service = UserService(db_session)
        update_data = UserUpdate(
            name="Nome Novo",
            email="multiplo@test.com",
            role="admin",
            is_active=False
        )
        
        user = service.update_user(seed_user_normal.id, update_data)
        
        assert user.name == "Nome Novo"
        assert user.email == "multiplo@test.com"
        assert user.role == "admin"
        assert user.is_active is False
    
    def test_update_user_not_found(self, db_session: Session):
        """Deve lançar NotFoundError ao tentar atualizar usuário inexistente"""
        service = UserService(db_session)
        fake_id = uuid4()
        update_data = UserUpdate(name="Teste")
        
        with pytest.raises(NotFoundError):
            service.update_user(fake_id, update_data)
    
    def test_update_user_same_email(self, db_session: Session, seed_user_normal):
        """Deve permitir 'atualizar' para o mesmo email (sem conflito)"""
        service = UserService(db_session)
        original_email = seed_user_normal.email
        update_data = UserUpdate(email=original_email)
        
        # Não deve lançar ConflictError
        user = service.update_user(seed_user_normal.id, update_data)
        assert user.email == original_email


class TestUserServiceDelete:
    """Testes de deleção (delete_user)"""
    
    def test_delete_user_success(self, db_session: Session, seed_user_normal):
        """Deve deletar usuário existente"""
        service = UserService(db_session)
        user_id = seed_user_normal.id
        
        service.delete_user(user_id)
        
        # Verificar que foi deletado
        with pytest.raises(NotFoundError):
            service.get_user_by_id(user_id)
    
    def test_delete_user_not_found(self, db_session: Session):
        """Deve lançar NotFoundError ao tentar deletar usuário inexistente"""
        service = UserService(db_session)
        fake_id = uuid4()
        
        with pytest.raises(NotFoundError):
            service.delete_user(fake_id)


# ============================================================================
# EDGE CASES E TESTES DE INTEGRAÇÃO
# ============================================================================

class TestUserServiceEdgeCases:
    """Testes de cenários especiais e edge cases"""
    
    def test_create_user_with_empty_password_hash(self, db_session: Session):
        """Deve permitir criar usuário com hash vazio (se o sistema permitir)"""
        service = UserService(db_session)
        user_data = UserCreate(
            name="Sem Senha",
            email="semusenha@test.com",
            password="",
            role="user"
        )
        
        user = service.create_user(user_data, password_hash="")
        assert user.password_hash == ""
    
    def test_update_user_partial_empty_values(self, db_session: Session, seed_user_normal):
        """Deve ignorar campos None no update (update parcial)"""
        service = UserService(db_session)
        original_email = seed_user_normal.email
        update_data = UserUpdate(name="Novo Nome")  # Só name, email fica None
        
        user = service.update_user(seed_user_normal.id, update_data)
        
        assert user.name == "Novo Nome"
        assert user.email == original_email  # Não foi alterado
    
    def test_list_users_empty_database(self, db_session: Session):
        """Deve retornar lista vazia quando não há usuários"""
        # Limpar todos os usuários (cuidado: pode afetar outros testes)
        db_session.query(User).delete()
        db_session.commit()
        
        service = UserService(db_session)
        result = service.list_users()
        
        assert result["total"] == 0
        assert result["items"] == []
    
    def test_list_users_page_beyond_total(self, db_session: Session, seed_user_admin):
        """Deve retornar lista vazia quando pede página além do total"""
        service = UserService(db_session)
        result = service.list_users(page=999, page_size=20)
        
        assert result["items"] == []
        assert result["page"] == 999
