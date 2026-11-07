### デザインのルール（オーナーが選んだミニマルデザイン）
- 色は白黒のみ（`--color-strong` #111 / `--color-muted` / `--color-border`）。角丸・影・グラデーションは使わない。強調は白黒の反転で表す（例：`.plan--featured`、`.btn--invert`）。
- フォント：本文は `--font-base` = BIZ UDPゴシック（日本語の読みやすさを重視して選んだ）。見出し・ボタン・メニューは `--font-heading` = Zen角ゴシック New で、`palt`（文字詰め）を効かせる。英字ラベルと数字は `--font-en` = Outfit。いずれも `<head>` で Google Fonts から読み込んでいる。`font: inherit` を使う要素（例：`.faq__q`）は、その後ろで `font-family` を指定し直す。

### フェードイン
- 要素に `reveal` クラスを付けると、画面に入ったときに下からふわっと表示される（`initReveal` の IntersectionObserver で制御）。
- 非表示の状態は `.js .reveal` にだけ適用している（`main.js` が `<html>` に `js` クラスを付ける）。そのため、JSが動かなくても内容は表示される。`prefers-reduced-motion`（視差効果を減らす設定）ではアニメーションを無効にする。
- 表示の遅れは自動で付く：同じ親要素の中にある `.reveal` 要素の順番 × 0.12秒。個別に変えたいときは `data-delay="0.5"`（秒）で上書きする。遅れの指定は `transitionend` で解除される。

### ファイルをまたぐ依存関係
- 料金プランのボタンには `data-plan="…"` が付いており、押すとフォームの `#plan` の `<select>` が自動で選ばれる。この値は `<option value>` と完全に一致させる必要がある。
- お問い合わせフォームは画面上で入力チェックと送信完了メッセージを出すだけで、**実際にはどこにも送信しない**（`initContactForm` の `TODO` を参照）。公開前に Formspree などの送信サービスとつなぐ予定。入力チェックのルールは input の `name` ごとに設定している。
- `--header-h` は固定ヘッダーの高さで、ページ内リンクで移動したときの `scroll-padding-top` にも使われている。