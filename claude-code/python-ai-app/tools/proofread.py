"""文章校正・リライト"""
import streamlit as st

from core.ui_common import BASE_SYSTEM, generate, render_result, require, resolve_input_text

TOOL_KEY = "proofread"

SYSTEM = BASE_SYSTEM + (
    "あなたは丁寧で正確な校正者です。原文の意図と事実を変えずに、指示された目的に沿って文章を改善してください。"
)

PURPOSES = {
    "誤字脱字・文法の修正": "誤字脱字、文法の誤り、表記ゆれだけを最小限に修正する",
    "読みやすく改善": "冗長な表現や分かりにくい構文を整理し、読みやすい文章にする",
    "ビジネス敬語に変換": "社外にも出せる適切なビジネス敬語に書き換える",
    "カジュアルに変換": "親しみやすいカジュアルな文体に書き換える",
    "簡潔に短縮": "意味を保ったまま、できるだけ短く簡潔にする",
    "詳しく膨らませる": "具体例や補足を加えて内容を充実させる",
}


def render() -> None:
    st.title("🔍 校正・リライト")

    with st.form(f"{TOOL_KEY}__form"):
        text = st.text_area("対象の文章", height=250)
        uploaded = st.file_uploader("またはファイルをアップロード（.txt / .md）", type=["txt", "md"])
        purpose = st.selectbox("目的", list(PURPOSES))
        explain = st.checkbox("修正点の説明もつける", value=True)
        submitted = st.form_submit_button("✨ 実行する", type="primary")

    if submitted:
        source = resolve_input_text(text, uploaded)
        if source is not None and require({"対象の文章": source}):
            output_rule = (
                "出力は「## 修正後」に修正後の全文、「## 主な修正点」に変更点と理由を箇条書きで示してください。"
                if explain
                else "修正後の全文のみを出力してください。"
            )
            prompt = (
                f"次の文章を、目的「{PURPOSES[purpose]}」に沿って修正してください。\n"
                f"{output_rule}\n\n--- 文章 ---\n{source}"
            )
            generate(TOOL_KEY, prompt, SYSTEM)

    render_result(TOOL_KEY, "proofread")
