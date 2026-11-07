"""タイトル・キャッチコピー案"""
import streamlit as st

from core.ui_common import BASE_SYSTEM, generate, render_result, require

TOOL_KEY = "headline"

SYSTEM = BASE_SYSTEM + (
    "あなたは数々のヒットを生んだコピーライターです。"
    "ターゲットの心に刺さる、具体的で印象に残る言葉を提案してください。"
)

KINDS = ["ブログ記事タイトル", "キャッチコピー", "メール件名", "YouTube動画タイトル", "商品名・サービス名", "プレゼン資料タイトル"]


def render() -> None:
    st.title("💡 タイトル・キャッチコピー案")

    with st.form(f"{TOOL_KEY}__form"):
        content = st.text_area("内容・概要 *", height=150, placeholder="例: 初心者向けに、1日10分でできる筋トレ習慣を紹介する記事")
        col1, col2 = st.columns(2)
        kind = col1.selectbox("種類", KINDS)
        count = col2.slider("案の数", min_value=3, max_value=20, value=10)
        target = st.text_input("ターゲット", placeholder="例: 運動が続かない30代")
        with_reason = st.checkbox("各案の狙いも書く", value=True)
        submitted = st.form_submit_button("✨ 案を出す", type="primary")

    if submitted and require({"内容・概要": content}):
        prompt = (
            f"次の内容について「{kind}」の案を{count}個、番号付きリストで出してください。\n"
            f"- ターゲット: {target or '指定なし'}\n"
            "- 数字・ベネフィット・意外性・問いかけなど、案ごとに異なる切り口を使う\n"
            f"- {'各案の後に「— 狙い: 」として一言で意図を添える' if with_reason else '案のみを出力する'}\n"
            "- 最後に「## おすすめ」として最も良い1案とその理由を書く\n\n"
            f"--- 内容 ---\n{content}"
        )
        generate(TOOL_KEY, prompt, SYSTEM)

    render_result(TOOL_KEY, "headline")
