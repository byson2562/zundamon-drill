"""data/{本}/{章}.json から、GitHub Pages で公開するクイズページ（docs/）を生成する。

使い方:
  python3 tools/build.py          # ページを生成
  python3 tools/build.py --ogp    # リンクカード用の画像（docs/assets/ogp/{本}.png）も作り直す（Google Chrome を使う）
"""
import glob, html, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
BASE_URL = "https://byson2562.github.io/zundamon-drill"
ZENN = "https://zenn.dev/bonobono/books"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# 本ごとの設定：タイトル、Zennのスラッグ、配色（本のカバーと同じ系統）
BOOKS = {
    "terraform-nyumon": dict(title="ずんだもんと学ぶTerraform：入門編", slug="zundamon-terraform-nyumon", accent="#2E7D4F", dark="#174D2C"),
    "terraform-jissen": dict(title="ずんだもんと学ぶTerraform：実践編", slug="zundamon-terraform-jissen", accent="#3B4C7A", dark="#1D283C"),
    "datadog-nyumon": dict(title="ずんだもんと学ぶDatadog：入門編", slug="zundamon-datadog-nyumon", accent="#7B22CC", dark="#5C21B7"),
    "datadog-jissen": dict(title="ずんだもんと学ぶDatadog：実践編", slug="zundamon-datadog-jissen", accent="#5A3D9E", dark="#2D1063"),
    "sre": dict(title="ずんだもんと学ぶSRE：入門編", slug="zundamon-sre", accent="#2563C7", dark="#14306E"),
    "sre-jissen": dict(title="ずんだもんと学ぶSRE：実践編", slug="zundamon-sre-jissen", accent="#A03358", dark="#4A1230"),
    "cs-zenpen": dict(title="ずんだもんと学ぶコンピュータサイエンス：前編", slug="zundamon-cs-zenpen", accent="#118F8D", dark="#0B595D"),
    "cs-kouhen": dict(title="ずんだもんと学ぶコンピュータサイエンス：後編", slug="zundamon-cs-kouhen", accent="#C2571F", dark="#803313"),
    "web-tech": dict(title="ずんだもんと学ぶWeb技術", slug="zundamon-web-tech", accent="#B8359B", dark="#5A1456"),
    "security-nyumon": dict(title="ずんだもんと学ぶセキュリティ：入門編", slug="zundamon-security-nyumon", accent="#3E5872", dark="#2B3A4D"),
    "security-jissen": dict(title="ずんだもんと学ぶセキュリティ：実践編", slug="zundamon-security-jissen", accent="#345B66", dark="#1E3A42"),
}

PAGE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{ogp}">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Yusei+Magic&family=Zen+Kaku+Gothic+New:wght@500;700&display=swap">
<link rel="stylesheet" href="../assets/quiz.css">
<style>:root{{--accent:{accent};--accent-dark:{dark}}}</style>
</head>
<body>
<header class="header"><div class="header-inner">
  <div class="header-text">
    <p class="book"><a href="../#{book_key}">{book_title}</a></p>
    <h1>理解度チェック：{chapter_title}</h1>
    <p class="lead">全{n}問。選択・○×・穴埋めは自動で採点されます。「説明してみよう」は解答例と見比べて自己採点してください。</p>
  </div>
  <img class="header-chara" src="../assets/chara/metan-smile.png" alt="四国めたん" width="118" height="133">
</div></header>
<div id="score-slot"></div>
<main id="quiz"></main>
<nav class="chapter-nav" aria-label="ほかの章のドリル">
  <div class="nav-prevnext">{prev_link}{next_link}</div>
  <section class="book-sheet">
    <h2 class="book-title">この本のドリル</h2>
    <ul class="book-list">{chapter_list}</ul>
  </section>
</nav>
<footer class="footer">
  <p><a href="{chapter_url}">本文（Zenn）に戻る</a>　／　<a href="../">ドリル一覧</a></p>
  <p>立ち絵：坂本アヒル（ずんだもん立ち絵素材・四国めたん立ち絵素材）</p>
</footer>
<script type="application/json" id="quiz-data">{data}</script>
<script src="../assets/quiz.js"></script>
</body>
</html>
"""

INDEX = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ずんだもんドリル</title>
<meta name="description" content="Zennの「ずんだもんと学ぶ」シリーズの理解度チェック（自動採点クイズ）">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Yusei+Magic&family=Zen+Kaku+Gothic+New:wght@500;700&display=swap">
<link rel="stylesheet" href="assets/quiz.css">
</head>
<body>
<header class="header"><div class="header-inner">
  <div class="header-text">
    <p class="book">「ずんだもんと学ぶ」シリーズ</p>
    <h1>ずんだもんドリル</h1>
    <p class="lead">各章の理解度チェック（自動採点クイズ）です。本文は <a href="https://zenn.dev/bonobono">Zenn</a> で無料公開しています。</p>
  </div>
  <img class="header-chara" src="assets/chara/zunda-joy.png" alt="ずんだもん" width="118" height="127">
</div></header>
<main>{books}</main>
<footer class="footer"><p>立ち絵：坂本アヒル（ずんだもん立ち絵素材・四国めたん立ち絵素材）</p></footer>
</body>
</html>
"""


def build():
    chapters = {}   # book -> [data, ...]（章順）
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "*", "*.json"))):
        d = json.load(open(path, encoding="utf-8"))
        d["chapter_url"] = f"{ZENN}/{BOOKS[d['book']]['slug']}/viewer/{d['chapter_slug']}"
        d["page"] = f"{d['chapter']:02d}.html"
        chapters.setdefault(d["book"], []).append(d)
    listing = {}
    for b, ds in chapters.items():
        ds.sort(key=lambda d: d["chapter"])
        book = BOOKS[b]
        for i, d in enumerate(ds):
            prev_d = ds[i - 1] if i > 0 else None
            next_d = ds[i + 1] if i + 1 < len(ds) else None
            if next_d:   # 結果画面の「次の章へ」に使う
                d["next"] = {"url": next_d["page"], "title": next_d["chapter_title"]}
            name = d["page"]
            url = f"{BASE_URL}/{b}/{name}"
            title = f"理解度チェック：{d['chapter_title']}｜{book['title']}"
            n = len(d["questions"])
            chapter_list = "".join(
                f'<li class="{"is-current" if c is d else ""}"><span class="ch">{c["chapter"]}</span>'
                + (f'<span class="current">{html.escape(c["chapter_title"])}<span class="n">いまここ</span></span>' if c is d
                   else f'<a href="{c["page"]}">{html.escape(c["chapter_title"])}<span class="n">全{len(c["questions"])}問</span></a>')
                + "</li>" for c in ds)
            page = PAGE.format(
                title=html.escape(title), desc=html.escape(f"{book['title']}「{d['chapter_title']}」の内容を確認する全{n}問のクイズ（自動採点）。"),
                url=url, ogp=f"{BASE_URL}/assets/ogp/{b}.png", accent=book["accent"], dark=book["dark"],
                book_key=b, book_title=html.escape(book["title"]), chapter_title=html.escape(d["chapter_title"]), n=n,
                chapter_url=d["chapter_url"],
                prev_link=(f'<a class="nav-link prev" href="{prev_d["page"]}"><span class="dir">← 前の章</span><span class="t">{html.escape(prev_d["chapter_title"])}</span></a>' if prev_d else '<span class="nav-link empty"></span>'),
                next_link=(f'<a class="nav-link next" href="{next_d["page"]}"><span class="dir">次の章 →</span><span class="t">{html.escape(next_d["chapter_title"])}</span></a>' if next_d else '<span class="nav-link empty"></span>'),
                chapter_list=chapter_list,
                data=json.dumps(d, ensure_ascii=False).replace("</", "<\\/"))
            os.makedirs(os.path.join(DOCS, b), exist_ok=True)
            open(os.path.join(DOCS, b, name), "w", encoding="utf-8").write(page)
            listing.setdefault(b, []).append((name, d["chapter_title"], n))
            print("wrote", b, name, f"({n}問)")
    order = [b for b in BOOKS if b in listing]   # 一覧はシリーズの刊行順（BOOKS の定義順）
    books = "".join(
        f'<section class="book-sheet" id="{b}" style="--accent:{BOOKS[b]["accent"]}"><h2 class="book-title">{html.escape(BOOKS[b]["title"])}</h2><ul class="book-list">'
        + "".join(f'<li><span class="ch">{int(name[:2])}</span><a href="{b}/{name}">{html.escape(t)}<span class="n">全{n}問</span></a></li>' for name, t, n in listing[b])
        + "</ul></section>" for b in order)
    open(os.path.join(DOCS, "index.html"), "w", encoding="utf-8").write(INDEX.format(books=books))
    open(os.path.join(DOCS, ".nojekyll"), "w").write("")
    return listing


OGP_HTML = """<!doctype html><html lang="ja"><meta charset="utf-8"><style>
body{{margin:0;width:1200px;height:630px;overflow:hidden;font-family:'Hiragino Sans',sans-serif;
  background:linear-gradient(120deg,{dark},{accent});color:#fff;position:relative}}
.t{{position:absolute;left:70px;top:96px;font-size:34px;font-weight:700;opacity:.9}}
.h{{position:absolute;left:66px;top:160px;font-size:104px;font-weight:900;line-height:1.12}}
.s{{position:absolute;left:72px;top:450px;font-size:28px;font-weight:700;background:rgba(255,255,255,.18);
  padding:10px 24px;border-radius:999px}}
img{{position:absolute;bottom:0}}
.z{{right:10px;height:450px}} .m{{right:370px;height:400px}}
</style>
<div class="t">{book}</div><div class="h">理解度<br>チェック</div><div class="s">自動採点クイズ</div>
<img class="m" src="file://{chara}/metan-smile.png"><img class="z" src="file://{chara}/zunda-joy.png">"""


def build_ogp(books):
    out = os.path.join(DOCS, "assets", "ogp")
    os.makedirs(out, exist_ok=True)
    chara = os.path.join(DOCS, "assets", "chara", "large")
    for b in books:
        cfg = BOOKS[b]
        src = os.path.join(out, f"_{b}.html")
        open(src, "w", encoding="utf-8").write(OGP_HTML.format(book=html.escape(cfg["title"]), accent=cfg["accent"], dark=cfg["dark"], chara=chara))
        subprocess.run([CHROME, "--headless", "--disable-gpu", "--allow-file-access-from-files", "--hide-scrollbars",
                        f"--screenshot={os.path.join(out, b + '.png')}", "--window-size=1200,630", f"file://{src}"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        os.remove(src)
        print("ogp", b)


if __name__ == "__main__":
    listing = build()
    if "--ogp" in sys.argv:
        build_ogp(listing)
