#!/usr/bin/env python3
"""Default collapsed path (in-card expand then overlay); wheel-forward to catalog scroller."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG.html",
    ROOT / "DS-CATALOG.html",
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]

CSS_MARK = "/* fix-DOC-NOTE-DOCK: About/Document pinned to content-pane bottom; cards scroll above */"
CSS_ADD = r"""/* fix-PATH-COLLAPSE: one-line path by default; click expands in-card then overlay */
.entry .path{
  cursor:pointer;box-sizing:border-box;min-width:0;
  margin:.4rem 0 .9rem!important
}
.entry .path:not(.is-expanded){
  display:flex!important;flex-wrap:nowrap!important;align-items:center!important;
  gap:.95rem;height:2.75em!important;min-height:2.75em!important;max-height:2.75em!important;
  overflow:hidden!important;white-space:nowrap!important
}
.entry .path:not(.is-expanded) code{
  display:inline-block!important;flex:1 1 auto;min-width:0;max-width:100%;
  overflow:hidden!important;text-overflow:ellipsis!important;white-space:nowrap!important;
  word-break:normal!important;overflow-wrap:normal!important
}
.entry .path .folder,
.entry .path .path-fs-hit{
  flex:0 0 auto;white-space:nowrap;display:inline-block;
  margin-left:.15rem;padding:.35rem .65rem;box-sizing:border-box
}
.entry .path.is-expanded{
  display:block!important;height:auto!important;min-height:0!important;max-height:none!important;
  overflow:visible!important;white-space:normal!important;flex-wrap:wrap!important
}
.entry .path.is-expanded code{
  display:inline!important;white-space:normal!important;overflow:visible!important;
  word-break:break-word!important;overflow-wrap:anywhere!important;text-overflow:clip!important
}
.entry.selected:not(.highlight) .path:not(.is-expanded),
.entry.highlight .path:not(.is-expanded),
body.chosen-preview-open .entry.selected:not(.highlight) .path:not(.is-expanded){
  height:2.75em!important;min-height:2.75em!important;max-height:2.75em!important;
  overflow:hidden!important;white-space:nowrap!important
}
.entry.selected:not(.highlight) .path.is-expanded,
.entry.highlight .path.is-expanded,
body.chosen-preview-open .entry.selected:not(.highlight) .path.is-expanded{
  height:auto!important;min-height:0!important;max-height:none!important;
  overflow:visible!important;white-space:normal!important
}
.entry details.patches,
.entry .patches{
  margin-bottom:.55rem!important;padding-top:.55rem
}
.entry:not(.highlight) details.patches,
.entry:not(.highlight) .patches{
  margin-top:auto;padding-top:.75rem;margin-bottom:.45rem!important
}
.entry .patches>summary{
  display:inline-block;padding:.45rem .25rem .55rem;min-height:2.2rem;box-sizing:border-box
}
.entry .card-actions,
.entry:not(.highlight) .card-actions{
  margin-top:.95rem!important;padding-top:.55rem
}
.entry .card-actions .search-popup-btn{margin-top:.15rem}
body.chosen-preview-open .entry.selected:not(.highlight) .path{margin:.65rem 0 1rem!important}
body.chosen-preview-open .entry.selected:not(.highlight) details.patches,
body.chosen-preview-open .entry.selected:not(.highlight) .patches{
  margin-top:1rem!important;margin-bottom:.55rem!important;padding-top:.4rem
}
body.chosen-preview-open .entry.selected:not(.highlight) .card-actions{
  margin-top:1.05rem!important;padding-top:.7rem!important
}

"""

SEL_PATH_OLD = ".entry.selected:not(.highlight) .path{max-height:none;overflow:hidden;overscroll-behavior:auto;touch-action:auto}"
SEL_PATH_NEW = ".entry.selected:not(.highlight) .path:not(.is-expanded){height:2.75em;max-height:2.75em;overflow:hidden;overscroll-behavior:auto;touch-action:auto}.entry.selected:not(.highlight) .path.is-expanded{max-height:none;overflow:visible}"

PREV_PATH_OLD = """body.chosen-preview-open .entry.selected:not(.highlight) .path{
  overflow:hidden!important;max-height:none!important
}"""
PREV_PATH_NEW = """body.chosen-preview-open .entry.selected:not(.highlight) .path:not(.is-expanded){
  overflow:hidden!important;max-height:2.75em!important
}
body.chosen-preview-open .entry.selected:not(.highlight) .path.is-expanded{
  overflow:visible!important;max-height:none!important
}"""

PORT_HIDE_OLD = "  body.catalog-portable .entry .path.is-collapsed code{display:none!important}"
PORT_HIDE_NEW = "  body.catalog-portable .entry .path:not(.is-expanded) code{display:inline-block!important;overflow:hidden!important;text-overflow:ellipsis!important;white-space:nowrap!important}"

PORT_EXPAND_OLD = "  body.catalog-portable .entry .path:not(.is-collapsed){flex-direction:column;align-items:flex-start}"
PORT_EXPAND_NEW = "  body.catalog-portable .entry .path.is-expanded{flex-direction:column;align-items:flex-start;display:flex!important}"

CLICK_DESK_OLD = "    if(e.target.closest('.path')){activatePath(entry);return;}"
CLICK_PATH = """    if(e.target.closest('.path')){
      var pathBox=e.target.closest('.path');
      if(e.target.closest('.path-fs-hit')){activatePath(entry);return;}
      if(!pathBox.classList.contains('is-expanded')){
        pathBox.classList.add('is-expanded');
        pathBox.classList.remove('is-collapsed');
        pathBox.setAttribute('aria-expanded','true');
        if(typeof scheduleEqualizeCardRows==='function')scheduleEqualizeCardRows();
        e.preventDefault();e.stopPropagation();return;
      }
      activatePath(entry);return;
    }"""

CLICK_PORT_OLD = """    if(e.target.closest('.path')){
      var pathBox=e.target.closest('.path');
      if(e.target.closest('.path-open-hit')||(e.target.closest('b')&&!e.target.closest('.path-fs-hit'))){
        pathBox.classList.toggle('is-collapsed');
        // #region agent log
        fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'H-PATH1',location:'catalog:path-open',message:'path-toggle',data:{collapsed:pathBox.classList.contains('is-collapsed')},timestamp:Date.now()})}).catch(function(){});
        // #endregion
        e.preventDefault();e.stopPropagation();return;
      }
      activatePath(entry);return;
    }"""

BIND_OLD = "    if(b){b.classList.add('path-open-hit');if(!/open/i.test((b.textContent||'').replace(/:$/,'')))b.textContent='open';}"
BIND_NEW = "    if(b)b.classList.add('path-open-hit');if(!p.classList.contains('is-expanded')){p.setAttribute('aria-expanded','false');}"

WHEEL1_OLD = """document.addEventListener('wheel',function(e){
  if(e.ctrlKey)return;
  var b=document.body.classList;
  if(b.contains('chosen-preview-open')||b.contains('hl-open')||b.contains('desc-focus-open')||b.contains('path-focus-open')||b.contains('gallery-open')||b.contains('img-focus-open'))return;
  var ent=e.target.closest&&e.target.closest('.entry.selected:not(.highlight)');
  if(!ent)return;
  if(!e.target.closest('.summary-panel,.path'))return;
  var sc=catalogScrollEl();
  if(!sc)return;
  sc.scrollTop+=e.deltaY;
  e.preventDefault();
},{passive:false});"""

WHEEL1_NEW = """function catalogWheelDeltaPx(e){
  var dy=e.deltaY;
  if(e.deltaMode===1)dy*=16;
  else if(e.deltaMode===2)dy*=window.innerHeight||400;
  return dy;
}
function catalogPickWheelScroller(){
  var main=document.getElementById('catalogMain');
  var body=document.querySelector('#catalogMain > .catalog-body');
  function can(el){
    if(!el)return false;
    var oy=getComputedStyle(el).overflowY;
    if(oy!=='auto'&&oy!=='scroll'&&oy!=='overlay')return false;
    return el.scrollHeight>el.clientHeight+1;
  }
  if(can(body))return body;
  if(can(main))return main;
  if(typeof catalogContentScroller==='function'){
    var c=catalogContentScroller();
    if(can(c))return c;
  }
  if(body){
    var oy=getComputedStyle(body).overflowY;
    if(oy==='auto'||oy==='scroll'||oy==='overlay')return body;
  }
  return main||body;
}
function catalogApplyWheel(el,dy){
  if(!el||!dy)return false;
  var max=el.scrollHeight-el.clientHeight;
  if(max<=1)return false;
  var before=el.scrollTop;
  if(dy<0&&before<=1)return false;
  if(dy>0&&before>=max-1)return false;
  el.scrollTop=before+dy;
  return el.scrollTop!==before;
}
function catalogInnerWheelEl(field){
  if(!field)return null;
  var path=field.classList.contains('path')?field:field.closest('.path');
  if(path&&path.classList.contains('is-expanded')){
    var oy=getComputedStyle(path).overflowY;
    if((oy==='auto'||oy==='scroll'||oy==='overlay')&&path.scrollHeight>path.clientHeight+1)return path;
  }
  var panel=field.classList.contains('summary-panel')?field:field.closest('.summary-panel');
  if(!panel)return null;
  var oy2=getComputedStyle(panel).overflowY;
  if(oy2!=='auto'&&oy2!=='scroll'&&oy2!=='overlay')return null;
  if(panel.scrollHeight<=panel.clientHeight+1)return null;
  return panel;
}
document.addEventListener('wheel',function(e){
  if(e.ctrlKey)return;
  var field=e.target.closest&&e.target.closest('.summary-panel,.summary-panel .desc,.path');
  if(!field)return;
  var ent=field.closest('.entry');
  if(!ent||!ent.classList.contains('selected'))return;
  var b=document.body.classList;
  if(b.contains('desc-focus-open')||b.contains('path-focus-open')||b.contains('gallery-open')||b.contains('img-focus-open')||b.contains('desc-reader-open')||b.contains('path-reader-open'))return;
  var dy=catalogWheelDeltaPx(e);
  var preview=b.contains('chosen-preview-open');
  var hl=ent.classList.contains('highlight')||b.contains('hl-open');
  if(preview||hl){
    var inner=catalogInnerWheelEl(field);
    if(inner&&catalogApplyWheel(inner,dy)){e.preventDefault();return;}
    var overlay=hl?(ent.querySelector('.hl-body')||ent):ent;
    if(catalogApplyWheel(overlay,dy)){e.preventDefault();return;}
    return;
  }
  var sc=catalogPickWheelScroller();
  if(!sc)return;
  var before=sc.scrollTop;
  sc.scrollTop=before+dy;
  if(sc.scrollTop!==before)e.preventDefault();
},{passive:false});"""

WHEEL2_OLD = """document.addEventListener('wheel',function(e){
  var field=e.target.closest&&e.target.closest('.summary-panel,.summary-panel .desc');
  if(!field)return;
  var ent=field.closest('.entry');
  if(!ent||!ent.classList.contains('selected'))return;
  var panel=field.classList&&field.classList.contains('summary-panel')?field:field.closest('.summary-panel');
  if(!panel)return;
  var max=panel.scrollHeight-panel.clientHeight;
  if(max<=1)return;
  var dy=e.deltaY;
  var atTop=panel.scrollTop<=1&&dy<0;
  var atBot=panel.scrollTop>=max-1&&dy>0;
  if(!atTop&&!atBot){e.stopPropagation();return;}
  if(document.body.classList.contains('chosen-preview-open')||ent.classList.contains('highlight'))return;
  var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||(typeof catalogScrollEl==='function'&&catalogScrollEl());
  if(!sc)return;
  sc.scrollTop+=dy;
  e.preventDefault();
},{passive:false});"""


def sub(text, old, new, label, required=True, replace_all=False):
    n = text.count(old)
    if n == 0:
        if new in text or (replace_all and "fix-PATH-COLLAPSE" in text and label.startswith("css")):
            print(f"  skip {label}")
            return text
        if required:
            raise SystemExit(f"missing {label}")
        print(f"  skip {label} (optional)")
        return text
    if not replace_all and n != 1:
        raise SystemExit(f"{label} count={n}")
    return text.replace(old, new) if replace_all else text.replace(old, new, 1)


def patch_one(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name} does not end with </html>")
    if "/* fix-PATH-COLLAPSE:" not in text:
        if CSS_MARK not in text:
            raise SystemExit(f"{path.name} missing CSS_MARK")
        text = text.replace(CSS_MARK, CSS_ADD + CSS_MARK, 1)
        print(f"  css {path.name}")
    else:
        print(f"  skip css {path.name}")
    text = sub(text, SEL_PATH_OLD, SEL_PATH_NEW, "sel-path", replace_all=True)
    text = sub(text, PREV_PATH_OLD, PREV_PATH_NEW, "preview-path")
    text = sub(text, PORT_HIDE_OLD, PORT_HIDE_NEW, "port-hide", required=False)
    text = sub(text, PORT_EXPAND_OLD, PORT_EXPAND_NEW, "port-expand", required=False)
    if CLICK_DESK_OLD in text:
        text = sub(text, CLICK_DESK_OLD, CLICK_PATH, "desk-click")
    elif CLICK_PORT_OLD in text:
        text = sub(text, CLICK_PORT_OLD, CLICK_PATH, "port-click")
    elif "pathBox.classList.add('is-expanded')" in text:
        print("  skip click")
    else:
        raise SystemExit(f"{path.name} missing path click")
    text = sub(text, BIND_OLD, BIND_NEW, "bind-open", required=False)
    if WHEEL1_OLD in text:
        text = sub(text, WHEEL1_OLD, WHEEL1_NEW, "wheel1")
    else:
        print("  skip wheel1")
    if WHEEL2_OLD in text:
        text = sub(text, WHEEL2_OLD, "", "wheel2")
    else:
        print("  skip wheel2")
    GRID_WHEEL_OLD = (
        "  var inner=catalogInnerWheelEl(field);\n"
        "  if(inner&&catalogApplyWheel(inner,dy)){e.preventDefault();return;}\n"
        "  var preview=b.contains('chosen-preview-open');\n"
        "  var hl=ent.classList.contains('highlight')||b.contains('hl-open');\n"
        "  if(preview||hl){\n"
        "    var overlay=hl?(ent.querySelector('.hl-body')||ent):ent;\n"
        "    if(catalogApplyWheel(overlay,dy)){e.preventDefault();return;}\n"
        "    return;\n"
        "  }"
    )
    GRID_WHEEL_NEW = (
        "  var preview=b.contains('chosen-preview-open');\n"
        "  var hl=ent.classList.contains('highlight')||b.contains('hl-open');\n"
        "  if(preview||hl){\n"
        "    var inner=catalogInnerWheelEl(field);\n"
        "    if(inner&&catalogApplyWheel(inner,dy)){e.preventDefault();return;}\n"
        "    var overlay=hl?(ent.querySelector('.hl-body')||ent):ent;\n"
        "    if(catalogApplyWheel(overlay,dy)){e.preventDefault();return;}\n"
        "    return;\n"
        "  }"
    )
    text = sub(text, GRID_WHEEL_OLD, GRID_WHEEL_NEW, "grid-wheel")
    if not text.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name} lost </html>")
    path.write_text(text, encoding="utf-8")
    print("OK", path.name, "bytes", path.stat().st_size)


def main():
    for p in FILES:
        patch_one(p)


if __name__ == "__main__":
    main()
