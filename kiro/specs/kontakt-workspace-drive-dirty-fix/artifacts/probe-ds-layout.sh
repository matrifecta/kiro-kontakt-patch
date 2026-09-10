#!/usr/bin/env bash
# probe-ds-layout.sh (READ-ONLY) — how deep are the .dspreset files under DS Libraries?
# DS browser scans a configured folder recursively; this shows nesting depth + examples.
set -u
ROOTS=( "/mnt/wd_black/DS Libraries" "/mnt/btrfs_disk/DS Libraries" )
for r in "${ROOTS[@]}"; do
  [ -d "$r" ] || continue
  echo "===== $r ====="
  echo "  total .dspreset: $(find "$r" -type f -iname '*.dspreset' ! -name '._*' | wc -l)"
  echo "  total .dslibrary: $(find "$r" -type f -iname '*.dslibrary' ! -name '._*' | wc -l)"
  echo "  depth distribution of .dspreset (dirs below root):"
  find "$r" -type f -iname '*.dspreset' ! -name '._*' 2>/dev/null | while IFS= read -r f; do
    rel="${f#"$r"/}"; echo "$rel" | awk -F/ '{print NF-1}'
  done | sort -n | uniq -c | sed 's/^/    depth /'
  echo "  first 8 example preset paths (relative):"
  find "$r" -type f -iname '*.dspreset' ! -name '._*' 2>/dev/null | head -8 | sed "s#$r/#    #"
  echo
done
echo "READ-ONLY. DS scans the configured folder RECURSIVELY, so any depth is found;"
echo "this just confirms nothing is unexpectedly shallow/empty."
