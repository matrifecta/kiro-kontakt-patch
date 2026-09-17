#!/usr/bin/env python3
"""Verify catalog pass 8: tin identity, bottom jump, stripe, covers, hist, sessions."""
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

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_catalog_pass8.json"
SHOTS = "/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots"
PORT = 9448
HTTP_PORT = 8788
ROOT = "/home/phnx/kiro-kontakt-patch/public/catalogs"
URL = "http://127.0.0.1:8788/DS-CATALOG.html?v=pass8"
PROFILE = "/tmp/catalog-pass8"
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
    raise SystemExit("http 8788 failed")


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
  function shown(){
    return Array.prototype.slice.call(document.querySelectorAll('.entry')).filter(function(e){
      return !e.classList.contains('is-hidden') && e.id;
    });
  }
  function tins(){
    var pills=Array.prototype.slice.call(document.querySelectorAll('#cardMinDock .card-min-pill'));
    return {
      n:pills.length,
      items:(cardMinDockItems||[]).map(function(x){return {id:x.id,kind:x.kind||'',mode:x.mode||''};}),
      attrs:pills.map(function(p){return {id:p.getAttribute('data-card-min-id'),kind:p.getAttribute('data-card-min-kind')};}),
      hl:document.body.classList.contains('hl-open'),
      preview:document.body.classList.contains('chosen-preview-open'),
      expanded: (typeof cardMinExpanded==='function' && cardMinExpanded()) ? cardMinExpanded().id : null,
      expandedKind: (typeof cardMinExpanded==='function' && cardMinExpanded() && typeof cardMinTinKind==='function') ? cardMinTinKind(cardMinExpanded()) : ''
    };
  }
  var out={ok:true, errors:[], steps:{}};
  try{
    if(typeof setDisplayMode==='function')setDisplayMode('sides');
    document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed');
    await wait(200);
    var bot=document.querySelector('a.bottom');
    var hold=document.getElementById('catalogBottomJump');
    var ix=document.getElementById('catalogIndex');
    var head=ix&&ix.querySelector('.catalog-index-head');
    out.steps.bottom={
      parent:bot&&bot.parentElement&&bot.parentElement.id,
      inIndex:!!(ix&&bot&&ix.contains(bot)),
      hold:!!hold,
      headH:head?Math.round(head.getBoundingClientRect().height):0,
      zHead:head?getComputedStyle(head).zIndex:'',
      embed:!!document.getElementById('catalogIndexEmbed')
    };
    if(out.steps.bottom.parent!=='catalogJumpStack'&&out.steps.bottom.parent!=='catalogBottomJump')out.errors.push('bottom not in jump stack');
    if(out.steps.bottom.inIndex)out.errors.push('bottom still inside Index');

    var main=document.getElementById('catalogMain');
    if(typeof window.bindMainHoverStripe==='function')window.bindMainHoverStripe();
    await wait(80);
    if(main){main.classList.add('has-hover-overflow');}
    var bodyStripe=document.getElementById('catalogMainHoverStripe');
    out.steps.stripe={
      mainHost:!!(main&&main.classList.contains('hover-scroll-host')),
      mainStripe:!!(main&&main.querySelector(':scope > .hover-scroll-stripe')),
      bodyStripe:!!bodyStripe,
      idxStripe:!!(ix&&ix.querySelector(':scope > .hover-scroll-stripe'))
    };
    if(!out.steps.stripe.mainStripe&&!out.steps.stripe.bodyStripe)out.errors.push('content hover stripe missing');

    var covers=Array.prototype.slice.call(document.querySelectorAll('.entry > .cover > img, .entry .cover > img')).slice(0,40);
    var live=0, pinned=0;
    covers.forEach(function(img){
      if(img.getAttribute('data-cover-src'))pinned++;
      if(img.naturalWidth>0)live++;
    });
    out.steps.covers={n:covers.length,live:live,pinned:pinned};
    if(covers.length && live<1 && pinned<1)out.errors.push('covers neither loaded nor pinned');

    out.steps.api={
      tinKind:typeof cardMinTinKind,
      histPush:typeof cardSearchHistPush,
      saveSess:typeof savePinSession,
      restoreSess:typeof restorePinSession
    };
    if(typeof cardMinTinKind!=='function')out.errors.push('missing cardMinTinKind');
    if(typeof cardSearchHistPush!=='function')out.errors.push('missing cardSearchHistPush');

    var entries=shown();
    if(entries.length<3){out.errors.push('need entries'); out.ok=false; return out;}
    var a=entries[0], b=entries[1];
    cardMinDockItems.splice(0,cardMinDockItems.length);
    if(typeof cardMinRender==='function')cardMinRender();

    openChosenPreview(a);
    await wait(60);
    minimizeExpandedCard(a);
    await wait(60);
    out.steps.embedOnce=tins();
    if(out.steps.embedOnce.n!==1)out.errors.push('embed tin n='+out.steps.embedOnce.n);
    if(out.steps.embedOnce.items[0] && out.steps.embedOnce.items[0].kind!=='preview')out.errors.push('embed tin kind '+JSON.stringify(out.steps.embedOnce.items[0]));

    openChosenPreview(a);
    await wait(50);
    minimizeExpandedCard(a);
    await wait(50);
    out.steps.embedTwice=tins();
    if(out.steps.embedTwice.n!==1)out.errors.push('duplicate embed tin n='+out.steps.embedTwice.n);

    openOverlay(a);
    await wait(80);
    out.steps.hlOpen={hl:document.body.classList.contains('hl-open'), kind:cardMinTinKind(a,cardMinMode(a))};
    minimizeExpandedCard(a);
    await wait(80);
    out.steps.both=tins();
    if(out.steps.both.n!==2)out.errors.push('fullscreen+embed should be 2 tins, got '+out.steps.both.n+' '+JSON.stringify(out.steps.both.items));
    var kinds=(out.steps.both.items||[]).map(function(x){return x.kind;}).sort().join(',');
    if(kinds!=='highlight,preview')out.errors.push('kinds '+kinds);
    var sameId=out.steps.both.items.every(function(x){return x.id===a.id;});
    if(!sameId)out.errors.push('both tins should share entry id');
    var attrKinds=(out.steps.both.attrs||[]).map(function(x){return x.kind;}).sort().join(',');
    if(attrKinds!=='highlight,preview')out.errors.push('pill attrs '+attrKinds);

    openOverlay(a);
    await wait(50);
    minimizeExpandedCard(a);
    await wait(50);
    out.steps.hlTwice=tins();
    if(out.steps.hlTwice.n!==2)out.errors.push('duplicate highlight tin n='+out.steps.hlTwice.n);

    cardMinRestore(a.id,'highlight');
    await wait(80);
    out.steps.restoreHl=tins();
    if(!out.steps.restoreHl.hl)out.errors.push('restore highlight did not open overlay');
    if(out.steps.restoreHl.preview)out.errors.push('restore highlight left preview open');

    cardMinRestore(a.id,'preview');
    await wait(80);
    out.steps.restorePrev=tins();
    if(!out.steps.restorePrev.preview)out.errors.push('restore preview did not open chosen preview');
    if(out.steps.restorePrev.hl)out.errors.push('restore preview left overlay open');

    if(typeof savePinSession==='function'){
      var saved=savePinSession('pass8-tins');
      var store=typeof pinSessionStore!=='undefined'?pinSessionStore:{};
      var sess=(store.sessions||[]).filter(function(s){return s&&s.name==='pass8-tins';})[0];
      out.steps.session={saved:!!saved, cards:sess&&sess.cards, frontKind:sess&&sess.frontKind};
      if(!sess||!sess.cards||sess.cards.length<2)out.errors.push('session did not store both tins');
      else{
        var sk=sess.cards.map(function(c){return c.kind;}).sort().join(',');
        if(sk!=='highlight,preview')out.errors.push('session kinds '+sk);
      }
    }

    openChosenPreview(b);
    await wait(40);
    minimizeExpandedCard(b);
    await wait(40);
    out.steps.cap=tins();
    if(out.steps.cap.n>3)out.errors.push('dock cap broken n='+out.steps.cap.n);

    var h=typeof cardSearchState!=='undefined'?cardSearchState.history:null;
    out.steps.hist={isArr:Array.isArray(h), n:h?h.length:0, push:typeof cardSearchHistPush};

    var ac=document.getElementById('acList');
    if(typeof showAc==='function')showAc('',{force:true});
    await wait(40);
    out.steps.ac={
      open:!!(ac&&ac.classList.contains('open')),
      html:(ac&&ac.innerHTML||'').slice(0,180),
      hasSession:!!(ac&&ac.querySelector('.ac-session'))
    };

    out.ok=out.errors.length===0;
    return out;
  }catch(err){
    return {ok:false, errors:[String(err&&err.stack||err)], steps:{}};
  }
})()
"""


def main():
    httpd = ensure_http()
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
    logf = open("/tmp/catalog-pass8.log", "w")
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
        cdp.call("Emulation.setDeviceMetricsOverride", {
            "width": 1400, "height": 900, "deviceScaleFactor": 1, "mobile": False
        })
        cdp.call("Page.navigate", {"url": URL})
        for _ in range(80):
            try:
                n = cdp.eval("document.querySelectorAll('.entry').length", await_promise=False)
            except Exception:
                n = 0
            if n and n > 20:
                break
            time.sleep(0.25)
        result = cdp.eval(JS)
        data = cdp.call("Page.captureScreenshot", {"format": "png"}).get("data", "")
        open(os.path.join(SHOTS, "D1400-pass8-tins.png"), "wb").write(__import__("base64").b64decode(data))
        json.dump(result, open(OUT, "w"), indent=2)
        print(json.dumps(result, indent=2)[:4000])
        if not result or not result.get("ok"):
            sys.exit(1)
    finally:
        proc.kill()
        if httpd:
            httpd.shutdown()


if __name__ == "__main__":
    main()
