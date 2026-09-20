from backend.tools.web.tool import WebTool
from backend.tools.results import ToolResult
from backend.debug.store import load_debug, save_debug
from backend.debug.web import entry
from backend import config


class ToolManager:
    def __init__(self):
        self.web_tool = WebTool()
    
    def run(self, name: str, text: str):
        if name == "web":
            if not config.use_web_search():
                return ToolResult(
                    tool="web",
                    status="skipped",
                    content={"query": text, "reason": "web search off"},
                    confidence=0.0,
                )
            result = self.web_tool.run(text)
            if config.use_debug():
                entries = load_debug()
                entries.append(entry(result))
                save_debug(entries)
            return result
        return ToolResult(tool=name, status="tool_not_found", content={"query": None}, confidence=0.0)

