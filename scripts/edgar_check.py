"""One-off check of the EDGAR source."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import update
for x in update.edgar_letters({"cik": 1001085}, set(), None):
    print("FOUND", x["period"]["label"], x["url"])
