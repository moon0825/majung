-- 마중(Majung) 모의 뱅킹 코어 — SQLite DDL (07 시스템설계 §5)
-- "LLM은 송금 실행 경로에 없다." 모든 판정은 결정적 코드 + 아래 테이블에서.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    user_id        TEXT PRIMARY KEY,
    name           TEXT NOT NULL,
    nationality    TEXT,
    visa_type      TEXT,
    visa_expiry    TEXT,            -- ISO date
    language       TEXT,            -- 모국어 (통지·확인용)
    account_status TEXT
);

CREATE TABLE IF NOT EXISTS accounts (
    account_id                 TEXT PRIMARY KEY,
    user_id                    TEXT NOT NULL REFERENCES users(user_id),
    balance_krw                INTEGER NOT NULL DEFAULT 0,
    is_limited_account         INTEGER NOT NULL DEFAULT 1,   -- 한도계좌 여부(1=한도)
    salary_months_consecutive  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS salary_events (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      TEXT NOT NULL REFERENCES users(user_id),
    amount_krw   INTEGER NOT NULL,
    deposited_at TEXT NOT NULL      -- ISO datetime
);

CREATE TABLE IF NOT EXISTS fx_rates (
    pair       TEXT NOT NULL,       -- e.g. 'KRW/VND'
    date       TEXT NOT NULL,       -- ISO date
    close_rate REAL NOT NULL,
    PRIMARY KEY (pair, date)
);

CREATE TABLE IF NOT EXISTS mandates (
    mandate_id  TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL REFERENCES users(user_id),
    json_blob   TEXT NOT NULL,      -- 위임장 전체 JSON (§3 스키마)
    status      TEXT NOT NULL DEFAULT 'active',
    valid_until TEXT,
    esign_hash  TEXT,
    revoked     INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS beneficiaries (
    bnf_id         TEXT PRIMARY KEY,
    user_id        TEXT NOT NULL REFERENCES users(user_id),
    name           TEXT,
    bank           TEXT,
    account_masked TEXT,
    is_whitelisted INTEGER NOT NULL DEFAULT 0,
    first_seen     TEXT
);

CREATE TABLE IF NOT EXISTS transactions (
    tx_id      TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL REFERENCES users(user_id),
    bnf_id     TEXT REFERENCES beneficiaries(bnf_id),
    amount_krw INTEGER NOT NULL,
    fx_rate    REAL,
    status     TEXT NOT NULL,       -- executed | held | blocked
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS blacklist_patterns (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_type TEXT,              -- 'loan_scam' | 'phishing' ...
    keyword      TEXT NOT NULL      -- 신분증·비번·OTP·선입금 요구 등
);

CREATE TABLE IF NOT EXISTS loans_external (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          TEXT NOT NULL REFERENCES users(user_id),
    principal        INTEGER NOT NULL,
    apr              REAL NOT NULL,   -- 연이율 (0.30 = 30%)
    lender           TEXT,
    remaining_months INTEGER
);

CREATE TABLE IF NOT EXISTS refi_products (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    apr             REAL NOT NULL,    -- JB 대환 연 13.59%
    max_term_months INTEGER
);

CREATE TABLE IF NOT EXISTS str_queue (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    tx_id  TEXT,
    score  INTEGER,
    flags  TEXT,                     -- JSON array
    status TEXT NOT NULL DEFAULT 'queued'
);

CREATE TABLE IF NOT EXISTS audit_log (
    log_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      TEXT,
    event_type   TEXT NOT NULL,
    payload_json TEXT,
    created_at   TEXT NOT NULL
);

-- 건별 통지 이력 — 전금법 요건 ② (건별 통지)
CREATE TABLE IF NOT EXISTS notifications (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       TEXT NOT NULL,
    type          TEXT NOT NULL,          -- executed | held | str_hold | blocked | system
    message_ko    TEXT NOT NULL,
    message_local TEXT NOT NULL,
    tx_id         TEXT,
    mandate_id    TEXT,
    revocable     INTEGER NOT NULL DEFAULT 1,  -- 1 = 철회 가능
    created_at    TEXT NOT NULL
);
