"""One-off check of the EDGAR source."""
import sys, pathlib, re, time, requests
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import update
s = requests.Session(); s.headers.update({"User-Agent": update.EDGAR_UA})
r = s.get("https://data.sec.gov/submissions/CIK0001001085.json", timeout=30)
print("status", r.status_code)
rec = r.json()["filings"]["recent"]
for form, acc, date, doc, desc in list(zip(rec["form"], rec["accessionNumber"], rec["filingDate"], rec["primaryDocument"], rec["primaryDocDescription"]))[:80]:
    if form in ("6-K", "40-F"):
        print("F", form, date, acc, doc, "|", desc)
time.sleep(1)
acc = "0001001085-26-000021"
idx = f"https://www.sec.gov/Archives/edgar/data/1001085/{acc.replace('-','')}/{acc}-index.htm"
p = s.get(idx, timeout=30); print("index", p.status_code, len(p.text))
from bs4 import BeautifulSoup
for row in BeautifulSoup(p.text, "html.parser").select("table.tableFile tr")[:8]:
    print("R", [c.get_text(" ").strip()[:50] for c in row.find_all("td")], [a["href"] for a in row.find_all("a")])
print("FOUND", update.edgar_letters({"cik": 1001085}, set(), None))
