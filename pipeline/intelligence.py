"""インテリジェンス substrate：事実から確度を積み上げる推論基盤（INV-R2 / NFR-8）。

設計原理は `core.py` と同じ「LLM/翻訳は提案であって verdict に非ず」「決定論・乱数なし」を継承。
**言語処理（抽出・文章化）はモデル、推論の確度と採否はコード**。この層は LLM-free・オフライン・
決定論で、証拠（Fact）から確度（Confidence）を計算し、裏付けなき主張を admission で弾く。

データモデルは document 中心ではなく claim/evidence 中心：
    Entity ← Signal Channel ← Fact → Claim（仮説）→ Inference（導出）→（公開ゲート）→ 記者

本モジュールは骨格（v0）であり `run_daily` には未接続（表示は不変）。記者/タスキングは後段でこれを消費する。
設計契約は docs/intelligence-substrate.md を参照。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from urllib.parse import urlparse


# ----------------------------------------------------------------- 確度（順序ラベル）
class Confidence(IntEnum):
    """確度の段。証拠が許す以上に上げない（単調・決定論）。"""
    UNVERIFIED = 0   # 未確認
    LOW = 1          # 低
    MEDIUM = 2       # 中
    HIGH = 3         # 高
    CONFIRMED = 4    # 確定


_LABELS = {0: "未確認", 1: "低", 2: "中", 3: "高", 4: "確定"}


def confidence_label(c: Confidence) -> str:
    """確度 → 日本語ラベル（公開時の表示用）。"""
    return _LABELS[int(c)]


# --------------------------------------------------- 周辺信号チャネルと Admiralty 信頼度
# Admiralty 流の信頼度グレード A（最高）..F（判定不能）を 0.0–1.0 の重みへ写像（決定論）。
_GRADE_RANK = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1, "F": 0}

# 収集チャネルと既定の信頼度グレード。法定開示（義務的公開）が最上位。
# 実運用では各チャネルの収集アダプタを差し込む（このPRでは型のみ）。
CHANNELS: dict[str, str] = {
    "disclosure":   "A",   # 法定開示：大量保有報告書・持分異動・8-K/13D/Form 4（義務的公開）
    "filings":      "A",   # 各種法定届出
    "equity":       "A",   # 取得・売却株式（開示ベースの持分異動）
    "official":     "B",   # 公式発表・プレスリリース
    "supply_chain": "C",   # 取引先・納品先の動き
    "energy":       "C",   # 使用電力量
    "hiring":       "C",   # 求人動向
    "press":        "C",   # 報道
    "forum":        "E",   # 掲示板・SNS（弱い信号）
}

# 矛盾として確度を下げるのは「信頼できる」反証のみ（グレード C 以上）。
_CREDIBLE_RANK = _GRADE_RANK["C"]


def _host(url: str) -> str:
    host = (urlparse(url).netloc or "").lower()
    return host[4:] if host.startswith("www.") else host


# ----------------------------------------------------------------- データモデル
@dataclass(frozen=True)
class Fact:
    """証拠原子：ソースの実在する一節から抽出した最小の主張（INV-R2 の錨）。

    Fact は決して発明しない。必ず実ソースの span（raw_excerpt）に紐づく＝後から監査できる。
    """
    statement: str          # 正規化した主張（例「X社がY社株を5.2%取得」）
    source_url: str         # 一次情報の出典（必須）
    channel: str            # 収集チャネル（CHANNELS のいずれか）
    raw_excerpt: str        # ソースの実際の一節（監査用・捏造防止の証跡。必須）
    observed_at: str        # 観測時刻（呼び出し側が渡す＝決定論）
    entity: str = ""        # 対象エンティティ（企業名など）
    origin: str = ""        # 独立系統キー（同一原典の焼き直しを畳む。空なら host で代替）
    reliability: str = ""   # 信頼度グレード上書き（空ならチャネル既定）

    def grade(self) -> str:
        return self.reliability or CHANNELS.get(self.channel, "F")

    def system(self) -> str:
        """独立系統の識別子（焼き直し畳み込み用）。"""
        return self.origin or _host(self.source_url)


@dataclass
class Claim:
    """命題（仮説）：同じ事象について複数 Fact が支持/矛盾する正規化主張。"""
    statement: str
    supporting: list[Fact] = field(default_factory=list)
    contradicting: list[Fact] = field(default_factory=list)
    entity: str = ""


@dataclass
class Inference:
    """導出：複数 Claim を規則で組み合わせ、誰も明言していない結論を生成（C ← A∧B）。

    観測された Fact ではなく**導出**であることを derived=True で明示し、チェーン（premises/rule）を保持する。
    """
    statement: str
    premises: list[Claim] = field(default_factory=list)
    rule: str = ""          # 適用した導出規則の名前（監査用）
    entity: str = ""
    derived: bool = True     # 公開時は「編集部の推論」として事実と分離表示する


@dataclass(frozen=True)
class AdmissionResult:
    ok: bool
    reason: str
    confidence: Confidence


# ----------------------------------------------------------------- admission（採否）
def is_admissible_fact(fact: Fact) -> tuple[bool, str]:
    """Fact が構造的に採用可能か（出典・正規チャネル・原文span を持つか）。"""
    if not fact.source_url:
        return False, "no-source"                 # 出典なきものは採らない（INV-R2）
    if fact.channel not in CHANNELS:
        return False, f"unknown-channel:{fact.channel}"
    if not fact.raw_excerpt.strip():
        return False, "no-excerpt"                # 原文span なき＝監査不能＝捏造の温床
    return True, "ok"


def _independent_systems(facts: list[Fact]) -> set[str]:
    """独立系統の集合。同一原典の焼き直しは1つに畳む（本数ではなく系統数）。"""
    return {f.system() for f in facts if is_admissible_fact(f)[0]}


def _best_grade(facts: list[Fact]) -> str:
    valid = [f for f in facts if is_admissible_fact(f)[0]]
    return max((f.grade() for f in valid), key=lambda g: _GRADE_RANK.get(g, 0))


def _base_confidence(grade: str, n_systems: int) -> Confidence:
    """信頼度グレード×独立系統数 → 基礎確度（決定論のはしご）。

    グレードが高いほど少数の系統で上位へ到達する。
    """
    rank = _GRADE_RANK.get(grade, 0)
    if n_systems <= 0:
        return Confidence.UNVERIFIED
    if rank >= _GRADE_RANK["A"]:                   # A：法定開示など
        return Confidence.CONFIRMED if n_systems >= 2 else Confidence.HIGH
    if rank >= _GRADE_RANK["B"]:                   # B：公式発表
        if n_systems >= 3:
            return Confidence.CONFIRMED
        return Confidence.HIGH if n_systems == 2 else Confidence.MEDIUM
    if rank >= _GRADE_RANK["C"]:                   # C：報道・周辺信号
        if n_systems >= 3:
            return Confidence.HIGH
        return Confidence.MEDIUM if n_systems == 2 else Confidence.LOW
    # D/E/F：弱い信号は系統数を多く要求する
    if n_systems >= 4:
        return Confidence.HIGH
    if n_systems == 3:
        return Confidence.MEDIUM
    return Confidence.LOW if n_systems == 2 else Confidence.UNVERIFIED


def claim_confidence(claim: Claim) -> Confidence:
    """Claim の確度を証拠から計算する（独立性で上げ、信頼できる矛盾で下げる・決定論）。"""
    support_systems = _independent_systems(claim.supporting)
    if not support_systems:
        return Confidence.UNVERIFIED              # 裏付けゼロ → 未確認
    base = _base_confidence(_best_grade(claim.supporting), len(support_systems))
    # 信頼できる（C 以上）独立な反証の系統数だけ1段ずつ下げる
    credible_contra = [
        f for f in claim.contradicting
        if is_admissible_fact(f)[0] and _GRADE_RANK.get(f.grade(), 0) >= _CREDIBLE_RANK
    ]
    steps = len(_independent_systems(credible_contra))
    return Confidence(max(int(Confidence.UNVERIFIED), int(base) - steps))


def inference_confidence(inf: Inference) -> Confidence:
    """導出の確度 = 前提 Claim の確度の最小（弱い前提が天井・証拠が許す上限を超えない）。"""
    if not inf.premises:
        return Confidence.UNVERIFIED
    return Confidence(min(int(claim_confidence(c)) for c in inf.premises))


def admit_claim(claim: Claim) -> AdmissionResult:
    """Claim を採否判定：採用可能な支持 Fact が無ければ不採用。"""
    if not _independent_systems(claim.supporting):
        return AdmissionResult(False, "no-evidence", Confidence.UNVERIFIED)
    return AdmissionResult(True, "ok", claim_confidence(claim))


def admit_inference(inf: Inference) -> AdmissionResult:
    """Inference を採否判定：derived 明示・前提が全て admissible・チェーンが Fact に解決すること。"""
    if not inf.derived:
        return AdmissionResult(False, "not-flagged-derived", Confidence.UNVERIFIED)
    if not inf.premises:
        return AdmissionResult(False, "no-premises", Confidence.UNVERIFIED)
    for c in inf.premises:
        if not admit_claim(c).ok:
            return AdmissionResult(False, "premise-not-admissible", Confidence.UNVERIFIED)
    return AdmissionResult(True, "ok", inference_confidence(inf))


def publishable(confidence: Confidence, *, min_confidence: Confidence = Confidence.MEDIUM) -> bool:
    """公開可否（確度側のゲート）。権利側（NFR-4）は compliance.py に委譲する。"""
    return int(confidence) >= int(min_confidence)


# ----------------------------------------------------------------- タスキング（掘る順）
def rank_channels(channels: list[str]) -> list[str]:
    """「どれを掘るか」を信頼度順に並べる（決定論）。

    v0 は信頼度のみ。実運用では期待情報価値×コスト項を加える（docs 参照）。
    同グレードは登録順を保つ安定ソート。
    """
    return sorted(channels, key=lambda c: -_GRADE_RANK.get(CHANNELS.get(c, "F"), 0))


# ----------------------------------------------------------------- 決定論サンプル（テスト/spec用）
def sample_facts(observed_at: str = "2026-06-08T07:00:00+09:00") -> list[Fact]:
    """周辺積み上げの最小例（架空企業 ACME・全て .example・独立系統3つ）。"""
    return [
        Fact("Fund-X が ACME Robotics 株を5.2%取得（大量保有報告書）",
             "https://edinet.example/acme/holdings", "disclosure",
             raw_excerpt="保有割合 5.2% 提出者 Fund-X", observed_at=observed_at,
             entity="ACME Robotics", origin="edinet.example/fund-x"),
        Fact("ACME Robotics が新規サプライヤと部品供給契約",
             "https://press.example/acme-supplier", "supply_chain",
             raw_excerpt="ACME は新サプライヤと供給契約を締結", observed_at=observed_at,
             entity="ACME Robotics", origin="press.example/acme-supplier"),
        Fact("ACME 主力工場の電力使用量が前年同月比+38%",
             "https://energy.example/acme-plant", "energy",
             raw_excerpt="当該地区の需要は前年比+38%", observed_at=observed_at,
             entity="ACME Robotics", origin="energy.example/acme-plant"),
    ]


def sample_inference() -> Inference:
    """周辺信号を積み上げた導出の最小例：大株主出現＋増産局面 → 拡張投資フェーズ。"""
    f = sample_facts()
    major_holder = Claim("ACME に新たな大株主が出現", supporting=[f[0]], entity="ACME Robotics")
    ramping = Claim("ACME は増産局面にある", supporting=[f[1], f[2]], entity="ACME Robotics")
    return Inference(
        "ACME は拡張投資フェーズに入った可能性",
        premises=[major_holder, ramping],
        rule="major_holder & production_ramp -> expansion",
        entity="ACME Robotics",
    )
