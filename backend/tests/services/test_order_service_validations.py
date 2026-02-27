"""
Testes de validação para OrderService - Coverage estratégico
COVERAGE TARGET: order_service.py validações (linhas 83, 89, 94, 283, 287)
"""
import pytest
from uuid import uuid4
from sqlalchemy.orm import Session

from app.services.order_service import OrderService
from app.models.order import Order


class TestOrderServiceValidations:
    """
    Testes de validação de regras de negócio do OrderService.
    
    TARGET: Cobrir branches de ValueError não testados anteriormente.
    ROI: ~1.2% coverage (3 branches críticos)
    """
    
    def test_create_order_empty_description_raises_error(self, db_session: Session, seed_user_normal):
        """
        COVERAGE: order_service.py:83 - ValueError quando description é vazio
        
        Regra: description é obrigatório e não pode estar vazio após strip()
        """
        # Act & Assert - description None
        with pytest.raises(ValueError) as exc_info:
            OrderService.create_order(
                db=db_session,
                user_id=seed_user_normal.id,
                description=None,
                total=100.0
            )
        assert "description é obrigatório" in str(exc_info.value)
        
        # Act & Assert - description vazio
        with pytest.raises(ValueError) as exc_info:
            OrderService.create_order(
                db=db_session,
                user_id=seed_user_normal.id,
                description="",
                total=100.0
            )
        assert "description é obrigatório" in str(exc_info.value)
        
        # Act & Assert - description apenas espaços
        with pytest.raises(ValueError) as exc_info:
            OrderService.create_order(
                db=db_session,
                user_id=seed_user_normal.id,
                description="   ",
                total=100.0
            )
        assert "description é obrigatório" in str(exc_info.value)
    
    def test_create_order_negative_total_raises_error(self, db_session: Session, seed_user_normal):
        """
        COVERAGE: order_service.py:89 - ValueError quando total é negativo
        
        Regra: total não pode ser negativo
        """
        # Act & Assert - total negativo
        with pytest.raises(ValueError) as exc_info:
            OrderService.create_order(
                db=db_session,
                user_id=seed_user_normal.id,
                description="Test Order",
                total=-50.0
            )
        assert "total não pode ser negativo" in str(exc_info.value)
        
        # Act & Assert - total muito negativo
        with pytest.raises(ValueError) as exc_info:
            OrderService.create_order(
                db=db_session,
                user_id=seed_user_normal.id,
                description="Test Order",
                total=-9999.99
            )
        assert "total não pode ser negativo" in str(exc_info.value)
    
    def test_create_order_invalid_user_id_raises_error(self, db_session: Session):
        """
        COVERAGE: order_service.py:94 - ValueError quando user_id não existe
        
        Regra: user_id deve existir no banco (integridade referencial)
        """
        # Arrange
        fake_user_id = uuid4()
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            OrderService.create_order(
                db=db_session,
                user_id=fake_user_id,
                description="Test Order",
                total=100.0
            )
        
        error_message = str(exc_info.value)
        assert "user_id inválido" in error_message
        assert str(fake_user_id) in error_message
        assert "não encontrado" in error_message


class TestOrderServiceDeleteValidations:
    """
    Testes de validação para delete_order.
    
    TARGET: Cobrir branches de ValueError em soft delete
    ROI: ~1.5% coverage (2 branches críticos)
    """
    
    def test_delete_order_requires_user_id(self, db_session: Session, seed_user_normal):
        """
        COVERAGE: order_service.py:283 - ValueError quando user_id é None
        
        Regra: user_id é obrigatório para soft delete (precisamos saber quem deletou)
        """
        # Criar order para teste
        order = Order(
            user_id=seed_user_normal.id,
            description="Test Order",
            total=100.0
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        
        # Act & Assert - user_id None
        with pytest.raises(ValueError) as exc_info:
            OrderService.delete_order(
                db=db_session,
                order_id=order.id,
                user_id=None,  # None é inválido
                is_admin=False
            )
        
        error_message = str(exc_info.value)
        assert "user_id é obrigatório" in error_message
        assert "soft delete" in error_message
    
    def test_delete_order_permission_denied_for_other_user(self, db_session: Session, seed_user_normal, seed_user_admin):
        """
        COVERAGE: order_service.py:287 - ValueError quando usuário tenta deletar pedido de outro
        
        Regra: Usuário não-admin só pode deletar seus próprios pedidos (multi-tenancy)
        """
        # Criar order do seed_user_normal
        order = Order(
            user_id=seed_user_normal.id,
            description="Normal User Order",
            total=100.0
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        
        # Act & Assert - seed_user_admin (não-admin) tentando deletar order de outro usuário
        with pytest.raises(ValueError) as exc_info:
            OrderService.delete_order(
                db=db_session,
                order_id=order.id,
                user_id=seed_user_admin.id,  # Usuário diferente do dono
                is_admin=False  # Não é admin
            )
        
        error_message = str(exc_info.value)
        assert "permissão" in error_message.lower()
        assert "deletar" in error_message.lower()
