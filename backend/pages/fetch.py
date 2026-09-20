# Download a URL and turn HTML headings into ## section text.
from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

SKIP = re.compile(
    r"^(contents|see also|references|notes|footnotes|external links|"
    r"further reading|bibliography|citations|navigation menu|sources)$",
    re.I,
)
UA = "Tabkit/0.1 (local terminal reader)"


def clean_title(raw):
    text = str(raw or "")
    text = re.sub(r"\[edit\]", "", text, flags=re.I)
    text = re.sub(r"\[.*?\]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def heading_root(el):
    parent = el.parent
    classes = parent.get("class", []) if parent else []
    if parent and "mw-heading" in classes:
        return parent
    return el


def page_root(soup):
    # Wikipedia has empty .mw-parser-output stubs. Pick the box with the most headings.
    candidates = []
    for selector in (".mw-parser-output", "article", "main"):
        candidates.extend(soup.select(selector))
    best = None
    best_n = -1
    for node in candidates:
        count = len(node.find_all(["h2", "h3", "h4"]))
        if count > best_n:
            best = node
            best_n = count
    if best is not None and best_n > 0:
        return best
    return soup.body or soup


def text_between(start, end):
    bits = []
    for sib in start.next_siblings:
        if end is not None and sib is end:
            break
        if isinstance(sib, NavigableString):
            chunk = str(sib).strip()
        elif isinstance(sib, Tag):
            chunk = sib.get_text("\n", strip=True)
        else:
            chunk = ""
        if chunk:
            bits.append(chunk)
    return "\n".join(bits).strip()


def sections_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "template"]):
        tag.decompose()

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    elif soup.find("h1"):
        title = soup.find("h1").get_text(" ", strip=True)

    root = page_root(soup)
    headings = []
    for node in root.find_all(["h2", "h3", "h4"]):
        name = clean_title(node.get_text(" ", strip=True))
        if name and len(name) < 80:
            headings.append(node)

    parts = []
    if headings:
        first = heading_root(headings[0])
        lead_bits = []
        for child in root.children:
            if child is first:
                break
            if isinstance(child, NavigableString):
                chunk = str(child).strip()
            elif isinstance(child, Tag):
                chunk = child.get_text("\n", strip=True)
            else:
                chunk = ""
            if chunk:
                lead_bits.append(chunk)
        lead = "\n".join(lead_bits).strip()
        if lead:
            parts.append(("Intro", lead))

        for i, node in enumerate(headings):
            name = clean_title(node.get_text(" ", strip=True))
            start = heading_root(node)
            nxt = heading_root(headings[i + 1]) if i + 1 < len(headings) else None
            if SKIP.match(name):
                continue
            body = text_between(start, nxt)
            parts.append((name, body or "(See subsections.)"))

    if len(parts) < 2:
        blob = root.get_text("\n", strip=True) if root else ""
        return title, blob

    blocks = []
    for name, body in parts:
        blocks.append("## " + name + "\n" + body)
    return title, "\n\n".join(blocks)


def fetch_page(url):
    response = requests.get(url, headers={"User-Agent": UA}, timeout=45)
    response.raise_for_status()
    return sections_text(response.text)
