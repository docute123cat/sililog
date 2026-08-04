#!/usr/bin/env bash
# Xem thử ở localhost — GỒM CẢ bài chưa publish (publish: false)
set -e
cd "$(dirname "$0")"
python3 scripts/sync.py --drafts
echo "🌐 http://localhost:1313  (Ctrl+C để dừng)"
hugo server -D --bind 0.0.0.0
