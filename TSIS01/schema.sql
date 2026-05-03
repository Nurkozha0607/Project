-- PhoneBook – Extended Schema

-- Groups directory
CREATE TABLE IF NOT EXISTS groups (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL          -- Family | Work | Friend | Other
);

-- Seed default groups
INSERT INTO groups (name)
VALUES ('Family'), ('Work'), ('Friend'), ('Other')
ON CONFLICT (name) DO NOTHING;

-- ── Contacts 
CREATE TABLE IF NOT EXISTS contacts (
    id         SERIAL PRIMARY KEY,
    first_name VARCHAR(50)  NOT NULL,
    last_name  VARCHAR(50)  NOT NULL,
    email      VARCHAR(120),
    birthday   DATE,
    group_id   INT REFERENCES groups(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (first_name, last_name)
);

-- ── Phones ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS phones (
    id         SERIAL PRIMARY KEY,
    contact_id INT NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    phone      VARCHAR(20)  NOT NULL,
    type       VARCHAR(10)  NOT NULL DEFAULT 'mobile'
                CHECK (type IN ('home', 'work', 'mobile'))
);

-- ── Pagination helper ─────────────────────
CREATE OR REPLACE FUNCTION paginate_contacts(p_limit INT, p_offset INT)
RETURNS TABLE (
    id         INT,
    first_name VARCHAR,
    last_name  VARCHAR,
    email      VARCHAR,
    birthday   DATE,
    group_name VARCHAR,
    created_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT c.id, c.first_name, c.last_name, c.email, c.birthday,
           g.name AS group_name, c.created_at
    FROM   contacts c
    LEFT JOIN groups g ON g.id = c.group_id
    ORDER BY c.last_name, c.first_name
    LIMIT  p_limit
    OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;