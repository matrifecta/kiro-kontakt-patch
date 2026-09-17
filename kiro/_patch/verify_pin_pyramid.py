#!/usr/bin/env python3
"""Verify pin pyramid (9), History chrome, Middle Save clearance."""
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

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_pin_pyramid.json"
SHOTS = "/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots"
PORT = 9478
HTTP_PORT = 8794
ROOT = "/home/phnx/kiro-kontakt-patch/public/catalogs"
URL = "http://127.0.0.1:8794/DS-CATALOG.html?v=pinpyr3"
PROFILE = "/tmp/catalog-pin-pyramid"
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
    raise SystemExit("http 8794 failed")


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

    def shot(self, name):
        data = self.call("Page.captureScreenshot", {"format": "png"}).get("data")
        if data:
            open(os.path.join(SHOTS, name), "wb").write(base64.b64decode(data))


JS_WIDE = r"""
(async function(){
  function wait(ms){return new Promise(function(r){setTimeout(r,ms);});}
  function box(el){
    if(!el)return null;
    var r=el.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),l:Math.round(r.left),r:Math.round(r.right),t:Math.round(r.top),b:Math.round(r.bottom),cx:Math.round(r.x+r.width/2)};
  }
  function overlaps(a,b){
    if(!a||!b)return false;
    return !(a.r<b.l||a.l>b.r||a.b<b.t||a.t>b.b);
  }
  function entries(){
    return [].slice.call(document.querySelectorAll('.entry')).filter(function(e){return e.id;});
  }
  function seed(n){
    var list=entries();
    cardMinDockItems=[];
    for(var i=0;i<n;i++){
      var el=list[i];
      cardMinDockItems.push({id:el.id,mode:'preview',kind:'preview',name:'P'+(i+1)});
    }
    cardMinRender();
  }
  function rowCounts(){
    return [].slice.call(document.querySelectorAll('#cardMinDock .card-min-row')).map(function(row){
      return row.querySelectorAll('.card-min-pill').length;
    });
  }
  function geom(){
    var dock=document.getElementById('cardMinDock');
    var stack=dock&&dock.querySelector('.card-min-stack');
    var rows=[].slice.call(document.querySelectorAll('#cardMinDock .card-min-row'));
    var pills=[].slice.call(document.querySelectorAll('#cardMinDock .card-min-pill'));
    var vw=window.innerWidth, vh=window.innerHeight;
    var overflow=pills.filter(function(p){
      var r=p.getBoundingClientRect();
      return r.left<-1||r.right>vw+1||r.bottom>vh+1||r.top<0;
    }).length;
    var rowTops=rows.map(function(row){return Math.round(row.getBoundingClientRect().top);});
    return {
      n:pills.length,
      counts:rowCounts(),
      per:dock&&dock.getAttribute('data-card-min-per'),
      maxPer:typeof cardMinMaxPerRow==='function'?cardMinMaxPerRow():null,
      dock:box(dock),
      stack:box(stack),
      rows:rows.map(box),
      rowTops:rowTops,
      pills:pills.map(box),
      overflow:overflow,
      on:!!(dock&&dock.classList.contains('is-on')),
      vw:vw,vh:vh
    };
  }
  function styleOf(sel){
    var el=document.querySelector(sel);
    if(!el)return null;
    var cs=getComputedStyle(el);
    var r=el.getBoundingClientRect();
    return {
      display:cs.display,
      bg:cs.backgroundColor,
      h:Math.round(r.height),
      radius:cs.borderRadius,
      fs:cs.fontSize,
      ff:cs.fontFamily,
      fw:cs.fontWeight,
      color:cs.color,
      border:cs.borderTopWidth+' '+cs.borderTopStyle
    };
  }
  var out={ok:true, errors:[], steps:{}};
  try{
    if(typeof setDisplayMode==='function')setDisplayMode('sides');
    document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed','search-extras-collapsed','hl-open','chosen-preview-open');
    await wait(120);
    out.steps.max={CARD_MIN_MAX:CARD_MIN_MAX, PIN_SESS_MAX:typeof PIN_SESS_MAX==='number'?PIN_SESS_MAX:null};
    if(CARD_MIN_MAX!==9)out.errors.push('CARD_MIN_MAX '+CARD_MIN_MAX+' expected 9');
    if(typeof PIN_SESS_MAX==='number'&&PIN_SESS_MAX<12)out.errors.push('PIN_SESS_MAX lowered to '+PIN_SESS_MAX);

    var expectFor={1:[1],2:[2],3:[3],4:[3,1],5:[3,2],6:[3,3],7:[5,2],8:[5,3],9:[5,4]};
    var algo={
      w9:cardMinPyramidCounts(9,5),
      w4:cardMinPyramidCounts(9,4),
      w3:cardMinPyramidCounts(9,3),
      n1:cardMinPyramidCounts(1,5),
      n5:cardMinPyramidCounts(5,5),
      n6:cardMinPyramidCounts(6,5),
      n7:cardMinPyramidCounts(7,5)
    };
    out.steps.algo=algo;
    if(JSON.stringify(algo.w9)!=='[5,4]')out.errors.push('algo 9/5 '+JSON.stringify(algo.w9));
    if(JSON.stringify(algo.w3)!=='[3,3,3]')out.errors.push('algo 9/3 '+JSON.stringify(algo.w3));
    if(JSON.stringify(algo.n1)!=='[1]')out.errors.push('algo 1/5 '+JSON.stringify(algo.n1));
    if(JSON.stringify(algo.n5)!=='[3,2]')out.errors.push('algo 5/5 (n<7 must not be 5-wide) '+JSON.stringify(algo.n5));
    if(JSON.stringify(algo.n6)!=='[3,3]')out.errors.push('algo 6/5 '+JSON.stringify(algo.n6));
    if(JSON.stringify(algo.n7)!=='[5,2]')out.errors.push('algo 7/5 '+JSON.stringify(algo.n7));
    var four=JSON.stringify(algo.w4);
    if(four!=='[4,3,2]'&&four!=='[4,4,1]')out.errors.push('algo 9/4 '+four);

    var wide=[];
    for(var n=1;n<=9;n++){
      seed(n);
      await wait(40);
      var g=geom();
      wide.push(g);
      if(g.n!==n)out.errors.push('wide n='+n+' pills '+g.n);
      var exp=expectFor[n];
      if(JSON.stringify(g.counts)!==JSON.stringify(exp))out.errors.push('wide n='+n+' rows '+JSON.stringify(g.counts)+' expected '+JSON.stringify(exp));
      if(n<7 && g.counts.some(function(c){return c>=5;}))out.errors.push('wide n='+n+' used 5-wide row '+JSON.stringify(g.counts));
      if(g.overflow)out.errors.push('wide n='+n+' overflow '+g.overflow);
      if(g.stack&&g.vw){
        var mid=g.vw/2;
        if(Math.abs(g.stack.cx-mid)>80)out.errors.push('wide n='+n+' stack cx '+g.stack.cx+' vw/2 '+mid);
      }
      if(g.stack&&g.vh&&(g.vh-g.stack.b)>64)out.errors.push('wide n='+n+' stack not at bottom gap '+(g.vh-g.stack.b));
    }
    out.steps.wide=wide.map(function(g){return {n:g.n,counts:g.counts,per:g.per,overflow:g.overflow,stack:g.stack,rowTops:g.rowTops};});
    var g9=wide[8];
    if(g9&&g9.rowTops&&g9.rowTops.length===2&&g9.rowTops[0]<g9.rowTops[1])out.errors.push('wide n=9 bottom row not visually lower '+JSON.stringify(g9.rowTops));

    seed(9);
    await wait(30);
    var first=cardMinDockItems[0]&&cardMinDockItems[0].id;
    var tenth=entries()[9];
    if(tenth){
      openChosenPreview(tenth);
      await wait(40);
      minimizeExpandedCard(tenth);
      await wait(40);
    }
    document.body.classList.remove('chosen-preview-open','hl-open');
    out.steps.fifo={
      n:cardMinDockItems.length,
      stillFirst:cardMinDockItems.some(function(x){return x.id===first;}),
      last:cardMinDockItems[cardMinDockItems.length-1]&&cardMinDockItems[cardMinDockItems.length-1].id,
      tenth:tenth&&tenth.id
    };
    if(cardMinDockItems.length!==9)out.errors.push('fifo n '+cardMinDockItems.length);
    if(out.steps.fifo.stillFirst)out.errors.push('fifo did not evict first pin');
    if(tenth&&out.steps.fifo.last!==tenth.id)out.errors.push('fifo last not tenth');

    seed(5);
    await wait(40);
    if(typeof savePinSession==='function')savePinSession('pyr-verify');
    var sid=(pinSessionStore.sessions||[]).filter(function(s){return s&&s.name==='pyr-verify';})[0];
    cardMinDockItems=[];
    cardMinRender();
    if(sid&&typeof restorePinSession==='function')restorePinSession(sid.id);
    await wait(40);
    out.steps.restore={
      n:cardMinDockItems.length,
      counts:rowCounts(),
      preview:document.body.classList.contains('chosen-preview-open'),
      hl:document.body.classList.contains('hl-open'),
      dockOn:!!(document.getElementById('cardMinDock')&&document.getElementById('cardMinDock').classList.contains('is-on'))
    };
    if(out.steps.restore.preview||out.steps.restore.hl)out.errors.push('restore auto-opened a card');
    if(out.steps.restore.n<1)out.errors.push('restore did not fill dock');
    if(out.steps.restore.n!==5)out.errors.push('restore n '+out.steps.restore.n+' expected 5');
    if(JSON.stringify(out.steps.restore.counts)!=='[3,2]')out.errors.push('restore 5 used 5-wide template '+JSON.stringify(out.steps.restore.counts));

    document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed');
    await wait(40);
    var hist=styleOf('#searchHistory');
    var refOn=styleOf('#hdrSearchBtn');
    var probe=document.createElement('button');
    probe.className='hdr-menu-btn';
    probe.textContent='H';
    probe.setAttribute('aria-hidden','true');
    probe.style.cssText='position:absolute;left:-9999px;top:0';
    document.body.appendChild(probe);
    var refOff=styleOf('body > .hdr-menu-btn:last-of-type')||null;
    var probeCs=getComputedStyle(probe);
    var probeBox=probe.getBoundingClientRect();
    var unpressed={bg:probeCs.backgroundColor,h:Math.round(probeBox.height),radius:probeCs.borderRadius,fs:probeCs.fontSize,ff:probeCs.fontFamily,fw:probeCs.fontWeight};
    if(probe.parentNode)probe.parentNode.removeChild(probe);
    var ref=refOn;
    out.steps.hist={hist:hist, refOn:refOn, unpressed:unpressed};
    if(!hist)out.errors.push('History button missing');
    if(hist){
      if(hist.bg!==unpressed.bg)out.errors.push('History bg '+hist.bg+' vs unpressed '+unpressed.bg);
      var rh=refOn?refOn.h:unpressed.h;
      if(Math.abs(hist.h-rh)>6)out.errors.push('History height '+hist.h+' vs '+rh);
      var hr=parseFloat(hist.radius)||0, rr=parseFloat(unpressed.radius|| (refOn&&refOn.radius) ||0);
      if(Math.abs(hr-rr)>4)out.errors.push('History radius '+hist.radius+' vs '+(unpressed.radius||(refOn&&refOn.radius)));
      if(hist.fs!==(refOn&&refOn.fs||unpressed.fs))out.errors.push('History font-size '+hist.fs);
      if(/Palatino|Garamond/i.test(hist.ff||''))out.errors.push('History still serif '+hist.ff);
    }

    if(typeof setDisplayMode==='function')setDisplayMode('middle');
    document.body.classList.remove('hl-open','chosen-preview-open');
    function saveHits(){
      var savEl=document.getElementById('cardMinDockSave');
      var pillsNow=[].slice.call(document.querySelectorAll('#cardMinDock .card-min-pill'));
      var sb=box(savEl);
      var hit=pillsNow.map(box).filter(function(p){return overlaps(sb,p);});
      var jump=box(document.getElementById('catalogJumpStack'));
      var hist=box(document.getElementById('searchHistory'));
      var chromeHit=(jump&&overlaps(sb,jump)?1:0)+(hist&&overlaps(sb,hist)?1:0);
      return {save:sb, hit:hit, chromeHit:chromeHit};
    }
    seed(2);
    await wait(80);
    if(typeof cardMinPlace==='function')cardMinPlace();
    await wait(40);
    var g2=geom();
    var h2=saveHits();
    var gap2=null;
    var gapOk=false;
    if(h2.save&&g2.stack){
      var besideGap=h2.save.l>=g2.stack.r+4||h2.save.r<=g2.stack.l-4;
      var aboveGap=h2.save.b<=g2.stack.t-4;
      gapOk=besideGap||aboveGap;
      gap2=besideGap?h2.save.l-g2.stack.r:(g2.stack.t-h2.save.b);
    }
    out.steps.middle2={
      middle:document.body.classList.contains('display-middle'),
      save:h2.save,
      counts:g2.counts,
      stack:g2.stack,
      hits:h2.hit.length,
      chromeHit:h2.chromeHit,
      gap:gap2,
      stretched:!!(g2.stack&&g2.vw&&g2.stack.w>g2.vw*0.45)
    };
    if(!document.body.classList.contains('display-middle'))out.errors.push('not in Middle mode');
    if(JSON.stringify(g2.counts)!=='[2]')out.errors.push('middle 2 pins rows '+JSON.stringify(g2.counts));
    if(h2.hit.length)out.errors.push('middle 2 Save overlaps '+h2.hit.length+' pins save='+JSON.stringify(h2.save)+' stack='+JSON.stringify(g2.stack));
    if(h2.chromeHit)out.errors.push('middle 2 Save overlaps chrome');
    if(!gapOk)out.errors.push('middle 2 Save gap missing (save.l='+(h2.save&&h2.save.l)+' stack.r='+(g2.stack&&g2.stack.r)+')');
    if(out.steps.middle2.stretched)out.errors.push('middle 2 pin row stretched w='+(g2.stack&&g2.stack.w)+' vw='+g2.vw);

    seed(9);
    await wait(80);
    if(typeof cardMinPlace==='function')cardMinPlace();
    await wait(40);
    var g9m=geom();
    var h9=saveHits();
    out.steps.middle9={
      counts:g9m.counts,
      save:h9.save,
      stack:g9m.stack,
      hits:h9.hit.length,
      chromeHit:h9.chromeHit
    };
    if(JSON.stringify(g9m.counts)!=='[5,4]')out.errors.push('middle 9 rows '+JSON.stringify(g9m.counts)+' expected [5,4]');
    if(h9.hit.length)out.errors.push('middle 9 Save overlaps '+h9.hit.length+' pins');
    if(h9.chromeHit)out.errors.push('middle 9 Save overlaps chrome');
    var bottom9=g9m.rows&&g9m.rows[0];
    if(h9.save&&bottom9){
      var sameBand=!(h9.save.b<bottom9.t+4||h9.save.t>bottom9.b-4);
      if(sameBand&&h9.save.l+4<bottom9.r&&h9.save.r>bottom9.l+4)out.errors.push('middle 9 Save inside 5-wide row (save.l='+h9.save.l+' row.r='+bottom9.r+' save.b='+h9.save.b+' row.t='+bottom9.t+')');
    }
    if(h9.save&&g9m.stack&&h9.save.b>g9m.stack.t+4&&h9.save.l+4<g9m.stack.r&&h9.save.t<g9m.stack.b-4)out.errors.push('middle 9 Save inside stack bbox (save.l='+h9.save.l+' stack.r='+g9m.stack.r+' save.b='+h9.save.b+' stack.t='+g9m.stack.t+')');

    seed(5);
    await wait(80);
    if(typeof cardMinPlace==='function')cardMinPlace();
    await wait(40);
    var sav=document.getElementById('cardMinDockSave');
    var g5=geom();
    var h5=saveHits();
    out.steps.middleSave={
      middle:document.body.classList.contains('display-middle'),
      save:h5.save,
      counts:g5.counts,
      stack:g5.stack,
      hits:h5.hit.length,
      saveHidden:!!(sav&&sav.hidden)
    };
    if(JSON.stringify(g5.counts)!=='[3,2]')out.errors.push('middle 5 pins rows '+JSON.stringify(g5.counts)+' expected [3,2] not 5-wide');
    if(h5.hit.length)out.errors.push('Save overlaps '+h5.hit.length+' pins');

    seed(2);
    await wait(40);
    out.ok=out.errors.length===0;
    return out;
  }catch(err){
    return {ok:false, errors:[String(err&&err.stack||err)], steps:out.steps||{}};
  }
})()
"""

JS_NARROW = r"""
(async function(){
  function wait(ms){return new Promise(function(r){setTimeout(r,ms);});}
  function entries(){return [].slice.call(document.querySelectorAll('.entry')).filter(function(e){return e.id;});}
  function seed(n){
    var list=entries();
    cardMinDockItems=[];
    for(var i=0;i<n;i++){
      var el=list[i];
      cardMinDockItems.push({id:el.id,mode:'preview',kind:'preview',name:'P'+(i+1)});
    }
    cardMinRender();
  }
  function rowCounts(){
    return [].slice.call(document.querySelectorAll('#cardMinDock .card-min-row')).map(function(row){
      return row.querySelectorAll('.card-min-pill').length;
    });
  }
  var out={ok:true, errors:[], steps:{}};
  try{
    document.body.classList.remove('hl-open','chosen-preview-open');
    if(typeof setDisplayMode==='function')setDisplayMode('sides');
    await wait(80);
    seed(9);
    if(typeof cardMinPlace==='function')cardMinPlace();
    await wait(80);
    var counts=rowCounts();
    var pills=[].slice.call(document.querySelectorAll('#cardMinDock .card-min-pill'));
    var vw=window.innerWidth, vh=window.innerHeight;
    var overflow=pills.filter(function(p){
      var r=p.getBoundingClientRect();
      return r.left<-2||r.right>vw+2||r.bottom>vh+2;
    }).length;
    var stack=document.querySelector('#cardMinDock .card-min-stack');
    var sr=stack&&stack.getBoundingClientRect();
    out.steps.narrow={
      vw:vw,vh:vh,
      per:typeof cardMinMaxPerRow==='function'?cardMinMaxPerRow():null,
      counts:counts,
      n:pills.length,
      overflow:overflow,
      stackCx:sr?Math.round(sr.left+sr.width/2):null
    };
    var sav=document.getElementById('cardMinDockSave');
    var sb=sav?sav.getBoundingClientRect():null;
    var saveHits=0;
    if(sb){
      pills.forEach(function(p){
        var r=p.getBoundingClientRect();
        if(!(sb.right<r.left||sb.left>r.right||sb.bottom<r.top||sb.top>r.bottom))saveHits++;
      });
    }
    out.steps.narrow.saveHits=saveHits;
    if(JSON.stringify(counts)!=='[3,3,3]')out.errors.push('narrow 9 rows '+JSON.stringify(counts)+' expected [3,3,3] per='+out.steps.narrow.per);
    if(overflow)out.errors.push('narrow overflow '+overflow);
    if(sr&&Math.abs((sr.left+sr.width/2)-vw/2)>50)out.errors.push('narrow not centered');
    if(saveHits)out.errors.push('narrow Save overlaps '+saveHits+' pins');
    out.ok=out.errors.length===0;
    return out;
  }catch(err){
    return {ok:false, errors:[String(err&&err.stack||err)], steps:{}};
  }
})()
"""


def main():
    ensure_http()
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
    logf = open("/tmp/catalog-pin-pyramid.log", "w")
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
        wide = cdp.eval(JS_WIDE)
        try:
            cdp.shot("D1400-pin-2-middle.png")
        except Exception:
            pass
        cdp.eval(
            """
(function(){
  var list=[].slice.call(document.querySelectorAll('.entry')).filter(function(e){return e.id;});
  cardMinDockItems=[];
  for(var i=0;i<9;i++){
    var el=list[i];
    if(el)cardMinDockItems.push({id:el.id,mode:'preview',kind:'preview',name:'P'+(i+1)});
  }
  if(typeof cardMinRender==='function')cardMinRender();
})()
""",
            await_promise=False,
        )
        try:
            cdp.shot("D1400-pin-pyramid-9.png")
        except Exception:
            pass
        cdp.call(
            "Emulation.setDeviceMetricsOverride",
            {"width": 390, "height": 844, "deviceScaleFactor": 1, "mobile": True},
        )
        time.sleep(0.3)
        cdp.eval(
            "if(typeof cardMinPlace==='function')cardMinPlace();",
            await_promise=False,
        )
        narrow = cdp.eval(JS_NARROW)
        try:
            cdp.shot("M390-pin-pyramid-9.png")
        except Exception:
            pass
        result = {
            "ok": bool(wide and wide.get("ok") and narrow and narrow.get("ok")),
            "wide": wide,
            "narrow": narrow,
        }
        if wide and not wide.get("ok"):
            result["ok"] = False
        if narrow and not narrow.get("ok"):
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
