# SCRUM-9 — Login page

- **Date:** 2026-11-23
- **Developer:** Zahraa
- **AI tool / model:** Claude Code / Claude Sonnet 5.5
- **PR:** #<number>

## What was asked
Turn the placeholder login page into a clear, centred login card that uses the shared form components and shows every login situation in a friendly way.

## What the AI did
- Rebuilt the login page as a narrow card with the shared form field component, a register link and an "ask an admin" line.
- Showed the backend's login messages (wrong password, waiting for approval, declined, disabled) as error messages.
- Added small page CSS for the card and a small script that disables the button after the first click.
- Checked each login state against the real page with a throw-away test run.

## What a human checked
- Reviewed the diff and the six checks.
- Browser checklist, screenshots and the list of states: to be done by the developer before the PR.

## Follow-ups
- The error box for non-field errors will be needed again on the register page; it could become a shared component.
