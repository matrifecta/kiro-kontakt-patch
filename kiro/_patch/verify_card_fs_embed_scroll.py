#!/usr/bin/env python3
"""CDP: Flip+Search FS, Index icon-free embed scroll, fullscreen/embed card scroll."""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_card_fs_embed_scroll.json")
PORT = 9567
HTTP = 8797
PROFILE = "/tmp/catalog-card-fs-embed-scroll"
os.makedirs(PROFILE, exist_ok=True)

CATS = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
KEEP = (
    "c00e3e",
    "fix-PORTABLE-FS-FLIP-INDEX-v1",
    "fix-CARD-FS-EMBED-SCROLL-v1",
)
FILES = [
    CATS / "KONTAKT-CATALOG.html",
    CATS / "DS-CATALOG.html",
    CATS / "KONTAKT-CATALOG-portable.html",
    CATS / "DS-CATALOG-portable.html",
]


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


def set_view(cdp, w, h, mobile=False):
    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {"width": w, "height": h, "deviceScaleFactor": 1 if not mobile else 2, "mobile": mobile},
    )


def integrity():
    rows = []
    ok = True
    for p in FILES:
        t = p.read_text(encoding="utf-8")
        row = {
            "file": p.name,
            "bytes": len(t.encode("utf-8")),
            "endswithHtml": t.strip().endswith("</html>"),
        }
        for k in KEEP:
            row[k] = k in t
            if k not in t:
                ok = False
        if not row["endswithHtml"]:
            ok = False
        rows.append(row)
    return {"ok": ok, "files": rows}


def nav(cdp, url):
    cdp.call("Page.navigate", {"url": url})
    for _ in range(60):
        try:
            ready = cdp.eval("document.readyState")
        except Exception:
            ready = ""
        if ready == "complete":
            break
        time.sleep(0.2)
    time.sleep(0.35)


def verify_fs_flip(cdp):
    nav(cdp, f"http://127.0.0.1:{HTTP}/KONTAKT-CATALOG-portable.html?cb=fsflip3")
    set_view(cdp, 844, 390, mobile=True)
    wait_entries(cdp)
    cdp.eval(
        """
        if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
        document.body.classList.remove('search-chrome-collapsed','ac-fs-open','kw-fs-open','dual-fs-open','kw-open','display-middle');
        document.body.classList.add('kw-chrome-collapsed');
        var fw=document.getElementById('filterWrap'); if(fw){fw.classList.remove('open');}
        if(!document.body.classList.contains('sides-portrait-flip') && typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();
        if(typeof placePortableHandles==='function')placePortableHandles();
        """
    )
    time.sleep(0.3)
    before = cdp.eval(
        """
        (()=>{
          var sc=document.getElementById('searchChrome');
          var r=sc?sc.getBoundingClientRect():null;
          var sfs=document.getElementById('searchStripFs')||document.querySelector('#searchStrip .search-strip-fs,.search-strip-fs');
          var cs=sfs?getComputedStyle(sfs):null;
          return {
            flip:document.body.classList.contains('sides-portrait-flip'),
            acFs:document.body.classList.contains('ac-fs-open'),
            kwOpen:document.body.classList.contains('kw-open'),
            searchW:r?Math.round(r.width):0,
            searchOn:!!(r&&r.width>8&&r.height>8),
            sfsOn:!!(sfs&&cs&&cs.display!=='none'&&cs.visibility!=='hidden'),
            vw:innerWidth,vh:innerHeight
          };
        })()
        """
    )
    cdp.eval(
        """
        var btn=document.getElementById('searchStripFs')||document.querySelector('#searchStrip .search-strip-fs,.search-strip-fs');
        if(btn)btn.click();
        else if(typeof toggleAcFullscreen==='function')toggleAcFullscreen();
        """
    )
    time.sleep(0.35)
    after = cdp.eval(
        """
        (()=>{
          var sc=document.getElementById('searchChrome');
          var sh=document.getElementById('acShell');
          var r=sc?sc.getBoundingClientRect():null;
          var sr=sh?sh.getBoundingClientRect():null;
          var jump=document.getElementById('catalogJumpStack');
          var jc=jump?getComputedStyle(jump):null;
          return {
            flip:document.body.classList.contains('sides-portrait-flip'),
            acFs:document.body.classList.contains('ac-fs-open'),
            searchW:r?Math.round(r.width):0,
            searchH:r?Math.round(r.height):0,
            shellW:sr?Math.round(sr.width):0,
            vw:innerWidth,
            jumpHidden:!(jump&&jc&&jc.display!=='none'&&jc.visibility!=='hidden'&&jump.getBoundingClientRect().height>4)
          };
        })()
        """
    )
    filled = bool(after and after.get("acFs") and after.get("searchW", 0) >= (after.get("vw") or 844) * 0.85)
    return {
        "before": before,
        "after": after,
        "pass": filled and not (before and before.get("acFs")),
    }


def verify_index(cdp):
    nav(cdp, f"http://127.0.0.1:{HTTP}/DS-CATALOG.html?cb=ixdupe3")
    set_view(cdp, 1400, 900, mobile=False)
    wait_entries(cdp, nmin=8)
    cdp.eval(
        """
        if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
        var ix=document.getElementById('catalogIndex');
        if(ix&&ix.classList.contains('is-collapsed')&&typeof toggleCatalogIndex==='function')toggleCatalogIndex();
        if(ix&&!ix.classList.contains('is-embedded')&&typeof toggleIndexEmbed==='function')toggleIndexEmbed();
        if(typeof stripIndexCardChrome==='function')stripIndexCardChrome(ix);
        """
    )
    time.sleep(0.3)
    return cdp.eval(
        r"""
        (()=>{
          var ix=document.getElementById('catalogIndex');
          var il=document.getElementById('catalogIndexList')||(ix&&ix.querySelector('ul.index'));
          if(!ix||!il)return {err:'no-index'};
          var icons=[].slice.call(ix.querySelectorAll('.path-icon-btn,.path-action-row,.path-label,a.folder,svg.path-icon-glyph'));
          var vis=icons.filter(function(el){
            var cs=getComputedStyle(el), r=el.getBoundingClientRect();
            return cs.display!=='none'&&cs.visibility!=='hidden'&&cs.opacity!=='0'&&r.width>2&&r.height>2;
          }).length;
          var names=il.querySelectorAll('a[href^="#"]');
          var clickable=names.length>0&&getComputedStyle(names[0]).pointerEvents!=='none';
          var card=document.querySelector('.entry .path-icon-btn,.entry .path-action-row');
          var cardIcons=document.querySelectorAll('.entry .path-icon-btn').length;
          var main=document.getElementById('catalogMain');
          var body=document.querySelector('#catalogMain > .catalog-body')||main;
          var sc=body&&body.scrollHeight>body.clientHeight+4?body:(il.scrollHeight>il.clientHeight+4?il:body);
          var y0=sc?sc.scrollTop:0;
          if(sc)sc.scrollTop=y0+80;
          var y1=sc?sc.scrollTop:0;
          if(sc)sc.scrollTop=y0;
          return {
            embed:ix.classList.contains('is-embedded'),
            indexPathIcons:vis,
            indexPathIconNodes:icons.length,
            names:names.length,
            clickable:clickable,
            cardPathIcons:cardIcons,
            hasCardPath:!!card,
            ovY:sc?getComputedStyle(sc).overflowY:null,
            sh:sc?sc.scrollHeight:0,
            ch:sc?sc.clientHeight:0,
            y0:y0,y1:y1,
            moved:Math.abs(y1-y0)>2,
            scId:sc&&(sc.id||sc.className||'')
          };
        })()
        """
    )


def verify_card_scroll(cdp, url, w, h, mobile, key):
    nav(cdp, url)
    set_view(cdp, w, h, mobile=mobile)
    wait_entries(cdp)
    cdp.eval(
        """
        if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
        document.body.classList.remove('ac-fs-open','kw-fs-open','dual-fs-open');
        """
    )
    time.sleep(0.2)
    return cdp.eval(
        r"""
        (()=>{
          var entry=document.querySelector('.entry');
          if(!entry)return {err:'no-entry'};
          if(typeof openOverlay==='function')openOverlay(entry);
          var patches=entry.querySelector('details.patches');
          if(patches)patches.open=true;
          var pad=document.createElement('div');
          pad.setAttribute('data-fs-scroll-pad','1');
          pad.style.cssText='height:70vh;flex:0 0 auto;min-height:70vh;pointer-events:none;opacity:0';
          var host=entry.querySelector('.hl-body')||entry;
          host.appendChild(pad);
          var card=document.querySelector('.entry.highlight')||entry;
          var cs=getComputedStyle(card);
          var main=document.getElementById('catalogMain');
          var body=document.querySelector('#catalogMain > .catalog-body');
          var y0=card.scrollTop;
          var m0=main?main.scrollTop:0;
          var b0=body?body.scrollTop:0;
          card.scrollTop=y0+64;
          var y1=card.scrollTop;
          var m1=main?main.scrollTop:0;
          var b1=body?body.scrollTop:0;
          card.scrollTop=y0;
          var chrome=entry.querySelector('.card-chrome-start,.preview-back,.fs-btn');
          var cr=chrome?chrome.getBoundingClientRect():null;
          var embedOpen=false;
          try{
            var btn=entry.querySelector('.search-popup-btn,.search-link');
            if(btn&&typeof openCardSearchEmbed==='function'){
              var web=btn.getAttribute('data-web')||'https://www.google.com/search?q=test';
              openCardSearchEmbed('web',web);
              embedOpen=document.body.classList.contains('card-embed-open');
            }
          }catch(eEmb){}
          var embed=document.getElementById('cardSearchEmbed');
          var ecs=embed?getComputedStyle(embed):null;
          return {
            key:null,
            hl:document.body.classList.contains('hl-open'),
            highlight:card.classList.contains('highlight'),
            embed:embedOpen,
            ovY:cs.overflowY,
            webkit:cs.webkitOverflowScrolling||'',
            sh:card.scrollHeight,
            ch:card.clientHeight,
            can:card.scrollHeight>card.clientHeight+2,
            y0:y0,y1:y1,moved:Math.abs(y1-y0)>2,
            mainMoved:Math.abs((m1||0)-(m0||0))>2,
            bodyMoved:Math.abs((b1||0)-(b0||0))>2,
            chromeOn:!!(cr&&cr.width>8&&cr.height>8),
            embedOvY:ecs?ecs.overflowY:null,
            vw:innerWidth,vh:innerHeight
          };
        })()
        """
    )


def main():
    integ = integrity()
    urllib.request.urlopen(f"http://127.0.0.1:{HTTP}/KONTAKT-CATALOG-portable.html", timeout=2).read(64)
    subprocess.run(["pkill", "-f", f"remote-debugging-port={PORT}"], check=False)
    time.sleep(0.3)
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
    logf = open("/tmp/catalog-card-fs-embed-scroll.log", "w")
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

        fs = verify_fs_flip(cdp)
        out["fsFlip"] = fs

        ix = verify_index(cdp)
        out["index"] = ix

        card_p = verify_card_scroll(
            cdp,
            f"http://127.0.0.1:{HTTP}/KONTAKT-CATALOG-portable.html?cb=cardfs1",
            844,
            390,
            True,
            "portable-land",
        )
        if isinstance(card_p, dict):
            card_p["key"] = "portable-land"
        out["cardPortable"] = card_p

        card_d = verify_card_scroll(
            cdp,
            f"http://127.0.0.1:{HTTP}/KONTAKT-CATALOG.html?cb=cardfs2",
            1400,
            900,
            False,
            "desktop",
        )
        if isinstance(card_d, dict):
            card_d["key"] = "desktop"
        out["cardDesktop"] = card_d

        def card_ok(c):
            return bool(
                c
                and c.get("hl")
                and (c.get("ovY") in ("auto", "scroll"))
                and c.get("can")
                and c.get("moved")
                and not c.get("mainMoved")
            )

        pass_map = {
            "integrity": bool(integ.get("ok")),
            "fsFlip": bool(fs.get("pass")),
            "indexIcons0": bool(ix and ix.get("indexPathIcons") == 0),
            "indexNames": bool(ix and ix.get("clickable") and ix.get("names", 0) > 0),
            "indexScroll": bool(ix and ix.get("moved")),
            "cardIconsStill": bool(ix and ix.get("cardPathIcons", 0) >= 1),
            "cardPortable": card_ok(card_p),
            "cardDesktop": card_ok(card_d),
        }
        out["pass"] = pass_map
        out["ok"] = all(pass_map.values())
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
    print(json.dumps(out["pass"] if "pass" in out else out, indent=2))
    print("ok", out.get("ok"))
    sys.exit(0 if out.get("ok") else 1)


if __name__ == "__main__":
    main()
