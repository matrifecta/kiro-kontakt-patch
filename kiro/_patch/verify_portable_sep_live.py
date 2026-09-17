#!/usr/bin/env python3
"""CDP: every visible Customize stripe drags; no dead hit targets. Both portable catalogs."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import threading
import time
from collections import deque
from pathlib import Path

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_portable_sep_live.json")
PORT = 9598
HTTP = 8797
PROFILE = "/tmp/catalog-sep-live"
CHROME = next(
    (p for p in ("/usr/lib/chromium/chromium", "/usr/bin/chromium", "/usr/bin/google-chrome") if os.path.exists(p)),
    "/usr/bin/chromium",
)
os.makedirs(PROFILE, exist_ok=True)

SETUP = r"""
(() => {
  window._sepProbeOrient = function(){
    try{
      if(window.matchMedia && window.matchMedia('(orientation:portrait)').matches) return 'portrait';
    }catch(e){}
    return (innerWidth < innerHeight) ? 'portrait' : 'landscape';
  };
  try{sidesPinned=false;}catch(e){}
  document.body.classList.remove('sides-pinned','mode-layout-pinned');
  if(!document.body.classList.contains('layout-edit') && typeof toggleLayoutEdit==='function') toggleLayoutEdit();
  if(typeof bindIndexHeight==='function') bindIndexHeight();
  if(typeof placePortableHandles==='function') placePortableHandles();
  return document.body.classList.contains('layout-edit');
})()
"""

COMBO_JS = r"""
(() => {
  try {
  const name = %NAME%;
  function vis(el){
    if(!el) return {shown:false};
    const cs=getComputedStyle(el), r=el.getBoundingClientRect();
    return {
      shown: cs.display!=='none' && cs.visibility!=='hidden' && r.width>2 && r.height>2,
      pe: cs.pointerEvents, disp: cs.display, vis: cs.visibility,
      w: Math.round(r.width), h: Math.round(r.height),
      x: Math.round(r.x), y: Math.round(r.y)
    };
  }
  function stripe(id){
    const el=document.getElementById(id);
    const o=vis(el);
    o.id=id;
    o.missing=!el;
    if(el){
      o.prop=el.getAttribute('data-port-prop')||'';
      o.axis=el.getAttribute('data-port-axis')||'';
      o.grow=el.getAttribute('data-port-grow')||'';
      o.cls=el.className||'';
    }
    o.hit = !!(o.shown && o.pe!=='none' && ((o.axis==='v'&&o.w>=6&&o.h>=24)||(o.axis==='h'&&o.h>=6&&o.w>=24)||(id==='indexHeight'&&o.shown&&o.pe!=='none'&&o.w>=24&&o.h>=4)));
    return o;
  }
  function cssVar(p, el){
    const cs=getComputedStyle(el||document.documentElement);
    return parseInt(cs.getPropertyValue(p),10)||0;
  }
  function fire(target, type, x, y, buttons, pointerId){
    const ev=new PointerEvent(type,{
      bubbles:true,cancelable:true,composed:true,pointerId:pointerId||(7+Math.floor(Math.random()*1000)),pointerType:'mouse',
      clientX:x,clientY:y,buttons:buttons,button:0,view:window
    });
    target.dispatchEvent(ev);
  }
  function drag(id, dx, dy, propOverride){
    const el=document.getElementById(id);
    if(!el) return {id, ok:false, reason:'missing'};
    const info=stripe(id);
    if(!info.shown) return {id, ok:false, reason:'hidden', info};
    if(info.pe==='none') return {id, ok:false, reason:'pe-none', info};
    const prop=propOverride||info.prop|| (id==='indexHeight'?'--sides-index-h':'--portable-lw');
    const root=id==='indexHeight'?document.body:document.documentElement;
    const before=cssVar(prop, root);
    const x=info.x+Math.max(2, Math.round(info.w/2));
    const y=info.y+Math.max(2, Math.round(info.h/2));
    const pid=11+Math.floor(Math.random()*5000);
    fire(el,'pointerdown',x,y,1,pid);
    fire(document,'pointermove',x+dx,y+dy,1,pid);
    fire(el,'pointermove',x+dx,y+dy,1,pid);
    fire(document,'pointerup',x+dx,y+dy,0,pid);
    fire(el,'pointerup',x+dx,y+dy,0,pid);
    if(typeof placePortableHandles==='function') placePortableHandles();
    const after=cssVar(prop, root);
    const afterHtml=cssVar(prop, document.documentElement);
    const used=after||afterHtml;
    const delta=used-before;
    return {id, prop, before, after:used, delta, abs:Math.abs(delta), ok:Math.abs(delta)>8, info:stripe(id)};
  }
  function applyCombo(spec){
    try{
      if(typeof portableMenuFsOn==='function' && portableMenuFsOn() && typeof portableExitMenuFs==='function') portableExitMenuFs();
      document.body.classList.remove('ac-fs-open','kw-fs-open','dual-fs-open','display-content');
      document.body.classList.add('display-sides');
      if(window.matchMedia && window.matchMedia('(orientation:portrait)').matches) document.body.classList.add('display-middle');
      else document.body.classList.remove('display-middle');
      if(spec.search){
        document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed');
      }else{
        document.body.classList.add('search-chrome-collapsed');
      }
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
      if(spec.flip) document.body.classList.add('sides-portrait-flip');
      else document.body.classList.remove('sides-portrait-flip');
      if(spec.hdrHide) document.body.classList.add('hdr-bar-hidden');
      else document.body.classList.remove('hdr-bar-hidden');
      var ix=document.getElementById('catalogIndex');
      if(ix && spec.indexWin){
        ix.classList.remove('is-collapsed','is-embedded');
      }else if(ix){
        ix.classList.add('is-collapsed');
      }
      if(spec.fs && typeof portableEnterMenuFs==='function') portableEnterMenuFs(spec.fs);
      if(!document.body.classList.contains('layout-edit') && typeof toggleLayoutEdit==='function') toggleLayoutEdit();
      if(typeof syncPortableLayoutChrome==='function') syncPortableLayoutChrome();
      if(typeof placeMenusForDisplay==='function') placeMenusForDisplay('sides');
      if(typeof placePortableHandles==='function') placePortableHandles();
    }catch(err){ window._sepApplyErr=String(err&&err.message||err); }
  }
  applyCombo(%SPEC%);
  const ids=['searchSplit','dualFsSep','indexHeight','searchHeight','kwShadeHeight','acWidth','acHeight'];
  const stripes=ids.map(stripe);
  const visible=stripes.filter(s=>s.shown);
  const deadVisible=visible.filter(s=>!s.hit);
  const hiddenBlockers=stripes.filter(s=>!s.shown && s.pe==='none'?false: (!s.shown && s.w>=6 && s.h>=6 && s.pe!=='none' && s.disp!=='none'));
  const drags=[];
  visible.forEach(s=>{
    if(s.id==='searchHeight'||s.id==='kwShadeHeight'||s.id==='acWidth'||s.id==='acHeight'){
      drags.push({id:s.id, ok:false, reason:'should-be-hidden', info:s});
      return;
    }
    const axis=s.axis||(s.h<=12?'h':'v');
    const dx=axis==='h'?0:36;
    const dy=axis==='h'?36:0;
    const prop=s.id==='indexHeight'?'--sides-index-h':(s.prop||'--portable-lw');
    drags.push(drag(s.id, dx, dy, prop));
  });
  const unused=['searchHeight','kwShadeHeight','acWidth','acHeight'].map(stripe);
  return {
    name,
    vw: innerWidth, vh: innerHeight,
    orient: window._sepProbeOrient(),
    cls: {
      edit: document.body.classList.contains('layout-edit'),
      sides: document.body.classList.contains('display-sides'),
      middle: document.body.classList.contains('display-middle'),
      content: document.body.classList.contains('display-content'),
      pair: document.body.classList.contains('portable-sk-pair'),
      land: document.body.classList.contains('portable-landscape'),
      port: document.body.classList.contains('portable-portrait'),
      flip: document.body.classList.contains('sides-portrait-flip'),
      acFs: document.body.classList.contains('ac-fs-open'),
      kwFs: document.body.classList.contains('kw-fs-open'),
      hdr: document.body.classList.contains('hdr-bar-hidden'),
      sCol: document.body.classList.contains('search-chrome-collapsed'),
      kCol: document.body.classList.contains('kw-chrome-collapsed'),
      kOpen: document.body.classList.contains('kw-open')
    },
    vars: {
      lw: cssVar('--portable-lw'),
      rw: cssVar('--portable-rw'),
      mh: cssVar('--portable-menu-h'),
      ix: cssVar('--sides-index-h', document.body)
    },
    search: vis(document.getElementById('searchChrome')),
    kw: vis(document.getElementById('filterWrap')),
    main: vis(document.getElementById('catalogMain')),
    stripes, visible: visible.map(s=>s.id), deadVisible, hiddenBlockers, drags,
    unusedHidden: unused.every(s=>!s.shown),
    allDragOk: drags.length? drags.every(d=>d.ok): true,
    noDead: deadVisible.length===0 && hiddenBlockers.length===0,
    applyErr: window._sepApplyErr||null
  };
  } catch (e) { return {_exc: String(e && e.stack || e)}; }
})()
"""

REGRESS_JS = r"""
(() => {
  function vis(el){
    if(!el) return {shown:false};
    const cs=getComputedStyle(el), r=el.getBoundingClientRect();
    return {shown: cs.display!=='none' && cs.visibility!=='hidden' && r.width>2 && r.height>2, w:Math.round(r.width), h:Math.round(r.height), x:Math.round(r.x)};
  }
  const hideS=document.querySelector('.search-strip-hide');
  const hideK=document.getElementById('kwStripHide');
  if(typeof portableExitMenuFs==='function' && (typeof portableMenuFsOn==='function'?portableMenuFsOn():'')) portableExitMenuFs();
  document.body.classList.remove('display-content','display-middle','ac-fs-open','kw-fs-open','dual-fs-open','search-chrome-collapsed','kw-chrome-collapsed');
  document.body.classList.add('display-sides','kw-open');
  var fw=document.getElementById('filterWrap'); if(fw) fw.classList.add('open');
  if(typeof syncPortableLayoutChrome==='function') syncPortableLayoutChrome();
  if(typeof placeMenusForDisplay==='function') placeMenusForDisplay('sides');
  if(typeof placePortableHandles==='function') placePortableHandles();
  const sc=vis(document.getElementById('searchChrome'));
  const kw=vis(document.getElementById('filterWrap'));
  const pair = !!(sc.shown && kw.shown && Math.abs((sc.x||0)-(kw.x||0))>40);
  const flipBtn=vis(document.getElementById('portraitFlipBtn'));
  if(typeof portableEnterMenuFs==='function') portableEnterMenuFs('search');
  const inFs=!!(typeof portableMenuFsOn==='function' && portableMenuFsOn()==='search');
  const fsStripes=['searchSplit','dualFsSep'].map(id=>{
    const el=document.getElementById(id); const o=vis(el); o.id=id; o.pe=el?getComputedStyle(el).pointerEvents:''; return o;
  });
  if(typeof portableExitMenuFs==='function') portableExitMenuFs();
  const outFs=!(typeof portableMenuFsOn==='function' && portableMenuFsOn());
  const after=vis(document.getElementById('searchChrome'));
  const ix=document.getElementById('catalogIndex');
  const card=document.querySelector('#catalogMain .entry');
  let indexFront=null;
  if(ix && card){
    const zi=parseInt(getComputedStyle(ix).zIndex,10)||0;
    const zc=parseInt(getComputedStyle(card).zIndex,10)||0;
    indexFront={zi, zc, ixH:Math.round(ix.getBoundingClientRect().height), cardT:Math.round(card.getBoundingClientRect().top)};
  }
  return {
    hideGone: !vis(hideS).shown && !vis(hideK).shown,
    pair, flipBtn: flipBtn.shown,
    inFs, outFs, afterSearch: after.shown,
    fsStripesHidden: fsStripes.every(s=>!s.shown),
    indexFront
  };
})()
"""


def combo_expr(name: str, spec: dict) -> str:
    return COMBO_JS.replace("%NAME%", json.dumps(name)).replace("%SPEC%", json.dumps(spec))


COMBOS_LAND = [
    ("land-search", {"search": True, "kw": False, "flip": False, "fs": "", "indexWin": False, "hdrHide": False}),
    ("land-kw", {"search": False, "kw": True, "flip": False, "fs": "", "indexWin": False, "hdrHide": False}),
    ("land-both", {"search": True, "kw": True, "flip": False, "fs": "", "indexWin": False, "hdrHide": False}),
    ("land-flip", {"search": True, "kw": False, "flip": True, "fs": "", "indexWin": False, "hdrHide": False}),
    ("land-index", {"search": True, "kw": False, "flip": False, "fs": "", "indexWin": True, "hdrHide": False}),
    ("land-hdr-hide", {"search": True, "kw": False, "flip": False, "fs": "", "indexWin": False, "hdrHide": True}),
    ("land-fs-search", {"search": True, "kw": False, "flip": False, "fs": "search", "indexWin": False, "hdrHide": False}),
    ("land-fs-kw", {"search": False, "kw": True, "flip": False, "fs": "keywords", "indexWin": False, "hdrHide": False}),
]
COMBOS_PORT = [
    ("port-middle-search", {"search": True, "kw": False, "flip": False, "fs": "", "indexWin": False, "hdrHide": False}),
    ("port-middle-kw", {"search": False, "kw": True, "flip": False, "fs": "", "indexWin": False, "hdrHide": False}),
    ("port-index", {"search": True, "kw": False, "flip": False, "fs": "", "indexWin": True, "hdrHide": False}),
    ("port-hdr-hide", {"search": True, "kw": False, "flip": False, "fs": "", "indexWin": False, "hdrHide": True}),
    ("port-fs-search", {"search": True, "kw": False, "flip": False, "fs": "search", "indexWin": False, "hdrHide": False}),
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


def run_catalog(send, ev, events, file_name: str) -> dict:
    def metrics(w, h, kind):
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
        time.sleep(0.35)
        ev(
            "if(typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();"
            "if(typeof portableRelayoutChrome==='function')portableRelayoutChrome('sep-orient'); true"
        )
        time.sleep(0.25)

    send("Page.navigate", {"url": f"http://127.0.0.1:{HTTP}/{file_name}?sep={int(time.time())}"})
    t0 = time.time()
    loaded = False
    while time.time() - t0 < 40:
        while events:
            if events.popleft().get("method") == "Page.loadEventFired":
                loaded = True
        if loaded:
            break
        time.sleep(0.1)
    time.sleep(1.4)
    out = {"file": file_name, "ready": ev(SETUP), "combos": {}, "regress": None}
    metrics(844, 390, "landscape")
    ev(SETUP)
    for name, spec in COMBOS_LAND:
        out["combos"][name] = ev(combo_expr(name, spec))
        time.sleep(0.15)
    out["regress"] = ev(REGRESS_JS)
    metrics(390, 844, "portrait")
    ev(SETUP)
    for name, spec in COMBOS_PORT:
        out["combos"][name] = ev(combo_expr(name, spec))
        time.sleep(0.15)
    return out


def summarize(cat: dict) -> dict:
    fails = []
    matrix = []
    for name, row in (cat.get("combos") or {}).items():
        if not isinstance(row, dict):
            fails.append(f"{name}: eval failed {row}")
            continue
        visible = row.get("visible") or []
        drags = row.get("drags") or []
        fs = (row.get("cls") or {}).get("acFs") or (row.get("cls") or {}).get("kwFs")
        if fs:
            extra = [s for s in visible if s in ("searchSplit", "dualFsSep")]
            if extra:
                fails.append(f"{name}: FS still shows {extra}")
        for d in drags:
            matrix.append(
                {
                    "combo": name,
                    "stripe": d.get("id"),
                    "prop": d.get("prop"),
                    "delta": d.get("delta"),
                    "ok": d.get("ok"),
                    "reason": d.get("reason"),
                }
            )
            if not d.get("ok"):
                fails.append(f"{name}:{d.get('id')} drag {d.get('reason') or d.get('delta')}")
        if row.get("deadVisible"):
            fails.append(f"{name}: dead visible {row['deadVisible']}")
        if row.get("hiddenBlockers"):
            fails.append(f"{name}: hidden blockers {row['hiddenBlockers']}")
        if row.get("unusedHidden") is False:
            fails.append(f"{name}: unused desktop handles visible")
    reg = cat.get("regress") or {}
    if isinstance(reg, dict):
        if not reg.get("hideGone"):
            fails.append("hide buttons still visible")
        if not reg.get("outFs"):
            fails.append("FS exit failed")
        if not reg.get("fsStripesHidden"):
            fails.append("FS showed seps")
        land_pair = (cat.get("combos") or {}).get("land-both") or {}
        if land_pair and not (land_pair.get("visible") or []):
            fails.append("land-both missing pair/stripe")
        land_s = (cat.get("combos") or {}).get("land-search") or {}
        if land_s and not (land_s.get("visible") or []):
            fails.append("land-search missing Search|content stripe")
    return {"fails": fails, "matrix": matrix, "ok": not fails}


def run():
    import websocket

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
            ok = pending[mid]["ev"].wait(20)
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
        OUT.write_text(json.dumps(report, indent=2)[:400000])
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
