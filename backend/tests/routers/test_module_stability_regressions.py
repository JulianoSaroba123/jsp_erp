"""
Regression tests for module stability after schema reconciliation.
"""

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.user import User


def _truncate_domain_tables(db_session: Session) -> None:
    db_session.execute(text("TRUNCATE TABLE core.service_orders CASCADE"))
    db_session.execute(text("TRUNCATE TABLE core.products CASCADE"))
    db_session.execute(text("TRUNCATE TABLE core.suppliers CASCADE"))
    db_session.commit()


def test_products_service_orders_suppliers_return_empty_list_200(
    client: TestClient,
    db_session: Session,
    seed_user_admin: User,
    auth_headers_admin: dict,
):
    _truncate_domain_tables(db_session)

    client.headers.update(auth_headers_admin)

    products_resp = client.get("/products")
    assert products_resp.status_code == 200
    products_payload = products_resp.json()
    assert products_payload["items"] == []

    service_orders_resp = client.get("/service-orders")
    assert service_orders_resp.status_code == 200
    service_orders_payload = service_orders_resp.json()
    assert service_orders_payload["items"] == []

    suppliers_resp = client.get("/suppliers")
    assert suppliers_resp.status_code == 200
    suppliers_payload = suppliers_resp.json()
    assert suppliers_payload["items"] == []


def test_suppliers_duplicate_document_conflicts_only_on_real_duplicate(
    client: TestClient,
    db_session: Session,
    seed_user_admin: User,
    auth_headers_admin: dict,
):
    _truncate_domain_tables(db_session)

    client.headers.update(auth_headers_admin)

    first_payload = {
        "nome": "Fornecedor PF 1",
        "tipo": "PF",
        "cnpj_cpf": "12345678901",
    }
    first_resp = client.post("/suppliers", json=first_payload)
    assert first_resp.status_code == 201

    same_doc_payload = {
        "nome": "Fornecedor PF Duplicado",
        "tipo": "PF",
        "cnpj_cpf": "123.456.789-01",
    }
    duplicate_resp = client.post("/suppliers", json=same_doc_payload)
    assert duplicate_resp.status_code == 409

    different_doc_payload = {
        "nome": "Fornecedor PF 2",
        "tipo": "PF",
        "cnpj_cpf": "98765432100",
    }
    second_resp = client.post("/suppliers", json=different_doc_payload)
    assert second_resp.status_code == 201


def test_suppliers_stats_summary_returns_zeroes_on_empty_state(
    client: TestClient,
    db_session: Session,
    seed_user_admin: User,
    auth_headers_admin: dict,
):
    _truncate_domain_tables(db_session)

    client.headers.update(auth_headers_admin)

    response = client.get("/suppliers/stats/summary")
    assert response.status_code == 200

    payload = response.json()
    assert payload["total"] == 0
    assert payload["por_tipo"]["PF"] == 0
    assert payload["por_tipo"]["PJ"] == 0
    assert payload["por_categoria"] == []
