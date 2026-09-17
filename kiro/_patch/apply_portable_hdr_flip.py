#!/usr/bin/env python3
from pathlib import Path

CSS_ADD = """
  body.catalog-portable #hdrMenuBtns #portraitFlipBtn,
  body.catalog-portable #hdrCluster #portraitFlipBtn,
  body.catalog-portable #portraitFlipBtn{
    display:inline-flex!important;visibility:visible!important;
    flex:0 0 auto;min-width:2.25rem;order:3
  }
  body.catalog-portable #portraitFlipBtn[hidden]{display:inline-flex!important}
"""

OLD_SYNC = """    function syncPortraitFlipBtn(){
    var fb=document.getElementById('portraitFlipBtn');
    if(!fb)return;
    var on=portraitFlipOn();
    var show=!!(document.body.classList.contains('display-sides')&&isPortraitDesktopSides()&&!(typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle')));
    fb.textContent=on?'Portrait: menus right':'Portrait: menus left';
    fb.setAttribute('aria-pressed',on?'true':'false');
    fb.title='Desktop portrait Sides: put Search/Keywords on the left or right of Content';
    fb.hidden=!show;
    fb.setAttribute('aria-hidden',show?'false':'true');
  }"""

NEW_SYNC = """    function syncPortraitFlipBtn(){
    var fb=document.getElementById('portraitFlipBtn');
    if(!fb)return;
    var on=portraitFlipOn();
    if(window.CATALOG_PORTABLE){
      fb.textContent='Flip';
      fb.setAttribute('aria-label','Flip');
      fb.title='Swap left and right panes';
      fb.setAttribute('aria-pressed',on?'true':'false');
      fb.classList.add('hdr-menu-btn');
      fb.classList.toggle('is-on',!!on);
      fb.hidden=false;
      fb.removeAttribute('hidden');
      fb.setAttribute('aria-hidden','false');
      // #region agent log
      try{
        if(!window._dbgFlipBtn||Date.now()-window._dbgFlipBtn>800){
          window._dbgFlipBtn=Date.now();
          fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'F',location:'portable:syncPortraitFlipBtn',message:'flip btn header',data:{on:!!on,hidden:!!fb.hidden,disp:getComputedStyle(fb).display,parent:fb.parentElement&&fb.parentElement.id,sides:document.body.classList.contains('display-sides'),middle:document.body.classList.contains('display-middle')},timestamp:Date.now()})}).catch(function(){});
        }
      }catch(eDbgFbtn){}
      // #endregion
      return;
    }
    var show=!!(document.body.classList.contains('display-sides')&&isPortraitDesktopSides()&&!(typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle')));
    fb.textContent=on?'Portrait: menus right':'Portrait: menus left';
    fb.setAttribute('aria-pressed',on?'true':'false');
    fb.title='Desktop portrait Sides: put Search/Keywords on the left or right of Content';
    fb.hidden=!show;
    fb.setAttribute('aria-hidden',show?'false':'true');
  }"""

OLD_ENSURE = """  function ensurePortraitFlipBtn(){
    var pop=document.getElementById('layoutPresetsPop');
    if(!pop)return;
    var fb=document.getElementById('portraitFlipBtn');
    if(!fb){
      fb=document.createElement('button');
      fb.type='button';fb.id='portraitFlipBtn';fb.className='layout-restore-defaults';
      fb.addEventListener('click',function(e){
        e.preventDefault();e.stopPropagation();
        togglePortraitSidesFlip();
      });
      var rb=document.getElementById('layoutRestoreDefaults');
      if(rb)rb.insertAdjacentElement('afterend',fb);
      else pop.appendChild(fb);
    }
    syncPortraitFlipBtn();
  }"""

NEW_ENSURE = """  function ensurePortraitFlipBtn(){
    var fb=document.getElementById('portraitFlipBtn');
    if(window.CATALOG_PORTABLE){
      var menu=document.getElementById('hdrMenuBtns')||document.getElementById('hdrCluster');
      if(!fb){
        fb=document.createElement('button');
        fb.type='button';fb.id='portraitFlipBtn';
        fb.addEventListener('click',function(e){
          e.preventDefault();e.stopPropagation();
          togglePortraitSidesFlip();
        });
      }
      fb.className='hdr-menu-btn';
      if(menu&&fb.parentElement!==menu)menu.appendChild(fb);
      syncPortraitFlipBtn();
      return;
    }
    var pop=document.getElementById('layoutPresetsPop');
    if(!pop)return;
    if(!fb){
      fb=document.createElement('button');
      fb.type='button';fb.id='portraitFlipBtn';fb.className='layout-restore-defaults';
      fb.addEventListener('click',function(e){
        e.preventDefault();e.stopPropagation();
        togglePortraitSidesFlip();
      });
      var rb=document.getElementById('layoutRestoreDefaults');
      if(rb)rb.insertAdjacentElement('afterend',fb);
      else pop.appendChild(fb);
    }
    syncPortraitFlipBtn();
  }"""

HTML_OLD = 'toggleHdrKw()">K</button></div>'
HTML_NEW = 'toggleHdrKw()">K</button><button type="button" class="hdr-menu-btn" id="portraitFlipBtn" aria-pressed="false" title="Swap left and right panes" aria-label="Flip" onclick="event.preventDefault();event.stopPropagation();if(typeof togglePortraitSidesFlip===\'function\')togglePortraitSidesFlip();">Flip</button></div>'

def patch(path: Path) -> None:
    t = path.read_text(encoding='utf-8')
    if 'body.catalog-portable #hdrMenuBtns #portraitFlipBtn' not in t:
        marker = '  body.catalog-portable #hdrLayoutBtns .layout-presets-tab[hidden]{display:none!important}\n}'
        if marker not in t:
            raise SystemExit(f'css marker missing in {path}')
        t = t.replace(marker, marker[:-2] + CSS_ADD + '}', 1)
    if 'id="portraitFlipBtn"' not in t.split('<script>', 1)[0]:
        if HTML_OLD not in t:
            raise SystemExit(f'header html missing in {path}')
        t = t.replace(HTML_OLD, HTML_NEW, 1)
    if OLD_SYNC not in t:
        raise SystemExit(f'syncPortraitFlipBtn missing in {path}')
    t = t.replace(OLD_SYNC, NEW_SYNC, 1)
    if OLD_ENSURE not in t:
        raise SystemExit(f'ensurePortraitFlipBtn missing in {path}')
    t = t.replace(OLD_ENSURE, NEW_ENSURE, 1)
    path.write_text(t, encoding='utf-8')
    print('patched', path)

def main():
    root = Path('/home/phnx/kiro-kontakt-patch/public/catalogs')
    for name in ('KONTAKT-CATALOG-portable.html', 'DS-CATALOG-portable.html'):
        patch(root / name)

if __name__ == '__main__':
    main()
