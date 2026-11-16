# CLAUDE.md — worldtech-jp

Guidance for Claude Code sessions in this repository. Facts below are taken from the code
(`pipeline/`, `tests/`, `.github/workflows/daily.yml`), not from memory.
(日本語の要約は末尾にあります。)

## What this repo is
- **NewsMatome** (repo root): a static, multilingual-collection → Japanese-ization tech news site.
  Pipeline: collect (RSS/Atom) → translate (proposer + deterministic verifier) → summarize →
  render static HTML → search index. Entry point: `python -m pipeline.run_daily --now <ISO8601>`.
- **I am You** (`iamyou/`): public landing page only. `iamyou/index.html` is **generated** by
  `scripts/sync_iamyou_lp.py` from a private source repo. Do not hand-edit it.

## Environment
- Python 3.11, **standard library only** at runtime (no `requirements.txt`).
  Dev tools: `pytest`, `ruff`. Optional: `anthropic` SDK (only used when `ANTHROPIC_API_KEY` is set).
- On Claude Code on the web, `.claude/hooks/session-start.sh` installs `pytest` + `ruff` and
  exports `PYTHONPATH=<repo root>`, `PYTHONUTF8=1`. Locally, run the same commands yourself.

## Commands
```bash
python -m pytest tests/ -q                 # test suite (must stay green; CI gates publishing on it)
python -m ruff check .                     # lint (config: ruff.toml — pyflakes + core pycodestyle)
python -m pipeline.run_daily --now "$(TZ=Asia/Tokyo date +%Y-%m-%dT07:00:00+09:00)"   # build site
python -m http.server 8765                 # preview at http://localhost:8765
```
Always pass `--now` explicitly; the pipeline is deterministic by design.

## Generated files — do not edit by hand
`index.html`, `articles/`, `en/`, `data/*.json`, `intel.html`, `iamyou/index.html`.
`.github/workflows/daily.yml` regenerates and commits them to `main` every day at 07:00 JST.
Change the generator (`pipeline/render.py`, `pipeline/i18n.py`, ...) instead, then rebuild.

## Governance rules (NFR-8 / INV-R1 / INV-R2)
- Translation/summary engines are **proposers, not verdicts**. Every LLM output must pass
  `TranslationVerifier` (source URL required, glossary consistency). Unknown input stays
  **untranslated, never fabricated**. API failure → `None` → fallback to corpus/original text.
- Every article must link its original source. Never remove source attribution.
- Requirement IDs (`FR-`, `NFR-`, `AC-`, ...) in `docs/` are read by the external Claim-Auditor
  `meet(A, B)`; do not write requirement-ID tokens in prose sections that are not requirements.
- Claude/Auditor never signs off requirements. Signatures in `docs/audit/` are human-only.

## Conventions
- Docs pushed to GitHub: English main, Japanese sub. Chat with the maintainer: Japanese.
- Keep changes minimal and covered by a test in `tests/` (tests carry `# covers: FR-xx` comments).
- Env vars: `ANTHROPIC_API_KEY`, `NEWSMATOME_TRANSLATE_MODEL`, `NEWSMATOME_REPORT_MODEL`.

---

## 日本語要約
- ルートは **NewsMatome**（多言語収集→日本語化の静的ニュースサイト）、`iamyou/` は公開LPのみ
  （`iamyou/index.html` は `scripts/sync_iamyou_lp.py` の生成物。手編集禁止）。
- ランタイム依存は標準ライブラリのみ。開発ツールは `pytest` と `ruff`。Web版 Claude Code では
  `.claude/hooks/session-start.sh` が自動インストールし、`PYTHONPATH` / `PYTHONUTF8=1` を設定する。
- テスト：`python -m pytest tests/ -q`、Lint：`python -m ruff check .`、
  サイト生成：`python -m pipeline.run_daily --now <ISO8601>`（`--now` 必須・決定論）。
- 生成物（`index.html`, `articles/`, `en/`, `data/*.json`, `intel.html`）は手編集せず生成器を直す。
- LLM は提案者であり verdict ではない（NFR-8/INV-R2）。出典必須・捏造禁止・署名は人間のみ（INV-R1）。
