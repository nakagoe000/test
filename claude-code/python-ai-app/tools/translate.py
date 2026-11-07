"""翻訳"""
import streamlit as st

from core.ui_common import BASE_SYSTEM, generate, render_result, require, resolve_input_text

TOOL_KEY = "translate"

SYSTEM = BASE_SYSTEM + (
    "あなたはプロの翻訳者です。原文の意味・ニュアンス・トーンを正確に保って翻訳してください。"
    "元の文章の段落構成や書式は維持してください。"
)

LANGUAGES = ["英語", "日本語", "中国語（簡体字）", "中国語（繁体字）", "韓国語", "スペイン語", "フランス語", "ドイツ語"]
STYLES = {
    "自然な訳": "ネイティブが読んで自然な表現を優先する",
    "直訳寄り": "原文の構造と語順にできるだけ忠実に訳す",
    "ビジネス向け": "ビジネス文書にふさわしいフォーマルな表現で訳す",
    "カジュアル": "会話的でくだけた表現で訳す",
}


def render() -> None:
    st.title("🌐 翻訳")

    with st.form(f"{TOOL_KEY}__form"):
        text = st.text_area("翻訳したい文章", height=250)
        uploaded = st.file_uploader("またはファイルをアップロード（.txt / .md）", type=["txt", "md"])
        col1, col2 = st.columns(2)
        target = col1.selectbox("翻訳先の言語", LANGUAGES)
        style = col2.selectbox("訳し方", list(STYLES))
        explain = st.checkbox("訳し分けのポイント・注意点も表示する")
        submitted = st.form_submit_button("✨ 翻訳する", type="primary")

    if submitted:
        source = resolve_input_text(text, uploaded)
        if source is not None and require({"翻訳したい文章": source}):
            output_rule = (
                "訳文の後に「## 翻訳メモ」として、意訳した箇所や注意すべき表現を日本語で箇条書きしてください。"
                if explain
                else "訳文のみを出力してください。"
            )
            prompt = (
                f"次の文章を{target}に翻訳してください。方針: {STYLES[style]}。\n"
                f"{output_rule}\n\n--- 原文 ---\n{source}"
            )
            generate(TOOL_KEY, prompt, SYSTEM)

    render_result(TOOL_KEY, "translation")
