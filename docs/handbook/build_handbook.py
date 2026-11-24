"""
Builds docs/TEAM_HANDBOOK.pdf (setup + how to do your job).

LEAD-ONLY, optional tool. It needs a package that is NOT a project dependency:
    pip install reportlab
    python docs/handbook/build_handbook.py

The PDF is only a friendly snapshot. The real rules live in the Markdown files
(CONTRIBUTING.md, docs/ONBOARDING.md, docs/PROMPTING_GUIDE.md, AGENTS.md). When they change,
update the text below and rebuild. Keep the text ASCII-friendly: the built-in PDF fonts have no
arrows, check marks or emoji.
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)

OUT = Path(__file__).resolve().parent.parent / "TEAM_HANDBOOK.pdf"
REPO = "https://github.com/Strain-Primer-Management/strain-primer-management"

TEAL = colors.HexColor("#0F6B5C")
TEAL_LIGHT = colors.HexColor("#E3F1EE")
BLUE = colors.HexColor("#1F5FBF")
BLUE_LIGHT = colors.HexColor("#E6EEFA")
AMBER = colors.HexColor("#B7791F")
AMBER_LIGHT = colors.HexColor("#FDF3DC")
RED = colors.HexColor("#B42318")
RED_LIGHT = colors.HexColor("#FDECEA")
GREY = colors.HexColor("#5B6B67")
GREY_LIGHT = colors.HexColor("#F1F4F3")
INK = colors.HexColor("#1B2A27")
LINE = colors.HexColor("#D6DEDB")

PAGE_W, PAGE_H = A4
MARGIN = 1.9 * cm
CONTENT_W = PAGE_W - 2 * MARGIN

# ---------------------------------------------------------------- styles
base = ParagraphStyle("base", fontName="Helvetica", fontSize=10, leading=14.5, textColor=INK)
S = {
    "body": ParagraphStyle("body", parent=base, spaceAfter=6, alignment=TA_LEFT),
    "small": ParagraphStyle("small", parent=base, fontSize=8.5, leading=12, textColor=GREY),
    "cell": ParagraphStyle("cell", parent=base, fontSize=9, leading=12.5),
    "cellb": ParagraphStyle(
        "cellb", parent=base, fontSize=9, leading=12.5, fontName="Helvetica-Bold"
    ),
    "head": ParagraphStyle(
        "head",
        parent=base,
        fontSize=9,
        leading=12,
        fontName="Helvetica-Bold",
        textColor=colors.white,
    ),
    "h1": ParagraphStyle(
        "h1",
        parent=base,
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=TEAL,
        spaceBefore=4,
        spaceAfter=8,
    ),
    "h2": ParagraphStyle(
        "h2",
        parent=base,
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=INK,
        spaceBefore=12,
        spaceAfter=4,
    ),
    "h3": ParagraphStyle(
        "h3",
        parent=base,
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=TEAL,
        spaceBefore=8,
        spaceAfter=2,
    ),
    "bullet": ParagraphStyle("bullet", parent=base, leftIndent=14, bulletIndent=3, spaceAfter=2.5),
    "num": ParagraphStyle("num", parent=base, leftIndent=18, bulletIndent=0, spaceAfter=3),
    "code": ParagraphStyle("code", fontName="Courier", fontSize=8.4, leading=11.2, textColor=INK),
}


# Never leave a heading alone at the bottom of a page.
for _name in ("h1", "h2", "h3"):
    S[_name].keepWithNext = 1


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def P(text, style="body"):
    return Paragraph(text, S[style])


def bullets(items, style="bullet"):
    return [Paragraph(t, S[style], bulletText="\u2022") for t in items]


def numbered(items):
    return [Paragraph(t, S["num"], bulletText=f"{i}.") for i, t in enumerate(items, 1)]


def code(text, width=CONTENT_W):
    box = Table([[Preformatted(text.strip("\n"), S["code"])]], colWidths=[width])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), GREY_LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return [box, Spacer(1, 7)]


def callout(kind, title, text):
    fg, bg = {"tip": (TEAL, TEAL_LIGHT), "warn": (AMBER, AMBER_LIGHT), "stop": (RED, RED_LIGHT)}[
        kind
    ]
    body = Paragraph(f"<b>{title}</b><br/>{text}", S["cell"])
    box = Table([[body]], colWidths=[CONTENT_W])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), bg),
                ("LINEBEFORE", (0, 0), (0, -1), 3.5, fg),
                ("LEFTPADDING", (0, 0), (-1, -1), 11),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return [KeepTogether([box]), Spacer(1, 7)]


def table(rows, widths, header=True, zebra=True):
    data = []
    for r, row in enumerate(rows):
        cells = []
        for c, value in enumerate(row):
            style = "head" if header and r == 0 else ("cellb" if c == 0 else "cell")
            cells.append(Paragraph(value, S[style]))
        data.append(cells)
    t = Table(data, colWidths=[w * CONTENT_W for w in widths], repeatRows=1 if header else 0)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
    ]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), TEAL))
    if zebra:
        for r in range(1 if header else 0, len(data)):
            if r % 2 == 0:
                style.append(("BACKGROUND", (0, r), (-1, r), GREY_LIGHT))
    t.setStyle(TableStyle(style))
    return [t, Spacer(1, 8)]


def checklist(items):
    return [Paragraph(t, S["bullet"], bulletText="[  ]") for t in items]


# ---------------------------------------------------------------- setup steps
S["stepnum"] = ParagraphStyle(
    "stepnum",
    parent=base,
    fontName="Helvetica-Bold",
    fontSize=26,
    leading=28,
    textColor=TEAL,
    alignment=TA_CENTER,
)
S["steptitle"] = ParagraphStyle(
    "steptitle", parent=base, fontName="Helvetica-Bold", fontSize=13, leading=17, spaceAfter=3
)
STEP_NUM_W = 1.35 * cm
STEP_INNER_W = CONTENT_W - STEP_NUM_W


def note(label, text, fg, bg):
    """A small coloured line used for 'YOU SHOULD SEE' and 'IF NOT'."""
    para = Paragraph(
        f'<font color="{fg.hexval().replace("0x", "#")}"><b>{label}</b></font>&nbsp;&nbsp;{text}',
        S["cell"],
    )
    box = Table([[para]], colWidths=[STEP_INNER_W])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), bg),
                ("LINEBEFORE", (0, 0), (0, -1), 3, fg),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return [Spacer(1, 3), box, Spacer(1, 3)]


def step(number, title, doing, see=None, ifnot=None):
    """One big setup step: the number on the left; do / you should see / if not on the right."""
    inner = [P(title, "steptitle"), *doing]
    if see:
        inner += note("YOU SHOULD SEE", see, TEAL, TEAL_LIGHT)
    if ifnot:
        inner += note("IF NOT", ifnot, AMBER, AMBER_LIGHT)
    row = Table([[P(str(number), "stepnum"), inner]], colWidths=[STEP_NUM_W, STEP_INNER_W])
    row.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.6, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return KeepTogether([row])


S["oslabel"] = ParagraphStyle(
    "oslabel",
    parent=base,
    fontName="Helvetica-Bold",
    fontSize=8.5,
    leading=11,
    textColor=TEAL,
    spaceBefore=5,
    spaceAfter=2,
)


def oscode(label, text):
    """A code box labelled with the system it is for (Windows / macOS / Linux)."""
    return [P(label, "oslabel"), *code(text, STEP_INNER_W)]


def bigstep(number, title, groups, see=None, ifnot=None):
    """Like step(), but the content is several groups that may flow over a page break."""
    notes = []
    if see:
        notes += note("YOU SHOULD SEE", see, TEAL, TEAL_LIGHT)
    if ifnot:
        notes += note("IF NOT", ifnot, AMBER, AMBER_LIGHT)
    blocks = [list(group) for group in groups] + ([notes] if notes else [])
    flow = []
    for i, block in enumerate(blocks):
        first, last = i == 0, i == len(blocks) - 1
        inner = ([P(title, "steptitle")] if first else []) + block
        number_cell = P(str(number), "stepnum") if first else ""
        row = Table([[number_cell, inner]], colWidths=[STEP_NUM_W, STEP_INNER_W])
        style = [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 8 if first else 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8 if last else 2),
        ]
        if last:
            style.append(("LINEBELOW", (0, 0), (-1, -1), 0.6, LINE))
        row.setStyle(TableStyle(style))
        flow.append(KeepTogether([row]))
    return flow


# ---------------------------------------------------------------- diagram
class FlowDiagram(Flowable):
    """The 10-step journey of one ticket. Colour = who acts."""

    STEPS = [
        ("1  Ticket", "in Jira (SCRUM-n)", "team"),
        ("2  Start Claude Code", "name + ticket text", "you"),
        ("3  Plan", "Claude checks, you read", "ai"),
        ('4  Say "go"', "checkpoint 1", "you"),
        ("5  Claude builds", "branch, code, tests", "ai"),
        ('6  Say "ship it"', "checkpoint 2", "you"),
        ("7  Pull request", "Claude pushes + opens", "ai"),
        ("8  Checks + review", "CI + teammate approve", "team"),
        ("9  Merge", "author clicks Squash", "you"),
        ("10  Done", "Jira to Done", "you"),
    ]
    COLORS = {"you": BLUE, "ai": TEAL, "team": GREY}

    def __init__(self, width):
        super().__init__()
        self.width = width
        self.height = 5.6 * cm

    def wrap(self, *_):
        return self.width, self.height

    def draw(self):
        c = self.canv
        gap = 0.32 * cm
        bw = (self.width - 4 * gap) / 5
        bh = 1.55 * cm
        ys = [self.height - bh - 0.1 * cm, 1.25 * cm]

        def box_x(col):
            return col * (bw + gap)

        def arrow(x1, y1, x2, y2):
            c.setStrokeColor(GREY)
            c.setFillColor(GREY)
            c.setLineWidth(1.2)
            c.line(x1, y1, x2, y2)
            # arrow head
            if y1 == y2:
                d = 1 if x2 > x1 else -1
                p = c.beginPath()
                p.moveTo(x2, y2)
                p.lineTo(x2 - d * 4, y2 + 2.5)
                p.lineTo(x2 - d * 4, y2 - 2.5)
                p.close()
                c.drawPath(p, stroke=0, fill=1)
            else:
                p = c.beginPath()
                p.moveTo(x2, y2)
                p.lineTo(x2 - 2.5, y2 + 4)
                p.lineTo(x2 + 2.5, y2 + 4)
                p.close()
                c.drawPath(p, stroke=0, fill=1)

        for i, (title, sub, who) in enumerate(self.STEPS):
            row, col = divmod(i, 5)
            x, y = box_x(col), ys[row]
            c.setFillColor(self.COLORS[who])
            c.roundRect(x, y, bw, bh, 5, stroke=0, fill=1)
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 8.3)
            c.drawCentredString(x + bw / 2, y + bh - 0.62 * cm, title)
            c.setFont("Helvetica", 7.4)
            c.drawCentredString(x + bw / 2, y + 0.42 * cm, sub)
            if col < 4:
                arrow(x + bw, y + bh / 2, x + bw + gap, y + bh / 2)
        # elbow from step 5 down and back to the left to step 6
        x5 = box_x(4) + bw / 2
        x6 = box_x(0) + bw / 2
        ymid = (ys[0] + ys[1] + bh) / 2
        c.setStrokeColor(GREY)
        c.setLineWidth(1.2)
        c.line(x5, ys[0], x5, ymid)
        c.line(x5, ymid, x6, ymid)
        arrow(x6, ymid, x6, ys[1] + bh)
        # legend
        lx = 0
        for who, label in (("you", "you"), ("ai", "Claude Code"), ("team", "team / GitHub")):
            c.setFillColor(self.COLORS[who])
            c.roundRect(lx, 0.1 * cm, 0.45 * cm, 0.3 * cm, 2, stroke=0, fill=1)
            c.setFillColor(INK)
            c.setFont("Helvetica", 8)
            c.drawString(lx + 0.6 * cm, 0.14 * cm, label)
            lx += 3.6 * cm


# ---------------------------------------------------------------- page furniture
def cover(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(TEAL)
    canvas.rect(0, PAGE_H - 11.5 * cm, PAGE_W, 11.5 * cm, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 12)
    canvas.drawString(MARGIN, PAGE_H - 3.2 * cm, "Strain & Primer Management")
    canvas.setFont("Helvetica-Bold", 34)
    canvas.drawString(MARGIN, PAGE_H - 5.4 * cm, "Team Handbook")
    canvas.setFont("Helvetica", 15)
    canvas.drawString(MARGIN, PAGE_H - 6.9 * cm, "Set up your computer, then do your job")
    canvas.setFont("Helvetica", 10.5)
    canvas.drawString(
        MARGIN,
        PAGE_H - 8.4 * cm,
        "For Nour, Lina, Eya, Zahraa and Judy  |  Windows, macOS, Linux  |  backend and frontend",
    )
    canvas.setFillColor(INK)
    canvas.setFont("Helvetica", 10)
    y = PAGE_H - 13.4 * cm
    for line in (
        "Part 1  Set up your computer (once, about 30-45 minutes)",
        "Part 2  How to do your job (every ticket)",
        "Part 3  Reference: checks, red lines, when things go wrong, cheat sheet",
        "Part 4  Git by hand: ready-made commands for every case",
    ):
        canvas.drawString(MARGIN, y, line)
        y -= 0.8 * cm
    canvas.setFillColor(GREY)
    canvas.setFont("Helvetica", 8.5)
    canvas.drawString(MARGIN, 2.2 * cm, "Version 1.0  |  November 2026")
    canvas.drawString(
        MARGIN,
        1.7 * cm,
        "If this PDF and the files in the repository disagree, the files win "
        "(CONTRIBUTING.md and docs/).",
    )
    canvas.restoreState()


def later(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, PAGE_H - 1.35 * cm, PAGE_W - MARGIN, PAGE_H - 1.35 * cm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GREY)
    canvas.drawString(MARGIN, PAGE_H - 1.1 * cm, "Strain & Primer Management  |  Team Handbook")
    canvas.drawRightString(PAGE_W - MARGIN, 1.1 * cm, f"Page {doc.page}")
    canvas.restoreState()


# ---------------------------------------------------------------- content
def build_story():
    st = [PageBreak()]  # page 1 is the cover, drawn by cover()

    # ---- Start here
    st.append(P("Start here", "h1"))
    st.append(
        P(
            "We are building a web tool for a synthetic-biology lab at a university. It replaces "
            "scattered Word files with <b>one database of strains, plasmids and primers</b>, linked to "
            "each other, with fast search, validated input, user logins and backups. The interface is "
            "English only and is used on Windows PCs."
        )
    )
    st.append(P("How we work, in one minute", "h2"))
    st += numbered(
        [
            "<b>One Jira ticket = one branch = one pull request.</b> Small and fast.",
            "<b><b>Claude Code</b> does the Git work.</b> You give it your name and the ticket, and you approve "
            'twice: <b>"go"</b> on its plan, <b>"ship it"</b> on its result.',
            "<b>Stay inside the files your ticket names.</b> Nobody edits another zone.",
            "<b>Nothing reaches <font face='Courier'>main</font></b> without a teammate's approval and green checks.",
            "<b>If you can't explain it, don't ship it.</b> Ask early. The client will ask us to explain our code.",
        ]
    )
    st.append(P("Who is who", "h2"))
    st += table(
        [
            ["Person", "Role", "Works in"],
            [
                "Nour",
                "Backend. Also keeps config, Docker, CI and docs",
                "<font face='Courier'>apps/</font> + lead-only files",
            ],
            ["Lina", "Backend", "<font face='Courier'>apps/</font>"],
            [
                "Eya, Zahraa, Judy",
                "Frontend (shared, no lead)",
                "<font face='Courier'>templates/</font>, <font face='Courier'>static/</font>",
            ],
        ],
        [0.22, 0.46, 0.32],
    )
    st.append(
        P(
            "Nobody owns a folder alone, so <b>the Jira ticket decides which files you may edit</b>, and "
            "two open tickets must never list the same file. Backend and frontend never edit each "
            "other's folders: if you need something from the other side, comment on their ticket."
        )
    )
    st.append(P("Where to find things", "h2"))
    st += table(
        [
            ["What", "Where"],
            ["The code and these documents", f'<link href="{REPO}" color="#1F5FBF">{REPO}</link>'],
            [
                "The task board (project key <b>SCRUM</b>)",
                "The link is pinned in the team chat",
            ],
            [
                "Rules for the team",
                "<font face='Courier'>CONTRIBUTING.md</font>, <font face='Courier'>docs/TEAM.md</font>",
            ],
            ["What the client wants, the data model", "<font face='Courier'>docs/DOMAIN.md</font>"],
            ["Settled decisions", "<font face='Courier'>docs/DECISIONS.md</font>"],
            [
                "How to brief <b>Claude Code</b>",
                "<font face='Courier'>docs/PROMPTING_GUIDE.md</font>",
            ],
            [
                "Stuck with Git? (the helper menu, and Git by hand)",
                "Part 4 of this handbook, <font face='Courier'>tools/git-helper.sh</font>, "
                "<font face='Courier'>docs/GIT_BY_HAND.md</font>",
            ],
        ],
        [0.45, 0.55],
    )
    st.append(PageBreak())

    # ---- PART 1: SETUP
    st.append(P("Part 1  Set up your computer", "h1"))
    st.append(
        P(
            "Works on <b>Windows, macOS and Linux</b>. Do the <b>6 steps in order</b>, once. Copy the commands "
            "exactly. After every step, check the green <b>YOU SHOULD SEE</b> line before you go on. About 30 "
            "minutes, mostly waiting. Steps 2 and 5 have one box per system: <b>use only yours</b>."
        )
    )
    st += callout(
        "tip",
        "Open a terminal.",
        "<b>Windows:</b> Windows key, type PowerShell, Enter. <b>macOS:</b> Cmd+Space, type Terminal, Enter. "
        "<b>Linux:</b> any terminal. You do <b>not</b> install Python, Django or PostgreSQL: Docker does "
        "that for you.",
    )

    st.append(
        step(
            1,
            "Accounts",
            [
                P(
                    "Send your <b>GitHub username</b> to Nour, accept the <b>invitation to the GitHub "
                    "organisation</b> (it arrives by email) and turn on <b>two-factor authentication</b> on "
                    "your GitHub account (the organisation requires it). The Jira invitation is already "
                    "done. You also need a <b>Claude</b> "
                    "account that includes <b>Claude Code</b>: ask Nour which plan the team uses."
                )
            ],
            see="The organisation <b>Strain-Primer-Management</b> appears under your profile menu, "
            "<i>Your organizations</i>.",
            ifnot="Ask Nour to send the invitation again, and check your spam folder.",
        )
    )
    st += bigstep(
        2,
        "Install the programs (including Claude Code)",
        [
            oscode(
                "WINDOWS  (PowerShell)",
                '$flags = "--accept-source-agreements", "--accept-package-agreements"\n'
                "winget install -e --id Git.Git $flags\n"
                "winget install -e --id Docker.DockerDesktop $flags\n"
                "winget install -e --id Microsoft.VisualStudioCode $flags\n"
                "winget install -e --id GitHub.cli $flags\n"
                "winget install -e --id Anthropic.ClaudeCode $flags",
            )
            + [
                P(
                    "Then <b>restart your PC</b>, open a fresh PowerShell, and open <b>Docker Desktop</b> "
                    "from the Start menu (accept the terms, wait)."
                )
            ],
            oscode(
                "MACOS  (Terminal)",
                "brew install git gh\nbrew install --cask visual-studio-code claude-code",
            )
            + [
                P(
                    "First install <b>Homebrew</b> from <font face='Courier'>brew.sh</font> (copy the one "
                    'command shown there, then run the "Next steps" lines it prints). Then download '
                    "<b>Docker Desktop for Mac</b> from <font face='Courier'>docker.com/products/docker-desktop</font> "
                    "(pick <b>Apple chip</b> or <b>Intel chip</b>), drag it to Applications, open it, accept "
                    "the terms, wait."
                )
            ],
            oscode(
                "LINUX  (your distribution, then the lines below it)",
                "# Debian / Ubuntu\n"
                "sudo apt update && sudo apt install -y git gh docker.io docker-compose-v2\n"
                "# Fedora\n"
                "sudo dnf install -y git gh docker docker-compose\n"
                "# Arch / CachyOS / Manjaro\n"
                "sudo pacman -S --needed git github-cli docker docker-compose\n"
                "\n"
                "# every distribution:\n"
                "sudo systemctl enable --now docker\n"
                "sudo usermod -aG docker $USER\n"
                "curl -fsSL https://claude.ai/install.sh | bash",
            )
            + [
                P(
                    "On Linux, <b>log out and log in again</b> afterwards (so Docker works without sudo). "
                    "<b>On every system:</b> use VS Code (Linux: code.visualstudio.com) with the extension "
                    "<b>EditorConfig</b>, or any editor you like."
                )
            ],
        ],
        see="<b>Windows/macOS:</b> Docker Desktop shows <b>Engine running</b>. <b>Linux:</b> "
        "<font face='Courier'>docker ps</font> prints a table header and no error. <b>Everywhere</b> "
        "(in a new terminal): <font face='Courier'>claude --version</font> prints a version.",
        ifnot="Windows: Fix A or B. Linux: Fix G. macOS: Fix H. <font face='Courier'>claude</font> not "
        "found: Fix I.",
    )
    st.append(
        step(
            3,
            "Sign in to GitHub and to Claude Code",
            code("gh auth login\nclaude", STEP_INNER_W)
            + [
                P(
                    "<b>gh:</b> answer <b>GitHub.com</b>, then <b>HTTPS</b>, then <b>Yes</b> (authenticate Git), "
                    "then <b>Login with a web browser</b>; paste the code it shows on the page that opens. "
                    "<b>claude:</b> it opens your browser: sign in with your Claude account. When "
                    "<b>Claude Code</b> shows its prompt, type <font face='Courier'>/exit</font> and press Enter."
                )
            ],
            see="<b>gh</b> says you are logged in as your GitHub username, and <b>Claude Code</b> shows its "
            "prompt after you sign in.",
            ifnot="GitHub: Fix C. Claude Code: Fix I.",
        )
    )
    st.append(
        step(
            4,
            "Tell Git your name",
            code(
                'git config --global user.name "Your Name"\n'
                'git config --global user.email "you@example.com"',
                STEP_INNER_W,
            )
            + [
                P(
                    "Replace <b>Your Name</b> with the name you want shown on your work and "
                    "<b>you@example.com</b> with the email you want on your commits. The repository is public, "
                    "so both are visible to everyone and cannot be removed once pushed. Use your personal email "
                    "if you are fine with that. If you would rather keep it private, use <b>GitHub's no-reply "
                    "address</b> instead (copy the whole address from <font face='Courier'>github.com/settings/emails</font>; "
                    "its shape is <font face='Courier'>&lt;your-number&gt;+&lt;your-username&gt;@users.noreply.github.com</font>, "
                    "and the number is personal to your account). <b>Never type a number you did not copy from that "
                    "page</b>: a wrong number makes GitHub show your work under a stranger's account. "
                    "<b>Keep the quotes.</b>"
                )
            ],
            see="Nothing is printed. That is normal.",
        )
    )
    st.append(
        step(
            5,
            "Download the project and start it",
            oscode(
                "WINDOWS  (PowerShell)",
                "mkdir C:\\dev\n"
                "cd C:\\dev\n"
                "git clone https://github.com/Strain-Primer-Management/strain-primer-management.git\n"
                "cd strain-primer-management\n"
                "powershell -ExecutionPolicy Bypass -File .\\setup.ps1",
            )
            + oscode(
                "MACOS and LINUX  (Terminal)",
                "mkdir -p ~/dev\n"
                "cd ~/dev\n"
                "git clone https://github.com/Strain-Primer-Management/strain-primer-management.git\n"
                "cd strain-primer-management\n"
                "bash setup.sh",
            )
            + [
                P(
                    "The first time takes several minutes (a few hundred MB). Do not close the window. "
                    "Do not put the project in OneDrive, iCloud, Desktop or Documents: sync tools fight "
                    "with Docker."
                )
            ],
            see="<b>All set.</b> Then open <font face='Courier'>http://localhost:8000</font> and log in with "
            "<font face='Courier'>admin</font> / <font face='Courier'>admin</font>. That login exists only on "
            "your own computer.",
            ifnot="Port busy: Fix D. Anything else: Fix E.",
        )
    )
    st.append(
        step(
            6,
            "Check that it works",
            code("docker compose exec web python manage.py test", STEP_INNER_W),
            see="<b>OK</b> at the end of the output.",
            ifnot="Fix E.",
        )
    )

    st.append(P("Practice run (once, before your first real ticket)", "h2"))
    st.append(
        P(
            "In the project folder, start <b>Claude Code</b> (type <font face='Courier'>claude</font>), paste the "
            "starter message from Part 2, step 2, and use this as the ticket. Say <b>go</b>, look at the change, "
            "say <b>ship it</b>, ask a teammate to review the pull request, then <b>close it without "
            "merging</b> (the <i>Close pull request</i> button)."
        )
    )
    st += code(
        "Ticket: SCRUM-0 - Practice run. Create only one new file:\n"
        "docs/ai-log/<today>_SCRUM-0_practice_<yourname>.md, copied from\n"
        "docs/ai-log/_TEMPLATE.md. Touch nothing else."
    )

    st.append(P("If something goes wrong", "h2"))
    st += table(
        [
            ["Fix", "Problem", "What to do"],
            [
                "A",
                "Windows: <font face='Courier'>winget</font> is not recognized",
                "Install <b>App Installer</b> from the Microsoft Store and try again. Or install by hand: "
                "git-scm.com/download/win, docker.com/products/docker-desktop (choose <b>WSL 2</b>), "
                "code.visualstudio.com, cli.github.com, and for <b>Claude Code</b> the PowerShell line from "
                "code.claude.com/docs/en/setup.",
            ],
            [
                "B",
                "Windows: Docker shows a WSL or virtualization error",
                "PowerShell as administrator: <font face='Courier'>wsl --install</font>, restart the PC. "
                "Still stuck: enable <i>Intel VT-x</i> / <i>AMD SVM</i> in the BIOS, then restart.",
            ],
            [
                "C",
                "GitHub login fails, or the wrong account",
                "<font face='Courier'>gh auth logout</font>, then <font face='Courier'>gh auth login</font> "
                'again, signed in to the right account in the browser. "Repository not found" means the '
                "invitation (step 1) was not accepted.",
            ],
            [
                "D",
                "Port 8000 is busy",
                "Close the other program that uses it, or ask Nour. Do not change project files for this.",
            ],
            [
                "E",
                "The app does not start, or anything else",
                "<font face='Courier'>docker compose logs -f web</font>, copy the last 20 lines into the team "
                "chat. To reset: <font face='Courier'>docker compose down -v</font>, then repeat step 5.",
            ],
            [
                "F",
                "After a restart the app is gone",
                "Start Docker Desktop (Linux: it starts by itself), wait for it, then run "
                "<font face='Courier'>docker compose up -d</font> in the project folder.",
            ],
            [
                "G",
                "Linux: <i>permission denied</i> on Docker, or the daemon is not running",
                "<font face='Courier'>sudo systemctl enable --now docker</font>, then "
                "<font face='Courier'>sudo usermod -aG docker $USER</font>, then <b>log out and log in "
                "again</b>. Files owned by root: copy <font face='Courier'>.env.example</font> to "
                "<font face='Courier'>.env</font> and set UID and GID to the output of "
                "<font face='Courier'>id -u</font> and <font face='Courier'>id -g</font>.",
            ],
            [
                "H",
                "macOS: <font face='Courier'>brew</font> or <font face='Courier'>git</font> not found, or "
                "Docker not running",
                'Install Homebrew from brew.sh and run the "Next steps" lines it prints, then open a new '
                "Terminal. For Docker: open Docker Desktop and wait for <i>Engine running</i>.",
            ],
            [
                "I",
                "<font face='Courier'>claude</font>: command not found, or it will not sign in",
                "Open a <b>new</b> terminal and try <font face='Courier'>claude --version</font>. Still failing: "
                "the troubleshooting page <font face='Courier'>code.claude.com/docs/en/troubleshoot-install</font>, "
                "or ask Nour. Signing in needs a Claude account that includes <b>Claude Code</b>.",
            ],
        ],
        [0.07, 0.3, 0.63],
    )

    # ---- PART 2: HOW TO DO YOUR JOB
    st.append(P("Part 2  How to do your job", "h1"))
    st.append(
        P(
            "This is the same for every ticket, backend or frontend. <b><b>Claude Code</b> does the Git work</b> "
            "(branch, commits, push, pull request). You give it your name and the ticket, check its work "
            "at two points, and click the final merge button yourself."
        )
    )
    st.append(FlowDiagram(CONTENT_W))
    st.append(Spacer(1, 6))

    st.append(P("1  Pick your ticket", "h2"))
    st += bullets(
        [
            "Open the Jira board and take a ticket assigned to you in <i>To Do</i>. Move it to <i>In Progress</i>.",
            "A good ticket has <b>Acceptance criteria</b> and says whether it is <b>backend or frontend</b>. "
            "<b>Files allowed</b> is optional: most tickets list none, and that is normal, because "
            '<b>Claude Code</b> proposes the files in its plan and you check them at "go". Ask only if the '
            "acceptance criteria are unclear or something the ticket depends on is missing.",
            "Look at the tickets in <i>In Progress</i> and <i>In Review</i>: if one lists the same files, one "
            "of you waits (<b>Claude Code</b> checks open pull requests too). Two people never change the same "
            "file, and <b>only one migration pull request per app is open at a time</b>.",
        ]
    )

    intro = P(
        "Open a terminal in the project folder (<font face='Courier'>C:\\dev\\strain-primer-management</font> on Windows, <font face='Courier'>~/dev/strain-primer-management</font> on macOS and Linux), start <b>Claude Code</b> there, and "
        "paste this starter message with your name and the ticket text from Jira (<b>Claude Code</b> cannot read Jira, "
        "so the number alone tells it nothing):"
    )
    starter = code(
        "Read AGENTS.md completely and follow it strictly.\n"
        "\n"
        "I am <your name>.\n"
        "Ticket: SCRUM-<n> - <title>\n"
        "<paste the ticket from Jira: description, acceptance criteria\n"
        ' and "Files allowed">\n'
        "\n"
        'Give me your plan and the exact files you will touch, and wait for my "go".'
    )
    st.append(KeepTogether([P("2  Start <b>Claude Code</b>", "h2"), intro, *starter]))

    st.append(P('3  Checkpoint 1: say "go"', "h2"))
    st.append(
        P(
            "<b>Claude Code</b> reads the project docs, checks other open pull requests for overlap, and shows a plan. Before "
            "you say <b>go</b>, check:"
        )
    )
    st += checklist(
        [
            "The files it lists make sense for the ticket (and match its <i>Files allowed</i>, if any) and are in <b>your</b> zone.",
            "The plan does what the acceptance criteria say, and nothing extra.",
            "It told you whether other open pull requests touch the same files or migrations.",
        ]
    )
    st.append(
        P(
            "Not right? Tell it what to change. Do not say go until you are happy. After your <b>go</b>, "
            "<b>Claude Code</b> gives you a one-line comment listing its files: paste it on the Jira ticket, so "
            "teammates can see what you claimed."
        )
    )

    st.append(P("4  While <b>Claude Code</b> works", "h2"))
    st += bullets(
        [
            "It creates the branch <font face='Courier'>feature/SCRUM-n-short-name</font> from the newest "
            "<font face='Courier'>main</font>, writes the code, adds tests where needed, runs the six checks "
            "(Part 3), writes a log file in <font face='Courier'>docs/ai-log/</font>, and commits <b>on your PC "
            "only</b>.",
            "Ask it to <b>explain</b> anything you don't understand. If it starts doing more than the ticket "
            'says ("I also fixed..."), answer: <i>"Revert that, it is out of scope."</i>',
            "A long or confusing session? Start a <b>fresh</b> one with the starter message.",
        ]
    )

    st.append(P('5  Checkpoint 2: say "ship it"', "h2"))
    st.append(
        P(
            "<b>Claude Code</b> audits its own work (only approved files changed, size, branch freshness, no secrets), "
            "then gives you a report: <b>Done, Files, Verified, Noticed, Needs from others</b>, and asks whether "
            "to push. Look at the changes yourself (in VS Code, the <i>Source Control</i> tab lists every "
            "changed file and line). Before you say <b>ship it</b>:"
        )
    )
    st += checklist(
        [
            "Only the files from the plan changed, and nothing was deleted by surprise.",
            'The six checks are green, with real results shown (not just "tests pass").',
            "You can explain every change in your own words.",
            "<b>Backend:</b> new tests exist for what you built.",
            "<b>Frontend:</b> you did the browser checklist below and have a screenshot.",
        ]
    )
    st.append(
        P(
            '<b>One "ship it" covers exactly one push.</b> <b>Claude Code</b> asks again before every later push.',
            "body",
        )
    )

    st.append(P("6  The pull request", "h2"))
    st += bullets(
        [
            "<b>Claude Code</b> pushes the branch and opens the pull request: title <font face='Courier'>SCRUM-n summary</font>, "
            "the template filled in honestly, and a <b>Reviewer guide</b> pointing at the riskiest places. "
            "No <font face='Courier'>gh</font>? It gives you a link plus text to paste.",
            "Move the ticket to <i>In Review</i> (<b>Claude Code</b> cannot reach Jira).",
            "Ask a teammate to review: <b>backend</b> reviewed by the other backend dev, <b>frontend</b> by "
            "another frontend dev. You cannot approve your own pull request.",
            "A minute or two later <b>Claude Code</b> reports the result of the automatic checks (the "
            "<font face='Courier'>checks</font> job on GitHub). A ticket is not done while they are red.",
        ]
    )

    st.append(P("7  Review and merge", "h2"))
    st += bullets(
        [
            "<b>Reviewer:</b> read the <i>Reviewer guide</i> first, check that only the ticket's files changed, "
            "that nothing surprising was deleted, and that the author can explain it. Then approve, or "
            'request changes. "I don\'t understand this" is a valid reason.',
            "When the pull request has <b>one approval and green checks</b>, the <b>author</b> clicks "
            "<b>Squash and merge</b>. <b>Claude Code</b> never merges or closes a pull request. GitHub deletes the "
            "branch by itself.",
            "Move the ticket to <i>Done</i>. For the next ticket, start a <b>fresh</b> <b>Claude Code</b> session.",
        ]
    )
    st += callout(
        "tip",
        "Who merges? The author, not Nour.",
        "Nour does not have to approve normal pull requests. A pull request can be merged as soon as it has "
        "<b>green checks and one teammate's approval</b>. Nour only has to approve pull requests that change "
        "lead-only files (config, Docker, docs, the rules for Claude Code), once the team's code-owner switch is turned on.",
    )

    st.append(P("8  If something needs changing", "h2"))
    st += table(
        [
            ["Situation", "Tell <b>Claude Code</b>"],
            [
                "A reviewer left comments",
                '"Address the review comments on my PR." It fixes them and asks before pushing.',
            ],
            [
                "The checks are red",
                '"The checks are red, please fix it." It reads the failure, explains it, proposes a fix and asks before pushing.',
            ],
            [
                "GitHub says the PR has conflicts",
                '"My PR has conflicts, help me update from main." Git does the merge. If nothing conflicts, <b>Claude Code</b> edits nothing. For a real conflict it shows you both sides, resolves only inside the conflict markers with lines that already exist, and waits for your yes. It stops and asks Nour for migrations, files outside your ticket, or when both sides changed the same line.',
            ],
            [
                "After a pull the app shows migration errors",
                "Restart it: <font face='Courier'>docker compose restart web</font>. Still errors, or the team reset the migrations: reset your local database (cheat sheet, Part 3).",
            ],
            [
                "The ticket feels too big",
                "It will say so (about 400 lines or 10 files) and suggest splitting the ticket. Agree with the team first.",
            ],
        ],
        [0.34, 0.66],
    )

    # role cards
    st.append(P("Role card: backend", "h2"))
    st += bullets(
        [
            "<b>Your files:</b> <font face='Courier'>apps/&lt;app&gt;/</font> (models, views, forms, urls, tests), only what the ticket names.",
            "<b>Tests are required.</b> For every view: anonymous goes to login, a permitted user sees 200 with the "
            "<i>expected content</i>, an unpermitted user gets 403. For every JSON endpoint: the exact JSON shape. "
            "For forms and models: valid input saves, invalid input is rejected. For deleting a record with "
            "relations: both choices.",
            "<b>Migrations:</b> create them only with <font face='Courier'>makemigrations &lt;app&gt; -n name</font>, "
            "one per ticket, one open migration pull request per app. Never edit or delete a migration that is "
            "already on <font face='Courier'>main</font>. Model order: primers, then plasmids, then strains.",
            "<b>Records are standalone:</b> relations are optional; deleting a record with relations asks the user "
            "to <i>choose</i> (delete only it, or also the linked ones); nothing cascades silently.",
            "<b>Hand-off to frontend:</b> write the URL names and every template variable (or the JSON shape) in the "
            "view's docstring and merge it first.",
            "<b>Never:</b> add packages, edit <font face='Courier'>config/</font>, or check a user's role name in a view "
            "(check Django permissions instead).",
        ]
    )
    st.append(P("Role card: frontend", "h2"))
    st += bullets(
        [
            "<b>Your files:</b> <font face='Courier'>templates/</font> and <font face='Courier'>static/</font>, only what the "
            "ticket names. One page = one set of files, one person at a time. The shared files "
            "(<font face='Courier'>base.html</font>, <font face='Courier'>components/</font>, <font face='Courier'>base.css</font>, "
            "<font face='Courier'>app.js</font>) change only in their own small ticket, announced in the chat first.",
            "Plain CSS and plain JavaScript only. No HTMX, no frameworks, no CDN, no inline "
            "<font face='Courier'>style</font> or <font face='Courier'>script</font>. URLs through "
            "<font face='Courier'>{% url %}</font>, never typed by hand.",
            "Live content: call the backend's JSON endpoint with <font face='Courier'>fetch()</font>, and insert text "
            "with <font face='Courier'>textContent</font>, never <font face='Courier'>innerHTML</font> with data.",
            "Need a variable that is not there? Comment on the backend ticket. Never edit <font face='Courier'>apps/</font>.",
        ]
    )
    st.append(P("Frontend browser checklist (there are no automated frontend tests)", "h3"))
    st.append(
        P(
            "<b>Claude Code</b> cannot see your browser, so it gives you a short list like this and waits for you:"
        )
    )
    st += checklist(
        [
            "The page looks right at normal desktop width.",
            "You can reach everything with the <b>Tab</b> key, and the focus is visible.",
            "The empty state and the error state look sensible.",
            "The page still works with JavaScript off.",
            "The browser console (F12) shows no errors. Add a screenshot to the pull request.",
        ]
    )

    st += callout(
        "tip",
        "Keep things in one place.",
        "Before you create a template piece, a CSS class, a JS function, a form or a query, <b>search for the "
        "existing one and reuse it</b>. Never copy-paste a block. Colours, spacing and fonts come from the "
        "shared design tokens. Shared pieces (the shared frontend files and <font face='Courier'>apps/core/</font>) "
        "change only in their own small ticket. The list of where each thing lives is in "
        "<font face='Courier'>docs/ARCHITECTURE.md</font>, section \"One place for each thing\".",
    )

    # ---- PART 3: REFERENCE
    st.append(P("Part 3  Reference", "h1"))
    st.append(P("The six checks", "h2"))
    st.append(
        P(
            '<b>Claude Code</b> runs them <b>after its last edit and before asking for "ship it"</b>. GitHub runs the '
            "same six on every pull request as the final judge. Each starts with "
            "<font face='Courier'>docker compose exec web</font> and needs the app running "
            "(<font face='Courier'>docker compose up -d</font>)."
        )
    )
    st += table(
        [
            ["#", "Command", "What it checks"],
            [
                "1",
                "<font face='Courier'>python manage.py check</font>",
                "Django's own self-check: settings, models, URLs.",
            ],
            [
                "2",
                "<font face='Courier'>python manage.py makemigrations --check --dry-run</font>",
                "Fails if a model changed without a migration, or two migrations collide. Creates nothing.",
            ],
            [
                "3",
                "<font face='Courier'>python manage.py test</font>",
                "<b>All automated tests</b>, including every backend test, on a separate throw-away database.",
            ],
            [
                "4",
                "<font face='Courier'>ruff check .</font>",
                "Python lint: unused imports, likely bugs, import order.",
            ],
            [
                "5",
                "<font face='Courier'>ruff format --check .</font>",
                "Python formatting (only checks). Fix with <font face='Courier'>ruff format &lt;your file&gt;</font>.",
            ],
            [
                "6",
                "<font face='Courier'>djlint templates --lint</font>",
                "Template mistakes: inline styles, unclosed tags...",
            ],
        ],
        [0.05, 0.5, 0.45],
    )

    st.append(P("Red lines", "h2"))
    red = Table(
        [
            [
                [P("<b>Never</b>", "cell")]
                + bullets(
                    [
                        "Push or commit directly to <font face='Courier'>main</font>.",
                        "Force-push, or rewrite pushed history.",
                        "Edit files outside your ticket or zone.",
                        "Put passwords, keys or <b>real lab data</b> anywhere (code, prompts, logs). Use fake "
                        "examples like <font face='Courier'>Example-042</font>.",
                        "Approve a pull request you don't understand.",
                        "Skip or weaken a test to make it pass.",
                        "Install packages or change Docker/CI yourself.",
                    ],
                    "bullet",
                ),
                [P("<b>Always</b>", "cell")]
                + bullets(
                    [
                        "Give <b>Claude Code</b> your name <i>and</i> the pasted ticket.",
                        "Read the plan before you say <b>go</b>.",
                        "Look at the changes before you say <b>ship it</b>.",
                        "Keep each pull request small: one ticket.",
                        "Ask when unsure: five minutes of asking beats an hour of untangling.",
                        "Tell the team when you change a shared file.",
                        "Start a fresh <b>Claude Code</b> session for each ticket.",
                    ],
                    "bullet",
                ),
            ]
        ],
        colWidths=[CONTENT_W / 2, CONTENT_W / 2],
    )
    red.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (0, 0), RED_LIGHT),
                ("BACKGROUND", (1, 0), (1, 0), TEAL_LIGHT),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    st += [red, Spacer(1, 8)]

    st.append(P("When something goes wrong", "h2"))
    st += table(
        [
            ["What happened", "What to do"],
            [
                "<b>Claude Code</b> changed files you did not expect",
                "<b>Do not say ship it.</b> Ask it to explain; if it was out of scope, ask it to revert only its own change. Tell Nour if unsure.",
            ],
            [
                "<b>Claude Code</b> pushed without asking",
                "Tell Nour right away with the branch name. Do not try to fix it with Git commands you don't understand.",
            ],
            [
                "You pushed to <font face='Courier'>main</font> by mistake",
                "Tell Nour immediately. Do not try to undo it yourself.",
            ],
            [
                "A password, key or real lab data was committed",
                "Tell Nour immediately, <b>before</b> pushing anything else. It must be removed from the history properly.",
            ],
            [
                "Docker or the app is broken",
                "Run the setup script again (setup.ps1 on Windows, setup.sh on macOS and Linux). Still broken: <font face='Courier'>docker compose down -v</font>, then the setup script. Then ask in the chat with the error text.",
            ],
            [
                "<b>Claude Code</b> keeps ignoring a rule",
                "Stop the session, start a fresh one with the starter message, and tell Nour which rule was ignored. That feedback improves the rules.",
            ],
        ],
        [0.34, 0.66],
    )

    st.append(P("Cheat sheet", "h2"))
    st += table(
        [
            ["I want to...", "Command"],
            [
                "Start working",
                "<font face='Courier'>docker compose up -d</font>, then open <font face='Courier'>http://localhost:8000</font>",
            ],
            ["Stop", "<font face='Courier'>docker compose down</font>"],
            ["See errors", "<font face='Courier'>docker compose logs -f web</font>"],
            [
                "Run all tests",
                "<font face='Courier'>docker compose exec web python manage.py test</font>",
            ],
            [
                "Run one app's tests",
                "<font face='Courier'>docker compose exec web python manage.py test apps.strains</font>",
            ],
            ["I pulled new migrations", "<font face='Courier'>docker compose restart web</font>"],
            [
                "The team reset the migrations (app will not start, or migration errors)",
                "<font face='Courier'>docker compose down -v</font>, then run the setup script again (it recreates admin). Helper: option 14, d",
            ],
            [
                "I pulled new requirements",
                "<font face='Courier'>docker compose up -d --build</font>",
            ],
            [
                "Start over with an empty local database",
                "<font face='Courier'>docker compose down -v</font>, then <font face='Courier'>docker compose up -d</font>",
            ],
            [
                "Look at a teammate's PR on my PC",
                "Commit your own work, then <font face='Courier'>git fetch origin</font>, <font face='Courier'>git switch &lt;their-branch&gt;</font>, <font face='Courier'>docker compose restart web</font>; afterwards <font face='Courier'>git switch main</font>",
            ],
        ],
        [0.34, 0.66],
    )

    st.append(P("Small glossary", "h2"))
    st += table(
        [
            ["Word", "Meaning"],
            ["Repository (repo)", "The project folder with its full history, kept on GitHub."],
            [
                "Branch",
                "Your own line of work, so you never change <font face='Courier'>main</font> directly.",
            ],
            ["Commit", "A saved step of your work, with a message."],
            ["Push", "Sending your commits from your PC to GitHub."],
            [
                "Pull request (PR)",
                "A request to add your branch to <font face='Courier'>main</font>, where a teammate reviews it.",
            ],
            ["CI / checks", "The automatic tests GitHub runs on every pull request."],
            ["Migration", "A file that changes the database structure when a model changes."],
            [
                "Squash and merge",
                "The button that adds your whole branch to <font face='Courier'>main</font> as one clean commit.",
            ],
            [
                "Zone",
                "The folders you may edit: backend <font face='Courier'>apps/</font>, frontend <font face='Courier'>templates/</font> + <font face='Courier'>static/</font>.",
            ],
        ],
        [0.28, 0.72],
    )
    # ---- PART 4: GIT BY HAND
    st.append(PageBreak())
    st.append(P("Part 4  Git by hand", "h1"))
    st += callout(
        "tip",
        "The easy way: the Git helper menu.",
        "Instead of typing the commands below, run the helper and just answer its questions. It explains "
        "everything in plain language, shows the exact command, <b>asks before it changes anything</b>, and "
        "already knows our rules (never works on <font face='Courier'>main</font>, never force-pushes, puts the "
        "ticket in every message). It <b>suggests your next step</b> at the top of the menu, and has a setup check, "
        'a pull request status, ticket cleanup (finished, cancelled, or tidy everything), "apply migrations / reset my database", a way to set unsaved edits aside, an "I have a conflict" guide with a '
        'safe cancel, an "Oops" rescue menu, and a "What is the difference between...?" page. Colours help: '
        "green = fine, yellow = careful, red = stop.",
    )
    st += oscode(
        "WINDOWS  (PowerShell, in the project folder)",
        "powershell -ExecutionPolicy Bypass -File tools\\git-helper.ps1",
    )
    st += oscode("MACOS and LINUX  (Terminal, in the project folder)", "bash tools/git-helper.sh")
    st.append(
        P(
            "The rest of this part is the same thing by hand. Use it when you do not use <b>Claude Code</b>, or "
            "it cannot reach Git. Every case is a box to "
            "copy. Replace the example <font face='Courier'>SCRUM-12</font> and "
            "<font face='Courier'>short-name</font> with your own. Branch names look like "
            "<font face='Courier'>feature/SCRUM-12-short-name</font> (2-5 lowercase words with dashes); commit "
            "messages start with the ticket: <font face='Courier'>SCRUM-12: what I did</font>. Open a terminal "
            "in the project folder first."
        )
    )
    st += table(
        [
            ["I want to...", "Case"],
            ["Start a ticket", "1"],
            ["See what I changed", "2"],
            ["Save my work", "3"],
            ["Send it to GitHub and open the pull request", "4"],
            ["Get the newest changes from <font face='Courier'>main</font>", "5"],
            ["Fix conflicts", "6"],
            ["Change something after a review", "7"],
            ["Look at a teammate's branch", "8"],
            ["Start the next ticket", "9"],
            ["I committed on <font face='Courier'>main</font> by mistake", "10"],
            ["Something else went wrong", "the <b>Oops</b> table"],
        ],
        [0.7, 0.3],
    )

    def case(title, commands, note=None):
        parts = [P(title, "h3"), *code(commands)]
        if note:
            parts.append(P(note))
        return KeepTogether(parts)

    st.append(
        case(
            "Case 1  Start a ticket (new branch)",
            "git fetch origin\ngit switch -c feature/SCRUM-12-short-name --no-track origin/main",
            "You should see: <font face='Courier'>Switched to a new branch 'feature/SCRUM-12-short-name'</font>.",
        )
    )
    st.append(
        case(
            "Case 2  See what I changed",
            "git branch --show-current     # which branch am I on?\n"
            "git status                    # which files changed?\n"
            "git diff                      # what exactly changed (press q to leave)",
        )
    )
    st.append(
        case(
            "Case 3  Save my work (commit)",
            'git add path/to/file1 path/to/file2\ngit commit -m "SCRUM-12: Short description of what you did"',
            "Name every file. <b>Never</b> <font face='Courier'>git add .</font> Run the six checks (Part 3) "
            "before you commit. If Git says <font face='Courier'>Blocked: you are on 'main'</font>, see the "
            "Oops table.",
        )
    )
    st.append(
        case(
            "Case 4  Send it to GitHub and open the pull request",
            "git push -u origin feature/SCRUM-12-short-name",
            'The output contains a link ("Create a pull request for..."): open it, fill in the template, click '
            "<b>Create pull request</b>. With the GitHub CLI you can use "
            "<font face='Courier'>gh pr create --base main --title \"SCRUM-12 Short description\"</font> instead. "
            "Then ask a teammate to review. With green checks and one approval, click "
            "<b>Squash and merge</b>. Later pushes on the same branch are just "
            "<font face='Courier'>git push</font>.",
        )
    )
    st.append(
        case(
            "Case 5  Get the newest changes from main",
            'git fetch origin\ngit merge origin/main -m "SCRUM-12: Merge main into my branch"',
            "No conflict: done (run the checks, then <font face='Courier'>git push</font>). Conflict: Case 6. "
            "Want to cancel: <font face='Courier'>git merge --abort</font>.",
        )
    )
    st.append(
        KeepTogether(
            [
                P("Case 6  Fix conflicts (Git says CONFLICT)", "h3"),
                *numbered(
                    [
                        "<font face='Courier'>git status</font> lists the conflicted files under <i>Unmerged paths</i>.",
                        "<b>Stop and ask Nour or Lina, then run <font face='Courier'>git merge --abort</font>,</b> if a "
                        "conflicted file is not one of your ticket's files, is a migration, you do not understand it, "
                        "or both sides changed the same line.",
                        "Otherwise open the file and find the blocks:",
                    ]
                ),
                *code(
                    "<<<<<<< HEAD\n"
                    "your version of the lines\n"
                    "=======\n"
                    "their version of the lines (from main)\n"
                    ">>>>>>> origin/main"
                ),
                P(
                    "4. Keep what both sides need (usually both sets of lines) and delete the three marker lines. "
                    "Do not guess: unsure means ask."
                ),
                P("5. Save, then:"),
                *code(
                    'git add path/to/the-file\ngit commit -m "SCRUM-12: Merge main into my branch"'
                ),
                P("6. Run the six checks, then <font face='Courier'>git push</font>."),
            ]
        )
    )
    st.append(
        case(
            "Case 7  Change something after a review",
            'git add path/to/file\ngit commit -m "SCRUM-12: Address review comments"\ngit push',
            "The pull request updates by itself.",
        )
    )
    st.append(
        case(
            "Case 8  Look at a teammate's branch",
            "git fetch origin\ngit switch their-branch-name\ndocker compose restart web",
            "Commit your own work first. When you are done: <font face='Courier'>git switch main</font> "
            "(or back to your own branch).",
        )
    )
    st.append(
        case(
            "Case 9  Start the next ticket",
            "git switch main\ngit pull --ff-only",
            "Then Case 1. (<font face='Courier'>--ff-only</font> is safe: it can never create a mess.) "
            "Leave old branches alone.",
        )
    )
    st.append(
        case(
            "Case 10  I committed on main by mistake (not pushed yet)",
            "git switch -c feature/SCRUM-12-short-name   # your commit now lives on this branch\n"
            "git switch main\n"
            "git reset --hard origin/main              # main is back to normal, your work is safe\n"
            "git switch feature/SCRUM-12-short-name",
            "This is safe <b>only</b> because the commit is saved on the new branch first. Unsure? Ask Nour.",
        )
    )

    st += callout(
        "stop",
        "Never",
        "<font face='Courier'>git push --force</font>, <font face='Courier'>git add .</font>, "
        "<font face='Courier'>git rebase</font>, <font face='Courier'>git reset --hard</font> (except Case 10), "
        "<font face='Courier'>git pull</font> on your own branch (use Case 5), or deleting branches.",
    )
    st.append(P("Oops table", "h2"))
    st += table(
        [
            ["Situation", "Do this"],
            [
                "<font face='Courier'>Blocked: you are on 'main'</font>, or I edited files on <font face='Courier'>main</font>",
                "<font face='Courier'>git switch -c feature/SCRUM-12-short-name</font> (your edits come along)",
            ],
            [
                "I pushed to <font face='Courier'>main</font> by mistake",
                "<b>Do not fix it yourself. Tell Nour right now.</b>",
            ],
            [
                "Undo my last commit, keep my changes (not pushed)",
                "<font face='Courier'>git reset --soft HEAD~1</font>",
            ],
            [
                "Put a file back exactly as in my last commit (<b>loses</b> my edits to it)",
                "<font face='Courier'>git restore --source=HEAD --staged --worktree path/to/file</font>",
            ],
            [
                "I staged the wrong file (before committing)",
                "<font face='Courier'>git restore --staged path/to/file</font>",
            ],
            [
                "I committed or pushed something wrong on my branch",
                "Fix it, make a <b>new</b> commit, <font face='Courier'>git push</font>. Never force-push.",
            ],
            [
                '"Please tell me who you are"',
                "<font face='Courier'>git config --global user.name \"Your Name\"</font> and "
                "<font face='Courier'>git config --global user.email \"you@example.com\"</font>",
            ],
            [
                "<font face='Courier'>git status</font> shows files I never touched",
                "Do not add them. Ask Nour.",
            ],
            [
                "Push rejected (non-fast-forward)",
                "Do not force. <font face='Courier'>git fetch origin</font>, then ask Nour.",
            ],
            [
                "I am lost",
                "<font face='Courier'>git status</font>, copy the output into the team chat. Do not type commands you do not understand.",
            ],
        ],
        [0.42, 0.58],
    )

    return st


def main():
    doc = BaseDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=1.9 * cm,
        bottomMargin=1.8 * cm,
        title="Strain & Primer Management - Team Handbook",
        author="Strain & Primer Management team",
        subject="Setup and how to do your job",
    )
    frame = Frame(
        MARGIN,
        1.8 * cm,
        CONTENT_W,
        PAGE_H - 3.7 * cm,
        id="body",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    doc.addPageTemplates(
        [
            PageTemplate(id="cover", frames=[frame], onPage=cover, autoNextPageTemplate="rest"),
            PageTemplate(id="rest", frames=[frame], onPage=later),
        ]
    )
    doc.build(build_story())
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
