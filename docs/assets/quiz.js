// ずんだもんドリル：章ごとの理解度チェック（自動採点）
// 問題データはページ内の <script type="application/json" id="quiz-data"> に埋め込まれている。
(function () {
  "use strict";

  const data = JSON.parse(document.getElementById("quiz-data").textContent);
  const root = document.getElementById("quiz");
  const CHARA = "../assets/chara/";
  const TYPE_LABEL = { truefalse: "○×", choice: "選択", fill: "穴埋め", essay: "説明" };

  const RETRY_KEY = `drill-retry:${data.book}/${data.chapter}`;
  let retryIdx = null;
  try {
    const raw = sessionStorage.getItem(RETRY_KEY);
    if (raw) { sessionStorage.removeItem(RETRY_KEY); retryIdx = JSON.parse(raw); }
  } catch (e) {}
  if (!Array.isArray(retryIdx) || !retryIdx.length || retryIdx.some((i) => !data.questions[i])) retryIdx = null;
  if (retryIdx) {
    // 出題しない問題は「回答済み・正解扱い」にして、再挑戦分だけ採点する
    data.questions = data.questions.map((q, i) => (retryIdx.includes(i) ? q : Object.assign({}, q, { skipped: true })));
  }
  const state = data.questions.map((q) => ({ done: !!q.skipped, correct: !!q.skipped && q.type !== "essay" }));
  const autoCount = data.questions.filter((q) => q.type !== "essay" && !q.skipped).length;

  function el(tag, attrs, ...children) {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (k === "class") e.className = v;
      else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
      else e.setAttribute(k, v);
    }
    for (const c of children.flat()) if (c != null) e.append(c);
    return e;
  }

  function normalize(s) {
    return s.normalize("NFKC").toLowerCase().replace(/[\s「」『』"'。、.,]/g, "");
  }

  function refLink(q) {
    return el("a", { href: data.chapter_url, target: "_blank", rel: "noopener", class: "ref" },
      `本文 ${q.ref} 節を読み返す →`);
  }

  function explain(card, q, ok) {
    const box = el("div", { class: "explain " + (ok === true ? "ok" : ok === false ? "ng" : "neutral") },
      el("img", { src: CHARA + (ok === false ? "metan.png" : "metan-smile.png"), alt: "四国めたん", class: "icon" }),
      el("div", { class: "explain-body" },
        el("p", { class: "verdict" }, ok === true ? "正解です！" : ok === false ? "おしい！" : "解答例と見比べてみましょう"),
        el("p", {}, q.explain || ""),
        refLink(q)));
    card.append(box);
  }

  function finish(i, ok) {
    state[i] = { done: true, correct: ok };
    updateScore();
  }

  function renderChoice(card, q, i, options, answerIndex) {
    const list = el("div", { class: "choices" + (options.length === 2 ? " tf" : "") });
    options.forEach((label, k) => {
      const b = el("button", { type: "button", class: "choice" }, label);
      b.addEventListener("click", () => {
        if (state[i].done) return;
        const ok = k === answerIndex;
        list.querySelectorAll("button").forEach((x, j) => {
          x.disabled = true;
          if (j === answerIndex) x.classList.add("is-answer");
        });
        b.classList.add(ok ? "is-correct" : "is-wrong");
        finish(i, ok);
        explain(card, q, ok);
      });
      list.append(b);
    });
    card.append(list);
  }

  function renderFill(card, q, i) {
    const input = el("input", { type: "text", class: "fill-input", placeholder: "ここに入力", "aria-label": "答え" });
    const btn = el("button", { type: "button", class: "primary" }, "答え合わせ");
    const check = () => {
      if (state[i].done || !input.value.trim()) return;
      const ok = q.accept.map(normalize).includes(normalize(input.value));
      input.disabled = btn.disabled = true;
      input.classList.add(ok ? "is-correct" : "is-wrong");
      if (!ok) card.append(el("p", { class: "answer-note" }, `正解：${q.accept[0]}`));
      finish(i, ok);
      explain(card, q, ok);
    };
    btn.addEventListener("click", check);
    input.addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.isComposing) check(); });
    card.append(el("div", { class: "fill" }, input, btn));
  }

  function renderEssay(card, q, i) {
    const area = el("textarea", { rows: "5", class: "essay-input", placeholder: "自分の言葉で書いてみよう（採点はされません）" });
    const btn = el("button", { type: "button", class: "primary" }, "解答例を見る");
    btn.addEventListener("click", () => {
      if (state[i].done) return;
      btn.disabled = true;
      const checks = el("div", { class: "points" },
        el("p", { class: "points-title" }, "書けていたポイントにチェックしよう（自己採点）"),
        q.points.map((p) => el("label", { class: "point" }, el("input", { type: "checkbox", onchange: updateScore }), p)));
      card.append(el("div", { class: "model" }, el("p", { class: "model-title" }, "解答例"), el("p", {}, q.model)), checks);
      state[i] = { done: true, correct: null };
      explain(card, Object.assign({}, q, { explain: "" }), null);
      updateScore();
    });
    card.append(area, btn);
  }

  const scoreBar = el("div", { class: "score", role: "status" });
  const result = el("section", { class: "result", hidden: "" });

  function updateScore() {
    const answered = state.filter((s, i) => s.done && data.questions[i].type !== "essay" && !data.questions[i].skipped).length;
    const correct = state.filter((s, i) => s.correct === true && !data.questions[i].skipped).length;
    const pts = root.querySelectorAll(".point input");
    const self = pts.length ? `・説明 ${root.querySelectorAll(".point input:checked").length}/${pts.length}` : "";
    const segs = el("div", { class: "segs" },
      data.questions.map((q, i) => {
        const s = state[i];
        const cls = q.skipped || !s.done ? "" : q.type === "essay" ? " essay" : s.correct ? " ok" : " ng";
        return el("span", { class: "seg" + cls, title: `Q${i + 1}` });
      }));
    scoreBar.replaceChildren(el("div", { class: "score-inner" },
      el("span", {}, "Q1"), segs, el("span", {}, `Q${data.questions.length}`),
      el("span", { class: "count" }, `正解 ${correct}/${autoCount}${self}`)));
    if (answered === autoCount) showResult(correct);
  }

  function showResult(correct) {
    const rate = correct / autoCount;
    const [img, msg] =
      rate === 1 ? ["zunda-joy.png", "全問正解なのだ！ この章はもう後輩に説明できるのだ！"] :
      rate >= 0.6 ? ["zunda-normal.png", "あと少しなのだ。間違えた問題の節だけ読み返すのだ。"] :
                    ["zunda-sad.png", "まだあやしいのだ……。本文をもう一度読んでから再挑戦するのだ。"];
    const missedIdx = data.questions.map((q, i) => i)
      .filter((i) => state[i].done && state[i].correct === false && data.questions[i].type !== "essay" && !data.questions[i].skipped);
    const missed = missedIdx.map((i) => data.questions[i].ref);
    const retryMissed = () => {
      try { sessionStorage.setItem(RETRY_KEY, JSON.stringify(missedIdx)); } catch (e) {}
      location.reload();
    };
    result.replaceChildren(
      el("img", { src: CHARA + img, alt: "ずんだもん", class: "result-chara" }),
      el("div", { class: "result-body" },
        el("p", { class: "result-score" }, `${correct} / ${autoCount} 問 正解`),
        el("p", { class: "result-msg" }, msg),
        missed.length ? el("p", { class: "result-missed" }, `読み返す節：${[...new Set(missed)].join("、")}`) : null,
        el("div", { class: "result-actions" },
          el("a", { href: data.chapter_url, target: "_blank", rel: "noopener", class: "button" }, "本文に戻る"),
          missed.length ? el("button", { type: "button", class: "button secondary", onclick: retryMissed }, "間違えた問題だけもう一度") : null,
          el("button", { type: "button", class: "button secondary", onclick: () => location.reload() }, "全部もう一度"),
          data.next ? el("a", { href: data.next.url, class: "button secondary" }, "次の章のドリルへ →") : null)));
    result.hidden = false;
  }

  if (retryIdx) {
    root.append(el("p", { class: "retry-note" }, `間違えた ${retryIdx.length} 問だけ出題しています。`,
      el("a", { href: location.pathname, onclick: (e) => { e.preventDefault(); location.reload(); } }, "全問に戻す")));
  }
  data.questions.forEach((q, i) => {
    if (q.skipped) return;
    const card = el("section", { class: "card" },
      el("div", { class: "card-head" },
        el("span", { class: "qno" }, `Q${i + 1}`),
        el("span", { class: "qtype" }, TYPE_LABEL[q.type])),
      el("p", { class: "question" }, q.q));
    if (q.type === "truefalse") renderChoice(card, q, i, ["○", "×"], q.answer ? 0 : 1);
    else if (q.type === "choice") renderChoice(card, q, i, q.choices, q.answer);
    else if (q.type === "fill") renderFill(card, q, i);
    else if (q.type === "essay") renderEssay(card, q, i);
    root.append(card);
  });
  root.append(result);
  document.getElementById("score-slot").append(scoreBar);
  updateScore();
})();
