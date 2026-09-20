from backend.tools.web.client import SearchClient
from backend.tools.results import ToolResult

class WebTool:
    def __init__(self):
        self.search_client = SearchClient()

    def run(self, text: str):
        query = (text or "").strip()

        if not query:
            return ToolResult(tool="web", status="query_failed", content={"query": query, "results": []}, confidence=0.0)

        status, results = self.search_client.search(query)

        if status != "ok":
            return ToolResult(tool="web", status=status, content={"query": query, "results": []}, confidence=0.0)

        return ToolResult(tool="web", status="ok", content={"query": query, "results": results}, confidence=0.0)
