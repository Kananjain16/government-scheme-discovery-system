
USE government_scheme_db;

CREATE TABLE IF NOT EXISTS schemes (
    scheme_id INT AUTO_INCREMENT PRIMARY KEY,
    scheme_name VARCHAR(500) NOT NULL,
    slug VARCHAR(255),
    details LONGTEXT,
    benefits LONGTEXT,
    eligibility LONGTEXT,
    application LONGTEXT,
    documents LONGTEXT,
    level VARCHAR(50),
    schemeCategory TEXT,
    tags TEXT,
    source_url TEXT,
    source_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_scheme_name (scheme_name(150)),
    INDEX idx_level (level),
    INDEX idx_slug (slug)
);
