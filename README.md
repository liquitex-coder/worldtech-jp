# worldtech-jp

**WORLD TECH, IN JAPANESE** — a multilingual-collection → Japanese-ization news media,
plus a second service (`iamyou/`) sharing this monorepo.

This repository hosts two products to keep management in one place:

| Path | Product | Status |
|---|---|---|
| repo root (`index.html`, `pipeline/`, ...) | **NewsMatome** — collect world tech/science news, Japanese-ize with source attribution, publish every 07:00 JST | working prototype |
| `iamyou/` | **I am You** — (service concept TBD) | reserved / not started |

## NewsMatome (root)

A static, SEO-friendly news site whose content is produced by a deterministic pipeline:
**collect (RSS/Atom) → translate (proposal + deterministic verifier, no fabrication) →
summarize → render static HTML → full-text search index**. 13 categories grouped into
pull-down menus; per-category specialist-agent bylines; original source always linked.

### Layout
- `index.html`, `article.html`, `about.html` — pages (card grid is generated)
- `articles/` — generated per-article pages
- `css/style.css` — styles (modern tech-media, dark glow category nav)
- `pipeline/` — `core.py` (collect/orchestrate), `translate.py`, `summarize.py`,
  `collect_rss.py`, `render.py`, `search.py`, `run_daily.py` (07:00 batch)
- `data/` — generated `articles.json` / `search-index.json`
- `tests/` — pytest acceptance + pipeline tests
- `docs/` — requirement spec (Claim-Auditor `meet(A,B)`) + audit logs + signatures

### Run
```bash
python -m pipeline.run_daily          # collect → translate → summarize → render → index
python -m pytest tests/ -q            # tests
python -m http.server 8765            # preview at http://localhost:8765
```

### Governance (NFR-8 / INV-R2)
Translation/summary engines are **proposers, not verdicts**: every output passes a
deterministic verifier (source required, glossary consistency); unknown input is left
**untranslated, not fabricated**. Foreign content is quoted within limits with the
original source always linked.

## I am You (`iamyou/`)

Reserved for a separate service kept in the same repo to avoid multi-repo overhead.
Concept to be defined.
