"""SNS投稿作成"""
import streamlit as st

from core.ui_common import BASE_SYSTEM, generate, render_result, require

TOOL_KEY = "sns"

SYSTEM = BASE_SYSTEM + (
    "あなたはSNSマーケティングに精通したコピーライターです。"
    "各プラットフォームの文化と文字数制限を踏まえ、反応を得やすい投稿文を作成してください。"
)

PLATFORMS = {
    "X（旧Twitter）": "全角140字以内。冒頭で興味を引き、簡潔に",
    "Instagram": "1行目で惹きつけ、改行を活用。キャプションとして300〜500字程度",
    "LinkedIn": "ビジネス向けの知見や学びを共有するトーン。300〜700字程度",
    "Threads": "会話的で親しみやすく、500字以内",
    "Facebook": "ストーリー性を持たせ、200〜400字程度",
}


def render() -> None:
    st.title("📣 SNS投稿作成")

    with st.form(f"{TOOL_KEY}__form"):
        content = st.text_area("投稿したい内容 *", height=150, placeholder="例: 新しいブログ記事を公開。在宅ワークの集中術を5つ紹介")
        col1, col2 = st.columns(2)
        platform = col1.selectbox("プラットフォーム", list(PLATFORMS))
        count = col2.number_input("案の数", min_value=1, max_value=5, value=3)
        tone = st.selectbox("トーン", ["親しみやすい", "プロフェッショナル", "熱量高め", "落ち着いた", "ユーモアあり"])
        col3, col4 = st.columns(2)
        hashtags = col3.checkbox("ハッシュタグをつける", value=True)
        emoji = col4.checkbox("絵文字を使う", value=True)
        submitted = st.form_submit_button("✨ 投稿文を作成", type="primary")

    if submitted and require({"投稿したい内容": content}):
        prompt = (
            f"次の内容で{platform}向けの投稿文を{int(count)}案作成してください。\n"
            f"- ルール: {PLATFORMS[platform]}\n"
            f"- トーン: {tone}\n"
            f"- ハッシュタグ: {'適切なものを3〜5個' if hashtags else 'なし'}\n"
            f"- 絵文字: {'適度に使用' if emoji else '使用しない'}\n"
            "- 各案は「### 案1」のような見出しで区切り、案ごとに切り口を変える\n\n"
            f"--- 内容 ---\n{content}"
        )
        generate(TOOL_KEY, prompt, SYSTEM)

    render_result(TOOL_KEY, "sns")
