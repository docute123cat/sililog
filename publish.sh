#!/usr/bin/env bash
# ĐĂNG: chỉ lấy bài publish: true, rồi push. KHÔNG cần nhớ tên post.
set -e
cd "$(dirname "$0")"
python3 scripts/sync.py
read -p "👉 Đăng những bài trên? [y/N] " ok
[[ "$ok" =~ ^[Yy]$ ]] || { echo "Đã huỷ."; exit 0; }
git add -A
git commit -m "blog: sync $(date +%Y-%m-%d\ %H:%M)" || { echo "Không có gì thay đổi."; exit 0; }
git push
echo "✅ Đã push. Cloudflare build ~1 phút."
