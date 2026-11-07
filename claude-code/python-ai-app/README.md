# AIライティングツール

Streamlit と Gemini API で作る、個人用のAIライティングツールです。
ブログ記事作成・メール返信・要約などのライティング機能を1つのアプリにまとめています。

## 機能

| カテゴリ | 機能 | 概要 |
|---|---|---|
| 作成 | 📝 ブログ記事作成 | テーマ・キーワード・読者・文字数・文体を指定して記事全文または構成案を生成 |
| 作成 | ✉️ メール返信作成 | 受信メールと伝えたい要点から返信文（件名付き）を生成 |
| 作成 | 📣 SNS投稿作成 | X / Instagram / LinkedIn / Threads / Facebook 向けの投稿文を複数案生成 |
| 作成 | 💡 タイトル・コピー案 | 記事タイトル・キャッチコピー・メール件名などを複数案とおすすめ付きで提案 |
| 編集・変換 | 📄 文章要約 | 箇条書き・3行・段落・要点＋結論・TL;DR の形式で要約 |
| 編集・変換 | 🔍 校正・リライト | 誤字修正・読みやすく・敬語化・カジュアル化・短縮・肉付け |
| 編集・変換 | 🌐 翻訳 | 8言語に対応。自然な訳・直訳寄り・ビジネス向け・カジュアルを選択可 |
| 相談 | 💬 文章相談チャット | ライティング全般をチャット形式で相談 |

### 共通機能

- 生成結果のストリーミング表示
- コピー用テキスト表示、Markdown / テキスト形式でのダウンロード
- 「もう少し短く」などの追加指示による再生成（会話履歴を引き継ぎ）
- 要約・校正・翻訳は `.txt` / `.md` ファイルのアップロードに対応
- サイドバーでモデル・創造性（temperature）を切り替え

## 必要環境

- Python 3.9 以上（3.11 以上を推奨）
- Gemini APIキー（[Google AI Studio](https://aistudio.google.com/apikey) で取得）

## セットアップ

```bash
# 仮想環境の作成と依存パッケージのインストール
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# APIキーの設定
cp .env.example .env
# .env を開き GEMINI_API_KEY に取得したキーを記入
```

### 環境変数

| 変数名 | 必須 | 説明 |
|---|---|---|
| `GEMINI_API_KEY` | ○ | Gemini APIキー。未設定の場合はサイドバーから入力可能 |
| `GEMINI_MODEL` | | 既定で使用するモデル名（デフォルト: `gemini-3.5-flash`） |

## 起動

```bash
streamlit run app.py
```

ブラウザで http://localhost:8501 が開きます。

## ディレクトリ構成

```
python-ai-app/
├── app.py                # エントリポイント（ページナビゲーション）
├── core/
│   ├── gemini_client.py  # Gemini API 呼び出し・エラー変換
│   └── ui_common.py      # 結果表示・ダウンロード・追加指示などの共通UI
├── tools/                # 各機能（プロンプトと画面）
│   ├── blog.py
│   ├── email_reply.py
│   ├── sns.py
│   ├── headline.py
│   ├── summarize.py
│   ├── proofread.py
│   ├── translate.py
│   └── chat.py
├── requirements.txt
├── .env.example
└── .gitignore
```

## 機能の追加方法

1. `tools/` に新しいファイルを作成し、`render()` 関数を定義する
2. 入力フォームからプロンプトを組み立て、`core.ui_common.generate()` で生成、`render_result()` で結果を表示する
3. `app.py` の `pages` に `st.Page(新モジュール.render, title=..., icon=..., url_path=...)` を追加する

## 注意事項

- 個人利用を想定しているため、認証・データベースはありません。生成結果はブラウザのセッション中のみ保持されます。
- 入力した文章は Gemini API に送信されます。機密情報の取り扱いに注意してください。
- `.env` はGit管理対象外です（`.gitignore` 済み）。
