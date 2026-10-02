from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    """
    Base class for all Phase 6 specialist agents.

    Each specialist agent receives the shared state and returns
    updates that can be merged back into the LangGraph state.
    """

    name = "BaseAgent"
    role = "Generic agent"

    @abstractmethod
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's responsibility.

        Parameters
        ----------
        state:
            Current shared AgentState represented as a dictionary.

        Returns
        -------
        dict
            State updates produced by this agent.
        """
        raise NotImplementedError

    def log(self, message: str) -> None:
        print()
        print("=" * 60)
        print(f"{self.name}")
        print("=" * 60)
        print(message)