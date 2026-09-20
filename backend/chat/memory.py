# Load / save chat memory JSON under backend/data/memory/.
import json
from typing import Any

from backend import config

EMPTY_MEMORY: list[Any] = []


def load_memory() -> list[Any]:
    path = config.MEMORY_PATH
    if not path.exists():
        return list(EMPTY_MEMORY)
    with open(path, encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        return list(EMPTY_MEMORY)
    return data


SORRY_LINE = "Sorry, I can only answer questions about the current tab."
HELP_LINE = (
    "Please get help. If you are in crisis, call or text 988 in the US "
    "(Suicide and Crisis Lifeline). You are not alone."
)


# Keep title + summary for memory. The panel still shows the full reply.
def clip_assistant_reply(text):
    if not text:
        return ""
    body = text.strip()
    if body == SORRY_LINE or body == HELP_LINE or body.startswith("I am not allowed"):
        return body
    lines = body.splitlines()
    if lines and lines[0].startswith("Status:"):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines = lines[1:]
    kept = []
    blank_seen = 0
    for line in lines:
        if line.strip() == "Sources:" or line.startswith("Sources:"):
            break
        if line.strip() == "Limitations":
            break
        if not line.strip():
            blank_seen += 1
            if blank_seen >= 2:
                break
            kept.append("")
            continue
        kept.append(line)
        if blank_seen >= 1 and len([x for x in kept if x.strip()]) >= 2:
            break
    return "\n".join(kept).strip()


def save_memory(memory: list[Any]) -> None:
    path = config.MEMORY_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    max_items = config.MAX_MEMORY_TURNS * 2

    if len(memory) > max_items:
        del memory[:-max_items]

    with open(path, "w", encoding="utf-8") as file:
        json.dump(memory, file, indent=2, ensure_ascii=False)

def turn_count(memory):
    if not memory:
        return 0
    return len(memory) // 2

def recent_items(memory, turns=None):
    if not memory:
        return []
    if turns is None:
        turns = config.MAX_CHAT_MEMORY_TURNS
    return memory[-(turns * 2):]

def older_items(memory, turns=None):
    if not memory:
        return []
    if turns is None:
        turns = config.MAX_CHAT_MEMORY_TURNS
    return memory[:-(turns * 2)]