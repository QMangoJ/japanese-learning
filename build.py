#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the unified N3/N2 study app into public/index.html (adds furigana <ruby>).

Run locally:  pip install -r requirements.txt && python build.py
Output:       public/index.html  (a single self-contained page)
"""
import json, os, re
import pykakasi

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src-data")
GSRC = os.path.join(SRC, "n3-grammar")
VSRC = os.path.join(SRC, "n3-vocab")
N2SRC = os.path.join(SRC, "n2-grammar")
TEMPLATE = os.path.join(HERE, "template.html")
OUT_DIR = os.path.join(HERE, "public")
OUT = os.path.join(OUT_DIR, "index.html")

kks = pykakasi.kakasi()

def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

KANJI = re.compile(r"[㐀-鿿豈-﫿々〆]")

def ruby(text):
    if not text or not KANJI.search(text):
        return esc(text or "")
    out = []
    for item in kks.convert(text):
        orig, hira = item["orig"], item["hira"]
        if not KANJI.search(orig) or not hira:
            out.append(esc(orig)); continue
        o, h, suf, pre = orig, hira, "", ""
        while o and h and o[-1] == h[-1]:
            suf = o[-1] + suf; o, h = o[:-1], h[:-1]
        while o and h and o[0] == h[0]:
            pre += o[0]; o, h = o[1:], h[1:]
        if not o or not h or not KANJI.search(o):
            out.append(esc(orig)); continue
        out.append(esc(pre) + f"<ruby>{esc(o)}<rt>{esc(h)}</rt></ruby>" + esc(suf))
    return "".join(out)

def rlist(xs):
    return [ruby(x) for x in xs]

def annotate_g(day):
    day["title_r"] = ruby(day["title"])
    if day.get("dialog"):
        day["dialog"]["lines_r"] = rlist(day["dialog"].get("lines", []))
    for p in day.get("points") or []:
        p["pattern_r"] = ruby(p["pattern"])
        if p.get("usage_jp"):
            p["usage_jp_r"] = ruby(p["usage_jp"])
        for ex in p.get("examples", []):
            ex["jp_r"] = ruby(ex["jp"])
            if ex.get("eq"):
                ex["eq_r"] = ruby(ex["eq"])
        for nt in p.get("notes", []):
            nt["text_r"] = ruby(nt["text"])
    exs = day.get("exercises")
    if exs:
        for sec in exs.get("sections", []):
            sec["instruction_r"] = ruby(sec["instruction"])
            for it in sec.get("items", []):
                it["q_r"] = ruby(it["q"])
                if it.get("options"):
                    it["options_r"] = rlist(it["options"])
    for k in ("mondai1", "mondai2", "mondai3"):
        m = day.get(k)
        if not m:
            continue
        m["instruction_r"] = ruby(m["instruction"])
        if m.get("passage"):
            m["passage_r"] = ruby(m["passage"])
        for it in m["items"]:
            if it.get("q"):
                it["q_r"] = ruby(it["q"])
            if it.get("opts"):
                it["opts_r"] = rlist(it["opts"])
    kg = day.get("keigo")
    if kg:
        kg["title_r"] = ruby(kg["title"])
        kg["content_r"] = rlist(kg.get("content", []))
        qz = kg.get("quiz")
        if qz:
            qz["instruction_r"] = ruby(qz["instruction"])
            qz["items_r"] = rlist(qz.get("items", []))
            if qz.get("answers"):
                qz["answers_r"] = ruby(qz["answers"])
    return day

def annotate_v(day):
    day["title_r"] = ruby(day["title"])
    if day.get("dialog"):
        day["dialog"]["lines_r"] = rlist(day["dialog"].get("lines", []))
    for s in day.get("sections") or []:
        for it in s.get("items", []):
            it["jp_r"] = ruby(it.get("jp", ""))
            if it.get("rel"):
                it["rel_r"] = ruby(it["rel"])
    exs = day.get("exercises")
    if exs:
        for sec in exs.get("sections", []):
            sec["instruction_r"] = ruby(sec["instruction"])
            for it in sec.get("items", []):
                it["q_r"] = ruby(it["q"])
                if it.get("opts"):
                    it["opts_r"] = rlist(it["opts"])
    for k in ("mondai1", "mondai2", "mondai3", "mondai4"):
        m = day.get(k)
        if not m:
            continue
        m["instruction_r"] = ruby(m["instruction"])
        for it in m["items"]:
            if it.get("q"):
                it["q_r"] = ruby(it["q"])
            if it.get("opts"):
                it["opts_r"] = rlist(it["opts"])
    return day

def load_days(folder, weeks, annotate):
    out = []
    for w in range(1, weeks + 1):
        days = []
        for d in range(1, 8):
            with open(os.path.join(folder, f"w{w}d{d}.json"), encoding="utf-8") as f:
                days.append(annotate(json.load(f)))
        out.append({"n": w, "days": days})
    return out

GMETA = {
    1: ("がんばらなくちゃ！", "必须努力！"), 2: ("がんばってごらん！", "你努力试试吧！"),
    3: ("もっとがんばってほしい！", "希望你能更加努力！"), 4: ("がんばるしかない！", "只能努力！"),
    5: ("もっとがんばればよかった！", "要是再努力些就好了"), 6: ("もっとがんばることにした", "决心更加努力"),
}

def main():
    gweeks = load_days(GSRC, 6, annotate_g)
    for w in gweeks:
        t, tc = GMETA[w["n"]]; w["title"], w["title_cn"] = t, tc

    besatsu = {}
    for fn in ("besatsu_w1-w3.json", "besatsu_w4-w5.json", "besatsu_w6.json"):
        with open(os.path.join(GSRC, fn), encoding="utf-8") as f:
            besatsu.update(json.load(f))
    for wk in besatsu.values():
        for k in ("mondai1", "mondai2", "mondai3"):
            for a in wk.get(k) or []:
                if a.get("note"):
                    a["note_r"] = ruby(a["note"])
    with open(os.path.join(GSRC, "reference.json"), encoding="utf-8") as f:
        reference = json.load(f)

    with open(os.path.join(GSRC, "contrast.json"), encoding="utf-8") as f:
        contrast = json.load(f)
    for g in contrast.get("groups", []):
        for r in g.get("rows", []):
            r["form_r"] = ruby(r["form"])
            if r.get("eg"):
                r["eg_r"] = ruby(r["eg"])

    vweeks = load_days(VSRC, 6, annotate_v)
    n2weeks = load_days(N2SRC, 8, annotate_g)

    data = {
        "grammar": {"weeks": gweeks, "besatsu": besatsu, "reference": reference, "contrast": contrast},
        "vocab": {"weeks": vweeks},
        "n2grammar": {"weeks": n2weeks},
    }
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    with open(TEMPLATE, encoding="utf-8") as f:
        tpl = f.read()
    if "__DATA__" not in tpl:
        raise SystemExit("template.html is missing the __DATA__ placeholder")

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(tpl.replace("__DATA__", blob, 1))
    print(f"OK  {os.path.getsize(OUT)//1024} KB -> {OUT}")

if __name__ == "__main__":
    main()
