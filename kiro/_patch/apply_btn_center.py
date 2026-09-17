#!/usr/bin/env python3
"""Center labels/symbols in catalog chrome buttons."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-ds-catalog-html.sh",
    ROOT / "kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-kontakt-catalog-html.sh",
]

CENTER_BLOCK = (
    " .ui-btn-center,.display-btn,.clear-miss-btn,.layout-edit-btn,.layout-default-btn,.layout-presets-btn,.layout-presets-tab,.hdr-menu-btn,.search-strip-clear,.search-strip-hide,.search-strip-fs,.search-strip-more,.mode-btn,.cat-btn,.tap-add-btn,.ui-scale-step,.ui-scale-readout,.ac-history-btn,.catalog-index-embed,.layout-restore-defaults,.layout-presets-save>button,.kw-strip-hide,.kw-fs-btn,.fs-stripe-scale-btn,.fs-snap-btn,.fs-stripe-trigger,.card-min-save{display:inline-flex;align-items:center;justify-content:center;line-height:1;text-align:center}\n"
    " .search-strip-clear,.mode-btn,.cat-btn,.tap-add-btn{padding-top:0;padding-bottom:0}\n"
    ' .display-btn[data-display="middle"]{align-items:center!important;justify-content:center!important;line-height:1}\n'
)

REPLACES = [
    (
        " .display-btn{box-sizing:border-box;min-height:2.25rem;padding:0 .65rem;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text-muted);font:inherit;font-size:.8125rem;cursor:pointer;touch-action:manipulation}\n",
        " .display-btn{box-sizing:border-box;min-height:2.25rem;padding:0 .65rem;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text-muted);font:inherit;font-size:.8125rem;cursor:pointer;touch-action:manipulation;display:inline-flex;align-items:center;justify-content:center;line-height:1;text-align:center}\n"
        + CENTER_BLOCK,
        "display-btn",
    ),
    (
        '.display-btn[data-display="middle"]{display:inline-flex!important}',
        '.display-btn[data-display="middle"]{display:inline-flex!important;align-items:center;justify-content:center;line-height:1}',
        "middle",
    ),
    (
        " .hdr-menu-btn{box-sizing:border-box;min-width:2.25rem;min-height:2.25rem;padding:0 .5rem;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text-muted);font:inherit;font-size:.875rem;font-weight:600;cursor:pointer;touch-action:manipulation;line-height:1}\n",
        " .hdr-menu-btn{box-sizing:border-box;min-width:2.25rem;min-height:2.25rem;padding:0 .5rem;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text-muted);font:inherit;font-size:.875rem;font-weight:600;cursor:pointer;touch-action:manipulation;line-height:1;display:inline-flex;align-items:center;justify-content:center;text-align:center}\n",
        "hdr",
    ),
    (
        " .search-strip-clear{flex-shrink:0;background:transparent;border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:6px 12px;font-size:.9375rem;cursor:pointer;min-height:2.75rem;touch-action:manipulation}\n",
        " .search-strip-clear{flex-shrink:0;background:transparent;border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:0 12px;font-size:.9375rem;cursor:pointer;min-height:2.75rem;touch-action:manipulation;display:inline-flex;align-items:center;justify-content:center;line-height:1;text-align:center}\n",
        "search-clear",
    ),
    (
        " .mode-btn{background:var(--bg-card);border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:6px 12px;font-size:.875rem;cursor:pointer;min-height:2.25rem;touch-action:manipulation}\n",
        " .mode-btn{background:var(--bg-card);border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:0 12px;font-size:.875rem;cursor:pointer;min-height:2.25rem;touch-action:manipulation;display:inline-flex;align-items:center;justify-content:center;line-height:1;text-align:center}\n",
        "mode",
    ),
    (
        " .clear-miss-btn{flex-shrink:0;box-sizing:border-box;min-height:2.25rem;background:transparent;border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:0 .625rem;font-size:.875rem;cursor:pointer;touch-action:manipulation;white-space:nowrap}\n",
        " .clear-miss-btn{flex-shrink:0;box-sizing:border-box;min-height:2.25rem;background:transparent;border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:0 .625rem;font-size:.875rem;cursor:pointer;touch-action:manipulation;white-space:nowrap;display:inline-flex;align-items:center;justify-content:center;line-height:1;text-align:center}\n",
        "clear-miss",
    ),
]


def apply(path: Path) -> None:
    t = path.read_text(encoding="utf-8")
    for old, new, label in REPLACES:
        if old not in t:
            if new in t or (label == "display-btn" and "ui-btn-center" in t):
                print(f"  skip {path.name} {label}")
                continue
            raise SystemExit(f"{path.name}: missing {label}")
        t = t.replace(old, new)
        print(f"  {path.name} {label}")
    path.write_text(t, encoding="utf-8")


def main() -> None:
    for path in FILES:
        apply(path)


if __name__ == "__main__":
    main()
