from pathlib import Path

from agent.security.security_rules import (
    security_scan,
)


def review_patch(project_path, patch):
    """
    Review an AI-generated patch before approval.
    """

    if not isinstance(patch, dict):

        return {
            "approved_for_review": False,
            "risk_level": "critical",
            "summary": "Patch is not a valid dictionary.",
            "findings": [
                "Patch must be a dictionary."
            ],
            "warnings": [],
        }

    required_fields = [
        "file",
        "old_code",
        "new_code",
    ]

    missing = [
        field
        for field in required_fields
        if field not in patch
    ]

    if missing:

        return {
            "approved_for_review": False,
            "risk_level": "critical",
            "summary": "Patch is missing required fields.",
            "findings": [
                f"Missing field: {field}"
                for field in missing
            ],
            "warnings": [],
        }

    security_result = security_scan(
        project_path,
        patch,
    )

    file_name = patch["file"]

    summary = (
        f"Patch modifies '{file_name}'. "
        f"Risk level: {security_result['risk_level']}."
    )

    if security_result["risk_level"] == "critical":

        summary += (
            " Automatic application is blocked."
        )

    elif security_result["risk_level"] == "high":

        summary += (
            " Human review is required."
        )

    else:

        summary += (
            " Patch passed automated security checks."
        )

    return {
        "approved_for_review": security_result["safe"],
        "risk_level": security_result["risk_level"],
        "summary": summary,
        "findings": security_result["findings"],
        "warnings": security_result["warnings"],
    }


def format_patch_review(review):
    """
    Convert patch review information into
    human-readable text for the UI/report.
    """

    lines = []

    lines.append("PATCH SECURITY REVIEW")
    lines.append("=" * 60)

    lines.append(
        f"Risk Level: {review.get('risk_level', 'unknown').upper()}"
    )

    lines.append(
        f"Summary: {review.get('summary', '')}"
    )

    findings = review.get("findings", [])

    if findings:

        lines.append("")
        lines.append("SECURITY FINDINGS:")

        for finding in findings:

            if isinstance(finding, dict):

                lines.append(
                    f"- [{finding.get('severity', 'unknown').upper()}] "
                    f"{finding.get('message', '')}"
                )

            else:

                lines.append(
                    f"- {finding}"
                )

    warnings = review.get("warnings", [])

    if warnings:

        lines.append("")
        lines.append("WARNINGS:")

        for warning in warnings:

            if isinstance(warning, dict):

                lines.append(
                    f"- [{warning.get('severity', 'unknown').upper()}] "
                    f"{warning.get('message', '')}"
                )

            else:

                lines.append(
                    f"- {warning}"
                )

    return "\n".join(lines)