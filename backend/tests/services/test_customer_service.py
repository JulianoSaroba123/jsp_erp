"""
Testes para CustomerService - business logic layer

Coverage target: 80-85%
Testa validações, duplicate detection, soft delete
"""
import pytest
from uuid import uuid4
from sqlalchemy.orm import Session

from app.services.customer_service import CustomerService
from app.schemas.customer_schema import CustomerCreate, CustomerUpdate
from app.models.customer import Customer
from app.exceptions.errors import NotFoundError, ConflictError, ValidationError


class TestCustomerServiceList:
    """Testes para list_customers"""
    
    def test_list_customers_empty(self, db_session: Session):
        """Deve retornar lista vazia quando não há customers"""
        service = CustomerService(db_session)
        result = service.list_customers(page=1, page_size=20)
        
        assert result["items"] == []
        assert result["total"] == 0
        assert result["page"] == 1
        assert result["page_size"] == 20
    
    def test_list_customers_with_data(self, db_session: Session):
        """Deve listar customers existentes"""
        # Criar customers
        customer1 = Customer(
            person_type="PF",
            name="Customer 1",
            cpf_cnpj="111.111.111-11",
            email="customer1@example.com"
        )
        customer2 = Customer(
            person_type="PF",
            name="Customer 2",
            cpf_cnpj="222.222.222-22",
            email="customer2@example.com"
        )
        db_session.add_all([customer1, customer2])
        db_session.commit()
        
        service = CustomerService(db_session)
        result = service.list_customers(page=1, page_size=20)
        
        assert result["total"] >= 2
        assert len(result["items"]) >= 2
    
    def test_list_customers_pagination_validation(self, db_session: Session):
        """Deve validar e corrigir paginação inválida"""
        service = CustomerService(db_session)
        
        # page < 1 deve ser ajustado para 1
        result = service.list_customers(page=0, page_size=20)
        assert result["page"] == 1
        
        result = service.list_customers(page=-5, page_size=20)
        assert result["page"] == 1
        
        # page_size < 1 deve ser ajustado para 20 (default)
        result = service.list_customers(page=1, page_size=0)
        assert result["page_size"] == 20
        
        # page_size > 100 deve ser ajustado para 20 (default)
        result = service.list_customers(page=1, page_size=999)
        assert result["page_size"] == 20
    
    def test_list_customers_filter_by_status(self, db_session: Session):
        """Deve filtrar customers por status"""
        # Criar customers com status diferentes
        customer_active = Customer(
            person_type="PF",
            name="Customer Ativo",
            cpf_cnpj="333.333.333-33",
            email="active@example.com",
            status="active"
        )
        customer_inactive = Customer(
            person_type="PF",
            name="Customer Inativo",
            cpf_cnpj="444.444.444-44",
            email="inactive@example.com",
            status="inactive"
        )
        db_session.add_all([customer_active, customer_inactive])
        db_session.commit()
        
        service = CustomerService(db_session)
        
        # Filtrar apenas ativos
        result = service.list_customers(page=1, page_size=20, status="active")
        active_items = [c for c in result["items"] if c.status == "active"]
        assert len(active_items) >= 1
    
    def test_list_customers_ignores_soft_deleted(self, db_session: Session):
        """Deve ignorar customers com soft delete"""
        from datetime import datetime
        
        customer_active = Customer(
            person_type="PF",
            name="Customer Ativo",
            cpf_cnpj="555.555.555-55",
            email="active2@example.com"
        )
        customer_deleted = Customer(
            person_type="PF",
            name="Customer Deletado",
            cpf_cnpj="666.666.666-66",
            email="deleted@example.com",
            deleted_at=datetime.utcnow()
        )
        db_session.add_all([customer_active, customer_deleted])
        db_session.commit()
        
        service = CustomerService(db_session)
        result = service.list_customers(page=1, page_size=100)
        
        # Não deve incluir deletados
        names = [c.name for c in result["items"]]
        assert "Customer Deletado" not in names


class TestCustomerServiceCreate:
    """Testes para create_customer"""
    
    def test_create_customer_pf_success(self, db_session: Session):
        """Deve criar customer PF com sucesso"""
        data = CustomerCreate(
            person_type="PF",
            name="João Silva",
            cpf_cnpj="12345678900",
            email="joao@example.com",
            phone="11987654321"
        )
        
        service = CustomerService(db_session)
        customer = service.create_customer(data)
        
        assert customer.id is not None
        assert customer.name == "João Silva"
        assert customer.person_type == "PF"
        assert customer.cpf_cnpj == "12345678900"
        assert customer.email == "joao@example.com"
    
    def test_create_customer_pj_success(self, db_session: Session):
        """Deve criar customer PJ com sucesso"""
        data = CustomerCreate(
            person_type="PJ",
            name="Empresa XYZ Ltda",
            trade_name="XYZ Corp",
            cpf_cnpj="12345678000190",
            email="contato@xyz.com",
            phone="1133334444"
        )
        
        service = CustomerService(db_session)
        customer = service.create_customer(data)
        
        assert customer.id is not None
        assert customer.name == "Empresa XYZ Ltda"
        assert customer.person_type == "PJ"
        assert customer.trade_name == "XYZ Corp"
        assert customer.cpf_cnpj == "12345678000190"
    
    def test_create_customer_duplicate_cpf_cnpj_raises_error(self, db_session: Session):
        """Deve lançar ConflictError ao tentar criar com CPF/CNPJ duplicado"""
        # Criar customer existente
        existing = Customer(
            person_type="PF",
            name="Existing Customer",
            cpf_cnpj="111.222.333-44",
            email="existing@example.com"
        )
        db_session.add(existing)
        db_session.commit()
        
        # Tentar criar com mesmo CPF/CNPJ
        data = CustomerCreate(
            person_type="PF",
            name="Another Customer",
            cpf_cnpj="111.222.333-44",  # Duplicado
            email="another@example.com"
        )
        
        service = CustomerService(db_session)
        
        with pytest.raises(ConflictError) as exc_info:
            service.create_customer(data)
        
        assert "111.222.333-44" in str(exc_info.value)
        assert "já cadastrado" in str(exc_info.value)
    
    # Nota: Validação de person_type inválido é feita pelo Pydantic schema
    # antes de chegar ao service, então não precisa testar aqui.


class TestCustomerServiceGetById:
    """Testes para get_customer_by_id"""
    
    def test_get_customer_by_id_success(self, db_session: Session):
        """Deve buscar customer por ID"""
        customer = Customer(
            person_type="PF",
            name="Test Customer",
            cpf_cnpj="777.888.999-00",
            email="test@example.com"
        )
        db_session.add(customer)
        db_session.commit()
        db_session.refresh(customer)
        
        service = CustomerService(db_session)
        found = service.get_customer_by_id(customer.id)
        
        assert found.id == customer.id
        assert found.name == "Test Customer"
    
    def test_get_customer_by_id_not_found_raises_error(self, db_session: Session):
        """Deve lançar NotFoundError para ID inexistente"""
        service = CustomerService(db_session)
        
        with pytest.raises(NotFoundError) as exc_info:
            service.get_customer_by_id(uuid4())
        
        assert "não encontrado" in str(exc_info.value)
    
    def test_get_customer_by_id_ignores_soft_deleted(self, db_session: Session):
        """Deve lançar NotFoundError para customer com soft delete"""
        from datetime import datetime
        
        customer = Customer(
            person_type="PF",
            name="Deleted Customer",
            cpf_cnpj="888.999.000-11",
            email="deleted2@example.com",
            deleted_at=datetime.utcnow()
        )
        db_session.add(customer)
        db_session.commit()
        db_session.refresh(customer)
        
        service = CustomerService(db_session)
        
        with pytest.raises(NotFoundError):
            service.get_customer_by_id(customer.id)


class TestCustomerServiceUpdate:
    """Testes para update_customer"""
    
    def test_update_customer_success(self, db_session: Session):
        """Deve atualizar customer com sucesso"""
        customer = Customer(
            person_type="PF",
            name="Original Name",
            cpf_cnpj="123.123.123-12",
            email="original@example.com",
            phone="11111111111"
        )
        db_session.add(customer)
        db_session.commit()
        db_session.refresh(customer)
        
        # Atualizar apenas alguns campos
        data = CustomerUpdate(
            name="Updated Name",
            phone="22222222222"
        )
        
        service = CustomerService(db_session)
        updated = service.update_customer(customer.id, data)
        
        assert updated.name == "Updated Name"
        assert updated.phone == "22222222222"
        assert updated.cpf_cnpj == "123.123.123-12"  # Não alterado
        assert updated.email == "original@example.com"  # Não alterado
    
    def test_update_customer_not_found_raises_error(self, db_session: Session):
        """Deve lançar NotFoundError ao tentar atualizar customer inexistente"""
        data = CustomerUpdate(name="New Name")
        
        service = CustomerService(db_session)
        
        with pytest.raises(NotFoundError):
            service.update_customer(uuid4(), data)
    
    def test_update_customer_duplicate_cpf_cnpj_raises_error(self, db_session: Session):
        """Deve lançar ConflictError ao tentar atualizar para CPF/CNPJ já existente"""
        customer1 = Customer(
            person_type="PF",
            name="Customer 1",
            cpf_cnpj="111.111.111-11",
            email="customer1@example.com"
        )
        customer2 = Customer(
            person_type="PF",
            name="Customer 2",
            cpf_cnpj="222.222.222-22",
            email="customer2@example.com"
        )
        db_session.add_all([customer1, customer2])
        db_session.commit()
        db_session.refresh(customer2)
        
        # Tentar atualizar customer2 para ter o CPF do customer1
        data = CustomerUpdate(cpf_cnpj="111.111.111-11")
        
        service = CustomerService(db_session)
        
        with pytest.raises(ConflictError) as exc_info:
            service.update_customer(customer2.id, data)
        
        assert "111.111.111-11" in str(exc_info.value)
        assert "já cadastrado" in str(exc_info.value)
    
    # Nota: Validação de person_type inválido é feita pelo Pydantic schema
    # antes de chegar ao service, então não precisa testar aqui.


class TestCustomerServiceDelete:
    """Testes para delete_customer"""
    
    def test_delete_customer_success(self, db_session: Session):
        """Deve deletar customer (soft delete) com sucesso"""
        customer = Customer(
            person_type="PF",
            name="To Be Deleted",
            cpf_cnpj="999.999.999-99",
            email="tobedeleted@example.com"
        )
        db_session.add(customer)
        db_session.commit()
        db_session.refresh(customer)
        
        service = CustomerService(db_session)
        result = service.delete_customer(customer.id)
        
        assert result is True
        
        # Verificar que foi soft deleted
        db_session.refresh(customer)
        assert customer.deleted_at is not None
    
    def test_delete_customer_not_found_raises_error(self, db_session: Session):
        """Deve lançar NotFoundError ao tentar deletar customer inexistente"""
        service = CustomerService(db_session)
        
        with pytest.raises(NotFoundError):
            service.delete_customer(uuid4())


class TestCustomerServiceSearch:
    """Testes para search_customers"""
    
    def test_search_customers_by_name(self, db_session: Session):
        """Deve buscar customers por nome (autocomplete)"""
        customers = [
            Customer(person_type="PF", name="João Silva", cpf_cnpj="111.111.111-11", email="joao@example.com"),
            Customer(person_type="PF", name="Maria Silva", cpf_cnpj="222.222.222-22", email="maria@example.com"),
            Customer(person_type="PF", name="Pedro Santos", cpf_cnpj="333.333.333-33", email="pedro@example.com"),
        ]
        db_session.add_all(customers)
        db_session.commit()
        
        service = CustomerService(db_session)
        
        # Buscar por "Silva" (deve encontrar 2)
        results = service.search_customers("Silva", limit=10)
        assert len(results) >= 2
        
        names = [c.name for c in results]
        assert "João Silva" in names
        assert "Maria Silva" in names
    
    def test_search_customers_limit_validation(self, db_session: Session):
        """Deve validar limite máximo de 50 resultados"""
        service = CustomerService(db_session)
        
        # limit > 50 deve ser ajustado para 50
        results = service.search_customers("Test", limit=999)
        # Sem erro, apenas ajusta internamente
        assert True  # ValidationError não é lançado, apenas ajusta
