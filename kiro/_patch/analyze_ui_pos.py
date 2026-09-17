#!/usr/bin/env python3
"""UI position matrix: measure menus/buttons across display states. Analysis only."""
import json, os, sys, time, base64, urllib.request, subprocess

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/analyze_ui_pos.json"
SHOTS = "/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots"
INGEST = "http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51"
PORT = 9367
PROFILE = "/tmp/catalog-ui-pos"
os.makedirs(PROFILE, exist_ok=True)
os.makedirs(SHOTS, exist_ok=True)
subprocess.run(["pkill", "-f", "remote-debugging-port=9367"], check=False)
time.sleep(0.3)
logf = open("/tmp/catalog-ui-pos.log", "w")
proc = subprocess.Popen([
    "/usr/lib/chromium/chromium", "--headless=new", "--disable-gpu", "--no-first-run",
    "--disable-extensions", f"--remote-debugging-port={PORT}", "--remote-allow-origins=*",
    f"--user-data-dir={PROFILE}", "--noerrdialogs", "--ozone-platform=headless",
    "--ozone-override-screen-size=2220,1250", "--use-angle=swiftshader-webgl", "about:blank"
], stdout=logf, stderr=subprocess.STDOUT)
for _ in range(80):
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=1).read()
        break
    except Exception:
        time.sleep(0.25)
else:
    open(OUT, "w").write(json.dumps({"err": "cdp"}))
    sys.exit(1)

import websocket

def new_tab(url):
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/json/new?" + url, method="PUT")
    return json.load(urllib.request.urlopen(req))

class CDP:
    def __init__(self, url):
        self.ws = websocket.create_connection(url, timeout=90)
        self.id = 0
    def call(self, method, params=None, timeout=180):
        self.id += 1
        mid = self.id
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        end = time.time() + timeout
        while time.time() < end:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg.get("result", {})
        raise TimeoutError(method)

MEASURE = r"""
(() => {
  function sleep(ms){return new Promise(r=>setTimeout(r,ms));}
  function rect(el){
    if(!el) return null;
    var b=el.getBoundingClientRect();
    var cs=getComputedStyle(el);
    return {
      x:Math.round(b.x), y:Math.round(b.y), w:Math.round(b.width), h:Math.round(b.height),
      bottom:Math.round(b.bottom), right:Math.round(b.right),
      pos:cs.position, disp:cs.display, vis:cs.visibility, ov:cs.overflow,
      ovx:cs.overflowX, ovy:cs.overflowY, z:cs.zIndex, pe:cs.pointerEvents,
      style:(el.getAttribute('style')||'').slice(0,180)
    };
  }
  function q(sel){return document.querySelector(sel);}
  function visBtn(sel, all){
    var els=all?document.querySelectorAll(sel):[q(sel)];
    var out=[];
    els.forEach(function(el){
      if(!el){ out.push({sel:sel,exists:false}); return; }
      var r=el.getBoundingClientRect(); var cs=getComputedStyle(el);
      var shown=cs.display!=='none' && cs.visibility!=='hidden' && r.width>1 && r.height>1;
      var off=r.right<0||r.bottom<0||r.left>innerWidth||r.top>innerHeight;
      var clip=r.left<0||r.right>innerWidth+2||r.top<0||r.bottom>innerHeight+2;
      out.push({sel:sel, id:el.id||'', txt:(el.textContent||'').trim().slice(0,28),
        exists:true, shown:shown, off:off, clip:clip, aria:el.getAttribute('aria-hidden'),
        x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height),
        disp:cs.display, vis:cs.visibility, z:cs.zIndex});
    });
    return all?out:(out[0]||{sel:sel,exists:false});
  }
  function parentChain(el, n){
    var a=[]; var i=0;
    while(el && i<n){ a.push(el.id||el.className||el.tagName); el=el.parentElement; i++; }
    return a;
  }
  function overlap(a,b){
    if(!a||!b||a.w<2||b.w<2||a.h<2||b.h<2) return null;
    if(a.disp==='none'||b.disp==='none') return null;
    var ix=Math.max(0, Math.min(a.x+a.w,b.x+b.w)-Math.max(a.x,b.x));
    var iy=Math.max(0, Math.min(a.y+a.h,b.y+b.h)-Math.max(a.y,b.y));
    if(ix<4||iy<4) return null;
    return {ix:ix, iy:iy};
  }
  function logIngest(hid, loc, msg, data){
    try{
      fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{
        method:'POST',
        headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},
        body:JSON.stringify({sessionId:'f491c2',runId:'ui-pos',hypothesisId:hid,location:loc,message:msg,data:data,timestamp:Date.now()})
      }).catch(function(){});
    }catch(e){}
  }
  window.__uiPosApply = async function(s){
    function resetChrome(){
      document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed');
      if(typeof showSearchExtras==='function') try{showSearchExtras();}catch(e){}
    }
    if(document.body.classList.contains('layout-edit') && typeof toggleLayoutEdit==='function') toggleLayoutEdit();
    if(document.body.classList.contains('sides-pinned') && typeof toggleDualFsPin==='function') toggleDualFsPin();
    resetChrome();
    var cm0=document.getElementById('catalogMain');
    if(cm0) cm0.scrollTop=0;
    if(s.display==='fs') setDisplayMode('fs',{menu:s.fsMenu||'keywords'});
    else setDisplayMode(s.display||'upper');
    await sleep(90);
    if(s.hide){
      if(typeof collapseSearchMenu==='function') collapseSearchMenu();
      else if(typeof toggleSearchChrome==='function') toggleSearchChrome();
    } else if(s.extras===false){
      document.body.classList.add('search-extras-collapsed');
      var acx=document.getElementById('acList'); if(acx){acx.classList.remove('open');}
    }
    var fw=document.getElementById('filterWrap');
    if(s.kw===true && fw && !fw.classList.contains('open') && typeof toggleFilter==='function') toggleFilter();
    if(s.kw===false && fw && fw.classList.contains('open') && typeof toggleFilter==='function') toggleFilter();
    if(s.ac===true){
      try{ if(typeof showAc==='function') showAc('',{force:true}); }catch(e){}
      var ac=document.getElementById('acList'); if(ac) ac.classList.add('open');
      var sh=document.getElementById('acShell'); if(sh) sh.classList.add('open');
      if(typeof placeAcShell==='function') try{placeAcShell();}catch(e){}
    }
    if(s.ac===false){
      var ac2=document.getElementById('acList'); if(ac2) ac2.classList.remove('open');
      var sh2=document.getElementById('acShell'); if(sh2) sh2.classList.remove('open');
    }
    if(s.edit && !document.body.classList.contains('layout-edit') && typeof toggleLayoutEdit==='function') toggleLayoutEdit();
    if(s.pin && !document.body.classList.contains('sides-pinned') && typeof toggleDualFsPin==='function') toggleDualFsPin();
    if(s.scrollMain){
      var cm=document.getElementById('catalogMain')||document.scrollingElement;
      if(cm){ cm.scrollTop=s.scrollMain; if(typeof syncIndexDock==='function') syncIndexDock(); }
    }
    await sleep(140);
    return true;
  };
  window.__uiPosMeasure = function(meta){
    var vw=innerWidth, vh=innerHeight;
    var sc=document.getElementById('searchChrome');
    var col=document.getElementById('searchCol');
    var sh=document.getElementById('acShell');
    var ac=document.getElementById('acList');
    var fw=document.getElementById('filterWrap');
    var fp=document.getElementById('filterPanel');
    var kw=document.getElementById('kwbar');
    var cm=document.getElementById('catalogMain');
    var ix=document.getElementById('catalogIndex');
    var sep=document.getElementById('dualFsSep');
    var split=document.getElementById('searchSplit');
    var hdr=document.querySelector('.catalog-header');
    var pills=document.querySelector('.search-active-pills');
    var data={
      scenario:meta.id, display:typeof currentDisplay!=='undefined'?currentDisplay:'',
      viewport:{w:vw,h:vh},
      body:document.body.className,
      parents:{
        searchChrome:parentChain(sc,4),
        filterWrap:parentChain(fw,4),
        acShell:parentChain(sh,4)
      },
      rects:{
        searchChrome:rect(sc), searchCol:rect(col), acShell:rect(sh), acList:rect(ac),
        filterWrap:rect(fw), filterPanel:rect(fp), kwbar:rect(kw),
        catalogMain:rect(cm), catalogIndex:rect(ix), header:rect(hdr),
        dualFsSep:rect(sep), searchSplit:rect(split), pills:rect(pills),
        displaySwitch:rect(document.getElementById('displaySwitch')),
        themePicker:rect(document.getElementById('themePicker')),
        top:rect(q('a.top')), fsModeNav:rect(document.getElementById('kwFsModeNav'))
      },
      buttons:{
        shade:visBtn('.mode-btn[data-mode="shade"]', true),
        searchMode:visBtn('.mode-btn[data-mode="search"]', true),
        hide:visBtn('.search-strip-hide'),
        tap:visBtn('.tap-add-btn', true),
        clear:visBtn('.search-strip-clear'),
        clearMiss:visBtn('.clear-miss-btn', true),
        fs:visBtn('#searchStripFs'),
        kwFs:visBtn('.kw-fs-btn'),
        edit:visBtn('.layout-edit-btn', true),
        pin:visBtn('#dualFsSepPin'),
        displayUpper:visBtn('[data-display="upper"]'),
        displaySides:visBtn('[data-display="sides"]'),
        displayFs:visBtn('[data-display="fs"]'),
        top:visBtn('a.top'),
        indexToggle:visBtn('#catalogIndexToggle'),
        companionAc:visBtn('#acCompanionBtn'),
        companionKw:visBtn('#kwCompanionBtn'),
        theme:visBtn('#themePicker'),
        displaySwitch:visBtn('#displaySwitch')
      },
      leftover:{
        dualStyle:sep?(sep.getAttribute('style')||''):null,
        splitStyle:split?(split.getAttribute('style')||''):null,
        sidesLw:getComputedStyle(document.body).getPropertyValue('--sides-lw').trim(),
        sidesRw:getComputedStyle(document.body).getPropertyValue('--sides-rw').trim(),
        dualFs:document.body.classList.contains('dual-fs-open'),
        acFs:document.body.classList.contains('ac-fs-open'),
        kwFs:document.body.classList.contains('kw-fs-open')
      }
    };
    var R=data.rects;
    var ov=[];
    [['acList','filterWrap'],['acShell','filterWrap'],['searchChrome','filterWrap'],
     ['catalogIndex','filterWrap'],['top','filterWrap'],['top','catalogIndex'],
     ['dualFsSep','searchChrome'],['dualFsSep','displaySwitch'],['searchSplit','searchChrome'],
     ['acList','searchStrip'],['kwbar','acList'],['header','filterWrap'],
     ['displaySwitch','themePicker']].forEach(function(pair){
      var a=R[pair[0]], b=R[pair[1]];
      if(pair[0]==='searchStrip') a=rect(document.getElementById('searchStrip'));
      var hit=overlap(a,b);
      if(hit) ov.push({a:pair[0],b:pair[1],ix:hit.ix,iy:hit.iy});
    });
    data.overlaps=ov;
    data.gaps={
      chromeLeft:R.searchChrome?R.searchChrome.x:null,
      chromeRight:R.searchChrome?vw-R.searchChrome.right:null,
      fwRight:R.filterWrap?vw-R.filterWrap.right:null,
      fwLeft:R.filterWrap?R.filterWrap.x:null,
      topRight:R.top?vw-R.top.right:null,
      headerRight:R.header?vw-R.header.right:null,
      themeRight:R.themePicker?vw-R.themePicker.right:null
    };
    var issues=[];
    var hid=meta.hid||'H?';
    if(data.display==='upper' || data.display==='fs'){
      if(R.dualFsSep && R.dualFsSep.disp!=='none' && R.dualFsSep.w>2 && R.dualFsSep.h>20)
        issues.push({h:'H1',m:'dualFsSep visible after leaving sides',r:R.dualFsSep});
      if(R.searchSplit && R.searchSplit.pos==='fixed' && R.searchSplit.disp!=='none' && R.searchSplit.w>2)
        issues.push({h:'H1',m:'searchSplit fixed leftover',r:R.searchSplit});
    }
    if(data.display==='upper' && fw && sc && sc.contains(fw)){
      if(R.filterWrap && R.searchChrome && R.filterWrap.h>40 && R.searchChrome.ov==='hidden')
        issues.push({h:'H2',m:'searchChrome overflow hidden clips nested keywords'});
      if(ov.some(function(x){return (x.a==='acList'||x.a==='acShell') && x.b==='filterWrap';}))
        issues.push({h:'H2',m:'AC overlaps Keywords in Upper'});
    }
    if(data.display==='sides' && document.body.classList.contains('search-chrome-collapsed')){
      if(R.searchChrome && R.searchChrome.w>120)
        issues.push({h:'H3',m:'hide-search sides gutter still wide',w:R.searchChrome.w});
      var hide=data.buttons.hide;
      if(!hide.shown) issues.push({h:'H3',m:'restore Search chip hidden'});
    }
    if(data.display==='fs'){
      var ds=data.buttons.displaySwitch;
      if(!ds.shown) issues.push({h:'H4',m:'displaySwitch hidden in Full'});
      if(R.filterWrap && R.filterWrap.h>vh*0.7 && R.catalogMain && R.catalogMain.h<80)
        issues.push({h:'H4',m:'Full menu covers catalog',fwH:R.filterWrap.h,cmH:R.catalogMain.h});
    }
    if(vw<900){
      var sb=data.buttons.displaySides;
      if(sb.shown) issues.push({h:'H5',m:'Sides button visible on mobile'});
      if(data.leftover.sidesLw) issues.push({h:'H5',m:'leftover --sides-lw on mobile',v:data.leftover.sidesLw});
    }
    if((data.display==='upper'||data.display==='fs') && document.body.classList.contains('layout-edit')){
      var handles=0;
      if(R.searchSplit && R.searchSplit.disp!=='none' && R.searchSplit.w>4) handles++;
      if(R.dualFsSep && R.dualFsSep.disp!=='none' && R.dualFsSep.w>4) handles++;
      if(!handles) issues.push({h:'H6',m:'edit-layout on but no resize handles in '+data.display});
    }
    if(data.display==='sides'){
      if(ov.some(function(x){return x.a==='catalogIndex'&&x.b==='filterWrap';}))
        issues.push({h:'H7',m:'index dock overlaps Keywords'});
      if(ov.some(function(x){return x.a==='top'&&x.b==='filterWrap';}))
        issues.push({h:'H7',m:'top button overlaps Keywords'});
    }
    if(sKwClosedSpace(data, fw, ac)) issues.push({h:'H8',m:'closed KW/AC still occupy space'});
    function sKwClosedSpace(d, fwEl, acEl){
      var kwOpen=document.body.classList.contains('kw-open')||(fwEl&&fwEl.classList.contains('open'));
      if(!kwOpen && d.rects.filterPanel && d.rects.filterPanel.h>24 && d.rects.filterPanel.disp!=='none') return true;
      if(acEl && !acEl.classList.contains('open') && d.rects.acList && d.rects.acList.h>40 && d.rects.acList.disp!=='none') return true;
      return false;
    }
    Object.keys(data.buttons).forEach(function(k){
      var b=data.buttons[k];
      var arr=Array.isArray(b)?b:[b];
      arr.forEach(function(x){
        if(x.shown && x.off) issues.push({h:'H5',m:'button off-screen '+k+' '+x.txt});
        if(x.shown && x.clip && (k==='displaySwitch'||k==='theme'||k==='hide'))
          issues.push({h:'H5',m:'button clipped '+k});
      });
    });
    data.issues=issues;
    data.flags={
      fwInChrome:!!(fw&&sc&&sc.contains(fw)),
      acOpen:!!(ac&&ac.classList.contains('open')),
      kwOpen:!!(fw&&fw.classList.contains('open')),
      hide:document.body.classList.contains('search-chrome-collapsed'),
      extras:document.body.classList.contains('search-extras-collapsed'),
      edit:document.body.classList.contains('layout-edit'),
      pin:document.body.classList.contains('sides-pinned'),
      ixCollapsed:!!(ix&&ix.classList.contains('is-collapsed'))
    };
    logIngest(hid, 'uiPosMeasure', meta.id, {
      scenario:meta.id, display:data.display, viewport:data.viewport,
      parents:data.parents, rects:summarizeRects(data.rects), leftover:data.leftover,
      overlaps:data.overlaps, gaps:data.gaps, issues:issues, flags:data.flags,
      buttons:compactBtns(data.buttons)
    });
    function summarizeRects(rr){
      var o={};
      Object.keys(rr).forEach(function(k){
        var r=rr[k]; if(!r){o[k]=null;return;}
        o[k]={x:r.x,y:r.y,w:r.w,h:r.h,bottom:r.bottom,pos:r.pos,disp:r.disp,ov:r.ov,z:r.z,style:r.style};
      });
      return o;
    }
    function compactBtns(bt){
      var o={};
      Object.keys(bt).forEach(function(k){
        var b=bt[k];
        if(Array.isArray(b)) o[k]=b.map(function(x){return {shown:x.shown,off:x.off,txt:x.txt,w:x.w,h:x.h,disp:x.disp};});
        else o[k]={shown:b.shown,off:b.off,txt:b.txt,w:b.w,h:b.h,disp:b.disp};
      });
      return o;
    }
    return data;
  };
  return {ok:true};
})()
"""

def ev(cdp, expr, await_promise=False):
    params = {"expression": expr, "returnByValue": True}
    if await_promise:
        params["awaitPromise"] = True
    return cdp.call("Runtime.evaluate", params)

def wait_ready(cdp, needle, seconds=45):
    end = time.time() + seconds
    last = None
    while time.time() < end:
        r = ev(cdp, "document.readyState+':'+typeof setDisplayMode+':'+typeof __uiPosMeasure+':'+document.querySelectorAll('.entry').length")
        last = (r.get("result") or {}).get("value")
        if isinstance(last, str) and last.startswith("complete:function") and ":function:" in last:
            try:
                n = int(str(last).rsplit(":", 1)[-1])
                if n > 5:
                    return last
            except Exception:
                pass
        if isinstance(last, str) and last.startswith("complete:function:undefined"):
            ev(cdp, MEASURE)
        time.sleep(0.35)
    return last

def viewport(cdp, w, h, mobile=False):
    cdp.call("Emulation.setDeviceMetricsOverride", {
        "width": w, "height": h, "deviceScaleFactor": 1 if not mobile else 2,
        "mobile": mobile
    })

def post_ingest(hid, loc, msg, data):
    payload = json.dumps({
        "sessionId": "f491c2", "runId": "ui-pos", "hypothesisId": hid,
        "location": loc, "message": msg, "data": data, "timestamp": int(time.time() * 1000)
    }).encode()
    req = urllib.request.Request(INGEST, data=payload, method="POST", headers={
        "Content-Type": "application/json", "X-Debug-Session-Id": "f491c2"
    })
    try:
        urllib.request.urlopen(req, timeout=2).read()
    except Exception:
        pass

def shot(cdp, name):
    try:
        raw = cdp.call("Page.captureScreenshot", {"format": "png", "fromSurface": True})
        b64 = raw.get("data")
        if not b64:
            return None
        path = os.path.join(SHOTS, name + ".png")
        open(path, "wb").write(base64.b64decode(b64))
        return path
    except Exception as e:
        return str(e)

def apply_and_measure(cdp, spec, hid):
    spec_js = json.dumps(spec)
    ev(cdp, f"window.__uiPosApply({spec_js})", await_promise=True)
    time.sleep(0.08)
    r = ev(cdp, f"window.__uiPosMeasure({json.dumps({'id': spec['id'], 'hid': hid})})")
    if r.get("exceptionDetails"):
        return {"err": r.get("exceptionDetails"), "id": spec["id"]}
    return (r.get("result") or {}).get("value")

SCENARIOS_D1400 = [
    ({"id": "D1400-upper-exp-kwclosed-acclosed", "display": "upper", "kw": False, "ac": False}, "H8"),
    ({"id": "D1400-upper-exp-kwopen-acclosed", "display": "upper", "kw": True, "ac": False}, "H2"),
    ({"id": "D1400-upper-exp-kwopen-acopen", "display": "upper", "kw": True, "ac": True}, "H2"),
    ({"id": "D1400-upper-hide", "display": "upper", "hide": True, "kw": True}, "H3"),
    ({"id": "D1400-upper-extras-collapsed", "display": "upper", "extras": False, "kw": True}, "H8"),
    ({"id": "D1400-upper-edit", "display": "upper", "kw": True, "edit": True}, "H6"),
    ({"id": "D1400-sides-exp-kwopen-acopen", "display": "sides", "kw": True, "ac": True}, "H7"),
    ({"id": "D1400-sides-hide", "display": "sides", "hide": True, "kw": True}, "H3"),
    ({"id": "D1400-sides-kwclosed", "display": "sides", "kw": False, "ac": True}, "H8"),
    ({"id": "D1400-sides-edit", "display": "sides", "kw": True, "edit": True}, "H6"),
    ({"id": "D1400-sides-pin", "display": "sides", "kw": True, "pin": True}, "H1"),
    ({"id": "D1400-sides-index-exp", "display": "sides", "kw": True, "scrollMain": 0}, "H7"),
    ({"id": "D1400-sides-index-compact", "display": "sides", "kw": True, "scrollMain": 420}, "H7"),
    ({"id": "D1400-sides-extras-collapsed", "display": "sides", "extras": False, "kw": True}, "H8"),
    ({"id": "D1400-fs-search", "display": "fs", "fsMenu": "search", "ac": True}, "H4"),
    ({"id": "D1400-fs-keywords", "display": "fs", "fsMenu": "keywords", "kw": True}, "H4"),
    ({"id": "D1400-fs-both-coerces", "display": "fs", "fsMenu": "both"}, "H4"),
    ({"id": "D1400-fs-edit", "display": "fs", "fsMenu": "keywords", "edit": True}, "H6"),
]

TRANSITIONS = [
    ("D1400-trans-sides-upper", "sides", "upper", "H1"),
    ("D1400-trans-sides-fs-upper", "chain", None, "H1"),
    ("D1400-trans-fs-sides", "fs", "sides", "H1"),
]

def slim(m):
    if not isinstance(m, dict):
        return m
    keep = ["scenario", "display", "viewport", "parents", "leftover", "overlaps", "gaps",
            "issues", "flags", "body"]
    out = {k: m.get(k) for k in keep}
    out["rects"] = {}
    for k, r in (m.get("rects") or {}).items():
        if not r:
            out["rects"][k] = None
        else:
            out["rects"][k] = {kk: r.get(kk) for kk in ("x", "y", "w", "h", "bottom", "pos", "disp", "ov", "z", "style")}
    out["buttons"] = {}
    for k, b in (m.get("buttons") or {}).items():
        arr = b if isinstance(b, list) else [b]
        out["buttons"][k] = [{kk: x.get(kk) for kk in ("shown", "off", "clip", "txt", "w", "h", "disp", "x", "y")} for x in arr if isinstance(x, dict)]
    return out

def main():
    results = {"scenarios": {}, "shots": {}, "kontakt": {}, "mobile": {}, "reload": {}, "large": {}}
    tab = new_tab("about:blank")
    cdp = CDP(tab["webSocketDebuggerUrl"])
    cdp.call("Page.enable")
    cdp.call("Runtime.enable")

    def load(url, w, h, mobile=False):
        viewport(cdp, w, h, mobile)
        cdp.call("Page.navigate", {"url": url})
        ready = wait_ready(cdp, url)
        ev(cdp, MEASURE)
        time.sleep(0.4)
        return ready

    # --- Desktop 1400x900 DS ---
    ready = load("http://127.0.0.1:8788/DS-CATALOG.html?uipos=1", 1400, 900, False)
    results["ready_d1400"] = ready
    post_ingest("H0", "analyze_ui_pos", "start-d1400", {"ready": ready})

    for spec, hid in SCENARIOS_D1400:
        m = apply_and_measure(cdp, spec, hid)
        results["scenarios"][spec["id"]] = slim(m)
        if isinstance(m, dict) and m.get("issues"):
            results["shots"][spec["id"]] = shot(cdp, spec["id"])
        time.sleep(0.05)

    # Transitions
    ev(cdp, "window.__uiPosApply(" + json.dumps({"display": "sides", "kw": True}) + ")", await_promise=True)
    time.sleep(0.15)
    ev(cdp, "setDisplayMode('upper')")
    time.sleep(0.2)
    m = ev(cdp, "window.__uiPosMeasure(" + json.dumps({"id": "D1400-trans-sides-upper", "hid": "H1"}) + ")")
    results["scenarios"]["D1400-trans-sides-upper"] = slim((m.get("result") or {}).get("value"))
    if (results["scenarios"]["D1400-trans-sides-upper"] or {}).get("issues"):
        results["shots"]["D1400-trans-sides-upper"] = shot(cdp, "D1400-trans-sides-upper")

    ev(cdp, "setDisplayMode('sides')")
    time.sleep(0.15)
    ev(cdp, "setDisplayMode('fs',{menu:'keywords'})")
    time.sleep(0.15)
    ev(cdp, "setDisplayMode('upper')")
    time.sleep(0.2)
    m = ev(cdp, "window.__uiPosMeasure(" + json.dumps({"id": "D1400-trans-sides-fs-upper", "hid": "H1"}) + ")")
    results["scenarios"]["D1400-trans-sides-fs-upper"] = slim((m.get("result") or {}).get("value"))
    if (results["scenarios"]["D1400-trans-sides-fs-upper"] or {}).get("issues"):
        results["shots"]["D1400-trans-sides-fs-upper"] = shot(cdp, "D1400-trans-sides-fs-upper")

    ev(cdp, "setDisplayMode('fs',{menu:'search'})")
    time.sleep(0.15)
    ev(cdp, "setDisplayMode('sides')")
    time.sleep(0.2)
    m = ev(cdp, "window.__uiPosMeasure(" + json.dumps({"id": "D1400-trans-fs-sides", "hid": "H1"}) + ")")
    results["scenarios"]["D1400-trans-fs-sides"] = slim((m.get("result") or {}).get("value"))

    # Reload with saved sides
    ev(cdp, "setDisplayMode('sides')")
    time.sleep(0.1)
    cdp.call("Page.reload", {"ignoreCache": False})
    wait_ready(cdp, "reload")
    ev(cdp, MEASURE)
    time.sleep(0.35)
    m = ev(cdp, "window.__uiPosMeasure(" + json.dumps({"id": "D1400-reload-sides", "hid": "H1"}) + ")")
    results["reload"]["D1400-reload-sides"] = slim((m.get("result") or {}).get("value"))
    results["shots"]["D1400-reload-sides"] = shot(cdp, "D1400-reload-sides")

    # Large desktop
    viewport(cdp, 1920, 1080, False)
    ev(cdp, "window.dispatchEvent(new Event('resize'))")
    time.sleep(0.2)
    for spec, hid in [
        ({"id": "D1920-upper-kwopen-acopen", "display": "upper", "kw": True, "ac": True}, "H2"),
        ({"id": "D1920-sides-kwopen-acopen", "display": "sides", "kw": True, "ac": True}, "H7"),
        ({"id": "D1920-fs-keywords", "display": "fs", "fsMenu": "keywords", "kw": True}, "H4"),
    ]:
        m = apply_and_measure(cdp, spec, hid)
        results["large"][spec["id"]] = slim(m)
        if isinstance(m, dict) and m.get("issues"):
            results["shots"][spec["id"]] = shot(cdp, spec["id"])

    # Mobile 390x844 — coerce + leftover
    ev(cdp, "setDisplayMode('sides')")
    time.sleep(0.1)
    viewport(cdp, 390, 844, True)
    ev(cdp, "window.dispatchEvent(new Event('resize'))")
    time.sleep(0.25)
    ev(cdp, MEASURE)
    m = ev(cdp, "window.__uiPosMeasure(" + json.dumps({"id": "M390-from-sides-resize", "hid": "H5"}) + ")")
    results["mobile"]["M390-from-sides-resize"] = slim((m.get("result") or {}).get("value"))
    results["shots"]["M390-from-sides-resize"] = shot(cdp, "M390-from-sides-resize")

    for spec, hid in [
        ({"id": "M390-upper-kwopen-acopen", "display": "upper", "kw": True, "ac": True}, "H2"),
        ({"id": "M390-upper-hide", "display": "upper", "hide": True, "kw": True}, "H3"),
        ({"id": "M390-sides-coerced", "display": "sides", "kw": True}, "H5"),
        ({"id": "M390-fs-keywords", "display": "fs", "fsMenu": "keywords", "kw": True}, "H4"),
        ({"id": "M390-fs-search", "display": "fs", "fsMenu": "search", "ac": True}, "H4"),
    ]:
        m = apply_and_measure(cdp, spec, hid)
        results["mobile"][spec["id"]] = slim(m)
        if isinstance(m, dict) and (m.get("issues") or spec["id"].endswith("coerced")):
            results["shots"][spec["id"]] = shot(cdp, spec["id"])

    # Kontakt spot-check desktop
    viewport(cdp, 1400, 900, False)
    load("http://127.0.0.1:8788/KONTAKT-CATALOG.html?uipos=1", 1400, 900, False)
    for spec, hid in [
        ({"id": "K1400-upper-kwopen-acopen", "display": "upper", "kw": True, "ac": True}, "H2"),
        ({"id": "K1400-sides-kwopen-acopen", "display": "sides", "kw": True, "ac": True}, "H7"),
        ({"id": "K1400-sides-hide", "display": "sides", "hide": True, "kw": True}, "H3"),
        ({"id": "K1400-fs-keywords", "display": "fs", "fsMenu": "keywords", "kw": True}, "H4"),
    ]:
        m = apply_and_measure(cdp, spec, hid)
        results["kontakt"][spec["id"]] = slim(m)
        if isinstance(m, dict) and m.get("issues"):
            results["shots"][spec["id"]] = shot(cdp, spec["id"])
    ev(cdp, "setDisplayMode('sides')")
    time.sleep(0.12)
    ev(cdp, "setDisplayMode('upper')")
    time.sleep(0.2)
    m = ev(cdp, "window.__uiPosMeasure(" + json.dumps({"id": "K1400-trans-sides-upper", "hid": "H1"}) + ")")
    results["kontakt"]["K1400-trans-sides-upper"] = slim((m.get("result") or {}).get("value"))

    # Baseline OK shots
    viewport(cdp, 1400, 900, False)
    load("http://127.0.0.1:8788/DS-CATALOG.html?uipos=2", 1400, 900, False)
    ev(cdp, "window.__uiPosApply(" + json.dumps({"display": "upper", "kw": False, "ac": False}) + ")", await_promise=True)
    results["shots"]["D1400-upper-baseline"] = shot(cdp, "D1400-upper-baseline")
    ev(cdp, "window.__uiPosApply(" + json.dumps({"display": "sides", "kw": True, "ac": True}) + ")", await_promise=True)
    results["shots"]["D1400-sides-baseline"] = shot(cdp, "D1400-sides-baseline")

    # Score
    bad, ok = [], []
    for bucket in ("scenarios", "mobile", "large", "reload", "kontakt"):
        for sid, m in (results.get(bucket) or {}).items():
            if not isinstance(m, dict):
                continue
            issues = m.get("issues") or []
            if issues:
                bad.append({"id": sid, "issues": issues, "display": m.get("display"), "vp": m.get("viewport")})
            else:
                ok.append(sid)
    results["bad"] = bad
    results["ok"] = ok
    open(OUT, "w").write(json.dumps(results, indent=2, default=str))
    post_ingest("H0", "analyze_ui_pos", "done", {"bad": len(bad), "ok": len(ok), "n": len(ok) + len(bad)})
    print("BAD", len(bad), "OK", len(ok))
    for b in bad:
        print(" -", b["id"], [i.get("m") for i in b["issues"]])
    proc.terminate()

if __name__ == "__main__":
    main()
