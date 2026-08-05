#!/usr/bin/env bash
# recover.sh — Cứu bài blog đã xoá nhầm khỏi vault.
#
# Dùng:
#   ~/blog/recover.sh              → liệt kê mọi bài từng bị xoá
#   ~/blog/recover.sh <tên-bài>    → cứu bài đó về "50 - Blog/"
set -e
VAULT="/home/shark/STrong"
DIR="50 - Blog"
cd "$VAULT"

if [ -z "$1" ]; then
  echo "📋 Các bài TỪNG TỒN TẠI nhưng giờ không còn trong '$DIR':"
  echo ""
  # mọi file .md từng xuất hiện trong lịch sử
  git log --all --diff-filter=D --name-only --format="%H|%ad|%s" --date=short -- "$DIR/*.md" \
  | awk -v d="$DIR" '
      /\|/ { split($0,a,"|"); commit=a[1]; date=a[2]; next }
      /\.md$/ {
        if (!seen[$0]++) printf "  • %-45s (xoá %s, commit %s)\n", substr($0, length(d)+2), date, substr(commit,1,7)
      }'
  echo ""
  echo "👉 Cứu:  ~/blog/recover.sh <tên-file.md>"
  exit 0
fi

FILE="$1"
[[ "$FILE" == *.md ]] || FILE="$FILE.md"
TARGET="$DIR/$FILE"

# commit CUỐI CÙNG mà file còn tồn tại
LAST=$(git log --all --format=%H -- "$TARGET" | head -1)
if [ -z "$LAST" ]; then
  echo "❌ Không thấy '$FILE' trong lịch sử git."
  echo "   Thử: ~/blog/recover.sh   (để xem danh sách)"
  exit 1
fi

# nếu commit đó là commit xoá, lùi thêm 1 bước
if ! git cat-file -e "$LAST:$TARGET" 2>/dev/null; then
  LAST=$(git log --all --format=%H -- "$TARGET" | sed -n 2p)
fi

if [ -f "$TARGET" ]; then
  echo "⚠️  '$TARGET' đang tồn tại. Sao lưu thành .bak trước."
  cp "$TARGET" "$TARGET.bak"
fi

git checkout "$LAST" -- "$TARGET"
echo "✅ Đã cứu: $TARGET"
echo "   (từ commit $(git log -1 --format='%h %ad %s' --date=short "$LAST"))"
echo ""
head -8 "$TARGET"
