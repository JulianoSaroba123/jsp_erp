"""
Testes para app/core/errors.py

Coverage target: 90%+
Covers: sanitize_error_message com diferentes ENVIRONMENTs
"""
import pytest
from unittest.mock import patch, MagicMock
from app.core.errors import sanitize_error_message


class TestSanitizeErrorMessage:
    """Testes para sanitize_error_message()"""
    
    @patch('app.core.errors.ENVIRONMENT', 'development')
    @patch('app.core.errors.DEBUG', False)
    @patch('app.core.errors.logger')
    def test_sanitize_error_in_development_returns_details(self, mock_logger):
        """Em development, deve retornar detalhes do erro"""
        error = ValueError("Divisão por zero")
        
        result = sanitize_error_message(error, "Erro ao calcular total")
        
        # Deve incluir detalhes do erro original
        assert "Erro ao calcular total" in result
        assert "Divisão por zero" in result
        
        # Deve logar o erro
        mock_logger.error.assert_called_once()
    
    @patch('app.core.errors.ENVIRONMENT', 'production')
    @patch('app.core.errors.DEBUG', False)
    @patch('app.core.errors.logger')
    def test_sanitize_error_in_production_hides_details(self, mock_logger):
        """Em production, deve ocultar detalhes sensíveis"""
        error = Exception("Connection to database failed: password=secret123")
        
        result = sanitize_error_message(error, "Erro interno do servidor")
        
        # Deve retornar APENAS mensagem genérica
        assert result == "Erro interno do servidor"
        
        # NÃO deve vazar senha ou detalhes sensíveis
        assert "password" not in result
        assert "secret123" not in result
        assert "Connection" not in result
        
        # Deve logar o erro completo (para análise interna)
        mock_logger.error.assert_called_once()
    
    @patch('app.core.errors.ENVIRONMENT', 'test')
    @patch('app.core.errors.DEBUG', True)
    @patch('app.core.errors.logger')
    def test_sanitize_error_with_debug_true_returns_details(self, mock_logger):
        """Com DEBUG=True, deve retornar detalhes mesmo fora de development"""
        error = RuntimeError("NoneType has no attribute 'id'")
        
        result = sanitize_error_message(error, "Erro ao processar pedido")
        
        # DEBUG ativo deve mostrar detalhes
        assert "Erro ao processar pedido" in result
        assert "NoneType" in result
        
        mock_logger.error.assert_called_once()
    
    @patch('app.core.errors.ENVIRONMENT', 'production')
    @patch('app.core.errors.DEBUG', False)
    @patch('app.core.errors.logger')
    def test_sanitize_error_logs_with_exc_info(self, mock_logger):
        """Deve sempre logar com exc_info=True (stack trace)"""
        error = Exception("Erro de teste")
        
        sanitize_error_message(error, "Mensagem genérica")
        
        # Verificar que logger.error foi chamado com exc_info=True
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        
        # Verifica que exc_info=True foi passado
        assert call_args[1].get('exc_info') is True
    
    @patch('app.core.errors.ENVIRONMENT', 'development')
    @patch('app.core.errors.DEBUG', False)
    @patch('app.core.errors.logger')
    def test_sanitize_error_with_empty_error_message(self, mock_logger):
        """Deve funcionar mesmo com erro sem mensagem"""
        error = ValueError("")  # mensagem vazia
        
        result = sanitize_error_message(error, "Erro de validação")
        
        # Deve incluir a mensagem genérica
        assert "Erro de validação" in result
        
        mock_logger.error.assert_called_once()
    
    @patch('app.core.errors.ENVIRONMENT', 'production')
    @patch('app.core.errors.DEBUG', False)
    @patch('app.core.errors.logger')
    def test_sanitize_error_with_custom_generic_message(self, mock_logger):
        """Deve usar mensagem genérica customizada"""
        error = Exception("Detalhes sensíveis")
        
        result = sanitize_error_message(error, "Operação não permitida")
        
        assert result == "Operação não permitida"
        mock_logger.error.assert_called_once()
    
    @patch('app.core.errors.ENVIRONMENT', 'development')
    @patch('app.core.errors.DEBUG', False)
    @patch('app.core.errors.logger')
    def test_sanitize_error_with_special_characters(self, mock_logger):
        """Deve lidar com caracteres especiais no erro"""
        error = Exception("Erro: <script>alert('xss')</script>")
        
        result = sanitize_error_message(error, "Erro ao processar entrada")
        
        # Em development, deve incluir os detalhes (o sanitization seria feito pelo FastAPI)
        assert "Erro ao processar entrada" in result
        assert "<script>" in result
        
        mock_logger.error.assert_called_once()
    
    @patch('app.core.errors.ENVIRONMENT', 'production')
    @patch('app.core.errors.DEBUG', False)
    @patch('app.core.errors.logger')
    def test_sanitize_error_default_generic_message(self, mock_logger):
        """Deve usar mensagem genérica padrão se não fornecida"""
        error = Exception("Database connection timeout")
        
        # Sem fornecer generic_message (usa default)
        result = sanitize_error_message(error)
        
        assert result == "Erro interno do servidor"
        mock_logger.error.assert_called_once()


class TestErrorSanitizationIntegration:
    """Testes de integração para sanitização de erros"""
    
    @patch('app.core.errors.ENVIRONMENT', 'production')
    @patch('app.core.errors.DEBUG', False)
    @patch('app.core.errors.logger')
    def test_multiple_errors_sanitization(self, mock_logger):
        """Deve sanitizar múltiplos erros independentemente"""
        errors = [
            ValueError("Invalid input: email"),
            KeyError("missing_field"),
            RuntimeError("timeout after 30s")
        ]
        
        results = [
            sanitize_error_message(e, "Erro de validação")
            for e in errors
        ]
        
        # Todos devem retornar a mesma mensagem genérica
        assert all(r == "Erro de validação" for r in results)
        
        # Todos devem ter sido logados
        assert mock_logger.error.call_count == 3
    
    @patch('app.core.errors.logger')
    def test_sanitization_with_different_environments(self, mock_logger):
        """Testa comportamento em diferentes ambientes"""
        error = Exception("Sensitive data: API_KEY=abc123")
        
        # Development - mostra detalhes
        with patch('app.core.errors.ENVIRONMENT', 'development'):
            with patch('app.core.errors.DEBUG', False):
                dev_result = sanitize_error_message(error, "Erro")
                assert "Sensitive data" in dev_result
                assert "API_KEY" in dev_result
        
        # Production - oculta detalhes
        with patch('app.core.errors.ENVIRONMENT', 'production'):
            with patch('app.core.errors.DEBUG', False):
                prod_result = sanitize_error_message(error, "Erro")
                assert prod_result == "Erro"
                assert "API_KEY" not in prod_result
