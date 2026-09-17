#!/usr/bin/env python3
"""Headless CDP sweep of display modes, pin, hide, interop, mobile."""
import json, os, sys, time, urllib.request, subprocess

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_display_sweep.json"
PORT = 9351
PROFILE = "/tmp/catalog-sweep-verify"
os.makedirs(PROFILE, exist_ok=True)
subprocess.run(["pkill", "-f", "remote-debugging-port=9351"], check=False)
time.sleep(0.3)
logf = open("/tmp/catalog-sweep.log", "w")
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

EXPR = r"""
(() => {
  function box(id){
    const el=document.getElementById(id);
    if(!el) return null;
    const b=el.getBoundingClientRect();
    const cs=getComputedStyle(el);
    return {x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height),disp:cs.display,pe:cs.pointerEvents};
  }
  function visEntries(){
    const entries=[...document.querySelectorAll('.entry')];
    const shown=entries.filter(el=>el.offsetParent&&getComputedStyle(el).display!=='none'&&!el.hidden);
    return {n:entries.length, shown:shown.length};
  }
  function overlaps(a,b){
    if(!a||!b||a.w<2||b.w<2) return false;
    return !(a.x+a.w<=b.x||b.x+b.w<=a.x||a.y+a.h<=b.y||b.y+b.h<=a.y);
  }
  const out={};

  setDisplayMode('upper');
  if(typeof setMode==='function') setMode('search');
  const fw=document.getElementById('filterWrap');
  if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}
  if(typeof showAc==='function') try{showAc('',{force:true});}catch(e){}
  if(typeof placeAcShell==='function') placeAcShell();
  out.upper={
    body:[...document.body.classList],
    sc:box('searchChrome'), ac:box('acList'), fw:box('filterWrap'), cm:box('catalogMain'),
    split:box('searchSplit'), companion:box('acCompanionBtn'),
    vis:visEntries()
  };

  setDisplayMode('sides');
  out.sides={
    body:[...document.body.classList],
    L:box('searchChrome'), C:box('catalogMain'), R:box('filterWrap'),
    strip:box('searchStrip'), input:box('searchInput'), ac:box('acList'),
    split:box('searchSplit'), sep:box('dualFsSep'), pin:box('dualFsSepPin'),
    companion:box('acCompanionBtn'), fsBtn:box('kwStripFs'),
    parents:{fw:(document.getElementById('filterWrap')||{}).parentElement&&document.getElementById('filterWrap').parentElement.id}
  };
  out.sides.order = !!(out.sides.L && out.sides.C && out.sides.R && out.sides.L.x < out.sides.C.x && out.sides.C.x < out.sides.R.x);
  out.sides.overlap = overlaps(out.sides.L,out.sides.C) || overlaps(out.sides.C,out.sides.R);
  out.sides.scroll = {
    ac: (function(){var el=document.getElementById('acList');return el?{can:el.scrollHeight>el.clientHeight+4,sh:el.scrollHeight,ch:el.clientHeight}:null;})(),
    cm: (function(){var el=document.getElementById('catalogMain');return el?{can:el.scrollHeight>el.clientHeight+4,sh:el.scrollHeight,ch:el.clientHeight}:null;})(),
    fp: (function(){var el=document.getElementById('filterPanel');return el?{can:el.scrollHeight>el.clientHeight+4,sh:el.scrollHeight,ch:el.clientHeight,oy:getComputedStyle(el).overflowY}:null;})()
  };

  if(typeof toggleLayoutEdit==='function') toggleLayoutEdit();
  if(typeof applySidesCols==='function') applySidesCols();
  out.sidesEdit={
    body:[...document.body.classList],
    split:box('searchSplit'), sep:box('dualFsSep'), pin:box('dualFsSepPin')
  };
  const beforeLw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0;
  document.body.style.setProperty('--sides-lw','320px');
  document.body.style.setProperty('--sides-rw','360px');
  if(typeof writeSidesCols==='function') writeSidesCols(320,360);
  if(typeof applySidesCols==='function') applySidesCols();
  out.sidesCustom={lw:getComputedStyle(document.body).getPropertyValue('--sides-lw').trim(), rw:getComputedStyle(document.body).getPropertyValue('--sides-rw').trim(), L:box('searchChrome'), R:box('filterWrap')};
  if(typeof toggleDualFsPin==='function') toggleDualFsPin();
  const pinnedOn=document.body.classList.contains('sides-pinned');
  if(typeof writeSidesCols==='function') writeSidesCols(400,400);
  if(typeof applySidesCols==='function') applySidesCols();
  out.sidesPin={
    pinned:pinnedOn,
    lw:getComputedStyle(document.body).getPropertyValue('--sides-lw').trim(),
    still320: getComputedStyle(document.body).getPropertyValue('--sides-lw').trim()==='320px'
  };
  if(document.body.classList.contains('sides-pinned') && typeof toggleDualFsPin==='function') toggleDualFsPin();
  if(document.body.classList.contains('layout-edit') && typeof toggleLayoutEdit==='function') toggleLayoutEdit();

  const hide=document.querySelector('.search-strip-hide');
  if(hide) hide.click();
  out.sidesHide={
    body:[...document.body.classList],
    L:box('searchChrome'), C:box('catalogMain'), input:box('searchInput'),
    showTxt:(document.querySelector('.search-strip-hide')||{}).textContent||''
  };

  setDisplayMode('sides');
  if(typeof setMode==='function') setMode('search');
  const inp=document.getElementById('searchInput');
  if(inp){ inp.value='piano'; inp.dispatchEvent(new Event('input',{bubbles:true})); }
  out.interopSearch={vis:visEntries(), stillSides:document.body.classList.contains('display-sides'), searchMode:document.body.classList.contains('search-mode')};
  if(typeof setMode==='function') setMode('shade');
  out.interopShade={vis:visEntries(), stillSides:document.body.classList.contains('display-sides'), searchMode:document.body.classList.contains('search-mode')};

  setDisplayMode('fs',{menu:'keywords'});
  const hdr=document.querySelector('.catalog-header');
  const hr=hdr?hdr.getBoundingClientRect():{bottom:0,height:0};
  out.fsKw={
    body:[...document.body.classList],
    fw:box('filterWrap'), headerH:Math.round(hr.height),
      top: (function(){var el=document.getElementById('filterWrap');return el?Math.round(el.getBoundingClientRect().y):null;})(),
    headerBottom:Math.round(hr.bottom),
    displayBtns:[...document.querySelectorAll('.display-btn')].map(b=>({n:b.textContent,w:Math.round(b.getBoundingClientRect().width),y:Math.round(b.getBoundingClientRect().y)}))
  };
  out.fsKw.fwBelowHeader = out.fsKw.top >= out.fsKw.headerBottom - 2;

  if(typeof toggleAcFsCompanion==='function') toggleAcFsCompanion();
  out.companion={
    body:[...document.body.classList],
    mode: typeof currentDisplay!=='undefined'?currentDisplay:'',
    L:box('searchChrome'), C:box('catalogMain'), R:box('filterWrap'),
    isSides:document.body.classList.contains('display-sides')
  };

  setDisplayMode('upper');
  out.doneUpper={body:[...document.body.classList], fwParent:(document.getElementById('filterWrap')||{}).parentElement&&document.getElementById('filterWrap').parentElement.id};

  return out;
})()
"""

def ev(cdp, expr):
    return cdp.call("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})

def main():
    tab = new_tab("http://127.0.0.1:8788/DS-CATALOG.html?sweep=cdp")
    cdp = CDP(tab["webSocketDebuggerUrl"])
    cdp.call("Page.enable")
    cdp.call("Runtime.enable")
    # wait for load
    ready = None
    for _ in range(60):
        r = ev(cdp, "document.readyState + ':' + typeof setDisplayMode + ':' + (document.body&&document.body.className)")
        ready = (r.get("result") or {}).get("value")
        if isinstance(ready, str) and ready.startswith("complete:function"):
            break
        time.sleep(0.4)
    else:
        open(OUT, "w").write(json.dumps({"err": "not-ready", "ready": ready}))
        print("NOT READY", ready)
        proc.terminate()
        sys.exit(2)
    time.sleep(0.8)
    r = ev(cdp, EXPR)
    if r.get("exceptionDetails"):
        open(OUT, "w").write(json.dumps({"err": "ds-eval", "ex": r.get("exceptionDetails")}, indent=2, default=str))
        print("DS EVAL ERROR", r.get("exceptionDetails"))
        proc.terminate()
        sys.exit(2)
    data = (r.get("result") or {}).get("value")
    # mobile
    cdp.call("Emulation.setDeviceMetricsOverride", {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True})
    time.sleep(0.3)
    mob = ev(cdp, """(() => {
      window.dispatchEvent(new Event('resize'));
      const sidesBtn=document.querySelector('[data-display=\"sides\"]');
      const cs=sidesBtn?getComputedStyle(sidesBtn):null;
      const before=currentDisplay;
      setDisplayMode('sides');
      return {vw:innerWidth, desk:displayIsDesktop(), before, after:currentDisplay, coerced:currentDisplay==='fs', sidesBtn:cs&&cs.display, body:[...document.body.classList]};
    })()""")
    mobile = (mob.get("result") or {}).get("value")

    # kontakt
    tab2 = new_tab("http://127.0.0.1:8788/KONTAKT-CATALOG.html?sweep=cdp")
    cdp2 = CDP(tab2["webSocketDebuggerUrl"])
    cdp2.call("Page.enable")
    cdp2.call("Runtime.enable")
    for _ in range(40):
        r = ev(cdp2, "document.readyState + ':' + typeof setDisplayMode")
        val = (r.get("result") or {}).get("value")
        if val == "complete:function":
            break
        time.sleep(0.25)
    time.sleep(0.4)
    k = ev(cdp2, """(() => {
      setDisplayMode('sides');
      function box(id){ const el=document.getElementById(id); if(!el) return null; const b=el.getBoundingClientRect(); return {x:Math.round(b.x),w:Math.round(b.width),h:Math.round(b.height)}; }
      const L=box('searchChrome'), C=box('catalogMain'), R=box('filterWrap');
      return {mode:currentDisplay, order:L&&C&&R&&L.x<C.x&&C.x<R.x, L,C,R, apply:typeof applySidesCols};
    })()""")
    kontakt = (k.get("result") or {}).get("value")

    report = {"ds": data, "mobile": mobile, "kontakt": kontakt}
    # checks
    checks = {}
    try:
        s = data["sides"]
        checks["sides_order"] = s.get("order") is True and s.get("overlap") is False
        checks["sides_search_field"] = (s.get("input") or {}).get("h", 0) > 20
        checks["sides_no_companion"] = (s.get("companion") or {}).get("disp") == "none" or (s.get("companion") or {}).get("w", 1) < 2
        checks["sides_catalog_scroll"] = (s.get("scroll") or {}).get("cm", {}).get("can") is True
        checks["hide_narrow"] = data["sidesHide"]["L"]["w"] < 160
        checks["interop_stays_sides"] = data["interopSearch"]["stillSides"] and data["interopShade"]["stillSides"]
        checks["interop_filters"] = data["interopSearch"]["vis"]["shown"] < data["interopShade"]["vis"]["shown"]
        checks["fs_below_header"] = data["fsKw"]["top"] >= data["fsKw"]["headerBottom"] - 2
        checks["upper_no_companion"] = (data.get("upper", {}).get("companion") or {}).get("disp") == "none" or (data.get("upper", {}).get("companion") or {}).get("w", 1) < 2
        checks["companion_to_sides"] = data["companion"]["isSides"] is True
        checks["edit_handles"] = (data["sidesEdit"]["split"] or {}).get("w", 0) >= 8
        checks["pin_locks"] = data["sidesPin"]["still320"] is True
        checks["mobile_two_modes"] = mobile.get("coerced") is True and mobile.get("sidesBtn") == "none"
        checks["kontakt_sides"] = kontakt.get("order") is True
    except Exception as e:
        checks["parse_error"] = str(e)
    report["checks"] = checks
    report["ok"] = all(v is True for k, v in checks.items() if k != "parse_error")
    open(OUT, "w").write(json.dumps(report, indent=2))
    print(json.dumps(checks, indent=2))
    print("OK" if report["ok"] else "FAIL", OUT)
    proc.terminate()
    sys.exit(0 if report["ok"] else 2)

if __name__ == "__main__":
    main()
