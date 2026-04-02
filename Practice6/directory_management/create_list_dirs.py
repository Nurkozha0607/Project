import os
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent / "management"

    # os.mkdir for a single level directory.
    single_dir = root / "single_level"
    if not root.exists():
        root.mkdir(parents=True)
    if not single_dir.exists():
        os.mkdir(single_dir)

    # os.makedirs for nested directories.
    nested_dir = root / "nested" / "level1" / "level2"
    os.makedirs(nested_dir, exist_ok=True)

    print("Current working directory before chdir:")
    print(os.getcwd())

    os.chdir(root)
    print("Current working directory after chdir:")
    print(os.getcwd())

    print("Contents of workspace (os.listdir):")
    print(os.listdir("."))

    # os.rmdir removes only empty directories.
    removable_dir = root / "remove_me"
    removable_dir.mkdir(exist_ok=True)
    os.rmdir(removable_dir)
    print(f"Removed empty directory: {removable_dir.name}")


if __name__ == "__main__":
    main()