"""Build the static site into docs/ from managers.yaml + data/letters.json."""
import datetime as dt
import json
import re
import unicodedata
import pathlib
import shutil
from email.utils import format_datetime
from xml.sax.saxutils import escape

from urllib.parse import urlparse

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs"
SITE_URL = "https://letters.ezrasnotes.com"
GA_ID = "G-5WBJ964B95"  # Google Analytics, "Letters" stream. Empty string turns it off.
NEWSLETTER_URL = "https://www.ezrasnotes.com"
SUBSCRIBE_URL = "https://www.ezrasnotes.com"
# Hosts that are copies, not the manager's own site: shown as "via ..."
THIRD_PARTY = {"web.archive.org": "Internet Archive", "gurufocus.com": "GuruFocus",
               "focusdst.com": "Focus DST", "seekingalpha.com": "Seeking Alpha",
               "hedgefundalpha.com": "Hedge Fund Alpha", "scribd.com": "Scribd",
               "sec.gov": "SEC EDGAR"}
LATEST_ON_HOME = 15


def load():
    config = yaml.safe_load((ROOT / "managers.yaml").read_text(encoding="utf-8"))
    archive_path = ROOT / "data" / "letters.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8")) if archive_path.exists() else {}
    run_path = ROOT / "data" / "last_run.json"
    last_run = json.loads(run_path.read_text(encoding="utf-8")).get("last_run") if run_path.exists() else None
    managers = []
    for m in config["managers"]:
        m = dict(m)
        m.setdefault("access", "open")
        letters = archive.get(m["id"], []) if m["access"] == "open" else []
        # the same period and title twice (a firm re-uploaded a file): show it once
        seen, m["letters"] = set(), []
        for x in letters:
            key = (x["period"]["label"], x.get("title"))
            if key not in seen:
                seen.add(key)
                m["letters"].append(x)
        for x in m["letters"]:
            x["display"] = x.get("title") or f"{x['period']['label']} letter"
            host = urlparse(x["url"]).netloc.lower().removeprefix("www.")
            x["via"] = next((v for k, v in THIRD_PARTY.items() if host.endswith(k)), None)
        years = {}
        for x in m["letters"]:
            years.setdefault(x["period"]["year"], []).append(x)
        m["by_year"] = sorted(years.items(), reverse=True)
        m["latest"] = m["letters"][0] if m["letters"] else None
        managers.append(m)
    managers.sort(key=lambda m: m["name"].split()[-1].lower())
    return managers, last_run


def pretty_date(iso):
    if not iso:
        return ""
    d = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return d.strftime("%B %-d, %Y")


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()).strip("-")


def load_companies(managers):
    """Match the names found in each letter (data/mentions.json) to the companies
    listed in data/companies.yaml. Returns companies sorted by number of letters."""
    cpath, mpath = ROOT / "data" / "companies.yaml", ROOT / "data" / "mentions.json"
    if not (cpath.exists() and mpath.exists()):
        return []
    mentions = json.loads(mpath.read_text(encoding="utf-8"))
    by_url = {x["url"]: (m, x) for m in managers for x in m["letters"]}
    companies = []
    for c in yaml.safe_load(cpath.read_text(encoding="utf-8"))["companies"]:
        terms = [c["name"]] + c.get("aliases", [])
        rx = re.compile("|".join(rf"(?<![\w&'’]){re.escape(t)}(?![\w&])" for t in terms))
        ex = re.compile(c["exclude"]) if c.get("exclude") else None
        hits = []
        for url, rec in mentions.items():
            if url not in by_url or rec.get("status") != "ok":
                continue
            n = sum(v for k, v in rec["names"].items() if rx.search(k) and not (ex and ex.search(k)))
            if n:
                m, x = by_url[url]
                hits.append({"manager": m, "letter": x, "count": n})
        if hits:
            hits.sort(key=lambda h: (h["letter"]["period"]["sort"], h["count"]), reverse=True)
            mgrs = {}
            for h in hits:
                mgrs.setdefault(h["manager"]["id"], [h["manager"], 0])[1] += 1
            companies.append({"name": c["name"], "slug": slugify(c["name"]), "hits": hits,
                              "managers": sorted(mgrs.values(), key=lambda v: -v[1]),
                              "mentions": sum(h["count"] for h in hits)})
    companies.sort(key=lambda c: (-len(c["hits"]), -c["mentions"], c["name"].lower()))
    return companies


def build():
    managers, last_run = load()
    companies = load_companies(managers)
    env = Environment(loader=FileSystemLoader(ROOT / "templates"),
                      autoescape=select_autoescape(["html"]))
    import hashlib
    asset_v = hashlib.md5(b"".join((ROOT / "static" / f).read_bytes()
                                   for f in ("style.css", "filter.js", "search.js"))).hexdigest()[:8]
    common = dict(asset_v=asset_v, ga_id=GA_ID, site_url=SITE_URL, newsletter_url=NEWSLETTER_URL,
                  subscribe_url=SUBSCRIBE_URL, updated=pretty_date(last_run),
                  manager_count=len(managers))

    all_letters = [dict(x, manager=m) for m in managers for x in m["letters"]]
    all_letters.sort(key=lambda x: (x["period"]["sort"], x["first_seen"]), reverse=True)

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "m").mkdir(parents=True)
    shutil.copytree(ROOT / "static", OUT / "static")
    shutil.copy(ROOT / "static" / "favicon.ico", OUT / "favicon.ico")

    def render(template, path, root, **kw):
        html = env.get_template(template).render(root=root, page=path, **common, **kw)
        (OUT / path).write_text(html, encoding="utf-8")

    render("index.html", "index.html", "", latest=all_letters[:LATEST_ON_HOME],
           managers=managers, letter_count=len(all_letters))
    render("directory.html", "managers.html", "", managers=managers)
    render("about.html", "about.html", "")
    render("companies.html", "companies.html", "", companies=companies)
    (OUT / "c").mkdir()
    for c in companies:
        render("company.html", f"c/{c['slug']}.html", "../", c=c)
    render("search.html", "search.html", "")
    index = {"managers": [{"n": m["name"], "f": m["firm"], "s": m["style"], "u": f"m/{m['id']}.html"}
                          for m in managers],
             "companies": [{"n": c["name"], "l": len(c["hits"]), "u": f"c/{c['slug']}.html"}
                           for c in companies]}
    (OUT / "search.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")),
                                     encoding="utf-8")
    render("404.html", "404.html", "/")
    for m in managers:
        render("manager.html", f"m/{m['id']}.html", "../", m=m)

    write_feed(all_letters)
    (OUT / "CNAME").write_text("letters.ezrasnotes.com\n")
    (OUT / ".nojekyll").write_text("")
    print(f"Built {len(managers)} managers, {len(all_letters)} letters into docs/")


def write_feed(letters):
    """RSS: letters discovered by the weekly check, newest first.
    The first import (backfill) is left out so readers aren't flooded,
    except to fill the feed up to 20 items when it is still new."""
    fresh = sorted([x for x in letters if not x.get("backfill")],
                   key=lambda x: x["first_seen"], reverse=True)
    if len(fresh) < 20:
        fresh += [x for x in letters if x.get("backfill")][: 20 - len(fresh)]
    items = []
    for x in fresh[:50]:
        m = x["manager"]
        when = dt.datetime.fromisoformat(x["first_seen"]).replace(tzinfo=dt.timezone.utc)
        title = f"{m['name']} ({m['firm']}): {x['display']}"
        items.append(f"""  <item>
    <title>{escape(title)}</title>
    <link>{escape(x['url'])}</link>
    <guid isPermaLink="false">{escape(x['url'])}</guid>
    <pubDate>{format_datetime(when)}</pubDate>
    <description>{escape(m['why'])} More from {escape(m['name'])}: {SITE_URL}/m/{m['id']}.html</description>
  </item>""")
    # stable date (newest letter seen), so the file only changes when letters change
    newest = max((x["first_seen"] for x in letters), default="2026-01-01")
    now = format_datetime(dt.datetime.fromisoformat(newest).replace(tzinfo=dt.timezone.utc))
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>Investor Letters · Ezra's Notes</title>
  <link>{SITE_URL}/</link>
  <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
  <description>New letters from the value investors Ezra reads, linked to the source.</description>
  <language>en</language>
  <lastBuildDate>{now}</lastBuildDate>
{chr(10).join(items)}
</channel>
</rss>
"""
    (OUT / "feed.xml").write_text(feed, encoding="utf-8")


if __name__ == "__main__":
    build()
