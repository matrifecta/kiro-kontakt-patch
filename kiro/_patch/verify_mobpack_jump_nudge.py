#!/usr/bin/env python3
"""Thorough MOBPACK + jump-scrollbar-nudge verification via local Chromium CDP.
No fetch() inside Runtime.evaluate expressions.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import time
import urllib.request
from pathlib import Path

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_mobpack_jump_nudge.json")
PORT = 9561
HTTP = 8797
PROFILE = "/tmp/catalog-mobpack-jump"
CHROME = "/usr/bin/chromium"

os.makedirs(PROFILE, exist_ok=True)


def wait_dbg(timeout=20):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json", timeout=1))
            pages = [t for t in tabs if t.get("type") == "page" and t.get("webSocketDebuggerUrl")]
            if pages:
                return pages[0]
        except Exception:
            time.sleep(0.2)
    raise SystemExit("no debugger tab")


class CDP:
    def __init__(self, ws_url):
        import websocket

        self.ws = websocket.create_connection(ws_url, timeout=60)
        self.id = 0

    def call(self, method, params=None, timeout=90):
        self.id += 1
        mid = self.id
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        t0 = time.time()
        while time.time() - t0 < timeout:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})
        raise TimeoutError(method)

    def eval(self, expr):
        r = self.call("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": False})
        if r.get("exceptionDetails"):
            raise RuntimeError(r["exceptionDetails"])
        return r.get("result", {}).get("value")


def set_view(cdp, w, h, mobile=False):
    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": w,
            "height": h,
            "deviceScaleFactor": 1,
            "mobile": mobile,
            "screenOrientation": {
                "type": "portraitPrimary" if h >= w else "landscapePrimary",
                "angle": 0 if h >= w else 90,
            },
        },
    )
    time.sleep(0.25)


def wait_ready(cdp):
    for _ in range(80):
        try:
            if cdp.eval("!!(document.getElementById('catalogMain')&&typeof placeCatalogJumpStack==='function')"):
                return
        except Exception:
            pass
        time.sleep(0.2)
    raise SystemExit("catalog not ready")


def nav(cdp, url):
    cdp.call("Page.enable")
    cdp.call("Runtime.enable")
    cdp.call("Page.navigate", {"url": url})
    time.sleep(1.2)
    wait_ready(cdp)
    time.sleep(0.4)


JUMP_CHECK = r"""
(() => {
  if (typeof placeCatalogJumpStack === 'function') placeCatalogJumpStack();
  var stack = document.getElementById('catalogJumpStack');
  var main = document.getElementById('catalogMain');
  var sc = (typeof catalogContentScroller === 'function' && catalogContentScroller()) || main;
  var top = stack && stack.querySelector('a.top');
  var bot = stack && stack.querySelector('a.bottom');
  var jr = stack ? stack.getBoundingClientRect() : null;
  var mr = main ? main.getBoundingClientRect() : null;
  var sr = sc ? sc.getBoundingClientRect() : null;
  var sbw = sc ? Math.max(0, (sc.offsetWidth || 0) - (sc.clientWidth || 0)) : 0;
  var stripe = document.getElementById('catalogMainHoverStripe');
  var str = stripe && !stripe.hidden ? stripe.getBoundingClientRect() : null;
  var trackLeft = sr ? (sr.right - Math.max(sbw, str ? str.width : 12, 12)) : null;
  var hits = [];
  if (sr) {
    var xs = [sr.right - 4, sr.right - 8, sr.right - 12];
    var y = jr ? (jr.top + jr.height / 2) : (sr.top + sr.height * 0.7);
    xs.forEach(function (x) {
      var el = document.elementFromPoint(x, y);
      var a = el && el.closest && el.closest('a.top,a.bottom,#catalogJumpStack');
      hits.push({
        x: Math.round(x),
        y: Math.round(y),
        tag: el ? ((el.id || '') + '.' + (el.className || '')).toString().slice(0, 48) : null,
        hitJump: !!a
      });
    });
  }
  var gutter = typeof catalogJumpScrollbarGutter === 'function' ? catalogJumpScrollbarGutter(main) : null;
  return {
    portable: !!window.CATALOG_PORTABLE,
    ns: window.CATALOG_NS,
    vw: innerWidth, vh: innerHeight,
    cls: document.body.className,
    gutter: gutter,
    sbw: sbw,
    jump: jr ? { l: Math.round(jr.left), r: Math.round(jr.right), t: Math.round(jr.top), b: Math.round(jr.bottom), vis: getComputedStyle(stack).visibility, disp: getComputedStyle(stack).display } : null,
    main: mr ? { l: Math.round(mr.left), r: Math.round(mr.right) } : null,
    sc: sr ? { id: sc.id || sc.className, l: Math.round(sr.left), r: Math.round(sr.right), sh: sc.scrollHeight, ch: sc.clientHeight } : null,
    stripe: str ? { l: Math.round(str.left), r: Math.round(str.right), w: Math.round(str.width), hidden: !!stripe.hidden } : null,
    trackLeft: trackLeft != null ? Math.round(trackLeft) : null,
    jumpLeftOfTrack: !!(jr && trackLeft != null && jr.right <= trackLeft - 1),
    gap: (jr && trackLeft != null) ? Math.round(trackLeft - jr.right) : null,
    hits: hits,
    scrollbarClear: hits.every(function (h) { return !h.hitJump; }),
    hasTop: !!(top && getComputedStyle(top).display !== 'none'),
    hasBot: !!(bot && getComputedStyle(bot).display !== 'none')
  };
})()
"""

PACK_JS = r"""
(() => {
  function box(el) {
    if (!el) return null;
    var r = el.getBoundingClientRect();
    var cs = getComputedStyle(el);
    return { x: Math.round(r.left), y: Math.round(r.top), r: Math.round(r.right), b: Math.round(r.bottom), w: Math.round(r.width), h: Math.round(r.height), disp: cs.display, vis: cs.visibility, pe: cs.pointerEvents, parent: (el.parentElement && (el.parentElement.id || el.parentElement.className) || '').toString().slice(0, 40), z: cs.zIndex };
  }
  function ov(a, b) {
    if (!a || !b || a.w < 2 || b.w < 2 || a.disp === 'none' || b.disp === 'none' || a.vis === 'hidden') return false;
    return !(a.r < b.x + 2 || a.x > b.r - 2 || a.b < b.y + 2 || a.y > b.b - 2);
  }
  var lead = document.querySelector('.hdr-title-lead');
  var tail = document.querySelector('.hdr-title-tail');
  var lr = lead ? lead.getBoundingClientRect() : null;
  var tr = tail ? tail.getBoundingClientRect() : null;
  var h1 = document.querySelector('h1#top');
  var h1r = h1 ? h1.getBoundingClientRect() : null;
  var mid = innerWidth / 2;
  var kwFs = document.getElementById('kwStripFs');
  var kwBack = document.getElementById('kwFsBack');
  var kwHide = document.getElementById('kwStripHide');
  var cs = document.getElementById('catSwitch');
  var pop = document.getElementById('kwStripMorePop');
  var fp = document.getElementById('filterPanel') || document.querySelector('#filterWrap .filter-panel');
  var ix = document.getElementById('catalogIndex');
  var note = document.getElementById('catalogDocNote');
  var card = document.querySelector('.entry.selected:not(.highlight)') || document.querySelector('.entry:not(.is-hidden)');
  var jump = document.getElementById('catalogJumpStack');
  var edge = document.getElementById('catalogEdgeStack');
  var stripe = document.getElementById('catalogMainHoverStripe');
  var search = document.getElementById('searchChrome');
  var fw = document.getElementById('filterWrap');
  var sc = (typeof catalogContentScroller === 'function' && catalogContentScroller()) || document.getElementById('catalogMain');
  return {
    vw: innerWidth, vh: innerHeight, portable: !!window.CATALOG_PORTABLE, ns: window.CATALOG_NS,
    cls: document.body.className,
    fill: document.body.classList.contains('index-fill-doc'),
    preview: document.body.classList.contains('chosen-preview-open'),
    titles: {
      lead: lr ? { t: lead.textContent, x: Math.round(lr.left), cx: Math.round(lr.left + lr.width / 2), w: Math.round(lr.width), js: getComputedStyle(lead).justifySelf } : null,
      tail: tr ? { t: tail.textContent, x: Math.round(tr.left), cx: Math.round(tr.left + tr.width / 2), w: Math.round(tr.width), js: getComputedStyle(tail).justifySelf } : null,
      gap: (h1 && getComputedStyle(h1).columnGap) || null,
      mid: Math.round(mid),
      h1: h1r ? { x: Math.round(h1r.left), r: Math.round(h1r.right), w: Math.round(h1r.width) } : null
    },
    kw: {
      fs: box(kwFs),
      back: box(kwBack),
      hide: box(kwHide),
      cats: box(cs),
      pop: pop ? { hidden: pop.hasAttribute('hidden'), disp: getComputedStyle(pop).display, containsCs: !!(cs && pop.contains(cs)) } : null,
      fpHasCs: !!(cs && fp && fp.contains(cs)),
      catsOpen: document.body.classList.contains('kw-cats-open'),
      fsOpen: document.body.classList.contains('kw-fs-open')
    },
    ix: box(ix),
    note: box(note),
    card: box(card),
    jump: box(jump),
    edge: box(edge),
    stripe: box(stripe),
    search: box(search),
    filter: box(fw),
    overlay: {
      stripeKw: ov(box(stripe), box(fw)),
      stripeSearch: ov(box(stripe), box(search)),
      jumpKw: ov(box(jump), box(fw)),
      jumpSearch: ov(box(jump), box(search)),
      edgeKw: ov(box(edge), box(fw)),
      ixCard: ov(box(ix), box(card))
    },
    sc: sc ? { id: sc.id || sc.className, st: sc.scrollTop, sh: sc.scrollHeight, ch: sc.clientHeight } : null,
    ixEmbedded: !!(ix && ix.classList.contains('is-embedded')),
    ixCollapsed: !!(ix && ix.classList.contains('is-collapsed')),
    cardTf: card ? getComputedStyle(card).transform : null,
    cardPos: card ? getComputedStyle(card).position : null
  };
})()
"""


def run_desktop_jump(cdp, name, url, mode="sides"):
    nav(cdp, url)
    set_view(cdp, 1400, 900, mobile=False)
    cdp.eval(
        f"if(typeof setDisplayMode==='function')setDisplayMode('{mode}',{{pick:true}});"
        "document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed');"
        "if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();"
    )
    time.sleep(0.5)
    cdp.eval("if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();")
    time.sleep(0.2)
    data = cdp.eval(JUMP_CHECK)
    data["file"] = name
    data["mode"] = mode
    data["pass"] = bool(data.get("jumpLeftOfTrack") and data.get("scrollbarClear") and data.get("hasTop") and data.get("hasBot") and data.get("jump") and data["jump"].get("disp") != "none")
    return data


def click_jump(cdp, which):
    before = cdp.eval(
        "var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||document.getElementById('catalogMain');"
        "sc?{st:sc.scrollTop,sh:sc.scrollHeight,ch:sc.clientHeight,id:sc.id||sc.className}:null"
    )
    cdp.eval(
        f"var a=document.querySelector('#catalogJumpStack a.{'top' if which=='top' else 'bottom'}');"
        "if(a){a.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));a.click();}"
    )
    time.sleep(0.55)
    after = cdp.eval(
        "var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||document.getElementById('catalogMain');"
        "sc?{st:sc.scrollTop,sh:sc.scrollHeight,ch:sc.clientHeight,id:sc.id||sc.className}:null"
    )
    moved = abs((after or {}).get("st", 0) - (before or {}).get("st", 0)) > 8
    return {"before": before, "after": after, "moved": moved, "which": which}


def run_portable_pack(cdp, name, url):
    nav(cdp, url)
    set_view(cdp, 390, 844, mobile=True)
    time.sleep(0.4)
    out = {"file": name, "checks": {}}

    # content-only
    cdp.eval("if(typeof setDisplayMode==='function')setDisplayMode('content',{pick:true});")
    time.sleep(0.4)
    cdp.eval("if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();")
    out["checks"]["titles_content"] = cdp.eval(PACK_JS)
    out["checks"]["jump_content"] = cdp.eval(JUMP_CHECK)
    out["checks"]["goBot"] = click_jump(cdp, "bottom")
    out["checks"]["goTop"] = click_jump(cdp, "top")

    # overlay Sides KW on
    cdp.eval("if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});")
    time.sleep(0.35)
    cdp.eval(
        "if(typeof expandKwMenu==='function')expandKwMenu();"
        "if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();"
        "if(typeof window.syncMainHoverStripe==='function')window.syncMainHoverStripe();"
    )
    time.sleep(0.25)
    out["checks"]["sides_kw"] = cdp.eval(PACK_JS)

    cdp.eval("if(typeof toggleKwStripMore==='function')toggleKwStripMore();")
    time.sleep(0.2)
    open1 = cdp.eval(PACK_JS)
    cdp.eval("if(typeof toggleKwStripMore==='function')toggleKwStripMore();")
    time.sleep(0.15)
    closed = cdp.eval(PACK_JS)
    cdp.eval("if(typeof toggleKwStripMore==='function')toggleKwStripMore();")
    time.sleep(0.15)
    open2 = cdp.eval(PACK_JS)
    out["checks"]["cats_open1"] = open1["kw"]
    out["checks"]["cats_closed"] = closed["kw"]
    out["checks"]["cats_open2"] = open2["kw"]

    cdp.eval("if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();")
    time.sleep(0.25)
    cdp.eval("if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();")
    out["checks"]["sides_flip"] = cdp.eval(PACK_JS)

    # Middle
    cdp.eval("if(typeof setDisplayMode==='function')setDisplayMode('middle',{pick:true});")
    time.sleep(0.35)
    cdp.eval("if(typeof expandKwMenu==='function')expandKwMenu(); if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();")
    out["checks"]["middle_kw"] = cdp.eval(PACK_JS)

    # Index fill in content
    cdp.eval("if(typeof setDisplayMode==='function')setDisplayMode('content',{pick:true});")
    time.sleep(0.3)
    cdp.eval(
        "var ix=document.getElementById('catalogIndex');"
        "if(ix&&ix.classList.contains('is-embedded')&&typeof toggleIndexEmbed==='function')toggleIndexEmbed();"
        "if(ix&&ix.classList.contains('is-collapsed')&&typeof toggleCatalogIndex==='function')toggleCatalogIndex();"
        "if(typeof applyIndexFillDocStyles==='function')applyIndexFillDocStyles();"
    )
    time.sleep(0.25)
    out["checks"]["ix_fill_content"] = cdp.eval(PACK_JS)
    cdp.eval("if(typeof toggleCatalogIndex==='function')toggleCatalogIndex();")
    time.sleep(0.15)
    out["checks"]["ix_collapsed"] = cdp.eval(PACK_JS)
    cdp.eval("if(typeof toggleCatalogIndex==='function')toggleCatalogIndex();")
    time.sleep(0.2)

    # Index fill sides one-menu / both
    cdp.eval("if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});")
    time.sleep(0.3)
    cdp.eval(
        "var ix=document.getElementById('catalogIndex');"
        "if(ix&&ix.classList.contains('is-embedded')&&typeof toggleIndexEmbed==='function')toggleIndexEmbed();"
        "if(ix&&ix.classList.contains('is-collapsed')&&typeof toggleCatalogIndex==='function')toggleCatalogIndex();"
        "document.body.classList.add('search-chrome-collapsed');"
        "if(typeof expandKwMenu==='function')expandKwMenu();"
        "if(typeof applyIndexFillDocStyles==='function')applyIndexFillDocStyles();"
    )
    time.sleep(0.25)
    out["checks"]["ix_fill_sides_one"] = cdp.eval(PACK_JS)
    cdp.eval(
        "document.body.classList.remove('search-chrome-collapsed');"
        "if(typeof expandKwMenu==='function')expandKwMenu();"
        "if(typeof applyIndexFillDocStyles==='function')applyIndexFillDocStyles();"
    )
    time.sleep(0.2)
    out["checks"]["ix_fill_sides_both"] = cdp.eval(PACK_JS)

    cdp.eval("if(typeof setDisplayMode==='function')setDisplayMode('middle',{pick:true});")
    time.sleep(0.3)
    cdp.eval(
        "var ix=document.getElementById('catalogIndex');"
        "if(ix&&ix.classList.contains('is-collapsed')&&typeof toggleCatalogIndex==='function')toggleCatalogIndex();"
        "if(typeof applyIndexFillDocStyles==='function')applyIndexFillDocStyles();"
    )
    time.sleep(0.2)
    out["checks"]["ix_fill_middle"] = cdp.eval(PACK_JS)

    # KW FS
    cdp.eval(
        "if(typeof expandKwMenu==='function')expandKwMenu();"
        "if(typeof toggleKwFullscreen==='function')toggleKwFullscreen();"
    )
    time.sleep(0.25)
    out["checks"]["kw_fs"] = cdp.eval(PACK_JS)
    cdp.eval("if(typeof toggleKwFullscreen==='function')toggleKwFullscreen();")
    time.sleep(0.15)

    # Preview vs Window Index
    cdp.eval("if(typeof setDisplayMode==='function')setDisplayMode('content',{pick:true});")
    time.sleep(0.25)
    cdp.eval(
        "var ix=document.getElementById('catalogIndex');"
        "if(ix&&ix.classList.contains('is-embedded')&&typeof toggleIndexEmbed==='function')toggleIndexEmbed();"
        "if(ix&&ix.classList.contains('is-collapsed')&&typeof toggleCatalogIndex==='function')toggleCatalogIndex();"
        "if(typeof applyIndexFillDocStyles==='function')applyIndexFillDocStyles();"
        "var card=document.querySelector('.entry:not(.is-hidden):not(.highlight)');"
        "if(card){card.classList.add('selected');document.body.classList.add('chosen-preview-open');}"
        "if(typeof applyIndexFillDocStyles==='function')applyIndexFillDocStyles();"
        "if(typeof syncPortableIndexContentGap==='function')syncPortableIndexContentGap();"
    )
    time.sleep(0.25)
    out["checks"]["preview_window_ix"] = cdp.eval(PACK_JS)
    cdp.eval(
        "document.body.classList.remove('chosen-preview-open');"
        "document.querySelectorAll('.entry.selected').forEach(function(e){e.classList.remove('selected');});"
        "if(typeof applyIndexFillDocStyles==='function')applyIndexFillDocStyles();"
    )
    time.sleep(0.2)
    out["checks"]["preview_closed"] = cdp.eval(PACK_JS)

    # Embed Index + preview should NOT hide embed
    cdp.eval(
        "var ix=document.getElementById('catalogIndex');"
        "if(ix&&!ix.classList.contains('is-embedded')&&typeof toggleIndexEmbed==='function')toggleIndexEmbed();"
        "var card=document.querySelector('.entry:not(.is-hidden):not(.highlight)');"
        "if(card){card.classList.add('selected');document.body.classList.add('chosen-preview-open');}"
        "if(typeof applyIndexFillDocStyles==='function')applyIndexFillDocStyles();"
    )
    time.sleep(0.2)
    out["checks"]["preview_embed_ix"] = cdp.eval(PACK_JS)
    cdp.eval(
        "document.body.classList.remove('chosen-preview-open');"
        "document.querySelectorAll('.entry.selected').forEach(function(e){e.classList.remove('selected');});"
        "var ix=document.getElementById('catalogIndex');"
        "if(ix&&ix.classList.contains('is-embedded')&&typeof toggleIndexEmbed==='function')toggleIndexEmbed();"
    )
    return out


def judge(report):
    fails = []

    def need(cond, msg):
        if not cond:
            fails.append(msg)

    for d in report.get("desktop", []):
        need(d.get("pass"), f"desktop jump {d.get('file')} {d.get('mode')}: leftOfTrack={d.get('jumpLeftOfTrack')} clear={d.get('scrollbarClear')} gap={d.get('gap')} jump={d.get('jump')}")

    for p in report.get("portable", []):
        name = p.get("file")
        c = p.get("checks", {})
        t = (c.get("titles_content") or {}).get("titles") or {}
        lead, tail = t.get("lead") or {}, t.get("tail") or {}
        if lead and tail and t.get("h1"):
            left_half_cx = t["h1"]["x"] + t["h1"]["w"] / 4
            right_half_cx = t["h1"]["x"] + 3 * t["h1"]["w"] / 4
            need(abs(lead.get("cx", 0) - left_half_cx) < 40, f"{name} lead not centered in left half cx={lead.get('cx')} vs {left_half_cx}")
            need(abs(tail.get("cx", 0) - right_half_cx) < 40, f"{name} tail not centered in right half cx={tail.get('cx')} vs {right_half_cx}")
            need(lead.get("js") == "center", f"{name} lead justify-self {lead.get('js')}")
        need(c.get("goBot", {}).get("moved"), f"{name} goBot did not scroll {c.get('goBot')}")
        need(c.get("goTop", {}).get("moved"), f"{name} goTop did not scroll {c.get('goTop')}")
        o1, cl, o2 = c.get("cats_open1") or {}, c.get("cats_closed") or {}, c.get("cats_open2") or {}
        need(o1.get("catsOpen") and o1.get("fpHasCs") and not (o1.get("pop") or {}).get("containsCs"), f"{name} cats open1 {o1}")
        need((o1.get("cats") or {}).get("disp") == "flex" and (o1.get("cats") or {}).get("h", 0) > 8, f"{name} cats not visible in pills window {o1.get('cats')}")
        need(not cl.get("catsOpen") or (cl.get("cats") or {}).get("disp") == "none", f"{name} cats did not hide")
        need(o2.get("catsOpen") and o2.get("fpHasCs"), f"{name} cats open2")
        for key in ("sides_kw", "sides_flip", "middle_kw"):
            ov = (c.get(key) or {}).get("overlay") or {}
            need(not ov.get("stripeKw") and not ov.get("jumpKw") and not ov.get("edgeKw"), f"{name} {key} overlay {ov}")
        fill = c.get("ix_fill_content") or {}
        need(fill.get("fill"), f"{name} index fill content false")
        ix, note = fill.get("ix") or {}, fill.get("note") or {}
        if ix and note and note.get("h", 0) > 8:
            need(ix.get("b", 0) <= note.get("y", 9999) + 12, f"{name} index overflow past About ix.b={ix.get('b')} note.y={note.get('y')}")
        need(ix.get("b", 0) <= (fill.get("vh") or 844) + 8, f"{name} index overflow screen")
        need((c.get("ix_collapsed") or {}).get("ixCollapsed"), f"{name} collapse did not restore bar")
        kwfs = c.get("kw_fs") or {}
        kw = kwfs.get("kw") or {}
        need(kw.get("fsOpen"), f"{name} kw fs not open")
        need((kw.get("back") or {}).get("disp") == "none" or (kw.get("back") or {}).get("w", 1) == 0, f"{name} kw back visible {kw.get('back')}")
        need((kw.get("fs") or {}).get("disp") not in ("none",), f"{name} kw fs btn hidden {kw.get('fs')}")
        prev = c.get("preview_window_ix") or {}
        need(prev.get("preview"), f"{name} preview not open")
        need((prev.get("ix") or {}).get("vis") == "hidden" or (prev.get("ix") or {}).get("disp") == "none" or (prev.get("ix") or {}).get("pe") == "none", f"{name} window index still visible over preview {prev.get('ix')}")
        need((prev.get("cardPos") or "") == "fixed", f"{name} preview card not fixed {prev.get('cardPos')}")
        need("matrix" in (prev.get("cardTf") or "") or "translate" in (prev.get("cardTf") or ""), f"{name} preview transform {prev.get('cardTf')}")
        need(not (c.get("preview_closed") or {}).get("preview"), f"{name} preview stayed open")
        emb = c.get("preview_embed_ix") or {}
        need(emb.get("ixEmbedded"), f"{name} embed not on for preview-embed check")
        need((emb.get("ix") or {}).get("vis") != "hidden", f"{name} embed index hidden during preview (should stay)")
        jc = c.get("jump_content") or {}
        need(jc.get("scrollbarClear"), f"{name} portable jump still hits scrollbar {jc.get('hits')}")
    return fails


def main():
    proc = subprocess.Popen(
        [
            CHROME,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            f"--remote-debugging-port={PORT}",
            "--remote-allow-origins=*",
            f"--user-data-dir={PROFILE}",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    report = {"desktop": [], "portable": [], "fails": []}
    try:
        tab = wait_dbg()
        cdp = CDP(tab["webSocketDebuggerUrl"])
        cdp.call("Page.enable")
        cdp.call("Runtime.enable")

        report["desktop"].append(run_desktop_jump(cdp, "KONTAKT-CATALOG.html", f"http://127.0.0.1:{HTTP}/KONTAKT-CATALOG.html?v=jump1", "sides"))
        report["desktop"].append(run_desktop_jump(cdp, "DS-CATALOG.html", f"http://127.0.0.1:{HTTP}/DS-CATALOG.html?v=jump1", "sides"))
        report["desktop"].append(run_desktop_jump(cdp, "KONTAKT-CATALOG.html", f"http://127.0.0.1:{HTTP}/KONTAKT-CATALOG.html?v=jump1b", "middle"))

        report["portable"].append(run_portable_pack(cdp, "KONTAKT-CATALOG-portable.html", f"http://127.0.0.1:{HTTP}/KONTAKT-CATALOG-portable.html?v=pack1"))
        report["portable"].append(run_portable_pack(cdp, "DS-CATALOG-portable.html", f"http://127.0.0.1:{HTTP}/DS-CATALOG-portable.html?v=pack1"))

        report["fails"] = judge(report)
        report["ok"] = not report["fails"]
    finally:
        try:
            proc.send_signal(signal.SIGTERM)
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("ok" if report.get("ok") else "FAIL")
    for f in report.get("fails") or []:
        print(" -", f)
    # compact desktop summary
    for d in report.get("desktop") or []:
        print("desktop", d.get("file"), d.get("mode"), "pass", d.get("pass"), "gap", d.get("gap"), "gutter", d.get("gutter"), "jumpR", (d.get("jump") or {}).get("r"), "track", d.get("trackLeft"))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
