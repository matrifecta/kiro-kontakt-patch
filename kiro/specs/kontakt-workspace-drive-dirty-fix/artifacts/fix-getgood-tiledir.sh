#!/usr/bin/env bash
# fix-getgood-tiledir.sh — GetGood is type-2 with .nicnt Product 'GGD Modern and Massive' and that image dir
# exists, yet the browser (which shows the db ALIAS 'GetGood Drums - Modern and Massive Pack') stays blank.
# Add an image dir named EXACTLY as the db alias, copied from the existing GGD Modern and Massive art.
# No db change, reversible.
set -u
MODE="${1:-dryrun}"
NIIMG="/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/image"
SRC="$NIIMG/GGD Modern and Massive"
DEST="$NIIMG/GetGood Drums - Modern and Massive Pack"
echo "src : $SRC"
echo "dest: $DEST"
[ -d "$SRC" ] || { echo "ABORT: source art dir missing"; exit 1; }
[ -e "$DEST" ] && echo "NOTE: dest exists; rm -rf to redo"
if [ "$MODE" != apply ]; then echo "DRY-RUN. Re-run: bash $0 apply"; exit 0; fi
mkdir -p "$DEST"
cp -av "$SRC"/MST_*.png "$SRC"/OSO_*.png "$SRC"/VB_*.png "$DEST"/ 2>/dev/null | sed 's/^/  /'
# meta must carry the ALIAS as its <name>
cat > "$DEST/GetGood Drums - Modern and Massive Pack.meta" <<EOF
<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<resource version="2.1544">
<name>GetGood Drums - Modern and Massive Pack</name>
<type>image</type>
</resource>
EOF
echo "created: $(ls "$DEST" | tr '\n' ' ')"
echo "ROLLBACK: rm -rf \"$DEST\""
