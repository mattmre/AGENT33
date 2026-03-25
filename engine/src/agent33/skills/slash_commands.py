"""Slash-command parser for skill activation.

Provides hermes-agent-style ``/skill-name`` UX:
- ``/research-agent analyse this codebase`` activates the *research-agent*
  skill with "analyse this codebase" as the instruction.
- Session preloading injects L1 instructions into the system prompt for
  all preloaded skills, so they persist across an entire conversation.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent33.skills.registry import SkillRegistry


# ------------------------------------------------------------------
# Slash-command scanning
# ------------------------------------------------------------------

_KEBAB_RE = re.compile(r"[_\s]+")


def _to_slash_command(skill_name: str) -> str:
    """Convert a skill name to its canonical slash-command form.

    ``research_agent`` -> ``/research-agent``
    ``kubernetes-deploy`` -> ``/kubernetes-deploy``
    """
    return "/" + _KEBAB_RE.sub("-", skill_name.strip().lower())


def scan_skill_commands(registry: SkillRegistry) -> dict[str, str]:
    """Build a mapping of slash-commands to skill names.

    Iterates over all registered skills and produces one ``/kebab-name``
    entry for each skill.  The returned dict maps
    ``{"/kebab-name": "original-skill-name"}``.
    """
    commands: dict[str, str] = {}
    for skill in registry.list_all():
        cmd = _to_slash_command(skill.name)
        commands[cmd] = skill.name
    return commands


# ------------------------------------------------------------------
# Slash-command parsing
# ------------------------------------------------------------------


def parse_slash_command(
    text: str,
    commands: dict[str, str],
) -> tuple[str, str] | None:
    """Parse user text for a leading slash-command.

    Returns ``(skill_name, remaining_instruction)`` when a match is found,
    or ``None`` when the text does not start with a registered command.

    When multiple commands share a prefix (e.g. ``/deploy`` and
    ``/deploy-k8s``), the longest matching command wins.
    """
    text = text.strip()
    if not text.startswith("/"):
        return None

    # Sort by length descending so the longest (most specific) command
    # is tried first.
    for cmd in sorted(commands.keys(), key=len, reverse=True):
        if text == cmd or text.startswith(cmd + " "):
            instruction = text[len(cmd) :].strip()
            return (commands[cmd], instruction)

    return None


# ------------------------------------------------------------------
# Session preloading
# ------------------------------------------------------------------


def build_preloaded_prompt(
    skill_names: list[str],
    registry: SkillRegistry,
) -> str:
    """Build a system-prompt prefix for session-preloaded skills.

    For each requested skill name:
    - Loads L1 full instructions from the registry.
    - Wraps them in a ``[PRELOADED SKILL: ...]`` header block.

    Skills that cannot be found are silently skipped (they may have been
    removed between session creation and prompt construction).
    """
    blocks: list[str] = []
    for name in skill_names:
        skill = registry.get(name)
        if skill is None:
            continue
        header = f"[PRELOADED SKILL: {skill.name}]"
        body = skill.instructions if skill.instructions else skill.description
        blocks.append(f"{header}\n{body}")
    return "\n\n".join(blocks)
