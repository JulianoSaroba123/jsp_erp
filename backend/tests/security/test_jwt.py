"""
Testes para módulo JWT (create e decode tokens)
Coverage atual: 50% → Meta: 100%
"""
import pytest
from datetime import datetime, timedelta
from jose import JWTError

from app.security.jwt import create_access_token, decode_access_token


class TestCreateAccessToken:
    """Testes de criação de JWT access token"""
    
    def test_create_token_with_default_expiration(self):
        """Deve criar token com expiração padrão"""
        data = {"sub": "user_123", "role": "admin"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tem tamanho considerável
        assert "." in token  # JWT tem formato header.payload.signature
    
    def test_create_token_and_decode(self):
        """Token criado deve ser decodificável"""
        data = {"sub": "user_456", "email": "test@test.com"}
        token = create_access_token(data)
        
        decoded = decode_access_token(token)
        
        assert decoded["sub"] == "user_456"
        assert decoded["email"] == "test@test.com"
        assert "exp" in decoded  # Deve incluir expiração
    
    def test_create_token_with_custom_expiration(self):
        """Deve respeitar expiração customizada"""
        data = {"sub": "user_789"}
        custom_expiration = timedelta(minutes=5)
        
        token = create_access_token(data, expires_delta=custom_expiration)
        decoded = decode_access_token(token)
        
        # Verificar que expiração está próxima de 5 minutos no futuro
        exp_timestamp = decoded["exp"]
        exp_datetime = datetime.utcfromtimestamp(exp_timestamp)
        now = datetime.utcnow()
        
        time_diff = (exp_datetime - now).total_seconds()
        assert 290 < time_diff < 310  # ~5 minutos (300s ± 10s margem)
    
    def test_create_token_with_very_short_expiration(self):
        """Deve funcionar com expiração muito curta"""
        data = {"sub": "user_short"}
        short_expiration = timedelta(seconds=1)
        
        token = create_access_token(data, expires_delta=short_expiration)
        
        # Token deve ser válido imediatamente após criação
        decoded = decode_access_token(token)
        assert decoded["sub"] == "user_short"
    
    def test_create_token_with_empty_data(self):
        """Deve criar token mesmo com data vazio"""
        data = {}
        token = create_access_token(data)
        
        decoded = decode_access_token(token)
        assert "exp" in decoded  # Deve ter expiração
    
    def test_create_token_preserves_all_fields(self):
        """Deve preservar todos os campos do payload"""
        data = {
            "sub": "user_123",
            "email": "user@test.com",
            "role": "admin",
            "permissions": ["read", "write"],
            "metadata": {"department": "IT"}
        }
        
        token = create_access_token(data)
        decoded = decode_access_token(token)
        
        assert decoded["sub"] == "user_123"
        assert decoded["email"] == "user@test.com"
        assert decoded["role"] == "admin"
        assert decoded["permissions"] == ["read", "write"]
        assert decoded["metadata"] == {"department": "IT"}
    
    def test_create_token_does_not_mutate_original_data(self):
        """Não deve mutar o dicionário original"""
        data = {"sub": "user_123"}
        original_data = data.copy()
        
        create_access_token(data)
        
        # Data original não deve ter 'exp'
        assert "exp" not in data
        assert data == original_data


class TestDecodeAccessToken:
    """Testes de decodificação de JWT tokens"""
    
    def test_decode_valid_token(self):
        """Deve decodificar token válido"""
        data = {"sub": "user_decode_test", "custom_field": "value"}
        token = create_access_token(data)
        
        decoded = decode_access_token(token)
        
        assert decoded["sub"] == "user_decode_test"
        assert decoded["custom_field"] == "value"
    
    def test_decode_expired_token(self):
        """Deve lançar JWTError para token expirado"""
        import time
        
        data = {"sub": "user_expired"}
        # Token que expira em 1 segundo
        token = create_access_token(data, expires_delta=timedelta(seconds=1))
        
        # Aguardar expiração
        time.sleep(2)
        
        # Deve lançar exception
        with pytest.raises(JWTError):
            decode_access_token(token)
    
    def test_decode_invalid_token_format(self):
        """Deve lançar JWTError para token mal formatado"""
        invalid_tokens = [
            "token_invalido",
            "abc.def.ghi",
            "",
            "Bearer token_invalido",
        ]
        
        for invalid_token in invalid_tokens:
            with pytest.raises(JWTError):
                decode_access_token(invalid_token)
    
    def test_decode_token_with_wrong_secret(self):
        """Token assinado com secret diferente deve falhar"""
        # Criar token com secret customizado (simulando ataque)
        from jose import jwt
        
        fake_token = jwt.encode(
            {"sub": "hacker"},
            "secret_errado",
            algorithm="HS256"
        )
        
        with pytest.raises(JWTError):
            decode_access_token(fake_token)
    
    def test_decode_token_none(self):
        """Deve lançar erro para token None"""
        with pytest.raises((JWTError, TypeError, AttributeError)):
            decode_access_token(None)


class TestJWTIntegration:
    """Testes de integração do fluxo JWT"""
    
    def test_full_authentication_flow(self):
        """Simula fluxo completo de autenticação"""
        # 1. Usuário faz login, sistema cria token
        user_data = {
            "sub": "user_123",
            "email": "user@example.com",
            "role": "user"
        }
        token = create_access_token(user_data)
        
        # 2. Cliente envia token em requisição subsequente
        # 3. Sistema decodifica e valida
        decoded = decode_access_token(token)
        
        # 4. Sistema confirma identidade
        assert decoded["sub"] == "user_123"
        assert decoded["role"] == "user"
    
    def test_token_refresh_scenario(self):
        """Simula refresh de token antes de expirar"""
        # Token original com expiração curta
        original_data = {"sub": "user_refresh"}
        token1 = create_access_token(original_data, expires_delta=timedelta(minutes=5))
        
        # Decodificar token original
        decoded1 = decode_access_token(token1)
        
        # Criar novo token (refresh) com mesmos dados
        token2 = create_access_token(original_data, expires_delta=timedelta(minutes=30))
        decoded2 = decode_access_token(token2)
        
        # Ambos devem ter mesmo sub, mas expirations diferentes
        assert decoded1["sub"] == decoded2["sub"]
        assert decoded1["exp"] != decoded2["exp"]
        assert decoded2["exp"] > decoded1["exp"]
    
    def test_multiple_users_different_tokens(self):
        """Tokens de diferentes usuários devem ser únicos"""
        user1_data = {"sub": "user_1"}
        user2_data = {"sub": "user_2"}
        
        token1 = create_access_token(user1_data)
        token2 = create_access_token(user2_data)
        
        assert token1 != token2
        
        decoded1 = decode_access_token(token1)
        decoded2 = decode_access_token(token2)
        
        assert decoded1["sub"] == "user_1"
        assert decoded2["sub"] == "user_2"
    
    def test_token_with_permissions_enforcement(self):
        """Simula verificação de permissões via token"""
        admin_data = {
            "sub": "admin_user",
            "role": "admin",
            "permissions": ["read", "write", "delete"]
        }
        user_data = {
            "sub": "regular_user",
            "role": "user",
            "permissions": ["read"]
        }
        
        admin_token = create_access_token(admin_data)
        user_token = create_access_token(user_data)
        
        admin_decoded = decode_access_token(admin_token)
        user_decoded = decode_access_token(user_token)
        
        # Verificar permissões
        assert "delete" in admin_decoded["permissions"]
        assert "delete" not in user_decoded["permissions"]
