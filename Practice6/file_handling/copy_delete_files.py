import shutil
from pathlib import Path


def main() -> None:
    base_dir = Path(__file__).resolve().parent / "data"
    backup_dir = base_dir / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)

    source_file = base_dir / "sample.txt"
    if not source_file.exists():
        source_file.write_text("Auto-created sample file for copy/delete demo.\n", encoding="utf-8")

    # Copy file for backup.
    backup_file = backup_dir / "sample_backup.txt"
    shutil.copy2(source_file, backup_file)
    print(f"Backup created: {backup_file}")

    # Copy again with a second name to demonstrate deletion safely.
    temp_delete_file = backup_dir / "to_delete.txt"
    shutil.copy2(source_file, temp_delete_file)
    print(f"Temporary file created: {temp_delete_file}")

    # Safe delete: check before removing.
    if temp_delete_file.exists() and temp_delete_file.is_file():
        temp_delete_file.unlink()
        print(f"Deleted file safely: {temp_delete_file}")
    else:
        print("No temporary file to delete.")


if __name__ == "__main__":
    main()