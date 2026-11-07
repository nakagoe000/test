## 概要

HP制作事業「Lumo Web」（屋号は仮）の1ページ構成の自社サイト。HTML / CSS / JS のみで作っており、フレームワーク・ビルド手順・パッケージ管理・テストはない。サイトの文章はすべて日本語で、サイトのオーナーとのやり取りも日本語で行う。

注意：git のルートは2階層上の `/Users/yya/projects/test`。このサイトは `claudeCode/webSite/` にある。

## コマンド

- プレビュー：`open index.html`、または `python3 -m http.server 8000` を実行して http://localhost:8000 を開く
- JSの文法チェック：`node --check js/main.js`

## 構成

- `index.html` にすべての内容、`css/style.css` にすべてのスタイル、`js/main.js` にすべての動きを書いている。JSは機能ごとに `init*` 関数を1つ作り、`DOMContentLoaded` でまとめて呼び出す。

### レイアウト（12列グリッド）
すべてのセクションが同じ構造になっている。セクションを追加するときもこの形に合わせる。

```html
<section class="section" id="...">
  <div class="container grid">
    <header class="section__head reveal">
      <p class="section__label">NN — English</p>
      <h2 class="section__title">日本語見出し</h2>
    </header>
    <div class="section__body"> ... </div>
  </div>
</section>
```

- `.grid` は12列。`.section__head` は1〜4列目（スクロールしても残る sticky）、`.section__body` は5〜12列目を使う。画面幅が1024px未満では、どちらも全幅になる。
- `.cells.cells--2` / `.cells--3` と `.cell` は、線で区切ったマス目。`.cells` に上と左の線、各 `.cell` に右と下の線を引いているので、列数が変わっても線が二重にならない。
- `.section__label` の番号（「01 — Features」…）は上から連番。セクションを追加・並べ替えしたら番号を振り直す。