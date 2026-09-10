#!/usr/bin/env bash
# build-ds-catalog.sh
# Clean TEXT catalog (no auto-embedded images — they were unreliable).
# Per entry: instrument name, art: path(s) referenced under the name, open: path to load.
# Plus an alphabetical NAME INDEX at the top (click to jump) and a note on adding artwork manually.
set -u

ART_DIR="/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts"
OUT="$ART_DIR/DS-CATALOG.md"
BODY="$ART_DIR/.catalog-body.tmp"
INDEX="$ART_DIR/.catalog-index.tmp"
HOME_LIB="$HOME/.config/DecentSampler/Sample Libraries"
BTRFS="/mnt/btrfs_disk/DS Libraries"
WDB="/mnt/wd_black/DS Libraries"

: > "$BODY"; : > "$INDEX"

# EXPLICIT HTML anchor ids (don't rely on Markdown auto-slugging, which varies by renderer).
# We emit <a id="ITEM_N"></a> on each entry and link the index to that exact id -> reliable jumps.
ENTRY_N=0
anchor() { echo "item-$1"; }   # id from the running entry number

# list ALL images in a library's dir (rejecting obvious UI widgets), for reference under the name
images_for() {
  local file="$1" dir
  if [[ "$file" == *.dsbundle ]]; then dir="$file"; else dir=$(dirname "$file"); fi
  find "$dir" -maxdepth 3 -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' \) 2>/dev/null \
    | grep -viE '/__MACOSX/|/\._' \
    | grep -viE 'knob|dial|fader|slider|button|hover|switch|led|arrow' \
    | sort
}

# find a readme-ish file in/near the library and return a short (~2-3 sentence) plain-text excerpt.
# strips RTF markup; skips FAQ/usage boilerplate; empty if none found.
desc_for() {
  local file="$1" dir
  if [[ "$file" == *.dsbundle ]]; then dir="$file"; else dir=$(dirname "$file"); fi
  # search this dir and its parent (readmes often sit one level up), prefer readme/description/about
  local rf
  rf=$(find "$dir" "$(dirname "$dir")" -maxdepth 2 -type f \
         \( -iname 'readme*' -o -iname 'read me*' -o -iname '*description*' -o -iname 'about*' -o -iname 'info*.txt' \) 2>/dev/null \
       | grep -viE '/__MACOSX/|/\._' | head -1)
  [ -z "$rf" ] && return 0
  # only accept real TEXT files (skip binaries that happen to match the name glob)
  case "$(file -b --mime-type "$rf" 2>/dev/null)" in
    text/*|application/rtf) : ;;
    *) return 0 ;;
  esac
  # read with null bytes stripped up front (avoids the 'ignored null byte' warnings)
  local raw txt
  raw=$(tr -d '\000' < "$rf" 2>/dev/null)
  if printf '%s' "$raw" | head -c 6 | grep -q '{\\rtf'; then
    txt=$(printf '%s' "$raw" | sed -e 's/\\par[d]*/\n/g' -e 's/{\\[^ }]*//g' -e 's/\\[a-zA-Z]*[0-9]*//g' -e 's/[{}]//g')
  else
    txt="$raw"
  fi
  # collapse whitespace, drop separator/boilerplate lines, take the first meaningful chunk
  txt=$(printf '%s\n' "$txt" \
        | sed -e 's/\r$//' \
        | grep -viE '^[[:space:]]*[-=_*#]{3,}[[:space:]]*$' \
        | grep -viE '^[[:space:]]*(the story|story|usage|faq|included formats|release notes|date:|by:|created by:|profile:|version)' \
        | grep -viE 'decentsampler.com|pianobook.co.uk|hyperlink|requires kontakt|drag the|\.dslibrary' \
        | sed '/^[[:space:]]*$/d' \
        | tr '\n' ' ' | sed 's/  */ /g; s/^ //')
  # first ~2-3 sentences, cap length
  txt=$(printf '%s' "$txt" | grep -oE '^.{0,320}([.!?]|$)' | head -1)
  # trim to a clean sentence end if long
  printf '%s' "$txt" | sed 's/[[:space:]]*$//'
}

emit() {
  local name="$1" file="$2"
  ENTRY_N=$((ENTRY_N+1))
  local a; a=$(anchor "$ENTRY_N")
  printf -- '- [%s](#%s)\n' "$name" "$a" >> "$INDEX"

  # explicit HTML anchor id on the heading so the link target is exact (renderer-independent)
  printf -- '<a id="%s"></a>\n' "$a" >> "$BODY"
  printf -- '### %s\n' "$name" >> "$BODY"
  local d; d=$(desc_for "$file")
  if [ -n "$d" ]; then printf -- '_%s_\n\n' "$d" >> "$BODY"; fi
  printf -- 'open: `%s`  \n' "$file" >> "$BODY"
  local imgs; imgs=$(images_for "$file")
  if [ -n "$imgs" ]; then
    while IFS= read -r img; do
      [ -z "$img" ] && continue
      printf -- 'art: `%s`  \n' "$img" >> "$BODY"
    done <<< "$imgs"
  else
    printf -- 'art: _(none found)_  \n' >> "$BODY"
  fi
  printf -- '\n' >> "$BODY"
}

list_items() {
  find "$1" -maxdepth 7 \( -iname '*.dsbundle' -o -iname '*.dspreset' \) 2>/dev/null \
    | grep -viE '/__MACOSX/|/\._|/_kiro_nonds_trash_' \
    | grep -viE '\.dsbundle/.*\.dspreset$' \
    | while read -r f; do base=$(basename "$f"); echo "${base%.*}|$f"; done | sort -f
}

echo "## 1. Via SAMPLE STORE  (DS default folder - BROWSE / Sample Store -> Installed)" >> "$BODY"
echo >> "$BODY"; echo "Folder: \`$HOME_LIB\`" >> "$BODY"; echo >> "$BODY"
list_items "$HOME_LIB" | while IFS='|' read -r nm f; do emit "$nm" "$f"; done

drive() {
  { echo; echo "## $1"; echo; echo "FILE BROWSER -> **$3** -> \`DS Libraries\` -> ..."; echo "Root: \`$2\`"; echo; } >> "$BODY"
  [ -d "$2" ] || { echo "_(drive not present)_" >> "$BODY"; return; }
  list_items "$2" | while IFS='|' read -r nm f; do emit "$nm" "$f"; done
}
drive "2. Via FILE BROWSER - BTRFS drive" "$BTRFS" "btrfs"
drive "3. Via FILE BROWSER - WD_BLACK drive" "$WDB" "wd_black"

{
  echo "# DecentSampler Library Catalog"
  echo
  echo "_generated: $(date)_"
  echo
  echo "Each entry lists the **open:** path to load in DecentSampler and the **art:** image path(s)"
  echo "found in that library (auto-detected; may include extras). Click a name in the index to jump."
  echo
  echo "## Index (alphabetical by instrument name)"
  echo
  sort -f "$INDEX" | uniq
  echo
  echo "---"
  echo
  echo "## How to add / view artwork"
  echo
  echo "The **art:** paths point at the real image files on disk. To view one, open the path in an"
  echo "image viewer (or drag it into one). To add a cover manually (e.g. from the web or a screenshot):"
  echo
  echo "1. **Get an image** — web: right-click → Save Image As; or screenshot the DS window with KDE"
  echo "   Spectacle (\`Shift+PrintScreen\` → *Rectangular Region* → Save As \`.png\`)."
  echo "2. **Save it** somewhere stable with a short dashless name, e.g."
  echo "   \`~/DS Covers/air-piano.png\`  (a folder OUTSIDE this catalog so a rebuild won't wipe it)."
  echo "3. **Embed it under an entry** (relative or absolute path both work when viewed in a browser;"
  echo "   Kiro's preview needs a RELATIVE path):"
  echo '   ```markdown'
  echo '   ![Air Piano](../../../DS Covers/air-piano.png)'
  echo '   ```'
  echo "4. **Or make a compact clickable label** (short name, blue + underlined) that opens the image:"
  echo '   ```markdown'
  echo '   <a href="/home/phnx/DS Covers/air-piano.png"><u><span style="color:#2563eb">Cover</span></u></a>'
  echo '   ```'
  echo
  echo "> Re-running \`build-ds-catalog.sh\` OVERWRITES this file, so keep manual edits/images elsewhere"
  echo "> and re-apply them after a rebuild, or copy this catalog to a new name before editing."
  echo
  echo "---"
  echo
} > "$OUT"
cat "$BODY" >> "$OUT"
rm -f "$BODY" "$INDEX"

echo "CATALOG: $OUT"
echo "done."
