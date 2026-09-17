#!/usr/bin/env python3
"""Full portable CDP pass: layout rules, FS rotate, first-open chrome. Both catalogs."""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from urllib.parse import urlparse

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_portable_full.json"
PORT = 9497
BASE = "http://127.0.0.1:8797"
PROFILE = "/tmp/catalog-portable-full"
os.makedirs(PROFILE, exist_ok=True)

DS = BASE + "/DS-CATALOG-portable.html?cb=full-v1"
KON = BASE + "/KONTAKT-CATALOG-portable.html?cb=full-v1"


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
    return {on:!hidden,l:Math.round(r.left),t:Math.round(r.top),r:Math.round(r.right),b:Math.round(r.bottom),w:Math.round(r.width),h:Math.round(r.height)};
  }
  var main=document.getElementById('catalogMain');
  var ac=document.getElementById('acList');
  var wrap=document.getElementById('hdrMenuBtns');
  var order=wrap?[].map.call(wrap.querySelectorAll('.hdr-menu-btn'),function(b){return b.id;}).join(','):'';
  var sb=document.getElementById('hdrSearchBtn');
  var kb=document.getElementById('hdrKwBtn');
  var fsBtn=document.querySelector('.display-btn[data-display="fs"]');
  var pick=document.querySelector('.mode-btn[data-mode="pick"]');
  var glass=document.querySelector('.kw-companion-btn,.ac-companion-btn');
  var scale=document.getElementById('searchOnlyScale')||document.getElementById('uiScale');
  var hist=document.getElementById('searchHistory');
  var jump=document.getElementById('catalogJumpStack');
  var ix=document.getElementById('catalogIndex');
  var moreH=document.getElementById('hdrMorePop');
  var moreS=document.getElementById('searchStripMorePop');
  var moreK=document.getElementById('kwStripMorePop');
  var ent=main&&main.querySelector('.entry:not(.highlight)');
  var mr=main?main.getBoundingClientRect():null;
  var er=ent?ent.getBoundingClientRect():null;
  function probe(el){
    if(!el)return {h:0,client:0,scroll:0,ov:'',can:false,moved:false};
    var cs=getComputedStyle(el);
    var r=el.getBoundingClientRect();
    var ov=cs.overflowY;
    var can=ov==='auto'||ov==='scroll'||ov==='overlay';
    var before=el.scrollTop||0;
    var max=Math.max(0,(el.scrollHeight||0)-(el.clientHeight||0));
    el.scrollTop=Math.min(max, Math.max(40, before+80));
    var moved=(el.scrollTop||0)>before+1;
    el.scrollTop=before;
    return {h:Math.round(r.height),client:el.clientHeight||0,scroll:el.scrollHeight||0,ov:ov,can:can,moved:moved};
  }
  var fp=document.getElementById('filterPanel')||document.querySelector('#filterWrap .filter-panel');
  var pathT=document.querySelector('.path-reader-text');
  return {
    vw:innerWidth,vh:innerHeight,
    cls:document.body.className,
    cur:typeof currentDisplay!=='undefined'?currentDisplay:'',
    hold:typeof portableMenuFsHold==='string'?portableMenuFsHold:'',
    fsOn:typeof portableMenuFsOn==='function'?portableMenuFsOn():'',
    orient:window.matchMedia&&window.matchMedia('(orientation:portrait)').matches?'portrait':'landscape',
    search:vis(document.getElementById('searchChrome')),
    kw:vis(document.getElementById('filterWrap')),
    main:vis(main),
    inp:vis(document.getElementById('searchInput')),
    acOpen:!!(ac&&ac.classList.contains('open')&&ac.getBoundingClientRect().height>8),
    acH:ac?Math.round(ac.getBoundingClientRect().height):0,
    acFs:document.body.classList.contains('ac-fs-open'),
    kwFs:document.body.classList.contains('kw-fs-open'),
    displayFs:document.body.classList.contains('display-fs'),
    middle:document.body.classList.contains('display-middle'),
    flip:document.body.classList.contains('sides-portrait-flip'),
    btnOrder:order,
    sOn:!!(sb&&sb.classList.contains('is-on')),
    kOn:!!(kb&&kb.classList.contains('is-on')),
    sVisible:vis(sb).on,
    kVisible:vis(kb).on,
    fullBtn:vis(fsBtn),
    pick:vis(pick),
    glass:vis(glass),
    scale:vis(scale),
    histTxt:hist?(hist.textContent||'').trim():'',
    histOn:vis(hist).on,
    jump:vis(jump),
    ixCollapsed:!!(ix&&ix.classList.contains('is-collapsed')),
    entryInMain:!!(er&&mr&&er.left>=mr.left-2&&er.right<=mr.right+2),
    sfsTitle:(document.getElementById('searchStripFs')||{}).title||'',
    moreHLabels:moreH&&!moreH.hidden?[].map.call(moreH.querySelectorAll('button'),function(b){return (b.textContent||'').trim();}):[],
    moreSCount:moreS&&!moreS.hidden?moreS.querySelectorAll('button').length:0,
    moreKCount:moreK&&!moreK.hidden?moreK.querySelectorAll('button').length:0,
    blackPane: vis(document.getElementById('searchChrome')).on && vis(document.getElementById('searchChrome')).h<20,
    acScroll:probe(ac),
    kwScroll:probe(fp),
    mainScroll:probe(main),
    ixScroll:probe(document.getElementById('catalogIndexList')),
    pathScroll:probe(pathT)
  };
})()
"""


def shown(box):
    return bool(box and box.get("on"))


def wait_entries(cdp):
    for _ in range(80):
        try:
            n = cdp.eval("document.querySelectorAll('.entry').length", await_promise=False)
        except Exception:
            n = 0
        if n and n > 8:
            return
        time.sleep(0.25)


def metrics(cdp, w, h, mobile, landscape=False):
    params = {
        "width": w,
        "height": h,
        "deviceScaleFactor": 2 if mobile else 1,
        "mobile": mobile,
        "screenOrientation": (
            {"type": "landscapePrimary", "angle": 90}
            if landscape
            else {"type": "portraitPrimary", "angle": 0}
        ),
    }
    cdp.call("Emulation.setDeviceMetricsOverride", params)
    cdp.eval(
        """
        window.dispatchEvent(new Event('resize'));
        window.dispatchEvent(new Event('orientationchange'));
        if(typeof syncDisplayForOrientation==='function')syncDisplayForOrientation();
        """
    )
    time.sleep(0.35)


def snap(cdp):
    return cdp.eval(SNAP, await_promise=False)


def click_away(cdp):
    cdp.eval(
        """
        var main=document.getElementById('catalogMain')||document.body;
        main.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,cancelable:true,composed:true}));
        document.body.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,cancelable:true,composed:true}));
        var kw=document.getElementById('filterWrap');
        if(kw)kw.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,cancelable:true,composed:true}));
        var inp=document.getElementById('searchInput');
        if(inp){inp.blur(); inp.dispatchEvent(new FocusEvent('focusout',{bubbles:true}));}
        """
    )
    time.sleep(0.2)


def open_sides_search(cdp):
    cdp.eval(
        """
        if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
        document.body.classList.remove('search-chrome-collapsed','kw-open','ac-fs-open','kw-fs-open','sides-portrait-flip','dual-fs-open');
        document.body.classList.add('kw-chrome-collapsed');
        var fw=document.getElementById('filterWrap'); if(fw)fw.classList.remove('open');
        if(typeof portableMenuFsHold!=='undefined')portableMenuFsHold='';
        if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
        if(typeof placePortableHandles==='function')placePortableHandles();
        if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
        if(typeof showAc==='function')try{showAc('',{force:true});}catch(e){}
        if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
        """
    )
    time.sleep(0.2)


def run_catalog(cdp, tag, url, out, errors):
    def chk(cond, msg):
        if cond:
            errors.append(f"{tag}: {msg}")

    def need_scroll(p, name):
        if not p:
            errors.append(f"{tag}: {name} missing scroll probe")
            return
        chk((p.get("h") or 0) < 80 and "Middle AC" in name, f"{name} height {p.get('h')} (clipped/0)")
        chk((p.get("h") or 0) < 16, f"{name} height {p.get('h')} (clipped/0)")
        chk(p.get("ov") not in ("auto", "scroll", "overlay"), f"{name} overflow-y={p.get('ov')}")
        if (p.get("scroll") or 0) > (p.get("client") or 0) + 8:
            chk(
                not p.get("can") or not p.get("moved"),
                f"{name} cannot reach last items (scroll {p.get('scroll')} client {p.get('client')} ov={p.get('ov')} moved={p.get('moved')})",
            )

    cdp.call("Page.navigate", {"url": url})
    wait_entries(cdp)
    cdp.eval("try{localStorage.clear();sessionStorage.clear();}catch(e){}")
    cdp.call("Page.navigate", {"url": url + "&fresh=1"})
    wait_entries(cdp)

    # --- 1400 first paint ---
    metrics(cdp, 1400, 900, False, landscape=True)
    time.sleep(0.25)
    first1400 = snap(cdp)
    out[f"{tag}_first1400"] = first1400
    chk(shown(first1400.get("fullBtn")), "1400 Full layout button visible")
    chk(shown(first1400.get("pick")), "1400 Pick visible")
    chk(shown(first1400.get("glass")), "1400 companion glass visible")
    chk(shown(first1400.get("scale")), "1400 Larger/Smaller scale visible")
    chk(not shown(first1400.get("search")), "1400 first-open Search missing")
    chk(not shown(first1400.get("main")), "1400 first-open catalog missing")
    chk(shown(first1400.get("kw")), "1400 first-open KW stacked (empty dual)")
    chk(not first1400.get("sVisible"), "1400 S button hidden")
    chk(not first1400.get("kVisible"), "1400 K button hidden")
    chk(first1400.get("displayFs"), "1400 leftover display-fs")
    chk(first1400.get("ixCollapsed") is False, "1400 Index not collapsed")
    chk(first1400.get("entryInMain") is False, "1400 card not inside catalog pane")
    chk(not shown(first1400.get("jump")), "1400 jump hidden while catalog shows")
    chk(not shown(first1400.get("inp")), "1400 search field hidden/overlaid")
    need_scroll(first1400.get("mainScroll"), "1400 catalog")

    # Flip spatial, S-only
    open_sides_search(cdp)
    s_only = snap(cdp)
    out[f"{tag}_s_only"] = s_only
    need_scroll(s_only.get("acScroll"), "Sides AC list")
    need_scroll(s_only.get("mainScroll"), "Sides catalog")
    cdp.eval("if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();")
    time.sleep(0.2)
    s_flip = snap(cdp)
    out[f"{tag}_s_flip"] = s_flip
    chk(s_flip.get("btnOrder") != "hdrSearchBtn,hdrKwBtn", f"Flip reordered S/K: {s_flip.get('btnOrder')}")
    if shown(s_only.get("search")) and shown(s_only.get("main")) and shown(s_flip.get("search")) and shown(s_flip.get("main")):
        chk(
            (s_flip["search"].get("l") or 0) <= (s_flip["main"].get("l") or 0),
            "Flip did not put catalog left of Search",
        )
        chk(s_only.get("search", {}).get("l") == s_flip.get("search", {}).get("l"), "Flip did not move Search pane")

    cdp.eval("if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();")
    time.sleep(0.1)

    # S+K dual
    cdp.eval(
        """
        document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed','ac-fs-open','kw-fs-open','sides-portrait-flip');
        var fw=document.getElementById('filterWrap');
        if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}
        if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
        if(typeof placePortableHandles==='function')placePortableHandles();
        if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
        """
    )
    time.sleep(0.25)
    dual = snap(cdp)
    out[f"{tag}_sk_dual"] = dual
    chk(not (shown(dual.get("search")) and shown(dual.get("kw"))), "S+K missing both menus")
    chk(shown(dual.get("main")), "S+K landscape catalog should be hidden")
    chk(shown(dual.get("jump")), "S+K jump visible while catalog hidden")

    cdp.eval("if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();")
    time.sleep(0.2)
    sk_flip = snap(cdp)
    out[f"{tag}_sk_flip"] = sk_flip
    chk(sk_flip.get("btnOrder") != "hdrSearchBtn,hdrKwBtn", "S+K Flip reordered S/K")
    if shown(sk_flip.get("search")) and shown(sk_flip.get("kw")):
        chk(
            (sk_flip["search"].get("l") or 0) < (sk_flip["kw"].get("l") or 0),
            "S+K Flip should put Keywords left of Search",
        )
    cdp.eval("if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();")

    # Search ⛶ from dual
    cdp.eval("if(typeof toggleAcFullscreen==='function')toggleAcFullscreen(); if(typeof showAc==='function')try{showAc('',{force:true});}catch(e){} if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();")
    time.sleep(0.25)
    s_fs = snap(cdp)
    out[f"{tag}_s_fs"] = s_fs
    need_scroll(s_fs.get("acScroll"), "Search ⛶ AC list")
    chk(not s_fs.get("acFs"), "Search ⛶ did not set ac-fs-open")
    chk(s_fs.get("kwFs"), "Search ⛶ still kw-fs-open")
    chk(not shown(s_fs.get("search")), "Search ⛶ search missing")
    chk(shown(s_fs.get("main")), "Search ⛶ catalog still visible")
    chk(shown(s_fs.get("kw")), "Search ⛶ KW still visible")
    if shown(s_fs.get("search")):
        chk((s_fs["search"].get("w") or 0) < 1000, "Search ⛶ not near full width")
        chk((s_fs["search"].get("h") or 0) < 400, "Search ⛶ not tall")
    chk((s_fs.get("acH") or 0) < 200, "Search ⛶ list too short")
    chk(not s_fs.get("acOpen"), "Search ⛶ list not open")

    click_away(cdp)
    s_fs_away = snap(cdp)
    out[f"{tag}_s_fs_away"] = s_fs_away
    chk(not s_fs_away.get("acOpen"), "Search ⛶ list collapsed after click-away")
    chk(not s_fs_away.get("acFs"), "Search ⛶ dropped after click-away")

    # Rotate to portrait 390 while Search FS
    metrics(cdp, 390, 844, True, landscape=False)
    time.sleep(0.3)
    s_fs_port = snap(cdp)
    out[f"{tag}_s_fs_port"] = s_fs_port
    need_scroll(s_fs_port.get("acScroll"), "Search ⛶ after rotate AC")
    chk(not s_fs_port.get("acFs") and s_fs_port.get("fsOn") != "search", "Search ⛶ dropped on rotate to portrait")
    chk(shown(s_fs_port.get("main")), "Search ⛶ portrait catalog visible")
    chk(s_fs_port.get("middle") and not s_fs_port.get("acFs"), "Search ⛶ coerced to Middle split on rotate")

    # Back to landscape
    metrics(cdp, 844, 390, True, landscape=True)
    time.sleep(0.3)
    s_fs_land = snap(cdp)
    out[f"{tag}_s_fs_land"] = s_fs_land
    chk(not s_fs_land.get("acFs") and s_fs_land.get("fsOn") != "search", "Search ⛶ dropped on rotate to landscape")
    chk(shown(s_fs_land.get("main")) or shown(s_fs_land.get("kw")), "Search ⛶ landscape still showing catalog/KW")

    # Exit FS, KW ⛶
    cdp.eval(
        """
        if(typeof portableExitMenuFs==='function')portableExitMenuFs();
        if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
        document.body.classList.add('search-chrome-collapsed');
        document.body.classList.remove('kw-chrome-collapsed','ac-fs-open','kw-fs-open');
        var fw=document.getElementById('filterWrap');
        if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}
        if(typeof toggleKwFullscreen==='function')toggleKwFullscreen();
        if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
        """
    )
    time.sleep(0.25)
    k_fs = snap(cdp)
    out[f"{tag}_k_fs"] = k_fs
    need_scroll(k_fs.get("kwScroll"), "KW ⛶ panel")
    chk(not k_fs.get("kwFs"), "KW ⛶ did not set kw-fs-open")
    chk(shown(k_fs.get("main")), "KW ⛶ catalog still visible")
    chk(shown(k_fs.get("search")), "KW ⛶ Search still visible")

    metrics(cdp, 390, 844, True, landscape=False)
    time.sleep(0.3)
    k_fs_port = snap(cdp)
    out[f"{tag}_k_fs_port"] = k_fs_port
    chk(not k_fs_port.get("kwFs") and k_fs_port.get("fsOn") != "keywords", "KW ⛶ dropped on rotate to portrait")

    metrics(cdp, 1400, 900, False, landscape=True)
    cdp.eval("if(typeof portableExitMenuFs==='function')portableExitMenuFs();")
    time.sleep(0.15)

    # 390 Middle one-menu + FS rotate
    metrics(cdp, 390, 844, True, landscape=False)
    cdp.eval(
        """
        if(typeof setDisplayMode==='function')setDisplayMode('middle',{pick:true});
        if(typeof portableCoerceMiddleMenu==='function')portableCoerceMiddleMenu('search');
        if(typeof showAc==='function')try{showAc('',{force:true});}catch(e){}
        if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
        """
    )
    time.sleep(0.3)
    mid = snap(cdp)
    out[f"{tag}_mid"] = mid
    need_scroll(mid.get("acScroll"), "Middle AC list")
    need_scroll(mid.get("mainScroll"), "Middle catalog")
    chk(not shown(mid.get("search")), "390 Middle Search missing")
    chk(shown(mid.get("kw")), "390 Middle stacking Keywords with Search")
    chk(not shown(mid.get("main")), "390 Middle catalog missing")
    chk(shown(mid.get("fullBtn")), "390 Full layout button visible")

    cdp.eval("if(typeof toggleHdrKw==='function')toggleHdrKw();")
    time.sleep(0.2)
    mid_k = snap(cdp)
    out[f"{tag}_mid_k"] = mid_k
    chk(not shown(mid_k.get("kw")), "Middle K did not show Keywords")
    chk(shown(mid_k.get("search")), "Middle K still showing Search")

    cdp.eval("if(typeof toggleHdrSearch==='function')toggleHdrSearch();")
    time.sleep(0.2)
    mid_s = snap(cdp)
    out[f"{tag}_mid_s"] = mid_s
    chk(not shown(mid_s.get("search")), "Middle S did not show Search")
    chk(shown(mid_s.get("kw")), "Middle S still showing Keywords")

    # Middle Search ⛶ then rotate landscape → Sides Search FS
    cdp.eval(
        """
        if(typeof portableCoerceMiddleMenu==='function')portableCoerceMiddleMenu('search');
        if(typeof toggleAcFullscreen==='function')toggleAcFullscreen();
        if(typeof showAc==='function')showAc('',{force:true});
        """
    )
    time.sleep(0.25)
    mid_fs = snap(cdp)
    out[f"{tag}_mid_fs"] = mid_fs
    chk(not mid_fs.get("acFs") and mid_fs.get("fsOn") != "search", "Middle Search ⛶ not on")

    metrics(cdp, 844, 390, True, landscape=True)
    time.sleep(0.35)
    mid_fs_land = snap(cdp)
    out[f"{tag}_mid_fs_land"] = mid_fs_land
    chk(
        not mid_fs_land.get("acFs") and mid_fs_land.get("fsOn") != "search",
        "Middle Search ⛶ did not persist as Sides Search FS in landscape",
    )
    chk(mid_fs_land.get("middle") and mid_fs_land.get("acFs"), "Middle FS stayed Middle in landscape")
    chk(shown(mid_fs_land.get("main")), "Middle→landscape Search FS catalog still visible")

    # 390 Sides S+K + ⛶ + overflow
    metrics(cdp, 390, 844, True, landscape=False)
    cdp.eval(
        """
        if(typeof portableExitMenuFs==='function')portableExitMenuFs();
        if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
        document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed','ac-fs-open','kw-fs-open');
        var fw=document.getElementById('filterWrap');
        if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}
        if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
        """
    )
    time.sleep(0.25)
    p390_sk = snap(cdp)
    out[f"{tag}_p390_sk"] = p390_sk
    chk(not (shown(p390_sk.get("search")) and shown(p390_sk.get("kw"))), "390 Sides S+K missing dual")
    chk(not p390_sk.get("sVisible"), "390 S hidden in overflow")
    chk(not p390_sk.get("kVisible"), "390 K hidden in overflow")

    cdp.eval("if(typeof toggleHdrMore==='function')toggleHdrMore();")
    time.sleep(0.15)
    more = snap(cdp)
    out[f"{tag}_more"] = more
    labels = more.get("moreHLabels") or []
    chk("Customize" not in labels and "Edit" not in labels, f"390 ⋯ missing Customize ({labels})")
    chk("Flip" not in labels, "390 ⋯ missing Flip")
    chk("History" not in labels, "390 ⋯ missing History")
    chk("Pick" in labels, "390 ⋯ still has Pick")
    cdp.eval("if(typeof closePhoneOverflowPops==='function')closePhoneOverflowPops();")

    cdp.eval("if(typeof toggleCatalogIndex==='function')toggleCatalogIndex();")
    time.sleep(0.15)
    ix = snap(cdp)
    out[f"{tag}_ix"] = ix
    chk(ix.get("ixCollapsed") is True, "Index arrow did not expand")
    cdp.eval("if(typeof toggleCatalogIndex==='function')toggleCatalogIndex();")


def main():
    urllib.request.urlopen(BASE + "/DS-CATALOG-portable.html", timeout=2).read(64)
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
    logf = open("/tmp/catalog-portable-full.log", "w")
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
        run_catalog(cdp, "DS", DS, out, out["errors"])
        run_catalog(cdp, "KON", KON, out, out["errors"])
        out["ok"] = len(out["errors"]) == 0
        json.dump(out, open(OUT, "w"), indent=2)
        print(json.dumps({"ok": out["ok"], "errors": out["errors"]}, indent=2))
        keys = [
            "DS_first1400",
            "DS_s_fs",
            "DS_s_fs_away",
            "DS_s_fs_port",
            "DS_s_fs_land",
            "DS_k_fs",
            "DS_k_fs_port",
            "DS_mid",
            "DS_mid_k",
            "DS_mid_s",
            "DS_mid_fs",
            "DS_mid_fs_land",
            "DS_p390_sk",
            "DS_more",
            "KON_s_fs",
            "KON_s_fs_land",
            "KON_mid",
            "KON_mid_fs_land",
        ]
        for key in keys:
            v = out.get(key) or {}
            print(
                f"{key}: vw={v.get('vw')}x{v.get('vh')} o={v.get('orient')} cur={v.get('cur')} "
                f"s={shown(v.get('search'))} kw={shown(v.get('kw'))} main={shown(v.get('main'))} "
                f"acFs={v.get('acFs')} kwFs={v.get('kwFs')} fsOn={v.get('fsOn')} hold={v.get('hold')} "
                f"mid={v.get('middle')} acH={v.get('acH')} acOpen={v.get('acOpen')} "
                f"sOn={v.get('sOn')} kOn={v.get('kOn')} flip={v.get('flip')}"
            )
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
