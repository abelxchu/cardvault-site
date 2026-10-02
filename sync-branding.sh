#!/bin/bash
# 從 App 專案同步品牌資訊到本站網頁:
#   - App icon:讀取 App 專案的 AppIcon.png,縮成 256px 存成 icon.png(所有頁面共用)
#   - App 名稱:中文用「CFBundleDisplayName + 專案名」(例:名片夾 CardVault);
#               英文只用專案名(例:CardVault),與 App Store 英文名一致
#     改寫的地方:各頁 span.app-name(data-lang-zh / data-lang-en)、<title> 與 data-title-en 的「· 」後面
#   - 最後重新產生更新紀錄頁(它的頁首頁尾與品牌名取自 privacy/index.html)
#
# App 換 icon 或改名後,三步驟更新網站:
#   1. bash sync-branding.sh
#   2. git add -A && git commit -m "更新品牌資訊"
#   3. git push        ← Cloudflare Pages 約 1 分鐘內自動部署
set -euo pipefail
cd "$(dirname "$0")"

APP_DIR="$(cd .. && pwd)"   # 網站位於 CardVault/cardvault-site/,上一層就是 App 專案
ICON_SRC="$APP_DIR/CardVault/Assets.xcassets/AppIcon.appiconset/AppIcon.png"
DISPLAY_NAME=$(grep 'CFBundleDisplayName:' "$APP_DIR/project.yml" | sed 's/.*CFBundleDisplayName: *//' | tr -d '"')
PROJECT_NAME=$(grep '^name:' "$APP_DIR/project.yml" | sed 's/^name: *//' | tr -d '"')
export BRAND_ZH="${DISPLAY_NAME} ${PROJECT_NAME}"
export BRAND_EN="${PROJECT_NAME}"

sips -Z 256 "$ICON_SRC" --out icon.png >/dev/null
echo "已同步 icon.png"

while IFS= read -r PAGE; do
  python3 - "$PAGE" <<'PY'
import os, re, sys

page = sys.argv[1]
zh, en = os.environ["BRAND_ZH"], os.environ["BRAND_EN"]
s = open(page, encoding="utf-8").read()
if 'class="app-name"' not in s:   # 舊網址的轉址頁,不用處理
    sys.exit(0)

s = re.sub(r'(<span class="app-name" data-lang-zh>)[^<]*(</span>)', lambda m: m.group(1) + zh + m.group(2), s)
s = re.sub(r'(<span class="app-name" data-lang-en>)[^<]*(</span>)', lambda m: m.group(1) + en + m.group(2), s)
s = re.sub(r'(<title>[^<]*· )[^<]*(</title>)', lambda m: m.group(1) + zh + m.group(2), s)
s = re.sub(r'(data-title-en="[^"]*· )[^"]*(")', lambda m: m.group(1) + en + m.group(2), s)
# 首頁標題格式是「名稱 — 標語」
s = re.sub(r'(<title>)[^<—·]*( — [^<]*</title>)', lambda m: m.group(1) + zh + m.group(2), s)
s = re.sub(r'(data-title-en=")[^"—·]*( — [^"]*")', lambda m: m.group(1) + en + m.group(2), s)

open(page, "w", encoding="utf-8").write(s)
print(f"已同步 {page}:「{zh}」/「{en}」")
PY
done < <(find . -name "*.html" -not -path "./changelog/*")

python3 build-changelog.py
