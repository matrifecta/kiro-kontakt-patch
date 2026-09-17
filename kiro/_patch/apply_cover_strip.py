#!/usr/bin/env python3
"""Skip UI filmstrips so covers are not 1px-wide left-edge stripes.

Updates the DS builder picker, stripe logs, and re-embeds live DS covers.
Does not commit.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
sys.path.insert(0, str(ROOT / "kiro/_patch"))
from apply_cover_pick import (  # noqa: E402
    BUILD_DS,
    COVER_RE,
    FILES_CENSUS,
    LOG,
    emit_jpeg,
    image_size,
    lib_images,
    libdir_from_path,
    pick_cover,
)

PRIMARY_CUR = """# Extra exclusions: sprite|filmstrip|_anim|template_skin|blank_icon.
primary_images(){ local d="$1" all
  all=$(find "$d" -maxdepth 3 -type f \\( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.gif' -o -iname '*.bmp' -o -iname '*.webp' \\) 2>/dev/null \\
        | grep -viE '/__MACOSX/|/\\._' | grep -viE 'knob|dial|fader|slider|button|hover|switch|led|arrow|sprite|filmstrip|_anim|template_skin|blank_icon')
  ranked(){ while IFS= read -r f; do [ -n "$f" ] && [ -f "$f" ] && printf '%s\\t%s\\n' "$(stat -c%s "$f" 2>/dev/null||echo 0)" "$f"; done | sort -rn | cut -f2-; }
  printf '%s\\n' "$all" | grep -iE 'cover|artwork|(^|/)photo[._-]|_ds\\.' | ranked
  printf '%s\\n' "$all" | grep -iE '(^|/)bg[_.-]|_bg\\.' | grep -viE '(^|/)background\\.(png|jpe?g|gif|webp|bmp)$' | ranked
  printf '%s\\n' "$all" | grep -iE '/(Images|Image|Resources|Samples)/' | while IFS= read -r f; do
    bn=$(basename "$f"); sz=$(stat -c%s "$f" 2>/dev/null||echo 0)
    printf '%s' "$bn" | grep -qiE '^background\\.(png|jpe?g|gif|webp|bmp)$' && [ "$sz" -lt 32768 ] && continue
    printf '%s\\t%s\\n' "$sz" "$f"
  done | sort -rn | cut -f2-
"""

PRIMARY_NEXT = """# Extra exclusions: sprite|filmstrip|_anim|template_skin|blank_icon|macro.
# Skip UI filmstrips (extreme aspect) so a 125x16000 macro does not beat wallpaper.
primary_images(){ local d="$1" all
  all=$(find "$d" -maxdepth 3 -type f \\( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.gif' -o -iname '*.bmp' -o -iname '*.webp' \\) 2>/dev/null \\
        | grep -viE '/__MACOSX/|/\\._' | grep -viE 'knob|dial|fader|slider|button|hover|switch|led|arrow|sprite|filmstrip|_anim|template_skin|blank_icon|macro')
  usable_img(){ local f="$1" w h; read -r w h < <(identify -format '%w %h' "$f" 2>/dev/null)
    [ -n "${w:-}" ] && [ -n "${h:-}" ] || return 0
    [ "$w" -ge 32 ] && [ "$h" -ge 32 ] || return 1
    if [ "$w" -ge "$h" ]; then [ "$w" -lt $((h * 4)) ]; else [ "$h" -lt $((w * 4)) ]; fi; }
  ranked(){ while IFS= read -r f; do [ -n "$f" ] && [ -f "$f" ] || continue; usable_img "$f" || continue
    printf '%s\\t%s\\n' "$(stat -c%s "$f" 2>/dev/null||echo 0)" "$f"; done | sort -rn | cut -f2-; }
  printf '%s\\n' "$all" | grep -iE 'cover|artwork|(^|/)photo[._-]|_ds\\.' | ranked
  printf '%s\\n' "$all" | grep -iE '(^|/)bg[_.-]|_bg\\.' | grep -viE '(^|/)background\\.(png|jpe?g|gif|webp|bmp)$' | ranked
  printf '%s\\n' "$all" | grep -iE '/(Images|Image|Resources|Samples)/' | while IFS= read -r f; do
    bn=$(basename "$f"); sz=$(stat -c%s "$f" 2>/dev/null||echo 0)
    printf '%s' "$bn" | grep -qiE '^background\\.(png|jpe?g|gif|webp|bmp)$' && [ "$sz" -lt 32768 ] && continue
    usable_img "$f" || continue
    printf '%s\\t%s\\n' "$sz" "$f"
  done | sort -rn | cut -f2-
"""

STRIPE_FN = r"""function dbgCoverStripe(phase){
  // #region agent log
  try{
    var stripes=[],n=0;
    document.querySelectorAll('.entry .cover > img').forEach(function(img){
      n++;
      var ir=img.getBoundingClientRect(), box=(img.parentElement||img).getBoundingClientRect();
      var nw=img.naturalWidth||0, nh=img.naturalHeight||0;
      var ar=(nw>0&&nh>0)?(Math.max(nw,nh)/Math.min(nw,nh)):0;
      var skinnyNat=nw>0&&(nw<24||ar>=4);
      var skinnyBox=ir.width>0&&ir.width<24&&ir.height>=40;
      var leftEdge=ir.width>0&&(ir.left-box.left)<8&&ir.width<box.width*0.2&&box.width>=80;
      if(skinnyNat||skinnyBox||leftEdge){
        var el=img.closest('.entry');
        stripes.push({id:el&&el.id||'',name:el?(el.getAttribute('data-name')||'').slice(0,48):'',nw:nw,nh:nh,iw:Math.round(ir.width),ih:Math.round(ir.height),cw:Math.round(box.width),left:Math.round(ir.left-box.left),why:skinnyNat?'nat':(skinnyBox?'box':'left')});
      }
    });
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'H-S1',location:'catalog:dbgCoverStripe',message:'cover-stripe',data:{phase:String(phase||''),n:n,stripe:stripes.length,stripes:stripes.slice(0,12),mode:document.body.classList.contains('display-middle')?'middle':(document.body.classList.contains('display-sides')?'sides':'other')},timestamp:Date.now()})}).catch(function(){});
  }catch(eStripe){}
  // #endregion
}
"""

WIN_OLD = "window.dbgCoverCensus=dbgCoverCensus;\nwindow.reviveEntryCovers=reviveEntryCovers;"
WIN_NEW = (
    STRIPE_FN
    + "window.dbgCoverCensus=dbgCoverCensus;\nwindow.dbgCoverStripe=dbgCoverStripe;\nwindow.reviveEntryCovers=reviveEntryCovers;"
)
CALL_OLD = "  if(typeof dbgCoverCensus==='function')dbgCoverCensus(phase||'revive',{revived:revived,boxFix:boxFix});\n}"
CALL_NEW = (
    "  if(typeof dbgCoverCensus==='function')dbgCoverCensus(phase||'revive',{revived:revived,boxFix:boxFix});\n"
    "  if(typeof dbgCoverStripe==='function')dbgCoverStripe(phase||'revive');\n}"
)


def log_line(msg, data, hyp="H-S1"):
    rec = {
        "sessionId": "c00e3e",
        "runId": "post-fix",
        "hypothesisId": hyp,
        "location": "apply_cover_strip.py",
        "message": msg,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def sub(text, old, new, label, path):
    if new in text and old not in text:
        print(f"  skip {path.name} {label}")
        return text
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{path.name}: {label} count={n} expected 1")
    return text.replace(old, new, 1)


def embedded_is_strip(b64: str) -> bool:
    try:
        raw = base64.b64decode(b64, validate=False)
    except Exception:
        return False
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=True) as tmp:
        tmp.write(raw)
        tmp.flush()
        wh = image_size(tmp.name)
    if not wh:
        return False
    w, h = wh
    if w < 24 or h < 24:
        return True
    return max(w, h) / min(w, h) >= 4.0


def recode_skinny(path: Path, portable: bool) -> dict:
    text = path.read_text(encoding="utf-8")
    h, q = (110, 70) if portable else (160, 85)
    changed = 0
    skipped = 0
    samples = []

    def repl(m):
        nonlocal changed, skipped
        name = m.group(3).replace("&amp;", "&")
        old_b64 = m.group(6)
        if not embedded_is_strip(old_b64):
            return m.group(0)
        code = m.group(8).replace("&amp;", "&")
        lib = libdir_from_path(code)
        if not lib:
            skipped += 1
            return m.group(0)
        pick = pick_cover(lib_images(lib))
        if not pick:
            skipped += 1
            return m.group(0)
        new_b64 = emit_jpeg(pick, h, q)
        if not new_b64:
            skipped += 1
            return m.group(0)
        changed += 1
        samples.append({"name": name[:60], "pick": os.path.basename(pick), "newLen": len(new_b64)})
        return (
            m.group(1)
            + "image/jpeg"
            + m.group(5)
            + new_b64
            + m.group(7)
            + m.group(8)
            + m.group(9)
        )

    new_text, nsub = COVER_RE.subn(repl, text)
    path.write_text(new_text, encoding="utf-8")
    return {"file": path.name, "matches": nsub, "changed": changed, "skipped": skipped, "samples": samples}


def main():
    t = BUILD_DS.read_text(encoding="utf-8")
    if PRIMARY_CUR in t:
        BUILD_DS.write_text(t.replace(PRIMARY_CUR, PRIMARY_NEXT, 1), encoding="utf-8")
        print("updated builder primary_images")
    elif PRIMARY_NEXT in t:
        print("builder already updated")
    else:
        raise SystemExit("builder primary_images block not found")

    for p in FILES_CENSUS:
        txt = p.read_text(encoding="utf-8")
        txt = sub(txt, CALL_OLD, CALL_NEW, "stripe-call", p)
        txt = sub(txt, WIN_OLD, WIN_NEW, "stripe-fn", p)
        p.write_text(txt, encoding="utf-8")
        print("stripe log", p.name)

    skinny_before = [
        "CH Foogered Piano DS",
        "CH Grumpy Strings DS",
        "CH Octodrums DS",
        "curly - electric piano",
        "LØ - Fragile Violins Free",
        "OOTG Piano DS",
        "syntheticstrings",
        "The-Viking-Log-Lyre",
        "IMPACTOS HYBRID PERCUSSION",
    ]
    picks = []
    codes = {
        "CH Foogered Piano DS": "/mnt/btrfs_disk/DS Libraries/CH Foogered Piano DS/CH Foogered Piano DS/CH Foogered Piano.dspreset",
        "CH Grumpy Strings DS": "/mnt/btrfs_disk/DS Libraries/CH Grumpy Strings DS/CH Grumpy Strings.dspreset",
        "CH Octodrums DS": "/mnt/btrfs_disk/DS Libraries/CH Octodrums DS/CH Octodrums.dspreset",
        "curly - electric piano": "/mnt/btrfs_disk/DS Libraries/curly - electric piano/curly - electric piano/curly-electric-piano.dspreset",
        "LØ - Fragile Violins Free": "/mnt/btrfs_disk/DS Libraries/LØ - Fragile Violins Free/LØ - Fragile Violins Free/LØ - Fragile Violins - Free.dspreset",
        "OOTG Piano DS": "/mnt/btrfs_disk/DS Libraries/OOTG Piano DS/OOTG Piano.dspreset",
        "syntheticstrings": "/mnt/btrfs_disk/DS Libraries/syntheticstrings/syntheticstrings/syntheticstrings.dspreset",
        "The-Viking-Log-Lyre": "/mnt/btrfs_disk/DS Libraries/The-Viking-Log-Lyre/The-Viking-Log-Lyre.dspreset",
        "IMPACTOS HYBRID PERCUSSION": "/mnt/wd_black/DS Libraries/IMPACTOS HYBRID PERCUSSION/IMPACTOS HYBRID PERCUSSION/ENSEMBLE.dspreset",
    }
    for name in skinny_before:
        lib = libdir_from_path(codes[name])
        pick = pick_cover(lib_images(lib)) if lib else None
        picks.append({"name": name, "pick": os.path.basename(pick) if pick else None, "path": pick})
        print("pick", name, "->", pick)
    log_line("stripe-picks", {"picks": picks})

    results = []
    for html, portable in (
        (ROOT / "public/catalogs/DS-CATALOG.html", False),
        (ROOT / "public/catalogs/DS-CATALOG-portable.html", True),
    ):
        print("recode-skinny", html.name, "...")
        r = recode_skinny(html, portable)
        print(r["changed"], "skinny covers replaced,", r["skipped"], "skipped,", r["matches"], "entries")
        results.append(r)
        log_line("cover-recode-strip", r)

    log_line("cover-strip-done", {"changed": [x["changed"] for x in results], "picks": picks})


if __name__ == "__main__":
    main()
