# Claude Code setup (web sessions)

This repository is configured for **Claude Code on the web**. A `SessionStart` hook installs the
tooling a fresh remote container needs so that tests and lint run in every session.
(日本語版は後半にあります。)

## What was added

| File | Purpose |
|---|---|
| `.claude/settings.json` | Registers the `SessionStart` hook (project-level settings, shared via git). |
| `.claude/hooks/session-start.sh` | Installs `pytest` + `ruff`; installs `anthropic` only when `ANTHROPIC_API_KEY` is set; exports `PYTHONPATH`, `PYTHONUTF8=1`, `PYTHONDONTWRITEBYTECODE=1` into the session env. Runs **only** when `CLAUDE_CODE_REMOTE=true`, so local sessions are unaffected. |
| `ruff.toml` | Pins a small, stable lint rule set (`E4`, `E7`, `E9`, `F`), target Python 3.11, and excludes generated directories. Without it, recent ruff versions enable a much broader default set. |
| `CLAUDE.md` | Repository guidance for Claude (layout, commands, generated files, governance rules). |

## How it behaves
- **Synchronous**: the session starts only after the hook finishes (about 5 s here; the
  packages are pure wheels). This guarantees `pytest`/`ruff` exist before Claude runs them.
  It can be switched to async (`echo '{"async": true, ...}'` at the top of the script) for a
  faster start at the cost of a possible race.
- **Idempotent**: re-running the hook is a no-op after the first install.
- **Runtime deps**: none. The pipeline is standard-library only; the hook installs dev tools only.

## Validation performed (2026-09-22)
- Hook executed with `CLAUDE_CODE_REMOTE=true`: OK (pytest 9.1.1, ruff 0.16.8 installed; env file written).
- Hook executed without `CLAUDE_CODE_REMOTE`: exits 0 without installing (local no-op).
- Lint: `python -m ruff check pipeline/core.py` runs; 4 pre-existing findings project-wide
  (2× unused import, 1× unused variable, 1× multiple imports on one line), fixed in this branch → 0 findings.
- Tests: `python -m pytest tests/ -q` → 137 passed.

## Activation
The hook takes effect for all future web sessions once this branch is merged into `main`.

## Verify locally
```bash
CLAUDE_CODE_REMOTE=true CLAUDE_PROJECT_DIR="$PWD" CLAUDE_ENV_FILE=/tmp/claude-env ./.claude/hooks/session-start.sh
python -m ruff check .
python -m pytest tests/ -q
```

---

# Claude Code セットアップ（Web セッション向け）

本リポジトリは **Claude Code on the web** 向けに設定済みです。`SessionStart` フックが、新しい
リモートコンテナで必要なツールを導入し、毎セッションでテストと Lint を実行できるようにします。

## 追加ファイル
| ファイル | 役割 |
|---|---|
| `.claude/settings.json` | `SessionStart` フックの登録（プロジェクト設定・git 共有）。 |
| `.claude/hooks/session-start.sh` | `pytest` と `ruff` を導入。`ANTHROPIC_API_KEY` がある時のみ `anthropic` も導入。`PYTHONPATH` / `PYTHONUTF8=1` / `PYTHONDONTWRITEBYTECODE=1` をセッション環境に書き出す。`CLAUDE_CODE_REMOTE=true` の時だけ動作（ローカルには影響なし）。 |
| `ruff.toml` | Lint 規則を小さく固定（`E4`,`E7`,`E9`,`F`）、Python 3.11、生成ディレクトリを除外。未設定だと最近の ruff は既定規則が大幅に広い。 |
| `CLAUDE.md` | Claude 向けのリポジトリ案内（構成・コマンド・生成物・ガバナンス規則）。 |

## 挙動
- **同期実行**：フック完了後にセッション開始（本環境で約5秒）。`pytest`/`ruff` が確実に揃う。
  起動優先なら先頭に `echo '{"async": true, ...}'` を置いて非同期化できる（競合の可能性あり）。
- **冪等**：2回目以降は実質 no-op。
- **ランタイム依存なし**：パイプラインは標準ライブラリのみ。フックは開発ツールのみ導入。

## 検証結果（2026-09-22）
- フック実行（`CLAUDE_CODE_REMOTE=true`）：OK（pytest 9.1.1 / ruff 0.16.8、env ファイル書き出し）。
- `CLAUDE_CODE_REMOTE` 未設定：導入せず exit 0（ローカル no-op）。
- Lint：`python -m ruff check pipeline/core.py` 動作確認。プロジェクト全体で既存の指摘4件
  （未使用 import×2、未使用変数×1、1行複数 import×1）を本ブランチで修正 → 指摘 0 件。
- テスト：`python -m pytest tests/ -q` → 137 passed。

## 有効化
このブランチを `main` にマージすると、以後の Web セッション全てでフックが使われます。
