import ast
from pathlib import Path
from typing import Any


# ============================================================
# AST ANALYSIS
# ============================================================

def analyze_python_source(source: str) -> dict[str, Any]:
    """
    Analyze Python source code using the Python AST.

    This function does not execute the code.
    """

    result = {
        "valid": False,
        "error": "",
        "imports": [],
        "functions": [],
        "classes": [],
        "variables": [],
    }

    try:
        tree = ast.parse(source)

    except SyntaxError as exc:

        result["error"] = (
            f"{exc.msg} "
            f"(line {exc.lineno}, column {exc.offset})"
        )

        return result

    imports = set()
    functions = []
    classes = []
    variables = []

    for node in ast.walk(tree):

        # ----------------------------------------------------
        # IMPORTS
        # ----------------------------------------------------

        if isinstance(node, ast.Import):

            for alias in node.names:

                imports.add(alias.name)

        elif isinstance(node, ast.ImportFrom):

            module = node.module or ""

            if module:
                imports.add(module)

        # ----------------------------------------------------
        # FUNCTIONS
        # ----------------------------------------------------

        elif isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ):

            functions.append(
                {
                    "name": node.name,
                    "line": node.lineno,
                    "end_line": getattr(
                        node,
                        "end_lineno",
                        node.lineno,
                    ),
                    "async": isinstance(
                        node,
                        ast.AsyncFunctionDef,
                    ),
                }
            )

        # ----------------------------------------------------
        # CLASSES
        # ----------------------------------------------------

        elif isinstance(node, ast.ClassDef):

            methods = []

            for child in node.body:

                if isinstance(
                    child,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                    ),
                ):

                    methods.append(
                        child.name
                    )

            classes.append(
                {
                    "name": node.name,
                    "line": node.lineno,
                    "end_line": getattr(
                        node,
                        "end_lineno",
                        node.lineno,
                    ),
                    "methods": methods,
                }
            )

        # ----------------------------------------------------
        # TOP-LEVEL VARIABLES
        # ----------------------------------------------------

        elif isinstance(
            node,
            (
                ast.Assign,
                ast.AnnAssign,
            ),
        ):

            targets = []

            if isinstance(node, ast.Assign):

                for target in node.targets:

                    if isinstance(
                        target,
                        ast.Name,
                    ):
                        targets.append(
                            target.id
                        )

            elif isinstance(
                node,
                ast.AnnAssign,
            ):

                if isinstance(
                    node.target,
                    ast.Name,
                ):
                    targets.append(
                        node.target.id
                    )

            variables.extend(targets)

    result["valid"] = True

    result["imports"] = sorted(
        imports
    )

    result["functions"] = functions

    result["classes"] = classes

    result["variables"] = sorted(
        set(variables)
    )

    return result


# ============================================================
# FILE ANALYSIS
# ============================================================

def analyze_python_file(
    file_path: Path,
) -> dict[str, Any]:
    """
    Read and analyze one Python file.
    """

    try:

        source = file_path.read_text(
            encoding="utf-8"
        )

    except UnicodeDecodeError:

        return {
            "valid": False,
            "error": "File is not valid UTF-8 text.",
            "imports": [],
            "functions": [],
            "classes": [],
            "variables": [],
        }

    except Exception as exc:

        return {
            "valid": False,
            "error": str(exc),
            "imports": [],
            "functions": [],
            "classes": [],
            "variables": [],
        }

    return analyze_python_source(
        source
    )


# ============================================================
# FORMAT AST INFORMATION
# ============================================================

def format_python_metadata(
    metadata: dict[str, Any],
) -> str:
    """
    Convert AST metadata into readable text
    for the LLM.
    """

    lines = []

    if not metadata.get("valid"):

        lines.append(
            "AST STATUS: INVALID"
        )

        lines.append(
            f"AST ERROR: {metadata.get('error', '')}"
        )

        return "\n".join(lines)

    lines.append(
        "AST STATUS: VALID"
    )

    # --------------------------------------------------------
    # IMPORTS
    # --------------------------------------------------------

    imports = metadata.get(
        "imports",
        [],
    )

    if imports:

        lines.append(
            "IMPORTS:"
        )

        for item in imports:

            lines.append(
                f"  - {item}"
            )

    # --------------------------------------------------------
    # FUNCTIONS
    # --------------------------------------------------------

    functions = metadata.get(
        "functions",
        [],
    )

    if functions:

        lines.append(
            "FUNCTIONS:"
        )

        for function in functions:

            async_text = (
                "async "
                if function.get("async")
                else ""
            )

            lines.append(
                f"  - {async_text}"
                f"{function['name']} "
                f"(lines "
                f"{function['line']}-"
                f"{function['end_line']})"
            )

    # --------------------------------------------------------
    # CLASSES
    # --------------------------------------------------------

    classes = metadata.get(
        "classes",
        [],
    )

    if classes:

        lines.append(
            "CLASSES:"
        )

        for class_info in classes:

            methods = ", ".join(
                class_info.get(
                    "methods",
                    [],
                )
            )

            lines.append(
                f"  - {class_info['name']} "
                f"(lines "
                f"{class_info['line']}-"
                f"{class_info['end_line']})"
            )

            if methods:

                lines.append(
                    f"    methods: {methods}"
                )

    # --------------------------------------------------------
    # VARIABLES
    # --------------------------------------------------------

    variables = metadata.get(
        "variables",
        [],
    )

    if variables:

        lines.append(
            "TOP-LEVEL VARIABLES:"
        )

        for variable in variables:

            lines.append(
                f"  - {variable}"
            )

    return "\n".join(lines)