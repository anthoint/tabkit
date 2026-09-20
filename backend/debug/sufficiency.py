from backend.sufficiency.results import SufficiencyResult
from backend.context import Context
from backend.debug.store import load_debug, save_debug


def debug_sufficiency(check: SufficiencyResult, user_text, assistant_text, context: Context):
    entries = load_debug()
    entries.append({
        "type": "sufficiency",
        "score": check.score,
        "related": check.related,
        "on_tab": check.on_tab,
        "rewrite": check.rewrite,
        "previous_user": user_text,
        "previous_assistant": assistant_text,
        "current": context.text,
        "summary": check.summary,
    })
    save_debug(entries)
