-- Manual SQL script to create Service Order tables
-- Run this directly via psql or Python to bypass Alembic transaction issue

BEGIN;

-- ==================== 1. SERVICE_ORDERS ====================
CREATE TABLE IF NOT EXISTS core.service_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    number VARCHAR(20) UNIQUE NOT NULL,
    customer_id UUID NOT NULL REFERENCES core.customers(id),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    requester VARCHAR(200),
    problem_description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pendente',
    priority VARCHAR(20) NOT NULL DEFAULT 'normal',
    opening_date DATE NOT NULL DEFAULT CURRENT_DATE,
    expected_date DATE,
    start_date TIMESTAMP,
    completion_date TIMESTAMP,
    technician VARCHAR(100),
    equipment VARCHAR(200),
    brand_model VARCHAR(200),
    serial_number VARCHAR(100),
    reported_defect TEXT,
    technical_diagnosis TEXT,
    solution TEXT,
    notes TEXT,
    start_time TIME,
    end_time TIME,
    total_hours VARCHAR(20),
    initial_km INTEGER,
    final_km INTEGER,
    total_km VARCHAR(20),
    service_amount NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    parts_amount NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    discount_amount NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    total_amount NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    warranty_days INTEGER DEFAULT 0,
    payment_condition VARCHAR(50) NOT NULL DEFAULT 'a_vista',
    installment_count INTEGER DEFAULT 1,
    down_payment NUMERIC(10, 2) DEFAULT 0.00,
    first_installment_date DATE,
    payment_due_date DATE,
    payment_description TEXT,
    payment_status VARCHAR(20) NOT NULL DEFAULT 'pendente',
    include_images_in_report BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP
);

-- ==================== 2. SERVICE_ORDER_ITEMS ====================
CREATE TABLE IF NOT EXISTS core.service_order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_order_id UUID NOT NULL REFERENCES core.service_orders(id) ON DELETE CASCADE,
    description VARCHAR(200) NOT NULL,
    service_type VARCHAR(20) NOT NULL DEFAULT 'hora',
    quantity NUMERIC(5, 2) NOT NULL DEFAULT 1.00,
    unit_price NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    total_price NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

-- ==================== 3. SERVICE_ORDER_PRODUCTS ====================
CREATE TABLE IF NOT EXISTS core.service_order_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_order_id UUID NOT NULL REFERENCES core.service_orders(id) ON DELETE CASCADE,
    product_id UUID REFERENCES core.products(id),
    description VARCHAR(200) NOT NULL,
    quantity NUMERIC(10, 3) NOT NULL DEFAULT 1.000,
    unit_price NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    total_price NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

-- ==================== 4. SERVICE_ORDER_INSTALLMENTS ====================
CREATE TABLE IF NOT EXISTS core.service_order_installments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_order_id UUID NOT NULL REFERENCES core.service_orders(id) ON DELETE CASCADE,
    installment_number INTEGER NOT NULL,
    due_date DATE NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    paid BOOLEAN NOT NULL DEFAULT FALSE,
    payment_date DATE,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

-- ==================== 5. SERVICE_ORDER_ATTACHMENTS ====================
CREATE TABLE IF NOT EXISTS core.service_order_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_order_id UUID NOT NULL REFERENCES core.service_orders(id) ON DELETE CASCADE,
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    mime_type VARCHAR(100),
    file_size INTEGER,
    file_path VARCHAR(500),
    file_content BYTEA,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

-- ==================== INDICES ====================
-- service_orders
CREATE INDEX IF NOT EXISTS ix_service_orders_number ON core.service_orders(number);
CREATE INDEX IF NOT EXISTS ix_service_orders_customer_id ON core.service_orders(customer_id);
CREATE INDEX IF NOT EXISTS ix_service_orders_status ON core.service_orders(status);
CREATE INDEX IF NOT EXISTS ix_service_orders_priority ON core.service_orders(priority);
CREATE INDEX IF NOT EXISTS ix_service_orders_deleted_at ON core.service_orders(deleted_at);
CREATE INDEX IF NOT EXISTS ix_service_orders_opening_date ON core.service_orders(opening_date);

-- service_order_items
CREATE INDEX IF NOT EXISTS ix_service_order_items_service_order_id ON core.service_order_items(service_order_id);

-- service_order_products
CREATE INDEX IF NOT EXISTS ix_service_order_products_service_order_id ON core.service_order_products(service_order_id);
CREATE INDEX IF NOT EXISTS ix_service_order_products_product_id ON core.service_order_products(product_id);

-- service_order_installments
CREATE INDEX IF NOT EXISTS ix_service_order_installments_service_order_id ON core.service_order_installments(service_order_id);
CREATE INDEX IF NOT EXISTS ix_service_order_installments_due_date ON core.service_order_installments(due_date);

-- service_order_attachments
CREATE INDEX IF NOT EXISTS ix_service_order_attachments_service_order_id ON core.service_order_attachments(service_order_id);

COMMIT;

-- Update Alembic version
UPDATE core.alembic_version SET version_num = '011_create_service_orders';

SELECT 'Service Order tables created successfully!' AS result;
