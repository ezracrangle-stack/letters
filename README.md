# Investor Letters · Ezra's Notes

Static site at **letters.ezrasnotes.com**: hand-picked investor letters, linked to the source.

- `managers.yaml` is the only file to edit (see `COMO-EDITAR.md`).
- Every Monday GitHub Actions runs `scripts/update.py` (finds new letters, never deletes) and `scripts/build.py` (writes the site to `docs/`).
- If a manager's page fails, an issue labeled `letters-alert` is opened.
- Offline test: `python scripts/update.py --fixtures tests/fixtures && python scripts/build.py`
