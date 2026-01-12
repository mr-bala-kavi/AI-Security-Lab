-- AI Security Lab - Database Schema
-- Contains tables for progress tracking and vulnerable data for exercises

-- ============================================
-- Progress Tracking Tables
-- ============================================

-- Module progress for each user session
CREATE TABLE IF NOT EXISTS module_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    module_name TEXT NOT NULL,
    security_level TEXT DEFAULT 'LOW',
    completed BOOLEAN DEFAULT 0,
    attempts INTEGER DEFAULT 0,
    hints_used INTEGER DEFAULT 0,
    successful_exploits INTEGER DEFAULT 0,
    first_attempt_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, module_name)
);

-- Chat history for chatbot-based modules
CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    module_name TEXT NOT NULL,
    role TEXT NOT NULL,  -- 'user', 'assistant', or 'system'
    content TEXT NOT NULL,
    is_exploit_attempt BOOLEAN DEFAULT 0,
    is_successful_exploit BOOLEAN DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Hints for all modules (3 per module)
CREATE TABLE IF NOT EXISTS hints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_name TEXT NOT NULL,
    hint_number INTEGER NOT NULL,
    hint_text TEXT NOT NULL,
    security_level TEXT DEFAULT 'ALL',  -- 'LOW', 'MEDIUM', 'HIGH', or 'ALL'
    UNIQUE(module_name, hint_number, security_level)
);

-- ============================================
-- Vulnerable Data Tables (for Module 8)
-- INTENTIONALLY INSECURE for educational purposes
-- ============================================

-- Users table with plaintext passwords (VULNERABLE BY DESIGN)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,  -- Stored in plaintext intentionally!
    email TEXT,
    full_name TEXT,
    role TEXT DEFAULT 'user',
    salary REAL,
    department TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Secrets table for sensitive data
CREATE TABLE IF NOT EXISTS secrets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    secret_key TEXT NOT NULL,
    secret_value TEXT NOT NULL,
    classification TEXT DEFAULT 'CONFIDENTIAL',  -- 'PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'TOP_SECRET'
    owner TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service TEXT NOT NULL,
    api_key TEXT NOT NULL,
    scope TEXT,
    environment TEXT DEFAULT 'production',
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Financial records with PII (VULNERABLE BY DESIGN)
CREATE TABLE IF NOT EXISTS financial_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_number TEXT NOT NULL,
    routing_number TEXT,
    balance REAL DEFAULT 0.0,
    ssn TEXT,  -- Social Security Number (VULNERABLE)
    credit_card TEXT,  -- Full credit card number (VULNERABLE)
    owner_name TEXT,
    account_type TEXT DEFAULT 'checking',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Model Inversion Data (for Module 4)
-- Simulates "memorized" training data
-- ============================================

CREATE TABLE IF NOT EXISTS training_data_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_type TEXT NOT NULL,  -- 'email', 'phone', 'address', 'medical', 'financial'
    content TEXT NOT NULL,
    person_name TEXT,
    is_sensitive BOOLEAN DEFAULT 1,
    extraction_difficulty TEXT DEFAULT 'LOW'  -- 'LOW', 'MEDIUM', 'HIGH'
);

-- ============================================
-- Tool/Plugin Logs (for Module 7)
-- ============================================

CREATE TABLE IF NOT EXISTS tool_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    parameters TEXT,  -- JSON string
    result TEXT,
    is_authorized BOOLEAN DEFAULT 1,
    is_dangerous BOOLEAN DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- DoS Attack Metrics (for Module 6)
-- ============================================

CREATE TABLE IF NOT EXISTS request_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    input_length INTEGER,
    token_count INTEGER,
    response_time_ms REAL,
    memory_usage_mb REAL,
    cpu_usage_percent REAL,
    was_throttled BOOLEAN DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Indexes for Performance
-- ============================================

CREATE INDEX IF NOT EXISTS idx_module_progress_session ON module_progress(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_session ON chat_history(session_id, module_name);
CREATE INDEX IF NOT EXISTS idx_hints_module ON hints(module_name);
CREATE INDEX IF NOT EXISTS idx_tool_calls_session ON tool_calls(session_id);
CREATE INDEX IF NOT EXISTS idx_request_metrics_session ON request_metrics(session_id);
