#!/usr/bin/env python3
"""One-shot Sides keywords flush screenshot + Upper gap measure."""
import importlib.util
import json
import os
import subprocess
import time
import urllib.request

PORT = 9464
URL = "http://127.0.0.1:8791/DS-CATALOG.html?v=kwflush3"
SHOTS = "/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots"
PROFILE = "/tmp/catalog-kw-flush"
os.makedirs(PROFILE, exist_ok=True)
os.makedirs(SHOTS, exist_ok=True)

spec = importlib.util.spec_from_file_location(
    "v", "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_combo_lib_hist.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.PORT = PORT

JS = r"""
(async function(){
  function wait(ms){return new Promise(function(r){setTimeout(r,ms);});}
  function box(el){if(!el)return null; var r=el.getBoundingClientRect(); return {t:Math.round(r.top),b:Math.round(r.bottom),h:Math.round(r.height)};}
  if(typeof setDisplayMode==='function')setDisplayMode('sides');
  document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed');
  var fw=document.getElementById('filterWrap');
  if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}
  if(typeof setMode==='function')setMode('pick');
  await wait(150);
  var kw=document.getElementById('kwbar');
  var fp=fw&&fw.querySelector('.filter-panel');
  var st=document.getElementById('kwstatus')||document.querySelector('.kwstatus');
  var cs=getComputedStyle(fw);
  var sides={
    mode:'sides', vh:innerHeight, vw:innerWidth,
    fw:box(fw), fp:box(fp), kw:box(kw), st:box(st),
    fwGap:Math.round(innerHeight-fw.getBoundingClientRect().bottom),
    fpGap:Math.round(innerHeight-fp.getBoundingClientRect().bottom),
    kwGap:Math.round(innerHeight-kw.getBoundingClientRect().bottom),
    stGap:st?Math.round(innerHeight-st.getBoundingClientRect().bottom):null,
    borderBottom:cs.borderBottomWidth,
    fwH:cs.height, fwMax:cs.maxHeight,
    shade:fw.classList.contains('kw-shade-height-set'),
    inlineH:fw.style.height||'', inlineMax:fw.style.maxHeight||''
  };
  if(typeof setDisplayMode==='function')setDisplayMode('upper');
  document.body.classList.remove('kw-chrome-collapsed');
  if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}
  await wait(150);
  var upper={
    mode:'upper', vh:innerHeight,
    fw:box(fw), fp:box(fw&&fw.querySelector('.filter-panel')), kw:box(document.getElementById('kwbar')),
    fwGap:fw?Math.round(innerHeight-fw.getBoundingClientRect().bottom):null
  };
  if(typeof setDisplayMode==='function')setDisplayMode('sides');
  document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed');
  if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}
  if(typeof setMode==='function')setMode('pick');
  await wait(80);
  return {sides:sides, upper:upper};
})()
"""


def main():
    urllib.request.urlopen("http://127.0.0.1:8791/DS-CATALOG.html", timeout=2).read(32)
    subprocess.run(["pkill", "-f", f"remote-debugging-port={PORT}"], check=False)
    time.sleep(0.25)
    chrome = next(
        p
        for p in ("/usr/lib/chromium/chromium", "/usr/bin/chromium")
        if os.path.exists(p)
    )
    logf = open("/tmp/catalog-kw-flush.log", "w")
    proc = subprocess.Popen(
        [
            chrome, "--headless=new", "--disable-gpu", "--no-first-run",
            "--disable-extensions", f"--remote-debugging-port={PORT}",
            "--remote-allow-origins=*", f"--user-data-dir={PROFILE}",
            "--noerrdialogs", "--ozone-platform=headless",
            "--ozone-override-screen-size=1400,900", "--use-angle=swiftshader-webgl",
            "about:blank",
        ],
        stdout=logf,
        stderr=subprocess.STDOUT,
    )
    try:
        for _ in range(80):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=1).read()
                break
            except Exception:
                time.sleep(0.2)
        else:
            raise SystemExit("cdp fail")
        tab = mod.new_tab("about:blank")
        cdp = mod.CDP(tab["webSocketDebuggerUrl"])
        cdp.call("Page.enable")
        cdp.call("Runtime.enable")
        cdp.call(
            "Emulation.setDeviceMetricsOverride",
            {"width": 1400, "height": 900, "deviceScaleFactor": 1, "mobile": False},
        )
        cdp.call("Page.navigate", {"url": URL})
        mod.wait_entries(cdp)
        result = cdp.eval(JS)
        data = cdp.call("Page.captureScreenshot", {"format": "png"}).get("data", "")
        open(os.path.join(SHOTS, "D1400-sides-kw-flush.png"), "wb").write(__import__("base64").b64decode(data))
        print(json.dumps(result, indent=2))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    main()
