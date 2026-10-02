from pathlib import Path


def read_file(file_path):
    path = Path(file_path)

    if not path.exists():
        return f"File does not exist: {file_path}"

    if not path.is_file():
        return f"Not a file: {file_path}"

    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"Unable to decode file: {file_path}"
    except Exception as exc:
        return f"Unable to read file: {exc}"


def write_file(file_path, content):
    path = Path(file_path)

    path.write_text(
        content,
        encoding="utf-8"
    )

    return f"Updated: {file_path}"