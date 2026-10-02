from agent.llm import llm


def analyze_error(
    error,
    project_structure,
    project_files,
    previous_test_output="",
    previous_patch=None,
):
    """
    Analyze the current project failure.

    During retry attempts, the model receives:

    - previous test output
    - previous patch

    This allows it to understand why the previous
    repair failed.
    """

    if previous_patch is None:
        previous_patch = {}

    # ========================================================
    # BUILD SOURCE CONTEXT
    # ========================================================

    files_text = ""

    for filename, content in project_files.items():

        files_text += f"""
==============================
FILE: {filename}
==============================

{content}

"""

    # ========================================================
    # RETRY CONTEXT
    # ========================================================

    retry_context = ""

    if previous_test_output:

        retry_context += f"""
==============================
PREVIOUS TEST FAILURE
==============================

{previous_test_output}

"""

    if previous_patch:

        retry_context += f"""
==============================
PREVIOUS PATCH
==============================

{previous_patch}

"""

    # ========================================================
    # PROMPT
    # ========================================================

    prompt = f"""
You are a senior Python debugging engineer.

Your task is to analyze the CURRENT failure
in a software project.

You must use the supplied source code as evidence.

PROJECT STRUCTURE:

{project_structure}

SOURCE CODE:

{files_text}

CURRENT ERROR:

{error}

{retry_context}

IMPORTANT:

This may be a retry attempt.

If a previous repair failed:

1. Do NOT blindly repeat the previous fix.
2. Carefully inspect the new test failure.
3. Inspect the current source code.
4. Determine whether the previous patch created a new problem.
5. Determine what still needs to be fixed.
6. Prefer the smallest safe change.

Return the following sections:

ROOT CAUSE:
RELEVANT FILE:
RELEVANT FUNCTION:
PROBLEMATIC CODE:
EXPLANATION:
CONFIDENCE:

RULES:

1. Only mention files that actually exist.
2. Do not invent code.
3. Use the provided source code as evidence.
4. Consider the latest test output.
5. Consider the previous patch if one exists.
6. Do not assume that the previous patch was correct.
7. Do not propose a solution yet.
8. Focus on identifying the actual current failure.
"""

    response = llm.invoke(prompt)

    return response.content