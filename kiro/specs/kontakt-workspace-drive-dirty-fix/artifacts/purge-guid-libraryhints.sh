#!/usr/bin/env bash
#
# purge-guid-libraryhints.sh
#
# Remove the 62 bare/orphan <Library> blocks in LibraryHints.xml whose <Name> is
# a raw GUID (leftover registration stubs from the DB/registration churn). These
# have NO <RegKey> (confirmed: 57 blocks have RegKey = the real named libraries;
# 62 do not = the GUID stubs), so they are non-functional and show as tile-less
# clutter in the Libraries browser. Keeps the 57 real, RegKey'd, tiled libraries.
#
# A <Library> block is: <Library> ... </Library>. We delete any block whose
# <Name> matches the GUID pattern 8-4-4-4-12 hex.
#
# FULLY REVERSIBLE: timestamped backup taken first. Run with Kontakt CLOSED.

set -u
LH="/mnt/workspace/VST Install/Kontakt Portable/UserData/Service Center/LibraryHints.xml"
STAMP="$(date +%Y%m%d_%H%M%S)"

if pgrep -fi 'Kontakt 8.exe' | grep -qv grep; then
    echo "ABORT: Kontakt running. File->Exit first."; exit 1
fi
[ -f "$LH" ] || { echo "ABORT: no LibraryHints.xml at $LH"; exit 1; }

echo "=== backup ==="
cp -av "$LH" "$LH.bak_purgeguid_$STAMP"

echo "=== BEFORE ==="
echo -n "  total <Library>: "; grep -c '<Library>' "$LH"
echo -n "  with RegKey:     "; grep -c '<RegKey>' "$LH"
echo -n "  GUID-named:      "; grep -cE '<Name>[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}</Name>' "$LH"

echo "=== purge GUID-named <Library> blocks (awk block filter) ==="
awk '
  /<Library>/ { inblk=1; buf=$0 ORS; isguid=0; next }
  inblk {
    buf = buf $0 ORS
    if ($0 ~ /<Name>[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}<\/Name>/) isguid=1
    if ($0 ~ /<\/Library>/) {
      if (!isguid) printf "%s", buf
      inblk=0; buf=""
    }
    next
  }
  { print }
' "$LH" > "$LH.tmp" && mv "$LH.tmp" "$LH"

echo "=== AFTER ==="
echo -n "  total <Library>: "; grep -c '<Library>' "$LH"
echo -n "  with RegKey:     "; grep -c '<RegKey>' "$LH"
echo -n "  GUID-named left: "; grep -cE '<Name>[0-9A-Fa-f]{8}-' "$LH"

echo "=== quick XML sanity (open vs close tags balance) ==="
echo -n "  <Library> open:  "; grep -c '<Library>' "$LH"
echo -n "  </Library> close:"; grep -c '</Library>' "$LH"

echo
echo "Expected AFTER: 57 total <Library>, 57 with RegKey, 0 GUID-named, open==close."
echo "NEXT: launch Kontakt, check the Libraries browser shows the clean named set."
echo "ROLLBACK (Kontakt closed):"
echo "  cp -av \"$LH.bak_purgeguid_$STAMP\" \"$LH\""
