-- ── 1. add_phone 
-- Adds a phone number to an existing contact (looked up by full name).
CREATE OR REPLACE PROCEDURE add_phone(
    p_contact_name VARCHAR,   -- "First Last"
    p_phone        VARCHAR,
    p_type         VARCHAR    -- home, work, mobile
)
LANGUAGE plpgsql AS $$
DECLARE
    v_id INT;
BEGIN
    SELECT id INTO v_id
    FROM   contacts
    WHERE  LOWER(first_name || ' ' || last_name) = LOWER(TRIM(p_contact_name))
    LIMIT  1;

    IF v_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found.', p_contact_name;
    END IF;

    IF p_type NOT IN ('home', 'work', 'mobile') THEN
        RAISE EXCEPTION 'Invalid phone type "%". Use home | work | mobile.', p_type;
    END IF;

    INSERT INTO phones (contact_id, phone, type)
    VALUES (v_id, TRIM(p_phone), p_type);
END;
$$;


-- 2. move_to_group 
-- Moves a contact to the specified group; creates the group if missing.
CREATE OR REPLACE PROCEDURE move_to_group(
    p_contact_name VARCHAR,
    p_group_name   VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INT;
    v_group_id   INT;
BEGIN
    -- Resolve (or create) the group
    SELECT id INTO v_group_id
    FROM   groups
    WHERE  LOWER(name) = LOWER(TRIM(p_group_name));

    IF v_group_id IS NULL THEN
        INSERT INTO groups (name)
        VALUES (INITCAP(TRIM(p_group_name)))
        RETURNING id INTO v_group_id;
    END IF;

    -- Resolve the contact
    SELECT id INTO v_contact_id
    FROM   contacts
    WHERE  LOWER(first_name || ' ' || last_name) = LOWER(TRIM(p_contact_name))
    LIMIT  1;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found.', p_contact_name;
    END IF;

    UPDATE contacts
    SET    group_id = v_group_id
    WHERE  id = v_contact_id;
END;
$$;


-- 3. search_contacts 
-- Full-text pattern search across name, email, and all phone numbers.
CREATE OR REPLACE FUNCTION search_contacts(p_query TEXT)
RETURNS TABLE (
    id         INT,
    first_name VARCHAR,
    last_name  VARCHAR,
    email      VARCHAR,
    birthday   DATE,
    group_name VARCHAR,
    phones     TEXT          -- comma-separated "number (type)"
)
LANGUAGE plpgsql AS $$
DECLARE
    v_pattern TEXT := '%' || LOWER(TRIM(p_query)) || '%';
BEGIN
    RETURN QUERY
    SELECT DISTINCT
           c.id,
           c.first_name,
           c.last_name,
           c.email,
           c.birthday,
           g.name AS group_name,
           STRING_AGG(p.phone || ' (' || p.type || ')', ', '
                      ORDER BY p.type) AS phones
    FROM   contacts c
    LEFT JOIN groups g ON g.id   = c.group_id
    LEFT JOIN phones p ON p.contact_id = c.id
    WHERE  LOWER(c.first_name)                    LIKE v_pattern
        OR LOWER(c.last_name)                     LIKE v_pattern
        OR LOWER(c.first_name || ' ' || c.last_name) LIKE v_pattern
        OR LOWER(COALESCE(c.email, ''))           LIKE v_pattern
        OR LOWER(COALESCE(p.phone, ''))           LIKE v_pattern
    GROUP BY c.id, c.first_name, c.last_name, c.email, c.birthday, g.name
    ORDER BY c.last_name, c.first_name;
END;
$$;