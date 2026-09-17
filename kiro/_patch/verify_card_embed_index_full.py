#!/usr/bin/env python3
"""CDP: card/embed unmix, chrome top row, Embed Index full height."""
import http.server
import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_card_embed_index_full.json")
PORT = 9571
HTTP = 8797
ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
PROFILE = "/tmp/catalog-card-embed-index-full"
os.makedirs(PROFILE, exist_ok=True)

KEEP = (
    "c00e3e",
    "fix-PORTABLE-FS-FLIP-INDEX-v1",
    "fix-CARD-FS-EMBED-SCROLL-v1",
    "fix-CARD-EMBED-SEPARATE-v1",
    "fix-CARD-CHROME-TOP-v1",
    "fix-INDEX-EMBED-FULL-v1",
    "fix-INDEX-EMBED-FULL-v2",
    "fix-INDEX-EMBED-FULL-v3",
)
FILES = [
    ROOT / "KONTAKT-CATALOG.html",
    ROOT / "DS-CATALOG.html",
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]


def integrity():
    rows = []
    ok = True
    for p in FILES:
        t = p.read_text(encoding="utf-8")
        row = {"file": p.name, "endswith": t.strip().endswith("</html>"), "size": len(t.encode("utf-8"))}
        for k in KEEP:
            row[k] = k in t
            if k not in t:
                ok = False
        if not row["endswith"] or row["size"] < 100000:
            ok = False
        rows.append(row)
    return {"ok": ok, "files": rows}


def ensure_http():
    url = f"http://127.0.0.1:{HTTP}/DS-CATALOG.html"
    try:
        urllib.request.urlopen(url, timeout=1).read(64)
        return None
    except Exception:
        pass
    os.chdir(ROOT)

    class H(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", HTTP), H)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    for _ in range(40):
        try:
            urllib.request.urlopen(url, timeout=1).read(64)
            return httpd
        except Exception:
            time.sleep(0.1)
    raise SystemExit("http 8797 failed")


class Ws:
    def __init__(self, url):
        u = urlparse(url)
        host, port = u.hostname, u.port or 80
        path = u.path + (("?" + u.query) if u.query else "")
        key = __import__("base64").b64encode(os.urandom(16)).decode()
        s = socket.create_connection((host, port), timeout=30)
        s.settimeout(120)
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

    def eval(self, expr, await_promise=False):
        r = self.call(
            "Runtime.evaluate",
            {"expression": expr, "awaitPromise": await_promise, "returnByValue": True},
        )
        if r.get("exceptionDetails"):
            raise RuntimeError(r["exceptionDetails"])
        return r.get("result", {}).get("value")


def wait_entries(cdp, nmin=4):
    for _ in range(80):
        try:
            n = cdp.eval("document.querySelectorAll('.entry').length")
        except Exception:
            n = 0
        if n and n >= nmin:
            return n
        time.sleep(0.25)
    return 0


def nav(cdp, url):
    cdp.call("Page.navigate", {"url": url})
    for _ in range(80):
        try:
            n = cdp.eval("document.querySelectorAll('.entry').length")
        except Exception:
            n = 0
        if n and n > 3:
            return n
        time.sleep(0.25)
    return 0


def set_view(cdp, w, h, mobile=False):
    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {"width": w, "height": h, "deviceScaleFactor": 1 if not mobile else 2, "mobile": mobile},
    )


JS_CARD = r"""
(() => {
  function vis(n){
    if(!n)return {on:false};
    var r=n.getBoundingClientRect(), cs=getComputedStyle(n);
    return {on:cs.display!=='none'&&cs.visibility!=='hidden'&&r.width>1&&r.height>1,d:cs.display,t:Math.round(r.top),b:Math.round(r.bottom),l:Math.round(r.left),r:Math.round(r.right),w:Math.round(r.width),h:Math.round(r.height)};
  }
  function overlap(a,b){
    if(!a||!b||!a.on||!b.on)return false;
    return !(a.r<=b.l||b.r<=a.l||a.b<=b.t||b.b<=a.t);
  }
  var entry=document.querySelector('.entry');
  if(!entry)return {err:'no-entry'};
  if(typeof openChosenPreview==='function')openChosenPreview(entry);
  var card=document.querySelector('.entry.selected')||entry;
  var cover=vis(card.querySelector('.cover'));
  var path=vis(card.querySelector('.path'));
  var name=vis(card.querySelector('.lib-name'));
  var embed=document.getElementById('cardSearchEmbed');
  var preview={
    preview:document.body.classList.contains('chosen-preview-open'),
    embed:document.body.classList.contains('card-embed-open'),
    cover:cover, path:path, name:name,
    embedOn:vis(embed).on && !embed.hidden,
    iframe:!!document.querySelector('#cardSearchEmbed iframe')
  };
  var btns=[].slice.call(card.querySelectorAll('.preview-back,.fav-btn,.fs-btn,.hl-min,.hl-close')).filter(function(b){
    var v=vis(b); return v.on;
  }).map(vis);
  var cr=card.getBoundingClientRect();
  var chromeH=Math.round((parseFloat(getComputedStyle(card).paddingTop)||0));
  var rowY=btns.map(function(b){return b.t;});
  var sameRow=btns.length<2||(Math.max.apply(null,rowY)-Math.min.apply(null,rowY))<=12;
  var inTop=btns.every(function(b){return b.t>=cr.top-2 && b.t<=cr.top+chromeH+8;});
  var hdr=vis(document.getElementById('hdrSearchBtn'));
  var title=vis(document.querySelector('h1#top'));
  var overlapHdr=btns.some(function(b){return overlap(b,hdr)||overlap(b,title);});
  var overlapEach=false;
  for(var i=0;i<btns.length;i++){
    for(var j=i+1;j<btns.length;j++){
      var A=btns[i],B=btns[j];
      if(!(A.r<=B.l+1||B.r<=A.l+1||A.b<=B.t+1||B.b<=A.t+1))overlapEach=true;
    }
  }
  var coverBelow=(!cover.on)||cover.t>=(btns.length?Math.max.apply(null,btns.map(function(b){return b.b;})):cr.top)-2;
  var chrome={
    n:btns.length, sameRow:sameRow, inTop:inTop, overlapHdr:overlapHdr, overlapEach:overlapEach,
    coverBelow:coverBelow, cardTop:Math.round(cr.top), chromeH:chromeH, btnTops:rowY, hdr:hdr
  };
  var opened=false;
  try{
    var btn=entry.querySelector('.search-popup-btn,.search-link');
    if(btn&&typeof openCardSearchEmbed==='function'){
      opened=!!openCardSearchEmbed('web', btn.getAttribute('data-web')||'https://www.google.com/search?q=test');
    }
  }catch(eOpen){}
  var embedOpen={
    opened:opened,
    embed:document.body.classList.contains('card-embed-open'),
    preview:document.body.classList.contains('chosen-preview-open'),
    cover:vis(card.querySelector('.cover')),
    path:vis(card.querySelector('.path')),
    name:vis(card.querySelector('.lib-name')),
    patches:vis(card.querySelector('details.patches,.patches')),
    embedOn:vis(document.getElementById('cardSearchEmbed')),
    hostHid:!!(document.getElementById('cardSearchEmbed')&&document.getElementById('cardSearchEmbed').hidden)
  };
  if(typeof cardSearchBack==='function')cardSearchBack();
  var afterBack={
    embed:document.body.classList.contains('card-embed-open'),
    preview:document.body.classList.contains('chosen-preview-open'),
    cover:vis(card.querySelector('.cover')),
    path:vis(card.querySelector('.path')),
    hostHid:!!(document.getElementById('cardSearchEmbed')&&document.getElementById('cardSearchEmbed').hidden)
  };
  if(typeof closeChosenPreview==='function')closeChosenPreview({skipJumpExit:true});
  if(typeof openOverlay==='function')openOverlay(entry);
  var hlCard=document.querySelector('.entry.highlight')||entry;
  var hlBtns=[].slice.call(hlCard.querySelectorAll('.fav-btn,.hl-min,.hl-close')).filter(function(b){return vis(b).on;}).map(vis);
  var hlr=hlCard.getBoundingClientRect();
  var hlCover=vis(hlCard.querySelector('.cover'));
  var hlRow=hlBtns.length<2||(Math.max.apply(null,hlBtns.map(function(b){return b.t;}))-Math.min.apply(null,hlBtns.map(function(b){return b.t;})))<=12;
  var hlCoverBelow=(!hlCover.on)||!hlBtns.length||hlCover.t>=Math.max.apply(null,hlBtns.map(function(b){return b.b;}))-2;
  var cs=getComputedStyle(hlCard);
  var y0=hlCard.scrollTop;
  var pad=document.createElement('div');
  pad.style.cssText='height:80vh;flex:0 0 auto;pointer-events:none;opacity:0';
  (hlCard.querySelector('.hl-body')||hlCard).appendChild(pad);
  hlCard.scrollTop=y0+80;
  var y1=hlCard.scrollTop;
  pad.remove();
  var hl={
    hl:document.body.classList.contains('hl-open'),
    n:hlBtns.length, sameRow:hlRow, coverBelow:hlCoverBelow,
    ovY:cs.overflowY, can:hlCard.scrollHeight>hlCard.clientHeight+2, moved:Math.abs(y1-y0)>2
  };
  if(typeof closeOverlay==='function')closeOverlay();
  return {preview:preview, chrome:chrome, embedOpen:embedOpen, afterBack:afterBack, hl:hl};
})()
"""

JS_INDEX = r"""
(() => {
  function vis(n){
    if(!n)return false;
    var r=n.getBoundingClientRect(), cs=getComputedStyle(n);
    return cs.display!=='none'&&cs.visibility!=='hidden'&&r.width>1&&r.height>1;
  }
  if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
  var ix=document.getElementById('catalogIndex');
  if(!ix)return {err:'no-index'};
  if(!ix.classList.contains('is-embedded')&&typeof toggleIndexEmbed==='function')toggleIndexEmbed();
  if(ix.classList.contains('is-collapsed')&&typeof toggleCatalogIndex==='function')toggleCatalogIndex();
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  if(typeof syncIndexEmbedFull==='function')syncIndexEmbedFull();
  var il=document.getElementById('catalogIndexList')||ix.querySelector('ul.index');
  var cb=document.querySelector('#catalogMain > .catalog-body');
  var main=document.getElementById('catalogMain');
  var names=il?il.querySelectorAll('li a[href^="#"]').length:0;
  var icons=ix.querySelectorAll('.path-icon-btn,.path-action-row,svg.path-icon-glyph,img.path-icon-glyph,a.folder:not([href^="#"])');
  var iconVis=[].filter.call(icons,vis).length;
  var ixCs=getComputedStyle(ix);
  var ilCs=il?getComputedStyle(il):null;
  var jump=document.getElementById('catalogJumpStack');
  var bg=ixCs.backgroundColor||'';
  var opaque=/rgba?\(/.test(bg)?!/^rgba?\(\s*0\s*,\s*0\s*,\s*0\s*,\s*0/.test(bg):bg!=='transparent';
  var ixOvSnap=ixCs.overflowY, ilOvSnap=ilCs?ilCs.overflowY:null;
  var ixHSnap=ix.scrollHeight, ixChSnap=ix.clientHeight;
  var ilHSnap=il?il.scrollHeight:0, ilChSnap=il?il.clientHeight:0;
  var innerScroll=(ixOvSnap==='auto'||ixOvSnap==='scroll')&&ixHSnap>ixChSnap+8;
  var listInner=!!(ilOvSnap&&(ilOvSnap==='auto'||ilOvSnap==='scroll')&&ilHSnap>ilChSnap+8);
  var jumpOn=!!(jump&&vis(jump));
  var pane=cb||main;
  var bodyTall=!!(cb&&cb.scrollHeight>cb.clientHeight+40);
  var mainTall=!!(main&&main.scrollHeight>main.clientHeight+40);
  var ixSt0=ix.scrollTop, ilSt0=il?il.scrollTop:0, b0=cb?cb.scrollTop:0, m0=main?main.scrollTop:0;
  var a=il&&il.querySelector('li a');
  if(a){
    var ev=new WheelEvent('wheel',{deltaY:240,deltaMode:0,bubbles:true,cancelable:true});
    a.dispatchEvent(ev);
  }
  var wheel={
    ixMoved:Math.abs(ix.scrollTop-ixSt0)>2,
    ilMoved:Math.abs((il?il.scrollTop:0)-ilSt0)>2,
    bodyMoved:Math.abs((cb?cb.scrollTop:0)-b0)>2,
    mainMoved:Math.abs((main?main.scrollTop:0)-m0)>2
  };
  if(ix)ix.scrollTop=ixSt0;
  if(il)il.scrollTop=ilSt0;
  if(cb)cb.scrollTop=b0;
  if(main)main.scrollTop=m0;
  var win={};
  if(typeof toggleIndexEmbed==='function'&&ix.classList.contains('is-embedded'))toggleIndexEmbed();
  if(ix.classList.contains('is-collapsed')&&typeof toggleCatalogIndex==='function')toggleCatalogIndex();
  document.body.classList.add('index-window-open');
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  var wix=document.getElementById('catalogIndex');
  var wil=document.getElementById('catalogIndexList');
  var wcs=wix?getComputedStyle(wix):null;
  var wlcs=wil?getComputedStyle(wil):null;
  win={
    embedded:!!(wix&&wix.classList.contains('is-embedded')),
    collapsed:!!(wix&&wix.classList.contains('is-collapsed')),
    ixOv:wcs?wcs.overflowY:null,
    ilOv:wlcs?wlcs.overflowY:null,
    ilCan:!!(wil&&wil.scrollHeight>wil.clientHeight+8),
    inner:(wlcs&&(wlcs.overflowY==='auto'||wlcs.overflowY==='scroll'))
  };
  return {
    names:names, iconVis:iconVis, icons:icons.length,
    ixOv:ixOvSnap, ilOv:ilOvSnap,
    ixH:ixHSnap, ixCh:ixChSnap,
    ilH:ilHSnap, ilCh:ilChSnap,
    innerScroll:innerScroll, listInner:listInner,
    bodyTall:bodyTall, mainTall:mainTall,
    opaque:opaque, bg:bg.slice(0,48),
    jumpOn:jumpOn,
    wheel:wheel, win:win
  };
})()
"""


def judge_card(rep, prefix):
    errs = []
    if not rep or rep.get("err"):
        return [f"{prefix}: {rep}"]
    prev = rep.get("preview") or {}
    if not prev.get("preview"):
        errs.append(f"{prefix}.preview not open")
    if prev.get("embed"):
        errs.append(f"{prefix}.preview mixed embed class")
    if not (prev.get("cover") or {}).get("on"):
        errs.append(f"{prefix}.preview cover hidden")
    if prev.get("embedOn"):
        errs.append(f"{prefix}.preview embed visible")
    ch = rep.get("chrome") or {}
    if not ch.get("sameRow"):
        errs.append(f"{prefix}.chrome not same row {ch.get('btnTops')}")
    if not ch.get("inTop"):
        errs.append(f"{prefix}.chrome not on card top")
    if ch.get("overlapHdr"):
        errs.append(f"{prefix}.chrome overlaps header")
    if ch.get("overlapEach"):
        errs.append(f"{prefix}.chrome overlap each other")
    if not ch.get("coverBelow"):
        errs.append(f"{prefix}.cover under chrome")
    em = rep.get("embedOpen") or {}
    if not em.get("embed"):
        errs.append(f"{prefix}.embed did not open")
    if (em.get("cover") or {}).get("on"):
        errs.append(f"{prefix}.embed cover still visible")
    if (em.get("path") or {}).get("on"):
        errs.append(f"{prefix}.embed path still visible")
    if not (em.get("embedOn") or {}).get("on"):
        errs.append(f"{prefix}.embed host not visible")
    ab = rep.get("afterBack") or {}
    if ab.get("embed"):
        errs.append(f"{prefix}.back left embed open")
    if not ab.get("preview"):
        errs.append(f"{prefix}.back lost preview")
    if not (ab.get("cover") or {}).get("on"):
        errs.append(f"{prefix}.back cover hidden")
    hl = rep.get("hl") or {}
    if not hl.get("hl"):
        errs.append(f"{prefix}.hl not open")
    if not hl.get("sameRow"):
        errs.append(f"{prefix}.hl chrome not same row")
    if not hl.get("coverBelow"):
        errs.append(f"{prefix}.hl cover under chrome")
    if hl.get("ovY") not in ("auto", "scroll"):
        errs.append(f"{prefix}.hl ovY={hl.get('ovY')}")
    return errs


def judge_index(rep, prefix):
    errs = []
    if not rep or rep.get("err"):
        return [f"{prefix}: {rep}"]
    if not (rep.get("names") or 0) >= 20:
        errs.append(f"{prefix}.names={rep.get('names')}")
    if rep.get("iconVis"):
        errs.append(f"{prefix}.path icons visible {rep.get('iconVis')}")
    if rep.get("innerScroll") or rep.get("listInner"):
        errs.append(f"{prefix}.inner scroller still on ixOv={rep.get('ixOv')} ilOv={rep.get('ilOv')}")
    if not (rep.get("bodyTall") or rep.get("mainTall")):
        errs.append(f"{prefix}.catalog pane not taller than index")
    if not (rep.get("ixOv") in ("visible", "hidden", "clip") or (rep.get("ixH") <= (rep.get("ixCh") or 0) + 8)):
        pass
    if not rep.get("opaque"):
        errs.append(f"{prefix}.bg not opaque {rep.get('bg')}")
    wh = rep.get("wheel") or {}
    if wh.get("ixMoved") or wh.get("ilMoved"):
        errs.append(f"{prefix}.wheel moved inner index {wh}")
    if not (wh.get("bodyMoved") or wh.get("mainMoved")):
        errs.append(f"{prefix}.wheel did not move catalog {wh}")
    win = rep.get("win") or {}
    if win.get("embedded"):
        errs.append(f"{prefix}.window still embedded")
    if not (win.get("inner") or win.get("ilCan")):
        errs.append(f"{prefix}.window missing inner scroll {win}")
    return errs


def main():
    integ = integrity()
    ensure_http()
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
    logf = open("/tmp/catalog-card-embed-index-full.log", "w")
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
    out = {"ok": True, "integrity": integ, "errors": []}
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

        set_view(cdp, 1400, 900, False)
        nav(cdp, f"http://127.0.0.1:{HTTP}/DS-CATALOG.html?v=ixfull3")
        wait_entries(cdp, 20)
        ds_ix = cdp.eval(JS_INDEX)
        out["dsIndex"] = ds_ix
        out["errors"].extend(judge_index(ds_ix, "DS-desk-index"))

        nav(cdp, f"http://127.0.0.1:{HTTP}/DS-CATALOG.html?v=card1")
        wait_entries(cdp, 8)
        ds_card = cdp.eval(JS_CARD)
        out["dsCard"] = ds_card
        out["errors"].extend(judge_card(ds_card, "DS-desk-card"))

        nav(cdp, f"http://127.0.0.1:{HTTP}/KONTAKT-CATALOG.html?v=card2")
        wait_entries(cdp, 8)
        kt_card = cdp.eval(JS_CARD)
        out["ktCard"] = kt_card
        out["errors"].extend(judge_card(kt_card, "KT-desk-card"))

        set_view(cdp, 390, 844, True)
        nav(cdp, f"http://127.0.0.1:{HTTP}/KONTAKT-CATALOG-portable.html?v=port")
        wait_entries(cdp, 8)
        port_card = cdp.eval(JS_CARD)
        out["portCard"] = port_card
        out["errors"].extend(judge_card(port_card, "KT-port-card"))

        set_view(cdp, 390, 844, True)
        nav(cdp, f"http://127.0.0.1:{HTTP}/DS-CATALOG-portable.html?v=portix3")
        wait_entries(cdp, 8)
        port_ix = cdp.eval(JS_INDEX)
        out["portIndex"] = port_ix
        out["errors"].extend(judge_index(port_ix, "DS-port-index"))

        if not integ.get("ok"):
            out["errors"].append("integrity")
        out["ok"] = len(out["errors"]) == 0
    except Exception as e:
        out["ok"] = False
        out["errors"].append(str(e))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
    OUT.write_text(json.dumps(out, indent=2))
    print(json.dumps({"ok": out.get("ok"), "errors": out.get("errors"), "integrity": integ}, indent=2)[:8000])
    sys.exit(0 if out.get("ok") else 1)


if __name__ == "__main__":
    main()
