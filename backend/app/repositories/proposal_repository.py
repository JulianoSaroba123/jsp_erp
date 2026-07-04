"""
Repository para Proposals (Propostas Comerciais).
Camada de acesso a dados com queries SQL.
"""

from typing import List, Optional, Dict
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_
from datetime import datetime, date

from app.models.proposal import Proposal, ProposalItem, ProposalProduct


class ProposalRepository:
    """Repository para operações CRUD de Proposals."""

    @staticmethod
    def generate_next_number(db: Session) -> str:
        """
        Gera próximo número de proposta no formato PROP{ANO}{SEQUENCIAL}.
        Exemplo: PROP2026001, PROP2026002...
        
        Regra: Sequencial reinicia a cada ano.
        """
        current_year = datetime.now().year
        prefix = f"PROP{current_year}"
        
        # Buscar o último número do ano atual
        last_proposal = (
            db.query(Proposal)
            .filter(Proposal.number.like(f"{prefix}%"))
            .order_by(Proposal.number.desc())
            .first()
        )
        
        if last_proposal:
            # Extrair número sequencial (últimos 4 dígitos)
            last_number = int(last_proposal.number[-4:])
            next_number = last_number + 1
        else:
            next_number = 1
        
        # Formatar com zero padding (4 dígitos)
        return f"{prefix}{next_number:04d}"

    @staticmethod
    def create(db: Session, proposal_data: dict) -> Proposal:
        """
        Cria nova proposta.
        Gera número automaticamente.
        """
        # Gerar número
        proposal_data['number'] = ProposalRepository.generate_next_number(db)
        
        # Criar instância
        proposal = Proposal(**proposal_data)
        db.add(proposal)
        db.commit()
        db.refresh(proposal)
        
        return proposal

    @staticmethod
    def get_by_id(db: Session, proposal_id: UUID) -> Optional[Proposal]:
        """Busca proposta por ID (sem soft delete)."""
        return (
            db.query(Proposal)
            .filter(Proposal.id == proposal_id)
            .filter(Proposal.deleted_at.is_(None))
            .first()
        )

    @staticmethod
    def get_by_id_with_relations(db: Session, proposal_id: UUID) -> Optional[Proposal]:
        """
        Busca proposta com itens e produtos carregados (eager loading).
        """
        return (
            db.query(Proposal)
            .options(
                joinedload(Proposal.customer),
            )
            .filter(Proposal.id == proposal_id)
            .filter(Proposal.deleted_at.is_(None))
            .first()
        )

    @staticmethod
    def get_by_number(db: Session, number: str) -> Optional[Proposal]:
        """Busca proposta por número (PROP2026001)."""
        return (
            db.query(Proposal)
            .filter(Proposal.number == number)
            .filter(Proposal.deleted_at.is_(None))
            .first()
        )

    @staticmethod
    def list_paginated(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        customer_id: Optional[UUID] = None,
        search: Optional[str] = None
    ) -> List[Proposal]:
        """
        Lista propostas com paginação e filtros.
        
        Args:
            page: Número da página (base 1)
            page_size: Itens por página
            status: Filtro por status (rascunho, enviada, aprovada, etc)
            customer_id: Filtro por cliente
            search: Busca em número, título
        """
        query = db.query(Proposal).filter(Proposal.deleted_at.is_(None))
        
        # Filtros
        if status:
            query = query.filter(Proposal.status == status)
        
        if customer_id:
            query = query.filter(Proposal.customer_id == customer_id)
        
        if search:
            query = query.filter(
                or_(
                    Proposal.number.ilike(f"%{search}%"),
                    Proposal.title.ilike(f"%{search}%")
                )
            )
        
        # Ordenação
        query = query.order_by(Proposal.created_at.desc())
        
        # Paginação
        offset = (page - 1) * page_size
        return query.offset(offset).limit(page_size).all()

    @staticmethod
    def count_total(
        db: Session,
        status: Optional[str] = None,
        customer_id: Optional[UUID] = None,
        search: Optional[str] = None
    ) -> int:
        """Conta total de propostas (para paginação)."""
        query = db.query(func.count(Proposal.id)).filter(Proposal.deleted_at.is_(None))
        
        if status:
            query = query.filter(Proposal.status == status)
        
        if customer_id:
            query = query.filter(Proposal.customer_id == customer_id)
        
        if search:
            query = query.filter(
                or_(
                    Proposal.number.ilike(f"%{search}%"),
                    Proposal.title.ilike(f"%{search}%")
                )
            )
        
        return query.scalar()

    @staticmethod
    def update(db: Session, proposal: Proposal, update_data: dict) -> Proposal:
        """Atualiza proposta."""
        for key, value in update_data.items():
            if value is not None:  # Só atualiza se valor não for None
                setattr(proposal, key, value)
        
        proposal.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(proposal)
        
        return proposal

    @staticmethod
    def soft_delete(db: Session, proposal: Proposal) -> None:
        """Soft delete de proposta."""
        proposal.deleted_at = datetime.utcnow()
        db.commit()

    @staticmethod
    def has_generated_service_order(db: Session, proposal_id: UUID) -> bool:
        """
        Verifica se a proposta já gerou uma ordem de serviço.
        
        REGRA DE NEGÓCIO: Uma proposta aprovada só pode gerar UMA ordem de serviço.
        Esta verificação evita duplicidade.
        
        Returns:
            True se já existe OS vinculada, False caso contrário
        """
        from app.models.service_order import ServiceOrder
        
        exists = (
            db.query(ServiceOrder)
            .filter(ServiceOrder.proposta_id == proposal_id)
            .filter(ServiceOrder.deleted_at.is_(None))
            .first()
        )
        
        return exists is not None


# ==================== Repositories para entidades relacionadas ====================

class ProposalItemRepository:
    """Repository para itens de serviço da proposta."""

    @staticmethod
    def create(db: Session, item_data: dict) -> ProposalItem:
        """Cria item de serviço."""
        item = ProposalItem(**item_data)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def get_by_proposal(db: Session, proposal_id: UUID) -> List[ProposalItem]:
        """Lista itens de uma proposta."""
        return (
            db.query(ProposalItem)
            .filter(ProposalItem.proposal_id == proposal_id)
            .order_by(ProposalItem.created_at)
            .all()
        )

    @staticmethod
    def delete(db: Session, item_id: UUID) -> None:
        """Remove item."""
        item = db.query(ProposalItem).filter(ProposalItem.id == item_id).first()
        if item:
            db.delete(item)
            db.commit()


class ProposalProductRepository:
    """Repository para produtos da proposta."""

    @staticmethod
    def create(db: Session, product_data: dict) -> ProposalProduct:
        """Adiciona produto."""
        product = ProposalProduct(**product_data)
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def get_by_proposal(db: Session, proposal_id: UUID) -> List[ProposalProduct]:
        """Lista produtos de uma proposta."""
        return (
            db.query(ProposalProduct)
            .filter(ProposalProduct.proposal_id == proposal_id)
            .order_by(ProposalProduct.created_at)
            .all()
        )

    @staticmethod
    def delete(db: Session, product_id: UUID) -> None:
        """Remove produto."""
        product = db.query(ProposalProduct).filter(ProposalProduct.id == product_id).first()
        if product:
            db.delete(product)
            db.commit()
