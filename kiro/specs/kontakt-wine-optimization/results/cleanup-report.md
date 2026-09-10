# Kontakt Content Cleanup Report

Generated from `kontakt_scan.py` (library-root granularity) across `/mnt/workspace`,
`/mnt/storage`, `/mnt/wd_black`. Read-only scan; nothing was modified.

## Final classification counts

| Category   | Count | Meaning                                             |
|------------|-------|-----------------------------------------------------|
| player     | 35    | Real encoded Player libraries (keep)                |
| custom     | 37    | Loose instrument libraries with samples (keep)      |
| presets    | 0     |                                                     |
| incomplete | 13    | Suspect — reviewed below                            |
| excluded   | 850   | Non-Kontakt (plugins, games, mods) — do NOT register|
| empty      | 3     | Noise                                               |

Per-category file lists are in `results/scan/*.tsv`.

## Highest-confidence action (biggest win)

**Unregister `D:\PROGRAMS\VST, Samples & DAW\` from Kontakt Import Content.**

This tree is overwhelmingly non-Kontakt audio PLUGINS (Accentize, BLEASS, EZDrummer,
iZotope, Mastering The Mix, XLN, etc.), plus loose/broken instrument stubs. It is the
dominant source of wasted scan time and nearly all flagged "incomplete" items live here.
Removing this single registered location eliminates most of the junk scanning at once.

Also remove the two **XLN Audio** entries and the broken **`F:\...\User Content`**
User-Presets entry (F: no longer exists).

## Incomplete list (13) — reviewed

Genuinely broken / not Kontakt content (safe to remove/ignore):
- `Keyscape - 13` (inst=13, samp=0) — Keyscape is Spectrasonics, not Kontakt; stray stubs
- `Vir2 Mojo Horn Section/.../__MACOSX/EXTRACTED` (inst=153, samp=0) — Mac archive artifact
- `60s Klira Violin Bass` (inst=1, samp=0, 4 files) — broken stub
- `Acoustic Blues Guitar Strummer` (inst=1, samp=0, 4 files) — broken stub

Not actually broken (normal split structure or duplicates — leave alone):
- `Leap - Acoustic Drums / Hot Vocals / Soul Gold` (samp=160, inst=0) — sample payload
  folders; the .nki side is registered separately (also duplicated in Kontakt Vst-i)
- `LM - Reel People Broken Beat ...2/3/4/5` (inst=N, samp=0) — sampler patches whose
  samples are external/registered elsewhere
- `THAT.SOUND.ORGANIC.PERCUSSION/z PRESETS` (inst=13, samp=0) — presets subfolder

## Duplication found

Several libraries are registered/present in BOTH:
- `D:\PROGRAMS\VST, Samples & DAW\FROM TIXATI DL\...`  AND
- `D:\VST Install\Kontakt Vst-i\...`
Examples: Leap - Hot Vocals, Dhol Ensemble, 8Dio Phenex, Acoustic Blues Guitar Strummer.
Keep the copy under `Kontakt Vst-i`; the `FROM TIXATI DL` copies go away when the
`PROGRAMS\VST, Samples & DAW` location is unregistered.

## Keep (authoritative "good" content)

- `results/scan/player.tsv` (35) — register via Library Manager
- `results/scan/custom.tsv` (37) — register via Import Content -> Custom Libraries

## Scanner limitation notes

- Classification is at library-root granularity. "samp=0" with instruments can mean
  either broken OR samples registered separately; the report distinguishes these by
  context (file count, __MACOSX, known non-Kontakt names).
- Game/OS/mod trees are skipped via SKIP_DIRS; plugin trees under PROGRAMS/VST,Samples
  are force-excluded unless they contain real Kontakt markers.
