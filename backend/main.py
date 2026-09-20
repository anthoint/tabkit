from backend.context import Context
from backend.chat.memory import clip_assistant_reply, load_memory, save_memory
from backend.pages.fetch import fetch_page
from backend.pages.read import PageReader
from backend.pipeline import Pipeline
from backend.debug.store import load_debug
from backend.chat.prompts import HELP_LINE, PASTE_LINE, ONE_HTTP_LINE
from backend import config
from backend.commands import (
    type_hints,
    type_instruction,
    current_url,
    exit_program,
    clear_memory,
    clear_debug,
    clear_pages,
    clear_all,
    list_pages,
    load_last_url,
    save_last_url,
)
import requests


class App:
    def __init__(self, url=None, title="", page_text=None):
        self.pipeline = Pipeline()
        self.memory = load_memory()
        self.debug = load_debug() if config.use_debug() else []
        self.reader = PageReader()
        self.url = url or load_last_url()
        self.title = title or (self.reader.page_title(self.url) if self.url else "")
        self.page_text = page_text
        self.send_page = bool(page_text)
        self.commands = {
            "/hints": type_hints,
            "hints": type_hints,
            "/instruction": type_instruction,
            "instructions": type_instruction,
            "current url": current_url,
            "quit": exit_program,
            "exit": exit_program,
            "clear memory": clear_memory,
            "clear pages": clear_pages,
            "clear all": clear_all,
            "pages": list_pages,
        }
        if config.use_debug():
            self.commands["clear debug"] = clear_debug

    def options(self, user_input):
        key = " ".join(user_input.lower().split())
        command = self.commands.get(key)
        if command:
            result = command(self)
            if result:
                print(result)
            return command

    # Fetch the URL if notes were cleared or never filed.
    def ensure_page(self):
        if not self.url:
            return False
        if self.reader.has_notes(self.url):
            if not self.title:
                self.title = self.reader.page_title(self.url)
            return True
        if not self.page_text:
            print("Fetching…")
            try:
                self.title, self.page_text = fetch_page(self.url)
            except requests.RequestException as error:
                print("Could not fetch that page:", error)
                return False
            if not (self.page_text or "").strip():
                print("No text found on that page.")
                return False
        print("Filing notes (first time is slow)…")
        self.pipeline.writer.reply(self.title or "", self.url, self.page_text)
        self.page_text = None
        self.send_page = False
        return True

    def _same_url(self, left, right):
        def norm(item):
            text = (item or "").strip().rstrip("/").lower()
            if text.startswith("www."):
                text = "https://" + text
            return text
        return bool(left) and bool(right) and norm(left) == norm(right)

    def chat_once(self):
        user_input = input("You: ").strip()

        if user_input == "":
            return

        if self.options(user_input):
            return

        if self.pipeline.is_crisis(user_input):
            print(HELP_LINE)
            return

        if self.pipeline.is_http_link(user_input):
            raw = user_input.strip().strip("<>").strip("\"'")
            if raw.lower().startswith("www."):
                raw = "https://" + raw
            if self.url and not self._same_url(self.url, raw):
                print(ONE_HTTP_LINE)
                return
            self.url = raw
            save_last_url(self.url)
            self.page_text = None
            self.send_page = False
            if not self.ensure_page():
                return
            print("Loaded: " + self.url)
            print("Ask about the page.")
            return

        if not self.url or not self.reader.has_notes(self.url):
            print(PASTE_LINE)
            return

        if not self.ensure_page():
            return

        context = Context(
            text=user_input,
            url=self.url,
            title=self.title or None,
            page_text=None,
        )
        try:
            reply = self.pipeline.handle(context, self.memory)
        except ValueError as error:
            print(error)
            return
        self.send_page = False

        self.memory.append({"role": "user", "text": user_input})
        self.memory.append({"role": "assistant", "text": clip_assistant_reply(reply)})
        save_memory(self.memory)

        print(f"Assistant: {reply}")

    def run(self):
        while True:
            try:
                self.chat_once()
            except (EOFError, KeyboardInterrupt):
                print("\n", end="")
                return


def main():
    print("Type instructions to start.\n")
    app = App()
    if app.url:
        print("Still on: " + app.url)
        print("Type <current url> to see it. You do not need to paste it again.\n")
    app.run()


if __name__ == "__main__":
    main()
