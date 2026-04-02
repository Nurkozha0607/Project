from pathlib import Path


def main() -> None:
    base_dir = Path(__file__).resolve().parent / "data"
    base_dir.mkdir(exist_ok=True)

    sample_file = base_dir / "sample.txt"

    # Mode 'w': create/truncate and write initial content.
    with sample_file.open("w", encoding="utf-8") as f:
        f.write("Line 1: Python file handling\n")
        f.write("Line 2: Mode w overwrites content\n")

    # Mode 'a': append without removing existing content.
    with sample_file.open("a", encoding="utf-8") as f:
        f.write("Line 3: Added with append mode\n")

    # Mode 'x': create only if file does not exist.
    exclusive_file = base_dir / "created_once.txt"
    if not exclusive_file.exists():
        with exclusive_file.open("x", encoding="utf-8") as f:
            f.write("This file was created using mode x.\n")
    else:
        print(f"Skipped mode x because {exclusive_file.name} already exists.")

    print(f"Wrote and appended data in: {sample_file}")
    print(f"Created (or kept) file: {exclusive_file}")


if __name__ == "__main__":
    main()