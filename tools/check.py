"""問題データの検査。本文（Zenn の book 形式）と突き合わせて、書き間違いを見つける。

使い方: python3 tools/check.py <technical-books の books ディレクトリ>

検査すること:
- 必須項目の抜け、type ごとの形式（正解番号が選択肢の範囲内か など）
- ref に書いた節番号が、本文の見出し（## X.Y）に実在するか
- chapter_slug が本の config.yaml にあり、chapter_title が本文の title と一致するか
- 1章あたりの問題数と種類の配分（自動採点5〜6問＋説明1問）
"""
import glob, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import BOOKS

REQUIRED = {
    "truefalse": ["q", "answer", "explain", "ref"],
    "choice": ["q", "choices", "answer", "explain", "ref"],
    "fill": ["q", "accept", "explain", "ref"],
    "essay": ["q", "model", "points", "ref"],
}


def main(books_dir):
    errors, warnings = [], []
    for path in sorted(glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "*", "*.json"))):
        name = os.path.relpath(path)
        d = json.load(open(path, encoding="utf-8"))
        book = BOOKS[d["book"]]
        cfg = open(os.path.join(books_dir, book["slug"], "config.yaml"), encoding="utf-8").read()
        if f"- {d['chapter_slug']}" not in cfg:
            errors.append(f"{name}: chapter_slug {d['chapter_slug']} が config.yaml にない")
            continue
        md = open(os.path.join(books_dir, book["slug"], d["chapter_slug"] + ".md"), encoding="utf-8").read()
        title = re.search(r'^title: "(.+)"', md, re.M).group(1)
        if title != d["chapter_title"]:
            errors.append(f"{name}: chapter_title が本文と違う（本文: {title}）")
        sections = set(re.findall(r"^## (\d+\.\d+)", md, re.M))
        qs = d["questions"]
        for i, q in enumerate(qs, 1):
            t = q.get("type")
            if t not in REQUIRED:
                errors.append(f"{name} Q{i}: 不明な type {t}")
                continue
            for k in REQUIRED[t]:
                if k not in q or q[k] in ("", None, []):
                    errors.append(f"{name} Q{i}: {k} がない")
            if t == "choice" and not (isinstance(q.get("answer"), int) and 0 <= q["answer"] < len(q.get("choices", []))):
                errors.append(f"{name} Q{i}: answer が選択肢の範囲外")
            if t == "choice" and len(set(q.get("choices", []))) != len(q.get("choices", [])):
                errors.append(f"{name} Q{i}: 選択肢が重複している")
            if t == "truefalse" and not isinstance(q.get("answer"), bool):
                errors.append(f"{name} Q{i}: truefalse の answer は true/false")
            for ref in re.findall(r"\d+\.\d+", q.get("ref", "")):
                if ref not in sections:
                    errors.append(f"{name} Q{i}: ref {ref} が本文の見出しにない（あるのは {sorted(sections)}）")
            if not q.get("ref", "").startswith(f"{d['chapter']}."):
                errors.append(f"{name} Q{i}: ref {q.get('ref')} が {d['chapter']}章の節ではない")
        auto = sum(q["type"] != "essay" for q in qs)
        essay = sum(q["type"] == "essay" for q in qs)
        if not (5 <= auto <= 6 and essay == 1):
            warnings.append(f"{name}: 自動採点 {auto} 問・説明 {essay} 問（基本は 5〜6 問＋1問）")
        answers = [q["answer"] for q in qs if q["type"] == "choice"]
        if len(answers) >= 3 and len(set(answers)) == 1:
            warnings.append(f"{name}: 選択問題の正解の位置がすべて同じ（{answers[0]}）")
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"検査完了：エラー {len(errors)} 件・警告 {len(warnings)} 件")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
