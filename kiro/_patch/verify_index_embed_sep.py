#!/usr/bin/env python3
"""CDP: expanded Embed Index has 1px line before cards; Window does not."""
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
from pathlib import Path
from urllib.parse import urlparse

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_index_embed_sep.json")
SHOT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots")
PORT = 9583
HTTP = 8797
ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
PROFILE = "/tmp/catalog-ix-embed-sep"
SHOT.mkdir(parents=True, exist_ok=True)
os.makedirs(PROFILE, exist_ok=True)

MARK = "fix-INDEX-EMBED-SEP-v2"
KEEP = (
    "c00e3e",
    "fix-INDEX-EMBED-FULL-v1",
    "fix-INDEX-EMBED-FULL-v2",
    "fix-INDEX-EMBED-FULL-v3",
    MARK,
    "fix-TAP-ADD-REMOVE-v1",
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
        key = base64.b64encode(os.urandom(16)).decode()
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


def shot(cdp, name):
    data = cdp.call("Page.captureScreenshot", {"format": "png"}).get("data", "")
    path = SHOT / name
    path.write_bytes(base64.b64decode(data))
    return str(path)


JS_EMBED = r"""
(() => {
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
  var loc=cb&&cb.querySelector('.loc-group');
  var card=cb&&cb.querySelector('.entry:not(.is-hidden)');
  if(cb)cb.scrollTop=0;
  var ixCs=getComputedStyle(ix);
  var ilCs=il?getComputedStyle(il):null;
  var cbCs=cb?getComputedStyle(cb):null;
  var mainCs=main?getComputedStyle(main):null;
  var last=il&&il.querySelector('li:last-child');
  var after=getComputedStyle(ix,'::after');
  var ir=ix.getBoundingClientRect();
  var lr=il?il.getBoundingClientRect():null;
  var nr=last?last.getBoundingClientRect():null;
  var cr=card?card.getBoundingClientRect():null;
  var locR=loc?loc.getBoundingClientRect():null;
  var gapPx=parseFloat(ixCs.getPropertyValue('--index-embed-gap'))||20;
  var sepY=ir.bottom+(gapPx/2);
  var nameToCard=(cr&&nr)?(cr.top-nr.bottom):null;
  var ixToCard=(cr)?(cr.top-ir.bottom):null;
  var overlap=(cr&&ir)?Math.min(ir.bottom,cr.bottom)-Math.max(ir.top,cr.top):null;
  var padB=ilCs?parseFloat(ilCs.paddingBottom)||0:0;
  var ixOv=ixCs.overflowY, ilOv=ilCs?ilCs.overflowY:'';
  var inner=(ixOv==='auto'||ixOv==='scroll')&&ix.scrollHeight>ix.clientHeight+8;
  var listInner=!!(il&&(ilOv==='auto'||ilOv==='scroll')&&il.scrollHeight>il.clientHeight+8);
  var bodyScroll=!!(cb&&(cbCs.overflowY==='auto'||cbCs.overflowY==='scroll')&&cb.scrollHeight>cb.clientHeight+8);
  var cardBelow=!!(cr&&ir&&cr.top>=ir.bottom+(gapPx/2)-2);
  if(cb){
    var vis=cb.clientHeight||Math.round(cb.getBoundingClientRect().height)||400;
    cb.scrollTop=Math.max(0, ix.offsetTop+ix.offsetHeight-Math.round(vis*0.42));
  }
  return {
    embedded:ix.classList.contains('is-embedded'),
    collapsed:ix.classList.contains('is-collapsed'),
    parent:(ix.parentElement&&(ix.parentElement.className||ix.parentElement.id||'')).toString().slice(0,40),
    inBody:!!(cb&&cb.contains(ix)),
    pos:ixCs.position,
    gridCol:ixCs.gridColumnStart+'/'+ixCs.gridColumnEnd,
    bodyCols:cbCs?cbCs.gridTemplateColumns:'',
    afterContent:(after&&after.content)||'',
    afterBottom:(after&&after.bottom)||'',
    afterBorder:(after&&after.borderBottomWidth)||'',
    borderBottom:ilCs?ilCs.borderBottomWidth:'',
    ixBorderBottom:ixCs.borderBottomWidth,
    padB:Math.round(padB),
    marginB:Math.round(parseFloat(ixCs.marginBottom)||0),
    gapPx:gapPx,
    ixOv:ixOv, ilOv:ilOv,
    inner:inner, listInner:listInner,
    bodyScroll:bodyScroll,
    bodyOv:cbCs?cbCs.overflowY:'',
    mainOv:mainCs?mainCs.overflowY:'',
    ixH:ix.scrollHeight, ixCh:ix.clientHeight,
    ilH:il?il.scrollHeight:0, ilCh:il?il.clientHeight:0,
    ixOffsetH:ix.offsetHeight,
    lastNameH:last?Math.round(last.getBoundingClientRect().height):null,
    names:il?il.querySelectorAll('li').length:0,
    cardBelow:cardBelow,
    gap:nameToCard!=null?Math.round(nameToCard):null,
    ixToCard:ixToCard!=null?Math.round(ixToCard):null,
    overlap:overlap!=null?Math.round(overlap):null,
    sepY:Math.round(sepY),
    listBottom:lr?Math.round(lr.bottom):null,
    nameBottom:nr?Math.round(nr.bottom):null,
    ixBottom:Math.round(ir.bottom),
    bodyDisp:cbCs?cbCs.display:'',
    bodyGap:cbCs?cbCs.rowGap||cbCs.gap:'',
    locGap:locR?Math.round(locR.top-ir.bottom):null,
    locTop:locR?Math.round(locR.top):null,
    cardTop:cr?Math.round(cr.top):null,
    lastBelowIx:nr?Math.round(nr.bottom-ir.bottom):null
  };
})()
"""

JS_WIN = r"""
(() => {
  var ix=document.getElementById('catalogIndex');
  if(!ix)return {err:'no-index'};
  if(ix.classList.contains('is-embedded')&&typeof toggleIndexEmbed==='function')toggleIndexEmbed();
  if(ix.classList.contains('is-collapsed')&&typeof toggleCatalogIndex==='function')toggleCatalogIndex();
  document.body.classList.add('index-window-open');
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  var cb=document.querySelector('#catalogMain > .catalog-body');
  var card=document.querySelector('#catalogMain .catalog-body .entry');
  var cs=getComputedStyle(ix);
  var ir=ix.getBoundingClientRect();
  var cr=card?card.getBoundingClientRect():null;
  var pos=cs.position;
  var inFlow=pos==='static'||pos==='relative';
  var overlay=pos==='absolute'||pos==='fixed';
  var coversCards=!!(cr&&ir&&ir.top<=cr.top+8&&ir.bottom>cr.top+40);
  return {
    embedded:ix.classList.contains('is-embedded'),
    collapsed:ix.classList.contains('is-collapsed'),
    pos:pos,
    overlay:overlay,
    inFlow:inFlow && !overlay,
    inBody:!!(cb&&cb.contains(ix)),
    borderBottom:cs.borderBottomWidth,
    borderTop:cs.borderTopWidth,
    coversCards:coversCards,
    parent:(ix.parentElement&&(ix.parentElement.id||ix.parentElement.className||'')).toString().slice(0,40)
  };
})()
"""


def judge_embed(rep, prefix, expect_names=None):
    errs = []
    if not rep or rep.get("err"):
        return [f"{prefix}: {rep}"]
    if not rep.get("embedded"):
        errs.append(f"{prefix}.not embedded")
    if rep.get("collapsed"):
        errs.append(f"{prefix}.still collapsed")
    if not rep.get("inBody"):
        errs.append(f"{prefix}.not in catalog-body")
    if (rep.get("pos") or "") not in ("relative", "static"):
        errs.append(f"{prefix}.pos={rep.get('pos')}")
    if (rep.get("bodyDisp") or "") != "flex":
        errs.append(f"{prefix}.catalog-body display={rep.get('bodyDisp')}")
    after_b = str(rep.get("afterBorder") or "")
    try:
        if abs(float(str(after_b).replace("px", "") or "0") - 1) > 0.3:
            errs.append(f"{prefix}.sep line {after_b}")
    except Exception:
        errs.append(f"{prefix}.sep line {after_b}")
    bb = str(rep.get("borderBottom") or "")
    try:
        if float(str(bb).replace("px", "") or "0") > 0.6:
            errs.append(f"{prefix}.list still has borderBottom={bb}")
    except Exception:
        pass
    if rep.get("inner") or rep.get("listInner"):
        errs.append(f"{prefix}.inner scroller ixOv={rep.get('ixOv')} ilOv={rep.get('ilOv')}")
    if (rep.get("ixCh") or 0) < 80:
        errs.append(f"{prefix}.index shell collapsed ixCh={rep.get('ixCh')}")
    if (rep.get("ixH") or 0) + 8 < (rep.get("ilH") or 0):
        errs.append(f"{prefix}.index shorter than list ixH={rep.get('ixH')} ilH={rep.get('ilH')}")
    last_below = rep.get("lastBelowIx")
    if last_below is not None and last_below > 4:
        errs.append(f"{prefix}.last name below index box {last_below}")
    if (rep.get("ixOv") not in ("visible", "hidden", "clip")) and (rep.get("ixH") or 0) > (rep.get("ixCh") or 0) + 8:
        errs.append(f"{prefix}.ix overflow {rep.get('ixOv')}")
    if not (rep.get("bodyScroll") or (rep.get("bodyOv") in ("auto", "scroll"))):
        errs.append(f"{prefix}.catalog-body not scroller ov={rep.get('bodyOv')}")
    name_b = rep.get("nameBottom")
    sep_y = rep.get("sepY")
    loc_t = rep.get("locTop")
    card_t = rep.get("cardTop")
    ix_b = rep.get("ixBottom")
    if name_b is None or sep_y is None or loc_t is None:
        errs.append(f"{prefix}.missing geometry")
    else:
        if not (name_b < sep_y < loc_t):
            errs.append(f"{prefix}.order name={name_b} sep={sep_y} loc={loc_t}")
    loc_gap = rep.get("locGap")
    if loc_gap is None or loc_gap < 12 or loc_gap > 24:
        errs.append(f"{prefix}.locGap={loc_gap}")
    if ix_b is not None and loc_t is not None and loc_t < ix_b + 8:
        errs.append(f"{prefix}.loc not below index loc={loc_t} ixB={ix_b}")
    if card_t is not None and ix_b is not None and card_t < ix_b + 8:
        errs.append(f"{prefix}.cards not below index card={card_t} ixB={ix_b}")
    if (rep.get("overlap") or 0) > 2:
        errs.append(f"{prefix}.overlap={rep.get('overlap')}")
    if expect_names and (rep.get("names") or 0) != expect_names:
        errs.append(f"{prefix}.names={rep.get('names')} want {expect_names}")
    return errs


def judge_win(rep, prefix):
    errs = []
    if not rep or rep.get("err"):
        return [f"{prefix}: {rep}"]
    if rep.get("embedded"):
        errs.append(f"{prefix}.still embedded")
    if rep.get("inBody") and not rep.get("overlay"):
        errs.append(f"{prefix}.window still in-flow in catalog-body")
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
    logf = open("/tmp/catalog-ix-embed-sep.log", "w")
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
    out = {"ok": True, "integrity": integ, "errors": [], "shots": []}
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
        nav(cdp, f"http://127.0.0.1:{HTTP}/DS-CATALOG.html?v=ixsep")
        ds = cdp.eval(JS_EMBED)
        out["dsEmbed"] = ds
        out["errors"].extend(judge_embed(ds, "DS-desk-embed", expect_names=366))
        out["shots"].append(shot(cdp, "D1400-ds-index-embed-sep.png"))

        win = cdp.eval(JS_WIN)
        out["dsWin"] = win
        out["errors"].extend(judge_win(win, "DS-desk-win"))
        out["shots"].append(shot(cdp, "D1400-ds-index-window-sep.png"))

        set_view(cdp, 390, 844, True)
        nav(cdp, f"http://127.0.0.1:{HTTP}/DS-CATALOG-portable.html?v=ixsep-p")
        port = cdp.eval(JS_EMBED)
        out["portEmbed"] = port
        out["errors"].extend(judge_embed(port, "DS-port-embed", expect_names=366))
        out["shots"].append(shot(cdp, "D390-ds-port-index-embed-sep.png"))

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
    print(json.dumps({"ok": out.get("ok"), "errors": out.get("errors"), "integrity": integ, "shots": out.get("shots"), "dsEmbed": out.get("dsEmbed"), "dsWin": out.get("dsWin"), "portEmbed": out.get("portEmbed")}, indent=2)[:12000])
    sys.exit(0 if out.get("ok") else 1)


if __name__ == "__main__":
    main()
