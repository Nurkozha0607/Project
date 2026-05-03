import csv
import json
import os
import sys
from datetime import date, datetime

import psycopg2
from connect import get_connection

# helpers

def _coerce_date(value: str):
    """Parse ISO date string or return None."""
    if not value:
        return None # blank input > no birthday stored
    try:
        # strptime parses the string according to the given format
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None

def _get_or_create_group(cur, name: str) -> int:
    """Return group id, creating the group if it doesn't exist."""
    name = name.strip().title() 
    cur.execute("SELECT id FROM groups WHERE LOWER(name) = LOWER(%s)", (name,))
    row = cur.fetchone()
    if row:
        return row[0] # group found > return its id
    cur.execute("INSERT INTO groups (name) VALUES (%s) RETURNING id", (name,))
    return cur.fetchone()[0] # Returning id gives us the new row's

def _print_contacts(rows, headers=None):
    """Pretty-print a list of contact rows."""
    if headers is None:
        headers = ["ID", "First", "Last", "Email", "Birthday", "Group", "Phones", "Added"]
    # Calculate how wide each column needs to be
    col_widths = [max(len(str(headers[i])), max((len(str(r[i] or "")) for r in rows), default=0)) # width of the header label
                  for i in range(len(headers))]
    sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    fmt = "|" + "|".join(f" {{:<{w}}} " for w in col_widths) + "|"

    print(sep)
    print(fmt.format(*headers))
    print(sep)
    for row in rows:
        # Convert every value to string; replace None with empty string
        print(fmt.format(*[str(v) if v is not None else "" for v in row]))
    print(sep)

# DB initialisation 

def init_db():
    """Apply schema.sql and procedures.sql to the database."""
    base = os.path.dirname(os.path.abspath(__file__))
    conn = get_connection()
    conn.autocommit = True # DDL statements need autocommit mode
    cur = conn.cursor()
    for fname in ("schema.sql", "procedures.sql"):
        path = os.path.join(base, fname)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                cur.execute(f.read()) # execute the entire SQL file at once
            print(f"Applied {fname}")
    cur.close()
    conn.close()

# CRUD 

def add_contact():
    first = input("First name: ").strip()
    last  = input("Last name: ").strip()
    email = input("Email: ").strip() or None
    bday  = _coerce_date(input("Birthday  (YYYY-MM-DD, blank to skip): "))
    group_name = input("Group (Family/Work/Friend/Other): ").strip() or "Other"

    # it will success or rolls back on exception when the block exits
    with get_connection() as conn:
        with conn.cursor() as cur:
            gid = _get_or_create_group(cur, group_name)
            try:
                cur.execute(
                    """INSERT INTO contacts (first_name, last_name, email, birthday, group_id)
                       VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                    (first, last, email, bday, gid)
                )
                cid = cur.fetchone()[0] # save the new contact's id for phone inserts
                # phones
                while True:
                    phone = input("  Phone number (blank to stop): ").strip()
                    if not phone:
                        break
                    ptype = input("  Type (home/work/mobile) [mobile]: ").strip() or "mobile"
                    cur.execute(
                        "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s)",
                        (cid, phone, ptype)
                    )
                conn.commit() # save all inserts permanently
                print(f"Contact '{first} {last}' added (id={cid}).")
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                print("A contact with that name already exists.")


def update_contact():
    name = input("Full name of contact to update: ").strip()
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Find the contact — LOWER() makes search case-insensitive
            cur.execute(
                "SELECT id, first_name, last_name, email, birthday FROM contacts "
                "WHERE LOWER(first_name||' '||last_name) = LOWER(%s)", (name,)
            )
            row = cur.fetchone()
            if not row:
                print("✗ Contact not found.")
                return
            cid = row[0]
            # Show what is currently stored so the user can decide what to change
            print(f"  Current → name: {row[1]} {row[2]}, email: {row[3]}, birthday: {row[4]}")
            # If user presses Enter, keep the existing value (row[3] / row[4])
            email = input("  New email (blank = keep): ").strip() or row[3]
            bday_str = input("  New birthday YYYY-MM-DD (blank = keep): ").strip()
            bday  = _coerce_date(bday_str) if bday_str else row[4]
            cur.execute(
                "UPDATE contacts SET email=%s, birthday=%s WHERE id=%s",
                (email, bday, cid)
            )
            conn.commit()
            print("✓ Contact updated.")


def delete_contact():
    name = input("Full name of contact to delete: ").strip()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM contacts "
                "WHERE LOWER(first_name||' '||last_name) = LOWER(%s) RETURNING id", (name,)
            )
            deleted = cur.fetchone() # None if no row matched
            conn.commit()
            if deleted:
                print(f"✓ Contact '{name}' deleted.")
            else:
                print("✗ Contact not found.")


# Search / filter / sort 

def _fetch_display(query: str, params: tuple, sort: str):
    """Run query, attach phones, sort, return rows ready for _print_contacts."""
    # Map user-friendly sort name → SQL ORDER BY expression
    sort_map = {
        "name":    "c.last_name, c.first_name",
        "birthday": "c.birthday NULLS LAST",
        "added":   "c.created_at",
    }
    order = sort_map.get(sort, "c.last_name, c.first_name")
    full_query = query + f" ORDER BY {order}"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(full_query, params)
            rows = cur.fetchall()
    # rows: (id, first, last, email, birthday, group_name, created_at)
    # attach phones
    result = []
    with get_connection() as conn:
        with conn.cursor() as cur:
            for r in rows:
                cur.execute(
                    "SELECT STRING_AGG(phone || ' (' || type || ')', ', ' ORDER BY type) "
                    "FROM phones WHERE contact_id = %s", (r[0],)
                )
                phones = (cur.fetchone() or ("",))[0] or ""
                result.append((r[0], # id
                               r[1], # First name
                               r[2], # Last name
                               r[3] or "", # Email (None -> "")
                               str(r[4]) if r[4] else "", # Birthday (date -> string)
                                r[5] or "", # Group name
                                phones, # Phones (aggregated string)
                                str(r[6])[:16] if r[6] else ""))# Created at (trim to date+time)
    return result


def _ask_sort() -> str:
    s = input("Sort by [name/birthday/added] (default=name): ").strip().lower()
    return s if s in ("name", "birthday", "added") else "name"


def filter_by_group():
    print("Available groups: Family, Work, Friend, Other (or any custom group)")
    group = input("Group name: ").strip()
    sort  = _ask_sort()
    base = (
        "SELECT c.id, c.first_name, c.last_name, c.email, c.birthday, g.name, c.created_at "
        "FROM contacts c LEFT JOIN groups g ON g.id = c.group_id "
        "WHERE LOWER(g.name) = LOWER(%s)"
    )
    rows = _fetch_display(base, (group,), sort)
    if rows:
        _print_contacts(rows)
    else:
        print("No contacts in that group.")


def search_by_email():
    term = input("Email search term: ").strip()
    sort = _ask_sort()
    base = (
        "SELECT c.id, c.first_name, c.last_name, c.email, c.birthday, g.name, c.created_at "
        "FROM contacts c LEFT JOIN groups g ON g.id = c.group_id "
        "WHERE LOWER(COALESCE(c.email,'')) LIKE %s"
    )
    # Wrap the term in % wildcards: 'gmail' → '%gmail%'
    rows = _fetch_display(base, (f"%{term.lower()}%",), sort)
    if rows:
        _print_contacts(rows)
    else:
        print("No contacts found.")


def search_all():
    """Use the search_contacts() PL/pgSQL function."""
    term = input("Search (name / email / phone): ").strip()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM search_contacts(%s)", (term,))
            rows = cur.fetchall()
    if rows:
        # id, first, last, email, birthday, group_name, phones
        display = [(r[0], r[1], r[2], r[3] or "", str(r[4]) if r[4] else "",
                    r[5] or "", r[6] or "", "") for r in rows]
        _print_contacts(display,
                        headers=["ID", "First", "Last", "Email", "Birthday", "Group", "Phones", ""])
    else:
        print("No contacts found.")


# paginated

def browse_paginated():
    PAGE = 5 # number of contacts shown per page
    offset = 0 # starts at first page
    sort_map = {"name": "last_name, first_name", "birthday": "birthday NULLS LAST", "added": "created_at"}
    sort = _ask_sort()
    col  = sort_map[sort]

# Get total count once so we can calculate total pages
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM contacts")
            total = cur.fetchone()[0]

    if total == 0:
        print("No contacts in database.")
        return

    while True:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""SELECT c.id, c.first_name, c.last_name, c.email, c.birthday,
                               g.name, c.created_at
                        FROM contacts c LEFT JOIN groups g ON g.id = c.group_id
                        ORDER BY {col}
                        LIMIT %s OFFSET %s""",
                    (PAGE, offset)
                )
                rows = cur.fetchall()

        # attach phones
        display = []
        with get_connection() as conn:
            with conn.cursor() as cur:
                for r in rows:
                    cur.execute(
                        "SELECT STRING_AGG(phone || ' (' || type || ')', ', ' ORDER BY type) "
                        "FROM phones WHERE contact_id = %s", (r[0],)
                    )
                    phones = (cur.fetchone() or ("",))[0] or ""
                    display.append((r[0], r[1], r[2], r[3] or "", str(r[4]) if r[4] else "",
                                    r[5] or "", phones, str(r[6])[:16] if r[6] else ""))
                    
        # Calculate and print current page number
        page_num = offset // PAGE + 1
        total_pages = (total + PAGE - 1) // PAGE
        print(f"\n── Page {page_num}/{total_pages}  (total: {total} contacts) ──")
        _print_contacts(display)

        nav = input("[next/prev/quit]: ").strip().lower()
        if nav == "next":
            if offset + PAGE < total:
                offset += PAGE # advance to next page
            else:
                print("Already on last page.")
        elif nav == "prev":
            if offset > 0:
                offset -= PAGE # go back one page
            else:
                print("Already on first page.")
        elif nav == "quit":
            break


# Phone Managing 

def add_phone_menu():
    name  = input("Contact full name: ").strip()
    phone = input("Phone number     : ").strip()
    ptype = input("Type (home/work/mobile) [mobile]: ").strip() or "mobile"
    with get_connection() as conn:
        with conn.cursor() as cur:
            try:
                # CALL executes a stored procedure (procedures return no value)
                cur.execute("CALL add_phone(%s, %s, %s)", (name, phone, ptype))
                conn.commit()
                print("✓ Phone added.")
            except Exception as e:
                conn.rollback()
                print(f"✗ {e}")


def move_to_group_menu():
    name  = input("Contact full name: ").strip()
    group = input("New group name   : ").strip()
    with get_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("CALL move_to_group(%s, %s)", (name, group))
                conn.commit()
                print("✓ Contact moved.")
            except Exception as e:
                conn.rollback()
                print(f"✗ {e}")


# EXPORT / IMPORT 

def export_json():
    path = input("Output JSON file path [contacts_export.json]: ").strip() or "contacts_export.json"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT c.id, c.first_name, c.last_name, c.email,
                          c.birthday::TEXT, g.name AS group_name, c.created_at::TEXT
                   FROM contacts c LEFT JOIN groups g ON g.id = c.group_id
                   ORDER BY c.last_name, c.first_name"""
            )
            contacts = cur.fetchall()
            result = []
            for row in contacts:
                cid, first, last, email, bday, grp, created = row
                cur.execute(
                    "SELECT phone, type FROM phones WHERE contact_id = %s ORDER BY type", (cid,)
                )
                phones = [{"phone": p[0], "type": p[1]} for p in cur.fetchall()]
                # Build the dict for this contact
                result.append({
                    "first_name": first,
                    "last_name":  last,
                    "email":      email,
                    "birthday":   bday,
                    "group":      grp,
                    "phones":     phones,
                    "created_at": created,
                })
    # Load the entire JSON file into memory as a Python list of dicts
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✓ Exported {len(result)} contacts → {path}")


def import_json():
    path = input("JSON file path: ").strip()
    if not os.path.exists(path):
        print("✗ File not found.")
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    skipped = inserted = overwritten = 0
    with get_connection() as conn:
        with conn.cursor() as cur:
            for c in data:
                # Extract fields from the JSON object (use .get() to avoid KeyError)
                first = c.get("first_name", "").strip()
                last  = c.get("last_name",  "").strip()
                email = c.get("email")
                bday  = _coerce_date(c.get("birthday", ""))
                grp   = c.get("group") or "Other"
                phones = c.get("phones", [])

                # duplicate check
                cur.execute(
                    "SELECT id FROM contacts WHERE LOWER(first_name)=LOWER(%s) AND LOWER(last_name)=LOWER(%s)",
                    (first, last)
                )
                existing = cur.fetchone()

                if existing:
                    choice = input(f"  '{first} {last}' already exists. [skip/overwrite]: ").strip().lower()
                    if choice != "overwrite":
                        skipped += 1
                        continue
                    # Overwrite: update main record and replace all phones
                    gid = _get_or_create_group(cur, grp)
                    cur.execute(
                        "UPDATE contacts SET email=%s, birthday=%s, group_id=%s WHERE id=%s",
                        (email, bday, gid, existing[0])
                    )
                    cur.execute("DELETE FROM phones WHERE contact_id=%s", (existing[0],))
                    for p in phones:
                        cur.execute(
                            "INSERT INTO phones (contact_id, phone, type) VALUES (%s,%s,%s)",
                            (existing[0], p["phone"], p.get("type", "mobile"))
                        )
                    overwritten += 1
                else:
                    gid = _get_or_create_group(cur, grp)
                    cur.execute(
                        "INSERT INTO contacts (first_name,last_name,email,birthday,group_id) "
                        "VALUES (%s,%s,%s,%s,%s) RETURNING id",
                        (first, last, email, bday, gid)
                    )
                    cid = cur.fetchone()[0]
                    for p in phones:
                        cur.execute(
                            "INSERT INTO phones (contact_id, phone, type) VALUES (%s,%s,%s)",
                            (cid, p["phone"], p.get("type", "mobile"))
                        )
                    inserted += 1

            conn.commit()
    print(f"✓ JSON import done – inserted: {inserted}, overwritten: {overwritten}, skipped: {skipped}")


def import_csv():
    """
    Extended CSV importer supporting columns:
      first_name, last_name, email, birthday, group, phone, phone_type
    Multiple rows with the same name create multiple phone entries.
    """
    path = input("CSV file path [contacts.csv]: ").strip() or "contacts.csv"
    if not os.path.exists(path):
        print("✗ File not found.")
        return

    inserted = skipped = phones_added = 0
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows   = list(reader)

    # Group rows by (first_name, last_name) to handle multi-phone entries
    from collections import defaultdict
    grouped = defaultdict(list)
    for row in rows:
        key = (row.get("first_name","").strip(), row.get("last_name","").strip())
        grouped[key].append(row)

    with get_connection() as conn:
        with conn.cursor() as cur:
            for (first, last), group_rows in grouped.items():
                if not first or not last:
                    continue
                sample = group_rows[0]
                email  = sample.get("email","").strip() or None
                bday   = _coerce_date(sample.get("birthday",""))
                grp    = sample.get("group","").strip() or "Other"

                cur.execute(
                    "SELECT id FROM contacts WHERE LOWER(first_name)=LOWER(%s) AND LOWER(last_name)=LOWER(%s)",
                    (first, last)
                )
                existing = cur.fetchone()

                if existing:
                    cid = existing[0]
                    skipped += 1
                else:
                    gid = _get_or_create_group(cur, grp)
                    try:
                        cur.execute(
                            "INSERT INTO contacts (first_name,last_name,email,birthday,group_id) "
                            "VALUES (%s,%s,%s,%s,%s) RETURNING id",
                            (first, last, email, bday, gid)
                        )
                        cid = cur.fetchone()[0]
                        inserted += 1
                    except psycopg2.errors.UniqueViolation:
                        conn.rollback()
                        skipped += 1
                        continue

                for row in group_rows:
                    phone = row.get("phone","").strip()
                    ptype = row.get("phone_type","mobile").strip() or "mobile"
                    if phone:
                        # avoid exact duplicate phone on same contact
                        cur.execute(
                            "SELECT 1 FROM phones WHERE contact_id=%s AND phone=%s", (cid, phone)
                        )
                        if not cur.fetchone():
                            cur.execute(
                                "INSERT INTO phones (contact_id, phone, type) VALUES (%s,%s,%s)",
                                (cid, phone, ptype)
                            )
                            phones_added += 1

            conn.commit()
    print(f"CSV import done – contacts inserted: {inserted}, skipped: {skipped}, phones added: {phones_added}")


# MENU 

MENU = """
╔══════════════════════════════════════════╗
║         PhoneBook  –  TSIS01             ║
╠══════════════════════════════════════════╣
║  1. Browse (paginated)                   ║
║  2. Search (name / email / phone)        ║
║  3. Filter by group                      ║
║  4. Search by email                      ║
║  5. Add contact                          ║
║  6. Update contact                       ║
║  7. Delete contact                       ║
║  8. Add phone to contact                 ║
║  9. Move contact to group                ║
║ 10. Export → JSON                        ║
║ 11. Import ← JSON                        ║
║ 12. Import ← CSV                         ║
║  0. Exit                                 ║
╚══════════════════════════════════════════╝
"""

ACTIONS = {
    "1":  browse_paginated,
    "2":  search_all,
    "3":  filter_by_group,
    "4":  search_by_email,
    "5":  add_contact,
    "6":  update_contact,
    "7":  delete_contact,
    "8":  add_phone_menu,
    "9":  move_to_group_menu,
    "10": export_json,
    "11": import_json,
    "12": import_csv,
}


def main():
    print("Initialising database …")
    try:
        init_db()
    except Exception as e:
        print(f"DB init error: {e}\n  (Continuing – schema may already exist.)")

    while True:
        print(MENU)
        choice = input("Choice: ").strip()
        if choice == "0":
            print("Bye!")
            sys.exit(0)
        action = ACTIONS.get(choice)
        if action:
            try:
                action()
            except Exception as e:
                print(f"✗ Error: {e}")
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()