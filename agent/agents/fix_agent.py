from typing import Any, Dict

from agent.agents.base_agent import BaseAgent
from agent.nodes import fix_planning_node


class FixAgent(BaseAgent):
    """
    Specialist responsible for creating the proposed source-code patch.
    """

    name = "FIX AGENT"
    role = "Safe code-fix generation"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self.log("Generating a safe code patch...")

        result = fix_planning_node(state)

        self.log("Fix planning completed.")

        return result