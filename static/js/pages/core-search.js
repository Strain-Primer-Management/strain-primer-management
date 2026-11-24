// Search results page: wrap the typed text in <mark> inside the result names and subtitles.
// Plain JavaScript; without it the page still works, just without the highlight.
// Safe by design: the text is split and rebuilt with text nodes and textContent, never innerHTML,
// so a record name can never run as HTML.
const container = document.querySelector(".search-results");
const query = container ? container.dataset.query.trim().toLowerCase() : "";

function highlight(element) {
  const text = element.textContent;
  const lower = text.toLowerCase();
  // Some characters change length in lower case; then the positions would be wrong, so skip.
  if (lower.length !== text.length) {
    return;
  }
  const parts = document.createDocumentFragment();
  let start = 0;
  let found = lower.indexOf(query, start);
  if (found === -1) {
    return;
  }
  while (found !== -1) {
    parts.append(text.slice(start, found));
    const mark = document.createElement("mark");
    mark.textContent = text.slice(found, found + query.length);
    parts.append(mark);
    start = found + query.length;
    found = lower.indexOf(query, start);
  }
  parts.append(text.slice(start));
  element.replaceChildren(parts);
}

if (query) {
  container.querySelectorAll("[data-highlight]").forEach(highlight);
}
