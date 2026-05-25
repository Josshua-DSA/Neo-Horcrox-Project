-- ============================================================
-- init.sql — PostgreSQL init script for Neo-Horcrox database
-- Mounted to /docker-entrypoint-initdb.d/ in container
-- ============================================================

-- ─── orders ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
    id              BIGSERIAL PRIMARY KEY,
    order_id        INTEGER NOT NULL UNIQUE,
    order_date      TIMESTAMP,
    shipping_date   TIMESTAMP,

    -- Customer
    customer_id         INTEGER NOT NULL,
    customer_segment    VARCHAR(50),
    customer_city       VARCHAR(100),
    customer_state      VARCHAR(100),
    customer_country    VARCHAR(100),

    -- Shipping
    shipping_mode               VARCHAR(50),
    days_for_shipping_real      INTEGER,
    days_for_shipment_scheduled INTEGER,
    delivery_status             VARCHAR(50),
    late_delivery_risk          INTEGER,      -- 0 or 1

    -- Geography
    market          VARCHAR(50),
    order_region    VARCHAR(100),
    order_country   VARCHAR(100),
    order_city      VARCHAR(100),
    order_state     VARCHAR(100),

    -- Financials
    sales_per_customer      DOUBLE PRECISION,
    benefit_per_order       DOUBLE PRECISION,
    order_profit_per_order  DOUBLE PRECISION,
    order_status            VARCHAR(50),
    type                    VARCHAR(50),

    -- Product
    product_card_id     INTEGER,
    product_name        VARCHAR(255),
    product_price       DOUBLE PRECISION,
    product_status      INTEGER,
    category_id         INTEGER,
    category_name       VARCHAR(100),
    department_id       INTEGER,
    department_name     VARCHAR(100),

    -- Store geo
    latitude    DOUBLE PRECISION,
    longitude   DOUBLE PRECISION,

    -- Engineered features
    actual_delay            DOUBLE PRECISION,
    shipping_speed_ratio    DOUBLE PRECISION,
    has_price_inconsistency INTEGER,
    country_mismatch        INTEGER,
    state_mismatch          INTEGER,
    city_mismatch           INTEGER
);

CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders (order_date);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders (customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_late_delivery_risk ON orders (late_delivery_risk);
CREATE INDEX IF NOT EXISTS idx_orders_market ON orders (market);


-- ─── order_items ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS order_items (
    id                      BIGSERIAL PRIMARY KEY,
    order_item_id           INTEGER NOT NULL UNIQUE,
    order_id                INTEGER NOT NULL,
    product_card_id         INTEGER,
    order_item_cardprod_id  INTEGER,
    order_item_quantity     INTEGER,
    order_item_product_price DOUBLE PRECISION,
    order_item_discount     DOUBLE PRECISION,
    order_item_discount_rate DOUBLE PRECISION,
    order_item_profit_ratio DOUBLE PRECISION,
    sales                   DOUBLE PRECISION,
    order_item_total        DOUBLE PRECISION,

    -- Engineered
    calculated_item_total   DOUBLE PRECISION,
    item_total_gap          DOUBLE PRECISION,
    abs_item_total_gap      DOUBLE PRECISION
);

CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items (order_id);


-- ─── predictions ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS predictions (
    id                  BIGSERIAL PRIMARY KEY,
    order_id            INTEGER,
    prediction          INTEGER NOT NULL,
    probability_late    DOUBLE PRECISION NOT NULL,
    probability_on_time DOUBLE PRECISION NOT NULL,
    label               VARCHAR(50) NOT NULL,
    model_version       VARCHAR(20) NOT NULL,
    input_snapshot      JSONB NOT NULL,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_predictions_order_id ON predictions (order_id);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions (created_at);
CREATE INDEX IF NOT EXISTS idx_predictions_prediction ON predictions (prediction);


-- ─── forecast_logs ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS forecast_logs (
    id              BIGSERIAL PRIMARY KEY,
    category_name   VARCHAR(100) NOT NULL,
    market          VARCHAR(50) NOT NULL,
    periods         INTEGER NOT NULL,
    forecast_result JSONB NOT NULL,
    model_version   VARCHAR(20) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_forecast_logs_created_at ON forecast_logs (created_at);
CREATE INDEX IF NOT EXISTS idx_forecast_logs_category_name ON forecast_logs (category_name);
