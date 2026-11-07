"""各ツールで共通利用するUI部品"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple

import streamlit as st

from core.gemini_client import (
    AVAILABLE_MODELS,
    DEFAULT_MODEL,
    Contents,
    GeminiError,
    build_contents,
    stream_generate,
)

# 全ツール共通のシステムプロンプト
BASE_SYSTEM = (
    "あなたは経験豊富なプロのライター兼編集者です。"
    "指示された成果物の本文のみを出力し、「承知しました」などの前置きや締めの挨拶は書かないでください。"
    "特に指定がなければ日本語で、Markdown形式で出力してください。"
)


def render_sidebar_settings() -> None:
    """サイドバーにモデル設定を表示する"""
    with st.sidebar:
        st.divider()
        st.subheader("⚙️ 設定")
        env_model = os.getenv("GEMINI_MODEL", "").strip()
        models = list(AVAILABLE_MODELS)
        if env_model and env_model not in models:
            models.insert(0, env_model)
        default = env_model or DEFAULT_MODEL
        st.selectbox("モデル", models, index=models.index(default), key="model")
        st.slider(
            "創造性（temperature）",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.1,
            key="temperature",
            help="低いほど安定した出力、高いほど多様な出力になります",
        )
        if not os.getenv("GEMINI_API_KEY", "").strip():
            st.text_input(
                "Gemini APIキー",
                type="password",
                key="api_key_input",
                help=".env に GEMINI_API_KEY を設定すると入力不要になります",
            )


def stream_to_screen(contents: Contents, system: str) -> Optional[str]:
    """Geminiの出力を画面にストリーミング表示し、全文を返す。失敗時はエラー表示して None"""
    try:
        text = st.write_stream(
            stream_generate(
                contents,
                system_instruction=system,
                model=st.session_state.get("model", DEFAULT_MODEL),
                temperature=st.session_state.get("temperature", 0.7),
                api_key=st.session_state.get("api_key_input"),
            )
        )
    except GeminiError as e:
        st.error(str(e))
        return None
    return text if isinstance(text, str) else "".join(str(t) for t in text)


def _state_key(tool_key: str) -> str:
    return f"{tool_key}__state"


def generate(tool_key: str, prompt: str, system: str) -> None:
    """初回生成。成功したら結果を保存して再描画する"""
    turns: List[Tuple[str, str]] = [("user", prompt)]
    with st.container(border=True):
        text = stream_to_screen(build_contents(turns), system)
    if text is None:
        return
    turns.append(("model", text))
    st.session_state[_state_key(tool_key)] = {"system": system, "turns": turns}
    st.rerun()


def render_result(
    tool_key: str,
    file_prefix: str,
    extra: Optional[Callable[[str], None]] = None,
) -> None:
    """生成結果・コピー・ダウンロード・追加指示での修正を表示する

    extra: 結果テキストを受け取り、ツール固有の表示（SEOチェック等）を行う関数
    """
    state = st.session_state.get(_state_key(tool_key))
    if not state:
        return

    turns: List[Tuple[str, str]] = state["turns"]
    result = turns[-1][1]
    revisions = sum(1 for role, _ in turns if role == "model") - 1

    st.divider()
    header = "生成結果" if revisions == 0 else f"生成結果（修正 {revisions} 回目）"
    st.subheader(header)
    with st.container(border=True):
        st.markdown(result)
    st.caption(f"{len(result):,} 文字")

    if extra is not None:
        extra(result)

    with st.expander("📋 コピー用テキスト（右上のアイコンでコピー）"):
        st.code(result, language=None, wrap_lines=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    col1, col2, col3 = st.columns(3)
    col1.download_button(
        "⬇️ Markdown", result, file_name=f"{file_prefix}_{stamp}.md",
        mime="text/markdown", key=f"{tool_key}__dl_md", use_container_width=True,
    )
    col2.download_button(
        "⬇️ テキスト", result, file_name=f"{file_prefix}_{stamp}.txt",
        mime="text/plain", key=f"{tool_key}__dl_txt", use_container_width=True,
    )
    if col3.button("🗑️ クリア", key=f"{tool_key}__clear", use_container_width=True):
        del st.session_state[_state_key(tool_key)]
        st.rerun()

    # 追加指示で修正（会話履歴を引き継いで再生成）
    with st.form(f"{tool_key}__refine", clear_on_submit=True):
        instruction = st.text_input(
            "追加指示で修正",
            placeholder="例: もう少し短く / 結論を先に / もっとカジュアルに",
        )
        submitted = st.form_submit_button("✏️ 修正する")
    if submitted:
        if not instruction.strip():
            st.warning("追加指示を入力してください。")
            return
        new_turns = turns + [("user", instruction.strip())]
        with st.container(border=True):
            text = stream_to_screen(build_contents(new_turns), state["system"])
        if text is None:
            return
        state["turns"] = new_turns + [("model", text)]
        st.rerun()


def require(fields: Dict[str, str]) -> bool:
    """必須入力の空チェック（{表示名: 値}）。未入力があれば警告を出して False"""
    missing = [label for label, value in fields.items() if not (value or "").strip()]
    if missing:
        st.warning(f"次の項目を入力してください: {', '.join(missing)}")
        return False
    return True


def resolve_input_text(text: str, uploaded) -> Optional[str]:
    """入力欄とアップロードファイルから対象テキストを決める（ファイル優先）。読込失敗時はエラー表示して None"""
    if uploaded is None:
        return text
    try:
        return read_uploaded_text(uploaded)
    except ValueError as e:
        st.error(str(e))
        return None


def read_uploaded_text(uploaded) -> str:
    """アップロードされたテキストファイルを文字列で返す"""
    data = uploaded.getvalue()
    for encoding in ("utf-8", "utf-8-sig", "cp932"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"{uploaded.name} の文字コードを判別できませんでした（UTF-8 または Shift_JIS で保存してください）。")
