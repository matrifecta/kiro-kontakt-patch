#!/usr/bin/env python3
"""CDP: preview centering + button overlap sweep (area>1px fail)."""
import base64
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

PHASE = sys.argv[1] if len(sys.argv) > 1 else "after"
OUT = f"/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_preview_overlap_{PHASE}.json"
SHOT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots"
PORT = 9521
HTTP_PORT = 8797
PROFILE = f"/tmp/catalog-preview-overlap-{PHASE}"
os.makedirs(SHOT, exist_ok=True)
os.makedirs(PROFILE, exist_ok=True)

MEASURE = r"""
(() => {
  var SKIP_ID = /^(searchSplit|searchHeight|kwShadeHeight|acHeight|acWidth|dualFsSep|acScrollStripe)$/;
  var SKIP_CLS = /(card-search-row|card-search-tile|ac-height|search-height|search-split|kw-shade-height|ac-width|ac-scroll)/;
  function vis(el){
    if(!el || el.hidden) return false;
    var r=el.getBoundingClientRect();
    if(r.width<2||r.height<2) return false;
    if(r.right<=1||r.bottom<=1||r.left>=innerWidth-1||r.top>=innerHeight-1) return false;
    var p=el;
    while(p && p.nodeType===1){
      if(p.hidden) return false;
      var c=getComputedStyle(p);
      if(c.display==='none'||c.visibility==='hidden'||c.opacity==='0') return false;
      p=p.parentElement;
    }
    var cs=getComputedStyle(el);
    if(cs.pointerEvents==='none') return false;
    return true;
  }
  function label(el){
    var id=el.id||'';
    var al=(el.getAttribute('aria-label')||'').trim();
    var cls=(el.className||'').toString().trim().split(/\s+/).slice(0,3).join('.');
    return id || al || cls || el.tagName;
  }
  function box(el){
    var r=el.getBoundingClientRect();
    return {n:label(el), t:r.top, l:r.left, b:r.bottom, r:r.right, w:r.width, h:r.height, pos:getComputedStyle(el).position};
  }
  function area(a,b){
    var ix=Math.max(0, Math.min(a.r,b.r)-Math.max(a.l,b.l));
    var iy=Math.max(0, Math.min(a.b,b.b)-Math.max(a.t,b.t));
    return ix*iy;
  }
  var sel='button, [role=button], select.theme-picker, .preview-back, .fav-btn, .fs-btn, .hl-min, .hl-close, .note-balloon';
  var nodes=[].slice.call(document.querySelectorAll(sel));
  var seen=new Set(), btns=[];
  nodes.forEach(function(el){
    if(seen.has(el)) return;
    seen.add(el);
    if(SKIP_ID.test(el.id||'')) return;
    if(SKIP_CLS.test((el.className||'').toString())) return;
    if(!vis(el)) return;
    btns.push(el);
  });
  var hits=[];
  for(var i=0;i<btns.length;i++){
    for(var j=i+1;j<btns.length;j++){
      if(btns[i].contains(btns[j])||btns[j].contains(btns[i])) continue;
      var A=box(btns[i]), B=box(btns[j]);
      var ar=area(A,B);
      if(ar>1) hits.push({
        a:A.n, b:B.n, area:Math.round(ar),
        aPos:A.pos, bPos:B.pos,
        at:{t:Math.round(A.t),l:Math.round(A.l),w:Math.round(A.w),h:Math.round(A.h)},
        bt:{t:Math.round(B.t),l:Math.round(B.l),w:Math.round(B.w),h:Math.round(B.h)}
      });
    }
  }
  var card=document.querySelector('.entry.highlight') || document.querySelector('body.chosen-preview-open .entry.selected') || document.querySelector('.entry.selected');
  var cr=card && card.getBoundingClientRect();
  var preview=null;
  if(cr && (document.body.classList.contains('chosen-preview-open')||document.body.classList.contains('hl-open'))){
    var ccx=cr.left+cr.width/2, ccy=cr.top+cr.height/2;
    function btnInfo(sel){
      var el=card.querySelector(sel) || document.querySelector(sel);
      if(!el||!vis(el)) return null;
      var r=el.getBoundingClientRect();
      return {
        n:sel, t:Math.round(r.top), l:Math.round(r.left),
        dt:Math.round(r.top-cr.top), dl:Math.round(r.left-cr.left),
        pos:getComputedStyle(el).position, w:Math.round(r.width), h:Math.round(r.height)
      };
    }
    function hdr(id){
      var el=document.getElementById(id);
      if(!el||!vis(el)) return null;
      var r=el.getBoundingClientRect();
      return {t:Math.round(r.top),l:Math.round(r.left),w:Math.round(r.width),h:Math.round(r.height)};
    }
    preview={
      vw:innerWidth, vh:innerHeight,
      card:{t:Math.round(cr.top),l:Math.round(cr.left),w:Math.round(cr.width),h:Math.round(cr.height),
            cx:Math.round(ccx),cy:Math.round(ccy)},
      dx:Math.round(ccx-(innerWidth/2)), dy:Math.round(ccy-(innerHeight/2)),
      pos:getComputedStyle(card).position,
      back:btnInfo('.preview-back'), fav:btnInfo('.fav-btn'), fs:btnInfo('.fs-btn'),
      min:btnInfo('.hl-min'), close:btnInfo('.hl-close'),
      embedBack:btnInfo('.card-search-back'), embedFs:btnInfo('#cardSearchFsBtn'),
      s:hdr('hdrSearchBtn'), k:hdr('hdrKwBtn'), flip:hdr('portraitFlipBtn'), more:hdr('hdrMoreBtn')
    };
  }
  var hdr=document.querySelector('.catalog-header');
  var main=document.getElementById('catalogMain');
  var tog=document.getElementById('hdrBarToggle');
  var h1=document.getElementById('top');
  var s=document.getElementById('hdrSearchBtn');
  var k=document.getElementById('hdrKwBtn');
  var ix=document.getElementById('catalogIndex');
  function visBox(el){
    if(!el||!vis(el)) return null;
    var r=el.getBoundingClientRect();
    return {t:Math.round(r.top),l:Math.round(r.left),b:Math.round(r.bottom),r:Math.round(r.right),w:Math.round(r.width),h:Math.round(r.height)};
  }
  function ov(a,b){
    if(!a||!b) return 0;
    var x=Math.max(0, Math.min(a.r,b.r)-Math.max(a.l,b.l));
    var y=Math.max(0, Math.min(a.b,b.b)-Math.max(a.t,b.t));
    return x*y;
  }
  var tb=visBox(tog), hb=hdr?hdr.getBoundingClientRect():null, mb=main?main.getBoundingClientRect():null;
  var header={
    hidden: document.body.classList.contains('hdr-bar-hidden'),
    h: hb?Math.round(hb.height):null,
    bottom: hb?Math.round(hb.bottom):null,
    catH: getComputedStyle(document.documentElement).getPropertyValue('--cat-header-h').trim(),
    mainTop: mb?Math.round(mb.top):null,
    tog: tb,
    togCx: tb?Math.round(tb.l+tb.w/2):null,
    h1: visBox(h1),
    s: visBox(s),
    k: visBox(k),
    ix: visBox(ix),
    ovSK: Math.max(ov(tb, visBox(s)), ov(tb, visBox(k))),
    ovH1: ov(tb, visBox(h1)),
    ovIx: ov(tb, visBox(ix)),
    h1Shown: vis(h1),
    sShown: vis(s)
  };
  return {
    vw:innerWidth, vh:innerHeight, title:document.title,
    cls:document.body.className,
    nBtns:btns.length,
    hits:hits.slice(0,40),
    hitCount:hits.length,
    preview:preview,
    header:header
  };
})()
"""


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
        mask = os.urandom(4)
        hdr = bytearray([0x81])
        if flen < 126:
            hdr.append(0x80 | flen)
        elif flen < 65536:
            hdr.append(0x80 | 126)
            hdr.extend(flen.to_bytes(2, "big"))
        else:
            hdr.append(0x80 | 127)
            hdr.extend(flen.to_bytes(8, "big"))
        hdr.extend(mask)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
        self.s.sendall(bytes(hdr) + masked)

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
            if b1 & 0x80:
                off += 4
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


def attach_tab():
    tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list"))
    for t in tabs:
        if t.get("type") == "page" and t.get("webSocketDebuggerUrl"):
            return t
    return json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/new?about:blank"))


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
            {"expression": expr, "returnByValue": True},
        )
        if r.get("exceptionDetails"):
            raise RuntimeError(r["exceptionDetails"])
        return r.get("result", {}).get("value")


def wait_ready(cdp):
    for _ in range(120):
        try:
            n = cdp.eval(
                "!!(document.getElementById('catalogIndex')&&document.querySelectorAll('.entry').length>3)"
            )
        except Exception:
            n = False
        if n:
            return
        time.sleep(0.2)
    raise SystemExit("catalog JS not ready")


def set_view(cdp, w, h, mobile=None):
    if mobile is None:
        mobile = w <= 900 or h <= 900
    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": w,
            "height": h,
            "deviceScaleFactor": 1,
            "mobile": mobile,
            "screenOrientation": {
                "type": "portraitPrimary" if h > w else "landscapePrimary",
                "angle": 0 if h > w else 90,
            },
        },
    )
    time.sleep(0.3)


def shot(cdp, name):
    data = cdp.call("Page.captureScreenshot", {"format": "png"})
    raw = data.get("data")
    if raw:
        Path(SHOT, name).write_bytes(base64.b64decode(raw))


def nav(cdp, url):
    cdp.call("Page.enable")
    cdp.call("Runtime.enable")
    cdp.call("Page.navigate", {"url": url})
    time.sleep(0.6)
    wait_ready(cdp)


def prep(cdp, display="sides"):
    cdp.eval(
        f"""
(() => {{
  try{{localStorage.setItem('catalog-index-embed-'+(window.CATALOG_NS||'catalog'), '0');}}catch(e){{}}
  try{{localStorage.setItem('catalog-doc-note-embed-'+(window.CATALOG_NS||'catalog'), '0');}}catch(e){{}}
  if(typeof closeOverlay==='function') closeOverlay({{skipScroll:true}});
  if(typeof closeChosenPreview==='function') closeChosenPreview({{skipJumpExit:true}});
  if(typeof closeCardSearchEmbed==='function') closeCardSearchEmbed();
  if(typeof toggleHdrBar==='function') toggleHdrBar(false);
  else document.body.classList.remove('hdr-bar-hidden');
  if(typeof setDisplayMode==='function') setDisplayMode({json.dumps(display)},{{pick:true}});
  if(typeof syncHdrBar==='function') syncHdrBar();
}})()
"""
    )
    time.sleep(0.25)


def open_preview(cdp):
    cdp.eval(
        """
(() => {
  var el=document.querySelector('.entry:not(.is-hidden)')||document.querySelector('.entry');
  if(el&&typeof openChosenPreview==='function') openChosenPreview(el);
})()
"""
    )
    time.sleep(0.35)


def open_embed(cdp):
    cdp.eval(
        """
(() => {
  var el=document.querySelector('.entry.selected')||document.querySelector('.entry:not(.is-hidden)')||document.querySelector('.entry');
  if(el&&typeof openChosenPreview==='function') openChosenPreview(el);
  if(typeof openCardSearchEmbed==='function') openCardSearchEmbed('web','https://example.com/search?q=kontakt');
})()
"""
    )
    time.sleep(0.4)


def open_hl(cdp):
    cdp.eval(
        """
(() => {
  if(typeof closeCardSearchEmbed==='function') closeCardSearchEmbed();
  if(typeof closeChosenPreview==='function') closeChosenPreview({skipJumpExit:true});
  var el=document.querySelector('.entry:not(.is-hidden)')||document.querySelector('.entry');
  if(el&&typeof openOverlay==='function') openOverlay(el);
})()
"""
    )
    time.sleep(0.35)


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


DOCK = {"catalogDocNoteToggle", "catalogDocNoteEmbed"}
DOCK_CHROME = {
    "catalogIndexToggle",
    "catalogIndexEmbed",
    "hdrSearchBtn",
    "hdrKwBtn",
    "hdrBarToggle",
    "portraitFlipBtn",
    "hdrMoreBtn",
    "hdrToolbarFs",
}


def real_hits(st):
    out = []
    for h in st.get("hits") or []:
        names = {h.get("a") or "", h.get("b") or ""}
        if names & DOCK:
            other = next(iter(names - DOCK), "")
            if other in DOCK or other in DOCK_CHROME:
                out.append(h)
            continue
        combo = " ".join(names)
        cls = st.get("cls") or ""
        if "catalogIndex" in combo and (
            "chosen-preview-open" in cls or "card-embed-open" in cls or "hl-open" in cls
        ):
            continue
        out.append(h)
    return out


def judge(name, st, errors, *, want_center=False):
    if not st:
        errors.append(name + ": no state")
        return
    hits = real_hits(st)
    if hits:
        pair = ",".join(f"{h.get('a')}×{h.get('b')}" for h in hits[:4])
        errors.append(f"{name}: {len(hits)} overlap(s) {pair}")
    hdr = st.get("header") or {}
    tog = hdr.get("tog")
    if not tog:
        if "hl-open" not in (st.get("cls") or ""):
            errors.append(name + ": hdrBarToggle missing/hidden")
    else:
        vw = st.get("vw") or 0
        if abs((hdr.get("togCx") or 0) - vw / 2) > 24:
            errors.append(f"{name}: pyramid not screen-centered cx={hdr.get('togCx')} vw={vw}")
        if (hdr.get("ovSK") or 0) > 1:
            errors.append(f"{name}: pyramid overlaps S/K area={hdr.get('ovSK')}")
        if (hdr.get("ovH1") or 0) > 1:
            errors.append(f"{name}: pyramid overlaps title area={hdr.get('ovH1')}")
        if (hdr.get("ovIx") or 0) > 1:
            errors.append(f"{name}: pyramid overlaps Index area={hdr.get('ovIx')}")
    if want_center:
        pv = st.get("preview") or {}
        card = pv.get("card") or {}
        if not card:
            errors.append(name + ": no preview card")
            return
        hb = (st.get("header") or {}).get("bottom") or 0
        vh = st.get("vh") or 0
        mid_y = hb + max(0, vh - hb) / 2.0
        cy = card.get("cy")
        if cy is None:
            errors.append(name + ": no card cy")
        elif abs(cy - mid_y) > 48:
            errors.append(
                f"{name}: center dx={pv.get('dx')} cy={cy} mid={round(mid_y)} hdrBottom={hb} card={card}"
            )
            errors.append(f"{name}: center dx={pv.get('dx')} dy={pv.get('dy')} card={card}")
        for key in ("back", "fav", "fs", "min"):
            b = pv.get(key)
            if not b:
                continue
            if b.get("dt") is None:
                continue
            if b["dt"] < -2 or b["dt"] > 28:
                errors.append(f"{name}: {key} dt={b.get('dt')} from card top (want inset)")
            if b.get("pos") == "fixed":
                errors.append(f"{name}: {key} position=fixed (want on card)")


def judge_hide(name, shown, hidden, errors):
    hs = shown.get("header") or {}
    hh = hidden.get("header") or {}
    if not hh.get("hidden"):
        errors.append(name + ": body not hdr-bar-hidden")
    if hh.get("h1Shown") or hh.get("sShown"):
        errors.append(name + ": title/S still visible while header hidden")
    sh, hd = hs.get("h") or 0, hh.get("h") or 0
    if hd >= max(sh - 8, sh * 0.75):
        errors.append(f"{name}: header did not shrink shown={sh} hidden={hd}")
    mt0, mt1 = hs.get("mainTop"), hh.get("mainTop")
    if mt0 is not None and mt1 is not None and mt1 > mt0 - 4:
        errors.append(f"{name}: content top did not move up {mt0}->{mt1}")
    tog = hh.get("tog") or {}
    if not tog.get("w"):
        errors.append(name + ": restore pyramid missing")


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
    logf = open(f"/tmp/catalog-preview-overlap-{PHASE}.log", "w")
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
    for _ in range(80):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=1).read()
            break
        except Exception:
            time.sleep(0.2)
    else:
        json.dump({"err": "cdp"}, open(OUT, "w"))
        sys.exit(1)

    results = {}
    errors = []
    try:
        tab = attach_tab()
        cdp = CDP(tab["webSocketDebuggerUrl"])
        cases = [
            ("K390", "KONTAKT-CATALOG-portable.html", 390, 844, True),
            ("K844", "KONTAKT-CATALOG-portable.html", 844, 390, True),
            ("DS390", "DS-CATALOG-portable.html", 390, 844, True),
            ("DS844", "DS-CATALOG-portable.html", 844, 390, True),
            ("K1400", "KONTAKT-CATALOG.html", 1400, 900, False),
            ("K900", "KONTAKT-CATALOG.html", 900, 1400, False),
            ("DS1400", "DS-CATALOG.html", 1400, 900, False),
            ("DS900", "DS-CATALOG.html", 900, 1400, False),
        ]
        last_page = None
        for tag, page, w, h, portable in cases:
            if page != last_page:
                nav(cdp, f"http://127.0.0.1:{HTTP_PORT}/{page}?v=ov-{PHASE}")
                last_page = page
            set_view(cdp, w, h, mobile=portable)

            for disp in ("sides",) if tag not in ("K390", "K1400") else ("upper", "sides", "middle", "fs"):
                if disp != "sides" and tag in ("K390", "K1400"):
                    prep(cdp, display=disp)
                    st = cdp.eval(MEASURE)
                    results[f"{tag}-{disp}-default"] = st
                    judge(f"{tag}-{disp}-default", st, errors)
                    continue
                prep(cdp, display="sides")
                st = cdp.eval(MEASURE)
                results[f"{tag}-default"] = st
                shot(cdp, f"{tag}-{PHASE}-default.png")
                judge(f"{tag}-default", st, errors)

                cdp.eval("if(typeof toggleHdrBar==='function') toggleHdrBar(true);")
                time.sleep(0.25)
                hid = cdp.eval(MEASURE)
                results[f"{tag}-hdr-hide"] = hid
                shot(cdp, f"{tag}-{PHASE}-hdr-hide.png")
                judge(f"{tag}-hdr-hide", hid, errors)
                judge_hide(f"{tag}-hdr-hide", st, hid, errors)
                cdp.eval("if(typeof toggleHdrBar==='function') toggleHdrBar(false);")
                time.sleep(0.25)
                shown = cdp.eval(MEASURE)
                results[f"{tag}-hdr-show"] = shown
                judge(f"{tag}-hdr-show", shown, errors)
                if (shown.get("header") or {}).get("hidden"):
                    errors.append(f"{tag}-hdr-show: still hidden")
                elif ((shown.get("header") or {}).get("h") or 0) + 8 < ((st.get("header") or {}).get("h") or 0):
                    errors.append(
                        f"{tag}-hdr-show: height not restored "
                        f"{(shown.get('header') or {}).get('h')} vs {(st.get('header') or {}).get('h')}"
                    )

                open_preview(cdp)
                st = cdp.eval(MEASURE)
                results[f"{tag}-preview"] = st
                shot(cdp, f"{tag}-{PHASE}-preview.png")
                judge(f"{tag}-preview", st, errors, want_center=True)

                open_embed(cdp)
                st = cdp.eval(MEASURE)
                results[f"{tag}-embed"] = st
                shot(cdp, f"{tag}-{PHASE}-embed.png")
                judge(f"{tag}-embed", st, errors, want_center=True)

                open_hl(cdp)
                st = cdp.eval(MEASURE)
                results[f"{tag}-hl"] = st
                shot(cdp, f"{tag}-{PHASE}-hl.png")
                judge(f"{tag}-hl", st, errors)
                prep(cdp, display="sides")

        out = {"phase": PHASE, "errors": errors, "results": results, "ok": not errors}
        json.dump(out, open(OUT, "w"), indent=2)
        print("phase", PHASE, "errors", len(errors))
        for e in errors[:40]:
            print(" -", e)
        if len(errors) > 40:
            print(" ...", len(errors) - 40, "more")
        if PHASE == "after" and errors:
            sys.exit(1)
    finally:
        proc.terminate()


if __name__ == "__main__":
    main()
