from typing import Any, Dict

from agent.agents.base_agent import BaseAgent
from agent.nodes import project_analysis_node


class ProjectAgent(BaseAgent):
    """
    Specialist responsible for understanding the target project.

    Existing Phase 3 project intelligence is reused here.
    """

    name = "PROJECT AGENT"
    role = "Project structure and dependency analysis"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self.log("Analyzing project structure and relevant files...")

        result = project_analysis_node(state)

        self.log("Project analysis completed.")

        return result