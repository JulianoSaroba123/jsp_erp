"""
Repository para Order - acesso a dados.
Camada exclusiva de persistência (queries SQLAlchemy).
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.models.order import Order


class OrderRepository:
    """Repositório com queries de Order."""

    @staticmethod
    def list_paginated(db: Session, page: int, page_size: int, include_deleted: bool = False) -> List[Order]:
        """
        Lista pedidos com paginação.
        Ordena por created_at desc (mais recentes primeiro).
        Por padrão filtra registros soft-deleted.
        """
        offset = (page - 1) * page_size
        query = db.query(Order)
        
        if not include_deleted:
            query = query.filter(Order.deleted_at.is_(None))

        return (
            query
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

    @staticmethod
    def count_total(db: Session, include_deleted: bool = False) -> int:
        """Conta total de pedidos no banco (por padrão exclui soft-deleted)."""
        query = db.query(Order)
        if not include_deleted:
            query = query.filter(Order.deleted_at.is_(None))
        return query.count()
    
    @staticmethod
    def list_by_user(db: Session, user_id: UUID, page: int, page_size: int, include_deleted: bool = False) -> List[Order]:
        """
        Lista pedidos de um usuário específico com paginação.
        Ordena por created_at desc (mais recentes primeiro).
        Por padrão exclui soft-deleted.
        """
        offset = (page - 1) * page_size
        query = db.query(Order).filter(Order.user_id == user_id)
        
        if not include_deleted:
            query = query.filter(Order.deleted_at.is_(None))

        return (
            query
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )
    
    @staticmethod
    def count_by_user(db: Session, user_id: UUID, include_deleted: bool = False) -> int:
        """Conta total de pedidos de um usuário específico (exclui soft-deleted por padrão)."""
        query = db.query(Order).filter(Order.user_id == user_id)
        if not include_deleted:
            query = query.filter(Order.deleted_at.is_(None))
        return query.count()

    @staticmethod
    def get_by_id(db: Session, order_id: UUID, include_deleted: bool = False) -> Optional[Order]:
        """Busca pedido por ID. Retorna None se não existir ou estiver soft-deleted."""
        query = db.query(Order).filter(Order.id == order_id)
        if not include_deleted:
            query = query.filter(Order.deleted_at.is_(None))
        return query.first()

    @staticmethod
    def get_by_id_and_user(db: Session, order_id: UUID, user_id: UUID) -> Optional[Order]:
        """
        Busca pedido por ID com filtro multi-tenant.
        
        Retorna None se:
        - Order não existe
        - Order não pertence ao user_id fornecido
        
        Usado para anti-enumeration (404 para ambos os casos).
        """
        return (
            db.query(Order)
            .filter(Order.id == order_id, Order.user_id == user_id)
            .first()
        )

    @staticmethod
    def create(db: Session, user_id: UUID, description: str, total: float) -> Order:
        """
        Cria novo pedido.
        
        Fluxo:
        - db.add(): adiciona na sessão (staging)
        - db.commit(): executa INSERT no banco
        - db.refresh(): recarrega objeto com valores gerados (id, created_at)
        """
        order = Order(
            user_id=user_id,
            description=description,
            total=total
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        return order

    @staticmethod
    def soft_delete(db: Session, order: Order, deleted_by_user_id: UUID) -> Order:
        """Soft delete: marca pedido como deletado sem remover do banco."""
        order.deleted_at = datetime.utcnow()
        order.deleted_by = deleted_by_user_id
        db.commit()
        db.refresh(order)
        return order
    
    @staticmethod
    def restore(db: Session, order: Order) -> Order:
        """Restaura pedido soft-deleted."""
        order.deleted_at = None
        order.deleted_by = None
        db.commit()
        db.refresh(order)
        return order
    
    @staticmethod
    def hard_delete(db: Session, order: Order) -> None:
        """Hard delete: remove permanentemente do banco (uso raro)."""
        db.delete(order)
        db.commit()

    @staticmethod
    def update_order(db: Session, order: Order, description: Optional[str] = None, total: Optional[float] = None) -> Order:
        """
        Atualiza campos do pedido.
        
        Args:
            db: Sessão SQLAlchemy
            order: Instância Order já carregada (deve ter user_id validado)
            description: Nova descrição (None = não altera)
            total: Novo total (None = não altera)
        
        Returns:
            Order atualizado e refreshed
        
        Note:
            - NÃO faz commit (deixa para Service layer)
            - updated_at é atualizado automaticamente via onupdate
        """
        if description is not None:
            order.description = description
        
        if total is not None:
            order.total = total
        
        return order
