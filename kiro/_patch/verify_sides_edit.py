#!/usr/bin/env python3
"""Verify Sides hide-search, Index height persist, Customize/Lock, pointer handles."""
import base64, hashlib, json, os, socket, subprocess, sys, time, urllib.request
from urllib.parse import urlparse

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_sides_edit.json"
PORT = 9363
PROFILE = "/tmp/catalog-sides-edit-verify"
URLS = [
    ("ds", "http://127.0.0.1:8788/DS-CATALOG.html"),
    ("kontakt", "http://127.0.0.1:8788/KONTAKT-CATALOG.html"),
]
os.makedirs(PROFILE, exist_ok=True)
subprocess.run(["pkill", "-f", "remote-debugging-port=9363"], check=False)
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
    stdout=open("/tmp/catalog-sides-edit.log", "w"),
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
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        s.sendall(req.encode())
        hdr = b""
        while b"\r\n\r\n" not in hdr:
            chunk = s.recv(4096)
            if not chunk:
                raise RuntimeError("no ws handshake")
            hdr += chunk
        extra = hdr.split(b"\r\n\r\n", 1)[1]
        self.s = s
        self.buf = extra

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
        return json.load(
            urllib.request.urlopen(
                urllib.request.Request(f"http://127.0.0.1:{PORT}/json/new?" + url, method="PUT")
            )
        )
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
    return {w:Math.round(b.width),h:Math.round(b.height),x:Math.round(b.x),y:Math.round(b.y),
      disp:s.display,pe:s.pointerEvents,z:s.zIndex};
  }
  function labels(){
    return {
      customize:(document.getElementById('layoutEditBtn')||{}).textContent||'',
      lock:(document.getElementById('modePinBtn')||{}).textContent||'',
      dualPin:!!document.getElementById('dualFsSepPin')&&!document.getElementById('dualFsSepPin').hidden
        &&getComputedStyle(document.getElementById('dualFsSepPin')).display!=='none'
    };
  }
  var out={title:document.title,vw:innerWidth,vh:innerHeight,fns:{
    hideSearchAc:typeof hideSearchAc==='function',
    logSidesEdit:typeof logSidesEdit==='function',
    toggleModeLock:typeof toggleModeLock==='function',
    bindIndexHeight:typeof bindIndexHeight==='function'
  }};

  if(typeof setDisplayMode==='function')setDisplayMode('sides');
  await sleep(280);
  var ch=document.getElementById('searchChrome');
  var cm=document.getElementById('catalogMain');
  var hide=document.querySelector('.search-strip-hide');
  out.sidesOpen={
    collapsed:document.body.classList.contains('search-chrome-collapsed'),
    lw:(getComputedStyle(document.body).getPropertyValue('--sides-lw')||'').trim(),
    ch:box(ch),cm:box(cm),hide:hide?{txt:hide.textContent,box:box(hide)}:null,
    labels:labels()
  };

  if(typeof collapseSearchMenu==='function')collapseSearchMenu();
  await sleep(200);
  ch=document.getElementById('searchChrome');
  cm=document.getElementById('catalogMain');
  hide=document.querySelector('.search-strip-hide');
  out.sidesHide={
    collapsed:document.body.classList.contains('search-chrome-collapsed'),
    lw:(getComputedStyle(document.body).getPropertyValue('--sides-lw')||'').trim(),
    ch:box(ch),cm:box(cm),
    hideShown:!!(hide&&getComputedStyle(hide).display!=='none'&&hide.getBoundingClientRect().width>2),
    catalogAtLeft:cm?cm.getBoundingClientRect().x<8:null
  };

  if(typeof setDisplayMode==='function')setDisplayMode('sides');
  await sleep(250);
  ch=document.getElementById('searchChrome');
  out.sidesRestore={
    collapsed:document.body.classList.contains('search-chrome-collapsed'),
    lw:(getComputedStyle(document.body).getPropertyValue('--sides-lw')||'').trim(),
    ch:box(ch),
    searchBack:!!(ch&&getComputedStyle(ch).display!=='none'&&ch.getBoundingClientRect().width>80)
  };

  if(!document.body.classList.contains('layout-edit')&&typeof toggleLayoutEdit==='function')toggleLayoutEdit();
  await sleep(200);
  if(typeof bindIndexHeight==='function')bindIndexHeight();
  if(typeof ensureIndexHeightHandle==='function')ensureIndexHeightHandle();
  await sleep(80);
  var split=document.getElementById('searchSplit');
  var ixh=document.getElementById('indexHeight');
  var ix=document.getElementById('catalogIndex');
  out.customize={
    on:document.body.classList.contains('layout-edit'),
    labels:labels(),
    split:box(split),
    indexHandle:box(ixh),
    ix:box(ix)
  };

  var lw0=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0;
  if(split){
    var r=split.getBoundingClientRect();
    split.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,cancelable:true,clientX:r.left+4,clientY:r.top+40,pointerId:91,pointerType:'mouse',button:0}));
    document.dispatchEvent(new PointerEvent('pointermove',{bubbles:true,cancelable:true,clientX:r.left+70,clientY:r.top+40,pointerId:91,pointerType:'mouse'}));
    document.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,cancelable:true,clientX:r.left+70,clientY:r.top+40,pointerId:91,pointerType:'mouse'}));
    await sleep(160);
  }
  var lw1=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0;
  out.dragSplit={lw0:lw0,lw1:lw1,changed:lw1!==lw0};

  var h0=ix?Math.round(ix.getBoundingClientRect().height):0;
  if(ixh){
    var ir=ixh.getBoundingClientRect();
    ixh.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,cancelable:true,clientX:ir.left+20,clientY:ir.top+4,pointerId:92,pointerType:'mouse',button:0}));
    document.dispatchEvent(new PointerEvent('pointermove',{bubbles:true,cancelable:true,clientX:ir.left+20,clientY:ir.top+90,pointerId:92,pointerType:'mouse'}));
    document.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,cancelable:true,clientX:ir.left+20,clientY:ir.top+90,pointerId:92,pointerType:'mouse'}));
    await sleep(160);
  }
  var h1=ix?Math.round(ix.getBoundingClientRect().height):0;
  var slot=typeof readModeSlot==='function'?readModeSlot('sides'):null;
  out.dragIndex={h0:h0,h1:h1,changed:h1!==h0,indexH:slot&&slot.indexH,css:(getComputedStyle(document.body).getPropertyValue('--sides-index-h')||'').trim()};

  if(typeof toggleModeLock==='function')toggleModeLock();
  else {var pin=document.getElementById('modePinBtn');if(pin)pin.click();}
  await sleep(150);
  slot=typeof readModeSlot==='function'?readModeSlot('sides'):null;
  var splitPe=split?getComputedStyle(split).pointerEvents:'';
  var ixPe=ixh?getComputedStyle(ixh).pointerEvents:'';
  out.lock={
    labels:labels(),
    pinned:typeof modeLayoutPinned==='function'?modeLayoutPinned():null,
    slot:slot,
    splitPe:splitPe,ixPe:ixPe
  };
  var lw2=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0;
  if(split){
    var r2=split.getBoundingClientRect();
    split.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,cancelable:true,clientX:r2.left+4,clientY:r2.top+40,pointerId:93,pointerType:'mouse',button:0}));
    document.dispatchEvent(new PointerEvent('pointermove',{bubbles:true,cancelable:true,clientX:r2.left+120,clientY:r2.top+40,pointerId:93,pointerType:'mouse'}));
    document.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,cancelable:true,clientX:r2.left+120,clientY:r2.top+40,pointerId:93,pointerType:'mouse'}));
    await sleep(120);
  }
  var lw3=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0;
  out.lock.dragWhileLocked={lw2:lw2,lw3:lw3,moved:lw3!==lw2};

  if(typeof setMode==='function')setMode('pick');
  await sleep(150);
  var pills=[].slice.call(document.querySelectorAll('#kwbar .kw:not(.clear):not(.active):not(.disabled)'));
  var sel0=typeof getSel==='function'?getSel().length:0;
  if(pills[0])pills[0].click();
  await sleep(120);
  out.pick={mode:typeof getCurrentMode==='function'?getCurrentMode():'',sel0:sel0,sel1:typeof getSel==='function'?getSel().length:0};

  return out;
  }catch(err){return {err:String(err),stack:err&&err.stack};}
})()
"""


def wait_ready(cdp):
    ready = None
    for _ in range(50):
        ready = cdp.eval(
            "typeof setDisplayMode==='function'&&typeof collapseSearchMenu==='function'&&document.querySelectorAll('.entry').length"
        )
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
        time.sleep(2.0)
        cdp.call(
            "Emulation.setDeviceMetricsOverride",
            {"width": 1400, "height": 900, "deviceScaleFactor": 1, "mobile": False},
        )
        ready = wait_ready(cdp)
        result = cdp.eval(EXPR)
        cdp.call("Page.reload", {"ignoreCache": True})
        time.sleep(2.2)
        wait_ready(cdp)
        persist = cdp.eval(
            r"""
(function(){
  if(typeof setDisplayMode==='function')setDisplayMode('sides');
  var slot=typeof readModeSlot==='function'?readModeSlot('sides'):null;
  var ix=document.getElementById('catalogIndex');
  return {
    slot:slot,
    lw:parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0,
    indexCss:(getComputedStyle(document.body).getPropertyValue('--sides-index-h')||'').trim(),
    ixH:ix?Math.round(ix.getBoundingClientRect().height):null,
    customize:(document.getElementById('layoutEditBtn')||{}).textContent||'',
    lock:(document.getElementById('modePinBtn')||{}).textContent||'',
    collapsed:document.body.classList.contains('search-chrome-collapsed')
  };
})()
"""
        )
        cdp.call(
            "Emulation.setDeviceMetricsOverride",
            {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True},
        )
        time.sleep(0.7)
        mobile = cdp.eval(
            r"""
(function(){
  var btn=document.querySelector('.display-btn[data-display="sides"]');
  var s=btn&&getComputedStyle(btn);
  return {exists:!!btn,disp:s&&s.display,shown:!!(btn&&s&&s.display!=='none'&&btn.getBoundingClientRect().width>2)};
})()
"""
        )
        if isinstance(result, dict):
            result["reload"] = persist
            result["mobile"] = mobile
            result["readyEntries"] = ready
        else:
            result = {"raw": result, "reload": persist, "mobile": mobile, "readyEntries": ready}
        all_out[key] = result
        try:
            cdp.ws.close()
        except Exception:
            pass
    open(OUT, "w").write(json.dumps(all_out, indent=2))
    print("WROTE", OUT)
    print(json.dumps(all_out, indent=2)[:6000])
finally:
    proc.terminate()
