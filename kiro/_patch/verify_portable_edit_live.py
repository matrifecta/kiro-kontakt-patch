#!/usr/bin/env python3
"""CDP A–G: no Customize 3-pane dupe; portrait KW uncut. Both portable catalogs."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import threading
import time
from collections import deque
from pathlib import Path

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_portable_edit_live.json")
PORT = 9617
HTTP = 8797
PROFILE = "/tmp/catalog-edit-live"
CHROME = next(
    (p for p in ("/usr/lib/chromium/chromium", "/usr/bin/chromium", "/usr/bin/google-chrome") if os.path.exists(p)),
    "/usr/bin/chromium",
)
os.makedirs(PROFILE, exist_ok=True)

PROBE = r"""
(() => {
  const name = %NAME%;
  function vis(el){
    if(!el) return {shown:false,w:0,h:0,x:0,y:0,b:0,r:0,disp:'',pe:'',mh:''};
    const cs=getComputedStyle(el), r=el.getBoundingClientRect();
    const shown=cs.display!=='none' && cs.visibility!=='hidden' && r.width>8 && r.height>8;
    return {
      shown, pe:cs.pointerEvents, disp:cs.display, vis:cs.visibility, zi:cs.zIndex,
      w:Math.round(r.width), h:Math.round(r.height),
      x:Math.round(r.x), y:Math.round(r.y), b:Math.round(r.bottom), r:Math.round(r.right),
      mh:cs.maxHeight, cols:cs.gridTemplateColumns, rows:cs.gridTemplateRows, flexDir:cs.flexDirection
    };
  }
  function cards(){
    const main=document.getElementById('catalogMain');
    if(!main) return {n:0,shown:false};
    const list=[...main.querySelectorAll('.entry')].slice(0,8);
    const hit=list.filter(e=>{
      const r=e.getBoundingClientRect();
      return r.width>24 && r.height>24 && r.bottom>0 && r.top<innerHeight;
    });
    return {n:list.length, shown:hit.length>0, vis:hit.length};
  }
  function hitId(x,y){
    const t=document.elementFromPoint(x,y);
    if(!t) return '';
    if(t.id) return t.id;
    const p=t.closest('#filterWrap,#searchChrome,#catalogMain,#searchSplit,#dualFsSep,.entry');
    return p?(p.id||p.className||'').toString().slice(0,60):((t.className||'')+'').toString().slice(0,60);
  }
  function cssVar(p){return parseInt(getComputedStyle(document.documentElement).getPropertyValue(p),10)||0;}
  function fire(target,type,x,y,buttons,pointerId){
    target.dispatchEvent(new PointerEvent(type,{
      bubbles:true,cancelable:true,composed:true,pointerId:pointerId,pointerType:'mouse',
      clientX:x,clientY:y,buttons:buttons,button:0,view:window
    }));
  }
  function drag(id,dx,dy){
    const el=document.getElementById(id);
    if(!el) return {id,ok:false,reason:'missing'};
    const info=vis(el);
    if(!info.shown) return {id,ok:false,reason:'hidden',info};
    if(info.pe==='none') return {id,ok:false,reason:'pe-none',info};
    const prop=el.getAttribute('data-port-prop')|| (id==='dualFsSep'&&document.body.classList.contains('search-chrome-collapsed')?'--portable-rw':'--portable-lw');
    const axis=el.getAttribute('data-port-axis')||(info.h<=16?'h':'v');
    const before=cssVar(prop);
    const fwB=vis(document.getElementById('filterWrap'));
    const chB=vis(document.getElementById('searchChrome'));
    const x=info.x+Math.max(2,Math.round(info.w/2));
    const y=info.y+Math.max(2,Math.round(info.h/2));
    const top=document.elementFromPoint(x,y);
    const covered=!(top&&(top.id===id||(top.closest&&top.closest('#'+id))));
    if(covered) return {id,ok:false,reason:'covered:'+((top&&(top.id||top.className))||'?'),info,fromPoint:top?(top.id||'') :''};
    const pid=21+Math.floor(Math.random()*4000);
    fire(el,'pointerdown',x,y,1,pid);
    fire(document,'pointermove',x+(axis==='h'?0:dx),y+(axis==='h'?dy:0),1,pid);
    fire(el,'pointermove',x+(axis==='h'?0:dx),y+(axis==='h'?dy:0),1,pid);
    fire(document,'pointerup',x+(axis==='h'?0:dx),y+(axis==='h'?dy:0),0,pid);
    fire(el,'pointerup',x+(axis==='h'?0:dx),y+(axis==='h'?dy:0),0,pid);
    if(typeof placePortableHandles==='function') placePortableHandles();
    const after=cssVar(prop);
    const fwA=vis(document.getElementById('filterWrap'));
    const chA=vis(document.getElementById('searchChrome'));
    let paneDelta=0;
    if(axis==='h'||prop==='--portable-menu-h'){
      const useKw=document.body.classList.contains('search-chrome-collapsed')||prop==='--portable-rw';
      paneDelta=(useKw?fwA.h:chA.h)-(useKw?fwB.h:chB.h);
    }else if(prop==='--portable-rw'){
      paneDelta=(fwA.w||0)-(fwB.w||0);
    }else{
      paneDelta=(chA.w||0)-(chB.w||0);
    }
    const varOk=Math.abs(after-before)>8;
    const paneOk=Math.abs(paneDelta)>8;
    return {id,prop,axis,before,after,delta:after-before,paneDelta,ok:varOk&&paneOk,reason:(!varOk&&'var-stale')||(!paneOk&&'pane-stale')||'',info:vis(el)};
  }
  function apply(spec){
    try{
      if(typeof portableMenuFsOn==='function' && portableMenuFsOn() && typeof portableExitMenuFs==='function') portableExitMenuFs();
      document.body.classList.remove('ac-fs-open','kw-fs-open','dual-fs-open','display-content','portable-edit-3pane');
      document.body.classList.add('display-sides');
      const port=!!(window.matchMedia && window.matchMedia('(orientation:portrait)').matches);
      if(port) document.body.classList.add('display-middle');
      else document.body.classList.remove('display-middle');
      if(spec.search){ document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed'); }
      else { document.body.classList.add('search-chrome-collapsed','search-extras-collapsed'); }
      var fw=document.getElementById('filterWrap');
      if(spec.kw){
        document.body.classList.add('kw-open');
        document.body.classList.remove('kw-chrome-collapsed');
        if(fw) fw.classList.add('open');
      }else{
        document.body.classList.remove('kw-open');
        document.body.classList.add('kw-chrome-collapsed');
        if(fw) fw.classList.remove('open');
      }
      if(spec.edit===false){
        if(document.body.classList.contains('layout-edit') && typeof toggleLayoutEdit==='function') toggleLayoutEdit();
      }else if(!document.body.classList.contains('layout-edit') && typeof toggleLayoutEdit==='function') toggleLayoutEdit();
      if(typeof placeMenusForDisplay==='function') placeMenusForDisplay('sides');
      if(typeof syncPortableLayoutChrome==='function') syncPortableLayoutChrome();
      if(typeof placePortableHandles==='function') placePortableHandles();
    }catch(err){ window._liveApplyErr=String(err&&err.message||err); }
  }
  apply(%SPEC%);
  const ch=document.getElementById('searchChrome');
  const fw=document.getElementById('filterWrap');
  const main=document.getElementById('catalogMain');
  const split=document.getElementById('searchSplit');
  const sep=document.getElementById('dualFsSep');
  const bodyCs=getComputedStyle(document.body);
  const search=vis(ch), kw=vis(fw), mainV=vis(main), splitV=vis(split), sepV=vis(sep);
  const pane=kw.shown?kw:search;
  const midHit=pane.shown?hitId(pane.x+Math.round(pane.w/2), pane.y+Math.round(pane.h*0.5)):'';
  const loHit=pane.shown?hitId(pane.x+Math.round(pane.w/2), pane.y+Math.round(pane.h*0.72)):'';
  const stripeAtMid=!!(midHit==='searchSplit'||midHit==='dualFsSep'||(midHit||'').indexOf('port-stripe')>=0);
  const stripeY=splitV.shown?splitV.y:(sepV.shown?sepV.y:-1);
  const stripeAtEdge=pane.shown && stripeY>=0 && Math.abs(stripeY-(pane.b-6))<=18;
  const cols=bodyCs.gridTemplateColumns||'';
  const colParts=cols.split(' ').filter(Boolean);
  const threeCol=colParts.length>=3 && !/none/i.test(cols);
  const drags=[];
  if(splitV.shown) drags.push(drag('searchSplit',40,48));
  if(sepV.shown) drags.push(drag('dualFsSep',40,48));
  return {
    name, vw:innerWidth, vh:innerHeight,
    orient: (window.matchMedia&&window.matchMedia('(orientation:portrait)').matches)?'portrait':'landscape',
    cls:{
      edit:document.body.classList.contains('layout-edit'),
      edit3:document.body.classList.contains('portable-edit-3pane'),
      pair:document.body.classList.contains('portable-sk-pair'),
      middle:document.body.classList.contains('display-middle'),
      sides:document.body.classList.contains('display-sides'),
      land:document.body.classList.contains('portable-landscape'),
      port:document.body.classList.contains('portable-portrait'),
      sCol:document.body.classList.contains('search-chrome-collapsed'),
      kOpen:document.body.classList.contains('kw-open')
    },
    search, kw, main:mainV, split:splitV, sep:sepV,
    cards:cards(),
    bodyCols:cols, bodyRows:bodyCs.gridTemplateRows, bodyDisp:bodyCs.display, threeCol,
    midHit, loHit, stripeAtMid, stripeAtEdge,
    vars:{lw:cssVar('--portable-lw'),rw:cssVar('--portable-rw'),mh:cssVar('--portable-menu-h')},
    drags, applyErr:window._liveApplyErr||null
  };
})()
"""


def probe_expr(name: str, spec: dict) -> str:
    return PROBE.replace("%NAME%", json.dumps(name)).replace("%SPEC%", json.dumps(spec))


EXIT_JS = r"""
(() => {
  function vis(el){
    if(!el) return {shown:false,w:0,h:0,x:0};
    const cs=getComputedStyle(el), r=el.getBoundingClientRect();
    return {shown:cs.display!=='none'&&cs.visibility!=='hidden'&&r.width>8&&r.height>8,w:Math.round(r.width),h:Math.round(r.height),x:Math.round(r.x)};
  }
  if(typeof portableExitMenuFs==='function' && (typeof portableMenuFsOn==='function'?portableMenuFsOn():'')) portableExitMenuFs();
  document.body.classList.remove('ac-fs-open','kw-fs-open','dual-fs-open','search-chrome-collapsed','kw-chrome-collapsed','display-middle','display-content');
  document.body.classList.add('display-sides','kw-open');
  var fw=document.getElementById('filterWrap'); if(fw) fw.classList.add('open');
  if(!document.body.classList.contains('layout-edit') && typeof toggleLayoutEdit==='function') toggleLayoutEdit();
  if(typeof syncPortableLayoutChrome==='function') syncPortableLayoutChrome();
  if(typeof placePortableHandles==='function') placePortableHandles();
  const inn={
    edit:document.body.classList.contains('layout-edit'),
    edit3:document.body.classList.contains('portable-edit-3pane'),
    pair:document.body.classList.contains('portable-sk-pair'),
    threeCol:(getComputedStyle(document.body).gridTemplateColumns||'').split(' ').filter(Boolean).length>=3,
    main:vis(document.getElementById('catalogMain')),
    search:vis(document.getElementById('searchChrome')),
    kw:vis(document.getElementById('filterWrap')),
    split:vis(document.getElementById('searchSplit')),
    sep:vis(document.getElementById('dualFsSep'))
  };
  if(typeof toggleLayoutEdit==='function') toggleLayoutEdit();
  if(typeof syncPortableLayoutChrome==='function') syncPortableLayoutChrome();
  if(typeof placePortableHandles==='function') placePortableHandles();
  const oute={
    edit:document.body.classList.contains('layout-edit'),
    edit3:document.body.classList.contains('portable-edit-3pane'),
    pair:document.body.classList.contains('portable-sk-pair'),
    threeCol:(getComputedStyle(document.body).gridTemplateColumns||'').split(' ').filter(Boolean).length>=3,
    main:vis(document.getElementById('catalogMain')),
    search:vis(document.getElementById('searchChrome')),
    kw:vis(document.getElementById('filterWrap')),
    split:vis(document.getElementById('searchSplit')),
    sep:vis(document.getElementById('dualFsSep'))
  };
  return {inn, oute};
})()
"""

CASES = [
    ("A-port-kw", 390, 844, "portrait", {"search": False, "kw": True}),
    ("B-port-search", 390, 844, "portrait", {"search": True, "kw": False}),
    ("C-land-both", 844, 390, "landscape", {"search": True, "kw": True}),
    ("D-land-search", 844, 390, "landscape", {"search": True, "kw": False}),
    ("E-land-kw", 844, 390, "landscape", {"search": False, "kw": True}),
    ("F-port-both", 390, 844, "portrait", {"search": True, "kw": True}),
]


def wait_dbg(timeout=20):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            import urllib.request

            tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json", timeout=1))
        except Exception:
            time.sleep(0.25)
            continue
        pages = [t for t in tabs if t.get("type") == "page"]
        if pages and pages[0].get("webSocketDebuggerUrl"):
            return pages[0]["webSocketDebuggerUrl"]
        time.sleep(0.25)
    raise SystemExit("no debugger url")


def metrics(send, ev, w, h, kind):
    send(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": w,
            "height": h,
            "deviceScaleFactor": 2,
            "mobile": True,
            "screenWidth": w,
            "screenHeight": h,
            "screenOrientation": {
                "type": "portraitPrimary" if kind == "portrait" else "landscapePrimary",
                "angle": 0 if kind == "portrait" else 90,
            },
        },
    )
    time.sleep(0.45)
    ev(
        "if(typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();"
        "if(typeof portableRelayoutChrome==='function')portableRelayoutChrome('edit-live'); true"
    )
    time.sleep(0.2)


def judge(row: dict) -> list[str]:
    fails = []
    if not isinstance(row, dict) or row.get("_exc"):
        return [f"{row.get('name','?')}: eval failed {row}"]
    name = row.get("name") or "?"
    cls = row.get("cls") or {}
    search, kw, main = row.get("search") or {}, row.get("kw") or {}, row.get("main") or {}
    split, sep = row.get("split") or {}, row.get("sep") or {}
    cards = row.get("cards") or {}
    drags = row.get("drags") or []
    if cls.get("edit3"):
        fails.append(f"{name}: leftover portable-edit-3pane")
    if row.get("threeCol"):
        fails.append(f"{name}: 3-col grid {row.get('bodyCols')}")
    if name.startswith("A-"):
        if not kw.get("shown"):
            fails.append("A: KW pane hidden")
        if search.get("shown"):
            fails.append("A: Search still shown with docked KW")
        if not main.get("shown"):
            fails.append("A: catalog hidden")
        if not cards.get("shown"):
            fails.append("A: no visible cards")
        if row.get("stripeAtMid"):
            fails.append(f"A: stripe through KW mid ({row.get('midHit')})")
        if kw.get("shown") and (kw.get("h") or 0) < 96:
            fails.append(f"A: KW too short {kw.get('h')}")
        mh = (kw.get("mh") or "").lower()
        if "32dvh" in mh or mh in ("240px", "15rem"):
            fails.append(f"A: KW max-height leftover {kw.get('mh')}")
        if not any(d.get("ok") and d.get("id") == "dualFsSep" for d in drags):
            fails.append(f"A: KW|content sep did not drag {drags}")
        mid, lo = row.get("midHit") or "", row.get("loHit") or ""
        if "catalogMain" in mid or "catalogMain" in lo:
            fails.append(f"A: catalog overlaps KW ({mid}/{lo})")
    if name.startswith("B-"):
        if not search.get("shown"):
            fails.append("B: Search pane hidden")
        if kw.get("shown"):
            fails.append("B: KW shown with docked Search")
        if not main.get("shown") or not cards.get("shown"):
            fails.append("B: catalog missing cards")
        if row.get("stripeAtMid"):
            fails.append(f"B: stripe through Search mid ({row.get('midHit')})")
        if not any(d.get("ok") and d.get("id") == "searchSplit" for d in drags):
            fails.append(f"B: Search|content sep did not drag {drags}")
    if name.startswith("C-"):
        if cls.get("edit3"):
            fails.append("C: 3-pane class on")
        if not cls.get("pair"):
            fails.append("C: missing portable-sk-pair")
        if not search.get("shown") or not kw.get("shown"):
            fails.append("C: SK-pair missing a menu")
        if main.get("shown"):
            fails.append("C: empty third content column present")
        if sep.get("shown"):
            fails.append("C: extra KW stripe; should be one S|K sep")
        if not split.get("shown"):
            fails.append("C: missing S|K sep")
        if not any(d.get("ok") and d.get("id") == "searchSplit" for d in drags):
            fails.append(f"C: S|K sep did not drag {drags}")
        if abs((search.get("x") or 0) - (kw.get("x") or 0)) < 40:
            fails.append("C: Search and KW not side by side")
    if name.startswith("D-"):
        if not search.get("shown"):
            fails.append("D: Search hidden")
        if kw.get("shown"):
            fails.append("D: KW shown in Search-only")
        if not main.get("shown") or not cards.get("shown"):
            fails.append("D: content missing cards")
        if not any(d.get("ok") and d.get("id") == "searchSplit" for d in drags):
            fails.append(f"D: Search|content sep did not drag {drags}")
    if name.startswith("E-"):
        if not kw.get("shown"):
            fails.append("E: KW hidden")
        if search.get("shown"):
            fails.append("E: Search shown in KW-only")
        if not main.get("shown") or not cards.get("shown"):
            fails.append("E: content missing cards")
        if not any(d.get("ok") and d.get("id") == "dualFsSep" for d in drags):
            fails.append(f"E: content|KW sep did not drag {drags}")
    if name.startswith("F-"):
        if cls.get("edit3") or row.get("threeCol"):
            fails.append("F: Customize became 3-region/3-col")
        both = bool(search.get("shown") and kw.get("shown"))
        if both:
            fails.append("F: stacked both menus still shown")
        if not cls.get("middle"):
            fails.append("F: not Middle")
        if not main.get("shown") or not cards.get("shown"):
            fails.append("F: content missing cards")
        if not drags or not any(d.get("ok") for d in drags):
            fails.append(f"F: menu|content sep did not drag {drags}")
    return fails


def run_catalog(send, ev, events, file_name: str) -> dict:
    send("Page.navigate", {"url": f"http://127.0.0.1:{HTTP}/{file_name}?live={int(time.time())}"})
    t0 = time.time()
    loaded = False
    while time.time() - t0 < 40:
        while events:
            if events.popleft().get("method") == "Page.loadEventFired":
                loaded = True
        if loaded:
            break
        time.sleep(0.1)
    time.sleep(1.6)
    out = {"file": file_name, "cases": {}, "exit": None}
    last_kind = None
    for name, w, h, kind, spec in CASES:
        if last_kind != kind:
            metrics(send, ev, w, h, kind)
            last_kind = kind
        out["cases"][name] = ev(probe_expr(name, spec))
        time.sleep(0.12)
    metrics(send, ev, 844, 390, "landscape")
    out["exit"] = ev(EXIT_JS)
    return out


def summarize(cat: dict) -> dict:
    fails = []
    for name, row in (cat.get("cases") or {}).items():
        fails.extend(judge(row))
    ex = cat.get("exit") or {}
    if isinstance(ex, dict):
        inn, oute = ex.get("inn") or {}, ex.get("oute") or {}
        if inn.get("edit3") or inn.get("threeCol"):
            fails.append("G-in: Customize both used 3-pane/3-col")
        if inn.get("main", {}).get("shown"):
            fails.append("G-in: Customize both still has content column")
        if not inn.get("pair"):
            fails.append("G-in: Customize both missing SK-pair")
        if oute.get("edit"):
            fails.append("G: still in layout-edit")
        if oute.get("edit3") or oute.get("threeCol"):
            fails.append("G: leftover 3-col/3-pane after Done")
        if not oute.get("pair"):
            fails.append("G: landscape both did not keep SK-pair")
        if oute.get("main", {}).get("shown"):
            fails.append("G: SK-pair still showing content")
        if (oute.get("split") or {}).get("shown") or (oute.get("sep") or {}).get("shown"):
            fails.append("G: dead seps left after Customize")
    return {"fails": fails, "ok": not fails}


def run():
    import urllib.request
    import websocket

    urllib.request.urlopen("http://127.0.0.1:8797/KONTAKT-CATALOG-portable.html", timeout=3).read(64)
    proc = subprocess.Popen(
        [
            CHROME,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            f"--remote-debugging-port={PORT}",
            "--remote-allow-origins=*",
            f"--user-data-dir={PROFILE}",
            "--disable-http-cache",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        ws = websocket.create_connection(wait_dbg(), timeout=20)
        box = {"id": 0}
        pending = {}
        events = deque()

        def send(method, params=None):
            box["id"] += 1
            mid = box["id"]
            payload = {"id": mid, "method": method}
            if params:
                payload["params"] = params
            pending[mid] = {"ev": threading.Event(), "res": None}
            ws.send(json.dumps(payload))
            ok = pending[mid]["ev"].wait(25)
            res = pending[mid]["res"]
            pending.pop(mid, None)
            if not ok:
                raise TimeoutError(method)
            return res

        def reader():
            while True:
                try:
                    raw = ws.recv()
                except Exception:
                    break
                data = json.loads(raw)
                if "id" in data and data["id"] in pending:
                    pending[data["id"]]["res"] = data
                    pending[data["id"]]["ev"].set()
                else:
                    events.append(data)

        threading.Thread(target=reader, daemon=True).start()
        send("Page.enable")
        send("Runtime.enable")
        send("Network.enable")
        send("Network.setCacheDisabled", {"cacheDisabled": True})

        def ev(expr):
            res = send("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": False})
            if res.get("result", {}).get("exceptionDetails"):
                return {"_exc": res["result"]["exceptionDetails"]}
            return res.get("result", {}).get("result", {}).get("value")

        report = {}
        for fname in ("KONTAKT-CATALOG-portable.html", "DS-CATALOG-portable.html"):
            cat = run_catalog(send, ev, events, fname)
            cat["summary"] = summarize(cat)
            report[fname] = cat
        OUT.write_text(json.dumps(report, indent=2)[:600000])
        fails = []
        for fname, cat in report.items():
            for f in cat["summary"]["fails"]:
                fails.append(f"{fname}: {f}")
        print(json.dumps({"ok": not fails, "fails": fails, "out": str(OUT)}, indent=2))
        return 0 if not fails else 1
    finally:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(run())
