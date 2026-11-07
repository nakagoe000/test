"""メール返信作成"""
import streamlit as st

from core.ui_common import BASE_SYSTEM, generate, render_result, require

TOOL_KEY = "email"

SYSTEM = BASE_SYSTEM + (
    "あなたはビジネスコミュニケーションに長けた秘書です。"
    "相手との関係を良好に保ちつつ、要件が明確に伝わるメールを書いてください。"
    "Markdownの装飾は使わず、そのままメールに貼り付けられるプレーンテキストで出力してください。"
)


def render() -> None:
    st.title("✉️ メール返信作成")

    with st.form(f"{TOOL_KEY}__form"):
        received = st.text_area("受信したメール *", height=200, placeholder="返信したいメール本文を貼り付け")
        points = st.text_area("返信で伝えたいこと", height=100, placeholder="例: 来週火曜14時なら参加可能。資料は前日までに送る")
        col1, col2 = st.columns(2)
        politeness = col1.selectbox("丁寧さ", ["ビジネス（社外向け・丁寧）", "社内向け（やや丁寧）", "カジュアル（友人・知人）"])
        stance = col2.selectbox("返答の方向性", ["指定なし", "承諾する", "丁重に断る", "保留・確認したい", "お礼を伝える", "お詫びする"])
        signature = st.text_input("署名・名前", placeholder="例: 山田太郎")
        with_subject = st.checkbox("件名も作成する", value=True)
        submitted = st.form_submit_button("✨ 返信文を作成", type="primary")

    if submitted and require({"受信したメール": received}):
        prompt = (
            "以下のメールへの返信文を作成してください。\n"
            f"- 丁寧さ: {politeness}\n"
            f"- 返答の方向性: {stance}\n"
            f"- 伝えたいこと: {points or '受信内容から適切に判断'}\n"
            f"- 署名: {signature or '[名前]'}\n"
            f"- 件名: {'「件名: 」として1行目に記載' if with_subject else '不要'}\n"
            "- 不明な日時や固有名詞は推測せず [　] のプレースホルダーにする\n\n"
            f"--- 受信メール ---\n{received}"
        )
        generate(TOOL_KEY, prompt, SYSTEM)

    render_result(TOOL_KEY, "email_reply")
