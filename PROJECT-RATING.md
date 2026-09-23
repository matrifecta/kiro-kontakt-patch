# Project Rating

An honest structural assessment of the self-contained catalog viewer files
(`public/catalogs/DS-CATALOG-portable.html`, `public/catalogs/KONTAKT-CATALOG-portable.html`),
grounded in measured signals rather than impressions.

## Rating: fragile-but-functional — roughly **4/10 structural robustness**

It reliably does what it's supposed to (a self-contained, offline catalog viewer),
but it's built in a way that makes each new fix riskier than the last.

## The hard signals (DS file alone)

- **6.5 MB, ~36k lines in a single HTML file** — CSS, JS, and data all inlined.
  No modules, no build step, no tests.
- **~3,770 `!important` declarations** and **~270 `z-index` uses** — the cascade is
  being fought, not used. Specificity is managed by force.
- **~170 versioned `fix-*-v#` markers** (v1→v6 in places) — this is the tell. Each
  marker is a patch layered on a prior patch rather than a fix at the source.
  `LANDSCAPE-PREVIEW-WIDTH` reached v4; the pencil button v2; embed-toolbar v6.
- **~78 orientation/media blocks** interacting with those overrides.

## Why it breaks the way it does

1. **Layered-override architecture.** Behavior is the *net result* of many competing
   `!important` rules across scattered blocks. Changing one means auditing all the
   others that touch the same element — exactly the containing-block/notch/scroll
   bugs that keep recurring.
2. **Device-only failure modes.** The real bugs (abspos resolving against the wrong
   container, `svh`/`dvh`, safe-area double-counting) don't reproduce headless, so
   there's no cheap regression net — only manual on-device testing, which is why
   "well-hidden bugs" is a real risk.
3. **DOM-reparenting for layout** (e.g. `syncHlNoteBtnPlacement` moving the note
   button) couples JS state to CSS assumptions. Robust when it works, but invisible
   coupling — a future CSS change can silently break placement.

## What's actually good

- **Self-containment** is a legitimate strength for the goal (portable, no server,
  works offline).
- The **`fix-NAME-v#` + rationale-comment convention** is genuinely disciplined —
  most single-file spaghetti has zero traceability; here you can read *why* each
  override exists. That's the main thing keeping it maintainable.
- Recent changes trend toward **root-cause fixes** (direct-child reparenting,
  dropping the JS-measured var for pure `svh`) rather than more band-aids.

## Biggest liabilities, ranked

1. No automated regression coverage for the device-specific layout invariants
   (highest risk).
2. Override depth — specificity is near a ceiling; the next conflicting rule may have
   nowhere to go but more `!important` or inline styles.
3. Single-file size makes review and diffing costly and error-prone.

## Cheapest wins if you want to harden it

- A small Playwright snapshot suite pinning the 4–5 known-fragile states
  (portrait/landscape × expanded/fullscreen × notes-open) at real device viewports.
- A periodic "consolidate the `v#` stack" pass that folds resolved override chains
  back into their base rule so the cascade depth stops growing.

## Net

It's not architecturally *sound*, but it's *legible* fragile — which is the
survivable kind. Thorough manual testing is the right compensating control until
there's an automated net.
