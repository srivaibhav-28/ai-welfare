-- Supabase schema for AI Welfare app

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    mobile_number TEXT,
    role TEXT NOT NULL DEFAULT 'citizen',
    profile JSONB DEFAULT '{}'::jsonb,
    is_blocked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

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
    created_at TIMESTAMPTZ DEFAULT NOW()
);

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

-- Disable Row-Level Security (RLS) so API queries can read, insert, update, and delete rows
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE schemes DISABLE ROW LEVEL SECURITY;
ALTER TABLE applications DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_documents DISABLE ROW LEVEL SECURITY;
