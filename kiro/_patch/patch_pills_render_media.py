#!/usr/bin/env python3
from pathlib import Path

FILES = [
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/DS-CATALOG.html"),
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/DS-CATALOG-portable.html"),
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/KONTAKT-CATALOG.html"),
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/KONTAKT-CATALOG-portable.html"),
    Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-ds-catalog-html.sh"),
    Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-kontakt-catalog-html.sh"),
]

RENDER_OLD = """  cardMinDockItems.forEach(function(item,idx){
    var el=document.getElementById(item.id);
    var pill=document.createElement('button');
    pill.type='button';
    pill.className='card-min-pill'+(item.id===curId?' is-front':'');
    pill.setAttribute('data-card-min-id',item.id);
    pill.setAttribute('data-card-min-slot',idx===0?'left':(idx===cardMinDockItems.length-1&&cardMinDockItems.length>1?'right':'middle'));
    if(cardMinDockItems.length===3)pill.setAttribute('data-card-min-slot',idx===0?'left':(idx===1?'middle':'right'));
    pill.setAttribute('aria-pressed',item.id===curId?'true':'false');
    var src=el?cardMinCoverSrc(el):'';
    if(src){
      var im=document.createElement('img');
      im.alt='';
      im.src=src;
      pill.appendChild(im);
    }
    var sp=document.createElement('span');
    sp.className='card-min-name';
    sp.textContent=el?cardMinShortName(el):(item.name||'Library');
    pill.appendChild(sp);
    d.appendChild(pill);
  });"""

RENDER_NEW = """  cardMinDockItems.forEach(function(item,idx){
    var el=document.getElementById(item.id);
    var playing=window.cardMinMediaOwnerId===item.id;
    var pill=document.createElement('div');
    pill.className='card-min-pill'+(item.id===curId?' is-front':'')+(playing?' is-playing':'');
    pill.setAttribute('data-card-min-id',item.id);
    pill.setAttribute('data-card-min-slot',idx===0?'left':(idx===cardMinDockItems.length-1&&cardMinDockItems.length>1?'right':'middle'));
    if(cardMinDockItems.length===3)pill.setAttribute('data-card-min-slot',idx===0?'left':(idx===1?'middle':'right'));
    var open=document.createElement('button');
    open.type='button';
    open.className='card-min-open';
    open.setAttribute('aria-pressed',item.id===curId?'true':'false');
    open.setAttribute('aria-label',(el?cardMinShortName(el):(item.name||'Library'))+' (restore)');
    var src=el?cardMinCoverSrc(el):'';
    if(src){
      var im=document.createElement('img');
      im.alt='';
      im.src=src;
      open.appendChild(im);
    }
    var sp=document.createElement('span');
    sp.className='card-min-name';
    sp.textContent=el?cardMinShortName(el):(item.name||'Library');
    open.appendChild(sp);
    pill.appendChild(open);
    var media=document.createElement('span');
    media.className='card-min-media';
    media.setAttribute('aria-hidden','true');
    pill.appendChild(media);
    var xb=document.createElement('button');
    xb.type='button';
    xb.className='card-min-close';
    xb.setAttribute('aria-label','Close pinned card');
    xb.setAttribute('title','Close');
    xb.innerHTML='\\u00d7';
    pill.appendChild(xb);
    d.appendChild(pill);
  });
  if(window.cardMinMediaOwnerId&&typeof cardMinParkMedia==='function'){
    var host=document.getElementById('cardSearchEmbed');
    var slot=d.querySelector('.card-min-pill[data-card-min-id="'+window.cardMinMediaOwnerId+'"] .card-min-media');
    if(host&&slot&&!slot.contains(host)&&!cardMinExpanded())slot.appendChild(host);
  }"""

MIN_OLD = """  if(document.body.classList.contains('hl-open')||entry.classList.contains('highlight'))closeOverlay({skipScroll:true});
  else if(document.body.classList.contains('chosen-preview-open'))closeChosenPreview({skipJumpExit:true});
  cardMinRender();
}"""

MIN_NEW = """  var keep=typeof cardMinMediaPlaying==='function'&&cardMinMediaPlaying();
  if(window.cardMinMediaOwnerId&&window.cardMinMediaOwnerId!==entry.id&&typeof cardMinPauseMedia==='function')cardMinPauseMedia();
  if(document.body.classList.contains('hl-open')||entry.classList.contains('highlight'))closeOverlay({skipScroll:true});
  else if(document.body.classList.contains('chosen-preview-open'))closeChosenPreview({skipJumpExit:true,skipDismiss:true,keepMedia:keep});
  cardMinRender();
  if(keep&&typeof cardMinParkMedia==='function')cardMinParkMedia(entry.id);
}"""

REST_OLD = """    if(document.body.classList.contains('hl-open')||cur.classList.contains('highlight'))closeOverlay({skipScroll:true});
    else if(document.body.classList.contains('chosen-preview-open'))closeChosenPreview({skipJumpExit:true});
  }
  if(item.mode==='highlight')openOverlay(el);
  else openChosenPreview(el);
  cardMinRender();
}"""

REST_NEW = """    if(document.body.classList.contains('hl-open')||cur.classList.contains('highlight'))closeOverlay({skipScroll:true});
    else if(document.body.classList.contains('chosen-preview-open'))closeChosenPreview({skipJumpExit:true,skipDismiss:true,keepMedia:true});
  }
  if(item.mode==='highlight')openOverlay(el);
  else openChosenPreview(el);
  if(typeof cardMinRestoreMedia==='function')cardMinRestoreMedia(id);
  cardMinRender();
}"""

CLOSE_OLD = """  document.body.classList.remove('search-modal-open');
  if(typeof closeCardSearchEmbed==='function')closeCardSearchEmbed();
  document.body.classList.remove('chosen-preview-open');"""

CLOSE_NEW = """  document.body.classList.remove('search-modal-open');
  if(!opts.skipDismiss&&typeof cardMinDismissOpen==='function')cardMinDismissOpen();
  if(!opts.keepMedia&&typeof closeCardSearchEmbed==='function')closeCardSearchEmbed();
  document.body.classList.remove('chosen-preview-open');"""

CLICK_OLD = """  if(e.target.closest('#cardMinDock')){
    var pill=e.target.closest('.card-min-pill');
    if(pill){cardMinActivate(pill.getAttribute('data-card-min-id'));e.preventDefault();e.stopPropagation();return;}
    e.stopPropagation();return;
  }"""

CLICK_NEW = """  if(e.target.closest('#cardMinDock')){
    var x=e.target.closest('.card-min-close');
    if(x){
      var xp=x.closest('.card-min-pill');
      if(xp)cardMinClose(xp.getAttribute('data-card-min-id'));
      e.preventDefault();e.stopPropagation();return;
    }
    var pill=e.target.closest('.card-min-pill');
    if(pill){cardMinActivate(pill.getAttribute('data-card-min-id'));e.preventDefault();e.stopPropagation();return;}
    e.stopPropagation();return;
  }"""

FIFO_OLD = """    cardMinDockItems.push(rec);
    while(cardMinDockItems.length>CARD_MIN_MAX)cardMinDockItems.shift();"""

FIFO_NEW = """    cardMinDockItems.push(rec);
    while(cardMinDockItems.length>CARD_MIN_MAX){
      var drop=cardMinDockItems.shift();
      if(drop&&drop.id===window.cardMinMediaOwnerId){
        window.cardMinMediaOwnerId='';
        if(typeof closeCardSearchEmbed==='function')closeCardSearchEmbed();
      }
    }"""

EXPORT_OLD = "window.cardMinDismissOpen=cardMinDismissOpen;"
EXPORT_NEW = "window.cardMinDismissOpen=cardMinDismissOpen;\nwindow.cardMinClose=cardMinClose;"

K_LI = "body.display-sides #catalogIndex .index li{display:flex!important;align-items:flex-start;gap:.3em;box-sizing:border-box;margin:.12rem 0;padding:0;max-width:100%;min-width:0;min-height:1.4em;line-height:1.35;overflow:visible;white-space:normal;overflow-wrap:anywhere;word-break:break-word;list-style:none}"
K_LI_NEW = K_LI.replace("overflow:visible", "overflow:hidden;isolation:isolate;position:relative;z-index:0")
K_LI2 = "body.display-sides #catalogIndex .index li{display:flex!important;align-items:flex-start;gap:.3em;min-height:1.35em;line-height:1.35;overflow:visible;white-space:normal;overflow-wrap:anywhere}"
K_LI2_NEW = K_LI2.replace("overflow:visible", "overflow:hidden;isolation:isolate;position:relative")


def do(t, src, dst, label, name):
    c = t.count(src)
    print(" ", name, label, "x" + str(c) if c else "MISS")
    if c:
        t = t.replace(src, dst)
    return t


def main():
    for p in FILES:
        t = p.read_text(encoding="utf-8", errors="replace")
        print("FILE", p.name)
        t = do(t, RENDER_OLD, RENDER_NEW, "render", p.name)
        t = do(t, MIN_OLD, MIN_NEW, "min", p.name)
        t = do(t, REST_OLD, REST_NEW, "restore", p.name)
        t = do(t, CLOSE_OLD, CLOSE_NEW, "closePrev", p.name)
        t = do(t, CLICK_OLD, CLICK_NEW, "clickX", p.name)
        t = do(t, FIFO_OLD, FIFO_NEW, "fifo", p.name)
        t = do(t, EXPORT_OLD, EXPORT_NEW, "export", p.name)
        t = do(t, K_LI, K_LI_NEW, "k-li", p.name)
        t = do(t, K_LI2, K_LI2_NEW, "k-li2", p.name)
        # xb innerHTML: we used \\u00d7 in the python string which becomes \u00d7 in file - good for JS
        p.write_text(t, encoding="utf-8")
        print("  wrote")


if __name__ == "__main__":
    main()
