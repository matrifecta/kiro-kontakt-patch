#!/usr/bin/env node
import { spawn } from "node:child_process";
import { setTimeout as delay } from "node:timers/promises";

const PORT = 9334;
const PAGE = "http://127.0.0.1:8788/DS-CATALOG.html";

const chrome = spawn(
  "/usr/bin/chromium",
  [
    "--headless=new",
    "--disable-gpu",
    "--no-first-run",
    "--disable-extensions",
    "--no-sandbox",
    `--remote-debugging-port=${PORT}`,
    "--window-size=1400,900",
    PAGE,
  ],
  { stdio: ["ignore", "pipe", "pipe"] }
);

function cleanup() {
  try {
    chrome.kill("SIGKILL");
  } catch {}
}
process.on("exit", cleanup);

async function waitHttp(path, tries = 50) {
  for (let i = 0; i < tries; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${PORT}${path}`);
      if (r.ok) return r.json();
    } catch {}
    await delay(150);
  }
  throw new Error("CDP HTTP not ready " + path);
}

function attach(ws) {
  const pending = new Map();
  ws.addEventListener("message", (ev) => {
    const data = JSON.parse(ev.data);
    if (data.id && pending.has(data.id)) {
      const { resolve, reject } = pending.get(data.id);
      pending.delete(data.id);
      if (data.error) reject(new Error(JSON.stringify(data.error)));
      else resolve(data.result);
    }
  });
  let i = 0;
  return (method, params = {}) => {
    const id = ++i;
    ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => {
      pending.set(id, { resolve, reject });
      setTimeout(() => {
        if (pending.has(id)) {
          pending.delete(id);
          reject(new Error("timeout " + method));
        }
      }, 30000);
    });
  };
}

const GEOM = `(() => {
  const box = (el) => {
    if (!el) return null;
    const b = el.getBoundingClientRect();
    return {x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height),bottom:Math.round(b.bottom)};
  };
  const fw = document.getElementById("filterWrap");
  const fp = fw && fw.querySelector(".filter-panel");
  const kw = document.getElementById("kwbar");
  const ix = document.getElementById("catalogIndex");
  const cm = document.getElementById("catalogMain");
  const top = document.querySelector("a.top");
  const ts = top && getComputedStyle(top);
  return {
    href: location.href,
    ready: document.readyState,
    title: document.title,
    vh: window.innerHeight,
    vw: window.innerWidth,
    mode: document.body.className,
    fw: box(fw),
    fp: box(fp),
    kw: box(kw),
    ix: box(ix),
    cm: box(cm),
    bottomGap: fw ? Math.round(window.innerHeight - fw.getBoundingClientRect().bottom) : null,
    ixCollapsed: !!(ix && ix.classList.contains("is-collapsed")),
    cmScroll: cm ? Math.round(cm.scrollTop) : null,
    topDisp: ts && ts.display,
    topPos: ts && ts.position,
    topBox: box(top),
    hasSetDisplay: typeof setDisplayMode === "function",
    hasBindDock: typeof bindIndexDock === "function"
  };
})()`;

try {
  await waitHttp("/json/version");
  let list = await waitHttp("/json/list");
  let target = (list || []).find((t) => t.type === "page" && t.webSocketDebuggerUrl);
  if (!target) {
    const created = await fetch(`http://127.0.0.1:${PORT}/json/new`, { method: "PUT" });
    const raw = await created.text();
    try { target = JSON.parse(raw); } catch { throw new Error("json/new: " + raw.slice(0, 200)); }
  }
  if (!target || !target.webSocketDebuggerUrl) throw new Error("no ws " + JSON.stringify(list));
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((res, rej) => {
    ws.addEventListener("open", res);
    ws.addEventListener("error", (e) => rej(e.error || e));
  });
  const call = attach(ws);
  await call("Runtime.enable");
  await call("Page.enable");
  await call("Emulation.setDeviceMetricsOverride", {
    width: 1400,
    height: 900,
    deviceScaleFactor: 1,
    mobile: false,
  });
  await call("Page.navigate", { url: PAGE });
  let first = null;
  for (let i = 0; i < 40; i++) {
    await delay(500);
    first = await call("Runtime.evaluate", { expression: GEOM, returnByValue: true });
    const v = first.result && first.result.value;
    if (v && v.hasSetDisplay && v.vw > 0) break;
    console.error("wait", i, v && v.ready, v && v.href, v && v.vw);
  }
  console.error("first", JSON.stringify(first.result && first.result.value));
  await call("Runtime.evaluate", { expression: "window.setDisplayMode && setDisplayMode('sides')" });
  await delay(600);
  const sides = (await call("Runtime.evaluate", { expression: GEOM, returnByValue: true })).result.value;
  await call("Runtime.evaluate", {
    expression:
      "var cm=document.getElementById('catalogMain'); if(cm){cm.scrollTop=500;} if(typeof syncIndexDock==='function')syncIndexDock();",
  });
  await delay(250);
  const afterScroll = (await call("Runtime.evaluate", { expression: GEOM, returnByValue: true })).result.value;
  await call("Runtime.evaluate", { expression: "typeof toggleCatalogIndex==='function' && toggleCatalogIndex();" });
  await delay(200);
  const afterToggle = (await call("Runtime.evaluate", { expression: GEOM, returnByValue: true })).result.value;
  await call("Runtime.evaluate", { expression: "var t=document.querySelector('a.top'); if(t) t.click();" });
  await delay(400);
  const afterTop = (await call("Runtime.evaluate", { expression: GEOM, returnByValue: true })).result.value;
  await call("Runtime.evaluate", { expression: "window.setDisplayMode && setDisplayMode('upper')" });
  await delay(400);
  const upper = (await call("Runtime.evaluate", { expression: GEOM, returnByValue: true })).result.value;
  console.log(JSON.stringify({ sides, afterScroll, afterToggle, afterTop, upper }, null, 2));
  ws.close();
} catch (err) {
  console.error(String(err && err.stack || err));
  process.exitCode = 1;
} finally {
  cleanup();
  await delay(150);
}
