#!/usr/bin/env python3
"""Measure Sides pane bottoms and gutters at landscape, scale, collapse, portrait."""
import json, os, socket, subprocess, sys, time, urllib.request
from urllib.parse import urlparse

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_sides_pane_align.json"
SHOTS = "/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots"
PORT = 9417
PROFILE = "/tmp/catalog-sides-pane-align"
URL_DS = "http://127.0.0.1:8788/DS-CATALOG.html?v=pane-align"
URL_K = "http://127.0.0.1:8788/KONTAKT-CATALOG.html?v=pane-align"
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
        "--ozone-override-screen-size=1400,900",
        "--use-angle=swiftshader-webgl",
        "about:blank",
    ],
    stdout=open("/tmp/catalog-sides-pane-align.log", "w"),
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

    def eval(self, expr):
        r = self.call("Runtime.evaluate", {"expression": expr, "awaitPromise": True, "returnByValue": True})
        return r.get("result", {}).get("value")


MEASURE = r"""
(function(){
  function box(el){
    if(!el) return null;
    var r=el.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),r:Math.round(r.right),b:Math.round(r.bottom)};
  }
  var sc=document.getElementById('searchChrome');
  var cm=document.getElementById('catalogMain');
  var fw=document.getElementById('filterWrap');
  var ix=document.getElementById('catalogIndex');
  var scb=box(sc), cmb=box(cm), fwb=box(fw), ixb=box(ix);
  var searchOn=!document.body.classList.contains('search-chrome-collapsed') && sc && getComputedStyle(sc).display!=='none';
  var kwOn=!document.body.classList.contains('kw-chrome-collapsed') && fw && getComputedStyle(fw).display!=='none';
  var bottoms=[];
  if(searchOn&&scb) bottoms.push(scb.b);
  if(cmb) bottoms.push(cmb.b);
  if(kwOn&&fwb) bottoms.push(fwb.b);
  var maxB=Math.max.apply(null,bottoms);
  var minB=Math.min.apply(null,bottoms);
  var portrait=innerHeight>innerWidth && innerWidth>=900;
  var gapL=null, gapR=null, gapIxL=null, gapIxR=null, gapIxB=null, gapStack=null, overlap=false;
  if(portrait){
    var stackR=null;
    if(searchOn&&scb) stackR=scb.r;
    if(kwOn&&fwb) stackR=stackR==null?fwb.r:Math.max(stackR,fwb.r);
    var stackL=null;
    if(searchOn&&scb) stackL=scb.x;
    if(kwOn&&fwb) stackL=stackL==null?fwb.x:Math.min(stackL,fwb.x);
    if(cmb&&stackR!=null){
      if(cmb.x>=stackR-2) gapL=cmb.x-stackR;
      else if(stackL!=null) gapR=stackL-cmb.r;
    }
    if(searchOn&&kwOn&&scb&&fwb) gapStack=fwb.y-scb.b;
    if(gapL!=null&&gapL<0) overlap=true;
    if(gapR!=null&&gapR<0) overlap=true;
    if(gapStack!=null&&gapStack<0) overlap=true;
  }else{
    if(searchOn&&scb&&cmb){
      gapL=cmb.x-scb.r;
      if(cmb.x<scb.r-1) overlap=true;
    }
    if(kwOn&&fwb&&cmb){
      gapR=fwb.x-cmb.r;
      if(cmb.r>fwb.x+1) overlap=true;
    }
  }
  if(ixb&&searchOn&&scb) gapIxL=ixb.x-scb.r;
  if(ixb&&kwOn&&fwb && !portrait) gapIxR=fwb.x-ixb.r;
  if(ixb&&cmb) gapIxB=cmb.b-ixb.b;
  var gapCss=(getComputedStyle(document.documentElement).getPropertyValue('--sides-pane-gap')||'').trim();
  var bodyGap=(getComputedStyle(document.body).columnGap||'').trim();
  var fs=getComputedStyle(document.documentElement).fontSize;
  return {
    vw:innerWidth, vh:innerHeight,
    display: document.body.className,
    searchOn:!!searchOn, kwOn:!!kwOn,
    sc:scb, cm:cmb, fw:fwb, ix:ixb,
    bottomSpread: maxB-minB,
    bottoms:{min:minB,max:maxB},
    gapL:gapL, gapR:gapR, gapIxL:gapIxL, gapIxR:gapIxR,
    overlap:overlap,
    fused: (gapL!=null&&gapL<=0)||(gapR!=null&&gapR<=0)||(gapStack!=null&&gapStack<=0),
    gapStack:gapStack,
    portrait:portrait,
    gapCss:gapCss, bodyGap:bodyGap, fontSize:fs,
    uiScale: document.documentElement.getAttribute('data-ui-scale'),
    catWrap: fw?getComputedStyle(fw.querySelector('.cat-switch')||fw).flexWrap:null,
    indexLines: ix?getComputedStyle(ix.querySelector('.index')||ix).getPropertyValue('--index-name-lines').trim():null
  };
})()
"""


def set_view(cdp, w, h):
    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False},
    )
    time.sleep(0.4)
    cdp.eval("if(typeof applySidesCols==='function')applySidesCols();")
    time.sleep(0.2)


def boot_sides(cdp):
    cdp.eval(
        r"""
(function(){
  try{
    ['catalog-portrait-lw','catalog-portrait-rw','catalog-portrait-menu-h'].forEach(function(k){localStorage.removeItem(k);});
    Object.keys(localStorage).forEach(function(k){
      if(k.indexOf('catalog-sides-portrait-flip')===0) localStorage.removeItem(k);
    });
  }catch(e){}
  document.body.classList.remove('sides-portrait-flip','sides-orient-portrait');
  if(typeof setDisplayMode==='function') setDisplayMode('sides');
  if(document.body.classList.contains('layout-edit')&&typeof toggleLayoutEdit==='function') toggleLayoutEdit();
  if(typeof applyLayoutChrome==='function') applyLayoutChrome('sck');
  if(typeof applySidesCols==='function') applySidesCols();
})()
"""
    )
    time.sleep(0.45)


def shot(cdp, name):
    data = cdp.call("Page.captureScreenshot", {"format": "png"})["data"]
    path = os.path.join(SHOTS, name)
    open(path, "wb").write(__import__("base64").b64decode(data))
    return path


def wait_ready(cdp):
    for _ in range(50):
        n = cdp.eval("typeof setDisplayMode==='function'&&document.querySelectorAll('.entry').length")
        if isinstance(n, int) and n > 3:
            return n
        time.sleep(0.2)
    return cdp.eval("typeof setDisplayMode")


out = {"ok": True, "checks": {}}
try:
    tab = new_tab(URL_DS)
    cdp = CDP(tab["webSocketDebuggerUrl"])
    cdp.call("Page.enable")
    cdp.call("Runtime.enable")
    time.sleep(2.0)
    set_view(cdp, 1400, 900)
    out["ready"] = wait_ready(cdp)
    boot_sides(cdp)
    land = cdp.eval(MEASURE)
    out["checks"]["landscape_sck"] = land
    shot(cdp, "D1400-pane-align-sck.png")

    cdp.eval(
        """
(function(){
  if(typeof toggleLayoutEdit==='function') toggleLayoutEdit();
  document.body.style.setProperty('--sides-lw','360px');
  document.body.style.setProperty('--sides-rw','400px');
})()
"""
    )
    time.sleep(0.25)
    out["checks"]["customize_wide"] = cdp.eval(MEASURE)
    cdp.eval(
        """
(function(){
  document.body.style.setProperty('--sides-lw','240px');
  document.body.style.setProperty('--sides-rw','260px');
})()
"""
    )
    time.sleep(0.25)
    out["checks"]["customize_narrow"] = cdp.eval(MEASURE)
    shot(cdp, "D1400-pane-align-customize.png")
    cdp.eval("if(document.body.classList.contains('layout-edit')&&typeof toggleLayoutEdit==='function')toggleLayoutEdit();")

    cdp.eval(
        """
(function(){
  if(typeof applyLayoutChrome==='function') applyLayoutChrome('sck');
  if(typeof stepUiScale==='function'){stepUiScale(1);stepUiScale(1);}
  else {document.documentElement.style.setProperty('--ui-scale','1.25');document.documentElement.setAttribute('data-ui-scale','125');}
  if(typeof applySidesCols==='function') applySidesCols();
})()
"""
    )
    time.sleep(0.3)
    out["checks"]["scale_larger"] = cdp.eval(MEASURE)
    cdp.eval(
        """
(function(){
  if(typeof stepUiScale==='function'){stepUiScale(-1);stepUiScale(-1);stepUiScale(-1);stepUiScale(-1);}
  else {document.documentElement.style.setProperty('--ui-scale','0.8');document.documentElement.setAttribute('data-ui-scale','80');}
  if(typeof applySidesCols==='function') applySidesCols();
})()
"""
    )
    time.sleep(0.3)
    out["checks"]["scale_smaller"] = cdp.eval(MEASURE)
    shot(cdp, "D1400-pane-align-scale.png")
    cdp.eval(
        """
(function(){
  if(typeof stepUiScale==='function'){
    var cur=parseInt(document.documentElement.getAttribute('data-ui-scale')||'100',10);
    while(cur<100){stepUiScale(1);cur=parseInt(document.documentElement.getAttribute('data-ui-scale')||'100',10);}
    while(cur>100){stepUiScale(-1);cur=parseInt(document.documentElement.getAttribute('data-ui-scale')||'100',10);}
  } else {
    document.documentElement.style.setProperty('--ui-scale','1');
    document.documentElement.setAttribute('data-ui-scale','100');
  }
  if(typeof applyLayoutChrome==='function') applyLayoutChrome('sck');
})()
"""
    )
    time.sleep(0.2)

    cdp.eval(
        """
(function(){
  if(typeof applyLayoutChrome==='function') applyLayoutChrome('sck');
  if(typeof toggleKwChrome==='function') toggleKwChrome();
  else if(typeof toggleHdrKw==='function') toggleHdrKw();
  else {
    document.body.classList.add('kw-chrome-collapsed');
    document.body.classList.remove('kw-open');
    var fw=document.getElementById('filterWrap');
    if(fw) fw.classList.remove('open');
  }
  if(typeof applySidesCols==='function') applySidesCols();
})()
"""
    )
    time.sleep(0.3)
    out["checks"]["collapse_kw"] = cdp.eval(MEASURE)
    shot(cdp, "D1400-pane-align-kwcollapsed.png")
    cdp.eval("if(typeof applyLayoutChrome==='function')applyLayoutChrome('sck');")
    time.sleep(0.2)

    set_view(cdp, 900, 1200)
    boot_sides(cdp)
    out["checks"]["portrait_900"] = cdp.eval(MEASURE)
    shot(cdp, "D900-pane-align-portrait.png")

    set_view(cdp, 1400, 900)
    tab2 = new_tab(URL_K)
    cdpk = CDP(tab2["webSocketDebuggerUrl"])
    cdpk.call("Page.enable")
    cdpk.call("Runtime.enable")
    time.sleep(2.0)
    set_view(cdpk, 1400, 900)
    out["kontaktReady"] = wait_ready(cdpk)
    boot_sides(cdpk)
    out["checks"]["kontakt_sck"] = cdpk.eval(MEASURE)
    shot(cdpk, "K1400-pane-align-sck.png")

    def judge(name, m, expect_search=True, expect_kw=True, portrait=False):
        if not m:
            return False, f"{name}: no measure"
        reasons = []
        if m.get("overlap") or m.get("fused"):
            reasons.append("overlap/fused")
        if portrait:
            g = m.get("gapL") if m.get("gapL") is not None else m.get("gapR")
            if g is not None and g < 3:
                reasons.append(f"stackGap={g}")
            if expect_search and expect_kw and m.get("gapStack") is not None and m["gapStack"] < 3:
                reasons.append(f"gapStack={m.get('gapStack')}")
            cm = (m.get("cm") or {}).get("b")
            fw = (m.get("fw") or {}).get("b")
            sc = (m.get("sc") or {}).get("b")
            if expect_kw and cm and fw and abs(cm - fw) > 4:
                reasons.append(f"cm/fw bottom {cm}/{fw}")
            elif expect_search and not expect_kw and cm and sc and abs(cm - sc) > 4:
                reasons.append(f"cm/sc bottom {cm}/{sc}")
        else:
            if expect_search and m.get("gapL") is not None and m["gapL"] < 3:
                reasons.append(f"gapL={m.get('gapL')}")
            if expect_kw and m.get("gapR") is not None and m["gapR"] < 3:
                reasons.append(f"gapR={m.get('gapR')}")
            if m.get("bottomSpread", 99) > 4:
                reasons.append(f"bottomSpread={m.get('bottomSpread')}")
        if expect_search and not m.get("searchOn"):
            reasons.append("search off")
        if expect_kw and not m.get("kwOn"):
            reasons.append("kw off")
        ixh = (m.get("ix") or {}).get("h") or 0
        if ixh and ixh < 40 and not portrait:
            reasons.append(f"indexH={ixh}")
        return (len(reasons) == 0, ",".join(reasons) or "ok")

    verdicts = {}
    verdicts["landscape_sck"] = judge("landscape", land, True, True)
    verdicts["customize_wide"] = judge("wide", out["checks"]["customize_wide"], True, True)
    verdicts["customize_narrow"] = judge("narrow", out["checks"]["customize_narrow"], True, True)
    verdicts["scale_larger"] = judge("larger", out["checks"]["scale_larger"], True, True)
    verdicts["scale_smaller"] = judge("smaller", out["checks"]["scale_smaller"], True, True)
    verdicts["collapse_kw"] = judge("collapse", out["checks"]["collapse_kw"], True, False)
    verdicts["portrait_900"] = judge("portrait", out["checks"]["portrait_900"], True, True, portrait=True)
    verdicts["kontakt_sck"] = judge("kontakt", out["checks"]["kontakt_sck"], True, True)
    out["verdicts"] = {k: {"pass": v[0], "detail": v[1]} for k, v in verdicts.items()}
    out["ok"] = all(v[0] for v in verdicts.values())
except Exception as e:
    out["ok"] = False
    out["err"] = str(e)
finally:
    try:
        proc.terminate()
    except Exception:
        pass
    open(OUT, "w").write(json.dumps(out, indent=2))
    print(json.dumps({k: out.get(k) for k in ("ok", "err", "verdicts")}, indent=2))
    sys.exit(0 if out.get("ok") else 1)
