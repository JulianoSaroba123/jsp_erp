"""
Repository para Order - acesso a dados.
Camada exclusiva de persistência (queries SQLAlchemy).
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.models.order import Order


class OrderRepository:
    """Repositório com queries de Order."""

    @staticmethod
    def list_paginated(db: Session, page: int, page_size: int) -> List[Order]:
        """
        Lista pedidos com paginação.
        Ordena por created_at desc (mais recentes primeiro).
        """
        offset = (page - 1) * page_size

        return (
            db.query(Order)
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

    @staticmethod
    def count_total(db: Session) -> int:
        """Conta total de pedidos no banco."""
        return db.query(Order).count()
    
    @staticmethod
    def list_by_user(db: Session, user_id: UUID, page: int, page_size: int) -> List[Order]:
        """
        Lista pedidos de um usuário específico com paginação.
        Ordena por created_at desc (mais recentes primeiro).
        """
        offset = (page - 1) * page_size

        return (
            db.query(Order)
            .filter(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )
    
    @staticmethod
    def count_by_user(db: Session, user_id: UUID) -> int:
        """Conta total de pedidos de um usuário específico."""
        return db.query(Order).filter(Order.user_id == user_id).count()

    @staticmethod
    def get_by_id(db: Session, order_id: UUID) -> Optional[Order]:
        """Busca pedido por ID. Retorna None se não existir."""
        return db.query(Order).filter(Order.id == order_id).first()

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
    def delete(db: Session, order: Order) -> None:
        """Remove pedido do banco."""
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
