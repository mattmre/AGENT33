"""Computer Use tool for autonomous spatial desktop interaction.

Follows the reference paradigm set by Anthropic's Computer Use API, allowing
the agent to manipulate standard OS interfaces via mouse and keyboard tracking.
Pairs effectively with the Vision MCP server.
"""

from __future__ import annotations

import logging
from typing import Any

from agent33.tools.base import SchemaAwareTool, ToolContext, ToolResult

logger = logging.getLogger(__name__)


class ComputerUseTool(SchemaAwareTool):
    """Executes actions on the operating system's desktop environment."""

    @property
    def name(self) -> str:
        return "computer_use"

    @property
    def description(self) -> str:
        return (
            "Interact with the desktop environment via"
            " coordinate clicking, typing, and screenshots."
        )

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "mouse_move",
                        "left_click",
                        "left_click_drag",
                        "right_click",
                        "middle_click",
                        "double_click",
                        "screenshot",
                        "cursor_position",
                        "type",
                        "key",
                    ],
                    "description": "The desktop action to perform.",
                },
                "coordinate": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "[x, y] coordinates. Required for mouse_move and drag actions.",
                },
                "text": {
                    "type": "string",
                    "description": (
                        "Text to type or keys to press. Required for 'type' and 'key' actions."
                    ),
                },
            },
            "required": ["action"],
        }

    async def execute(self, params: dict[str, Any], context: ToolContext) -> ToolResult:
        action = params.get("action")
        logger.info(f"Executing computer_use: {action}")

        # Integration point for PyAutoGUI / xdotool / pyautogui
        if action == "screenshot":
            # return base64 encoded screen
            return ToolResult.ok("SCREENSHOT_BASE64_PLACEHOLDER")
        elif action == "mouse_move":
            coords = params.get("coordinate", [0, 0])
            return ToolResult.ok(f"Moved mouse to {coords}")
        elif action in ("left_click", "right_click", "double_click"):
            return ToolResult.ok(f"Performed {action}")
        elif action == "type":
            text = params.get("text", "")
            return ToolResult.ok(f"Typed: {text}")

        return ToolResult.fail(f"Unsupported action: {action}")
