"""ブログ記事のSEO簡易チェックとFAQ構造化データ生成（Streamlit非依存）

生成結果は次の形式を前提とする:
    【SEOメタ情報】
    - タイトル案1: ...
    - メタディスクリプション: ...
    - URLスラッグ: ...
    ---
    # 記事タイトル
    導入文
    ## 見出し
    ## よくある質問
    ### Q. 質問
    回答
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# 判定の目安
TITLE_RANGE = (28, 40)
DESCRIPTION_RANGE = (90, 130)
MAX_KEYWORD_DENSITY = 0.05
MIN_KEYWORD_COUNT = 3
MIN_H2_COUNT = 3
MIN_HEADING_KEYWORD_RATIO = 0.3

_META_PATTERNS = {
    "title": re.compile(r"^\s*[-*]?\s*タイトル案\s*\d*\s*[:：]\s*(.+)$"),
    "description": re.compile(r"^\s*[-*]?\s*メタディスクリプション\s*[:：]\s*(.+)$"),
    "slug": re.compile(r"^\s*[-*]?\s*URLスラッグ\s*[:：]\s*(.+)$"),
}
_H1 = re.compile(r"^#\s+(.+)$")
_HEADING = re.compile(r"^(#{2,3})\s+(.+)$")
_FAQ_HEADING = re.compile(r"よくある質問|FAQ|Q\s*&\s*A", re.IGNORECASE)
_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass
class CheckItem:
    label: str
    value: str
    ok: bool
    hint: str = ""


@dataclass
class FaqItem:
    question: str
    answer: str


@dataclass
class ParsedArticle:
    title_candidates: List[str] = field(default_factory=list)
    meta_description: str = ""
    slug: str = ""
    title: str = ""
    intro: str = ""
    headings: List[Tuple[int, str]] = field(default_factory=list)  # (レベル, 見出し文)
    body: str = ""  # H1以降の記事本文（Markdown）
    faqs: List[FaqItem] = field(default_factory=list)


def _clean(text: str) -> str:
    """Markdownの強調・リンク・括弧などを除いた素のテキストにする"""
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[*_`]", "", text)
    return text.strip().strip("「」『』\"'")


def _plain_text(markdown: str) -> str:
    """文字数カウント用に記号を除いたテキスト"""
    lines = []
    for line in markdown.splitlines():
        line = re.sub(r"^\s*(#{1,6}|[-*+]|\d+[.)]|>)\s*", "", line)
        lines.append(_clean(line))
    return "\n".join(lines)


def count_chars(markdown: str) -> int:
    """空白・改行を除いた文字数"""
    return len(re.sub(r"\s", "", _plain_text(markdown)))


def split_keywords(keyword: str) -> List[str]:
    """「在宅ワーク 集中力」のような複合キーワードを語に分割する"""
    return [t for t in re.split(r"[\s　]+", keyword.strip()) if t]


def _strip_prefix(text: str, letter: str) -> str:
    """「Q.」「A：」などの接頭辞を除く"""
    return re.sub(rf"^\s*{letter}\s*\d*\s*[.．:：、]?\s*", "", text)


def _parse_faqs(lines: List[str]) -> List[FaqItem]:
    faqs: List[FaqItem] = []
    in_faq = False
    question: Optional[str] = None
    answer_lines: List[str] = []

    def flush() -> None:
        if question and answer_lines:
            # 日本語の句読点の後ろには空白を入れずに連結する
            joined = re.sub(r"(?<=[。！？!?])\s+", "", " ".join(answer_lines))
            answer = _strip_prefix(joined, "A")
            faqs.append(FaqItem(question=question, answer=answer))

    for line in lines:
        m = _HEADING.match(line)
        if m and len(m.group(1)) == 2:
            if in_faq:
                break  # FAQセクションの終わり
            in_faq = bool(_FAQ_HEADING.search(m.group(2)))
            continue
        if not in_faq:
            continue
        if m and len(m.group(1)) == 3:
            flush()
            question = _strip_prefix(_clean(m.group(2)), "Q")
            answer_lines = []
        elif question is not None and line.strip():
            answer_lines.append(_clean(line))
    if in_faq:
        flush()
    return faqs


def parse_article(text: str) -> ParsedArticle:
    """生成結果からメタ情報・見出し・FAQなどを抽出する"""
    parsed = ParsedArticle()
    lines = text.splitlines()

    h1_index: Optional[int] = None
    for i, line in enumerate(lines):
        m = _H1.match(line)
        if m:
            h1_index = i
            parsed.title = _clean(m.group(1))
            break
        for key, pattern in _META_PATTERNS.items():
            mm = pattern.match(line)
            if not mm:
                continue
            value = _clean(mm.group(1))
            if key == "title":
                parsed.title_candidates.append(value)
            elif key == "description":
                parsed.meta_description = value
            else:
                parsed.slug = value

    if h1_index is None:
        return parsed

    article_lines = lines[h1_index:]
    parsed.body = "\n".join(article_lines)

    intro_lines: List[str] = []
    for line in article_lines[1:]:
        if _HEADING.match(line):
            break
        if line.strip() and line.strip() != "---":
            intro_lines.append(line)
    parsed.intro = _plain_text("\n".join(intro_lines))

    for line in article_lines:
        m = _HEADING.match(line)
        if m:
            parsed.headings.append((len(m.group(1)), _clean(m.group(2))))

    parsed.faqs = _parse_faqs(article_lines)
    return parsed


def _contains_all(text: str, terms: List[str]) -> bool:
    lowered = text.lower()
    return all(t.lower() in lowered for t in terms)


def _contains_any(text: str, terms: List[str]) -> bool:
    lowered = text.lower()
    return any(t.lower() in lowered for t in terms)


def build_checks(
    parsed: ParsedArticle,
    keyword: str,
    target_chars: Optional[int] = None,
    outline: bool = False,
) -> List[CheckItem]:
    """SEOの目安に沿ったチェック結果を返す。outline=True は構成案向け（本文系の判定を省く）"""
    terms = split_keywords(keyword)
    checks: List[CheckItem] = []

    # メタ情報
    if parsed.meta_description:
        n = len(parsed.meta_description)
        lo, hi = DESCRIPTION_RANGE
        checks.append(CheckItem(
            "メタディスクリプション文字数", f"{n}字", lo <= n <= hi, f"{lo}〜{hi}字が目安です",
        ))
        checks.append(CheckItem(
            "メタディスクリプションにKW", "あり" if _contains_all(parsed.meta_description, terms) else "なし",
            _contains_all(parsed.meta_description, terms), "メインキーワードを含めるとクリック率向上が期待できます",
        ))
    else:
        checks.append(CheckItem("メタディスクリプション", "未検出", False, "追加指示で作成を依頼してください"))

    if parsed.slug:
        checks.append(CheckItem(
            "URLスラッグ", parsed.slug, bool(_SLUG.match(parsed.slug)), "英小文字・数字・ハイフンのみが推奨です",
        ))

    # タイトル
    if not parsed.title:
        checks.append(CheckItem("記事タイトル（H1）", "未検出", False, "「# タイトル」の形式で出力されていません"))
        return checks
    n = len(parsed.title)
    lo, hi = TITLE_RANGE
    checks.append(CheckItem("タイトル文字数", f"{n}字", lo <= n <= hi, f"{lo}〜{hi}字（32字前後）が目安です"))
    has_kw = _contains_all(parsed.title, terms)
    checks.append(CheckItem("タイトルにKW", "あり" if has_kw else "なし", has_kw, "メインキーワードを含めてください"))
    if has_kw and terms:
        pos = parsed.title.lower().find(terms[0].lower())
        checks.append(CheckItem(
            "KWの位置（タイトル）", f"{pos + 1}文字目", pos < n / 2, "キーワードはタイトルの前半に置くのが効果的です",
        ))

    # 見出し
    h2 = [t for level, t in parsed.headings if level == 2]
    checks.append(CheckItem("H2見出し数", f"{len(h2)}個", len(h2) >= MIN_H2_COUNT, f"{MIN_H2_COUNT}個以上が目安です"))
    if parsed.headings:
        hit = sum(1 for _, t in parsed.headings if _contains_any(t, terms))
        ratio = hit / len(parsed.headings)
        checks.append(CheckItem(
            "見出しのKW含有率", f"{hit}/{len(parsed.headings)}（{ratio:.0%}）",
            ratio >= MIN_HEADING_KEYWORD_RATIO, f"{MIN_HEADING_KEYWORD_RATIO:.0%}以上の見出しにKW・関連語を含めましょう",
        ))

    has_faq_heading = any(level == 2 and _FAQ_HEADING.search(t) for level, t in parsed.headings)
    checks.append(CheckItem(
        "FAQセクション",
        f"{len(parsed.faqs)}問" if parsed.faqs else ("見出しのみ" if has_faq_heading else "なし"),
        bool(parsed.faqs) or (outline and has_faq_heading),
        "「## よくある質問」＋「### Q. 質問」形式で追加してください",
    ))

    if outline:
        return checks

    # 本文
    total = count_chars(parsed.body)
    if target_chars:
        checks.append(CheckItem(
            "本文文字数", f"{total:,}字 / 目安{target_chars:,}字", total >= target_chars * 0.7,
            "目安の70%未満です。追加指示で加筆を依頼してください",
        ))
    else:
        checks.append(CheckItem("本文文字数", f"{total:,}字", True))

    intro_ok = _contains_all(parsed.intro, terms)
    checks.append(CheckItem("導入文にKW", "あり" if intro_ok else "なし", intro_ok, "導入文の冒頭でキーワードに触れましょう"))

    plain = _plain_text(parsed.body).lower()
    for term in terms:
        count = plain.count(term.lower())
        density = count * len(term) / total if total else 0.0
        if count < MIN_KEYWORD_COUNT:
            ok, hint = False, f"出現が少なめです（{MIN_KEYWORD_COUNT}回以上が目安）"
        elif density > MAX_KEYWORD_DENSITY:
            ok, hint = False, f"密度が{MAX_KEYWORD_DENSITY:.0%}超で詰め込み気味です"
        else:
            ok, hint = True, ""
        checks.append(CheckItem(f"KW「{term}」出現", f"{count}回（密度{density:.1%}）", ok, hint))

    return checks


def build_faq_jsonld(faqs: List[FaqItem]) -> str:
    """FAQPage の構造化データ（scriptタグ込み）を生成する"""
    if not faqs:
        raise ValueError("FAQが空のため構造化データを生成できません。")
    data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": faq.question,
                "acceptedAnswer": {"@type": "Answer", "text": faq.answer},
            }
            for faq in faqs
        ],
    }
    # scriptタグ内で "</" が閉じタグと解釈されないようエスケープ
    body = json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")
    return f'<script type="application/ld+json">\n{body}\n</script>'
