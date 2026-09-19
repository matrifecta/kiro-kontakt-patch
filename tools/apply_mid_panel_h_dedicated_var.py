#!/usr/bin/env python3
"""
Refactor: Middle-mode's Search/Keywords panel height was driven by
`--portable-menu-h`, a global custom property on <html> that is ALSO
written by completely unrelated code for the phone/landscape-stacked
mode's own persisted bucket (applyLayoutBucket()'s portable/non-middle/
non-wide branch). Because both modes shared one variable, any resize-
triggered application of the phone bucket (which fires during a
portrait->landscape rotation, before Middle mode's own restore logic
gets a chance to run) silently overwrote Middle mode's height with the
phone bucket's unrelated stored value - this was the actual cause of the
Middle-mode panel appearing to "contract" after rotating back.

This is fixed structurally, not by chasing every resize listener:
Middle mode already has its own dedicated, already-correctly-managed
variable `--middle-menu-h` (read/written only by applyMiddleLayout(),
writeMiddleLayout(), and the 'middle-*' bucket branch of
applyLayoutBucket()/snapshotCurrentLayoutBucket()). The only reason it
wasn't already immune to this bug is that the CSS rules that actually
render the Middle-mode panel height were, inconsistently, reading
`--portable-menu-h` instead. Retargeting those rules to `--middle-menu-h`
removes the cross-mode collision by construction - no matter how many
independent resize/orientation code paths exist, they can no longer
step on Middle mode's own state, because they never touch its variable.

Fix (MID-PANEL-H-DEDICATED-VAR-v1):
  1. CSS: every `.display-middle`-scoped rule that set #searchChrome or
     #filterWrap's `height` from `var(--portable-menu-h, ...)` is
     retargeted to `var(--middle-menu-h, ...)`. Rules for OTHER modes
     (phone-stacked non-middle, drag-resize handle placement, etc.)
     keep using `--portable-menu-h` untouched - only the display-middle
     branches are renamed.
  2. JS: removed the single stray line in applyLayoutBucket()'s
     phone-bucket branch that additionally wrote `--middle-menu-h`
     (a leftover cross-write from before Middle mode had all of the
     CSS rules it needed - now redundant and actively harmful).
"""
import sys

FILES = [
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

TAG = "MID-PANEL-H-DEDICATED-VAR-v1"

CSS_REPLACEMENTS = [
    (
        "  body.catalog-portable.display-sides.display-middle:not(.ac-fs-open):not(.kw-fs-open):not(.search-chrome-collapsed) #searchChrome,\n"
        "  body.catalog-portable.display-sides.display-middle.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed):not(.kw-fs-open) #filterWrap{\n"
        "    height:var(--portable-menu-h,min(44dvh,22rem))!important;\n"
        "    max-height:min(52dvh,28rem)!important\n"
        "  }\n"
        "}\n"
        "@media(orientation:portrait){\n"
        "  body.catalog-portable.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.dual-fs-open){",
        "  body.catalog-portable.display-sides.display-middle:not(.ac-fs-open):not(.kw-fs-open):not(.search-chrome-collapsed) #searchChrome,\n"
        "  body.catalog-portable.display-sides.display-middle.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed):not(.kw-fs-open) #filterWrap{\n"
        "    height:var(--middle-menu-h,min(44dvh,22rem))!important;\n"
        "    max-height:min(52dvh,28rem)!important\n"
        "  }\n"
        "}\n"
        "@media(orientation:portrait){\n"
        "  body.catalog-portable.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.dual-fs-open){",
    ),
    (
        "  body.catalog-portable.display-sides.display-middle:not(.ac-fs-open):not(.kw-fs-open):not(.search-chrome-collapsed) #searchChrome{\n"
        "    height:var(--portable-menu-h,min(44dvh,22rem))!important;\n"
        "    max-height:min(52dvh,28rem)!important;flex:0 0 auto!important;overflow:hidden!important\n"
        "  }\n"
        "  body.catalog-portable.display-sides.display-middle.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed):not(.kw-fs-open) #filterWrap{\n"
        "    height:var(--portable-menu-h,min(44dvh,22rem))!important;\n"
        "    max-height:min(52dvh,28rem)!important;flex:0 0 auto!important;overflow:hidden!important\n"
        "  }",
        "  body.catalog-portable.display-sides.display-middle:not(.ac-fs-open):not(.kw-fs-open):not(.search-chrome-collapsed) #searchChrome{\n"
        "    height:var(--middle-menu-h,min(44dvh,22rem))!important;\n"
        "    max-height:min(52dvh,28rem)!important;flex:0 0 auto!important;overflow:hidden!important\n"
        "  }\n"
        "  body.catalog-portable.display-sides.display-middle.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed):not(.kw-fs-open) #filterWrap{\n"
        "    height:var(--middle-menu-h,min(44dvh,22rem))!important;\n"
        "    max-height:min(52dvh,28rem)!important;flex:0 0 auto!important;overflow:hidden!important\n"
        "  }",
    ),
    (
        "  body.catalog-portable.display-sides.display-middle:not(.ac-fs-open):not(.kw-fs-open):not(.search-chrome-collapsed) #searchChrome,\n"
        "  body.catalog-portable.display-sides.display-middle.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed):not(.kw-fs-open) #filterWrap{\n"
        "    height:var(--portable-menu-h,min(44dvh,22rem))!important;\n"
        "    max-height:min(52dvh,28rem)!important;flex:0 0 auto!important\n"
        "  }\n"
        "}\n"
        "\n"
        "/* fix-NAV-INDEX-KW",
        "  body.catalog-portable.display-sides.display-middle:not(.ac-fs-open):not(.kw-fs-open):not(.search-chrome-collapsed) #searchChrome,\n"
        "  body.catalog-portable.display-sides.display-middle.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed):not(.kw-fs-open) #filterWrap{\n"
        "    height:var(--middle-menu-h,min(44dvh,22rem))!important;\n"
        "    max-height:min(52dvh,28rem)!important;flex:0 0 auto!important\n"
        "  }\n"
        "}\n"
        "\n"
        "/* fix-NAV-INDEX-KW",
    ),
    (
        "  height:var(--portable-menu-h,min(44dvh,22rem))!important;\n"
        "  max-height:min(70dvh,36rem)!important;min-height:96px!important;\n"
        "  flex:0 0 auto!important;width:100%!important;max-width:none!important;\n"
        "  overflow:hidden!important;position:relative!important;inset:auto!important;\n"
        "  transform:none!important;z-index:6!important;grid-column:auto!important;grid-row:auto!important\n"
        "}",
        "  height:var(--middle-menu-h,min(44dvh,22rem))!important;\n"
        "  max-height:min(70dvh,36rem)!important;min-height:96px!important;\n"
        "  flex:0 0 auto!important;width:100%!important;max-width:none!important;\n"
        "  overflow:hidden!important;position:relative!important;inset:auto!important;\n"
        "  transform:none!important;z-index:6!important;grid-column:auto!important;grid-row:auto!important\n"
        "}",
    ),
    (
        "  height:var(--portable-menu-h,min(44dvh,22rem))!important;\n"
        "  max-height:min(70dvh,36rem)!important;min-height:96px!important;\n"
        "  flex:0 0 auto!important;overflow:hidden!important;z-index:6!important;\n"
        "  width:100%!important;grid-column:auto!important;grid-row:auto!important",
        "  height:var(--middle-menu-h,min(44dvh,22rem))!important;\n"
        "  max-height:min(70dvh,36rem)!important;min-height:96px!important;\n"
        "  flex:0 0 auto!important;overflow:hidden!important;z-index:6!important;\n"
        "  width:100%!important;grid-column:auto!important;grid-row:auto!important",
    ),
    (
        "body.catalog-portable.display-middle:not(.display-sides).kw-open:not(.kw-chrome-collapsed) #filterWrap{height:var(--portable-menu-h,min(44dvh,22rem))!important;max-height:min(52dvh,28rem)!important;flex:0 0 auto!important;overflow:hidden!important}",
        "body.catalog-portable.display-middle:not(.display-sides).kw-open:not(.kw-chrome-collapsed) #filterWrap{height:var(--middle-menu-h,min(44dvh,22rem))!important;max-height:min(52dvh,28rem)!important;flex:0 0 auto!important;overflow:hidden!important}",
    ),
]

JS_OLD = (
    "    if(b.pmh){\n"
    "      var pmhC=Math.max(56,Math.min(Math.max(56,vhP-120),parseInt(b.pmh,10)));\n"
    "      document.documentElement.style.setProperty('--portable-menu-h',pmhC+'px');\n"
    "      document.documentElement.style.setProperty('--middle-menu-h',pmhC+'px');\n"
    "    }"
)
JS_NEW = (
    "    if(b.pmh){\n"
    "      var pmhC=Math.max(56,Math.min(Math.max(56,vhP-120),parseInt(b.pmh,10)));\n"
    "      document.documentElement.style.setProperty('--portable-menu-h',pmhC+'px');\n"
    "      /* fix-" + TAG + ": this branch is the phone/landscape-stacked (non-Middle)\n"
    "         bucket - it must not also write --middle-menu-h, which is Middle mode's\n"
    "         own dedicated variable (managed by applyMiddleLayout()/writeMiddleLayout()/\n"
    "         the 'middle-*' bucket branch below). Writing it here caused Middle mode's\n"
    "         panel height to get silently clobbered by this unrelated bucket during\n"
    "         a portrait->landscape->portrait rotation. */\n"
    "    }"
)


def patch(path):
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    if TAG in src:
        print(f"{path}: already patched, skipping")
        return
    for i, (old, new) in enumerate(CSS_REPLACEMENTS):
        if old not in src:
            print(f"{path}: CSS anchor #{i} not found", file=sys.stderr)
            sys.exit(1)
        if src.count(old) != 1:
            print(f"{path}: CSS anchor #{i} not unique ({src.count(old)} matches)", file=sys.stderr)
            sys.exit(1)
        src = src.replace(old, new, 1)
    if JS_OLD not in src:
        print(f"{path}: JS anchor not found", file=sys.stderr)
        sys.exit(1)
    src = src.replace(JS_OLD, JS_NEW, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    print(f"{path}: patched")


if __name__ == "__main__":
    for rel in FILES:
        patch(rel)
