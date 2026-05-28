"""
Repository para Customer - camada de acesso a dados.

Segue padrão Repository Pattern:
- Encapsula toda lógica SQL/ORM
- Retorna modelos SQLAlchemy
- Não contém regras de negócio
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.customer import Customer


class CustomerRepository:
    """Repository para operações de Customer no banco de dados"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, customer_id: UUID) -> Optional[Customer]:
        """Busca customer por ID (apenas não deletados)"""
        return self.db.query(Customer).filter(
            and_(
                Customer.id == customer_id,
                Customer.deleted_at.is_(None)
            )
        ).first()
    
    def get_by_cpf_cnpj(self, cpf_cnpj: str) -> Optional[Customer]:
        """Busca customer por CPF/CNPJ (apenas não deletados)"""
        return self.db.query(Customer).filter(
            and_(
                Customer.cpf_cnpj == cpf_cnpj,
                Customer.deleted_at.is_(None)
            )
        ).first()
    
    def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None
    ) -> tuple[List[Customer], int]:
        """
        Lista customers com paginação e filtro opcional de status.
        
        Returns:
            (lista_customers, total_count)
        """
        # Base query (apenas não deletados)
        query = self.db.query(Customer).filter(Customer.deleted_at.is_(None))
        
        # Filtro de status
        if status:
            query = query.filter(Customer.status == status)
        
        # Total
        total = query.count()
        
        # Paginação
        offset = (page - 1) * page_size
        items = query.order_by(Customer.created_at.desc()).offset(offset).limit(page_size).all()
        
        return items, total
    
    def create(self, customer: Customer) -> Customer:
        """Cria novo customer"""
        self.db.add(customer)
        self.db.flush()
        self.db.refresh(customer)
        return customer
    
    def update(self, customer: Customer) -> Customer:
        """Atualiza customer existente"""
        self.db.flush()
        self.db.refresh(customer)
        return customer
    
    def soft_delete(self, customer: Customer) -> Customer:
        """
        Soft delete de customer.
        Seta deleted_at = NOW().
        """
        from sqlalchemy import text
        customer.deleted_at = text("NOW()")
        self.db.flush()
        self.db.refresh(customer)
        return customer
    
    def search_by_name(self, name: str, limit: int = 10) -> List[Customer]:
        """
        Busca customers por nome (ILIKE).
        Útil para autocomplete.
        """
        return self.db.query(Customer).filter(
            and_(
                Customer.name.ilike(f"%{name}%"),
                Customer.deleted_at.is_(None)
            )
        ).limit(limit).all()
