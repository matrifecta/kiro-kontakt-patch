#!/usr/bin/env python3
"""Embed expanded Index: full-width in-flow list that pushes cards; centered 1px rule in a small gap."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]
MARK = "fix-INDEX-EMBED-SEP-v2"
OLD_MARK = "fix-INDEX-EMBED-SEP-v1"
KEEP = (
    "c00e3e",
    "fix-INDEX-EMBED-FULL-v1",
    "fix-INDEX-EMBED-FULL-v2",
    "fix-INDEX-EMBED-FULL-v3",
    MARK,
    "fix-TAP-ADD-REMOVE-v1",
)

PIN_OLD = """  function pin(el){
    el.style.setProperty('height','auto','important');
    el.style.setProperty('max-height','none','important');
    el.style.setProperty('min-height',el===ix?'min-content':'0','important');
    el.style.setProperty('overflow','visible','important');
    el.style.setProperty('overflow-x','visible','important');
    el.style.setProperty('overflow-y','visible','important');
    el.style.setProperty('flex','0 0 auto','important');
    if(el===ix){
      el.style.setProperty('position','relative','important');
      el.style.setProperty('grid-column','1 / -1','important');
      el.style.setProperty('align-self','start','important');
      el.style.setProperty('margin-bottom','calc(20px - clamp(0.6rem,1.2vw,1.15rem))','important');
    }
  }
  pin(ix);pin(il);"""

PIN_NEW = """  function pin(el){
    el.style.setProperty('height','auto','important');
    el.style.setProperty('max-height','none','important');
    el.style.setProperty('min-height',el===ix?'min-content':'0','important');
    el.style.setProperty('overflow','visible','important');
    el.style.setProperty('overflow-x','visible','important');
    el.style.setProperty('overflow-y','visible','important');
    el.style.setProperty('flex','0 0 auto','important');
    if(el===ix){
      el.style.setProperty('position','relative','important');
      el.style.setProperty('align-self','stretch','important');
      el.style.setProperty('margin-bottom','0','important');
    }
  }
  pin(ix);pin(il);"""

CLEAR_OLD = """    ['overflow','overflow-x','overflow-y'].forEach(function(p){ix.style.removeProperty(p);il.style.removeProperty(p);});
    ['height','max-height','min-height','flex'].forEach(function(p){il.style.removeProperty(p);});
    if(!document.body.classList.contains('index-fill-doc')){
      ['height','max-height','min-height','flex'].forEach(function(p){ix.style.removeProperty(p);});
    }
    return;"""

CLEAR_NEW = """    ['overflow','overflow-x','overflow-y'].forEach(function(p){ix.style.removeProperty(p);il.style.removeProperty(p);});
    ['height','max-height','min-height','flex'].forEach(function(p){il.style.removeProperty(p);});
    if(!document.body.classList.contains('index-fill-doc')){
      ['height','max-height','min-height','flex'].forEach(function(p){ix.style.removeProperty(p);});
    }
    ['position','grid-column','align-self','margin-bottom'].forEach(function(p){ix.style.removeProperty(p);});
    return;"""


def add_indent(s, n=1):
    pad = " " * n
    return "\n".join((pad + line) if line.strip() else line for line in s.split("\n"))


def sub(text, old, new, label, optional=False):
    n = text.count(old)
    if n == 1:
        return text.replace(old, new)
    if n > 1:
        raise SystemExit(f"{label}: {n} matches")
    if new in text:
        print(f"  skip {label} (already)")
        return text
    for i in range(1, 9):
        oldi, newi = add_indent(old, i), add_indent(new, i)
        ni = text.count(oldi)
        if ni == 1:
            return text.replace(oldi, newi)
        if ni > 1:
            raise SystemExit(f"{label}: {ni} matches (indent {i})")
        if newi in text:
            print(f"  skip {label} (already)")
            return text
    if optional:
        print(f"  skip {label}")
        return text
    raise SystemExit(f"{label}: not found")

CSS_ADD = r"""
/* fix-INDEX-EMBED-SEP-v2: Embed expanded — full list height, cards below, 1px rule centered in a small gap */
html body .catalog-body:has(>#catalogIndex.is-embedded:not(.is-collapsed)),
html body.display-sides .catalog-body:has(>#catalogIndex.is-embedded:not(.is-collapsed)),
html body.display-middle .catalog-body:has(>#catalogIndex.is-embedded:not(.is-collapsed)),
html body.catalog-portable .catalog-body:has(>#catalogIndex.is-embedded:not(.is-collapsed)),
html body #catalogMain>.catalog-body:has(>#catalogIndex.is-embedded:not(.is-collapsed)),
html body.display-sides #catalogMain>.catalog-body:has(>#catalogIndex.is-embedded:not(.is-collapsed)),
html body.display-middle #catalogMain>.catalog-body:has(>#catalogIndex.is-embedded:not(.is-collapsed)),
html body.catalog-portable #catalogMain>.catalog-body:has(>#catalogIndex.is-embedded:not(.is-collapsed)){
  display:flex!important;
  flex-direction:column!important;
  flex-wrap:nowrap!important;
  align-items:stretch!important;
  gap:20px!important
}
html body .catalog-body:has(>#catalogIndex.is-embedded:not(.is-collapsed))>.loc-group:not(.is-hidden),
html body #catalogMain>.catalog-body:has(>#catalogIndex.is-embedded:not(.is-collapsed))>.loc-group:not(.is-hidden){
  display:grid!important;
  grid-template-columns:var(--cat-cols)!important;
  gap:clamp(0.6rem,1.2vw,1.15rem)!important;
  width:100%!important;
  max-width:100%!important;
  flex:0 0 auto!important;
  position:relative!important;
  top:auto!important;
  left:auto!important;
  right:auto!important;
  margin-top:0!important;
  order:0!important
}
html body #catalogIndex.is-embedded:not(.is-collapsed),
html body.display-sides #catalogIndex.is-embedded:not(.is-collapsed),
html body.display-middle #catalogIndex.is-embedded:not(.is-collapsed),
html body.catalog-portable #catalogIndex.is-embedded:not(.is-collapsed),
html body.catalog-portable.display-sides #catalogIndex.is-embedded:not(.is-collapsed),
html body.catalog-portable.display-content #catalogIndex.is-embedded:not(.is-collapsed),
html body #catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed),
html body.display-sides #catalogMain .catalog-body>#catalogIndex.is-embedded:not(.is-collapsed),
html body.display-middle #catalogMain .catalog-body>#catalogIndex.is-embedded:not(.is-collapsed),
html body.catalog-portable #catalogMain .catalog-body>#catalogIndex.is-embedded:not(.is-collapsed),
html body.catalog-portable.display-sides #catalogMain .catalog-body>#catalogIndex.is-embedded:not(.is-collapsed){
  --index-embed-gap:20px;
  position:relative!important;
  top:auto!important;
  left:auto!important;
  right:auto!important;
  grid-column:auto!important;
  grid-row:auto!important;
  width:100%!important;
  max-width:100%!important;
  height:auto!important;
  max-height:none!important;
  min-height:min-content!important;
  flex:0 0 auto!important;
  order:-6!important;
  margin-bottom:0!important;
  border:0!important;
  border-radius:0!important;
  box-shadow:none!important;
  box-sizing:border-box!important;
  overflow:visible!important;
  overflow-x:visible!important;
  overflow-y:visible!important;
  align-self:stretch!important;
  z-index:2!important
}
html body #catalogIndex.is-embedded:not(.is-collapsed)::after,
html body.display-sides #catalogIndex.is-embedded:not(.is-collapsed)::after,
html body.display-middle #catalogIndex.is-embedded:not(.is-collapsed)::after,
html body.catalog-portable #catalogIndex.is-embedded:not(.is-collapsed)::after,
html body #catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed)::after{
  content:"";
  position:absolute;
  left:0;
  right:0;
  bottom:calc(var(--index-embed-gap,20px) / -2);
  height:0;
  border:0;
  border-bottom:1px solid var(--border);
  pointer-events:none;
  z-index:3
}
html body #catalogIndex.is-embedded:not(.is-collapsed) .index,
html body #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList,
html body.display-sides #catalogIndex.is-embedded:not(.is-collapsed) .index,
html body.display-sides #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList,
html body.display-middle #catalogIndex.is-embedded:not(.is-collapsed) .index,
html body.display-middle #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList,
html body.catalog-portable #catalogIndex.is-embedded:not(.is-collapsed) .index,
html body.catalog-portable #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList,
html body #catalogMain .catalog-body #catalogIndex.is-embedded:not(.is-collapsed) ul#catalogIndexList.index{
  border:0!important;
  border-bottom:0!important;
  padding-bottom:2px!important;
  box-sizing:border-box!important;
  border-radius:0!important;
  overflow:visible!important;
  overflow-x:visible!important;
  overflow-y:visible!important;
  height:auto!important;
  max-height:none!important;
  flex:0 0 auto!important
}
"""


def replace_sep_block(text: str, n: str) -> str:
    for mark in (MARK, OLD_MARK):
        needle = "/* " + mark
        start = text.find(needle)
        if start < 0:
            continue
        # Do not swallow later patches (Tap remove sits immediately after).
        next_cmt = text.find("\n/* ", start + 4)
        style_end = text.find("</style>", start)
        if style_end < 0:
            raise SystemExit(f"{n}: marker without </style>")
        end = next_cmt if 0 <= next_cmt < style_end else style_end
        return text[:start] + CSS_ADD.lstrip("\n") + text[end:]
    idx = text.rfind("</style>")
    if idx < 0:
        raise SystemExit(f"{n}: no </style>")
    return text[:idx] + CSS_ADD + text[idx:]


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    n = path.name
    before_c00 = text.count("sessionId:'c00e3e'")
    before_tap = "fix-TAP-ADD-REMOVE-v1" in text
    text = replace_sep_block(text, n)
    text = sub(text, PIN_OLD, PIN_NEW, f"{n}: pin grid-column")
    text = sub(text, CLEAR_OLD, CLEAR_NEW, f"{n}: clear embed pin", optional=True)
    raw = text.encode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(raw)
    out = tmp.read_bytes().decode("utf-8")
    if not out.strip().endswith("</html>"):
        tmp.unlink()
        raise SystemExit(f"{n}: truncated")
    for keep in KEEP:
        if keep not in out:
            tmp.unlink()
            raise SystemExit(f"{n}: lost {keep}")
    if before_tap and "fix-TAP-ADD-REMOVE-v1" not in out:
        tmp.unlink()
        raise SystemExit(f"{n}: lost TAP remove")
    if out.count("sessionId:'c00e3e'") < before_c00:
        tmp.unlink()
        raise SystemExit(f"{n}: lost c00e3e logs")
    if OLD_MARK in out:
        tmp.unlink()
        raise SystemExit(f"{n}: old SEP marker remains")
    tmp.replace(path)
    print("OK", n, len(raw))


def main() -> None:
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)


if __name__ == "__main__":
    main()
