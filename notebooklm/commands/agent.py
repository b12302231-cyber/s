"""notebooklm agent <subcommand> — bundled agent instruction templates."""

import click

# ---------------------------------------------------------------------------
# Bundled templates
# ---------------------------------------------------------------------------

_CODEX_INSTRUCTIONS = """\
# NotebookLM — Codex Agent Instructions

You are an AI coding assistant that can interact with Google NotebookLM
via the `notebooklm` CLI. Use these instructions to help users research,
synthesise, and generate content from their notebooks.

## Workflow

1. **Authenticate** (once per session):
   notebooklm login

2. **Create or select a notebook**:
   notebooklm create "My Research"
   notebooklm use <notebook_id>

3. **Add sources** — URLs, PDFs, or local files:
   notebooklm source add "https://example.com/paper"
   notebooklm source add ./local.pdf
   notebooklm source add-research "quantum computing"

4. **Chat with sources**:
   notebooklm ask "What are the key findings?"

5. **Generate content**:
   notebooklm generate audio "make it engaging" --wait
   notebooklm generate quiz --difficulty hard
   notebooklm generate flashcards --quantity more

6. **Download artifacts**:
   notebooklm download audio ./podcast.mp3
   notebooklm download quiz --format markdown ./quiz.md

## Diagnostics

   notebooklm auth check --test   # verify token is live
   notebooklm metadata --json     # inspect active notebook
   notebooklm language list       # available output languages
"""

_CLAUDE_SKILL_TEMPLATE = """\
---
name: notebooklm
description: >
  Interact with Google NotebookLM — manage notebooks, add sources,
  chat with documents, and generate audio/video/quiz/flashcard artifacts.
  Trigger when the user wants to research a topic, summarise documents,
  or create study materials from web or local sources.
triggers:
  - notebooklm
  - notebook lm
  - google notebooklm
  - research notebook
---

# NotebookLM Skill

## Authentication

Always verify auth before running commands:

```bash
notebooklm auth check --test
```

If not authenticated:

```bash
notebooklm login
# For organisations that require Microsoft Edge for SSO:
notebooklm login --browser msedge
```

## Common Tasks

### Research a topic and build a notebook

```bash
notebooklm create "{notebook_title}"
notebooklm source add-research "{research_query}"
notebooklm ask "Summarise the key themes"
```

### Add specific sources

```bash
notebooklm use {notebook_id}
notebooklm source add "https://..."
notebooklm source add ./paper.pdf
```

### Generate and download content

```bash
notebooklm generate audio "make it engaging" --wait
notebooklm generate quiz --difficulty hard
notebooklm generate flashcards --quantity more
notebooklm generate slide-deck
notebooklm generate mind-map

notebooklm download audio ./podcast.mp3
notebooklm download quiz --format markdown ./quiz.md
notebooklm download flashcards --format json ./cards.json
```

### Inspect notebook state

```bash
notebooklm metadata --json
notebooklm language list
notebooklm share status
```

## Notes

- Active notebook is persisted at `~/.config/notebooklm/state.json`.
- Credentials are stored at `~/.config/notebooklm/credentials.json` (mode 0600).
- Run `notebooklm skill status` to verify this skill file is installed correctly.
"""

# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

_AGENTS = {
    "codex": _CODEX_INSTRUCTIONS,
    "claude": _CLAUDE_SKILL_TEMPLATE,
}


@click.group("agent")
def agent_group():
    """Bundled agent instruction templates."""


@agent_group.command("show")
@click.argument("name", type=click.Choice(list(_AGENTS), case_sensitive=False))
def agent_show(name: str):
    """Print the bundled instructions for the named agent (codex or claude)."""
    click.echo(_AGENTS[name.lower()])
