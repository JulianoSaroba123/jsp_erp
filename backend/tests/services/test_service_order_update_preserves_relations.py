from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.models.customer import Customer
from app.models.service_order import (
    ServiceOrderInstallment,
    ServiceOrderItem,
    ServiceOrderProduct,
)
from app.models.user import User
from app.services.service_order_service import ServiceOrderService


def _seed_user_and_customer(db_session):
    user = User(
        name="OS Tester",
        email=f"os-{uuid4()}@test.com",
        password_hash="not-used",
        role="admin",
        is_active=True,
    )
    customer = Customer(
        name="Cliente OS",
        person_type="PJ",
        status="active",
    )
    db_session.add_all([user, customer])
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(customer)
    return user, customer


def _create_service_order(db_session, with_product=False):
    user, customer = _seed_user_and_customer(db_session)
    payload = {
        "customer_id": customer.id,
        "user_id": user.id,
        "order_type": "comercial",
        "title": "OS original",
        "status": "pendente",
        "priority": "normal",
        "items": [
            {
                "description": "MANUTENCAO EM GERADORES",
                "service_type": "hora",
                "quantity": Decimal("3"),
                "unit_price": Decimal("180"),
            }
        ],
        "products": [],
        "installments": [],
    }
    if with_product:
        payload["products"] = [
            {
                "description": "Peca de teste",
                "quantity": Decimal("1"),
                "unit_price": Decimal("100"),
            }
        ]

    return ServiceOrderService.create_service_order(db_session, payload)


def test_editar_titulo_nao_apaga_servicos(db_session):
    service_order = _create_service_order(db_session)

    updated = ServiceOrderService.update_service_order(
        db_session,
        service_order.id,
        {"title": "OS editada"},
    )

    items = db_session.query(ServiceOrderItem).filter_by(service_order_id=service_order.id).all()
    assert updated.title == "OS editada"
    assert len(items) == 1
    assert items[0].description == "MANUTENCAO EM GERADORES"
    assert updated.total_amount == Decimal("540.00")


def test_editar_pagamento_nao_apaga_servicos_ou_produtos(db_session):
    service_order = _create_service_order(db_session, with_product=True)

    updated = ServiceOrderService.update_service_order(
        db_session,
        service_order.id,
        {
            "discount_amount": Decimal("40"),
            "installments": [
                {
                    "installment_number": 1,
                    "due_date": date.today(),
                    "amount": Decimal("600"),
                    "paid": False,
                }
            ],
        },
    )

    items = db_session.query(ServiceOrderItem).filter_by(service_order_id=service_order.id).all()
    products = db_session.query(ServiceOrderProduct).filter_by(service_order_id=service_order.id).all()
    installments = db_session.query(ServiceOrderInstallment).filter_by(service_order_id=service_order.id).all()
    assert len(items) == 1
    assert len(products) == 1
    assert len(installments) == 1
    assert updated.service_amount == Decimal("540.00")
    assert updated.parts_amount == Decimal("100.00")
    assert updated.total_amount == Decimal("600.00")


def test_editar_servicos_recalcula_total_corretamente(db_session):
    service_order = _create_service_order(db_session)
    item = db_session.query(ServiceOrderItem).filter_by(service_order_id=service_order.id).one()

    updated = ServiceOrderService.update_service_order(
        db_session,
        service_order.id,
        {
            "items": [
                {
                    "id": item.id,
                    "description": "MANUTENCAO EM GERADORES",
                    "service_type": "hora",
                    "quantity": Decimal("4"),
                    "unit_price": Decimal("180"),
                }
            ]
        },
    )

    items = db_session.query(ServiceOrderItem).filter_by(service_order_id=service_order.id).all()
    assert len(items) == 1
    assert items[0].quantity == Decimal("4.00")
    assert items[0].total_price == Decimal("720.00")
    assert updated.service_amount == Decimal("720.00")
    assert updated.total_amount == Decimal("720.00")


def test_update_parcial_nao_zera_valor_total(db_session):
    service_order = _create_service_order(db_session)

    updated = ServiceOrderService.update_service_order(
        db_session,
        service_order.id,
        {
            "notes": "Observacao alterada",
            "total_amount": Decimal("0"),
        },
    )

    assert updated.notes == "Observacao alterada"
    assert updated.total_amount == Decimal("540.00")


def test_update_nao_duplica_itens(db_session):
    service_order = _create_service_order(db_session)
    item = db_session.query(ServiceOrderItem).filter_by(service_order_id=service_order.id).one()
    item_payload = {
        "id": item.id,
        "description": "MANUTENCAO EM GERADORES",
        "service_type": "hora",
        "quantity": Decimal("3"),
        "unit_price": Decimal("180"),
    }

    ServiceOrderService.update_service_order(db_session, service_order.id, {"items": [item_payload]})
    ServiceOrderService.update_service_order(db_session, service_order.id, {"items": [item_payload]})

    items = db_session.query(ServiceOrderItem).filter_by(service_order_id=service_order.id).all()
    assert len(items) == 1
    assert items[0].total_price == Decimal("540.00")


def test_update_sem_service_items_mantem_itens_existentes(db_session):
    service_order = _create_service_order(db_session)

    ServiceOrderService.update_service_order(
        db_session,
        service_order.id,
        {"requester": "Solicitante atualizado"},
    )

    items = db_session.query(ServiceOrderItem).filter_by(service_order_id=service_order.id).all()
    assert len(items) == 1
    assert items[0].total_price == Decimal("540.00")
