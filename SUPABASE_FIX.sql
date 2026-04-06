-- ============================================================
-- SUPABASE_FIX.sql
-- Run this ENTIRE script in Supabase SQL Editor.
-- It disables RLS, clears stale data, and re-seeds the tables.
-- Password hashes below are pre-generated (bcrypt, cost 12):
--   admin@demo.com    → admin123
--   analyst@demo.com  → analyst123
--   viewer@demo.com   → viewer123
-- ============================================================

-- 1. Disable Row Level Security on all tables
ALTER TABLE users        DISABLE ROW LEVEL SECURITY;
ALTER TABLE transactions DISABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs   DISABLE ROW LEVEL SECURITY;
ALTER TABLE categories   DISABLE ROW LEVEL SECURITY;

-- 2. Drop all existing data (order matters for FK constraints)
DELETE FROM audit_logs;
DELETE FROM transactions;
DELETE FROM users;
DELETE FROM categories;

-- 3. Seed categories (matches SUPABASE_SETUP.sql)
INSERT INTO categories (name, color) VALUES
  ('Salary',        '#10b981'),
  ('Freelance',     '#6366f1'),
  ('Investment',    '#f59e0b'),
  ('Food & Dining', '#ef4444'),
  ('Transport',     '#3b82f6'),
  ('Housing',       '#8b5cf6'),
  ('Healthcare',    '#ec4899'),
  ('Entertainment', '#f97316'),
  ('Shopping',      '#14b8a6'),
  ('Utilities',     '#64748b'),
  ('Education',     '#06b6d4'),
  ('Other',         '#94a3b8')
ON CONFLICT (name) DO NOTHING;

-- 4. Seed demo users with real bcrypt hashes
INSERT INTO users (email, full_name, password_hash, role, status) VALUES
  ('admin@demo.com',   'Admin User',   '$2b$12$v8iN1NuLGqwQ5Pw08UEn3e3XyeF080mh4OVtUjTYTHdtC2zeaCL0C', 'admin',   'active'),
  ('analyst@demo.com', 'Analyst User', '$2b$12$E9M1ELw9R6an5swhFnSAa..XyjcSjEJZSCfWjyHdVmz/Uasba4xXy', 'analyst', 'active'),
  ('viewer@demo.com',  'Viewer User',  '$2b$12$5cppF9z02evf4IwXrJkMee.viXRS51Le/iQkGThC/yLdGb1ejBLmu', 'viewer',  'active')
ON CONFLICT (email) DO UPDATE SET
  password_hash = EXCLUDED.password_hash,
  role          = EXCLUDED.role,
  status        = EXCLUDED.status;

-- 5. Seed sample transactions using admin's auto-generated UUID
DO $$
DECLARE admin_id UUID;
BEGIN
  SELECT id INTO admin_id FROM users WHERE email = 'admin@demo.com';

  INSERT INTO transactions (amount, type, category, date, notes, description, created_by) VALUES
    -- 5 months ago
    (75000.00, 'income',  'Salary',        (NOW() - INTERVAL '5 months')::date, 'Monthly salary',        'Nov salary',        admin_id),
    (25000.00, 'income',  'Freelance',     (NOW() - INTERVAL '5 months')::date, 'Web project',           'Client payment',    admin_id),
    (18000.00, 'expense', 'Housing',       (NOW() - INTERVAL '5 months')::date, 'Office rent',           'Monthly rent',      admin_id),
    ( 5500.00, 'expense', 'Utilities',     (NOW() - INTERVAL '5 months')::date, 'Electricity bill',      'MSEB bill',         admin_id),
    ( 3200.00, 'expense', 'Food & Dining', (NOW() - INTERVAL '5 months')::date, 'Team lunch',            'Catering',          admin_id),
    -- 4 months ago
    (75000.00, 'income',  'Salary',        (NOW() - INTERVAL '4 months')::date, 'Monthly salary',        'Dec salary',        admin_id),
    (12000.00, 'income',  'Freelance',     (NOW() - INTERVAL '4 months')::date, 'Design work',           'Logo project',      admin_id),
    (18000.00, 'expense', 'Housing',       (NOW() - INTERVAL '4 months')::date, 'Office rent',           'Monthly rent',      admin_id),
    ( 4800.00, 'expense', 'Transport',     (NOW() - INTERVAL '4 months')::date, 'Fuel + cab',            'Travel expenses',   admin_id),
    (15000.00, 'income',  'Investment',    (NOW() - INTERVAL '4 months')::date, 'Dividend',              'Mutual fund',       admin_id),
    -- 3 months ago
    (75000.00, 'income',  'Salary',        (NOW() - INTERVAL '3 months')::date, 'Monthly salary',        'Jan salary',        admin_id),
    ( 9500.00, 'income',  'Freelance',     (NOW() - INTERVAL '3 months')::date, 'Content writing',       'Blog articles',     admin_id),
    (18000.00, 'expense', 'Housing',       (NOW() - INTERVAL '3 months')::date, 'Office rent',           'Monthly rent',      admin_id),
    ( 6200.00, 'expense', 'Entertainment', (NOW() - INTERVAL '3 months')::date, 'Team outing',           'Team dinner',       admin_id),
    ( 4100.00, 'expense', 'Healthcare',    (NOW() - INTERVAL '3 months')::date, 'Medical check',         'Annual checkup',    admin_id),
    -- 2 months ago
    (75000.00, 'income',  'Salary',        (NOW() - INTERVAL '2 months')::date, 'Monthly salary',        'Feb salary',        admin_id),
    (30000.00, 'income',  'Freelance',     (NOW() - INTERVAL '2 months')::date, 'App development',       'Mobile app',        admin_id),
    (18000.00, 'expense', 'Housing',       (NOW() - INTERVAL '2 months')::date, 'Office rent',           'Monthly rent',      admin_id),
    ( 8900.00, 'expense', 'Shopping',      (NOW() - INTERVAL '2 months')::date, 'Office supplies',       'Stationery',        admin_id),
    ( 3600.00, 'expense', 'Food & Dining', (NOW() - INTERVAL '2 months')::date, 'Catering',              'Office snacks',     admin_id),
    -- 1 month ago
    (75000.00, 'income',  'Salary',        (NOW() - INTERVAL '1 month')::date,  'Monthly salary',        'Mar salary',        admin_id),
    (18500.00, 'income',  'Freelance',     (NOW() - INTERVAL '1 month')::date,  'SEO project',           'SEO audit',         admin_id),
    (20000.00, 'income',  'Investment',    (NOW() - INTERVAL '1 month')::date,  'Stock sale',            'Equity gains',      admin_id),
    (18000.00, 'expense', 'Housing',       (NOW() - INTERVAL '1 month')::date,  'Office rent',           'Monthly rent',      admin_id),
    ( 5000.00, 'expense', 'Utilities',     (NOW() - INTERVAL '1 month')::date,  'Internet + electricity','Broadband + MSEB',  admin_id),
    -- current month
    (75000.00, 'income',  'Salary',        CURRENT_DATE,                         'Monthly salary',        'Apr salary',        admin_id),
    (22000.00, 'income',  'Freelance',     CURRENT_DATE,                         'UI/UX project',         'Dashboard design',  admin_id),
    (18000.00, 'expense', 'Housing',       CURRENT_DATE,                         'Office rent',           'Monthly rent',      admin_id),
    ( 7500.00, 'expense', 'Transport',     CURRENT_DATE,                         'Monthly travel',        'Fuel + metro',      admin_id),
    ( 4200.00, 'expense', 'Food & Dining', CURRENT_DATE,                         'Office snacks',         'Team breakfast',    admin_id);
END $$;

-- ============================================================
-- NEXT STEPS:
-- 1. Restart the FastAPI server.
-- 2. Login with admin@demo.com / admin123
-- ============================================================
