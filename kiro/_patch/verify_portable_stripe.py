#!/usr/bin/env python3
"""CDP measures portable stripe, one-menu fill, History, no Pick/glass."""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from urllib.parse import urlparse

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_portable_stripe.json"
PORT = 9488
URL = "http://127.0.0.1:8797/DS-CATALOG-portable.html?cb=stripe-verify"
PROFILE = "/tmp/catalog-portable-stripe"
os.makedirs(PROFILE, exist_ok=True)


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


JS = r"""
(async function(){
  function wait(ms){return new Promise(function(r){setTimeout(r,ms);});}
  function rb(el){
    if(!el)return null;
    var r=el.getBoundingClientRect(),cs=getComputedStyle(el);
    return {l:Math.round(r.left),t:Math.round(r.top),w:Math.round(r.width),h:Math.round(r.height),disp:cs.display,vis:cs.visibility};
  }
  function visBtn(sel,text){
    var n=0;
    document.querySelectorAll(sel).forEach(function(b){
      var cs=getComputedStyle(b);
      if(cs.display==='none'||cs.visibility==='hidden'||b.offsetParent===null)return;
      if(!text||(b.textContent||'').trim()===text)n++;
    });
    return n;
  }
  function snap(tag){
    var split=document.getElementById('searchSplit');
    var sep=document.getElementById('dualFsSep');
    var ch=document.getElementById('searchChrome');
    var fw=document.getElementById('filterWrap');
    var main=document.getElementById('catalogMain');
    var hist=document.getElementById('searchHistory');
    var ix=document.getElementById('catalogIndex');
    var path=document.querySelector('.entry .path');
    return {
      tag:tag, vw:innerWidth, vh:innerHeight,
      cls:document.body.className,
      search:rb(ch), kw:rb(fw), main:rb(main),
      split:rb(split), sep:rb(sep),
      splitOn:!!(split&&split.classList.contains('port-stripe-v')||(split&&split.classList.contains('port-stripe-h'))),
      sepOn:!!(sep&&(sep.classList.contains('port-stripe-v')||sep.classList.contains('port-stripe-h'))),
      hist:hist?hist.textContent.trim():'',
      histAria:hist?hist.getAttribute('aria-label'):'',
      pickVis:visBtn('.mode-btn','Pick')+visBtn('.fs-mode-nav .mode-btn','Pick'),
      companion:visBtn('.ac-companion-btn')+visBtn('#acCompanionBtn'),
      ixCollapsed:!!(ix&&ix.classList.contains('is-collapsed')),
      pathCollapsed:!!(path&&path.classList.contains('is-collapsed')),
      hdrSK:[].map.call(document.querySelectorAll('#hdrMenuBtns .hdr-menu-btn'),function(b){return b.id;})
    };
  }
  function dragSep(dx){
    var sep=document.getElementById('dualFsSep');
    var split=document.getElementById('searchSplit');
    var el=(sep&&sep.classList.contains('port-stripe-v'))?sep:((split&&split.classList.contains('port-stripe-v'))?split:sep||split);
    if(!el)return {err:'no stripe'};
    var r=el.getBoundingClientRect();
    var x0=r.left+r.width/2, y0=r.top+Math.min(40,r.height/2);
    el.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,cancelable:true,clientX:x0,clientY:y0,pointerId:7,pointerType:'mouse',button:0}));
    document.dispatchEvent(new PointerEvent('pointermove',{bubbles:true,cancelable:true,clientX:x0+dx,clientY:y0,pointerId:7,pointerType:'mouse'}));
    el.dispatchEvent(new PointerEvent('pointermove',{bubbles:true,cancelable:true,clientX:x0+dx,clientY:y0,pointerId:7,pointerType:'mouse'}));
    document.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,cancelable:true,clientX:x0+dx,clientY:y0,pointerId:7,pointerType:'mouse'}));
    el.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,cancelable:true,clientX:x0+dx,clientY:y0,pointerId:7,pointerType:'mouse'}));
    if(typeof placePortableHandles==='function')placePortableHandles();
    return {ok:true,x0:Math.round(x0),dx:dx};
  }
  var out={ok:true,errors:[],d1400:{},m390:{}};
  try{
    if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
    document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed');
    var fw=document.getElementById('filterWrap');
    if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}
    if(typeof placePortableHandles==='function')placePortableHandles();
    await wait(80);
    out.d1400.dual=snap('sides-dual');
    var beforeL=out.d1400.dual.kw&&out.d1400.dual.kw.l;
    var beforeW=out.d1400.dual.search&&out.d1400.dual.search.w;
    out.d1400.drag=dragSep(80);
    await wait(40);
    out.d1400.afterDrag=snap('sides-dual-drag');
    out.d1400.paneLeftBefore=beforeL;
    out.d1400.paneLeftAfter=out.d1400.afterDrag.kw&&out.d1400.afterDrag.kw.l;
    out.d1400.searchWBefore=beforeW;
    out.d1400.searchWAfter=out.d1400.afterDrag.search&&out.d1400.afterDrag.search.w;
    if(typeof toggleHdrKw==='function')toggleHdrKw();
    if(typeof placePortableHandles==='function')placePortableHandles();
    await wait(40);
    out.d1400.oneSearch=snap('sides-search-only');
    if(typeof toggleHdrKw==='function')toggleHdrKw();
    if(typeof toggleHdrSearch==='function')toggleHdrSearch();
    if(typeof placePortableHandles==='function')placePortableHandles();
    await wait(40);
    out.d1400.oneKw=snap('sides-kw-only');
    if(typeof setDisplayMode==='function')setDisplayMode('fs');
    await wait(80);
    if(typeof placePortableHandles==='function')placePortableHandles();
    out.d1400.fullDual=snap('full-dual');
    if(typeof toggleHdrSearch==='function')toggleHdrSearch();
    await wait(60);
    if(typeof placePortableHandles==='function')placePortableHandles();
    out.d1400.fullKw=snap('full-kw-only');
    if(typeof toggleHdrSearch==='function')toggleHdrSearch();
    if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();
    await wait(40);
    out.d1400.flip=snap('full-flip');
    out.d1400.more={};
    if(typeof toggleSearchStripMore==='function')toggleSearchStripMore();
    var pop=document.getElementById('searchStripMorePop');
    out.d1400.more.search=[].map.call((pop&&pop.querySelectorAll('button'))||[],function(b){return b.textContent;});
    if(typeof toggleSearchStripMore==='function')toggleSearchStripMore();
    if(typeof toggleHdrMore==='function')toggleHdrMore();
    var hp=document.getElementById('hdrMorePop');
    out.d1400.more.hdr=[].map.call((hp&&hp.querySelectorAll('button,label'))||[],function(b){return b.textContent;});
    if(typeof closePhoneOverflowPops==='function')closePhoneOverflowPops();
    [
      ['dual stripe', !out.d1400.dual.sepOn && !out.d1400.dual.splitOn, 'landscape dual missing stripe'],
      ['drag moved', !(Math.abs((out.d1400.searchWAfter||0)-(out.d1400.searchWBefore||0))>=8 || Math.abs((out.d1400.paneLeftAfter||0)-(out.d1400.paneLeftBefore||0))>=8), 'drag did not change pane'],
      ['one search fill', out.d1400.oneSearch.search && out.d1400.oneSearch.search.w<innerWidth*0.28, 'search-only too narrow'],
      ['full kw fill', out.d1400.fullKw.kw && out.d1400.fullKw.kw.w<innerWidth*0.72, 'full kw did not fill'],
      ['history', out.d1400.dual.hist!=='History' && out.d1400.dual.hist!=='H', 'history label '+out.d1400.dual.hist],
      ['pick gone', out.d1400.dual.pickVis>0, 'Pick visible'],
      ['glass gone', out.d1400.dual.companion>0, 'companion visible'],
      ['no pick more', out.d1400.more.search.indexOf('Pick')>=0, 'Pick in search more']
    ].forEach(function(row){
      if(row[1])out.errors.push(row[0]+': '+row[2]);
    });
  }catch(err){out.errors.push(String(err&&err.stack||err));}
  out.ok=out.errors.length===0;
  return out;
})()
"""


def main():
    urllib.request.urlopen("http://127.0.0.1:8797/DS-CATALOG-portable.html", timeout=2).read(64)
    subprocess.run(["pkill", "-f", f"remote-debugging-port={PORT}"], check=False)
    time.sleep(0.25)
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
    logf = open("/tmp/catalog-portable-stripe.log", "w")
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
            "--ozone-override-screen-size=1400,900",
            "--use-angle=swiftshader-webgl",
            "about:blank",
        ],
        stdout=logf,
        stderr=subprocess.STDOUT,
    )
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
            {"width": 1400, "height": 900, "deviceScaleFactor": 1, "mobile": False},
        )
        cdp.call("Page.navigate", {"url": URL})
        for _ in range(80):
            try:
                n = cdp.eval("document.querySelectorAll('.entry').length", await_promise=False)
            except Exception:
                n = 0
            if n and n > 20:
                break
            time.sleep(0.25)
        d1400 = cdp.eval(JS)
        cdp.call(
            "Emulation.setDeviceMetricsOverride",
            {
                "width": 390,
                "height": 844,
                "deviceScaleFactor": 2,
                "mobile": True,
            },
        )
        cdp.eval(
            "window.dispatchEvent(new Event('resize'));if(typeof placePortableHandles==='function')placePortableHandles();"
        )
        time.sleep(0.3)
        m390 = cdp.eval(
            r"""
(async function(){
  function wait(ms){return new Promise(function(r){setTimeout(r,ms);});}
  function rb(el){if(!el)return null;var r=el.getBoundingClientRect(),cs=getComputedStyle(el);return {l:Math.round(r.left),t:Math.round(r.top),w:Math.round(r.width),h:Math.round(r.height),disp:cs.display};}
  if(typeof setDisplayMode==='function')setDisplayMode('middle',{pick:true});
  document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed');
  var fw=document.getElementById('filterWrap');
  if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}
  if(typeof placePortableHandles==='function')placePortableHandles();
  await wait(80);
  var split=document.getElementById('searchSplit'),sep=document.getElementById('dualFsSep');
  var ch=document.getElementById('searchChrome');
  if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
  document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed');
  if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}
  if(typeof placePortableHandles==='function')placePortableHandles();
  await wait(80);
  var sides={
    vw:innerWidth,vh:innerHeight,cls:document.body.className,
    search:rb(document.getElementById('searchChrome')),
    kw:rb(document.getElementById('filterWrap')),
    main:rb(document.getElementById('catalogMain')),
    split:rb(document.getElementById('searchSplit')),
    sep:rb(document.getElementById('dualFsSep')),
    splitOn:!!(document.getElementById('searchSplit')&&(document.getElementById('searchSplit').classList.contains('port-stripe-h')||document.getElementById('searchSplit').classList.contains('port-stripe-v'))),
    sepOn:!!(document.getElementById('dualFsSep')&&(document.getElementById('dualFsSep').classList.contains('port-stripe-h')||document.getElementById('dualFsSep').classList.contains('port-stripe-v'))),
    hist:(document.getElementById('searchHistory')||{}).textContent||'',
    hdrSK:[].map.call(document.querySelectorAll('#hdrMenuBtns .hdr-menu-btn'),function(b){return b.id;})
  };
  if(typeof setDisplayMode==='function')setDisplayMode('fs');
  await wait(80);
  if(typeof toggleHdrSearch==='function')toggleHdrSearch();
  await wait(50);
  var fullKw={
    cls:document.body.className,
    search:rb(document.getElementById('searchChrome')),
    kw:rb(document.getElementById('filterWrap')),
    fill:!!(document.getElementById('filterWrap')&&document.getElementById('filterWrap').getBoundingClientRect().width>innerWidth*0.85)
  };
  return {middle:{splitOn:!!(split&&(split.classList.contains('port-stripe-h')||split.classList.contains('port-stripe-v'))),sepOn:!!(sep&&(sep.classList.contains('port-stripe-v')||sep.classList.contains('port-stripe-h'))),search:rb(ch)},sides:sides,fullKw:fullKw};
})()
"""
        )
        result = d1400 or {}
        result["m390"] = m390
        if m390 and m390.get("fullKw") and not m390["fullKw"].get("fill"):
            result.setdefault("errors", []).append("390 full kw did not fill")
            result["ok"] = False
        json.dump(result, open(OUT, "w"), indent=2)
        print(json.dumps(result, indent=2))
        if not result.get("ok"):
            sys.exit(1)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    main()
