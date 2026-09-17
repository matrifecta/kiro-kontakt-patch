#!/usr/bin/env python3
"""CDP: SK-pair widths persist after Customize; Flip drag follows pointer. Both portable catalogs."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import threading
import time
from collections import deque
from pathlib import Path

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_portable_sk_persist.json")
PORT = 9623
HTTP = 8797
PROFILE = "/tmp/catalog-sk-persist"
CHROME = next(
    (p for p in ("/usr/lib/chromium/chromium", "/usr/bin/chromium", "/usr/bin/google-chrome") if os.path.exists(p)),
    "/usr/bin/chromium",
)
os.makedirs(PROFILE, exist_ok=True)

SETUP_BOTH = r"""
(() => {
  try{sidesPinned=false;}catch(e){}
  document.body.classList.remove('sides-pinned','mode-layout-pinned','ac-fs-open','kw-fs-open','dual-fs-open','display-content','display-middle','search-chrome-collapsed','kw-chrome-collapsed','portable-edit-3pane');
  document.body.classList.add('display-sides','kw-open');
  var fw=document.getElementById('filterWrap');
  if(fw) fw.classList.add('open');
  if(typeof syncPortableLayoutChrome==='function') syncPortableLayoutChrome();
  if(typeof placeMenusForDisplay==='function') placeMenusForDisplay('sides');
  if(!document.body.classList.contains('layout-edit') && typeof toggleLayoutEdit==='function') toggleLayoutEdit();
  if(typeof placePortableHandles==='function') placePortableHandles();
  return {
    edit:document.body.classList.contains('layout-edit'),
    pair:document.body.classList.contains('portable-sk-pair'),
    threeCol:(getComputedStyle(document.body).gridTemplateColumns||'').split(' ').filter(Boolean).length>=3
  };
})()
"""

FLOW = r"""
(() => {
  const name = %NAME%;
  const dxWant = %DX%;
  const flipOn = %FLIP%;
  function vis(el){
    if(!el) return {shown:false,w:0,h:0,x:0,y:0,r:0,b:0,pe:'',disp:''};
    const cs=getComputedStyle(el), r=el.getBoundingClientRect();
    return {
      shown: cs.display!=='none' && cs.visibility!=='hidden' && r.width>8 && r.height>8,
      pe:cs.pointerEvents, disp:cs.display,
      w:Math.round(r.width), h:Math.round(r.height),
      x:Math.round(r.x), y:Math.round(r.y), r:Math.round(r.right), b:Math.round(r.bottom)
    };
  }
  function cssVar(p){return parseInt(getComputedStyle(document.documentElement).getPropertyValue(p),10)||0;}
  function cols(){return getComputedStyle(document.body).gridTemplateColumns||'';}
  function fire(target,type,x,y,buttons,pointerId){
    target.dispatchEvent(new PointerEvent(type,{
      bubbles:true,cancelable:true,composed:true,pointerId:pointerId,pointerType:'mouse',
      clientX:x,clientY:y,buttons:buttons,button:0,view:window
    }));
  }
  function setFlip(on){
    const has=document.body.classList.contains('sides-portrait-flip');
    if(!!on===has) return has;
    if(typeof togglePortraitSidesFlip==='function') togglePortraitSidesFlip();
    else document.body.classList.toggle('sides-portrait-flip', !!on);
    if(typeof syncPortableLayoutChrome==='function') syncPortableLayoutChrome();
    if(typeof placePortableHandles==='function') placePortableHandles();
    return document.body.classList.contains('sides-portrait-flip');
  }
  function dragSplit(dx){
    const el=document.getElementById('searchSplit');
    const info=vis(el);
    if(!info.shown) return {ok:false,reason:'hidden',info};
    if(info.pe==='none') return {ok:false,reason:'pe-none',info};
    const x=info.x+Math.max(2,Math.round(info.w/2));
    const y=info.y+Math.max(8,Math.round(info.h/2));
    const top=document.elementFromPoint(x,y);
    const covered=!(top&&(top.id==='searchSplit'||(top.closest&&top.closest('#searchSplit'))));
    if(covered) return {ok:false,reason:'covered:'+((top&&(top.id||top.className))||'?'),info};
    const edge0=info.x+Math.round(info.w/2);
    const ch0=vis(document.getElementById('searchChrome'));
    const kw0=vis(document.getElementById('filterWrap'));
    const lw0=cssVar('--portable-lw');
    const pid=31+Math.floor(Math.random()*4000);
    fire(el,'pointerdown',x,y,1,pid);
    fire(document,'pointermove',x+dx,y,1,pid);
    fire(el,'pointermove',x+dx,y,1,pid);
    fire(document,'pointerup',x+dx,y,0,pid);
    fire(el,'pointerup',x+dx,y,0,pid);
    if(typeof placePortableHandles==='function') placePortableHandles();
    const after=vis(document.getElementById('searchSplit'));
    const ch1=vis(document.getElementById('searchChrome'));
    const kw1=vis(document.getElementById('filterWrap'));
    const edge1=after.shown?(after.x+Math.round(after.w/2)):null;
    return {
      ok:true, dx, edge0, edge1, edgeDelta:edge1==null?null:(edge1-edge0),
      lw0, lw1:cssVar('--portable-lw'),
      search0:ch0, search1:ch1, kw0:kw0, kw1:kw1,
      leftGrow:(kw0.x<ch0.x?(kw1.w-kw0.w):(ch1.w-ch0.w))
    };
  }

  setFlip(flipOn);
  if(!document.body.classList.contains('layout-edit') && typeof toggleLayoutEdit==='function') toggleLayoutEdit();
  if(typeof placePortableHandles==='function') placePortableHandles();
  const before={
    edit:document.body.classList.contains('layout-edit'),
    pair:document.body.classList.contains('portable-sk-pair'),
    flip:document.body.classList.contains('sides-portrait-flip'),
    threeCol:cols().split(' ').filter(Boolean).length>=3,
    cols:cols(), lw:cssVar('--portable-lw'),
    search:vis(document.getElementById('searchChrome')),
    kw:vis(document.getElementById('filterWrap')),
    main:vis(document.getElementById('catalogMain')),
    split:vis(document.getElementById('searchSplit')),
    sep:vis(document.getElementById('dualFsSep'))
  };
  const drag=dragSplit(dxWant);
  const mid={
    edit:document.body.classList.contains('layout-edit'),
    pair:document.body.classList.contains('portable-sk-pair'),
    flip:document.body.classList.contains('sides-portrait-flip'),
    cols:cols(), lw:cssVar('--portable-lw'),
    search:vis(document.getElementById('searchChrome')),
    kw:vis(document.getElementById('filterWrap')),
    split:vis(document.getElementById('searchSplit'))
  };
  if(document.body.classList.contains('layout-edit') && typeof toggleLayoutEdit==='function') toggleLayoutEdit();
  if(typeof syncPortableLayoutChrome==='function') syncPortableLayoutChrome();
  if(typeof placePortableHandles==='function') placePortableHandles();
  const after={
    edit:document.body.classList.contains('layout-edit'),
    pair:document.body.classList.contains('portable-sk-pair'),
    flip:document.body.classList.contains('sides-portrait-flip'),
    threeCol:cols().split(' ').filter(Boolean).length>=3,
    cols:cols(), lw:cssVar('--portable-lw'),
    lwInline:(document.documentElement.style.getPropertyValue('--portable-lw')||'').trim(),
    stored:(function(){try{return localStorage.getItem('catalog-portable-lw-'+(window.CATALOG_NS||'catalog'));}catch(e){return null;}})(),
    search:vis(document.getElementById('searchChrome')),
    kw:vis(document.getElementById('filterWrap')),
    main:vis(document.getElementById('catalogMain')),
    split:vis(document.getElementById('searchSplit')),
    sep:vis(document.getElementById('dualFsSep'))
  };
  return {name, vw:innerWidth, vh:innerHeight, dxWant, flipOn, before, drag, mid, after};
})()
"""

PORT_KW = r"""
(() => {
  try{if(typeof portableMenuFsOn==='function' && portableMenuFsOn() && typeof portableExitMenuFs==='function') portableExitMenuFs();}catch(e){}
  document.body.classList.remove('ac-fs-open','kw-fs-open','dual-fs-open','display-content','search-chrome-collapsed','portable-edit-3pane','sides-portrait-flip');
  document.body.classList.add('display-sides','display-middle','kw-open','search-chrome-collapsed');
  var fw=document.getElementById('filterWrap'); if(fw) fw.classList.add('open');
  if(typeof portableCoerceMiddleMenu==='function') portableCoerceMiddleMenu('keywords');
  if(typeof syncPortableLayoutChrome==='function') syncPortableLayoutChrome();
  if(!document.body.classList.contains('layout-edit') && typeof toggleLayoutEdit==='function') toggleLayoutEdit();
  if(typeof placePortableHandles==='function') placePortableHandles();
  function vis(el){
    if(!el) return {shown:false,w:0,h:0};
    const cs=getComputedStyle(el), r=el.getBoundingClientRect();
    return {shown:cs.display!=='none'&&cs.visibility!=='hidden'&&r.width>8&&r.height>8,w:Math.round(r.width),h:Math.round(r.height),pe:cs.pointerEvents};
  }
  function cssVar(p){return parseInt(getComputedStyle(document.documentElement).getPropertyValue(p),10)||0;}
  function fire(target,type,x,y,buttons,pointerId){
    target.dispatchEvent(new PointerEvent(type,{
      bubbles:true,cancelable:true,composed:true,pointerId:pointerId,pointerType:'mouse',
      clientX:x,clientY:y,buttons:buttons,button:0,view:window
    }));
  }
  const sep=document.getElementById('dualFsSep')||document.getElementById('searchSplit');
  const info=vis(sep);
  const kw0=vis(document.getElementById('filterWrap'));
  const mh0=cssVar('--portable-menu-h');
  let drag=null;
  if(info.shown && info.pe!=='none' && sep){
    const x=info.w?Math.round((sep.getBoundingClientRect().x)+info.w/2):10;
    const y=info.h?Math.round((sep.getBoundingClientRect().y)+info.h/2):10;
    const pid=41;
    fire(sep,'pointerdown',x,y,1,pid);
    fire(document,'pointermove',x,y+36,1,pid);
    fire(sep,'pointermove',x,y+36,1,pid);
    fire(document,'pointerup',x,y+36,0,pid);
    fire(sep,'pointerup',x,y+36,0,pid);
    if(typeof placePortableHandles==='function') placePortableHandles();
    drag={ok:true, mh0, mh1:cssVar('--portable-menu-h'), kw0h:kw0.h, kw1h:vis(document.getElementById('filterWrap')).h};
  }
  const cols=(getComputedStyle(document.body).gridTemplateColumns||'').split(' ').filter(Boolean);
  return {
    edit:document.body.classList.contains('layout-edit'),
    pair:document.body.classList.contains('portable-sk-pair'),
    middle:document.body.classList.contains('display-middle'),
    threeCol:cols.length>=3 && !/none/i.test(getComputedStyle(document.body).gridTemplateColumns||''),
    cols:getComputedStyle(document.body).gridTemplateColumns,
    search:vis(document.getElementById('searchChrome')),
    kw:vis(document.getElementById('filterWrap')),
    main:vis(document.getElementById('catalogMain')),
    split:vis(document.getElementById('searchSplit')),
    sep:vis(document.getElementById('dualFsSep')),
    drag
  };
})()
"""


def flow_expr(name: str, dx: int, flip: bool) -> str:
    return (
        FLOW.replace("%NAME%", json.dumps(name))
        .replace("%DX%", str(int(dx)))
        .replace("%FLIP%", "true" if flip else "false")
    )


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
        "if(typeof portableRelayoutChrome==='function')portableRelayoutChrome('sk-persist'); true"
    )
    time.sleep(0.2)


def judge_flow(row: dict, expect_flip: bool) -> list[str]:
    fails = []
    if not isinstance(row, dict) or row.get("_exc"):
        return [f"{row.get('name','?')}: eval failed {row}"]
    name = row.get("name") or "?"
    before, drag, mid, after = row.get("before") or {}, row.get("drag") or {}, row.get("mid") or {}, row.get("after") or {}
    if before.get("threeCol") or after.get("threeCol"):
        fails.append(f"{name}: 3-col grid {after.get('cols') or before.get('cols')}")
    if not before.get("pair") or not after.get("pair"):
        fails.append(f"{name}: missing SK-pair")
    if (before.get("main") or {}).get("shown") or (after.get("main") or {}).get("shown"):
        fails.append(f"{name}: content column visible")
    if (before.get("sep") or {}).get("shown"):
        fails.append(f"{name}: extra KW stripe")
    if not (before.get("split") or {}).get("shown"):
        fails.append(f"{name}: missing S|K sep in Customize")
    if after.get("edit"):
        fails.append(f"{name}: still in layout-edit")
    if not drag.get("ok"):
        fails.append(f"{name}: drag failed {drag}")
        return fails
    edge = drag.get("edgeDelta")
    if edge is None or abs(edge - 40) > 16:
        fails.append(f"{name}: edge delta {edge} (want ~+40)")
    if (drag.get("leftGrow") or 0) < 16:
        fails.append(f"{name}: left pane did not grow {drag.get('leftGrow')}")
    search_mid = (mid.get("search") or {}).get("w") or 0
    search_after = (after.get("search") or {}).get("w") or 0
    if abs(search_after - search_mid) > 18:
        fails.append(f"{name}: Search width reset {search_mid}->{search_after}")
    lw_mid, lw_after = mid.get("lw") or 0, after.get("lw") or 0
    if lw_mid > 40 and abs(lw_after - lw_mid) > 8:
        fails.append(f"{name}: --portable-lw reset {lw_mid}->{lw_after}")
    if expect_flip and not after.get("flip"):
        fails.append(f"{name}: Flip not on")
    if not expect_flip and after.get("flip"):
        fails.append(f"{name}: Flip still on")
    return fails


def judge_port(row: dict) -> list[str]:
    fails = []
    if not isinstance(row, dict) or row.get("_exc"):
        return [f"portrait: eval failed {row}"]
    if row.get("threeCol"):
        fails.append(f"portrait: 3-col {row.get('cols')}")
    if row.get("pair"):
        fails.append("portrait: SK-pair class in portrait")
    if not (row.get("kw") or {}).get("shown"):
        fails.append("portrait: KW hidden")
    if (row.get("search") or {}).get("shown"):
        fails.append("portrait: Search shown with docked KW")
    if not (row.get("main") or {}).get("shown"):
        fails.append("portrait: content hidden")
    drag = row.get("drag") or {}
    if not drag.get("ok"):
        fails.append(f"portrait: KW sep missing {row.get('sep')} {row.get('split')}")
    else:
        grew = (drag.get("mh1") or 0) - (drag.get("mh0") or 0)
        pane = (drag.get("kw1h") or 0) - (drag.get("kw0h") or 0)
        if grew < 8 and pane < 8:
            fails.append(f"portrait: KW sep did not move {drag}")
    return fails


def run_catalog(send, ev, events, file_name: str) -> dict:
    send("Page.navigate", {"url": f"http://127.0.0.1:{HTTP}/{file_name}?skp={int(time.time())}"})
    t0 = time.time()
    loaded = False
    while time.time() - t0 < 40:
        while events:
            if events.popleft().get("method") == "Page.loadEventFired":
                loaded = True
        if loaded:
            break
        time.sleep(0.1)
    time.sleep(1.8)
    metrics(send, ev, 844, 390, "landscape")
    setup = ev(SETUP_BOTH)
    off = ev(flow_expr("land-off", 40, False))
    time.sleep(0.12)
    ev(SETUP_BOTH)
    on = ev(flow_expr("land-flip", 40, True))
    time.sleep(0.12)
    metrics(send, ev, 390, 844, "portrait")
    port = ev(PORT_KW)
    return {"file": file_name, "setup": setup, "off": off, "on": on, "port": port}


def summarize(cat: dict) -> dict:
    fails = []
    setup = cat.get("setup") or {}
    if isinstance(setup, dict) and setup.get("threeCol"):
        fails.append("setup: 3-col")
    fails.extend(judge_flow(cat.get("off") or {}, False))
    fails.extend(judge_flow(cat.get("on") or {}, True))
    fails.extend(judge_port(cat.get("port") or {}))
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
        OUT.write_text(json.dumps(report, indent=2)[:700000])
        fails = []
        nums = {}
        for fname, cat in report.items():
            for f in cat["summary"]["fails"]:
                fails.append(f"{fname}: {f}")
            off, on = cat.get("off") or {}, cat.get("on") or {}
            nums[fname] = {
                "off_edge": (off.get("drag") or {}).get("edgeDelta"),
                "off_search_mid": ((off.get("mid") or {}).get("search") or {}).get("w"),
                "off_search_after": ((off.get("after") or {}).get("search") or {}).get("w"),
                "off_lw_mid": (off.get("mid") or {}).get("lw"),
                "off_lw_after": (off.get("after") or {}).get("lw"),
                "flip_edge": (on.get("drag") or {}).get("edgeDelta"),
                "flip_leftGrow": (on.get("drag") or {}).get("leftGrow"),
                "flip_search_mid": ((on.get("mid") or {}).get("search") or {}).get("w"),
                "flip_search_after": ((on.get("after") or {}).get("search") or {}).get("w"),
            }
        print(json.dumps({"ok": not fails, "fails": fails, "nums": nums, "out": str(OUT)}, indent=2))
        return 0 if not fails else 1
    finally:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(run())
