#!/usr/bin/env python3
"""CDP: header ⋯ closes; ⛶ only on document toolbar; Flip keeps Search above Keywords."""
import json, os, socket, subprocess, time, urllib.request
from urllib.parse import urlparse

PORT = 9514
URL = "http://127.0.0.1:8797/KONTAKT-CATALOG-portable.html?cb=chrome-flip3"
OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_portable_chrome_flip.json"
PROFILE = "/tmp/catalog-portable-chrome-flip"
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


class CDP:
    def __init__(self, url):
        self.ws = Ws(url)
        self.id = 0

    def call(self, method, params=None, timeout=60):
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
        if r.get("exceptionDetails"):
            raise RuntimeError(r["exceptionDetails"])
        return r.get("result", {}).get("value")


def chrome():
    for p in ("/usr/lib/chromium/chromium", "/usr/bin/chromium", "/usr/bin/google-chrome"):
        if os.path.exists(p):
            return p
    raise SystemExit("no chromium")


JS = r"""
async function run(){
  function cs(id){
    const el=document.getElementById(id);
    if(!el) return null;
    const s=getComputedStyle(el);
    return {disp:s.display, vis:s.visibility, pe:s.pointerEvents};
  }
  function moreState(){
    const pop=document.getElementById('hdrMorePop');
    const btn=document.getElementById('hdrMoreBtn');
    const s=pop?getComputedStyle(pop):null;
    return {hidden:!!(pop&&pop.hasAttribute('hidden')), disp:s&&s.display, aria:btn&&btn.getAttribute('aria-expanded')};
  }
  function g(id){
    const el=document.getElementById(id); if(!el) return null;
    const r=el.getBoundingClientRect(); const s=getComputedStyle(el);
    return {l:Math.round(r.left), t:Math.round(r.top), w:Math.round(r.width), h:Math.round(r.height), col:s.gridColumnStart, row:s.gridRowStart, disp:s.display};
  }
  try{localStorage.removeItem('catalog-sides-portrait-flip-'+(window.CATALOG_NS||'catalog'));}catch(e){}
  if(typeof toggleHdrMore==='function') toggleHdrMore();
  await new Promise(r=>setTimeout(r,80));
  const opened=moreState();
  if(typeof toggleHdrMore==='function') toggleHdrMore();
  await new Promise(r=>setTimeout(r,80));
  const closed=moreState();
  if(typeof toggleSearchStripMore==='function') toggleSearchStripMore();
  await new Promise(r=>setTimeout(r,80));
  const sp=document.getElementById('searchStripMorePop');
  const searchMore={hidden:sp&&sp.hasAttribute('hidden'), labels:sp?[...sp.querySelectorAll('button')].map(b=>b.textContent):[]};
  if(typeof toggleLayoutEdit==='function') toggleLayoutEdit();
  if(typeof placePortableHandles==='function') placePortableHandles();
  await new Promise(r=>setTimeout(r,80));
  const stripe=cs('searchSplit');
  let dockErr=null;
  try{
    const sb=document.getElementById('hdrSearchBtn'); if(sb) sb.click();
    await new Promise(r=>setTimeout(r,250));
    const kb=document.getElementById('hdrKwBtn'); if(kb) kb.click();
    await new Promise(r=>setTimeout(r,250));
  }catch(e){dockErr=String(e&&e.message||e);}
  const sk=()=>{const w=document.getElementById('hdrMenuBtns'); return w?[...w.children].map(n=>n.id):[];};
  const before={flip:document.body.classList.contains('sides-portrait-flip'), search:g('searchChrome'), kw:g('filterWrap'), main:g('catalogMain'), sk:sk(), dockErr, mode:document.body.className};
  try{ if(typeof togglePortraitSidesFlip==='function') togglePortraitSidesFlip(); }catch(e){ dockErr=String(e&&e.message||e); }
  await new Promise(r=>setTimeout(r,250));
  const after={flip:document.body.classList.contains('sides-portrait-flip'), search:g('searchChrome'), kw:g('filterWrap'), main:g('catalogMain'), sk:sk(), mode:document.body.className};
  return {
    hdrFs: cs('hdrToolbarFs'),
    searchFs: cs('searchStripFs'),
    kwFs: cs('kwStripFs'),
    kwTogglePe: cs('filterToggle'),
    opened, closed, searchMore, stripe, before, after
  };
}
run()
"""


def main():
    proc = subprocess.Popen(
        [
            chrome(),
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            f"--user-data-dir={PROFILE}",
            f"--remote-debugging-port={PORT}",
            "--window-size=1400,900",
            URL,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        tab = None
        for _ in range(50):
            try:
                tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list"))
                for t in tabs:
                    if t.get("type") == "page" and "CATALOG-portable" in (t.get("url") or ""):
                        tab = t
                        break
                if tab:
                    break
            except Exception:
                pass
            time.sleep(0.2)
        if not tab:
            raise SystemExit("no catalog tab")
        cdp = CDP(tab["webSocketDebuggerUrl"])
        cdp.call("Page.enable")
        cdp.call("Runtime.enable")
        cdp.call(
            "Emulation.setDeviceMetricsOverride",
            {"width": 1400, "height": 900, "deviceScaleFactor": 1, "mobile": False},
        )
        for _ in range(40):
            href = cdp.eval("Promise.resolve(location.href)")
            has = cdp.eval("Promise.resolve(!!document.getElementById('searchChrome'))")
            if href and "CATALOG-portable" in str(href) and has:
                break
            time.sleep(0.2)
        time.sleep(0.6)
        data = cdp.eval(JS)
        __import__("pathlib").Path(OUT).write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(json.dumps(data, indent=2))
    finally:
        proc.kill()


if __name__ == "__main__":
    main()
