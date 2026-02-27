"""
Testes de validação para ReportService - Coverage estratégico
COVERAGE TARGET: report_service.py validações (linhas 37, 41-43, 287-293)
"""
import pytest
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.services.report_service import ReportService


class TestReportServiceDateValidations:
    """
    Testes de validação de data range.
    
    TARGET: Cobrir validate_date_range (linhas 37, 41-43)
    ROI: ~1.5% coverage
    """
    
    def test_validate_date_range_inverted_dates_raises_error(self):
        """
        COVERAGE: report_service.py:37 - ValueError quando date_from > date_to
        
        Regra: date_from não pode ser maior que date_to
        """
        # Arrange
        date_from = date(2024, 12, 31)
        date_to = date(2024, 1, 1)  # Invertido
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ReportService.validate_date_range(date_from, date_to)
        
        error_message = str(exc_info.value)
        assert "date_from" in error_message
        assert "não pode ser maior que date_to" in error_message
        assert "2024-12-31" in error_message
        assert "2024-01-01" in error_message
    
    def test_validate_date_range_too_large_raises_error(self):
        """
        COVERAGE: report_service.py:41-43 - ValueError quando intervalo > 366 dias
        
        Regra: Intervalo máximo de 366 dias (MAX_DATE_RANGE_DAYS)
        """
        # Arrange - 367 dias (366 + 1)
        date_from = date(2024, 1, 1)
        date_to = date(2025, 1, 2)  # 367 dias
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ReportService.validate_date_range(date_from, date_to)
        
        error_message = str(exc_info.value)
        assert "Intervalo muito grande" in error_message
        assert "367" in error_message
        assert "366" in error_message
        assert "Máximo permitido" in error_message
    
    def test_validate_date_range_valid_dates_succeeds(self):
        """
        Validação positiva: datas válidas não lançam erro
        """
        # Arrange - 30 dias (válido)
        date_from = date(2024, 1, 1)
        date_to = date(2024, 1, 31)
        
        # Act & Assert - não deve lançar erro
        ReportService.validate_date_range(date_from, date_to)
        
        # Arrange - 366 dias exato (limite válido)
        date_from = date(2024, 1, 1)
        date_to = date(2025, 1, 1)  # Exatamente 366 dias
        
        # Act & Assert - não deve lançar erro
        ReportService.validate_date_range(date_from, date_to)


class TestReportServiceTopEntriesValidations:
    """
    Testes de validação para get_top_entries.
    
    TARGET: Cobrir validações de kind e status (linhas 287-293)
    ROI: ~1.2% coverage
    """
    
    def test_get_top_entries_invalid_kind_raises_error(self, db_session: Session):
        """
        COVERAGE: report_service.py:287-289 - ValueError quando kind é inválido
        
        Regra: kind deve estar em VALID_KINDS = ['revenue', 'expense']
        """
        # Arrange
        date_from = date(2024, 1, 1)
        date_to = date(2024, 1, 31)
        
        # Act & Assert - kind inválido
        with pytest.raises(ValueError) as exc_info:
            ReportService.get_top_entries(
                db=db_session,
                kind="invalid_kind",
                status="pending",
                date_from=date_from,
                date_to=date_to,
                limit=10
            )
        
        error_message = str(exc_info.value)
        assert "kind inválido" in error_message
        assert "invalid_kind" in error_message
        assert "revenue" in error_message
        
        # Act & Assert - outro kind inválido
        with pytest.raises(ValueError) as exc_info:
            ReportService.get_top_entries(
                db=db_session,
                kind="income",  # Não existe, deve ser "revenue"
                status="pending",
                date_from=date_from,
                date_to=date_to,
                limit=10
            )
        
        error_message = str(exc_info.value)
        assert "kind inválido" in error_message
    
    def test_get_top_entries_invalid_status_raises_error(self, db_session: Session):
        """
        COVERAGE: report_service.py:291-293 - ValueError quando status é inválido
        
        Regra: status deve estar em VALID_STATUSES = ['pending', 'paid', 'canceled']
        """
        # Arrange
        date_from = date(2024, 1, 1)
        date_to = date(2024, 1, 31)
        
        # Act & Assert - status inválido
        with pytest.raises(ValueError) as exc_info:
            ReportService.get_top_entries(
                db=db_session,
                kind="revenue",
                status="invalid_status",
                date_from=date_from,
                date_to=date_to,
                limit=10
            )
        
        error_message = str(exc_info.value)
        assert "status inválido" in error_message
        assert "invalid_status" in error_message
        assert "pending" in error_message
        
        # Act & Assert - outro status inválido
        with pytest.raises(ValueError) as exc_info:
            ReportService.get_top_entries(
                db=db_session,
                kind="revenue",
                status="completed",  # Não existe, deve ser "paid"
                date_from=date_from,
                date_to=date_to,
                limit=10
            )
        
        error_message = str(exc_info.value)
        assert "status inválido" in error_message
    
    def test_get_top_entries_limit_adjustments(self, db_session: Session):
        """
        Validação de ajuste de limit (< 1 ou > MAX_TOP_LIMIT).
        
        Não lança erro, apenas ajusta para valores válidos.
        """
        # Arrange
        date_from = date(2024, 1, 1)
        date_to = date(2024, 1, 31)
        
        # Act - limit < 1 (deve usar DEFAULT_TOP_LIMIT = 10)
        result = ReportService.get_top_entries(
            db=db_session,
            kind="revenue",
            status="pending",
            date_from=date_from,
            date_to=date_to,
            limit=0
        )
        
        # Assert - retorna estrutura válida
        assert "items" in result
        assert "total" in result
        
        # Act - limit > MAX_TOP_LIMIT (deve usar MAX_TOP_LIMIT = 50)
        result = ReportService.get_top_entries(
            db=db_session,
            kind="revenue",
            status="pending",
            date_from=date_from,
            date_to=date_to,
            limit=9999
        )
        
        # Assert - retorna estrutura válida
        assert "items" in result
        assert "total" in result
