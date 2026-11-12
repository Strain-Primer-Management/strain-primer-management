"""Builds a Jira CSV import file from the ticket files in docs/tickets/ (lead tool).

Usage (run it from this folder or from the repository root):
    python docs/tickets/tickets_to_csv.py                  all waves except wave 1 (already in Jira)
    python docs/tickets/tickets_to_csv.py --waves 2,3      only these waves
    python docs/tickets/tickets_to_csv.py --waves 2 --out wave2.csv
    python docs/tickets/tickets_to_csv.py --sprint-ids 0=101,2=102,3=103

Tickets come out in creation order: wave by wave, in the order of the files, so Jira
numbers them in that order. Every ticket has the labels wave-N, its plan ID (for example
w2-b1) and its zone, and the component Backend, Frontend or Lead. A frontend parent ticket
(W2-F-MAIN ...) is a Task and its tickets (W2-F1, W2-F2 ...) are Sub-tasks that point at it
through the Parent column, so the parent always comes first. Links between tickets are NOT
imported (Jira Cloud's importer is unreliable for them): each description keeps its
"Depends on:" line, which uses ticket titles.

Sprints: the team uses one sprint per wave. Jira's CSV import cannot create sprints and wants the
sprint's numeric ID, not its name, so create the sprints first and pass their IDs here (wave=ID).
Waves without an ID get an empty Sprint cell.
"""

import argparse
import csv
import re
from pathlib import Path

TICKETS = Path(__file__).resolve().parent
DEFAULT_OUT = TICKETS / "jira-import.csv"
WAVE_FILES = {
    0: "wave-0-lead-and-team-tasks.md",
    2: "wave-2-browse-and-edit-records.md",
    3: "wave-3-search-and-filter.md",
    4: "wave-4-lab-features.md",
    5: "wave-5-data-import-export-backup.md",
    6: "wave-6-quality-security-docs.md",
    7: "wave-7-deployment-and-go-live.md",
}
# Wave 1 (database, accounts, login) was created in Jira first, so it is not in the default output.
LABEL_COLUMNS = 4
HEADING = re.compile(r"^## (?P<id>[A-Z0-9]+(?:-[A-Z0-9]+)*): (?P<title>.+)$")
CHILD = re.compile(r"^(?P<prefix>W\d+)-F\d+$")


def to_wiki(line: str) -> str:
    """Make one text line safe for Jira's description (check boxes, braces and brackets)."""
    line = line.replace("[ ]", "☐").replace("[x]", "☑").replace("[X]", "☑")
    for char in "{}[]":
        line = line.replace(char, "\\" + char)
    return line


def component_for(zone: str) -> str:
    """Backend, Frontend or Lead from the ticket's Zone line ('' if it is none of them)."""
    for name in ("Frontend", "Backend", "Lead"):
        if name.lower() in zone.lower():
            return name
    return ""


def parse_wave(wave: int, filename: str) -> list[dict]:
    """Return the tickets of one wave file: every '## ID: title' heading with its text box."""
    tickets = []
    current = None
    box = None
    for line in (TICKETS / filename).read_text(encoding="utf-8").splitlines():
        match = HEADING.match(line)
        if match:
            current = {"id": match["id"], "heading": match["title"], "wave": wave, "lines": []}
            continue
        if current is None:
            continue
        if line.strip() == "```text" and box is None:
            box = current["lines"]
        elif line.strip() == "```" and box is not None:
            tickets.append(current)
            current, box = None, None
        elif box is not None:
            box.append(line)
    return tickets


def parent_id_for(ticket: dict, known_ids: set[str]) -> str | None:
    """The plan ID of the parent (for example W2-F-MAIN for W2-F3), if that parent exists."""
    match = CHILD.match(ticket["id"])
    if match and f"{match['prefix']}-F-MAIN" in known_ids:
        return f"{match['prefix']}-F-MAIN"
    return None


def parse_sprint_ids(text: str) -> dict[int, str]:
    """'0=101,2=102' becomes {0: '101', 2: '102'} (wave number to Jira sprint ID)."""
    ids = {}
    for part in filter(None, text.split(",")):
        wave, _, sprint_id = part.partition("=")
        if not wave.strip().isdigit() or not sprint_id.strip().isdigit():
            raise SystemExit(f"--sprint-ids wants pairs like 0=101,2=102, got {part!r}")
        ids[int(wave)] = sprint_id.strip()
    return ids


def build_row(
    number: int, ticket: dict, parent_number: int | None, sprint_ids: dict[int, str]
) -> list[str]:
    """One CSV row: id, summary, type, parent, description, labels, component, sprint."""
    lines = ticket["lines"]
    summary = next(
        (line.split(":", 1)[1].strip() for line in lines if line.startswith("Summary:")),
        ticket["heading"],
    )
    zone = next((line.split(":", 1)[1].strip() for line in lines if line.startswith("Zone:")), "")
    body = [line for line in lines if not line.startswith("Summary:")]
    description = "\n".join([f"Plan ID: {ticket['id']} (wave {ticket['wave']})", ""] + body)
    labels = [f"wave-{ticket['wave']}", ticket["id"].lower()]
    component = component_for(zone)
    if component:
        labels.append(component.lower())
    elif zone:
        labels.append(zone.split()[0].lower())  # for example "team" (no component for those)
    if "WAITING" in ticket["heading"] or "client answers" in description:
        labels.append("waiting-client")
    labels += [""] * (LABEL_COLUMNS - len(labels))
    wiki = "\n".join(to_wiki(line) for line in description.splitlines()).strip()
    issue_type = "Sub-task" if parent_number else "Task"
    parent = str(parent_number) if parent_number else ""
    sprint = sprint_ids.get(ticket["wave"], "")
    cells = [str(number), summary, issue_type, parent, wiki, *labels[:LABEL_COLUMNS]]
    return [*cells, component, sprint]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--waves", default="0,2,3,4,5,6,7", help="comma-separated wave numbers")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--sprint-ids", default="", help="wave=sprint ID pairs, e.g. 0=101,2=102")
    args = parser.parse_args()
    sprint_ids = parse_sprint_ids(args.sprint_ids)
    waves = [int(part) for part in args.waves.split(",")]

    tickets = [ticket for wave in waves for ticket in parse_wave(wave, WAVE_FILES[wave])]
    numbers = {ticket["id"]: number for number, ticket in enumerate(tickets, start=1)}
    rows = []
    for number, ticket in enumerate(tickets, start=1):
        parent_id = parent_id_for(ticket, set(numbers))
        parent_number = numbers[parent_id] if parent_id else None
        if parent_number and parent_number > number:
            raise SystemExit(f"{ticket['id']} comes before its parent {parent_id}; fix the order")
        rows.append(build_row(number, ticket, parent_number, sprint_ids))

    header = ["Issue id", "Summary", "Issue Type", "Parent", "Description"]
    header += ["Labels"] * LABEL_COLUMNS + ["Component/s", "Sprint"]
    with args.out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")  # LF, as the repository requires
        writer.writerow(header)
        writer.writerows(rows)
    subtasks = sum(1 for row in rows if row[2] == "Sub-task")
    print(f"wrote {len(rows)} tickets ({subtasks} of them sub-tasks) to {args.out}")


if __name__ == "__main__":
    main()
