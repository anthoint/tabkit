# Type /hints in the terminal to receive the hints
# assume any command with a space as spaces included
# uppercase or lowercase letters does not matter nor does blank spaces
import os
import shutil
import stat
import sys

from backend.chat.memory import save_memory
from backend.debug.store import save_debug
from backend.chat.prompts import PASTE_LINE
from backend import config


# Remember the last pasted URL so quit does not require pasting it again.
def load_last_url():
    path = config.LAST_URL_PATH
    if not path.exists():
        return None
    url = path.read_text(encoding="utf-8").strip()
    if url:
        return url
    return None


def save_last_url(url):
    path = config.LAST_URL_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    if url:
        path.write_text(url.strip() + "\n", encoding="utf-8")
    elif path.exists():
        path.unlink()


def type_hints(app) -> str:
    lines = [
        "Hints:",
        "- Type instructions for how to start.",
        "- Type <current url> to see the loaded page.",
        "- Type <quit> or <exit> to leave the program.",
        "- Type <clear all> to clear memory, debug (if on), all saved page folders, and the current URL.",
        "- Type <clear memory> to clear memory.json.",
    ]
    if config.use_debug():
        lines.append("- Type <clear debug> to clear debug.json.")
    lines.append("- Type <clear pages> to clear page notes for this URL.")
    lines.append("- Type <pages> to list saved section names.")
    return "\n".join(lines)


def type_instruction(app) -> str:
    return "\n".join([
        "Instructions:",
        "- Paste an http(s) URL to load a page, then ask about it.",
        "- After quit, the same URL is still loaded. You do not need to paste it again.",
        "- Only one http URL can be fetched at a time. Type <clear all> to load a different page.",
        "- Type <current url> to see which page is loaded.",
        "- Type /hints for commands.",
        "- If no page is loaded, the reply is: " + PASTE_LINE,
    ])


def current_url(app) -> str:
    if not app.url:
        return PASTE_LINE
    return "current url: " + app.url

def exit_program(app):
    return sys.exit()


def clear_memory(app):
    app.memory = []
    save_memory(app.memory)
    return "memory.json cleared"


def clear_debug(app):
    if not config.use_debug():
        return "debug is off"
    app.debug = []
    save_debug(app.debug)
    return "debug.json cleared"


# Delete the notes folder for the current URL so the next question rescans.
def clear_pages(app):
    if not app.url:
        return PASTE_LINE
    folder = app.reader.folder(app.url)
    app.page_text = None
    app.send_page = True
    return _clear_path(folder, "page notes")


def clear_all(app):
    clear_memory(app)
    if config.use_debug():
        clear_debug(app)
    app.page_text = None
    app.send_page = True
    pages_msg = _clear_path(config.PAGES_DIR, "the pages folder")
    app.url = None
    save_last_url("")
    if config.use_debug():
        return "memory.json, debug.json, and " + pages_msg
    return "memory.json and " + pages_msg


# Windows often denies rmtree if a .txt is open in the editor. Unlock, then retry.
def _unlock(path):
    try:
        os.chmod(path, stat.S_IWRITE)
    except OSError:
        return


def _rmtree_retry(func, path, _exc):
    _unlock(path)
    func(path)


def _remove_tree(path):
    if not path.exists():
        return True, ""
    try:
        shutil.rmtree(path, onerror=_rmtree_retry)
    except OSError:
        pass
    if not path.exists():
        return True, ""
    leftover = []
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            item = os.path.join(root, name)
            _unlock(item)
            try:
                os.remove(item)
            except OSError:
                leftover.append(item)
        for name in dirs:
            item = os.path.join(root, name)
            _unlock(item)
            try:
                os.rmdir(item)
            except OSError:
                leftover.append(item)
    _unlock(str(path))
    try:
        os.rmdir(path)
    except OSError:
        leftover.append(str(path))
    if leftover:
        return False, leftover[0]
    return True, ""


def _clear_path(path, label):
    if not path.exists():
        return "no " + label + " to clear"
    ok, locked = _remove_tree(path)
    if ok:
        return label + " cleared"
    return (
        label
        + " not fully deleted. Windows denied access to "
        + locked
        + ". Close that file in the editor (and OneDrive if it is syncing), then try again."
    )


# List section files for the current URL.
def list_pages(app):
    if not app.url:
        return PASTE_LINE
    notes = app.reader.paraphrases(app.url)
    if not notes:
        return "no page notes yet"
    names = [item.get("name") or "" for item in notes]
    return "pages:\n" + "\n".join("- " + name for name in names if name)
