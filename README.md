# 日语学习助手 · N3/N2 语法 + 词汇

一个自包含的静态网页学习工具，覆盖《考前对策》三个模块：

- **N3 语法**（6 周 × 7 天，含别册逐题答案 + 接续表参考页）
- **N2 语法**（8 周 × 7 天，含实战问题答案）
- **N3 词汇**（6 周 × 7 天）

功能：按级别（N3/N2）二次分类、跨模块搜索、假名注音（furigana）、日语朗读（TTS）、收藏生词本、记忆卡（闪卡）、每题答案折叠、深色模式、手机/电脑自适应。上次所选模块与收藏均保存在浏览器本地。

## 目录结构

```
build.py            # 构建脚本：合并 src-data + 注音，注入 template.html → public/index.html
template.html       # 页面模板（含 __DATA__ 占位符、全部样式与逻辑）
src-data/
  n3-grammar/       # w1d1.json … w6d7.json + besatsu_*.json + reference.json
  n3-vocab/         # w1d1.json … w6d7.json
  n2-grammar/       # w1d1.json … w8d7.json
requirements.txt    # pykakasi
public/index.html   # 构建产物（已在 .gitignore 中，由构建生成）
```

## 本地构建

```bash
pip install -r requirements.txt
python build.py
# 打开 public/index.html 即可
```

## 部署到 Cloudflare Pages

1. 把本仓库推到 GitHub（或直接连 Cloudflare 的 Git）。
2. Cloudflare 控制台 → **Workers & Pages → Create → Pages → 连接 Git 仓库**。
3. 构建设置：
   - **Build command**: `pip install -r requirements.txt && python build.py`
   - **Build output directory**: `public`
   - **Environment variables**: 加一个 `PYTHON_VERSION` = `3.12`
4. 保存并部署。之后**每次修改 `src-data/` 里的 JSON 并 push，Cloudflare 会自动重新构建并发布**。

> 数据改动只需编辑 `src-data/**/*.json`，无需改模板；注音在构建时自动生成。

## 更新内容

- 改语法/词汇内容 → 编辑对应 `src-data/<模块>/wXdY.json`
- 改页面样式或交互 → 编辑 `template.html`
- 本地验证：`python build.py` 后打开 `public/index.html`
