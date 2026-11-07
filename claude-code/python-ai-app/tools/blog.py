"""ブログ記事作成（SEO対応）"""
from typing import List

import streamlit as st

from core.seo_check import CheckItem, build_checks, build_faq_jsonld, parse_article
from core.ui_common import BASE_SYSTEM, generate, render_result, require

TOOL_KEY = "blog"
OPTS_KEY = f"{TOOL_KEY}__seo_opts"

SYSTEM = BASE_SYSTEM + (
    "あなたはSEOとコンテンツマーケティングに精通したブログライターです。"
    "検索ユーザーの意図に最短で答え、Googleの「有用で信頼できるコンテンツ」の考え方（E-E-A-T）に沿った記事を書きます。\n"
    "SEOのルール:\n"
    "- 記事タイトルは32字前後で、メインキーワードを前半に自然に含める\n"
    "- 導入文の最初の段落でメインキーワードに触れ、読者の悩みと記事の結論を先に示す\n"
    "- H2・H3見出しにメインキーワードやサブキーワード・関連語を自然に含める（全見出しへの機械的な詰め込みは禁止）\n"
    "- 具体例・手順・数値・比較・注意点を入れ、一般論だけで終わらせない\n"
    "- 根拠のない数値や架空の統計・出典は書かない。不確かな情報は断定しない\n"
    "- 段落は短く、箇条書きや表を適度に使い、スマホでも読みやすくする"
)

LENGTHS = {"約1,000字": 1000, "約2,000字": 2000, "約3,000字": 3000, "約5,000字": 5000}
INTENTS = {
    "自動判定": "メインキーワードから検索意図を推測し、それに最適な構成にする",
    "Know（情報を知りたい）": "知りたい情報を網羅的かつ分かりやすく解説する",
    "Do（やり方を知りたい）": "具体的な手順をステップ形式で示し、すぐ実践できるようにする",
    "Buy（購入・申込を検討）": "選ぶ基準・メリット・デメリット・注意点を示し、判断を後押しする",
    "比較（選び方・おすすめ）": "比較軸を明示し、表などで違いが一目で分かるようにする",
}

META_FORMAT = (
    "【SEOメタ情報】\n"
    "- タイトル案1: （32字前後）\n"
    "- タイトル案2: （32字前後・別の切り口）\n"
    "- タイトル案3: （32字前後・別の切り口）\n"
    "- メタディスクリプション: （110〜120字。メインキーワードを含め、記事を読むメリットを伝える）\n"
    "- URLスラッグ: （英小文字とハイフンのみ）\n"
    "\n---\n\n"
)
FAQ_FORMAT = (
    "## よくある質問\n"
    "### Q. 質問文\n"
    "回答文（1〜3文）\n"
    "（検索されやすい関連質問を3〜5問、この形式で）\n"
)


def _build_prompt(
    *, keyword: str, sub_keywords: str, theme: str, reader: str, intent: str,
    mode: str, length: str, tone: str, unique_points: str, notes: str,
) -> str:
    conditions = (
        f"- メインキーワード: {keyword}\n"
        f"- サブキーワード・関連語: {sub_keywords or 'メインキーワードから適切に選定'}\n"
        f"- テーマ・切り口: {theme or 'メインキーワードから最適なものを選定'}\n"
        f"- 想定読者: {reader or 'メインキーワードで検索する人'}\n"
        f"- 検索意図: {INTENTS[intent]}\n"
        f"- 文体: {tone}\n"
        f"- 独自の体験・差別化ポイント: {unique_points or 'なし（一般的な具体例で補う）'}\n"
        f"- その他の要望: {notes or 'なし'}\n"
    )
    if mode == "記事全文":
        return (
            "以下の条件で、SEOに強いブログ記事を書いてください。\n"
            f"- 文字数: 本文{length}\n" + conditions
            + "\n次の形式を厳守して出力してください。\n\n"
            + META_FORMAT
            + "# 記事タイトル（タイトル案1と同じ）\n"
            "導入文\n"
            "## 見出し（H2、必要に応じて ### のH3）\n"
            "本文\n"
            "（H2を3つ以上）\n"
            + FAQ_FORMAT
            + "## まとめ\n"
            "要点の振り返りと読者への次の行動の提案\n"
        )
    return (
        "以下の条件で、SEOに強いブログ記事の構成案を作ってください。\n"
        f"- 想定文字数: {length}\n" + conditions
        + "\n次の形式を厳守して出力してください。各見出しの下には、書く内容の要点を1〜2行の箇条書きで添えてください。\n\n"
        + META_FORMAT
        + "# 記事タイトル（タイトル案1と同じ）\n"
        "## 見出し（H2を3つ以上、必要に応じて ### のH3）\n"
        "## よくある質問\n"
        "### Q. 質問文（3〜5問）\n"
        "## まとめ\n"
    )


def _checks_table(checks: List[CheckItem]) -> str:
    def esc(s: str) -> str:
        return s.replace("|", "\\|")

    rows = ["| 判定 | 項目 | 結果 | アドバイス |", "|:-:|---|---|---|"]
    for c in checks:
        rows.append(f"| {'✅' if c.ok else '⚠️'} | {esc(c.label)} | {esc(c.value)} | {'' if c.ok else esc(c.hint)} |")
    return "\n".join(rows)


def _render_seo(result: str) -> None:
    """生成結果のSEOチェックとFAQ構造化データを表示する"""
    opts = st.session_state.get(OPTS_KEY)
    if not opts:
        return
    outline = opts["mode"] != "記事全文"
    parsed = parse_article(result)
    checks = build_checks(parsed, opts["keyword"], LENGTHS[opts["length"]], outline=outline)

    passed = sum(c.ok for c in checks)
    st.subheader(f"🔎 SEOチェック（{passed}/{len(checks)} 項目クリア）")
    st.markdown(_checks_table(checks))
    st.caption("⚠️ の項目は「追加指示で修正」から改善を依頼できます（例: タイトルを32字前後にして）")

    if outline or opts["skip_jsonld"]:
        return

    st.subheader("🧩 FAQ構造化データ（JSON-LD）")
    if not parsed.faqs:
        st.warning(
            "記事内のFAQ（「## よくある質問」＋「### Q. 質問」形式）を検出できず、構造化データを生成できませんでした。"
            "追加指示で「よくある質問を指定の形式で追加して」と依頼してください。"
        )
        return
    jsonld = build_faq_jsonld(parsed.faqs)
    st.caption(
        f"記事内のFAQ {len(parsed.faqs)} 問から自動生成しました。記事HTMLの本文または <head> に貼り付けてください。"
        "※ GoogleのFAQリッチリザルトは現在、政府・医療系など一部サイトに限定されています。"
    )
    st.code(jsonld, language="html")
    st.download_button(
        "⬇️ JSON-LD", jsonld, file_name="faq_jsonld.html", mime="text/html", key=f"{TOOL_KEY}__dl_jsonld",
    )


def render() -> None:
    st.title("📝 ブログ記事作成（SEO対応）")

    with st.form(f"{TOOL_KEY}__form"):
        keyword = st.text_input("メインキーワード *", placeholder="例: 在宅ワーク 集中力")
        sub_keywords = st.text_input("サブキーワード・関連語（カンマ区切り）", placeholder="例: 集中できない, 作業環境, ポモドーロ")
        theme = st.text_input("テーマ・切り口", placeholder="例: 集中力を保つための習慣と環境づくり")
        reader = st.text_input("想定読者", placeholder="例: リモートワークを始めたばかりの20〜30代会社員")
        col1, col2 = st.columns(2)
        intent = col1.selectbox("検索意図", list(INTENTS))
        mode = col2.selectbox("出力", ["記事全文", "構成案（見出しのみ）"])
        col3, col4 = st.columns(2)
        length = col3.selectbox("文字数の目安", list(LENGTHS), index=2)
        tone = col4.selectbox("文体", ["です・ます調", "だ・である調", "カジュアル", "専門的"])
        unique_points = st.text_area(
            "独自の体験・差別化ポイント",
            placeholder="例: 自分が3年在宅勤務で試して効果があった方法、失敗談など（E-E-A-Tの「経験」として記事の信頼性が高まります）",
            height=80,
        )
        notes = st.text_area("その他の要望", placeholder="例: 初心者向けに専門用語は避ける", height=68)
        skip_jsonld = st.checkbox("FAQ構造化データ（JSON-LD）を出力しない", value=False)
        submitted = st.form_submit_button("✨ 生成する", type="primary")

    if submitted and require({"メインキーワード": keyword}):
        # SEOチェック用に条件を保存（追加指示で修正した結果にも同じ条件で再チェックする）
        previous_opts = st.session_state.get(OPTS_KEY)
        st.session_state[OPTS_KEY] = {
            "keyword": keyword, "mode": mode, "length": length, "skip_jsonld": skip_jsonld,
        }
        prompt = _build_prompt(
            keyword=keyword, sub_keywords=sub_keywords, theme=theme, reader=reader, intent=intent,
            mode=mode, length=length, tone=tone, unique_points=unique_points, notes=notes,
        )
        generate(TOOL_KEY, prompt, SYSTEM)
        # 成功時は generate 内で再描画されるため、ここに来るのは失敗時のみ。前回結果の条件に戻す
        st.session_state[OPTS_KEY] = previous_opts

    render_result(TOOL_KEY, "blog", extra=_render_seo)
