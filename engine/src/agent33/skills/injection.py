"""Skill-to-prompt injection and tool context resolution."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent33.skills.registry import SkillRegistry
    from agent33.tools.base import ToolContext


class SkillInjector:
    """Injects skill content into agent system prompts.

    Supports progressive disclosure:
    - L0: compact metadata block (name + description) for all available skills
    - L1: full instructions block for actively invoked skills
    - L2: on-demand resource loading via registry.get_resource()
    """

    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry

    # ------------------------------------------------------------------
    # Prompt Building
    # ------------------------------------------------------------------

    def build_skill_metadata_block(self, skill_names: list[str]) -> str:
        """L0: Build a compact skill list for the base system prompt.

        Returns a section listing available skills so the LLM knows what
        capabilities can be activated.
        """
        lines = ["# Available Skills"]
        for name in sorted(skill_names):
            meta = self._registry.get_metadata_only(name)
            if meta:
                lines.append(f"- {meta['name']}: {meta['description']}")
        if len(lines) == 1:
            lines.append("(none)")
        return "\n".join(lines)

    def build_skill_instructions_block(self, skill_name: str) -> str:
        """L1: Build full instructions block for an active skill.

        Includes governance metadata (allowed tools, approval requirements)
        and the complete skill instructions.
        """
        skill = self._registry.get(skill_name)
        if skill is None:
            return f"# Skill: {skill_name}\n(skill not found)"

        lines = [f"# Active Skill: {skill.name}"]

        # Governance info
        governance_lines: list[str] = []
        if skill.allowed_tools:
            governance_lines.append(
                f"- Allowed tools: {', '.join(skill.allowed_tools)}"
            )
        if skill.disallowed_tools:
            governance_lines.append(
                f"- Blocked tools: {', '.join(skill.disallowed_tools)}"
            )
        if skill.autonomy_level:
            governance_lines.append(f"- Autonomy: {skill.autonomy_level}")
        if skill.approval_required_for:
            governance_lines.append(
                f"- Requires approval for: {', '.join(skill.approval_required_for)}"
            )
        if governance_lines:
            lines.append("## Governance")
            lines.extend(governance_lines)

        # Instructions
        if skill.instructions:
            lines.append("")
            lines.append(skill.instructions)

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Tool Context Resolution
    # ------------------------------------------------------------------

    def resolve_tool_context(
        self,
        active_skills: list[str],
        base_context: ToolContext,
    ) -> ToolContext:
        """Merge tool restrictions from active skills into the ToolContext.

        Skills narrow tool access: the resulting allowlist is the intersection
        of the agent's base allowlist and the skill's allowed_tools.
        Disallowed tools are always removed.
        """
        from agent33.tools.base import ToolContext as _ToolContext

        # Start with the base context's values
        allowed = set(base_context.command_allowlist) if base_context.command_allowlist else None
        blocked: set[str] = set()

        for name in active_skills:
            skill = self._registry.get(name)
            if skill is None:
                continue

            # Accumulate blocked tools
            blocked.update(skill.disallowed_tools)

            # Intersect allowed tools
            if skill.allowed_tools:
                skill_allowed = set(skill.allowed_tools)
                allowed = (
                    skill_allowed if allowed is None else allowed & skill_allowed
                )

        # Remove blocked from allowed
        if allowed is not None:
            allowed -= blocked

        # Build a new context with the merged allowlist
        new_allowlist = sorted(allowed) if allowed is not None else []
        return _ToolContext(
            command_allowlist=new_allowlist,
            path_allowlist=base_context.path_allowlist,
            working_dir=base_context.working_dir,
        )
