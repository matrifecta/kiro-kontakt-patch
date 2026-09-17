#!/usr/bin/env python3
"""CDP: Hide Keywords, Sides restore both, Index dock health (DS + Kontakt)."""
import json, os, socket, subprocess, sys, time, urllib.request, base64
from urllib.parse import urlparse

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_sides_restore.json"
PORT = 9367
PROFILE = "/tmp/catalog-sides-restore-verify"
URLS = [
    ("ds", "http://127.0.0.1:8788/DS-CATALOG.html?v=sides-restore"),
    ("kontakt", "http://127.0.0.1:8788/KONTAKT-CATALOG.html?v=sides-restore"),
]
os.makedirs(PROFILE, exist_ok=True)
subprocess.run(["pkill", "-f", "remote-debugging-port=9367"], check=False)
time.sleep(0.3)
chrome = "/usr/lib/chromium/chromium" if os.path.exists("/usr/lib/chromium/chromium") else "/usr/bin/chromium"
proc = subprocess.Popen(
    [
        chrome, "--headless=new", "--disable-gpu", "--no-first-run",
        "--disable-extensions", f"--remote-debugging-port={PORT}", "--remote-allow-origins=*",
        f"--user-data-dir={PROFILE}", "--noerrdialogs", "--ozone-platform=headless",
        "--ozone-override-screen-size=1400,900", "--use-angle=swiftshader-webgl", "about:blank",
    ],
    stdout=open("/tmp/catalog-sides-restore.log", "w"),
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
  function box(id){var el=document.getElementById(id);if(!el)return null;var b=el.getBoundingClientRect();return{x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height),disp:getComputedStyle(el).display};}
  function ixSnap(){
    var ix=document.getElementById('catalogIndex');
    var il=document.getElementById('catalogIndexList');
    var last=il&&il.querySelector('li:last-child');
    var cs=il&&getComputedStyle(il);
    var ixR=ix&&ix.getBoundingClientRect();
    var lastR=last&&last.getBoundingClientRect();
    var liR=il&&il.getBoundingClientRect();
    var colN=cs?String(cs.columnCount):'';
    return {
      col:!!(ix&&ix.classList.contains('is-collapsed')),
      box:box('catalogIndex'),
      sh:il?il.scrollHeight:null, ch:il?il.clientHeight:null, st:il?Math.round(il.scrollTop):null,
      ov:cs?cs.overflowY:'', cols:cs?(cs.columnCount+'/'+cs.columnWidth):'',
      sideways:!!(colN&&colN!=='auto'&&colN!=='1'&&parseInt(colN,10)>1),
      lastVis:!!(lastR&&ixR&&lastR.bottom<=ixR.bottom+4&&lastR.left>=ixR.left-2&&lastR.right<=ixR.right+6),
      lastInList:!!(lastR&&liR&&lastR.bottom<=liR.bottom+4)
    };
  }
  var out={title:document.title,vw:innerWidth,vh:innerHeight,fns:{
    hideSearchAc:typeof hideSearchAc==='function',
    collapseKwMenu:typeof collapseKwMenu==='function',
    resetIndexDock:typeof resetIndexDock==='function',
    toggleKwChrome:typeof toggleKwChrome==='function'
  }};

  if(typeof setDisplayMode==='function')setDisplayMode('sides');
  await sleep(280);
  out.sidesBase={
    fw:box('filterWrap'), ch:box('searchChrome'), cm:box('catalogMain'),
    rw:(getComputedStyle(document.body).getPropertyValue('--sides-rw')||'').trim(),
    lw:(getComputedStyle(document.body).getPropertyValue('--sides-lw')||'').trim(),
    kwHid:document.body.classList.contains('kw-chrome-collapsed'),
    hideBtn:box('kwStripHide'),
    hideTxt:(document.getElementById('kwStripHide')||{}).textContent||'',
    ix:ixSnap()
  };

  if(typeof collapseKwMenu==='function')collapseKwMenu();
  await sleep(160);
  var chip=document.getElementById('filterToggle');
  out.hideKw={
    kwHid:document.body.classList.contains('kw-chrome-collapsed'),
    rw:(getComputedStyle(document.body).getPropertyValue('--sides-rw')||'').trim(),
    fw:box('filterWrap'),
    chipDisp:chip?getComputedStyle(chip).display:'',
    chipW:chip?Math.round(chip.getBoundingClientRect().width):0,
    cmW:box('catalogMain')&&box('catalogMain').w,
    cmWider:!!(out.sidesBase.cm&&box('catalogMain')&&box('catalogMain').w>out.sidesBase.cm.w+40)
  };

  if(typeof collapseSearchMenu==='function')collapseSearchMenu();
  await sleep(160);
  out.hideBoth={
    searchCol:document.body.classList.contains('search-chrome-collapsed'),
    kwHid:document.body.classList.contains('kw-chrome-collapsed'),
    lw:(getComputedStyle(document.body).getPropertyValue('--sides-lw')||'').trim(),
    rw:(getComputedStyle(document.body).getPropertyValue('--sides-rw')||'').trim(),
    ch:box('searchChrome'), fw:box('filterWrap'), cm:box('catalogMain')
  };

  if(typeof setDisplayMode==='function')setDisplayMode('sides');
  await sleep(240);
  var ch=document.getElementById('searchChrome');
  var fw=document.getElementById('filterWrap');
  out.restore={
    searchCol:document.body.classList.contains('search-chrome-collapsed'),
    kwHid:document.body.classList.contains('kw-chrome-collapsed'),
    kwOpen:document.body.classList.contains('kw-open'),
    fwOpen:!!(fw&&fw.classList.contains('open')),
    chBack:!!(ch&&getComputedStyle(ch).display!=='none'&&ch.getBoundingClientRect().width>80),
    fwBack:!!(fw&&getComputedStyle(fw).display!=='none'&&fw.getBoundingClientRect().width>80),
    hideTxt:(document.getElementById('kwStripHide')||{}).textContent||'',
    ix:ixSnap()
  };

  var il=document.getElementById('catalogIndexList');
  var cm=document.getElementById('catalogMain');
  if(il){il.scrollTop=il.scrollHeight;await sleep(80);}
  out.ixScrollEnd=ixSnap();
  if(cm){cm.scrollTop=400;await sleep(80);}
  out.ixAfterCatalogScroll={col:!!(document.getElementById('catalogIndex')&&document.getElementById('catalogIndex').classList.contains('is-collapsed')), ix:ixSnap()};
  if(typeof setDisplayMode==='function')setDisplayMode('sides');
  await sleep(160);
  out.ixAfterSidesAgain=ixSnap();

  if(!document.body.classList.contains('layout-edit')&&typeof toggleLayoutEdit==='function')toggleLayoutEdit();
  await sleep(80);
  document.body.style.setProperty('--sides-index-h','220px');
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  await sleep(80);
  out.ixAfterResize=ixSnap();
  if(document.body.classList.contains('layout-edit')&&typeof toggleLayoutEdit==='function')toggleLayoutEdit();

  if(typeof setMode==='function')setMode('pick');
  await sleep(120);
  var pills=[].slice.call(document.querySelectorAll('#kwbar .kw:not(.clear):not(.active):not(.disabled)'));
  var sel0=typeof getSel==='function'?getSel().length:0;
  if(pills[0])pills[0].click();
  await sleep(80);
  out.pick={mode:typeof getCurrentMode==='function'?getCurrentMode():'',sel0:sel0,sel1:typeof getSel==='function'?getSel().length:0};

  out.checks={
    hideKwRw0: out.hideKw.rw==='0px',
    hideKwFwNone: !!(out.hideKw.fw&&(out.hideKw.fw.disp==='none'||out.hideKw.fw.w===0)),
    hideKwNoChip: out.hideKw.chipW===0||out.hideKw.chipDisp==='none',
    hideKwCatalogWider: !!out.hideKw.cmWider,
    hideBothFull: out.hideBoth.lw==='0px'&&out.hideBoth.rw==='0px'&&!!out.hideBoth.cm&&out.hideBoth.cm.w>900,
    restoreSearch: !!out.restore.chBack&&!out.restore.searchCol,
    restoreKw: !!out.restore.fwBack&&!out.restore.kwHid&&!!out.restore.kwOpen,
    ixHealthy: !!(out.restore.ix&&!out.restore.ix.col&&out.restore.ix.sh>out.restore.ix.ch+8),
    ixLastReachable: !!out.ixScrollEnd.lastVis||!!out.ixScrollEnd.lastInList,
    ixNoSideways: !out.restore.ix.sideways&&!out.ixScrollEnd.sideways,
    ixNoAutocollapse: !out.ixAfterCatalogScroll.col,
    ixUnstuckAfterSides: !out.ixAfterSidesAgain.col&&out.ixAfterSidesAgain.sh>out.ixAfterSidesAgain.ch+8,
    ixAfterResizeH: !!(out.ixAfterResize&&out.ixAfterResize.ch>40&&!out.ixAfterResize.col),
    pickWorks: out.pick.mode==='pick'&&out.pick.sel1>out.pick.sel0,
    hideSearchAc: !!out.fns.hideSearchAc,
    hideKwBtn: out.sidesBase.hideTxt.indexOf('Hide')>=0
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
        cdp.call("Emulation.setDeviceMetricsOverride", {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True})
        cdp.eval("window.dispatchEvent(new Event('resize'))")
        time.sleep(0.3)
        mobile = cdp.eval("""(function(){
          var btn=document.querySelector('[data-display="sides"]');
          return {has:!!btn, disp:btn?getComputedStyle(btn).display:'missing', vw:innerWidth};
        })()""")
        if isinstance(result, dict):
            result["mobileSides"] = mobile
            result.setdefault("checks", {})["mobileNoSides"] = not mobile or mobile.get("disp") == "none"
        all_out[key] = result
        try:
            cdp.ws.close()
        except Exception:
            pass
    open(OUT, "w").write(json.dumps(all_out, indent=2))
    print("WROTE", OUT)
    ok = True
    for key, result in all_out.items():
        if not isinstance(result, dict):
            print(key, result)
            ok = False
            continue
        checks = result.get("checks") or {}
        print(key, json.dumps(checks, indent=2))
        if not all(checks.values()):
            ok = False
            print(key, "FAIL keys", [k for k, v in checks.items() if not v])
    sys.exit(0 if ok else 2)
finally:
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except Exception:
        proc.kill()
