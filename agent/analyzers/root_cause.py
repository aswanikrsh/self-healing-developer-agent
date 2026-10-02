from agent.llm import llm


def find_root_cause(error, project_structure):

    prompt = f"""
You are a senior Python debugging engineer.

Project:

{project_structure}

Error:

{error}

Determine the most likely root cause.

Return:

ROOT CAUSE:
RELEVANT FILE:
RELEVANT CODE:
REASON:
CONFIDENCE:
"""

    response = llm.invoke(prompt)

    return response.content