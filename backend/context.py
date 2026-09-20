from dataclasses import dataclass


@dataclass
class Context:
    text: str
    source: str = "chat"
    url: str | None = None
    title: str | None = None
    page_text: str | None = None
