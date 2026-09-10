# Progress Notes

## Root cause found (Task 2) — CASE SENSITIVITY, not corrupt DBs

The ~10,260 failed lookups were dominated by NTFS mounts being **case-sensitive**.
Kontakt probes lowercase paths (e.g. `.../database/pal/categories.db`) but the on-disk
folder is `PAL` (uppercase). Under the ntfs3 `case_sensitive` mount default on this
CachyOS kernel, `pal` != `PAL`, so every probe failed and retried thousands of times.

Same mechanism explained the `image`, `dist_database`, and `Shared/Resources` misses:
Kontakt's internal casing didn't match the actual on-disk library folder casing
(e.g. `ANALOG STRINGS`, `Acoustic Drums`).

### Fix applied (non-destructive; no DB deletion needed)

Remounted all three content partitions with the ntfs3 `nocase` option:

- `/mnt/workspace` (UUID B82064122063D642)
- `/mnt/storage`   (UUID D44A1FC54A1FA2F2)
- `/mnt/wd_black`  (UUID 58EAAC8AEAAC65CA)

Runtime remount confirmed working: lowercase `games` -> `Games`, and the previously
failing `pal/categories.db` now resolves to the real 86k file.

### Persistence (fstab)

`/etc/fstab` backed up to `/etc/fstab.bak_20260901`, then the three content-drive lines
rewritten to use UUID + `ntfs3` + `nocase,nofail,x-systemd.device-timeout=5`.
Validated with `mount --all --fake` and `systemctl daemon-reload` (no errors).

## Verified via live process inspection (no strace available)

Read the running Kontakt process open files via `/proc/<pid>/fd`:
- `PAL/categories.db`, `color.db`, `shortname.db`, `pal.db`, `komplete.db3`,
  `favorites.db3` are all OPEN and resolved (previously failing).
- Process is sequentially crawling `Kontakt Vst-i Folders` (113 GB, 192 folders),
  advancing folder-to-folder (Storm Orchestra -> Moody Clarinet -> Lyre Lyre ->
  FS_NoiseBox -> Irish Tin Whistle ...). This is a genuine FIRST-TIME full content
  index that could never complete before (paths were failing early).

## Current status / decision

User chose to let the full 113 GB index pass complete, confirm the NEXT launch is fast,
THEN review `Kontakt Vst-i Folders` for junk/incomplete libraries to remove once the
list is well-rounded.

## Pending

- Task 2.3: run traced launch AFTER first index completes + a clean second launch;
  compare per-bucket vs baseline (results/baseline.txt) using analyze_kontakt_log.sh.
- Confirm the index PERSISTS (subsequent launch fast, not re-scanning). If it re-scans
  every launch, check Loading options (background sample loading / auto content scan).
- Task 3: drive-letter normalization (currently still D:+F: dup, E:/J: controllers).
- Task 4: scanner to classify content + identify junk/incomplete for cleanup.

## Backups (see RESTORE.md)

- UserData: `_kiro_backup_20260901/` (komplete.db3, user_config.db3, NI Resources,
  Service Center)
- Wine drives: `~/.wine/dosdevices.bak_20260901`
- fstab: `/etc/fstab.bak_20260901`


## Observations from Options screens (to address in Task 3)

- **Standalone audio buffer = 236 samples** (Kontakt Audio panel: WASAPI Shared Mode,
  SSL 2+ Pro, 44100). This is Kontakt's own WASAPI buffer and is what actually governs
  standalone latency (~5.3ms/direction), SEPARATE from the PipeWire quantum (set to 128).
  In standalone via Wine WASAPI, this 236 dominates. Revisit lowering after the scan; it
  is independent of the load-time work.
- **Non-Player content base path still `F:\VST Install\Kontakt Portable\UserData\Kontakt 8\`**.
  Works for now (F: still maps to /mnt/workspace), but it's the leftover from the original
  problem. In Task 3, repoint to canonical `D:` so there's no dependency on the duplicate
  `F:` alias before removing it.
- **"Load samples in background" is currently UNCHECKED** — this does NOT affect the
  browser indexing crawl; it only affects per-instrument load feel. Leaving as user prefers.
  The real startup speedup after indexing will come from trimming junk/incomplete folders
  (Task 4 cleanup), not this toggle.

## Reminder for next session

1. Let the 113 GB browser index finish; watch cursor/tiles settle.
2. Fully close Kontakt, relaunch — confirm second launch is FAST (index persisted).
   - If it re-scans every launch, investigate auto-rescan / content base path.
3. Then proceed to Task 3 (drive-letter normalization: fix D:+F: dup, move controllers
   off E:/J:, repoint base path to D:) and Task 4 (scanner + junk/incomplete cleanup).


## BREAKTHROUGH: stale scan mutex was the endless-loading cause

After ~20h of the scan never completing across many relaunches, probing the live process
via /proc/<pid>/fd showed it was touching ONLY database files + the
`boost_interprocess/01000000/Kontakt 8_scan_mtx` mutex, with a completely STATIC WAL
(no writes) and NO library crawling. The komplete.db3 was byte-identical to the baseline
backup (41,705,472 bytes) — proving the interrupted scans never persisted anything.

Diagnosis: the first abrupt end (overnight) left a STALE scan mutex. Every subsequent
launch tried to "resume" a scan that could never complete or commit, so Kontakt spun on
the DB/mutex indefinitely without writing progress. This also explains why the
`F:\...\User Content` User-Presets entry wouldn't delete (config writes weren't persisting).

### Fix applied
- Backed up `boost_interprocess/` to `_kiro_backup_20260901/boost_interprocess`.
- Removed the stale mutex file:
  `boost_interprocess/01000000/Kontakt 8_scan_mtx`

### Result (confirmed by live probe)
- Launch is noticeably FASTER (user-observed).
- Kontakt now actively CRAWLS library content (`Kontakt Vst-i Folders/Angelus Lapsus/...`
  reading .wav samples, moving through folders).
- `komplete.db3-wal` is now ACTIVELY WRITTEN (mtime advancing) — index is persisting,
  whereas before it was static. The scan can now finish and commit.

### Import Content state (user actions)
- Removed all custom-library entries EXCEPT `/mnt/workspace/VST Install/Kontakt Vst-i Folders/`.
- One `F:` User-Presets entry (`F:\...\User Content`) resisted removal — expected, since
  config writes weren't persisting during the stuck state. Re-check after this scan
  completes and commits; it should be removable now.

### Next
- Let THIS scan finish (it's now persisting). Then close + relaunch to confirm a fast,
  no-rescan startup (index committed).
- Then retry removing the stale `F:\...\User Content` entry (should stick now).
- Then finishing tasks: drive-letter tidy, latency persistence, .so repair.


## BREAKTHROUGH: stale scan mutex was blocking completion

After ~20h of "endless loading" across many relaunches, live /proc/<pid>/fd probing
showed Kontakt touching ONLY database files (komplete.db3, favorites.db3, pal/color/
shortname.db) plus `boost_interprocess/01000000/Kontakt 8_scan_mtx`, with the WAL
completely STATIC (no writes) -- i.e. stuck on the scan mutex, not indexing.

Also confirmed: komplete.db3 was byte-identical to the baseline backup (41,705,472 B),
so the interrupted scans never persisted anything -- they spun without committing.

### Action taken
- Closed Kontakt, confirmed no process.
- Backed up `boost_interprocess/` to `_kiro_backup_20260901/boost_interprocess`.
- Removed the stale mutex file `boost_interprocess/01000000/Kontakt 8_scan_mtx`.

### Result after relaunch
- Kontakt now ACTIVELY crawling `Kontakt Vst-i Folders` again AND writing komplete.db3-wal.
- Progressing alphabetically: BeyondBow Cello -> Bilocation Drum v1.2 (real forward motion).
- So the mutex was the blocker; the remaining cost is the legitimate 113GB one-time index
  of the single still-registered custom location `Kontakt Vst-i Folders`.

### Plan
1. LET IT FINISH UNINTERRUPTED (disable sleep). Do not touch config mid-scan.
2. After it settles + commits: fix the stubborn `F:\...\User Content` User-Presets entry
   via Option A -> recreate F:->/mnt/workspace, Remove entry in Kontakt, then delete F:.
3. Clean relaunch to confirm fast startup (index persisted).

### Open item: config may be unwritable
The `F:\...\User Content` User-Presets entry won't delete across relaunches -> suggests
Kontakt couldn't persist config while stuck. Re-test removal AFTER scan completes; if it
still won't stick, investigate user_config.db3 writability/permissions.


## Scan completed + Kontakt usable (main goal reached) — CORRECTED

- Full index committed: komplete.db3 41.7MB (baseline) -> 66.6MB. Preset count 9630
  (down from ~51k pre-cleanup, junk removed = expected).
- Artwork/thumbnails populated for real libraries; instruments load and PLAY.

### Presets fixed by RECREATING F: (baked F: paths) — corrected
The per-preset "Content Missing / external drives" errors were NOT a transient/timing
artifact. They were caused by presets with baked absolute `F:\...` sample paths that
could not resolve while F: was unmapped. After the user RE-CREATED `f: -> /mnt/workspace`
in dosdevices, those presets began loading correctly (verified: Analog Strings
"Abrasive Soloists"). Conclusion: baked F: paths are real; F: must stay mapped to
/mnt/workspace for those presets/libraries to resolve.

### F: User Content entry — STILL PRESENT (corrected)
The `F:\VST Install\Kontakt Portable\UserData\User Content` User-Presets entry was NOT
removed; it is still registered. Now that F: maps to /mnt/workspace again it should
resolve fine. Keep it (it points at real User Content) or remove later — not urgent.

### Spinning cursor
Live probe shows Kontakt reading encoded sample monoliths (e.g.
`Kontakt Vst-i/Output Analog Strings KONTAKT/Samples/AS_002.nkx`) at steady ~39% CPU —
background sample/preview cache building. App is usable meanwhile.

### Implication for drive-letter plan (Task 3)
Because presets have baked `F:` paths pointing at /mnt/workspace, we must KEEP
F: -> /mnt/workspace. Do NOT repurpose F: for /mnt/wd_black (that would re-break these
presets). Revised target: D: and F: both -> /mnt/workspace; pick a DIFFERENT free letter
for wd_black (e.g. G:) and for storage (e.g. map storage where the baked e:\ ref expects).

### Remaining validation
- CLEAN RESTART TEST: close normally, reopen -> confirm fast, no full re-scan (persistence).


## Authoritative: how Player libraries resolve (Settings.cfg ContentDir analysis)

All 120 registered Player libraries use the SAME convention in Settings.cfg:
    ContentDir = Z:\mnt\workspace\VST Install\Kontakt Vst-i\<Library Name>
ZERO use D:, E:, or F:. (Verified: no ContentDir entry fails the `^Z:\mnt\workspace` test.)

Because Z: -> / , `Z:\mnt\workspace\...` maps to Linux `/mnt/workspace/...`. So every
library resolves as long as Z: -> / exists (it does). This convention is drive-letter
independent and robust.

Two path systems coexist:
1. LIBRARY registrations (Library Manager, 120 entries): all `Z:\mnt\workspace\...` -> bulletproof.
2. PRESET/instrument baked sample paths (inside .nki/.nksn): SOME use baked `F:\...`,
   which is why F: -> /mnt/workspace must remain mapped (fixes those presets).

### Drive-letter plan implications (final)
- KEEP Z: -> /            (makes all 120 libraries resolve; never remove)
- KEEP F: -> /mnt/workspace (needed for baked-F: preset sample paths)
- KEEP D: -> /mnt/workspace (harmless; matches any baked D: refs)
- storage (/mnt/storage) and wd_black (/mnt/wd_black) only need letters when importing
  content FROM them later (the E:/F: items in import-candidates.md). Not urgent now.
- Do NOT repurpose F: for wd_black (would break baked-F: presets). Use another free
  letter for wd_black if/when needed.


## Player-library "not installed" error + re-registration (new issue)

Symptom: some libraries (confirmed: EWQL RA) show tiles in the browser but loading any
preset throws "This instrument belongs to a library that is not installed currently!"

Not a path/sample issue: EWQL RA content is fully present on disk — 6+ GB of real .nkx
(Ra Samples 1-3 = 2.1GB each), Ra Resources.nkr 466MB, and `EWQL RA.nicnt` (515k) at the
library root. Structurally identical to working libs (e.g. Electro Acoustic).

Root cause: the KTP portable "Library Manager v8.0.0" registration state (encoded DB) does
not have these libraries as activated Player libraries, even though files + .nicnt exist.
These are repack libraries registered via the "empty registration file / unencoded" method.

KTP Library Manager Options (confirmed good settings):
- "Add unencoded libraries created by the empty registration file method" = CHECKED (essential)
- "Manage libraries in NKS browser" = UNCHECKED (correct; not using Komplete Kontrol/NKS)
- "Don't update encoded libraries metadata on rescan" = CHECKED (fine)

### Action in progress (corrected)
User navigated INTO the `EWQL RA` folder and pressed Open (no specific file selected) ->
scanning/registering ONLY EWQL RA (single library, ~6GB), not the whole tree. This is the
clean single-library test. Let it finish, click SAVE, then verify an EWQL RA preset loads
without the "not installed" error. If it works, repeat for other affected libraries.

NOTE: This is a separate concern from load-time/scan work. It's Kontakt/KTP Player-library
registration, driven from inside the Wine app (encoded DB, not shell-editable).


## EWQL RA "not installed" ROOT CAUSE: duplicate/conflicting registration

Found in `Service Center/LibraryHints.xml` (plaintext) TWO conflicting EWQL RA entries:
- `<Name>EWQL RA</Name>  <SNPID>A02</SNPID>`
- `<Name>EWQL RA </Name> <SNPID>A05</SNPID>`   (trailing space in name, DIFFERENT SNPID)

The instruments in EWQL RA presets carry one SNPID; the duplicated/ambiguous registration
(two names, two SNPIDs) means Kontakt can't match the instrument to a single installed
library -> "not installed". This is a registration METADATA conflict, NOT a file/path/scan
issue (content + .nicnt confirmed present). Likely caused by registering the library twice
(original repack registration + recent KTP re-add).

### Latency finding (item 2)
Kontakt's audio node runs at QUANT 236 even though PipeWire global quantum = 128, and even
`clock.force-quantum 128` did NOT pull it down. The 236 is dictated by Wine WASAPI SHARED
mode internally; PipeWire honors it per-node. To change it: use Kontakt Audio -> WASAPI
Exclusive Mode (editable buffer, less stable under Wine) OR accept 236 (~10.7ms RTT, stable,
ERR 0). Reverted force-quantum to 0. PipeWire 128 config remains persistent + correct.

### Startup persistence (item 1) = SUCCESS
Reopen after clean close was FAST (no full re-scan). The committed index (komplete.db3 66.6MB)
persists. The core endless-load problem is SOLVED.

### Fix plan for EWQL RA
Use KTP Library Manager: locate EWQL RA, Remove BOTH duplicate entries, then Add/register
it ONCE cleanly so a single SNPID registration remains. Re-test preset load. Do NOT hand-edit
LibraryHints.xml (it's only a hint mirror; authoritative reg is in encoded DB).


## EWQL RA: clean re-register did NOT fix -> SNPID mismatch (repack packaging issue)

Removed both duplicate registrations and re-added EWQL RA cleanly from its folder; preset
STILL errors "not installed". This rules out duplicate-conflict as the whole cause.

Root cause: SNPID mismatch between the library REGISTRATION (.nicnt declares one SNPID)
and the INSTRUMENTS/presets (.nki stamped with a different SNPID). Two IDs seen earlier:
A02 vs A05. Kontakt matches instrument->library by SNPID; they disagree, so no clean
registration can satisfy it. Classic repack problem where presets and registration files
came from different sources/versions.

Instruments are REAL (e.g. `EWQL RA/Instruments/Drums & Percussion/- Africa/Atsimevu.nki`
= 84k, not a stub).

### Workaround under test
Load the .nki DIRECTLY via Kontakt Files browser (bypass the Library tile):
Z:\mnt\workspace\VST Install\Kontakt Vst-i\EWQL RA\Instruments\...\Atsimevu.nki
- If it loads -> instruments are fine; only the Player-library tile is broken. Use via
  Files browser or register EWQL RA as a CUSTOM library (Import Content) instead of Player.
- If it still errors -> encoded instruments enforce SNPID even on direct load; needs the
  CORRECT matching library package (content acquisition issue, not a config fix).

### Not a setup/Wine/path problem
This is Kontakt Player library licensing/packaging metadata, distinct from all the
load-time/case/scan work (which is solved). Affects only mismatched-repack libraries.

### FINAL VERDICT (confirmed)
Direct .nki load via Files browser ALSO errors "not installed". So the encoded instruments
enforce the SNPID check on any load path. EWQL RA is UNUSABLE in its current form and this
CANNOT be fixed by configuration, re-registration, drive letters, or the Wine/Linux setup.
The presets and the registration file carry mismatched SNPIDs (A02 vs A05) baked in.

Resolution options (all content-side, outside this spec's scope):
1. Re-acquire a complete EWQL RA package where .nicnt SNPID matches the instruments.
2. Obtain the matching registration/.nicnt for the SNPID the instruments actually use.
3. Remove EWQL RA to stop the error/clutter.

Action: flag EWQL RA (and any similarly-mismatched repacks) as content issues; not a
system fix. Everything else in the load-time/optimization scope is resolved.



## Audio health verified + open items (session wrap)

### pw-top verification (clipping)
During playback, Kontakt node (ID 107) shows ERR 0, BUSY ~4-8us vs ~5350us budget,
B/Q 0.00 across all samples. Audio engine is PRISTINE — zero xruns, huge headroom at the
236 buffer. Clipping is NOT a system/timing issue. User reports clipping now not noticeable
(likely the -6dB + not hammering the hot Amazing Organ preset). Any residual clipping is
per-preset internal level, fixable by lowering that instrument's internal drive/output.
NOTE: pw-top measures buffer/timing health, NOT signal level — it can't see intra-Kontakt
0dBFS overload.

### Latency (final state)
- PipeWire global quantum: 128 @ 44.1kHz (persistent config, confirmed).
- Kontakt node: 236 via Wine WASAPI SHARED mode; cannot be lowered from PipeWire.
- User CANNOT switch to WASAPI Exclusive Mode (blocked/greyed). So 236 Shared is the
  working buffer (~10.7ms RTT, stable, ERR 0). Accepted.

### User intentions / open items
- LONG-TERM: repair Reaper .so/yabridge path (Task 7). Adopt IF it proves crash-stable
  over testing. Use lessons from standalone to build good library policy (only register
  clean, matching libraries) to minimize crash risk.
- EWQL RA: revisit when adding more instrument libraries later; test whether a matching-
  SNPID registration/db makes it apply successfully.
- storage/wd_black drive letters: map when importing from them.


## Low-latency launcher + KEY correction on the audio path

Created `~/.local/bin/launch_kontakt_lowlatency.sh` + desktop shortcut
"Kontakt 8 (Low Latency 128)" (in ~/.local/share/applications and ~/Desktop). It forces
PipeWire quantum 128 @ 44100 before launch, launches Kontakt, restores on exit.

### KEY CORRECTION: Wine uses the PulseAudio backend, not direct WASAPI
Launch log showed `fixme:pulse:pulse_channel_map_to_channel_mask` -> Wine routes audio via
winepulse (PulseAudio) -> PipeWire's pulse emulation. So Kontakt's 236 buffer is dictated
by the PULSEAUDIO layer, which is why forcing the PipeWire graph quantum (128) never changed
it -- wrong knob.

### The actual lever: PULSE_LATENCY_MSEC
The launcher now exports PULSE_LATENCY_MSEC (default 8) before wine. This is what can
influence the winepulse buffer. Tuning: try 8 -> 6 -> 4; lower = tighter but more xrun risk.
Edit `PULSE_LATENCY_MSEC_VALUE` at the top of the script. Judge by ear + pw-top ERR, not by
Kontakt's displayed "236" (may not update even if real latency improves). Wine's pulse
driver may clamp the value.

Confirmed: forcing PipeWire quantum 128 alone leaves Kontakt at 236 (Wine pulse path).

### RESULT: PULSE_LATENCY_MSEC=8 works (confirmed by ear)
With PULSE_LATENCY_MSEC=8 the playing action is "super tight" (user-confirmed), even though
Kontakt's Audio panel STILL displays 236 -- that readout is cosmetic and does not update.
Real latency improved. Judge by feel/ear, not the number. 8ms is the current sweet spot;
can try 6 or 4 for tighter feel at higher xrun risk. This is the effective latency fix
given Exclusive Mode is unavailable and Wine uses the pulse backend.



## Latency win + decision to pivot to Reaper .so

### PULSE_LATENCY_MSEC=8 works (playability)
Kontakt still DISPLAYS 236, but actual playing action is "super tight" now with
PULSE_LATENCY_MSEC=8 via the launcher. Confirms the winepulse latency was the real lever,
not the displayed buffer. Optional: push value to 6/4 for tighter response if it stays
xrun-free; keep 8 if it already feels great.

### Clipping: decision to STOP chasing in standalone
Clipping still occurs on some presets. Established: not system-level (pw-top ERR 0), not
fixed by -6dB -> internal to preset effects under this Kontakt/Wine build. User decision
(agreed): stop trying to fix clipping in standalone; pivot to building a stable Reaper
yabridge/.so environment. Rationale: .so runs Kontakt in Reaper's audio engine (not Wine
PulseAudio output), so clipping may not manifest there, and Reaper provides proper gain
staging/metering. Library discipline learned here (clean, matching registrations; no junk)
should minimize the crashes that plagued the .so path before.

### NEXT SESSION FOCUS: Task 7 (Reaper .so / yabridge repair)
- yabridgectl status; confirm Kontakt Windows plugin path under ~/.wine prefix
- yabridgectl add <Kontakt VST dir> if missing; yabridgectl sync (the step skipped before)
- rescan in Reaper; load Kontakt; verify content resolves via same Z:/D:/F: mapping
- crash-test over days incl. heavy projects; adopt as primary if stable, keep standalone fallback


## Research: escaping the WASAPI 236 buffer -> use ASIO, not WASAPI

Community consensus: WASAPI exclusive mode isn't the fix under Wine; the low-latency path
is ASIO (native low-latency Windows driver, supported by Kontakt) bridged to PipeWire/JACK.
Kontakt would then select an ASIO driver (buffer directly settable, e.g. 128/96/64) instead
of WASAPI, bypassing the winepulse 236 ceiling entirely.

Options (choose by backend):
- WineASIO (falkTX/wineasio): ASIO -> JACK. Mature/stable. Works via pipewire-jack. Most
  reliable bet. Register with `wineasio-register` in the prefix; select "WineASIO" in
  Kontakt Audio, route through PipeWire's JACK.
- pwasio (golfiros/pwasio): ASIO -> PipeWire directly. Needs PipeWire >= 1.6. Forces graph
  via PW_KEY_NODE_FORCE_QUANTUM/RATE; config at HKCU\Software\ASIO\pwasio (buffer_size,
  sample_rate, priority) or its control panel. Newer/basic but works.
- pipeasio (M0n7y5): another ASIO->PipeWire option (SteamRT-oriented).

Tuning tips from guides: lock PipeWire sample rate, give RT priority, find lowest stable
quantum by ear (people push toward 32). (Content rephrased for compliance.)

Path relevance:
- REAPER .so path: NO ASIO bridge needed — Reaper talks PipeWire/JACK natively and sets its
  own buffer; Kontakt-as-plugin uses Reaper's engine. (Another point in favor of .so.)
- STANDALONE fallback: install WineASIO (or pwasio) to get real low latency and escape 236.

Sources: github.com/falkTX/wineasio, github.com/golfiros/pwasio, github.com/M0n7y5/pipeasio,
osu-winello wiki (PipeWire latency), Guitar Pro + WineASIO gist.


## WineASIO registration (Task 9) — REGISTERED

Findings:
- `wineasio` package already installed; `pw-jack` + `pipewire-jack` present; libjack OK.
- Initially NOT registered (0 ASIO entries in system.reg/user.reg).
- The standard `wineasio-register` script FAILS on modern unified Wine (wine-staging 11.16):
  it looks for a separate `wine64` binary and a `syswow64` dir, neither of which exist in
  unified Wine, so it bails with "no wine64 was found".
- `regsvr32 wineasio64.dll` (bare name) also failed to load.

WORKING METHOD (register by pointing at the unix .so, as the script does internally):
    cp /usr/lib/wine/x86_64-windows/wineasio64.dll ~/.wine/drive_c/windows/system32/
    WINEPREFIX=$HOME/.wine regsvr32 /usr/lib/wine/x86_64-unix/wineasio64.dll.so

Result: system.reg now has the ASIO reg:
- [Software\ASIO\WineASIO] CLSID {48D0C522-BFCC-45CC-8B84-17F25F33E6E8} "WineASIO Driver"
- CLSID InProcServer32 -> wineasio64.dll (Apartment)
Note: the 2k wineasio64.dll is the PE stub half; real code is in wineasio64.dll.so (normal
for split-PE Wine builtins). Restored the system32 copy (the earlier removal was a misstep).

Remaining Task 9 steps:
- 9.3 launch Kontakt via pw-jack (WineASIO -> PipeWire JACK)
- 9.4 select WineASIO in Kontakt Audio; set buffer 128
- 9.5 tune buffer by ear + pw-top ERR


## WineASIO load failure diagnosis + fix attempt

Debug log (~/wineasio_debug.log) showed the real error on ASIO select:
    err:ole:apartment_add_dll couldn't load in-process dll L"wineasio64.dll"
So CLSID resolves but the DLL fails to LOAD in-process.

Also confirmed:
- pw-jack on Arch is effectively a no-op passthrough (its LD_LIBRARY_PATH lines are
  commented out) because pipewire-jack installs libjack.so into /usr/lib system-wide.
- JACK-over-PipeWire WORKS: `jack_lsp` lists real ports incl. SSL 2+ Pro. So the backend
  is fine; the problem is WineASIO loading inside Wine.
- Builtin halves exist + paired: /usr/lib/wine/x86_64-windows/wineasio64.dll (PE) and
  /usr/lib/wine/x86_64-unix/wineasio64.dll.so (unix). The loose 2k system32 PE copy could
  not be paired with its unix half at load time -> load failure.

Fix applied:
- Removed the redundant system32 wineasio64.dll stub (so Wine uses the paired builtin).
- Set DllOverride: HKCU\Software\Wine\DllOverrides wineasio64 = builtin.
- Re-registered via the .so; 4 ASIO reg entries intact.

Next: launch via pw-jack with WINEDLLOVERRIDES=...;wineasio64=b and WINEDEBUG=+asio to
~/wineasio_debug2.log; select ASIO; check if it initializes (Status Running) or if the
apartment_add_dll load error persists.


## WineASIO ROOT CAUSE: ABI mismatch with wine-staging 11.16

Debug log (~/wineasio_debug2.log) after the builtin fix STILL shows:
    err:ole:apartment_add_dll couldn't load in-process dll L"wineasio64.dll"
    err:ole:com_get_class_object no class object {48d0c522-...} could be created
No missing-dependency error (only unrelated libodbc.so.2). CLSID resolves, DLL is found,
but the class object can't be created.

Installed versions:
- wine-staging 11.16-1.1  (active; `wine --version` = wine-11.16 Staging)
- wineasio 1.3.0-2  (AUR)
(Also present: wine-cachyos-opt 2:10.0... for Steam/Proton.)

Conclusion: WineASIO's split-PE unix .so (wineasio64.dll.so) is ABI-locked to the Wine
version it was BUILT against, which is NOT wine-staging 11.16. Loading under 11.16 fails
to instantiate the COM class -> exactly this symptom.

FIX (proper): rebuild wineasio against the active wine-staging 11.16:
    paru -S wineasio --rebuild   (with wine-staging as the active/build wine)
Then re-register via: WINEPREFIX=$HOME/.wine regsvr32 /usr/lib/wine/x86_64-unix/wineasio64.dll.so
Verify it loads (no apartment_add_dll error), then select ASIO in Kontakt, set buffer via
the "Device driver configuration" (WineASIO panel).

Alternatives if rebuild is deferred:
- Keep WASAPI + PULSE_LATENCY_MSEC=8 (already "super tight", working).
- Pivot to Reaper .so path (native PipeWire/JACK, sidesteps this ABI issue).

Reverted/near-clean state: system32 wineasio stub removed (.bak kept); DllOverride
wineasio64=builtin set; ASIO reg entries present (4).


## WineASIO rebuilt against wine-staging 11.16 -> load error GONE

Confirmed /usr/bin/wine owned by wine-staging 11.16-1.1 (build target correct).
Rebuilt: `paru -S wineasio --rebuild --noconfirm` -> recompiled wineasio 1.3.0-2 against
the active wine-staging. Re-registered via regsvr32 on the .so (4 ASIO entries intact).

Load test: `WINEDEBUG=+ole regsvr32 .../wineasio64.dll.so` now shows NO
"couldn't load wineasio64.dll" / no failed apartment_add_dll for wineasio -> the ABI
mismatch is resolved. Pending: confirm ASIO sticks in Kontakt (Status Running), set buffer
via WineASIO "Device driver configuration" panel, verify sound.
system32 stub remains absent (Wine uses the rebuilt builtin); DllOverride wineasio64=builtin set.


## WineASIO STILL failing in Kontakt after rebuild (PAUSED - resume here)

Puzzle: `regsvr32 ... wineasio64.dll.so` load test showed NO error (loads fine standalone),
but launching KONTAKT via pw-jack (~/wineasio_debug3.log) STILL shows on ASIO select:
    err:ole:apartment_add_dll couldn't load in-process dll L"wineasio64.dll"
    err:ole:com_get_class_object no class object {48d0c522-...} could be created
So the .so loads under a bare regsvr32 wine call but NOT inside the Kontakt (pw-jack wine)
process. This means it's likely NOT (only) an ABI issue -- something about HOW Kontakt's
process loads the in-process DLL differs.

### Hypotheses to test tomorrow (in priority order)
1. system32 PE half MISSING: we removed ~/.wine/.../system32/wineasio64.dll. Kontakt's COM
   in-process load may need the PE `wineasio64.dll` PRESENT in the prefix (system32) even
   though the code is in the builtin .so. TRY: copy the rebuilt PE back:
     cp /usr/lib/wine/x86_64-windows/wineasio64.dll ~/.wine/drive_c/windows/system32/
   then relaunch Kontakt and select ASIO. (The regsvr32 load test worked because it points
   directly at the .so path; Kontakt loads by bare name "wineasio64.dll" which needs the PE
   in system32 to pair with the builtin .so.)
2. DllOverride scope: ensure `wineasio64=builtin` (we set it) AND that Kontakt's launch env
   doesn't override it. The launch used WINEDLLOVERRIDES without wineasio64=b -> add it:
     WINEDLLOVERRIDES="...;wineasio64=b"
3. 32 vs 64: Kontakt 8 x64 is 64-bit -> wineasio64 is correct. Confirm Kontakt isn't loading
   a 32-bit ASIO CLSID.
4. If still failing: capture with WINEDEBUG=+module,+ole to see the underlying LoadLibrary
   error for wineasio64.dll (why the module init returns failure inside Kontakt).

### Current state (for resume)
- wineasio 1.3.0-2 REBUILT against wine-staging 11.16 (correct build target confirmed:
  /usr/bin/wine owned by wine-staging 11.16-1.1).
- Registered: 4 ASIO entries in system.reg; CLSID {48D0C522-BFCC-45CC-8B84-17F25F33E6E8}.
- system32 wineasio64.dll: REMOVED (.bak exists) <- prime suspect, restore it first tomorrow.
- DllOverride wineasio64=builtin: set.
- JACK-over-PipeWire works (jack_lsp sees SSL 2+). pw-jack is a no-op passthrough on Arch.
- Launchers: ~/.local/bin/launch_kontakt_wineasio.sh (pw-jack) and
  launch_kontakt_lowlatency.sh (WASAPI + PULSE_LATENCY_MSEC=8, currently the WORKING path).

### Fallback that WORKS today
WASAPI + PULSE_LATENCY_MSEC=8 gives "super tight" action. Kontakt fully usable. WineASIO is
an enhancement, not a blocker.


## Workspace mount failed after reboot — dirty NTFS (resume after Windows shutdown)

Root cause of "cannot cd to Kontakt dir": `/mnt/workspace` (/dev/sdb2) FAILED to mount.
systemd `mnt-workspace.mount` = failed; dmesg: `ntfs3(sdb2): volume is dirty and "force"
flag is not set!` + "recommended to use chkdsk". Other drives (storage, wd_black,
win_system) mounted fine. This is NOT a WineASIO issue.

ntfsfix (/usr/bin/ntfsfix from `ntfsprogs`, which we installed) processed the volume OK
(MFT clean) but did NOT clear the dirty bit ntfs3 checks -> the dirty state is from Windows
fast-startup/hibernation, not a simple unclean unmount.

USER CHOSE: boot Windows and do a FULL shutdown to clear the state cleanly (best for drive
longevity). While in Windows:
- Disable Fast Startup (Power Options -> uncheck "Turn on fast startup") to STOP recurrence.
- Optionally run `chkdsk <WorkspaceLetter>: /f` (was F: in Windows) to clear pending check.
- Full Shut down (not restart), then boot CachyOS. Workspace should auto-mount clean.

### RESUME POINT (WineASIO test, once workspace is mounted)
Everything for WineASIO is staged:
- wineasio 1.3.0-2 REBUILT against wine-staging 11.16; registered (4 ASIO entries).
- system32 PE `wineasio64.dll` RESTORED (prime-suspect fix for the in-process load error).
- DllOverride wineasio64=builtin set; launcher updated with WINEDLLOVERRIDES=...;wineasio64=b.
- Bare-name load test (`WINEDEBUG=+ole regsvr32 wineasio64.dll`) showed NO load error after
  restoring the PE -> promising.
NEXT: launch `~/.local/bin/launch_kontakt_wineasio.sh` -> Options>Audio> select ASIO ->
check Status=Running -> set buffer via "Device driver configuration" -> verify sound.
If still fails: capture WINEDEBUG=+asio,+module,+ole to ~/wineasio_debug4.log and read it.

Fallback still working: WASAPI + PULSE_LATENCY_MSEC=8 (super tight).


## Back in Linux after clean Windows shutdown

- chkdsk D: (Workspace, label "Workspace") = "found no problems". Clean shutdown cleared
  the dirty flag. Fast Startup was NOT the cause (user confirmed it was already off).
- Workspace now mounts clean (no ntfs3 dirty message). All 3 content drives mounted.
- WineASIO staging intact after reboot: system32 PE present, ASIO reg entries present.

## Content-missing after reboot = F: symlink gone again
dosdevices after reboot had d:, w:, z: but NO f:. Presets have baked F: paths (and some
tile artwork), so they reported "content missing / drive not connected" and tiles were
blank. FIX: recreated `ln -s /mnt/workspace ~/.wine/dosdevices/f:`.
IMPORTANT: the f: symlink does NOT persist across reboots -> recurring issue. TODO: make
it permanent (winecfg drive entry OR a small login/launcher step that recreates f:).
Consider adding the f: symlink creation into the launcher scripts so it's always present.

## ASIO still not switching (debug pending)
Relaunching with WINEDEBUG=+asio,+ole -> ~/wineasio_debug4.log to capture the real ASIO
init error, after confirming content loads again with f: restored.


## WineASIO ROOT CAUSE FOUND + FIXED: builtin name mismatch

+loaddll,+module trace revealed the real failure (NOT ABI):
    load_builtin ...wineasio64.dll is a fake Wine dll
    find_builtin_dll looking for "wineasio.dll" for file ...wineasio64.dll
    find_builtin_dll cannot find builtin library for ...wineasio64.dll
    load_dll Failed to load module wineasio64.dll; status=c0000135
Wine's loader strips the arch suffix and searches for builtin "wineasio.dll", but the
package only ships "wineasio64.dll(.so)" -> no match -> c0000135 (module not found).

FIX (alias so the stripped-name lookup succeeds):
    sudo ln -sf /usr/lib/wine/x86_64-unix/wineasio64.dll.so    /usr/lib/wine/x86_64-unix/wineasio.dll.so
    sudo ln -sf /usr/lib/wine/x86_64-windows/wineasio64.dll    /usr/lib/wine/x86_64-windows/wineasio.dll

Re-test (+loaddll,+module regsvr32 wineasio64.dll): now shows
    build_module loaded ...wineasio64.dll ... builtin
    process_attach START ... END   -> DllMain ran, load SUCCEEDS. No c0000135.

CAVEAT: these aliases live in /usr/lib/wine and will be WIPED on the next wineasio (or wine)
package update. TODO: add a pacman hook or note to recreate them after updates, OR file
upstream. For now they persist until an update.

NEXT: launch ~/.local/bin/launch_kontakt_wineasio.sh -> select ASIO (should stick now) ->
set buffer 128 via "Device driver configuration" -> verify sound.
Also fixed this session: recreated f:->/mnt/workspace (content-missing after reboot).


## WineASIO WORKING — latency goal achieved
Kontakt Audio panel: Driver=ASIO, Device=WineASIO Driver, Status=RUNNING, Latency=64 samples,
Overall ~3.0ms (in 0.0 / proc 1.5 / out 1.5). Escaped the WASAPI 236 ceiling entirely.
WineASIO Settings: Connect to hardware ON, 16 in/16 out, Fixed buffersize ON. Set preferred
buffersize to desired (64 running now; bump to 128 if xruns under load). Autostart server OFF
(PipeWire provides JACK). Task 9 essentially COMPLETE.


## Buffer-change behavior (final, user-clarified)
The buffer switch DOES apply without a Kontakt restart, but there's a delay/flakiness:
it takes some seconds to take effect and is inconsistent. Unclear whether the flakiness is
WineASIO's ASIO driver, Kontakt's ASIO handling, or both. Practical rule: change Preferred
buffersize (Fixed UNCHECKED), then WAIT a few seconds — the latency will switch on its own.
No restart and no special trick required; just patience. Confirmed at 128 samples / 2.9ms.


## Library status after f: restore + WineASIO
- PRESETS LOAD now (f: restored; instruments work; user confirmed via sample test). Only
  EWQL RA still fails (SNPID mismatch, separate content issue).
- ARTWORK TILES: some show (Cuba, Bowls, Exhale, India, Mass, Melodies, Mysteria, Palette,
  Tablas, World Percussion 2.0), others blank (Amati Viola, 5Elements, Stradivari/Guarneri
  family, etc.).
  EVIDENCE: working-art libs have a `Library Data` resources folder + fuller .nicnt (Cuba
  .nicnt 1.1M w/ Library Data); blank-tile libs LACK the Library Data/resources (Amati .nicnt
  956k, no Library Data folder). Artwork is packed in the .nicnt/Library Data, not loose PNGs.
  CONCLUSION: blank tiles = artwork resources missing on disk for those repacks. Instruments
  + samples ARE present (they load/play fine). This is a COSMETIC, content-side gap — NOT
  fixable by drive letters/case/config. Would need the complete library package to get art.
  Decision: not worth chasing; purely cosmetic. 

Remaining: EWQL RA (SNPID-mismatch repack) is the last library item.


## ARTWORK TILES — CORRECTED diagnosis (user was right)
Earlier "artwork not on disk" was WRONG. Found the cache:
`UserData/Kontakt 8/LibrariesCache/` = 62 `.cache` files, 17MB. Each .cache = one library's
cached tile artwork + browser metadata, keyed by library ID (filenames like K..1728....cache).
`pictures/` folder is empty (0) — not the source.

Why some tiles blank: there are 62 cache entries but ~100+ libraries -> the blank-tile libs
have NO matching .cache. The tiles were all present BEFORE because the cache was complete;
our DB resets / interrupted scans left LibrariesCache PARTIAL. Not erased content — a stale/
partial browser cache.

FIX (matches user's hypothesis): rebuild the library cache so missing .cache entries
regenerate. Options: Library Manager rescan, batch re-save + rescan, or per-library
refresh/rebuild. The blank tiles should repopulate once their .cache is regenerated.
This is cosmetic/cache, NOT a path/content problem.


## "Incompatible Files" dialog during rescan = HARMLESS
Rescanning `D:\VST Install\Kontakt Vst-i Folders` surfaced an "Incompatible Files" list of
loose `.ncw` files (e.g. Designer Samples\NN Audio NN.ncw). `.ncw` = Kontakt compressed
SAMPLE payload, not a loadable instrument, so Import Content can't add them as browser
entries and flags them. SAFE TO DISMISS — the samples work fine when their parent .nki
loads. Never showed before because the folder is now registered as a Custom Library and the
rescan walks into raw sample subfolders.
Tip: when adding libraries, point Add at library ROOT folders (with the .nki), not deep
Samples subfolders, and leave "Import subfolders as individual libraries" UNCHECKED to avoid
recurring loose-sample warnings.

## Plan in progress (user)
Rescan (regenerating LibrariesCache/artwork) -> batch re-save only if instruments still
missing -> add remaining libraries from import-candidates.md (point at roots) -> close
Kontakt, let it index -> done.


## Artwork tiles: Import Content rescan did NOT help (wrong tool)
After the Import Content rescan of Kontakt Vst-i Folders, LibrariesCache stayed at 62 files
/17M (unchanged). Import Content rescan is for the CUSTOM library; it does NOT rebuild the
PLAYER-library artwork cache. The blank tiles are Player libraries (Amati, 5Elements, etc.).
Confirmed gap: 120 registered Player libs (ContentDir) vs 62 .cache files -> ~58 uncached
= the blank tiles.

CORRECT trigger to regenerate Player-lib tile art: the KTP LIBRARY MANAGER rescan (re-read
Player libraries), NOT Import Content. Watch LibrariesCache count climb 62 -> ~120.
Caveat: KTP full rescan can be slow (as seen before). Options: (a) KTP rescan all, (b)
target/refresh only the blank libs if the tool allows, (c) accept grey tiles (cosmetic;
instruments load fine). User's choice.


## Tile artwork fix + library-add plan (Option B, in place)

Decisive finding: blank-tile libraries' .nicnt DO contain artwork (Amati .nicnt: 8 image
markers vs Cuba working: 4). So art IS present; only the browser LibrariesCache .cache
entries were missing (62 of 120 libs). Neither Import Content rescan nor KTP re-add
regenerated them (stayed at 62, 0 recent writes).

ACTION TAKEN: backed up LibrariesCache -> _kiro_backup_20260901/LibrariesCache_bak (62 files),
then CLEARED live LibrariesCache (0 files, folder kept). Kontakt rebuilds tiles from .nicnt
on next launch.

LIBRARY ADDS = Option B (register in place; NO collected folder, NO symlinks — avoids Wine
symlink-scan flakiness; symlinks wouldn't help Player libs anyway since they register by
.nicnt via Library Manager, not folder scan):
- Player libs (import-candidates.md top list) -> KTP Library Manager -> Add -> real path.
- Custom libs (bottom list) -> Import Content -> Custom Libraries -> Add -> real path.
- E:/F: items need those drive letters mapped, or use Z:\mnt\... form.

NEXT (user): relaunch Kontakt -> verify tiles rebuild (LibrariesCache count climbs 0 -> ~120)
-> add the new libraries in place per above.


## Artwork tiles — HONEST CONCLUSION (guess-loop stopped)
Tried: Import Content rescan, KTP re-add, and CLEARING LibrariesCache -> none regenerated
the missing tile caches (count stayed 0 after clear+relaunch; restored to 62 from backup).
.cache filenames embed install-date epochs (2015-2024) => they were generated at each
library's ORIGINAL install/registration, not by any rescan. Blank-tile libs = repacks
registered via the unencoded/empty-registration method, which does NOT generate the browser
artwork cache a proper NI/Native Access install does. Artwork IS in the .nicnt, but Kontakt
won't rebuild the cache for these via available rescan tools.

VERDICT: not fixable by config/rescan/cache-clear. Only a full Batch Re-save MIGHT rebuild
some (heavy, slow, not guaranteed for repacks). RECOMMENDATION: accept grey tiles (cosmetic;
instruments load & play fine). LibrariesCache restored to 62 (working tiles preserved).

Player libs: user re-added via Library Manager pointing at D: (D:=/mnt/workspace) — fine.


## CAUSE of tile loss — CORRECTED by user timeline
User clarified: tiles worked fine THROUGH the mutex clear AND the KTP re-adds. They only
went blank AFTER the Workspace-drive chkdsk. So the KTP-re-add theory is WRONG.

Real cause: chkdsk on the Workspace partition (where LibrariesCache lives:
/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/LibrariesCache) rewrote NTFS
metadata (MFT/USN/timestamps) + the dirty-volume clear/remount. Kontakt validates cache
entries by file identity/mtime against the libraries; the chkdsk metadata rewrite made the
existing .cache entries look stale/mismatched -> browser treated them invalid -> blank tiles.

This is a ONE-TIME event (chkdsk), not a recurring setup issue. Clearing LibrariesCache is
the correct remedy (forces fresh rebuild from .nicnt). Relaunch should restore valid tiles.


## EWQL RA — FINAL: not fixable on our end (content casualty)
Even after the LibraryHints duplicate cleaned up to a SINGLE clean entry (Name=EWQL RA,
SNPID=A02), the presets STILL fail to load ("not installed"). Direct .nki load also failed
earlier. SNPID is binary-encoded in the .nicnt (not readable via strings), so can't be
matched from disk. Conclusion stands: the instruments demand an SNPID the A02 registration
doesn't satisfy — a baked-in packaging mismatch in this repack. CANNOT be fixed by config,
registration, drive letters, or Wine setup. Requires re-acquiring a correct EWQL RA package.
Accepted as a single content-side casualty (~1 of 120+ libraries). Closed.


## Reaper .so / yabridge — ANALYSIS of previous build + sync fix (Task 7)
yabridge + yabridgectl installed (modern chainloader: libyabridge-chainloader-vst2/vst3/clap.so,
yabridge-host.exe present). Bridges output to ~/.vst/.vst3/.clap/yabridge.

Tracked directories (survived previous build):
- /mnt/win_system/Program Files/Common Files/VST3/{FabFilter,Neural DSP,Plugin Alliance,ValhallaDSP}/
- /mnt/win_system/Program Files/{Neural DSP,NeuralAmpModeler}/
- /mnt/workspace/VST Install/Kontakt Portable/Kontakt 8/x64/VST3/  <- KONTAKT (Kontakt 8 Portable.vst3)

Finding: yabridgectl status said Kontakt "synced", but the bridge was NOT actually present in
~/.vst3/yabridge/ (171 other bridges were). Discrepancy = the missing sync step (as hypothesized
long ago). RAN `yabridgectl sync` -> Kontakt 8 Portable.vst3 bridge now EXISTS in ~/.vst3/yabridge/.

State: Reaper .so path is now largely intact. NEXT: rescan plugins in Reaper, load Kontakt as a
VST3, confirm content resolves (Z:/D:/F: mapping shared with standalone since same ~/.wine prefix),
then crash-test over days per the mode strategy. WineASIO is standalone-only; Reaper uses its own
PipeWire/JACK engine so no ASIO bridge needed there.


## EWQL RA — FINAL: unfixable repack (accept as casualty)
LibraryHints now has a SINGLE clean entry (Name=EWQL RA, SNPID=A02; the A05 duplicate is
gone). Preset STILL won't load. So instruments demand an SNPID that A02 doesn't satisfy;
the ID is baked/binary (unreadable via strings). No PAResources/EWQL RA folder either.
CONCLUSION: packaging mismatch in the repack — NOT fixable by config/registration. Needs a
correct EWQL RA package re-acquired. One broken lib out of ~120 working. Marked as
content-side casualty; stop chasing.

## Task 7 analysis — yabridge/.so state (BETTER than expected)
yabridge is INSTALLED and HEALTHY:
- yabridgectl present; VST2 ~/.vst, VST3 ~/.vst3/yabridge, CLAP ~/.clap locations set.
- chainloader libs present (/usr/lib/libyabridge-chainloader-*.so); yabridge-host.exe present.
- Actively managing FabFilter, Neural DSP, etc. from /mnt/win_system VST3 — all "synced".
- KONTAKT IS TRACKED + SYNCED: `/mnt/workspace/VST Install/Kontakt Portable/Kontakt 8/x64/VST3/`
  -> "Kontakt 8 Portable.vst3 :: VST3, legacy, 64-bit, synced".
- Bridge .so EXISTS: ~/.vst3/yabridge/Kontakt 8 Portable.vst3/Contents/x86_64-linux/Kontakt 8 Portable.so
  (+ x86_64-win/ points to the Windows .vst3).

So the .so path was NOT broken — it's synced and ready. Shared install: plugin uses the same
~/.wine prefix + same UserData/komplete.db3 as standalone (same libraries, presets, and same
EWQL RA issue).

REMAINING (Reaper-side): ensure Reaper's VST3 scan path includes ~/.vst3/yabridge, rescan
plugins, load Kontakt, verify content resolves (it will — shared DB). Then crash-test period.
