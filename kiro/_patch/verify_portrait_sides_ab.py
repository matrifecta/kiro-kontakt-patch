#!/usr/bin/env python3
"""CDP: desktop Sides landscape 3-col + portrait A/B stacked menus, ±30% clamp."""
import base64, json, os, socket, subprocess, sys, time, urllib.request
from urllib.parse import urlparse

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_portrait_sides_ab.json"
SHOTS = "/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots"
PORT = 9394
PROFILE = "/tmp/catalog-portrait-ab-verify"
URL = "http://127.0.0.1:8788/DS-CATALOG.html"
os.makedirs(SHOTS, exist_ok=True)
os.makedirs(PROFILE, exist_ok=True)
subprocess.run(["pkill", "-f", f"remote-debugging-port={PORT}"], check=False)
time.sleep(0.3)
chrome = next(
    (
        p
        for p in (
            "/usr/lib/chromium/chromium",
            "/usr/bin/chromium",
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
        )
        if os.path.exists(p)
    ),
    None,
)
if not chrome:
    raise SystemExit("no chromium")
proc = subprocess.Popen(
    [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--disable-extensions",
        f"--remote-debugging-port={PORT}",
        "--remote-allow-origins=*",
        f"--user-data-dir={PROFILE}",
        "--noerrdialogs",
        "--ozone-platform=headless",
        "--ozone-override-screen-size=1920,1200",
        "--use-angle=swiftshader-webgl",
        "about:blank",
    ],
    stdout=open("/tmp/catalog-portrait-ab.log", "w"),
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

    def shot(self, name):
        data = self.call("Page.captureScreenshot", {"format": "png"}).get("data")
        path = os.path.join(SHOTS, name)
        if data:
            open(path, "wb").write(base64.b64decode(data))
        return path


def new_tab(url):
    try:
        return json.load(
            urllib.request.urlopen(
                urllib.request.Request(f"http://127.0.0.1:{PORT}/json/new?" + url, method="PUT")
            )
        )
    except Exception:
        return json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/new?" + url))


GEOM = r"""
(function(){
  function box(id){
    var el=document.getElementById(id);
    if(!el)return null;
    var b=el.getBoundingClientRect(),s=getComputedStyle(el);
    return {x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height),disp:s.display,cursor:s.cursor};
  }
  var ch=box('searchChrome'), fw=box('filterWrap'), cm=box('catalogMain'), ix=box('catalogIndex');
  var split=box('searchSplit'), sep=box('dualFsSep');
  var menusLeft = !!(ch && fw && cm && ch.x < cm.x && fw.x < cm.x && Math.abs(ch.x-fw.x)<40);
  var menusRight = !!(ch && fw && cm && ch.x > cm.x && fw.x > cm.x && Math.abs(ch.x-fw.x)<40);
  var stacked = !!(ch && fw && Math.abs(ch.x-fw.x)<40 && fw.y > ch.y + 40);
  var threeCol = !!(ch && fw && cm && ch.x < cm.x && cm.x < fw.x && Math.abs(ch.y-cm.y)<80 && Math.abs(fw.y-cm.y)<80);
  var topRow = !!(ch && fw && cm && Math.abs(ch.y-fw.y)<40 && cm.y > (ch.y+ch.h) - 8);
  return {
    vw:innerWidth,vh:innerHeight,
    portrait:matchMedia('(orientation:portrait)').matches,
    desk:matchMedia('(min-width:900px)').matches,
    flip:document.body.classList.contains('sides-portrait-flip'),
    edit:document.body.classList.contains('layout-edit'),
    searchCol:document.body.classList.contains('search-chrome-collapsed'),
    kwHid:document.body.classList.contains('kw-chrome-collapsed'),
    lw:(getComputedStyle(document.documentElement).getPropertyValue('--portrait-lw')||'').trim(),
    mh:(getComputedStyle(document.documentElement).getPropertyValue('--portrait-menu-h')||'').trim(),
    sidesLw:(getComputedStyle(document.body).getPropertyValue('--sides-lw')||'').trim(),
    sidesRw:(getComputedStyle(document.body).getPropertyValue('--sides-rw')||'').trim(),
    gridCols:getComputedStyle(document.body).gridTemplateColumns,
    gridRows:getComputedStyle(document.body).gridTemplateRows,
    ch:ch,fw:fw,cm:cm,ix:ix,split:split,sep:sep,
    menusLeft:menusLeft,menusRight:menusRight,stacked:stacked,threeCol:threeCol,topRow:topRow,
    fns:{apply:typeof applyPortraitSides==='function',flip:typeof togglePortraitSidesFlip==='function',clamp:typeof clampPortraitTravel==='function'}
  };
})()
"""


def wait_ready(cdp):
    for _ in range(50):
        ready = cdp.eval(
            "typeof setDisplayMode==='function'&&typeof applyPortraitSides==='function'&&document.querySelectorAll('.entry').length"
        )
        if isinstance(ready, int) and ready > 5:
            return ready
        time.sleep(0.25)
    return cdp.eval("typeof setDisplayMode==='function'&&typeof applyPortraitSides")


def set_view(cdp, w, h):
    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False},
    )
    time.sleep(0.45)
    cdp.eval("if(typeof applySidesCols==='function')applySidesCols();")
    time.sleep(0.25)


out = {}
try:
    tab = new_tab(URL)
    cdp = CDP(tab["webSocketDebuggerUrl"])
    cdp.call("Page.enable")
    cdp.call("Runtime.enable")
    time.sleep(2.2)
    set_view(cdp, 1920, 900)
    ready = wait_ready(cdp)
    cdp.eval(
        r"""
(function(){
  try{
    ['catalog-portrait-lw','catalog-portrait-rw','catalog-portrait-menu-h'].forEach(function(k){localStorage.removeItem(k);});
    Object.keys(localStorage).forEach(function(k){if(k.indexOf('catalog-sides-portrait-flip')===0)localStorage.removeItem(k);});
  }catch(e){}
  if(typeof setDisplayMode==='function')setDisplayMode('sides');
  if(document.body.classList.contains('layout-edit')&&typeof toggleLayoutEdit==='function')toggleLayoutEdit();
  if(typeof applyLayoutChrome==='function')applyLayoutChrome('sck');
  if(typeof applyPortraitSides==='function')applyPortraitSides();
  if(typeof applySidesCols==='function')applySidesCols();
})()
"""
    )
    time.sleep(0.4)
    out["readyEntries"] = ready
    out["landscape"] = cdp.eval(GEOM)
    out["shots"] = {"landscape": cdp.shot("D1920-sides-landscape.png")}

    set_view(cdp, 900, 1200)
    time.sleep(0.3)
    out["portraitA"] = cdp.eval(GEOM)
    out["shots"]["portraitA"] = cdp.shot("D900-sides-portrait-A.png")

    cdp.eval(
        r"""
(function(){
  if(!document.body.classList.contains('layout-edit')&&typeof toggleLayoutEdit==='function')toggleLayoutEdit();
  if(typeof applySidesCols==='function')applySidesCols();
})()
"""
    )
    time.sleep(0.25)
    out["portraitA_edit"] = cdp.eval(GEOM)
    out["shots"]["portraitA_edit"] = cdp.shot("D900-sides-portrait-A-edit.png")

    out["clamp"] = cdp.eval(
        r"""
(async function(){
  function sleep(ms){return new Promise(r=>setTimeout(r,ms));}
  var d=portraitSidesDefaults();
  var split=document.getElementById('searchSplit');
  var sep=document.getElementById('dualFsSep');
  var mh0=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--portrait-menu-h'),10)||0;
  var lw0=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--portrait-lw'),10)||0;
  if(split){
    var r=split.getBoundingClientRect();
    split.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,cancelable:true,clientX:r.left+20,clientY:r.top+6,pointerId:201,pointerType:'mouse',button:0}));
    document.dispatchEvent(new PointerEvent('pointermove',{bubbles:true,cancelable:true,clientX:r.left+20,clientY:r.top+2000,pointerId:201,pointerType:'mouse'}));
    document.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,cancelable:true,clientX:r.left+20,clientY:r.top+2000,pointerId:201,pointerType:'mouse'}));
    await sleep(120);
  }
  var mh1=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--portrait-menu-h'),10)||0;
  if(sep){
    var r2=sep.getBoundingClientRect();
    sep.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,cancelable:true,clientX:r2.left+6,clientY:r2.top+80,pointerId:202,pointerType:'mouse',button:0}));
    document.dispatchEvent(new PointerEvent('pointermove',{bubbles:true,cancelable:true,clientX:r2.left+2000,clientY:r2.top+80,pointerId:202,pointerType:'mouse'}));
    document.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,cancelable:true,clientX:r2.left+2000,clientY:r2.top+80,pointerId:202,pointerType:'mouse'}));
    await sleep(120);
  }
  var lw1=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--portrait-lw'),10)||0;
  var maxH=d.searchH+0.3*d.availH;
  var maxW=d.stackW+0.3*d.availW;
  return {
    def:d,mh0:mh0,mh1:mh1,lw0:lw0,lw1:lw1,
    maxH:Math.round(maxH),maxW:Math.round(maxW),
    hClamped:mh1<=maxH+2 && mh1>=d.searchH-2,
    wClamped:lw1<=maxW+2 && lw1>=d.stackW-2,
    stored:{lw:localStorage.getItem('catalog-portrait-lw'),mh:localStorage.getItem('catalog-portrait-menu-h')}
  };
})()
"""
    )
    out["shots"]["portraitA_clamped"] = cdp.shot("D900-sides-portrait-A-clamped.png")

    # restore defaults then flip
    cdp.eval(
        r"""
(function(){
  try{
    localStorage.removeItem('catalog-portrait-lw');
    localStorage.removeItem('catalog-portrait-rw');
    localStorage.removeItem('catalog-portrait-menu-h');
  }catch(e){}
  if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();
  if(typeof applySidesCols==='function')applySidesCols();
})()
"""
    )
    time.sleep(0.3)
    out["portraitB"] = cdp.eval(GEOM)
    out["shots"]["portraitB"] = cdp.shot("D900-sides-portrait-B.png")

    out["hideSearch"] = cdp.eval(
        r"""
(function(){
  if(typeof applyLayoutChrome==='function')applyLayoutChrome('sck');
  if(typeof toggleHdrSearch==='function')toggleHdrSearch();
  else if(typeof collapseSearchMenu==='function')collapseSearchMenu();
  if(typeof applySidesCols==='function')applySidesCols();
  var ch=document.getElementById('searchChrome');
  var fw=document.getElementById('filterWrap');
  var cm=document.getElementById('catalogMain');
  var cb=function(el){if(!el)return null;var b=el.getBoundingClientRect();return {x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height),disp:getComputedStyle(el).display};};
  return {flip:document.body.classList.contains('sides-portrait-flip'),ch:cb(ch),fw:cb(fw),cm:cb(cm),searchCol:document.body.classList.contains('search-chrome-collapsed'),flipBtn:(document.getElementById('portraitFlipBtn')||{}).textContent||''};
})()
"""
    )
    out["shots"]["portraitB_ck"] = cdp.shot("D900-sides-portrait-B-ck.png")

    out["hideKw"] = cdp.eval(
        r"""
(function(){
  if(typeof expandSearchMenu==='function')expandSearchMenu();
  if(typeof toggleHdrKw==='function')toggleHdrKw();
  else if(typeof collapseKwMenu==='function')collapseKwMenu();
  if(typeof applySidesCols==='function')applySidesCols();
  var ch=document.getElementById('searchChrome');
  var fw=document.getElementById('filterWrap');
  var cm=document.getElementById('catalogMain');
  var cb=function(el){if(!el)return null;var b=el.getBoundingClientRect();return {x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height),disp:getComputedStyle(el).display};};
  return {flip:document.body.classList.contains('sides-portrait-flip'),ch:cb(ch),fw:cb(fw),cm:cb(cm),kwHid:document.body.classList.contains('kw-chrome-collapsed')};
})()
"""
    )
    out["shots"]["portraitB_sc"] = cdp.shot("D900-sides-portrait-B-sc.png")

    out["contentOnly"] = cdp.eval(
        r"""
(function(){
  if(typeof collapseSearchMenu==='function')collapseSearchMenu();
  if(typeof collapseKwMenu==='function')collapseKwMenu();
  if(typeof applySidesCols==='function')applySidesCols();
  var cm=document.getElementById('catalogMain');
  var b=cm&&cm.getBoundingClientRect();
  return {flip:document.body.classList.contains('sides-portrait-flip'),cm:b?{x:Math.round(b.x),w:Math.round(b.width),h:Math.round(b.height)}:null,vw:innerWidth,searchCol:document.body.classList.contains('search-chrome-collapsed'),kwHid:document.body.classList.contains('kw-chrome-collapsed')};
})()
"""
    )

    # back to landscape to confirm 3-col still works
    cdp.eval(
        "if(typeof applyLayoutChrome==='function')applyLayoutChrome('sck');if(typeof applySidesCols==='function')applySidesCols();"
    )
    set_view(cdp, 1920, 900)
    time.sleep(0.3)
    out["landscape_after"] = cdp.eval(GEOM)
    out["shots"]["landscape_after"] = cdp.shot("D1920-sides-landscape-after.png")

    open(OUT, "w").write(json.dumps(out, indent=2))
    print("WROTE", OUT)
    summary = {
        "landscape_threeCol": (out.get("landscape") or {}).get("threeCol"),
        "portraitA_left_stacked": {
            "menusLeft": (out.get("portraitA") or {}).get("menusLeft"),
            "stacked": (out.get("portraitA") or {}).get("stacked"),
            "topRow": (out.get("portraitA") or {}).get("topRow"),
        },
        "portraitB_right_stacked": {
            "menusRight": (out.get("portraitB") or {}).get("menusRight"),
            "stacked": (out.get("portraitB") or {}).get("stacked"),
            "flip": (out.get("portraitB") or {}).get("flip"),
        },
        "clamp": out.get("clamp"),
        "hideSearch_fw": (out.get("hideSearch") or {}).get("fw"),
        "hideKw_ch": (out.get("hideKw") or {}).get("ch"),
        "contentOnly": out.get("contentOnly"),
        "landscape_after": (out.get("landscape_after") or {}).get("threeCol"),
        "fns": (out.get("portraitA") or {}).get("fns"),
        "shots": out.get("shots"),
    }
    print(json.dumps(summary, indent=2))
    try:
        cdp.ws.close()
    except Exception:
        pass
finally:
    proc.terminate()
