#!/usr/bin/env bash
set -u
ART_DIR="/tmp"
MODE="${1:-desktop}"
N=0
e() { printf '%s' "$1" | sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g'; }
emit_ds_patches() {
  local root="$1"
  # resolve the directory that holds the presets
  local dir
  if [[ "$root" == *.dsbundle ]] || [ -d "$root" ]; then dir="$root"; else dir=$(dirname "$root"); fi
  [ -n "$dir" ] && [ -d "$dir" ] || { printf '  <div class="patches nopatch"><i>no browsable patches</i></div>\n'; return 0; }

  local nki_list="$ART_DIR/.dspatch.$N.tmp"; : > "$nki_list"
  local found=0 f rel
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    rel="${f#"$dir"/}"
    printf '%s\n' "$rel" >> "$nki_list"
    found=1
  done < <(find "$dir" -maxdepth 7 -type f -iname '*.dspreset' 2>/dev/null \
             | grep -viE '/__MACOSX/|/\._|/_kiro_nonds_trash_' | sort -f)

  if [ "$found" -eq 0 ]; then
    rm -f "$nki_list"
    printf '  <div class="patches nopatch"><i>no browsable patches</i></div>\n'
    return 0
  fi

  local total; total=$(wc -l < "$nki_list" | tr -cd '0-9')
  printf '  <details class="patches"><summary>Patches (%s)</summary>\n' "$total"

  local groups="$ART_DIR/.dsgrp.$N.tmp"; : > "$groups"
  while IFS= read -r rel; do
    [ -z "$rel" ] && continue
    case "$rel" in
      */*) printf '%s\n' "${rel%/*}" >> "$groups" ;;
      *)   printf '%s\n' "(root)"    >> "$groups" ;;
    esac
  done < "$nki_list"

  local grp gcnt base
  while IFS= read -r grp; do
    [ -z "$grp" ] && continue
    gcnt=0
    while IFS= read -r rel; do
      [ -z "$rel" ] && continue
      case "$rel" in
        */*) [ "${rel%/*}" = "$grp" ] && gcnt=$((gcnt+1)) ;;
        *)   [ "$grp" = "(root)" ] && gcnt=$((gcnt+1)) ;;
      esac
    done < "$nki_list"
    printf '    <details class="grp"><summary>%s (%s)</summary>\n' "$(e "$grp")" "$gcnt"
    printf '      <ul class="patchlist">\n'
    while IFS= read -r rel; do
      [ -z "$rel" ] && continue
      case "$rel" in
        */*) [ "${rel%/*}" = "$grp" ] || continue ;;
        *)   [ "$grp" = "(root)" ] || continue ;;
      esac
      base="${rel##*/}"; base="${base%.*}"
      if [ "$MODE" = portable ]; then
        printf '        <li>%s</li>\n' "$(e "$base")"
      else
        printf '        <li>%s <span class="ppath">%s</span></li>\n' "$(e "$base")" "$(e "$rel")"
      fi
    done < "$nki_list"
    printf '      </ul>\n'
    printf '    </details>\n'
  done < <(sort -f -u "$groups")

  printf '  </details>\n'
  rm -f "$nki_list" "$groups"
  return 0
}
list_items() {
  local root="$1"
  [ -d "$root" ] || return 0
  local libs="$ART_DIR/.dslibs.$$.tmp"; : > "$libs"

  # 1) .dsbundle libraries (each bundle dir is one library)
  while IFS= read -r bundle; do
    [ -z "$bundle" ] && continue
    local bname; bname=$(basename "$bundle"); bname="${bname%.dsbundle}"
    printf '%s\t%s\n' "$bname" "$bundle" >> "$libs"
  done < <(find "$root" -maxdepth 7 -type d -iname '*.dsbundle' 2>/dev/null \
             | grep -viE '/__MACOSX/|/\._|/_kiro_nonds_trash_' | sort -f)

  # 2) loose .dspreset presets (NOT inside a .dsbundle) -> map to their top-level
  #    library folder under $root.
  while IFS= read -r preset; do
    [ -z "$preset" ] && continue
    # relative path of the preset under root
    local rel="${preset#"$root"/}"
    local libpath libname
    case "$rel" in
      */*)
        # first path component under root is the library folder
        local first="${rel%%/*}"
        libpath="$root/$first"
        libname="$first"
        ;;
      *)
        # preset sits directly in root -> library IS the root
        libpath="$root"
        libname=$(basename "$root")
        ;;
    esac
    printf '%s\t%s\n' "$libname" "$libpath" >> "$libs"
  done < <(find "$root" -maxdepth 7 -type f -iname '*.dspreset' 2>/dev/null \
             | grep -viE '/__MACOSX/|/\._|/_kiro_nonds_trash_' \
             | grep -viE '\.dsbundle/' | sort -f)

  # dedup by library path (keep first), emit name|path, sorted by name
  local seen="$ART_DIR/.dsseen.$$.tmp"; : > "$seen"
  local nm lp
  while IFS=$'\t' read -r nm lp; do
    [ -z "$lp" ] && continue
    grep -qxF "$lp" "$seen" 2>/dev/null && continue
    printf '%s\n' "$lp" >> "$seen"
    printf '%s|%s\n' "$nm" "$lp"
  done < "$libs" | sort -f
  rm -f "$libs" "$seen"
}

echo "=== list_items /tmp/dsmock ==="
list_items /tmp/dsmock
echo "=== patches per lib ==="
while IFS="|" read -r nm f; do N=$((N+1)); echo "--- LIB: $nm ($f) ---"; emit_ds_patches "$f"; done < <(list_items /tmp/dsmock)
