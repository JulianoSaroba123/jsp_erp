"""
Testes de validação para OrderService - Coverage estratégico
COVERAGE TARGET: order_service.py validações (linhas 83, 89, 94)
"""
import pytest
from uuid import uuid4
from sqlalchemy.orm import Session

from app.services.order_service import OrderService


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
