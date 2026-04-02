-- ============================================================
-- PROCEDURE 1 – upsert_user(p_name, p_phone)
--   Inserts a new record.  If the phone already exists, updates
--   the name instead (upsert / insert-or-update).
-- ============================================================
CREATE OR REPLACE PROCEDURE upsert_user(p_name TEXT, p_phone TEXT)
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO phonebook (name, phone)
    VALUES (p_name, p_phone)
    ON CONFLICT (phone)
        DO UPDATE SET name = EXCLUDED.name;
END;
$$;


-- ============================================================
-- PROCEDURE 2 – insert_many_users(p_names[], p_phones[])
--   Iterates parallel arrays; validates each phone with a regex.
--   Valid  → upsert into phonebook.
--   Invalid → insert into phonebook_invalid_records.
--   Call SELECT * FROM phonebook_invalid_records afterwards to
--   see every bad row returned by this procedure.
-- ============================================================
CREATE OR REPLACE PROCEDURE insert_many_users(
    p_names  TEXT[],
    p_phones TEXT[]
)
LANGUAGE plpgsql AS $$
DECLARE
    i           INT;
    total       INT;
    v_name      TEXT;
    v_phone     TEXT;
    phone_regex CONSTANT TEXT := '^\+?[0-9]{7,15}$';
BEGIN
    -- Clear previous invalid-record log
    DELETE FROM phonebook_invalid_records;

    total := array_length(p_names, 1);

    FOR i IN 1 .. total LOOP
        v_name  := p_names[i];
        v_phone := p_phones[i];

        IF v_phone ~ phone_regex THEN
            -- Valid: upsert
            INSERT INTO phonebook (name, phone)
            VALUES (v_name, v_phone)
            ON CONFLICT (phone)
                DO UPDATE SET name = EXCLUDED.name;
        ELSE
            -- Invalid: log it
            INSERT INTO phonebook_invalid_records (name, phone)
            VALUES (v_name, v_phone);
        END IF;
    END LOOP;
END;
$$;


-- ============================================================
-- PROCEDURE 3 – delete_user(p_search)
--   Deletes every row whose name OR phone matches p_search
--   exactly.  Raises a NOTICE when nothing was deleted.
-- ============================================================
CREATE OR REPLACE PROCEDURE delete_user(p_search TEXT)
LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM phonebook
    WHERE name  = p_search
       OR phone = p_search;

    IF NOT FOUND THEN
        RAISE NOTICE 'No record found matching: %', p_search;
    END IF;
END;
$$;