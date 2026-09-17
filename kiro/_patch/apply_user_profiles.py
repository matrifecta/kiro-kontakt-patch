#!/usr/bin/env python3
"""User profiles (max 12): snapshot layout/pills/session per CATALOG_NS. Keep prior fixes."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]


def add_indent(s, n=1):
    pad = " " * n
    return "\n".join((pad + line) if line.strip() else line for line in s.split("\n"))


def sub(text, old, new, label, optional=False):
    n = text.count(old)
    if n == 1:
        return text.replace(old, new, 1)
    if n > 1:
        raise SystemExit(f"{label}: {n} matches")
    if new in text:
        print(f"  skip {label} (already)")
        return text
    for i in range(1, 9):
        oldi, newi = add_indent(old, i), add_indent(new, i)
        ni = text.count(oldi)
        if ni == 1:
            return text.replace(oldi, newi, 1)
        if ni > 1:
            raise SystemExit(f"{label}: {ni} matches (indent {i})")
        if ni == 0 and newi in text:
            print(f"  skip {label} (already)")
            return text
    if optional:
        print(f"  skip {label}")
        return text
    raise SystemExit(f"{label}: not found")


CSS_OLD = """#portraitFlipBtn[hidden]{display:none!important}"""

CSS_NEW = """#portraitFlipBtn[hidden]{display:none!important}
/* fix-USER-PROFILES: toolbar + overflow menu, match existing chrome */
#hdrProfilesBtn{flex-shrink:0;box-sizing:border-box;min-height:2.25rem;background:transparent;border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:0 .625rem;font-size:.875rem;cursor:pointer;touch-action:manipulation;white-space:nowrap}
#hdrProfilesBtn.is-on,#hdrProfilesBtn[aria-expanded="true"]{background:var(--accent-instrument-bg);color:var(--accent-instrument);border-color:var(--accent-instrument);font-weight:600}
.hdr-layout-btns #hdrProfilesBtn{min-height:2.25rem}
.hdr-profiles-pop{position:absolute;z-index:370;display:flex;flex-direction:column;gap:.35rem;min-width:min(16.5rem,calc(100vw - 1.5rem));max-width:min(22rem,calc(100vw - 1rem));padding:.5rem;background:var(--bg-surface);border:1px solid var(--border);border-radius:8px;box-shadow:0 12px 28px rgba(0,0,0,.38);box-sizing:border-box}
.hdr-profiles-pop[hidden]{display:none!important}
.hdr-profiles-pop .up-title{font-size:.75rem;font-weight:600;color:var(--text-muted);padding:0 .15rem}
.hdr-profiles-pop .up-item{display:flex;align-items:center;gap:.3rem}
.hdr-profiles-pop .up-item>button.up-pick{flex:1 1 auto;text-align:left;min-height:2.25rem;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text);font:inherit;cursor:pointer;padding:0 .55rem}
.hdr-profiles-pop .up-item.is-active>button.up-pick{font-weight:700;border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg)}
.hdr-profiles-pop .up-actions{display:flex;flex-wrap:wrap;gap:.35rem}
.hdr-profiles-pop .up-actions>button,.hdr-profiles-pop .up-item .up-x,.hdr-profiles-pop .up-item .up-ren{min-height:2.25rem;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text);font:inherit;font-size:.8rem;cursor:pointer;padding:0 .5rem}
.hdr-profiles-pop .up-actions>button:disabled{opacity:.45;cursor:not-allowed}
.hdr-profiles-pop .up-msg{font-size:.75rem;color:var(--text-muted)}
body.catalog-portable #hdrProfilesBtn{display:none!important}
@media(max-width:899px),(hover:none) and (pointer:coarse){
  #hdrProfilesBtn{display:none!important}
}"""

JS_OLD = """window.noteMiddleMenuOpened=noteMiddleMenuOpened;
// fix-PORTRAIT-SEP:"""

JS_NEW = r"""window.noteMiddleMenuOpened=noteMiddleMenuOpened;
/* fix-USER-PROFILES: named per-user snapshots, max 12, localStorage only */
var USER_PROFILE_MAX=12;
var _userProfileApplying=false;
var _userProfileBooted=false;
function userProfilesKey(){return 'catalog-user-profiles-'+(window.CATALOG_NS||'catalog');}
function readUserProfileStore(){
  try{
    var o=JSON.parse(localStorage.getItem(userProfilesKey())||'{}');
    if(!o||typeof o!=='object')o={};
    if(!Array.isArray(o.profiles))o.profiles=[];
    o.profiles=o.profiles.filter(function(p){return p&&p.id;}).slice(0,USER_PROFILE_MAX);
    if(o.activeId&&!o.profiles.some(function(p){return p.id===o.activeId;}))o.activeId='';
    return o;
  }catch(e){return {activeId:'',profiles:[]};}
}
function writeUserProfileStore(st){
  if(!st||typeof st!=='object')st={activeId:'',profiles:[]};
  if(!Array.isArray(st.profiles))st.profiles=[];
  st.profiles=st.profiles.filter(function(p){return p&&p.id;}).slice(0,USER_PROFILE_MAX);
  try{localStorage.setItem(userProfilesKey(),JSON.stringify({activeId:st.activeId||'',profiles:st.profiles}));}catch(e){}
}
function userProfileKeyWanted(k){
  if(!k||k===userProfilesKey())return false;
  if(k.indexOf('catalog-google-cse')===0)return false;
  if(/boot|debug|agent-log|c00e3e/i.test(k))return false;
  if(k.indexOf('catalog-')!==0)return false;
  var ns=window.CATALOG_NS||'catalog';
  if(k.indexOf(ns)>=0)return true;
  return ['catalog-theme','catalog-tap-to-add','catalog-clear-on-miss','catalog-portrait-menu-h','catalog-portrait-lw','catalog-portrait-rw','catalog-middle-lw','catalog-middle-menu-h'].indexOf(k)>=0;
}
function snapshotUserProfileCss(){
  var keys=['--sides-lw','--sides-rw','--sides-index-h','--middle-lw','--middle-rw','--middle-menu-h','--portable-lw','--portrait-lw','--portrait-rw','--portrait-menu-h','--fs-ac-h','--fs-kw-h'];
  var o={},cs=getComputedStyle(document.body),cr=getComputedStyle(document.documentElement);
  keys.forEach(function(k){var v=(cs.getPropertyValue(k)||cr.getPropertyValue(k)||'').trim();if(v)o[k]=v;});
  return o;
}
function applyUserProfileCss(o){
  if(!o)return;
  Object.keys(o).forEach(function(k){
    try{document.body.style.setProperty(k,o[k]);document.documentElement.style.setProperty(k,o[k]);}catch(e){}
  });
}
function collectUserProfilePills(){
  try{if(typeof searchKeywords!=='undefined'&&searchKeywords&&searchKeywords.length)return searchKeywords.slice();}catch(e){}
  var out=[];
  document.querySelectorAll('#searchPills .pill-label,.search-active-pills .pill-label').forEach(function(el){
    var t=(el.textContent||'').replace(/^\s+|\s+$/g,'');
    if(t&&out.indexOf(t)<0)out.push(t);
  });
  return out;
}
function snapshotUserProfileData(){
  try{if(typeof persistAllLiveLayouts==='function')persistAllLiveLayouts();}catch(e){}
  try{if(typeof persistPinSessions==='function')persistPinSessions();}catch(e){}
  try{if(typeof persistKwCombos==='function')persistKwCombos();}catch(e){}
  try{if(typeof snapshotCurrentLayoutBucket==='function')snapshotCurrentLayoutBucket();}catch(e){}
  var ls={};
  try{
    for(var i=0;i<localStorage.length;i++){
      var k=localStorage.key(i);
      if(userProfileKeyWanted(k))ls[k]=localStorage.getItem(k);
    }
  }catch(e){}
  var si=document.getElementById('searchInput');
  var selEl=document.querySelector('.entry.selected')||(typeof lastViewedEntry!=='undefined'?lastViewedEntry:null);
  var sid='';
  try{var ac=document.getElementById('acList');var hit=ac&&ac.querySelector('.ac-item.ac-session.is-on,[data-sid].is-on');if(hit)sid=hit.getAttribute('data-sid')||'';}catch(e){}
  return {
    portable:!!window.CATALOG_PORTABLE,
    display:(typeof currentDisplay!=='undefined'&&currentDisplay)||((document.body.classList.contains('display-middle')?'middle':(document.body.classList.contains('display-sides')?'sides':''))),
    searchCollapsed:document.body.classList.contains('search-chrome-collapsed'),
    kwCollapsed:document.body.classList.contains('kw-chrome-collapsed'),
    kwOpen:document.body.classList.contains('kw-open')||!!(document.getElementById('filterWrap')&&document.getElementById('filterWrap').classList.contains('open')),
    extrasCollapsed:document.body.classList.contains('search-extras-collapsed'),
    query:si?si.value:'',
    pills:collectUserProfilePills(),
    activeCat:(typeof activeCat!=='undefined'&&activeCat)||'all',
    selectedId:selEl&&selEl.id||'',
    selectedName:selEl?(selEl.getAttribute('data-name')||''):'',
    theme:document.documentElement.getAttribute('data-theme')||'',
    dataMode:(typeof currentMode!=='undefined'&&currentMode)||'search',
    indexEmbed:!!(document.getElementById('catalogIndex')&&document.getElementById('catalogIndex').classList.contains('is-embedded')),
    docNoteEmbed:!!(document.getElementById('catalogDocNote')&&document.getElementById('catalogDocNote').classList.contains('is-embedded')),
    sessionId:sid,
    css:snapshotUserProfileCss(),
    ls:ls
  };
}
function applyUserProfileLs(data){
  if(!data)return;
  var ls=data.ls||{};
  var keep={};
  Object.keys(ls).forEach(function(k){if(userProfileKeyWanted(k))keep[k]=1;});
  try{
    var drop=[];
    for(var i=0;i<localStorage.length;i++){
      var k=localStorage.key(i);
      if(userProfileKeyWanted(k)&&!keep[k])drop.push(k);
    }
    drop.forEach(function(k){try{localStorage.removeItem(k);}catch(e){}});
    Object.keys(ls).forEach(function(k){
      if(!userProfileKeyWanted(k))return;
      try{if(ls[k]==null)localStorage.removeItem(k);else localStorage.setItem(k,ls[k]);}catch(e){}
    });
  }catch(e){}
  try{
    if(typeof PIN_SESS_KEY!=='undefined'&&typeof lsGet==='function'&&typeof pinSessionStore!=='undefined'){
      var ps=lsGet(PIN_SESS_KEY,{sessions:[],recent:[]});
      pinSessionStore.sessions=ps.sessions||[];
      pinSessionStore.recent=ps.recent||[];
    }
    if(typeof KW_COMBO_KEY!=='undefined'&&typeof lsGet==='function'&&typeof kwComboStore!=='undefined'){
      var kc=lsGet(KW_COMBO_KEY,[]);
      kwComboStore=Array.isArray(kc)?kc:[];
    }
    if(typeof CARD_HIT_KEY!=='undefined'&&typeof lsGet==='function'&&typeof cardHitStore!=='undefined'){
      var ch=lsGet(CARD_HIT_KEY,{});
      cardHitStore=(ch&&typeof ch==='object'&&!Array.isArray(ch))?ch:{};
    }
    if(typeof RECENT_KW_KEY!=='undefined'&&typeof lsGet==='function'&&typeof recentKwStore!=='undefined'){
      var rk=lsGet(RECENT_KW_KEY,[]);
      recentKwStore=Array.isArray(rk)?rk:[];
    }
    if(typeof FAV_KEY!=='undefined'&&typeof lsGet==='function'&&typeof favSet!=='undefined'){
      Object.keys(favSet).forEach(function(n){delete favSet[n];});
      var fa=lsGet(FAV_KEY,[]);
      if(Array.isArray(fa))fa.forEach(function(n){if(n)favSet[n]=1;});
    }
  }catch(e){}
}
function applyUserProfileLive(data){
  if(!data)return;
  if(data.theme&&typeof setTheme==='function')setTheme(data.theme);
  if(data.dataMode&&typeof setMode==='function')try{setMode(data.dataMode);}catch(e){}
  if(data.display&&typeof setDisplayMode==='function'){
    try{setDisplayMode(data.display,{keepMenus:true});}catch(e){try{setDisplayMode(data.display);}catch(e2){}}
  }
  if(data.searchCollapsed){if(typeof collapseSearchMenu==='function')collapseSearchMenu();}
  else if(typeof expandSearchMenu==='function')expandSearchMenu();
  if(data.kwCollapsed){if(typeof collapseKwMenu==='function')collapseKwMenu();}
  else if(typeof expandKwMenu==='function')expandKwMenu();
  document.body.classList.toggle('search-extras-collapsed',!!data.extrasCollapsed);
  applyUserProfileCss(data.css);
  try{if(typeof applyDesktopArrange==='function')applyDesktopArrange();}catch(e){}
  try{if(typeof applyModeSlot==='function')applyModeSlot(data.display||(typeof currentDisplay!=='undefined'?currentDisplay:''));}catch(e){}
  try{if(typeof applySidesCols==='function')applySidesCols();}catch(e){}
  try{if(typeof applyActiveLayoutStore==='function')applyActiveLayoutStore();}catch(e){}
  try{if(typeof applyPortraitSides==='function')applyPortraitSides();}catch(e){}
  try{
    searchKeywords=(data.pills||[]).slice();
    if(typeof renderPills==='function')renderPills();
    if(data.activeCat&&typeof setCat==='function')setCat(data.activeCat);
    else if(typeof renderKwBar==='function')renderKwBar();
    var si=document.getElementById('searchInput');
    if(si&&data.query!=null)si.value=data.query;
    if(typeof applySearch==='function')applySearch();
    if(typeof ensureSearchList==='function')ensureSearchList('profile');
  }catch(e){
    try{(data.pills||[]).forEach(function(k){if(typeof window.addSearchKw==='function')window.addSearchKw(k);});}catch(e2){}
  }
  if(data.selectedId){
    var el=document.getElementById(data.selectedId);
    if(el&&typeof selectEntry==='function')selectEntry(el);
    else if(el&&typeof rememberViewed==='function')rememberViewed(el);
  }
  var idx=document.getElementById('catalogIndex');
  if(idx&&typeof data.indexEmbed==='boolean'){
    idx.classList.toggle('is-embedded',!!data.indexEmbed);
    if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();
    if(data.indexEmbed&&typeof stripIndexCardChrome==='function')try{stripIndexCardChrome(idx);}catch(e){}
  }
  if(typeof restoreFilterUi==='function')restoreFilterUi();
  if(typeof restoreSearchUi==='function')restoreSearchUi();
  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
  if(typeof syncPortraitFlipBtn==='function')syncPortraitFlipBtn();
}
function applyUserProfileData(data){
  if(!data||_userProfileApplying)return;
  _userProfileApplying=true;
  try{
    applyUserProfileLs(data);
    applyUserProfileLive(data);
  }finally{_userProfileApplying=false;}
}
function applyActiveUserProfileLs(){
  var st=readUserProfileStore();
  if(!st.activeId)return;
  var p=null;
  st.profiles.forEach(function(x){if(x.id===st.activeId)p=x;});
  if(p&&p.data)applyUserProfileLs(p.data);
}
function applyActiveUserProfileLive(){
  if(_userProfileBooted)return;
  var st=readUserProfileStore();
  if(!st.activeId){_userProfileBooted=true;return;}
  var p=null;
  st.profiles.forEach(function(x){if(x.id===st.activeId)p=x;});
  if(p&&p.data){
    _userProfileApplying=true;
    try{applyUserProfileLive(p.data);}finally{_userProfileApplying=false;}
  }
  _userProfileBooted=true;
}
function userProfileAutoName(st){
  return 'Profile '+( ((st&&st.profiles&&st.profiles.length)||0)+1 );
}
function newUserProfile(name){
  var st=readUserProfileStore();
  if(st.profiles.length>=USER_PROFILE_MAX)return {ok:false,full:true,store:st};
  if(name==null){
    var typed=window.prompt('Name this profile',userProfileAutoName(st));
    if(typed==null)return {ok:false,cancel:true,store:st};
    name=typed;
  }
  name=String(name||'').replace(/^\s+|\s+$/g,'');
  if(!name)name=userProfileAutoName(st);
  var p={id:'p'+Date.now().toString(36)+Math.random().toString(36).slice(2,6),name:name,savedAt:Date.now(),data:snapshotUserProfileData()};
  st.profiles.push(p);
  st.activeId=p.id;
  writeUserProfileStore(st);
  renderUserProfilesMenu();
  try{fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'profiles',hypothesisId:'UP',location:'user-profiles',message:'new profile',data:{ns:window.CATALOG_NS,id:p.id,name:p.name,n:st.profiles.length},timestamp:Date.now()})}).catch(function(){});}catch(e){}
  return {ok:true,profile:p,store:st};
}
function saveUserProfileCurrent(){
  var st=readUserProfileStore();
  if(!st.activeId)return newUserProfile(userProfileAutoName(st));
  var hit=null;
  st.profiles.forEach(function(p){if(p.id===st.activeId)hit=p;});
  if(!hit)return newUserProfile(userProfileAutoName(st));
  hit.data=snapshotUserProfileData();
  hit.savedAt=Date.now();
  writeUserProfileStore(st);
  renderUserProfilesMenu();
  try{fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'profiles',hypothesisId:'UP',location:'user-profiles',message:'save profile',data:{ns:window.CATALOG_NS,id:hit.id,name:hit.name},timestamp:Date.now()})}).catch(function(){});}catch(e){}
  return {ok:true,profile:hit,store:st};
}
function switchUserProfile(id){
  var st=readUserProfileStore();
  var hit=null;
  st.profiles.forEach(function(p){if(p.id===id)hit=p;});
  if(!hit)return {ok:false,store:st};
  st.activeId=hit.id;
  writeUserProfileStore(st);
  applyUserProfileData(hit.data);
  renderUserProfilesMenu();
  try{fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'profiles',hypothesisId:'UP',location:'user-profiles',message:'switch profile',data:{ns:window.CATALOG_NS,id:hit.id,name:hit.name,pills:(hit.data&&hit.data.pills)||[],flip:document.body.classList.contains('sides-portrait-flip')},timestamp:Date.now()})}).catch(function(){});}catch(e){}
  return {ok:true,profile:hit,store:st};
}
function renameUserProfile(id,name){
  var st=readUserProfileStore();
  var hit=null;
  st.profiles.forEach(function(p){if(p.id===id)hit=p;});
  if(!hit)return {ok:false,store:st};
  if(name==null){
    var typed=window.prompt('Rename profile',hit.name||'');
    if(typed==null)return {ok:false,cancel:true,store:st};
    name=typed;
  }
  name=String(name||'').replace(/^\s+|\s+$/g,'');
  if(!name)name=hit.name||userProfileAutoName(st);
  hit.name=name;
  writeUserProfileStore(st);
  renderUserProfilesMenu();
  return {ok:true,profile:hit,store:st};
}
function deleteUserProfile(id){
  var st=readUserProfileStore();
  st.profiles=st.profiles.filter(function(p){return p.id!==id;});
  if(st.activeId===id)st.activeId=st.profiles[0]?st.profiles[0].id:'';
  writeUserProfileStore(st);
  renderUserProfilesMenu();
  return {ok:true,store:st};
}
function userProfilesStandingOk(){
  if(window.CATALOG_PORTABLE)return false;
  try{return !(window.matchMedia('(max-width:899px)').matches||window.matchMedia('(hover:none) and (pointer:coarse)').matches);}catch(e){return true;}
}
function placeUserProfilesPop(){
  var pop=document.getElementById('hdrProfilesPop');
  var btn=document.getElementById('hdrProfilesBtn');
  var hdr=document.querySelector('.catalog-header')||document.getElementById('hdrCluster');
  if(!pop)return;
  if(hdr&&pop.parentElement!==hdr)hdr.appendChild(pop);
  var br=null;
  if(userProfilesStandingOk()&&btn){
    var cs=getComputedStyle(btn);
    if(cs.display!=='none'&&btn.getBoundingClientRect().width>8)br=btn.getBoundingClientRect();
  }
  if(br){
    var w=Math.min(280,Math.max(220,(window.innerWidth||900)*0.22));
    var left=Math.round(Math.min(Math.max(8,br.right-w), (window.innerWidth||900)-w-8));
    pop.style.position='fixed';
    pop.style.top=Math.round(br.bottom+4)+'px';
    pop.style.left=left+'px';
    pop.style.right='auto';
    pop.style.width=Math.round(w)+'px';
    pop.style.zIndex='420';
  }else{
    var top=hdr?Math.round(hdr.getBoundingClientRect().bottom)+4:56;
    pop.style.position='fixed';
    pop.style.top=top+'px';
    pop.style.right='8px';
    pop.style.left='auto';
    pop.style.width='min(16.5rem,calc(100vw - 16px))';
    pop.style.zIndex='420';
  }
}
function renderUserProfilesMenu(){
  var pop=document.getElementById('hdrProfilesPop');
  if(!pop)return;
  var st=readUserProfileStore();
  pop.innerHTML='';
  var title=document.createElement('div');title.className='up-title';title.textContent='Profiles';
  pop.appendChild(title);
  if(!st.profiles.length){
    var empty=document.createElement('div');empty.className='up-msg';empty.textContent='No saved profiles yet.';
    pop.appendChild(empty);
  }
  st.profiles.forEach(function(p){
    var row=document.createElement('div');row.className='up-item'+(p.id===st.activeId?' is-active':'');
    var pick=document.createElement('button');pick.type='button';pick.className='up-pick';
    pick.textContent=(p.id===st.activeId?'✓ ':'')+(p.name||'Profile');
    pick.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();switchUserProfile(p.id);});
    var ren=document.createElement('button');ren.type='button';ren.className='up-ren';ren.textContent='Rename';
    ren.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();renameUserProfile(p.id);});
    var del=document.createElement('button');del.type='button';del.className='up-x';del.textContent='Delete';
    del.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();deleteUserProfile(p.id);});
    row.appendChild(pick);row.appendChild(ren);row.appendChild(del);
    pop.appendChild(row);
  });
  var actions=document.createElement('div');actions.className='up-actions';
  var save=document.createElement('button');save.type='button';save.textContent=st.activeId?'Save':'Save current';
  save.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();saveUserProfileCurrent();});
  var neu=document.createElement('button');neu.type='button';neu.textContent='New';
  var full=st.profiles.length>=USER_PROFILE_MAX;
  neu.disabled=full;
  neu.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();if(full)return;newUserProfile();});
  actions.appendChild(save);actions.appendChild(neu);
  pop.appendChild(actions);
  if(full){
    var msg=document.createElement('div');msg.className='up-msg';msg.textContent='12 profiles max — delete one to add another.';
    pop.appendChild(msg);
  }
  var btn=document.getElementById('hdrProfilesBtn');
  if(btn){
    btn.classList.toggle('is-on',!!st.activeId);
    btn.setAttribute('aria-pressed',st.activeId?'true':'false');
  }
}
function closeUserProfilesMenu(){
  var pop=document.getElementById('hdrProfilesPop');
  var btn=document.getElementById('hdrProfilesBtn');
  if(pop)pop.setAttribute('hidden','');
  if(btn)btn.setAttribute('aria-expanded','false');
}
function openUserProfilesMenu(){
  var pop=document.getElementById('hdrProfilesPop');
  if(!pop){ensureUserProfilesChrome();pop=document.getElementById('hdrProfilesPop');}
  if(!pop)return;
  if(typeof closePhoneOverflowPops==='function')try{closePhoneOverflowPops();}catch(e){}
  renderUserProfilesMenu();
  placeUserProfilesPop();
  pop.removeAttribute('hidden');
  var btn=document.getElementById('hdrProfilesBtn');
  if(btn)btn.setAttribute('aria-expanded','true');
}
function toggleUserProfilesMenu(){
  var pop=document.getElementById('hdrProfilesPop');
  if(pop&&!pop.hasAttribute('hidden')){closeUserProfilesMenu();return;}
  openUserProfilesMenu();
}
function ensureUserProfilesChrome(){
  var host=document.getElementById('hdrLayoutBtns')||document.getElementById('hdrMenuBtns')||document.getElementById('hdrCluster');
  if(!host)return;
  var btn=document.getElementById('hdrProfilesBtn');
  if(!btn){
    btn=document.createElement('button');
    btn.type='button';btn.id='hdrProfilesBtn';btn.className='hdr-menu-btn';
    btn.textContent='Profiles';
    btn.title='Save and switch user profiles';
    btn.setAttribute('aria-expanded','false');
    btn.setAttribute('aria-haspopup','true');
    btn.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();toggleUserProfilesMenu();});
  }
  if(btn.parentElement!==host)host.appendChild(btn);
  var pop=document.getElementById('hdrProfilesPop');
  if(!pop){
    pop=document.createElement('div');
    pop.id='hdrProfilesPop';pop.className='hdr-profiles-pop';pop.hidden=true;
    pop.addEventListener('click',function(e){e.stopPropagation();});
  }
  var hdr=document.querySelector('.catalog-header')||host;
  if(pop.parentElement!==hdr)hdr.appendChild(pop);
  if(!document.documentElement.dataset.upBound){
    document.documentElement.dataset.upBound='1';
    document.addEventListener('click',function(e){
      var t=e.target;
      if(t&&t.closest&&t.closest('#hdrProfilesBtn,#hdrProfilesPop,#hdrMoreBtn,#hdrMorePop'))return;
      closeUserProfilesMenu();
    });
  }
}
window.USER_PROFILE_MAX=USER_PROFILE_MAX;
window.userProfilesKey=userProfilesKey;
window.readUserProfileStore=readUserProfileStore;
window.snapshotUserProfileData=snapshotUserProfileData;
window.applyUserProfileData=applyUserProfileData;
window.applyActiveUserProfileLs=applyActiveUserProfileLs;
window.applyActiveUserProfileLive=applyActiveUserProfileLive;
window.newUserProfile=newUserProfile;
window.saveUserProfileCurrent=saveUserProfileCurrent;
window.switchUserProfile=switchUserProfile;
window.renameUserProfile=renameUserProfile;
window.deleteUserProfile=deleteUserProfile;
window.openUserProfilesMenu=openUserProfilesMenu;
window.ensureUserProfilesChrome=ensureUserProfilesChrome;
// fix-PORTRAIT-SEP:"""

DESKTOP_MORE_OLD = """  phoneMoreAdd(pop,'Clear on miss',function(){var x=document.getElementById('clearMissBtn');if(x)x.click();});
  phoneMoreAdd(pop,'Customize',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();});
  phoneMoreAdd(pop,'Layouts',function(){var x=document.getElementById('layoutPresetsBtn');if(x)x.click();});"""

DESKTOP_MORE_NEW = """  phoneMoreAdd(pop,'Clear on miss',function(){var x=document.getElementById('clearMissBtn');if(x)x.click();});
  phoneMoreAdd(pop,'Customize',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();});
  phoneMoreAdd(pop,'Layouts',function(){var x=document.getElementById('layoutPresetsBtn');if(x)x.click();});
  phoneMoreAdd(pop,'Profiles',function(){if(typeof openUserProfilesMenu==='function')openUserProfilesMenu();});"""

PORTABLE_MORE_OLD = """  phoneMoreAdd(pop,'Layouts',function(){var x=document.getElementById('layoutPresetsBtn');if(x)x.click();},'Layouts');
  phoneMoreAdd(pop,'Miss',function(){var x=document.getElementById('clearMissBtn');if(x)x.click();},'Clear on miss');"""

PORTABLE_MORE_NEW = """  phoneMoreAdd(pop,'Layouts',function(){var x=document.getElementById('layoutPresetsBtn');if(x)x.click();},'Layouts');
  phoneMoreAdd(pop,'Profiles',function(){if(typeof openUserProfilesMenu==='function')openUserProfilesMenu();},'User profiles');
  phoneMoreAdd(pop,'Miss',function(){var x=document.getElementById('clearMissBtn');if(x)x.click();},'Clear on miss');"""

CHROME_OLD = """  if(typeof syncLayoutEditBtn==='function')syncLayoutEditBtn();"""

CHROME_NEW = """  if(typeof syncLayoutEditBtn==='function')syncLayoutEditBtn();
  if(typeof ensureUserProfilesChrome==='function')ensureUserProfilesChrome();"""

BOOT_LS_DESK_OLD = """  // Landscape defaults to Sides, portrait to Middle. Explicit picks are stored per orientation.
  setDisplayMode(m);"""

BOOT_LS_DESK_NEW = """  // Landscape defaults to Sides, portrait to Middle. Explicit picks are stored per orientation.
  if(typeof applyActiveUserProfileLs==='function')applyActiveUserProfileLs();
  setDisplayMode(m);"""

BOOT_LS_PORT_OLD = """  // Portable boots content-only; opening S/K enters Sides or Middle.
  setDisplayMode(window.CATALOG_PORTABLE?'content':m);"""

BOOT_LS_PORT_NEW = """  // Portable boots content-only; opening S/K enters Sides or Middle.
  if(typeof applyActiveUserProfileLs==='function')applyActiveUserProfileLs();
  setDisplayMode(window.CATALOG_PORTABLE?'content':m);"""

BOOT_LIVE_OLD = """  if(typeof ensureSearchList==='function'){
    ensureSearchList('boot');
    requestAnimationFrame(function(){if(typeof ensureSearchList==='function')ensureSearchList('boot-raf');});
  }"""

BOOT_LIVE_NEW = """  if(typeof ensureSearchList==='function'){
    ensureSearchList('boot');
    requestAnimationFrame(function(){if(typeof ensureSearchList==='function')ensureSearchList('boot-raf');});
  }
  if(typeof applyActiveUserProfileLive==='function')applyActiveUserProfileLive();"""

KEEP = (
    "fix-MIDDLE-ONE-MENU",
    "fix-INDEX-ISOLATE-v3",
    "fix-FOLDER-GLYPH-SIZE-v2",
    "fix-DESKTOP-FLIP-ARRANGE",
    "function desktopArrangeSlotId",
    "noteMiddleMenuOpened",
    "c00e3e",
)


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    n = path.name
    if "fix-USER-PROFILES" in text and "function userProfilesKey" in text:
        print("skip", n)
        return
    text = sub(text, CSS_OLD, CSS_NEW, f"{n}: css")
    text = sub(text, JS_OLD, JS_NEW, f"{n}: js")
    text = sub(text, DESKTOP_MORE_OLD, DESKTOP_MORE_NEW, f"{n}: desktop-more", optional=True)
    text = sub(text, PORTABLE_MORE_OLD, PORTABLE_MORE_NEW, f"{n}: portable-more", optional=True)
    text = sub(text, CHROME_OLD, CHROME_NEW, f"{n}: chrome")
    text = sub(text, BOOT_LS_DESK_OLD, BOOT_LS_DESK_NEW, f"{n}: boot-ls-desk", optional=True)
    text = sub(text, BOOT_LS_PORT_OLD, BOOT_LS_PORT_NEW, f"{n}: boot-ls-port", optional=True)
    text = sub(text, BOOT_LIVE_OLD, BOOT_LIVE_NEW, f"{n}: boot-live")
    raw = text.encode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(raw)
    out = tmp.read_bytes().decode("utf-8")
    if not out.strip().endswith("</html>"):
        tmp.unlink()
        raise SystemExit(f"{n}: truncated")
    if len(raw) < 100000:
        tmp.unlink()
        raise SystemExit(f"{n}: size too small {len(raw)}")
    for keep in KEEP:
        if keep not in out:
            tmp.unlink()
            raise SystemExit(f"{n}: lost {keep}")
    if "fix-USER-PROFILES" not in out or "function userProfilesKey" not in out:
        tmp.unlink()
        raise SystemExit(f"{n}: profiles missing")
    tmp.replace(path)
    print("OK", n, len(raw))


def main() -> None:
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)


if __name__ == "__main__":
    main()
