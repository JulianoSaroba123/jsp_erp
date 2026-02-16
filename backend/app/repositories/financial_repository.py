"""
Repository para FinancialEntry - acesso a dados.
Camada exclusiva de persistência (queries SQLAlchemy).
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.models.financial_entry import FinancialEntry


class FinancialRepository:
    """Repositório com queries de FinancialEntry."""

    @staticmethod
    def create(db: Session, entry: FinancialEntry) -> FinancialEntry:
        """
        Cria novo lançamento financeiro.
        
        Args:
            db: Sessão SQLAlchemy
            entry: Objeto FinancialEntry (não commitado)
            
        Returns:
            FinancialEntry criado com ID
        """
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def get_by_id(db: Session, entry_id: UUID) -> Optional[FinancialEntry]:
        """Busca lançamento por ID."""
        return db.query(FinancialEntry).filter(FinancialEntry.id == entry_id).first()
    
    @staticmethod
    def get_by_order_id(db: Session, order_id: UUID) -> Optional[FinancialEntry]:
        """
        Busca lançamento vinculado a um pedido específico.
        
        Args:
            db: Sessão SQLAlchemy
            order_id: UUID do pedido
            
        Returns:
            FinancialEntry ou None se não existir
        """
        return db.query(FinancialEntry).filter(FinancialEntry.order_id == order_id).first()

    @staticmethod
    def list_paginated(
        db: Session,
        page: int,
        page_size: int,
        user_id: Optional[UUID] = None,
        status: Optional[str] = None,
        kind: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[FinancialEntry]:
        """
        Lista lançamentos com paginação e filtros opcionais.
        
        Args:
            db: Sessão SQLAlchemy
            page: Número da página (1-indexed)
            page_size: Itens por página
            user_id: Filtro opcional por usuário (multi-tenant)
            status: Filtro opcional por status
            kind: Filtro opcional por tipo (revenue/expense)
            date_from: Data inicial (occurred_at >= date_from)
            date_to: Data final (occurred_at <= date_to)
            
        Returns:
            Lista de FinancialEntry
        """
        offset = (page - 1) * page_size
        query = db.query(FinancialEntry)

        # Filtros opcionais
        if user_id:
            query = query.filter(FinancialEntry.user_id == user_id)
        if status:
            query = query.filter(FinancialEntry.status == status)
        if kind:
            query = query.filter(FinancialEntry.kind == kind)
        if date_from:
            query = query.filter(FinancialEntry.occurred_at >= date_from)
        if date_to:
            query = query.filter(FinancialEntry.occurred_at <= date_to)

        # Ordenação: mais recentes primeiro
        return (
            query
            .order_by(FinancialEntry.occurred_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

    @staticmethod
    def count_total(
        db: Session,
        user_id: Optional[UUID] = None,
        status: Optional[str] = None,
        kind: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> int:
        """
        Conta total de lançamentos com filtros opcionais.
        
        Args:
            db: Sessão SQLAlchemy
            user_id: Filtro opcional por usuário
            status: Filtro opcional por status
            kind: Filtro opcional por tipo
            date_from: Data inicial
            date_to: Data final
            
        Returns:
            Número total de registros
        """
        query = db.query(FinancialEntry)

        # Aplicar mesmos filtros da lista
        if user_id:
            query = query.filter(FinancialEntry.user_id == user_id)
        if status:
            query = query.filter(FinancialEntry.status == status)
        if kind:
            query = query.filter(FinancialEntry.kind == kind)
        if date_from:
            query = query.filter(FinancialEntry.occurred_at >= date_from)
        if date_to:
            query = query.filter(FinancialEntry.occurred_at <= date_to)

        return query.count()

    @staticmethod
    def update_status(db: Session, entry: FinancialEntry, new_status: str) -> FinancialEntry:
        """
        Atualiza status de um lançamento.
        
        Args:
            db: Sessão SQLAlchemy
            entry: FinancialEntry a ser atualizado
            new_status: Novo status (pending, paid, canceled)
            
        Returns:
            FinancialEntry atualizado
        """
        entry.status = new_status
        entry.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(entry)
        return entry
    
    @staticmethod
    def delete(db: Session, entry: FinancialEntry) -> None:
        """
        Deleta lançamento (uso raro - preferir cancelamento via status).
        
        Args:
            db: Sessão SQLAlchemy
            entry: FinancialEntry a ser deletado
        """
        db.delete(entry)
        db.commit()
