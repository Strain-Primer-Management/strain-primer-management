# Wave 3: search and filter

Create these when the three list pages exist (wave 2: Primer, Plasmid and Strain pages merged).
The client's main wish is "find things fast", so this wave matters more than it looks.

Conventions for the whole wave
- Search and filters use GET parameters in the address (for example `/strains/?q=pET&host=E.+coli&page=2`),
  so every result page can be bookmarked and shared.
- One query-building method per entity, written ONCE in a queryset class in the app's models file area
  (decision: views never build filters by hand).
- Search is case-insensitive and ignores leading/trailing spaces. Empty search = show everything.
- The same page size (25) and the same sort parameter name (`sort`, with a leading `-` for descending).
- Live search (no page reload) is an EXTRA on top of normal search. The page must still work with
  JavaScript turned off.

---

# BACKEND

## W3-B1: Search and filter methods per entity

```text
Summary: Search and filter methods for primers, plasmids and strains
Zone: Backend
Depends on: Primer pages, Plasmid pages, Strain pages
Files allowed (optional): apps/primers/, apps/plasmids/, apps/strains/ (models/querysets, forms, tests)

In plain words (for beginners)
A "queryset" is Django's way of asking the database a question. We write the questions ("find primers whose name or sequence contains this text") once, as methods with clear names, and the views simply call them. That keeps the pages short and the rules in one place.

What
- Per entity a queryset method `search(text)`: case-insensitive "contains" on the main text fields
  - primers: primer_id, purpose, sequence, freezer_location
  - plasmids: plasmid_name, resistance_markers, description
  - strains: strain_id, host_organism, genotype, freezer_location
  Several words mean ALL words must match (AND). A word may match in any of the fields.
- Per entity filter methods, one per filter, each ignoring an empty value:
  - primers: purpose, has_plasmid (yes/no)
  - plasmids: resistance marker, copy number, size range (min/max)
  - strains: host organism, biosafety level, culturing temperature range, plasmid (strain carries plasmid X), parent strain
- A FilterForm per entity (Django form, not required fields) that validates the GET parameters and returns the filtered queryset.
- Wrong input (letters in a size box) shows a form error and is ignored, it never crashes the page.

Contract for the frontend (view docstrings)
- Parameters: `q`, the filter names above, `sort`, `page`.
- Context: `filter_form` (fields to render), `result_count`, `active_filters` (list of label + value + the address that removes it).

Acceptance criteria
- [ ] Tests for every search field and every filter, empty input, wrong input, multi-word search, capital letters.
- [ ] A test with 3 records shows that only the right ones come back.
- [ ] Six checks green.
Out of scope: templates, JavaScript, global search.
```

## W3-B2: Sorting and pagination that keep the search

```text
Summary: Sorting and pagination that keep search and filters
Zone: Backend (the helper lives in apps/core: SHARED, announce first)
Depends on: Search and filter methods
Files allowed (optional): apps/core/, the three list views, tests

In plain words (for beginners)
If you search for "pET", go to page 2 and the search disappears, that is a bug. Also people want to click a column title to sort. This ticket makes page numbers and sorting remember the search.

What
- A shared helper that takes the current GET parameters and builds new addresses: "page 3", "sort by size", "remove this filter" (always keeping the other parameters).
- Allowed sort columns are a fixed list per entity (a whitelist). Any other `sort` value is ignored (safety: never pass raw text to the database).
- Default sort: newest first (or by name, decide once and write it in the docstring).
- Context for the frontend: `querystring_without_page`, `sort_links` (column -> address, current direction).

Acceptance criteria
- [ ] Tests: page 2 keeps `q` and filters; unknown sort ignored; descending sort works; going out of range gives the last page, not an error.
- [ ] Six checks green.
```

## W3-B3: Global search across all three kinds

```text
Summary: Global search page across strains, plasmids and primers
Zone: Backend (SHARED: apps/core, announce to the other backend dev first)
Depends on: Search and filter methods
Files allowed (optional): apps/core/views.py, apps/core/urls.py, apps/core/tests/

In plain words (for beginners)
A person looking for "pUC19" often does not know whether it is a plasmid or the name inside a strain. One search box in the top bar searches everything and shows results grouped by kind.

What
- URL name `core:search`, parameter `q`. Uses the three `search()` methods (never new query code here).
- At most 10 results per kind, with a "see all N" address into the full list page with the same `q`.
- Needs the view permission of each kind: kinds the user may not view are skipped.
- Fewer than 2 characters: no search, a friendly hint.

Contract for the frontend
- Context: `q`, `results` = list of groups (kind label, items, total, list_url), `too_short`.

Acceptance criteria
- [ ] Tests: results grouped correctly; empty and short search; a user without a permission does not see that group; capital letters.
- [ ] Six checks green.
```

## W3-B4: Live search endpoint (JSON)

```text
Summary: Live search JSON endpoint
Zone: Backend (SHARED: apps/core, announce to the other backend dev first)
Depends on: Global search page
Files allowed (optional): apps/core/api.py, apps/core/urls.py, apps/core/tests/

In plain words (for beginners)
"Live search" shows suggestions while you type, without reloading the page. The browser asks a small web address and gets JSON back (JSON is just structured text a program can read). This ticket builds that address; the frontend ticket builds the typing box.

What
- URL name `core:search_api`, GET only, parameter `q`, login required like everything else.
- Returns JSON with the SAME grouping rules as the global search but small: at most 5 results per kind.
- Uses Django's JsonResponse. Never build JSON by hand.
- Wrong or empty input returns an empty result, never an error page.

Contract for the frontend (this exact shape, also in the docstring)
  { "q": "puc",
    "groups": [
      { "kind": "plasmid", "label": "Plasmids", "total": 12,
        "items": [ { "id": 7, "title": "pUC19", "subtitle": "2686 bp, AmpR", "url": "/plasmids/7/" } ] }
    ] }

Acceptance criteria
- [ ] Tests: shape is exactly as above; anonymous request is redirected or refused (never data); permission skipping; at most 5 per kind.
- [ ] Six checks green.
```

## W3-B5: Search performance and indexes

```text
Summary: Search performance: indexes and query count
Zone: Backend
Depends on: Search and filter methods, Global search page
Files allowed (optional): apps/*/models.py (Meta indexes), apps/*/migrations/ (follow the migration rules!), apps/*/tests/, apps/core/management/commands/

In plain words (for beginners)
With 50 records everything is fast. With 5000 it can become slow if the database has to look at every row. An "index" is like the index of a book: it lets the database jump straight to the answer. We measure first, then add only the indexes we need.

What
- Extend the fake data command with a bigger size (for example `--size large`: 5000 strains, 2000 plasmids, 5000 primers, with links). Development only.
- Add tests that assert the number of database queries on each list page and the detail pages (use `assertNumQueries`), fixing N+1 problems with select_related / prefetch_related.
- Measure the search with the large data set. If a search takes longer than 200 ms, add the indexes (or trigram indexes with the Postgres pg_trgm extension, which needs a lead-approved migration step) and show before/after numbers in the pull request.
- Follow the migration rules: one open migration pull request for the app, never edit a merged migration.

Acceptance criteria
- [ ] Query counts are fixed and tested (do not grow with the number of rows).
- [ ] Before/after timings in the pull request.
- [ ] Six checks green.
```

---

# FRONTEND

## W3-F-MAIN: Search and filter experience (parent ticket)

```text
Summary: Search and filter experience (parent)
Zone: Frontend

In plain words (for beginners)
This is the feature the lab will use every day: type a few letters, find the strain. It must feel fast, clear and forgiving. You build on the backend contract (parameters and context variables in the view docstrings).

Sub-tasks
  1. W3-F1 Search bar component in the top bar                  (SHARED FILES)
  2. W3-F2 Filter panel component and per-entity filter layouts
  3. W3-F3 Sortable column headers and active-filter chips
  4. W3-F4 Global search results page
  5. W3-F5 Live search dropdown (JavaScript)
  6. W3-F6 Search states: empty, loading, error, too short, no results

Definition of done for the parent
From any page a person can search, open a result, narrow a list with filters, share the address of the result, and everything still works without JavaScript.

Things to take care of
- Search is a normal <form method="get">; JavaScript only adds speed.
- Keep what the user typed in the box after searching; show the number of results.
- Labels for every input; the search input has type="search" and an accessible name.
- Matches may be highlighted with the <mark> element (done in the template filter, never with innerHTML on user text).
- All earlier frontend rules apply (plain CSS, no CDN, no inline styles, keyboard use, English only).
```

## W3-F1: Search bar in the top bar (shared files)

```text
Summary: Search bar component in the top bar
Zone: Frontend (SHARED FILES: announce first)
Depends on: Global search page (backend), Design foundation
Files allowed (optional): templates/components/search_bar.html, templates/base.html (nav part only), static/css/base.css

What
- A search form in the top navigation on every page (GET to core:search, input name `q`), keeping the current text on the results page.
- On small screens it moves below the menu (no horizontal scroll).
Acceptance criteria
- [ ] Works with keyboard only (Tab, Enter); a screenshot at desktop and phone width.
```

## W3-F2: Filter panel

```text
Summary: Filter panel and filter layouts for the three lists
Zone: Frontend
Depends on: Search and filter methods (backend), Shared list layout (wave 2)
Files allowed (optional): templates/components/filter_panel.html, templates/primers/, templates/plasmids/, templates/strains/, static/css/pages/*-filters.css

In plain words (for beginners)
Filters are small controls above the table (dropdowns, number boxes) that shrink the list. One generic panel component draws the fields the backend gives us; each list page only chooses which fields appear.

What
- components/filter_panel.html rendering `filter_form`, with an "Apply" button and a "Clear all" link.
- Collapsible on narrow screens using <details>/<summary> (no JavaScript needed).
- Range filters (size, temperature) as "from" and "to" boxes side by side.
Acceptance criteria
- [ ] Used on all three lists; keeps values after submitting; form errors shown next to the field; works without JavaScript.
```

## W3-F3: Sortable headers and filter chips

```text
Summary: Sortable column headers and active-filter chips
Zone: Frontend
Depends on: Sorting and pagination that keep search (backend), Filter panel
Files allowed (optional): templates/components/, static/css/pages/ (list-page CSS; shared look goes in base.css only via a shared ticket)

What
- Column titles are links using `sort_links`; the current column shows an arrow and an accessible text ("sorted ascending").
- A row of "chips" for the active filters; each has a small remove link (`active_filters`) with an accessible label ("Remove filter host: E. coli").
- Page numbers use `querystring_without_page` so they never lose the search.
Acceptance criteria
- [ ] Keyboard and screen-reader text checked; sorting and paging keep search and filters on all three lists.
```

## W3-F4: Global search results page

```text
Summary: Global search results page
Zone: Frontend
Depends on: Global search page (backend), Search bar component
Files allowed (optional): templates/core/search.html, static/css/pages/core-search.css

What
- Groups with headings (Strains, Plasmids, Primers), each result a link with title and subtitle, a "see all N" link per group, the count of results, the typed text kept in the box.
- States: nothing typed, too short (hint), no results (helpful text: check the spelling, try fewer letters), results.
Acceptance criteria
- [ ] All states shown in the pull request; matches highlighted safely.
```

## W3-F5: Live search dropdown (JavaScript)

```text
Summary: Live search dropdown while typing
Zone: Frontend
Depends on: Live search JSON endpoint (backend), Search bar component
Files allowed (optional): static/js/pages/core-live-search.js, static/css/pages/core-live-search.css, templates/components/search_bar.html (SHARED: announce first)

In plain words (for beginners)
While the user types, a small box under the input shows the best matches. JavaScript sends the text to the JSON address and draws the answer. "Debounce" means waiting about 250 ms after the last key so we do not ask the server on every single letter.

What
- Plain JavaScript file (no libraries, no CDN). Debounce 250 ms; cancel the previous request when a new one starts (AbortController).
- Draw results with textContent (never innerHTML with user text, to avoid XSS).
- Accessibility: role="listbox"/"option" or a simple list with aria-live="polite" announcing "N results"; arrow keys move, Enter opens, Escape closes; focus never trapped.
- If JavaScript fails or the address errors: the normal form submit still works and a short message appears.
Acceptance criteria
- [ ] Works with the mouse and keyboard only; slow network and error states checked (browser dev tools "Slow 3G", offline).
- [ ] No console errors; the page works with JavaScript disabled.
```

## W3-F6: Search states

```text
Summary: Search states: empty, loading, error, too short
Zone: Frontend
Depends on: Live search dropdown, Global search results page

What
- A short consistent wording and style for each state, reused by the list pages, the global page and the dropdown (components, no copy-paste).
- Loading indicator in plain CSS (no GIF); respects "reduce motion".
Acceptance criteria
- [ ] Screenshot of each state; the same component used everywhere.
```
