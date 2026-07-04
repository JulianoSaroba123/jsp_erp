"""
Service Layer para Proposals.
Contém toda a lógica de negócio e validações.

REGRAS DE NEGÓCIO CRÍTICAS:
1. Status workflow: rascunho → enviada → aprovada/rejeitada/cancelada
2. Apenas propostas 'aprovada' podem ser convertidas para OS
3. Uma proposta aprovada só pode gerar UMA ordem de serviço (prevenção de duplicidade)
4. Conversão gera OS com tipo_ordem='projeto' e exibir_valores=False
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date
from sqlalchemy.orm import Session

from app.repositories.proposal_repository import (
    ProposalRepository,
    ProposalItemRepository,
    ProposalProductRepository
)
from app.models.proposal import Proposal, ProposalItem, ProposalProduct
from app.models.service_order import ServiceOrder
from app.schemas.proposal_schema import (
    ProposalCreate,
    ProposalUpdate,
    ProposalOut,
    ProposalSummary,
    ProposalsResponse
)
from app.services.service_order_service import ServiceOrderService
from app.exceptions.errors import ValidationError, NotFoundError


class ProposalService:
    """Service para operações de negócio com Proposals."""

    @staticmethod
    def list_proposals(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        customer_id: Optional[UUID] = None,
        search: Optional[str] = None
    ) -> ProposalsResponse:
        """
        Lista propostas com paginação e filtros.
        
        Validações:
        - page >= 1
        - page_size entre 1 e 100
        - status válido (se fornecido)
        """
        # Validações
        if page < 1:
            raise ValidationError("Página deve ser maior ou igual a 1")
        
        if not (1 <= page_size <= 100):
            raise ValidationError("Tamanho da página deve estar entre 1 e 100")
        
        valid_statuses = ['rascunho', 'enviada', 'aprovada', 'rejeitada', 'cancelada']
        if status and status not in valid_statuses:
            raise ValidationError(f"Status inválido. Valores permitidos: {', '.join(valid_statuses)}")
        
        # Buscar dados
        proposals = ProposalRepository.list_paginated(
            db=db,
            page=page,
            page_size=page_size,
            status=status,
            customer_id=customer_id,
            search=search
        )
        
        total = ProposalRepository.count_total(
            db=db,
            status=status,
            customer_id=customer_id,
            search=search
        )
        
        total_pages = (total + page_size - 1) // page_size
        
        return ProposalsResponse(
            items=[ProposalSummary.model_validate(p) for p in proposals],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    @staticmethod
    def create_proposal(
        db: Session,
        proposal_data: ProposalCreate,
        user_id: UUID
    ) -> Proposal:
        """
        Cria nova proposta com itens e produtos.
        
        Validações:
        - customer_id existe
        - Valores >= 0
        - Status inicial só pode ser 'rascunho' ou 'enviada'
        """
        # Validações de entrada
        if proposal_data.service_amount < 0:
            raise ValidationError("Valor de serviços não pode ser negativo")
        
        if proposal_data.parts_amount < 0:
            raise ValidationError("Valor de peças não pode ser negativo")
        
        if proposal_data.discount_amount < 0:
            raise ValidationError("Valor de desconto não pode ser negativo")
        
        # Status inicial só pode ser rascunho ou enviada
        if proposal_data.status not in ['rascunho', 'enviada']:
            raise ValidationError("Status inicial deve ser 'rascunho' ou 'enviada'")
        
        # Calcular total
        total_amount = (
            proposal_data.service_amount +
            proposal_data.parts_amount -
            proposal_data.discount_amount
        )
        
        # Criar proposta
        proposal_dict = proposal_data.model_dump(exclude={'items', 'products'})
        proposal_dict['total_amount'] = total_amount
        proposal_dict['user_id'] = user_id
        
        proposal = ProposalRepository.create(db, proposal_dict)
        
        # Criar itens
        if proposal_data.items:
            for item_data in proposal_data.items:
                item_dict = item_data.model_dump()
                item_dict['proposal_id'] = proposal.id
                ProposalItemRepository.create(db, item_dict)
        
        # Criar produtos
        if proposal_data.products:
            for product_data in proposal_data.products:
                product_dict = product_data.model_dump()
                product_dict['proposal_id'] = proposal.id
                ProposalProductRepository.create(db, product_dict)
        
        # Recarregar com relações
        db.refresh(proposal)
        return proposal

    @staticmethod
    def get_proposal(
        db: Session,
        proposal_id: UUID,
        with_relations: bool = False
    ) -> Proposal:
        """
        Busca proposta por ID.
        
        Raises:
            NotFoundError se não encontrar
        """
        if with_relations:
            proposal = ProposalRepository.get_by_id_with_relations(db, proposal_id)
        else:
            proposal = ProposalRepository.get_by_id(db, proposal_id)
        
        if not proposal:
            raise NotFoundError("Proposta não encontrada")
        
        return proposal

    @staticmethod
    def get_proposal_by_number(db: Session, number: str) -> Proposal:
        """Busca proposta por número."""
        proposal = ProposalRepository.get_by_number(db, number)
        if not proposal:
            raise NotFoundError(f"Proposta {number} não encontrada")
        return proposal

    @staticmethod
    def update_proposal(
        db: Session,
        proposal_id: UUID,
        update_data: ProposalUpdate
    ) -> Proposal:
        """
        Atualiza proposta.
        
        Validações:
        - Proposta existe
        - Não atualizar status aqui (usar change_status)
        - Valores >= 0
        """
        proposal = ProposalService.get_proposal(db, proposal_id)
        
        # Validações
        update_dict = update_data.model_dump(exclude_unset=True)
        
        if 'service_amount' in update_dict and update_dict['service_amount'] < 0:
            raise ValidationError("Valor de serviços não pode ser negativo")
        
        if 'parts_amount' in update_dict and update_dict['parts_amount'] < 0:
            raise ValidationError("Valor de peças não pode ser negativo")
        
        if 'discount_amount' in update_dict and update_dict['discount_amount'] < 0:
            raise ValidationError("Valor de desconto não pode ser negativo")
        
        # Recalcular total se valores mudaram
        if any(k in update_dict for k in ['service_amount', 'parts_amount', 'discount_amount']):
            service = update_dict.get('service_amount', proposal.service_amount)
            parts = update_dict.get('parts_amount', proposal.parts_amount)
            discount = update_dict.get('discount_amount', proposal.discount_amount)
            update_dict['total_amount'] = service + parts - discount
        
        # Não permitir atualizar status aqui
        if 'status' in update_dict:
            del update_dict['status']
        
        return ProposalRepository.update(db, proposal, update_dict)

    @staticmethod
    def delete_proposal(db: Session, proposal_id: UUID) -> None:
        """
        Remove proposta (soft delete).
        
        Validações:
        - Proposta existe
        - Não pode deletar proposta aprovada que já gerou OS
        """
        proposal = ProposalService.get_proposal(db, proposal_id)
        
        # Validação: não deletar proposta com OS gerada
        if proposal.status == 'aprovada':
            has_os = ProposalRepository.has_generated_service_order(db, proposal_id)
            if has_os:
                raise ValidationError(
                    "Não é possível excluir proposta aprovada que já gerou ordem de serviço"
                )
        
        ProposalRepository.soft_delete(db, proposal)

    @staticmethod
    def change_status(
        db: Session,
        proposal_id: UUID,
        new_status: str,
        user_id: UUID
    ) -> Proposal:
        """
        Altera status da proposta com validação de workflow.
        
        Workflow válido:
        - rascunho → [enviada, cancelada]
        - enviada → [aprovada, rejeitada, cancelada]
        - aprovada → [cancelada] (apenas se NÃO gerou OS)
        - rejeitada → [cancelada]
        - cancelada → não pode mudar
        """
        proposal = ProposalService.get_proposal(db, proposal_id)
        
        # Validar transição de status
        current = proposal.status
        valid_statuses = ['rascunho', 'enviada', 'aprovada', 'rejeitada', 'cancelada']
        
        if new_status not in valid_statuses:
            raise ValidationError(f"Status inválido: {new_status}")
        
        # Workflow rules
        valid_transitions = {
            'rascunho': ['enviada', 'cancelada'],
            'enviada': ['aprovada', 'rejeitada', 'cancelada'],
            'aprovada': ['cancelada'],
            'rejeitada': ['cancelada'],
            'cancelada': []
        }
        
        if new_status not in valid_transitions.get(current, []):
            raise ValidationError(
                f"Transição de status inválida: {current} → {new_status}"
            )
        
        # Validação especial: aprovada só pode cancelar se não gerou OS
        if current == 'aprovada' and new_status == 'cancelada':
            has_os = ProposalRepository.has_generated_service_order(db, proposal_id)
            if has_os:
                raise ValidationError(
                    "Não é possível cancelar proposta aprovada que já gerou ordem de serviço"
                )
        
        # Atualizar status e data
        update_data = {'status': new_status}
        
        if new_status == 'aprovada':
            update_data['approved_at'] = datetime.utcnow()
            update_data['approved_by_id'] = user_id
        elif new_status == 'rejeitada':
            update_data['rejected_at'] = datetime.utcnow()
        
        return ProposalRepository.update(db, proposal, update_data)

    @staticmethod
    def convert_to_service_order(
        db: Session,
        proposal_id: UUID,
        technician_id: Optional[UUID] = None,
        expected_completion_date: Optional[date] = None,
        observations: Optional[str] = None
    ) -> ServiceOrder:
        """
        **CONVERSÃO: PROPOSTA APROVADA → ORDEM DE SERVIÇO**
        
        Esta é a função CENTRAL do fluxo de negócio.
        
        REGRAS DE NEGÓCIO CRÍTICAS:
        1. Apenas propostas com status 'aprovada' podem ser convertidas
        2. Uma proposta só pode gerar UMA ordem de serviço (prevenção de duplicidade)
        3. A OS gerada tem tipo_ordem='projeto' e exibir_valores=False
        4. Copia dados da proposta: cliente, valores, descrição, itens, produtos
        5. Vincula via proposta_id para rastreabilidade
        
        Args:
            proposal_id: ID da proposta aprovada
            technician_id: Técnico responsável (opcional)
            expected_completion_date: Data prevista de conclusão (opcional)
            observations: Observações adicionais (opcional)
        
        Returns:
            ServiceOrder criada
        
        Raises:
            NotFoundError: Proposta não encontrada
            ValidationError: Proposta não aprovada ou já possui OS gerada
        """
        # 1. Buscar proposta com validação
        proposal = ProposalService.get_proposal(db, proposal_id, with_relations=True)
        
        # 2. Validar status: APENAS 'aprovada' pode converter
        if proposal.status != 'aprovada':
            raise ValidationError(
                f"Apenas propostas aprovadas podem ser convertidas. "
                f"Status atual: {proposal.status}"
            )
        
        # 3. Validar duplicidade: UMA proposta → UMA OS
        has_existing_os = ProposalRepository.has_generated_service_order(db, proposal_id)
        if has_existing_os:
            raise ValidationError(
                f"A proposta {proposal.number} já possui uma ordem de serviço gerada. "
                "Não é possível gerar duplicatas."
            )
        
        # 4. Buscar itens e produtos da proposta
        items = ProposalItemRepository.get_by_proposal(db, proposal_id)
        products = ProposalProductRepository.get_by_proposal(db, proposal_id)
        
        # 5. Delegar conversão para ServiceOrderService
        # IMPORTANTE: Toda lógica de conversão fica no service layer
        # Não duplicar em controller/route
        service_order = ServiceOrderService.create_os_from_proposal(
            db=db,
            proposal=proposal,
            items=items,
            products=products,
            technician_id=technician_id,
            expected_completion_date=expected_completion_date,
            observations=observations
        )
        
        return service_order

    @staticmethod
    def get_proposal_items(db: Session, proposal_id: UUID) -> List[ProposalItem]:
        """Lista itens de uma proposta."""
        # Valida que proposta existe
        ProposalService.get_proposal(db, proposal_id)
        return ProposalItemRepository.get_by_proposal(db, proposal_id)

    @staticmethod
    def add_proposal_item(
        db: Session,
        proposal_id: UUID,
        item_data: dict
    ) -> ProposalItem:
        """Adiciona item a uma proposta existente."""
        # Valida que proposta existe
        proposal = ProposalService.get_proposal(db, proposal_id)
        
        # Não permitir adicionar itens em propostas aprovadas/rejeitadas
        if proposal.status in ['aprovada', 'rejeitada']:
            raise ValidationError(
                f"Não é possível adicionar itens em proposta com status '{proposal.status}'"
            )
        
        item_data['proposal_id'] = proposal_id
        return ProposalItemRepository.create(db, item_data)

    @staticmethod
    def get_proposal_products(db: Session, proposal_id: UUID) -> List[ProposalProduct]:
        """Lista produtos de uma proposta."""
        # Valida que proposta existe
        ProposalService.get_proposal(db, proposal_id)
        return ProposalProductRepository.get_by_proposal(db, proposal_id)

    @staticmethod
    def add_proposal_product(
        db: Session,
        proposal_id: UUID,
        product_data: dict
    ) -> ProposalProduct:
        """Adiciona produto a uma proposta existente."""
        # Valida que proposta existe
        proposal = ProposalService.get_proposal(db, proposal_id)
        
        # Não permitir adicionar produtos em propostas aprovadas/rejeitadas
        if proposal.status in ['aprovada', 'rejeitada']:
            raise ValidationError(
                f"Não é possível adicionar produtos em proposta com status '{proposal.status}'"
            )
        
        product_data['proposal_id'] = proposal_id
        return ProposalProductRepository.create(db, product_data)

    @staticmethod
    def generate_share_link(
        db: Session,
        proposal_id: UUID,
        expires_in_days: Optional[int] = None
    ) -> Proposal:
        """
        Gera token de compartilhamento público para PDF da proposta.
        
        Args:
            proposal_id: ID da proposta
            expires_in_days: Dias até expiração (None = sem expiração)
        
        Returns:
            Proposta atualizada com share_token
        
        Raises:
            NotFoundError: Proposta não encontrada
        """
        import secrets
        from datetime import timedelta
        
        # Buscar proposta
        proposal = ProposalService.get_proposal(db, proposal_id)
        
        # Gerar token único (64 caracteres hexadecimais)
        share_token = secrets.token_urlsafe(48)[:64]
        
        # Calcular data de expiração
        share_expires_at = None
        if expires_in_days:
            share_expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Atualizar proposta
        update_data = {
            'share_token': share_token,
            'share_enabled': True,
            'share_expires_at': share_expires_at,
            'share_created_at': datetime.utcnow()
        }
        
        return ProposalRepository.update(db, proposal, update_data)

    @staticmethod
    def revoke_share_link(db: Session, proposal_id: UUID) -> Proposal:
        """
        Revoga link de compartilhamento de uma proposta.
        
        Args:
            proposal_id: ID da proposta
        
        Returns:
            Proposta atualizada
        """
        proposal = ProposalService.get_proposal(db, proposal_id)
        
        update_data = {
            'share_enabled': False
        }
        
        return ProposalRepository.update(db, proposal, update_data)

    @staticmethod
    def validate_share_token(
        db: Session,
        proposal_id: UUID,
        token: str
    ) -> Proposal:
        """
        Valida token de compartilhamento e retorna proposta.
        
        Args:
            proposal_id: ID da proposta
            token: Token de compartilhamento
        
        Returns:
            Proposta se token válido
        
        Raises:
            ValidationError: Token inválido, expirado ou compartilhamento desabilitado
            NotFoundError: Proposta não encontrada
        """
        proposal = ProposalService.get_proposal(db, proposal_id)
        
        # Validar se compartilhamento está habilitado
        if not proposal.share_enabled:
            raise ValidationError("Compartilhamento desta proposta está desabilitado")
        
        # Validar token
        if proposal.share_token != token:
            raise ValidationError("Token de compartilhamento inválido")
        
        # Validar expiração
        if proposal.share_expires_at and proposal.share_expires_at < datetime.utcnow():
            raise ValidationError("Link de compartilhamento expirado")
        
        return proposal

