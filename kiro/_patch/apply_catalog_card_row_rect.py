#!/usr/bin/env python3
"""Row equalize (portrait rects), path collapse/expand, Collapse-all paths, DS piano covers."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]

MARK = "fix-CARD-ROW-RECT"
CSS_ANCHOR = "/* fix-PATH-COLLAPSE:"
CSS_ADD = r"""/* fix-CARD-ROW-RECT: portrait cards; tighter chrome; path-fs control; no cube equalize */
.entry:not(.highlight){align-self:start}
.entry:not(.highlight) .cover,.entry:not(.highlight) .cover img{
  aspect-ratio:auto!important;object-fit:contain!important;object-position:center center;
  width:auto!important;height:auto!important;max-width:100%;
  max-height:clamp(7.5rem,18vw,12.5rem)!important
}
.entry .path .path-fs-hit{
  font:inherit;font-size:.8125rem;line-height:1.2;cursor:pointer;touch-action:manipulation;
  border:1px solid var(--border);border-radius:6px;background:var(--bg-surface);color:var(--text-muted);
  min-height:2rem;padding:.25rem .55rem
}
.entry .path.is-expanded code{cursor:pointer}
.entry .path.is-expanded code:hover{text-decoration:underline;text-decoration-style:dotted}

"""

# spacing: between wide-gap and tight
SPACING_OLD = """/* fix-PATH-COLLAPSE: one-line path by default; click expands in-card then overlay */
.entry .path{
  cursor:pointer;box-sizing:border-box;min-width:0;
  margin:.4rem 0 .9rem!important
}"""
SPACING_NEW = """/* fix-PATH-COLLAPSE: one-line path by default; click expands in-card then overlay */
.entry .path{
  cursor:pointer;box-sizing:border-box;min-width:0;
  margin:.35rem 0 .65rem!important
}"""

SPACING2_OLD = """.entry details.patches,
.entry .patches{
  margin-bottom:.55rem!important;padding-top:.55rem
}
.entry:not(.highlight) details.patches,
.entry:not(.highlight) .patches{
  margin-top:auto;padding-top:.75rem;margin-bottom:.45rem!important
}"""
SPACING2_NEW = """.entry details.patches,
.entry .patches{
  margin-bottom:.42rem!important;padding-top:.42rem
}
.entry:not(.highlight) details.patches,
.entry:not(.highlight) .patches{
  margin-top:auto;padding-top:.55rem;margin-bottom:.32rem!important
}"""

SPACING3_OLD = """.entry .card-actions,
.entry:not(.highlight) .card-actions{
  margin-top:.95rem!important;padding-top:.55rem
}
.entry .card-actions .search-popup-btn{margin-top:.15rem}"""
SPACING3_NEW = """.entry .card-actions,
.entry:not(.highlight) .card-actions{
  margin-top:.62rem!important;padding-top:.38rem
}
.entry .card-actions .search-popup-btn{margin-top:.08rem}"""

HELPERS_OLD = "function equalizeCatalogCardRows(){\n  var _eqT0="
HELPERS_NEW = r"""function catalogCardHeightCube(h,w){
  return w>20&&h>=w*0.92&&h<=w*1.08;
}
function collapseCatalogPaths(){
  var n=0;
  document.querySelectorAll('.entry .path.is-expanded').forEach(function(p){
    p.classList.remove('is-expanded');
    p.classList.add('is-collapsed');
    p.setAttribute('aria-expanded','false');
    n++;
  });
  return n;
}
function bindCatalogPathHits(){
  document.querySelectorAll('.entry .path').forEach(function(p){
    if(p.dataset.pathBound==='1')return;
    p.dataset.pathBound='1';
    if(!p.classList.contains('is-expanded')){p.setAttribute('aria-expanded','false');}
    if(!p.querySelector('.path-fs-hit')){
      var hit=document.createElement('button');
      hit.type='button';hit.className='path-fs-hit';hit.textContent='path';
      hit.setAttribute('aria-label','Open path fullscreen');
      p.appendChild(hit);
    }
  });
}
window.collapseCatalogPaths=collapseCatalogPaths;
window.bindCatalogPathHits=bindCatalogPathHits;
function equalizeCatalogCardRows(){
  var _eqT0="""

EQ_ROW_OLD = """    rows.forEach(function(row){
      if(row.cards.length<2)return;
      var maxH=0;
      row.cards.forEach(function(e){
        if(e.querySelector('details.patches[open]'))return;
        maxH=Math.max(maxH,e.getBoundingClientRect().height);
      });
      if(!(maxH>0)){
        row.cards.forEach(function(e){maxH=Math.max(maxH,e.getBoundingClientRect().height);});
      }
      var mh=Math.round(maxH);
      if(!(mh>0))return;
      row.cards.forEach(function(e){e.style.minHeight=mh+'px';});
      if(!rowLog)rowLog={n:row.cards.length,mh:mh,hs:row.cards.map(function(e){return Math.round(e.getBoundingClientRect().height);}),open:row.cards.map(function(e){return !!e.querySelector('details.patches[open]');})};
    });"""

EQ_ROW_NEW = """    rows.forEach(function(row){
      if(row.cards.length<2)return;
      var maxH=0;
      row.cards.forEach(function(e){
        var r=e.getBoundingClientRect();
        var h=r.height,w=r.width;
        if(catalogCardHeightCube(h,w))return;
        maxH=Math.max(maxH,h);
      });
      if(!(maxH>0)){
        row.cards.forEach(function(e){maxH=Math.max(maxH,e.getBoundingClientRect().height);});
      }
      var mh=Math.round(maxH);
      if(!(mh>0))return;
      row.cards.forEach(function(e){
        var w=e.getBoundingClientRect().width;
        var use=mh;
        if(catalogCardHeightCube(mh,w))use=Math.round(e.getBoundingClientRect().height);
        e.style.minHeight=use>0?use+'px':'';
      });
      if(!rowLog)rowLog={n:row.cards.length,mh:mh,hs:row.cards.map(function(e){return Math.round(e.getBoundingClientRect().height);}),open:row.cards.map(function(e){return !!e.querySelector('details.patches[open]');}),paths:row.cards.map(function(e){var p=e.querySelector('.path');return !!(p&&p.classList.contains('is-expanded'));})};
    });"""

COLLAPSE_PATHS_OLD = """    document.querySelectorAll('.entry details.patches, .entry details.grp').forEach(function(d){
      if(d.open){d.open=false;n++;}
    });
    if(typeof equalizeCatalogCardRows==='function')equalizeCatalogCardRows();"""

COLLAPSE_PATHS_NEW = """    document.querySelectorAll('.entry details.patches, .entry details.grp').forEach(function(d){
      if(d.open){d.open=false;n++;}
    });
    if(typeof collapseCatalogPaths==='function')collapseCatalogPaths();
    if(typeof equalizeCatalogCardRows==='function')equalizeCatalogCardRows();"""

CLICK_OLD = """      if(!pathBox.classList.contains('is-expanded')){
        pathBox.classList.add('is-expanded');
        pathBox.classList.remove('is-collapsed');
        pathBox.setAttribute('aria-expanded','true');
        if(typeof scheduleEqualizeCardRows==='function')scheduleEqualizeCardRows();
        e.preventDefault();e.stopPropagation();return;
      }
      activatePath(entry);return;"""

CLICK_NEW = """      if(!pathBox.classList.contains('is-expanded')){
        pathBox.classList.add('is-expanded');
        pathBox.classList.remove('is-collapsed');
        pathBox.setAttribute('aria-expanded','true');
        if(typeof scheduleEqualizeCardRows==='function')scheduleEqualizeCardRows();
        e.preventDefault();e.stopPropagation();return;
      }
      if(e.target.closest('code')||e.target.closest('b')){
        pathBox.classList.remove('is-expanded');
        pathBox.classList.add('is-collapsed');
        pathBox.setAttribute('aria-expanded','false');
        if(typeof scheduleEqualizeCardRows==='function')scheduleEqualizeCardRows();
        e.preventDefault();e.stopPropagation();return;
      }
      return;"""

BOOT_OLD = "document.querySelectorAll('.entry').forEach(function(el){entryPatchCount(el);});\nwindow.addEventListener('resize'"
BOOT_NEW = """document.querySelectorAll('.entry').forEach(function(el){entryPatchCount(el);});
if(typeof bindCatalogPathHits==='function')bindCatalogPathHits();
if(typeof scheduleEqualizeCardRows==='function')scheduleEqualizeCardRows();
window.addEventListener('resize'"""

PORT_BIND_OLD = """function bindPortablePathHits(){
  document.querySelectorAll('.entry .path').forEach(function(p){
    if(p.dataset.pathBound==='1')return;
    p.dataset.pathBound='1';
    p.classList.add('is-collapsed');
    var b=p.querySelector('b');
    if(b)b.classList.add('path-open-hit');if(!p.classList.contains('is-expanded')){p.setAttribute('aria-expanded','false');}
    if(!p.querySelector('.path-fs-hit')){
      var hit=document.createElement('button');
      hit.type='button';hit.className='path-fs-hit';hit.textContent='path';
      hit.setAttribute('aria-label','Open path fullscreen');
      p.appendChild(hit);
    }
  });
}"""

PORT_BIND_NEW = """function bindPortablePathHits(){
  document.querySelectorAll('.entry .path').forEach(function(p){
    if(!p.classList.contains('is-expanded'))p.classList.add('is-collapsed');
  });
  if(typeof bindCatalogPathHits==='function')bindCatalogPathHits();
}"""

# DS piano libraries with stock background.png skin
DS_PIANO_IDS = (
    "1417838_ClaustrophobicPianoV2_ChristianHenson",
    "1445643_TheCoolPiano_ChristianHenson",
    "1453143_TheGaffer_ChristianHenson",
)
DS_LIB_ROOT = Path("/mnt/btrfs_disk/DS Libraries")

IMG_EXT = re.compile(r"\.(png|jpe?g|gif|bmp|webp)$", re.I)
SKIP_NAME = re.compile(
    r"knob|dial|fader|slider|button|hover|switch|led|arrow|sprite|filmstrip|_anim|template_skin|blank_icon|macro",
    re.I,
)
PREF_NAME = re.compile(r"cover|artwork|(^|/)photo[._-]|_ds\.", re.I)
BG_NAMED = re.compile(r"(^|/)bg[_.-]|_bg\.", re.I)
BARE_BG = re.compile(r"(^|/)background\.(png|jpe?g|gif|webp|bmp)$", re.I)
IN_RES = re.compile(r"/(Images|Image|Resources|Samples)/", re.I)


def once(text: str, old: str, new: str, label: str, required: bool = True) -> str:
    if old not in text:
        if new in text or (not required and MARK in text):
            print(f"  skip {label}")
            return text
        if required:
            raise SystemExit(f"MISSING [{label}]")
        print(f"  skip {label} (optional)")
        return text
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"COUNT [{label}]: {n}")
    print(f"  OK {label}")
    return text.replace(old, new, 1)


def safe_write(path: Path, text: str) -> None:
    if not text.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name}: bad end before write")
    old_size = path.stat().st_size
    fd, tmp_name = tempfile.mkstemp(suffix=".html", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            tmp.write(text)
        check = Path(tmp_name).read_text(encoding="utf-8")
        if not check.rstrip().endswith("</html>"):
            raise SystemExit(f"{path.name}: temp lost </html>")
        new_size = Path(tmp_name).stat().st_size
        if new_size < old_size * 0.5:
            raise SystemExit(f"{path.name}: size drop {old_size} -> {new_size}")
        os.replace(tmp_name, path)
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)
        raise
    print(f"  wrote {path.name} bytes {new_size}")


def patch_html(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name}: no </html>")
    print(f"==== {path.name}")

    if f"/* {MARK}:" not in text:
        if CSS_ANCHOR not in text:
            raise SystemExit(f"{path.name}: no CSS anchor")
        text = text.replace(CSS_ANCHOR, CSS_ADD + CSS_ANCHOR, 1)
        print(f"  OK css-{MARK}")

    for old, new, label in (
        (SPACING_OLD, SPACING_NEW, "spacing-path"),
        (SPACING2_OLD, SPACING2_NEW, "spacing-patches"),
        (SPACING3_OLD, SPACING3_NEW, "spacing-search"),
        (HELPERS_OLD, HELPERS_NEW, "helpers"),
        (EQ_ROW_OLD, EQ_ROW_NEW, "eq-row"),
        (COLLAPSE_PATHS_OLD, COLLAPSE_PATHS_NEW, "collapse-paths"),
        (CLICK_OLD, CLICK_NEW, "path-click"),
        (BOOT_OLD, BOOT_NEW, "boot-bind"),
    ):
        text = once(text, old, new, label)

    if "function bindPortablePathHits" in text:
        text = once(text, PORT_BIND_OLD, PORT_BIND_NEW, "port-bind", required=False)

    if f"/* {MARK}:" not in text or "catalogCardHeightCube" not in text:
        raise SystemExit(f"VERIFY FAIL {path.name}")
    safe_write(path, text)


def lib_images(libdir: Path) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    if not libdir.is_dir():
        return out
    for root, _dirs, files in os.walk(libdir):
        if root.count(os.sep) - str(libdir).count(os.sep) > 3:
            continue
        for fn in files:
            if not IMG_EXT.search(fn) or SKIP_NAME.search(fn):
                continue
            p = os.path.join(root, fn)
            try:
                out.append((os.path.getsize(p), p))
            except OSError:
                pass
    return out


def cover_skip_name(path: str) -> bool:
    bn = os.path.basename(path).lower()
    return bool(BARE_BG.search(path) or "template_skin" in bn or bn.startswith("template"))


def pick_cover(imgs: list[tuple[int, str]]) -> str | None:
    if not imgs:
        return None
    cand = [(sz, p) for sz, p in imgs if not cover_skip_name(p)]
    if not cand:
        cand = list(imgs)

    def good_art(sz: int, path: str) -> bool:
        bn = os.path.basename(path).lower()
        if "_ds." in bn or bn.endswith("_ds.png"):
            return False
        if "template" in bn or "knob" in bn or "slider" in bn:
            return False
        return bool(re.search(r"piano|gaffer|cool|cover|artwork|photo", bn, re.I) or (IN_RES.search(path) and sz > 48000))

    art = [(sz, p) for sz, p in cand if good_art(sz, p)]
    if art:
        return max(art, key=lambda x: x[0])[1]

    pref = [(sz, p) for sz, p in cand if PREF_NAME.search(p) and "_ds." not in os.path.basename(p).lower()]
    if pref:
        return max(pref, key=lambda x: x[0])[1]

    res = [(sz, p) for sz, p in cand if IN_RES.search(p) and os.path.getsize(p) > 32768]
    if res:
        return max(res, key=lambda x: x[0])[1]
    return max(cand, key=lambda x: x[0])[1]


def emit_jpeg(src: str, height: int, quality: int) -> str | None:
    magick = shutil.which("magick") or shutil.which("convert")
    if not magick:
        return None
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "c.jpg")
        for args in ([src], [src + "[0]"]):
            cmd = [magick, *args, "-background", "white", "-flatten", "-resize", f"x{height}", "-quality", str(quality), out]
            r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if r.returncode == 0 and os.path.isfile(out) and os.path.getsize(out) >= 32:
                import base64

                return base64.b64encode(Path(out).read_bytes()).decode("ascii")
    return None


def patch_ds_piano_covers(path: Path, portable: bool) -> dict:
    text = path.read_text(encoding="utf-8")
    h, q = (110, 70) if portable else (160, 85)
    changed = []
    for name in DS_PIANO_IDS:
        lib = DS_LIB_ROOT / name
        pick = pick_cover(lib_images(lib))
        if not pick:
            print(f"  cover skip {name}: no image")
            continue
        new_b64 = emit_jpeg(pick, h, q)
        if not new_b64:
            print(f"  cover skip {name}: encode fail")
            continue
        pat = re.compile(
            rf'(<div class="entry"[^>]*data-name="{re.escape(name)}"[\s\S]*?'
            rf'<div class="cover"><img src="data:)([^;]+)(;base64,)([^"]+)(")',
            re.I,
        )
        m = pat.search(text)
        if not m:
            print(f"  cover skip {name}: entry not found")
            continue
        old_b64 = m.group(4)
        if old_b64 == new_b64 and len(old_b64) > 12000:
            print(f"  cover same {name}")
            continue
        text = pat.sub(rf"\1image/jpeg\3{new_b64}\5", text, count=1)
        changed.append({"name": name, "pick": os.path.basename(pick), "oldLen": len(old_b64), "newLen": len(new_b64)})
        print(f"  cover OK {name} <- {os.path.basename(pick)}")
    if changed:
        safe_write(path, text)
    return {"file": path.name, "changed": changed}


def main() -> None:
    for p in FILES:
        patch_html(p)
    for html, portable in (
        (ROOT / "public/catalogs/DS-CATALOG.html", False),
        (ROOT / "public/catalogs/DS-CATALOG-portable.html", True),
    ):
        print(f"==== covers {html.name}")
        patch_ds_piano_covers(html, portable)
    print("OK", MARK)


if __name__ == "__main__":
    main()
