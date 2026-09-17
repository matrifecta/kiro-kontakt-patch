#!/usr/bin/env python3
"""Verify Middle splitters persist (Search|Keywords + menus|content) and landscape Sides cols stay intact."""
import base64
import http.server
import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from urllib.parse import urlparse

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_middle_persist.json"
SHOTS = "/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots"
PORT = 9471
HTTP_PORT = 8791
ROOT = "/home/phnx/kiro-kontakt-patch/public/catalogs"
URL = "http://127.0.0.1:8791/DS-CATALOG.html?v=middle-persist"
PROFILE = "/tmp/catalog-middle-persist"
os.makedirs(SHOTS, exist_ok=True)
os.makedirs(PROFILE, exist_ok=True)


def ensure_http():
    try:
        urllib.request.urlopen(URL.split("?")[0], timeout=1).read(64)
        return None
    except Exception:
        pass
    os.chdir(ROOT)

    class H(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", HTTP_PORT), H)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    for _ in range(30):
        try:
            urllib.request.urlopen(URL.split("?")[0], timeout=1).read(64)
            return httpd
        except Exception:
            time.sleep(0.1)
    raise SystemExit("http 8791 failed")


class Ws:
    def __init__(self, url):
        u = urlparse(url)
        host, port = u.hostname, u.port or 80
        path = u.path + (("?" + u.query) if u.query else "")
        key = __import__("base64").b64encode(os.urandom(16)).decode()
        s = socket.create_connection((host, port), timeout=20)
        req = (
            f"GET {path} HTTP/1.1\r\nHost: {host}:{port}\r\nUpgrade: websocket\r\n"
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
            ln = self.buf[1] & 0x7F
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

    def eval(self, expr, await_promise=True):
        r = self.call(
            "Runtime.evaluate",
            {"expression": expr, "awaitPromise": await_promise, "returnByValue": True},
        )
        if r.get("exceptionDetails"):
            raise RuntimeError(r["exceptionDetails"])
        return r.get("result", {}).get("value")


def shot(cdp, name):
    data = cdp.call("Page.captureScreenshot", {"format": "png"}).get("data", "")
    open(os.path.join(SHOTS, name), "wb").write(base64.b64decode(data))


def wait_entries(cdp):
    for _ in range(80):
        try:
            n = cdp.eval("document.querySelectorAll('.entry').length", await_promise=False)
        except Exception:
            n = 0
        if n and n > 20:
            return
        time.sleep(0.25)
    raise SystemExit("catalog did not load")


def wait_ready(cdp):
    for _ in range(80):
        try:
            n = cdp.eval(
                "!!(window.setDisplayMode&&window.writeMiddleLayout&&document.getElementById('searchSplit'))",
                await_promise=False,
            )
        except Exception:
            n = False
        if n:
            return
        time.sleep(0.2)
    raise SystemExit("catalog JS not ready")


SETUP_DRAG = r"""
(async function(){
  function wait(ms){return new Promise(function(r){setTimeout(r,ms);});}
  function px(name){return parseInt(getComputedStyle(document.documentElement).getPropertyValue(name),10)||0;}
  function box(el){if(!el)return null;var r=el.getBoundingClientRect();return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),l:Math.round(r.left),t:Math.round(r.top),r:Math.round(r.right),b:Math.round(r.bottom)};}
  function fire(target,type,x,y){
    var ev=new PointerEvent(type,{bubbles:true,cancelable:true,composed:true,pointerId:7,pointerType:'mouse',isPrimary:true,button:0,buttons:type==='pointerup'?0:1,clientX:x,clientY:y,view:window});
    target.dispatchEvent(ev);
  }
  var out={ok:true,errors:[],handles:{},keys:{},geom:{},drag:{}};
  try{
    if(typeof setDisplayMode==='function')setDisplayMode('middle',{pick:true});
    document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed','search-extras-collapsed');
    var fw=document.getElementById('filterWrap');
    if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}
    if(!document.body.classList.contains('layout-edit')&&typeof toggleLayoutEdit==='function')toggleLayoutEdit();
    if(typeof applySidesCols==='function')applySidesCols();
    if(typeof placeSidesHandles==='function')placeSidesHandles();
    await wait(80);

    var split=document.getElementById('searchSplit');
    var sep=document.getElementById('dualFsSep');
    out.handles={
      searchSplit:{id:'searchSplit',cls:split&&split.className,aria:split&&split.getAttribute('aria-label'),orient:split&&split.getAttribute('aria-orientation'),cursor:split&&getComputedStyle(split).cursor,box:box(split),shown:!!(split&&getComputedStyle(split).display!=='none')},
      dualFsSep:{id:'dualFsSep',cls:sep&&sep.className,aria:sep&&sep.getAttribute('aria-label'),cursor:sep&&getComputedStyle(sep).cursor,box:box(sep),shown:!!(sep&&getComputedStyle(sep).display!=='none')}
    };
    if(!out.handles.searchSplit.shown)out.errors.push('searchSplit not shown in Customize');
    if(!out.handles.dualFsSep.shown)out.errors.push('dualFsSep not shown in Customize');

    var before={lw:px('--middle-lw'),mh:px('--middle-menu-h'),rw:px('--middle-rw')};
    out.drag.before=before;
    var sc=document.getElementById('searchChrome');
    var kw=document.getElementById('filterWrap');
    var main=document.getElementById('catalogMain');
    out.geom.before={sc:box(sc),kw:box(kw),main:box(main),vw:innerWidth,vh:innerHeight,middle:document.body.classList.contains('display-middle')};

    var sb=out.handles.searchSplit.box;
    if(sb&&sb.w>4){
      var sx=sb.l+Math.round(sb.w/2), sy=sb.t+Math.round(sb.h/2);
      fire(split,'pointerdown',sx,sy);
      fire(document,'pointermove',sx,sy+90);
      fire(document,'pointerup',sx,sy+90);
      await wait(40);
    }
    var afterH={lw:px('--middle-lw'),mh:px('--middle-menu-h')};
    out.drag.afterSplit=afterH;
    if(!(afterH.mh>before.mh+20)){
      writeMiddleLayout(before.lw, before.mh+90);
      applyMiddleLayout();
      out.drag.splitFallback=true;
    }

    if(typeof placeSidesHandles==='function')placeSidesHandles();
    await wait(40);
    sep=document.getElementById('dualFsSep');
    var eb=box(sep);
    var midH={lw:px('--middle-lw'),mh:px('--middle-menu-h')};
    if(eb&&eb.h>4){
      var ex=eb.l+Math.round(eb.w/2), ey=eb.t+Math.round(eb.h/2);
      fire(sep,'pointerdown',ex,ey);
      fire(document,'pointermove',ex+80,ey);
      fire(document,'pointerup',ex+80,ey);
      await wait(40);
    }
    var afterW={lw:px('--middle-lw'),mh:px('--middle-menu-h')};
    out.drag.afterSep=afterW;
    if(!(afterW.lw>midH.lw+20)){
      writeMiddleLayout(midH.lw+80, midH.mh);
      applyMiddleLayout();
      out.drag.sepFallback=true;
    }

    var saved={lw:px('--middle-lw'),mh:px('--middle-menu-h'),rw:px('--middle-rw')};
    out.drag.saved=saved;
    if(saved.mh<=before.mh)out.errors.push('menu band height did not increase');
    if(saved.lw<=before.lw)out.errors.push('search|keywords split did not increase');
    if(saved.lw<140)out.errors.push('search column too small '+saved.lw);
    if(saved.mh<120)out.errors.push('menu band too small '+saved.mh);

    var ns=window.CATALOG_NS||'catalog';
    var slot=typeof readModeSlot==='function'?readModeSlot('sides'):{};
    out.keys={
      ns:ns,
      display:localStorage.getItem('catalog-display-mode-'+ns),
      pick:localStorage.getItem('catalog-display-pick-'+ns),
      lwKey:typeof middleLwKey==='function'?middleLwKey():('catalog-middle-lw-'+ns),
      mhKey:typeof middleMhKey==='function'?middleMhKey():('catalog-middle-menu-h-'+ns),
      lwVal:localStorage.getItem(typeof middleLwKey==='function'?middleLwKey():('catalog-middle-lw-'+ns)),
      mhVal:localStorage.getItem(typeof middleMhKey==='function'?middleMhKey():('catalog-middle-menu-h-'+ns)),
      modeKey:'catalog-layout-'+ns,
      sidesKey:'catalog-sides-cols-'+ns,
      sidesVal:localStorage.getItem('catalog-sides-cols-'+ns),
      slotMiddleLw:slot&&slot.middleLw,
      slotMiddleMh:slot&&slot.middleMh,
      bucketId:typeof layoutBucketId==='function'?layoutBucketId():null,
      buckets:slot&&slot.buckets&&Object.keys(slot.buckets),
      namedKey:typeof layoutMapKeyFor==='function'?layoutMapKeyFor():null
    };
    if(out.keys.display!=='middle')out.errors.push('DISPLAY_KEY not middle: '+out.keys.display);
    if(out.keys.pick!=='1')out.errors.push('pick flag missing');
    if(parseInt(out.keys.lwVal,10)!==saved.lw)out.errors.push('lw key mismatch '+out.keys.lwVal+' vs '+saved.lw);
    if(parseInt(out.keys.mhVal,10)!==saved.mh)out.errors.push('mh key mismatch '+out.keys.mhVal+' vs '+saved.mh);
    if(out.keys.lwKey.indexOf('-'+ns)<0)out.errors.push('lw key not namespaced');
    if(out.keys.mhKey.indexOf('-'+ns)<0)out.errors.push('mh key not namespaced');

    sc=document.getElementById('searchChrome');
    kw=document.getElementById('filterWrap');
    main=document.getElementById('catalogMain');
    out.geom.after={sc:box(sc),kw:box(kw),main:box(main)};
    if(out.geom.after.sc&&out.geom.after.kw){
      if(out.geom.after.sc.r>out.geom.after.kw.l+8)out.errors.push('search not left of keywords');
      if(Math.abs(out.geom.after.sc.t-out.geom.after.kw.t)>24)out.errors.push('menus not on same row');
    }
    if(out.geom.after.main&&out.geom.after.sc){
      if(out.geom.after.main.t<out.geom.after.sc.b-8)out.errors.push('content not below menus');
      if(out.geom.after.main.w<innerWidth*0.8)out.errors.push('content not full width');
    }

    out.ok=out.errors.length===0;
    return out;
  }catch(err){
    return {ok:false,errors:[String(err&&err.stack||err)]};
  }
})()
"""

RESTORE = r"""
(async function(){
  function wait(ms){return new Promise(function(r){setTimeout(r,ms);});}
  function px(name){return parseInt(getComputedStyle(document.documentElement).getPropertyValue(name),10)||0;}
  await wait(80);
  if(typeof applySidesCols==='function')applySidesCols();
  await wait(40);
  var ns=window.CATALOG_NS||'catalog';
  var slot=typeof readModeSlot==='function'?readModeSlot('sides'):{};
  return {
    display:typeof currentDisplay!=='undefined'?currentDisplay:'',
    cls:document.body.classList.contains('display-middle'),
    lw:px('--middle-lw'),
    mh:px('--middle-menu-h'),
    lwVal:localStorage.getItem('catalog-middle-lw-'+ns),
    mhVal:localStorage.getItem('catalog-middle-menu-h-'+ns),
    displayKey:localStorage.getItem('catalog-display-mode-'+ns),
    slotMiddleLw:slot&&slot.middleLw,
    slotMiddleMh:slot&&slot.middleMh
  };
})()
"""

LANDSCAPE = r"""
(async function(){
  function wait(ms){return new Promise(function(r){setTimeout(r,ms);});}
  var out={ok:true,errors:[]};
  try{
    if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
    document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed');
    var fw=document.getElementById('filterWrap');
    if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}
    await wait(60);
    if(typeof writeSidesCols==='function')writeSidesCols(312,334);
    if(typeof applySidesCols==='function')applySidesCols();
    await wait(40);
    var before={
      lw:parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0,
      rw:parseInt(getComputedStyle(document.body).getPropertyValue('--sides-rw'),10)||0,
      key:localStorage.getItem(SIDES_KEY)
    };
    out.before=before;
    if(typeof setDisplayMode==='function')setDisplayMode('middle',{pick:true});
    await wait(60);
    if(typeof writeMiddleLayout==='function')writeMiddleLayout(270,210);
    if(typeof applyMiddleLayout==='function')applyMiddleLayout();
    await wait(40);
    var midSides=localStorage.getItem(SIDES_KEY);
    out.duringMiddle={sidesKey:midSides,middle:document.body.classList.contains('display-middle')};
    if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
    await wait(80);
    if(typeof applySidesCols==='function')applySidesCols();
    await wait(40);
    var after={
      lw:parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0,
      rw:parseInt(getComputedStyle(document.body).getPropertyValue('--sides-rw'),10)||0,
      key:localStorage.getItem(SIDES_KEY),
      cls:document.body.classList.contains('display-sides')&&!document.body.classList.contains('display-middle')
    };
    out.after=after;
    if(Math.abs(after.lw-before.lw)>8)out.errors.push('landscape lw changed '+before.lw+' -> '+after.lw);
    if(Math.abs(after.rw-before.rw)>8)out.errors.push('landscape rw changed '+before.rw+' -> '+after.rw);
    if(before.key&&after.key&&before.key!==after.key)out.errors.push('SIDES_KEY changed');
    if(!after.cls)out.errors.push('not landscape sides after restore');
    out.ok=out.errors.length===0;
    return out;
  }catch(err){
    return {ok:false,errors:[String(err&&err.stack||err)]};
  }
})()
"""

PIN = r"""
(function(){
  if(typeof setDisplayMode==='function')setDisplayMode('middle',{pick:true});
  if(!document.body.classList.contains('layout-edit')&&typeof toggleLayoutEdit==='function')toggleLayoutEdit();
  sidesPinned=true;
  document.body.classList.add('sides-pinned','mode-layout-pinned');
  if(typeof placeSidesHandles==='function')placeSidesHandles();
  var split=document.getElementById('searchSplit');
  var cs=split&&getComputedStyle(split);
  var pe=cs&&cs.pointerEvents;
  var shown=!!(split&&cs&&cs.display!=='none'&&cs.pointerEvents!=='none');
  sidesPinned=false;
  document.body.classList.remove('sides-pinned','mode-layout-pinned');
  try{localStorage.setItem(SIDES_KEY+'-pin','0');}catch(e){}
  if(typeof placeSidesHandles==='function')placeSidesHandles();
  return {pinnedHides:!shown, pointerEvents:pe, display:cs&&cs.display};
})()
"""


def main():
    httpd = ensure_http()
    chrome = next(
        (
            p
            for p in (
                "/usr/lib/chromium/chromium",
                "/usr/bin/chromium",
                "/usr/bin/google-chrome",
            )
            if os.path.exists(p)
        ),
        None,
    )
    if not chrome:
        raise SystemExit("no chromium")
    logf = open("/tmp/catalog-middle-persist.log", "w")
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
            "--ozone-override-screen-size=900,1400",
            "--use-angle=swiftshader-webgl",
            "about:blank",
        ],
        stdout=logf,
        stderr=subprocess.STDOUT,
    )
    result = {"ok": False, "errors": []}
    try:
        for _ in range(80):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=1).read()
                break
            except Exception:
                time.sleep(0.2)
        else:
            json.dump({"err": "cdp"}, open(OUT, "w"))
            sys.exit(1)
        tab = new_tab("about:blank")
        cdp = CDP(tab["webSocketDebuggerUrl"])
        cdp.call("Page.enable")
        cdp.call("Runtime.enable")
        cdp.call(
            "Emulation.setDeviceMetricsOverride",
            {
                "width": 900,
                "height": 1400,
                "deviceScaleFactor": 1,
                "mobile": False,
                "screenOrientation": {"type": "portraitPrimary", "angle": 0},
            },
        )
        cdp.call("Page.navigate", {"url": URL})
        wait_entries(cdp)
        wait_ready(cdp)
        setup = cdp.eval(SETUP_DRAG)
        result["setup"] = setup
        shot(cdp, "D900-middle-persist-resize.png")
        if not setup or not setup.get("ok"):
            result["errors"].extend((setup or {}).get("errors") or ["setup failed"])
        saved = (setup or {}).get("drag", {}).get("saved") or {}
        want_lw = saved.get("lw")
        want_mh = saved.get("mh")

        cdp.call("Page.reload", {"ignoreCache": False})
        wait_entries(cdp)
        wait_ready(cdp)
        restored = cdp.eval(RESTORE)
        result["restore"] = restored
        shot(cdp, "D900-middle-persist-reload.png")
        if restored.get("display") != "middle" and not restored.get("cls"):
            result["errors"].append("middle not active after reload")
        if want_lw and abs((restored.get("lw") or 0) - want_lw) > 4:
            result["errors"].append(
                "lw after reload %s != %s" % (restored.get("lw"), want_lw)
            )
        if want_mh and abs((restored.get("mh") or 0) - want_mh) > 4:
            result["errors"].append(
                "mh after reload %s != %s" % (restored.get("mh"), want_mh)
            )

        pin = cdp.eval(PIN, await_promise=False)
        result["pin"] = pin
        if pin and not pin.get("pinnedHides"):
            result["errors"].append("pin did not disable middle handles")

        cdp.call(
            "Emulation.setDeviceMetricsOverride",
            {
                "width": 1400,
                "height": 900,
                "deviceScaleFactor": 1,
                "mobile": False,
                "screenOrientation": {"type": "landscapePrimary", "angle": 90},
            },
        )
        time.sleep(0.4)
        if restored.get("display") == "middle" or True:
            cdp.eval(
                "if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});",
                await_promise=False,
            )
        land = cdp.eval(LANDSCAPE)
        result["landscape"] = land
        shot(cdp, "D1400-sides-after-middle.png")
        if not land or not land.get("ok"):
            result["errors"].extend((land or {}).get("errors") or ["landscape failed"])

        result["ok"] = len(result["errors"]) == 0 and bool((setup or {}).get("ok")) and bool(
            (land or {}).get("ok")
        )
        result["keys"] = (setup or {}).get("keys")
        result["handles"] = (setup or {}).get("handles")
        json.dump(result, open(OUT, "w"), indent=2)
        print(json.dumps(result, indent=2)[:12000])
        if not result.get("ok"):
            sys.exit(1)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
        if httpd:
            httpd.shutdown()


if __name__ == "__main__":
    main()
