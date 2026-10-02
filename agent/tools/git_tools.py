from pathlib import Path

from git import Repo, InvalidGitRepositoryError


def create_checkpoint(project_path):
    """
    Create a Git checkpoint before the AI modifies code.
    """

    try:
        repo = Repo(project_path)

    except InvalidGitRepositoryError:

        return {
            "success": False,
            "message": (
                "Project is not a Git repository. "
                "Git checkpoint was skipped."
            ),
            "commit": "",
        }

    if repo.is_dirty():

        repo.git.add(A=True)

        repo.index.commit(
            "AI agent checkpoint before automated fix"
        )

    return {
        "success": True,
        "message": "Git checkpoint created.",
        "commit": repo.head.commit.hexsha,
    }


def rollback_to_checkpoint(project_path, checkpoint):
    """
    Restore project to the checkpoint.
    """

    if not checkpoint:
        return {
            "success": False,
            "message": "No checkpoint available."
        }

    try:

        repo = Repo(project_path)

        repo.git.reset(
            "--hard",
            checkpoint
        )

        return {
            "success": True,
            "message": "Project rolled back to checkpoint."
        }

    except Exception as exc:

        return {
            "success": False,
            "message": f"Rollback failed: {exc}"
        }