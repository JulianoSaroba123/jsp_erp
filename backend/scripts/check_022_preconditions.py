#!/usr/bin/env python3
"""Diagnostico de pre-condicoes para a migration 022 (somente leitura).

Verifica:
1) Duplicidade de core.service_orders.code (nao nulo)
2) Duplicidade de core.financial_entries.service_order_id ativo (deleted_at IS NULL)
3) Valores invalidos em core.audit_logs.entity_type e core.audit_logs.resource_type
4) Existencia das tabelas exigidas

Resultado final:
- PASS (exit code 0): sem problemas
- FAIL (exit code 1): com problemas de pre-condicao
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

from sqlalchemy import text

# Garante import de `app.*` quando executado via `python scripts/...`.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.database import SessionLocal


ALLOWED_AUDIT_TYPES = ("order", "financial_entry", "user", "service_order")
REQUIRED_TABLES = ("service_orders", "financial_entries", "audit_logs")


def print_section(title: str) -> None:
    print(f"\n=== {title} ===")


def table_exists(db: Any, table_name: str) -> bool:
    query = text(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'core'
              AND table_name = :table_name
        )
        """
    )
    return bool(db.execute(query, {"table_name": table_name}).scalar())


def column_exists(db: Any, table_name: str, column_name: str) -> bool:
    query = text(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'core'
              AND table_name = :table_name
              AND column_name = :column_name
        )
        """
    )
    params = {"table_name": table_name, "column_name": column_name}
    return bool(db.execute(query, params).scalar())


def check_duplicate_service_order_codes(db: Any) -> list[tuple[str, int]]:
    query = text(
        """
        SELECT code, COUNT(*) AS occurrences
        FROM core.service_orders
        WHERE code IS NOT NULL
        GROUP BY code
        HAVING COUNT(*) > 1
        ORDER BY occurrences DESC, code
        """
    )
    rows = db.execute(query).fetchall()
    return [(row[0], int(row[1])) for row in rows]


def check_duplicate_active_financial_service_order_ids(db: Any) -> list[tuple[str, int]]:
    query = text(
        """
        SELECT service_order_id::text AS service_order_id, COUNT(*) AS occurrences
        FROM core.financial_entries
        WHERE service_order_id IS NOT NULL
          AND deleted_at IS NULL
        GROUP BY service_order_id
        HAVING COUNT(*) > 1
        ORDER BY occurrences DESC, service_order_id::text
        """
    )
    rows = db.execute(query).fetchall()
    return [(row[0], int(row[1])) for row in rows]


def check_invalid_audit_values(db: Any, column_name: str) -> list[tuple[str, int]]:
    query = text(
        f"""
        SELECT {column_name}::text AS invalid_value, COUNT(*) AS occurrences
        FROM core.audit_logs
        WHERE {column_name} IS NOT NULL
          AND {column_name} NOT IN ('order', 'financial_entry', 'user', 'service_order')
        GROUP BY {column_name}
        ORDER BY occurrences DESC, {column_name}::text
        """
    )
    rows = db.execute(query).fetchall()
    return [(row[0], int(row[1])) for row in rows]


def main() -> int:
    print("CHECK 022 PRECONDITIONS (READ ONLY)")
    print(f"Allowed audit types: {', '.join(ALLOWED_AUDIT_TYPES)}")

    has_problems = False
    has_fatal_structure_issue = False

    with SessionLocal() as db:
        db.execute(text("SET TRANSACTION READ ONLY"))

        print_section("1) Existencia de tabelas obrigatorias")
        missing_tables: list[str] = []
        for table_name in REQUIRED_TABLES:
            exists = table_exists(db, table_name)
            status = "OK" if exists else "MISSING"
            print(f"- core.{table_name}: {status}")
            if not exists:
                missing_tables.append(table_name)

        if missing_tables:
            has_problems = True
            has_fatal_structure_issue = True
            print("\nProblema: tabelas obrigatorias ausentes para o diagnostico completo.")

        print_section("2) Duplicidade de service_orders.code (nao nulo)")
        duplicated_codes: list[tuple[str, int]] = []
        if "service_orders" in missing_tables:
            print("- Nao avaliado: tabela core.service_orders ausente.")
        else:
            duplicated_codes = check_duplicate_service_order_codes(db)
            if duplicated_codes:
                has_problems = True
                for code, occurrences in duplicated_codes:
                    print(f"- code={code} | ocorrencias={occurrences}")
            else:
                print("- Nenhuma duplicidade encontrada.")

        print_section("3) Duplicidade de financial_entries.service_order_id ativo")
        duplicated_financial_links: list[tuple[str, int]] = []
        if "financial_entries" in missing_tables:
            print("- Nao avaliado: tabela core.financial_entries ausente.")
        else:
            if not column_exists(db, "financial_entries", "deleted_at"):
                has_problems = True
                has_fatal_structure_issue = True
                print("- Problema estrutural: coluna core.financial_entries.deleted_at ausente.")
            elif not column_exists(db, "financial_entries", "service_order_id"):
                has_problems = True
                has_fatal_structure_issue = True
                print("- Problema estrutural: coluna core.financial_entries.service_order_id ausente.")
            else:
                duplicated_financial_links = check_duplicate_active_financial_service_order_ids(db)
                if duplicated_financial_links:
                    has_problems = True
                    for service_order_id, occurrences in duplicated_financial_links:
                        print(f"- service_order_id={service_order_id} | ocorrencias={occurrences}")
                else:
                    print("- Nenhuma duplicidade ativa encontrada.")

        print_section("4) Valores invalidos em audit_logs")
        invalid_entity_types: list[tuple[str, int]] = []
        invalid_resource_types: list[tuple[str, int]] = []

        if "audit_logs" in missing_tables:
            print("- Nao avaliado: tabela core.audit_logs ausente.")
        else:
            has_entity_type = column_exists(db, "audit_logs", "entity_type")
            has_resource_type = column_exists(db, "audit_logs", "resource_type")

            print("entity_type:")
            if has_entity_type:
                invalid_entity_types = check_invalid_audit_values(db, "entity_type")
                if invalid_entity_types:
                    has_problems = True
                    for value, occurrences in invalid_entity_types:
                        print(f"- valor_invalido={value} | ocorrencias={occurrences}")
                else:
                    print("- Nenhum valor invalido encontrado.")
            else:
                print("- Coluna nao existe (nao aplicavel neste schema).")

            print("resource_type:")
            if has_resource_type:
                invalid_resource_types = check_invalid_audit_values(db, "resource_type")
                if invalid_resource_types:
                    has_problems = True
                    for value, occurrences in invalid_resource_types:
                        print(f"- valor_invalido={value} | ocorrencias={occurrences}")
                else:
                    print("- Nenhum valor invalido encontrado.")
            else:
                print("- Coluna nao existe (nao aplicavel neste schema).")

            if not has_entity_type and not has_resource_type:
                has_problems = True
                has_fatal_structure_issue = True
                print("- Problema estrutural: nenhuma coluna de tipo de auditoria encontrada.")

        print_section("5) Resultado final")
        if has_problems:
            print("FAIL - Pre-condicoes da migration 022 NAO atendidas.")
            if has_fatal_structure_issue:
                print("Motivo adicional: ha problemas estruturais que impedem validacao completa.")
            return 1

        print("PASS - Banco apto para aplicar a migration 022.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
