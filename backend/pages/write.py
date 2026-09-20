from backend import config
from backend.pages import prompts


# Turn a url into a folder name (letters and numbers only) so the same page reuses one folder.
def folder_key(url):
    cleaned = []
    for ch in url:
        if ch.isalnum():
            cleaned.append(ch.lower())
    key = "".join(cleaned)
    if key:
        return key[:80]
    return "sample"


class PageAssistant:
    def __init__(self):
        self.client = config.make_client()
        self.model = config.PAGES_MODEL

    # Prefer ## heading blocks from the tab. Else cut by character count.
    def split_text(self, text):
        headed = self.split_headings(text)
        if headed:
            return headed
        size = config.PAGE_CHUNKS_CHARS
        limit = config.MAX_PAGE_SECTIONS
        chunks = []
        start = 0
        while start < len(text) and len(chunks) < limit:
            chunks.append({"name": "", "exact": text[start : start + size]})
            start += size
        return chunks

    # Split "## Legacy\\n..." into [{name, exact}, ...].
    def split_headings(self, text):
        if not text or ("\n## " not in text and not text.startswith("## ")):
            return []
        parts = []
        name = ""
        body = []
        for line in text.splitlines():
            if line.startswith("## "):
                if name and "".join(body).strip():
                    parts.append({"name": name, "exact": "\n".join(body).strip()})
                    if len(parts) >= config.MAX_PAGE_SECTIONS:
                        return parts
                name = line[3:].strip()
                body = []
            else:
                body.append(line)
        if name and "".join(body).strip() and len(parts) < config.MAX_PAGE_SECTIONS:
            parts.append({"name": name, "exact": "\n".join(body).strip()})
        if len(parts) >= 2:
            return parts
        return []

    # Ask the cheap model for a paraphrase only. The heading is already the file name.
    def paraphrase_chunk(self, chunk):
        try:
            messages = [
                {"role": "system", "content": prompts.page_paraphrase_prompt()},
                {"role": "user", "content": chunk},
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=config.PAGES_MAX_TOKENS,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception:
            return ""

    # Ask the cheap model for a name + paraphrase of one slice. Returns that text, or empty on failure.
    def name_chunk(self, chunk):
        try:
            messages = [
                {"role": "system", "content": prompts.page_prompt()},
                {"role": "user", "content": chunk},
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=config.PAGES_MAX_TOKENS,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception:
            return ""

    # Keep only letters, numbers, and hyphen so a model name cannot become a bad path.
    def safe_name(self, name, fallback):
        cleaned = []
        for ch in name:
            if ch.isalnum() or ch == "-":
                cleaned.append(ch)
        cleaned = "".join(cleaned)
        if cleaned:
            return cleaned
        return fallback

    # Heading "Early life" → Early-life.
    def heading_name(self, name, fallback):
        spaced = (name or "").replace("/", " ").replace("—", " ").replace("–", " ")
        hyphen = "-".join(spaced.split())
        return self.safe_name(hyphen, fallback)

    # One sentence per line so the note file is easier to scan.
    def format_paraphrase(self, text):
        text = " ".join((text or "").split())
        if not text:
            return ""
        parts = []
        rest = text
        while rest:
            cut = -1
            for mark in (". ", "? ", "! "):
                at = rest.find(mark)
                if at != -1 and (cut == -1 or at < cut):
                    cut = at
                    take = at + 1
            if cut == -1:
                parts.append(rest.strip())
                break
            parts.append(rest[:take].strip())
            rest = rest[take:].strip()
        return "\n\n".join(parts)

    # Split the page text, name each slice, and write the notes folder.
    def reply(self, title, url, text):
        sections = []

        for part in self.split_text(text):
            exact = part.get("exact") or ""
            given = (part.get("name") or "").strip()
            if given:
                name = given
                paraphrase = self.paraphrase_chunk(exact)
            else:
                raw = self.name_chunk(exact)
                lines = raw.split("\n", 1)
                name = lines[0].strip()
                paraphrase = lines[1].strip() if len(lines) > 1 else ""

            sections.append({
                "name": name,
                "paraphrase": paraphrase,
                "exact": exact,
            })
        self.get_item(sections, title, url)
        return sections

    # Write _meta and one file per section into data/pages/<url-key>/.
    def get_item(self, sections, title, url):
        folder = config.PAGES_DIR / folder_key(url)
        folder.mkdir(parents=True, exist_ok=True)
        for old in folder.iterdir():
            if old.is_file():
                old.unlink()

        (folder / "_meta.txt").write_text(
            "title: " + title + "\nurl: " + url + "\n",
            encoding="utf-8",
        )

        used = set()
        for i, item in enumerate(sections, start=1):
            name = self.heading_name(item.get("name") or "", "section-" + str(i))
            base = name
            n = 2
            while name.lower() in used:
                name = base + "-" + str(n)
                n += 1
            used.add(name.lower())
            paraphrase = self.format_paraphrase(item.get("paraphrase") or "")
            body = (
                "Name: "
                + name
                + "\n\n"
                + "## Paraphrase\n\n"
                + paraphrase
                + "\n\n"
                + "## Exact\n\n"
                + (item["exact"] or "").strip()
                + "\n"
            )
            (folder / (name + ".txt")).write_text(
                body,
                encoding="utf-8",
            )
        return folder
