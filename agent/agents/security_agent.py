from typing import Any, Dict

from agent.agents.base_agent import BaseAgent
from agent.nodes import patch_review_node


class SecurityAgent(BaseAgent):
    """
    Specialist responsible for reviewing generated patches
    before human approval.
    """

    name = "SECURITY AGENT"
    role = "Patch security and safety review"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self.log("Reviewing patch for security and safety...")

        result = patch_review_node(state)

        self.log("Security review completed.")

        return result