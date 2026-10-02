from typing import Any, Dict

from agent.agents.base_agent import BaseAgent
from agent.agents.project_agent import ProjectAgent
from agent.agents.error_agent import ErrorAgent
from agent.agents.test_generation_agent import TestAgent
from agent.agents.fix_agent import FixAgent
from agent.agents.security_agent import SecurityAgent
from agent.agents.repair_agent import RepairAgent
from agent.agents.validation_agent import ValidationAgent


class AgentManager(BaseAgent):
    """
    Phase 6 multi-agent coordinator.

    The manager does not perform specialist work itself.
    Instead, it coordinates specialist agents and maintains
    the shared state between them.
    """

    name = "AGENT MANAGER"
    role = "Multi-agent orchestration"

    def __init__(self):
        self.project_agent = ProjectAgent()
        self.error_agent = ErrorAgent()
        self.test_agent = TestAgent()
        self.fix_agent = FixAgent()
        self.security_agent = SecurityAgent()
        self.repair_agent = RepairAgent()
        self.validation_agent = ValidationAgent()

    def run_analysis(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the analysis side of the multi-agent system.

        This stops before human approval.
        """

        self.log("Starting Phase 6 multi-agent analysis.")

        state = self.project_agent.run(state)
        state = self.error_agent.run(state)
        state = self.test_agent.run(state)
        state = self.fix_agent.run(state)
        state = self.security_agent.run(state)

        state["multi_agent_analysis_completed"] = True

        self.log("Multi-agent analysis completed.")

        return state

    def run_repair(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the repair and validation side after human approval.
        """

        self.log("Starting multi-agent repair.")

        state = self.repair_agent.run(state)

        if state.get("patch_error"):
            return state

        state = self.validation_agent.run(state)

        state["multi_agent_repair_completed"] = True

        self.log("Multi-agent repair completed.")

        return state

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Base-agent interface.

        The default operation is analysis because repair requires
        explicit human approval.
        """

        return self.run_analysis(state)