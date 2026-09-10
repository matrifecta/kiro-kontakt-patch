#!/usr/bin/env bash
#
# db-tile-diagnose.sh   (READ-ONLY — changes nothing)
#
# Goal: PROVE, from data, why a set of libraries that USED to show browser tiles
# now render generic folder icons after the Task-10 Z-only convergence.
#
# Method: dump the full k_content_path table from BOTH the last-known-good backup
# (komplete.db3.pre_ewqlra_144329 — tiles confirmed working) and the CURRENT DB,
# then diff by ALIAS (the library's display identity, which the browser tile keys
# on) and by row identity. No WHERE / no || on the collated column, so the custom
# KOMPLETE collation cannot abort the query (we dump unfiltered, then grep/awk).
#
# Also enumerates the actual .cache files present so we can see which surviving
# aliases have a matching cache vs which lost their linkage.
#
# Run with Kontakt CLOSED. Nothing here writes to the DB.

set -u

K8="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8"
CUR="${K8}/komplete.db3"
GOOD="${K8}/komplete.db3.pre_ewqlra_144329"
OUT="/tmp/tile-diag"
mkdir -p "$OUT"

echo "=== files ==="
ls -la "$CUR" "$GOOD" 2>&1

# ---- discover the real column list (schema differs between Kontakt versions) ----
echo
echo "=== k_content_path schema (current DB) ==="
sqlite3 "$CUR" ".schema k_content_path" 2>&1 | head -40

# ---- full unfiltered dumps (collation-safe: no WHERE, no ||, no PRAGMA) ----
# columns kept generic: id | content_type | alias | path
dump() { # $1 db  $2 outfile
  sqlite3 -separator '|' "$1" \
    "SELECT id, content_type, alias, path FROM k_content_path ORDER BY alias;" \
    > "$2" 2>"$2.err" || { echo "(dump had a collation note; see $2.err)"; }
}
dump "$GOOD" "$OUT/good.txt"
dump "$CUR"  "$OUT/cur.txt"

echo
echo "=== row counts ==="
echo -n "GOOD rows: "; grep -c '|' "$OUT/good.txt" 2>/dev/null
echo -n "CUR  rows: "; grep -c '|' "$OUT/cur.txt" 2>/dev/null

# ---- alias-only lists (field 3) ----
awk -F'|' '{print $3}' "$OUT/good.txt" | sort -u > "$OUT/good_alias.txt"
awk -F'|' '{print $3}' "$OUT/cur.txt"  | sort -u > "$OUT/cur_alias.txt"

echo
echo "=== ALIASES that existed in GOOD but are GONE in CURRENT (candidate lost tiles) ==="
comm -23 "$OUT/good_alias.txt" "$OUT/cur_alias.txt"

echo
echo "=== ALIASES present in CURRENT that were NOT in GOOD (new/repointed rows) ==="
comm -13 "$OUT/good_alias.txt" "$OUT/cur_alias.txt"

# ---- .cache inventory ----
echo
echo "=== LibrariesCache .cache files present (these are the tile artworks) ==="
ls -1 "${K8}/LibrariesCache" 2>/dev/null | grep -i '\.cache$' > "$OUT/cache_files.txt"
echo -n "cache count: "; wc -l < "$OUT/cache_files.txt"
echo "--- names ---"
cat "$OUT/cache_files.txt"

# ---- for the user-reported folder-icon libraries: show their row in BOTH DBs ----
# (grep is collation-safe; we search the dumped text, not the DB)
echo
echo "=== side-by-side rows for the reported folder-icon libraries ==="
for lib in \
  "Balinese Gamelan" "Best Service" "Cloud Supply" "Doru Malaia" "Drumdrops" \
  "Epic SoundLab" "Ethereal Earth" "Evolution" "GetGood" "Hy2rogen" "Keyscape" \
  "Middle East" "Mysteria" "Analog" "Exhale" "Pharlight" "Red Room" \
  "Session Guitarist" "String Audio"; do
  echo "----- [$lib] -----"
  echo "  GOOD:"; grep -i "$lib" "$OUT/good.txt" | sed 's/^/    /'
  echo "  CUR :"; grep -i "$lib" "$OUT/cur.txt"  | sed 's/^/    /'
done

# ---- control: libraries the user says STILL show tiles ----
echo
echo "=== CONTROL rows (libraries that STILL show tiles) ==="
for lib in "Amati" "Cuba" "5Elements" "Butch Vig" "ANALOG STRINGS"; do
  echo "----- [$lib] -----"
  echo "  GOOD:"; grep -i "$lib" "$OUT/good.txt" | sed 's/^/    /'
  echo "  CUR :"; grep -i "$lib" "$OUT/cur.txt"  | sed 's/^/    /'
done

echo
echo "=== DONE (read-only). Paste the whole output back. ==="
echo "Dumps saved under $OUT for follow-up."
