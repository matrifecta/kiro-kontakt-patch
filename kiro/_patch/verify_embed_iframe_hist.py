#!/usr/bin/env python3
"""CDP: in-iframe embed Back stacks, pops one page, exits only from landing."""
import json
import os
import socket
import subprocess
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
import base64

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_embed_iframe_hist.json")
PORT = 9532
HTTP_PORT = 8797
PROFILE = "/tmp/catalog-iframe-hist"


class Ws:
    def __init__(self, url):
        u = urlparse(url)
        host, port = u.hostname, u.port or 80
        path = u.path + (("?" + u.query) if u.query else "")
        key = base64.b64encode(os.urandom(16)).decode()
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

    def eval(self, expr, await_promise=False):
        r = self.call(
            "Runtime.evaluate",
            {"expression": expr, "awaitPromise": await_promise, "returnByValue": True},
        )
        if r.get("exceptionDetails"):
            raise RuntimeError(r["exceptionDetails"])
        return r.get("result", {}).get("value")


def port_open(port):
    s = socket.socket()
    s.settimeout(0.3)
    try:
        s.connect(("127.0.0.1", port))
        return True
    except Exception:
        return False
    finally:
        s.close()


def new_tab(url):
    try:
        return json.load(
            urllib.request.urlopen(
                urllib.request.Request(f"http://127.0.0.1:{PORT}/json/new?" + url, method="PUT")
            )
        )
    except Exception:
        return json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/new?" + url))


def wait_ready(cdp):
    for _ in range(150):
        try:
            n = cdp.eval(
                "!!(document.querySelector('.entry')&&typeof openCardSearchEmbed==='function'&&typeof cardSearchOnFrameNav==='function')"
            )
        except Exception:
            n = False
        if n:
            return
        time.sleep(0.2)
    raise SystemExit("catalog JS not ready")


WEB = r"""
(async () => {
  var card=document.querySelector('.entry:not(.is-hidden)')||document.querySelector('.entry');
  if(!card)return {err:'no-card'};
  if(typeof rememberViewed==='function')rememberViewed(card);
  if(typeof openChosenPreview==='function')openChosenPreview(card);
  var btn=card.querySelector('.search-popup-btn');
  var web=(btn&&btn.dataset.web)||'https://www.google.com/search?q=kontakt';
  var opened=openCardSearchEmbed('web',web);
  var landN=(cardSearchState.history||[]).length;
  var embedOpen=document.body.classList.contains('card-embed-open');
  var fns={
    onNav:typeof cardSearchOnFrameNav==='function',
    restore:typeof cardSearchRestoreFrame==='function',
    pop:typeof cardSearchPopEmbed==='function'
  };
  await new Promise(function(r){setTimeout(r,900);});
  var frame=document.getElementById('cardSearchFrame');
  var landSrc=(cardSearchState.embedUrl||(frame&&(frame.getAttribute('src')||frame.src))||'');
  var page2='http://127.0.0.1:8797/KONTAKT-CATALOG.html?embed-page=2';
  cardSearchState._ownFrameNav=false;
  cardSearchState._applyingHist=false;
  var loadP=new Promise(function(res){
    if(!frame){res('no-frame');return;}
    var to=setTimeout(function(){res('timeout');},4000);
    frame.addEventListener('load',function once(){
      frame.removeEventListener('load',once);
      clearTimeout(to);
      res('load');
    });
  });
  frame.src=page2;
  var loadHow=await loadP;
  await new Promise(function(r){setTimeout(r,120);});
  if((cardSearchState.history||[]).length<2&&typeof cardSearchOnFrameNav==='function'){
    cardSearchState._embedUserInteracted=true;
    cardSearchOnFrameNav(frame);
  }
  var afterNav=(cardSearchState.history||[]).length;
  var kinds=(cardSearchState.history||[]).map(function(s){return (s&&s.kind)||s;});
  var srcAfter=frame.getAttribute('src')||frame.src||'';
  var stillAfterNav=document.body.classList.contains('card-embed-open');
  cardSearchBack();
  var afterBack=(cardSearchState.history||[]).length;
  var stillEmbed=document.body.classList.contains('card-embed-open');
  var srcBack=frame.getAttribute('src')||frame.src||'';
  var embedUrlBack=cardSearchState.embedUrl||'';
  cardSearchBack();
  var afterExit=(cardSearchState.history||[]).length;
  var exited=!document.body.classList.contains('card-embed-open');
  return {
    opened:!!opened,landN:landN,embedOpen:embedOpen,fns:fns,landSrc:String(landSrc).slice(0,120),
    loadHow:loadHow,afterNav:afterNav,kinds:kinds,srcAfter:String(srcAfter).slice(0,120),
    stillAfterNav:stillAfterNav,afterBack:afterBack,stillEmbed:stillEmbed,
    srcBack:String(srcBack).slice(0,160),embedUrlBack:String(embedUrlBack).slice(0,160),
    afterExit:afterExit,exited:exited
  };
})()
"""

YT = r"""
(() => {
  var card=document.querySelector('.entry:not(.is-hidden)')||document.querySelector('.entry');
  if(!card)return {err:'no-card'};
  if(typeof rememberViewed==='function')rememberViewed(card);
  if(typeof openChosenPreview==='function')openChosenPreview(card);
  var btn=card.querySelector('.search-popup-btn');
  var yt=(btn&&btn.dataset.yt)||'https://www.youtube.com/results?search_query=kontakt';
  var opened=openCardSearchEmbed('yt',yt);
  var landN=(cardSearchState.history||[]).length;
  cardSearchState.ytItems=[{id:'dQw4w9WgXcQ',title:'t1',thumb:''},{id:'9bZkp7q19f0',title:'t2',thumb:''}];
  cardSearchPlayYt(1);
  var afterNav=(cardSearchState.history||[]).length;
  var frame=document.getElementById('cardSearchFrame');
  var srcVid=frame&&(frame.getAttribute('src')||frame.src)||'';
  cardSearchBack();
  var afterBack=(cardSearchState.history||[]).length;
  var stillEmbed=document.body.classList.contains('card-embed-open');
  var frameHidden=!!(frame&&frame.classList.contains('is-hidden'));
  cardSearchBack();
  var exited=!document.body.classList.contains('card-embed-open');
  return {
    opened:!!opened,landN:landN,afterNav:afterNav,srcVid:String(srcVid).slice(0,80),
    afterBack:afterBack,stillEmbed:stillEmbed,frameHidden:frameHidden,exited:exited
  };
})()
"""

FALLBACK = r"""
(() => {
  var card=document.querySelector('.entry:not(.is-hidden)')||document.querySelector('.entry');
  if(typeof rememberViewed==='function')rememberViewed(card);
  if(typeof openChosenPreview==='function')openChosenPreview(card);
  var opened=openCardSearchEmbed('web','https://www.google.com/search?q=kontakt');
  cardSearchState._iframeHasStack=true;
  cardSearchState._embedFrameLoads=2;
  cardSearchState._iframeLoads=2;
  cardSearchState._landingEmbedUrl=cardSearchState.embedUrl||'https://www.google.com/search?igu=1&q=kontakt';
  var landN=(cardSearchState.history||[]).length;
  cardSearchBack();
  var still=document.body.classList.contains('card-embed-open');
  var n=(cardSearchState.history||[]).length;
  cardSearchBack();
  var exited=!document.body.classList.contains('card-embed-open');
  return {opened:!!opened,landN:landN,stillAfterUnsnapBack:still,nAfter:n,exited:exited};
})()
"""


def run(cdp, url):
    cdp.call("Page.enable")
    cdp.call("Runtime.enable")
    cdp.call("Page.navigate", {"url": url})
    time.sleep(0.8)
    wait_ready(cdp)
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
    time.sleep(0.25)
    web = cdp.eval(WEB, await_promise=True)
    yt = cdp.eval(YT)
    fb = cdp.eval(FALLBACK)
    return {"web": web, "yt": yt, "fallback": fb}


def judge(rep, errors, prefix):
    web = rep.get("web") or {}
    if web.get("landN") != 1:
        errors.append(f"{prefix}.web landN={web.get('landN')} want 1")
    if not web.get("embedOpen"):
        errors.append(f"{prefix}.web not embed-open after open")
    if (web.get("afterNav") or 0) < 2:
        errors.append(f"{prefix}.web afterNav={web.get('afterNav')} want >=2")
    if not web.get("stillAfterNav"):
        errors.append(f"{prefix}.web exited after src change")
    if web.get("afterBack") != 1:
        errors.append(f"{prefix}.web afterBack={web.get('afterBack')} want 1")
    if not web.get("stillEmbed"):
        errors.append(f"{prefix}.web Back from page2 exited")
    src_back = web.get("srcBack") or ""
    page2 = "embed-page=2"
    if page2 in src_back and "google" not in (web.get("embedUrlBack") or src_back).lower():
        errors.append(f"{prefix}.web Back did not restore landing src {src_back}")
    if not web.get("exited"):
        errors.append(f"{prefix}.web second Back did not exit")
    yt = rep.get("yt") or {}
    if yt.get("landN") != 1:
        errors.append(f"{prefix}.yt landN={yt.get('landN')} want 1")
    if (yt.get("afterNav") or 0) < 2:
        errors.append(f"{prefix}.yt afterNav={yt.get('afterNav')} want >=2")
    if yt.get("afterBack") != 1:
        errors.append(f"{prefix}.yt afterBack={yt.get('afterBack')} want 1")
    if not yt.get("stillEmbed"):
        errors.append(f"{prefix}.yt Back from video exited")
    if not yt.get("exited"):
        errors.append(f"{prefix}.yt second Back did not exit")
    fb = rep.get("fallback") or {}
    if not fb.get("stillAfterUnsnapBack"):
        errors.append(f"{prefix}.fallback Back with hist=1+iframe stack exited")
    if not fb.get("exited"):
        errors.append(f"{prefix}.fallback second Back did not exit")


def main():
    if not port_open(HTTP_PORT):
        raise SystemExit("http://127.0.0.1:8797 not serving")
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
    subprocess.run(["pkill", "-f", f"remote-debugging-port={PORT}"], check=False)
    time.sleep(0.2)
    os.makedirs(PROFILE, exist_ok=True)
    logf = open("/tmp/catalog-iframe-hist.log", "w")
    proc = subprocess.Popen(
        [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--disable-extensions",
            "--disable-background-networking",
            f"--user-data-dir={PROFILE}",
            f"--remote-debugging-port={PORT}",
            "about:blank",
        ],
        stdout=logf,
        stderr=logf,
    )
    try:
        for _ in range(50):
            if port_open(PORT):
                break
            time.sleep(0.1)
        else:
            raise SystemExit("chromium debug port failed")
        tab = new_tab("about:blank")
        cdp = CDP(tab["webSocketDebuggerUrl"])
        reports = {}
        reports["kontakt"] = run(cdp, "http://127.0.0.1:8797/KONTAKT-CATALOG.html?v=iframe-hist-cdp")
        reports["portable"] = run(
            cdp, "http://127.0.0.1:8797/KONTAKT-CATALOG-portable.html?v=iframe-hist-cdp"
        )
        errors = []
        judge(reports["kontakt"], errors, "K")
        judge(reports["portable"], errors, "P")
        payload = {"ok": not errors, "errors": errors, "reports": reports}
        OUT.write_text(json.dumps(payload, indent=2))
        print(json.dumps({"ok": payload["ok"], "errors": errors, "reports": reports}, indent=2))
        if errors:
            raise SystemExit(1)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    main()
