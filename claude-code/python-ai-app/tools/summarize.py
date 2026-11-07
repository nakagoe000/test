"""文章要約"""
import streamlit as st

from core.ui_common import BASE_SYSTEM, generate, render_result, require, resolve_input_text

TOOL_KEY = "summarize"

SYSTEM = BASE_SYSTEM + (
    "あなたは要点抽出が得意な編集者です。"
    "原文にない情報は加えず、重要な事実・数値・結論を落とさずに要約してください。"
)

FORMATS = {
    "箇条書き": "重要なポイントを箇条書き（- ）で",
    "3行要約": "ちょうど3行で",
    "段落": "自然な文章の段落で",
    "要点＋結論": "「## 要点」（箇条書き）と「## 結論」（1〜2文）の2部構成で",
    "TL;DR": "1文で",
}
LENGTHS = {"短め": "元の約10%", "標準": "元の約20%", "詳しめ": "元の約35%"}


def render() -> None:
    st.title("📄 文章要約")

    with st.form(f"{TOOL_KEY}__form"):
        text = st.text_area("要約したい文章", height=250)
        uploaded = st.file_uploader("またはファイルをアップロード（.txt / .md）", type=["txt", "md"])
        col1, col2 = st.columns(2)
        fmt = col1.selectbox("形式", list(FORMATS))
        length = col2.select_slider("分量", options=list(LENGTHS), value="標準")
        submitted = st.form_submit_button("✨ 要約する", type="primary")

    if submitted:
        source = resolve_input_text(text, uploaded)
        if source is not None and require({"要約したい文章": source}):
            st.caption(f"入力: {len(source):,} 文字")
            prompt = (
                f"次の文章を{FORMATS[fmt]}要約してください。分量の目安は{LENGTHS[length]}です。\n\n"
                f"--- 文章 ---\n{source}"
            )
            generate(TOOL_KEY, prompt, SYSTEM)

    render_result(TOOL_KEY, "summary")
