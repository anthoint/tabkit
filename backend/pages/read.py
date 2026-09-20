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
        notes.sort(key=self.time_key)
        return notes

    # Years in the file name first, then usual life-stage words, then A-Z.
    def time_key(self, item):
        name = (item.get("name") or "").lower().replace("_", "-")
        year = 9999
        digits = ""
        for ch in name:
            if ch.isdigit():
                digits += ch
                if len(digits) == 4:
                    year = int(digits)
                    break
            else:
                digits = ""
        stages = (
            ("intro", 0),
            ("early-life", 1),
            ("family", 1),
            ("childhood", 1),
            ("education", 2),
            ("marriage", 3),
            ("vocation", 4),
            ("militia", 4),
            ("lawyer", 4),
            ("prairie", 4),
            ("legislature", 5),
            ("house-of", 5),
            ("republican", 6),
            ("emergence", 6),
            ("debate", 6),
            ("election", 7),
            ("inauguration", 7),
            ("secession", 7),
            ("president", 8),
            ("first-term", 8),
            ("commander", 8),
            ("emancipation", 9),
            ("gettysburg", 9),
            ("re-election", 10),
            ("second-term", 10),
            ("assassin", 11),
            ("funeral", 12),
            ("burial", 12),
            ("legacy", 13),
            ("memorial", 13),
            ("reputation", 13),
        )
        stage = 50
        for word, rank in stages:
            if word in name and rank < stage:
                stage = rank
        return (year if year != 9999 else 1800 + stage, stage, name)

    # Return the verbatim Exact block from one file (name='Cats' reads Cats.txt).
    def exact(self, url, name):
        folder = self.folder(url)
        path = folder / (name + ".txt")
        if not path.exists():
            return ""
        _paraphrase, exact = self.parse_file(path.read_text(encoding="utf-8"))
        return exact
