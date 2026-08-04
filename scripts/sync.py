#!/usr/bin/env python3
"""
sync.py — Obsidian ("50 - Blog") -> Hugo (content/posts/<parent>/<child>/)

Việc nó làm:
  1. Đọc mọi .md trong vault blog folder.
  2. publish: true  -> đăng (ghi draft: false)
     publish: false -> KHÔNG đăng (bỏ qua hẳn, trừ khi chạy --drafts để xem thử)
  3. Dựng cây chuyên mục cha/con từ 2 field `parent` / `child` (Hugo nested sections).
  4. Tự tạo _index.md cho mọi section (để chuyên mục có trang riêng).
  5. Copy ảnh từ "50 - Blog/images" -> static/images.
  6. Xoá content/posts trước mỗi lần sync => bài đã unpublish sẽ biến mất khỏi site.

Dùng:
  python3 scripts/sync.py            # chỉ bài publish: true
  python3 scripts/sync.py --drafts   # gồm cả bài chưa publish (để xem thử local)
"""

import re
import shutil
import sys
from pathlib import Path

VAULT_BLOG = Path("/home/shark/STrong/50 - Blog")
HUGO_ROOT = Path("/home/shark/blog")
CONTENT = HUGO_ROOT / "content" / "posts"
STATIC_IMG = HUGO_ROOT / "static" / "images"

# Tên hiển thị đẹp cho từng section (dùng trong _index.md)
NICE = {
    "embedded": "Embedded",
    "linux-bsp": "Linux / BSP",
    "edge-ai": "Edge AI",
    "career": "Career",
    "tools": "Tools",
    "bare-metal": "Bare-metal",
    "rtos": "RTOS",
    "protocols": "Protocols",
    "debugging": "Debugging",
    "kernel": "Kernel",
    "drivers": "Drivers",
    "yocto": "Yocto",
    "device-tree": "Device Tree",
    "boot": "Boot",
    "quantization": "Quantization",
    "runtimes": "Runtimes",
    "slam": "SLAM",
    "learning-log": "Learning Log",
    "job-hunt": "Job Hunt",
    "german": "German",
    "git-ci": "Git & CI",
    "editor": "Editor",
    "hardware-tools": "Hardware Tools",
}

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)


def parse_front_matter(text):
    """Tách front matter (dạng YAML đơn giản) và body."""
    m = FM_RE.match(text)
    if not m:
        return None, text
    raw, body = m.group(1), m.group(2)
    fm, order = {}, []
    for line in raw.split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        fm[k] = v
        order.append(k)
    return (fm, order), body


def unquote(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def is_true(v):
    return unquote(str(v)).lower() in ("true", "yes", "1")


def ensure_index(folder: Path, name: str):
    """Tạo _index.md cho một section nếu chưa có (để chuyên mục có trang riêng)."""
    idx = folder / "_index.md"
    if idx.exists():
        return
    title = NICE.get(name, name.replace("-", " ").title())
    idx.write_text(f'---\ntitle: "{title}"\n---\n', encoding="utf-8")


def main():
    include_drafts = "--drafts" in sys.argv

    if not VAULT_BLOG.exists():
        print(f"LỖI: không thấy {VAULT_BLOG}")
        return 1

    # AN TOÀN: cảnh báo nếu content/posts có file .md KHÔNG bắt nguồn từ vault.
    # (content/posts là thư mục SINH RA — nguồn thật luôn là vault. Nhưng nếu bạn
    #  từng tạo bài trực tiếp ở đây, ta phải cứu nó chứ không xoá thầm.)
    if CONTENT.exists():
        vault_names = {p.name for p in VAULT_BLOG.rglob("*.md")}
        orphans = [
            p for p in CONTENT.rglob("*.md")
            if p.name != "_index.md" and p.name not in vault_names
        ]
        if orphans:
            rescue = VAULT_BLOG / "_rescued"
            rescue.mkdir(parents=True, exist_ok=True)
            print("⚠️  Tìm thấy bài KHÔNG có trong vault -> đã cứu sang '50 - Blog/_rescued/':")
            for p in orphans:
                shutil.copy2(p, rescue / p.name)
                print(f"   • {p.relative_to(CONTENT)}")
            print("   (Sửa lại front matter cho đúng template rồi chuyển ra ngoài _rescued/)\n")
        shutil.rmtree(CONTENT)
    CONTENT.mkdir(parents=True, exist_ok=True)
    ensure_index(CONTENT, "posts")
    (CONTENT / "_index.md").write_text(
        '---\ntitle: "Posts"\n---\n', encoding="utf-8"
    )

    published, skipped = [], []

    for md in sorted(VAULT_BLOG.rglob("*.md")):
        if md.name.startswith("_") or "/images/" in md.as_posix():
            continue
        # bỏ qua thư mục cứu hộ (bài cần sửa tay trước khi dùng)
        if "_rescued" in md.parts:
            continue

        text = md.read_text(encoding="utf-8")
        parsed, body = parse_front_matter(text)
        if not parsed:
            skipped.append((md.name, "không có front matter"))
            continue
        fm, order = parsed

        pub = is_true(fm.get("publish", "false"))
        if not pub and not include_drafts:
            skipped.append((md.name, "publish: false"))
            continue

        parent = unquote(fm.get("parent", "")) or "uncategorized"
        child = unquote(fm.get("child", ""))

        # Cây thư mục = chuyên mục cha/con (Hugo nested sections)
        dest_dir = CONTENT / parent
        dest_dir.mkdir(parents=True, exist_ok=True)
        ensure_index(dest_dir, parent)
        if child:
            dest_dir = dest_dir / child
            dest_dir.mkdir(parents=True, exist_ok=True)
            ensure_index(dest_dir, child)

        # Dựng lại front matter cho Hugo: publish -> draft (ĐẢO NGƯỢC)
        out = ["---"]
        for k in order:
            if k in ("publish", "parent", "child"):
                continue
            out.append(f"{k}: {fm[k]}")

        # draft = ngược lại của publish
        out.append(f"draft: {'false' if pub else 'true'}")

        # Vẫn giữ categories phẳng để có trang /categories/ (Hugo taxonomy)
        cats = [parent] + ([child] if child else [])
        cats_yaml = ", ".join(f'"{c}"' for c in cats)
        out.append(f"categories: [{cats_yaml}]")
        out.append("---")

        new_text = "\n".join(out) + "\n" + body
        (dest_dir / md.name).write_text(new_text, encoding="utf-8")
        published.append(f"{parent}/{child + '/' if child else ''}{md.name}")

    # Copy ảnh
    src_img = VAULT_BLOG / "images"
    if src_img.exists():
        STATIC_IMG.mkdir(parents=True, exist_ok=True)
        n = 0
        for img in src_img.rglob("*"):
            if img.is_file():
                shutil.copy2(img, STATIC_IMG / img.name)
                n += 1
        if n:
            print(f"🖼  Copy {n} ảnh -> static/images/")

    print(f"\n✅ ĐĂNG ({len(published)}):")
    for p in published:
        print(f"   • {p}")
    if skipped:
        print(f"\n⏸  BỎ QUA ({len(skipped)}):")
        for name, why in skipped:
            print(f"   • {name}  ({why})")
    if include_drafts:
        print("\n⚠️  Đang ở chế độ --drafts (chỉ để xem thử local, ĐỪNG deploy)")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
