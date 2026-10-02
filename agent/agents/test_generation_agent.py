
from typing import Any, Dict

from agent.agents.base_agent import BaseAgent
from agent.nodes import generate_tests_node


class TestAgent(BaseAgent):
    """
    Specialist responsible for automated test generation.

    Existing Phase 5 test-generation functionality is reused.
    """

    name = "TEST AGENT"
    role = "Automated test generation and evidence collection"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self.log("Generating and validating automated tests...")

        result = generate_tests_node(state)

        self.log("Automated test generation completed.")

        return result
