"""One-off check: what would the EDGAR source find if we had no letters yet?"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import update
for x in update.edgar_letters({"cik": 1001085, "lookback_days": 400}, set(), None):
    print(x["period"]["label"], "|", x["text"][:60], "|", x["url"])
