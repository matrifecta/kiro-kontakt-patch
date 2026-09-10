#!/usr/bin/env bash
#
# inspect-nkt-headers.sh  (READ-ONLY)
#
# Chords/Phrases .nkt still "corrupted" after restoring from BACKUP -> maybe the BACKUP
# .nkt are ALSO bad, or .nkt won't load for another reason. Compare header magic bytes
# of: a LIVE Chords .nkt, the BACKUP Chords .nkt, and a KNOWN-GOOD patch from a library
# that loads fine. Kontakt containers have a recognizable magic (e.g. hcex/Kontakt/NI
# FC monolith headers). A truncated/garbage header = corrupt.

set -u
WS="/mnt/workspace/VST Install/Kontakt Portable/Kontakt 8/Content/Tools"
BK="/mnt/workspace/BACKUP/Kontakt 8/Content/Tools"

show() {  # $1 label  $2 file
  local f="$2"
  echo "----- $1 -----"
  if [ ! -e "$f" ]; then echo "  (missing: $f)"; return; fi
  ls -la "$f"
  echo -n "  file: "; file "$f"
  echo "  first 32 bytes (hex):"
  head -c 32 "$f" | xxd | sed 's/^/    /'
  echo "  readable magic near start:"
  head -c 256 "$f" | strings | head -3 | sed 's/^/    /'
  echo
}

# a Chords .nkt (live + backup)
CH_LIVE=$(find "$WS/Chords/Instruments" -maxdepth 1 -type f -iname '*.nkt' | head -1)
CH_BK=$(find "$BK/Chords/Instruments" -maxdepth 1 -type f -iname '*.nkt' | head -1)
show "LIVE Chords .nkt"   "$CH_LIVE"
show "BACKUP Chords .nkt" "$CH_BK"

# a KNOWN-GOOD patch from a library that loads (Amati / 5Elements) — find any .nki
GOOD=$(find "/mnt/btrfs_disk/Kontakt Libraries/Player/Amati Viola Library" \
             "/mnt/btrfs_disk/Kontakt Libraries/Player/5Elements" \
             -type f -iname '*.nki' 2>/dev/null | head -1)
show "KNOWN-GOOD .nki (loads fine)" "$GOOD"

# also: a working factory .nkt if any tool loads? and a Kits .nkl from Lo-Fi (loads w/ warning)
LOFI=$(find "/mnt/workspace/VST Install/Kontakt Portable/Kontakt 8/Content/Presets/Lo-Fi Vibes" -type f -iname '*.nkl' | head -1)
show "Lo-Fi .nkl (loads w/ warning)" "$LOFI"

echo "READ-ONLY. Compare the magic/first-bytes: matching header = format OK;"
echo "garbage/zeros/short = corrupt. If LIVE==BACKUP header and both differ from the"
echo "KNOWN-GOOD pattern, the .nkt were already bad in backup (corruption predates it)."
