"""Turn the file names of Ezra's Obsidian letter summaries into short
"In this letter:" lines for the site.

Only the file NAME is used (it is Ezra's own one-line summary). Nothing from
inside the notes is published.

Usage:
    python scripts/sync_notes.py names.txt
where names.txt has one note file name per line. Writes data/notes.json:
    {manager_id: {period_label: "topics"}}
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import periods  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# Which managers get notes on the site, and how their notes are named in the vault.
MANAGERS = {
    "greystone": r"Greystone Capital",
    "saga": r"Saga Partners",
}

SKIP = re.compile(r"letters index|pitchbook", re.I)


def topics_of(stem):
    # "Q3 2026 Greystone Capital Letter Summary - Misfit Toys, ..." -> "Misfit Toys, ..."
    # "Saga Partners - The Growth of Knowledge - What Progress, ... (August 2026)" -> last part
    parts = [p.strip() for p in stem.split(" - ")]
    if len(parts) < 2:
        return None
    t = re.sub(r"\s*\((?:[A-Za-z]+ )?\d{4}\)$", "", parts[-1]).strip()
    return t or None


def main(names_file):
    archive = json.loads((ROOT / "data" / "letters.json").read_text(encoding="utf-8"))
    notes, unmatched = {}, []
    for raw in Path(names_file).read_text(encoding="utf-8").splitlines():
        stem = Path(raw.strip()).name.removesuffix(".md")
        if not stem or SKIP.search(stem):
            continue
        mid = next((k for k, rx in MANAGERS.items() if re.search(rx, stem, re.I)), None)
        if not mid:
            continue
        head = stem.split(" - ")[0]
        p = periods.parse(head) or periods.parse(stem)
        topics = topics_of(stem)
        if not p or not topics:
            unmatched.append(stem)
            continue
        labels = {(l.get("period") or {}).get("label") for l in archive.get(mid, [])}
        label = p["label"]
        if label not in labels and p["part"] == "Annual":
            # A year-end letter the site lists as Q4 or H2.
            label = next((c for c in (f"Q4 {p['year']}", f"H2 {p['year']}") if c in labels), label)
        if label not in labels:
            unmatched.append(stem)
            continue
        notes.setdefault(mid, {})[label] = topics
    out = ROOT / "data" / "notes.json"
    out.write_text(json.dumps(notes, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Matched {sum(len(v) for v in notes.values())} notes for {len(notes)} managers.")
    for u in unmatched:
        print("  no letter on the site for:", u)


if __name__ == "__main__":
    main(sys.argv[1])
