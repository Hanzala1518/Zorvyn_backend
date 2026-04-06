-- Run this entire file in Supabase SQL Editor (Dashboard → SQL Editor → New Query → Paste → Run)

-- STEP 1: Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- STEP 2: Custom types
CREATE TYPE user_role AS ENUM ('viewer', 'analyst', 'admin');
CREATE TYPE user_status AS ENUM ('active', 'inactive');
CREATE TYPE transaction_type AS ENUM ('income', 'expense');

-- STEP 3: Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'viewer',
    status user_status NOT NULL DEFAULT 'active',
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- STEP 4: Categories table
CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) UNIQUE NOT NULL,
    color VARCHAR(7) DEFAULT '#6366f1',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- STEP 5: Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    type transaction_type NOT NULL,
    category VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    notes TEXT,
    description VARCHAR(200),
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- STEP 6: Audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action VARCHAR(100) NOT NULL,
    performed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    target_id VARCHAR(255),
    details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- STEP 7: Performance indexes
CREATE INDEX idx_transactions_type ON transactions(type) WHERE is_deleted = FALSE;
CREATE INDEX idx_transactions_date ON transactions(date) WHERE is_deleted = FALSE;
CREATE INDEX idx_transactions_category ON transactions(category) WHERE is_deleted = FALSE;
CREATE INDEX idx_transactions_created_by ON transactions(created_by);
CREATE INDEX idx_users_email ON users(email) WHERE is_deleted = FALSE;
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_performed_by ON audit_logs(performed_by);

-- STEP 8: Auto-update updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER transactions_updated_at
    BEFORE UPDATE ON transactions FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- STEP 9: Seed categories
INSERT INTO categories (name, color) VALUES
    ('Salary', '#10b981'), ('Freelance', '#6366f1'), ('Investment', '#f59e0b'),
    ('Food & Dining', '#ef4444'), ('Transport', '#3b82f6'), ('Housing', '#8b5cf6'),
    ('Healthcare', '#ec4899'), ('Entertainment', '#f97316'), ('Shopping', '#14b8a6'),
    ('Utilities', '#64748b'), ('Education', '#06b6d4'), ('Other', '#94a3b8')
ON CONFLICT (name) DO NOTHING;

-- STEP 10: Seed demo users
-- admin@demo.com / admin123
INSERT INTO users (email, full_name, password_hash, role, status) VALUES
    ('admin@demo.com', 'Admin User',
     '$2b$12$v8iN1NuLGqwQ5Pw08UEn3e3XyeF080mh4OVtUjTYTHdtC2zeaCL0C',
     'admin', 'active')
ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash;

-- analyst@demo.com / analyst123
INSERT INTO users (email, full_name, password_hash, role, status) VALUES
    ('analyst@demo.com', 'Analyst User',
     '$2b$12$E9M1ELw9R6an5swhFnSAa..XyjcSjEJZSCfWjyHdVmz/Uasba4xXy',
     'analyst', 'active')
ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash;

-- viewer@demo.com / viewer123
INSERT INTO users (email, full_name, password_hash, role, status) VALUES
    ('viewer@demo.com', 'Viewer User',
     '$2b$12$5cppF9z02evf4IwXrJkMee.viXRS51Le/iQkGThC/yLdGb1ejBLmu',
     'viewer', 'active')
ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash;

-- STEP 11: Seed sample transactions
DO $$
DECLARE admin_id UUID;
BEGIN
    SELECT id INTO admin_id FROM users WHERE email = 'admin@demo.com';
    INSERT INTO transactions (amount, type, category, date, notes, description, created_by) VALUES
        (85000.00, 'income',  'Salary',          CURRENT_DATE - 1,  'Monthly salary',    'Jan salary',        admin_id),
        (25000.00, 'income',  'Freelance',        CURRENT_DATE - 5,  'Web project',       'Client payment',    admin_id),
        (15000.00, 'income',  'Investment',       CURRENT_DATE - 10, 'SIP returns',       'Mutual fund',       admin_id),
        (12000.00, 'expense', 'Housing',          CURRENT_DATE - 2,  'Monthly rent',      'Apartment rent',    admin_id),
        (3500.00,  'expense', 'Food & Dining',    CURRENT_DATE - 3,  'Groceries',         'Monthly shopping',  admin_id),
        (2800.00,  'expense', 'Utilities',        CURRENT_DATE - 7,  'Electricity bill',  'MPEZ bill',         admin_id),
        (1200.00,  'expense', 'Transport',        CURRENT_DATE - 4,  'Fuel',              'Petrol',            admin_id),
        (5000.00,  'expense', 'Entertainment',    CURRENT_DATE - 6,  'Subscriptions',     'OTT + gaming',      admin_id),
        (92000.00, 'income',  'Salary',           CURRENT_DATE - 32, 'Monthly salary',    'Dec salary',        admin_id),
        (8000.00,  'expense', 'Shopping',         CURRENT_DATE - 15, 'Clothes',           'Winter wardrobe',   admin_id);
END $$;
