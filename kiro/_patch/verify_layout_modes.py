#!/usr/bin/env python3
"""Verify per-mode layout store, nesting, buttons, and isolation."""
import json, os, sys, time, urllib.request, subprocess

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_layout_modes.json"
PORT = 9362
PROFILE = "/tmp/catalog-layout-modes-verify"
os.makedirs(PROFILE, exist_ok=True)
subprocess.run(["pkill", "-f", "remote-debugging-port=9362"], check=False)
time.sleep(0.3)
logf = open("/tmp/catalog-layout-modes.log", "w")
chrome = "/usr/lib/chromium/chromium" if os.path.exists("/usr/lib/chromium/chromium") else "/usr/bin/chromium"
proc = subprocess.Popen([
    chrome, "--headless=new", "--disable-gpu", "--no-first-run",
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
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/json/new?" + url, method="PUT")
    return json.load(urllib.request.urlopen(req))

class CDP:
    def __init__(self, url):
        self.ws = websocket.create_connection(url, timeout=90) if websocket else _Ws(url)
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
    const el=document.getElementById(id);
    if(!el) return {id, missing:true};
    const b=el.getBoundingClientRect();
    const cs=getComputedStyle(el);
    return {id, x:Math.round(b.x), y:Math.round(b.y), w:Math.round(b.width), h:Math.round(b.height),
      disp:cs.display, vis:cs.visibility, parent:el.parentElement?(el.parentElement.id||el.parentElement.tagName):''};
  }
  function shown(id){
    const b=box(id);
    return !b.missing && b.disp!=='none' && b.vis!=='hidden' && b.w>0 && b.h>0;
  }
  function wait(ms){return new Promise(r=>setTimeout(r,ms));}
  async function go(mode, opts){
    if(typeof setDisplayMode==='function') setDisplayMode(mode, opts||{});
    const fw=document.getElementById('filterWrap');
    if(fw && mode!=='fs'){fw.classList.add('open');document.body.classList.add('kw-open');}
    if(typeof showAc==='function' && mode!=='fs') try{showAc('',{force:true});}catch(e){}
    if(typeof placeAcShell==='function') try{placeAcShell();}catch(e){}
    if(typeof applyAll==='function') try{applyAll();}catch(e){}
    if(typeof logLayoutModes==='function') logLayoutModes('verify-'+mode);
    await wait(80);
    return {
      mode: currentDisplay,
      body: [...document.body.classList].filter(c=>c.startsWith('display-')||c==='search-mode'||c==='kw-open'||c==='layout-edit'),
      fw: box('filterWrap'), ch: box('searchChrome'), sh: box('acShell'), cm: box('catalogMain'),
      split: box('searchSplit'), sep: box('dualFsSep'),
      acH: box('acHeight'), kwH: box('kwShadeHeight'), searchH: box('searchHeight'),
      hide: shown('searchInput'),
      fsBtn: shown('searchStripFs'), kwFs: shown('kwStripFs'),
      companion: shown('acCompanionBtn'), kwComp: shown('kwCompanionBtn'),
      edit: shown('layoutEditBtn'), pin: shown('dualFsSepPin'), modePin: shown('modePinBtn'),
      tap: shown('tapAddBtnPanel'),
      shade: [...document.querySelectorAll('.mode-btn[data-mode="shade"]')].map(el=>({disp:getComputedStyle(el).display,w:el.getBoundingClientRect().width})),
      store: (()=>{try{return JSON.parse(localStorage.getItem('catalog-layout-'+(window.CATALOG_NS||'catalog'))||'null');}catch(e){return 'err';}})(),
      vh: window.innerHeight, vw: window.innerWidth
    };
  }

  document.body.classList.add('layout-edit');
  if(typeof syncLayoutEditBtn==='function') syncLayoutEditBtn();

  const out={ns: window.CATALOG_NS||'', vw: window.innerWidth, vh: window.innerHeight};
  out.upper1 = await go('upper');
  // grow Upper chrome via store
  if(typeof writeModeSlot==='function') writeModeSlot({chromeH:'0.62', splitH:'0.40'}, 'upper');
  if(typeof applyModeSlot==='function') applyModeSlot('upper');
  if(typeof applyAll==='function') applyAll();
  await wait(60);
  out.upperSized = await go('upper');
  const upperH = out.upperSized.ch.h;

  out.sides = await go('sides');
  if(typeof writeModeSlot==='function') writeModeSlot({lw:320, rw:340}, 'sides');
  if(typeof applyModeSlot==='function') applyModeSlot('sides');
  if(typeof applySidesCols==='function') applySidesCols();
  await wait(60);
  out.sidesSized = await go('sides');

  out.fs = await go('fs', {menu:'keywords'});
  if(typeof writeModeSlot==='function') writeModeSlot({kwH:'0.70'}, 'fs');
  if(typeof applyFsChromeSize==='function') applyFsChromeSize();
  await wait(60);
  out.fsSized = await go('fs', {menu:'keywords'});

  out.upperAgain = await go('upper');
  out.sidesAgain = await go('sides');
  out.storeFinal = (()=>{try{return JSON.parse(localStorage.getItem('catalog-layout-'+(window.CATALOG_NS||'catalog'))||'null');}catch(e){return 'err';}})();

  out.checks = {
    upperFwInChrome: out.upper1.fw.parent==='searchChrome',
    sidesFwInBody: out.sides.fw.parent==='BODY' || out.sides.fw.parent==='body',
    fsFwNotInAc: out.fs.fw.parent!=='acShell',
    upperEdit: out.upper1.edit,
    sidesEdit: out.sides.edit,
    fsEdit: out.fs.edit || out.fsSized.edit,
    upperFsBtn: out.upper1.fsBtn || out.upper1.kwFs,
    sidesFsBtn: out.sides.fsBtn || out.sides.kwFs,
    shadeHidden: (out.upper1.shade||[]).every(s=>s.disp==='none'||s.w===0),
    upperFilled: out.upper1.ch.h > 200 || out.upperSized.ch.h > 200,
    upperKeptAfterSides: Math.abs((out.upperAgain.ch.h||0) - (upperH||0)) < 80,
    sidesOwnWidth: (out.sidesSized.ch.w||0) > 200 && (out.sidesSized.fw.w||0) > 200,
    storeHasThree: !!(out.storeFinal && out.storeFinal.upper && out.storeFinal.sides && out.storeFinal.fs)
  };
  return out;
})()
"""

MOBILE = r"""
(() => {
  const sidesBtn = document.querySelector('[data-display="sides"]');
  const cs = sidesBtn ? getComputedStyle(sidesBtn) : {display:'missing'};
  if(typeof setDisplayMode==='function') setDisplayMode('sides');
  return {
    vw: window.innerWidth,
    sidesBtnDisp: cs.display,
    afterSidesClick: typeof currentDisplay!=='undefined'?currentDisplay:'',
    body: [...document.body.classList].filter(c=>c.startsWith('display-'))
  };
})()
"""

def run_page(url, mobile=False):
    tab = new_tab(url)
    cdp = CDP(tab["webSocketDebuggerUrl"])
    cdp.call("Page.enable")
    if mobile:
        cdp.call("Emulation.setDeviceMetricsOverride", {
            "width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True
        })
        cdp.call("Page.reload", {"ignoreCache": True})
        time.sleep(1.2)
    else:
        time.sleep(0.8)
    # wait for load
    for _ in range(20):
        ready = cdp.eval("document.readyState")
        if ready == "complete":
            break
        time.sleep(0.2)
    time.sleep(0.4)
    return cdp.eval(MOBILE if mobile else EXPR)

results = {}
try:
    for name, url in (
        ("ds", "http://127.0.0.1:8788/DS-CATALOG.html"),
        ("kontakt", "http://127.0.0.1:8788/KONTAKT-CATALOG.html"),
    ):
        results[name] = run_page(url, mobile=False)
        results[name+"_mobile"] = run_page(url, mobile=True)
    open(OUT, "w").write(json.dumps(results, indent=2))
    print(json.dumps({
        k: (v.get("checks") if isinstance(v, dict) and "checks" in v else v)
        for k, v in results.items()
    }, indent=2))
finally:
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except Exception:
        proc.kill()
