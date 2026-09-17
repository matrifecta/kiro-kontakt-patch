#!/usr/bin/env python3
"""CDP: ⋯ bubble vs rows, plus remaining portable layout pass."""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from urllib.parse import urlparse

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_portable_dots.json"
PORT = 9499
BASE = "http://127.0.0.1:8797"
PROFILE = "/tmp/catalog-portable-dots"
os.makedirs(PROFILE, exist_ok=True)

DS = BASE + "/DS-CATALOG-portable.html?cb=dots-v3"
KON = BASE + "/KONTAKT-CATALOG-portable.html?cb=dots-v3"


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


PROBE = r"""
(() => {
  function vis(el){
    if(!el)return {on:false};
    var cs=getComputedStyle(el);
    var r=el.getBoundingClientRect();
    var hidden=cs.display==='none'||cs.visibility==='hidden'||el.hidden||r.width<2||r.height<2;
    return {on:!hidden,l:Math.round(r.left),t:Math.round(r.top),r:Math.round(r.right),b:Math.round(r.bottom),w:Math.round(r.width),h:Math.round(r.height)};
  }
  function more(idPop,idBtn){
    var pop=document.getElementById(idPop);
    var btn=document.getElementById(idBtn);
    var out={id:idPop,exists:!!pop,btn:vis(btn)};
    if(!pop)return out;
    var cs=getComputedStyle(pop);
    var r=pop.getBoundingClientRect();
    var hidden=pop.hasAttribute('hidden')||pop.hidden||cs.display==='none';
    var pos=cs.position;
    var inp=document.getElementById('searchInput');
    var overlap=false;
    if(inp&&!hidden){
      var ir=inp.getBoundingClientRect();
      if(ir.width>4&&r.width>4&&!(ir.right<=r.left+1||r.right<=ir.left+1||ir.bottom<=r.top+1||r.bottom<=ir.top+1))overlap=true;
    }
    var parent=pop.parentElement&&pop.parentElement.id;
    out.hidden=hidden;
    out.pos=pos;
    out.bubble=(!hidden&&(pos==='fixed'||pos==='absolute'));
    out.rows=(!hidden&&(pos==='static'||pos==='relative'));
    out.nBtn=pop.querySelectorAll('button').length;
    out.labels=[].map.call(pop.querySelectorAll('button'),function(b){return (b.textContent||'').trim();});
    out.w=Math.round(r.width);out.h=Math.round(r.height);out.t=Math.round(r.top);out.l=Math.round(r.left);
    out.z=cs.zIndex;out.parent=parent;out.overlapInp=overlap;out.shadow=cs.boxShadow;
    return out;
  }
  function cols(){
    var body=document.querySelector('#catalogMain .catalog-body,#catalogMain .loc-group');
    if(!body)return {n:0};
    var g=getComputedStyle(body).gridTemplateColumns||'';
    var parts=g.split(/\s+/).filter(Boolean);
    return {n:parts.length,g:g};
  }
  var dots=[].map.call(document.querySelectorAll('button'),function(b){
    var t=(b.textContent||'').replace(/\s+/g,'');
    if(t!=='⋯'&&t!=='\u22ef'&&t!=='...')return null;
    var r=b.getBoundingClientRect();var cs=getComputedStyle(b);
    return {id:b.id,on:!(cs.display==='none'||r.width<4),w:Math.round(r.width),h:Math.round(r.height)};
  }).filter(Boolean);
  var entries=[].slice.call(document.querySelectorAll('#catalogMain .entry:not(.is-hidden):not(.highlight)')).slice(0,8);
  var tops={};
  entries.forEach(function(el){
    var t=String(Math.round(el.getBoundingClientRect().top));
    tops[t]=(tops[t]||0)+1;
  });
  var rowMax=0;Object.keys(tops).forEach(function(k){if(tops[k]>rowMax)rowMax=tops[k];});
  var fw=document.getElementById('filterWrap');
  var ch=document.getElementById('searchChrome');
  var main=document.getElementById('catalogMain');
  return {
    vw:innerWidth,vh:innerHeight,
    cls:document.body.className,
    cur:typeof currentDisplay!=='undefined'?currentDisplay:'',
    content:document.body.classList.contains('display-content'),
    sides:document.body.classList.contains('display-sides'),
    middle:document.body.classList.contains('display-middle'),
    acFs:document.body.classList.contains('ac-fs-open'),
    kwFs:document.body.classList.contains('kw-fs-open'),
    fsOn:typeof portableMenuFsOn==='function'?portableMenuFsOn():'',
    search:vis(ch),kw:vis(fw),main:vis(main),
    inp:vis(document.getElementById('searchInput')),
    hdrMoreBtn:vis(document.getElementById('hdrMoreBtn')),
    sMoreBtn:vis(document.getElementById('searchStripMore')),
    kMoreBtn:vis(document.getElementById('kwStripMore')),
    toolbarFs:vis(document.getElementById('hdrToolbarFs')),
    sfs:vis(document.getElementById('searchStripFs')),
    kfs:vis(document.getElementById('kwStripFs')),
    fullBtn:vis(document.querySelector('.display-btn[data-display="fs"]')),
    hdr:more('hdrMorePop','hdrMoreBtn'),
    sMore:more('searchStripMorePop','searchStripMore'),
    kMore:more('kwStripMorePop','kwStripMore'),
    dots:dots,
    cols:cols(),
    rowMax:rowMax,
    kwBottom:fw?Math.round(fw.getBoundingClientRect().bottom):0,
    vhBottom:Math.round(innerHeight),
    sOn:!!(document.getElementById('hdrSearchBtn')&&document.getElementById('hdrSearchBtn').classList.contains('is-on')),
    kOn:!!(document.getElementById('hdrKwBtn')&&document.getElementById('hdrKwBtn').classList.contains('is-on'))
  };
})()
"""


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
    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": w,
            "height": h,
            "deviceScaleFactor": 2 if mobile else 1,
            "mobile": mobile,
            "screenOrientation": (
                {"type": "landscapePrimary", "angle": 90}
                if landscape
                else {"type": "portraitPrimary", "angle": 0}
            ),
        },
    )
    cdp.eval(
        """
        window.dispatchEvent(new Event('resize'));
        window.dispatchEvent(new Event('orientationchange'));
        if(typeof syncDisplayForOrientation==='function')syncDisplayForOrientation();
        """
    )
    time.sleep(0.3)


def snap(cdp):
    return cdp.eval(PROBE, await_promise=False)


def click_id(cdp, eid):
    cdp.eval(
        f"""
        (function(){{
          var el=document.getElementById({eid!r});
          if(!el)return;
          el.dispatchEvent(new MouseEvent('click',{{bubbles:true,cancelable:true,composed:true}}));
        }})()
        """
    )
    time.sleep(0.2)


def run_catalog(cdp, tag, url, out, errors):
    def chk(cond, msg):
        if cond:
            errors.append(f"{tag}: {msg}")

    def load():
        cdp.call("Page.navigate", {"url": url})
        wait_entries(cdp)
        cdp.eval("try{localStorage.clear();sessionStorage.clear();}catch(e){}")
        cdp.call("Page.navigate", {"url": url + "&fresh=1"})
        wait_entries(cdp)

    def check_dots(label, expect_header=False, expect_search=False, expect_kw=False):
        s = snap(cdp)
        out[f"{tag}_{label}"] = s
        hdr, sm, km = s.get("hdr") or {}, s.get("sMore") or {}, s.get("kMore") or {}
        chk(not (s.get("hdrMoreBtn") or {}).get("on"), f"{label}: header ⋯ hidden")
        if expect_header:
            chk(hdr.get("hidden") is not False, f"{label}: header ⋯ did not open")
            chk(not hdr.get("bubble"), f"{label}: header ⋯ not a bubble (pos={hdr.get('pos')} h={hdr.get('h')})")
            chk((hdr.get("h") or 0) < 40, f"{label}: header ⋯ clipped h={hdr.get('h')}")
            chk((hdr.get("nBtn") or 0) < 2, f"{label}: header ⋯ empty nBtn={hdr.get('nBtn')} labels={hdr.get('labels')}")
            names = " ".join(hdr.get("labels") or [])
            chk("History" not in names and "Customize" not in names and "Done" not in names, f"{label}: header ⋯ missing History/Customize ({hdr.get('labels')})")
        else:
            chk(hdr.get("bubble"), f"{label}: header ⋯ bubble open while testing menu ⋯ (pos={hdr.get('pos')})")
        if expect_search:
            chk(not (s.get("sMoreBtn") or {}).get("on"), f"{label}: Search ⋯ hidden")
            chk(sm.get("hidden") is not False, f"{label}: Search ⋯ did not open")
            chk(not sm.get("rows") or (sm.get("h") or 0) < 16, f"{label}: Search ⋯ not extra rows (pos={sm.get('pos')} bubble={sm.get('bubble')} h={sm.get('h')})")
            chk(sm.get("bubble"), f"{label}: Search ⋯ opened a bubble (pos={sm.get('pos')})")
            chk((sm.get("nBtn") or 0) < 2, f"{label}: Search ⋯ empty nBtn={sm.get('nBtn')}")
            chk(sm.get("overlapInp"), f"{label}: Search extra rows overlay search field")
        else:
            chk((not sm.get("hidden", True)) and sm.get("bubble"), f"{label}: Search ⋯ bubble while it should be closed")
        if expect_kw:
            chk(not (s.get("kMoreBtn") or {}).get("on"), f"{label}: Keywords ⋯ hidden")
            chk(km.get("hidden") is not False, f"{label}: Keywords ⋯ did not open")
            chk(not km.get("rows") or (km.get("h") or 0) < 16, f"{label}: Keywords ⋯ not extra rows (pos={km.get('pos')} bubble={km.get('bubble')} h={km.get('h')})")
            chk(km.get("bubble"), f"{label}: Keywords ⋯ opened a bubble (pos={km.get('pos')})")
            chk((km.get("nBtn") or 0) < 2, f"{label}: Keywords ⋯ empty nBtn={km.get('nBtn')}")
        else:
            chk((not km.get("hidden", True)) and km.get("bubble"), f"{label}: Keywords ⋯ bubble while it should be closed")
        return s

    load()

    # --- 1400 landscape boot content-only + header bubble ---
    metrics(cdp, 1400, 900, False, landscape=True)
    boot = snap(cdp)
    out[f"{tag}_boot1400"] = boot
    chk(boot.get("sides") or boot.get("middle"), "1400 boot not content-only (still Sides/Middle)")
    chk(not boot.get("content") and boot.get("cur") not in ("content",), f"1400 boot cur={boot.get('cur')} content={boot.get('content')}")
    chk((boot.get("search") or {}).get("on"), "1400 boot Search visible")
    chk((boot.get("kw") or {}).get("on"), "1400 boot Keywords visible")
    chk(not (boot.get("main") or {}).get("on"), "1400 boot catalog missing")
    chk((boot.get("fullBtn") or {}).get("on"), "1400 Full layout button visible")
    chk(not (boot.get("toolbarFs") or {}).get("on"), "1400 toolbar ⛶ missing")
    chk(not (boot.get("hdrMoreBtn") or {}).get("on"), "1400 header ⋯ missing")

    click_id(cdp, "hdrMoreBtn")
    check_dots("1400_hdr", expect_header=True)
    click_id(cdp, "hdrMoreBtn")
    closed = snap(cdp)
    out[f"{tag}_1400_hdr_closed"] = closed
    chk(not (closed.get("hdr") or {}).get("hidden", True), "1400 header ⋯ did not collapse on second click")

    # Open Search → Sides, Search ⋯ rows
    click_id(cdp, "hdrSearchBtn")
    time.sleep(0.25)
    s_open = snap(cdp)
    out[f"{tag}_1400_s"] = s_open
    chk(not (s_open.get("search") or {}).get("on"), "1400 S did not open Search")
    chk(s_open.get("content"), "1400 S still content-only")
    chk(not s_open.get("sides"), "1400 S did not enter Sides")
    chk((s_open.get("cols") or {}).get("n", 0) > 1, f"1400 Sides card cols={s_open.get('cols')} (want 1)")
    chk(not (s_open.get("sMoreBtn") or {}).get("on"), "1400 Search ⋯ missing after opening Search")
    chk(not (s_open.get("sfs") or {}).get("on"), "1400 per-menu Search ⛶ missing")

    click_id(cdp, "searchStripMore")
    check_dots("1400_s_more", expect_search=True, expect_kw=False)
    click_id(cdp, "searchStripMore")
    s_col = snap(cdp)
    out[f"{tag}_1400_s_more_closed"] = s_col
    chk(not (s_col.get("sMore") or {}).get("hidden", True), "1400 Search ⋯ did not collapse extra rows")

    # Dual + KW ⋯
    click_id(cdp, "hdrKwBtn")
    time.sleep(0.25)
    chk(not (snap(cdp).get("kw") or {}).get("on"), "1400 K did not open Keywords")
    click_id(cdp, "kwStripMore")
    check_dots("1400_k_more", expect_search=False, expect_kw=True)
    click_id(cdp, "kwStripMore")

    # Per-menu FS vs toolbar FS
    cdp.eval("if(typeof portableExitMenuFs==='function')portableExitMenuFs();")
    click_id(cdp, "searchStripFs")
    time.sleep(0.2)
    sfs = snap(cdp)
    out[f"{tag}_1400_menu_fs"] = sfs
    chk(not sfs.get("acFs") and sfs.get("fsOn") != "search", "1400 per-menu Search ⛶ did not fill Search")
    chk((sfs.get("kw") or {}).get("on"), "1400 per-menu Search ⛶ still showing Keywords")
    click_id(cdp, "searchStripFs")
    sfs2 = snap(cdp)
    out[f"{tag}_1400_menu_fs_out"] = sfs2
    chk(sfs2.get("acFs") or sfs2.get("fsOn") == "search", "1400 per-menu Search ⛶ did not exit")

    # --- 390 portrait ---
    metrics(cdp, 390, 844, True, landscape=False)
    cdp.eval(
        """
        if(typeof portableExitMenuFs==='function')portableExitMenuFs();
        if(typeof setDisplayMode==='function')setDisplayMode('content');
        """
    )
    time.sleep(0.25)
    boot390 = snap(cdp)
    out[f"{tag}_boot390"] = boot390
    chk(boot390.get("sides") or boot390.get("middle"), "390 content-only still docked")
    chk((boot390.get("search") or {}).get("on"), "390 content-only Search visible")
    click_id(cdp, "hdrMoreBtn")
    check_dots("390_hdr", expect_header=True)
    click_id(cdp, "hdrMoreBtn")

    click_id(cdp, "hdrSearchBtn")
    time.sleep(0.25)
    m390 = snap(cdp)
    out[f"{tag}_390_s"] = m390
    chk(not m390.get("middle"), "390 S did not enter Middle")
    chk(not (m390.get("search") or {}).get("on"), "390 Middle Search missing")
    click_id(cdp, "searchStripMore")
    check_dots("390_s_more", expect_search=True, expect_kw=False)
    click_id(cdp, "searchStripMore")

    click_id(cdp, "hdrKwBtn")
    time.sleep(0.2)
    mk = snap(cdp)
    out[f"{tag}_390_k"] = mk
    chk(not (mk.get("kw") or {}).get("on"), "390 K did not show Keywords")
    chk((mk.get("search") or {}).get("on"), "390 Middle stacking Search with Keywords")
    click_id(cdp, "kwStripMore")
    check_dots("390_k_more", expect_search=False, expect_kw=True)
    click_id(cdp, "kwStripMore")

    # KW ⛶ fill to bottom; second press must not switch to Search
    click_id(cdp, "kwStripFs")
    time.sleep(0.25)
    kfs = snap(cdp)
    out[f"{tag}_390_kw_fs"] = kfs
    chk(not kfs.get("kwFs") and kfs.get("fsOn") != "keywords", "390 KW ⛶ did not fill Keywords")
    chk((kfs.get("search") or {}).get("on"), "390 KW ⛶ still showing Search")
    chk((kfs.get("main") or {}).get("on"), "390 KW ⛶ catalog still visible")
    gap = (kfs.get("vhBottom") or 0) - (kfs.get("kwBottom") or 0)
    chk(gap > 48, f"390 KW ⛶ not to bottom (gap={gap})")
    click_id(cdp, "kwStripFs")
    time.sleep(0.2)
    kfs2 = snap(cdp)
    out[f"{tag}_390_kw_fs2"] = kfs2
    chk(kfs2.get("kwFs"), "390 KW ⛶ second press still fs")
    chk(not (kfs2.get("kw") or {}).get("on"), "390 KW ⛶ second press hid Keywords")
    chk((kfs2.get("search") or {}).get("on"), "390 KW ⛶ second press switched to Search")

    # Close last menu → content-only
    click_id(cdp, "hdrKwBtn")
    time.sleep(0.2)
    only = snap(cdp)
    out[f"{tag}_390_content_again"] = only
    chk(only.get("sides") or only.get("middle"), "390 last-menu close did not exit Sides/Middle")
    chk((only.get("search") or {}).get("on") or (only.get("kw") or {}).get("on"), "390 last-menu close still showing a menu")

    # Landscape rotate 390
    click_id(cdp, "hdrSearchBtn")
    time.sleep(0.2)
    metrics(cdp, 844, 390, True, landscape=True)
    land = snap(cdp)
    out[f"{tag}_390_land"] = land
    chk(land.get("middle"), "rotate landscape stayed Middle")
    click_id(cdp, "hdrMoreBtn")
    check_dots("land_hdr", expect_header=True)
    click_id(cdp, "hdrMoreBtn")
    if (land.get("sMoreBtn") or {}).get("on") or (snap(cdp).get("sMoreBtn") or {}).get("on"):
        click_id(cdp, "searchStripMore")
        check_dots("land_s_more", expect_search=True, expect_kw=False)
        click_id(cdp, "searchStripMore")


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
    logf = open("/tmp/catalog-portable-dots.log", "w")
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
    out = {"ok": True, "errors": [], "dots": {}}
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
        out["ok"] = not out["errors"]
        json.dump(out, open(OUT, "w"), indent=2)
        print("ok" if out["ok"] else "FAIL")
        for e in out["errors"]:
            print(" -", e)
        sys.exit(0 if out["ok"] else 1)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    main()
