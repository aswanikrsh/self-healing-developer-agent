from pathlib import Path


def list_project_files(project_path):

    path = Path(project_path)

    files = []

    for file in path.rglob("*"):

        if file.is_file():

            if ".git" not in file.parts:
                files.append(str(file))

    return files


def read_file(file_path):

    path = Path(file_path)

    try:

        return path.read_text(
            encoding="utf-8"
        )

    except Exception as e:

        return f"Unable to read file: {e}"