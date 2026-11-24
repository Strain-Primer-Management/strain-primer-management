// Live search dropdown (SCRUM-138): while you type in the search bar, a box under the input shows
// the best matches from the JSON endpoint core:search_api. Plain JavaScript, no libraries.
//
// Without JavaScript, or when this fails, the search form still works: press Enter or the button.
// The endpoint (GET /api/search/?q=...) answers { q, groups: [ { kind, label, total,
// items: [ { id, title, subtitle, url } ] } ] }. Everything is drawn with textContent, never with
// innerHTML, so the text of a record can never run as code.

const DEBOUNCE_MS = 250; // wait this long after the last key before asking the server
const MIN_LENGTH = 2; // the backend returns nothing for shorter text

function initLiveSearch() {
  const form = document.querySelector(".search-bar");
  const input = form && form.querySelector("input[name='q']");
  if (!form || !input || !form.dataset.apiUrl) return;

  // The box that holds the suggestions, and a hidden line that screen readers announce.
  const list = document.createElement("ul");
  list.id = "live-search-list";
  list.className = "live-search-list";
  list.setAttribute("role", "listbox");
  list.setAttribute("aria-label", "Search suggestions");
  list.hidden = true;
  const status = document.createElement("p");
  status.className = "visually-hidden";
  status.setAttribute("role", "status");
  status.setAttribute("aria-live", "polite");
  form.append(list, status);

  // Tell assistive technology that the input controls the list. Focus always stays in the input.
  input.setAttribute("role", "combobox");
  input.setAttribute("aria-autocomplete", "list");
  input.setAttribute("aria-controls", list.id);
  input.setAttribute("aria-expanded", "false");
  input.setAttribute("autocomplete", "off");

  let timer = null; // the 250 ms wait
  let controller = null; // lets us cancel the request that is still running
  let options = []; // the <li role="option"> rows that can be chosen
  let active = -1; // index of the chosen row, -1 = none

  function announce(text) {
    status.textContent = text;
  }

  function close() {
    list.hidden = true;
    list.replaceChildren();
    options = [];
    setActive(-1);
    input.setAttribute("aria-expanded", "false");
  }

  function open() {
    list.hidden = false;
    input.setAttribute("aria-expanded", "true");
  }

  function setActive(index) {
    active = index;
    options.forEach((option, i) => {
      option.setAttribute("aria-selected", i === index ? "true" : "false");
      option.classList.toggle("is-active", i === index);
    });
    if (index >= 0) {
      input.setAttribute("aria-activedescendant", options[index].id);
      options[index].scrollIntoView({ block: "nearest" });
    } else {
      input.removeAttribute("aria-activedescendant");
    }
  }

  // A line of text that is not a result: "Searching…", "No results" or the error message.
  function showMessage(text) {
    list.replaceChildren();
    options = [];
    setActive(-1);
    const item = document.createElement("li");
    item.className = "live-search-message";
    item.setAttribute("role", "presentation");
    item.textContent = text;
    list.append(item);
    open();
  }

  function makeOption(index, href) {
    const option = document.createElement("li");
    option.id = `live-search-option-${index}`;
    option.className = "live-search-option";
    option.setAttribute("role", "option");
    option.setAttribute("aria-selected", "false");
    const link = document.createElement("a");
    link.href = href;
    link.tabIndex = -1; // the arrow keys move through the rows; Tab keeps its normal order
    option.append(link);
    return { option, link };
  }

  function render(data, q) {
    list.replaceChildren();
    options = [];
    const total = data.groups.reduce((sum, group) => sum + group.total, 0);
    if (total === 0) {
      showMessage(`No results for "${q}"`);
      announce("No results");
      return;
    }
    data.groups.forEach((group) => {
      const heading = document.createElement("li");
      heading.className = "live-search-heading";
      heading.setAttribute("role", "presentation");
      heading.textContent = `${group.label} (${group.total})`;
      list.append(heading);
      group.items.forEach((item) => {
        const { option, link } = makeOption(options.length, item.url);
        const title = document.createElement("span");
        title.className = "live-search-title";
        title.textContent = item.title;
        link.append(title);
        if (item.subtitle) {
          const subtitle = document.createElement("span");
          subtitle.className = "live-search-subtitle";
          subtitle.textContent = item.subtitle;
          link.append(subtitle);
        }
        options.push(option);
        list.append(option);
      });
    });
    // The last row opens the full results page with the same text.
    const all = makeOption(options.length, `${form.action}?${new URLSearchParams({ q })}`);
    all.option.classList.add("live-search-all");
    all.link.textContent = `See all results for "${q}"`;
    options.push(all.option);
    list.append(all.option);
    setActive(-1);
    open();
    announce(`${total} ${total === 1 ? "result" : "results"}. Use the up and down arrow keys.`);
  }

  async function search(q) {
    if (controller) controller.abort(); // only the newest request counts
    const mine = new AbortController();
    controller = mine;
    showMessage("Searching…");
    try {
      const url = `${form.dataset.apiUrl}?${new URLSearchParams({ q })}`;
      const response = await fetch(url, {
        signal: mine.signal,
        headers: { Accept: "application/json" },
      });
      // A redirect (logged out) or an error page is not the JSON we expect.
      const isJson = (response.headers.get("content-type") || "").includes("application/json");
      if (!response.ok || response.redirected || !isJson) throw new Error("Unexpected answer");
      const data = await response.json();
      if (input.value.trim() !== q) return; // the text changed while we waited
      render(data, q);
    } catch (error) {
      if (error.name === "AbortError") return;
      showMessage("Suggestions are not available. Press Enter to search.");
      announce("Suggestions are not available. Press Enter to search.");
    }
  }

  input.addEventListener("input", () => {
    clearTimeout(timer);
    if (controller) controller.abort();
    const q = input.value.trim();
    if (q.length < MIN_LENGTH) {
      close();
      announce("");
      return;
    }
    timer = setTimeout(() => search(q), DEBOUNCE_MS);
  });

  input.addEventListener("keydown", (event) => {
    const isOpen = !list.hidden;
    if (event.key === "Escape" && isOpen) {
      event.preventDefault(); // also stops the browser from clearing the box
      close();
    } else if ((event.key === "ArrowDown" || event.key === "ArrowUp") && options.length) {
      event.preventDefault();
      const step = event.key === "ArrowDown" ? 1 : -1;
      setActive((active + step + options.length) % options.length);
    } else if (event.key === "Enter" && active >= 0) {
      event.preventDefault(); // open the chosen row instead of sending the form
      window.location.assign(options[active].querySelector("a").href);
    }
  });

  // Keep the focus in the input when a row is clicked, then let the link open normally.
  list.addEventListener("mousedown", (event) => event.preventDefault());

  // Close when the focus leaves the search bar (Tab or a click elsewhere).
  form.addEventListener("focusout", (event) => {
    if (!form.contains(event.relatedTarget)) close();
  });

  // Sending the form (Enter with no chosen row, or the button) cancels any waiting suggestion.
  form.addEventListener("submit", () => {
    clearTimeout(timer);
    if (controller) controller.abort();
    close();
  });

  // Coming back with the browser's Back button must not show an old box.
  window.addEventListener("pageshow", (event) => {
    if (event.persisted) close();
  });
}

initLiveSearch();
