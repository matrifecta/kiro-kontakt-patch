#!/usr/bin/env python3
"""Index Window = hover overlay; Embed = in .catalog-body and scrolls away."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG.html",
    ROOT / "DS-CATALOG.html",
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]

EMBED_CSS_OLD = """#catalogMain>.catalog-body>#catalogIndex.is-embedded,
body.display-sides #catalogMain .catalog-body>#catalogIndex.is-embedded,
body.display-middle #catalogMain .catalog-body>#catalogIndex.is-embedded,
body.catalog-portable #catalogMain .catalog-body>#catalogIndex.is-embedded{
  position:static!important;top:auto!important;height:auto!important;max-height:none!important;
  flex:0 0 auto!important;margin:.45rem 0 .6rem!important;box-shadow:none!important;
  border-radius:8px;overflow:visible!important;z-index:auto
}"""

EMBED_CSS_NEW = """#catalogMain>.catalog-body>#catalogIndex.is-embedded,
body.display-sides #catalogMain .catalog-body>#catalogIndex.is-embedded,
body.display-middle #catalogMain .catalog-body>#catalogIndex.is-embedded,
body.catalog-portable #catalogMain .catalog-body>#catalogIndex.is-embedded{
  position:static!important;top:auto!important;left:auto!important;right:auto!important;
  height:auto!important;max-height:none!important;flex:0 0 auto!important;
  grid-column:1/-1!important;width:100%!important;max-width:100%!important;order:-6;
  margin:.45rem 0 .6rem!important;box-shadow:none!important;
  border-radius:8px;overflow:visible!important;z-index:auto
}"""

HOVER_CSS_OLD = "#catalogMain>#catalogIndex:not(.is-embedded){flex:0 0 auto;z-index:16}"

HOVER_CSS_NEW = """#catalogMain>#catalogIndex:not(.is-embedded){flex:0 0 auto;z-index:16}
/* fix-INDEX-WINDOW-HOVER: Window Index overlays the content pane; cards scroll underneath */
body.index-window-open:not(.index-fill-doc) #catalogMain,
body.display-sides.index-window-open:not(.index-fill-doc) #catalogMain,
body.display-middle.index-window-open:not(.index-fill-doc) #catalogMain,
body.catalog-portable.index-window-open:not(.index-fill-doc) #catalogMain{
  position:relative!important
}
body.index-window-open:not(.index-fill-doc) #catalogIndex:not(.is-embedded),
body.display-sides.index-window-open:not(.index-fill-doc) #catalogIndex:not(.is-embedded),
body.display-middle.index-window-open:not(.index-fill-doc) #catalogIndex:not(.is-embedded),
body.catalog-portable.index-window-open:not(.index-fill-doc) #catalogIndex:not(.is-embedded),
body.catalog-portable.display-sides.index-window-open:not(.index-fill-doc) #catalogIndex:not(.is-embedded),
body.catalog-portable.display-middle.index-window-open:not(.index-fill-doc) #catalogIndex:not(.is-embedded),
body.catalog-portable.display-content.index-window-open:not(.index-fill-doc) #catalogIndex:not(.is-embedded){
  position:absolute!important;top:0!important;left:0!important;right:0!important;
  width:auto!important;max-width:none!important;margin:0!important;
  z-index:16!important;pointer-events:auto!important
}"""

ABOUT_CSS_OLD = """#catalogDocNote.is-embedded,
#catalogMain .catalog-body>#catalogDocNote,
body.display-sides #catalogMain .catalog-body>#catalogDocNote,
body.display-middle #catalogMain .catalog-body>#catalogDocNote,
body.catalog-portable #catalogMain .catalog-body>#catalogDocNote{
  flex:0 0 auto!important;order:0;margin:.75rem 0 .65rem!important;width:auto!important;max-width:none!important;
  align-self:stretch!important;position:static!important;max-height:none!important;overflow:visible;
  border-radius:8px;z-index:auto;padding-bottom:0
}"""

ABOUT_CSS_NEW = """#catalogDocNote.is-embedded,
#catalogMain .catalog-body>#catalogDocNote,
body.display-sides #catalogMain .catalog-body>#catalogDocNote,
body.display-middle #catalogMain .catalog-body>#catalogDocNote,
body.catalog-portable #catalogMain .catalog-body>#catalogDocNote{
  flex:0 0 auto!important;order:20;margin:.75rem 0 .65rem!important;width:auto!important;max-width:none!important;
  grid-column:1/-1!important;align-self:stretch!important;position:static!important;
  max-height:none!important;overflow:visible;border-radius:8px;z-index:auto;padding-bottom:0
}"""

FILL_BODY_OLD = """  body.catalog-portable.index-fill-doc #catalogMain>.catalog-body,
  body.catalog-portable.index-fill-doc #catalogMain .catalog-body{
    flex:0 0 0px!important;height:0!important;min-height:0!important;max-height:0!important;
    margin:0!important;overflow:hidden!important;overflow-y:hidden!important
  }"""

FILL_BODY_NEW = """  body.catalog-portable.index-fill-doc:not(.doc-note-embedded) #catalogMain>.catalog-body,
  body.catalog-portable.index-fill-doc:not(.doc-note-embedded) #catalogMain .catalog-body{
    flex:0 0 0px!important;height:0!important;min-height:0!important;max-height:0!important;
    margin:0!important;overflow:hidden!important;overflow-y:hidden!important
  }"""

FILL_IX_OLD = """body.catalog-portable.index-fill-doc.index-window-open #catalogIndex:not(.is-embedded):not(.is-collapsed){
  flex:1 1 0%!important;height:auto!important;max-height:none!important;min-height:0!important;
  margin-top:0!important;margin-bottom:4px!important
}"""

FILL_IX_NEW = """body.catalog-portable.index-fill-doc.index-window-open #catalogIndex:not(.is-embedded):not(.is-collapsed){
  position:relative!important;top:auto!important;left:auto!important;right:auto!important;
  flex:1 1 0%!important;height:auto!important;max-height:none!important;min-height:0!important;
  margin-top:0!important;margin-bottom:4px!important
}"""

FILL_IX_EARLY_OLD = """  body.catalog-portable.index-fill-doc #catalogIndex:not(.is-embedded):not(.is-collapsed){
    flex:1 1 0%!important;height:auto!important;max-height:none!important;min-height:0!important;
    margin-top:0!important;margin-bottom:4px!important
  }"""

FILL_IX_EARLY_NEW = """  body.catalog-portable.index-fill-doc #catalogIndex:not(.is-embedded):not(.is-collapsed){
    position:relative!important;top:auto!important;left:auto!important;right:auto!important;
    flex:1 1 0%!important;height:auto!important;max-height:none!important;min-height:0!important;
    margin-top:0!important;margin-bottom:4px!important
  }"""

FILL_JS_OLD = """  var ix=document.getElementById('catalogIndex');
  var fill=!!(document.body.classList.contains('index-window-open')&&indexWindowFillsToDoc()&&ix&&!ix.classList.contains('is-collapsed')&&!ix.classList.contains('is-embedded'));
  document.body.classList.toggle('index-fill-doc',fill);
  var main=document.getElementById('catalogMain');
  var cb=main&&(main.querySelector(':scope > .catalog-body')||main.querySelector('.catalog-body'));
  var note=document.getElementById('catalogDocNote');"""

FILL_JS_NEW = """  var ix=document.getElementById('catalogIndex');
  var note=document.getElementById('catalogDocNote');
  var fill=!!(document.body.classList.contains('index-window-open')&&indexWindowFillsToDoc()&&ix&&!ix.classList.contains('is-collapsed')&&!ix.classList.contains('is-embedded')&&!(note&&note.classList.contains('is-embedded')));
  document.body.classList.toggle('index-fill-doc',fill);
  var main=document.getElementById('catalogMain');
  var cb=main&&(main.querySelector(':scope > .catalog-body')||main.querySelector('.catalog-body'));"""

DOCK_ELSE_OLD = """  }else if(!on&&prev&&main&&cb){
    var keep2=cb.scrollTop;
    cb.scrollTop=0;
    if(keep2)main.scrollTop=keep2;
  }
  if(main){
    if(on){
      main.style.setProperty('display','flex','important');
      main.style.setProperty('flex-direction','column','important');
      main.style.setProperty('overflow-y','hidden','important');
      main.style.setProperty('overflow-x','hidden','important');
      if(cb){
        cb.style.setProperty('overflow-y','auto','important');
        cb.style.setProperty('overflow-x','hidden','important');
        cb.style.setProperty('min-height','0','important');
        cb.style.setProperty('flex','1 1 0%','important');
        cb.style.setProperty('height','0','important');
      }
    }else{
      ['display','flex-direction','overflow-y','overflow-x'].forEach(function(p){main.style.removeProperty(p);});
      if(cb){['overflow-y','overflow-x','min-height','flex','height'].forEach(function(p){cb.style.removeProperty(p);});}
    }
  }"""

DOCK_ELSE_NEW = """  }else if(!on&&prev&&main){
    main.scrollTop=0;
  }
  if(main){
    main.style.setProperty('display','flex','important');
    main.style.setProperty('flex-direction','column','important');
    main.style.setProperty('overflow-y','hidden','important');
    main.style.setProperty('overflow-x','hidden','important');
    if(cb){
      cb.style.setProperty('overflow-y','auto','important');
      cb.style.setProperty('overflow-x','hidden','important');
      cb.style.setProperty('min-height','0','important');
      cb.style.setProperty('flex','1 1 0%','important');
      cb.style.setProperty('height','0','important');
    }
  }"""

DESK_DOCK_OLD = """  if(on&&main){
    main.style.setProperty('overflow-y','hidden','important');
    main.style.setProperty('overflow-x','hidden','important');
    if(cb){
      cb.style.setProperty('overflow-y','auto','important');
      cb.style.setProperty('overflow-x','hidden','important');
      cb.style.setProperty('min-height','0','important');
      cb.style.setProperty('flex','1 1 auto','important');
    }
  }"""

DESK_DOCK_NEW = """  if(main&&windowOk){
    main.style.setProperty('overflow-y','hidden','important');
    main.style.setProperty('overflow-x','hidden','important');
    if(cb){
      cb.style.setProperty('overflow-y','auto','important');
      cb.style.setProperty('overflow-x','hidden','important');
      cb.style.setProperty('min-height','0','important');
      cb.style.setProperty('flex','1 1 auto','important');
    }
  }"""

ENSURE_OLD = """  if(dock){
    port(main,'hidden');
    if(cbMain)port(cbMain,'auto');
  }else{
    port(main,'auto');
  }"""

ENSURE_NEW = """  if(dock||(ix&&ix.classList.contains('is-embedded'))){
    port(main,'hidden');
    if(cbMain)port(cbMain,'auto');
  }else{
    port(main,'auto');
  }"""

SEL_PANEL_OLD = ".entry.selected:not(.highlight) .summary-panel{height:8.2em;max-height:8.2em;overflow:hidden}"
SEL_PANEL_NEW = ".entry.selected:not(.highlight) .summary-panel{height:8.2em;max-height:8.2em;overflow-x:hidden;overflow-y:auto;overscroll-behavior:contain;-webkit-overflow-scrolling:touch}"

SEL_DESC_OLD = ".entry.selected:not(.highlight) .summary-panel .desc,.entry.selected:not(.highlight) .desc{max-height:100%;overflow:hidden;overscroll-behavior:auto;touch-action:auto}"
SEL_DESC_NEW = ".entry.selected:not(.highlight) .summary-panel .desc,.entry.selected:not(.highlight) .desc{max-height:none;overflow:visible}"

CLIP_PREVIEW_OLD = """body.chosen-preview-open .entry.selected:not(.highlight) .summary-panel{
  height:auto!important;max-height:min(14em,calc(36vh - 2.5em))!important;
  overflow:hidden!important;overflow-y:auto!important;flex:1 1 auto!important;min-height:0!important
}
body.chosen-preview-open .entry.selected:not(.highlight) .summary-panel .desc,
body.chosen-preview-open .entry.selected:not(.highlight) .desc{
  max-height:100%!important;min-height:0!important;overflow-x:hidden!important;overflow-y:auto!important
}"""

CLIP_PREVIEW_NEW = """body.chosen-preview-open .entry.selected:not(.highlight) .summary-panel{
  height:auto!important;max-height:min(14em,calc(36vh - 2.5em))!important;
  overflow-x:hidden!important;overflow-y:auto!important;flex:0 0 auto!important;min-height:0!important;
  overscroll-behavior:contain!important
}
body.chosen-preview-open .entry.selected:not(.highlight) .summary-panel .desc,
body.chosen-preview-open .entry.selected:not(.highlight) .desc{
  max-height:none!important;min-height:0!important;overflow:visible!important
}"""

HL_PANEL_CLIP_OLD = ".entry.highlight .summary-panel{max-height:min(14em,32vh);overflow:hidden;overflow-y:auto}"
HL_PANEL_CLIP_NEW = ".entry.highlight .summary-panel{max-height:min(14em,32vh);overflow-x:hidden;overflow-y:auto;overscroll-behavior:contain;-webkit-overflow-scrolling:touch}"

WHEEL_OLD = """document.addEventListener('wheel',function(e){
  var field=e.target.closest&&e.target.closest('.summary-panel,.summary-panel .desc,.path');
  if(!field)return;
  var ent=field.closest('.entry');
  if(!ent||!ent.classList.contains('selected'))return;
  if(window._eqWheelLog&&Date.now()-window._eqWheelLog<400)return;
  window._eqWheelLog=Date.now();
  try{
    var cs=getComputedStyle(field);
    var main=document.getElementById('catalogMain');
    var body=document.querySelector('#catalogMain > .catalog-body');
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'A',location:'catalog:wheelOverDescPath',message:'wheel over active desc/path',data:{tag:field.tagName,cls:(field.className||'').toString().slice(0,40),ovY:cs.overflowY,osc:cs.overscrollBehavior||cs.overscrollBehaviorY,canScroll:field.scrollHeight>field.clientHeight+1,hl:ent.classList.contains('highlight'),preview:document.body.classList.contains('chosen-preview-open'),mainSt:main?Math.round(main.scrollTop):null,bodySt:body?Math.round(body.scrollTop):null,delta:Math.round(e.deltaY)},timestamp:Date.now()})}).catch(function(){});
  }catch(eDbgA){}
},{passive:true});"""

WHEEL_NEW = WHEEL_OLD + """
document.addEventListener('wheel',function(e){
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


def patch_one(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    if not text.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name} does not end with </html>")
    done = []

    def sub(old, new, label, required=True):
        nonlocal text
        n = text.count(old)
        if n == 0:
            if required:
                raise SystemExit(f"{path.name} missing {label}")
            return
        text = text.replace(old, new)
        done.append(f"{label} x{n}")

    sub(EMBED_CSS_OLD, EMBED_CSS_NEW, "embed-css")
    sub(HOVER_CSS_OLD, HOVER_CSS_NEW, "hover-css")
    sub(ABOUT_CSS_OLD, ABOUT_CSS_NEW, "about-css")
    sub(FILL_BODY_OLD, FILL_BODY_NEW, "fill-body-css", required=False)
    sub(FILL_IX_EARLY_OLD, FILL_IX_EARLY_NEW, "fill-ix-early", required=False)
    sub(FILL_IX_OLD, FILL_IX_NEW, "fill-ix-css")
    sub(FILL_JS_OLD, FILL_JS_NEW, "fill-js", required=False)
    sub(DOCK_ELSE_OLD, DOCK_ELSE_NEW, "dock-else", required=False)
    sub(DESK_DOCK_OLD, DESK_DOCK_NEW, "desk-dock", required=False)
    sub(ENSURE_OLD, ENSURE_NEW, "ensure-scroll", required=False)
    sub(SEL_PANEL_OLD, SEL_PANEL_NEW, "sel-panel-scroll")
    sub(SEL_DESC_OLD, SEL_DESC_NEW, "sel-desc-visible")
    sub(CLIP_PREVIEW_OLD, CLIP_PREVIEW_NEW, "preview-panel-scroll")
    sub(HL_PANEL_CLIP_OLD, HL_PANEL_CLIP_NEW, "hl-panel-scroll")
    sub(WHEEL_OLD, WHEEL_NEW, "desc-wheel-forward")

    if not text.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name} lost </html> after patch")
    path.write_text(text, encoding="utf-8")
    return done


def main():
    for path in FILES:
        done = patch_one(path)
        print(path.name, ", ".join(done) if done else "no-op")


if __name__ == "__main__":
    main()
