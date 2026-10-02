from datetime import datetime


def create_audit_event(
    event,
    session_id=None,
    iteration=None,
    details=None,
):
    """
    Create a structured security/audit event.

    This is intentionally kept as a dictionary for Phase 4.
    It can later be persisted in a database model.
    """

    return {
        "timestamp": datetime.now().isoformat(),
        "event": event,
        "session_id": session_id,
        "iteration": iteration,
        "details": details or {},
    }


def add_audit_event(state, event, details=None):
    """
    Append an audit event to agent state.
    """

    audit_log = state.setdefault(
        "audit_log",
        []
    )

    audit_log.append(
        create_audit_event(
            event=event,
            session_id=state.get("session_id"),
            iteration=state.get("iteration"),
            details=details,
        )
    )

    state["audit_log"] = audit_log

    return state