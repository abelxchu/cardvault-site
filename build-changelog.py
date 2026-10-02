#!/usr/bin/env python3
"""
Generate cardvault-site/changelog/index.html from the app repo's user-facing changelog.

Source of truth: ../docs/changelog.md  (CardVault app repo; the site lives in CardVault/cardvault-site).
Run from anywhere:  python3 build-changelog.py
Override source:    python3 build-changelog.py /path/to/changelog.md

Source format (see that file's header):
    ## <version> · <YYYY-MM or YYYY-MM-DD>
    <summary zh> || <summary en>
    - <item zh> || <item en>

The page chrome (head, header, menu, footer) is copied from privacy/index.html,
so the changelog always matches the rest of the site.
"""

import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SRC = os.path.normpath(os.path.join(HERE, "..", "docs", "changelog.md"))
CHROME = os.path.join(HERE, "privacy", "index.html")
OUT = os.path.join(HERE, "changelog", "index.html")

MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July",
             "August", "September", "October", "November", "December"]


def split_bilingual(text):
    if "||" in text:
        zh, en = text.split("||", 1)
        return zh.strip(), en.strip()
    text = text.strip()
    return text, text


def bilingual_span(zh, en):
    ez, ee = html.escape(zh), html.escape(en)
    if zh == en:
        return ez
    return f'<span data-lang-zh>{ez}</span><span data-lang-en>{ee}</span>'


def format_date(d):
    m = re.fullmatch(r"(\d{4})-(\d{2})(?:-(\d{2}))?", d)
    if not m:
        return d, d
    y, mo, day = m.group(1), int(m.group(2)), m.group(3)
    if day:
        return f"{y} 年 {mo} 月 {int(day)} 日", f"{MONTHS_EN[mo - 1]} {int(day)}, {y}"
    return f"{y} 年 {mo} 月", f"{MONTHS_EN[mo - 1]} {y}"


def parse(md):
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    releases, cur = [], None
    for raw in md.splitlines():
        line = raw.strip()
        if raw.startswith("## "):
            head = raw[3:].strip()
            ver, date = (head.split("·", 1) + [""])[:2]
            cur = {"version": ver.strip(), "date": date.strip(), "summary": "", "items": []}
            releases.append(cur)
        elif cur is not None and line.startswith("- "):
            cur["items"].append(line[2:].strip())
        elif cur is not None and line and not cur["summary"] and not cur["items"]:
            cur["summary"] = line
    return releases


def slug(v):
    return "v-" + re.sub(r"[^0-9a-zA-Z]+", "-", v).strip("-")


def render(releases):
    sidebar, articles = [], []
    for r in releases:
        sid = slug(r["version"])
        ver = html.escape(r["version"])
        dz, de = format_date(r["date"]) if r["date"] else ("", "")
        date_span = bilingual_span(dz, de) if r["date"] else ""
        sidebar.append(f'    <a href="#{sid}"><b>{ver}</b>' + (f"<span>{date_span}</span>" if date_span else "") + "</a>")
        items = "\n".join(f"        <li>{bilingual_span(*split_bilingual(i))}</li>" for i in r["items"])
        summary = f'\n      <p class="rel-sum">{bilingual_span(*split_bilingual(r["summary"]))}</p>' if r["summary"] else ""
        date_html = f'<span class="rel-date">{date_span}</span>' if date_span else ""
        articles.append(
            f"""    <article class="rel" id="{sid}">
      <div class="rel-head"><h2>{ver}</h2>{date_html}</div>{summary}
      <ul class="rel-list">
{items}
      </ul>
    </article>"""
        )
    return "\n".join(sidebar), "\n".join(articles)


BODY = """<div class="wrap cl-head">
  <div class="eyebrow" data-lang-zh>更新紀錄</div><div class="eyebrow" data-lang-en>Changelog</div>
  <h1><span data-lang-zh>每個版本，做了什麼。</span><span data-lang-en>What changed, version by version.</span></h1>
  <p><span data-lang-zh>名片夾 CardVault 的更新內容。</span><span data-lang-en>Everything new in CardVault.</span></p>
</div>

<div class="wrap cl-body">
  <aside class="cl-side">
__SIDEBAR__
  </aside>
  <main class="cl-main">
__ARTICLES__
  </main>
</div>

"""


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC
    if not os.path.exists(src):
        sys.exit(f"changelog source not found: {src}")
    with open(src, encoding="utf-8") as f:
        releases = parse(f.read())
    if not releases:
        sys.exit(f"no releases parsed from {src}")
    sidebar, articles = render(releases)

    with open(CHROME, encoding="utf-8") as f:
        chrome = f.read()
    start = chrome.index('<div class="wrap doc-head">')
    end = chrome.index('<footer class="site">')
    page = chrome[:start] + BODY.replace("__SIDEBAR__", sidebar).replace("__ARTICLES__", articles) + chrome[end:]
    # 品牌名沿用 privacy 頁的 <title>（由 sync-branding.sh 維護）
    brand_zh = re.search(r"<title>[^<]*· ([^<]*)</title>", chrome).group(1)
    brand_en = re.search(r'data-title-en="[^"]*· ([^"]*)"', chrome).group(1)
    page = re.sub(r'data-title-en="[^"]*"', f'data-title-en="Changelog · {brand_en}"', page, count=1)
    page = re.sub(r"<title>[^<]*</title>", f"<title>更新紀錄 · {brand_zh}</title>", page, count=1)
    page = re.sub(r'<meta name="description" content="[^"]*">',
                  f'<meta name="description" content="{brand_zh} 每個版本的更新內容。">', page, count=1)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"wrote {OUT}  ({len(releases)} releases, source: {src})")


if __name__ == "__main__":
    main()
