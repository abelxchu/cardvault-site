#!/bin/bash
# 從 App 專案同步品牌資訊到本站網頁:
#   - App icon:讀取 ../business-card-app 的 AppIcon.png,縮成 120px 內嵌
#   - App 名稱:讀取 project.yml 的 CFBundleDisplayName + 專案名(例:「名片夾 CardVault」)
#
# App 換 icon 或改名後,三步驟更新網站:
#   1. bash sync-branding.sh
#   2. git add -A && git commit -m "更新品牌資訊"
#   3. git push        ← 約 30~60 秒後網站自動更新
set -euo pipefail
cd "$(dirname "$0")"

APP_DIR="../business-card-app"
ICON_SRC="$APP_DIR/CardVault/Assets.xcassets/AppIcon.appiconset/AppIcon.png"
DISPLAY_NAME=$(grep 'CFBundleDisplayName:' "$APP_DIR/project.yml" | sed 's/.*CFBundleDisplayName: *//' | tr -d '"')
PROJECT_NAME=$(grep '^name:' "$APP_DIR/project.yml" | sed 's/^name: *//' | tr -d '"')
BRAND="${DISPLAY_NAME} ${PROJECT_NAME}"

TMP_ICON=$(mktemp -t appicon).png
sips -Z 120 "$ICON_SRC" --out "$TMP_ICON" >/dev/null
ICON_B64=$(base64 -i "$TMP_ICON")
rm -f "$TMP_ICON"

export BRAND ICON_B64
while IFS= read -r PAGE; do
  python3 - "$PAGE" <<'PY'
import os, re, sys

page = sys.argv[1]
brand = os.environ["BRAND"]
icon = os.environ["ICON_B64"]

s = open(page, encoding="utf-8").read()

# 1) App icon(img#app-icon 的 src)
s = re.sub(
    r'(<img id="app-icon"[^>]*src=")[^"]*(")',
    lambda m: m.group(1) + "data:image/png;base64," + icon + m.group(2),
    s,
)
# 2) App 名稱(所有 span.app-name)
s = re.sub(
    r'(<span class="app-name">)[^<]*(</span>)',
    lambda m: m.group(1) + brand + m.group(2),
    s,
)
# 3) <title> 破折號後的 App 名稱
s = re.sub(
    r'(<title>[^<—]*— )[^<]*(</title>)',
    lambda m: m.group(1) + brand + m.group(2),
    s,
)

open(page, "w", encoding="utf-8").write(s)
print(f"已同步 {page}:名稱「{brand}」+ App icon")
PY
done < <(find . -name "*.html")
