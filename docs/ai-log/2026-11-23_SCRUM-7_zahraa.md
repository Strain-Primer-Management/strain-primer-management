# SCRUM-7 — Form and feedback components

- **Date:** 2026-11-23
- **Developer:** Zahraa
- **AI tool / model:** Claude Code / Claude Sonnet 5.5
- **PR:** #<number>

## What was asked
Build the shared form and feedback pieces once, so every form looks and behaves the same: a form field component, buttons, message styles and a card container.

## What the AI did
- Added a reusable form field component (label, required marker, input, help text, errors).
- Restyled the messages component for info, success, warning and error.
- Added shared styles for form fields (normal, focus, error, disabled), buttons and a card, using only the existing design tokens plus a few new ones.

## What a human checked
- Reviewed the diff and the six checks.
- Browser checklist and screenshot: to be done by the developer before the PR.

## Follow-ups
- Checkbox and radio fields are not styled specially yet; add when a form needs them.
