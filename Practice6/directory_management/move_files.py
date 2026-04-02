import shutil
from pathlib import Path


def find_by_extension(root: Path, extension: str) -> list[Path]:
    return sorted(root.rglob(f"*{extension}"))


def main() -> None:
    base = Path(__file__).resolve().parent / "management_move"
    source_dir = base / "source"
    destination_dir = base / "destination"

    source_dir.mkdir(parents=True, exist_ok=True)
    destination_dir.mkdir(parents=True, exist_ok=True)

    sample_txt = source_dir / "notes.txt"
    sample_py = source_dir / "script.py"
    sample_txt.write_text("Notes file for move/copy demo.\n", encoding="utf-8")
    sample_py.write_text("print('hello from script')\n", encoding="utf-8")

    # Copy file from source to destination.
    copied_file = destination_dir / "notes_copy.txt"
    shutil.copy2(sample_txt, copied_file)

    # Move file from source to destination.
    moved_file = destination_dir / "script_moved.py"
    shutil.move(str(sample_py), str(moved_file))

    print("Source contents:", [p.name for p in sorted(source_dir.iterdir())])
    print("Target contents:", [p.name for p in sorted(destination_dir.iterdir())])

    py_files = find_by_extension(base, ".py")
    print("Found .py files:")
    for path in py_files:
        print(path)


if __name__ == "__main__":
    main()
