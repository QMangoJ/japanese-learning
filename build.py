#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the unified N3/N2 study app into public/index.html (adds furigana <ruby>).

Run locally:  pip install -r requirements.txt && python build.py
Output:       public/index.html  (a single self-contained page)
"""
import hashlib, json, os, re, shutil
import pykakasi

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src-data")
GSRC = os.path.join(SRC, "n3-grammar")
VSRC = os.path.join(SRC, "n3-vocab")
N2SRC = os.path.join(SRC, "n2-grammar")
KSRC = os.path.join(SRC, "n3-kanji")
V2SRC = os.path.join(SRC, "n2-vocab")
K2SRC = os.path.join(SRC, "n2-kanji")
N4SRC = os.path.join(SRC, "n4-grammar")
N4VSRC = os.path.join(SRC, "n4-vocab")
K4SRC = os.path.join(SRC, "n4-kanji")
COMSRC = os.path.join(SRC, "common")  # 跟级别无关的通用参考：接续表 / 活用表 / 数字表达
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

def ruby_ul(text, pattern):
    """Like ruby(), but wraps the first exact occurrence of `pattern` in <u>.
    Only underlines on an exact substring match (never guesses), mirroring the
    underline the source textbook prints under the grammar point inside each
    example sentence."""
    if pattern:
        i = text.find(pattern)
        if i >= 0:
            before, match, after = text[:i], text[i:i+len(pattern)], text[i+len(pattern):]
            return ruby(before) + "<u>" + ruby(match) + "</u>" + ruby(after)
    return ruby(text)

def annotate_g(day):
    day["title_r"] = ruby(day["title"])
    if day.get("dialog"):
        day["dialog"]["lines_r"] = rlist(day["dialog"].get("lines", []))
    for p in day.get("points") or []:
        p["pattern_r"] = ruby(p["pattern"])
        if p.get("usage_jp"):
            p["usage_jp_r"] = ruby(p["usage_jp"])
        for ex in p.get("examples", []):
            ex["jp_r"] = ruby_ul(ex["jp"], p.get("pattern"))
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

def ruby_word(jp, reading):
    """Wrap a compound word using its EXPLICIT reading (transcribed from the book),
    trimming shared okurigana prefix/suffix the same way ruby() does — never guessed
    via kakasi, since we already have the verified reading."""
    if not reading or not KANJI.search(jp):
        return esc(jp)
    o, h, suf, pre = jp, reading, "", ""
    while o and h and o[-1] == h[-1]:
        suf = o[-1] + suf; o, h = o[:-1], h[:-1]
    while o and h and o[0] == h[0]:
        pre += o[0]; o, h = o[1:], h[1:]
    if not o or not h or not KANJI.search(o):
        return esc(jp)
    return esc(pre) + f"<ruby>{esc(o)}<rt>{esc(h)}</rt></ruby>" + esc(suf)

def annotate_k(day):
    day["title_r"] = ruby(day["title"])
    for k in day.get("kanji") or []:
        for w in k.get("words", []):
            w["jp_r"] = ruby_word(w["jp"], w.get("reading"))
    exs = day.get("exercises")
    if exs:
        for sec in exs.get("sections", []):
            sec["instruction_r"] = ruby(sec["instruction"])
            for it in sec.get("items", []):
                it["q_r"] = ruby(it["q"])
                if it.get("opts"):
                    it["opts_r"] = rlist(it["opts"])
    for mk in ("mondai1", "mondai2", "mondai3"):
        m = day.get(mk)
        if not m:
            continue
        m["instruction_r"] = ruby(m["instruction"])
        for it in m["items"]:
            it["q_r"] = ruby_ul(it["q"], it.get("ul"))
            if it.get("opts"):
                it["opts_r"] = rlist(it["opts"])
    return day

def annotate_v(day):
    day["title_r"] = ruby(day["title"])
    if day.get("dialog"):
        day["dialog"]["lines_r"] = rlist(day["dialog"].get("lines", []))
    for s in day.get("sections") or []:
        if s.get("pattern"):
            s["pattern_r"] = ruby(s["pattern"])
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

def count_weeks(folder):
    """Auto-detect how many complete weeks (7 day files each) exist, starting from week 1."""
    n = 0
    while all(os.path.exists(os.path.join(folder, f"w{n+1}d{d}.json")) for d in range(1, 8)):
        n += 1
    return n

def load_days(folder, weeks, annotate):
    out = []
    for w in range(1, weeks + 1):
        days = []
        for d in range(1, 8):
            with open(os.path.join(folder, f"w{w}d{d}.json"), encoding="utf-8") as f:
                days.append(annotate(json.load(f)))
        out.append({"n": w, "days": days})
    return out

def complete_week_numbers(folder, max_week=20):
    """Weeks (not necessarily contiguous) where all 7 day files exist."""
    return [w for w in range(1, max_week + 1)
            if all(os.path.exists(os.path.join(folder, f"w{w}d{d}.json")) for d in range(1, 8))]

def load_days_sparse(folder, week_numbers, annotate):
    out = []
    for w in week_numbers:
        days = []
        for d in range(1, 8):
            with open(os.path.join(folder, f"w{w}d{d}.json"), encoding="utf-8") as f:
                days.append(annotate(json.load(f)))
        out.append({"n": w, "days": days})
    return out

GMETA = {
    1: ("がんばらなくちゃ！", "必须努力！", "I have to stick at it!"), 2: ("がんばってごらん！", "你努力试试吧！", None),
    3: ("もっとがんばってほしい！", "希望你能更加努力！", None), 4: ("がんばるしかない！", "只能努力！", None),
    5: ("もっとがんばればよかった！", "要是再努力些就好了", None), 6: ("もっとがんばることにした", "决心更加努力", None),
}

def main():
    gweeks = load_days(GSRC, 6, annotate_g)
    for w in gweeks:
        t, tc, te = GMETA[w["n"]]; w["title"], w["title_cn"], w["title_en"] = t, tc, te

    besatsu = {}
    for fn in ("besatsu_w1-w3.json", "besatsu_w4-w5.json", "besatsu_w6.json"):
        with open(os.path.join(GSRC, fn), encoding="utf-8") as f:
            besatsu.update(json.load(f))
    for wk in besatsu.values():
        for k in ("mondai1", "mondai2", "mondai3"):
            for a in wk.get(k) or []:
                if a.get("note"):
                    a["note_r"] = ruby(a["note"])
    with open(os.path.join(GSRC, "contrast.json"), encoding="utf-8") as f:
        contrast = json.load(f)
    for g in contrast.get("groups", []):
        for r in g.get("rows", []):
            r["form_r"] = ruby(r["form"])
            if r.get("eg"):
                r["eg_r"] = ruby(r["eg"])
        # 每个语法家族的辨析练习：题干和选项都注音，答对/答错后的解析不注音（解析是中文）
        qz = g.get("quiz")
        if qz:
            for it in qz.get("items", []):
                it["q_r"] = ruby(it["q"])
                if it.get("opts"):
                    it["opts_r"] = rlist(it["opts"])

    # 接续表 / 活用表 / 数字表达属于日语本身，跟 N3/N2/N4 无关，
    # 所以放在 common/ 下打成一个独立的包，不再挂在 N3 语法里。
    with open(os.path.join(COMSRC, "reference.json"), encoding="utf-8") as f:
        reference = json.load(f)
    with open(os.path.join(COMSRC, "katsuyou.json"), encoding="utf-8") as f:
        katsuyou = json.load(f)
    with open(os.path.join(COMSRC, "numbers.json"), encoding="utf-8") as f:
        numbers = json.load(f)
    # 只给量词的例词注音：表格本身就是「汉字→读法」的对照，注音会把答案提前剧透
    for sec in numbers.get("sections", []):
        for c in sec.get("counters", []):
            if c.get("eg"):
                c["eg_r"] = ruby(c["eg"])

    vweeks = load_days(VSRC, 6, annotate_v)
    n2weeks = load_days(N2SRC, 8, annotate_g)
    kweeks = load_days(KSRC, count_weeks(KSRC), annotate_k)  # N3汉字: auto-detects how many weeks are extracted so far
    for w in kweeks:
        d1 = w["days"][0]
        w["title"], w["title_cn"] = d1.get("theme", ""), d1.get("theme_cn", "")
    v2weeks = load_days_sparse(V2SRC, complete_week_numbers(V2SRC), annotate_v)  # N2词汇: 允许跳过缺失的周(第5/6周部分数据暂缺)
    k2weeks = load_days(K2SRC, count_weeks(K2SRC), annotate_k)  # N2汉字: auto-detects how many周已录入
    for w in k2weeks:
        d1 = w["days"][0]
        w["title"], w["title_cn"] = d1.get("theme", ""), d1.get("theme_cn", "")
    n4weeks = load_days(N4SRC, count_weeks(N4SRC), annotate_g)  # N4语法: auto-detects how many weeks are extracted so far
    n4vweeks = load_days_sparse(N4VSRC, complete_week_numbers(N4VSRC), annotate_v)  # N4词汇: 从第4周开始编号，非从1开始
    k4weeks = load_days(K4SRC, count_weeks(K4SRC), annotate_k)  # N4汉字: auto-detects how many weeks are extracted so far
    for w in k4weeks:
        d1 = w["days"][0]
        w["title"], w["title_cn"] = d1.get("theme", ""), d1.get("theme_cn", "")

    data = {
        "grammar": {"weeks": gweeks, "besatsu": besatsu, "contrast": contrast},
        "kanji": {"weeks": kweeks},
        "vocab": {"weeks": vweeks},
        "n2grammar": {"weeks": n2weeks},
        "n2vocab": {"weeks": v2weeks},
        "n2kanji": {"weeks": k2weeks},
        "n4grammar": {"weeks": n4weeks},
        "n4vocab": {"weeks": n4vweeks},
        "n4kanji": {"weeks": k4weeks},
        "common": {"reference": reference, "katsuyou": katsuyou, "numbers": numbers},
    }

    with open(TEMPLATE, encoding="utf-8") as f:
        tpl = f.read()
    if "__DATA__" in tpl:
        raise SystemExit("template.html still has the old inline __DATA__ placeholder; it should fetch per-module JSON from data/ instead")
    if "__DATA_FILES__" not in tpl:
        raise SystemExit("template.html is missing the __DATA_FILES__ placeholder")

    os.makedirs(OUT_DIR, exist_ok=True)
    data_dir = os.path.join(OUT_DIR, "data")
    if os.path.isdir(data_dir):
        shutil.rmtree(data_dir)  # drop stale hashed filenames from previous builds
    os.makedirs(data_dir)
    total_kb = 0
    files = {}
    for name, obj in data.items():
        blob = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()[:10]
        fname = f"{name}.{digest}.json"
        with open(os.path.join(data_dir, fname), "w", encoding="utf-8") as f:
            f.write(blob)
        files[name] = fname
        total_kb += len(blob.encode("utf-8")) // 1024

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(tpl.replace("__DATA_FILES__", json.dumps(files, separators=(",", ":")), 1))

    # data/*.json filenames are content-hashed -> safe to cache forever; index.html must
    # always be revalidated since it's what points at the current hashed filenames.
    with open(os.path.join(OUT_DIR, "_headers"), "w", encoding="utf-8") as f:
        f.write(
            "/data/*\n"
            "  Cache-Control: public, max-age=31536000, immutable\n\n"
            "/\n"
            "  Cache-Control: public, max-age=0, must-revalidate\n\n"
            "/index.html\n"
            "  Cache-Control: public, max-age=0, must-revalidate\n"
        )

    print(f"OK  index.html {os.path.getsize(OUT)//1024} KB + data/*.json {total_kb} KB -> {OUT_DIR}")

if __name__ == "__main__":
    main()
