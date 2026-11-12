# AI log

The course asks which AI tool was used for what, and the client wants a record of how AI was used.
This folder is that record. **The repository is public, so every entry is short and general.**

- **One new file per task**: `YYYY-MM-DD_SCRUM-<n>_<firstname>.md`, copied from `_TEMPLATE.md`.
  One file per task means logs can never cause merge conflicts.
- **At most 40 lines**, with the template's headings and one line per bullet.
- **What was asked**: one or two sentences in your own words. Do not paste prompts, tickets or messages.
- **What the AI did**: the areas or features it touched, not code and not a file-by-file list.
- **Never include**: names of people other than your own first name, e-mails, links, passwords or keys,
  private details, and opinions about people or tools. Normal project words (strain, plasmid, primer,
  the ticket title) are fine.
- Never edit someone else's log file.

CI checks the format of every new or changed entry (`.github/scripts/check_ai_log.sh`). If it fails,
the message says what to shorten or remove.
