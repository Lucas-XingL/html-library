"""Add an HTML artifact to the library.

Usage:
    add <path-to-html> [--slug NAME] [--tags tag1,tag2] [--no-llm]

What it does:
1. Reads the HTML, extracts <title> and a short text preview.
2. Asks an LLM to suggest 2-3 tags (skippable with --no-llm).
3. You confirm or edit the title and tags interactively.
4. Copies file to artifacts/<slug>.html.
5. Updates metadata.json.
6. Regenerates index.html.
7. git add + commit + push (Vercel auto-deploys).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent
ARTIFACTS = LIB / "artifacts"
META = LIB / "metadata.json"

LLM_API = "https://codebase-api.byted.org/v2/api/2022-06-01/LLMProxy/Model/chat/completions"
LLM_MODEL = "qwen3.6-plus"


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_skip = 0
        self.title = ""
        self.in_title = False
        self.chunks = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "svg"):
            self.in_skip += 1
        if tag == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag in ("script", "style", "svg") and self.in_skip:
            self.in_skip -= 1
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        elif not self.in_skip:
            t = data.strip()
            if t:
                self.chunks.append(t)


def extract(path: Path):
    parser = TextExtractor()
    parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
    text = " ".join(parser.chunks)
    text = re.sub(r"\s+", " ", text)
    return parser.title.strip() or path.stem, text


def llm_suggest_tags(title: str, preview: str) -> list[str]:
    auth = os.environ.get("CODE_USER_JWT")
    if not auth:
        return []
    prompt = (
        "你是一个知识库标签助手。看下面的 HTML 文章标题和正文摘录, "
        "返回 2-3 个简洁的中文标签 (1-4 字), 用于个人阅读分类。\n\n"
        "标签风格示例:\n"
        "- 主题维度: AI / Agent / LLM / 设计 / 工程 / 数据 / 产品\n"
        "- 形式维度: 译文 / 指南 / 报告 / 总结 / dashboard / 工具\n"
        "- 来源维度: Perplexity / Anthropic / Karpathy\n"
        "选最贴切的 2-3 个,不要冗余,不要近义重复。\n\n"
        f"标题: {title}\n\n"
        f"正文摘录 (前 1500 字):\n{preview[:1500]}\n\n"
        "返回 JSON: {\"tags\": [\"...\", \"...\"]}"
    )
    body = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200,
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
    }
    try:
        req = urllib.request.Request(
            LLM_API,
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {auth}", "Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=30).read()
        content = json.loads(resp)["choices"][0]["message"]["content"]
        tags = json.loads(content).get("tags", [])
        return [t.strip() for t in tags if isinstance(t, str) and t.strip()][:3]
    except Exception as e:
        print(f"  [warn] LLM tag suggestion failed: {e}", file=sys.stderr)
        return []


def slugify(title: str, fallback: str) -> str:
    s = title.lower()
    s = re.sub(r"[^\w\u4e00-\u9fff\-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    s = s[:60] or fallback
    return s


def load_meta() -> dict:
    if META.exists():
        return json.loads(META.read_text())
    return {"items": []}


def save_meta(meta: dict):
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")


def confirm(prompt: str, default: str) -> str:
    val = input(f"{prompt} [{default}]: ").strip()
    return val or default


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="path to .html file")
    ap.add_argument("--slug", help="filename without .html (default: derived from title)")
    ap.add_argument("--tags", help="comma-separated tags, skips LLM")
    ap.add_argument("--no-llm", action="store_true", help="don't call LLM for tag suggestions")
    ap.add_argument("--no-push", action="store_true", help="skip git commit + push")
    args = ap.parse_args()

    src = Path(args.path).expanduser().resolve()
    if not src.exists() or src.suffix.lower() != ".html":
        sys.exit(f"not an html file: {src}")

    title, preview = extract(src)
    print(f"\n📄 source: {src}")
    print(f"   title:  {title[:80]}")
    print(f"   length: {len(preview):,} chars text")

    # tags
    if args.tags:
        suggested = [t.strip() for t in args.tags.split(",") if t.strip()]
    elif args.no_llm:
        suggested = []
    else:
        print("   suggesting tags...")
        suggested = llm_suggest_tags(title, preview)
        if suggested:
            print(f"   suggested: {', '.join(suggested)}")

    title = confirm("\n标题", title)
    slug = args.slug or slugify(title, src.stem)
    slug = confirm("文件名 (slug)", slug)
    tags_str = confirm("标签 (逗号分隔)", ", ".join(suggested))
    tags = [t.strip() for t in tags_str.split(",") if t.strip()]

    # write
    dst = ARTIFACTS / f"{slug}.html"
    if dst.exists():
        if input(f"\n{dst.name} 已存在, 覆盖? [y/N]: ").lower() != "y":
            sys.exit("aborted")
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    size_kb = dst.stat().st_size // 1024

    # update metadata
    meta = load_meta()
    meta["items"] = [it for it in meta.get("items", []) if it["slug"] != slug]
    meta["items"].append({
        "slug": slug,
        "title": title,
        "tags": tags,
        "added": datetime.now().strftime("%Y-%m-%d"),
        "size_kb": size_kb,
    })
    meta["items"].sort(key=lambda x: x["added"], reverse=True)
    save_meta(meta)

    # regenerate gallery
    subprocess.run([sys.executable, str(LIB / "scripts" / "build_gallery.py")], check=True)

    print(f"\n✅ added: artifacts/{slug}.html ({size_kb} KB)")
    print(f"   tags: {tags}")

    # git push
    if args.no_push:
        return
    os.chdir(LIB)
    subprocess.run(["git", "add", "-A"], check=True)
    msg = f"add: {title}"
    r = subprocess.run(["git", "commit", "-m", msg], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"   nothing to commit ({r.stdout.strip() or r.stderr.strip()})")
        return
    subprocess.run(["git", "push"], check=True)
    print(f"\n🚀 pushed. Vercel will auto-deploy in ~30s.")
    print(f"   share link will be: https://html-library-lucas.vercel.app/artifacts/{slug}.html")


if __name__ == "__main__":
    main()
