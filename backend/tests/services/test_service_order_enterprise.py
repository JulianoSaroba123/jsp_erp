from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.auth.security import create_access_token
from app.models.customer import Customer
from app.models.financial_entry import FinancialEntry
from app.models.user import User
from app.services.service_order_service import ServiceOrderService


def _seed_user_and_customer(db_session, role="user"):
    user = User(
        name="OS Enterprise",
        email=f"os-enterprise-{uuid4()}@test.com",
        password_hash="not-used",
        role=role,
        is_active=True,
    )
    customer = Customer(
        name="Cliente Enterprise",
        person_type="PJ",
        status="active",
    )
    db_session.add_all([user, customer])
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(customer)
    return user, customer


def _create_os(db_session, user_id, customer_id):
    payload = {
        "customer_id": customer_id,
        "user_id": user_id,
        "title": "OS enterprise",
        "order_type": "comercial",
        "status": "open",
        "priority": "medium",
        "items": [
            {
                "description": "Serviço técnico",
                "quantity": Decimal("2"),
                "unit_price": Decimal("150"),
            }
        ],
    }
    return ServiceOrderService.create_service_order(db_session, payload)


def test_create_service_order_creates_financial_entry(db_session):
    user, customer = _seed_user_and_customer(db_session)

    service_order = _create_os(db_session, user.id, customer.id)

    entry = (
        db_session.query(FinancialEntry)
        .filter(FinancialEntry.service_order_id == service_order.id)
        .first()
    )
    assert entry is not None
    assert entry.kind == "revenue"
    assert entry.status == "pending"
    assert entry.amount == Decimal("300.00")


def test_update_service_order_syncs_financial_amount(db_session):
    user, customer = _seed_user_and_customer(db_session)
    service_order = _create_os(db_session, user.id, customer.id)
    item = service_order.items[0]

    updated = ServiceOrderService.update_service_order(
        db_session,
        service_order.id,
        {
            "items": [
                {
                    "id": item.id,
                    "description": item.description,
                    "quantity": Decimal("3"),
                    "unit_price": Decimal("150"),
                }
            ]
        },
    )

    entry = (
        db_session.query(FinancialEntry)
        .filter(FinancialEntry.service_order_id == service_order.id)
        .first()
    )
    assert updated.total_amount == Decimal("450.00")
    assert entry.amount == Decimal("450.00")


def test_delete_service_order_blocks_when_financial_paid(db_session):
    user, customer = _seed_user_and_customer(db_session)
    service_order = _create_os(db_session, user.id, customer.id)

    entry = (
        db_session.query(FinancialEntry)
        .filter(FinancialEntry.service_order_id == service_order.id)
        .first()
    )
    entry.status = "paid"
    db_session.commit()

    try:
        ServiceOrderService.delete_service_order(db_session, service_order.id)
        assert False, "Deveria bloquear exclusão com financeiro pago"
    except Exception as exc:
        assert "pago" in str(exc).lower()


def test_service_order_anti_enumeration_and_print_endpoint(client, db_session, seed_user_normal, seed_user_other):
    # Cria customer e OS para o usuário normal
    customer = Customer(name="Cliente API", person_type="PJ", status="active")
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)

    client.headers.update({"Authorization": f"Bearer {create_access_token(subject=str(seed_user_normal.id))}"})
    payload = {
        "customer_id": str(customer.id),
        "title": "OS API",
        "status": "open",
        "priority": "medium",
        "items": [
            {"description": "Serviço", "quantity": 1, "unit_price": 100}
        ],
        "equipments": [
            {
                "equipment_name": "Compressor",
                "brand": "JSP",
                "model": "X1",
                "serial_number": "SN-123",
                "defect_reported": "Não liga",
            }
        ],
        "installments": [
            {
                "installment_number": 1,
                "due_date": str(date.today()),
                "amount": 100,
                "status": "pending",
            }
        ],
    }
    response = client.post("/service-orders", json=payload)
    assert response.status_code == 201
    so_id = response.json()["id"]

    # Usuário diferente deve receber 404 (anti-enumeration)
    client.headers.update({"Authorization": f"Bearer {create_access_token(subject=str(seed_user_other.id))}"})
    forbidden_resp = client.get(f"/service-orders/{so_id}")
    assert forbidden_resp.status_code == 404

    # Dono consegue imprimir HTML
    client.headers.update({"Authorization": f"Bearer {create_access_token(subject=str(seed_user_normal.id))}"})
    print_resp = client.get(f"/service-orders/{so_id}/print?version=summary")
    assert print_resp.status_code == 200
    assert "window.print()" in print_resp.text
    assert "JSP ERP" in print_resp.text
