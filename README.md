# Tabkit

Page-aware AI assistant that summarizes and extracts exact context about a web page in a terminal.

You load a URL. Tabkit files the page into section notes on your machine, then you ask questions. It answers from those notes, through sections. It stays on that page unless you ask it to search. The same notes are reused until you clear them. A pasted URL only loads. Chat starts on the next line.

**Works:** Wikipedia, HTML articles, most public pages.  
**Does not:** PDFs, Canvas, login walls, Python 3.9 and older.

Two modes, same program. You pick the mode when you start, not by copying the folder. **api** and **local** share the same saved notes and memory.

Click to jump:

- [Api](#api)
- [Local](#local)
- [The structure](#the-structure)
- [Safety](#safety)
- [Customization](#customization)
- [View license](LICENSE)

Do not commit or post `.env`. Do not post `debug.json` or anything under `backend/data/` — those can hold the page and your questions. Git already ignores them.

## Setup

Run these in this folder. Same for both modes.

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
copy .env.example .env
pip install -r requirements.txt
```

macOS / Linux:

```bash
source .venv/bin/activate
cp .env.example .env
pip install -r requirements.txt
```

On Windows, if `python` is not found, use `py` in the commands below.

Search is optional in both modes. It uses a SerpAPI key. Page questions work without it. If you do not have one, set `WEB_SEARCH = False` in `backend/config.py`.

Anything other than `api` or `local` after `run.py` exits: `Mode must be api or local.`

The first line prints the mode, the chat model, and the host.

## Api

This mode uses the OpenAI API.

Open `.env` and set:

```
OPENAI_API_KEY=sk-...
```

```bash
python run.py
```

Same thing: `python run.py api`.

The default chat and page models are the names in `backend/config.py` under `API_*`. Change those if you want different OpenAI models.

The first load of a long page is the only expensive part because it takes the designated HTML heading text from the web page. It gets cheaper after the assistant compiles the web page context. example: `Mode: api  Chat: …  Host: api.openai.com`

## Local

This mode uses Ollama. No OpenAI key.

1. Install [Ollama](https://ollama.com).
2. Pull the names in `backend/config.py` under `LOCAL_CHAT_MODEL` and the smaller `LOCAL_*` models. Defaults are a bigger chat model and a smaller one for notes / the web check / recaps.
3. Leave Ollama running. It listens at `http://127.0.0.1:11434/v1`.
4. Start Tabkit:

```bash
python run.py local
```

The default local setup is `qwen2.5:14b` for chat and `qwen2.5:7b` for the smaller jobs. If your machine is under the specs below, local is not a good fit.

Recommended specs:

- 12 GB or more VRAM
- 16 GB or more RAM (32 GB+ preferred)

If chat runs out of memory on a long page, set `LOCAL_CHAT_MODEL` in `backend/config.py` to the smaller name too.

First load is still one model call per heading, just on your GPU.

## Using it

Same after either mode starts.

Type `instructions` if you want the short how-to. Then paste a URL **alone on the line** (`http://` or `https://`, or `www.…`). No extra words. You need internet for that first fetch. Some sites that block bots return empty text.

A pasted URL only **loads** the page (`Loaded: …` then `Ask about the page.`). It is not a question. Chat starts on the next line you type.

**Only one http URL can be fetched at a time.** A second, different link gets `Only one http is allowed to fetch.` Use `clear all` to drop the current page, then paste a new one. Pasting the same URL again prints `Loaded:` and `Ask about the page.` again. A fetch that fails prints `Could not fetch that page:` or `No text found on that page.`

If nothing is loaded, it says `Please type instructions to start.`  
Quit and come back: the last URL is still loaded. You do not paste it again.

The **first** time you load a URL is slow (it files notes). After that it is much cheaper until `clear pages`. Switching mode does not rescan the page.

Commands ignore case and extra spaces. example: `Clear Memory` still works.

## Commands

| Command         | What it does                                                            |
| --------------- | ----------------------------------------------------------------------- |
| `instructions`  | How to start                                                            |
| `/hints`        | List commands (`hints` also works)                                      |
| `current url`   | Show the loaded page                                                    |
| `pages`         | List saved section names                                                |
| `clear memory`  | Wipe chat memory                                                        |
| `clear debug`   | Wipe debug.json (only if `DEBUG = True`)                                |
| `clear pages`   | Delete notes for this URL (next ask rescans)                            |
| `clear all`     | Wipe memory, debug (if on), all page folders, and the saved current URL |
| `quit` / `exit` | Leave                                                                   |

## The structure

```
tabkit/
  run.py                 start the terminal (`api` or `local`)
  README.md              this file
  LICENSE                MIT
  requirements.txt       Python packages
  .env.example           copy to .env and add your key (api mode)
  backend/
    config.py            flags, keys, api vs local model names
    main.py              input loop and commands
    pipeline.py          one turn: file page, maybe search, reply
    commands.py          /hints, clear, pages, current url
    context.py           one turn of input
    pages/               download the URL, file notes, read them later
    chat/                the model that talks to you + session memory
    sufficiency/         silent step: does this question need the web?
    tools/               web search (only if WEB_SEARCH is on)
    debug/               writes debug.json when DEBUG is on
    data/                runtime notes, memory, debug (gitignored)
```

You normally only edit `backend/config.py` and, for cheaper scans, `backend/pages/fetch.py`. Leave the rest unless you are changing the program.

## How it works

What one turn looks like for the model.

```mermaid
flowchart TD
  you[You type in the terminal] --> kind{What is it?}

  kind -->|command| cmds[Handle here<br/>hints, clear, pages, quit]
  kind -->|URL alone| slot{A page already loaded?}
  kind -->|question| have{Notes for this URL?}

  slot -->|different URL| one[Only one http is allowed to fetch.]
  slot -->|none or same URL| fetch[Download the page]
  fetch --> filed{Notes already saved?}
  filed -->|no| write[File section notes<br/>one model call per heading]
  filed -->|yes| reuse[Reuse saved notes]
  write --> loaded[Loaded. Ask about the page.]
  reuse --> loaded

  have -->|no| paste[Please type instructions to start.]
  have -->|yes| tab{About this page?}
  tab -->|no| sorry[Sorry, I can only answer questions about the current tab.]
  tab -->|yes| gate[Silent check:<br/>does this need the live web?]
  gate --> search{WEB_SEARCH on<br/>and the check says yes?}
  search -->|yes| web[Optional web search]
  search -->|no| notes[Read saved notes]
  web --> notes
  notes --> mem[Related follow-ups keep chat memory]
  mem --> reply[Chat replies]
```

Bare URL: download and file notes if needed. No chat reply and no web-search check — there is no question yet. A second different URL is refused until `clear all`.

Question: reuse notes, maybe search, then reply. Long threads keep recent turns and a short recap of the older ones.

Off-topic (math, homework, greetings, facts not on the page) is only this line: `Sorry, I can only answer questions about the current tab.` Asking to search / look it up is on-topic. example: a math question while an article is loaded.

## Safety

The program has a few hard stops.

- **Stay on the page.** Off-topic questions get only the sorry line. It will not do homework or chat as a general assistant.
- **Crisis.** If someone is talking about harming themselves, the reply is only a help line with **988**. It does not use the page, search, or the usual answer shape.
- **Page text is data.** Notes, quotes, memory, and search hits are not treated as instructions. A page cannot tell the assistant to ignore its rules.
- **No raw HTML in chat.** The model sees filed notes, not the downloaded page.

If `DEBUG = True`, the same turn can also write `debug.json`. That is for you, not for the reply.

## Customization

Near the top of `backend/config.py`:

```
DEBUG = True
WEB_SEARCH = True
```

- `True` — that feature is on.
- `False` — that feature is off.

`DEBUG` writes `debug.json`. `WEB_SEARCH` allows the optional web-search step when the gate asks for it.

Mode is not a flag in that file. It is the word after `run.py`: `api` or `local`. Change the `API_*` and `LOCAL_*` names in config to pick models.

Filing notes costs **one model call per heading**. Long pages with lots of `h2` / `h3` / `h4` sections get expensive.

If you are low on tokens (api) or VRAM (local), open `backend/pages/fetch.py` and only keep `h2` (drop `h3` and `h4`). Coarser sections, fewer files, cheaper first load.

Then run `clear pages` so it rescans with the new setting.

You can also lower `MAX_PAGE_SECTIONS` in `backend/config.py` as a hard cap.

## License

MIT. Click [View license](LICENSE) to read it.
