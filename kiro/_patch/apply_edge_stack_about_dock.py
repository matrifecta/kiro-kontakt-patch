#!/usr/bin/env python3
"""Dock #catalogEdgeStack with the same About/Document bottom clearance as ↑↓.

Does not touch Legend/Guide help body HTML. Safe temp writes, assert </html>.
Does not commit. Keeps c00e3e agent logs.
"""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
]

MARKER = "fix-EDGE-ABOUT-DOCK"

CSS_ONE_OLD = (
    "#catalogEdgeStack{display:none;position:fixed;z-index:41;flex-direction:column;"
    "align-items:flex-start;gap:.4rem;pointer-events:none;width:0;overflow:visible}"
)
CSS_ONE_NEW = (
    "/* fix-EDGE-ABOUT-DOCK: real height so bottom inset clears About like ↑↓ */\n"
    "#catalogEdgeStack{display:none;position:fixed;z-index:41;flex-direction:column;"
    "align-items:flex-start;gap:.4rem;pointer-events:none;width:max-content;height:auto;overflow:visible}"
)

CSS_PORT_OLD = (
    "    flex-direction:column;align-items:flex-start;gap:.4rem;pointer-events:none;\n"
    "    width:0;overflow:visible\n"
)
CSS_PORT_NEW = (
    "    flex-direction:column;align-items:flex-start;gap:.4rem;pointer-events:none;\n"
    "    width:max-content;height:auto;overflow:visible\n"
)

JS_OLD = """  stack.hidden=false;
  var inset=typeof catalogJumpStackBottomInset==='function'?catalogJumpStackBottomInset():0;
  var bottom=Math.max(6,Math.round((window.innerHeight||0)-r.bottom)+12+inset);
  var left=Math.max(0,Math.round(r.left));
  stack.style.position='fixed';
  stack.style.left=left+'px';
  stack.style.bottom=bottom+'px';
  stack.style.right='auto';
  stack.style.top='auto';
  stack.style.zIndex=helpOn?'860':'41';
  if(typeof catalogHelpSyncChrome==='function')catalogHelpSyncChrome();
}"""

JS_NEW = """  stack.hidden=false;
  var jump=document.getElementById('catalogJumpStack');
  var inset=typeof catalogJumpStackBottomInset==='function'?catalogJumpStackBottomInset():0;
  var padB=cs?parseFloat(cs.paddingBottom):NaN;
  var insetB=Math.max(8,Math.round((!isNaN(padB)&&padB>0)?padB:12));
  var bottom=Math.max(6,Math.round((window.innerHeight||0)-r.bottom)+insetB+inset);
  if(jump){
    var jcs=getComputedStyle(jump);
    var jBottom=parseFloat(jump.style.bottom||jcs.bottom);
    if(jcs.display!=='none'&&jcs.visibility!=='hidden'&&!isNaN(jBottom))bottom=jBottom;
  }
  var left=Math.max(0,Math.round(r.left));
  stack.style.position='fixed';
  stack.style.left=left+'px';
  stack.style.bottom=bottom+'px';
  stack.style.right='auto';
  stack.style.top='auto';
  stack.style.transform='none';
  stack.style.height='auto';
  stack.style.width='max-content';
  stack.style.zIndex=helpOn?'860':'41';
  var noteR=typeof catalogDocNoteBarRect==='function'?catalogDocNoteBarRect():null;
  var lg=document.getElementById('catalogLegendBtn');
  if(noteR&&lg){
    var lr=lg.getBoundingClientRect();
    if(lr.bottom>noteR.top-8){
      bottom+=Math.round(lr.bottom-(noteR.top-8));
      stack.style.bottom=bottom+'px';
    }
  }
  if(typeof catalogHelpSyncChrome==='function')catalogHelpSyncChrome();
}"""


def once(text, old, new, label, name, optional=False):
    n = text.count(old)
    if n == 1:
        return text.replace(old, new, 1)
    if optional and n == 0:
        print(f"  skip {name}: {label}")
        return text
    if n == 0 and new in text:
        print(f"  skip {name}: {label} already")
        return text
    raise SystemExit(f"{name}: {label} count={n} expected 1")


def patch(path: Path) -> None:
    raw = path.read_bytes()
    orig = len(raw)
    if not raw.rstrip().endswith(b"</html>"):
        raise SystemExit(f"{path.name}: missing </html> before patch")
    text = raw.decode("utf-8")
    name = path.name
    if MARKER in text and JS_NEW in text:
        print("SKIP already patched", name)
        return

    text = once(text, CSS_ONE_OLD, CSS_ONE_NEW, "css-one", name)
    text = once(text, CSS_PORT_OLD, CSS_PORT_NEW, "css-port", name, optional=True)
    text = once(text, JS_OLD, JS_NEW, "js-dock", name)

    if MARKER not in text:
        raise SystemExit(f"{name}: marker missing after patch")
    if "function placeCatalogEdgeStack(" not in text:
        raise SystemExit(f"{name}: placeCatalogEdgeStack missing")
    if JS_OLD in text:
        raise SystemExit(f"{name}: old dock JS still present")
    if not text.strip().endswith("</html>"):
        raise SystemExit(f"{name}: truncated, missing </html>")

    out = text.encode("utf-8")
    if orig > 4_000_000 and len(out) < orig * 0.9:
        raise SystemExit(f"{name}: size collapsed {orig} -> {len(out)}")

    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(out)
    wrote = tmp.read_bytes()
    if len(wrote) != len(out):
        tmp.unlink()
        raise SystemExit(f"{name}: tmp size mismatch")
    if not wrote.rstrip().endswith(b"</html>"):
        tmp.unlink()
        raise SystemExit(f"{name}: tmp missing </html>")
    tmp.replace(path)
    print("OK", name, "bytes", len(out), "delta", len(out) - orig)


def main():
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)


if __name__ == "__main__":
    main()
