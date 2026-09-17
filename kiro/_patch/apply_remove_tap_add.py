#!/usr/bin/env python3
"""Remove redundant Tap / Tap to add control; KW/search already add+filter."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]
MARK = "fix-TAP-ADD-REMOVE-v1"
KEEP = (
    "c00e3e",
    "fix-INDEX-EMBED-SEP-v1",
    MARK,
)

CSS_ADD = r"""
/* fix-TAP-ADD-REMOVE-v1: Tap to add is redundant with default KW/search add */
.tap-add-btn,.cat-switch-lead:empty{display:none!important}
"""

BTN_DESK = (
    '<span class="cat-switch-lead"><button type="button" class="tap-add-btn" id="tapAddBtnPanel"'
    ' aria-pressed="false" onclick="toggleTapToAdd()">Tap to add</button></span>'
)
BTN_PORT = (
    '<span class="cat-switch-lead"><button type="button" class="tap-add-btn" id="tapAddBtnPanel"'
    ' aria-pressed="false" onclick="toggleTapToAdd()">Tap</button></span>'
)
PHONE = (
    "  phoneMoreAdd(pop,'Tap to add',function(){if(typeof toggleTapToAdd==='function')toggleTapToAdd();});\n"
)
KEY_OLD = """ var TAP_ADD_KEY='catalog-tap-to-add';
 var tapToAdd=false;
 try{tapToAdd=localStorage.getItem(TAP_ADD_KEY)==='1';}catch(err){}
 var CLEAR_MISS_KEY="""
KEY_NEW = """ var CLEAR_MISS_KEY="""
KEY_OLD_FLAT = """var TAP_ADD_KEY='catalog-tap-to-add';
var tapToAdd=false;
try{tapToAdd=localStorage.getItem(TAP_ADD_KEY)==='1';}catch(err){}
var CLEAR_MISS_KEY="""
KEY_NEW_FLAT = """var CLEAR_MISS_KEY="""

SYNC_FN_OLD_FLAT = """function syncTapToAddBtns(){
document.querySelectorAll('.tap-add-btn').forEach(function(b){
b.setAttribute('aria-pressed',tapToAdd?'true':'false');
b.classList.toggle('on',tapToAdd);
});
document.body.classList.toggle('tap-to-add',!!(tapToAdd&&currentMode==='search'));
}
function syncClearOnMissBtns(){"""
SYNC_FN_NEW_FLAT = """function syncClearOnMissBtns(){"""

TOGGLE_OLD_FLAT = """window.toggleTapToAdd=function(){
tapToAdd=!tapToAdd;
try{localStorage.setItem(TAP_ADD_KEY,tapToAdd?'1':'0');}catch(err){}
syncTapToAddBtns();
};
window.toggleClearOnMiss=function(){"""
TOGGLE_NEW_FLAT = """window.toggleClearOnMiss=function(){"""

SYNC_FN_OLD = """ function syncTapToAddBtns(){
   document.querySelectorAll('.tap-add-btn').forEach(function(b){
     b.setAttribute('aria-pressed',tapToAdd?'true':'false');
     b.classList.toggle('on',tapToAdd);
   });
   document.body.classList.toggle('tap-to-add',!!(tapToAdd&&currentMode==='search'));
 }
 function syncClearOnMissBtns(){"""
SYNC_FN_NEW = """ function syncClearOnMissBtns(){"""

TOGGLE_OLD = """ window.toggleTapToAdd=function(){
   tapToAdd=!tapToAdd;
   try{localStorage.setItem(TAP_ADD_KEY,tapToAdd?'1':'0');}catch(err){}
   syncTapToAddBtns();
 };
 window.toggleClearOnMiss=function(){"""
TOGGLE_NEW = """ window.toggleClearOnMiss=function(){"""

PARK_OLD = """  var cs=document.getElementById('catSwitch');
  var tap=document.getElementById('tapAddBtnPanel');
  if(cs&&tap){
    var lead=cs.querySelector('.cat-switch-lead');
    if(!lead){lead=document.createElement('span');lead.className='cat-switch-lead';}
    if(lead.parentElement!==cs||cs.firstElementChild!==lead)cs.insertBefore(lead,cs.firstChild);
    if(tap.parentElement!==lead)lead.appendChild(tap);
  }
  var clrBtn="""
PARK_NEW = """  var clrBtn="""


def add_indent(s, n=1):
    pad = " " * n
    return "\n".join((pad + line) if line.strip() else line for line in s.split("\n"))


def sub(text, old, new, label, optional=False, replace_all=False):
    n = text.count(old)
    if n == 1 or (replace_all and n > 0):
        return text.replace(old, new)
    if n > 1:
        raise SystemExit(f"{label}: {n} matches")
    if new in text:
        print(f"  skip {label} (already)")
        return text
    for i in range(1, 9):
        oldi, newi = add_indent(old, i), add_indent(new, i)
        ni = text.count(oldi)
        if ni == 1 or (replace_all and ni > 0):
            return text.replace(oldi, newi)
        if ni > 1:
            raise SystemExit(f"{label}: {ni} matches (indent {i})")
        if ni == 0 and newi in text:
            print(f"  skip {label} (already)")
            return text
    if optional:
        print(f"  skip {label}")
        return text
    raise SystemExit(f"{label}: not found")


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    n = path.name
    if MARK in text:
        print("skip", n)
        return
    idx = text.rfind("</style>")
    if idx < 0:
        raise SystemExit(f"{n}: no </style>")
    text = text[:idx] + CSS_ADD + text[idx:]
    if BTN_DESK in text:
        text = text.replace(BTN_DESK, "", 1)
    elif BTN_PORT in text:
        text = text.replace(BTN_PORT, "", 1)
    else:
        raise SystemExit(f"{n}: tap button html not found")
    text = sub(text, PHONE, "", f"{n}: phone more", optional=True)
    if "var TAP_ADD_KEY=" in text and " var TAP_ADD_KEY=" not in text:
        text = sub(text, KEY_OLD_FLAT, KEY_NEW_FLAT, f"{n}: tap key flat")
        text = sub(text, SYNC_FN_OLD_FLAT, SYNC_FN_NEW_FLAT, f"{n}: sync fn flat")
        text = sub(text, TOGGLE_OLD_FLAT, TOGGLE_NEW_FLAT, f"{n}: toggle fn flat")
    else:
        text = sub(text, KEY_OLD, KEY_NEW, f"{n}: tap key")
        text = sub(text, SYNC_FN_OLD, SYNC_FN_NEW, f"{n}: sync fn")
        text = sub(text, TOGGLE_OLD, TOGGLE_NEW, f"{n}: toggle fn")
    text = sub(text, PARK_OLD, PARK_NEW, f"{n}: park tap")
    text = text.replace("syncTapToAddBtns();", "")
    if "syncTapToAddBtns" in text:
        raise SystemExit(f"{n}: leftover syncTapToAddBtns")
    if "toggleTapToAdd" in text:
        raise SystemExit(f"{n}: leftover toggleTapToAdd")
    if "id=\"tapAddBtnPanel\"" in text:
        raise SystemExit(f"{n}: leftover tapAddBtnPanel")
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
    if "c00e3e" not in out:
        tmp.unlink()
        raise SystemExit(f"{n}: lost c00e3e logs")
    tmp.replace(path)
    print("OK", n, len(raw))


def main() -> None:
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)


if __name__ == "__main__":
    main()
