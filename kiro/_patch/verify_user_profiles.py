#!/usr/bin/env python3
"""CDP: user profiles switch, 13th blocked, reload, portable ⋯ only."""
import base64
import json
import os
import socket
import subprocess
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_user_profiles.json")
SHOT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots")
PORT = 9543
HTTP_PORT = 8797
PROFILE = "/tmp/catalog-user-profiles"
SHOT.mkdir(parents=True, exist_ok=True)
os.makedirs(PROFILE, exist_ok=True)

DESK = f"http://127.0.0.1:{HTTP_PORT}/KONTAKT-CATALOG.html?up=1"
PORTABLE = f"http://127.0.0.1:{HTTP_PORT}/KONTAKT-CATALOG-portable.html?up=1"


class Ws:
    def __init__(self, url):
        u = urlparse(url)
        host, port = u.hostname, u.port or 80
        path = u.path + (("?" + u.query) if u.query else "")
        key = base64.b64encode(os.urandom(16)).decode()
        s = socket.create_connection((host, port), timeout=60)
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


def wait_ready(cdp):
    for _ in range(200):
        try:
            n = cdp.eval(
                "!!(document.querySelectorAll('.entry').length>2&&typeof newUserProfile==='function'&&typeof toggleHdrSearch==='function')"
            )
        except Exception:
            n = False
        if n:
            return
        time.sleep(0.2)
    raise SystemExit("catalog JS not ready")


def set_view(cdp, w, h, mobile=False):
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
    time.sleep(0.35)


def shot(cdp, name):
    data = cdp.call("Page.captureScreenshot", {"format": "png"})
    raw = data.get("data")
    path = SHOT / name
    if raw:
        path.write_bytes(base64.b64decode(raw))
    return str(path)


def nav(cdp, url):
    cdp.call("Page.enable")
    cdp.call("Runtime.enable")
    cdp.call("Page.navigate", {"url": url})
    time.sleep(1.0)
    wait_ready(cdp)


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


UI = r"""
(() => {
  var btn=document.getElementById('hdrProfilesBtn');
  var pop=document.getElementById('hdrProfilesPop');
  function vis(el){
    if(!el)return {exists:false,on:false,w:0,h:0,disp:''};
    var cs=getComputedStyle(el);
    var r=el.getBoundingClientRect();
    var on=cs.display!=='none'&&cs.visibility!=='hidden'&&r.width>8&&r.height>8;
    return {exists:true,on:on,w:Math.round(r.width),h:Math.round(r.height),disp:cs.display,txt:(el.textContent||'').slice(0,40)};
  }
  return {
    portable:!!window.CATALOG_PORTABLE,
    ns:window.CATALOG_NS,
    btn:vis(btn),
    pop:vis(pop),
    hdrMore:!!document.getElementById('hdrMoreBtn'),
    flip:document.body.classList.contains('sides-portrait-flip'),
    pills: (typeof collectUserProfilePills==='function'?collectUserProfilePills():[]),
    store: (typeof readUserProfileStore==='function'?readUserProfileStore():null)
  };
})()
"""


def run_desktop(cdp):
    set_view(cdp, 1400, 900)
    cdp.eval(
        "localStorage.removeItem(typeof userProfilesKey==='function'?userProfilesKey():'catalog-user-profiles-kontakt');"
        "if(typeof ensureUserProfilesChrome==='function')ensureUserProfilesChrome();"
        "if(typeof ensureLayoutChromeBtns==='function')ensureLayoutChromeBtns();"
    )
    time.sleep(0.2)
    ui0 = cdp.eval(UI)
    cdp.eval(
        "if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});"
        "if(typeof expandSearchMenu==='function')expandSearchMenu();"
        "if(typeof expandKwMenu==='function')expandKwMenu();"
        "if(typeof writePortraitFlip==='function')writePortraitFlip(false);"
        "if(typeof applyDesktopArrange==='function')applyDesktopArrange();"
        "if(typeof applySidesCols==='function')applySidesCols();"
        "if(typeof clearAllFilters==='function')clearAllFilters();"
        "if(typeof addSearchKw==='function')addSearchKw('viola');"
    )
    time.sleep(0.35)
    a = cdp.eval("newUserProfile('Alpha Viola')")
    cdp.eval(
        "if(typeof writePortraitFlip==='function')writePortraitFlip(true);"
        "if(typeof applyDesktopArrange==='function')applyDesktopArrange();"
        "if(typeof applySidesCols==='function')applySidesCols();"
        "if(typeof clearAllFilters==='function')clearAllFilters();"
        "if(typeof addSearchKw==='function')addSearchKw('drums');"
    )
    time.sleep(0.35)
    b = cdp.eval("newUserProfile('Beta Drums')")
    after_b = cdp.eval(
        "({flip:document.body.classList.contains('sides-portrait-flip'),pills:collectUserProfilePills(),active:(readUserProfileStore().activeId),n:readUserProfileStore().profiles.length})"
    )
    sw_a = cdp.eval("switchUserProfile(readUserProfileStore().profiles[0].id)")
    time.sleep(0.45)
    after_a = cdp.eval(
        "({flip:document.body.classList.contains('sides-portrait-flip'),pills:collectUserProfilePills(),active:(readUserProfileStore().activeId),name:(readUserProfileStore().profiles.find(function(p){return p.id===readUserProfileStore().activeId})||{}).name})"
    )
    sw_b = cdp.eval("switchUserProfile(readUserProfileStore().profiles[1].id)")
    time.sleep(0.45)
    after_b2 = cdp.eval(
        "({flip:document.body.classList.contains('sides-portrait-flip'),pills:collectUserProfilePills(),active:(readUserProfileStore().activeId)})"
    )
    # fill to 12 and block 13
    fill = cdp.eval(
        r"""
(() => {
  var st=readUserProfileStore();
  var made=0;
  while(st.profiles.length<12){
    var r=newUserProfile('Fill '+st.profiles.length);
    if(!r||!r.ok)break;
    made++;
    st=r.store||readUserProfileStore();
  }
  var blocked=newUserProfile('Should fail');
  return {n:readUserProfileStore().profiles.length,made:made,blockedOk:!!(blocked&&blocked.ok),blockedFull:!!(blocked&&blocked.full)};
})()
"""
    )
    cdp.eval("if(typeof openUserProfilesMenu==='function')openUserProfilesMenu();")
    time.sleep(0.2)
    ui_open = cdp.eval(UI)
    shot(cdp, "D1400-user-profiles.png")
    aid = cdp.eval("readUserProfileStore().activeId")
    cdp.call("Page.reload", {"ignoreCache": True})
    time.sleep(1.2)
    wait_ready(cdp)
    set_view(cdp, 1400, 900)
    time.sleep(0.4)
    after_reload = cdp.eval(
        "({active:readUserProfileStore().activeId,n:readUserProfileStore().profiles.length,pills:collectUserProfilePills(),flip:document.body.classList.contains('sides-portrait-flip')})"
    )
    # phone ⋯
    set_view(cdp, 390, 844, mobile=True)
    cdp.eval(
        "if(typeof ensureLayoutChromeBtns==='function')ensureLayoutChromeBtns();"
        "if(typeof toggleHdrMore==='function')toggleHdrMore();"
    )
    time.sleep(0.25)
    phone = cdp.eval(
        r"""
(() => {
  var btn=document.getElementById('hdrProfilesBtn');
  var more=document.getElementById('hdrMorePop');
  var cs=btn?getComputedStyle(btn):null;
  var r=btn?btn.getBoundingClientRect():null;
  var standing=!!(btn&&cs&&cs.display!=='none'&&cs.visibility!=='hidden'&&r&&r.width>8&&r.height>8);
  var labels=[];
  if(more)more.querySelectorAll('button').forEach(function(b){labels.push(b.textContent||'');});
  return {standing:standing,hdrMore:!!document.getElementById('hdrMoreBtn'),labels:labels,hasProfiles:labels.indexOf('Profiles')>=0};
})()
"""
    )
    shot(cdp, "D390-user-profiles-more.png")
    return {
        "ui0": ui0,
        "newA": a,
        "newB": b,
        "afterB": after_b,
        "afterSwitchA": after_a,
        "afterSwitchB": after_b2,
        "fill": fill,
        "uiOpen": ui_open,
        "reload": after_reload,
        "reloadWanted": aid,
        "phone": phone,
    }


def run_portable(cdp):
    set_view(cdp, 390, 844, mobile=True)
    cdp.eval(
        "if(typeof ensureLayoutChromeBtns==='function')ensureLayoutChromeBtns();"
        "if(typeof ensureUserProfilesChrome==='function')ensureUserProfilesChrome();"
        "if(typeof toggleHdrMore==='function')toggleHdrMore();"
    )
    time.sleep(0.3)
    info = cdp.eval(
        r"""
(() => {
  var btn=document.getElementById('hdrProfilesBtn');
  var cs=btn?getComputedStyle(btn):null;
  var r=btn?btn.getBoundingClientRect():null;
  var standing=!!(btn&&cs&&cs.display!=='none'&&cs.visibility!=='hidden'&&r&&r.width>8&&r.height>8);
  var more=document.getElementById('hdrMorePop');
  var labels=[];
  if(more)more.querySelectorAll('button').forEach(function(b){labels.push((b.textContent||b.getAttribute('aria-label')||''));});
  return {
    portable:!!window.CATALOG_PORTABLE,
    btnExists:!!btn,
    standing:standing,
    disp:cs?cs.display:'',
    hdrMore:!!document.getElementById('hdrMoreBtn'),
    labels:labels,
    hasProfiles:labels.some(function(t){return /profile/i.test(t);})
  };
})()
"""
    )
    shot(cdp, "P390-user-profiles-more.png")
    return info


def main():
    if not port_open(HTTP_PORT):
        raise SystemExit("http 8797 down")
    if not port_open(PORT):
        subprocess.Popen(
            [
                "chromium",
                f"--remote-debugging-port={PORT}",
                f"--user-data-dir={PROFILE}",
                "--headless=new",
                "--disable-gpu",
                "--no-first-run",
                "--no-default-browser-check",
                "about:blank",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(40):
            if port_open(PORT):
                break
            time.sleep(0.2)
        else:
            raise SystemExit("chromium debug port failed")
        time.sleep(0.4)

    out = {}
    tab = new_tab(DESK)
    cdp = CDP(tab["webSocketDebuggerUrl"])
    try:
        nav(cdp, DESK)
        out["desktop"] = run_desktop(cdp)
    finally:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/close/{tab['id']}")
        except Exception:
            pass

    tab2 = new_tab(PORTABLE)
    cdp2 = CDP(tab2["webSocketDebuggerUrl"])
    try:
        nav(cdp2, PORTABLE)
        out["portable"] = run_portable(cdp2)
    finally:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/close/{tab2['id']}")
        except Exception:
            pass

    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    fails = []
    d = out.get("desktop") or {}
    if not ((d.get("ui0") or {}).get("btn") or {}).get("on"):
        fails.append("desktop Profiles button not visible")
    a = d.get("afterSwitchA") or {}
    b = d.get("afterSwitchB") or {}
    if "viola" not in (a.get("pills") or []) and not a.get("flip") is False:
        # require either pills or flip difference
        if a.get("pills") == b.get("pills") and a.get("flip") == b.get("flip"):
            fails.append(f"switch did not change state A={a} B={b}")
    if a.get("pills") == b.get("pills") and a.get("flip") == b.get("flip"):
        fails.append(f"profiles A/B identical after switch A={a} B={b}")
    fill = d.get("fill") or {}
    if fill.get("n") != 12:
        fails.append(f"cap store n={fill.get('n')}")
    if fill.get("blockedOk") or not fill.get("blockedFull"):
        fails.append(f"13th not blocked {fill}")
    rel = d.get("reload") or {}
    if rel.get("active") != d.get("reloadWanted"):
        fails.append(f"reload active {rel.get('active')} != {d.get('reloadWanted')}")
    if (rel.get("n") or 0) != 12:
        fails.append(f"reload lost profiles n={rel.get('n')}")
    phone = d.get("phone") or {}
    if phone.get("standing"):
        fails.append("desktop-phone standing Profiles button visible")
    if not phone.get("hasProfiles"):
        fails.append(f"desktop-phone ⋯ missing Profiles {phone.get('labels')}")
    p = out.get("portable") or {}
    if p.get("standing"):
        fails.append("portable standing Profiles button visible")
    if not p.get("hasProfiles"):
        fails.append(f"portable ⋯ missing Profiles {p.get('labels')}")
    if fails:
        raise SystemExit("FAIL " + " | ".join(fails))
    print("PASS")


if __name__ == "__main__":
    main()
