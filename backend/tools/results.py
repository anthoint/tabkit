from dataclasses import dataclass
from typing import Any

@dataclass
class ToolResult:
    tool: str
    status: str
    content: dict[str, Any]
    confidence: float = 0.0
