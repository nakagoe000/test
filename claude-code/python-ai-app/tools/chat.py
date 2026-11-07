"""文章の相談チャット"""
import streamlit as st

from core.gemini_client import build_contents
from core.ui_common import stream_to_screen

STATE_KEY = "chat__messages"

SYSTEM = (
    "あなたは親身で有能な文章アシスタントです。"
    "文章の書き方、言い回し、構成、アイデア出しなど、ライティング全般の相談に具体的に答えてください。"
    "必要に応じて例文を示し、日本語で回答してください。"
)


def render() -> None:
    st.title("💬 文章相談チャット")

    messages = st.session_state.setdefault(STATE_KEY, [])

    if messages and st.button("🗑️ 会話をリセット"):
        st.session_state[STATE_KEY] = []
        st.rerun()

    if not messages:
        st.info("例: 「退職の挨拶文の書き出しを考えたい」「この文章をもっと説得力のある構成にするには？」")

    for role, text in messages:
        with st.chat_message("user" if role == "user" else "assistant"):
            st.markdown(text)

    user_input = st.chat_input("メッセージを入力")
    if not user_input:
        return

    with st.chat_message("user"):
        st.markdown(user_input)
    turns = messages + [("user", user_input)]
    with st.chat_message("assistant"):
        reply = stream_to_screen(build_contents(turns), SYSTEM)
    # 失敗時は履歴に残さない（エラーは stream_to_screen 内で表示済み）
    if reply is not None:
        st.session_state[STATE_KEY] = turns + [("model", reply)]
