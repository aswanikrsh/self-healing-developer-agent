from agent.graph import build_graph


graph = build_graph()


result = graph.invoke({

    "project_path": "workspace/test_project",

    "error_message": """
TypeError: unsupported operand type(s)
for +: 'int' and 'str'
""",

    "project_structure": "",

    "project_files": {},

    "relevant_files": [],

    "error_analysis": "",

    "root_cause": "",

    "proposed_fix": "",

    "patch": "",

    "changes": [],

    "test_output": "",

    "test_passed": False,

    "approval_required": False,

    "approved": False,

    "status": "starting",

    "iteration": 1,

    "max_iterations": 5,
})


print("\n========== ROOT CAUSE ==========\n")

print(result["root_cause"])


print("\n========== PROPOSED FIX ==========\n")

print(result["proposed_fix"])