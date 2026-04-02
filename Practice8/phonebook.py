from connect import get_connection, init_db


def _print_rows(rows: list, header: str = "") -> None:
    """Pretty-print a list of (id, name, phone) tuples."""
    if header:
        print(f"\n{'─' * 50}")
        print(f"  {header}")
        print(f"{'─' * 50}")
    if not rows:
        print("  (no records)")
        return
    print(f"  {'ID':<6} {'Name':<25} {'Phone'}")
    print(f"  {'─'*4:<6} {'─'*23:<25} {'─'*15}")
    for row in rows:
        print(f"  {row[0]:<6} {row[1]:<25} {row[2]}")


# ── 1. search by pattern 

def search_phonebook(pattern: str) -> list:
    """
    Return all phonebook rows where name OR phone contains *pattern*
    (case-insensitive).  Calls the SQL function search_phonebook().
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM search_phonebook(%s);", (pattern,))
            rows = cur.fetchall()
    _print_rows(rows, f"Search results for '{pattern}'")
    return rows


# ── 2. upsert one user 

def upsert_user(name: str, phone: str) -> None:
    """
    Insert a new user.  If the phone number already exists, update the name.
    Calls the SQL procedure upsert_user().
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("CALL upsert_user(%s, %s);", (name, phone))
        conn.commit()
    print(f"  ✔  upsert_user({name!r}, {phone!r}) – done.")


# ── 3. bulk insert with validation 

def insert_many_users(names: list[str], phones: list[str]) -> list:
    """
    Insert multiple users from parallel lists.
    Each phone is validated inside the SQL procedure; invalid rows are
    stored in phonebook_invalid_records and returned here as a list.
    """
    if len(names) != len(phones):
        raise ValueError("'names' and 'phones' lists must be the same length.")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "CALL insert_many_users(%s::text[], %s::text[]);",
                (names, phones),
            )
            # Fetch invalid records written by the procedure
            cur.execute("SELECT name, phone FROM phonebook_invalid_records;")
            invalid = cur.fetchall()
        conn.commit()

    print(f"\n  ✔  insert_many_users – processed {len(names)} record(s).")
    if invalid:
        print(f"\n  ⚠  Invalid records ({len(invalid)}) – NOT inserted:")
        print(f"  {'Name':<25} {'Phone'}")
        print(f"  {'─'*23:<25} {'─'*15}")
        for row in invalid:
            print(f"  {row[0]:<25} {row[1]}")
    else:
        print("  All phones were valid.")
    return invalid


# ── 4. paginated query 

def get_phonebook_page(limit: int = 10, offset: int = 0) -> list:
    """
    Return one page of the phonebook (ordered by id).
    Calls the SQL function get_phonebook_page().
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM get_phonebook_page(%s, %s);",
                (limit, offset),
            )
            rows = cur.fetchall()
    page_num = offset // limit + 1 if limit else 1
    _print_rows(rows, f"Page {page_num}  (limit={limit}, offset={offset})")
    return rows


# ── 5. delete by name or phone 

def delete_user(name_or_phone: str) -> None:
    """
    Delete every phonebook row whose name OR phone matches the argument.
    Calls the SQL procedure delete_user().
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("CALL delete_user(%s);", (name_or_phone,))
        conn.commit()
    print(f"  ✔  delete_user({name_or_phone!r}) – done.")


# ── demo / smoke-test 

def main():
    # Initialise DB (creates tables + loads SQL files)
    with get_connection() as conn:
        init_db(conn)

    print("\n" + "═" * 50)
    print("  PhoneBook – Practice 8 Demo")
    print("═" * 50)

    # ── 2: upsert single users
    print("\n[2] Upsert single users")
    upsert_user("Aibek Seitkali",  "+77011111111")
    upsert_user("Dana Bekova",     "+77022222222")
    upsert_user("Zarina Nurlan",   "+77033333333")
    upsert_user("Timur Akhmet",    "+77044444444")
    upsert_user("Aibek Seitkali",  "+77011111111")  # duplicate → update

    # ── 3: bulk insert with some invalid phones
    print("\n[3] Bulk insert (with intentionally bad phones)")
    insert_many_users(
        names  = ["Baglan", "Aruzhan", "Sanzhar",  "Ghost"],
        phones = ["+77055555555", "abc123", "+77077777777", "12"],
    )

    # ── 1: search
    print("\n[1] Pattern search")
    search_phonebook("bek")          # matches 'Aibek' and 'Bekova'
    search_phonebook("+7707")        # matches by phone prefix

    # ── 4: pagination
    print("\n[4] Pagination")
    get_phonebook_page(limit=3, offset=0)  # page 1
    get_phonebook_page(limit=3, offset=3)  # page 2

    # ── 5: delete
    print("\n[5] Delete")
    delete_user("Ghost")             # by name – won't exist (invalid phone)
    delete_user("+77033333333")      # by phone
    delete_user("Dana Bekova")       # by name

    # Final state
    print("\n[Final] Full phonebook (page 1, limit=20)")
    get_phonebook_page(limit=20, offset=0)


if __name__ == "__main__":
    main()