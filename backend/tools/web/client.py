import requests

from backend import config

class SearchClient:
    def __init__(self):
        self.max_snippet_len = config.MAX_SEARCH_SNIPPETS
        self.max_results = config.MAX_SEARCH_RESULTS
    
    def search(self, search_query: str):
        
        if config.SERPAPI_API_KEY is None:
            return ("missing_serpapi_api_key", [])

        try:
            response = requests.get(
                "https://serpapi.com/search.json",
                params={
                    "engine": "google",
                    "api_key": config.SERPAPI_API_KEY,
                    "q": search_query,
                    "num": self.max_results,
                },
                timeout=15
            )
            response.raise_for_status()
        except Exception as e:
            return (str(e), [])
        
        data = response.json()

        if data.get("error"):
            return ("serpapi_error", [])
        
        results = []

        for result in data.get("organic_results", []):
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            snippet = self.precise_snippet(snippet)

            url = result.get("link", "")
            results.append({
                "title": title,
                "snippet": snippet,
                "url": url,
            })

        if results == []:
            return ("no_results", [])
        return ("ok", results[:self.max_results])
     
    def precise_snippet(self, snippet: str) -> str:
        snippet = snippet.strip()

        if len(snippet) <= self.max_snippet_len:
            return snippet
        
        cut = snippet[:self.max_snippet_len]

        end = max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"))

        if end >= int(self.max_snippet_len * 0.5):
            return cut[: end + 1].strip()

        return cut.rstrip() + "..."
        

            

