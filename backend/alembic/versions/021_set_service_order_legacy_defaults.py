"""set service_order database defaults

Revision ID: 021_set_service_order_legacy_defaults
Revises: 020_reconcile_service_order_model_columns
Create Date: 2026-05-17
"""

from alembic import op


revision = "021_set_service_order_legacy_defaults"
down_revision = "020_reconcile_service_order_model_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'core'
                  AND table_name = 'service_orders'
                  AND column_name = 'tipo_ordem'
            ) THEN
                ALTER TABLE core.service_orders ALTER COLUMN tipo_ordem SET DEFAULT 'comercial';
                UPDATE core.service_orders SET tipo_ordem = 'comercial' WHERE tipo_ordem IS NULL;
                ALTER TABLE core.service_orders ALTER COLUMN tipo_ordem SET NOT NULL;
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'core'
                  AND table_name = 'service_orders'
                  AND column_name = 'exibir_valores'
            ) THEN
                ALTER TABLE core.service_orders ALTER COLUMN exibir_valores SET DEFAULT true;
                UPDATE core.service_orders SET exibir_valores = true WHERE exibir_valores IS NULL;
                ALTER TABLE core.service_orders ALTER COLUMN exibir_valores SET NOT NULL;
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'core'
                  AND table_name = 'service_orders'
                  AND column_name = 'percentual_concluido'
            ) THEN
                ALTER TABLE core.service_orders ALTER COLUMN percentual_concluido SET DEFAULT 0;
                UPDATE core.service_orders SET percentual_concluido = 0 WHERE percentual_concluido IS NULL;
                ALTER TABLE core.service_orders ALTER COLUMN percentual_concluido SET NOT NULL;
            END IF;

            ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS payment_condition VARCHAR(50);
            ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS installment_count INTEGER;
            ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS down_payment NUMERIC(10, 2);
            ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS first_installment_date DATE;
            ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS payment_due_date DATE;
            ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS payment_description TEXT;
            ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS payment_status VARCHAR(20);
            ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS include_images_in_report BOOLEAN;

            UPDATE core.service_orders
            SET payment_condition = 'a_vista'
            WHERE payment_condition IS NULL;

            UPDATE core.service_orders
            SET payment_status = 'pendente'
            WHERE payment_status IS NULL;

            UPDATE core.service_orders
            SET installment_count = 1
            WHERE installment_count IS NULL;

            UPDATE core.service_orders
            SET down_payment = 0
            WHERE down_payment IS NULL;

            UPDATE core.service_orders
            SET include_images_in_report = false
            WHERE include_images_in_report IS NULL;

            ALTER TABLE core.service_orders ALTER COLUMN payment_condition SET DEFAULT 'a_vista';
            ALTER TABLE core.service_orders ALTER COLUMN payment_condition SET NOT NULL;
            ALTER TABLE core.service_orders ALTER COLUMN payment_status SET DEFAULT 'pendente';
            ALTER TABLE core.service_orders ALTER COLUMN payment_status SET NOT NULL;
            ALTER TABLE core.service_orders ALTER COLUMN installment_count SET DEFAULT 1;
            ALTER TABLE core.service_orders ALTER COLUMN down_payment SET DEFAULT 0;
            ALTER TABLE core.service_orders ALTER COLUMN include_images_in_report SET DEFAULT false;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE core.service_orders ALTER COLUMN payment_condition DROP DEFAULT;
        ALTER TABLE core.service_orders ALTER COLUMN payment_status DROP DEFAULT;
        ALTER TABLE core.service_orders ALTER COLUMN installment_count DROP DEFAULT;
        ALTER TABLE core.service_orders ALTER COLUMN down_payment DROP DEFAULT;
        ALTER TABLE core.service_orders ALTER COLUMN include_images_in_report DROP DEFAULT;
        """
    )
