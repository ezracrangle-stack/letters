"""Read each letter once and record which names it mentions.

Only names and counts are saved (data/mentions.json). The text of the
letters is never stored or published.

Usage:
  python scripts/mentions.py                      # managers in INDEXED (weekly run)
  python scripts/mentions.py --only fundsmith     # a manager not yet in INDEXED
"""
import argparse
import datetime as dt
import io
import json
import pathlib
import re
import sys
import time
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from update import Fetcher, LETTERS_FILE, DATA  # noqa: E402

MENTIONS_FILE = DATA / "mentions.json"

# Managers whose letters are read for the company index. Add ids here as
# they are checked; the weekly run then reads their new letters.
INDEXED = ["fundsmith", "hayden", "1-main", "laughing-water", "saga", "greystone",
           "giverny", "plural", "massif"]
MAX_BYTES = 40 * 1024 * 1024

# Capitalised words that are almost never company names.
STOP = set("""
a an and the of in on at to for from by with as or but if than then this that these those there their
our we us you your he she it its they them i my me his her who whom which what when where why how
however although also because while after before during since until although despite moreover
furthermore therefore thus hence indeed still yet so not no nor all any some each every most more
many much few other such own same both either neither one two three four five six seven eight nine ten
first second third fourth last next new old
january february march april may june july august september october november december
jan feb mar apr jun jul aug sep sept oct nov dec
monday tuesday wednesday thursday friday saturday sunday
q1 q2 q3 q4 h1 h2 fy ytd usd gbp eur us uk eu
mr mrs ms dr inc ltd plc corp co llc lp sa ag nv se group
fund funds partner partners partnership portfolio investor investors shareholder shareholders
letter annual semi report table figure chart source note notes page appendix total year years
""".split())

UP = "A-ZÀ-ÖØ-Þ"
WORD = rf"[{UP}][\w'’\.\-&]*[\w]|[{UP}]"
LINK = r"(?:&|of|de|du|la|le|der|van|von)"
PHRASE = re.compile(rf"\b(?:{WORD})(?:\s+(?:{LINK}\s+)?(?:{WORD})){{0,4}}")


def clean(text):
    text = text.replace("­", "")                 # soft hyphens
    text = re.sub(r"-\n(\w)", r"\1", text)            # words split across lines
    text = re.sub(r"[ \t]+", " ", text)
    return text


def names(text):
    """Return Counter of capitalised names in the text."""
    text = clean(text)
    lower = set(w.lower() for w in re.findall(r"\b[a-z][a-z'’\-]+\b", text))
    found = Counter()
    for line in text.splitlines():
        for m in PHRASE.finditer(line):
            words = m.group(0).split()
            # trim leading/trailing words that are ordinary capitalised words
            while words and (words[0].lower().strip("'’.") in STOP or words[0].lower() in lower):
                words.pop(0)
            while words and (words[-1].lower().strip("'’.") in STOP or re.fullmatch(LINK, words[-1].lower())):
                words.pop()
            if not words:
                continue
            name = " ".join(words).rstrip(".").removesuffix("'s").removesuffix("’s")
            if len(name) < 2 or name.isdigit():
                continue
            if len(words) == 1 and (name.lower() in lower or name.lower() in STOP):
                continue
            found[name] += 1
    return found


def pdf_text(data):
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data))
    return "\n".join((p.extract_text() or "") for p in reader.pages), len(reader.pages)


class BytesFetcher(Fetcher):
    def get_bytes(self, url):
        rp = self._robots_for(url)
        from update import USER_AGENT, MIN_DELAY, TIMEOUT
        from urllib.parse import urlparse
        if not rp.can_fetch(USER_AGENT, url):
            raise RuntimeError("robots.txt does not allow this file")
        host = urlparse(url).netloc
        delay = max(MIN_DELAY, rp.crawl_delay(USER_AGENT) or 0)
        wait = self.last_hit.get(host, 0) + delay - time.time()
        if wait > 0:
            time.sleep(wait)
        r = self.session.get(url, timeout=60, headers={"Accept": "application/pdf,*/*;q=0.8"})
        self.last_hit[host] = time.time()
        r.raise_for_status()
        if len(r.content) > MAX_BYTES:
            raise RuntimeError("file too large")
        return r.content, r.headers.get("Content-Type", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", action="append", help="manager id (repeatable)")
    ap.add_argument("--retry-errors", action="store_true")
    args = ap.parse_args()

    letters = json.loads(LETTERS_FILE.read_text(encoding="utf-8"))
    store = json.loads(MENTIONS_FILE.read_text(encoding="utf-8")) if MENTIONS_FILE.exists() else {}
    fetcher = BytesFetcher()
    today = dt.date.today().isoformat()
    done = failed = 0

    for mid, items in letters.items():
        if mid not in (args.only or INDEXED):
            continue
        for x in items or []:
            url = x["url"]
            old = store.get(url)
            if old and (old["status"] == "ok" or not args.retry_errors):
                continue
            rec = {"manager": mid, "checked": today}
            try:
                data, ctype = fetcher.get_bytes(url)
                if data[:4] != b"%PDF":
                    raise RuntimeError(f"not a PDF ({ctype.split(';')[0] or 'unknown type'})")
                text, pages = pdf_text(data)
                rec["pages"] = pages
                words = len(text.split())
                if words < 50 * max(pages, 1) // 4:
                    rec["status"] = "no-text"        # scanned images, needs OCR
                else:
                    rec["status"] = "ok"
                    rec["words"] = words
                    rec["names"] = dict(names(text).most_common())
                done += 1
            except Exception as e:  # noqa: BLE001
                rec["status"] = "error"
                rec["error"] = str(e)[:200]
                failed += 1
            store[url] = rec
            print(f"{mid:16} {rec['status']:8} {url}", flush=True)
            MENTIONS_FILE.write_text(json.dumps(store, indent=1, ensure_ascii=False, sort_keys=True) + "\n",
                                     encoding="utf-8")
    print(f"Read {done} letters, {failed} failed.")


if __name__ == "__main__":
    main()
