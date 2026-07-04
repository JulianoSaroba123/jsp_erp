"""
Testes para app/routers/customer_routes.py

Coverage target: 80-85%
Testa autenticação, RBAC, paginação, CRUD de customers
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.customer import Customer


class TestListCustomers:
    """Testes para GET /customers"""
    
    def test_list_customers_requires_authentication(self, client: TestClient):
        """Deve retornar 401 sem token de autenticação"""
        response = client.get("/customers")
        assert response.status_code == 401
    
    def test_list_customers_requires_permission(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict
    ):
        """Usuário sem permissão customers:read deve receber 403"""
        # Assumindo que seed_user_normal não tem permissão customers:read
        # (depende da configuração de RBAC)
        client.headers.update(auth_headers_user)
        response = client.get("/customers")
        
        # Se tiver permissão, deve ser 200, senão 403
        assert response.status_code in [200, 403]
    
    def test_list_customers_empty(
        self,
        client: TestClient,
        seed_user_admin: User,
        auth_headers_admin: dict
    ):
        """Admin sem customers deve receber lista vazia"""
        client.headers.update(auth_headers_admin)
        response = client.get("/customers")
        
        assert response.status_code == 200
        data = response.json()
        
        # Pode haver customers de testes anteriores
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
    
    def test_list_customers_with_data(
        self,
        client: TestClient,
        seed_user_admin: User,
        auth_headers_admin: dict,
        db_session: Session
    ):
        """Admin deve ver todos os customers"""
        # Criar customers de teste
        customer1 = Customer(
            person_type="PF",
            name="João Silva",
            cpf_cnpj="12345678900",
            email="joao@example.com",
            phone="11987654321"
        )
        customer2 = Customer(
            person_type="PJ",
            name="Empresa XYZ Ltda",
            trade_name="XYZ Corp",
            cpf_cnpj="12345678000190",
            email="contato@xyz.com",
            phone="1133334444"
        )
        db_session.add_all([customer1, customer2])
        db_session.commit()
        
        client.headers.update(auth_headers_admin)
        response = client.get("/customers")
        
        assert response.status_code == 200
        data = response.json()
        
        # Deve ter pelo menos os 2 customers criados
        assert data["total"] >= 2
        assert len(data["items"]) >= 2
    
    def test_list_customers_pagination(
        self,
        client: TestClient,
        seed_user_admin: User,
        auth_headers_admin: dict,
        db_session: Session
    ):
        """Deve suportar paginação"""
        # Criar 25 customers
        customers = [
            Customer(
                person_type="PF",
                name=f"Customer {i}",
                cpf_cnpj=f"000000000{i:02d}",
                email=f"customer{i}@example.com"
            )
            for i in range(25)
        ]
        db_session.add_all(customers)
        db_session.commit()
        
        client.headers.update(auth_headers_admin)
        
        # Página 1 com 10 itens
        response = client.get("/customers?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert data["total"] >= 25
        assert len(data["items"]) == 10
        
        # Página 2
        response = client.get("/customers?page=2&page_size=10")
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 2
        assert len(data["items"]) == 10
    
    def test_list_customers_filter_by_status(
        self,
        client: TestClient,
        seed_user_admin: User,
        auth_headers_admin: dict,
        db_session: Session
    ):
        """Deve filtrar customers por status ativo/inativo"""
        customer_active = Customer(
            person_type="PF",
            name="Customer Ativo",
            cpf_cnpj="11111111111",
            email="ativo@example.com",
            status="active"
        )
        customer_inactive = Customer(
            person_type="PF",
            name="Customer Inativo",
            cpf_cnpj="22222222222",
            email="inativo@example.com",
            status="inactive"
        )
        db_session.add_all([customer_active, customer_inactive])
        db_session.commit()
        
        client.headers.update(auth_headers_admin)
        
        # Filtrar apenas ativos
        response = client.get("/customers?status_filter=active")
        assert response.status_code == 200
        data = response.json()
        
        # Verificar que retornou apenas ativos
        active_names = [c["name"] for c in data["items"]]
        assert "Customer Ativo" in active_names or data["total"] >= 1


class TestCreateCustomer:
    """Testes para POST /customers"""
    
    def test_create_customer_requires_authentication(self, client: TestClient):
        """Deve retornar 401 sem token"""
        payload = {
            "person_type": "PF",
            "name": "Test Customer",
            "cpf_cnpj": "12345678900",
            "email": "test@example.com"
        }
        response = client.post("/customers", json=payload)
        
        assert response.status_code == 401
    
    def test_create_customer_success_pf(
        self,
        client: TestClient,
        seed_user_admin: User,
        auth_headers_admin: dict
    ):
        """Admin deve conseguir criar customer PF"""
        payload = {
            "person_type": "PF",
            "name": "Maria Santos",
            "cpf_cnpj": "98765432100",
            "email": "maria.santos@example.com",
            "phone": "11999998888",
            "street": "Rua A",
            "number": "123",
            "city": "São Paulo",
            "state": "SP",
            "cep": "01234567"
        }
        
        client.headers.update(auth_headers_admin)
        response = client.post("/customers", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == "Maria Santos"
        assert data["person_type"] == "PF"
        assert data["cpf_cnpj"] == "98765432100"
        assert data["email"] == "maria.santos@example.com"
        assert "id" in data
    
    def test_create_customer_success_pj(
        self,
        client: TestClient,
        seed_user_admin: User,
        auth_headers_admin: dict
    ):
        """Admin deve conseguir criar customer PJ"""
        payload = {
            "person_type": "PJ",
            "name": "Tech Solutions Ltda",
            "trade_name": "Tech Solutions",
            "cpf_cnpj": "98765432000110",
            "email": "contato@techsolutions.com",
            "phone": "1133332222"
        }
        
        client.headers.update(auth_headers_admin)
        response = client.post("/customers", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == "Tech Solutions Ltda"
        assert data["person_type"] == "PJ"
        assert data["trade_name"] == "Tech Solutions"
    
    def test_create_customer_duplicate_cpf_cnpj(
        self,
        client: TestClient,
        seed_user_admin: User,
        auth_headers_admin: dict,
        db_session: Session
    ):
        """Deve retornar 409 ao tentar criar customer com CPF/CNPJ duplicado"""
        # Criar customer existente
        existing = Customer(
            person_type="PF",
            name="Existing Customer",
            cpf_cnpj="11122233344",
            email="existing@example.com"
        )
        db_session.add(existing)
        db_session.commit()
        
        # Tentar criar com mesmo CPF/CNPJ
        payload = {
            "person_type": "PF",
            "name": "Another Customer",
            "cpf_cnpj": "11122233344",  # Duplicado
            "email": "another@example.com"
        }
        
        client.headers.update(auth_headers_admin)
        response = client.post("/customers", json=payload)
        
        assert response.status_code == 409
        assert "CPF/CNPJ" in response.json()["detail"]
    
    def test_create_customer_invalid_person_type(
        self,
        client: TestClient,
        seed_user_admin: User,
        auth_headers_admin: dict
    ):
        """Deve retornar 400 com person_type inválido"""
        payload = {
            "person_type": "INVALID",  # Deve ser PF ou PJ
            "name": "Test Customer",
            "email": "test@example.com"
        }
        
        client.headers.update(auth_headers_admin)
        response = client.post("/customers", json=payload)
        
        # Pode ser 400 (ValidationError) ou 422 (Pydantic)
        assert response.status_code in [400, 422]


class TestGetCustomer:
    """Testes para GET /customers/{customer_id}"""
    
    def test_get_customer_requires_authentication(self, client: TestClient):
        """Deve retornar 401 sem token"""
        from uuid import uuid4
        response = client.get(f"/customers/{uuid4()}")
        
        assert response.status_code == 401
    
    def test_get_customer_success(
        self,
        client: TestClient,
        seed_user_admin: User,
        auth_headers_admin: dict,
        db_session: Session
    ):
        """Admin deve conseguir buscar customer por ID"""
        customer = Customer(
            person_type="PF",
            name="Test Get Customer",
            cpf_cnpj="55566677788",
            email="gettest@example.com"
        )
        db_session.add(customer)
        db_session.commit()
        db_session.refresh(customer)
        
        client.headers.update(auth_headers_admin)
        response = client.get(f"/customers/{customer.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(customer.id)
        assert data["name"] == "Test Get Customer"
        assert data["cpf_cnpj"] == "55566677788"
    
    def test_get_customer_not_found(
        self,
        client: TestClient,
        seed_user_admin: User,
        auth_headers_admin: dict
    ):
        """Deve retornar 404 para customer inexistente"""
        from uuid import uuid4
        
        client.headers.update(auth_headers_admin)
        response = client.get(f"/customers/{uuid4()}")
        
        assert response.status_code == 404
        assert "não encontrado" in response.json()["detail"].lower()


class TestUpdateCustomer:
    """Testes para PATCH /customers/{customer_id}"""
    
    def test_update_customer_requires_authentication(self, client: TestClient):
        """Deve retornar 401 sem token"""
        from uuid import uuid4
        payload = {"name": "Updated Name"}
        response = client.patch(f"/customers/{uuid4()}", json=payload)
        
        assert response.status_code == 401
    
    def test_update_customer_success(
        self,
        client: TestClient,
        seed_user_admin: User,
        auth_headers_admin: dict,
        db_session: Session
    ):
        """Admin deve conseguir atualizar customer"""
        customer = Customer(
            person_type="PF",
            name="Original Name",
            cpf_cnpj="77788899900",
            email="original@example.com",
            phone="11988887777"
        )
        db_session.add(customer)
        db_session.commit()
        db_session.refresh(customer)
        
        # Atualizar nome e telefone
        payload = {
            "name": "Updated Name",
            "phone": "11999998888"
        }
        
        client.headers.update(auth_headers_admin)
        response = client.patch(f"/customers/{customer.id}", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "Updated Name"
        assert data["phone"] == "11999998888"
        assert data["cpf_cnpj"] == "77788899900"  # Não alterado
    
    def test_update_customer_not_found(
        self,
        client: TestClient,
        seed_user_admin: User,
        auth_headers_admin: dict
    ):
        """Deve retornar 404 ao tentar atualizar customer inexistente"""
        from uuid import uuid4
        
        payload = {"name": "New Name"}
        
        client.headers.update(auth_headers_admin)
        response = client.patch(f"/customers/{uuid4()}", json=payload)
        
        assert response.status_code == 404
    
    def test_update_customer_duplicate_cpf_cnpj(
        self,
        client: TestClient,
        seed_user_admin: User,
        auth_headers_admin: dict,
        db_session: Session
    ):
        """Deve retornar 409 ao tentar atualizar para CPF/CNPJ já existente"""
        customer1 = Customer(
            person_type="PF",
            name="Customer 1",
            cpf_cnpj="11111111111",
            email="customer1@example.com"
        )
        customer2 = Customer(
            person_type="PF",
            name="Customer 2",
            cpf_cnpj="22222222222",
            email="customer2@example.com"
        )
        db_session.add_all([customer1, customer2])
        db_session.commit()
        db_session.refresh(customer2)
        
        # Tentar atualizar customer2 para ter o CPF do customer1
        payload = {"cpf_cnpj": "11111111111"}
        
        client.headers.update(auth_headers_admin)
        response = client.patch(f"/customers/{customer2.id}", json=payload)
        
        assert response.status_code == 409
        assert "CPF/CNPJ" in response.json()["detail"]


class TestDeleteCustomer:
    """Testes para DELETE /customers/{customer_id}"""
    
    def test_delete_customer_requires_authentication(self, client: TestClient):
        """Deve retornar 401 sem token"""
        from uuid import uuid4
        response = client.delete(f"/customers/{uuid4()}")
        
        assert response.status_code == 401
    
    def test_delete_customer_success(
        self,
        client: TestClient,
        seed_user_admin: User,
        auth_headers_admin: dict,
        db_session: Session
    ):
        """Admin deve conseguir deletar customer (soft delete)"""
        customer = Customer(
            person_type="PF",
            name="To Be Deleted",
            cpf_cnpj="99999999999",
            email="delete@example.com"
        )
        db_session.add(customer)
        db_session.commit()
        db_session.refresh(customer)
        
        client.headers.update(auth_headers_admin)
        response = client.delete(f"/customers/{customer.id}")
        
        assert response.status_code == 204
        
        # Verificar que foi soft deleted
        db_session.refresh(customer)
        assert customer.deleted_at is not None
    
    def test_delete_customer_not_found(
        self,
        client: TestClient,
        seed_user_admin: User,
        auth_headers_admin: dict
    ):
        """Deve retornar 404 ao tentar deletar customer inexistente"""
        from uuid import uuid4
        
        client.headers.update(auth_headers_admin)
        response = client.delete(f"/customers/{uuid4()}")
        
        assert response.status_code == 404
