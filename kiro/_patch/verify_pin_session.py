#!/usr/bin/env python3
"""Verify pin-session save includes the open card and AC click actually restores it."""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from urllib.parse import urlparse

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_pin_session.json"
PORT = 9462
HTTP_PORT = 8791
URL = "http://127.0.0.1:8791/DS-CATALOG.html?v=pinsess"
PROFILE = "/tmp/catalog-pin-session"
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
  var out={ok:true, errors:[], steps:{}};
  try{
    if(typeof setDisplayMode==='function')setDisplayMode('sides');
    document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed','search-extras-collapsed');
    await wait(80);
    var entries=[].slice.call(document.querySelectorAll('.entry[id]')).filter(function(el){return el.id;}).slice(0,4);
    out.steps.entries=entries.map(function(el){return el.id;});
    if(entries.length<3){out.errors.push('need 3 entries'); out.ok=false; return out;}

    cardMinDockItems=[];
    if(typeof closeChosenPreview==='function')closeChosenPreview({skipJumpExit:true,skipDismiss:true,keepMedia:true});
    if(typeof closeOverlay==='function')closeOverlay({skipScroll:true});
    if(typeof cardMinRender==='function')cardMinRender();

    openChosenPreview(entries[0]);
    minimizeExpandedCard(entries[0]);
    openChosenPreview(entries[1]);
    minimizeExpandedCard(entries[1]);
    openChosenPreview(entries[2]);
    await wait(40);

    var dockBefore=cardMinDockItems.map(function(it){return it.id;});
    var front=typeof cardMinExpanded==='function'?cardMinExpanded():null;
    var snap=snapshotPinSessionCards();
    out.steps.saveBefore={
      dockN:dockBefore.length,
      dockIds:dockBefore,
      frontId:front&&front.id||'',
      snapN:snap.length,
      snapIds:snap.map(function(c){return c.id;}),
      preview:document.body.classList.contains('chosen-preview-open')
    };
    if(snap.length!==3)out.errors.push('snapshot saved '+snap.length+' expected 3 (open card + 2 pills)');
    if(front&&snap.map(function(c){return c.id;}).indexOf(front.id)<0)out.errors.push('snapshot missed open card '+front.id);

    var ok=savePinSession('verify-pin-session');
    var sess=(pinSessionStore.sessions||[]).filter(function(s){return s&&s.name==='verify-pin-session';})[0];
    out.steps.saved={
      ok:!!ok,
      n:sess&&sess.cards&&sess.cards.length,
      ids:sess&&sess.cards?sess.cards.map(function(c){return c.id;}):[],
      frontId:sess&&sess.frontId||'',
      dockN:cardMinDockItems.length
    };
    if(!sess)out.errors.push('session not persisted');
    else if((sess.cards||[]).length!==3)out.errors.push('saved '+((sess.cards||[]).length)+' cards expected 3');

    cardMinDockItems=[];
    if(typeof closeChosenPreview==='function')closeChosenPreview({skipJumpExit:true,skipDismiss:true,keepMedia:true});
    if(typeof cardMinRender==='function')cardMinRender();
    await wait(20);
    out.steps.cleared={dockN:cardMinDockItems.length, preview:document.body.classList.contains('chosen-preview-open')};

    var ac=document.getElementById('acList');
    if(ac){ac.classList.add('open');}
    var item=document.createElement('div');
    item.className='ac-item ac-session';
    item.setAttribute('data-cat','session');
    item.setAttribute('onclick',"restorePinSession('"+sess.id+"',event)");
    item.textContent='verify-pin-session';
    (ac||document.body).appendChild(item);
    item.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,view:window}));
    await wait(80);

    var restoredFront=typeof cardMinExpanded==='function'?cardMinExpanded():null;
    out.steps.loaded={
      dockN:cardMinDockItems.length,
      dockIds:cardMinDockItems.map(function(it){return it.id;}),
      preview:document.body.classList.contains('chosen-preview-open'),
      frontId:restoredFront&&restoredFront.id||'',
      hl:!!document.querySelector('.entry.highlight')
    };
    if(cardMinDockItems.length!==3)out.errors.push('restore dock '+cardMinDockItems.length+' expected 3');
    if(!out.steps.loaded.preview)out.errors.push('restore did not keep/open preview');
    if(sess.frontId&&out.steps.loaded.frontId&&out.steps.loaded.frontId!==sess.frontId)out.errors.push('restored front '+out.steps.loaded.frontId+' expected '+sess.frontId);

    var covers=typeof overlayCoversSearch==='function'?overlayCoversSearch():null;
    out.steps.coversSides=covers;
    if(covers)out.errors.push('overlayCoversSearch true in Sides with preview open');

    out.ok=out.errors.length===0;
    return out;
  }catch(err){
    return {ok:false, errors:[String(err&&err.stack||err)], steps:{}};
  }
})()
"""


def main():
    try:
        urllib.request.urlopen("http://127.0.0.1:8791/DS-CATALOG.html", timeout=1).read(64)
    except Exception:
        print("need catalogs http on 8791", file=sys.stderr)
        sys.exit(2)
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
    logf = open("/tmp/catalog-pin-session.log", "w")
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
        json.dump(result, open(OUT, "w"), indent=2)
        print(json.dumps(result, indent=2))
        if not result or not result.get("ok"):
            sys.exit(1)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    main()
