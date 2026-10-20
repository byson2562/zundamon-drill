# ずんだもんドリル

Zenn で無料公開している「ずんだもんと学ぶ」シリーズの、章ごとの理解度チェック（自動採点クイズ）です。

- 公開ページ：https://byson2562.github.io/zundamon-drill/
- 本文：https://zenn.dev/bonobono

## しくみ

- 問題は `data/{本}/{章番号2桁}.json` に書く
- `python3 tools/check.py <technical-books の books ディレクトリ>` で、本文と突き合わせて問題データを検査する（節番号が実在するか、章タイトルが一致するか、正解番号の範囲など）
- `python3 tools/build.py` で `docs/` にクイズページを生成し、GitHub Pages（main ブランチの `/docs`）で公開する
- 本を新しく追加したときは `python3 tools/build.py --ogp` でリンクカード用の画像も作る（Google Chrome を使う）
- Zenn の章末には `@[card](https://byson2562.github.io/zundamon-drill/{本}/{章}.html)` でリンクカードを貼る

## 問題データの書き方

| type | 内容 | 必須の項目 |
|---|---|---|
| `truefalse` | ○×問題 | `q`, `answer`（true / false）, `explain`, `ref` |
| `choice` | 選択問題 | `q`, `choices`, `answer`（正解の番号・0始まり）, `explain`, `ref` |
| `fill` | 穴埋め | `q`, `accept`（正解として認める答えの一覧。全角半角・大文字小文字は区別しない）, `explain`, `ref` |
| `essay` | 説明してみよう（自己採点） | `q`, `model`（解答例）, `points`（自己採点のチェック項目）, `ref` |

`ref` は本文の節番号（例：`4.3`）。解説の下に、本文の該当章へのリンクとして表示される。

1章あたり、自動採点の問題（○×・選択・穴埋め）を5〜6問、説明問題を1問にするのを基本とする。

## クレジット

- 立ち絵：坂本アヒル（ずんだもん立ち絵素材・四国めたん立ち絵素材）
