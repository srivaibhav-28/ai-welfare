-- Supabase schema for AI Welfare app

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    mobile_number TEXT DEFAULT '',
    role TEXT NOT NULL DEFAULT 'citizen',
    picture TEXT DEFAULT '',
    profile JSONB DEFAULT '{}'::jsonb,
    is_blocked BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Migration Statements: Ensure existing production tables acquire any missing columns
ALTER TABLE users ADD COLUMN IF NOT EXISTS id TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS name TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS mobile_number TEXT DEFAULT '';
ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'citizen';
ALTER TABLE users ADD COLUMN IF NOT EXISTS picture TEXT DEFAULT '';
ALTER TABLE users ADD COLUMN IF NOT EXISTS profile JSONB DEFAULT '{}'::jsonb;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_blocked BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS verified_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

CREATE TABLE IF NOT EXISTS schemes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT,
    description TEXT,
    benefits TEXT,
    criteria JSONB DEFAULT '{}'::jsonb,
    required_documents JSONB DEFAULT '[]'::jsonb,
    official_link TEXT,
    last_date TEXT,
    state_restriction TEXT,
    icon TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS applications (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user_name TEXT,
    user_email TEXT,
    scheme_id TEXT NOT NULL REFERENCES schemes(id),
    scheme_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Applied',
    applied_date TEXT,
    uploaded_documents JSONB DEFAULT '{}'::jsonb,
    remarks TEXT,
    is_flagged_fraud BOOLEAN DEFAULT FALSE,
    fraud_risk_score INT DEFAULT 0,
    fraud_flags JSONB DEFAULT '[]'::jsonb,
    timeline_history JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Migration Statements: Ensure existing applications table acquires any missing columns
ALTER TABLE applications ADD COLUMN IF NOT EXISTS is_flagged_fraud BOOLEAN DEFAULT FALSE;
ALTER TABLE applications ADD COLUMN IF NOT EXISTS fraud_risk_score INT DEFAULT 0;
ALTER TABLE applications ADD COLUMN IF NOT EXISTS fraud_flags JSONB DEFAULT '[]'::jsonb;
ALTER TABLE applications ADD COLUMN IF NOT EXISTS timeline_history JSONB DEFAULT '[]'::jsonb;

CREATE TABLE IF NOT EXISTS user_documents (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Uploaded',
    upload_date TEXT,
    file_name TEXT,
    file_url TEXT,
    remarks TEXT,
    verified_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, document_name)
);

CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_user_documents_user_id ON user_documents(user_id);

CREATE TABLE IF NOT EXISTS pending_registrations (
    email TEXT PRIMARY KEY,
    otp TEXT NOT NULL,
    user_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    expires_at TIMESTAMPTZ NOT NULL,
    last_sent_at TIMESTAMPTZ NOT NULL,
    attempts INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE schemes ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE pending_registrations ENABLE ROW LEVEL SECURITY;

-- Payments Table
CREATE TABLE IF NOT EXISTS payments (
    id TEXT PRIMARY KEY,
    payment_id TEXT,
    application_id TEXT REFERENCES applications(id) ON DELETE CASCADE,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    scheme_id TEXT,
    scheme_name TEXT,
    beneficiary_name TEXT,
    amount NUMERIC DEFAULT 0.00,
    payment_status TEXT NOT NULL DEFAULT 'Pending',
    payment_reference TEXT DEFAULT '',
    approved_by TEXT DEFAULT '',
    approved_at TEXT DEFAULT '',
    paid_at TEXT DEFAULT '',
    remarks TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_application_id ON payments(application_id);
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;

-- Notifications Table
CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    target_user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    type TEXT DEFAULT 'info',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    sent_by TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_notifications_target_user_id ON notifications(target_user_id);
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    action TEXT NOT NULL,
    performed_by TEXT NOT NULL,
    details TEXT DEFAULT '',
    ip_address TEXT DEFAULT '127.0.0.1',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'applications' AND policyname = 'Allow public read write applications') THEN
        CREATE POLICY "Allow public read write applications" ON applications FOR ALL USING (true) WITH CHECK (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'users' AND policyname = 'Allow public read write users') THEN
        CREATE POLICY "Allow public read write users" ON users FOR ALL USING (true) WITH CHECK (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'schemes' AND policyname = 'Allow public read write schemes') THEN
        CREATE POLICY "Allow public read write schemes" ON schemes FOR ALL USING (true) WITH CHECK (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'user_documents' AND policyname = 'Allow public read write user_documents') THEN
        CREATE POLICY "Allow public read write user_documents" ON user_documents FOR ALL USING (true) WITH CHECK (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'pending_registrations' AND policyname = 'Allow public read write pending_registrations') THEN
        CREATE POLICY "Allow public read write pending_registrations" ON pending_registrations FOR ALL USING (true) WITH CHECK (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'payments' AND policyname = 'Allow public read write payments') THEN
        CREATE POLICY "Allow public read write payments" ON payments FOR ALL USING (true) WITH CHECK (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'notifications' AND policyname = 'Allow public read write notifications') THEN
        CREATE POLICY "Allow public read write notifications" ON notifications FOR ALL USING (true) WITH CHECK (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'audit_logs' AND policyname = 'Allow public read write audit_logs') THEN
        CREATE POLICY "Allow public read write audit_logs" ON audit_logs FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;
