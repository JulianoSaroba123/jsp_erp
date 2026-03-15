"""
Testes para app/routers/product_routes.py

Coverage target: 80-85%
Testa autenticação, RBAC, multi-tenant, paginação, CRUD de products
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.product import Product


class TestListProducts:
    """Testes para GET /products"""
    
    def test_list_products_requires_authentication(self, client: TestClient):
        """Deve retornar 401 sem token de autenticação"""
        response = client.get("/products")
        assert response.status_code == 401
    
    def test_list_products_empty_for_user(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict
    ):
        """Usuário sem produtos deve receber lista vazia"""
        client.headers.update(auth_headers_user)
        response = client.get("/products")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["items"] == []
        assert data["total"] == 0
    
    def test_list_products_multi_tenant_user_sees_own_only(
        self,
        client: TestClient,
        seed_user_normal: User,
        seed_user_other: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """User normal deve ver apenas seus próprios produtos"""
        # Criar produto para user_normal
        product_own = Product(
            user_id=seed_user_normal.id,
            name="Produto do User Normal",
            code="PROD001",
            cost_price=100.0,
            sale_price=150.0,
            stock_qty=10
        )
        db_session.add(product_own)
        
        # Criar produto para outro usuário
        product_other = Product(
            user_id=seed_user_other.id,
            name="Produto de Outro User",
            code="PROD002",
            cost_price=200.0,
            sale_price=250.0,
            stock_qty=5
        )
        db_session.add(product_other)
        db_session.commit()
        
        client.headers.update(auth_headers_user)
        response = client.get("/products")
        
        assert response.status_code == 200
        data = response.json()
        
        # Deve ver apenas 1 produto (o próprio)
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Produto do User Normal"
    
    def test_list_products_admin_sees_all(
        self,
        client: TestClient,
        seed_user_admin: User,
        seed_user_normal: User,
        seed_user_other: User,
        auth_headers_admin: dict,
        db_session: Session
    ):
        """Admin deve ver todos os produtos (multi-tenant)"""
        # Criar produtos de diferentes usuários
        product1 = Product(user_id=seed_user_normal.id, name="Product 1", cost_price=100, sale_price=150, stock_qty=10)
        product2 = Product(user_id=seed_user_other.id, name="Product 2", cost_price=200, sale_price=250, stock_qty=5)
        product3 = Product(user_id=seed_user_admin.id, name="Product 3", cost_price=300, sale_price=350, stock_qty=8)
        
        db_session.add_all([product1, product2, product3])
        db_session.commit()
        
        client.headers.update(auth_headers_admin)
        response = client.get("/products")
        
        assert response.status_code == 200
        data = response.json()
        
        # Admin vê todos os 3 produtos
        assert data["total"] == 3
        assert len(data["items"]) == 3
    
    def test_list_products_filter_by_q(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """Deve filtrar produtos por nome ou código (busca parcial)"""
        products = [
            Product(user_id=seed_user_normal.id, name="Notebook Dell", code="PROD001", cost_price=2500, sale_price=3500, stock_qty=5),
            Product(user_id=seed_user_normal.id, name="Mouse Logitech", code="PROD002", cost_price=50, sale_price=80, stock_qty=20),
            Product(user_id=seed_user_normal.id, name="Teclado Dell", code="PROD003", cost_price=150, sale_price=200, stock_qty=10),
        ]
        db_session.add_all(products)
        db_session.commit()
        
        client.headers.update(auth_headers_user)
        
        # Buscar por "Dell" (deve encontrar 2)
        response = client.get("/products?q=Dell")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        
        # Buscar por "PROD002" (deve encontrar 1)
        response = client.get("/products?q=PROD002")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["code"] == "PROD002"
    
    def test_list_products_filter_by_category(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """Deve filtrar produtos por categoria"""
        products = [
            Product(user_id=seed_user_normal.id, name="Notebook", category="Informática", cost_price=2500, sale_price=3500, stock_qty=5),
            Product(user_id=seed_user_normal.id, name="Mouse", category="Informática", cost_price=50, sale_price=80, stock_qty=20),
            Product(user_id=seed_user_normal.id, name="Mesa", category="Móveis", cost_price=500, sale_price=700, stock_qty=3),
        ]
        db_session.add_all(products)
        db_session.commit()
        
        client.headers.update(auth_headers_user)
        
        response = client.get("/products?category=Informática")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
    
    def test_list_products_filter_by_active(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """Deve filtrar produtos por status ativo/inativo"""
        products = [
            Product(user_id=seed_user_normal.id, name="Product 1", active=True, cost_price=100, sale_price=150, stock_qty=10),
            Product(user_id=seed_user_normal.id, name="Product 2", active=False, cost_price=200, sale_price=250, stock_qty=5),
            Product(user_id=seed_user_normal.id, name="Product 3", active=True, cost_price=300, sale_price=350, stock_qty=8),
        ]
        db_session.add_all(products)
        db_session.commit()
        
        client.headers.update(auth_headers_user)
        
        # Filtrar apenas ativos
        response = client.get("/products?active=true")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2


class TestCreateProduct:
    """Testes para POST /products"""
    
    def test_create_product_requires_authentication(self, client: TestClient):
        """Deve retornar 401 sem token"""
        payload = {"name": "Test Product", "cost_price": 100.0, "sale_price": 150.0}
        response = client.post("/products", json=payload)
        
        assert response.status_code == 401
    
    def test_create_product_success(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict
    ):
        """Deve criar produto com sucesso"""
        payload = {
            "name": "Notebook Dell",
            "code": "PROD001",
            "category": "Informática",
            "unit": "un",
            "description": "Notebook 15.6 polegadas",
            "cost_price": 2500.0,
            "sale_price": 3500.0,
            "stock_qty": 10,
            "stock_min": 2,
            "active": True
        }
        
        client.headers.update(auth_headers_user)
        response = client.post("/products", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == "Notebook Dell"
        assert data["code"] == "PROD001"
        assert data["cost_price"] == 2500.0
        assert data["user_id"] == str(seed_user_normal.id)
    
    def test_create_product_duplicate_code_same_user(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """Não deve permitir código duplicado para o mesmo usuário"""
        # Criar primeiro produto
        product = Product(
            user_id=seed_user_normal.id,
            name="Product 1",
            code="PROD001",
            cost_price=100,
            sale_price=150,
            stock_qty=10
        )
        db_session.add(product)
        db_session.commit()
        
        # Tentar criar segundo com mesmo código
        payload = {
            "name": "Product 2",
            "code": "PROD001",  # Código duplicado
            "cost_price": 200,
            "sale_price": 250
        }
        
        client.headers.update(auth_headers_user)
        response = client.post("/products", json=payload)
        
        assert response.status_code == 409  # Conflict
        assert "já está em uso" in response.json()["detail"]
    
    def test_create_product_validation_negative_price(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Não deve permitir preços negativos"""
        payload = {
            "name": "Product Invalid",
            "cost_price": -100.0,  # Negativo
            "sale_price": 150.0
        }
        
        client.headers.update(auth_headers_user)
        response = client.post("/products", json=payload)
        
        assert response.status_code == 422  # Validation Error


class TestGetProduct:
    """Testes para GET /products/{id}"""
    
    def test_get_product_requires_authentication(self, client: TestClient):
        """Deve retornar 401 sem token"""
        from uuid import uuid4
        response = client.get(f"/products/{uuid4()}")
        
        assert response.status_code == 401
    
    def test_get_product_success(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """Deve retornar produto por ID"""
        product = Product(
            user_id=seed_user_normal.id,
            name="Notebook Dell",
            code="PROD001",
            cost_price=2500,
            sale_price=3500,
            stock_qty=10
        )
        db_session.add(product)
        db_session.commit()
        
        client.headers.update(auth_headers_user)
        response = client.get(f"/products/{product.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "Notebook Dell"
        assert data["code"] == "PROD001"
    
    def test_get_product_not_found(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 404 para produto inexistente"""
        from uuid import uuid4
        
        client.headers.update(auth_headers_user)
        response = client.get(f"/products/{uuid4()}")
        
        assert response.status_code == 404
    
    def test_get_product_anti_enumeration(
        self,
        client: TestClient,
        seed_user_normal: User,
        seed_user_other: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """User não deve ver produto de outro usuário (anti-enumeration)"""
        # Criar produto para outro usuário
        product_other = Product(
            user_id=seed_user_other.id,
            name="Product Other User",
            code="PROD999",
            cost_price=1000,
            sale_price=1500,
            stock_qty=5
        )
        db_session.add(product_other)
        db_session.commit()
        
        # Tentar acessar como user_normal
        client.headers.update(auth_headers_user)
        response = client.get(f"/products/{product_other.id}")
        
        # Deve retornar 404 (não 403) para anti-enumeration
        assert response.status_code == 404


class TestUpdateProduct:
    """Testes para PATCH /products/{id}"""
    
    def test_update_product_success(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """Deve atualizar produto com sucesso"""
        product = Product(
            user_id=seed_user_normal.id,
            name="Notebook Dell",
            cost_price=2500,
            sale_price=3500,
            stock_qty=10
        )
        db_session.add(product)
        db_session.commit()
        
        payload = {
            "name": "Notebook Dell Atualizado",
            "sale_price": 3800.0
        }
        
        client.headers.update(auth_headers_user)
        response = client.patch(f"/products/{product.id}", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "Notebook Dell Atualizado"
        assert data["sale_price"] == 3800.0
        assert data["cost_price"] == 2500.0  # Não alterado
    
    def test_update_product_not_found(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 404 para produto inexistente"""
        from uuid import uuid4
        
        payload = {"name": "Updated Name"}
        
        client.headers.update(auth_headers_user)
        response = client.patch(f"/products/{uuid4()}", json=payload)
        
        assert response.status_code == 404


class TestDeleteProduct:
    """Testes para DELETE /products/{id}"""
    
    def test_delete_product_success(
        self,
        client: TestClient,
        seed_user_admin: User,
        auth_headers_admin: dict,
        db_session: Session
    ):
        """Deve fazer soft delete do produto"""
        product = Product(
            user_id=seed_user_admin.id,
            name="Notebook Dell",
            cost_price=2500,
            sale_price=3500,
            stock_qty=10
        )
        db_session.add(product)
        db_session.commit()
        
        client.headers.update(auth_headers_admin)
        response = client.delete(f"/products/{product.id}")
        
        assert response.status_code == 204
        
        # Verificar que produto não aparece mais no list
        response = client.get("/products")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
    
    def test_delete_product_not_found(
        self,
        client: TestClient,
        auth_headers_admin: dict
    ):
        """Deve retornar 404 para produto inexistente"""
        from uuid import uuid4
        
        client.headers.update(auth_headers_admin)
        response = client.delete(f"/products/{uuid4()}")
        
        assert response.status_code == 404
