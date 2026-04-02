-- ============================================================
-- FUNCTION 1 – search_phonebook(pattern)
--   Returns all rows where name OR phone contains the pattern
--   (case-insensitive).
-- ============================================================
CREATE OR REPLACE FUNCTION search_phonebook(pattern TEXT)
RETURNS TABLE(id INT, name VARCHAR, phone VARCHAR) AS $$
BEGIN
    RETURN QUERY
        SELECT pb.id, pb.name, pb.phone
        FROM   phonebook pb
        WHERE  pb.name  ILIKE '%' || pattern || '%'
           OR  pb.phone ILIKE '%' || pattern || '%'
        ORDER BY pb.id;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- FUNCTION 2 – get_phonebook_page(p_limit, p_offset)
--   Returns a single page of records ordered by id.
--   Default: first 10 rows.
-- ============================================================
CREATE OR REPLACE FUNCTION get_phonebook_page(
    p_limit  INT DEFAULT 10,
    p_offset INT DEFAULT 0
)
RETURNS TABLE(id INT, name VARCHAR, phone VARCHAR) AS $$
BEGIN
    RETURN QUERY
        SELECT pb.id, pb.name, pb.phone
        FROM   phonebook pb
        ORDER BY pb.id
        LIMIT  p_limit
        OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;