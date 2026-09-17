#!/usr/bin/env python3
"""Verify Pick data-mode, pill clicks, Sides fill, Edit handles, Pin persist."""
import json, time, urllib.request, subprocess, os, sys

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_pick_lock.json"
PORT = 9361
PROFILE = "/tmp/catalog-pick-lock-verify"
URL = "http://127.0.0.1:8788/DS-CATALOG.html"
os.makedirs(PROFILE, exist_ok=True)
subprocess.run(["pkill", "-f", "remote-debugging-port=9361"], check=False)
time.sleep(0.3)
proc = subprocess.Popen(
    [
        "/usr/lib/chromium/chromium",
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--disable-extensions",
        f"--remote-debugging-port={PORT}",
        "--remote-allow-origins=*",
        f"--user-data-dir={PROFILE}",
        "--noerrdialogs",
        "--ozone-platform=headless",
        "--ozone-override-screen-size=1400,900",
        "--use-angle=swiftshader-webgl",
        "about:blank",
    ],
    stdout=open("/tmp/catalog-pick-lock.log", "w"),
    stderr=subprocess.STDOUT,
)
for _ in range(60):
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=1).read()
        break
    except Exception:
        time.sleep(0.25)
else:
    open(OUT, "w").write(json.dumps({"err": "cdp"}))
    sys.exit(1)

try:
    import websocket
except ImportError:
    websocket = None
import base64, socket
from urllib.parse import urlparse


class _Ws:
    def __init__(self, url):
        u = urlparse(url)
        host, port = u.hostname, u.port or 80
        path = u.path + (("?" + u.query) if u.query else "")
        key = base64.b64encode(os.urandom(16)).decode()
        s = socket.create_connection((host, port), timeout=20)
        req = (
            f"GET {path} HTTP/1.1\r\nHost:{host}:{port}\r\nUpgrade: websocket\r\n"
            f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        )
        s.sendall(req.encode())
        hdr = b""
        while b"\r\n\r\n" not in hdr:
            chunk = s.recv(4096)
            if not chunk:
                raise RuntimeError("no ws handshake")
            hdr += chunk
        self.s = s
        self.buf = hdr.split(b"\r\n\r\n", 1)[1]

    def send(self, text):
        data = text.encode()
        flen = len(data)
        hdr = bytearray([0x81])
        mask = os.urandom(4)
        if flen < 126:
            hdr.append(0x80 | flen)
        elif flen < 65536:
            hdr.append(0x80 | 126)
            hdr.extend(flen.to_bytes(2, "big"))
        else:
            hdr.append(0x80 | 127)
            hdr.extend(flen.to_bytes(8, "big"))
        hdr.extend(mask)
        self.s.sendall(bytes(hdr) + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def recv(self):
        while True:
            if len(self.buf) < 2:
                chunk = self.s.recv(65536)
                if not chunk:
                    raise RuntimeError("ws eof")
                self.buf += chunk
                continue
            b1 = self.buf[1]
            ln = b1 & 0x7F
            off = 2
            if ln == 126:
                if len(self.buf) < 4:
                    continue
                ln = int.from_bytes(self.buf[2:4], "big")
                off = 4
            elif ln == 127:
                if len(self.buf) < 10:
                    continue
                ln = int.from_bytes(self.buf[2:10], "big")
                off = 10
            if len(self.buf) < off + ln:
                chunk = self.s.recv(65536)
                if not chunk:
                    raise RuntimeError("ws eof")
                self.buf += chunk
                continue
            payload = self.buf[off : off + ln]
            self.buf = self.buf[off + ln :]
            return payload.decode()


def new_tab(url):
    try:
        return json.load(
            urllib.request.urlopen(
                urllib.request.Request(f"http://127.0.0.1:{PORT}/json/new?" + url, method="PUT")
            )
        )
    except Exception:
        return json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/new?" + url))


class CDP:
    def __init__(self, url):
        self.ws = websocket.create_connection(url, timeout=60) if websocket else _Ws(url)
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
        r = self.call(
            "Runtime.evaluate",
            {"expression": expr, "awaitPromise": True, "returnByValue": True},
        )
        return r.get("result", {}).get("value")


EXPR = r"""
(async function(){
  try{
  function sleep(ms){return new Promise(r=>setTimeout(r,ms));}
  function box(el){
    if(!el)return null;
    var b=el.getBoundingClientRect(),s=getComputedStyle(el);
    return {w:Math.round(b.width),h:Math.round(b.height),y:Math.round(b.y),bottom:Math.round(b.bottom),
      pos:s.position,maxH:s.maxHeight,pe:s.pointerEvents,disp:s.display,z:s.zIndex};
  }
  function modeNow(){return typeof getCurrentMode==='function'?getCurrentMode(): (document.body.classList.contains('pick-mode')?'pick':(document.body.classList.contains('search-mode')?'search':'?'));}
  function selNow(){return typeof getSel==='function'?getSel():[];}
  var out={title:document.title,vw:innerWidth,vh:innerHeight};

  if(typeof setDisplayMode==='function')setDisplayMode('upper');
  await sleep(200);
  var fw=document.getElementById('filterWrap');
  if(fw&&!fw.classList.contains('open')&&typeof toggleFilter==='function')toggleFilter();
  await sleep(150);

  var pickBtns=[].slice.call(document.querySelectorAll('.mode-btn[data-mode="pick"],.mode-btn[data-mode="shade"]'));
  out.pickBtns=pickBtns.map(function(b){
    var s=getComputedStyle(b),r=b.getBoundingClientRect();
    return {text:(b.textContent||'').trim(),mode:b.dataset.mode,disp:s.display,
      shown:s.display!=='none'&&r.width>2&&r.height>2};
  });
  out.shadeLabels=[];
  document.querySelectorAll('.mode-btn,.fs-mode-nav button').forEach(function(b){
    if(/shade/i.test(b.textContent||''))out.shadeLabels.push((b.textContent||'').trim());
  });

  if(typeof setMode==='function')setMode('pick');
  await sleep(250);
  out.pick={
    mode:modeNow(),
    searchMode:document.body.classList.contains('search-mode'),
    pickMode:document.body.classList.contains('pick-mode'),
    sel0:selNow().length
  };
  var pills=[].slice.call(document.querySelectorAll('#kwbar .kw:not(.clear):not(.active):not(.disabled)'));
  out.pick.pillCount=pills.length;
  if(pills[0]){
    pills[0].click();
    await sleep(200);
  }
  var shown=[].slice.call(document.querySelectorAll('.entry')).filter(function(el){
    return el.style.display!=='none'&&!el.classList.contains('is-hidden');
  }).length;
  var hidden=[].slice.call(document.querySelectorAll('.entry')).filter(function(el){
    return el.style.display==='none'||el.classList.contains('is-hidden')||el.classList.contains('dim');
  }).length;
  out.pick.afterClick={sel:selNow(),shown:shown,hidden:hidden,status:(document.getElementById('kwstatus')||{}).textContent||''};

  var fp=document.querySelector('#filterWrap .filter-panel');
  out.pick.upperGeom={fw:box(fw),fp:box(fp),kw:box(document.getElementById('kwbar'))};

  if(typeof setMode==='function')setMode('search');
  await sleep(200);
  out.search={
    mode:modeNow(),
    searchMode:document.body.classList.contains('search-mode'),
    pickMode:document.body.classList.contains('pick-mode')
  };
  var si=document.getElementById('searchInput');
  if(si){si.value='piano';si.dispatchEvent(new Event('input',{bubbles:true}));}
  await sleep(250);
  out.search.typedHits=typeof currentHits==='function'?currentHits().length:null;
  var tap=document.getElementById('tapAddBtnPanel');
  if(tap&&!document.body.classList.contains('tap-to-add')&&typeof toggleTapToAdd==='function')toggleTapToAdd();
  await sleep(80);
  var beforeKw=[].slice.call(document.querySelectorAll('#searchPills .kw,#kwbar .kw.active')).map(function(b){return b.getAttribute('data-kw');});
  var sp=[].slice.call(document.querySelectorAll('#kwbar .kw:not(.clear):not(.active):not(.disabled)'));
  if(sp[0])sp[0].click();
  await sleep(150);
  var afterKw=[].slice.call(document.querySelectorAll('#searchPills .kw,#kwbar .kw.active')).map(function(b){return b.getAttribute('data-kw');});
  out.search.tap={tapClass:document.body.classList.contains('tap-to-add'),before:beforeKw,after:afterKw};

  if(typeof setMode==='function')setMode('pick');
  await sleep(150);
  if(typeof setDisplayMode==='function')setDisplayMode('sides');
  await sleep(300);
  fw=document.getElementById('filterWrap');
  fp=fw&&fw.querySelector('.filter-panel');
  var kw=document.getElementById('kwbar');
  out.sides={
    mode:modeNow(),
    searchMode:document.body.classList.contains('search-mode'),
    fw:box(fw),fp:box(fp),kw:box(kw),
    vh:innerHeight,
    bottomGap:fw?Math.round(innerHeight-fw.getBoundingClientRect().bottom):null
  };

  if(!document.body.classList.contains('layout-edit')&&typeof toggleLayoutEdit==='function')toggleLayoutEdit();
  await sleep(200);
  out.editSides={
    on:document.body.classList.contains('layout-edit'),
    handles:typeof handleSnap==='function'?handleSnap():null,
    split:box(document.getElementById('searchSplit')),
    sep:box(document.getElementById('dualFsSep'))
  };
  var split=document.getElementById('searchSplit');
  var lw0=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0;
  if(split){
    var r=split.getBoundingClientRect();
    split.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,clientX:r.left+4,clientY:r.top+40,pointerId:1,button:0}));
    document.dispatchEvent(new PointerEvent('pointermove',{bubbles:true,clientX:r.left+80,clientY:r.top+40,pointerId:1}));
    document.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,clientX:r.left+80,clientY:r.top+40,pointerId:1}));
    await sleep(150);
  }
  var lw1=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0;
  out.editSides.drag={lw0:lw0,lw1:lw1,changed:lw1!==lw0};

  var pin=document.getElementById('modePinBtn');
  if(pin)pin.click();
  await sleep(150);
  var slot=typeof readModeSlot==='function'?readModeSlot('sides'):null;
  out.pinSides={pressed:pin&&pin.getAttribute('aria-pressed'),slot:slot,pinned:typeof modeLayoutPinned==='function'?modeLayoutPinned():null};

  if(typeof setDisplayMode==='function')setDisplayMode('upper');
  await sleep(250);
  if(!document.body.classList.contains('layout-edit')&&typeof toggleLayoutEdit==='function')toggleLayoutEdit();
  await sleep(150);
  out.editUpper={
    on:document.body.classList.contains('layout-edit'),
    handles:typeof handleSnap==='function'?handleSnap():null,
    kwH:box(document.getElementById('kwShadeHeight')),
    searchH:box(document.getElementById('searchHeight'))
  };

  if(typeof setDisplayMode==='function')setDisplayMode('fs');
  await sleep(250);
  out.editFs={
    on:document.body.classList.contains('layout-edit'),
    handles:typeof handleSnap==='function'?handleSnap():null,
    acH:box(document.getElementById('acHeight')),
    kwH:box(document.getElementById('kwShadeHeight'))
  };

  var store=null;
  try{store=JSON.parse(localStorage.getItem('catalog-layout-'+(window.CATALOG_NS||'catalog'))||'null');}catch(e){}
  out.store=store;
  return out;
  }catch(err){return {err:String(err),stack:err&&err.stack};}
})()
"""

try:
    tab = new_tab(URL)
    cdp = CDP(tab["webSocketDebuggerUrl"])
    cdp.call("Page.enable")
    cdp.call("Runtime.enable")
    time.sleep(2.5)
    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {"width": 1400, "height": 900, "deviceScaleFactor": 1, "mobile": False},
    )
    # wait for catalog JS
    ready = None
    for _ in range(40):
        ready = cdp.eval(
            "typeof setMode==='function'&&typeof setDisplayMode==='function'&&document.querySelectorAll('.entry').length"
        )
        if isinstance(ready, int) and ready > 10:
            break
        time.sleep(0.25)
    result = cdp.eval(EXPR)
    # reload persist check
    cdp.call("Page.reload", {"ignoreCache": True})
    time.sleep(2.5)
    for _ in range(40):
        ready = cdp.eval("typeof readModeSlot==='function'&&document.querySelectorAll('.entry').length")
        if ready:
            break
        time.sleep(0.25)
    persist = cdp.eval(
        r"""
(function(){
  if(typeof setDisplayMode==='function')setDisplayMode('sides');
  var slot=typeof readModeSlot==='function'?readModeSlot('sides'):null;
  var lw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0;
  var dm=null;try{dm=localStorage.getItem('catalog-data-mode-'+(window.CATALOG_NS||'catalog'));}catch(e){}
  return {slot:slot,lw:lw,dataMode:dm,currentMode:typeof getCurrentMode==='function'?getCurrentMode():'',
    pickMode:document.body.classList.contains('pick-mode'),
    pickBtn:[].slice.call(document.querySelectorAll('.mode-btn')).map(function(b){return (b.textContent||'').trim()+'|'+b.dataset.mode;})};
})()
"""
    )
    # mobile coerce
    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True},
    )
    time.sleep(0.8)
    mobile = cdp.eval(
        r"""
(function(){
  var btn=document.querySelector('.display-btn[data-display="sides"]');
  var s=btn&&getComputedStyle(btn);
  return {exists:!!btn,disp:s&&s.display,shown:!!(btn&&s&&s.display!=='none'&&btn.getBoundingClientRect().width>2),
    body:document.body.className};
})()
"""
    )
    if isinstance(result, dict):
        result["reload"] = persist
        result["mobile"] = mobile
        result["readyEntries"] = ready
    else:
        result = {"raw": result, "reload": persist, "mobile": mobile}
    open(OUT, "w").write(json.dumps(result, indent=2))
    print("WROTE", OUT)
    print(json.dumps(result, indent=2)[:4000])
finally:
    proc.terminate()
