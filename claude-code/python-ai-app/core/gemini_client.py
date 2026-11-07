"""Gemini API 呼び出しのラッパー（Streamlitに依存しない）"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Iterator, List, Optional, Sequence, Tuple, Union

import httpx
from google import genai
from google.genai import errors, types

DEFAULT_MODEL = "gemini-3.5-flash"
AVAILABLE_MODELS = [
    "gemini-3.5-flash",
    "gemini-2.5-pro",
    "gemini-2.5-flash-lite",
]

# 文字列 or 会話履歴（Contentのリスト）
Contents = Union[str, List[types.Content]]


class GeminiError(Exception):
    """画面にそのまま表示できるメッセージを持つエラー"""


def get_api_key(override: Optional[str] = None) -> str:
    """APIキーを取得する（引数 > 環境変数 の優先順）"""
    key = (override or "").strip() or os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise GeminiError(
            "Gemini APIキーが設定されていません。"
            ".env に GEMINI_API_KEY を設定するか、サイドバーで入力してください。"
        )
    return key


@lru_cache(maxsize=4)
def _get_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def build_contents(turns: Sequence[Tuple[str, str]]) -> List[types.Content]:
    """(role, text) のリストを Gemini の Content 形式に変換する。role は 'user' / 'model'"""
    return [types.Content(role=role, parts=[types.Part(text=text)]) for role, text in turns]


def _translate_api_error(e: errors.APIError) -> GeminiError:
    """APIエラーを原因が分かる日本語メッセージに変換する"""
    code = e.code
    detail = e.message or str(e)
    if code == 400 and "api key" in detail.lower():
        summary = "APIキーが無効です。キーの値を確認してください。"
    elif code in (401, 403):
        summary = "APIキーの権限がないか、無効です。"
    elif code == 404:
        summary = "指定したモデルが見つかりません。モデル名を確認してください。"
    elif code == 429:
        summary = "レート制限またはクォータ上限に達しました。少し待ってから再実行してください。"
    elif code is not None and code >= 500:
        summary = "Gemini側でサーバーエラーが発生しました。時間をおいて再実行してください。"
    else:
        summary = "Gemini APIの呼び出しに失敗しました。"
    return GeminiError(f"{summary}（HTTP {code}）\n詳細: {detail}")


def _empty_response_reason(chunk: Optional[types.GenerateContentResponse]) -> str:
    """テキストが返らなかった理由を組み立てる"""
    base = "Geminiから本文が返されませんでした。"
    if chunk is None:
        return base + "レスポンスが空です。"
    feedback = chunk.prompt_feedback
    if feedback is not None and feedback.block_reason:
        return base + f"入力がブロックされました（理由: {feedback.block_reason}）。内容を変えて再実行してください。"
    if chunk.candidates:
        finish = chunk.candidates[0].finish_reason
        if finish:
            return base + f"終了理由: {finish}。"
    return base


def stream_generate(
    contents: Contents,
    *,
    system_instruction: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    api_key: Optional[str] = None,
) -> Iterator[str]:
    """テキストを逐次返すジェネレータ。失敗時は GeminiError を送出する"""
    client = _get_client(get_api_key(api_key))
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=temperature,
    )
    received = False
    last_chunk: Optional[types.GenerateContentResponse] = None
    try:
        for chunk in client.models.generate_content_stream(
            model=model, contents=contents, config=config
        ):
            last_chunk = chunk
            text = chunk.text
            if text:
                received = True
                yield text
    except errors.APIError as e:
        raise _translate_api_error(e) from e
    except httpx.TimeoutException as e:
        raise GeminiError("Gemini APIへの接続がタイムアウトしました。ネットワークを確認してください。") from e
    except httpx.HTTPError as e:
        raise GeminiError(f"Gemini APIへの通信に失敗しました: {e}") from e

    if not received:
        raise GeminiError(_empty_response_reason(last_chunk))
