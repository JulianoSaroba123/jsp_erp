"""
Service para ServiceOrder - regras de negócio.
Camada de validações e lógica de negócio para Ordens de Serviço.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime, date
from decimal import Decimal

from app.repositories.service_order_repository import (
    ServiceOrderRepository,
    ServiceOrderItemRepository,
    ServiceOrderProductRepository,
    ServiceOrderInstallmentRepository,
    ServiceOrderEquipmentRepository,
    ServiceOrderAttachmentRepository
)
from app.repositories.financial_repository import FinancialRepository
from app.models.financial_entry import FinancialEntry
from app.exceptions.errors import ConflictError, NotFoundError, ValidationError
from app.models.customer import Customer
from app.models.proposal import Proposal, ProposalItem, ProposalProduct
from app.models.service_order import (
    ServiceOrder,
    ServiceOrderItem,
    ServiceOrderProduct,
    ServiceOrderInstallment,
    ServiceOrderAttachment,
)


class ServiceOrderService:
    """Service com regras de negócio para ordens de serviço."""

    VALID_STATUSES = [
        'draft', 'open', 'in_progress', 'waiting_parts', 'completed', 'canceled',
        'pendente', 'em_execucao', 'finalizada', 'cancelada',
    ]
    VALID_PRIORITIES = ['low', 'medium', 'high', 'urgent', 'baixa', 'normal', 'alta', 'urgente']
    VALID_ORDER_TYPES = ['comercial', 'operacional']
    VALID_PAYMENT_CONDITIONS = ['a_vista', 'parcelado']
    VALID_PAYMENT_STATUSES = ['pending', 'partial', 'paid', 'canceled', 'pendente', 'parcial', 'pago', 'vencido']
    VALID_INSTALLMENT_STATUSES = ['pending', 'paid', 'overdue', 'canceled']
    FINAL_STATUSES = ['completed', 'canceled', 'finalizada', 'cancelada']
    STATUS_TRANSITIONS = {
        'draft': ['open', 'canceled'],
        'open': ['in_progress', 'waiting_parts', 'completed', 'canceled'],
        'in_progress': ['waiting_parts', 'completed', 'canceled'],
        'waiting_parts': ['in_progress', 'completed', 'canceled'],
        'completed': [],
        'canceled': [],
        'pendente': ['em_execucao', 'cancelada'],
        'em_execucao': ['finalizada', 'cancelada'],
        'finalizada': [],
        'cancelada': [],
    }

    @staticmethod
    def _normalize_service_order_data(service_order_data: dict) -> None:
        """Normaliza valores vazios vindos do formulário antes de validar."""
        nullable_fields = [
            'description', 'location', 'requester', 'problem_description',
            'technician', 'equipment', 'brand_model', 'serial_number',
            'reported_defect', 'technical_diagnosis', 'solution', 'notes',
            'technical_report', 'observations', 'client_name', 'client_document',
            'client_phone', 'client_email', 'client_address', 'payment_method',
            'opening_date', 'scheduled_date', 'expected_date', 'start_date',
            'completed_date', 'completion_date', 'start_time', 'end_time',
            'total_hours', 'total_km', 'morning_entry_time', 'lunch_exit_time',
            'lunch_return_time', 'evening_exit_time', 'overtime_entry_time',
            'overtime_exit_time', 'customer_signature', 'customer_signature_name',
            'customer_signature_date', 'technician_signature',
            'technician_signature_name', 'technician_signature_date',
            'attachments_notes', 'proposal_id', 'service_type',
            'first_installment_date', 'payment_due_date', 'payment_description',
            'started_at', 'completed_at'
        ]

        for field in nullable_fields:
            if field in service_order_data and service_order_data[field] == '':
                service_order_data[field] = None

        numeric_fields = [
            'initial_km', 'final_km', 'warranty_days', 'regular_hours',
            'overtime_hours', 'lunch_break_minutes', 'installment_count'
        ]

        for field in numeric_fields:
            if field in service_order_data and service_order_data[field] == '':
                service_order_data[field] = None

        money_fields = ['service_amount', 'parts_amount', 'discount_amount', 'total_amount', 'down_payment']
        money_fields.extend([
            'total_services', 'total_products', 'total_displacement', 'total_discount', 'total_amount_enterprise'
        ])

        for field in money_fields:
            if field in service_order_data and (service_order_data[field] == '' or service_order_data[field] is None):
                service_order_data[field] = 0.00

    @staticmethod
    def _validate_customer_exists(db: Session, customer_id: Optional[UUID]) -> None:
        if not customer_id:
            raise ValidationError("Cliente é obrigatório")

        customer = (
            db.query(Customer)
            .filter(Customer.id == customer_id, Customer.deleted_at.is_(None))
            .first()
        )
        if not customer:
            raise ValidationError("Cliente informado não existe ou está inativo")

    @staticmethod
    def _validate_professional_rules(
        db: Session,
        service_order_data: dict,
        existing_order: Optional["ServiceOrder"] = None
    ) -> None:
        title = (service_order_data.get('title') or getattr(existing_order, 'title', '') or '').strip()
        if not title:
            raise ValidationError("Título é obrigatório")

        customer_id = service_order_data.get('customer_id') or getattr(existing_order, 'customer_id', None)
        ServiceOrderService._validate_customer_exists(db, customer_id)

        status_value = service_order_data.get('status', getattr(existing_order, 'status', 'pendente'))
        if status_value not in ServiceOrderService.VALID_STATUSES:
            raise ValidationError(f"Status inválido. Deve ser: {', '.join(ServiceOrderService.VALID_STATUSES)}")

        priority = service_order_data.get('priority', getattr(existing_order, 'priority', 'normal'))
        if priority not in ServiceOrderService.VALID_PRIORITIES:
            raise ValidationError(f"Prioridade inválida. Deve ser: {', '.join(ServiceOrderService.VALID_PRIORITIES)}")

        order_type = service_order_data.get('order_type', getattr(existing_order, 'order_type', 'comercial'))
        if order_type not in ServiceOrderService.VALID_ORDER_TYPES:
            raise ValidationError("Tipo da OS invalido. Use comercial ou operacional")

        payment_condition = service_order_data.get(
            'payment_condition',
            getattr(existing_order, 'payment_condition', 'a_vista')
        )
        if payment_condition not in ServiceOrderService.VALID_PAYMENT_CONDITIONS:
            raise ValidationError("Forma de pagamento invalida. Use a_vista ou parcelado")

        payment_status = service_order_data.get(
            'payment_status',
            getattr(existing_order, 'payment_status', 'pendente')
        )
        if payment_status not in ServiceOrderService.VALID_PAYMENT_STATUSES:
            raise ValidationError(
                f"Status de pagamento invalido. Deve ser: {', '.join(ServiceOrderService.VALID_PAYMENT_STATUSES)}"
            )

        opening_date = service_order_data.get('opening_date') or getattr(existing_order, 'opening_date', None) or date.today()
        expected_date = service_order_data.get('expected_date') or getattr(existing_order, 'expected_date', None)
        scheduled_date = service_order_data.get('scheduled_date') or getattr(existing_order, 'scheduled_date', None)
        completed_date = service_order_data.get('completed_date') or getattr(existing_order, 'completed_date', None)

        for field_name, field_value in [
            ('Data prevista', expected_date),
            ('Data agendada', scheduled_date),
            ('Data de conclusão', completed_date),
        ]:
            if field_value and opening_date and field_value < opening_date:
                raise ValidationError(f"{field_name} não pode ser anterior à data de abertura")

        initial_km = service_order_data.get('initial_km', getattr(existing_order, 'initial_km', None))
        final_km = service_order_data.get('final_km', getattr(existing_order, 'final_km', None))
        if initial_km is not None and final_km is not None and final_km < initial_km:
            raise ValidationError("KM final não pode ser menor que KM inicial")

        if status_value == 'finalizada':
            has_solution = service_order_data.get('solution') or getattr(existing_order, 'solution', None)
            has_diagnosis = service_order_data.get('technical_diagnosis') or getattr(existing_order, 'technical_diagnosis', None)
            if not has_solution and not has_diagnosis:
                raise ValidationError("Para finalizar a OS, informe ao menos o diagnóstico técnico ou a solução aplicada")

    @staticmethod
    def _as_decimal(value) -> Decimal:
        if value is None:
            return Decimal("0")
        return Decimal(str(value))

    @staticmethod
    def _calculate_total(service_amount, parts_amount, discount_amount) -> Decimal:
        total = (
            ServiceOrderService._as_decimal(service_amount)
            + ServiceOrderService._as_decimal(parts_amount)
            - ServiceOrderService._as_decimal(discount_amount)
        )
        return max(total, Decimal("0"))

    @staticmethod
    def _set_total_from_amounts(service_order_data: dict) -> None:
        service_order_data['total_amount'] = ServiceOrderService._calculate_total(
            service_order_data.get('service_amount', 0),
            service_order_data.get('parts_amount', 0),
            service_order_data.get('discount_amount', 0),
        )

    @staticmethod
    def _set_related_totals(
        db: Session,
        service_order: "ServiceOrder",
        force_items: bool = False,
        force_products: bool = False
    ) -> None:
        items = ServiceOrderItemRepository.list_by_service_order(db, service_order.id)
        products = ServiceOrderProductRepository.list_by_service_order(db, service_order.id)
        service_amount = (
            sum(ServiceOrderService._as_decimal(item.total_price) for item in items)
            if items or force_items
            else ServiceOrderService._as_decimal(service_order.service_amount)
        )
        parts_amount = (
            sum(ServiceOrderService._as_decimal(product.total_price) for product in products)
            if products or force_products
            else ServiceOrderService._as_decimal(service_order.parts_amount)
        )
        discount_amount = ServiceOrderService._as_decimal(service_order.discount_amount)

        service_order.service_amount = service_amount
        service_order.parts_amount = parts_amount
        service_order.total_amount = ServiceOrderService._calculate_total(
            service_amount,
            parts_amount,
            discount_amount,
        )
        db.commit()
        db.refresh(service_order)

    @staticmethod
    def _with_calculated_line_total(line_data: dict) -> dict:
        line_data = dict(line_data)
        if ServiceOrderService._as_decimal(line_data.get('quantity')) < 0:
            raise ValidationError("Quantidade não pode ser negativa")
        if ServiceOrderService._as_decimal(line_data.get('unit_price')) < 0:
            raise ValidationError("Valor unitário não pode ser negativo")
        line_data['total_price'] = (
            ServiceOrderService._as_decimal(line_data.get('quantity'))
            * ServiceOrderService._as_decimal(line_data.get('unit_price'))
        )
        return line_data

    @staticmethod
    def _normalize_payment_status(value: Optional[str]) -> str:
        status = (value or 'pending').strip().lower()
        mapping = {
            'pendente': 'pending',
            'parcial': 'partial',
            'pago': 'paid',
            'cancelado': 'canceled',
            'vencido': 'pending',
        }
        return mapping.get(status, status)

    @staticmethod
    def _sync_enterprise_totals(service_order: "ServiceOrder") -> None:
        service_order.total_services = ServiceOrderService._as_decimal(service_order.service_amount)
        service_order.total_products = ServiceOrderService._as_decimal(service_order.parts_amount)
        service_order.total_discount = ServiceOrderService._as_decimal(service_order.discount_amount)
        service_order.total_amount_enterprise = ServiceOrderService._as_decimal(service_order.total_amount)

    @staticmethod
    def _sync_financial_entry(db: Session, service_order: "ServiceOrder") -> None:
        """Sincroniza lançamento financeiro automático da OS."""
        if not service_order.user_id:
            raise ValidationError("user_id é obrigatório para ordem de serviço")

        financial_entry = (
            db.query(FinancialEntry)
            .filter(
                FinancialEntry.service_order_id == service_order.id,
                FinancialEntry.deleted_at.is_(None),
            )
            .first()
        )

        total_amount = ServiceOrderService._as_decimal(service_order.total_amount)
        payment_status = ServiceOrderService._normalize_payment_status(service_order.payment_status)

        if financial_entry and financial_entry.status == 'paid' and payment_status in ('paid', 'pago'):
            # Não altera lançamento já quitado.
            return

        if financial_entry and financial_entry.status == 'paid' and service_order.status in ('cancelada', 'canceled'):
            raise ConflictError("Não é possível cancelar OS com financeiro já pago")

        if service_order.status in ('cancelada', 'canceled'):
            if financial_entry and financial_entry.status != 'paid':
                financial_entry.status = 'canceled'
                financial_entry.updated_at = datetime.utcnow()
                db.commit()
            return

        if total_amount <= 0:
            if financial_entry and financial_entry.status == 'pending':
                financial_entry.status = 'canceled'
                financial_entry.updated_at = datetime.utcnow()
                db.commit()
            return

        description = f"OS {service_order.number} - {service_order.title}"
        if financial_entry:
            if financial_entry.status == 'paid' and total_amount != ServiceOrderService._as_decimal(financial_entry.amount):
                raise ConflictError("Não é possível alterar total de OS com financeiro pago")

            financial_entry.amount = total_amount
            financial_entry.description = description
            if financial_entry.status == 'canceled':
                financial_entry.status = 'pending'
            financial_entry.origin = 'ORDEM_SERVICO'
            financial_entry.updated_at = datetime.utcnow()
            db.commit()
            return

        entry = FinancialEntry(
            user_id=service_order.user_id,
            order_id=None,
            service_order_id=service_order.id,
            kind='revenue',
            status='pending',
            amount=total_amount,
            description=description,
            occurred_at=datetime.utcnow(),
            origin='ORDEM_SERVICO',
        )
        FinancialRepository.create(db=db, entry=entry)

    @staticmethod
    def list_service_orders(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[UUID] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        customer_id: Optional[UUID] = None,
        search: Optional[str] = None
    ) -> Dict:
        """
        Lista ordens de serviço com paginação e filtros.
        
        Regras de negócio:
        - page mínimo: 1
        - page_size máximo: 100
        
        Returns:
            Dict com items, page, page_size, total
        """
        # Validação: page >= 1
        if page < 1:
            page = 1

        # Regra: limitar page_size
        if page_size > 100:
            page_size = 100
        if page_size < 1:
            page_size = 1

        # Busca dados
        service_orders = ServiceOrderRepository.list_paginated(
            db=db,
            page=page,
            page_size=page_size,
            user_id=user_id,
            status=status,
            priority=priority,
            customer_id=customer_id,
            search=search
        )
        
        total = ServiceOrderRepository.count_total(
            db=db,
            user_id=user_id,
            status=status,
            priority=priority,
            customer_id=customer_id,
            search=search
        )

        return {
            "items": service_orders,
            "page": page,
            "page_size": page_size,
            "total": total
        }

    @staticmethod
    def create_service_order(db: Session, service_order_data: dict) -> "ServiceOrder":
        """
        Cria ordem de serviço com validações.
        
        Validações:
        1. customer_id deve existir
        2. title não pode ser vazio
        3. Gera número automático
        4. Valida status e priority
        """
        ServiceOrderService._normalize_service_order_data(service_order_data)
        service_order_data.setdefault('opening_date', date.today())

        # Extrai itens relacionados antes de criar registro principal
        items_data = service_order_data.pop('items', [])
        products_data = service_order_data.pop('products', [])
        installments_data = service_order_data.pop('installments', [])
        equipments_data = service_order_data.pop('equipments', [])

        items_data = [ServiceOrderService._with_calculated_line_total(item) for item in items_data]
        products_data = [ServiceOrderService._with_calculated_line_total(product) for product in products_data]

        service_amount = sum((item.get('total_price') or 0) for item in items_data)
        parts_amount = sum((product.get('total_price') or 0) for product in products_data)
        if service_amount and 'service_amount' not in service_order_data:
            service_order_data['service_amount'] = service_amount
        if parts_amount and 'parts_amount' not in service_order_data:
            service_order_data['parts_amount'] = parts_amount
        ServiceOrderService._set_total_from_amounts(service_order_data)
        service_order_data['total_services'] = service_order_data.get('service_amount', 0)
        service_order_data['total_products'] = service_order_data.get('parts_amount', 0)
        service_order_data['total_discount'] = service_order_data.get('discount_amount', 0)
        service_order_data['total_amount_enterprise'] = service_order_data.get('total_amount', 0)
        if not service_order_data.get('code') and service_order_data.get('number'):
            service_order_data['code'] = service_order_data.get('number')
        if service_order_data.get('payment_status'):
            service_order_data['payment_status'] = ServiceOrderService._normalize_payment_status(
                service_order_data.get('payment_status')
            )

        ServiceOrderService._validate_professional_rules(db, service_order_data)

        # Cria ordem de serviço (número é gerado automaticamente no repository)
        service_order = ServiceOrderRepository.create(db=db, service_order_data=service_order_data)

        # Cria itens de serviço
        for item_data in items_data:
            item_data['service_order_id'] = service_order.id
            ServiceOrderItemRepository.create(db=db, item_data=item_data)

        # Cria produtos utilizados
        for product_data in products_data:
            product_data['service_order_id'] = service_order.id
            ServiceOrderProductRepository.create(db=db, product_data=product_data)

        # Cria parcelas
        for installment_data in installments_data:
            installment_data['service_order_id'] = service_order.id
            installment_data.setdefault('status', 'paid' if installment_data.get('paid') else 'pending')
            ServiceOrderInstallmentRepository.create(db=db, installment_data=installment_data)

        # Cria equipamentos
        for equipment_data in equipments_data:
            equipment_data = dict(equipment_data)
            equipment_data['service_order_id'] = service_order.id
            ServiceOrderEquipmentRepository.create(db=db, equipment_data=equipment_data)

        ServiceOrderService._set_related_totals(db, service_order, force_items=True, force_products=True)
        ServiceOrderService._sync_enterprise_totals(service_order)
        if not service_order.code:
            service_order.code = service_order.number
        db.commit()
        db.refresh(service_order)
        ServiceOrderService._sync_financial_entry(db, service_order)

        return service_order

    @staticmethod
    def get_service_order(db: Session, service_order_id: UUID, with_relations: bool = False) -> Optional["ServiceOrder"]:
        """
        Busca ordem de serviço por ID.
        
        Args:
            service_order_id: UUID da ordem
            with_relations: Se True, carrega itens, produtos, parcelas e anexos
        """
        if with_relations:
            return ServiceOrderRepository.get_by_id_with_relations(db=db, service_order_id=service_order_id)
        return ServiceOrderRepository.get_by_id(db=db, service_order_id=service_order_id)

    @staticmethod
    def get_service_order_scoped(
        db: Session,
        service_order_id: UUID,
        user_id: Optional[UUID],
        with_relations: bool = False,
    ) -> Optional["ServiceOrder"]:
        if user_id is None:
            return ServiceOrderService.get_service_order(
                db=db,
                service_order_id=service_order_id,
                with_relations=with_relations,
            )
        return ServiceOrderRepository.get_by_id_and_user(
            db=db,
            service_order_id=service_order_id,
            user_id=user_id,
            with_relations=with_relations,
        )

    @staticmethod
    def get_service_order_by_number(db: Session, number: str) -> Optional["ServiceOrder"]:
        """Busca ordem de serviço por número (OS2025001, etc)."""
        return ServiceOrderRepository.get_by_number(db=db, number=number)

    @staticmethod
    def _sync_items(db: Session, service_order_id: UUID, items_data: List[dict]) -> None:
        existing_items = {
            item.id: item
            for item in ServiceOrderItemRepository.list_by_service_order(db, service_order_id)
        }
        incoming_ids = set()

        for item_data in items_data:
            item_data = ServiceOrderService._with_calculated_line_total(item_data)
            item_id = item_data.pop('id', None)
            item_data['service_order_id'] = service_order_id

            if item_id and item_id in existing_items:
                incoming_ids.add(item_id)
                ServiceOrderItemRepository.update(db, existing_items[item_id], item_data)
            else:
                ServiceOrderItemRepository.create(db, item_data)

        for item_id, item in existing_items.items():
            if item_id not in incoming_ids:
                ServiceOrderItemRepository.delete(db, item)

    @staticmethod
    def _sync_products(db: Session, service_order_id: UUID, products_data: List[dict]) -> None:
        existing_products = {
            product.id: product
            for product in ServiceOrderProductRepository.list_by_service_order(db, service_order_id)
        }
        incoming_ids = set()

        for product_data in products_data:
            product_data = ServiceOrderService._with_calculated_line_total(product_data)
            product_id = product_data.pop('id', None)
            product_data['service_order_id'] = service_order_id

            if product_id and product_id in existing_products:
                incoming_ids.add(product_id)
                ServiceOrderProductRepository.update(db, existing_products[product_id], product_data)
            else:
                ServiceOrderProductRepository.create(db, product_data)

        for product_id, product in existing_products.items():
            if product_id not in incoming_ids:
                ServiceOrderProductRepository.delete(db, product)

    @staticmethod
    def _sync_installments(db: Session, service_order_id: UUID, installments_data: List[dict]) -> None:
        existing_installments = {
            installment.id: installment
            for installment in ServiceOrderInstallmentRepository.list_by_service_order(db, service_order_id)
        }
        incoming_ids = set()

        for installment_data in installments_data:
            installment_data = dict(installment_data)
            installment_id = installment_data.pop('id', None)
            installment_data['service_order_id'] = service_order_id
            installment_data['status'] = installment_data.get('status') or ('paid' if installment_data.get('paid') else 'pending')

            if installment_id and installment_id in existing_installments:
                incoming_ids.add(installment_id)
                ServiceOrderInstallmentRepository.update(db, existing_installments[installment_id], installment_data)
            else:
                ServiceOrderInstallmentRepository.create(db, installment_data)

        for installment_id, installment in existing_installments.items():
            if installment_id not in incoming_ids:
                ServiceOrderInstallmentRepository.delete(db, installment)

    @staticmethod
    def _sync_equipments(db: Session, service_order_id: UUID, equipments_data: List[dict]) -> None:
        existing_equipments = {
            equipment.id: equipment
            for equipment in ServiceOrderEquipmentRepository.list_by_service_order(db, service_order_id)
        }
        incoming_ids = set()

        for equipment_data in equipments_data:
            equipment_data = dict(equipment_data)
            equipment_id = equipment_data.pop('id', None)
            equipment_data['service_order_id'] = service_order_id

            if equipment_id and equipment_id in existing_equipments:
                incoming_ids.add(equipment_id)
                ServiceOrderEquipmentRepository.update(db, existing_equipments[equipment_id], equipment_data)
            else:
                ServiceOrderEquipmentRepository.create(db, equipment_data)

        for equipment_id, equipment in existing_equipments.items():
            if equipment_id not in incoming_ids:
                ServiceOrderEquipmentRepository.delete(db, equipment)

    @staticmethod
    def update_service_order(
        db: Session,
        service_order_id: UUID,
        update_data: dict
    ) -> "ServiceOrder":
        """
        Atualiza ordem de serviço.
        
        Validações:
        - Ordem deve existir
        - Status e priority devem ser válidos
        """
        # Busca ordem
        service_order = ServiceOrderRepository.get_by_id(db=db, service_order_id=service_order_id)
        if not service_order:
            raise NotFoundError(f"Ordem de serviço {service_order_id} não encontrada")

        items_data = update_data.pop('items', None)
        products_data = update_data.pop('products', None)
        installments_data = update_data.pop('installments', None)
        equipments_data = update_data.pop('equipments', None)
        update_data.pop('attachments', None)
        update_data.pop('total_amount', None)
        has_financial_update = any(
            field in update_data
            for field in ('service_amount', 'parts_amount', 'discount_amount')
        )

        ServiceOrderService._normalize_service_order_data(update_data)
        if service_order.payment_status in ('paid', 'pago', 'PAID'):
            raise ValidationError("Não é permitido editar OS paga")

        if update_data.get('payment_status'):
            update_data['payment_status'] = ServiceOrderService._normalize_payment_status(update_data.get('payment_status'))
        if 'status' in update_data and update_data['status'] != service_order.status:
            allowed_targets = ServiceOrderService.STATUS_TRANSITIONS.get(service_order.status, [])
            if update_data['status'] not in allowed_targets:
                raise ValidationError(
                    f"Transição de status inválida: {service_order.status} -> {update_data['status']}"
                )
            if update_data['status'] == 'em_execucao' and not service_order.start_date:
                update_data['start_date'] = datetime.utcnow()
            if update_data['status'] == 'finalizada' and not service_order.completion_date:
                update_data['completion_date'] = datetime.utcnow()
                update_data['completed_date'] = date.today()
        ServiceOrderService._validate_professional_rules(db, update_data, service_order)

        if update_data:
            service_order = ServiceOrderRepository.update(db=db, service_order=service_order, update_data=update_data)

        if items_data is not None:
            ServiceOrderService._sync_items(db, service_order.id, items_data)

        if products_data is not None:
            ServiceOrderService._sync_products(db, service_order.id, products_data)

        if installments_data is not None:
            ServiceOrderService._sync_installments(db, service_order.id, installments_data)

        if equipments_data is not None:
            ServiceOrderService._sync_equipments(db, service_order.id, equipments_data)

        if items_data is not None or products_data is not None or has_financial_update:
            ServiceOrderService._set_related_totals(
                db,
                service_order,
                force_items=items_data is not None,
                force_products=products_data is not None,
            )

        ServiceOrderService._sync_enterprise_totals(service_order)
        if not service_order.code:
            service_order.code = service_order.number
        db.commit()
        db.refresh(service_order)
        ServiceOrderService._sync_financial_entry(db, service_order)

        db.refresh(service_order)
        return service_order

    @staticmethod
    def delete_service_order(db: Session, service_order_id: UUID) -> None:
        """
        Soft delete de ordem de serviço.
        
        Remove também todos os registros relacionados (cascade).
        """
        service_order = ServiceOrderRepository.get_by_id(db=db, service_order_id=service_order_id)
        if not service_order:
            raise NotFoundError(f"Ordem de serviço {service_order_id} não encontrada")

        financial_entry = (
            db.query(FinancialEntry)
            .filter(
                FinancialEntry.service_order_id == service_order.id,
                FinancialEntry.deleted_at.is_(None),
            )
            .first()
        )
        if financial_entry and financial_entry.status == 'paid':
            raise ConflictError("Não é permitido excluir OS com financeiro pago")

        if financial_entry and financial_entry.status == 'pending':
            financial_entry.status = 'canceled'
            financial_entry.updated_at = datetime.utcnow()
            db.commit()

        ServiceOrderRepository.soft_delete(db=db, service_order=service_order)

    @staticmethod
    def get_statistics(db: Session) -> Dict:
        """
        Retorna estatísticas para dashboard.
        
        Returns:
            Dict com: total, pendente, em_execucao, finalizada_mes
        """
        return ServiceOrderRepository.get_statistics(db=db)

    @staticmethod
    def change_status(
        db: Session,
        service_order_id: UUID,
        new_status: str
    ) -> "ServiceOrder":
        """
        Altera status da ordem de serviço com validações de transição.
        
        Regras:
        - pendente -> em_execucao: define start_date
        - em_execucao -> finalizada: define completion_date
        - finalizada -> não permite mudança (exceto admin)
        """
        service_order = ServiceOrderRepository.get_by_id(db=db, service_order_id=service_order_id)
        if not service_order:
            raise NotFoundError(f"Ordem de serviço {service_order_id} não encontrada")

        if new_status not in ServiceOrderService.VALID_STATUSES:
            raise ValidationError(f"Status inválido. Deve ser: {', '.join(ServiceOrderService.VALID_STATUSES)}")

        current_status = service_order.status
        if new_status == current_status:
            return service_order

        allowed_targets = ServiceOrderService.STATUS_TRANSITIONS.get(current_status, [])
        if new_status not in allowed_targets:
            raise ValidationError(
                f"Transição de status inválida: {current_status} -> {new_status}. "
                "Fluxo permitido: pendente -> em execução -> finalizada, ou cancelamento antes da finalização."
            )

        update_data = {'status': new_status}

        # Lógica específica por transição
        if new_status == 'em_execucao' and not service_order.start_date:
            update_data['start_date'] = datetime.utcnow()

        if new_status == 'finalizada' and not service_order.completion_date:
            update_data['completion_date'] = datetime.utcnow()
            update_data['completed_date'] = date.today()

        ServiceOrderService._validate_professional_rules(db, update_data, service_order)

        service_order = ServiceOrderRepository.update(db=db, service_order=service_order, update_data=update_data)
        ServiceOrderService._sync_financial_entry(db, service_order)
        return service_order

    @staticmethod
    def create_os_from_proposal(
        db: Session,
        proposal: "Proposal",
        items: List["ProposalItem"],
        products: List["ProposalProduct"],
        technician_id: Optional[UUID] = None,
        expected_completion_date: Optional[date] = None,
        observations: Optional[str] = None
    ) -> "ServiceOrder":
        """
        Cria uma Ordem de Serviço do tipo 'projeto' a partir de uma proposta aprovada.
        
        Regras de negócio:
        1. Proposta deve estar com status 'aprovada'  
        2. OS criada será do tipo 'projeto'
        3. exibir_valores = False (não mostra valores no relatório operacional)
        4. Copia dados da proposta: cliente, título, descrição, valores
        5. Vincula OS com proposta_id
        6. Copia itens e produtos da proposta
        
        Args:
            proposal: Instância da Proposal aprovada
            items: Lista de ProposalItem da proposta
            products: Lista de ProposalProduct da proposta
            technician_id: ID do técnico responsável (opcional)
            expected_completion_date: Data prevista de conclusão (opcional)
            observations: Observações adicionais (opcional)
        
        Returns:
            ServiceOrder criada
        
        Raises:
            ValidationError: Se proposta não está aprovada
        """
        from app.models.proposal import Proposal, ProposalItem, ProposalProduct
        from app.models.user import User
        
        # Validação: proposta deve estar aprovada
        if proposal.status != 'aprovada':
            raise ValidationError(
                f"Proposta {proposal.number} não está aprovada. "
                f"Status atual: {proposal.status}"
            )
        
        # Buscar técnico se technician_id fornecido
        technician = None
        if technician_id:
            tech_user = db.query(User).filter_by(id=technician_id).first()
            if tech_user:
                technician = tech_user.name
        
        warranty_days = 0
        if proposal.warranty_days and str(proposal.warranty_days).isdigit():
            warranty_days = int(proposal.warranty_days)

        # Montar dados da OS operacional vinculada à proposta aprovada
        service_order_data = {
            'proposal_id': proposal.id,
            'customer_id': proposal.customer_id,
            'user_id': proposal.user_id,
            'order_type': 'operacional',
            'service_type': 'projeto',
            'title': f"Execução: {proposal.title}",
            'description': proposal.description or '',
            'status': 'pendente',
            'priority': 'normal',
            'technician': technician,
            'expected_date': expected_completion_date,
            'notes': observations or f"OS gerada automaticamente da proposta {proposal.number}",
            'service_amount': proposal.service_amount or 0,
            'parts_amount': proposal.parts_amount or 0,
            'discount_amount': proposal.discount_amount or 0,
            'total_amount': proposal.total_amount or 0,
            'warranty_days': warranty_days,
        }
        
        # Converter itens da proposta para formato da OS
        items_data = [
            {
                'description': item.description,
                'service_type': item.service_type,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'total_price': item.total_price,
            }
            for item in items
        ]
        
        # Converter produtos da proposta para formato da OS
        products_data = [
            {
                'product_id': product.product_id,
                'description': product.description,
                'quantity': product.quantity,
                'unit_price': product.unit_price,
                'total_price': product.total_price,
            }
            for product in products
        ]
        
        # Adicionar itens e produtos ao service_order_data
        service_order_data['items'] = items_data
        service_order_data['products'] = products_data
        
        # Criar OS usando o método padrão (que já aplica validações)
        service_order = ServiceOrderService.create_service_order(
            db=db,
            service_order_data=service_order_data
        )
        
        return service_order


# ==================== Service para Itens ====================

class ServiceOrderItemService:
    """Service para itens de serviço."""

    @staticmethod
    def add_item(db: Session, service_order_id: UUID, item_data: dict) -> "ServiceOrderItem":
        """Adiciona item de serviço."""
        # Verifica se ordem existe
        service_order = ServiceOrderRepository.get_by_id(db=db, service_order_id=service_order_id)
        if not service_order:
            raise NotFoundError(f"Ordem de serviço {service_order_id} não encontrada")

        item_data = ServiceOrderService._with_calculated_line_total(item_data)
        item_data['service_order_id'] = service_order_id
        return ServiceOrderItemRepository.create(db=db, item_data=item_data)

    @staticmethod
    def list_items(db: Session, service_order_id: UUID) -> List["ServiceOrderItem"]:
        """Lista itens de uma ordem."""
        return ServiceOrderItemRepository.list_by_service_order(db=db, service_order_id=service_order_id)


# ==================== Service para Produtos ====================

class ServiceOrderProductService:
    """Service para produtos utilizados."""

    @staticmethod
    def add_product(db: Session, service_order_id: UUID, product_data: dict) -> "ServiceOrderProduct":
        """Adiciona produto utilizado."""
        service_order = ServiceOrderRepository.get_by_id(db=db, service_order_id=service_order_id)
        if not service_order:
            raise NotFoundError(f"Ordem de serviço {service_order_id} não encontrada")

        product_data = ServiceOrderService._with_calculated_line_total(product_data)
        product_data['service_order_id'] = service_order_id
        return ServiceOrderProductRepository.create(db=db, product_data=product_data)

    @staticmethod
    def list_products(db: Session, service_order_id: UUID) -> List["ServiceOrderProduct"]:
        """Lista produtos de uma ordem."""
        return ServiceOrderProductRepository.list_by_service_order(db=db, service_order_id=service_order_id)


# ==================== Service para Parcelas ====================

class ServiceOrderInstallmentService:
    """Service para parcelas."""

    @staticmethod
    def add_installment(db: Session, service_order_id: UUID, installment_data: dict) -> "ServiceOrderInstallment":
        """Adiciona parcela."""
        service_order = ServiceOrderRepository.get_by_id(db=db, service_order_id=service_order_id)
        if not service_order:
            raise NotFoundError(f"Ordem de serviço {service_order_id} não encontrada")

        installment_data['service_order_id'] = service_order_id
        installment_data['status'] = installment_data.get('status') or ('paid' if installment_data.get('paid') else 'pending')
        return ServiceOrderInstallmentRepository.create(db=db, installment_data=installment_data)

    @staticmethod
    def list_installments(db: Session, service_order_id: UUID) -> List["ServiceOrderInstallment"]:
        """Lista parcelas de uma ordem."""
        return ServiceOrderInstallmentRepository.list_by_service_order(db=db, service_order_id=service_order_id)

    @staticmethod
    def update_installment(db: Session, installment_id: UUID, update_data: dict) -> "ServiceOrderInstallment":
        """Atualiza parcela."""
        installment = ServiceOrderInstallmentRepository.get_by_id(db=db, installment_id=installment_id)
        if not installment:
            raise NotFoundError(f"Parcela {installment_id} não encontrada")
        return ServiceOrderInstallmentRepository.update(db=db, installment=installment, update_data=update_data)

    @staticmethod
    def delete_installment(db: Session, installment_id: UUID) -> None:
        """Remove parcela."""
        installment = ServiceOrderInstallmentRepository.get_by_id(db=db, installment_id=installment_id)
        if not installment:
            raise NotFoundError(f"Parcela {installment_id} não encontrada")
        ServiceOrderInstallmentRepository.delete(db=db, installment=installment)

    @staticmethod
    def mark_paid(db: Session, installment_id: UUID, payment_date: Optional[str] = None) -> "ServiceOrderInstallment":
        """Marca parcela como paga."""
        installment = db.query(ServiceOrderInstallment).filter_by(id=installment_id).first()
        if not installment:
            raise NotFoundError(f"Parcela {installment_id} não encontrada")

        update_data = {
            'paid': True,
            'payment_date': payment_date or datetime.utcnow().date()
        }
        return ServiceOrderInstallmentRepository.update(db=db, installment=installment, update_data=update_data)


# ==================== Service para Anexos ====================

class ServiceOrderAttachmentService:
    """Service para anexos."""

    @staticmethod
    def add_attachment(db: Session, service_order_id: UUID, attachment_data: dict) -> "ServiceOrderAttachment":
        """Adiciona anexo."""
        service_order = ServiceOrderRepository.get_by_id(db=db, service_order_id=service_order_id)
        if not service_order:
            raise NotFoundError(f"Ordem de serviço {service_order_id} não encontrada")

        attachment_data['service_order_id'] = service_order_id
        return ServiceOrderAttachmentRepository.create(db=db, attachment_data=attachment_data)

    @staticmethod
    def list_attachments(db: Session, service_order_id: UUID) -> List["ServiceOrderAttachment"]:
        """Lista anexos de uma ordem."""
        return ServiceOrderAttachmentRepository.list_by_service_order(db=db, service_order_id=service_order_id)

    @staticmethod
    def delete_attachment(db: Session, attachment_id: UUID) -> None:
        """Remove anexo."""
        attachment = ServiceOrderAttachmentRepository.get_by_id(db=db, attachment_id=attachment_id)
        if not attachment:
            raise NotFoundError(f"Anexo {attachment_id} não encontrado")

        ServiceOrderAttachmentRepository.delete(db=db, attachment=attachment)
