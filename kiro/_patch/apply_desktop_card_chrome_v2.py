#!/usr/bin/env python3
"""Desktop card chrome: shared PATH/patches/Search/heart baseline; jump off labels.

Desktop catalogs only. Does not touch *-portable.html.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
]
MARK = "fix-DESKTOP-CARD-CHROME-V2"

CSS_OLD = """/* fix-DESKTOP-SEARCH-CARD-ALIGN-v1: Search-strip + card chrome share a baseline (desktop only) */
body:not(.catalog-portable) #searchStrip{
  align-items:center!important;flex-wrap:nowrap!important;min-height:2.75rem
}
body:not(.catalog-portable) #searchStrip #searchInput{
  box-sizing:border-box;align-self:center;min-height:2.75rem;height:2.75rem;
  padding:0 .35rem;line-height:2.75rem;display:block
}
body:not(.catalog-portable) #searchStrip .search-strip-clear,
body:not(.catalog-portable) #searchStrip .search-strip-hide,
body:not(.catalog-portable) #searchStrip .search-strip-fs,
body:not(.catalog-portable) #searchStrip .search-strip-more,
body:not(.catalog-portable) #searchStrip .ac-history-wrap,
body:not(.catalog-portable) #searchStrip .ac-history-btn{
  box-sizing:border-box;align-self:center;min-height:2.75rem;height:2.75rem;
  display:inline-flex;align-items:center;justify-content:center;line-height:1
}
body:not(.catalog-portable) #searchStrip .ac-history-btn,
body:not(.catalog-portable) #searchStrip .search-strip-fs,
body:not(.catalog-portable) #searchStrip .search-strip-more{
  width:2.75rem;min-width:2.75rem;padding:0
}
body:not(.catalog-portable) .search-autocomplete .ac-item{align-items:center}
body:not(.catalog-portable) .search-autocomplete .ac-item.ac-lib{align-items:center;height:auto}
body:not(.catalog-portable) .search-autocomplete .ac-item .ac-count,
body:not(.catalog-portable) .search-autocomplete .ac-item.ac-lib .ac-lib-mark{
  align-self:center;flex:0 0 auto;font-variant-numeric:tabular-nums;
  min-width:2.5em;text-align:right
}
body:not(.catalog-portable) .entry:not(.highlight) .cover{
  width:100%!important;max-width:100%!important;flex:0 0 auto;
  display:flex!important;align-items:center!important;justify-content:center!important;
  box-sizing:border-box
}
body:not(.catalog-portable) .entry:not(.highlight) .cover img{
  width:auto!important;height:auto!important;max-width:100%!important;
  object-fit:contain!important;object-position:center center!important
}
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight):not(:has(details.patches[open])):not(:has(.path.is-expanded)) .path{
  margin-top:auto!important
}
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) details.patches,
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .patches{
  margin-top:0!important;margin-bottom:0!important;
  padding-top:var(--card-chrome-gap)!important;flex:0 0 auto
}
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .patches>summary{
  display:flex;align-items:center;box-sizing:border-box;
  min-height:2.25rem;padding:.35rem .25rem;margin:0
}
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .card-actions{
  margin-top:0!important;margin-bottom:0!important;
  padding-top:var(--card-chrome-gap)!important;padding-bottom:0!important;
  padding-right:calc(var(--card-chrome-btn) + var(--card-chrome-gap))!important;
  align-self:stretch;align-items:center;min-height:var(--card-chrome-btn);
  box-sizing:border-box
}
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .search-popup-btn,
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .search-link{
  box-sizing:border-box;min-height:var(--card-chrome-btn);height:var(--card-chrome-btn);
  margin-top:0!important;padding-top:0;padding-bottom:0;
  display:inline-flex;align-items:center;justify-content:center;line-height:1
}
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .fav-btn{
  right:.8rem;bottom:.8rem
}
/* fix-DESKTOP-NOCOVER-SLOT-v1: missing-cover tiles keep the cover band so titles line up */
body:not(.catalog-portable) .entry:not(.highlight):not(:has(.cover)) .hl-body{
  box-sizing:border-box;padding-top:calc(clamp(4.5rem,12vw,7.5rem) + .6rem)
}
/* fix-DESKTOP-NOCOVER-SLOT-v1b */
"""

CSS_NEW = f"""/* {MARK}: lock desc + pin chrome on hl-body; Search=heart; jump in gutter */
body:not(.catalog-portable) #searchStrip{{
  align-items:center!important;flex-wrap:nowrap!important;
  min-height:var(--card-chrome-btn)!important;height:auto!important
}}
body:not(.catalog-portable) #searchStrip #searchInput{{
  box-sizing:border-box;align-self:center;
  min-height:var(--card-chrome-btn)!important;height:var(--card-chrome-btn)!important;
  padding:0 .35rem!important;line-height:var(--card-chrome-btn)!important;display:block
}}
body:not(.catalog-portable) #searchStrip .search-strip-clear,
body:not(.catalog-portable) #searchStrip .search-strip-hide,
body:not(.catalog-portable) #searchStrip .search-strip-fs,
body:not(.catalog-portable) #searchStrip .search-strip-more,
body:not(.catalog-portable) #searchStrip .ac-history-wrap,
body:not(.catalog-portable) #searchStrip .ac-history-btn{{
  box-sizing:border-box;align-self:center;
  min-height:var(--card-chrome-btn)!important;height:var(--card-chrome-btn)!important;
  display:inline-flex;align-items:center;justify-content:center;line-height:1
}}
body:not(.catalog-portable) #searchStrip .ac-history-btn,
body:not(.catalog-portable) #searchStrip .search-strip-fs,
body:not(.catalog-portable) #searchStrip .search-strip-more{{
  width:var(--card-chrome-btn)!important;min-width:var(--card-chrome-btn)!important;padding:0!important
}}
body:not(.catalog-portable) .search-autocomplete .ac-item{{align-items:center}}
body:not(.catalog-portable) .search-autocomplete .ac-item.ac-lib{{align-items:center;height:auto}}
body:not(.catalog-portable) .search-autocomplete .ac-item .ac-count,
body:not(.catalog-portable) .search-autocomplete .ac-item.ac-lib .ac-lib-mark{{
  align-self:center;flex:0 0 auto;font-variant-numeric:tabular-nums;
  min-width:2.5em;text-align:right
}}
body:not(.catalog-portable) .entry:not(.highlight) .cover{{
  width:100%!important;max-width:100%!important;flex:0 0 auto;
  display:flex!important;align-items:center!important;justify-content:center!important;
  box-sizing:border-box
}}
body:not(.catalog-portable) .entry:not(.highlight) .cover img{{
  width:auto!important;height:auto!important;max-width:100%!important;
  object-fit:contain!important;object-position:center center!important
}}
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .hl-body{{
  display:flex!important;flex-direction:column!important;flex:1 1 auto!important;min-height:0!important
}}
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .lib-notes{{
  margin:0!important;padding:0!important;min-height:0!important;height:0!important;
  overflow:hidden!important;flex:0 0 0!important
}}
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .summary-panel{{
  box-sizing:border-box!important;
  height:8.2em!important;min-height:8.2em!important;max-height:8.2em!important;
  overflow:hidden!important;flex:0 0 8.2em!important;
  margin-top:var(--card-chrome-gap)!important;margin-bottom:0!important
}}
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight):not(:has(details.patches[open])):not(:has(.path.is-expanded)) .path{{
  margin-top:auto!important;margin-bottom:0!important;flex:0 0 auto
}}
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .path-label{{
  margin:0 0 .1rem!important;min-height:1.05em!important;line-height:1.2!important
}}
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .path-action-row{{
  min-height:var(--path-icon-size,calc(var(--card-chrome-btn) * .88))!important
}}
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) details.patches,
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .patches{{
  margin-top:0!important;margin-bottom:0!important;
  padding-top:var(--card-chrome-gap)!important;flex:0 0 auto
}}
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .patches>summary{{
  display:flex!important;align-items:center!important;box-sizing:border-box;
  min-height:2.25rem!important;height:2.25rem!important;padding:.35rem .25rem!important;margin:0!important
}}
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .card-actions{{
  margin-top:0!important;margin-bottom:0!important;
  padding-top:var(--card-chrome-gap)!important;padding-bottom:0!important;
  padding-right:calc(var(--card-chrome-btn) + var(--card-chrome-gap))!important;
  align-self:stretch!important;align-items:center!important;
  min-height:var(--card-chrome-btn)!important;height:var(--card-chrome-btn)!important;
  box-sizing:border-box
}}
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .search-popup-btn,
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .search-link{{
  box-sizing:border-box;
  min-height:var(--card-chrome-btn)!important;height:var(--card-chrome-btn)!important;
  margin-top:0!important;padding:0 .85rem!important;
  display:inline-flex!important;align-items:center!important;justify-content:center!important;
  line-height:1!important;border-radius:8px!important;font-size:1rem!important
}}
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .fav-btn{{
  right:.8rem!important;bottom:.8rem!important;top:auto!important;left:auto!important;
  width:var(--card-chrome-btn)!important;height:var(--card-chrome-btn)!important;
  min-width:var(--card-chrome-btn)!important;min-height:var(--card-chrome-btn)!important;
  border-radius:8px!important
}}
body:not(.catalog-portable).display-sides #catalogMain .catalog-body,
body:not(.catalog-portable).display-middle #catalogMain .catalog-body{{
  padding-right:2.85rem!important
}}
body:not(.catalog-portable).display-sides a.top,
body:not(.catalog-portable).display-sides a.bottom,
body:not(.catalog-portable).display-middle a.top,
body:not(.catalog-portable).display-middle a.bottom{{
  display:none!important
}}
body:not(.catalog-portable).display-sides #catalogJumpStack>a.top,
body:not(.catalog-portable).display-sides #catalogJumpStack>a.bottom,
body:not(.catalog-portable).display-middle #catalogJumpStack>a.top,
body:not(.catalog-portable).display-middle #catalogJumpStack>a.bottom{{
  display:inline-flex!important;position:relative!important;
  top:auto!important;bottom:auto!important;right:auto!important;left:auto!important;margin:0!important
}}
/* fix-DESKTOP-NOCOVER-SLOT-v1: missing-cover tiles keep the cover band so titles line up */
body:not(.catalog-portable) .entry:not(.highlight):not(:has(.cover)) .hl-body{{
  box-sizing:border-box;padding-top:calc(clamp(4.5rem,12vw,7.5rem) + .6rem)
}}
/* fix-DESKTOP-NOCOVER-SLOT-v1b */
"""

RESET_OLD = """      e.style.minHeight='';
      var _cov=e.querySelector('.cover');
      if(_cov)_cov.style.minHeight='';
      var _sp=e.querySelector('.summary-panel');
      if(_sp)_sp.style.marginTop='';
      var _hb=e.querySelector('.hl-body');
      if(_hb)_hb.style.paddingTop='';"""

RESET_NEW = """      e.style.minHeight='';
      var _cov=e.querySelector('.cover');
      if(_cov)_cov.style.minHeight='';
      var _sp=e.querySelector('.summary-panel');
      if(_sp){_sp.style.marginTop='';_sp.style.minHeight='';}
      var _hb=e.querySelector('.hl-body');
      if(_hb){_hb.style.paddingTop='';_hb.style.minHeight='';}
      var _path=e.querySelector('.path');
      if(_path)_path.style.paddingTop='';
      var _fav=e.querySelector('.fav-btn');
      if(_fav){_fav.style.top='';_fav.style.bottom='';}"""

ROW_TOL_OLD = "for(var i=0;i<rows.length;i++){if(Math.abs(rows[i].t-t)<=10){row=rows[i];break;}}"
ROW_TOL_NEW = "for(var i=0;i<rows.length;i++){if(Math.abs(rows[i].t-t)<=24){row=rows[i];break;}}"

ROW_OLD = """      if(row.cards.length<2)return;
      var collapsedMax=0;
      row.cards.forEach(function(e){
        if(typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e))return;
        var r=e.getBoundingClientRect();
        var h=r.height,w=r.width;
        if(catalogCardHeightCube(h,w))return;
        collapsedMax=Math.max(collapsedMax,h);
      });
      if(!(collapsedMax>0)){
        row.cards.forEach(function(e){
          if(typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e))return;
          collapsedMax=Math.max(collapsedMax,e.getBoundingClientRect().height);
        });
      }
      var colMh=collapsedMax>0?Math.round(collapsedMax):0;
      row.cards.forEach(function(e){
        if(typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e)){
          e.style.minHeight='';
          return;
        }
        if(!colMh)return;
        var w=e.getBoundingClientRect().width;
        var use=colMh;
        if(catalogCardHeightCube(colMh,w))use=Math.round(e.getBoundingClientRect().height);
        e.style.minHeight=use>0?use+'px':'';
      });
      var _bandCards=row.cards.filter(function(e){
        return !(typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e));
      });
      if(!_bandCards.length)_bandCards=row.cards;
      var _maxCovH=0,_refCard=null;
      _bandCards.forEach(function(e){
        var _c=e.querySelector('.cover');
        if(!_c)return;
        var _h=Math.round(_c.getBoundingClientRect().height);
        var _img=_c.querySelector('img');
        if(_img){
          var _ih=Math.round(_img.getBoundingClientRect().height);
          if(_ih>_h)_h=_ih;
        }
        if(_h>_maxCovH){_maxCovH=_h;_refCard=e;}
      });
      var _desk=!(typeof window!=='undefined'&&window.CATALOG_PORTABLE);
      var _slotH=_maxCovH;
      if(_refCard){
        var _rc=_refCard.querySelector('.cover');
        if(_rc){
          var _rcs=getComputedStyle(_rc);
          _slotH=_maxCovH+Math.round(parseFloat(_rcs.marginTop)||0)+Math.round(parseFloat(_rcs.marginBottom)||0);
        }
      }
      row.cards.forEach(function(e){
        var _c=e.querySelector('.cover');
        var _sp=e.querySelector('.summary-panel');
        var _exp=typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e);
        var _hb=e.querySelector('.hl-body');
        if(_c){
          if(_desk&&_maxCovH>0&&!_exp)_c.style.minHeight=_maxCovH+'px';
          else _c.style.minHeight='';
          if(_hb)_hb.style.paddingTop='';
        }else if(_hb){
          if(_desk&&_slotH>0&&!_exp)_hb.style.paddingTop=_slotH+'px';
          else _hb.style.paddingTop='';
        }
        if(_sp)_sp.style.marginTop='';
      });
      if(_desk&&typeof document!=='undefined'&&document.body)void document.body.offsetHeight;
      if(_refCard){
        var _tSp=_refCard.querySelector('.summary-panel');
        var _targetTop=_tSp?Math.round(_tSp.getBoundingClientRect().top):0;
        if(_targetTop>0){
          row.cards.forEach(function(e){
            if(typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e))return;
            var _sp=e.querySelector('.summary-panel');
            if(!_sp)return;
            var _d=_targetTop-Math.round(_sp.getBoundingClientRect().top);
            _sp.style.marginTop=(_d>0?_d:0)+'px';
          });
        }
      }"""

ROW_NEW = """      if(row.cards.length<2)return;
      var _desk=!(typeof window!=='undefined'&&window.CATALOG_PORTABLE);
      var _bandCards=row.cards.filter(function(e){
        return !(typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e));
      });
      if(!_bandCards.length)_bandCards=row.cards;
      var _maxCovH=0,_refCard=null;
      _bandCards.forEach(function(e){
        var _c=e.querySelector('.cover');
        if(!_c)return;
        var _h=Math.round(_c.getBoundingClientRect().height);
        var _img=_c.querySelector('img');
        if(_img){
          var _ih=Math.round(_img.getBoundingClientRect().height);
          if(_ih>_h)_h=_ih;
        }
        if(_h>_maxCovH){_maxCovH=_h;_refCard=e;}
      });
      var _slotH=_maxCovH;
      if(_refCard){
        var _rc=_refCard.querySelector('.cover');
        if(_rc){
          var _rcs=getComputedStyle(_rc);
          _slotH=_maxCovH+Math.round(parseFloat(_rcs.marginTop)||0)+Math.round(parseFloat(_rcs.marginBottom)||0);
        }
      }
      row.cards.forEach(function(e){
        var _c=e.querySelector('.cover');
        var _sp=e.querySelector('.summary-panel');
        var _exp=typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e);
        var _hb=e.querySelector('.hl-body');
        if(_c){
          if(_desk&&_maxCovH>0&&!_exp)_c.style.minHeight=_maxCovH+'px';
          else _c.style.minHeight='';
          if(_hb&&!_exp)_hb.style.paddingTop='';
        }else if(_hb){
          if(_desk&&_slotH>0&&!_exp)_hb.style.paddingTop=_slotH+'px';
          else _hb.style.paddingTop='';
        }
        if(_sp)_sp.style.marginTop='';
      });
      if(_desk&&typeof document!=='undefined'&&document.body)void document.body.offsetHeight;
      var collapsedMax=0;
      row.cards.forEach(function(e){
        if(typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e))return;
        collapsedMax=Math.max(collapsedMax,e.getBoundingClientRect().height);
      });
      var colMh=collapsedMax>0?Math.round(collapsedMax):0;
      row.cards.forEach(function(e){
        if(typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e)){
          e.style.minHeight='';
          return;
        }
        e.style.minHeight=colMh>0?colMh+'px':'';
      });
      if(_desk&&typeof document!=='undefined'&&document.body)void document.body.offsetHeight;
      if(_desk){
        var _chromeTops=[];
        _bandCards.forEach(function(e){
          var lab=e.querySelector('.path-label')||e.querySelector('.path');
          if(!lab)return;
          _chromeTops.push(Math.round(lab.getBoundingClientRect().top));
        });
        if(_chromeTops.length){
          var _chromeTarget=Math.max.apply(null,_chromeTops);
          _bandCards.forEach(function(e){
            var lab=e.querySelector('.path-label')||e.querySelector('.path');
            var path=e.querySelector('.path');
            if(!lab||!path)return;
            var d=_chromeTarget-Math.round(lab.getBoundingClientRect().top);
            if(d>1){
              path.style.paddingTop=d+'px';
              var eh=Math.round(e.getBoundingClientRect().height);
              e.style.minHeight=Math.max(colMh,eh+d)+'px';
            }
          });
        }
      }"""

PARK_OLD = """  var bot=document.querySelector('a.bottom');
  if(!bot){
    bot=document.createElement('a');
    bot.className='bottom';
    bot.href='#catalogBottom';
  }
  var topBtn=document.querySelector('a.top');
  ensureCatalogJumpGlyph(topBtn,'top');
  ensureCatalogJumpGlyph(bot,'bottom');
  var stack=document.getElementById('catalogJumpStack');
  if(!stack){
    stack=document.createElement('div');
    stack.id='catalogJumpStack';
  }
  if(stack.parentNode!==document.body)document.body.appendChild(stack);
  if(topBtn&&topBtn.parentNode!==stack)stack.appendChild(topBtn);
  if(bot.parentNode!==stack)stack.appendChild(bot);
  if(topBtn&&bot.previousElementSibling!==topBtn)stack.insertBefore(topBtn,bot);"""

PARK_NEW = """  var stack=document.getElementById('catalogJumpStack');
  if(!stack){
    stack=document.createElement('div');
    stack.id='catalogJumpStack';
  }
  if(stack.parentNode!==document.body)document.body.appendChild(stack);
  var tops=[],bots=[];
  document.querySelectorAll('a.top,a.bottom').forEach(function(el){
    if(el.classList.contains('top'))tops.push(el);else bots.push(el);
  });
  var topBtn=tops[0]||null;
  var bot=bots[0]||null;
  if(!bot){
    bot=document.createElement('a');
    bot.className='bottom';
    bot.href='#catalogBottom';
  }
  if(!topBtn){
    topBtn=document.createElement('a');
    topBtn.className='top';
    topBtn.href='#top';
    tops.push(topBtn);
  }
  tops.forEach(function(el){if(el.parentNode!==stack)stack.appendChild(el);ensureCatalogJumpGlyph(el,'top');});
  bots.forEach(function(el){if(el.parentNode!==stack)stack.appendChild(el);ensureCatalogJumpGlyph(el,'bottom');});
  topBtn=stack.querySelector('a.top');
  bot=stack.querySelector('a.bottom')||bot;
  if(topBtn&&bot&&bot.previousElementSibling!==topBtn)stack.insertBefore(topBtn,bot);
  Array.prototype.slice.call(stack.querySelectorAll('a.top'),1).forEach(function(el){el.remove();});
  Array.prototype.slice.call(stack.querySelectorAll('a.bottom'),1).forEach(function(el){el.remove();});
  ensureCatalogJumpGlyph(stack.querySelector('a.top'),'top');
  ensureCatalogJumpGlyph(stack.querySelector('a.bottom'),'bottom');"""

JUMP_OLD = """  var r=main.getBoundingClientRect();
  var gutter=typeof catalogJumpScrollbarGutter==='function'?catalogJumpScrollbarGutter(main):16;
  var right=Math.max(6,Math.round((window.innerWidth||0)-r.right)+gutter);
  var inset=typeof catalogJumpStackBottomInset==='function'?catalogJumpStackBottomInset():0;
  var bottom=Math.max(6,Math.round((window.innerHeight||0)-r.bottom)+12+inset);"""

JUMP_NEW = """  var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||main;
  var r=(sc||main).getBoundingClientRect();
  var gutter=typeof catalogJumpScrollbarGutter==='function'?catalogJumpScrollbarGutter(sc||main):16;
  if(!(gutter>0)||gutter>48)gutter=16;
  var right=Math.max(8,Math.round((window.innerWidth||0)-r.right)+Math.max(8,gutter));
  var inset=typeof catalogJumpStackBottomInset==='function'?catalogJumpStackBottomInset():0;
  var bottom=Math.max(6,Math.round((window.innerHeight||0)-r.bottom)+12+inset);"""

LOG_OLD = """      var _fav=_e.querySelector('.fav-btn');
      var _search=_e.querySelector('.search-popup-btn');
      var _patches=_e.querySelector('details.patches');
      var _hl=_e.querySelector('.hl-body');
      var _cs=_hl?getComputedStyle(_hl):null;
      fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'E',location:'catalog:cardChromeAlign',message:'search/fav/patches bottoms',data:{fav:_box(_fav),search:_box(_search),patches:_box(_patches),gapPatchSearch:_search&&_patches?Math.round(_search.getBoundingClientRect().top-_patches.getBoundingClientRect().bottom):null,gapSearchFav:_search&&_fav?Math.round(_search.getBoundingClientRect().bottom-_fav.getBoundingClientRect().bottom):null,hl:_cs?[_cs.display,_cs.flexGrow,_cs.marginTop].join(','):null},timestamp:Date.now()})}).catch(function(){});"""

LOG_NEW = """      var _fav=_e.querySelector('.fav-btn');
      var _search=_e.querySelector('.search-popup-btn');
      var _patches=_e.querySelector('details.patches');
      var _pl=_e.querySelector('.path-label');
      var _icons=_e.querySelector('.path-action-row');
      var _hl=_e.querySelector('.hl-body');
      var _cs=_hl?getComputedStyle(_hl):null;
      var _jump=document.getElementById('catalogJumpStack');
      var _jr=_jump?_jump.getBoundingClientRect():null;
      var _pr=_patches?_patches.getBoundingClientRect():null;
      fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'chrome-v2',hypothesisId:'G',location:'catalog:cardChromeAlign',message:'path/patches/search/fav/jump',data:{fav:_box(_fav),search:_box(_search),patches:_box(_patches),pathLabel:_box(_pl),icons:_box(_icons),gapPatchSearch:_search&&_patches?Math.round(_search.getBoundingClientRect().top-_patches.getBoundingClientRect().bottom):null,gapSearchFav:_search&&_fav?Math.round(_search.getBoundingClientRect().bottom-_fav.getBoundingClientRect().bottom):null,searchH:_search?Math.round(_search.getBoundingClientRect().height):null,favH:_fav?Math.round(_fav.getBoundingClientRect().height):null,jumpOver:!!(_jr&&_pr&&!(_jr.right<_pr.left||_jr.left>_pr.right||_jr.bottom<_pr.top||_jr.top>_pr.bottom)),hl:_cs?[_cs.display,_cs.flexGrow,_cs.minHeight].join(','):null},timestamp:Date.now()})}).catch(function(){});"""


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
    print(f"  wrote {path.name} {old_size} -> {new_size}")


def patch_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"  {label}: matches {n}, expected 1")
    return text.replace(old, new, 1)


def main() -> None:
    for path in FILES:
        if "portable" in path.name:
            raise SystemExit(f"refusing portable file {path.name}")
        text = path.read_text(encoding="utf-8")
        print(path.name)
        if MARK in text:
            print("  skip (already patched)")
            continue
        text = patch_once(text, CSS_OLD, CSS_NEW, "css")
        text = patch_once(text, RESET_OLD, RESET_NEW, "reset")
        text = patch_once(text, ROW_TOL_OLD, ROW_TOL_NEW, "row-tol")
        text = patch_once(text, ROW_OLD, ROW_NEW, "row-eq")
        text = patch_once(text, PARK_OLD, PARK_NEW, "jump-park")
        text = patch_once(text, JUMP_OLD, JUMP_NEW, "jump-place")
        text = patch_once(text, LOG_OLD, LOG_NEW, "debug-log")
        safe_write(path, text)


if __name__ == "__main__":
    main()
