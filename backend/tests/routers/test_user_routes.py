"""
Testes para app/routers/user_routes.py

Coverage target: 80-85%
Testa contrato HTTP: status codes, payloads, validação, paginação
"""
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from sqlalchemy.orm import Session

from app.models.user import User


class TestListUsers:
    """Testes para GET /users (list com paginação)"""
    
    def test_list_users_empty_database(self, client: TestClient, db_session: Session):
        """Deve retornar lista vazia quando não há usuários"""
        response = client.get("/users")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["items"] == []
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total"] == 0
    
    def test_list_users_default_pagination(
        self,
        client: TestClient,
        seed_user_admin: User,
        seed_user_normal: User
    ):
        """Deve listar usuários com paginação padrão"""
        response = client.get("/users")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total"] == 2
        
        # Verificar estrutura de UserResponse
        first_user = data["items"][0]
        assert "id" in first_user
        assert "name" in first_user
        assert "email" in first_user
        assert "role" in first_user
        assert "is_active" in first_user
        assert "created_at" in first_user
        
        # NUNCA deve vazar password_hash
        assert "password_hash" not in first_user
        assert "password" not in first_user
    
    def test_list_users_custom_page_size(
        self,
        client: TestClient,
        seed_user_admin: User,
        seed_user_normal: User,
        seed_user_other: User
    ):
        """Deve respeitar page_size customizado"""
        response = client.get("/users?page=1&page_size=2")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total"] == 3
    
    def test_list_users_second_page(
        self,
        client: TestClient,
        seed_user_admin: User,
        seed_user_normal: User,
        seed_user_other: User
    ):
        """Deve retornar segunda página corretamente"""
        response = client.get("/users?page=2&page_size=2")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["items"]) == 1  # último usuário
        assert data["page"] == 2
        assert data["page_size"] == 2
        assert data["total"] == 3
    
    def test_list_users_page_beyond_total(
        self,
        client: TestClient,
        seed_user_admin: User
    ):
        """Deve retornar lista vazia para página além do total"""
        response = client.get("/users?page=10&page_size=20")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["items"] == []
        assert data["page"] == 10
        assert data["total"] == 1


class TestGetUser:
    """Testes para GET /users/{user_id}"""
    
    def test_get_user_success(self, client: TestClient, seed_user_admin: User):
        """Deve retornar usuário por ID"""
        response = client.get(f"/users/{seed_user_admin.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(seed_user_admin.id)
        assert data["name"] == "Admin Test"
        assert data["email"] == "admin@test.com"
        assert data["role"] == "admin"
        assert data["is_active"] is True
        
        # NUNCA deve vazar password_hash
        assert "password_hash" not in data
    
    def test_get_user_not_found(self, client: TestClient):
        """Deve retornar 404 para usuário inexistente"""
        fake_id = uuid4()
        response = client.get(f"/users/{fake_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_get_user_invalid_uuid(self, client: TestClient):
        """Deve retornar 422 para UUID inválido"""
        response = client.get("/users/not-a-valid-uuid")
        
        assert response.status_code == 422


class TestCreateUser:
    """Testes para POST /users"""
    
    def test_create_user_success(self, client: TestClient, db_session: Session):
        """Deve criar novo usuário com sucesso"""
        payload = {
            "name": "New User",
            "email": "newuser@test.com",
            "password": "secure123",
            "role": "user"
        }
        
        response = client.post("/users", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == "New User"
        assert data["email"] == "newuser@test.com"
        assert data["role"] == "user"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        
        # NUNCA deve retornar a senha
        assert "password" not in data
        assert "password_hash" not in data
    
    def test_create_user_duplicate_email(
        self,
        client: TestClient,
        seed_user_admin: User
    ):
        """Deve retornar 409 ao tentar criar usuário com email duplicado"""
        payload = {
            "name": "Duplicate",
            "email": "admin@test.com",  # já existe
            "password": "test123"
        }
        
        response = client.post("/users", json=payload)
        
        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
    
    def test_create_user_missing_required_fields(self, client: TestClient):
        """Deve retornar 422 se faltar campos obrigatórios"""
        payload = {
            "name": "Incomplete User"
            # faltando email e password
        }
        
        response = client.post("/users", json=payload)
        
        assert response.status_code == 422
    
    def test_create_user_invalid_email(self, client: TestClient):
        """Deve retornar 422 para email inválido"""
        payload = {
            "name": "Bad Email",
            "email": "not-an-email",
            "password": "test123"
        }
        
        response = client.post("/users", json=payload)
        
        assert response.status_code == 422
    
    def test_create_user_default_role(self, client: TestClient):
        """Deve usar role='user' como padrão"""
        payload = {
            "name": "Default Role",
            "email": "defaultrole@test.com",
            "password": "test123"
            # não especificando role
        }
        
        response = client.post("/users", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "user"
    
    def test_create_user_admin_role(self, client: TestClient):
        """Deve permitir criar usuário com role admin"""
        payload = {
            "name": "Admin User",
            "email": "newadmin@test.com",
            "password": "admin123",
            "role": "admin"
        }
        
        response = client.post("/users", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "admin"


class TestUpdateUser:
    """Testes para PUT /users/{user_id}"""
    
    def test_update_user_name_only(
        self,
        client: TestClient,
        seed_user_normal: User
    ):
        """Deve atualizar apenas o nome"""
        payload = {"name": "Updated Name"}
        
        response = client.put(f"/users/{seed_user_normal.id}", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "Updated Name"
        assert data["email"] == "user@test.com"  # não alterado
    
    def test_update_user_email(
        self,
        client: TestClient,
        seed_user_normal: User
    ):
        """Deve atualizar email para valor válido"""
        payload = {"email": "newemail@test.com"}
        
        response = client.put(f"/users/{seed_user_normal.id}", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["email"] == "newemail@test.com"
    
    def test_update_user_email_duplicate(
        self,
        client: TestClient,
        seed_user_admin: User,
        seed_user_normal: User
    ):
        """Deve retornar 409 ao tentar atualizar para email já existente"""
        payload = {"email": "admin@test.com"}  # já existe
        
        response = client.put(f"/users/{seed_user_normal.id}", json=payload)
        
        assert response.status_code == 409
    
    def test_update_user_role(
        self,
        client: TestClient,
        seed_user_normal: User
    ):
        """Deve atualizar role"""
        payload = {"role": "admin"}
        
        response = client.put(f"/users/{seed_user_normal.id}", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["role"] == "admin"
    
    def test_update_user_is_active(
        self,
        client: TestClient,
        seed_user_normal: User
    ):
        """Deve atualizar is_active"""
        payload = {"is_active": False}
        
        response = client.put(f"/users/{seed_user_normal.id}", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_active"] is False
    
    def test_update_user_multiple_fields(
        self,
        client: TestClient,
        seed_user_normal: User
    ):
        """Deve atualizar múltiplos campos simultaneamente"""
        payload = {
            "name": "Multi Update",
            "email": "multiupdate@test.com",
            "role": "admin",
            "is_active": False
        }
        
        response = client.put(f"/users/{seed_user_normal.id}", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "Multi Update"
        assert data["email"] == "multiupdate@test.com"
        assert data["role"] == "admin"
        assert data["is_active"] is False
    
    def test_update_user_not_found(self, client: TestClient):
        """Deve retornar 404 para usuário inexistente"""
        fake_id = uuid4()
        payload = {"name": "Ghost User"}
        
        response = client.put(f"/users/{fake_id}", json=payload)
        
        assert response.status_code == 404
    
    def test_update_user_empty_payload(
        self,
        client: TestClient,
        seed_user_normal: User
    ):
        """Deve aceitar payload vazio (sem alterações)"""
        payload = {}
        
        response = client.put(f"/users/{seed_user_normal.id}", json=payload)
        
        assert response.status_code == 200


class TestDeleteUser:
    """Testes para DELETE /users/{user_id}"""
    
    def test_delete_user_success(
        self,
        client: TestClient,
        seed_user_other: User,
        db_session: Session
    ):
        """Deve deletar usuário com sucesso"""
        user_id = seed_user_other.id
        
        response = client.delete(f"/users/{user_id}")
        
        assert response.status_code == 204
        assert response.content == b""  # No content
        
        # Verificar que foi deletado do banco
        deleted_user = db_session.query(User).filter(User.id == user_id).first()
        assert deleted_user is None
    
    def test_delete_user_not_found(self, client: TestClient):
        """Deve retornar 404 ao tentar deletar usuário inexistente"""
        fake_id = uuid4()
        
        response = client.delete(f"/users/{fake_id}")
        
        assert response.status_code == 404
    
    def test_delete_user_invalid_uuid(self, client: TestClient):
        """Deve retornar 422 para UUID inválido"""
        response = client.delete("/users/invalid-uuid")
        
        assert response.status_code == 422


class TestUserRoutesIntegration:
    """Testes de integração end-to-end"""
    
    def test_full_user_lifecycle(self, client: TestClient, db_session: Session):
        """Testa ciclo completo: create → read → update → delete"""
        # 1. CREATE
        create_payload = {
            "name": "Lifecycle User",
            "email": "lifecycle@test.com",
            "password": "test123"
        }
        create_response = client.post("/users", json=create_payload)
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]
        
        # 2. READ (by ID)
        get_response = client.get(f"/users/{user_id}")
        assert get_response.status_code == 200
        assert get_response.json()["email"] == "lifecycle@test.com"
        
        # 3. UPDATE
        update_payload = {"name": "Updated Lifecycle"}
        update_response = client.put(f"/users/{user_id}", json=update_payload)
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated Lifecycle"
        
        # 4. DELETE
        delete_response = client.delete(f"/users/{user_id}")
        assert delete_response.status_code == 204
        
        # 5. VERIFY deletion
        verify_response = client.get(f"/users/{user_id}")
        assert verify_response.status_code == 404
    
    def test_pagination_consistency(self, client: TestClient, db_session: Session):
        """Verifica consistência de paginação ao criar múltiplos usuários"""
        # Criar 5 usuários
        for i in range(5):
            payload = {
                "name": f"User {i}",
                "email": f"user{i}@pagination.com",
                "password": "test123"
            }
            response = client.post("/users", json=payload)
            assert response.status_code == 201
        
        # Listar com page_size=2
        page1 = client.get("/users?page=1&page_size=2").json()
        page2 = client.get("/users?page=2&page_size=2").json()
        page3 = client.get("/users?page=3&page_size=2").json()
        
        assert len(page1["items"]) == 2
        assert len(page2["items"]) == 2
        assert len(page3["items"]) == 1  # último
        assert page1["total"] == 5
        assert page2["total"] == 5
        assert page3["total"] == 5
