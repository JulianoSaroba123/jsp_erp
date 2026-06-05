"""
Repository para FinancialEntry - acesso a dados.
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.models.financial_entry import FinancialEntry


class FinancialRepository:
    """Repositorio com queries de FinancialEntry."""

    @staticmethod
    def create(db: Session, entry: FinancialEntry) -> FinancialEntry:
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def get_by_id(db: Session, entry_id: UUID, include_deleted: bool = False) -> Optional[FinancialEntry]:
        query = db.query(FinancialEntry).filter(FinancialEntry.id == entry_id)
        if not include_deleted:
            query = query.filter(FinancialEntry.deleted_at.is_(None))
        return query.first()

    @staticmethod
    def get_by_order_id(db: Session, order_id: UUID, include_deleted: bool = False) -> Optional[FinancialEntry]:
        query = db.query(FinancialEntry).filter(FinancialEntry.order_id == order_id)
        if not include_deleted:
            query = query.filter(FinancialEntry.deleted_at.is_(None))
        return query.first()

    @staticmethod
    def list_paginated(
        db: Session,
        page: int,
        page_size: int,
        user_id: Optional[UUID] = None,
        status: Optional[str] = None,
        kind: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        include_deleted: bool = False,
    ) -> List[FinancialEntry]:
        offset = (page - 1) * page_size
        query = db.query(FinancialEntry)

        if not include_deleted:
            query = query.filter(FinancialEntry.deleted_at.is_(None))

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
        date_to: Optional[datetime] = None,
        include_deleted: bool = False,
    ) -> int:
        query = db.query(FinancialEntry)

        if not include_deleted:
            query = query.filter(FinancialEntry.deleted_at.is_(None))

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
        entry.status = new_status
        entry.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def soft_delete(db: Session, entry: FinancialEntry, deleted_by_user_id: UUID) -> FinancialEntry:
        entry.deleted_at = datetime.utcnow()
        entry.deleted_by = deleted_by_user_id
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def restore(db: Session, entry: FinancialEntry) -> FinancialEntry:
        entry.deleted_at = None
        entry.deleted_by = None
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def hard_delete(db: Session, entry: FinancialEntry) -> None:
        db.delete(entry)
        db.commit()
