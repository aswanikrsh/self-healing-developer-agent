from typing import Any, Dict

from agent.agents.base_agent import BaseAgent
from agent.nodes import checkpoint_node, apply_patch_node


class RepairAgent(BaseAgent):
    """
    Specialist responsible for safely applying an approved patch.

    A Git checkpoint is created before the patch is applied.
    """

    name = "REPAIR AGENT"
    role = "Checkpoint creation and patch application"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self.log("Creating Git checkpoint...")

        state = checkpoint_node(state)

        if state.get("patch_error"):
            self.log(
                f"Checkpoint failed: {state.get('patch_error')}"
            )
            return state

        self.log("Applying approved patch...")

        state = apply_patch_node(state)

        self.log("Repair operation completed.")

        return state