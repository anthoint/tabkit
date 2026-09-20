from backend.context import Context
from backend.sufficiency.checker import SufficiencyChecker
from backend.tools.manager import ToolManager
from backend.chat.engine import BrowserAssistant
from backend.chat.memory import turn_count, recent_items, older_items
from backend.chat.summarize import summarize
from backend.sufficiency.results import SufficiencyResult
from backend.pages.read import PageReader
from backend.pages.write import PageAssistant
from backend.debug.sufficiency import debug_sufficiency
from backend.chat.prompts import HELP_LINE, PASTE_LINE, SORRY_LINE
from backend import config


class Pipeline:
    def __init__(self):
        self.checker = SufficiencyChecker()
        self.manager = ToolManager()
        self.assistant = BrowserAssistant()
        self.writer = PageAssistant()
        self.reader = PageReader()
        self.sufficiency_threshold = config.SUFFICIENCY_THRESHOLD
        self.max_len = config.MAX_ASSISTANT_SNIPPETS
    

    def handle(self, context: Context, memory=None) -> str:
        if self.is_crisis(context.text):
            return HELP_LINE
        if self.is_off_topic(context.text):
            return SORRY_LINE

        user_text = self.previous_user_text(memory)
        assistant_text = self.previous_assistant_text(memory)
        assistant_text = self.precise_assistant_snippet(assistant_text)

        url = context.url
        if url and not context.title:
            context.title = self.reader.page_title(url) or None
        if url and context.page_text and not self.reader.has_notes(url):
            self.writer.reply(context.title or "", url, context.page_text)

        notes_ready = bool(url and self.reader.has_notes(url))
        if not url and not self.is_http_link(context.text):
            return PASTE_LINE

        # Bare URL: no question to score. Real questions always go through sufficiency.
        if self.is_http_link(context.text):
            check = SufficiencyResult(
                score=10,
                related=bool(user_text),
                rewrite="",
                summary="",
                on_tab=True,
            )
        else:
            check = self.checker.check(context, user_text, assistant_text)

        if config.use_debug():
            debug_sufficiency(check, user_text, assistant_text, context)

        if isinstance(check, SufficiencyResult) and not check.on_tab:
            return SORRY_LINE

        if (
            config.use_web_search()
            and isinstance(check, SufficiencyResult)
            and check.score < self.sufficiency_threshold
        ):
            tool_result = self.manager.run("web", check.rewrite or context.text)
        else:
            tool_result = None
        
        chat_memory = None
        older_summary = None

        if isinstance(check, SufficiencyResult) and check.related:
            if turn_count(memory) > config.MAX_CHAT_MEMORY_TURNS:
                older_summary = summarize(older_items(memory))
                chat_memory = recent_items(memory)
            else:
                chat_memory = memory

        # Attach folder notes if this turn has a url. Quote → one Exact block;
        # otherwise names + paraphrases. Never put the raw tab in context.text.
        page_notes = None
        exact = None
        if url:
            notes = self.reader.paraphrases(url)
            if notes:
                page_notes = notes
            if notes and self.want_exact(context.text):
                name = self.pick_name(context.text, notes)
                if name:
                    exact = {"name": name, "text": self.reader.exact(url, name)}

        return self.assistant.reply(
            context,
            tool_result,
            chat_memory,
            older_summary,
            page_notes=page_notes,
            exact=exact,
        )

    # First-person crisis only. "how did he die" and other page deaths do not match.
    def is_crisis(self, text):
        q = " ".join((text or "").lower().split())
        if not q:
            return False
        hard = (
            "kill myself",
            "killing myself",
            "want to die",
            "wanna die",
            "end my life",
            "ending my life",
            "take my life",
            "taking my life",
            "hurt myself",
            "hurting myself",
            "self harm",
            "self-harm",
            "selfharm",
            "i'm suicidal",
            "im suicidal",
            "i am suicidal",
            "i feel suicidal",
            "my suicide",
            "don't want to be alive",
            "dont want to be alive",
            "don't want to live",
            "dont want to live",
            "no reason to live",
            "better off dead",
        )
        for word in hard:
            if word in q:
                return True
        if self.is_page_death(q):
            return False
        about_self = (
            q == "i"
            or q.startswith("i ")
            or q.startswith("i'")
            or q.startswith("im ")
            or " i " in q
            or " i'm " in q
            or " im " in q
            or " me " in q
            or " my " in q
            or q.startswith("my ")
        )
        if not about_self:
            return False
        mental = (
            "depressed",
            "depression",
            "hopeless",
            "panic attack",
            "can't go on",
            "cant go on",
            "can't take it",
            "cant take it",
            "want to disappear",
            "worthless",
            "no one cares",
            "nobody cares",
        )
        for word in mental:
            if word in q:
                return True
        return False

    # Page questions about someone else's death or funeral. Not a crisis line.
    def is_page_death(self, text):
        q = " ".join((text or "").lower().split())
        cues = (
            "how did",
            "when did",
            "how was",
            "how were",
            "what killed",
            "cause of death",
            "his death",
            "her death",
            "their death",
            "date of death",
            "death of",
            "funeral",
            "burial",
            "assassinated",
            "assassinate",
        )
        for word in cues:
            if word in q:
                return True
        if q.endswith(" die") or q.endswith(" death") or q.endswith(" died"):
            return True
        if " die " in q or " died " in q or " dying " in q:
            return True
        return False

    # Math, greetings, or a short jab at the bot. Not "how did he die".
    def is_off_topic(self, text):
        q = " ".join((text or "").lower().split())
        if not q:
            return False
        if (
            self.about_this_tab(q)
            or self.want_search(q)
            or self.want_exact(q)
            or self.is_page_death(q)
            or self.is_http_link(text)
        ):
            return False
        compact = q.replace(" ", "")
        math_ok = True
        for ch in compact:
            if ch not in "0123456789+-*=/.x":
                math_ok = False
                break
        if math_ok and any(ch.isdigit() for ch in compact):
            return True
        if q in (
            "yo",
            "hey",
            "hi",
            "hello",
            "sup",
            "whats up",
            "what's up",
        ):
            return True
        words = q.split()
        if len(words) <= 3 and (
            q.startswith("your ")
            or q.startswith("you're ")
            or q.startswith("youre ")
            or q.startswith("you are ")
            or q.startswith("you ")
        ):
            return True
        return False

    def want_search(self, question):
        if not question:
            return False
        q = question.lower()
        markers = (
            "search",
            "look it up",
            "look up",
            "look this up",
            "use the internet",
            "use web",
            "google",
        )
        for word in markers:
            if word in q:
                return True
        return False

    # True if the question is about the open tab (notes are enough; skip search).
    def about_this_tab(self, question):
        if not question:
            return False
        q = question.lower()
        markers = (
            "this page",
            "this article",
            "this tab",
            "this site",
            "on this page",
            "on the page",
            "summarize this",
            "summarize the",
            "what is this about",
            "what's this about",
            "what does it say",
            "exact",
            "quote",
            "word for word",
            "word-for-word",
        )
        for word in markers:
            if word in q:
                return True
        return False

    def is_http_link(self, text):
        t = (text or "").strip().strip("<>").strip("\"'")
        if not t or " " in t:
            return False
        low = t.lower()
        if low.startswith("http://") or low.startswith("https://"):
            return True
        if low.startswith("www.") and "." in t[4:]:
            return True
        return False

    # True if the question is asking for wording from the page, not a summary.
    def want_exact(self, question):
        if not question:
            return False
        q = question.lower()
        markers = (
            "exact",
            "quote",
            "word for word",
            "word-for-word",
            "what does it say",
        )
        for word in markers:
            if word in q:
                return True
        return False

    # Pick a section name mentioned in the question. No match → None (do not default to Intro).
    def pick_name(self, question, notes):
        if not notes:
            return None
        q = (question or "").lower()
        for item in notes:
            name = (item.get("name") or "")
            low = name.lower()
            if low and low in q:
                return name
            spaced = low.replace("-", " ")
            if spaced and spaced in q:
                return name
            for part in low.split("-"):
                if len(part) >= 4 and part in q:
                    return name
        return None
    
    def previous_user_text(self, memory=None) -> str | None:
        if memory is None:
            return None

        for item in reversed(memory):
            if item.get("role") == "user":
                text = item.get("text", "").strip()
                if text:
                    return text
        return None
    
    def previous_assistant_text(self, memory=None) -> str | None:
        if memory is None:
            return None
        
        for item in reversed(memory):
            if item.get("role") == "assistant":
                text = item.get("text", "").strip()
                if text:
                    return text
        return None

    def precise_assistant_snippet(self, text: str) -> str | None:
        if not text:
            return None
        
        text = " ".join(text.split())

        if len(text) <= self.max_len:
            return text
        
        cut = text[:self.max_len]
        end = max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"))

        if end >= int(self.max_len * 0.5):
            return cut[: end + 1].strip()
        return cut.rstrip() + "..."


