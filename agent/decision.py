def should_continue_after_tests(state):

    if state.get("test_passed"):

        return "success"

    if state.get("iteration", 1) >= state.get(
        "max_iterations",
        5,
    ):

        return "rollback"

    return "retry"