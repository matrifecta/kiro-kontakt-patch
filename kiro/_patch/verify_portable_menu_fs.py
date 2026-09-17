#!/usr/bin/env python3
"""CDP: no Full layout btn; S+K dual; Sides menu ⛶ fills one menu."""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from urllib.parse import urlparse

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_portable_menu_fs.json"
PORT = 9493
URL = "http://127.0.0.1:8797/DS-CATALOG-portable.html?cb=menu-fs5"
PROFILE = "/tmp/catalog-portable-menu-fs"
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


SNAP = r"""
(() => {
  function vis(el){
    if(!el)return {on:false};
    var cs=getComputedStyle(el);
    var r=el.getBoundingClientRect();
    var hidden=cs.display==='none'||cs.visibility==='hidden'||el.hidden||r.width<2||r.height<2;
    return {on:!hidden,l:Math.round(r.left),t:Math.round(r.top),r:Math.round(r.right),b:Math.round(r.bottom),w:Math.round(r.width),h:Math.round(r.height),disp:cs.display};
  }
  var fsBtn=document.querySelector('.display-btn[data-display="fs"]');
  var sfs=document.getElementById('searchStripFs');
  var kfs=document.getElementById('kwStripFs')||document.querySelector('.kw-fs-btn');
  var hdr=document.querySelector('.catalog-header');
  var ht=hdr?Math.round(hdr.getBoundingClientRect().bottom):0;
  var main=document.getElementById('catalogMain');
  var ac=document.getElementById('acList');
  var inp=document.getElementById('searchInput');
  var jump=document.getElementById('catalogJumpStack');
  var ent=main&&main.querySelector('.entry:not(.highlight)');
  var cov=ent&&ent.querySelector('.cover');
  var cr=cov?cov.getBoundingClientRect():null;
  var img=cov&&cov.querySelector('img');
  var ir=img?img.getBoundingClientRect():null;
  var mr=main?main.getBoundingClientRect():null;
  var er=ent?ent.getBoundingClientRect():null;
  var jr=jump?jump.getBoundingClientRect():null;
  var pick=document.querySelector('.mode-btn[data-mode="pick"]');
  var glass=document.querySelector('.kw-companion-btn,.ac-companion-btn');
  var hist=document.getElementById('searchHistory');
  var split=document.getElementById('searchSplit');
  var sep=document.getElementById('dualFsSep');
  var ix=document.getElementById('catalogIndex');
  var moreS=document.getElementById('searchStripMorePop');
  var moreK=document.getElementById('kwStripMorePop');
  var moreH=document.getElementById('hdrMorePop');
  function inside(a,b){
    if(!a||!b)return false;
    return a.left>=b.left-1&&a.right<=b.right+1&&a.top>=b.top-1&&a.bottom<=b.bottom+1;
  }
  return {
    vw:innerWidth,vh:innerHeight,cls:document.body.className,
    cur:typeof currentDisplay!=='undefined'?currentDisplay:'',
    fullBtn:vis(fsBtn), sfs:vis(sfs), kfs:vis(kfs),
    search:vis(document.getElementById('searchChrome')),
    kw:vis(document.getElementById('filterWrap')),
    main:vis(main),
    inp:vis(inp),
    acList:vis(ac),
    acH:ac?Math.round(ac.getBoundingClientRect().height):0,
    acScroll:ac?ac.scrollHeight:0,
    hdrB:ht,
    acFs:document.body.classList.contains('ac-fs-open'),
    kwFs:document.body.classList.contains('kw-fs-open'),
    displayFs:document.body.classList.contains('display-fs'),
    browserFs:document.body.classList.contains('is-browser-fs'),
    jump:vis(jump),
    jumpInMain:!!(jr&&mr&&jr.right<=mr.right+8&&jr.bottom<=mr.bottom+8&&jr.left>=mr.left-8),
    entryInMain:!!(er&&mr&&er.left>=mr.left-2&&er.right<=mr.right+2),
    coverAR: (cr&&cr.width>8)?Math.round((cr.height/cr.width)*100)/100:null,
    imgFit: img?getComputedStyle(img).objectFit:'',
    pick:vis(pick),
    glass:vis(glass),
    histTxt: hist?(hist.textContent||'').trim():'',
    histOn: vis(hist).on,
    stripe: vis(split).on||vis(sep).on,
    ixCollapsed: !!(ix&&ix.classList.contains('is-collapsed')),
    moreSOpen: !!(moreS&&!moreS.hidden&&!moreS.hasAttribute('hidden')),
    moreKOpen: !!(moreK&&!moreK.hidden&&!moreK.hasAttribute('hidden')),
    moreHOpen: !!(moreH&&!moreH.hidden&&!moreH.hasAttribute('hidden')),
    moreSCount: moreS?moreS.querySelectorAll('button').length:0,
    moreKCount: moreK?moreK.querySelectorAll('button').length:0,
    moreHCount: moreH?moreH.querySelectorAll('button,select').length:0,
    layoutEdit: document.body.classList.contains('layout-edit'),
    gapSM:null
  };
})()
"""


def fill_gap(s):
    if not s:
        return s
    a, b = s.get("search") or {}, s.get("main") or {}
    if a.get("on") and b.get("on"):
        s["gapSM"] = b.get("l", 0) - a.get("r", 0)
    a, b = s.get("search") or {}, s.get("kw") or {}
    if a.get("on") and b.get("on") and not (s.get("main") or {}).get("on"):
        s["gapSK"] = b.get("l", 0) - a.get("r", 0)
    return s


def wait_entries(cdp):
    for _ in range(80):
        try:
            n = cdp.eval("document.querySelectorAll('.entry').length", await_promise=False)
        except Exception:
            n = 0
        if n and n > 8:
            return
        time.sleep(0.25)


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
    logf = open("/tmp/catalog-portable-menu-fs.log", "w")
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
    out = {"ok": True, "errors": []}
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
        wait_entries(cdp)
        cdp.eval(
            """
            if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
            document.body.classList.remove('search-chrome-collapsed','kw-open','ac-fs-open','kw-fs-open','dual-fs-open');
            document.body.classList.add('kw-chrome-collapsed');
            var fw=document.getElementById('filterWrap'); if(fw)fw.classList.remove('open');
            if(typeof placePortableHandles==='function')placePortableHandles();
            if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
            """
        )
        time.sleep(0.25)
        out["s_only"] = fill_gap(cdp.eval(SNAP, await_promise=False))

        cdp.eval("if(typeof toggleAcFullscreen==='function')toggleAcFullscreen();")
        time.sleep(0.25)
        out["s_fs"] = fill_gap(cdp.eval(SNAP, await_promise=False))

        cdp.eval("if(typeof toggleAcFullscreen==='function')toggleAcFullscreen();")
        time.sleep(0.2)
        out["s_fs_back"] = fill_gap(cdp.eval(SNAP, await_promise=False))

        cdp.eval(
            """
            document.body.classList.add('search-chrome-collapsed');
            document.body.classList.remove('kw-chrome-collapsed');
            var fw=document.getElementById('filterWrap');
            if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}
            if(typeof placePortableHandles==='function')placePortableHandles();
            """
        )
        time.sleep(0.2)
        out["k_only"] = fill_gap(cdp.eval(SNAP, await_promise=False))

        cdp.eval("if(typeof toggleKwFullscreen==='function')toggleKwFullscreen();")
        time.sleep(0.25)
        out["k_fs"] = fill_gap(cdp.eval(SNAP, await_promise=False))

        cdp.eval("if(typeof toggleKwFullscreen==='function')toggleKwFullscreen();")
        time.sleep(0.2)
        out["k_fs_back"] = fill_gap(cdp.eval(SNAP, await_promise=False))

        cdp.eval(
            """
            document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed','ac-fs-open','kw-fs-open');
            var fw=document.getElementById('filterWrap');
            if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}
            if(typeof placePortableHandles==='function')placePortableHandles();
            """
        )
        time.sleep(0.25)
        out["sk_dual"] = fill_gap(cdp.eval(SNAP, await_promise=False))

        cdp.eval("if(typeof toggleAcFullscreen==='function')toggleAcFullscreen();")
        time.sleep(0.25)
        out["sk_search_fs"] = fill_gap(cdp.eval(SNAP, await_promise=False))

        cdp.eval("if(typeof toggleAcFullscreen==='function')toggleAcFullscreen();")
        time.sleep(0.2)
        cdp.eval("if(typeof toggleKwFullscreen==='function')toggleKwFullscreen();")
        time.sleep(0.25)
        out["sk_kw_fs"] = fill_gap(cdp.eval(SNAP, await_promise=False))

        cdp.eval("if(typeof portableExitMenuFs==='function')portableExitMenuFs();")
        time.sleep(0.15)
        cdp.eval(
            """
            document.body.classList.add('search-chrome-collapsed');
            document.body.classList.remove('kw-chrome-collapsed','ac-fs-open','kw-fs-open');
            var fw=document.getElementById('filterWrap');
            if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}
            if(typeof toggleSearchStripMore==='function')toggleSearchStripMore();
            """
        )
        time.sleep(0.15)
        out["more_search"] = fill_gap(cdp.eval(SNAP, await_promise=False))
        cdp.eval("if(typeof closePhoneOverflowPops==='function')closePhoneOverflowPops();")
        cdp.eval(
            """
            document.body.classList.remove('search-chrome-collapsed');
            if(typeof toggleKwStripMore==='function')toggleKwStripMore();
            """
        )
        time.sleep(0.15)
        out["more_kw"] = fill_gap(cdp.eval(SNAP, await_promise=False))
        cdp.eval("if(typeof closePhoneOverflowPops==='function')closePhoneOverflowPops();")
        cdp.eval(
            """
            if(typeof toggleHdrMore==='function')toggleHdrMore();
            """
        )
        time.sleep(0.15)
        out["more_hdr"] = fill_gap(cdp.eval(SNAP, await_promise=False))
        cdp.eval("if(typeof closePhoneOverflowPops==='function')closePhoneOverflowPops();")
        cdp.eval(
            """
            var miss=document.getElementById('clearMissBtn');
            var before=miss&&miss.getAttribute('aria-pressed');
            if(typeof toggleClearOnMiss==='function')toggleClearOnMiss();
            window.__missFlip=(miss&&miss.getAttribute('aria-pressed'))!==before;
            if(typeof toggleCatalogIndex==='function')toggleCatalogIndex();
            """
        )
        time.sleep(0.15)
        out["index_open"] = fill_gap(cdp.eval(SNAP, await_promise=False))
        out["missFlip"] = cdp.eval("window.__missFlip||false", await_promise=False)
        cdp.eval("if(typeof toggleCatalogIndex==='function')toggleCatalogIndex();")
        cdp.eval(
            """
            var p=document.querySelector('#catalogMain .entry:not(.highlight) .path, #catalogMain .entry:not(.highlight) .lib-path, #catalogMain a.path');
            window.__pathClicked=false;
            if(p){p.click();window.__pathClicked=true;}
            """
        )
        time.sleep(0.2)
        out["path"] = cdp.eval(
            """
            ({clicked:!!window.__pathClicked,
              reader:!!(document.body.classList.contains('path-reader-open')||document.querySelector('.path-reader,.embed-reader,body.chosen-preview-open')),
              cls:document.body.className})
            """,
            await_promise=False,
        )
        cdp.eval(
            """
            if(typeof closePathReader==='function')closePathReader();
            if(typeof closeChosenPreview==='function')closeChosenPreview();
            document.body.classList.remove('chosen-preview-open','path-reader-open');
            """
        )
        cdp.eval(
            """
            document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed','ac-fs-open','kw-fs-open');
            var fw=document.getElementById('filterWrap');
            if(fw){fw.classList.remove('open');document.body.classList.remove('kw-open');document.body.classList.add('kw-chrome-collapsed');}
            if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();
            if(typeof placePortableHandles==='function')placePortableHandles();
            """
        )
        time.sleep(0.2)
        out["flip_s"] = fill_gap(cdp.eval(SNAP, await_promise=False))
        cdp.eval(
            """
            if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();
            if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();
            """
        )
        time.sleep(0.2)
        out["customize"] = fill_gap(cdp.eval(SNAP, await_promise=False))
        cdp.eval("if(document.body.classList.contains('layout-edit')&&typeof toggleLayoutEdit==='function')toggleLayoutEdit();")

        cdp.call(
            "Emulation.setDeviceMetricsOverride",
            {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True},
        )
        cdp.eval(
            """
            window.dispatchEvent(new Event('resize'));
            if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
            document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed','ac-fs-open','kw-fs-open');
            var fw=document.getElementById('filterWrap');
            if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}
            if(typeof placePortableHandles==='function')placePortableHandles();
            """
        )
        time.sleep(0.3)
        out["p390_sk"] = fill_gap(cdp.eval(SNAP, await_promise=False))
        cdp.eval("if(typeof toggleAcFullscreen==='function')toggleAcFullscreen();")
        time.sleep(0.2)
        out["p390_s_fs"] = fill_gap(cdp.eval(SNAP, await_promise=False))
        cdp.eval("if(typeof toggleAcFullscreen==='function')toggleAcFullscreen();")
        time.sleep(0.15)
        cdp.eval(
            """
            if(typeof setDisplayMode==='function')setDisplayMode('middle',{pick:true});
            """
        )
        time.sleep(0.25)
        out["p390_middle"] = fill_gap(cdp.eval(SNAP, await_promise=False))
        cdp.eval("if(typeof toggleSearchStripMore==='function')toggleSearchStripMore();")
        time.sleep(0.15)
        out["p390_more_s"] = fill_gap(cdp.eval(SNAP, await_promise=False))
        cdp.eval("if(typeof closePhoneOverflowPops==='function')closePhoneOverflowPops();")
        cdp.eval("if(typeof toggleHdrMore==='function')toggleHdrMore();")
        time.sleep(0.15)
        out["p390_more_h"] = fill_gap(cdp.eval(SNAP, await_promise=False))
        cdp.eval("if(typeof closePhoneOverflowPops==='function')closePhoneOverflowPops();")

        cdp.call(
            "Emulation.setDeviceMetricsOverride",
            {"width": 1400, "height": 900, "deviceScaleFactor": 1, "mobile": False},
        )
        cdp.call("Page.navigate", {"url": "http://127.0.0.1:8797/KONTAKT-CATALOG-portable.html?cb=menu-fs5"})
        wait_entries(cdp)
        cdp.eval(
            """
            if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
            document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed','ac-fs-open','kw-fs-open');
            var fw=document.getElementById('filterWrap');
            if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}
            if(typeof placePortableHandles==='function')placePortableHandles();
            """
        )
        time.sleep(0.25)
        out["k_sk_dual"] = fill_gap(cdp.eval(SNAP, await_promise=False))
        cdp.eval("if(typeof toggleAcFullscreen==='function')toggleAcFullscreen();")
        time.sleep(0.2)
        out["k_sk_search_fs"] = fill_gap(cdp.eval(SNAP, await_promise=False))

        def chk(cond, msg):
            if cond:
                out["errors"].append(msg)

        def shown(box):
            return bool(box and box.get("on"))

        chk(shown((out.get("s_only") or {}).get("fullBtn")), "Full layout button visible at 1400")
        chk(not shown((out.get("s_only") or {}).get("sfs")), "Search ⛶ hidden in Sides S-only")
        s = out.get("s_only") or {}
        chk(not (shown(s.get("search")) and shown(s.get("main"))), "S-only missing Search|Content")
        chk(shown(s.get("kw")), "S-only still showing KW")

        fs = out.get("s_fs") or {}
        chk(not shown(fs.get("search")), "Search FS: search not shown")
        chk(shown(fs.get("main")), "Search FS: catalog still visible")
        chk(shown(fs.get("kw")), "Search FS: KW still visible")
        if shown(fs.get("search")):
            chk(fs["search"].get("w", 0) < 1000, "Search FS not full width")
            chk(fs["search"].get("h", 0) < 400, "Search FS not tall")
            chk(abs((fs["search"].get("t") or 0) - (fs.get("hdrB") or 0)) > 8, "Search FS not below header")

        back = out.get("s_fs_back") or {}
        chk(not (shown(back.get("search")) and shown(back.get("main"))), "exit Search FS did not restore catalog")

        ko = out.get("k_only") or {}
        chk(not (shown(ko.get("kw")) and shown(ko.get("main"))), "K-only missing Content|KW")

        kfs = out.get("k_fs") or {}
        chk(not shown(kfs.get("kw")), "KW FS: kw not shown")
        chk(shown(kfs.get("main")), "KW FS: catalog still visible")
        chk(shown(kfs.get("search")), "KW FS: search still visible")

        dual = out.get("sk_dual") or {}
        chk(shown(dual.get("main")), "S+K dual catalog should be hidden")
        chk(not (shown(dual.get("search")) and shown(dual.get("kw"))), "S+K dual missing both menus")

        sfs2 = out.get("sk_search_fs") or {}
        chk(shown(sfs2.get("main")) or shown(sfs2.get("kw")), "dual→Search FS still showing catalog/KW")
        chk(not shown(sfs2.get("search")), "dual→Search FS search missing")
        if shown(sfs2.get("search")):
            chk(sfs2["search"].get("w", 0) < 1200, "dual→Search FS not full width")

        kfs2 = out.get("sk_kw_fs") or {}
        chk(shown(kfs2.get("main")) or shown(kfs2.get("search")), "dual→KW FS still showing catalog/Search")
        chk(not shown(kfs2.get("kw")), "dual→KW FS kw missing")
        if shown(kfs2.get("kw")):
            chk(kfs2["kw"].get("w", 0) < 1200, "dual→KW FS not full width")

        if shown(kfs.get("kw")):
            chk(kfs["kw"].get("w", 0) < 1200, "KW FS not full width")

        p3 = out.get("p390_sk") or {}
        chk(shown(p3.get("fullBtn")), "390 Full layout button visible")
        chk(not (out.get("s_fs_back") or {}).get("jump", {}).get("on"), "jump missing after exiting Search ⛶")
        chk(not (out.get("k_only") or {}).get("jump", {}).get("on"), "jump missing in K-only")
        chk((out.get("sk_dual") or {}).get("jump", {}).get("on"), "jump visible in S+K dual (catalog hidden)")
        chk(not (out.get("p390_sk") or {}).get("jump", {}).get("on"), "jump missing on 390 S+K with catalog")

        for key in ("s_only", "s_fs", "sk_dual"):
            snap = out.get(key) or {}
            chk(snap.get("displayFs"), f"{key}: leftover display-fs")
            chk(shown(snap.get("pick")), f"{key}: Pick/Search mode visible")
            chk(shown(snap.get("glass")), f"{key}: companion glass visible")

        chk(shown(s.get("inp")) is False, "S-only: search field hidden")
        gap = s.get("gapSM")
        chk(gap is not None and not (4 <= gap <= 10), f"S-only gutter {gap} not 4–8px")
        chk(s.get("entryInMain") is False, "S-only: first card not inside catalog pane")
        ar = s.get("coverAR")
        chk(ar is not None and abs(ar - 4 / 3) > 0.2, f"cover aspect {ar} not ~4/3")
        chk(s.get("imgFit") not in ("cover",), f"cover object-fit {s.get('imgFit')}")
        chk(not s.get("jump", {}).get("on"), "S-only: jump stack hidden")
        chk(s.get("ixCollapsed") is False, "Index not collapsed at start")
        chk((fs.get("acH") or 0) < 200, "Search FS: acList too short")
        chk(fs.get("stripe"), "Search FS: resize stripe still visible")
        chk(not shown(fs.get("inp")), "Search FS: search field hidden")
        chk(not shown(fs.get("sfs")), "Search FS: ⛶ not reachable")
        chk(kfs.get("stripe"), "KW FS: resize stripe still visible")
        chk((out.get("more_search") or {}).get("moreSCount", 0) < 1, "Search ⋯ pop empty")
        chk((out.get("more_kw") or {}).get("moreKCount", 0) < 1, "KW ⋯ pop empty (1400 isPhone?)")
        chk((out.get("index_open") or {}).get("ixCollapsed") is True, "Index arrow did not expand")
        p390fs = out.get("p390_s_fs") or {}
        chk(shown(p390fs.get("main")) or shown(p390fs.get("kw")), "390 Search FS still showing catalog/KW")
        mid = out.get("p390_middle") or {}
        chk(not (shown(mid.get("search")) and shown(mid.get("main"))), "390 Middle missing stacked search+catalog")
        chk((out.get("p390_more_s") or {}).get("moreSCount", 0) < 1, "390 Search ⋯ pop empty")
        chk((out.get("p390_more_h") or {}).get("moreHCount", 0) < 1, "390 header ⋯ pop empty")
        kdual = out.get("k_sk_dual") or {}
        chk(shown(kdual.get("main")), "KONTAKT S+K catalog should be hidden")
        kfsS = out.get("k_sk_search_fs") or {}
        chk(shown(kfsS.get("kw")), "KONTAKT Search FS KW still visible")

        out["ok"] = len(out["errors"]) == 0
        json.dump(out, open(OUT, "w"), indent=2)
        print(json.dumps(out, indent=2))
        if not out["ok"]:
            sys.exit(1)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    main()
