#!/usr/bin/env python3
"""Headless CDP: Index Window/Embed load + mobile polish checks."""
import json, os, shutil, subprocess, time, urllib.request

import websocket

PORT = 9534
UD = "/tmp/catalog-ix-load-cdp2"
URL_K = "http://127.0.0.1:8797/KONTAKT-CATALOG-portable.html?v=ixload3"
URL_DS = "http://127.0.0.1:8797/DS-CATALOG-portable.html?v=ixload3"


def wait_http(url, n=40):
    for _ in range(n):
        try:
            urllib.request.urlopen(url, timeout=0.4)
            return True
        except Exception:
            time.sleep(0.15)
    return False


class Cdp:
    def __init__(self, wsurl):
        self.ws = websocket.create_connection(wsurl, timeout=20)
        self.n = 0

    def send(self, method, params=None, wait=True):
        self.n += 1
        mid = self.n
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        if not wait:
            return None
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == mid:
                return msg

    def eval(self, expr, await_p=False):
        params = {"expression": expr, "returnByValue": True, "awaitPromise": bool(await_p)}
        msg = self.send("Runtime.evaluate", params)
        res = (msg.get("result") or {}).get("result") or {}
        if res.get("subtype") == "error":
            return {"_err": res.get("description") or res}
        return res.get("value")

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


SNAP = r"""(function(){
  var ix=document.getElementById('catalogIndex');
  var il=document.getElementById('catalogIndexList');
  var main=document.getElementById('catalogMain');
  var h2=document.querySelector('#catalogMain .catalog-body h2');
  var js=document.getElementById('catalogJumpStack');
  var es=document.getElementById('catalogEdgeStack');
  var sfs=document.getElementById('searchStripFs');
  var kfs=document.getElementById('kwStripFs');
  var inp=document.getElementById('searchInput');
  var more=document.getElementById('searchStripMorePop');
  function r(el){if(!el)return null;var b=el.getBoundingClientRect();var cs=getComputedStyle(el);return {d:cs.display,v:cs.visibility,p:cs.position,op:cs.opacity,z:cs.zIndex,ov:cs.overflow,x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height)};}
  var ir=ix?ix.getBoundingClientRect():null, hr=h2?h2.getBoundingClientRect():null;
  return {
    vw:innerWidth, vh:innerHeight, orient:innerWidth>=innerHeight?'land':'port',
    body:document.body.className,
    contentOn:document.body.classList.contains('content-window-on'),
    ixWin:document.body.classList.contains('index-window-open'),
    collapsed:!!(ix&&ix.classList.contains('is-collapsed')),
    embed:!!(ix&&ix.classList.contains('is-embedded')),
    parent:ix&&ix.parentElement?(ix.parentElement.id||ix.parentElement.className||''):'',
    listN:il?il.children.length:0,
    ix:r(ix), il:r(il), main:r(main), h2:r(h2),
    gap:ir&&hr?Math.round(hr.top-ir.bottom):null,
    jump:r(js), edge:r(es),
    sfs:r(sfs), kfs:r(kfs),
    kwLabel:((document.getElementById('filterToggle')||{}).textContent||'').replace(/\s+/g,' ').trim(),
    moreHasFs:!!(more&&/fullscreen/i.test(more.textContent||'')),
    active:document.activeElement&&document.activeElement.id,
    pref:(typeof readIndexEmbedPref==='function')?readIndexEmbedPref():null
  };
})()"""


def run_page(cdp, url, w, h, label):
    cdp.send("Emulation.setDeviceMetricsOverride", {
        "width": w, "height": h, "deviceScaleFactor": 2, "mobile": True
    })
    cdp.send("Page.navigate", {"url": url})
    cdp.send("Page.enable")
    # wait load via Runtime
    for _ in range(50):
        time.sleep(0.2)
        ready = cdp.eval("document.readyState")
        if ready == "complete":
            has = cdp.eval("!!(window.toggleCatalogIndex && document.getElementById('catalogIndex'))")
            if has:
                break
    time.sleep(0.8)
    boot = cdp.eval(SNAP)
    cdp.eval("typeof toggleCatalogIndex==='function' && toggleCatalogIndex()")
    time.sleep(0.5)
    expanded = cdp.eval(SNAP)
    cdp.eval("typeof toggleIndexEmbed==='function' && toggleIndexEmbed()")
    time.sleep(0.5)
    embed = cdp.eval(SNAP)
    # expand if still collapsed after embed
    if embed and embed.get("collapsed"):
        cdp.eval("typeof toggleCatalogIndex==='function' && toggleCatalogIndex()")
        time.sleep(0.4)
        embed = cdp.eval(SNAP)
    # Search FS hide Index: open Search in Sides then enter menu FS
    cdp.eval("""(function(){
      if(typeof setDisplayMode==='function') setDisplayMode('sides',{pick:true,keepMenus:true});
      if(typeof expandSearchMenu==='function') expandSearchMenu();
      else if(typeof toggleHdrSearch==='function') toggleHdrSearch();
      if(typeof portableEnterMenuFs==='function') portableEnterMenuFs('search');
      else if(typeof setAcFullscreen==='function') setAcFullscreen(true);
    })()""")
    time.sleep(0.45)
    fs = cdp.eval(SNAP)
    cdp.eval("""(function(){
      if(typeof portableExitMenuFs==='function') portableExitMenuFs();
      else if(typeof setAcFullscreen==='function') setAcFullscreen(false);
    })()""")
    time.sleep(0.25)
    # autofocus check: enable search
    focus = cdp.eval("""(function(){
      var el=document.getElementById('searchInput');
      if(el) el.blur();
      if(typeof expandSearchMenu==='function') expandSearchMenu();
      else if(typeof toggleHdrSearch==='function') toggleHdrSearch();
      return {id:document.activeElement&&document.activeElement.id, tag:document.activeElement&&document.activeElement.tagName};
    })()""")
    # ⋯ menu items
    more = cdp.eval("""(function(){
      if(typeof toggleSearchStripMore==='function') toggleSearchStripMore();
      var pop=document.getElementById('searchStripMorePop');
      var labels=pop?[].slice.call(pop.querySelectorAll('button')).map(function(b){return (b.textContent||'').trim();}):[];
      return {hidden:!!(pop&&pop.hidden), labels:labels};
    })()""")
    # scroll debug
    scroll = cdp.eval("""(function(){
      if(typeof portableEnsureScrollMenus==='function') portableEnsureScrollMenus();
      if(typeof dbgPortableScroll==='function') dbgPortableScroll('cdp-orient',{hyp:'H-OVF'});
      var ac=document.getElementById('acList');
      var kw=document.getElementById('kwbar');
      var cb=document.querySelector('#catalogMain > .catalog-body');
      function s(el){if(!el)return null;var cs=getComputedStyle(el);return {oy:cs.overflowY,h:Math.round(el.getBoundingClientRect().height),sh:el.scrollHeight,ch:el.clientHeight};}
      return {ac:s(ac), kw:s(kw), cb:s(cb), sides:document.body.classList.contains('display-sides'), middle:document.body.classList.contains('display-middle')};
    })()""")
    titles = cdp.eval("""(function(){
      var lead=document.querySelector('.hdr-title-lead');
      var tail=document.querySelector('.hdr-title-tail');
      function r(el){if(!el)return null;var b=el.getBoundingClientRect();return {t:el.textContent,x:Math.round(b.left),r:Math.round(b.right)};}
      return {lead:r(lead), tail:r(tail), vw:innerWidth};
    })()""")
    return {
        "label": label, "boot": boot, "expanded": expanded, "embed": embed,
        "fs": fs, "focus": focus, "more": more, "scroll": scroll, "titles": titles
    }


def main():
    shutil.rmtree(UD, ignore_errors=True)
    os.makedirs(UD, exist_ok=True)
    proc = subprocess.Popen(
        [
            "/usr/bin/chromium", "--headless=new", "--disable-gpu",
            f"--remote-debugging-port={PORT}", f"--user-data-dir={UD}",
            "--remote-allow-origins=*",
            "--no-first-run", "--noerrdialogs", "--ozone-platform=headless",
            "--ozone-override-screen-size=390,844", "--use-angle=swiftshader-webgl",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        if not wait_http(f"http://127.0.0.1:{PORT}/json/version"):
            raise SystemExit("cdp not up")
        tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list"))
        page = next((t for t in tabs if t.get("type") == "page" and t.get("webSocketDebuggerUrl")), None)
        if not page:
            page = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/new"))
        wsurl = page["webSocketDebuggerUrl"]
        cdp = Cdp(wsurl)
        cdp.send("Runtime.enable")
        out = []
        out.append(run_page(cdp, URL_K, 390, 844, "K-port"))
        # reload with embed pref from previous toggle
        cdp.send("Page.navigate", {"url": URL_K + "&reload=1"})
        time.sleep(1.6)
        out.append({"label": "K-reload-embed-pref", "boot": cdp.eval(SNAP)})
        cdp.eval("typeof toggleCatalogIndex==='function' && toggleCatalogIndex()")
        time.sleep(0.45)
        out.append({"label": "K-reload-embed-expand", "snap": cdp.eval(SNAP)})
        out.append(run_page(cdp, URL_K, 844, 390, "K-land"))
        out.append(run_page(cdp, URL_DS, 390, 844, "DS-port"))
        dump = json.dumps(out, indent=2, default=str)
        open("/tmp/ix-load-cdp.json", "w", encoding="utf-8").write(dump)
        print(dump[:20000])
        cdp.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    main()
