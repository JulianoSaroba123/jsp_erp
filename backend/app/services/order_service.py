"""
Service para Order - regras de negócio.
Camada de validações e lógica de negócio.
Integração automática com módulo financeiro (ETAPA 3A).
"""

from typing import Dict, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.user import User
from app.models.financial_entry import FinancialEntry
from app.repositories.order_repository import OrderRepository
from app.services.financial_service import FinancialService
from app.exceptions.errors import NotFoundError, ValidationError


class OrderService:
    """Service com regras de negócio para pedidos."""

    @staticmethod
    def list_orders(
        db: Session, 
        page: int = 1, 
        page_size: int = 20,
        user_id: Optional[UUID] = None
    ) -> Dict:
        """
        Lista pedidos com paginação.
        
        Se user_id for fornecido, retorna apenas pedidos daquele usuário (multi-tenant).
        Se user_id for None, retorna todos os pedidos (admin).
        
        Regras de negócio:
        - page mínimo: 1
        - page_size máximo: 100 (proteção de performance)
        
        Retorna: {"items": [...], "page": 1, "page_size": 20, "total": 123}
        """
        # Validação: page >= 1
        if page < 1:
            page = 1

        # Regra de negócio: limitar page_size para não derrubar API
        if page_size > 100:
            page_size = 100
        if page_size < 1:
            page_size = 1

        # Busca dados (filtrando por user_id se fornecido)
        if user_id:
            orders = OrderRepository.list_by_user(db=db, user_id=user_id, page=page, page_size=page_size)
            total = OrderRepository.count_by_user(db=db, user_id=user_id)
        else:
            orders = OrderRepository.list_paginated(db=db, page=page, page_size=page_size)
            total = OrderRepository.count_total(db=db)

        return {
            "items": orders,
            "page": page,
            "page_size": page_size,
            "total": total
        }

    @staticmethod
    def create_order(db: Session, user_id: UUID, description: str, total: float) -> Order:
        """
        Cria pedido com validações de negócio.
        
        **INTEGRAÇÃO FINANCEIRA (ETAPA 3A):**
        - Se total > 0, cria lançamento financeiro automático (revenue, pending)
        - Idempotente: não duplica lançamento se já existir
        
        Validações:
        1. description não pode ser vazio
        2. total >= 0
        3. user_id deve existir no banco
        """
        # Validação 1: description obrigatório
        description = (description or "").strip()
        if not description:
            raise ValueError("description é obrigatório e não pode estar vazio")

        # Validação 2: total não pode ser negativo
        if total is None:
            total = 0.0
        if total < 0:
            raise ValueError("total não pode ser negativo")

        # Validação 3: usuário precisa existir (integridade referencial)
        user_exists = db.query(User.id).filter(User.id == user_id).first()
        if not user_exists:
            raise ValueError(f"user_id inválido: usuário {user_id} não encontrado")

        # Persiste pedido via repository
        order = OrderRepository.create(
            db=db,
            user_id=user_id,
            description=description,
            total=total
        )
        
        # INTEGRAÇ Financial: Criar lançamento automático se total > 0
        if total > 0:
            financial_description = f"Pedido {order.id} - {description}"
            FinancialService.create_from_order(
                db=db,
                order_id=order.id,
                user_id=user_id,
                amount=total,
                description=financial_description
            )
        
        return order

    @staticmethod
    def get_order(db: Session, order_id: UUID) -> Optional[Order]:
        """Busca pedido por ID."""
        return OrderRepository.get_by_id(db=db, order_id=order_id)

    @staticmethod
    def update_order(
        db: Session,
        order_id: UUID,
        user_id: UUID,
        description: Optional[str] = None,
        total: Optional[float] = None
    ) -> Order:
        """
        Atualiza pedido com sincronização financeira automática.
        
        **INTEGRAÇÃO FINANCEIRA (ETAPA 5):**
        
        Regras de negócio:
        1. **Financial pending + total change**: Atualiza amount da entry
        2. **Financial paid + total change**: BLOQUEIA (ValidationError)
        3. **Financial canceled + total > 0**: REABRE entry (pending)
        4. **Total = 0 + pending financial**: CANCELA entry
        5. **No financial + total > 0**: CRIA entry idempotente
        
        Multi-tenant:
        - User só pode atualizar seus próprios pedidos
        - Anti-enumeration: 404 se order não existe ou não pertence ao user
        
        Args:
            db: Sessão SQLAlchemy
            order_id: UUID do pedido
            user_id: UUID do usuário autenticado
            description: Nova descrição (None = mantém atual)
            total: Novo total (None = mantém atual)
        
        Returns:
            Order atualizado
        
        Raises:
            NotFoundError: Order não encontrado ou não pertence ao user
            ValidationError: Tentativa de alterar total com financial paid
        """
        from sqlalchemy.exc import IntegrityError
        
        # 1. Buscar order com filtro multi-tenant
        order = OrderRepository.get_by_id_and_user(db, order_id, user_id)
        if not order:
            raise NotFoundError("Pedido não encontrado")
        
        # 2. Buscar financial entry associada (se existir)
        financial_entry = (
            db.query(FinancialEntry)
            .filter(FinancialEntry.order_id == order_id)
            .first()
        )
        
        # 3. Validar regras de negócio se total está sendo alterado
        if total is not None and total != float(order.total):
            # 3.1. Bloquear se financial está paid
            if financial_entry and financial_entry.status == "paid":
                raise ValidationError(
                    "Não é possível alterar total de pedido com lançamento financeiro pago"
                )
        
        # 4. Atualizar order (description e/ou total)
        if description is not None:
            order.description = description
        
        if total is not None:
            order.total = total
            
            # 5. Sincronizar financial entry
            if total > 0:
                if financial_entry:
                    # 5.1. Atualizar entry existente
                    financial_entry.amount = total
                    
                    # 5.2. Reabrir se estava canceled
                    if financial_entry.status == "canceled":
                        financial_entry.status = "pending"
                
                else:
                    # 5.3. Criar nova entry (idempotente via UNIQUE order_id)
                    try:
                        new_financial = FinancialEntry(
                            order_id=order_id,
                            user_id=user_id,
                            kind="revenue",
                            status="pending",
                            amount=total,
                            description=f"Pedido {order_id} - {order.description}"
                        )
                        db.add(new_financial)
                        db.flush()  # Testa UNIQUE constraint sem commit
                    
                    except IntegrityError:
                        # Entry foi criado em race condition (idempotência)
                        # Rollback REVERTE TUDO - precisamos reaplicar mudanças no order
                        db.rollback()
                        
                        # Re-buscar order (sessão foi revertida)
                        order = OrderRepository.get_by_id_and_user(db, order_id, user_id)
                        if not order:
                            raise NotFoundError("Pedido não encontrado após rollback")
                        
                        # Reaplicar mudanças que foram perdidas no rollback
                        if description is not None:
                            order.description = description
                        if total is not None:
                            order.total = total
                        
                        # Atualizar financial entry existente
                        financial_entry = (
                            db.query(FinancialEntry)
                            .filter(FinancialEntry.order_id == order_id)
                            .first()
                        )
                        if financial_entry:
                            financial_entry.amount = total
            
            elif total == 0:
                # 5.4. Cancelar financial entry se total = 0
                if financial_entry and financial_entry.status == "pending":
                    financial_entry.status = "canceled"
        
        # 6. Commit
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def delete_order(db: Session, order_id: UUID, user_id: Optional[UUID] = None, is_admin: bool = False) -> bool:
        """
        Remove pedido (soft delete).
        
        **INTEGRAÇÃO FINANCEIRA (ETAPA 3A):**
        - Se existe lançamento financeiro vinculado:
          - status='pending': cancela automaticamente (marca como 'canceled')
          - status='paid': BLOQUEIA exclusão (exceção ValueError)
          - status='canceled': ok, já estava cancelado
        
        Regras multi-tenant:
        - Admin pode deletar qualquer pedido (is_admin=True)
        - User comum só pode deletar seus próprios pedidos
        
        Args:
            db: Sessão do banco
            order_id: ID do pedido a deletar
            user_id: ID do usuário fazendo a operação (obrigatório para soft delete)
            is_admin: Se o usuário é admin (bypass de validação)
        
        Returns:
            True se removeu, False se não existia
            
        Raises:
            ValueError: Se user tentou deletar pedido de outro usuário OU
                       se lançamento financeiro está 'paid' (não pode deletar) OU
                       se user_id não foi fornecido
        """
        order = OrderRepository.get_by_id(db=db, order_id=order_id)
        if not order:
            return False
        
        # user_id é obrigatório para soft delete (precisamos saber quem deletou)
        if user_id is None:
            raise ValueError("user_id é obrigatório para soft delete")
        
        # Validação multi-tenant: user só pode deletar seus próprios pedidos
        if not is_admin and order.user_id != user_id:
            raise ValueError("Você não tem permissão para deletar este pedido")

        # INTEGRAÇÃO FINANCEIRA: Cancelar lançamento se existir e status='pending'
        # Se status='paid', lança exceção (bloqueia delete)
        FinancialService.cancel_entry_by_order(db=db, order_id=order_id)
        
        # Soft delete do pedido
        OrderRepository.soft_delete(db=db, order=order, deleted_by_user_id=user_id)
        return True
