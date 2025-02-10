-- Credit Packages (available credit purchase options)
CREATE TABLE credit_packages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    credits INTEGER NOT NULL,
    price_cents INTEGER NOT NULL,
    tier VARCHAR(50) NOT NULL, -- 'basic', 'pro', 'enterprise'
    savings_percentage INTEGER, -- how much savings compared to basic tier
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Feature Costs (cost of different operations)
CREATE TABLE feature_costs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feature_key VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    credits_cost INTEGER NOT NULL,
    description TEXT,
    internal_cost_cents INTEGER, -- for tracking purposes
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Credit Transactions (all credit-related activities)
CREATE TABLE credit_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    amount INTEGER NOT NULL, -- positive for credits added, negative for credits used
    balance_after INTEGER NOT NULL,
    transaction_type VARCHAR(50) NOT NULL, -- 'purchase', 'usage', 'refund', 'bonus'
    feature_key VARCHAR(100) REFERENCES feature_costs(feature_key), -- NULL for non-usage transactions
    description TEXT,
    metadata JSONB, -- store additional info like package bought, etc.
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_balance_non_negative CHECK (balance_after >= 0)
);

-- Credit Balance (current credit status per user)
CREATE TABLE credit_balances (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    balance INTEGER NOT NULL DEFAULT 0,
    lifetime_credits INTEGER NOT NULL DEFAULT 0,
    tier VARCHAR(50) NOT NULL DEFAULT 'basic', -- user's current tier
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_balance_non_negative CHECK (balance >= 0)
);

-- Indexes
CREATE INDEX idx_credit_transactions_user_id ON credit_transactions(user_id);
CREATE INDEX idx_credit_transactions_created_at ON credit_transactions(created_at);
CREATE INDEX idx_credit_transactions_feature_key ON credit_transactions(feature_key);
