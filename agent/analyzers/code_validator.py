import ast


def validate_python_code(code):
    """
    Check whether generated Python code has valid syntax.
    """

    try:
        ast.parse(code)

        return {
            "valid": True,
            "error": "",
        }

    except SyntaxError as exc:

        return {
            "valid": False,
            "error": (
                f"SyntaxError: {exc.msg} "
                f"at line {exc.lineno}, column {exc.offset}"
            ),
        }