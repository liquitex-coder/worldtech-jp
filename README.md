# worldtech-jp

**WORLD TECH, IN JAPANESE** — a multilingual-collection → Japanese-ization news media,
plus a second service (`iamyou/`) sharing this monorepo.

This repository hosts two products to keep management in one place:

| Path | Product | Status |
|---|---|---|
| repo root (`index.html`, `pipeline/`, ...) | **NewsMatome** — collect world tech/science news, Japanese-ize with source attribution, publish every 07:00 JST | working prototype |
| `iamyou/` | **I am You** — real human-agent service. Public landing page only (表紙); member/agent internals stay in the private repo/backend | public LP live |

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

**Public landing page (表紙)** for the *I am You* real-human-agent service — "I can be your
eyes in Japan" (現地視察・購入/発送代行・訪問動画). Served on Pages at `/iamyou/`.

This is the **non-member public layer only** (FR-17 access tiers): concept, values
(eyes/hands/feet), Phase-1 menu and indicative prices, agent-protection policy, legal
notice. The **member area and agent application internals** (auth, quotes, application
management — concrete pricing/strategy) live in the **private `iamyou` repo / backend**
and are intentionally **not published here**. Member CTAs route to LINE intake (MVP).
