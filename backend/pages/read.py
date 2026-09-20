from backend import config
from backend.pages.write import folder_key


# Reads page-note files from disk. Does not call a model.
class PageReader:
    # Return the notes folder for this url.
    def folder(self, url):
        return config.PAGES_DIR / folder_key(url)

    # True if this url already has at least one section file.
    def has_notes(self, url):
        return bool(self.paraphrases(url))

    # Title saved in _meta when notes were filed. Empty if missing.
    def page_title(self, url):
        path = self.folder(url) / "_meta.txt"
        if not path.exists():
            return ""
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.lower().startswith("title:"):
                return line.split(":", 1)[1].strip()
        return ""

    # Split one section file into (paraphrase, exact).
    def parse_file(self, text):
        paraphrase = ""
        exact = ""
        if "## Exact" in text:
            left, right = text.split("## Exact", 1)
            paraphrase = left.replace("## Paraphrase", "").strip()
            exact = right.strip()
        else:
            paraphrase = text.replace("## Paraphrase", "").strip()
        if paraphrase.startswith("Name:"):
            paraphrase = paraphrase.split("\n", 1)[-1].strip()
        return paraphrase, exact

    # Load every section file except _meta. Returns [{name, paraphrase}, ...] with no Exact text.
    def paraphrases(self, url):
        folder = self.folder(url)
        if not folder.exists():
            return []

        notes = []
        for path in sorted(folder.iterdir()):
            if not path.is_file() or path.name == "_meta.txt":
                continue
            if path.suffix != ".txt":
                continue
            paraphrase, _exact = self.parse_file(path.read_text(encoding="utf-8"))
            notes.append({"name": path.stem, "paraphrase": paraphrase})
        return notes

    # Return the verbatim Exact block from one file (name='Cats' reads Cats.txt).
    def exact(self, url, name):
        folder = self.folder(url)
        path = folder / (name + ".txt")
        if not path.exists():
            return ""
        _paraphrase, exact = self.parse_file(path.read_text(encoding="utf-8"))
        return exact
