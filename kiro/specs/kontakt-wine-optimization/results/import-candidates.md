# Import Candidates (for after scan completes + F: cleanup)

Derived from the existing scan (`results/scan/player.tsv`, `custom.tsv`). No new disk
scan was run (Kontakt was mid-index). Register the SPECIFIC library subfolders below,
NOT whole parent trees like `PROGRAMS\VST, Samples & DAW` (that tree mixes real
libraries WITH plugin junk and recordings).

## Player libraries to register via Library Manager (high-value, confirmed)

Under `D:\PROGRAMS\VST, Samples & DAW\`:
- Kontakt Factory Library (1270 inst)
- EWQL RA (673), EWQL Colossus (510)
- Best Service - The Orchestra Complete (295)
- Evolution Series - World Percussion v2.0 (133)
- Middle East Library (55)
- Output Analog Strings, Output Exhale, Pharlight, Mysteria, Piano Colors, Cloud Supply
- Session Guitarist: Electric Sunburst Deluxe, Electric Vintage, Picked Acoustic
- Session Keys Electric R
- Red Room Audio - Palette Symphonic Sketchpad
- Play Series Selection, GetGood Drums Modern & Massive
- Balinese Gamelan, Electro Acoustic

Under `D:\PROGRAMS\VST, Samples & DAW\FROM TIXATI DL\`:
- Kontakt Factory Selection 2 (74), Kithara (21), Conflux (31), India / Discovery India
- Celtic Instruments, Flute Textures, Hybrid Tools 4 [8Dio], Kora, Oriental Strings,
  Soundiron Tablas

Other drives:
- `E:\Programs\Ultimate Orchestral Toolkit V.2 (BannanaButt)` (85)
- `F:\Kontakt VST-i Library\New Century Orchestral Series - Ensemble Strings [8Dio]` (193)

## Custom (loose-instrument) libraries worth importing

- Audio Imperia - Sinfonia Drums, Doru Malaia - Ethnic Super Drums, Epic SoundLab The Forge
- 8Dio Phenex Bundle, Dhol Ensemble, Hybrid Tools Dark Prophecy, Neo Guitar Hinterland
- PlugInGuru MegaMagic Bells & Winds, Drumforge I Ultimate, IndianSantoor
- Liminal Vocal Textures, Cy-FX, Amen Drums, Sonic Mechanics packs
- `E:\Programs\Ultimate Orchestral Sample Toolkit [BanannaButt]` (1087)
- `E:\Programs\Ultimate Orchestral Toolkit (Kontakt)[BananaButt]` (51)

## DO NOT import (false positives / not Kontakt / not libraries)

- `E:\Programs\Spectrasonics\STEAM\Omnisphere` — Spectrasonics, not Kontakt
- All `/mnt/storage/REC/...` folders — recordings, not libraries
- All Ableton project folders (`ABLETON SNEMANJE`, `Backup_..._Ableton_Projects`) — projects
- `Keyscape` — Spectrasonics, not Kontakt
- Any `__MACOSX` / EXTRACTED archive-artifact folders

## Key principle

Register specific library folders, not the whole `PROGRAMS\VST, Samples & DAW` tree,
so plugins/recordings/projects never get scanned as content again. This keeps future
startup scans small and fast.

## Reference
- Preset count before junk removal: ~51k. Compare against post-scan total once complete.


---

# Grouped with full root paths (for import)

Drive map: D: = /mnt/workspace, E: = /mnt/storage, F: = /mnt/wd_black, Z: = / (fallback).
NOTE: E:/F: must be mapped in Wine before importing those items (Task 3), or use Z:\mnt\...

## PLAYER LIBRARIES -> Library Manager

- Kontakt Factory Library    D:\PROGRAMS\VST, Samples & DAW\Kontakt Factory Library
- EWQL RA                    D:\PROGRAMS\VST, Samples & DAW\EWQL RA
- EWQL Colossus              D:\PROGRAMS\VST, Samples & DAW\EWQL Colossus
- The Orchestra Complete     D:\PROGRAMS\VST, Samples & DAW\Best Service - The Orchestra Complete
- World Percussion v2.0      D:\PROGRAMS\VST, Samples & DAW\Evolution Series - World Percussion v2.0 Close Front Mics
- Middle East Library        D:\PROGRAMS\VST, Samples & DAW\Middle East Library
- Output Analog Strings      D:\PROGRAMS\VST, Samples & DAW\Output Analog Strings KONTAKT
- Output Exhale              D:\PROGRAMS\VST, Samples & DAW\Output Exhale
- Pharlight                  D:\PROGRAMS\VST, Samples & DAW\Pharlight Library
- Mysteria                   D:\PROGRAMS\VST, Samples & DAW\Mysteria Library
- Piano Colors               D:\PROGRAMS\VST, Samples & DAW\Piano Colors Library
- Cloud Supply               D:\PROGRAMS\VST, Samples & DAW\Cloud Supply Library
- Session Guitarist Electric Sunburst Deluxe  D:\PROGRAMS\VST, Samples & DAW\Session Guitarist - Electric Sunburst Deluxe
- Session Guitarist Electric Vintage          D:\PROGRAMS\VST, Samples & DAW\Session Guitarist - Electric Vintage Library
- Session Guitarist Picked Acoustic           D:\PROGRAMS\VST, Samples & DAW\Session Guitarist - Picked Acoustic Library
- Session Keys Electric R    D:\PROGRAMS\VST, Samples & DAW\Session Keys Electric R
- Palette Symphonic Sketchpad D:\PROGRAMS\VST, Samples & DAW\Red Room Audio - Palette Symphonic Sketchpad
- Play Series Selection      D:\PROGRAMS\VST, Samples & DAW\Play Series Selection Library
- GetGood Modern & Massive   D:\PROGRAMS\VST, Samples & DAW\GetGood Drums - Modern and Massive Pack\Modern & Massive
- Balinese Gamelan           D:\PROGRAMS\VST, Samples & DAW\Balinese Gamelan Library
- Electro Acoustic           D:\PROGRAMS\VST, Samples & DAW\Electro Acoustic
- Kontakt Factory Selection 2 D:\PROGRAMS\VST, Samples & DAW\FROM TIXATI DL\Kontakt Factory Selection 2 v1.2.0 [Native Instruments]
- Conflux                    D:\PROGRAMS\VST, Samples & DAW\FROM TIXATI DL\Conflux [Native Instruments]
- Kithara                    D:\PROGRAMS\VST, Samples & DAW\FROM TIXATI DL\Kithara 1.0.1 [Native Instruments]
- Discovery Series India     D:\PROGRAMS\VST, Samples & DAW\FROM TIXATI DL\Native.Instruments.Discovery.Series.India.KONTAKT
- India                      D:\PROGRAMS\VST, Samples & DAW\FROM TIXATI DL\India
- Celtic Instruments         D:\PROGRAMS\VST, Samples & DAW\FROM TIXATI DL\Celtic Instruments [Big Fish Audio]
- Flute Textures             D:\PROGRAMS\VST, Samples & DAW\FROM TIXATI DL\Flute Textures [Emergence Audio]
- Hybrid Tools 4 [8Dio]      D:\PROGRAMS\VST, Samples & DAW\FROM TIXATI DL\Hybrid Tools 4 [8Dio]
- Kora                       D:\PROGRAMS\VST, Samples & DAW\FROM TIXATI DL\Kora 1.0.1 [Soniccouture]
- Oriental Pro Strings       D:\PROGRAMS\VST, Samples & DAW\FROM TIXATI DL\Oriental Sounds - Ultimate Pro Oriental Strings Arabic Turkish Indian
- Soundiron Tablas           D:\PROGRAMS\VST, Samples & DAW\FROM TIXATI DL\Soundiron - Tablas
- Ultimate Orch Toolkit V.2  E:\Programs\Ultimate Orchestral Toolkit V. 2 (BannanaButt)
- New Century Ensemble Strings F:\Kontakt VST-i Library\New Century Orchestral Series, The - Ensemble Strings [8Dio]

## CUSTOM LIBRARIES -> Import Content -> Custom Libraries

- Audio Imperia Sinfonia Drums  D:\PROGRAMS\VST, Samples & DAW\Audio Imperia - Sinfonia Drums
- Doru Malaia Ethnic Super Drums D:\PROGRAMS\VST, Samples & DAW\Doru Malaia - Ethnic Super Drums Collection
- Epic SoundLab The Forge       D:\PROGRAMS\VST, Samples & DAW\Epic SoundLab - The Forge
- Drumforge I Ultimate          D:\PROGRAMS\VST, Samples & DAW\Drumforge I Ultimate [KONTAKT-TRiGGER-DRUMAGOG]\KONTAKT\Drumforge.I.Ultimate.KONTAKT-SYNTHiC4TE
- PlugInGuru MegaMagic Bells&Winds D:\PROGRAMS\VST, Samples & DAW\PlugInGuru.MegaMagic.Bells.Winds.KONTAKT
- Drumdrops Vintage Funk Kit    D:\PROGRAMS\VST, Samples & DAW\Drumdrops - Vintage Funk Kit
- Sonic Mechanics Classic Guitar Licks  D:\PROGRAMS\VST, Samples & DAW\Sonic Mechanics - Classic Guitar Licks\KONTAKT
- Sonic Mechanics EDM Energy Drums      D:\PROGRAMS\VST, Samples & DAW\Sonic Mechanics - EDM Energy Drums\EED - KITS
- Sonic Mechanics Future Cinematic FX   D:\PROGRAMS\VST, Samples & DAW\Sonic Mechanics - Future Cinematic FX\2_FFX_PRESETS
- Sonic Mechanics Tropical Trap         D:\PROGRAMS\VST, Samples & DAW\Sonic Mechanics - Tropical Trap\TRT_INSTRUMENTS\KONTAKT
- String Audio Alchemist Impacts        D:\PROGRAMS\VST, Samples & DAW\String Audio - Alchemist Cinematic Impacts
- 8Dio Phenex Bundle            D:\PROGRAMS\VST, Samples & DAW\FROM TIXATI DL\8Dio Phenex Bundle
- Dhol Ensemble                 D:\PROGRAMS\VST, Samples & DAW\FROM TIXATI DL\Dhol Ensemble [Sonuscore]
- Hybrid Tools Dark Prophecy    D:\PROGRAMS\VST, Samples & DAW\FROM TIXATI DL\Hybrid_Tools_Dark_Prophecy
- Neo Guitar Hinterland         D:\PROGRAMS\VST, Samples & DAW\FROM TIXATI DL\Neo Guitar Series - Hinterland 1.1.0 [Musical Sampling]
- IndianSantoor                 D:\PROGRAMS\VST, Samples & DAW\FROM TIXATI DL\IndianSantoor\PSISA
- Liminal Vocal Textures V1     D:\PROGRAMS\VST, Samples & DAW\FROM TIXATI DL\Liminal - Vocal Textures Volume 1 [Crocus Soundware]
- Cy-FX                         D:\PROGRAMS\VST, Samples & DAW\FROM TIXATI DL\Cy-FX [Ergo Kukke]
- Amen Drums                    D:\PROGRAMS\VST, Samples & DAW\FROM TIXATI DL\Amen Drums [Vintage Drum Samples]
- Organic Loops Indian Sitar    D:\PROGRAMS\VST, Samples & DAW\FROM TIXATI DL\Organic.Loops.Classical.Indian.Sitar.KONTAKT-0TH3Rside
- Rhythmic Robot Bass III       D:\PROGRAMS\VST, Samples & DAW\FROM TIXATI DL\Rhythmic.Robot.Bass.III.KONTAKT
- Ultimate Orch Sample Toolkit  E:\Programs\Ultimate Orchestral Sample Toolkit [BanannaButt]
- Ultimate Orch Toolkit Kontakt E:\Programs\Ultimate Orchestral Toolkit (Kontakt)[BananaButt]

## Caveat
Player/Custom split is based on presence of encoded .nicnt/.nkx. A few (e.g. Soundiron
Tablas: samples but 0 encoded) may actually belong under Custom. If a "Player" entry
doesn't appear as a proper library tile after registering, move it to Custom instead.
