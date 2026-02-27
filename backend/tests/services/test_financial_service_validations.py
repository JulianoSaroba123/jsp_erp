"""
Testes de validação para FinancialService - Coverage estratégico
COVERAGE TARGET: financial_service.py validações (linhas 62-68, 133-144, 253)
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from decimal import Decimal

from app.services.financial_service import FinancialService
from app.models.financial_entry import FinancialEntry


class TestFinancialServiceListValidations:
    """
    Testes de validação para list_entries_paginated.
    
    TARGET: Cobrir validações de filtros (status e kind inválidos)
    ROI: ~0.8% coverage
    """
    
    def test_list_entries_invalid_status_raises_error(self, db_session: Session, seed_user_normal):
        """
        COVERAGE: financial_service.py:62-64 - ValueError quando status é inválido
        
        Regra: status deve estar em VALID_STATUSES = ['pending', 'paid', 'canceled']
        """
        # Arrange
        service = FinancialService(db_session)
        
        # Act & Assert - status inválido
        with pytest.raises(ValueError) as exc_info:
            service.list_entries_paginated(
                user_id=seed_user_normal.id,
                status="invalid_status"
            )
        
        error_message = str(exc_info.value)
        assert "status inválido" in error_message
        assert "invalid_status" in error_message
        assert "pending" in error_message  # Deve listar opções válidas
        
        # Act & Assert - outro status inválido
        with pytest.raises(ValueError) as exc_info:
            service.list_entries_paginated(
                user_id=seed_user_normal.id,
                status="completed"  # Não existe, deve ser "paid"
            )
        
        error_message = str(exc_info.value)
        assert "status inválido" in error_message
    
    def test_list_entries_invalid_kind_raises_error(self, db_session: Session, seed_user_normal):
        """
        COVERAGE: financial_service.py:66-68 - ValueError quando kind é inválido
        
        Regra: kind deve estar em VALID_KINDS = ['revenue', 'expense']
        """
        # Arrange
        service = FinancialService(db_session)
        
        # Act & Assert - kind inválido
        with pytest.raises(ValueError) as exc_info:
            service.list_entries_paginated(
                user_id=seed_user_normal.id,
                kind="invalid_kind"
            )
        
        error_message = str(exc_info.value)
        assert "kind inválido" in error_message
        assert "invalid_kind" in error_message
        assert "revenue" in error_message  # Deve listar opções válidas
        
        # Act & Assert - outro kind inválido
        with pytest.raises(ValueError) as exc_info:
            service.list_entries_paginated(
                user_id=seed_user_normal.id,
                kind="income"  # Não existe, deve ser "revenue"
            )
        
        error_message = str(exc_info.value)
        assert "kind inválido" in error_message


class TestFinancialServiceCreateValidations:
    """
    Testes de validação para create_entry.
    
    TARGET: Cobrir validações de amount, description e kind
    ROI: ~1.2% coverage
    """
    
    def test_create_entry_negative_amount_raises_error(self, db_session: Session, seed_user_normal):
        """
        COVERAGE: financial_service.py:139 - ValueError quando amount < 0
        
        Regra: amount deve ser >= 0
        """
        # Arrange
        service = FinancialService(db_session)
        
        # Act & Assert - amount negativo
        with pytest.raises(ValueError) as exc_info:
            service.create_entry(
                user_id=seed_user_normal.id,
                kind="expense",
                amount=-100.0,
                description="Test Entry"
            )
        assert "amount deve ser >= 0" in str(exc_info.value)
        
        # Act & Assert - amount muito negativo
        with pytest.raises(ValueError) as exc_info:
            service.create_entry(
                user_id=seed_user_normal.id,
                kind="expense",
                amount=-9999.99,
                description="Test Entry"
            )
        assert "amount deve ser >= 0" in str(exc_info.value)
        
        # Act & Assert - amount None (também deve falhar)
        with pytest.raises(ValueError) as exc_info:
            service.create_entry(
                user_id=seed_user_normal.id,
                kind="expense",
                amount=None,
                description="Test Entry"
            )
        assert "amount deve ser >= 0" in str(exc_info.value)
    
    def test_create_entry_empty_description_raises_error(self, db_session: Session, seed_user_normal):
        """
        COVERAGE: financial_service.py:144 - ValueError quando description é vazio
        
        Regra: description é obrigatório e não pode estar vazio após strip()
        """
        # Arrange
        service = FinancialService(db_session)
        
        # Act & Assert - description None
        with pytest.raises(ValueError) as exc_info:
            service.create_entry(
                user_id=seed_user_normal.id,
                kind="expense",
                amount=100.0,
                description=None
            )
        assert "description é obrigatório" in str(exc_info.value)
        
        # Act & Assert - description vazio
        with pytest.raises(ValueError) as exc_info:
            service.create_entry(
                user_id=seed_user_normal.id,
                kind="expense",
                amount=100.0,
                description=""
            )
        assert "description é obrigatório" in str(exc_info.value)
        
        # Act & Assert - description apenas espaços
        with pytest.raises(ValueError) as exc_info:
            service.create_entry(
                user_id=seed_user_normal.id,
                kind="expense",
                amount=100.0,
                description="   "
            )
        assert "description é obrigatório" in str(exc_info.value)
    
    def test_create_entry_invalid_kind_raises_error(self, db_session: Session, seed_user_normal):
        """
        COVERAGE: financial_service.py:133-136 - ValueError quando kind é inválido
        
        Regra: kind deve estar em VALID_KINDS = ['revenue', 'expense']
        """
        # Arrange
        service = FinancialService(db_session)
        
        # Act & Assert - kind inválido
        with pytest.raises(ValueError) as exc_info:
            service.create_entry(
                user_id=seed_user_normal.id,
                kind="invalid_kind",
                amount=100.0,
                description="Test Entry"
            )
        
        error_message = str(exc_info.value)
        assert "kind inválido" in error_message
        assert "invalid_kind" in error_message
        assert "revenue" in error_message  # Deve listar opções válidas


class TestFinancialServiceUpdateValidations:
    """
    Testes de validação para update_status.
    
    TARGET: Cobrir validação de status inválido
    ROI: ~0.5% coverage
    """
    
    def test_update_status_invalid_status_raises_error(self, db_session: Session, seed_user_normal):
        """
        COVERAGE: financial_service.py:253 - ValueError quando status é inválido
        
        Regra: new_status deve estar em VALID_STATUSES = ['pending', 'paid', 'canceled']
        """
        # Arrange
        service = FinancialService(db_session)
        
        # Criar entry válido para teste
        entry = FinancialEntry(
            user_id=seed_user_normal.id,
            kind='revenue',
            status='pending',
            amount=Decimal('100.00'),
            description='Test Entry',
            occurred_at=datetime.utcnow()
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)
        
        # Act & Assert - status inválido
        with pytest.raises(ValueError) as exc_info:
            service.update_status(
                db=db_session,
                entry=entry,
                new_status="completed"  # Não existe, deve ser "paid"
            )
        
        error_message = str(exc_info.value)
        assert "status inválido" in error_message
        assert "completed" in error_message
        assert "pending" in error_message  # Deve listar opções válidas
        
        # Act & Assert - outro status inválido
        with pytest.raises(ValueError) as exc_info:
            service.update_status(
                db=db_session,
                entry=entry,
                new_status="invalid_status"
            )
        
        error_message = str(exc_info.value)
        assert "status inválido" in error_message
