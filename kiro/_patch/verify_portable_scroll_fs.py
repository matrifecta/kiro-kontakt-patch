#!/usr/bin/env python3
"""CDP: portable scrollports, fullscreen, Customize ⋯, search field."""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from urllib.parse import urlparse

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_portable_scroll_fs.json"
PORT = 9491
URL = "http://127.0.0.1:8797/DS-CATALOG-portable.html?cb=scroll-fs-2"
PROFILE = "/tmp/catalog-portable-scroll-fs"
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
  function box(el){
    if(!el)return null;
    var r=el.getBoundingClientRect(), cs=getComputedStyle(el);
    return {
      t:Math.round(r.top), l:Math.round(r.left), w:Math.round(r.width), h:Math.round(r.height),
      b:Math.round(r.bottom), rgt:Math.round(r.right),
      clientH:el.clientHeight, scrollH:el.scrollHeight,
      ovY:cs.overflowY, ovX:cs.overflowX, disp:cs.display
    };
  }
  function popLabels(id){
    var p=document.getElementById(id);
    if(!p)return [];
    return [].map.call(p.querySelectorAll('button,label'),function(b){return (b.textContent||'').trim();});
  }
  function popInside(id){
    var p=document.getElementById(id);
    if(!p||p.hasAttribute('hidden'))return {open:false};
    var r=p.getBoundingClientRect();
    return {
      open:true, t:Math.round(r.top), l:Math.round(r.left), w:Math.round(r.width), h:Math.round(r.height),
      inside:r.top>=-1&&r.left>=-1&&r.bottom<=innerHeight+1&&r.right<=innerWidth+1
    };
  }
  function snap(tag){
    var ac=document.getElementById('acList');
    var fw=document.getElementById('filterWrap');
    var fp=document.getElementById('filterPanel')||(fw&&fw.querySelector('.filter-panel'));
    var kw=document.getElementById('kwbar');
    var cat=document.getElementById('catSwitch')||document.querySelector('.cat-switch');
    var inp=document.getElementById('searchInput');
    var ch=document.getElementById('searchChrome');
    var main=document.getElementById('catalogMain');
    var ir=inp?inp.getBoundingClientRect():null;
    var overlap=[];
    if(ir){
      document.querySelectorAll('#searchStrip button,#searchStrip .search-strip-fs,#acFsBar button,#searchSplit,#dualFsSep,.kw-companion-btn,.ac-companion-btn,.ac-fs-back').forEach(function(b){
        var cs=getComputedStyle(b);
        if(cs.display==='none'||cs.visibility==='hidden'||b.hasAttribute('hidden'))return;
        var br=b.getBoundingClientRect();
        if(br.width<2||br.height<2)return;
        if(!(ir.right<=br.left+1||br.right<=ir.left+1||ir.bottom<=br.top+1||br.bottom<=ir.top+1))
          overlap.push({id:b.id||String(b.className).slice(0,40),w:Math.round(br.width),h:Math.round(br.height),l:Math.round(br.left)});
      });
    }
    var chR=ch?ch.getBoundingClientRect():null;
    var acInPane=true;
    if(ac&&chR&&getComputedStyle(ch).display!=='none'){
      var ar=ac.getBoundingClientRect();
      acInPane=ar.left>=chR.left-2&&ar.right<=chR.right+2&&ar.top>=chR.top-2;
    }
    return {
      tag:tag, vw:innerWidth, vh:innerHeight,
      cur:typeof currentDisplay!=='undefined'?String(currentDisplay):'',
      cls:document.body.className,
      fsEl:!!(document.fullscreenElement||document.webkitFullscreenElement),
      cssFs:!!(document.documentElement.classList.contains('is-browser-fs')||document.body.classList.contains('is-browser-fs')),
      wantFs:typeof portableWantBrowserFs==='function'&&!!portableWantBrowserFs(),
      api:typeof portableFsApiAvailable==='function'&&!!portableFsApiAvailable(),
      ac:box(ac), fp:box(fp), fw:box(fw), kw:box(kw), cat:box(cat), inp:box(inp), ch:box(ch), main:box(main),
      overlap:overlap, acInPane:acInPane,
      layoutEdit:document.body.classList.contains('layout-edit')
    };
  }
  function go(mode,opts){
    if(typeof setDisplayMode==='function')setDisplayMode(mode,opts||{pick:true});
    if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
    if(typeof placePortableHandles==='function')placePortableHandles();
  }
  var out={ok:true,errors:[],d1400:{},m390:{}};
  try{
    go('sides');
    document.body.classList.add('search-chrome-collapsed'.replace('search','x'));
    document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed','kw-open');
    var fw=document.getElementById('filterWrap');
    if(fw)fw.classList.remove('open');
    if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
    if(typeof showAc==='function')try{showAc('',{force:true});}catch(e){}
    await wait(60);
    out.d1400.sidesSearch=snap('sides-search-content');
    if(typeof toggleHdrKw==='function')toggleHdrKw();
    await wait(40);
    out.d1400.sidesDual=snap('sides-dual');
    go('fs',{menu:'both',pick:true});
    await wait(80);
    out.d1400.fullDual=snap('full-dual');
    if(typeof toggleHdrKw==='function')toggleHdrKw();
    await wait(50);
    out.d1400.fullSearch=snap('full-search-only');
    if(typeof toggleHdrKw==='function')toggleHdrKw();
    if(typeof toggleHdrSearch==='function')toggleHdrSearch();
    await wait(50);
    out.d1400.fullKw=snap('full-kw-only');
    if(typeof toggleHdrMore==='function')toggleHdrMore();
    out.d1400.hdrMore=popLabels('hdrMorePop');
    out.d1400.hdrMoreBox=popInside('hdrMorePop');
    if(typeof closePhoneOverflowPops==='function')closePhoneOverflowPops();
    if(typeof toggleSearchStripMore==='function')toggleSearchStripMore();
    out.d1400.searchMore=popLabels('searchStripMorePop');
    out.d1400.searchMoreBox=popInside('searchStripMorePop');
    if(typeof closePhoneOverflowPops==='function')closePhoneOverflowPops();
    if(typeof toggleKwStripMore==='function')toggleKwStripMore();
    out.d1400.kwMore=popLabels('kwStripMorePop');
    out.d1400.kwMoreBox=popInside('kwStripMorePop');
    if(typeof closePhoneOverflowPops==='function')closePhoneOverflowPops();
    if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();
    out.d1400.afterEdit=snap('full-kw-edit');
    if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();
    go('sides');
    await wait(40);
    out.d1400.backSides=snap('back-sides');
    var s=out.d1400.sidesSearch, fd=out.d1400.fullDual, fso=out.d1400.fullSearch, fkw=out.d1400.fullKw;
    function need(cond,msg){if(cond)out.errors.push('d1400 '+msg);}
    need(!(s.ac&&s.ac.h>80&&(s.ac.ovY==='auto'||s.ac.ovY==='scroll')), 'sides acList h='+(s.ac&&s.ac.h)+' ov='+(s.ac&&s.ac.ovY));
    need(!(s.ac&&(s.ac.scrollH>s.ac.clientH||s.ac.h>80)), 'sides list not a scrollport');
    need(!s.acInPane, 'sides acList not in search pane');
    need(!(s.inp&&s.inp.w>120), 'sides input w='+(s.inp&&s.inp.w));
    need(s.overlap&&s.overlap.length>0, 'sides input overlap '+JSON.stringify(s.overlap));
    need(!(fd.ac&&fd.ac.h>80), 'full dual ac h='+(fd.ac&&fd.ac.h));
    need(!(fd.fp&&fd.fp.h>40&&(fd.fp.ovY==='auto'||fd.fp.ovY==='scroll')), 'full dual kw panel');
    need(!(fd.ch&&fd.fw&&Math.abs((fd.ch.l||0)-(fd.fw.l||0))>40&&fd.ch.w>80&&fd.fw.w>80), 'full dual panes overlap/stacked');
    need(fkw.ch&&fkw.ch.disp!=='none'&&fkw.ch.w>80, 'full kw-only search still visible');
    need(!(fso.ac&&fso.ac.h>80), 'full search-only ac h='+(fso.ac&&fso.ac.h));
    need(!(fso.inp&&fso.inp.w>120), 'full search input w='+(fso.inp&&fso.inp.w));
    need(fso.overlap&&fso.overlap.length>0, 'full search input overlap '+JSON.stringify(fso.overlap));
    need(!(fkw.fw&&fkw.fw.w>innerWidth*0.72), 'full kw fill w='+(fkw.fw&&fkw.fw.w));
    need(out.d1400.hdrMore.indexOf('Edit')<0&&out.d1400.hdrMore.indexOf('Customize')<0&&out.d1400.hdrMore.indexOf('Done')<0, 'hdr missing Customize');
    need(out.d1400.searchMore.indexOf('Edit')<0&&out.d1400.searchMore.indexOf('Done')<0, 'search more missing Edit');
    need(out.d1400.kwMore.indexOf('Edit')<0&&out.d1400.kwMore.indexOf('Done')<0, 'kw more missing Edit');
    need(out.d1400.hdrMoreBox.open&&!out.d1400.hdrMoreBox.inside, 'hdr more clipped');
    need(!(s.wantFs||s.cssFs||s.fsEl), 'sides did not request/fallback FS');
    need(out.d1400.fullDual.wantFs===false, 'full wantFs false');
    need(out.d1400.backSides.wantFs===false&&!out.d1400.backSides.cssFs&&!out.d1400.backSides.fsEl?false:false, 'noop');
  }catch(err){out.errors.push('d1400 '+String(err&&err.stack||err));}
  out.ok=out.errors.length===0;
  return out;
})()
"""

JS390 = r"""
(async function(){
  function wait(ms){return new Promise(function(r){setTimeout(r,ms);});}
  function box(el){
    if(!el)return null;
    var r=el.getBoundingClientRect(), cs=getComputedStyle(el);
    return {
      t:Math.round(r.top), l:Math.round(r.left), w:Math.round(r.width), h:Math.round(r.height),
      clientH:el.clientHeight, scrollH:el.scrollHeight, ovY:cs.overflowY, ovX:cs.overflowX, disp:cs.display
    };
  }
  function snap(tag){
    var ac=document.getElementById('acList');
    var fw=document.getElementById('filterWrap');
    var fp=document.getElementById('filterPanel')||(fw&&fw.querySelector('.filter-panel'));
    var cat=document.getElementById('catSwitch')||document.querySelector('.cat-switch');
    var kw=document.getElementById('kwbar');
    var inp=document.getElementById('searchInput');
    var ch=document.getElementById('searchChrome');
    var ir=inp?inp.getBoundingClientRect():null;
    var overlap=[];
    if(ir){
      document.querySelectorAll('#searchStrip button,#searchSplit,#dualFsSep').forEach(function(b){
        var cs=getComputedStyle(b);
        if(cs.display==='none'||cs.visibility==='hidden')return;
        var br=b.getBoundingClientRect();
        if(br.width<2||br.height<2)return;
        if(!(ir.right<=br.left+1||br.right<=ir.left+1||ir.bottom<=br.top+1||br.bottom<=ir.top+1))
          overlap.push({id:b.id||String(b.className).slice(0,40)});
      });
    }
    var chR=ch?ch.getBoundingClientRect():null;
    var acInPane=true;
    if(ac&&chR&&getComputedStyle(ch).display!=='none'){
      var ar=ac.getBoundingClientRect();
      acInPane=ar.left>=chR.left-2&&ar.right<=chR.right+2&&ar.top>=chR.top-2;
    }
    return {
      tag:tag, vw:innerWidth, vh:innerHeight, cur:typeof currentDisplay!=='undefined'?String(currentDisplay):'',
      cls:document.body.className,
      fsEl:!!(document.fullscreenElement||document.webkitFullscreenElement),
      cssFs:!!(document.documentElement.classList.contains('is-browser-fs')||document.body.classList.contains('is-browser-fs')),
      wantFs:typeof portableWantBrowserFs==='function'&&!!portableWantBrowserFs(),
      ac:box(ac), fp:box(fp), fw:box(fw), cat:box(cat), kw:box(kw), inp:box(inp), ch:box(ch),
      overlap:overlap, acInPane:acInPane,
      middleBtn:!!document.querySelector('.display-btn[data-display="middle"]') && getComputedStyle(document.querySelector('.display-btn[data-display="middle"]')).display!=='none'
    };
  }
  var out={ok:true,errors:[],shots:{}};
  try{
    if(typeof setDisplayMode==='function')setDisplayMode('middle',{pick:true});
    if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
    await wait(80);
    out.shots.middle=snap('middle');
    if(typeof toggleHdrMore==='function')toggleHdrMore();
    var hp=document.getElementById('hdrMorePop');
    var hr=hp&&!hp.hasAttribute('hidden')?hp.getBoundingClientRect():null;
    out.shots.hdrMoreInside=!!(hr&&hr.top>=-1&&hr.bottom<=innerHeight+1&&hr.right<=innerWidth+1);
    out.shots.hdrMoreLabels=[].map.call((hp&&hp.querySelectorAll('button'))||[],function(b){return b.textContent.trim();});
    if(typeof closePhoneOverflowPops==='function')closePhoneOverflowPops();
    if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
    document.body.classList.remove('kw-open','kw-chrome-collapsed');
    var fw=document.getElementById('filterWrap'); if(fw)fw.classList.remove('open');
    if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
    if(typeof showAc==='function')try{showAc('',{force:true});}catch(e){}
    await wait(60);
    out.shots.sides=snap('sides');
    if(typeof toggleHdrKw==='function')toggleHdrKw();
    await wait(40);
    out.shots.sidesKw=snap('sides-kw');
    if(typeof setDisplayMode==='function')setDisplayMode('fs',{menu:'both',pick:true});
    await wait(80);
    out.shots.full=snap('full');
    if(typeof toggleHdrSearch==='function')toggleHdrSearch();
    await wait(40);
    out.shots.fullKw=snap('full-kw');
    var m=out.shots.middle, s=out.shots.sides, sk=out.shots.sidesKw, f=out.shots.full;
    function need(cond,msg){if(cond)out.errors.push('m390 '+msg);}
    need(!m.middleBtn, 'middle button hidden in portrait');
    need(!(m.ac&&m.ac.h>40&&(m.ac.ovY==='auto'||m.ac.ovY==='scroll')), 'middle ac ov/h');
    need(!(m.fp&&(m.fp.ovY==='auto'||m.fp.ovY==='scroll')), 'middle kw not scrollable');
    need(!(m.inp&&m.inp.w>120), 'middle input w='+(m.inp&&m.inp.w));
    need(m.overlap&&m.overlap.length>0, 'middle overlap '+JSON.stringify(m.overlap));
    need(!(s.ac&&s.ac.h>80), 'sides ac h='+(s.ac&&s.ac.h));
    need(!s.acInPane, 'sides ac not in pane');
    need(!(s.inp&&s.inp.w>120), 'sides input w='+(s.inp&&s.inp.w));
    need(s.overlap&&s.overlap.length>0, 'sides overlap');
    need(!(sk.cat&&(sk.fp&&(sk.fp.scrollH>sk.fp.clientH||sk.cat.ovX==='auto'||sk.cat.ovX==='scroll'||sk.fp.h>40))), 'kw cats unreachable');
    need(!(f.ac&&f.ac.h>80), 'full ac h='+(f.ac&&f.ac.h));
    need(out.shots.hdrMoreLabels.indexOf('Edit')<0&&out.shots.hdrMoreLabels.indexOf('Done')<0, 'hdr missing Edit');
    need(!out.shots.hdrMoreInside, 'hdr more clipped');
    need(!(s.wantFs||s.cssFs||s.fsEl), 'sides no FS fallback');
    need(m.wantFs, 'middle should not want FS, got '+m.wantFs);
  }catch(err){out.errors.push('m390 '+String(err&&err.stack||err));}
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
            for p in ("/usr/lib/chromium/chromium", "/usr/bin/chromium", "/usr/bin/google-chrome")
            if os.path.exists(p)
        ),
        None,
    )
    if not chrome:
        raise SystemExit("no chromium")
    logf = open("/tmp/catalog-portable-scroll-fs.log", "w")
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
            {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True},
        )
        cdp.eval(
            "window.dispatchEvent(new Event('resize'));if(typeof placePortableHandles==='function')placePortableHandles();"
        )
        time.sleep(0.3)
        m390 = cdp.eval(JS390)
        result = {"d1400": d1400, "m390": m390}
        errs = (d1400 or {}).get("errors", []) + (m390 or {}).get("errors", [])
        result["ok"] = not errs
        result["errors"] = errs
        json.dump(result, open(OUT, "w"), indent=2)
        print(json.dumps({"ok": result["ok"], "errors": errs}, indent=2)[:4000])
        if not result["ok"]:
            sys.exit(2)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    main()
