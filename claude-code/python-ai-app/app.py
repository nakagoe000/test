"""AIライティングツール エントリポイント

起動: streamlit run app.py
"""
import streamlit as st
from dotenv import load_dotenv

# モジュール読み込み前に環境変数を反映する
load_dotenv()

from core.ui_common import render_sidebar_settings  # noqa: E402
from tools import blog, chat, email_reply, headline, proofread, sns, summarize, translate  # noqa: E402

st.set_page_config(page_title="AIライティングツール", page_icon="✍️", layout="centered")

pages = {
    "作成": [
        st.Page(blog.render, title="ブログ記事作成", icon="📝", url_path="blog", default=True),
        st.Page(email_reply.render, title="メール返信作成", icon="✉️", url_path="email"),
        st.Page(sns.render, title="SNS投稿作成", icon="📣", url_path="sns"),
        st.Page(headline.render, title="タイトル・コピー案", icon="💡", url_path="headline"),
    ],
    "編集・変換": [
        st.Page(summarize.render, title="文章要約", icon="📄", url_path="summarize"),
        st.Page(proofread.render, title="校正・リライト", icon="🔍", url_path="proofread"),
        st.Page(translate.render, title="翻訳", icon="🌐", url_path="translate"),
    ],
    "相談": [
        st.Page(chat.render, title="文章相談チャット", icon="💬", url_path="chat"),
    ],
}

navigation = st.navigation(pages)
render_sidebar_settings()
navigation.run()
