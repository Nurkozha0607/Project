from pathlib import Path


def main() -> None:
    base_dir = Path(__file__).resolve().parent / "data"
    sample_file = base_dir / "sample.txt"

    if not sample_file.exists():
        print("sample.txt does not exist. Run write_files.py first.")
        return

    # Mode 'r': read file content in different ways.
    with sample_file.open("r", encoding="utf-8") as f:
        all_content = f.read()
    print("Using read():")
    print(all_content)

    with sample_file.open("r", encoding="utf-8") as f:
        first_line = f.readline().strip()
        second_line = f.readline().strip()
    print("Using readline() twice:")
    print(first_line)
    print(second_line)

    with sample_file.open("r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines()]
    print("Using readlines():")
    print(lines)


if __name__ == "__main__":
    main()