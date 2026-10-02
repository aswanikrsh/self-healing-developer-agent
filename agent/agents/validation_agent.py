from typing import Any, Dict

from agent.agents.base_agent import BaseAgent
from agent.nodes import test_runner_node, validation_node


class ValidationAgent(BaseAgent):
    """
    Specialist responsible for running tests and validating
    the repaired project.
    """

    name = "VALIDATION AGENT"
    role = "Test execution and repair validation"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self.log("Running project tests...")

        state = test_runner_node(state)

        self.log("Validating test results...")

        state = validation_node(state)

        self.log("Validation completed.")

        return state