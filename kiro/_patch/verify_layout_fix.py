#!/usr/bin/env python3
"""Verify exclusivity, Upper clip/header, Sides well, mobile coerce, per-mode save."""
import json, os, sys, time, urllib.request, subprocess

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_layout_fix.json"
PORT = 9364
PROFILE = "/tmp/catalog-layout-fix-verify"
os.makedirs(PROFILE, exist_ok=True)
subprocess.run(["pkill", "-f", "remote-debugging-port=9364"], check=False)
time.sleep(0.3)
logf = open("/tmp/catalog-layout-fix.log", "w")
chrome = "/usr/lib/chromium/chromium" if os.path.exists("/usr/lib/chromium/chromium") else "/usr/bin/chromium"
proc = subprocess.Popen([
    chrome, "--headless=new", "--disable-gpu", "--no-first-run",
    "--disable-extensions", f"--remote-debugging-port={PORT}", "--remote-allow-origins=*",
    f"--user-data-dir={PROFILE}", "--noerrdialogs", "--ozone-platform=headless",
    "--ozone-override-screen-size=1400,900", "--use-angle=swiftshader-webgl", "about:blank"
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
    def eval(self, expr):
        r = self.call("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
        if r.get("exceptionDetails"):
            raise RuntimeError(r["exceptionDetails"])
        return r.get("result", {}).get("value")

EXPR = r"""
(async () => {
  function box(id){
    const el=document.getElementById(id)||document.querySelector(id);
    if(!el) return {id, missing:true};
    const b=el.getBoundingClientRect();
    const cs=getComputedStyle(el);
    return {id, x:Math.round(b.x), y:Math.round(b.y), w:Math.round(b.width), h:Math.round(b.height),
      bottom:Math.round(b.bottom), disp:cs.display, overflow:cs.overflow, parent:el.parentElement?(el.parentElement.id||el.parentElement.tagName):''};
  }
  function wait(ms){return new Promise(r=>setTimeout(r,ms));}
  const out={ns: window.CATALOG_NS||'', vw: innerWidth, vh: innerHeight};

  // A. Upper + KW + AC
  setDisplayMode('upper');
  const fw=document.getElementById('filterWrap');
  if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}
  try{if(typeof showAc==='function')showAc('',{force:true});}catch(e){}
  if(typeof placeAcShell==='function')placeAcShell();
  if(typeof applyAll==='function')applyAll();
  if(typeof applyUpperContain==='function')applyUpperContain();
  if(typeof logLayoutModes==='function')logLayoutModes('verify-A-upper');
  await wait(100);
  const hdr=box('.catalog-header');
  const ch=box('searchChrome');
  const sh=box('acShell');
  const fwb=box('filterWrap');
  const kw=box('kwbar');
  out.A={
    body: document.body.className,
    hdr, ch, sh, fw: fwb, kw,
    headerVisible: hdr.y>=-2 && hdr.y<80 && hdr.h>20,
    acInsideChrome: !sh.missing && sh.bottom <= ch.bottom+8,
    kwInsideWrap: !kw.missing && (kw.h===0 || kw.bottom <= fwb.bottom+20),
    noDual: !document.body.classList.contains('dual-fs-open')
  };

  // grow Upper then switch
  if(typeof writeModeSlot==='function') writeModeSlot({chromeH:'0.55', splitH:'0.42'}, 'upper');
  if(typeof applyModeSlot==='function') applyModeSlot('upper');
  if(typeof applyAll==='function') applyAll();
  await wait(40);
  const upperH=box('searchChrome').h;

  // B. Full search then Full keywords
  setDisplayMode('fs', {menu:'search'});
  await wait(80);
  if(typeof logLayoutModes==='function')logLayoutModes('verify-B-fs-search');
  const fsSearch={
    body: document.body.className,
    acFs: document.body.classList.contains('ac-fs-open'),
    kwFs: document.body.classList.contains('kw-fs-open'),
    dual: document.body.classList.contains('dual-fs-open'),
    sh: box('acShell'), fw: box('filterWrap')
  };
  setDisplayMode('fs', {menu:'keywords'});
  await wait(80);
  if(typeof logLayoutModes==='function')logLayoutModes('verify-B-fs-kw');
  const fsKw={
    body: document.body.className,
    acFs: document.body.classList.contains('ac-fs-open'),
    kwFs: document.body.classList.contains('kw-fs-open'),
    dual: document.body.classList.contains('dual-fs-open'),
    sh: box('acShell'), fw: box('filterWrap'), sep: box('dualFsSep')
  };
  out.B={
    fsSearch, fsKw,
    searchExclusive: fsSearch.acFs && !fsSearch.kwFs && !fsSearch.dual,
    kwExclusive: fsKw.kwFs && !fsKw.acFs && !fsKw.dual,
    searchNotCoveringKw: !fsSearch.dual
  };

  // Sides KW closed well
  setDisplayMode('sides');
  await wait(60);
  if(fw){fw.classList.remove('open');document.body.classList.remove('kw-open');}
  if(typeof applySidesCols==='function')applySidesCols();
  await wait(60);
  if(typeof logLayoutModes==='function')logLayoutModes('verify-H8-well');
  const fwClosed=box('filterWrap');
  const rw=getComputedStyle(document.body).getPropertyValue('--sides-rw').trim();
  out.H8={
    fw: fwClosed,
    rw,
    collapsed: fwClosed.h < 120 && !rw
  };

  // per-mode isolation
  if(typeof writeModeSlot==='function') writeModeSlot({lw:300, rw:310}, 'sides');
  setDisplayMode('upper');
  await wait(50);
  const upperAgain=box('searchChrome').h;
  const store=(()=>{try{return JSON.parse(localStorage.getItem('catalog-layout-'+(window.CATALOG_NS||'catalog'))||'null');}catch(e){return null;}})();
  out.H6={
    store,
    upperKept: !!(store&&store.upper&&store.upper.chromeH&&!store.upper.lw),
    sidesHasOwn: !!(store&&store.sides&&store.sides.lw),
    upperNoSidesLw: !(store&&store.upper&&store.upper.lw),
    upperH: upperH, upperAgain: upperAgain
  };

  out.ok = !!(out.A.headerVisible && out.A.acInsideChrome && out.B.searchExclusive && out.B.kwExclusive && out.H8.collapsed && out.H6.upperKept);
  return out;
})()
"""

SIDES_THEN_NARROW = r"""
(async () => {
  function box(el){if(!el)return null;const b=el.getBoundingClientRect();return {x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height)};}
  setDisplayMode('sides');
  await new Promise(r=>setTimeout(r,80));
  const before={vw:innerWidth, display: currentDisplay, dual:document.body.classList.contains('dual-fs-open')};
  return {before, ready:true};
})()
"""

AFTER_NARROW = r"""
(() => {
  function box(el){if(!el)return null;const b=el.getBoundingClientRect();return {x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height)};}
  window.dispatchEvent(new Event('resize'));
  const fw=document.getElementById('filterWrap');
  const sh=document.getElementById('acShell');
  const ch=document.getElementById('searchChrome');
  return {
    vw: innerWidth,
    body: document.body.className,
    display: typeof currentDisplay!=='undefined'?currentDisplay:'',
    dual: document.body.classList.contains('dual-fs-open'),
    acFs: document.body.classList.contains('ac-fs-open'),
    kwFs: document.body.classList.contains('kw-fs-open'),
    fw: box(fw), sh: box(sh),
    chGrid: ch?(ch.style.gridTemplateColumns||''):'',
    sidesBtn: (function(){const b=document.querySelector('[data-display="sides"]');return b?getComputedStyle(b).display:'missing';})(),
    fwOffCanvas: fw?(fw.getBoundingClientRect().x>innerWidth-20):false,
    blackWell: document.body.classList.contains('display-sides') && !document.body.classList.contains('kw-open')
  };
})()
"""

def run(url):
    tab = new_tab(url)
    cdp = CDP(tab["webSocketDebuggerUrl"])
    cdp.call("Page.enable")
    time.sleep(0.8)
    for _ in range(20):
        if cdp.eval("document.readyState") == "complete":
            break
        time.sleep(0.2)
    time.sleep(0.4)
    desktop = cdp.eval(EXPR)
    sides = cdp.eval(SIDES_THEN_NARROW)
    cdp.call("Emulation.setDeviceMetricsOverride", {
        "width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True
    })
    time.sleep(0.25)
    mobile = cdp.eval(AFTER_NARROW)
    return desktop, {"sidesBefore": sides, **(mobile or {})}

results = {}
try:
    for name, url in (
        ("ds", "http://127.0.0.1:8788/DS-CATALOG.html"),
        ("kontakt", "http://127.0.0.1:8788/KONTAKT-CATALOG.html"),
    ):
        desktop, mobile = run(url)
        results[name] = desktop
        results[name+"_mobile"] = mobile
    open(OUT, "w").write(json.dumps(results, indent=2))
    summary = {}
    for k, v in results.items():
        if isinstance(v, dict) and "ok" in v:
            summary[k] = {
                "ok": v.get("ok"),
                "A": {kk: v["A"].get(kk) for kk in ("headerVisible", "acInsideChrome", "kwInsideWrap", "noDual") if "A" in v},
                "B": {kk: v["B"].get(kk) for kk in ("searchExclusive", "kwExclusive") if "B" in v},
                "H8": v.get("H8", {}).get("collapsed"),
                "H6": {kk: v.get("H6", {}).get(kk) for kk in ("upperKept", "sidesHasOwn")},
            }
        else:
            summary[k] = {
                "dual": v.get("dual"),
                "fwOffCanvas": v.get("fwOffCanvas"),
                "sidesBtn": v.get("sidesBtn"),
                "body": v.get("body"),
            }
    print(json.dumps(summary, indent=2))
finally:
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except Exception:
        proc.kill()
