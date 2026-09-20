from backend.tools.results import ToolResult


def entry(result: ToolResult):
    results = result.content.get("results") or []
    return {
        "tool": result.tool,
        "status": result.status,
        "query": result.content.get("query"),
        "urls": [item.get("url", "") for item in results],
        "snippet": [item.get("snippet", "") for item in results],
    }
