"""
Service para Customer - camada de regras de negócio.

Responsabilidades:
- Validações de negócio
- Orquestração de operações
- Gerenciamento de transações
- Conversão entre DTOs e Models
"""
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.repositories.customer_repository import CustomerRepository
from app.schemas.customer_schema import CustomerCreate, CustomerUpdate
from app.exceptions.errors import NotFoundError, ConflictError, ValidationError


class CustomerService:
    """Service para operações de Customer"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = CustomerRepository(db)
    
    def get_customer_by_id(self, customer_id: UUID) -> Customer:
        """
        Busca customer por ID.
        
        Raises:
            NotFoundError: Se customer não encontrado
        """
        customer = self.repo.get_by_id(customer_id)
        if not customer:
            raise NotFoundError(f"Customer {customer_id} não encontrado")
        return customer
    
    def list_customers(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Lista customers com paginação.
        
        Returns:
            {
                "items": [...],
                "page": 1,
                "page_size": 20,
                "total": 123
            }
        """
        # Validar paginação
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20
        
        # Buscar
        items, total = self.repo.list_all(page, page_size, status)
        
        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total
        }
    
    def create_customer(self, data: CustomerCreate) -> Customer:
        """
        Cria novo customer.
        
        Validações:
        - CPF/CNPJ único (se fornecido)
        - person_type válido ('PF' ou 'PJ')
        
        Raises:
            ConflictError: Se CPF/CNPJ já existe
            ValidationError: Se dados inválidos
        """
        # Validar person_type
        if data.person_type and data.person_type not in ['PF', 'PJ']:
            raise ValidationError("person_type deve ser 'PF' ou 'PJ'")
        
        # Verificar CPF/CNPJ duplicado
        if data.cpf_cnpj:
            existing = self.repo.get_by_cpf_cnpj(data.cpf_cnpj)
            if existing:
                raise ConflictError(
                    f"CPF/CNPJ {data.cpf_cnpj} já cadastrado para customer {existing.id}"
                )
        
        # Criar model
        customer = Customer(**data.model_dump())
        
        # Persistir
        customer = self.repo.create(customer)
        self.db.commit()
        
        return customer
    
    def update_customer(
        self,
        customer_id: UUID,
        data: CustomerUpdate
    ) -> Customer:
        """
        Atualiza customer existente.
        
        Validações:
        - Customer existe
        - CPF/CNPJ único (se alterado)
        - person_type válido (se alterado)
        
        Raises:
            NotFoundError: Se customer não encontrado
            ConflictError: Se novo CPF/CNPJ já existe
            ValidationError: Se dados inválidos
        """
        # Buscar customer
        customer = self.get_customer_by_id(customer_id)
        
        # Atualizar apenas campos fornecidos
        update_data = data.model_dump(exclude_unset=True)
        
        # Validar person_type (se fornecido)
        if 'person_type' in update_data:
            if update_data['person_type'] not in ['PF', 'PJ']:
                raise ValidationError("person_type deve ser 'PF' ou 'PJ'")
        
        # Validar CPF/CNPJ duplicado (se alterado)
        if 'cpf_cnpj' in update_data and update_data['cpf_cnpj'] != customer.cpf_cnpj:
            existing = self.repo.get_by_cpf_cnpj(update_data['cpf_cnpj'])
            if existing:
                raise ConflictError(
                    f"CPF/CNPJ {update_data['cpf_cnpj']} já cadastrado"
                )
        
        # Aplicar mudanças
        for key, value in update_data.items():
            setattr(customer, key, value)
        
        # Persistir
        customer = self.repo.update(customer)
        self.db.commit()
        
        return customer
    
    def delete_customer(self, customer_id: UUID) -> bool:
        """
        Soft delete de customer.
        
        Returns:
            True se deletado com sucesso
        
        Raises:
            NotFoundError: Se customer não encontrado
        """
        customer = self.get_customer_by_id(customer_id)
        
        self.repo.soft_delete(customer)
        self.db.commit()
        
        return True
    
    def search_customers(self, name: str, limit: int = 10) -> list[Customer]:
        """
        Busca customers por nome (autocomplete).
        
        Args:
            name: Termo de busca
            limit: Máximo de resultados (default 10, max 50)
        """
        if limit > 50:
            limit = 50
        
        return self.repo.search_by_name(name, limit)
