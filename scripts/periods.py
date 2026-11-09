"""Turn text like 'Q3 2026', 'q4-25', '2012-q1', 'YE 2025', '3Q2026',
'H1 2026' or 'Annual Letter 2024' into a period the site can sort.

Returns a dict {year, part, label, sort} or None.
part is one of Q1..Q4, H1, H2, Annual.
"""
import re

_MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
_MONTH_END = {"Q1": 3, "Q2": 6, "Q3": 9, "Q4": 12, "H1": 6, "H2": 12, "Annual": 12}


def _y(two_or_four):
    y = int(two_or_four)
    return y + 2000 if y < 100 else y


def make(year, part):
    year = int(year)
    if not 1980 <= year <= 2100:
        return None
    label = f"{part} {year}" if part != "Annual" else f"{year}"
    return {"year": year, "part": part, "label": label,
            "sort": year * 100 + _MONTH_END[part]}


# Ordered from most to least specific. Each returns (year, part).
_PATTERNS = [
    # Q3 2026 · Q3-2026 · Q3_2026 · Q3 Brookfield ... (no) · 2026 Q3 · 2026/Q3
    (r"\bq([1-4])[\s_\-'.]{0,3}(20\d\d|19\d\d)\b", lambda m: (m[2], f"Q{m[1]}")),
    (r"(?<!\d)(20\d\d|19\d\d)[\s_\-/.]{0,3}q([1-4])", lambda m: (m[1], f"Q{m[2]}")),
    # 2026 2Q (Maran)
    (r"(?<!\d)(20\d\d)[\s_\-/.]{0,3}([1-4])q\b", lambda m: (m[1], f"Q{m[2]}")),
    # 3Q2026 · 3Q26 · 3Q 2026
    (r"\b([1-4])q[\s_\-']{0,2}(20\d\d|\d\d)\b", lambda m: (_y(m[2]), f"Q{m[1]}")),
    # H1 2026 · 2026 H1 · 1H26
    (r"\bh([12])[\s_\-'.]{0,3}(20\d\d|19\d\d)\b", lambda m: (m[2], f"H{m[1]}")),
    (r"(?<!\d)(20\d\d|19\d\d)[\s_\-/.]{0,3}h([12])\b", lambda m: (m[1], f"H{m[2]}")),
    (r"\b([12])h[\s_\-']{0,2}(20\d\d|\d\d)\b", lambda m: (_y(m[2]), f"H{m[1]}")),
    # H1'24 · H2 24 (Saga)
    (r"\bh([12])[\s_\-'.]{0,2}(\d\d)(?!\d)", lambda m: (_y(m[2]), f"H{m[1]}")),
    # Q4-25 · Q1'26 · Q126 (1 Main style) · Q4 25
    (r"\bq([1-4])[\s_\-'.]{0,2}(\d\d)(?!\d)", lambda m: (_y(m[2]), f"Q{m[1]}")),
    # August 1999 · March-2020 · Aug 2026
    (r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s_\-.,']{1,3}(20\d\d|19\d\d)\b",
     lambda m: (m[2], f"Q{(_MONTHS.index(m[1]) // 3) + 1}")),
    # Year-end 2017 · YE 2025 · YE25
    (r"\b(?:year[\s_\-]?end|ye)[\s_\-']{0,2}(20\d\d|\d\d)\b", lambda m: (_y(m[1]), "Q4")),
    # Semi-annual letter 2025 (Fundsmith)
    (r"semi[\s_\-]?annual\D{0,40}(20\d\d)", lambda m: (m[1], "H1")),
    (r"(20\d\d)\D{0,10}semi[\s_\-]?annual", lambda m: (m[1], "H1")),
]


def parse(text, fallback_year=None):
    """Find a period inside text. fallback_year is used when only a
    quarter is present (e.g. '.../2020/letters-to-shareholders-q4.pdf')."""
    if not text:
        return None
    # underscores count as word characters for regex, so treat them as spaces
    s = text.lower().replace("%20", " ").replace("_", " ")
    for pat, fn in _PATTERNS:
        m = re.search(pat, s)
        if m:
            year, part = fn(m)
            return make(year, part)
    m = re.search(r"\bq([1-4])\b", s)
    if m and fallback_year:
        return make(fallback_year, f"Q{m[1]}")
    m = re.search(r"\b(20\d\d|19\d\d)\b", s)
    if m:
        return make(m[1], "Annual")
    return None


def parse_url(url):
    """Try the file name first, then the full path (folder years)."""
    path = url.split("?")[0]
    name = path.rsplit("/", 1)[-1]
    folder_year = None
    m = re.findall(r"/(20\d\d)/", path)
    if m:
        folder_year = m[-1]
    return parse(name, folder_year) or parse(path, folder_year)


def from_parts(year, part):
    """For sites that give year and quarter in separate fields."""
    if not year:
        return None
    part = (part or "").strip().upper()
    if part in {"Q1", "Q2", "Q3", "Q4", "H1", "H2"}:
        return make(year, part)
    if part in {"1", "2", "3", "4"}:
        return make(year, f"Q{part}")
    return make(year, "Annual")


def from_manual(text):
    """Periods typed by hand in managers.yaml."""
    s = str(text).strip()
    if re.fullmatch(r"\d{4}", s):
        return make(s, "Annual")
    return parse(s)
