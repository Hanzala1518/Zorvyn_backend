-- ============================================================
-- APPROVAL_FLOW_MIGRATION.sql
-- Run this in Supabase SQL Editor AFTER SUPABASE_FIX.sql
-- Adds approval workflow, budgets, and notifications tables.
-- ============================================================

-- 1. Add approval columns to existing users table
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS approval_status VARCHAR(20) DEFAULT 'approved',
  ADD COLUMN IF NOT EXISTS rejection_reason TEXT,
  ADD COLUMN IF NOT EXISTS approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS approved_at TIMESTAMPTZ;

-- 2. Ensure all existing users are marked as approved
UPDATE users SET approval_status = 'approved' WHERE approval_status IS NULL OR approval_status = '';

-- 3. Budgets table
CREATE TABLE IF NOT EXISTS budgets (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  category VARCHAR(50) NOT NULL,
  monthly_limit NUMERIC(12,2) NOT NULL CHECK (monthly_limit > 0),
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, category)
);

-- 4. Notifications table (replaces mock email)
CREATE TABLE IF NOT EXISTS notifications (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type VARCHAR(50) NOT NULL,
  title VARCHAR(200) NOT NULL,
  message TEXT NOT NULL,
  is_read BOOLEAN DEFAULT FALSE,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Performance indexes
CREATE INDEX IF NOT EXISTS idx_users_approval_status ON users(approval_status) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_budgets_user_id ON budgets(user_id) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id, is_read);

-- 6. Disable RLS on new tables
ALTER TABLE budgets       DISABLE ROW LEVEL SECURITY;
ALTER TABLE notifications DISABLE ROW LEVEL SECURITY;

-- ============================================================
-- Done. New endpoints available:
-- POST /api/auth/register         — public self-registration
-- GET  /api/admin/pending-approvals
-- POST /api/admin/approve/{id}
-- POST /api/admin/reject/{id}
-- GET  /api/budgets/
-- POST /api/budgets/
-- DELETE /api/budgets/{id}
-- GET  /api/notifications/
-- GET  /api/analytics/health-score
-- GET  /api/analytics/recurring
-- GET  /api/analytics/velocity
-- ============================================================
