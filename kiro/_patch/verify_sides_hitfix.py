#!/usr/bin/env python3
"""Verify Sides jump clicks, content hover stripe, and History menu."""
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

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_sides_hitfix.json"
SHOTS = "/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots"
PORT = 9461
HTTP_PORT = 8791
ROOT = "/home/phnx/kiro-kontakt-patch/public/catalogs"
URL = "http://127.0.0.1:8791/DS-CATALOG.html?v=hitfix"
PROFILE = "/tmp/catalog-sides-hitfix"
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


JS = r"""
(async function(){
  function wait(ms){return new Promise(function(r){setTimeout(r,ms);});}
  var out={ok:true, errors:[], steps:{}};
  try{
    if(typeof setDisplayMode==='function')setDisplayMode('sides');
    document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed');
    if(typeof ensureCatalogMain==='function')ensureCatalogMain();
    if(typeof bindCatalogTop==='function')bindCatalogTop();
    if(typeof window.bindMainHoverStripe==='function')window.bindMainHoverStripe();
    if(typeof window.syncMainHoverStripe==='function')window.syncMainHoverStripe();
    await wait(160);

    var main=document.getElementById('catalogMain');
    var stack=document.getElementById('catalogJumpStack');
    var top=stack&&stack.querySelector('a.top');
    var bot=stack&&stack.querySelector('a.bottom');
    var pe=stack?getComputedStyle(stack).pointerEvents:'';
    var z=stack?getComputedStyle(stack).zIndex:'';
    out.steps.jump={
      parent:stack&&stack.parentNode&&(stack.parentNode.id||stack.parentNode.tagName||''),
      bound:!!(stack&&stack.dataset.sidesJumpBound),
      hasTop:!!top, hasBot:!!bot,
      pe:pe, z:z,
      order:stack&&stack.firstElementChild&&stack.firstElementChild.className
    };
    if(!stack)out.errors.push('no catalogJumpStack');
    if(pe==='none')out.errors.push('jump stack pointer-events none');
    if(!out.steps.jump.bound)out.errors.push('jump stack not capture-bound');
    if(out.steps.jump.order&&out.steps.jump.order.indexOf('top')<0)out.errors.push('↑ not first in stack');

    if(main){main.scrollTop=Math.min(800,Math.max(120,main.scrollHeight/4));}
    await wait(80);
    var mid=main?main.scrollTop:0;
    if(bot){
      bot.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,view:window}));
      await wait(700);
    }
    var afterBot=main?main.scrollTop:0;
    if(main){try{main.scrollTo({top:main.scrollTop,behavior:'instant'});}catch(err){}}
    if(top){
      top.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,view:window}));
      await wait(700);
    }
    var afterTop=main?main.scrollTop:0;
    out.steps.jumpScroll={mid:Math.round(mid), afterBot:Math.round(afterBot), afterTop:Math.round(afterTop), max:main?Math.round(main.scrollHeight-main.clientHeight):0};
    if(!(afterBot>mid+20))out.errors.push('↓ did not scroll down');
    if(!(afterTop<afterBot-20))out.errors.push('↑ did not scroll up');

    var st=document.getElementById('catalogMainHoverStripe');
    if(typeof window.syncMainHoverStripe==='function')window.syncMainHoverStripe();
    await wait(60);
    var cs=st&&getComputedStyle(st);
    var sr=st&&st.getBoundingClientRect();
    var mr=main&&main.getBoundingClientRect();
    out.steps.stripe={
      exists:!!st,
      parent:st&&st.parentNode&&(st.parentNode.id||st.parentNode.tagName||''),
      parkedOnBody:!!(st&&st.parentNode===document.body),
      pos:cs&&cs.position,
      hidden:!!(st&&st.hidden),
      showClass:document.body.classList.contains('has-hover-overflow-content'),
      h:sr?Math.round(sr.height):0,
      t:sr?Math.round(sr.top):0,
      mainH:mr?Math.round(mr.height):0,
      overflow:!!(main&&main.scrollHeight>main.clientHeight+8)
    };
    if(!st)out.errors.push('content stripe missing');
    if(st&&st.parentNode!==document.body)out.errors.push('content stripe not on body');
    if(cs&&cs.position!=='fixed')out.errors.push('content stripe not fixed');
    if(out.steps.stripe.overflow&&out.steps.stripe.hidden)out.errors.push('content stripe hidden despite overflow');
    if(out.steps.stripe.overflow&&out.steps.stripe.h<40)out.errors.push('content stripe height '+out.steps.stripe.h);

    var btn=document.getElementById('searchHistory');
    var cloud=document.getElementById('historyCloud');
    var wrap=document.getElementById('searchHistoryWrap');
    if(typeof parkHistoryCloud==='function')parkHistoryCloud();
    var pre={btn:!!btn,cloud:!!cloud,wrapParent:wrap&&wrap.parentElement&&wrap.parentElement.id,fn:typeof showHistoryCloud};
    if(typeof showHistoryCloud==='function')showHistoryCloud();
    else if(btn)btn.click();
    cloud=document.getElementById('historyCloud');
    var picks=document.getElementById('historyPicks');
    var cr=cloud&&cloud.getBoundingClientRect();
    out.steps.hist={
      pre:pre,
      btn:!!btn,
      cloud:!!cloud,
      parent:cloud&&cloud.parentNode&&(cloud.parentNode.id||cloud.parentNode.tagName||''),
      wrapParent:wrap&&wrap.parentElement&&wrap.parentElement.id,
      hidden:!!(cloud&&cloud.hidden),
      w:cr?Math.round(cr.width):0,
      h:cr?Math.round(cr.height):0,
      picks:!!picks,
      picksN:picks?picks.children.length:0,
      fnNow:typeof showHistoryCloud
    };
    await wait(200);
    out.steps.hist.stillOpen=!!(cloud&&!cloud.hidden);
    document.body.classList.add('is-content-hover');
    if(typeof window.syncMainHoverStripe==='function')window.syncMainHoverStripe();
    await wait(40);

    if(!cloud)out.errors.push('history cloud missing');
    if(cloud&&cloud.parentNode!==document.body)out.errors.push('history cloud not on body');
    if(out.steps.hist.w<80||out.steps.hist.h<40)out.errors.push('history cloud size '+out.steps.hist.w+'x'+out.steps.hist.h);
    if(!out.steps.hist.stillOpen)out.errors.push('history cloud dismissed immediately');
    if(out.steps.hist.picksN<4)out.errors.push('history picks '+out.steps.hist.picksN);

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
    logf = open("/tmp/catalog-sides-hitfix.log", "w")
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
        result = cdp.eval(JS)
        data = cdp.call("Page.captureScreenshot", {"format": "png"}).get("data", "")
        open(os.path.join(SHOTS, "D1400-sides-hitfix.png"), "wb").write(base64.b64decode(data))
        json.dump(result, open(OUT, "w"), indent=2)
        print(json.dumps(result, indent=2)[:5000])
        if not result or not result.get("ok"):
            sys.exit(1)
    finally:
        proc.kill()
        if httpd:
            httpd.shutdown()


if __name__ == "__main__":
    main()
