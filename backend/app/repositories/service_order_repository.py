"""
Repository para Service Order - acesso a dados.
Camada exclusiva de persistência (queries SQLAlchemy).
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, extract, or_
from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime, date

from app.models.service_order import (
    ServiceOrder,
    ServiceOrderItem,
    ServiceOrderProduct,
    ServiceOrderInstallment,
    ServiceOrderAttachment
)


class ServiceOrderRepository:
    """Repositório com queries de ServiceOrder."""

    @staticmethod
    def generate_next_number(db: Session) -> str:
        """
        Gera o próximo número de OS no formato OS2025001, OS2025002, etc.
        
        Sistema inteligente que:
        - Usa o ano atual
        - Busca o maior número existente
        - Garante sequência sem duplicatas
        - Formato: OS + ANO + SEQUENCIAL (4 dígitos)
        """
        current_year = date.today().year
        prefix = f"OS{current_year}"
        
        # Busca a OS com maior número do ano
        last_so = (
            db.query(ServiceOrder)
            .filter(
                ServiceOrder.number.like(f"{prefix}%"),
                ServiceOrder.deleted_at.is_(None)
            )
            .order_by(ServiceOrder.number.desc())
            .first()
        )
        
        if last_so:
            try:
                # Extrai a parte numérica
                numeric_part = last_so.number.replace(prefix, "")
                if numeric_part.isdigit():
                    next_number = int(numeric_part) + 1
                else:
                    next_number = 1
            except (ValueError, AttributeError):
                next_number = 1
        else:
            next_number = 1
        
        # Gera o número final
        new_number = f"{prefix}{next_number:04d}"
        
        # Verificação de segurança contra duplicatas
        attempts = 0
        while ServiceOrderRepository.get_by_number(db, new_number) and attempts < 100:
            next_number += 1
            new_number = f"{prefix}{next_number:04d}"
            attempts += 1
        
        return new_number

    @staticmethod
    def list_paginated(
        db: Session, 
        page: int, 
        page_size: int, 
        include_deleted: bool = False,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        customer_id: Optional[UUID] = None,
        search: Optional[str] = None
    ) -> List[ServiceOrder]:
        """
        Lista ordens de serviço com paginação e filtros.
        Ordena por created_at desc (mais recentes primeiro).
        """
        offset = (page - 1) * page_size
        query = db.query(ServiceOrder)
        
        # Filtro de soft delete
        if not include_deleted:
            query = query.filter(ServiceOrder.deleted_at.is_(None))
        
        # Filtros opcionais
        if status:
            query = query.filter(ServiceOrder.status == status)
        if priority:
            query = query.filter(ServiceOrder.priority == priority)
        if customer_id:
            query = query.filter(ServiceOrder.customer_id == customer_id)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    ServiceOrder.number.ilike(search_pattern),
                    ServiceOrder.title.ilike(search_pattern),
                    ServiceOrder.equipment.ilike(search_pattern),
                    ServiceOrder.technician.ilike(search_pattern)
                )
            )
        
        return (
            query
            .order_by(ServiceOrder.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

    @staticmethod
    def count_total(
        db: Session, 
        include_deleted: bool = False,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        customer_id: Optional[UUID] = None,
        search: Optional[str] = None
    ) -> int:
        """Conta total de ordens de serviço com filtros."""
        query = db.query(ServiceOrder)
        
        if not include_deleted:
            query = query.filter(ServiceOrder.deleted_at.is_(None))
        
        if status:
            query = query.filter(ServiceOrder.status == status)
        if priority:
            query = query.filter(ServiceOrder.priority == priority)
        if customer_id:
            query = query.filter(ServiceOrder.customer_id == customer_id)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    ServiceOrder.number.ilike(search_pattern),
                    ServiceOrder.title.ilike(search_pattern),
                    ServiceOrder.equipment.ilike(search_pattern),
                    ServiceOrder.technician.ilike(search_pattern)
                )
            )
        
        return query.count()

    @staticmethod
    def get_by_id(db: Session, service_order_id: UUID, include_deleted: bool = False) -> Optional[ServiceOrder]:
        """Busca ordem de serviço por ID."""
        query = db.query(ServiceOrder).filter(ServiceOrder.id == service_order_id)
        if not include_deleted:
            query = query.filter(ServiceOrder.deleted_at.is_(None))
        return query.first()

    @staticmethod
    def get_by_id_with_relations(db: Session, service_order_id: UUID) -> Optional[ServiceOrder]:
        """Busca ordem de serviço por ID com todas as relações carregadas."""
        return (
            db.query(ServiceOrder)
            .options(
                joinedload(ServiceOrder.items),
                joinedload(ServiceOrder.products),
                joinedload(ServiceOrder.installments),
                joinedload(ServiceOrder.attachments)
            )
            .filter(
                ServiceOrder.id == service_order_id,
                ServiceOrder.deleted_at.is_(None)
            )
            .first()
        )

    @staticmethod
    def get_by_number(db: Session, number: str) -> Optional[ServiceOrder]:
        """Busca ordem de serviço por número."""
        return (
            db.query(ServiceOrder)
            .filter(
                ServiceOrder.number == number,
                ServiceOrder.deleted_at.is_(None)
            )
            .first()
        )

    @staticmethod
    def create(db: Session, service_order_data: dict) -> ServiceOrder:
        """Cria nova ordem de serviço."""
        # Gera número automaticamente se não fornecido
        if 'number' not in service_order_data or not service_order_data['number']:
            service_order_data['number'] = ServiceOrderRepository.generate_next_number(db)
        
        service_order = ServiceOrder(**service_order_data)
        db.add(service_order)
        db.commit()
        db.refresh(service_order)
        return service_order

    @staticmethod
    def update(db: Session, service_order: ServiceOrder, update_data: dict) -> ServiceOrder:
        """
        Atualiza ordem de serviço.
        
        Aplica apenas campos fornecidos e não vazios para preservar dados existentes.
        """
        for key, value in update_data.items():
            if not hasattr(service_order, key):
                continue
            
            # Ignorar None e strings vazias para preservar dados existentes
            if value is None:
                continue
            if isinstance(value, str) and value.strip() == '':
                continue
            
            # Aplicar o novo valor
            setattr(service_order, key, value)
        
        service_order.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(service_order)
        return service_order

    @staticmethod
    def soft_delete(db: Session, service_order: ServiceOrder) -> ServiceOrder:
        """Soft delete: marca ordem como deletada."""
        service_order.deleted_at = datetime.utcnow()
        db.commit()
        db.refresh(service_order)
        return service_order

    @staticmethod
    def restore(db: Session, service_order: ServiceOrder) -> ServiceOrder:
        """Restaura ordem de serviço soft-deleted."""
        service_order.deleted_at = None
        db.commit()
        db.refresh(service_order)
        return service_order

    @staticmethod
    def get_statistics(db: Session) -> Dict:
        """
        Retorna estatísticas para o dashboard.
        
        Returns:
            Dict com: total, pendente, em_execucao, finalizada_mes_atual
        """
        current_month = date.today().month
        current_year = date.today().year
        
        # Total ativo
        total = db.query(ServiceOrder).filter(ServiceOrder.deleted_at.is_(None)).count()
        
        # Por status
        pendente = db.query(ServiceOrder).filter(
            ServiceOrder.deleted_at.is_(None),
            ServiceOrder.status == 'pendente'
        ).count()
        
        em_execucao = db.query(ServiceOrder).filter(
            ServiceOrder.deleted_at.is_(None),
            ServiceOrder.status == 'em_execucao'
        ).count()
        
        # Finalizadas no mês atual
        finalizada_mes = db.query(ServiceOrder).filter(
            ServiceOrder.deleted_at.is_(None),
            ServiceOrder.status == 'finalizada',
            extract('month', ServiceOrder.completion_date) == current_month,
            extract('year', ServiceOrder.completion_date) == current_year
        ).count()
        
        return {
            'total': total,
            'pendente': pendente,
            'em_execucao': em_execucao,
            'finalizada_mes': finalizada_mes
        }


# ==================== ServiceOrderItem Repository ====================

class ServiceOrderItemRepository:
    """Repositório para itens de serviço."""

    @staticmethod
    def get_by_id(db: Session, item_id: UUID) -> Optional[ServiceOrderItem]:
        """Busca item de serviço por ID."""
        return (
            db.query(ServiceOrderItem)
            .filter(ServiceOrderItem.id == item_id)
            .first()
        )

    @staticmethod
    def list_by_service_order(db: Session, service_order_id: UUID) -> List[ServiceOrderItem]:
        """Lista itens de uma ordem de serviço."""
        return (
            db.query(ServiceOrderItem)
            .filter(ServiceOrderItem.service_order_id == service_order_id)
            .all()
        )

    @staticmethod
    def create(db: Session, item_data: dict) -> ServiceOrderItem:
        """Cria novo item de serviço."""
        item = ServiceOrderItem(**item_data)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def update(db: Session, item: ServiceOrderItem, update_data: dict) -> ServiceOrderItem:
        """Atualiza item de serviço."""
        for key, value in update_data.items():
            if hasattr(item, key):
                setattr(item, key, value)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def delete(db: Session, item: ServiceOrderItem) -> None:
        """Remove item de serviço."""
        db.delete(item)
        db.commit()


# ==================== ServiceOrderProduct Repository ====================

class ServiceOrderProductRepository:
    """Repositório para produtos utilizados."""

    @staticmethod
    def get_by_id(db: Session, product_id: UUID) -> Optional[ServiceOrderProduct]:
        """Busca produto utilizado por ID."""
        return (
            db.query(ServiceOrderProduct)
            .filter(ServiceOrderProduct.id == product_id)
            .first()
        )

    @staticmethod
    def list_by_service_order(db: Session, service_order_id: UUID) -> List[ServiceOrderProduct]:
        """Lista produtos de uma ordem de serviço."""
        return (
            db.query(ServiceOrderProduct)
            .filter(ServiceOrderProduct.service_order_id == service_order_id)
            .all()
        )

    @staticmethod
    def create(db: Session, product_data: dict) -> ServiceOrderProduct:
        """Cria novo produto utilizado."""
        product = ServiceOrderProduct(**product_data)
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def update(db: Session, product: ServiceOrderProduct, update_data: dict) -> ServiceOrderProduct:
        """Atualiza produto utilizado."""
        for key, value in update_data.items():
            if hasattr(product, key):
                setattr(product, key, value)
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def delete(db: Session, product: ServiceOrderProduct) -> None:
        """Remove produto utilizado."""
        db.delete(product)
        db.commit()


# ==================== ServiceOrderInstallment Repository ====================

class ServiceOrderInstallmentRepository:
    """Repositório para parcelas."""

    @staticmethod
    def get_by_id(db: Session, installment_id: UUID) -> Optional[ServiceOrderInstallment]:
        """Busca parcela por ID."""
        return (
            db.query(ServiceOrderInstallment)
            .filter(ServiceOrderInstallment.id == installment_id)
            .first()
        )

    @staticmethod
    def list_by_service_order(db: Session, service_order_id: UUID) -> List[ServiceOrderInstallment]:
        """Lista parcelas de uma ordem de serviço."""
        return (
            db.query(ServiceOrderInstallment)
            .filter(ServiceOrderInstallment.service_order_id == service_order_id)
            .order_by(ServiceOrderInstallment.installment_number)
            .all()
        )

    @staticmethod
    def create(db: Session, installment_data: dict) -> ServiceOrderInstallment:
        """Cria nova parcela."""
        installment = ServiceOrderInstallment(**installment_data)
        db.add(installment)
        db.commit()
        db.refresh(installment)
        return installment

    @staticmethod
    def update(db: Session, installment: ServiceOrderInstallment, update_data: dict) -> ServiceOrderInstallment:
        """Atualiza parcela."""
        for key, value in update_data.items():
            if hasattr(installment, key):
                setattr(installment, key, value)
        db.commit()
        db.refresh(installment)
        return installment

    @staticmethod
    def delete(db: Session, installment: ServiceOrderInstallment) -> None:
        """Remove parcela."""
        db.delete(installment)
        db.commit()


# ==================== ServiceOrderAttachment Repository ====================

class ServiceOrderAttachmentRepository:
    """Repositório para anexos."""

    @staticmethod
    def list_by_service_order(db: Session, service_order_id: UUID) -> List[ServiceOrderAttachment]:
        """Lista anexos de uma ordem de serviço."""
        return (
            db.query(ServiceOrderAttachment)
            .filter(ServiceOrderAttachment.service_order_id == service_order_id)
            .order_by(ServiceOrderAttachment.created_at)
            .all()
        )

    @staticmethod
    def get_by_id(db: Session, attachment_id: UUID) -> Optional[ServiceOrderAttachment]:
        """Busca anexo por ID."""
        return (
            db.query(ServiceOrderAttachment)
            .filter(ServiceOrderAttachment.id == attachment_id)
            .first()
        )

    @staticmethod
    def create(db: Session, attachment_data: dict) -> ServiceOrderAttachment:
        """Cria novo anexo."""
        attachment = ServiceOrderAttachment(**attachment_data)
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
        return attachment

    @staticmethod
    def delete(db: Session, attachment: ServiceOrderAttachment) -> None:
        """Remove anexo."""
        db.delete(attachment)
        db.commit()
