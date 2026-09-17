#!/usr/bin/env python3
"""CDP: header Search/K, Sides index collapse/cols/embed, search buttons in 3 modes."""
import json, os, socket, subprocess, sys, time, urllib.request, base64
from urllib.parse import urlparse

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_ui_chrome_index.json"
PORT = 9371
PROFILE = "/tmp/catalog-ui-chrome-index"
URLS = [
    ("ds", "http://127.0.0.1:8788/DS-CATALOG.html?v=ui-chrome"),
    ("kontakt", "http://127.0.0.1:8788/KONTAKT-CATALOG.html?v=ui-chrome"),
]
os.makedirs(PROFILE, exist_ok=True)
subprocess.run(["pkill", "-f", "remote-debugging-port=9371"], check=False)
time.sleep(0.3)
chrome = "/usr/lib/chromium/chromium" if os.path.exists("/usr/lib/chromium/chromium") else "/usr/bin/chromium"
proc = subprocess.Popen(
    [
        chrome, "--headless=new", "--disable-gpu", "--no-first-run",
        "--disable-extensions", f"--remote-debugging-port={PORT}", "--remote-allow-origins=*",
        f"--user-data-dir={PROFILE}", "--noerrdialogs", "--ozone-platform=headless",
        "--ozone-override-screen-size=1400,900", "--use-angle=swiftshader-webgl", "about:blank",
    ],
    stdout=open("/tmp/catalog-ui-chrome-index.log", "w"),
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
  function vis(id){
    var el=document.getElementById(id)||document.querySelector(id);
    if(!el)return {ok:false};
    var s=getComputedStyle(el), b=el.getBoundingClientRect();
    return {ok:s.display!=='none'&&s.visibility!=='hidden'&&b.width>8&&b.height>8, disp:s.display, w:Math.round(b.width), h:Math.round(b.height), x:Math.round(b.x), y:Math.round(b.y)};
  }
  function ixInfo(){
    var ix=document.getElementById('catalogIndex');
    var il=document.getElementById('catalogIndexList');
    if(!ix||!il)return null;
    var cs=getComputedStyle(il);
    var cols=cs.gridTemplateColumns.split(' ').filter(Boolean).length;
    var last=il.querySelector('li:last-child');
    if(il.scrollHeight>il.clientHeight+8)il.scrollTop=il.scrollHeight;
    var lastR=last&&last.getBoundingClientRect();
    var liR=il.getBoundingClientRect();
    return {
      collapsed:ix.classList.contains('is-collapsed'),
      embedded:ix.classList.contains('is-embedded'),
      ixH:Math.round(ix.getBoundingClientRect().height),
      listDisp:cs.display, cols:cols, ov:cs.overflowY,
      sh:il.scrollHeight, ch:il.clientHeight,
      lastVis:!!(lastR&&liR&&lastR.bottom<=liR.bottom+8)
    };
  }
  var out={};

  if(typeof setDisplayMode==='function')setDisplayMode('upper');
  if(typeof expandSearchMenu==='function')expandSearchMenu();
  if(typeof expandKwMenu==='function')expandKwMenu();
  else {var w=document.getElementById('filterWrap'); if(w)w.classList.add('open'); document.body.classList.add('kw-open');}
  await sleep(250);
  out.upper={
    hdrSearch:vis('hdrSearchBtn'), hdrKw:vis('hdrKwBtn'),
    hide:vis('.search-strip-hide')||{},
    clear:vis('.search-strip-clear'),
    more:vis('#searchStripMore'),
    fs:vis('searchStripFs'),
    chromeH:(function(){var el=document.getElementById('searchChrome');return el?Math.round(el.getBoundingClientRect().height):0;})(),
    well:(function(){var ch=document.getElementById('searchChrome');var ix=document.getElementById('catalogIndex');if(!ch||!ix)return null;return Math.round(ix.getBoundingClientRect().top-ch.getBoundingClientRect().bottom);})(),
    sides:document.body.classList.contains('display-sides'),
    fsMode:document.body.classList.contains('display-fs')
  };

  if(typeof setDisplayMode==='function')setDisplayMode('sides');
  await sleep(280);
  out.sidesHdr={hdrSearch:vis('hdrSearchBtn'), hdrKw:vis('hdrKwBtn'), hide:vis('.search-strip-hide'), clear:vis('.search-strip-clear'), more:vis('#searchStripMore'), ix:ixInfo()};
  if(typeof toggleCatalogIndex==='function')toggleCatalogIndex();
  await sleep(120);
  out.sidesCollapse=ixInfo();
  if(typeof toggleCatalogIndex==='function')toggleCatalogIndex();
  await sleep(80);
  out.sidesExpand=ixInfo();
  if(typeof toggleIndexEmbed==='function')toggleIndexEmbed();
  await sleep(120);
  out.sidesEmbed=ixInfo();
  if(typeof toggleIndexEmbed==='function')toggleIndexEmbed();
  if(typeof toggleHdrSearch==='function')toggleHdrSearch();
  await sleep(80);
  out.sidesHideSearch={collapsed:document.body.classList.contains('search-chrome-collapsed'), chDisp:(function(){var el=document.getElementById('searchChrome');return el?getComputedStyle(el).display:'missing';})()};
  if(typeof toggleHdrSearch==='function')toggleHdrSearch();
  if(typeof toggleHdrKw==='function')toggleHdrKw();
  await sleep(80);
  out.sidesHideKw={kwHid:document.body.classList.contains('kw-chrome-collapsed'), fwDisp:(function(){var el=document.getElementById('filterWrap');return el?getComputedStyle(el).display:'missing';})()};
  if(typeof toggleHdrKw==='function')toggleHdrKw();

  if(typeof setDisplayMode==='function')setDisplayMode('fs');
  await sleep(280);
  out.full={
    fs:document.body.classList.contains('display-fs'),
    sides:document.body.classList.contains('display-sides'),
    hdrSearch:vis('hdrSearchBtn'), hdrKw:vis('hdrKwBtn'),
    hide:vis('.search-strip-hide'), clear:vis('.search-strip-clear'),
    more:vis('#searchStripMore'), fsBtn:vis('#searchStripFs')
  };

  out.pass={
    hdrUpper:!!(out.upper.hdrSearch&&out.upper.hdrSearch.ok&&out.upper.hdrKw&&out.upper.hdrKw.ok),
    hdrSides:!!(out.sidesHdr.hdrSearch&&out.sidesHdr.hdrSearch.ok),
    hdrFull:!!(out.full.hdrSearch&&out.full.hdrSearch.ok),
    collapse:!!(out.sidesCollapse&&out.sidesCollapse.collapsed&&out.sidesCollapse.listDisp==='none'),
    cols:!!(out.sidesExpand&&out.sidesExpand.cols>=1&&out.sidesExpand.cols<=3),
    embed:!!(out.sidesEmbed&&out.sidesEmbed.embedded),
    hideSearch:!!(out.sidesHideSearch&&out.sidesHideSearch.collapsed),
    hideKw:!!(out.sidesHideKw&&out.sidesHideKw.kwHid),
    fullIndep:!!(out.full.fs&&!out.full.sides),
    fullHide:!!(out.full.hide&&out.full.hide.ok),
    upperBtns:!!(out.upper.hide&&out.upper.hide.ok&&out.upper.more&&out.upper.more.ok),
    upperWell:typeof out.upper.well==='number'&&out.upper.well<220
  };
  return out;
})()
"""


def judge(data):
    p = data.get("pass") or {}
    fails = [k for k, v in p.items() if not v]
    return fails


results = {}
try:
    for key, url in URLS:
        tab = new_tab(url)
        cdp = CDP(tab["webSocketDebuggerUrl"])
        cdp.call("Runtime.enable")
        cdp.call("Page.enable")
        for _ in range(40):
            ready = cdp.eval("document.readyState==='complete' && typeof setDisplayMode==='function'")
            if ready:
                break
            time.sleep(0.25)
        data = cdp.eval(EXPR)
        data["fails"] = judge(data)
        results[key] = data
        print(key, "fails", data["fails"] or "none")
finally:
    proc.terminate()

open(OUT, "w").write(json.dumps(results, indent=2))
print("WROTE", OUT)
if any((results.get(k) or {}).get("fails") for k in results):
    sys.exit(1)
