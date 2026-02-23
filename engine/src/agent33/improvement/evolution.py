"""Self-Evolution service to generate heuristic process improvements via local Git."""

from __future__ import annotations

import logging
import os
import subprocess
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ImprovementProposal(BaseModel):
    """Data model representing a proposed self-evolution change."""

    proposal_id: str
    title: str
    description: str
    target_component: str
    proposed_patch: str | None = None
    created_at: datetime


class EvolutionEngine:
    """Heuristic engine to formulate and execute self-improvement PRs locally."""

    def __init__(self, workspace_root: str = "/app") -> None:
        # Defaulting to /app for Docker, can be overridden for local Windows
        self._workspace_root = os.environ.get("AGENT33_WORKSPACE", workspace_root)

    def formulate_improvement(self, context: str, metric_id: str) -> ImprovementProposal:
        """Formulate a heuristic improvement based on declining metrics or recon data."""
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        proposal_id = f"evolve-{metric_id}-{timestamp}"

        # In a fully autonomous loop, we would call an LLM here to generate the patch
        # based on context. For this baseline, we generate a mock safe patch structure.
        return ImprovementProposal(
            proposal_id=proposal_id,
            title=f"Autonomous Improvement: Optimize {metric_id}",
            description=f"Automated PR generated from context: {context}",
            target_component="core_system",
            proposed_patch="""# Simulated optimization patch
def optimized_func():
    pass
""",
            created_at=datetime.now(UTC)
        )

    def execute_git_workflow(self, proposal: ImprovementProposal) -> dict[str, Any]:
        """Create a local branch, commit the proposed patch, and simulate a PR."""
        branch_name = f"auto-evolve/{proposal.proposal_id}"

        try:
            # We execute this inside the workspace.
            # Note: For safety, this catches errors and doesn't push to remote automatically.
            def run_git(*args: str) -> str:
                cmd = ["git"] + list(args)
                result = subprocess.run(
                    cmd,
                    cwd=self._workspace_root,
                    capture_output=True,
                    text=True,
                    check=True
                )
                return result.stdout.strip()

            # 1. Create and checkout strict improvement branch
            run_git("checkout", "-b", branch_name)

            # 2. Write the patch (simulated by dropping a markdown proposal file)
            proposal_file = os.path.join(self._workspace_root, f"{proposal.proposal_id}.md")
            with open(proposal_file, "w", encoding="utf-8") as f:
                f.write(f"# {proposal.title}\n\n{proposal.description}\n\n")
                if proposal.proposed_patch:
                    f.write(f"```python\n{proposal.proposed_patch}\n```\n")

            # 3. Commit the structural change safely
            run_git("add", proposal_file)
            run_git("commit", "-m", f"feat(evolution): {proposal.title}")

            # 4. Try returning to previous branch if possible, but for docker workers
            # they might stay on the PR branch for testing. We will switch back to main.
            run_git("checkout", "-")

            return {
                "status": "success",
                "branch": branch_name,
                "proposal_id": proposal.proposal_id,
                "message": f"Successfully committed autonomous PR branch {branch_name}"
            }
        except subprocess.CalledProcessError as e:
            logger.error("Git workflow failed: %s %s", e.stdout, e.stderr)
            return {
                "status": "failed",
                "error": str(e),
                "stderr": e.stderr
            }
        except Exception as e:
            logger.exception("Unexpected error during Git execution")
            return {
                "status": "error",
                "error": str(e)
            }
