"""
Service para FinancialEntry - regras de negócio.
Camada de validações e lógica financeira.
"""

from typing import Dict, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal

from app.models.financial_entry import FinancialEntry
from app.repositories.financial_repository import FinancialRepository
from app.exceptions.errors import ConflictError


class FinancialService:
    """Service com regras de negócio para lançamentos financeiros."""

    # Constantes de validação
    VALID_KINDS = ['revenue', 'expense']
    VALID_STATUSES = ['pending', 'paid', 'canceled']
    MAX_PAGE_SIZE = 100

    @staticmethod
    def list_entries(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[UUID] = None,
        status: Optional[str] = None,
        kind: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict:
        """
        Lista lançamentos com paginação e filtros.
        
        Args:
            db: Sessão SQLAlchemy
            page: Número da página (>= 1)
            page_size: Itens por página (max 100)
            user_id: Filtro multi-tenant (None = admin vê tudo)
            status: Filtro por status (pending, paid, canceled)
            kind: Filtro por tipo (revenue, expense)
            date_from: Data inicial (occurred_at >= date_from)
            date_to: Data final (occurred_at <= date_to)
            
        Returns:
            {"items": [...], "page": 1, "page_size": 20, "total": 50}
        """
        # Validação de paginação
        if page < 1:
            page = 1
        if page_size > FinancialService.MAX_PAGE_SIZE:
            page_size = FinancialService.MAX_PAGE_SIZE
        if page_size < 1:
            page_size = 1

        # Validação de filtros opcionais
        if status and status not in FinancialService.VALID_STATUSES:
            raise ValueError(
                f"status inválido: '{status}'. Use: {', '.join(FinancialService.VALID_STATUSES)}"
            )
        if kind and kind not in FinancialService.VALID_KINDS:
            raise ValueError(
                f"kind inválido: '{kind}'. Use: {', '.join(FinancialService.VALID_KINDS)}"
            )

        # Busca dados
        entries = FinancialRepository.list_paginated(
            db=db,
            page=page,
            page_size=page_size,
            user_id=user_id,
            status=status,
            kind=kind,
            date_from=date_from,
            date_to=date_to
        )

        total = FinancialRepository.count_total(
            db=db,
            user_id=user_id,
            status=status,
            kind=kind,
            date_from=date_from,
            date_to=date_to
        )

        return {
            "items": entries,
            "page": page,
            "page_size": page_size,
            "total": total
        }

    @staticmethod
    def get_entry_by_id(db: Session, entry_id: UUID) -> Optional[FinancialEntry]:
        """Busca lançamento por ID."""
        return FinancialRepository.get_by_id(db=db, entry_id=entry_id)

    @staticmethod
    def create_manual_entry(
        db: Session,
        user_id: UUID,
        kind: str,
        amount: float,
        description: str,
        occurred_at: Optional[datetime] = None,
        # Campos profissionais Phase 1
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        due_date: Optional[datetime] = None,
        payment_date: Optional[datetime] = None,
        document_number: Optional[str] = None,
        document_type: Optional[str] = None,
        payment_method: Optional[str] = None,
        notes: Optional[str] = None,
        customer_id: Optional[UUID] = None,
        supplier_id: Optional[UUID] = None,
        service_order_id: Optional[UUID] = None,
        original_amount: Optional[float] = None,
        interest: Optional[float] = None,
        discount: Optional[float] = None,
        penalty: Optional[float] = None,
        installment_info: Optional[str] = None,
        is_recurring: Optional[bool] = False,
        recurrence_frequency: Optional[str] = None,
        origin: Optional[str] = None
    ) -> FinancialEntry:
        """
        Cria lançamento manual (sem order_id) com campos profissionais.
        
        Validações:
        - kind IN ('revenue', 'expense')
        - amount >= 0
        - description não vazio
        
        Args:
            db: Sessão SQLAlchemy
            user_id: UUID do usuário (vem do token JWT)
            kind: 'revenue' ou 'expense'
            amount: Valor (>= 0)
            description: Descrição textual
            occurred_at: Data de ocorrência (default: now)
            category: Categoria do lançamento (ex: Vendas, Fornecedores)
            subcategory: Subcategoria (ex: Produtos, Serviços)
            due_date: Data de vencimento
            payment_date: Data de pagamento efetivo
            document_number: Número do documento (NF, boleto)
            document_type: Tipo do documento (NF-e, boleto)
            payment_method: Forma de pagamento (pix, dinheiro, cartão)
            notes: Observações adicionais
            customer_id: ID do cliente (para receitas)
            supplier_id: ID do fornecedor (para despesas)
            service_order_id: ID da ordem de serviço relacionada
            original_amount: Valor original antes de juros/descontos
            interest: Juros aplicados
            discount: Desconto concedido
            penalty: Multa por atraso
            installment_info: Info de parcelas (ex: 3/12)
            is_recurring: É um lançamento recorrente?
            recurrence_frequency: Frequência (mensal, anual)
            origin: Origem do lançamento (manual, pedido, importação)
            
        Returns:
            FinancialEntry criado
        """
        # Validação de kind
        if kind not in FinancialService.VALID_KINDS:
            raise ValueError(
                f"kind inválido: '{kind}'. Use: {', '.join(FinancialService.VALID_KINDS)}"
            )

        # Validação de amount
        if amount is None or amount < 0:
            raise ValueError("amount deve ser >= 0")

        # Validação de description
        description = (description or "").strip()
        if not description:
            raise ValueError("description é obrigatório e não pode estar vazio")

        normalized_origin = (origin or "MANUAL").strip().upper()

        # Criar lançamento
        entry = FinancialEntry(
            user_id=user_id,
            order_id=None,  # Lançamento manual
            kind=kind,
            status='pending',
            amount=Decimal(str(amount)),
            description=description,
            occurred_at=occurred_at or datetime.utcnow(),
            # Campos profissionais
            category=category,
            subcategory=subcategory,
            due_date=due_date,
            payment_date=payment_date,
            document_number=document_number,
            document_type=document_type,
            payment_method=payment_method,
            notes=notes,
            customer_id=customer_id,
            supplier_id=supplier_id,
            service_order_id=service_order_id,
            original_amount=Decimal(str(original_amount)) if original_amount is not None else None,
            interest=Decimal(str(interest)) if interest is not None else None,
            discount=Decimal(str(discount)) if discount is not None else None,
            penalty=Decimal(str(penalty)) if penalty is not None else None,
            installment_info=installment_info,
            is_recurring=is_recurring or False,
            recurrence_frequency=recurrence_frequency,
            origin=normalized_origin
        )

        return FinancialRepository.create(db=db, entry=entry)

    @staticmethod
    def create_from_order(
        db: Session,
        order_id: UUID,
        user_id: UUID,
        amount: float,
        description: str
    ) -> FinancialEntry:
        """
        Cria lançamento automático de receita vinculado a um pedido.
        
        IDEMPOTÊNCIA: Se já existir lançamento para este order_id, retorna o existente.
        Trata race condition via try/except IntegrityError + rollback.
        
        Regras:
        - kind = 'revenue' (pedidos sempre geram receita)
        - status = 'pending' (aguardando pagamento)
        - order_id UNIQUE (garante um lançamento por pedido)
        
        Args:
            db: Sessão SQLAlchemy
            order_id: UUID do pedido
            user_id: UUID do usuário dono do pedido
            amount: Valor do pedido
            description: Descrição formatada
            
        Returns:
            FinancialEntry criado ou existente
        """
        from sqlalchemy.exc import IntegrityError
        
        # Verificar se já existe lançamento para este pedido (idempotência - primeira tentativa)
        existing = FinancialRepository.get_by_order_id(db=db, order_id=order_id)
        if existing:
            # Já existe, retornar o existente (não duplicar)
            return existing

        # Validação de amount
        if amount < 0:
            raise ValueError("amount de pedido não pode ser negativo")

        # Criar novo lançamento
        entry = FinancialEntry(
            order_id=order_id,
            user_id=user_id,
            kind='revenue',  # Pedidos sempre geram receita
            status='pending',  # Aguardando pagamento
            amount=Decimal(str(amount)),
            description=description,
            occurred_at=datetime.utcnow()
        )

        try:
            return FinancialRepository.create(db=db, entry=entry)
        except IntegrityError as e:
            # Race condition: outro request criou entry para este order_id
            db.rollback()  # OBRIGATÓRIO: desfazer transação falha
            
            # Buscar entry existente criado pelo outro request
            existing = FinancialRepository.get_by_order_id(db=db, order_id=order_id)
            if existing:
                # Encontrou, retornar (idempotência garantida)
                return existing
            
            # Não encontrou (erro diferente de UNIQUE), repassar exceção
            raise e

    @staticmethod
    def update_status(
        db: Session,
        entry: FinancialEntry,
        new_status: str,
        payment_date: Optional[datetime] = None
    ) -> FinancialEntry:
        """
        Atualiza status de um lançamento.
        
        Regras de transição permitidas (MVP):
        - pending → paid
        - pending → canceled
        - Demais transições bloqueadas (regra simplificada)
        
        Args:
            db: Sessão SQLAlchemy
            entry: FinancialEntry a atualizar
            new_status: Novo status
            payment_date: Data de pagamento (usado quando new_status='paid')
            
        Returns:
            FinancialEntry atualizado
            
        Raises:
            ValueError: Se transição for inválida
        """
        # Validação de status válido
        if new_status not in FinancialService.VALID_STATUSES:
            raise ValueError(
                f"status inválido: '{new_status}'. Use: {', '.join(FinancialService.VALID_STATUSES)}"
            )

        # Regras de transição (MVP simplificado)
        current_status = entry.status

        # Se já está no status desejado, ok
        if current_status == new_status:
            return entry

        # pending → paid ou canceled: OK
        if current_status == 'pending' and new_status in ['paid', 'canceled']:
            # Se está marcando como pago, definir payment_date
            if new_status == 'paid':
                entry.payment_date = payment_date or datetime.utcnow()
            
            return FinancialRepository.update_status(db=db, entry=entry, new_status=new_status)

        # Demais transições bloqueadas
        raise ValueError(
            f"Transição inválida: {current_status} → {new_status}. "
            "Apenas 'pending' pode mudar para 'paid' ou 'canceled'."
        )

    @staticmethod
    def cancel_entry_by_order(db: Session, order_id: UUID) -> Optional[FinancialEntry]:
        """
        Cancela lançamento vinculado a um pedido (se status='pending').
        
        Usado quando um pedido é deletado.
        
        Regra:
        - Se status='pending': marca como 'canceled'
        - Se status='paid': não altera (retorna None para bloquear delete do pedido)
        - Se não existir lançamento: retorna None (ok, seguir)
        
        Args:
            db: Sessão SQLAlchemy
            order_id: UUID do pedido
            
        Returns:
            FinancialEntry cancelado, None se não havia lançamento, 
            ou Exception se status='paid'
        """
        entry = FinancialRepository.get_by_order_id(db=db, order_id=order_id)

        if not entry:
            # Não havia lançamento, pode deletar pedido
            return None

        if entry.status == 'paid':
            # Lançamento pago não pode ser cancelado automaticamente
            raise ConflictError(
                f"Não é possível deletar pedido: lançamento financeiro já está 'paid'. "
                "Solicite estorno manual ao financeiro."
            )

        if entry.status == 'pending':
            # Cancelar lançamento pendente
            return FinancialRepository.update_status(db=db, entry=entry, new_status='canceled')

        # Status='canceled': já estava cancelado, ok
        return entry

    @staticmethod
    def delete_entry(db: Session, entry: FinancialEntry, deleted_by_user_id: UUID) -> FinancialEntry:
        """
        Soft delete de lançamento financeiro pendente/cancelado.

        Lançamentos pagos não podem ser apagados diretamente, pois isso quebra a
        trilha financeira; nesses casos o fluxo correto é estorno/cancelamento.
        """
        if entry.status == 'paid':
            raise ConflictError(
                "Não é possível deletar lançamento financeiro com status='paid'. "
                "Solicite estorno formal ao financeiro."
            )

        return FinancialRepository.soft_delete(
            db=db,
            entry=entry,
            deleted_by_user_id=deleted_by_user_id
        )
