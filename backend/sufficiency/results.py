from dataclasses import dataclass

@dataclass
class SufficiencyResult:
    score: int = 0
    related: bool = False
    rewrite: str = ""
    summary: str = ""
    on_tab: bool = True
