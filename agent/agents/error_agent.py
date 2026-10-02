from typing import Any, Dict

from agent.agents.base_agent import BaseAgent
from agent.nodes import error_analysis_node


class ErrorAgent(BaseAgent):
    """
    Specialist responsible for traceback and root-cause analysis.

    Existing Phase 3/4 error analysis is reused.
    """

    name = "ERROR AGENT"
    role = "Error and root-cause analysis"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self.log("Analyzing error and identifying root cause...")

        result = error_analysis_node(state)

        self.log("Error analysis completed.")

        return result