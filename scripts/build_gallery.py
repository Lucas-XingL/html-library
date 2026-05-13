"""Regenerate index.html from metadata.json.

Apple-style minimal gallery — soft gray bg, large title, tag pills, hover cards.
Search box + tag filter on the client side.
"""
import html
import json
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent
META = LIB / "metadata.json"
INDEX = LIB / "index.html"
ARTIFACTS = LIB / "artifacts"

SITE_TITLE = "Reading Library"
SITE_SUBTITLE = "Visualized articles, dashboards & artifacts"

HOME_BUTTON_MARK = "<!-- HL_HOME_BUTTON_v1 -->"
HOME_BUTTON_SNIPPET = """<!-- HL_HOME_BUTTON_v1 -->
<a href="../" class="hl-home-btn" aria-label="返回首页">
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <path d="M3 12l9-9 9 9"/><path d="M5 10v10h14V10"/>
  </svg>
  <span>Library</span>
</a>
<style>
  .hl-home-btn{position:fixed;top:16px;right:16px;z-index:99999;display:inline-flex;align-items:center;gap:6px;padding:8px 14px;border-radius:999px;background:rgba(255,255,255,.78);backdrop-filter:saturate(180%) blur(20px);-webkit-backdrop-filter:saturate(180%) blur(20px);color:#1d1d1f;text-decoration:none;font:500 13px/1 -apple-system,BlinkMacSystemFont,"PingFang SC","Helvetica Neue",sans-serif;box-shadow:0 1px 3px rgba(0,0,0,.06),0 6px 16px rgba(0,0,0,.08);border:1px solid rgba(0,0,0,.05);transition:transform .15s,box-shadow .15s,background .15s}
  .hl-home-btn:hover{transform:translateY(-1px);box-shadow:0 2px 6px rgba(0,0,0,.08),0 10px 22px rgba(0,0,0,.1);background:rgba(255,255,255,.92)}
  .hl-home-btn svg{width:14px;height:14px}
  @media (prefers-color-scheme:dark){.hl-home-btn{background:rgba(28,28,30,.78);color:#f5f5f7;border-color:rgba(255,255,255,.08)}.hl-home-btn:hover{background:rgba(44,44,46,.92)}}
  @media print{.hl-home-btn{display:none}}
</style>
"""


def inject_home_button(artifacts_dir: Path) -> int:
    """Add a floating 'back to library' button to every artifact HTML.

    Idempotent: skips files that already contain HOME_BUTTON_MARK.
    Returns the number of files newly injected.
    """
    if not artifacts_dir.exists():
        return 0
    injected = 0
    for path in sorted(artifacts_dir.glob("*.html")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if HOME_BUTTON_MARK in text:
            continue
        lower = text.lower()
        idx = lower.rfind("</body>")
        if idx >= 0:
            new_text = text[:idx] + HOME_BUTTON_SNIPPET + text[idx:]
        else:
            new_text = text + "\n" + HOME_BUTTON_SNIPPET
        path.write_text(new_text, encoding="utf-8")
        injected += 1
    return injected


def main():
    if not META.exists():
        items = []
    else:
        items = json.loads(META.read_text()).get("items", [])

    n = inject_home_button(ARTIFACTS)
    if n:
        print(f"injected home button into {n} artifact(s)")

    # tag counts
    tag_counts = {}
    for it in items:
        for t in it.get("tags", []):
            tag_counts[t] = tag_counts.get(t, 0) + 1
    sorted_tags = sorted(tag_counts.items(), key=lambda x: -x[1])

    # cards JSON for client-side filter
    cards_json = json.dumps([
        {
            "slug": it["slug"],
            "title": it["title"],
            "tags": it.get("tags", []),
            "added": it.get("added", ""),
            "size_kb": it.get("size_kb", 0),
        } for it in items
    ], ensure_ascii=False)

    tag_buttons = "\n".join(
        f'<button class="tag" data-tag="{html.escape(t)}">'
        f'{html.escape(t)} <span class="count">{c}</span></button>'
        for t, c in sorted_tags
    )

    out = TEMPLATE.format(
        title=SITE_TITLE,
        subtitle=SITE_SUBTITLE,
        count=len(items),
        tag_buttons=tag_buttons,
        cards_json=cards_json,
    )
    INDEX.write_text(out, encoding="utf-8")
    print(f"wrote {INDEX} ({INDEX.stat().st_size:,} bytes, {len(items)} items)")


TEMPLATE = r"""<!doctype html>
<html lang="zh-Hans">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{
    --bg: #f5f5f7;
    --surface: #ffffff;
    --surface-hover: #fbfbfd;
    --ink: #1d1d1f;
    --ink-soft: #6e6e73;
    --ink-dim: #86868b;
    --line: #d2d2d7;
    --line-soft: #e8e8ed;
    --accent: #0071e3;
    --tag-bg: #f5f5f7;
    --tag-bg-active: #1d1d1f;
    --tag-fg-active: #ffffff;
    --shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.04);
    --shadow-hover: 0 2px 6px rgba(0,0,0,0.06), 0 12px 24px rgba(0,0,0,0.06);
    --sans: -apple-system, BlinkMacSystemFont, "SF Pro Display", "PingFang SC", "Helvetica Neue", sans-serif;
    --mono: "SF Mono", "JetBrains Mono", Menlo, Consolas, monospace;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #000000;
      --surface: #1c1c1e;
      --surface-hover: #2c2c2e;
      --ink: #f5f5f7;
      --ink-soft: #a1a1a6;
      --ink-dim: #6e6e73;
      --line: #38383a;
      --line-soft: #2c2c2e;
      --accent: #2997ff;
      --tag-bg: #2c2c2e;
      --tag-bg-active: #f5f5f7;
      --tag-fg-active: #1d1d1f;
      --shadow: 0 1px 3px rgba(0,0,0,0.3), 0 4px 12px rgba(0,0,0,0.4);
      --shadow-hover: 0 2px 6px rgba(0,0,0,0.4), 0 12px 24px rgba(0,0,0,0.5);
    }}
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; }}
  body {{
    background: var(--bg);
    color: var(--ink);
    font-family: var(--sans);
    font-size: 16px;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
  }}
  .wrap {{
    max-width: 1080px;
    margin: 0 auto;
    padding: 64px 32px 96px;
  }}
  header {{
    margin-bottom: 48px;
  }}
  h1 {{
    font-size: 48px;
    font-weight: 700;
    letter-spacing: -0.022em;
    line-height: 1.08;
    margin: 0 0 12px;
  }}
  .subtitle {{
    font-size: 21px;
    color: var(--ink-soft);
    letter-spacing: 0.011em;
    margin: 0 0 8px;
    font-weight: 400;
  }}
  .meta {{
    font-size: 13px;
    color: var(--ink-dim);
    font-family: var(--mono);
    letter-spacing: 0.04em;
  }}

  .toolbar {{
    display: flex;
    gap: 12px;
    align-items: center;
    margin-bottom: 24px;
    flex-wrap: wrap;
  }}
  .search {{
    flex: 1;
    min-width: 240px;
    position: relative;
  }}
  .search input {{
    width: 100%;
    padding: 12px 16px 12px 40px;
    font-size: 15px;
    font-family: var(--sans);
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 10px;
    color: var(--ink);
    outline: none;
    transition: border-color .15s, box-shadow .15s;
  }}
  .search input:focus {{
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(0,113,227,0.12);
  }}
  .search svg {{
    position: absolute;
    left: 14px;
    top: 50%;
    transform: translateY(-50%);
    width: 16px;
    height: 16px;
    color: var(--ink-dim);
  }}

  .tags {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 32px;
  }}
  .tag {{
    border: none;
    background: var(--tag-bg);
    color: var(--ink);
    font-size: 13px;
    font-family: var(--sans);
    padding: 6px 14px;
    border-radius: 980px;
    cursor: pointer;
    transition: background .12s, color .12s, transform .08s;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }}
  .tag:hover {{ background: var(--line-soft); }}
  .tag.active {{
    background: var(--tag-bg-active);
    color: var(--tag-fg-active);
  }}
  .tag .count {{
    font-family: var(--mono);
    font-size: 11px;
    opacity: 0.6;
  }}
  .tag.active .count {{ opacity: 0.7; }}

  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
  }}
  .card {{
    background: var(--surface);
    border-radius: 16px;
    padding: 24px;
    box-shadow: var(--shadow);
    transition: transform .18s ease, box-shadow .18s ease, background .12s;
    text-decoration: none;
    color: inherit;
    display: flex;
    flex-direction: column;
    gap: 14px;
    min-height: 160px;
    position: relative;
  }}
  .card:hover {{
    transform: translateY(-2px);
    box-shadow: var(--shadow-hover);
    background: var(--surface-hover);
  }}
  .card-title {{
    font-size: 17px;
    font-weight: 600;
    line-height: 1.35;
    letter-spacing: -0.005em;
    color: var(--ink);
    margin: 0;
    /* clamp 3 lines */
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }}
  .card-tags {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: auto;
  }}
  .card-tags .pill {{
    font-size: 11px;
    padding: 3px 9px;
    background: var(--tag-bg);
    color: var(--ink-soft);
    border-radius: 980px;
    font-weight: 500;
  }}
  .card-meta {{
    font-family: var(--mono);
    font-size: 11px;
    color: var(--ink-dim);
    letter-spacing: 0.04em;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .share-btn {{
    background: none;
    border: none;
    color: var(--ink-dim);
    cursor: pointer;
    padding: 4px;
    border-radius: 6px;
    transition: color .12s, background .12s;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 11px;
    font-family: var(--mono);
  }}
  .share-btn:hover {{
    color: var(--accent);
    background: var(--tag-bg);
  }}
  .share-btn svg {{ width: 12px; height: 12px; }}
  .share-btn.copied {{ color: var(--accent); }}

  .empty {{
    grid-column: 1 / -1;
    text-align: center;
    padding: 64px 16px;
    color: var(--ink-dim);
    font-size: 15px;
  }}
  footer {{
    margin-top: 64px;
    padding-top: 24px;
    border-top: 1px solid var(--line-soft);
    text-align: center;
    font-size: 12px;
    color: var(--ink-dim);
    font-family: var(--mono);
    letter-spacing: 0.05em;
  }}
  footer a {{ color: var(--ink-soft); text-decoration: none; }}
  footer a:hover {{ color: var(--accent); }}

  @media (max-width: 600px) {{
    .wrap {{ padding: 32px 20px 64px; }}
    h1 {{ font-size: 34px; }}
    .subtitle {{ font-size: 17px; }}
    .grid {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>{title}</h1>
    <p class="subtitle">{subtitle}</p>
    <p class="meta"><span id="count">{count}</span> ARTIFACTS</p>
  </header>

  <div class="toolbar">
    <div class="search">
      <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="7" cy="7" r="5.5"/><path d="m11 11 3.5 3.5"/></svg>
      <input id="q" type="text" placeholder="搜索标题或标签..." autocomplete="off">
    </div>
  </div>

  <div class="tags" id="tags">
    <button class="tag active" data-tag="">全部 <span class="count" id="all-count">{count}</span></button>
    {tag_buttons}
  </div>

  <div class="grid" id="grid"></div>

  <footer>
    Updated automatically · <a href="https://github.com/Lucas-XingL/html-library" target="_blank">source on github</a>
  </footer>
</div>

<script>
const ITEMS = {cards_json};
const grid = document.getElementById('grid');
const q = document.getElementById('q');
const tags = document.getElementById('tags');
let activeTag = '';
let search = '';

function copyToClipboard(text) {{
  if (navigator.clipboard && navigator.clipboard.writeText) {{
    return navigator.clipboard.writeText(text);
  }}
  const ta = document.createElement('textarea');
  ta.value = text;
  ta.style.position = 'fixed';
  ta.style.opacity = '0';
  document.body.appendChild(ta);
  ta.select();
  try {{ document.execCommand('copy'); }} catch (e) {{}}
  ta.remove();
  return Promise.resolve();
}}

function render() {{
  const sq = search.toLowerCase().trim();
  const filtered = ITEMS.filter(it => {{
    if (activeTag && !it.tags.includes(activeTag)) return false;
    if (sq) {{
      const hay = (it.title + ' ' + it.tags.join(' ')).toLowerCase();
      if (!hay.includes(sq)) return false;
    }}
    return true;
  }});
  document.getElementById('count').textContent = filtered.length;
  if (!filtered.length) {{
    grid.innerHTML = '<div class="empty">No artifacts match.</div>';
    return;
  }}
  grid.innerHTML = filtered.map(it => `
    <a class="card" href="./artifacts/${{it.slug}}.html" target="_blank">
      <h2 class="card-title">${{escapeHtml(it.title)}}</h2>
      <div class="card-tags">
        ${{it.tags.map(t => `<span class="pill">${{escapeHtml(t)}}</span>`).join('')}}
      </div>
      <div class="card-meta">
        <span>${{it.added}} · ${{it.size_kb}}KB</span>
        <button class="share-btn" data-slug="${{it.slug}}" onclick="event.preventDefault(); event.stopPropagation(); shareCard(this)">
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M8 1v9M8 1 5 4M8 1l3 3M2.5 9v4a1.5 1.5 0 0 0 1.5 1.5h8a1.5 1.5 0 0 0 1.5-1.5V9"/></svg>
          <span>复制链接</span>
        </button>
      </div>
    </a>
  `).join('');
}}

function escapeHtml(s) {{
  return String(s).replace(/[&<>"']/g, c => ({{ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }})[c]);
}}

function shareCard(btn) {{
  const slug = btn.dataset.slug;
  const url = `${{location.origin}}/artifacts/${{slug}}.html`;
  copyToClipboard(url).then(() => {{
    btn.classList.add('copied');
    const span = btn.querySelector('span');
    const orig = span.textContent;
    span.textContent = '已复制 ✓';
    setTimeout(() => {{ span.textContent = orig; btn.classList.remove('copied'); }}, 1500);
  }});
}}
window.shareCard = shareCard;

q.addEventListener('input', e => {{ search = e.target.value; render(); }});
tags.addEventListener('click', e => {{
  const btn = e.target.closest('.tag');
  if (!btn) return;
  document.querySelectorAll('.tag').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  activeTag = btn.dataset.tag;
  render();
}});

render();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
