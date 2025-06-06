-- Users
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(128) UNIQUE,
    full_name VARCHAR(128),
    role VARCHAR(32) DEFAULT 'employee'
);

-- Chat logs for chatbot analytics and audit
CREATE TABLE IF NOT EXISTS chat_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    channel VARCHAR(32) NOT NULL DEFAULT 'web',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Leave management
CREATE TABLE IF NOT EXISTS leave_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    type VARCHAR(32) NOT NULL,
    reason TEXT,
    status VARCHAR(32) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS leave_balances (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    leave_type VARCHAR(32) NOT NULL,
    balance NUMERIC DEFAULT 0
);

-- Attendance management
CREATE TABLE IF NOT EXISTS attendance (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    date DATE NOT NULL,
    punch_in TIME,
    punch_out TIME,
    status VARCHAR(32) DEFAULT 'absent'
);

-- Payslip and tax
CREATE TABLE IF NOT EXISTS payslips (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    url TEXT NOT NULL,
    date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS tax_summary (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    year INT,
    total_income NUMERIC,
    tax_paid NUMERIC,
    tax_due NUMERIC
);

-- Onboarding assistant
CREATE TABLE IF NOT EXISTS onboarding_steps (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    step VARCHAR(64) NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS onboarding_documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    document VARCHAR(64) NOT NULL,
    status VARCHAR(32) DEFAULT 'pending',
    url TEXT
);

-- HR policies and FAQ
CREATE TABLE IF NOT EXISTS hr_policies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(64) UNIQUE NOT NULL,
    content TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hr_faqs (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL
);

-- Reimbursement process
CREATE TABLE IF NOT EXISTS reimbursement_process (
    id SERIAL PRIMARY KEY,
    step INT NOT NULL,
    process TEXT NOT NULL,
    notes TEXT
);

-- Holiday calendar
CREATE TABLE IF NOT EXISTS holiday_calendar (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    name VARCHAR(128) NOT NULL
);