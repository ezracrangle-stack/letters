"""Weekly check: visit each manager's letters page, find new letters,
add them to data/letters.json. Never removes anything.

Usage:
  python scripts/update.py                     # live run (GitHub Actions)
  python scripts/update.py --fixtures tests/fixtures   # offline test
"""
import argparse
import datetime as dt
import json
import pathlib
import re
import sys
import time
import urllib.robotparser
from urllib.parse import urljoin, urlparse

import yaml
from bs4 import BeautifulSoup

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import periods  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
LETTERS_FILE = DATA / "letters.json"
RUN_FILE = DATA / "last_run.json"
ALERT_FILE = ROOT / "alert.md"

USER_AGENT = "EzrasNotesLettersBot/1.0 (+https://letters.ezrasnotes.com/about.html)"
MIN_DELAY = 8          # seconds between requests to any site
TIMEOUT = 30


# ── fetching ────────────────────────────────────────────────

class Fetcher:
    def __init__(self, fixtures=None):
        self.fixtures = pathlib.Path(fixtures) if fixtures else None
        self.robots = {}
        self.last_hit = {}
        if not self.fixtures:
            import requests
            self.session = requests.Session()
            self.session.headers.update({
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            })

    def _robots_for(self, url):
        host = urlparse(url).scheme + "://" + urlparse(url).netloc
        if host not in self.robots:
            rp = urllib.robotparser.RobotFileParser()
            try:
                r = self.session.get(host + "/robots.txt", timeout=TIMEOUT)
                rp.parse(r.text.splitlines() if r.status_code == 200 else [])
            except Exception:
                rp.parse([])          # unreachable robots.txt: treat as allowed
            self.robots[host] = rp
            time.sleep(1)
        return self.robots[host]

    def get(self, manager_id, url):
        if self.fixtures:
            return (self.fixtures / f"{manager_id}.html").read_text(encoding="utf-8"), url
        rp = self._robots_for(url)
        if not rp.can_fetch(USER_AGENT, url):
            raise RuntimeError("robots.txt does not allow this page")
        host = urlparse(url).netloc
        delay = max(MIN_DELAY, rp.crawl_delay(USER_AGENT) or 0)
        wait = self.last_hit.get(host, 0) + delay - time.time()
        if wait > 0:
            time.sleep(wait)
        r = self.session.get(url, timeout=TIMEOUT)
        self.last_hit[host] = time.time()
        r.raise_for_status()
        return r.text, r.url


# ── finding letters on a page ───────────────────────────────

def _attr(el, names):
    for n in [x.strip() for x in names.split(",")]:
        v = el.get(n)
        if v and v.strip():
            return v.strip()
    return None


_JUNK = re.compile(r"\b(button|pdf|view|open|download|read more)\b|>", re.I)


def _clean(t):
    return " ".join(_JUNK.sub(" ", t).split())


def _context(el):
    p = el
    for _ in range(8):
        p = p.parent
        if p is None:
            break
        t = _clean(p.get_text(" "))
        if len(t) > 3:
            return t[:160]
    return ""


def _label(el, prefer_context=False):
    """Visible text of a link; falls back to image alt or nearby text."""
    if prefer_context:
        return _context(el)
    t = _clean(el.get_text(" "))
    if len(t) > 2:
        return " ".join(el.get_text(" ").split())
    img = el.find("img")
    if img and img.get("alt"):
        return img["alt"].strip()
    return _context(el)


def find_letters(html, page_url, cfg):
    soup = BeautifulSoup(html, "html.parser")
    url_attr = cfg.get("url_attr", "href")
    include = re.compile(cfg["include"], re.I) if cfg.get("include") else None
    exclude = re.compile(cfg["exclude"], re.I) if cfg.get("exclude") else None
    since = int(cfg.get("since", 0))
    found, seen = [], set()
    for el in soup.select(cfg["select"]):
        raw = _attr(el, url_attr)
        if not raw or raw.startswith(("#", "javascript:", "mailto:")):
            continue
        url = urljoin(page_url, raw).replace(" ", "%20")
        if url in seen:
            continue
        text = _label(el, cfg.get("label") == "context")
        hay = f"{text} {url}"
        if include and not include.search(hay):
            continue
        if exclude and exclude.search(hay):
            continue
        if cfg.get("period_attrs"):
            ya, qa = cfg["period_attrs"]
            per = periods.from_parts(el.get(ya), el.get(qa))
        elif cfg.get("period_from") == "text":
            per = periods.parse(text) or periods.parse_url(url)
        else:                    # period_from: url → the file name decides, nothing else
            per = periods.parse_url(url)
        if not per:              # no date found: not a letter (presentations, memos)
            continue
        if per["year"] < since:
            continue
        seen.add(url)
        found.append({"url": url, "period": per, "text": text})
    return found


# ── main ────────────────────────────────────────────────────

def load_json(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures")
    ap.add_argument("--only", help="check one manager id")
    args = ap.parse_args()

    config = yaml.safe_load((ROOT / "managers.yaml").read_text(encoding="utf-8"))
    archive = load_json(LETTERS_FILE, {})
    fetcher = Fetcher(args.fixtures)
    today = dt.date.today().isoformat()
    problems, report = [], {}

    for m in config["managers"]:
        mid = m["id"]
        if args.only and mid != args.only:
            continue
        known = archive.setdefault(mid, [])
        known_urls = {x["url"] for x in known}
        first_time = not any(x.get("source") == "auto" for x in known)
        added = 0

        # 1) letters typed by hand in managers.yaml
        for item in m.get("letters") or []:
            per = periods.from_manual(item.get("period", ""))
            if not per or not item.get("url"):
                problems.append((m, f"A manual letter has a missing or unreadable period/url: {item}"))
                continue
            if item["url"] not in known_urls:
                known.append({"url": item["url"], "period": per, "title": item.get("title"),
                              "first_seen": today, "source": "manual", "backfill": False})
                known_urls.add(item["url"])
                added += 1

        # 2) letters found on the manager's page
        cfg = m.get("scrape")
        if cfg and m.get("access", "open") == "open":
            try:
                html, final_url = fetcher.get(mid, m["letters_page"])
                found = find_letters(html, final_url, cfg)
                if not found:
                    raise RuntimeError("the page loaded but no letters were found (its layout may have changed)")
                prev_auto = [x for x in known if x.get("source") == "auto"]
                still_there = {f["url"] for f in found}
                missing = [x for x in prev_auto if x["url"] not in still_there]
                if prev_auto and len(missing) > len(prev_auto) / 2:
                    problems.append((m, f"{len(missing)} of {len(prev_auto)} letters we had are no longer on the page. "
                                        "They stay on the site, but the page may have moved or changed."))
                for f in found:
                    if f["url"] in known_urls:
                        continue
                    known.append({"url": f["url"], "period": f["period"],
                                  "title": f["text"] if cfg.get("title_from_text") else None,
                                  "first_seen": today, "source": "auto", "backfill": first_time})
                    known_urls.add(f["url"])
                    added += 1
                report[mid] = {"status": "ok", "found_on_page": len(found), "new": added}
            except Exception as e:  # noqa: BLE001
                problems.append((m, f"{type(e).__name__}: {e}"))
                report[mid] = {"status": "error", "error": str(e), "new": added}
        else:
            report[mid] = {"status": "manual", "new": added}

        # 3) fixes typed by hand: overrides: [{match, period, title}]
        #    "match" is a piece of the letter's web address (a regex);
        #    "{label}" in a title is replaced by the period, e.g. Q2 2026.
        for fix in m.get("overrides") or []:
            if not fix.get("match"):
                continue
            pat = re.compile(fix["match"], re.I)
            for x in known:
                if pat.search(x["url"].replace("%20", " ")):
                    if fix.get("period") and periods.from_manual(fix["period"]):
                        x["period"] = periods.from_manual(fix["period"])
                    if fix.get("title"):
                        x["title"] = fix["title"].replace("{label}", x["period"]["label"])

        known.sort(key=lambda x: x["period"]["sort"], reverse=True)

    DATA.mkdir(exist_ok=True)
    LETTERS_FILE.write_text(json.dumps(archive, indent=1, ensure_ascii=False), encoding="utf-8")
    RUN_FILE.write_text(json.dumps({"last_run": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                                    "managers": report}, indent=1), encoding="utf-8")

    if problems:
        lines = [f"The weekly check found {len(problems)} problem(s) on {today}.",
                 "No letters were deleted. Fix the entry in managers.yaml or wait for the next run.", ""]
        for m, msg in problems:
            lines.append(f"- **{m['name']} ({m['firm']})**: {msg}  \n  Page: {m.get('letters_page')}")
        ALERT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    elif ALERT_FILE.exists():
        ALERT_FILE.unlink()

    for mid, r in report.items():
        print(f"{mid:<16} {r['status']:<7} new: {r['new']:<4} {r.get('found_on_page', '')} {r.get('error', '')}")
    if problems:
        print(f"\n{len(problems)} problem(s), see alert.md")


if __name__ == "__main__":
    main()
