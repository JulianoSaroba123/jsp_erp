"""
Testes para módulo de password (hash e verify)
Coverage atual: 43% → Meta: 100%
"""
import pytest
from app.security.password import hash_password, verify_password


class TestHashPassword:
    """Testes de hash de senha"""
    
    def test_hash_password_generates_valid_bcrypt(self):
        """Deve gerar hash bcrypt válido"""
        password = "minha_senha_secreta_123"
        hashed = hash_password(password)
        
        # Hash bcrypt sempre começa com $2b$
        assert hashed.startswith("$2b$")
        # Hash bcrypt tem comprimento específico (~60 chars)
        assert len(hashed) >= 59
    
    def test_hash_password_different_hashes_for_same_password(self):
        """Deve gerar hashes diferentes para a mesma senha (salt aleatório)"""
        password = "teste123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2  # Salts diferentes
        # Mas ambos devem verificar corretamente
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)
    
    def test_hash_password_empty_string(self):
        """Deve gerar hash até para senha vazia"""
        hashed = hash_password("")
        assert hashed.startswith("$2b$")
        assert verify_password("", hashed)
    
    def test_hash_password_special_characters(self):
        """Deve funcionar com caracteres especiais"""
        password = "SenhaC0mple%a!@#$&*()"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed)
    
    def test_hash_password_unicode(self):
        """Deve funcionar com caracteres unicode"""
        password = "Sẽnha_çom_açéntos_é_ñ"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed)
    
    def test_hash_password_very_long(self):
        """Deve funcionar com senhas muito longas"""
        password = "a" * 200
        hashed = hash_password(password)
        
        assert verify_password(password, hashed)


class TestVerifyPassword:
    """Testes de verificação de senha"""
    
    def test_verify_password_correct(self):
        """Deve retornar True para senha correta"""
        password = "senha_correta"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Deve retornar False para senha incorreta"""
        password = "senha_correta"
        hashed = hash_password(password)
        
        assert verify_password("senha_errada", hashed) is False
    
    def test_verify_password_case_sensitive(self):
        """Deve ser case-sensitive"""
        password = "SenhaComMaiusculas"
        hashed = hash_password(password)
        
        assert verify_password("SenhaComMaiusculas", hashed) is True
        assert verify_password("senhacommaiusculas", hashed) is False
        assert verify_password("SENHACOMMAIUSCULAS", hashed) is False
    
    def test_verify_password_empty_against_empty(self):
        """Senha vazia deve verificar contra hash de senha vazia"""
        hashed = hash_password("")
        
        assert verify_password("", hashed) is True
        assert verify_password("alguma_coisa", hashed) is False
    
    def test_verify_password_whitespace_matters(self):
        """Espaços em branco devem ser considerados"""
        password = "senha com espacos"
        hashed = hash_password(password)
        
        assert verify_password("senha com espacos", hashed) is True
        assert verify_password("senhacom espacos", hashed) is False
        assert verify_password("senha  com espacos", hashed) is False
    
    def test_verify_password_invalid_hash_format(self):
        """Deve lançar exceção para hash inválido"""
        with pytest.raises(Exception):  # bcrypt lança ValueError
            verify_password("qualquer", "hash_invalido")
    
    def test_verify_password_none_values(self):
        """Deve lançar exceção para valores None"""
        password = "teste"
        hashed = hash_password(password)
        
        with pytest.raises((TypeError, AttributeError)):
            verify_password(None, hashed)
        
        with pytest.raises((TypeError, AttributeError)):
            verify_password(password, None)


class TestPasswordIntegration:
    """Testes de integração hash + verify"""
    
    def test_full_flow_hash_then_verify(self):
        """Fluxo completo: hash → armazenar → verificar"""
        # Simula registro de usuário
        user_password = "MinhaS3nhaS3gur4!"
        stored_hash = hash_password(user_password)
        
        # Simula login correto
        assert verify_password("MinhaS3nhaS3gur4!", stored_hash) is True
        
        # Simula tentativas incorretas
        assert verify_password("senha_errada", stored_hash) is False
        assert verify_password("", stored_hash) is False
        assert verify_password("MinhaS3nhaS3gur4", stored_hash) is False  # Faltou !
    
    def test_multiple_users_different_hashes(self):
        """Múltiplos usuários com mesma senha devem ter hashes diferentes"""
        senha_comum = "senha123"
        
        hash_user1 = hash_password(senha_comum)
        hash_user2 = hash_password(senha_comum)
        hash_user3 = hash_password(senha_comum)
        
        # Todos diferentes (salts únicos)
        assert hash_user1 != hash_user2
        assert hash_user2 != hash_user3
        assert hash_user1 != hash_user3
        
        # Mas todos verificam corretamente
        assert verify_password(senha_comum, hash_user1)
        assert verify_password(senha_comum, hash_user2)
        assert verify_password(senha_comum, hash_user3)
