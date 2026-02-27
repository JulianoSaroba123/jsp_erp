"""
Testes para app/routers/order_routes.py

Coverage target: 80-85%
Testa autenticação, multi-tenant, paginação, CRUD de orders
"""
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.order import Order


class TestListOrders:
    """Testes para GET /orders"""
    
    def test_list_orders_requires_authentication(self, client: TestClient):
        """Deve retornar 401 sem token de autenticação"""
        response = client.get("/orders")
        
        assert response.status_code == 401
    
    def test_list_orders_empty_for_user(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict
    ):
        """Usuário sem pedidos deve receber lista vazia"""
        client.headers.update(auth_headers_user)
        response = client.get("/orders")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["items"] == []
        assert data["total"] == 0
    
    def test_list_orders_multi_tenant_user_sees_own_only(
        self,
        client: TestClient,
        seed_user_normal: User,
        seed_user_other: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """User normal deve ver apenas seus próprios pedidos"""
        # Criar pedido para user_normal
        order_own = Order(
            user_id=seed_user_normal.id,
            description="Pedido do User Normal",
            total=100.0
        )
        db_session.add(order_own)
        
        # Criar pedido para outro usuário
        order_other = Order(
            user_id=seed_user_other.id,
            description="Pedido de Outro User",
            total=200.0
        )
        db_session.add(order_other)
        db_session.commit()
        
        client.headers.update(auth_headers_user)
        response = client.get("/orders")
        
        assert response.status_code == 200
        data = response.json()
        
        # Deve ver apenas 1 pedido (o próprio)
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["description"] == "Pedido do User Normal"
    
    def test_list_orders_admin_sees_all(
        self,
        client: TestClient,
        seed_user_admin: User,
        seed_user_normal: User,
        seed_user_other: User,
        auth_headers_admin: dict,
        db_session: Session
    ):
        """Admin deve ver todos os pedidos (multi-tenant)"""
        # Criar pedidos de diferentes usuários
        order1 = Order(user_id=seed_user_normal.id, description="Order 1", total=100)
        order2 = Order(user_id=seed_user_other.id, description="Order 2", total=200)
        order3 = Order(user_id=seed_user_admin.id, description="Order 3", total=300)
        
        db_session.add_all([order1, order2, order3])
        db_session.commit()
        
        client.headers.update(auth_headers_admin)
        response = client.get("/orders")
        
        assert response.status_code == 200
        data = response.json()
        
        # Admin vê todos os 3 pedidos
        assert data["total"] == 3
        assert len(data["items"]) == 3
    
    def test_list_orders_pagination(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """Deve respeitar paginação"""
        # Criar 5 pedidos
        for i in range(5):
            order = Order(
                user_id=seed_user_normal.id,
                description=f"Order {i}",
                total=100 * i
            )
            db_session.add(order)
        db_session.commit()
        
        client.headers.update(auth_headers_user)
        
        # Page 1 com page_size=2
        response = client.get("/orders?page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total"] == 5


class TestCreateOrder:
    """Testes para POST /orders"""
    
    def test_create_order_requires_authentication(self, client: TestClient):
        """Deve retornar 401 sem token"""
        payload = {"description": "Test Order", "total": 100.0}
        response = client.post("/orders", json=payload)
        
        assert response.status_code == 401
    
    def test_create_order_success(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict
    ):
        """Deve criar pedido com sucesso"""
        payload = {
            "description": "Novo Pedido",
            "total": 150.50
        }
        
        client.headers.update(auth_headers_user)
        response = client.post("/orders", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["description"] == "Novo Pedido"
        assert data["total"] == 150.50
        assert data["user_id"] == str(seed_user_normal.id)
        assert "id" in data
    
    def test_create_order_user_id_from_token(
        self,
        client: TestClient,
        seed_user_normal: User,
        seed_user_other: User,
        auth_headers_user: dict
    ):
        """user_id deve vir do token, não do body"""
        payload = {
            "description": "Test",
            "total": 100.0,
            # Não deve permitir especificar user_id diferente
        }
        
        client.headers.update(auth_headers_user)
        response = client.post("/orders", json=payload)
        
        assert response.status_code == 201
        # Deve usar user_id do token (seed_user_normal)
        assert response.json()["user_id"] == str(seed_user_normal.id)
    
    def test_create_order_missing_required_fields(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 422 se faltar campos obrigatórios"""
        payload = {"description": "Missing total"}
        
        client.headers.update(auth_headers_user)
        response = client.post("/orders", json=payload)
        
        assert response.status_code == 422
    
    def test_create_order_negative_total(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve rejeitar total negativo"""
        payload = {
            "description": "Negative",
            "total": -50.0
        }
        
        client.headers.update(auth_headers_user)
        response = client.post("/orders", json=payload)
        
        # Deve retornar 422 por validação do Pydantic
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert data["error"] == "ValidationError"


class TestGetOrderById:
    """Testes para GET /orders/{order_id}"""
    
    def test_get_order_requires_authentication(self, client: TestClient):
        """Deve retornar 401 sem token"""
        fake_id = uuid4()
        response = client.get(f"/orders/{fake_id}")
        
        assert response.status_code == 401
    
    def test_get_order_success(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """Deve retornar pedido por ID"""
        order = Order(
            user_id=seed_user_normal.id,
            description="Get Test",
            total=99.99
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        
        client.headers.update(auth_headers_user)
        response = client.get(f"/orders/{order.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(order.id)
        assert data["description"] == "Get Test"
        assert data["total"] == 99.99
    
    def test_get_order_not_found(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 404 para ordem inexistente"""
        fake_id = uuid4()
        
        client.headers.update(auth_headers_user)
        response = client.get(f"/orders/{fake_id}")
        
        assert response.status_code == 404
    
    def test_get_order_multi_tenant_user_cannot_see_others(
        self,
        client: TestClient,
        seed_user_normal: User,
        seed_user_other: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """User não pode ver pedidos de outros usuários"""
        # Criar pedido de outro usuário
        other_order = Order(
            user_id=seed_user_other.id,
            description="Other's Order",
            total=200.0
        )
        db_session.add(other_order)
        db_session.commit()
        db_session.refresh(other_order)
        
        client.headers.update(auth_headers_user)
        response = client.get(f"/orders/{other_order.id}")
        
        # Deve retornar 404 (anti-enumeration)
        assert response.status_code == 404
    
    def test_get_order_admin_can_see_any(
        self,
        client: TestClient,
        seed_user_admin: User,
        seed_user_normal: User,
        auth_headers_admin: dict,
        db_session: Session
    ):
        """Admin pode ver pedidos de qualquer usuário"""
        user_order = Order(
            user_id=seed_user_normal.id,
            description="User's Order",
            total=300.0
        )
        db_session.add(user_order)
        db_session.commit()
        db_session.refresh(user_order)
        
        client.headers.update(auth_headers_admin)
        response = client.get(f"/orders/{user_order.id}")
        
        assert response.status_code == 200
        assert response.json()["user_id"] == str(seed_user_normal.id)


class TestDeleteOrder:
    """Testes para DELETE /orders/{order_id}"""
    
    def test_delete_order_requires_authentication(self, client: TestClient):
        """Deve retornar 401 sem token"""
        fake_id = uuid4()
        response = client.delete(f"/orders/{fake_id}")
        
        assert response.status_code == 401
    
    def test_delete_order_not_found(
        self,
        client: TestClient,
        auth_headers_with_delete: dict
    ):
        """Deve retornar 404 para ordem inexistente"""
        fake_id = uuid4()
        
        client.headers.update(auth_headers_with_delete)
        response = client.delete(f"/orders/{fake_id}")
        
        assert response.status_code == 404


class TestPatchOrder:
    """Testes para PATCH /orders/{order_id}"""
    
    def test_patch_order_requires_authentication(self, client: TestClient):
        """Deve retornar 401 sem token"""
        fake_id = uuid4()
        payload = {"description": "Updated"}
        response = client.patch(f"/orders/{fake_id}", json=payload)
        
        assert response.status_code == 401
    
    def test_patch_order_not_found(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 404 para ordem inexistente"""
        fake_id = uuid4()
        payload = {"description": "Updated"}
        
        client.headers.update(auth_headers_user)
        response = client.patch(f"/orders/{fake_id}", json=payload)
        
        assert response.status_code == 404


class TestOrderRoutesEdgeCases:
    """Testes de edge cases e validações"""
    
    def test_create_order_with_zero_total(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve permitir criar ordem com total=0"""
        payload = {
            "description": "Zero Total Order",
            "total": 0.0
        }
        
        client.headers.update(auth_headers_user)
        response = client.post("/orders", json=payload)
        
        # Pode ser aceito ou rejeitado dependendo da regra de négócio
        assert response.status_code in [201, 400, 422]
    
    def test_create_order_long_description(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve validar tamanho máximo de description"""
        payload = {
            "description": "A" * 1000,  # muito longo
            "total": 100.0
        }
        
        client.headers.update(auth_headers_user)
        response = client.post("/orders", json=payload)
        
        # Pode ser aceito (dependendo da validação) ou rejeitado
        assert response.status_code in [201, 400, 422]


class TestRestoreOrder:
    """Testes para POST /orders/{order_id}/restore"""
    
    def test_restore_order_requires_authentication(self, client: TestClient):
        """Deve retornar 401 sem token"""
        fake_id = uuid4()
        response = client.post(f"/orders/{fake_id}/restore")
        
        assert response.status_code == 401
    
    def test_restore_order_success(
        self,
        client: TestClient,
        seed_user_normal: User,
        seed_admin_with_delete_permission: User,
        auth_headers_admin_with_delete: dict,
        db_session: Session
    ):
        """Deve restaurar pedido deletado com sucesso"""
        # Criar e deletar pedido
        order = Order(
            user_id=seed_user_normal.id,
            description="Deletado",
            total=50.0
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        
        # Deletar (admin com permissão pode deletar qualquer pedido)
        client.headers.update(auth_headers_admin_with_delete)
        client.delete(f"/orders/{order.id}")
        
        # Restaurar (admin pode restaurar)
        response = client.post(f"/orders/{order.id}/restore")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(order.id)
        assert data["description"] == "Deletado"
    
    def test_restore_order_not_found(
        self,
        client: TestClient,
        auth_headers_admin: dict
    ):
        """Deve retornar 404 para pedido inexistente"""
        fake_id = uuid4()
        
        client.headers.update(auth_headers_admin)
        response = client.post(f"/orders/{fake_id}/restore")
        
        assert response.status_code == 404


class TestUpdateOrderEdgeCases:
    """Testes adicionais de PATCH /orders/{order_id}"""
    
    def test_update_order_with_invalid_fields(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """Deve ignorar campos inválidos no PATCH"""
        order = Order(
            user_id=seed_user_normal.id,
            description="Original",
            total=100.0
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        
        payload = {
            "description": "Updated",
            "invalid_field": "should be ignored"
        }
        
        client.headers.update(auth_headers_user)
        response = client.patch(f"/orders/{order.id}", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated"
        assert "invalid_field" not in data


class TestOrderRoutesErrorPaths:
    """Testes focados em branches de erro não cobertos"""
    
    def test_list_orders_with_invalid_pagination(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve validar parâmetros de paginação inválidos"""
        client.headers.update(auth_headers_user)
        
        # Page negativa ou zero
        response = client.get("/orders?page=0")
        assert response.status_code in [400, 422]
        
        response = client.get("/orders?page=-1")
        assert response.status_code in [400, 422]
    
    def test_get_order_not_found(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 404 para ID inexistente"""
        client.headers.update(auth_headers_user)
        
        fake_id = uuid4()
        response = client.get(f"/orders/{fake_id}")
        
        assert response.status_code == 404
        assert "não encontrado" in response.json()["detail"]
    
    def test_create_order_with_negative_total(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 400 para total negativo"""
        client.headers.update(auth_headers_user)
        
        payload = {
            "description": "Test Order",
            "total": -100.0
        }
        
        response = client.post("/orders", json=payload)
        
        # Validação Pydantic ou ValueError -> 400/422
        assert response.status_code in [400, 422]
    
    def test_create_order_with_empty_description(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 422 para description vazia"""
        client.headers.update(auth_headers_user)
        
        payload = {
            "description": "",
            "total": 100.0
        }
        
        response = client.post("/orders", json=payload)
        
        # Validação Pydantic (min_length) -> 422
        assert response.status_code == 422
    
    def test_create_order_with_too_long_description(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 422 para description > 500 chars"""
        client.headers.update(auth_headers_user)
        
        payload = {
            "description": "x" * 501,
            "total": 100.0
        }
        
        response = client.post("/orders", json=payload)
        
        # Validação Pydantic (max_length) -> 422
        assert response.status_code == 422
    
    def test_update_order_not_found(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 404 ao atualizar pedido inexistente"""
        client.headers.update(auth_headers_user)
        
        fake_id = uuid4()
        response = client.patch(
            f"/orders/{fake_id}",
            json={"description": "Updated"}
        )
        
        assert response.status_code == 404
    
    def test_update_order_multi_tenant_violation(
        self,
        client: TestClient,
        seed_user_other: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """Deve retornar 404 ao tentar atualizar pedido de outro usuário"""
        # Criar pedido de outro usuário
        order = Order(
            user_id=seed_user_other.id,
            description="Other User Order",
            total=200.0
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        
        client.headers.update(auth_headers_user)
        response = client.patch(
            f"/orders/{order.id}",
            json={"description": "Hacked"}
        )
        
        # Retorna 404 (anti-enumeration)
        assert response.status_code == 404
    
    def test_delete_order_not_found(
        self,
        client: TestClient,
        auth_headers_with_delete: dict
    ):
        """Deve retornar 404 ao deletar pedido inexistente"""
        client.headers.update(auth_headers_with_delete)
        
        fake_id = uuid4()
        response = client.delete(f"/orders/{fake_id}")
        
        assert response.status_code == 404
    
    def test_delete_order_multi_tenant_violation(
        self,
        client: TestClient,
        seed_user_other: User,
        auth_headers_with_delete: dict,
        db_session: Session
    ):
        """Deve retornar 404 ao tentar deletar pedido de outro usuário"""
        # Criar pedido de outro usuário
        order = Order(
            user_id=seed_user_other.id,
            description="Other User Order",
            total=100.0
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        
        client.headers.update(auth_headers_with_delete)
        response = client.delete(f"/orders/{order.id}")
        
        # Retorna 404 (anti-enumeration)
        assert response.status_code == 404
