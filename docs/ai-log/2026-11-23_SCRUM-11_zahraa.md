# SCRUM-11 — Password change pages

- **Date:** 2026-11-23
- **Developer:** Zahraa
- **AI tool / model:** Claude Code / Claude Sonnet 5.5
- **PR:** #<number>

## What was asked
Restyle the change-password form and its confirmation page so they match the login page and show errors under each field.

## What the AI did
- Rebuilt the change-password page as a centred card using the shared form field component.
- Rebuilt the confirmation page with a success message and a link back to the start page.
- Added small page CSS for the card width.
- Checked each state (empty, wrong old password, weak new password, mismatch, success) against the real pages with a throw-away test run.

## What a human checked
- Reviewed the diff and the six checks.
- Browser checklist and screenshots: to be done by the developer before the PR.

## Follow-ups
- The password rules help text is a list, and the shared form field wraps help text in a paragraph; this needs a small fix in the shared component.
