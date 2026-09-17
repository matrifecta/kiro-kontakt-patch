#!/usr/bin/env python3
"""Show ↑/↓ unless Index Window/Embed is actually expanded.

Runtime proof (c00e3e): jump stack placed with disp:flex, then
syncIndexWindowDock set index-window-open while ixCol:true and
body.index-window-open #catalogJumpStack { display:none !important }
zeroed the buttons. Embed hide already required :not(.is-collapsed).
Also show the stack in display-middle (JS already positions it).
"""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
]

REPLACES = [
    (
        "body.index-window-open #catalogJumpStack,\n"
        "body:has(#catalogIndex.is-embedded:not(.is-collapsed)) #catalogJumpStack{\n"
        "  display:none!important\n"
        "}",
        "body.index-window-open:has(#catalogIndex:not(.is-embedded):not(.is-collapsed)) #catalogJumpStack,\n"
        "body:has(#catalogIndex.is-embedded:not(.is-collapsed)) #catalogJumpStack{\n"
        "  display:none!important\n"
        "}",
    ),
    (
        "  body.display-sides a.bottom,body.display-sides a.top{",
        "  body.display-sides a.bottom,body.display-sides a.top,body.display-middle a.bottom,body.display-middle a.top{",
    ),
    (
        "  body.display-sides #catalogJumpStack{position:fixed;z-index:40;display:flex;flex-direction:column;align-items:flex-end;gap:.35rem;pointer-events:auto}",
        "  body.display-sides #catalogJumpStack,body.display-middle #catalogJumpStack{position:fixed;z-index:40;display:flex;flex-direction:column;align-items:flex-end;gap:.35rem;pointer-events:auto}",
    ),
    (
        "  body.display-sides #catalogJumpStack>a.top,body.display-sides #catalogJumpStack>a.bottom{",
        "  body.display-sides #catalogJumpStack>a.top,body.display-sides #catalogJumpStack>a.bottom,body.display-middle #catalogJumpStack>a.top,body.display-middle #catalogJumpStack>a.bottom{",
    ),
    (
        "  body.catalog-portable.display-sides #catalogJumpStack{\n"
        "    display:flex!important;position:fixed!important;z-index:45!important;\n"
        "    flex-direction:column;align-items:flex-end;gap:.35rem;pointer-events:auto;\n"
        "    max-width:min(100%,12rem)\n"
        "  }",
        "  body.catalog-portable.display-sides #catalogJumpStack,\n"
        "  body.catalog-portable.display-middle #catalogJumpStack{\n"
        "    display:flex!important;position:fixed!important;z-index:45!important;\n"
        "    flex-direction:column;align-items:flex-end;gap:.35rem;pointer-events:auto;\n"
        "    max-width:min(100%,12rem)\n"
        "  }",
    ),
    (
        "  body.catalog-portable.display-sides #catalogJumpStack>a.top,\n"
        "  body.catalog-portable.display-sides #catalogJumpStack>a.bottom{",
        "  body.catalog-portable.display-sides #catalogJumpStack>a.top,\n"
        "  body.catalog-portable.display-sides #catalogJumpStack>a.bottom,\n"
        "  body.catalog-portable.display-middle #catalogJumpStack>a.top,\n"
        "  body.catalog-portable.display-middle #catalogJumpStack>a.bottom{",
    ),
]


def safe_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    out = tmp.read_text(encoding="utf-8")
    if not out.rstrip().endswith("</html>"):
        tmp.unlink(missing_ok=True)
        raise SystemExit(f"{path.name}: rewrite would drop </html>")
    path.write_text(out, encoding="utf-8")
    tmp.unlink(missing_ok=True)


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    orig = text
    for old, new in REPLACES:
        if old not in text:
            if new in text:
                print(f"  already: {old[:48]!r} in {path.name}")
                continue
            print(f"  MISS: {old[:72]!r} in {path.name}")
            continue
        n = text.count(old)
        text = text.replace(old, new)
        print(f"  {n}x {old[:48]!r} -> {path.name}")
    if text == orig:
        raise SystemExit(f"{path.name}: no changes")
    if "index-window-open:has(#catalogIndex:not(.is-embedded):not(.is-collapsed)) #catalogJumpStack" not in text:
        raise SystemExit(f"{path.name}: hide selector missing after splice")
    safe_write(path, text)
    print(f"ok {path.name} bytes={path.stat().st_size}")


def main() -> None:
    for p in FILES:
        print("==", p.name)
        patch(p)


if __name__ == "__main__":
    main()
