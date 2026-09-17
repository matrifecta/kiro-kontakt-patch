#!/usr/bin/env python3
"""CDP nest parent matrix + Index scroll-to-end (DS + Kontakt)."""
import json, os, socket, subprocess, sys, time, urllib.request, base64
from urllib.parse import urlparse

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_nest_fix.json"
PORT = 9364
PROFILE = "/tmp/catalog-nest-fix-verify"
URLS = [
    ("ds", "http://127.0.0.1:8788/DS-CATALOG.html?v=nest-fix"),
    ("kontakt", "http://127.0.0.1:8788/KONTAKT-CATALOG.html?v=nest-fix"),
]
os.makedirs(PROFILE, exist_ok=True)
subprocess.run(["pkill", "-f", "remote-debugging-port=9364"], check=False)
time.sleep(0.3)
chrome = "/usr/lib/chromium/chromium" if os.path.exists("/usr/lib/chromium/chromium") else "/usr/bin/chromium"
proc = subprocess.Popen(
    [
        chrome, "--headless=new", "--disable-gpu", "--no-first-run",
        "--disable-extensions", f"--remote-debugging-port={PORT}", "--remote-allow-origins=*",
        f"--user-data-dir={PROFILE}", "--noerrdialogs", "--ozone-platform=headless",
        "--ozone-override-screen-size=1400,900", "--use-angle=swiftshader-webgl", "about:blank",
    ],
    stdout=open("/tmp/catalog-nest-fix.log", "w"),
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


class Ws:
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
                self._fill()
                continue
            b1 = self.buf[1]
            ln = b1 & 0x7F
            off = 2
            if ln == 126:
                if len(self.buf) < 4:
                    self._fill()
                    continue
                ln = int.from_bytes(self.buf[2:4], "big")
                off = 4
            elif ln == 127:
                if len(self.buf) < 10:
                    self._fill()
                    continue
                ln = int.from_bytes(self.buf[2:10], "big")
                off = 10
            if len(self.buf) < off + ln:
                self._fill()
                continue
            payload = self.buf[off : off + ln]
            self.buf = self.buf[off + ln :]
            return payload.decode()

    def _fill(self):
        chunk = self.s.recv(65536)
        if not chunk:
            raise RuntimeError("ws eof")
        self.buf += chunk

    def close(self):
        try:
            self.s.close()
        except OSError:
            pass


def new_tab(url):
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{PORT}/json/new?" + url, method="PUT")))
    except Exception:
        return json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/new?" + url))


class CDP:
    def __init__(self, url):
        self.ws = Ws(url)
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
        r = self.call("Runtime.evaluate", {"expression": expr, "awaitPromise": True, "returnByValue": True})
        if r.get("exceptionDetails"):
            raise RuntimeError(json.dumps(r["exceptionDetails"])[:400])
        return r.get("result", {}).get("value")


EXPR = r"""
(async function(){
  function sleep(ms){return new Promise(r=>setTimeout(r,ms));}
  function pid(id){var el=document.getElementById(id);return el&&el.parentElement?(el.parentElement.id||el.parentElement.tagName):'';}
  function box(el){if(!el)return null;var b=el.getBoundingClientRect();return{x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height),b:Math.round(b.bottom)};}
  function snap(tag){
    var ch=document.getElementById('searchChrome');
    var fw=document.getElementById('filterWrap');
    var sh=document.getElementById('acShell');
    var sep=document.getElementById('dualFsSep');
    var hdr=document.querySelector('.catalog-header');
    var ix=document.getElementById('catalogIndex');
    var il=document.getElementById('catalogIndexList');
    var last=il&&il.querySelector('li:last-child');
    return {
      tag:tag, mode:typeof currentDisplay!=='undefined'?currentDisplay:'',
      parents:{fw:pid('filterWrap'),ch:pid('searchChrome'),sh:pid('acShell'),split:pid('searchSplit'),sep:pid('dualFsSep')},
      chStyle:ch?(ch.getAttribute('style')||''):'',
      chGrid:ch?(ch.style.gridTemplateColumns||''):'',
      chH:ch?(ch.style.height||''):'',
      fwH:fw?(fw.style.height||''):'',
      sepX:sep&&getComputedStyle(sep).display!=='none'?Math.round(sep.getBoundingClientRect().x):null,
      sepDisp:sep?getComputedStyle(sep).display:'',
      dual:document.body.classList.contains('dual-fs-open'),
      acFs:document.body.classList.contains('ac-fs-open'),
      kwFs:document.body.classList.contains('kw-fs-open'),
      hdrY:hdr?Math.round(hdr.getBoundingClientRect().y):null,
      hdrVis:hdr?getComputedStyle(hdr).visibility:'',
      chBox:box(ch), fwBox:box(fw), shBox:box(sh), ixBox:box(ix),
      il:il?{box:box(il),sh:il.scrollHeight,ch:il.clientHeight,st:Math.round(il.scrollTop),ov:getComputedStyle(il).overflowY,cols:getComputedStyle(il).columnCount}:{missing:true},
      last:last?box(last):null
    };
  }
  var out={title:document.title,vw:innerWidth,vh:innerHeight,fns:{
    hideSearchAc:typeof hideSearchAc==='function',
    logNestFix:typeof logNestFix==='function',
    applyIndexScrollFit:typeof applyIndexScrollFit==='function',
    placeMenusForDisplay:typeof placeMenusForDisplay==='function'
  }};

  if(typeof setDisplayMode==='function')setDisplayMode('upper');
  var fw=document.getElementById('filterWrap');
  if(fw&&!fw.classList.contains('open')&&typeof toggleFilter==='function')toggleFilter();
  try{if(typeof showAc==='function')showAc('',{force:true});}catch(e){}
  if(typeof applyUpperContain==='function')applyUpperContain();
  await sleep(200);
  out.upper=snap('upper');

  if(!document.body.classList.contains('layout-edit')&&typeof toggleLayoutEdit==='function')toggleLayoutEdit();
  await sleep(80);
  var sh0=out.upper.chBox&&out.upper.chBox.h;
  if(typeof writeModeSlot==='function')writeModeSlot({chromeH:'0.55',splitH:'0.42'},'upper');
  if(typeof applyModeSlot==='function')applyModeSlot('upper');
  if(typeof applyAll==='function')applyAll();
  await sleep(120);
  out.upperSized=snap('upper-sized');
  out.upperSized.chromeChanged=!!(out.upperSized.chBox&&sh0&&Math.abs(out.upperSized.chBox.h-sh0)>8);

  if(typeof setDisplayMode==='function')setDisplayMode('sides');
  await sleep(280);
  out.sides=snap('sides');
  var cm=document.getElementById('catalogMain');
  out.sides.cmX=cm?Math.round(cm.getBoundingClientRect().x):null;
  out.sides.ixBleed=!!(out.sides.ixBox&&cm&&(out.sides.ixBox.x<cm.getBoundingClientRect().x-2||out.sides.ixBox.x+out.sides.ixBox.w>cm.getBoundingClientRect().right+2));
  out.sides.indexBefore={sh:out.sides.il.sh,ch:out.sides.il.ch,ov:out.sides.il.ov,cols:out.sides.il.cols,last:out.sides.last};
  var il=document.getElementById('catalogIndexList');
  if(il){il.scrollTop=il.scrollHeight;await sleep(80);}
  var last=il&&il.querySelector('li:last-child');
  var ix=document.getElementById('catalogIndex');
  var ixR=ix&&ix.getBoundingClientRect();
  var lastR=last&&last.getBoundingClientRect();
  out.sides.indexAfter={
    sh:il?il.scrollHeight:null, ch:il?il.clientHeight:null, st:il?Math.round(il.scrollTop):null,
    lastVis:!!(lastR&&ixR&&lastR.bottom<=ixR.bottom+3&&lastR.left>=ixR.left-2&&lastR.right<=ixR.right+4),
    lastInList:!!(lastR&&il&&(function(){var r=il.getBoundingClientRect();return lastR.bottom<=r.bottom+3&&lastR.left>=r.left-2&&lastR.right<=r.right+4;})()),
    last:last?{x:Math.round(lastR.x),y:Math.round(lastR.y),b:Math.round(lastR.bottom)}:null,
    ixBottom:ixR?Math.round(ixR.bottom):null
  };

  if(typeof collapseSearchMenu==='function')collapseSearchMenu();
  await sleep(160);
  ch=document.getElementById('searchChrome');
  out.sidesHide={
    collapsed:document.body.classList.contains('search-chrome-collapsed'),
    lw:(getComputedStyle(document.body).getPropertyValue('--sides-lw')||'').trim(),
    chW:ch?Math.round(ch.getBoundingClientRect().width):null,
    chDisp:ch?getComputedStyle(ch).display:'',
    fwParent:pid('filterWrap')
  };
  if(typeof setDisplayMode==='function')setDisplayMode('sides');
  await sleep(200);
  ch=document.getElementById('searchChrome');
  out.sidesRestore={
    collapsed:document.body.classList.contains('search-chrome-collapsed'),
    searchBack:!!(ch&&getComputedStyle(ch).display!=='none'&&ch.getBoundingClientRect().width>80),
    fwParent:pid('filterWrap')
  };

  if(typeof setDisplayMode==='function')setDisplayMode('fs',{menu:'keywords'});
  await sleep(220);
  out.fs=snap('fs-kw');
  if(typeof setDisplayMode==='function')setDisplayMode('fs',{menu:'search'});
  await sleep(220);
  out.fsSearch=snap('fs-search');

  if(typeof setDisplayMode==='function')setDisplayMode('upper');
  await sleep(200);
  out.upperAgain=snap('upper-again');

  if(typeof setMode==='function')setMode('pick');
  await sleep(150);
  var pills=[].slice.call(document.querySelectorAll('#kwbar .kw:not(.clear):not(.active):not(.disabled)'));
  var sel0=typeof getSel==='function'?getSel().length:0;
  if(pills[0])pills[0].click();
  await sleep(100);
  out.pick={mode:typeof getCurrentMode==='function'?getCurrentMode():'',sel0:sel0,sel1:typeof getSel==='function'?getSel().length:0,pills:pills.length};

  function leftoverGrid(s){return !!(s.chGrid&&s.mode!=='upper');}
  out.checks={
    upperFwInChrome: out.upper.parents.fw==='searchChrome',
    upperHdrVisible: out.upper.hdrY!=null&&out.upper.hdrY>=0&&out.upper.hdrY<80,
    sidesFwInBody: out.sides.parents.fw==='BODY'||out.sides.parents.fw==='body',
    sidesChromeNotWrapKw: out.sides.parents.fw!=='searchChrome',
    sidesHideZero: out.sidesHide.lw==='0px'&&(out.sidesHide.chW===0||out.sidesHide.chDisp==='none'),
    sidesRestore: !!out.sidesRestore.searchBack,
    fsExclusive: !out.fs.dual&&!out.fsSearch.dual,
    fsSepNot25: (out.fs.sepX==null||out.fs.sepX>40)&&(out.fsSearch.sepX==null||out.fsSearch.sepX>40),
    noLeftoverSidesGrid: !leftoverGrid(out.sides),
    noLeftoverFsGrid: !leftoverGrid(out.fs)&&!leftoverGrid(out.fsSearch),
    indexScrolls: !!(out.sides.il&&out.sides.il.sh>out.sides.il.ch+8),
    indexLastVisible: !!out.sides.indexAfter.lastVis,
    pickWorks: out.pick.mode==='pick'&&out.pick.sel1>out.pick.sel0,
    hideSearchAc: !!out.fns.hideSearchAc
  };
  return out;
})()
"""


def wait_ready(cdp):
    ready = None
    for _ in range(50):
        ready = cdp.eval("typeof setDisplayMode==='function'&&typeof hideSearchAc==='function'&&document.querySelectorAll('.entry').length")
        if isinstance(ready, int) and ready > 5:
            return ready
        time.sleep(0.25)
    return ready


all_out = {}
try:
    for key, url in URLS:
        tab = new_tab(url)
        cdp = CDP(tab["webSocketDebuggerUrl"])
        cdp.call("Page.enable")
        cdp.call("Runtime.enable")
        time.sleep(1.6)
        cdp.call("Emulation.setDeviceMetricsOverride", {"width": 1400, "height": 900, "deviceScaleFactor": 1, "mobile": False})
        ready = wait_ready(cdp)
        result = cdp.eval(EXPR)
        if isinstance(result, dict):
            result["readyEntries"] = ready
        all_out[key] = result
        try:
            cdp.ws.close()
        except Exception:
            pass
    open(OUT, "w").write(json.dumps(all_out, indent=2))
    print("WROTE", OUT)
    for key, result in all_out.items():
        if isinstance(result, dict):
            print(key, json.dumps(result.get("checks"), indent=2))
            ix = (result.get("sides") or {}).get("indexAfter")
            print(key, "indexAfter", json.dumps(ix))
        else:
            print(key, result)
finally:
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except Exception:
        proc.kill()
