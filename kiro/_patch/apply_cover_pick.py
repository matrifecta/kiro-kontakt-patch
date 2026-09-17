#!/usr/bin/env python3
"""Prefer unique cover/photo art over the stock Decent Sampler background.png skin.

Updates the DS builder picker, cover-census logs, and re-embeds live DS catalog covers.
Does not commit.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES_CENSUS = [
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-ds-catalog-html.sh",
    ROOT / "kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-kontakt-catalog-html.sh",
]
BUILD_DS = ROOT / "kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-ds-catalog-html.sh"
LOG = ROOT / ".cursor/debug-c00e3e.log"

IMG_EXT = re.compile(r"\.(png|jpe?g|gif|bmp|webp)$", re.I)
SKIP_NAME = re.compile(
    r"knob|dial|fader|slider|button|hover|switch|led|arrow|sprite|filmstrip|_anim|template_skin|blank_icon|macro",
    re.I,
)
PREF_NAME = re.compile(r"cover|artwork|(^|/)photo[._-]|_ds\.", re.I)
BG_NAMED = re.compile(r"(^|/)bg[_.-]|_bg\.", re.I)
BARE_BG = re.compile(r"(^|/)background\.(png|jpe?g|gif|webp|bmp)$", re.I)
IN_RES = re.compile(r"/(Images|Image|Resources|Samples)/", re.I)

PRIMARY_OLD = """# return cover image candidates in priority order; caller iterates until emit_cover succeeds.
# tier1=named cover/bg/artwork, tier2=Images/Resources dirs (largest first), tier3=rest (largest first).
# Extra exclusions: sprite|filmstrip|_anim catch UI animation strips missed by name alone.
primary_images(){ local d="$1" all
  all=$(find "$d" -maxdepth 3 -type f \\( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.gif' -o -iname '*.bmp' -o -iname '*.webp' \\) 2>/dev/null \\
        | grep -viE '/__MACOSX/|/\\._' | grep -viE 'knob|dial|fader|slider|button|hover|switch|led|arrow|sprite|filmstrip|_anim')
  printf '%s\\n' "$all" | grep -iE 'background|cover|artwork|(^|/)bg[_.-]|_bg\\.'
  printf '%s\\n' "$all" | grep -iE '/(Images|Image|Resources|Samples)/' | while IFS= read -r f; do
    printf '%s\\t%s\\n' "$(stat -c%s "$f" 2>/dev/null||echo 0)" "$f"; done | sort -rn | cut -f2-
  printf '%s\\n' "$all" | grep -viE '/(Images|Image|Resources|Samples)/' | \\
    grep -viE 'background|cover|artwork|(^|/)bg[_.-]|_bg\\.' | while IFS= read -r f; do
    printf '%s\\t%s\\n' "$(stat -c%s "$f" 2>/dev/null||echo 0)" "$f"; done | sort -rn | cut -f2-
}
"""

PRIMARY_NEW = """# return cover image candidates in priority order; caller iterates until emit_cover succeeds.
# Prefer named cover/artwork/photo/*_DS over a generic background.png (stock Decent Sampler piano-book skin).
# Extra exclusions: sprite|filmstrip|_anim|template_skin|blank_icon.
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
  printf '%s\\n' "$all" | grep -viE '/(Images|Image|Resources|Samples)/' | \\
    grep -viE 'cover|artwork|(^|/)photo[._-]|(^|/)bg[_.-]|_bg\\.|_ds\\.' | ranked
}
"""

CENSUS_LOOP_OLD = """    var n=0,withImg=0,naturalOk=0,boxOk=0,zeroBox=0,emptySrc=0,noCover=0,tiny=0,samples=[];
    document.querySelectorAll('.entry').forEach(function(el){
      n++;
      var img=el.querySelector(':scope > .cover > img')||el.querySelector('.cover > img');
      if(!img){noCover++;return;}
      withImg++;
      var src=img.getAttribute('src')||'';
      if(!src||src==='about:blank')emptySrc++;
      var nat=img.naturalWidth||0;
      if(nat>0)naturalOk++;
      var box=(img.parentElement||img).getBoundingClientRect();
      if(box.width>=8&&box.height>=8)boxOk++;
      else if(samples.length<6){zeroBox++;samples.push({id:el.id||'',w:Math.round(box.width),h:Math.round(box.height),nat:nat,src:(src||'').slice(0,28)});}
      else zeroBox++;
      if(nat>0&&box.width>=8&&box.height>0&&box.height<20)tiny++;
    });
"""

CENSUS_LOOP_NEW = """    var n=0,withImg=0,naturalOk=0,boxOk=0,zeroBox=0,emptySrc=0,noCover=0,tiny=0,samples=[];
    var clipped=0,tinySrc=0,dupMax=0,srcHash={};
    document.querySelectorAll('.entry').forEach(function(el){
      n++;
      var img=el.querySelector(':scope > .cover > img')||el.querySelector('.cover > img');
      if(!img){noCover++;return;}
      withImg++;
      var src=img.getAttribute('src')||'';
      if(!src||src==='about:blank')emptySrc++;
      var nat=img.naturalWidth||0;
      if(nat>0)naturalOk++;
      var box=(img.parentElement||img).getBoundingClientRect();
      var er=el.getBoundingClientRect();
      if(box.width>=8&&box.height>=8){
        boxOk++;
        if(box.bottom<er.top+2||box.top>er.bottom-2)clipped++;
      } else if(samples.length<6){zeroBox++;samples.push({id:el.id||'',name:(el.getAttribute('data-name')||'').slice(0,40),w:Math.round(box.width),h:Math.round(box.height),nat:nat,srcLen:(src||'').length});}
      else zeroBox++;
      if(nat>0&&box.width>=8&&box.height>0&&box.height<20)tiny++;
      if(src&&src.length<3600)tinySrc++;
      var hk=(src||'').length+':'+(src||'').slice(80,140);
      if(src){srcHash[hk]=(srcHash[hk]||0)+1;if(srcHash[hk]>dupMax)dupMax=srcHash[hk];}
    });
    var uiScale=0;try{uiScale=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--ui-scale'))||0;}catch(eSc){}
"""

CENSUS_DATA_OLD = "data:{phase:String(phase||''),n:n,withImg:withImg,naturalOk:naturalOk,boxOk:boxOk,zeroBox:zeroBox,emptySrc:emptySrc,noCover:noCover,tiny:tiny,revived:extra.revived||0,boxFix:extra.boxFix||0,samples:samples,mode:document.body.classList.contains('display-middle')?'middle':(document.body.classList.contains('display-sides')?'sides':'other'),vw:window.innerWidth||0}"
CENSUS_DATA_NEW = "data:{phase:String(phase||''),n:n,withImg:withImg,naturalOk:naturalOk,boxOk:boxOk,zeroBox:zeroBox,emptySrc:emptySrc,noCover:noCover,tiny:tiny,clipped:clipped,tinySrc:tinySrc,dupMax:dupMax,uiScale:uiScale,revived:extra.revived||0,boxFix:extra.boxFix||0,samples:samples,mode:document.body.classList.contains('display-middle')?'middle':(document.body.classList.contains('display-sides')?'sides':'other'),vw:window.innerWidth||0}"


def log_line(msg, data, hyp="H-C"):
    import json, time
    rec = {
        "sessionId": "c00e3e",
        "runId": "post-fix",
        "hypothesisId": hyp,
        "location": "apply_cover_pick.py",
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


def lib_images(d: str):
    out = []
    if not os.path.isdir(d):
        return out
    for root, dirs, files in os.walk(d):
        rel = os.path.relpath(root, d)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        if depth > 3:
            dirs[:] = []
            continue
        dirs[:] = [x for x in dirs if x not in ("__MACOSX",) and not x.startswith(".")]
        if "__MACOSX" in root.split(os.sep):
            continue
        for fn in files:
            if fn.startswith("._") or not IMG_EXT.search(fn) or SKIP_NAME.search(fn):
                continue
            p = os.path.join(root, fn)
            try:
                sz = os.path.getsize(p)
            except OSError:
                continue
            out.append((sz, p))
    return out


def ranked(paths_with_size):
    return [p for sz, p in sorted(paths_with_size, key=lambda x: -x[0])]


def image_size(path: str):
    try:
        with open(path, "rb") as f:
            head = f.read(24)
            if head.startswith(b"\x89PNG\r\n\x1a\n") and len(head) >= 24:
                return struct.unpack(">II", head[16:24])
            if head[:6] in (b"GIF87a", b"GIF89a") and len(head) >= 10:
                return struct.unpack("<HH", head[6:10])
            if head[:2] == b"BM":
                f.seek(14)
                dib = f.read(16)
                if len(dib) >= 12:
                    hdr = struct.unpack_from("<I", dib)[0]
                    if hdr == 12:
                        return struct.unpack_from("<HH", dib, 4)
                    w, h = struct.unpack_from("<ii", dib, 4)
                    return w, abs(h)
            if head[:2] == b"\xff\xd8":
                f.seek(2)
                while True:
                    b = f.read(4)
                    if len(b) < 4 or b[0] != 0xFF:
                        break
                    marker, seglen = b[1], struct.unpack(">H", b[2:4])[0]
                    if seglen < 2:
                        break
                    if marker in (0xC0, 0xC1, 0xC2, 0xC3):
                        sof = f.read(seglen - 2)
                        if len(sof) >= 5:
                            h, w = struct.unpack(">HH", sof[1:5])
                            return w, h
                        break
                    f.seek(seglen - 2, os.SEEK_CUR)
    except OSError:
        return None
    try:
        r = subprocess.run(
            ["identify", "-format", "%w %h", path],
            capture_output=True,
            text=True,
            timeout=6,
        )
        if r.returncode == 0:
            parts = r.stdout.split()
            if len(parts) >= 2:
                return int(parts[0]), int(parts[1])
    except Exception:
        return None
    return None


def is_ui_strip(path: str) -> bool:
    wh = image_size(path)
    if not wh:
        return False
    w, h = wh
    if w < 32 or h < 32:
        return True
    return max(w, h) / min(w, h) >= 4.0


def pick_cover(imgs):
    if not imgs:
        return None
    imgs = [(sz, p) for sz, p in imgs if not is_ui_strip(p)]
    if not imgs:
        return None
    pref = [(sz, p) for sz, p in imgs if PREF_NAME.search(p)]
    if pref:
        return ranked(pref)[0]
    bg = [(sz, p) for sz, p in imgs if BG_NAMED.search(p) and not BARE_BG.search(p)]
    if bg:
        return ranked(bg)[0]
    res = []
    for sz, p in imgs:
        if not IN_RES.search(p):
            continue
        bn = os.path.basename(p)
        if re.match(r"^background\.(png|jpe?g|gif|webp|bmp)$", bn, re.I) and sz < 32768:
            continue
        res.append((sz, p))
    if res:
        return ranked(res)[0]
    rest = [
        (sz, p)
        for sz, p in imgs
        if not IN_RES.search(p)
        and not PREF_NAME.search(p)
        and not BG_NAMED.search(p)
    ]
    if rest:
        return ranked(rest)[0]
    return ranked(imgs)[0]


def emit_jpeg(src: str, height: int, quality: int) -> str | None:
    magick = shutil.which("magick") or shutil.which("convert")
    if not magick:
        return None
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "c.jpg")
        cmd = [magick, src, "-background", "white", "-flatten", "-resize", f"x{height}", "-quality", str(quality), out]
        r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode != 0 or not os.path.isfile(out):
            cmd = [magick, src + "[0]", "-background", "white", "-flatten", "-resize", f"x{height}", "-quality", str(quality), out]
            r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode != 0 or not os.path.isfile(out) or os.path.getsize(out) < 32:
            return None
        if is_ui_strip(out):
            return None
        import base64
        return base64.b64encode(Path(out).read_bytes()).decode("ascii")


def libdir_from_path(code: str) -> str | None:
    code = code.strip()
    for marker in ("/DS Libraries/", "/DS Libraries\\"):
        if marker in code:
            rest = code.split(marker, 1)[1]
            first = rest.split("/")[0].split("\\")[0]
            root = code[: code.index(marker)] + "/DS Libraries/" + first
            return root
    if os.path.isfile(code):
        return os.path.dirname(code)
    if os.path.isdir(code):
        return code
    return None


COVER_RE = re.compile(
    r'(<div class="entry" id="(item-\d+)"[^>]*data-name="([^"]+)"[\s\S]*?'
    r'<div class="cover"><img src="data:)([^;]+)(;base64,)([^"]+)("[\s\S]*?'
    r'<div class="path"><b>open:</b> <code>)([^<]+)(</code>)',
    re.I,
)


def recode_html(path: Path, portable: bool) -> dict:
    text = path.read_text(encoding="utf-8")
    h, q = (110, 70) if portable else (160, 85)
    changed = 0
    skipped = 0
    samples = []

    def repl(m):
        nonlocal changed, skipped
        name = m.group(3).replace("&amp;", "&")
        old_b64 = m.group(6)
        code = m.group(8).replace("&amp;", "&")
        lib = libdir_from_path(code)
        if not lib:
            skipped += 1
            return m.group(0)
        imgs = lib_images(lib)
        pick = pick_cover(imgs)
        if not pick:
            skipped += 1
            return m.group(0)
        new_b64 = emit_jpeg(pick, h, q)
        if not new_b64:
            skipped += 1
            return m.group(0)
        if new_b64 == old_b64:
            return m.group(0)
        changed += 1
        if len(samples) < 12:
            samples.append(
                {
                    "name": name[:60],
                    "pick": os.path.basename(pick),
                    "oldLen": len(old_b64),
                    "newLen": len(new_b64),
                }
            )
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
    t = sub(t, PRIMARY_OLD, PRIMARY_NEW, "primary_images", BUILD_DS)
    BUILD_DS.write_text(t, encoding="utf-8")
    print("updated primary_images")

    for p in FILES_CENSUS:
        txt = p.read_text(encoding="utf-8")
        txt = sub(txt, CENSUS_LOOP_OLD, CENSUS_LOOP_NEW, "census-loop", p)
        txt = sub(txt, CENSUS_DATA_OLD, CENSUS_DATA_NEW, "census-data", p)
        p.write_text(txt, encoding="utf-8")
        print("census", p.name)

    patcher = ROOT / "kiro/_patch/apply_save_covers_index.py"
    if patcher.exists():
        pt = patcher.read_text(encoding="utf-8")
        if CENSUS_LOOP_OLD in pt:
            pt = pt.replace(CENSUS_LOOP_OLD, CENSUS_LOOP_NEW, 1)
            pt = pt.replace(CENSUS_DATA_OLD, CENSUS_DATA_NEW, 1)
            patcher.write_text(pt, encoding="utf-8")
            print("census patcher")

    results = []
    for html, portable in (
        (ROOT / "public/catalogs/DS-CATALOG.html", False),
        (ROOT / "public/catalogs/DS-CATALOG-portable.html", True),
    ):
        print("recode", html.name, "...")
        r = recode_html(html, portable)
        print(r["changed"], "covers replaced,", r["skipped"], "skipped,", r["matches"], "entries")
        results.append(r)
        log_line("cover-recode", r)

    # artifact copies used by the builder output dir if present
    for html, portable in (
        (ROOT / "kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/DS-CATALOG.html", False),
        (ROOT / "kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/DS-CATALOG-portable.html", True),
    ):
        if html.exists() and html.stat().st_size > 100000:
            print("recode", html.name, "artifact ...")
            r = recode_html(html, portable)
            print(r["changed"], "covers replaced")
            results.append(r)

    log_line("cover-recode-done", {"results": [{"file": x["file"], "changed": x["changed"]} for x in results]})


if __name__ == "__main__":
    main()
