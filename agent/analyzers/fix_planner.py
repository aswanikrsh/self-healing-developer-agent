import json
import re

from agent.llm import llm


# ============================================================
# JSON EXTRACTION
# ============================================================

def _extract_json(text):
    """
    Extract JSON from the LLM response.

    Supports:
    1. Plain JSON
    2. Markdown JSON blocks
    3. JSON embedded inside other text
    """

    if not isinstance(text, str):
        text = str(text)

    text = text.strip()

    # --------------------------------------------------------
    # Direct JSON
    # --------------------------------------------------------

    try:
        return json.loads(text)

    except json.JSONDecodeError:
        pass

    # --------------------------------------------------------
    # Markdown JSON block
    # --------------------------------------------------------

    match = re.search(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        text,
        re.DOTALL,
    )

    if match:

        try:
            return json.loads(
                match.group(1)
            )

        except json.JSONDecodeError:
            pass

    # --------------------------------------------------------
    # JSON embedded inside other text
    # --------------------------------------------------------

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1:

        try:
            return json.loads(
                text[start:end + 1]
            )

        except json.JSONDecodeError:
            pass

    return None


# ============================================================
# NORMALIZE WHITESPACE FOR MATCHING ONLY
# ============================================================

def _normalize_for_matching(text):
    """
    Normalize whitespace ONLY for locating AI-generated
    old_code inside the real source.

    The actual source is never modified.

    This handles differences in:

    - line endings
    - tabs
    - spaces
    - trailing whitespace
    - blank lines
    """

    if not isinstance(text, str):
        text = str(text)

    # --------------------------------------------------------
    # Normalize line endings
    # --------------------------------------------------------

    text = text.replace(
        "\r\n",
        "\n",
    )

    text = text.replace(
        "\r",
        "\n",
    )

    # --------------------------------------------------------
    # Normalize tabs
    # --------------------------------------------------------

    text = text.replace(
        "\t",
        "    ",
    )

    # --------------------------------------------------------
    # Remove trailing spaces
    # --------------------------------------------------------

    lines = []

    for line in text.split("\n"):

        lines.append(
            line.rstrip()
        )

    text = "\n".join(lines)

    # --------------------------------------------------------
    # Normalize repeated spaces
    # --------------------------------------------------------

    text = re.sub(
        r"[ ]+",
        " ",
        text,
    )

    # --------------------------------------------------------
    # Normalize repeated blank lines
    # --------------------------------------------------------

    text = re.sub(
        r"\n[ \n]*\n+",
        "\n\n",
        text,
    )

    return text.strip()


# ============================================================
# FIND ALL EXACT MATCHES
# ============================================================

def _find_all_exact_matches(
    source,
    old_code,
):
    """
    Find every exact occurrence of old_code.

    IMPORTANT:

    We do NOT use str.find() only once because that would
    silently select the first occurrence when the same code
    exists multiple times.

    Returning every match allows the safety layer to reject
    ambiguous patches.
    """

    matches = []

    if not isinstance(
        source,
        str,
    ):

        return matches

    if not isinstance(
        old_code,
        str,
    ):

        return matches

    if not old_code:

        return matches

    start = 0

    while True:

        index = source.find(
            old_code,
            start,
        )

        if index == -1:

            break

        matches.append(
            (
                index,
                index + len(old_code),
            )
        )

        start = index + 1

    return matches


# ============================================================
# FIND ALL NORMALIZED SOURCE MATCHES
# ============================================================

def _find_all_normalized_matches(
    source,
    old_code,
):
    """
    Find all source regions matching old_code while allowing
    harmless whitespace differences.

    Returns every candidate instead of silently selecting the
    first candidate.

    This is important for patch safety.
    """

    if not isinstance(
        source,
        str,
    ):

        return []

    if not isinstance(
        old_code,
        str,
    ):

        return []

    if not old_code.strip():

        return []

    source_lines = source.splitlines(
        keepends=True
    )

    old_lines = old_code.splitlines()

    if not old_lines:

        return []

    normalized_old_lines = [
        _normalize_for_matching(line)
        for line in old_lines
    ]

    # --------------------------------------------------------
    # Remove empty lines from the comparison representation.
    # --------------------------------------------------------

    normalized_old_lines = [
        line
        for line in normalized_old_lines
        if line != ""
    ]

    if not normalized_old_lines:

        return []

    matches = []

    # --------------------------------------------------------
    # Search every possible source region.
    # --------------------------------------------------------

    for start in range(
        len(source_lines)
    ):

        collected = []

        end = start

        while (
            end < len(source_lines)
            and len(collected)
            < len(normalized_old_lines)
        ):

            normalized_line = (
                _normalize_for_matching(
                    source_lines[end]
                )
            )

            if normalized_line:

                collected.append(
                    normalized_line
                )

            end += 1

        if collected == normalized_old_lines:

            start_index = sum(
                len(line)
                for line in source_lines[:start]
            )

            end_index = sum(
                len(line)
                for line in source_lines[:end]
            )

            matches.append(
                (
                    start_index,
                    end_index,
                )
            )

    return matches


# ============================================================
# FIND SOURCE REGION SAFELY
# ============================================================

def _find_source_region(
    source,
    old_code,
):
    """
    Find a UNIQUE occurrence of old_code inside source.

    IMPORTANT SECURITY RULE:

    If old_code occurs more than once, this function NEVER
    chooses one automatically.

    Instead it returns an ambiguity error.

    This prevents the agent from modifying the wrong function
    when two functions contain identical code.
    """

    if not isinstance(
        source,
        str,
    ):

        return None

    if not isinstance(
        old_code,
        str,
    ):

        return None

    if not old_code.strip():

        return None

    # ========================================================
    # FIRST: EXACT MATCH
    # ========================================================

    exact_matches = _find_all_exact_matches(
        source,
        old_code,
    )

    # --------------------------------------------------------
    # No exact match
    # --------------------------------------------------------

    if len(exact_matches) == 0:

        exact_matches = []

    # --------------------------------------------------------
    # Exactly one exact match
    # --------------------------------------------------------

    if len(exact_matches) == 1:

        return exact_matches[0]

    # --------------------------------------------------------
    # Multiple exact matches
    # --------------------------------------------------------

    if len(exact_matches) > 1:

        raise ValueError(
            f"Exact old_code occurs "
            f"{len(exact_matches)} times in the source. "
            "The patch is ambiguous."
        )

    # ========================================================
    # SECOND: NORMALIZED MATCH
    # ========================================================

    normalized_matches = (
        _find_all_normalized_matches(
            source,
            old_code,
        )
    )

    # --------------------------------------------------------
    # No normalized match
    # --------------------------------------------------------

    if len(normalized_matches) == 0:

        return None

    # --------------------------------------------------------
    # Exactly one normalized match
    # --------------------------------------------------------

    if len(normalized_matches) == 1:

        return normalized_matches[0]

    # --------------------------------------------------------
    # Multiple normalized matches
    # --------------------------------------------------------

    raise ValueError(
        f"Normalized old_code matches "
        f"{len(normalized_matches)} source regions. "
        "The patch is ambiguous."
    )


# ============================================================
# BUILD EXACT PATCH FROM AI PATCH
# ============================================================

def _build_exact_patch(
    patch,
    project_files,
):
    """
    Convert the AI-generated patch into a safe patch.

    The AI-generated:

        file
        new_code
        reason

    are preserved.

    The AI-generated old_code is used only to locate the
    corresponding region.

    The final old_code comes directly from the actual source.
    """

    filename = patch[
        "file"
    ]

    ai_old_code = patch[
        "old_code"
    ]

    new_code = patch[
        "new_code"
    ]

    reason = patch[
        "reason"
    ]

    # --------------------------------------------------------
    # File must exist.
    # --------------------------------------------------------

    if filename not in project_files:

        raise ValueError(
            f"Generated patch references file "
            f"'{filename}', but that file is not present "
            "in the current project context."
        )

    current_source = project_files[
        filename
    ]

    # --------------------------------------------------------
    # Find UNIQUE source region.
    # --------------------------------------------------------

    region = _find_source_region(
        current_source,
        ai_old_code,
    )

    if region is None:

        raise ValueError(
            "The AI-generated old_code could not be matched "
            "to the current project source."
        )

    start_index, end_index = region

    # --------------------------------------------------------
    # Extract EXACT source.
    # --------------------------------------------------------

    exact_old_code = current_source[
        start_index:end_index
    ]

    if not exact_old_code.strip():

        raise ValueError(
            "The extracted source region is empty."
        )

    # --------------------------------------------------------
    # Final exact occurrence check.
    # --------------------------------------------------------

    occurrences = current_source.count(
        exact_old_code
    )

    if occurrences != 1:

        raise ValueError(
            f"Matched source region occurs "
            f"{occurrences} times in '{filename}'. "
            "Refusing ambiguous patch."
        )

    # --------------------------------------------------------
    # Return canonical patch.
    # --------------------------------------------------------

    return {
        "file": filename,
        "old_code": exact_old_code,
        "new_code": new_code,
        "reason": reason,
    }


# ============================================================
# VALIDATE FINAL PATCH AGAINST CURRENT SOURCE
# ============================================================

def _validate_patch_against_source(
    patch,
    project_files,
):
    """
    Verify that the final locally constructed old_code
    exists exactly once in the CURRENT project source.
    """

    filename = patch[
        "file"
    ]

    old_code = patch[
        "old_code"
    ]

    # --------------------------------------------------------
    # File must exist.
    # --------------------------------------------------------

    if filename not in project_files:

        return (
            False,
            f"Generated patch references file '{filename}', "
            "but that file is not present in the current "
            "project context.",
        )

    current_source = project_files[
        filename
    ]

    # --------------------------------------------------------
    # Exact substring check.
    # --------------------------------------------------------

    occurrences = current_source.count(
        old_code
    )

    if occurrences == 0:

        return (
            False,
            "Generated old_code does not exactly match the "
            f"current contents of '{filename}'.",
        )

    if occurrences > 1:

        return (
            False,
            f"Generated old_code occurs {occurrences} times "
            f"in '{filename}'. The patch is ambiguous.",
        )

    return (
        True,
        "Patch matches the current project source.",
    )


# ============================================================
# PATCH STRUCTURE VALIDATION
# ============================================================

def _validate_patch_structure(
    patch,
):
    """
    Validate basic patch structure and field types.
    """

    if not isinstance(
        patch,
        dict,
    ):

        raise ValueError(
            "Generated patch must be a dictionary."
        )

    required = [
        "file",
        "old_code",
        "new_code",
        "reason",
    ]

    for field in required:

        if field not in patch:

            raise ValueError(
                f"Generated patch is missing: {field}"
            )

    # --------------------------------------------------------
    # Field types
    # --------------------------------------------------------

    if not isinstance(
        patch["file"],
        str,
    ):

        raise ValueError(
            "Patch field 'file' must be a string."
        )

    if not isinstance(
        patch["old_code"],
        str,
    ):

        raise ValueError(
            "Patch field 'old_code' must be a string."
        )

    if not isinstance(
        patch["new_code"],
        str,
    ):

        raise ValueError(
            "Patch field 'new_code' must be a string."
        )

    if not isinstance(
        patch["reason"],
        str,
    ):

        raise ValueError(
            "Patch field 'reason' must be a string."
        )

    # --------------------------------------------------------
    # Empty values
    # --------------------------------------------------------

    if not patch[
        "file"
    ].strip():

        raise ValueError(
            "Generated patch contains an empty file path."
        )

    if not patch[
        "old_code"
    ].strip():

        raise ValueError(
            "Generated patch contains empty old_code."
        )

    if not patch[
        "new_code"
    ].strip():

        raise ValueError(
            "Generated patch contains empty new_code."
        )


# ============================================================
# PATCH FILE SAFETY
# ============================================================

def _validate_patch_file_safety(
    filename,
):
    """
    Perform local path safety validation before returning
    the patch.
    """

    if not isinstance(
        filename,
        str,
    ):

        raise ValueError(
            "Patch filename must be a string."
        )

    normalized_filename = filename.replace(
        "\\",
        "/",
    )

    file_parts = normalized_filename.split(
        "/"
    )

    # --------------------------------------------------------
    # Parent directory traversal
    # --------------------------------------------------------

    if ".." in file_parts:

        raise ValueError(
            "Patch attempts to access a parent directory."
        )

    # --------------------------------------------------------
    # Protected paths
    # --------------------------------------------------------

    protected_paths = {
        ".git",
        ".env",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
    }

    for part in file_parts:

        if part in protected_paths:

            raise ValueError(
                f"Patch attempts to modify a protected "
                f"path: {filename}"
            )

    # --------------------------------------------------------
    # Protected filenames
    # --------------------------------------------------------

    protected_files = {
        "settings.py",
        "manage.py",
        "requirements.txt",
    }

    basename = file_parts[-1]

    if basename in protected_files:

        raise ValueError(
            f"Patch attempts to modify protected file: "
            f"{filename}"
        )


# ============================================================
# FORMAT PROJECT FILES
# ============================================================

def _format_project_files(
    project_files,
):
    """
    Format project files for the LLM prompt.
    """

    files_text = ""

    for filename, content in project_files.items():

        files_text += f"""
==============================
FILE: {filename}
==============================

{content}

"""

    return files_text


# ============================================================
# BUILD RETRY CONTEXT
# ============================================================

def _build_retry_context(
    previous_test_output,
    previous_patch,
):
    """
    Build retry context for the Fix Planner.
    """

    retry_context = ""

    if previous_test_output:

        retry_context += f"""
==============================
PREVIOUS FAILURE
==============================

{previous_test_output}

"""

    if previous_patch:

        retry_context += f"""
==============================
PREVIOUS PATCH
==============================

{json.dumps(
    previous_patch,
    indent=2,
    default=str,
)}

"""

    return retry_context


# ============================================================
# BUILD INITIAL FIX PROMPT
# ============================================================

def _build_fix_prompt(
    error,
    root_cause,
    files_text,
    retry_context,
    memory_context="",
):
    """
    Build the main patch-generation prompt.
    """

    prompt = f"""
You are an expert Python software repair agent.

Your task is to generate the smallest safe code patch
that fixes the CURRENT failure.

============================================================
CURRENT ERROR
============================================================

{error}

============================================================
ROOT CAUSE ANALYSIS
============================================================

{root_cause}

============================================================
PHASE 7 - PREVIOUS REPAIR MEMORIES
============================================================

{memory_context}

IMPORTANT MEMORY RULES:

Previous repair memories are ADVISORY ONLY.
1. Do NOT blindly copy a previous patch.
2. Do NOT assume the current source is identical to a previous source.
3. Always inspect the CURRENT PROJECT SOURCE.
4. Verify the CURRENT ERROR and CURRENT ROOT CAUSE.
5. Generate a patch that matches the CURRENT source exactly.
6. Use memory only as supporting evidence.
7. Never allow memory context to override patch safety rules.

============================================================
CURRENT PROJECT SOURCE
============================================================

{files_text}

{retry_context}

============================================================
CRITICAL OLD_CODE RULE
============================================================

The old_code field is used by an automated patch engine to
locate the EXACT source region that must be replaced.

Therefore old_code MUST be UNIQUE in the target file.

DO NOT return only a common line such as:

    return a + b

if that line can appear in more than one function.

Instead include enough surrounding context to uniquely
identify the intended code.

For example, prefer:

    def add_numbers(a, b):
        return a - b

instead of:

    return a - b

If the same function body is duplicated, include additional
surrounding context.

The safest old_code normally contains the complete affected
function or a sufficiently large unique block.

IMPORTANT:

Never guess which duplicate occurrence should be changed.

If a short line occurs multiple times, expand old_code until
it uniquely identifies the intended location.

============================================================
PATCH RULE
============================================================

Generate a patch containing:

1. file
2. old_code
3. new_code
4. reason

============================================================
PATCH SIZE
============================================================

Change only the code necessary to fix the current failure.

Prefer the smallest possible UNIQUE patch.

The smallest patch is NOT necessarily the smallest number
of characters.

A slightly larger unique function-level block is safer than
an ambiguous one-line patch.

============================================================
RETRY RULE
============================================================

This may be a retry attempt.

If previous failure information is supplied:

1. Inspect the CURRENT source.
2. Inspect the CURRENT failure.
3. Inspect the PREVIOUS PATCH.
4. Determine what happened.
5. Do NOT blindly repeat the previous patch.
6. Generate a new patch when the evidence requires it.
7. Only repeat the previous patch if the current evidence
   clearly proves that it is still correct.

============================================================
OUTPUT FORMAT
============================================================

Return ONLY valid JSON.

Required format:

{{
    "file": "relative/path/to/file.py",
    "old_code": "unique existing code that needs to be replaced",
    "new_code": "replacement code",
    "reason": "short explanation"
}}

============================================================
RULES
============================================================

1. The file MUST exist in the supplied project source.

2. old_code MUST uniquely identify the actual code that
   needs replacement.

3. old_code MUST contain enough surrounding context to
   distinguish the target from duplicate code.

4. Prefer a complete affected function when necessary.

5. new_code must contain the correct repair.

6. Change the smallest possible UNIQUE code region.

7. Do not modify unrelated files.

8. Do not modify tests.

9. Do not remove tests.

10. Do not add dependencies.

11. Do not change database schema.

12. Do not invent files.

13. Do not include markdown.

14. Return JSON only.

15. Do not blindly repeat a failed patch.

16. The patch must address the CURRENT failure.

17. Do not modify tests to hide the problem.

18. Do not modify configuration unless necessary.

19. Prefer modifying one file.

20. Preserve the existing program structure unless the
    current failure requires a structural change.

21. If a candidate old_code appears multiple times, expand
    it with surrounding function/class context.

22. Never rely on the patch engine to choose between
    duplicate occurrences.
"""

    return prompt


# ============================================================
# BUILD REGENERATION PROMPT
# ============================================================

def _build_regeneration_prompt(
    error,
    root_cause,
    files_text,
    previous_test_output,
    rejected_patch,
    rejection_reason,
    attempt_number,
    memory_context="",
):
    """
    Build a stronger prompt after a patch has been rejected.

    Each regeneration attempt explicitly tells the model why
    the previous patch was unsafe.
    """

    prompt = f"""
You are repairing a Python project.

This is PATCH REGENERATION ATTEMPT {attempt_number}.

The previous AI-generated patch was rejected because the
patch engine could not identify a UNIQUE source region.

You MUST generate a safer patch.

============================================================
CURRENT PROJECT SOURCE
============================================================

{files_text}

============================================================
CURRENT ERROR
============================================================

{error}

============================================================
ROOT CAUSE
============================================================

{root_cause}

============================================================
PHASE 7 - PREVIOUS REPAIR MEMORIES
============================================================

{memory_context}

Memory is advisory only. Never blindly reuse a previous patch.
Always verify the CURRENT source, CURRENT error, and CURRENT root cause.

============================================================
PREVIOUS TEST OUTPUT
============================================================

{previous_test_output}

============================================================
PREVIOUS PATCH
============================================================

{json.dumps(
    rejected_patch,
    indent=2,
    default=str,
)}

============================================================
PATCH REJECTION REASON
============================================================

{rejection_reason}

============================================================
CRITICAL REQUIREMENT
============================================================

The previous old_code was ambiguous or could not be safely
matched.

DO NOT return the same short line again.

For example, if:

    return a + b

appears more than once, DO NOT use:

    return a + b

as old_code.

Instead use enough context, such as:

    def add_numbers(a, b):
        return a - b

or another uniquely identifying block from the CURRENT
SOURCE.

If necessary, include the COMPLETE affected function.

The patch engine will reject any old_code that matches more
than one region.

NEVER ask the patch engine to guess which duplicate occurrence
is intended.

============================================================
PATCH REQUIREMENTS
============================================================

The patch must contain:

1. file
2. old_code
3. new_code
4. reason

The file must exist.

The old_code must exist in the CURRENT source.

The old_code must identify exactly ONE region.

The new_code must be the correct repair.

Do not modify tests.

Do not modify unrelated code.

Do not add dependencies.

Do not change configuration unless necessary.

Do not change database schema.

============================================================
OUTPUT
============================================================

Return ONLY valid JSON.

{{
    "file": "relative/path/to/file.py",
    "old_code": "UNIQUE existing source region",
    "new_code": "replacement code",
    "reason": "short explanation"
}}

Do not include markdown.

Do not include explanations outside JSON.
"""

    return prompt


# ============================================================
# GENERATE AND VALIDATE ONE PATCH
# ============================================================

def _generate_and_validate_patch(
    prompt,
    project_files,
):
    """
    Ask the LLM for one patch and locally validate it.

    Returns:

        final_patch

    or raises an exception.
    """

    response = llm.invoke(
        prompt
    )

    raw = response.content

    print()
    print("=" * 60)
    print("FIX PLANNER - RAW LLM RESPONSE")
    print("=" * 60)
    print(raw)
    print("=" * 60)

    # --------------------------------------------------------
    # Parse JSON
    # --------------------------------------------------------

    patch = _extract_json(
        raw
    )

    if patch is None:

        raise ValueError(
            "LLM did not return valid JSON patch data."
        )

    # --------------------------------------------------------
    # Validate structure
    # --------------------------------------------------------

    _validate_patch_structure(
        patch
    )

    # --------------------------------------------------------
    # Validate filename safety
    # --------------------------------------------------------

    _validate_patch_file_safety(
        patch["file"]
    )

    # --------------------------------------------------------
    # Build exact patch
    # --------------------------------------------------------

    final_patch = _build_exact_patch(
        patch,
        project_files,
    )

    # --------------------------------------------------------
    # Validate against current source
    # --------------------------------------------------------

    valid_source, source_message = (
        _validate_patch_against_source(
            final_patch,
            project_files,
        )
    )

    if not valid_source:

        raise ValueError(
            "Final patch failed source validation: "
            f"{source_message}"
        )

    return final_patch


# ============================================================
# FIX PLANNER
# ============================================================

def create_fix_plan(
    error,
    root_cause,
    project_files,
    previous_test_output="",
    previous_patch=None,
    memory_context="",
):
    """
    Generate a structured code patch.

    Features preserved:

    - JSON extraction
    - whitespace-insensitive matching
    - exact source extraction
    - patch structure validation
    - source validation
    - protected path validation
    - previous test context
    - previous patch context
    - LLM regeneration
    - retry-aware repair planning
    - Phase 3 project intelligence
    - Phase 4 patch safety
    - Phase 5 generated-test context
    - Phase 7 semantic repair-memory context
    - Previous successful repair context is advisory only

    Improvements:

    - Detects ALL duplicate matches.
    - Never silently selects the first duplicate.
    - Uses stronger unique-context instructions.
    - Allows up to 3 LLM patch-generation attempts.
    - Gives the LLM the exact rejection reason.
    """

    if previous_patch is None:

        previous_patch = {}

    if memory_context is None:
        memory_context = "No previous repair memories were found."

    # ========================================================
    # PROJECT SOURCE
    # ========================================================

    files_text = _format_project_files(
        project_files
    )

    # ========================================================
    # RETRY CONTEXT
    # ========================================================

    retry_context = _build_retry_context(
        previous_test_output,
        previous_patch,
    )

    # ========================================================
    # FIRST PROMPT
    # ========================================================

    prompt = _build_fix_prompt(
        error,
        root_cause,
        files_text,
        retry_context,
        memory_context,
    )

    # ========================================================
    # MULTI-ATTEMPT PATCH GENERATION
    # ========================================================

    max_generation_attempts = 3

    last_error = None

    current_prompt = prompt

    for attempt in range(
        1,
        max_generation_attempts + 1,
    ):

        print()
        print("=" * 60)
        print(
            "FIX PLANNING - GENERATION ATTEMPT",
            attempt,
            "/",
            max_generation_attempts,
        )
        print("=" * 60)

        try:

            final_patch = (
                _generate_and_validate_patch(
                    current_prompt,
                    project_files,
                )
            )

            # ------------------------------------------------
            # SUCCESS
            # ------------------------------------------------

            print()
            print("=" * 60)
            print("PATCH GENERATION SUCCESSFUL")
            print("=" * 60)
            print(
                "File:",
                final_patch["file"],
            )
            print(
                "Reason:",
                final_patch["reason"],
            )
            print("=" * 60)

            return final_patch

        except Exception as generation_error:

            last_error = generation_error

            print()
            print("=" * 60)
            print("PATCH GENERATION ATTEMPT FAILED")
            print("=" * 60)
            print(
                type(generation_error).__name__
            )
            print(
                generation_error
            )
            print("=" * 60)

            # ------------------------------------------------
            # If this was the final attempt, stop.
            # ------------------------------------------------

            if attempt >= max_generation_attempts:

                raise ValueError(
                    "LLM generated a patch that could not be "
                    "matched safely to the current source "
                    f"after {max_generation_attempts} "
                    "generation attempts. "
                    f"Last validation error: "
                    f"{generation_error}"
                )

            # ------------------------------------------------
            # Get the rejected patch when possible.
            # ------------------------------------------------
            #
            # We cannot always access the exact parsed patch
            # here because validation may fail before it is
            # returned. Therefore we provide the original
            # previous patch as context when available.
            # ------------------------------------------------

            rejected_patch = (
                previous_patch
                if previous_patch
                else {}
            )

            # ------------------------------------------------
            # Stronger regeneration prompt.
            # ------------------------------------------------

            current_prompt = (
                _build_regeneration_prompt(
                    error=error,
                    root_cause=root_cause,
                    files_text=files_text,
                    previous_test_output=(
                        previous_test_output
                    ),
                    rejected_patch=rejected_patch,
                    rejection_reason=str(
                        generation_error
                    ),
                    attempt_number=attempt + 1,
                    memory_context=memory_context,
                )
            )

    # ========================================================
    # SAFETY FALLBACK
    # ========================================================

    raise ValueError(
        "Patch generation failed unexpectedly. "
        f"Last error: {last_error}"
    )
