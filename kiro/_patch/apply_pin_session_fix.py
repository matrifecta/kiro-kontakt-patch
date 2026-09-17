#!/usr/bin/env python3
"""Fix saved-session save (off-by-one) and load (click dismisses restore) in all 6 catalogs."""
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


def once(text, old, new, label, path):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{path.name}: {label} count={n} expected 1")
    return text.replace(old, new, 1)


SNAP_OLD = """function snapshotPinSessionCards(){
  return (typeof cardMinDockItems!=='undefined'?cardMinDockItems:[]).map(function(it){
    return {id:it.id,mode:it.mode||'preview',kind:pinTinKindOf(it),name:it.name||''};
  });
}
"""

SNAP_NEW = """function snapshotPinSessionCards(){
  var max=typeof CARD_MIN_MAX==='number'?CARD_MIN_MAX:3;
  var cards=[];
  var seen={};
  function add(it){
    if(!it||!it.id)return;
    var kind=pinTinKindOf(it);
    var k=String(it.id)+'|'+kind;
    if(seen[k])return;
    seen[k]=1;
    cards.push({id:it.id,mode:it.mode||kind,kind:kind,name:it.name||''});
  }
  (typeof cardMinDockItems!=='undefined'?cardMinDockItems:[]).forEach(add);
  var front=typeof cardMinExpanded==='function'?cardMinExpanded():null;
  if(front&&front.id){
    add({
      id:front.id,
      mode:typeof cardMinMode==='function'?cardMinMode(front):'preview',
      kind:typeof cardMinTinKind==='function'?cardMinTinKind(front):'preview',
      name:typeof cardMinShortName==='function'?cardMinShortName(front):''
    });
  }
  if(cards.length>max)cards=cards.slice(-max);
  return cards;
}
function pinFrontIntoDock(){
  var front=typeof cardMinExpanded==='function'?cardMinExpanded():null;
  if(!front||!front.id)return;
  var kind=typeof cardMinTinKind==='function'?cardMinTinKind(front):'preview';
  if(typeof cardMinIndex==='function'&&cardMinIndex(front.id,kind)>=0)return;
  var rec={id:front.id,mode:typeof cardMinMode==='function'?cardMinMode(front):'preview',kind:kind,name:typeof cardMinShortName==='function'?cardMinShortName(front):''};
  var max=typeof CARD_MIN_MAX==='number'?CARD_MIN_MAX:3;
  if(cardMinDockItems.length>=max){
    var drop=cardMinDockItems[0];
    if(drop)cardMinClose(drop.id,true,drop.kind||(drop.mode==='highlight'?'highlight':'preview'));
  }
  cardMinDockItems.push(rec);
  if(typeof cardMinRender==='function')cardMinRender();
}
"""

SAVE_OLD = """window.savePinSession=function(name){
  name=String(name||'').replace(/^\\s+|\\s+$/g,'');
  if(!name)return false;
  var cards=snapshotPinSessionCards();
  if(!cards.length)return false;
  var front=typeof cardMinExpanded==='function'?cardMinExpanded():null;
  var rec={id:pinSessionId(),name:name,savedAt:Date.now(),usedAt:Date.now(),cards:cards,frontId:front&&front.id||'',frontKind:front?cardMinTinKind(front):''};
"""

SAVE_NEW = """window.savePinSession=function(name){
  name=String(name||'').replace(/^\\s+|\\s+$/g,'');
  if(!name)return false;
  if(typeof pinFrontIntoDock==='function')pinFrontIntoDock();
  var cards=snapshotPinSessionCards();
  if(!cards.length)return false;
  var front=typeof cardMinExpanded==='function'?cardMinExpanded():null;
  var rec={id:pinSessionId(),name:name,savedAt:Date.now(),usedAt:Date.now(),cards:cards,frontId:front&&front.id||(cards[cards.length-1]&&cards[cards.length-1].id)||'',frontKind:front?cardMinTinKind(front):(cards[cards.length-1]&&(cards[cards.length-1].kind||cards[cards.length-1].mode))||'preview'};
"""

RESTORE_OLD = """window.restorePinSession=function(id){
  var sess=null;
  (pinSessionStore.sessions||[]).forEach(function(s){if(s&&s.id===id)sess=s;});
  if(!sess||!sess.cards)return;
  touchPinSession(id);persistPinSessions();
  cardMinDockItems=[];
  sess.cards.forEach(function(c){
    if(!c||!c.id)return;
    cardMinDockItems.push({id:c.id,mode:c.mode||c.kind||'preview',kind:c.kind||(c.mode==='highlight'?'highlight':'preview'),name:c.name||''});
  });
  if(typeof cardMinRender==='function')cardMinRender();
  var frontId=sess.frontId||(sess.cards[0]&&sess.cards[0].id);
  var frontKind=sess.frontKind||(sess.cards[0]&&(sess.cards[0].kind||sess.cards[0].mode))||'preview';
  if(frontId&&typeof cardMinRestore==='function')cardMinRestore(frontId,frontKind);
};
"""

RESTORE_NEW = """window.restorePinSession=function(id,ev){
  if(ev&&ev.stopPropagation){ev.preventDefault();ev.stopPropagation();}
  var sess=null;
  (pinSessionStore.sessions||[]).forEach(function(s){if(s&&s.id===id)sess=s;});
  if(!sess||!sess.cards)return;
  touchPinSession(id);persistPinSessions();
  if(typeof hideSearchAc==='function')hideSearchAc();
  var ac=document.getElementById('acList');
  if(ac){ac.classList.remove('open');ac.innerHTML='';}
  var cur=typeof cardMinExpanded==='function'?cardMinExpanded():null;
  if(cur){
    if(document.body.classList.contains('hl-open')||(cur.classList&&cur.classList.contains('highlight'))){
      if(typeof closeOverlay==='function')closeOverlay({skipScroll:true});
    }else if(document.body.classList.contains('chosen-preview-open')&&typeof closeChosenPreview==='function'){
      closeChosenPreview({skipJumpExit:true,skipDismiss:true,keepMedia:true});
    }
  }
  cardMinDockItems=[];
  sess.cards.forEach(function(c){
    if(!c||!c.id)return;
    cardMinDockItems.push({id:c.id,mode:c.mode||c.kind||'preview',kind:c.kind||(c.mode==='highlight'?'highlight':'preview'),name:c.name||''});
  });
  var frontId=sess.frontId||(sess.cards[sess.cards.length-1]&&sess.cards[sess.cards.length-1].id);
  var frontKind=sess.frontKind||'preview';
  var inDock=false;
  cardMinDockItems.forEach(function(c){if(c&&c.id===frontId&&pinTinKindOf(c)===frontKind)inDock=true;});
  if(frontId&&!inDock){
    cardMinDockItems.push({id:frontId,mode:frontKind,kind:frontKind,name:''});
    var max=typeof CARD_MIN_MAX==='number'?CARD_MIN_MAX:3;
    if(cardMinDockItems.length>max)cardMinDockItems.shift();
  }
  if(typeof cardMinRender==='function')cardMinRender();
  setTimeout(function(){
    if(frontId&&typeof cardMinRestore==='function')cardMinRestore(frontId,frontKind);
  },0);
};
"""

ONCLICK_OLD = r"""onclick="restorePinSession(\''+jsStr(s.id)+'\')" """[:-1]
ONCLICK_NEW = r"""onclick="restorePinSession(\''+jsStr(s.id)+'\',event)" """[:-1]

COVER_OLD = """function overlayCoversSearch(){
  var b=document.body.classList;
  return overlayFocusOpen()||b.contains('hl-open')||b.contains('chosen-preview-open')||b.contains('card-embed-open')||b.contains('search-modal-open')||!!document.querySelector('.entry.highlight');
}
"""

COVER_NEW = """function overlayCoversSearch(){
  var b=document.body.classList;
  if(overlayFocusOpen()||b.contains('hl-open')||b.contains('search-modal-open'))return true;
  if(b.contains('display-sides'))return false;
  return b.contains('chosen-preview-open')||b.contains('card-embed-open')||!!document.querySelector('.entry.highlight');
}
"""

CLICK_OLD = (
    "    if(e.target.closest('#searchModal,.search-modal,.search-modal-link,#cardMinDock')) return;\n"
)
CLICK_NEW = (
    "    if(e.target.closest('#searchModal,.search-modal,.search-modal-link,#cardMinDock,.search-chrome,.search-ac-shell,.search-autocomplete,#acList,#acShell,#historyCloud,.ac-item,.ac-history-cloud')) return;\n"
)

LOG_SAVE = (
    "  persistPinSessions();\n"
    "  return true;\n"
    "};\n"
    "function touchPinSession(id){"
)
LOG_SAVE_NEW = (
    "  persistPinSessions();\n"
    "  try{fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'post-fix',hypothesisId:'H-SESS',location:'savePinSession',message:'pin-session-save',data:{name:name,n:cards.length,ids:cards.map(function(c){return c.id;}),frontId:rec.frontId||'',dockN:(typeof cardMinDockItems!=='undefined'?cardMinDockItems.length:0)},timestamp:Date.now()})}).catch(function(){});}catch(err){}\n"
    "  return true;\n"
    "};\n"
    "function touchPinSession(id){"
)


def patch(text, path):
    text = once(text, SNAP_OLD, SNAP_NEW, "snapshot", path)
    text = once(text, SAVE_OLD, SAVE_NEW, "save", path)
    text = once(text, RESTORE_OLD, RESTORE_NEW, "restore", path)
    n = text.count(ONCLICK_OLD)
    if n != 2:
        raise SystemExit(f"{path.name}: session-onclick count={n} expected 2")
    text = text.replace(ONCLICK_OLD, ONCLICK_NEW)
    text = once(text, COVER_OLD, COVER_NEW, "overlay-covers", path)
    text = once(text, CLICK_OLD, CLICK_NEW, "preview-click", path)
    text = once(text, LOG_SAVE, LOG_SAVE_NEW, "save-log", path)
    return text


def main():
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        new = patch(text, path)
        path.write_text(new, encoding="utf-8")
        print(f"patched {path.name}")


if __name__ == "__main__":
    main()
