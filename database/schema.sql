CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- MERCHANTS

CREATE TABLE merchants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(150) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PRODUCTS

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,

    name VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL,
    brand VARCHAR(100),

    description TEXT,

    price NUMERIC(12,2) NOT NULL CHECK (price >= 0),

    specifications JSONB DEFAULT '{}'::jsonb,

    use_cases TEXT[] DEFAULT '{}',

    active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- INVENTORY

CREATE TABLE inventory (
    product_id INTEGER PRIMARY KEY
        REFERENCES products(id) ON DELETE CASCADE,

    stock_quantity INTEGER NOT NULL DEFAULT 0
        CHECK (stock_quantity >= 0),

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PRODUCT RELATIONSHIPS

CREATE TABLE product_relationships (
    id SERIAL PRIMARY KEY,

    product_id INTEGER NOT NULL
        REFERENCES products(id) ON DELETE CASCADE,

    related_product_id INTEGER NOT NULL
        REFERENCES products(id) ON DELETE CASCADE,

    relationship_type VARCHAR(50) NOT NULL,

    confidence NUMERIC(5,4)
        CHECK (confidence >= 0 AND confidence <= 1),

    UNIQUE(product_id, related_product_id, relationship_type)
);

-- BUYERS

CREATE TABLE buyers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name VARCHAR(150) NOT NULL,

    preferences JSONB DEFAULT '{}'::jsonb,

    spending_limit NUMERIC(12,2)
        CHECK (spending_limit >= 0),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ORDERS

CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    buyer_id UUID REFERENCES buyers(id),

    merchant_id UUID NOT NULL
        REFERENCES merchants(id),

    razorpay_order_id VARCHAR(100) UNIQUE,

    total_amount NUMERIC(12,2) NOT NULL
        CHECK (total_amount >= 0),

    currency VARCHAR(10) DEFAULT 'INR',

    status VARCHAR(30) NOT NULL DEFAULT 'created',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ORDER ITEMS

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,

    order_id UUID NOT NULL
        REFERENCES orders(id) ON DELETE CASCADE,

    product_id INTEGER NOT NULL
        REFERENCES products(id),

    quantity INTEGER NOT NULL
        CHECK (quantity > 0),

    unit_price NUMERIC(12,2) NOT NULL
        CHECK (unit_price >= 0)
);

-- PAYMENTS

CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    order_id UUID NOT NULL
        REFERENCES orders(id) ON DELETE CASCADE,

    razorpay_payment_id VARCHAR(100) UNIQUE,

    status VARCHAR(30) NOT NULL,

    method VARCHAR(50),

    amount NUMERIC(12,2),

    failure_reason TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AGENT SESSIONS

CREATE TABLE agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    buyer_id UUID REFERENCES buyers(id),

    merchant_id UUID REFERENCES merchants(id),

    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    ended_at TIMESTAMP
);

-- AGENT ACTIONS

CREATE TABLE agent_actions (
    id BIGSERIAL PRIMARY KEY,

    session_id UUID NOT NULL
        REFERENCES agent_sessions(id) ON DELETE CASCADE,

    agent_type VARCHAR(50) NOT NULL,

    action VARCHAR(100) NOT NULL,

    arguments JSONB DEFAULT '{}'::jsonb,

    result JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AUDIT LOG

CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,

    session_id UUID
        REFERENCES agent_sessions(id),

    action VARCHAR(100) NOT NULL,

    reason TEXT,

    amount NUMERIC(12,2),

    authorization_status VARCHAR(50),

    policy_result VARCHAR(50),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- MERCHANT POLICIES

CREATE TABLE merchant_policies (
    id SERIAL PRIMARY KEY,

    merchant_id UUID NOT NULL
        REFERENCES merchants(id) ON DELETE CASCADE,

    max_transaction_amount NUMERIC(12,2),

    max_discount_percent NUMERIC(5,2),

    max_retry_attempts INTEGER DEFAULT 1,

    allow_upsell BOOLEAN DEFAULT TRUE,

    require_confirmation_above NUMERIC(12,2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- INDEXES

CREATE INDEX idx_products_merchant
ON products(merchant_id);

CREATE INDEX idx_products_category
ON products(category);

CREATE INDEX idx_products_price
ON products(price);

CREATE INDEX idx_products_active
ON products(active);

CREATE INDEX idx_orders_buyer
ON orders(buyer_id);

CREATE INDEX idx_orders_merchant
ON orders(merchant_id);

CREATE INDEX idx_agent_actions_session
ON agent_actions(session_id);

CREATE INDEX idx_audit_logs_session
ON audit_logs(session_id);