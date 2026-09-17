#!/usr/bin/env python3
"""Dock Patches + Search to card bottom-left, level Search with Favorite."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]

OLD = ".card-actions{display:flex;gap:clamp(4px,0.8vw,8px);padding:clamp(4px,0.6vw,6px) 0 0 0;margin-top:auto}"
NEW = """.card-actions{display:flex;gap:clamp(4px,0.8vw,8px);padding:clamp(4px,0.6vw,6px) 0 0 0;margin-top:auto}
.entry:not(.highlight) .hl-body{display:flex;flex-direction:column;flex:1 1 auto;min-height:0}
.entry:not(.highlight) details.patches,.entry:not(.highlight) .patches{margin-top:auto;margin-bottom:0;flex:0 0 auto}
.entry:not(.highlight) .card-actions{margin-top:0;margin-bottom:calc(.5rem - .8rem);padding-bottom:0;align-self:flex-start}"""


def patch_one(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if OLD not in text:
        raise SystemExit(f"Missing card-actions rule in {path.name}")
    if text.count(OLD) != 1:
        raise SystemExit(f"{path.name}: expected 1 card-actions rule, got {text.count(OLD)}")
    path.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
    print(f"{path.name}: ok")


def main() -> None:
    for p in FILES:
        patch_one(p)


if __name__ == "__main__":
    main()
