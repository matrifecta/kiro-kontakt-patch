#!/usr/bin/env bash
# build-kontakt-catalog-html.sh
# Browsable catalog of registered KONTAKT libraries (content_type=2 in komplete.db3), library-level only.
# Banner art = NI Resources/image/<alias>/MST_artwork.png (fallback MST_logo.png); none if unmatched.
# Same UX as the DS catalog: jump-index, name-keyword filter (highlight + narrowing), [open folder] links,
# desktop + mobile builds.  Modes: (default) desktop | portable | both
#   desktop  -> KONTAKT-CATALOG.html          (banner thumbs in kontakt-thumbs/, [open folder] links)
#   portable -> KONTAKT-CATALOG-portable.html (single self-contained file, embedded x110 q70 jpg, no folder links)
set -u

ART_DIR="/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts"
MODE="${1:-desktop}"
if [ "$MODE" = both ]; then bash "$0" desktop && bash "$0" portable; exit $?; fi
if [ "$MODE" = portable ]; then OUT="$ART_DIR/KONTAKT-CATALOG-portable.html"; else OUT="$ART_DIR/KONTAKT-CATALOG.html"; fi
THUMBS="$ART_DIR/kontakt-thumbs-$MODE"
IDX="$ART_DIR/.kidx.$MODE.tmp"; BODY="$ART_DIR/.kbody.$MODE.tmp"
DB_SRC="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/komplete.db3"
NIIMG="/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/image"
LIBLIST="$ART_DIR/.klibs.$MODE.tmp"

mkdir -p "$ART_DIR"
exec 9>"$ART_DIR/.catalog-rebuild.lock"
flock 9
rm -rf "$THUMBS"; mkdir -p "$THUMBS"; : > "$IDX"; : > "$BODY"
HAVE_MAGICK=0; { command -v magick >/dev/null 2>&1 || command -v convert >/dev/null 2>&1; } && HAVE_MAGICK=1
N=0
esc(){ sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g'; }
e(){ printf '%s' "$1" | esc; }
eattr(){ printf '%s' "$1" | sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g' -e 's/"/\&quot;/g'; }
slug(){ echo "$1" | tr -c 'A-Za-z0-9._-' '_' | cut -c1-70; }
anchor(){ echo "item-$1"; }

# display-name override: name-overrides.tsv  <raw alias/library name><TAB><clean display name>
# Shared with build-ds-catalog-html.sh. Lets a rebuild keep hand-corrected names instead of
# reverting to the raw komplete.db3 alias every time. Maintained by tools/update_catalog.py.
NAME_OVERRIDES="$ART_DIR/name-overrides.tsv"
RAWNAMES_LOG="$ART_DIR/.raw-names.kontakt.$MODE.log"
: > "$RAWNAMES_LOG"
name_override(){ printf '%s\n' "$1" >> "$RAWNAMES_LOG"
  [ -f "$NAME_OVERRIDES" ] || { printf '%s' "$1"; return 0; }; local want="$1" n c
  while IFS=$'\t' read -r n c; do case "$n" in \#*) continue;; esac
    [ "$n" = "$want" ] || continue; [ -n "$c" ] && { printf '%s' "$c"; return 0; }; done < "$NAME_OVERRIDES"
  printf '%s' "$want"; }

# ---- pull library list (content_type=2) from the DB: alias<TAB>linux_path ----
DBTMP="/tmp/kontakt_cat.db3"; cp "$DB_SRC" "$DBTMP" 2>/dev/null
python3 - "$DBTMP" "$LIBLIST" <<'PY'
import sqlite3,sys
db,out=sys.argv[1],sys.argv[2]
con=sqlite3.connect(db)
def z2l(p):  # Z:\mnt\... -> /mnt/... ; backslashes -> forward
    p=p.replace('\\','/')
    if p[1:3]==':/': p=p[2:]          # strip drive letter
    return p
rows=con.execute("SELECT id,alias,path FROM k_content_path WHERE content_type=2 ORDER BY id")
seen_alias={}; seen_path=set(); out_rows=[]
for _id,alias,path in rows:
    alias=(alias or '').strip() or 'Unknown'
    lp=z2l(path)
    ka=alias.strip().lower()          # dedup key: normalized alias
    kp=lp.rstrip('/').lower()         # and normalized path (catches same lib re-added under a diff alias)
    if ka in seen_alias or kp in seen_path:   # keep the FIRST (lowest id = original registration)
        continue
    seen_alias[ka]=1; seen_path.add(kp)
    # collect preset/patch names for this library from k_sound_info (read-only SELECT)
    preset_rows=con.execute(
        "SELECT name FROM k_sound_info WHERE content_path_id=? LIMIT 150", (_id,))
    pnames=' '.join(r[0] for r in preset_rows if r[0])
    out_rows.append((alias,lp,pnames))
out_rows.sort(key=lambda r: r[0].lower())
with open(out,'w') as f:
    for alias,lp,pnames in out_rows:
        f.write(f"{alias}\t{lp}\t{pnames}\n")
PY
rm -f "$DBTMP"

KEYWORDS="piano keys organ strings violin viola cello guitar bass harp choir vocal voice \
flute reed brass horn drums drum percussion bells gamelan tabla kalimba \
synth pad ambient cinematic orchestral world lofi analog \
ethereal string orchestra guitarist tablas soul vintage hybrid \
stradivari amati guarneri"
classify(){ local w; w=$(printf '%s' "${1:-}" | tr 'A-Z' 'a-z' | tr -c 'a-z0-9' ' '); local o=""
  for k in $KEYWORDS; do case " $w " in *" $k "*) o="$o $k";; esac; done; printf '%s' "${o# }"; }

# searchable tokens from the library display name (typed Search). not shown as .kw buttons.
# drop filler / file-format noise so Patch pills can discern libraries
STOPWORDS="a an the and or of to in on at by for from with into onto upon as vs via \
is it its this that these those be was were are not no nor but so if then than \
your my our their you we they he she them us me \
vol version ver rev patch patches preset presets nki nkm nkr dspreset ds \
wav ogg flac mp3 midi kit bank inst lib \
demo free edition ed unpack unpacked mac win windows linux \
v1 v2 v3 v4 v5 v6 v7 v8 v9"
PATCH_NOISE="default init user multi mic mics unpacked"
is_stop(){ case " $STOPWORDS " in *" $1 "*) return 0;; esac; return 1; }
name_tokens(){ local raw t o=""
  raw=$(printf '%s' "${1:-}" | tr 'A-Z' 'a-z' | tr -c 'a-z0-9' ' ')
  for t in $raw; do
    [ "${#t}" -lt 2 ] && continue
    case "$t" in [0-9]|[0-9][0-9]) continue ;; esac   # drop useless 1-2 digit numbers; keep 808-style
    is_stop "$t" && continue
    o="$o $t"
  done
  printf '%s' "${o# }"; }
patch_tokens(){ local raw t o=""
  raw=$(name_tokens "${1:-}")
  for t in $raw; do
    [ "${#t}" -lt 3 ] && continue
    case " $PATCH_NOISE " in *" $t "*) continue ;; esac
    o="$o $t"
  done
  printf '%s' "${o# }"; }
other_from_name(){ local classified=" $1 " t o=""
  for t in $2; do
    case "$classified" in *" $t "*) continue ;; esac
    o="$o $t"
  done
  printf '%s' "${o# }"; }
uniq_tokens(){ local seen=" " t o=""
  for t in $1; do
    [ -z "$t" ] && continue
    case "$seen" in *" $t "*) continue ;; esac
    seen="$seen$t "
    o="$o $t"
  done
  printf '%s' "${o# }"; }

# ---- category map for keyword buttons (emitted as JS object at build time) ----
KW_CATS_JS='{"piano":"instrument","keys":"instrument","organ":"instrument","harmonium":"instrument","celeste":"instrument","harpsichord":"instrument","clavinova":"model","wurlitzer":"instrument","choir":"instrument","vocal":"instrument","voice":"instrument","strings":"instrument","string":"instrument","violin":"instrument","cello":"instrument","viola":"instrument","domra":"instrument","guitar":"instrument","bass":"instrument","bassoon":"instrument","harp":"instrument","mandolin":"instrument","lute":"instrument","flute":"instrument","recorder":"instrument","ocarina":"instrument","whistle":"instrument","woodwind":"instrument","reed":"instrument","clarinet":"instrument","oboe":"instrument","drum":"instrument","drums":"instrument","percussion":"instrument","kalimba":"instrument","bell":"instrument","bells":"instrument","glock":"instrument","chimes":"instrument","bodhran":"instrument","tabla":"instrument","tablas":"instrument","xylophone":"instrument","marimba":"instrument","synth":"instrument","pad":"instrument","bowed":"instrument","accordion":"instrument","saxophone":"instrument","harmonica":"instrument","melodica":"instrument","bagpipe":"instrument","didgeridoo":"instrument","flutina":"instrument","ukulele":"instrument","autoharp":"instrument","lapsteel":"instrument","dobro":"instrument","hurdy":"instrument","lyre":"instrument","erhu":"instrument","kantele":"instrument","gusli":"instrument","bandola":"instrument","guitarron":"instrument","jaw":"instrument","tongue":"instrument","bowl":"instrument","cajon":"instrument","djembe":"instrument","udu":"instrument","clave":"instrument","brass":"instrument","horn":"instrument","gamelan":"instrument","orchestra":"instrument","guitarist":"instrument","mellotron":"instrument","rhodes":"instrument","hammond":"instrument","optigan":"instrument","chamberlin":"instrument","fairlight":"instrument","synclavier":"instrument","gretsch":"brand","moog":"brand","oberheim":"brand","korg":"brand","roland":"brand","yamaha":"brand","casio":"brand","arp":"instrument","emu":"brand","ppg":"brand","steinway":"brand","broadwood":"brand","ensoniq":"brand","ibanez":"brand","digitech":"brand","selmer":"brand","stradivari":"brand","amati":"brand","guarneri":"brand","808":"model","909":"model","707":"model","606":"model","727":"model","cr-78":"model","cr78":"model","tr-808":"model","tr-909":"model","linndrum":"model","juno":"model","jupiter":"model","minimoog":"model","prophet":"model","dx7":"model","sh-101":"model","ms-20":"model","op-1":"model","volca":"model","leslie":"model","dfam":"model","casiotone":"model","tx81z":"model","drone":"vibe","ambient":"vibe","texture":"vibe","noise":"vibe","fx":"vibe","fm":"vibe","granular":"vibe","glitch":"vibe","lofi":"vibe","vintage":"vibe","cinematic":"vibe","orchestral":"vibe","ethereal":"vibe","atmospheric":"vibe","hybrid":"vibe","world":"vibe","analog":"vibe","soul":"vibe"}'

# description from a readme/txt/rtf in the library folder (junk-filtered). empty if none/unusable.
desc_for(){ local d="${1:-}" rf raw txt
  [ -n "$d" ] && [ -d "$d" ] || return 0
  rf=$(find "$d" -maxdepth 3 -type f \( -iname 'readme*' -o -iname 'read me*' -o -iname '*description*' -o -iname 'about*' -o -iname 'info*.txt' -o -iname 'manual*.txt' \) 2>/dev/null | grep -viE '/__MACOSX/|/\._' | head -1)
  [ -z "$rf" ] && return 0
  case "$(file -b --mime-type "$rf" 2>/dev/null)" in text/*|application/rtf) : ;; *) return 0 ;; esac
  raw=$(tr -d '\000' < "$rf" 2>/dev/null)
  if printf '%s' "$raw" | head -c 6 | grep -q '{\\rtf'; then
    txt=$(printf '%s' "$raw" | sed -e 's/\\par[d]*/\n/g' -e 's/{\\[^ }]*//g' -e 's/\\[a-zA-Z]*[0-9]*//g' -e 's/[{}]//g')
  else txt="$raw"; fi
  txt=$(printf '%s\n' "$txt" | sed 's/\r$//' \
    | grep -viE '^[[:space:]]*[-=_*#]{3,}[[:space:]]*$' \
    | grep -viE '^[[:space:]]*(the story|story|usage|faq|installation|install|included|release notes|date:|by:|created by:|version|copyright|license|www\.|http|contents|table of contents|version history|readme file|changelog)' \
    | grep -viE '/mnt/|/home/|file://|[A-Za-z]:[\\/]' \
    | sed '/^[[:space:]]*$/d' | tr '\n' ' ' | sed 's/  */ /g; s/^ //')
  case "$(printf '%s' "$txt" | tr 'A-Z' 'a-z')" in *"your full name"*|*"your sample pack"*|*"lorem ipsum"*) return 0;; esac
  printf '%s' "$txt" | cut -c1-2500 | sed 's/[[:space:]]*$//'; }

# 1–5 sentence catalog blurb. Heuristic only (no Gemini/API key in env).
# Cleans paths / TOC / license junk. Fallback: product line + comma-separated tags.
desc_blurb(){
  local name="${1:-}" text="${2:-}" kw="${3:-}" product="${4:-Native Instruments library}"
  python3 - "$name" "$text" "$kw" "$product" <<'PY'
import re, sys
name, text, kw, product = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
PATH_RE = re.compile(
    r'(?i)(?:file://)?(?:[A-Za-z]:)?/(?:mnt|home|Users|usr|opt|var|tmp|windows|program files)[^\s]*'
    r'|[A-Za-z]:\\[^\s]+'
    r'|(?<![A-Za-z0-9])/(?:mnt|home|Users|usr)/[^\s,;]+'
)
JUNK_HEAD = re.compile(
    r'(?i)^(contents|table of contents|version history|readme(\s+file)?|'
    r'installation|install(?:ation)?|license|copyright|changelog|release notes|'
    r'faq|usage|the story|included|by:|created by:|date:|version\b|www\.|https?://)'
)
JUNK_PHRASE = re.compile(
    r'(?i)\b(contents|version history|readme file|table of contents|all rights reserved|known issues)\b'
)
RTF_FONT = re.compile(r'(?i)\b(times new roman|calibri|arial|fonttbl|fcharset|wingdings|courier new)\b')
HEADING_ONLY = re.compile(r'(?i)^(introduction|known issues|contents|chapter|section|appendix|overview)\b')

def is_junk(s):
    sl = s.lower().strip()
    if not sl or len(sl) < 12:
        return True
    if PATH_RE.search(s) or JUNK_HEAD.match(s):
        return True
    if JUNK_PHRASE.search(sl) and (len(sl) < 100 or HEADING_ONLY.match(sl)):
        return True
    if HEADING_ONLY.match(sl) and not re.search(r'(?i)\b(thank you|this (library|instrument)|recorded|samples)\b', sl):
        return True
    if len(re.findall(r'\b\d+\.\s+[A-Z]', s)) >= 2:
        return True
    letters = sum(c.isalpha() for c in s)
    digits = sum(c.isdigit() for c in s)
    if RTF_FONT.search(s) or (digits > 12 and letters and digits > letters * 0.45):
        return True
    if sl.count('/') >= 3 and ' ' not in sl[:24]:
        return True
    return False

def sentences_from(raw):
    raw = (raw or '').replace('\r', '\n')
    raw = re.sub(r'https?://\S+', ' ', raw)
    raw = PATH_RE.sub(' ', raw)
    kept_lines = []
    for line in raw.split('\n'):
        t = line.strip()
        if not t or re.match(r'^[-_=*#]{3,}$', t) or JUNK_HEAD.match(t):
            continue
        if JUNK_PHRASE.search(t) and len(t) < 60:
            continue
        kept_lines.append(t)
    blob = re.sub(r'\s+', ' ', ' '.join(kept_lines)).strip()
    parts = re.split(r'(?<=[.!?])\s+', blob) if blob else []
    out = []
    for p in parts:
        p = p.strip()
        if not p or is_junk(p):
            continue
        if not re.search(r'[.!?]$', p):
            p = p.rstrip(';:,') + '.'
        if len(p) > 280:
            p = p[:277].rsplit(' ', 1)[0] + '.'
        out.append(p)
        if len(out) >= 5:
            break
    return out

sents = sentences_from(text)
if sents:
    print(' '.join(sents), end='')
    raise SystemExit(0)
print('%s: %s.' % (product, name), end='')
tags = []
seen = set()
for t in kw.split():
    if t and t not in seen:
        seen.add(t)
        tags.append(t)
if tags:
    print(' Tags: %s.' % ', '.join(tags), end='')
PY
}

banner_for(){ # alias -> best banner image path (or empty)
  local a; a="${1:-}"
  local d; d="$NIIMG/$a"
  if   [ -f "$d/MST_artwork.png" ]; then printf '%s' "$d/MST_artwork.png"
  elif [ -f "$d/MST_logo.png" ];    then printf '%s' "$d/MST_logo.png"
  fi
  return 0
}

emit_img(){ # src -> embedded base64 <img> in BOTH modes (few images; guarantees display, self-contained).
  local src="$1" name="$2"
  # desktop: sharper x160 q82 ; portable: smaller x110 q70
  local h q; if [ "$MODE" = portable ]; then h=110; q=70; else h=160; q=82; fi
  local b64="" mime="image/jpeg"
  if [ "$HAVE_MAGICK" -eq 1 ]; then
    local s="$THUMBS/.m_$N.jpg"
    { magick "$src" -background white -flatten -resize x$h -quality $q "$s" 2>/dev/null || \
      convert "$src" -background white -flatten -resize x$h -quality $q "$s" 2>/dev/null; }
    [ -f "$s" ] && b64=$(base64 -w0 "$s") && rm -f "$s"
  fi
  if [ -z "$b64" ]; then
    b64=$(base64 -w0 "$src" 2>/dev/null)
    mime=$(file --mime-type -b "$src" 2>/dev/null); [ -z "$mime" ] && mime="image/png"
  fi
  printf '  <div class="cover"><img src="data:%s;base64,%s" alt="%s"></div>\n' "$mime" "$b64" "$(e "$name")"
}

# ---- nested collapsible patch listing for a library ----------------------------
# Enumerates .nki patch files under the library root (recursively, maxdepth 6),
# groups them by their subfolder relative to the root, and emits <details>/<summary>.
# Libraries with only encoded/monolith content (.nkx and no loose .nki) show a note.
emit_patches(){
  local root="$1"
  [ -n "$root" ] && [ -d "$root" ] || { printf '  <div class="patches nopatch"><i>no browsable patches</i></div>\n'; return 0; }

  # collect .nki files (skip mac cruft); relative path from root
  local nki_list="$ART_DIR/.knki.$MODE.$N.tmp"; : > "$nki_list"
  local found=0 f rel
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    rel="${f#"$root"/}"
    printf '%s\n' "$rel" >> "$nki_list"
    found=1
  done < <(find "$root" -maxdepth 6 -type f -iname '*.nki' 2>/dev/null \
             | grep -viE '/__MACOSX/|/\._' | sort -f)

  if [ "$found" -eq 0 ]; then
    rm -f "$nki_list"
    printf '  <div class="patches nopatch"><i>no browsable patches</i></div>\n'
    return 0
  fi

  local total; total=$(wc -l < "$nki_list" | tr -cd '0-9')
  printf '  <details class="patches" data-patch-count="%s"><summary>Patches (%s)</summary>\n' "$total" "$total"

  # unique group subfolders (dir of rel path, or "(root)")
  local groups="$ART_DIR/.kgrp.$MODE.$N.tmp"; : > "$groups"
  while IFS= read -r rel; do
    [ -z "$rel" ] && continue
    case "$rel" in
      */*) printf '%s\n' "${rel%/*}" >> "$groups" ;;
      *)   printf '%s\n' "(root)"    >> "$groups" ;;
    esac
  done < "$nki_list"

  # how many distinct groups? if only ONE, flatten: list patches directly under Patches (no nested toggle).
  local ngroups; ngroups=$(sort -f -u "$groups" | grep -c .)
  local base
  if [ "$ngroups" -le 1 ]; then
    printf '      <ul class="patchlist">\n'
    while IFS= read -r rel; do
      [ -z "$rel" ] && continue
      base="${rel##*/}"; base="${base%.*}"
      printf '        <li>%s</li>\n' "$(e "$base")"
    done < "$nki_list"
    printf '      </ul>\n'
    rm -f "$nki_list" "$groups"
    printf '  </details>\n'
    return 0
  fi

  # multiple groups: nested collapsible groups, each CLOSED so you open them individually.
  local grp gcnt
  while IFS= read -r grp; do
    [ -z "$grp" ] && continue
    # count patches in this group first (so the summary can show the count)
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
      printf '        <li>%s</li>\n' "$(e "$base")"
    done < "$nki_list"
    printf '      </ul>\n'
    printf '    </details>\n'
  done < <(sort -f -u "$groups")

  printf '  </details>\n'
  rm -f "$nki_list" "$groups"
  return 0
}

entry(){
  local name="$1" path="$2" pnames="${3:-}"
  N=$((N+1)); local id; id=$(anchor "$N")
  local raw_dsc; raw_dsc=$(desc_for "$path")
  local kw; kw=$(classify "$name $raw_dsc")   # name + desc feed instrument tags; patch tokens are teal
  local dsc; dsc=$(desc_blurb "$name" "$raw_dsc" "$kw" "Native Instruments library")
  local ntoks; ntoks=$(name_tokens "$name")
  local other; other=$(other_from_name "$kw" "$ntoks")
  local ptoks; ptoks=$(uniq_tokens "$(patch_tokens "$pnames")")
  local enc; enc=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote_plus(sys.argv[1]))" "$name" 2>/dev/null || printf '%s' "$name" | sed 's/ /+/g; s/&/%26/g; s/"/%22/g')
  local yturl weburl imgurl
  yturl=$(printf 'https://www.youtube.com/results?search_query=%s+kontakt+library' "$enc")
  weburl=$(printf 'https://www.google.com/search?q=%s+vst+instrument' "$enc")
  imgurl=$(printf 'https://www.google.com/search?tbm=isch&q=%s+kontakt+library' "$enc")
  printf '<li data-kw="%s"><a href="#%s">%s</a></li>\n' "$(e "$kw")" "$id" "$(e "$name")" >> "$IDX"
  local pcount=0
  if [ -n "$path" ] && [ -d "$path" ]; then
    pcount=$(find "$path" -maxdepth 6 -type f -iname '*.nki' 2>/dev/null | grep -viE '/__MACOSX/|/\._' | grep -c .)
  fi
  [ -z "$pcount" ] && pcount=0
  {
    printf '<div class="entry" id="%s" data-kw="%s" data-name="%s" data-other="%s" data-patch="%s" data-patch-count="%s">\n' "$id" "$(e "$kw")" "$(eattr "$name")" "$(e "$other")" "$(e "$ptoks")" "$pcount"
    printf '  <div class="card-chrome card-chrome-start">\n'
    printf '  <button type="button" class="preview-back" aria-label="Back" onclick="event.preventDefault();event.stopPropagation();closeChosenPreview()">&#x2190;</button>\n'
    printf '  <button type="button" class="fav-btn" aria-label="Favorite" aria-pressed="false" onclick="event.preventDefault();event.stopPropagation();toggleFav(this)">&#x2661;</button>\n'
    printf '  </div>\n'
    printf '  <div class="card-chrome card-chrome-end">\n'
    printf "  <button type=\"button\" class=\"fs-btn\" aria-label=\"Open fullscreen\" onclick=\"event.preventDefault();event.stopPropagation();openOverlay(this.closest('.entry'))\">&#x26F6;</button>\n"
    printf "  <button type=\"button\" class=\"hl-min\" aria-label=\"Minimize\" title=\"Minimize\" onclick=\"event.preventDefault();event.stopPropagation();minimizeExpandedCard(this.closest('.entry'))\">&#x2212;</button>\n"
    printf '  <button type="button" class="hl-close" aria-label="Close" onclick="clearHighlight();event.stopPropagation()">&#x2715;</button>\n'
    printf '  </div>\n'
    printf '  <span class="un-badge" hidden title="User notes" aria-label="User notes">&#x1F4AC;</span>\n'
    local shown=0
    local b; b=$(banner_for "$name")
    if [ -n "$b" ] && [ -f "$b" ]; then emit_img "$b" "$name"; shown=1; fi
    printf '  <div class="hl-body">\n'
    printf '    <h3 class="lib-name">%s</h3>\n' "$(e "$name")"
    printf '    <div class="lib-notes">\n'
    printf '      <p class="note-text" hidden></p>\n'
    printf '      <button type="button" class="note-balloon" aria-label="Edit note" onclick="event.preventDefault();event.stopPropagation();openNotePop(this)">&#x1F4AC;</button>\n'
    printf '      <div class="note-pop" hidden role="dialog" aria-label="Library note">\n'
    printf '        <textarea class="note-ta" rows="4" placeholder="Your notes..."></textarea>\n'
    printf '        <div class="note-pop-actions"><button type="button" class="note-save" onclick="event.preventDefault();event.stopPropagation();saveNotePop(this)">Save</button><button type="button" class="note-cancel" onclick="event.preventDefault();event.stopPropagation();cancelNotePop(this)">Cancel</button></div>\n'
    printf '      </div>\n'
    printf '    </div>\n'
    printf '    <div class="summary-panel">\n'
    printf '      <p class="desc">%s</p>\n' "$(e "$dsc")"
    printf '    </div>\n'
    if [ "$MODE" = portable ]; then
      printf '    <div class="path"><b>path:</b> <code>%s</code></div>\n' "$(e "$path")"
    else
      local url; url="file://$(printf '%s' "$path" | sed 's/ /%20/g')"
      printf '    <div class="path"><b>path:</b> <code>%s</code> &nbsp;<a class="folder" href="%s">[open folder]</a></div>\n' "$(e "$path")" "$(e "$url")"
    fi
    emit_patches "$path"
    local act_cls="card-actions"; [ "$shown" -eq 0 ] && act_cls="card-actions card-actions--noart"
    printf '    <div class="%s">\n' "$act_cls"
    printf '      <button class="search-link search-popup-btn" onclick="openSearchModal(this);event.stopPropagation()" data-yt="%s" data-web="%s" data-img="%s" data-name="%s">&#x1F50D; Search</button>\n' "$(e "$yturl")" "$(e "$weburl")" "$(e "$imgurl")" "$(e "$name")"
    printf '    </div>\n'
    printf '  </div>\n'
    printf '</div>\n'
  } >> "$BODY"
}

loc_key(){
  case "$1" in
    /mnt/btrfs_disk*) printf '%s' btrfs ;;
    /mnt/wd_black*) printf '%s' wd_black ;;
    /mnt/storage*) printf '%s' storage ;;
    /mnt/workspace*) printf '%s' workspace ;;
    /home/*) printf '%s' home ;;
    *) printf '%s' other ;;
  esac
}
emit_loc_group(){
  local key="$1" title="$2" root="$3"
  local tmp="$ART_DIR/.kloc.$MODE.$key.tmp"
  : > "$tmp"
  while IFS=$'\t' read -r alias path pnames; do
    [ -z "$alias" ] && continue
    [ "$(loc_key "$path")" = "$key" ] || continue
    printf '%s\t%s\t%s\n' "$alias" "$path" "$pnames" >> "$tmp"
  done < "$LIBLIST"
  if [ ! -s "$tmp" ]; then rm -f "$tmp"; return 0; fi
  printf '<div class="loc-group">\n' >> "$BODY"
  printf '<h2>%s</h2>\n' "$(e "$title")" >> "$BODY"
  printf '<p class="loc-hint">Root: <code>%s</code></p>\n' "$(e "$root")" >> "$BODY"
  while IFS=$'\t' read -r alias path pnames; do
    [ -z "$alias" ] && continue
    alias=$(name_override "$alias")
    entry "$alias" "$path" "$pnames"
  done < "$tmp"
  printf '</div>\n' >> "$BODY"
  rm -f "$tmp"
}
emit_loc_group btrfs "1. btrfs_disk" "/mnt/btrfs_disk"
emit_loc_group wd_black "2. WD Black" "/mnt/wd_black"
emit_loc_group storage "3. Storage" "/mnt/storage"
emit_loc_group workspace "4. Workspace" "/mnt/workspace"
emit_loc_group home "5. Home" "$HOME"
emit_loc_group other "6. Other locations" "/"
rm -f "$LIBLIST"

{
  cat <<'HTML'
<!DOCTYPE html><html lang="en" data-theme="desert"><head><script>(function(){var s=[50,67,75,80,90,100,110,125,133,140,150,175,200,250,300];var r=document.documentElement;var n=100;try{var v=parseInt(localStorage.getItem("catalog-ui-scale-kontakt")||"",10);if(s.indexOf(v)>=0)n=v;}catch(e){}r.style.setProperty("--ui-scale",String(n/100));r.setAttribute("data-ui-scale",String(n));var sn=100;try{var sv=parseInt(localStorage.getItem("catalog-search-only-ui-scale-kontakt")||"",10);if(s.indexOf(sv)>=0)sn=sv;}catch(e){}r.style.setProperty("--search-ui-scale",String(sn/100));r.setAttribute("data-search-ui-scale",String(sn));})();</script><meta charset="utf-8">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="viewport" id="catalogViewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Kontakt Library</title>
<style>
 [data-theme="desert"]{--bg:#0f0f12;--bg-surface:#141417;--bg-card:#1a1a20;--text:#e8e0d0;--text-muted:#8a8070;--border:#2a2820;--accent-instrument:#e8c84a;--accent-gear:#e07830;--accent-instrument-bg:rgba(232,200,74,0.18);--accent-gear-bg:rgba(224,120,48,0.18);--accent-instrument-active:#fff0a0;--accent-gear-active:#ffb060}
 [data-theme="studio"]{--bg:#080c14;--bg-surface:#0e1620;--bg-card:#101824;--text:#c8d8e8;--text-muted:#5a7080;--border:#1a2838;--accent-instrument:#e8c84a;--accent-gear:#e07830;--accent-instrument-bg:rgba(232,200,74,0.15);--accent-gear-bg:rgba(224,120,48,0.15);--accent-instrument-active:#fff0a0;--accent-gear-active:#ffb060}
 [data-theme="smoked"]{--bg:#181818;--bg-surface:#1e1e1e;--bg-card:#222222;--text:#d8d0c8;--text-muted:#706860;--border:#2a2826;--accent-instrument:#e8c84a;--accent-gear:#e07830;--accent-instrument-bg:rgba(232,200,74,0.16);--accent-gear-bg:rgba(224,120,48,0.16);--accent-instrument-active:#fff0a0;--accent-gear-active:#ffb060}
 [data-theme="sandstorm"]{--bg:#f5edd8;--bg-surface:#ede0c4;--bg-card:#faf5e8;--text:#3a2a14;--text-muted:#8a7050;--border:#d8c8a0;--accent-instrument:#a07010;--accent-gear:#b04808;--accent-instrument-bg:rgba(160,112,16,0.15);--accent-gear-bg:rgba(176,72,8,0.15);--accent-instrument-active:#c89020;--accent-gear-active:#d06010}
 [data-theme="bleached"]{--bg:#faf7f0;--bg-surface:#f0ece4;--bg-card:#ffffff;--text:#2a2520;--text-muted:#807060;--border:#ddd8cc;--accent-instrument:#9a7808;--accent-gear:#a84010;--accent-instrument-bg:rgba(154,120,8,0.12);--accent-gear-bg:rgba(168,64,16,0.12);--accent-instrument-active:#c8a020;--accent-gear-active:#cc5820}
 [data-theme="spring-bloom"]{--bg:#f0f8ec;--bg-surface:#e4f0dc;--bg-card:#fafff8;--text:#1a3010;--text-muted:#507040;--border:#b8d8a8;--accent-instrument:#208040;--accent-gear:#c03080;--accent-instrument-bg:rgba(32,128,64,0.14);--accent-gear-bg:rgba(192,48,128,0.14);--accent-instrument-active:#40c070;--accent-gear-active:#e050a0}
 [data-theme="spring-rain"]{--bg:#080f0a;--bg-surface:#0e1a10;--bg-card:#121e14;--text:#c8e8c0;--text-muted:#507050;--border:#1a2e1c;--accent-instrument:#40c878;--accent-gear:#80e840;--accent-instrument-bg:rgba(64,200,120,0.15);--accent-gear-bg:rgba(128,232,64,0.15);--accent-instrument-active:#80ffb0;--accent-gear-active:#b0ff60}
 [data-theme="summer-beach"]{--bg:#fdf5e0;--bg-surface:#f5e8c8;--bg-card:#fffdf5;--text:#2a1808;--text-muted:#806040;--border:#e0c888;--accent-instrument:#0080c0;--accent-gear:#e04000;--accent-instrument-bg:rgba(0,128,192,0.14);--accent-gear-bg:rgba(224,64,0,0.14);--accent-instrument-active:#20a8f0;--accent-gear-active:#ff6020}
 [data-theme="tropical-night"]{--bg:#04100e;--bg-surface:#081a18;--bg-card:#0a2020;--text:#b0f0e0;--text-muted:#307060;--border:#103028;--accent-instrument:#00d4a0;--accent-gear:#f0c000;--accent-instrument-bg:rgba(0,212,160,0.15);--accent-gear-bg:rgba(240,192,0,0.15);--accent-instrument-active:#40ffcc;--accent-gear-active:#ffe040}
 [data-theme="autumn-ember"]{--bg:#100806;--bg-surface:#1c1008;--bg-card:#221408;--text:#f0d8b0;--text-muted:#806040;--border:#302010;--accent-instrument:#e09020;--accent-gear:#c04010;--accent-instrument-bg:rgba(224,144,32,0.18);--accent-gear-bg:rgba(192,64,16,0.18);--accent-instrument-active:#ffb840;--accent-gear-active:#ff6030}
 [data-theme="harvest"]{--bg:#faf0d8;--bg-surface:#f0e0b8;--bg-card:#fffaf0;--text:#2a1808;--text-muted:#806030;--border:#d8b870;--accent-instrument:#a05800;--accent-gear:#903010;--accent-instrument-bg:rgba(160,88,0,0.14);--accent-gear-bg:rgba(144,48,16,0.14);--accent-instrument-active:#c87810;--accent-gear-active:#c05020}
 [data-theme="arctic"]{--bg:#f0f5ff;--bg-surface:#e0eaf8;--bg-card:#f8fbff;--text:#101828;--text-muted:#5070a0;--border:#b8d0e8;--accent-instrument:#1060c0;--accent-gear:#8020a0;--accent-instrument-bg:rgba(16,96,192,0.13);--accent-gear-bg:rgba(128,32,160,0.13);--accent-instrument-active:#3090f0;--accent-gear-active:#b040d0}
 [data-theme="deep-winter"]{--bg:#060810;--bg-surface:#0a0e1c;--bg-card:#0e1228;--text:#c0cce0;--text-muted:#405070;--border:#141a30;--accent-instrument:#6090e0;--accent-gear:#a060e0;--accent-instrument-bg:rgba(96,144,224,0.15);--accent-gear-bg:rgba(160,96,224,0.15);--accent-instrument-active:#90c0ff;--accent-gear-active:#d090ff}
 [data-theme="hc-dark"]{--bg:#000000;--bg-surface:#0a0a0a;--bg-card:#111111;--text:#ffffff;--text-muted:#cccccc;--border:#444444;--accent-instrument:#ffff00;--accent-gear:#ff8000;--accent-instrument-bg:rgba(255,255,0,0.2);--accent-gear-bg:rgba(255,128,0,0.2);--accent-instrument-active:#ffff88;--accent-gear-active:#ffbb44}
 [data-theme="hc-light"]{--bg:#ffffff;--bg-surface:#f0f0f0;--bg-card:#ffffff;--text:#000000;--text-muted:#333333;--border:#000000;--accent-instrument:#0000cc;--accent-gear:#990000;--accent-instrument-bg:rgba(0,0,204,0.15);--accent-gear-bg:rgba(153,0,0,0.15);--accent-instrument-active:#0000ff;--accent-gear-active:#cc0000}
 html{--hl-backdrop:rgba(0,0,0,.55);--hl-shadow:0 12px 48px rgba(0,0,0,.45);--accent-patch:#3ecfbf;--accent-patch-bg:rgba(62,207,191,0.18);--accent-patch-active:#7eefe4;--catalog-max:1800px;--ui-base:16px;--ui-scale:1;--search-ui-scale:1;--cat-land-cols:3;--card-chrome-inset:.5rem;--card-chrome-btn:2.75rem;--card-chrome-gap:.5rem;--safe-top:env(safe-area-inset-top,0px);--safe-right:env(safe-area-inset-right,0px);--safe-bottom:env(safe-area-inset-bottom,0px);--safe-left:env(safe-area-inset-left,0px);--sides-pane-gap:clamp(4px,.35em,8px);font-size:calc(var(--ui-base) * var(--ui-scale))}
 *{box-sizing:border-box}
 html,body{min-height:100vh;min-height:100dvh}
 @media (min-width:1920px){html{--catalog-max:min(96vw,2200px)}}
 @media (min-width:2560px){html{--catalog-max:min(96vw,3000px)}}
 @media (min-width:3200px){html{--catalog-max:min(96vw,3400px)}}
 @media (min-width:3840px){html{--catalog-max:min(96vw,3800px)}}
 body{font-family:system-ui,Segoe UI,Roboto,sans-serif;max-width:min(100%,var(--catalog-max,1800px));margin:0 auto;padding:clamp(.5rem,2vw,2rem);line-height:1.5;color:var(--text);background:var(--bg);font-size:1rem}
 .catalog-header{display:flex;align-items:center;flex-wrap:nowrap;gap:.75rem;width:100%;max-width:100%;box-sizing:border-box;min-width:0;margin:0 0 .2rem}
 .catalog-header h1{flex:1 1 auto;min-width:0;margin:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
 .catalog-header .theme-picker{flex:0 0 auto;margin-left:auto;max-width:min(12rem,46vw);min-width:0}
 h1{margin-bottom:.2rem;color:var(--text);font-size:clamp(1.35rem,4.2vw,2rem)} h2{margin-top:2rem;border-bottom:2px solid var(--border);padding-bottom:.2rem;color:var(--text-muted);font-size:clamp(1.1rem,3.2vw,1.5rem)}
 .filter-wrap{position:sticky;top:0;z-index:210;background:var(--bg-surface);border-bottom:1px solid var(--border);box-sizing:border-box;width:100%;max-width:100%;min-width:0;padding-left:env(safe-area-inset-left,0px);padding-right:env(safe-area-inset-right,0px);display:flex;flex-direction:column}
 .filter-toggle{width:100%;min-height:2.75rem;height:auto;background:transparent;border:none;cursor:pointer;color:var(--text-muted);font-size:1rem;text-align:left;padding:.5rem clamp(.5rem,1.5vw,1rem);display:flex;align-items:center;gap:6px;user-select:none;overflow:hidden;min-width:0}
 .filter-top{display:flex;align-items:center;flex-wrap:wrap;gap:6px;width:100%;max-width:100%;box-sizing:border-box;min-width:0;flex:0 0 auto;position:relative;z-index:2}
 .filter-top .filter-toggle{flex:1 1 7rem;width:auto;min-width:0;max-width:100%;overflow:hidden}
 .filter-top .clear-miss-btn{flex:0 0 auto;position:relative;z-index:2}
 .clear-miss-btn{flex-shrink:0;box-sizing:border-box;min-height:2.25rem;background:transparent;border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:0 .625rem;font-size:.875rem;cursor:pointer;touch-action:manipulation;white-space:nowrap;display:inline-flex;align-items:center;justify-content:center;line-height:1;text-align:center}
 .clear-miss-btn[aria-pressed="true"]{background:var(--accent-instrument-bg);color:var(--accent-instrument);border-color:var(--accent-instrument);font-weight:600}
 .layout-edit-btn{flex-shrink:0;box-sizing:border-box;min-height:2.25rem;background:transparent;border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:0 .625rem;font-size:.875rem;cursor:pointer;touch-action:manipulation;white-space:nowrap}
 .layout-edit-btn[aria-pressed="true"]{background:var(--accent-instrument-bg);color:var(--accent-instrument);border-color:var(--accent-instrument);font-weight:600}
 .layout-default-btn{flex-shrink:0;box-sizing:border-box;min-height:2.25rem;background:transparent;border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:0 .625rem;font-size:.875rem;cursor:pointer;touch-action:manipulation;white-space:nowrap}
 .layout-default-btn:hover{border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 .layout-presets{display:flex;align-items:center;flex-wrap:wrap;gap:6px;width:100%;max-width:100%;box-sizing:border-box;padding:0 clamp(.5rem,1.5vw,1rem) .375rem;min-width:0;flex:0 0 auto;position:relative;z-index:5}
 .layout-presets-store{margin:0 0 6px;font-size:.75em;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--accent-instrument)}
 .layout-presets-tabs{display:flex;gap:6px;flex:0 0 auto;margin:0 0 6px}
 .layout-presets-tab{flex:1 1 0;min-height:2.25rem;padding:0 .5rem;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text-muted);font:inherit;font-size:.8125rem;cursor:pointer;touch-action:manipulation}
 .layout-presets-tab.is-active{background:var(--accent-instrument-bg);color:var(--accent-instrument);border-color:var(--accent-instrument);font-weight:600}
 .layout-presets-btn{flex:0 0 auto;box-sizing:border-box;min-height:2.25rem;background:transparent;border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:0 .625rem;font-size:.875rem;cursor:pointer;touch-action:manipulation;white-space:nowrap}
 .layout-presets-btn[aria-expanded="true"]{background:var(--accent-instrument-bg);color:var(--accent-instrument);border-color:var(--accent-instrument);font-weight:600}
 .layout-presets-pop{display:none;position:fixed;z-index:240;box-sizing:border-box;min-width:min(260px,calc(100vw - 16px));max-width:min(420px,calc(100vw - 16px));max-height:min(52dvh,420px);overflow:hidden;flex-direction:column;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--bg-surface);color:var(--text);box-shadow:0 10px 28px rgba(0,0,0,.35)}
 .layout-presets-pop.open{display:flex}
 .layout-presets-list{overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;min-height:0;flex:1 1 auto;max-height:100%}
 .layout-presets-item{display:flex;align-items:center;gap:6px;width:100%;box-sizing:border-box;margin:0 0 4px;padding:0}
 .layout-presets-item-name{flex:1 1 auto;min-width:0;min-height:2.25rem;text-align:left;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;border:1px solid transparent;border-radius:6px;background:transparent;color:var(--text);font:inherit;cursor:pointer;padding:0 8px}
 .layout-presets-item-name.is-active{background:var(--accent-instrument-bg);color:var(--accent-instrument);border-color:var(--accent-instrument);font-weight:600}
 .layout-presets-item-del{flex:0 0 auto;min-width:2.25rem;min-height:2.25rem;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text-muted);cursor:pointer}
 .layout-presets-save{display:flex;flex-wrap:wrap;gap:6px;flex:0 0 auto;padding-top:6px;border-top:1px solid var(--border)}
 .layout-presets-save input{flex:1 1 8rem;min-width:0;min-height:2.25rem;box-sizing:border-box;padding:0 8px;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text);font:inherit}
 .layout-presets-save button{flex:0 0 auto;min-height:2.25rem;padding:0 10px;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text);font:inherit;cursor:pointer;touch-action:manipulation;transition:background .15s,border-color .15s,color .15s} .layout-presets-save button:active,.layout-presets-save button.is-pressed,.layout-presets-save button.is-flash{background:var(--accent-instrument-bg);color:var(--accent-instrument);border-color:var(--accent-instrument);font-weight:600} .layout-presets-flash{margin:6px 0 0;min-height:1.25em;font-size:.8125rem;font-weight:600;color:var(--accent-instrument);opacity:0;transition:opacity .15s} .layout-presets-flash.is-on{opacity:1}

 .ui-scale{display:flex;align-items:center;gap:4px;flex:0 0 auto;position:relative;z-index:5;min-width:0}
 .ui-scale-step,.ui-scale-readout{box-sizing:border-box;min-height:2.25rem;background:transparent;border:1px solid var(--border);color:var(--text-muted);border-radius:4px;cursor:pointer;touch-action:manipulation;font-size:.875rem;padding:0 .5rem;white-space:nowrap}
 .ui-scale-step{min-width:2.25rem;padding:0}
 .ui-scale-step:disabled{opacity:.4;cursor:default}
 .ui-scale-readout[aria-expanded="true"],.ui-scale-choice.is-active{background:var(--accent-instrument-bg);color:var(--accent-instrument);border-color:var(--accent-instrument);font-weight:600}
 .ui-scale-pop{display:none;position:fixed;z-index:240;box-sizing:border-box;min-width:min(9rem,calc(100vw - 16px));max-width:min(14rem,calc(100vw - 16px));max-height:min(40dvh,22rem);overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;padding:6px;border:1px solid var(--border);border-radius:8px;background:var(--bg-surface);color:var(--text);box-shadow:0 10px 28px rgba(0,0,0,.35)}
 .ui-scale-pop.open{display:flex;flex-direction:column;gap:4px}
 .ui-scale-choice{display:block;width:100%;box-sizing:border-box;min-height:2.25rem;text-align:left;padding:0 .625rem;border:1px solid transparent;border-radius:6px;background:transparent;color:var(--text);font:inherit;cursor:pointer}
 .filter-panel{overflow:hidden;max-height:0;transition:max-height 0.3s ease,padding 0.3s ease;padding:0 clamp(8px,1.5vw,16px);max-width:100%;box-sizing:border-box;position:relative;z-index:1;flex:0 1 auto}
 .filter-wrap.open .filter-panel{max-height:calc(100dvh - 24px);overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;padding:clamp(6px,1vw,12px) clamp(8px,1.5vw,16px)}
 @media(min-width:900px){
  /* Combined split: Search left, Keywords right, catalog visible below. Compact chrome. */
  body.search-mode.kw-open:not(.kw-fs-open):not(.search-chrome-collapsed) .filter-wrap{overflow:hidden}
  body.search-mode.kw-open:not(.kw-fs-open):not(.search-chrome-collapsed):not(.display-sides):not(.display-fs) .filter-wrap.open .filter-panel{position:static!important;width:auto!important;max-width:100%;max-height:var(--upper-kw-h,min(64dvh,44rem))!important;box-shadow:none;border:0;border-radius:0}
  body.search-mode.kw-open:not(.kw-fs-open):not(.search-chrome-collapsed):not(.display-sides):not(.display-fs) .filter-wrap.kw-shade-height-set.open .filter-panel,
  body.search-mode.kw-open:not(.kw-fs-open):not(.search-chrome-collapsed).search-height-set .filter-wrap.open .filter-panel,
  body.search-mode.kw-open:not(.kw-fs-open):not(.search-chrome-collapsed) .search-chrome.search-height-set .filter-wrap.open .filter-panel{position:static!important;width:auto!important;max-width:100%;max-height:none!important;box-shadow:none;border:0;border-radius:0}
  body.search-mode.kw-open:not(.ac-fs-open):not(.search-chrome-collapsed) .search-col{overflow:hidden;z-index:auto}
  body.search-mode.kw-open:not(.ac-fs-open):not(.search-chrome-collapsed):not(.display-sides):not(.display-fs) .search-ac-shell.open:not(.ac-fs),
  body.search-mode.kw-open:not(.ac-fs-open):not(.search-chrome-collapsed):not(.display-sides):not(.display-fs) .search-ac-shell:has(#acList.open):not(.ac-fs){position:relative!important;left:auto!important;top:auto!important;right:auto!important;width:auto!important;max-width:100%!important;height:auto!important;max-height:var(--upper-ac-h,min(64dvh,44rem));box-shadow:none;border:0;border-radius:0;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;overscroll-behavior:contain}
  body.search-mode.kw-open:not(.ac-fs-open):not(.search-chrome-collapsed) .search-chrome.search-height-set .search-ac-shell.open:not(.ac-fs),
  body.search-mode.kw-open:not(.ac-fs-open):not(.search-chrome-collapsed) .search-ac-shell.ac-height-set.open:not(.ac-fs){max-height:none;height:auto}
  body.search-mode.kw-open:not(.ac-fs-open):not(.search-chrome-collapsed):not(.display-sides):not(.display-fs) .search-autocomplete.open{max-height:inherit;overflow-y:auto}
  body.search-mode.kw-open:not(.ac-fs-open):not(.search-chrome-collapsed):not(.display-sides):not(.display-fs) .search-chrome.search-height-set .search-autocomplete.open{max-height:none}
  /* Pick: Keywords stay in-flow. Do not restore the 40vh Shade dropdown. */
  body:not(.search-mode):not(.kw-fs-open):not(.display-sides):not(.display-fs) .filter-wrap{overflow:hidden}
  body:not(.search-mode):not(.kw-fs-open):not(.display-sides):not(.display-fs) .filter-wrap.open .filter-panel{position:static!important;width:auto!important;max-width:100%;max-height:var(--upper-kw-h,min(64dvh,44rem))!important;box-shadow:none;border:0;border-radius:0}
  /* Collapsed toolbar: side dropdowns. Do not overlay the combined split. */
  body.search-mode.search-chrome-collapsed:not(.kw-fs-open) .filter-wrap{overflow:visible}
  body.search-mode.search-chrome-collapsed:not(.kw-fs-open) .filter-wrap.open .filter-panel{position:absolute;top:calc(100% + 4px);right:0;left:auto;width:min(36vw,32rem);max-width:calc(100vw - 1.25rem);max-height:min(56vh,28rem);z-index:230;background:var(--bg-surface);border:1px solid var(--border);border-radius:8px;box-shadow:0 16px 40px rgba(0,0,0,.38)}
  body.search-mode.search-chrome-collapsed:not(.ac-fs-open) .search-col{overflow:visible;z-index:225}
  body.search-mode.search-chrome-collapsed:not(.ac-fs-open) .search-ac-shell.open:not(.ac-fs),
  body.search-mode.search-chrome-collapsed:not(.ac-fs-open) .search-ac-shell:has(#acList.open):not(.ac-fs){position:absolute;left:0;right:auto;top:calc(100% + 4px);width:min(36vw,32rem);max-width:calc(100vw - 1.25rem);max-height:min(56vh,28rem);z-index:226;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;background:var(--bg-surface);border:1px solid var(--border);border-radius:8px;box-shadow:0 16px 40px rgba(0,0,0,.38)}
 }
 body.layout-edit .filter-panel{transition:none}
 body.layout-edit .filter-wrap.open .filter-panel,
 .filter-wrap.kw-shade-height-set.open .filter-panel{max-height:none}
 .toggle-arrow{display:inline-block;transition:transform 0.3s}
 .filter-wrap.open .toggle-arrow{transform:rotate(180deg)}
 .theme-picker{margin-left:0;background:var(--bg-card);color:var(--text-muted);border:1px solid var(--border);border-radius:4px;padding:.25rem .5rem;font-size:.9375rem;cursor:pointer;min-height:2.25rem;max-width:100%}
 .catalog-index{margin:0;width:100%;max-width:100%}
 .catalog-index-head{display:flex;align-items:center;gap:.4rem;margin:1rem 0 .35rem}
 .catalog-index-title{margin:0;font:inherit;font-size:1.125rem;font-weight:600;color:var(--text)}
 .catalog-index-toggle{box-sizing:border-box;min-width:2.25rem;min-height:2.25rem;padding:0;border:1px solid var(--border);border-radius:8px;background:var(--bg-surface);color:var(--text);font:inherit;cursor:pointer;touch-action:manipulation;display:inline-flex;align-items:center;justify-content:center}
 .catalog-index-toggle:hover{border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 .catalog-index-toggle .toggle-arrow{display:inline-block;transition:transform .2s}
 .catalog-index.is-collapsed .index{display:none}
 .catalog-index.is-collapsed .catalog-index-toggle .toggle-arrow{transform:rotate(-90deg)}
.index{column-width:clamp(14rem,28vw,18rem);column-gap:clamp(1rem,2.5vw,2rem);font-size:.9rem;padding-left:0;list-style:none;--index-name-lines:2}
.index li{display:flex;align-items:flex-start;gap:.3em;box-sizing:border-box;break-inside:avoid;margin:.1rem 0;padding:0;list-style:none;max-width:100%;min-width:0;line-height:1.35;white-space:normal;overflow-wrap:anywhere;word-break:break-word}
.index li::before{content:"•";flex:0 0 auto;width:.7em;line-height:1.35;color:var(--text);pointer-events:none}
.index a{flex:1 1 auto;min-width:0;color:var(--accent-instrument);text-decoration:underline;white-space:normal;overflow-wrap:anywhere;word-break:break-word;overflow:hidden;display:block;-webkit-line-clamp:unset;line-clamp:unset;max-height:calc(1.35em * var(--index-name-lines,2));line-height:1.35} .index li.hit{background:var(--accent-instrument-bg);border-radius:3px}
html[data-ui-scale="110"] .index,html[data-ui-scale="125"] .index{--index-name-lines:3}
html[data-ui-scale="133"] .index,html[data-ui-scale="140"] .index,html[data-ui-scale="150"] .index,html[data-ui-scale="175"] .index,html[data-ui-scale="200"] .index,html[data-ui-scale="250"] .index,html[data-ui-scale="300"] .index{--index-name-lines:4}
 .catalog-body{--cat-min:15rem;--cat-cols:repeat(auto-fill,minmax(min(100%,var(--cat-min)),1fr));display:grid;grid-template-columns:var(--cat-cols);gap:clamp(0.6rem,1.2vw,1.15rem);align-items:stretch;margin-top:1rem;width:100%;max-width:100%}
 .catalog-body>h2,.catalog-body>p,.loc-group>h2,.loc-group>p,.loc-group>.loc-hint{grid-column:1/-1;order:-5}
 .loc-group{grid-column:1/-1;display:grid;grid-template-columns:var(--cat-cols);gap:inherit;align-items:start}
 @media (orientation:portrait){
  .catalog-body,.loc-group{--cat-cols:1fr;grid-template-columns:1fr}
  body.search-mode .catalog-body,body.search-mode .loc-group{--cat-cols:1fr;grid-template-columns:1fr}
 }
 @media (orientation:landscape) and (max-width:1023px){
  .catalog-body,.loc-group{--cat-cols:repeat(var(--cat-land-cols,3),minmax(0,1fr));grid-template-columns:repeat(var(--cat-land-cols,3),minmax(0,1fr))}
  body.search-mode .catalog-body,body.search-mode .loc-group{--cat-cols:repeat(var(--cat-land-cols,3),minmax(0,1fr));grid-template-columns:repeat(var(--cat-land-cols,3),minmax(0,1fr))}
 }
 .loc-group.is-hidden{display:none!important}
 .entry.is-hidden{display:none!important}
 .entry.is-hidden.highlight{display:flex!important}
 body.chosen-preview-open .loc-group:has(.entry.selected){display:grid!important}
 body.chosen-preview-open .entry.selected.is-hidden:not(.highlight){display:grid!important}
 .entry{background:var(--bg-card);border:1px solid var(--border);border-radius:8px;padding:.8rem;transition:border-color .2s;display:flex;flex-direction:column;height:auto;min-height:0;overflow:hidden;order:0;position:relative;max-width:100%;min-width:0}
 .entry:hover{border-color:var(--accent-instrument)} .entry h3,.entry .lib-name{margin:.2rem 0;color:var(--text);font-size:clamp(1rem,1.15em,1.375rem);word-wrap:break-word;overflow-wrap:break-word;word-break:normal;hyphens:none;white-space:normal;min-width:0;cursor:pointer}
 .entry.hit{background:var(--accent-instrument-bg);border-left:4px solid var(--accent-gear);padding-left:.6rem}
 .entry.selected{outline:2px solid var(--accent-instrument);outline-offset:2px;border-color:var(--accent-instrument);box-shadow:0 0 0 4px var(--accent-instrument-bg);z-index:2}
 .card-chrome{display:contents}
 .card-chrome-start>.preview-back,.card-chrome-start>.fav-btn,.card-chrome-end>.fs-btn,.card-chrome-end>.hl-min,.card-chrome-end>.hl-close{flex:0 0 auto}
 .preview-back{display:none;position:absolute;top:var(--card-chrome-inset);left:var(--card-chrome-inset);z-index:5;box-sizing:border-box;width:var(--card-chrome-btn);height:var(--card-chrome-btn);min-width:var(--card-chrome-btn);min-height:var(--card-chrome-btn);align-items:center;justify-content:center;padding:0;background:var(--bg-surface);color:var(--text);border:1px solid var(--border);border-radius:8px;cursor:pointer;touch-action:manipulation;font-size:1.375rem;line-height:1}
 .preview-back:hover{color:var(--accent-instrument);border-color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 .fs-btn{display:none;position:absolute;top:var(--card-chrome-inset);right:var(--card-chrome-inset);left:auto;z-index:4;box-sizing:border-box;width:var(--card-chrome-btn);height:var(--card-chrome-btn);min-width:var(--card-chrome-btn);min-height:var(--card-chrome-btn);align-items:center;justify-content:center;padding:0;background:var(--bg-surface);color:var(--accent-instrument);border:1px solid var(--accent-instrument);border-radius:8px;cursor:pointer;touch-action:manipulation;font-size:1.25rem;line-height:1}
 .entry.selected:not(.highlight) .fs-btn{display:flex}
 .entry.highlight .fs-btn{display:none!important}
 .entry.highlight .preview-back{display:none!important}
 .fs-btn:hover{color:var(--accent-instrument-active);border-color:var(--accent-instrument-active);background:var(--accent-instrument-bg)}
 .fav-btn{position:absolute;right:.5rem;bottom:.5rem;top:auto;left:auto;z-index:4;box-sizing:border-box;width:var(--card-chrome-btn);height:var(--card-chrome-btn);min-width:var(--card-chrome-btn);min-height:var(--card-chrome-btn);display:flex;align-items:center;justify-content:center;padding:0;background:var(--bg-surface);color:var(--text-muted);border:1px solid var(--border);border-radius:8px;cursor:pointer;touch-action:manipulation;font-size:1.25rem;line-height:1}
 .fav-btn.on{color:var(--accent-gear);border-color:var(--accent-gear)}
 .fav-btn:hover{color:var(--accent-instrument);border-color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 .entry:not(.highlight) .card-actions{padding-right:3.25rem}
 .entry.highlight .fav-btn{top:max(.5rem,env(safe-area-inset-top));left:max(.5rem,env(safe-area-inset-left));right:auto;bottom:auto}
 body.gallery-open .entry .fav-btn,body.img-focus-open .entry .fav-btn{visibility:hidden}
 .gallery-fav,.img-focus-fav{position:absolute;top:max(.5rem,env(safe-area-inset-top));right:max(.5rem,env(safe-area-inset-right));left:auto;bottom:auto;z-index:3;box-sizing:border-box;width:2.75rem;height:2.75rem;min-width:2.75rem;min-height:2.75rem;display:flex;align-items:center;justify-content:center;padding:0;background:rgba(20,20,24,.82);color:#fff;border:1px solid rgba(255,255,255,.35);border-radius:8px;cursor:pointer;touch-action:manipulation;font-size:1.25rem;line-height:1}
 .gallery-fav.on,.img-focus-fav.on{color:#ffb0a0;border-color:#ffb0a0}
 .un-badge{display:none;position:absolute;top:.5rem;right:.5rem;z-index:3;width:1.75rem;height:1.75rem;min-width:1.75rem;padding:0;align-items:center;justify-content:center;font-size:1rem;font-weight:400;letter-spacing:0;line-height:1;background:var(--accent-instrument-bg);color:var(--accent-instrument);border:1px solid var(--accent-instrument);border-radius:6px;pointer-events:none}
 .un-badge.has-note{display:inline-flex}
 .entry.selected:not(.highlight) .un-badge{right:3.5rem}
 .entry.highlight .un-badge{display:none!important}
 .lib-notes{position:relative;margin:.15rem 0 .35rem}
 .note-text{display:none;margin:.25rem 0;padding:.5rem .7rem;background:var(--bg-surface);border:1px dashed var(--border);border-radius:6px;color:var(--text);font-size:.9375rem;white-space:pre-wrap;overflow-wrap:anywhere}
 .entry.highlight .note-text.has-note{display:block}
 .note-balloon{display:none}
 .entry.highlight .note-balloon{display:inline-flex;align-items:center;justify-content:center;width:2.75rem;height:2.75rem;min-width:2.75rem;min-height:2.75rem;background:var(--bg-surface);color:var(--text-muted);border:1px solid var(--border);border-radius:8px;cursor:pointer;touch-action:manipulation;font-size:1.125rem;line-height:1}
 .note-pop{display:none;position:absolute;z-index:6;left:0;top:48px;width:min(90vw,360px);max-width:min(90vw,360px);background:var(--bg-card);color:var(--text);border:1px solid var(--border);border-radius:8px;padding:10px;box-shadow:var(--hl-shadow)}
 .note-pop.open{display:block}
 .note-ta{width:100%;min-height:88px;resize:vertical;background:var(--bg);color:var(--text);border:1px solid var(--border);border-radius:6px;padding:8px;font:inherit}
 .note-pop-actions{display:flex;gap:8px;margin-top:8px;justify-content:flex-end}
 .note-save,.note-cancel{min-height:2.75rem;min-width:4.5rem;padding:0 14px;border-radius:6px;cursor:pointer;touch-action:manipulation;border:1px solid var(--border);background:var(--bg-surface);color:var(--text);font:inherit}
 .note-save{background:var(--accent-instrument-bg);color:var(--accent-instrument);border-color:var(--accent-instrument)}
 .fav-recs-label{display:none;grid-column:1/-1;order:-20;font-size:.9375rem;color:var(--text-muted);letter-spacing:.06em;text-transform:uppercase;opacity:.9;padding:.35rem 0 .15rem;border-bottom:1px dashed var(--border);margin:0 0 .25rem}
 .index li.selected{background:var(--accent-instrument-bg);border-radius:3px;box-shadow:inset 0 0 0 1px var(--accent-instrument)}
 .hl-backdrop{display:none;position:fixed;inset:0;z-index:850;background:var(--hl-backdrop)}
 .hl-backdrop.open{display:block}
 .hl-ph{visibility:hidden;pointer-events:none}
 body.hl-open{overflow:hidden}
 html.overlay-fs,html.overlay-fs body{overflow:hidden!important;overscroll-behavior:none;height:100%;height:100dvh}
 html.overlay-fs body{position:fixed;width:100%;left:0;right:0}
 body:is(.hl-open,.gallery-open,.img-focus-open,.desc-reader-open,.path-reader-open,.desc-focus-open,.path-focus-open,.chosen-preview-open,.card-embed-open) .top,body:is(.hl-open,.gallery-open,.img-focus-open,.desc-reader-open,.path-reader-open,.desc-focus-open,.path-focus-open,.chosen-preview-open,.card-embed-open) .bottom{visibility:hidden!important;pointer-events:none!important}
 body:is(.hl-open,.gallery-open,.img-focus-open,.desc-reader-open,.path-reader-open,.desc-focus-open,.path-focus-open,.chosen-preview-open,.card-embed-open) :is(.search-chrome,.filter-wrap,.search-ac-shell,.layout-presets-pop,.ui-scale-pop){pointer-events:none!important;z-index:1!important}
 .hl-close{display:none}
 .entry.highlight .hl-close{display:flex;position:absolute;top:max(var(--card-chrome-inset),env(safe-area-inset-top));right:max(var(--card-chrome-inset),env(safe-area-inset-right));z-index:5;width:var(--card-chrome-btn);height:var(--card-chrome-btn);min-width:var(--card-chrome-btn);min-height:var(--card-chrome-btn);font-size:1.375rem;align-items:center;justify-content:center;background:var(--bg-surface);color:var(--text);border:1px solid var(--border);border-radius:8px;cursor:pointer;touch-action:manipulation;line-height:1;padding:0}
 .entry.highlight .hl-close:hover{color:var(--accent-instrument);border-color:var(--accent-instrument)}
 .hl-min{display:none;position:absolute;top:max(var(--card-chrome-inset),env(safe-area-inset-top));right:calc(var(--card-chrome-inset) + var(--card-chrome-btn) + var(--card-chrome-gap));z-index:5;width:var(--card-chrome-btn);height:var(--card-chrome-btn);min-width:var(--card-chrome-btn);min-height:var(--card-chrome-btn);font-size:1.375rem;align-items:center;justify-content:center;background:var(--bg-surface);color:var(--text);border:1px solid var(--border);border-radius:8px;cursor:pointer;touch-action:manipulation;line-height:1;padding:0}
 .entry.highlight .hl-min,body.chosen-preview-open .entry.selected:not(.highlight) .hl-min{display:flex;z-index:841}
 .entry.highlight .hl-min:hover,body.chosen-preview-open .entry.selected:not(.highlight) .hl-min:hover{color:var(--accent-instrument);border-color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 #cardMinDock{display:none;position:fixed;z-index:10040;left:0;width:100%;bottom:0;flex-direction:column;justify-content:flex-end;align-items:center;flex-wrap:nowrap;gap:.4rem;padding:0 .75rem max(.85rem,env(safe-area-inset-bottom));box-sizing:border-box;pointer-events:none;overflow:visible;max-width:100vw}
 #cardMinDock.is-on{display:flex}
 #cardMinDock .card-min-stack{display:flex;flex-direction:column-reverse;justify-content:flex-end;align-items:center;gap:.4rem;width:auto;max-width:100%;pointer-events:none}
 #cardMinDock .card-min-row{display:flex;justify-content:center;align-items:center;flex-wrap:nowrap;gap:.45rem;min-width:0;width:auto;max-width:100%;pointer-events:none}
 #cardMinDock .card-min-pill{pointer-events:auto;display:inline-flex;align-items:center;gap:.35rem;max-width:min(14.5rem,var(--card-min-pill-max,14.5rem));min-width:0;flex:0 0 auto;width:auto;min-height:2.85rem;padding:.28rem;border:1px solid var(--accent-instrument);border-radius:999px;background:var(--bg-card);color:var(--accent-instrument);font:inherit;font-size:1rem;font-weight:650;letter-spacing:.01em;line-height:1.15;cursor:default;touch-action:manipulation;box-shadow:0 8px 28px rgba(0,0,0,.38);transform-origin:center bottom;transition:transform .14s ease,opacity .14s ease,box-shadow .14s ease,border-color .14s ease;opacity:.92}
#cardMinDock .card-min-open{pointer-events:auto;display:inline-flex;align-items:center;gap:.45rem;min-width:0;flex:1 1 auto;margin:0;padding:.15rem .2rem .15rem .15rem;border:0;background:transparent;color:inherit;font:inherit;font-weight:inherit;cursor:pointer;border-radius:999px}
#cardMinDock .card-min-media{display:none;flex:0 0 auto;width:2.15rem;height:2.15rem;border-radius:999px;overflow:hidden;border:1px solid var(--border);background:#000;position:relative}
#cardMinDock .card-min-pill.is-playing .card-min-media{display:block}
#cardMinDock .card-min-pill.is-playing .card-min-open>img{display:none}
#cardMinDock .card-min-media .card-search-embed,#cardMinDock .card-min-media #cardSearchEmbed{display:block!important;position:absolute;inset:-40% -70%;width:240%;height:180%;border:0;border-radius:0;background:#000;pointer-events:none}
#cardMinDock .card-min-media .card-search-chrome,#cardMinDock .card-min-media .card-yt-comments,#cardMinDock .card-min-media .card-search-hint,#cardMinDock .card-min-media .card-search-fallback,#cardMinDock .card-min-media .card-search-reader,#cardMinDock .card-min-media .card-search-img-view,#cardMinDock .card-min-media .card-img-exit{display:none!important}
#cardMinDock .card-min-media .card-search-frame,#cardMinDock .card-min-media #cardSearchFrame{display:block!important;width:100%!important;height:100%!important;border:0;pointer-events:none}
#cardMinDock .card-min-close{pointer-events:auto;flex:0 0 auto;width:1.65rem;height:1.65rem;margin:0;padding:0;border:1px solid var(--border);border-radius:999px;background:var(--bg-surface);color:var(--text);font:inherit;font-size:1.05rem;line-height:1;cursor:pointer}
#cardMinDock .card-min-close:hover{color:var(--accent-instrument);border-color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 #cardMinDock .card-min-pill img{width:2.15rem;height:2.15rem;border-radius:999px;object-fit:cover;flex:0 0 auto;border:1px solid var(--border);background:var(--bg-surface)}
 #cardMinDock .card-min-name{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
 #cardMinDock .card-min-pill:hover{transform:scale(1.08);opacity:1;z-index:1}
 #cardMinDock .card-min-pill.is-front{background:var(--accent-instrument-bg);border-color:var(--accent-instrument-active);color:var(--accent-instrument-active);box-shadow:0 10px 32px rgba(0,0,0,.45);opacity:1}
 body.hl-open #cardMinDock,body.chosen-preview-open #cardMinDock,body.gallery-open #cardMinDock,body.img-focus-open #cardMinDock,body.desc-reader-open #cardMinDock,body.path-reader-open #cardMinDock,body.desc-focus-open #cardMinDock,body.path-focus-open #cardMinDock{visibility:hidden!important;pointer-events:none!important}
 .entry.highlight{position:fixed;inset:0;top:0;left:0;right:0;bottom:0;width:100vw;width:100dvw;height:100vh;height:100dvh;height:100svh;max-width:none;max-height:none;z-index:860;display:flex;flex-direction:column;overflow:hidden;padding:max(52px,calc(env(safe-area-inset-top) + 8px)) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left);box-sizing:border-box;grid-column:unset;transform:none;border-radius:0;outline:2px solid var(--accent-instrument);outline-offset:-2px;background:var(--bg-card);border:1px solid var(--border);box-shadow:var(--hl-shadow)}
 .hl-body{min-width:0}
 .entry.highlight .hl-body{flex:1 1 auto;min-height:0;overflow-y:auto;-webkit-overflow-scrolling:touch;padding:12px 16px 24px}
 .cover{flex:0 0 auto;flex-shrink:0;width:100%;max-width:100%;min-height:clamp(4.5rem,12vw,7.5rem);max-height:clamp(7.5rem,18vw,12.5rem);margin:.3rem 0;display:flex;align-items:center;justify-content:center;overflow:hidden;border:1px solid var(--border);border-radius:4px;background:var(--bg-surface);box-sizing:border-box;cursor:pointer}
 .cover img{width:auto;height:auto;min-width:0;min-height:4.5rem;max-width:100%;max-height:clamp(7.5rem,18vw,12.5rem);object-fit:contain;object-position:center center;display:block;visibility:visible}
 .entry.highlight .cover{flex:0 0 auto;width:100%;max-width:100%;height:auto;max-height:min(38dvh,100%);margin:.3rem 0;overflow:visible;align-items:center;justify-content:center}
 .entry.highlight .cover img{width:auto;height:auto;max-width:100%;max-height:min(38dvh,100%);object-fit:contain;object-position:center center;display:block}
HTML
  if [ "$MODE" != portable ]; then
    cat <<'HOVERCSS'
 .cover img,.entry .cover img{transform-origin:center center;transition:transform .2s ease;pointer-events:auto}
 .entry.highlight .cover img{transform-origin:center center;transition:transform .2s ease;pointer-events:auto}
 @media (hover:hover) and (pointer:fine){
  .entry:not(.highlight) .cover{overflow:visible}
  .entry:not(.highlight):has(.cover:hover){overflow:visible;z-index:8}
  .entry:not(.highlight) .cover img:hover,.entry:not(.highlight) .cover:hover img{transform:scale(1.35);z-index:8;position:relative}
  .entry.highlight .cover img:hover{transform:scale(1.08);z-index:8;position:relative}
 }
HOVERCSS
    cat <<'OVERLAYTITLECSS'
 .entry.highlight h3,.entry.highlight .lib-name{text-align:center;width:100%;max-width:100%;overflow-wrap:break-word;word-break:break-word;white-space:normal;padding-inline:calc(var(--card-chrome-inset) + var(--card-chrome-btn) + var(--card-chrome-gap));box-sizing:border-box}
OVERLAYTITLECSS
  fi
  cat <<'GALLERYCSS'
 .entry.highlight .cover,.entry.highlight .cover img{cursor:pointer;touch-action:none}
 .entry.highlight .summary-panel .desc,.summary-panel .desc{cursor:pointer}
 .path,.entry.highlight .path{cursor:pointer}
 .img-gallery{display:none;position:fixed;inset:0;top:0;left:0;right:0;bottom:0;width:100vw;width:100dvw;height:100vh;height:100dvh;height:100svh;z-index:870;background:#000;align-items:center;justify-content:center;touch-action:none;overflow:hidden;-webkit-user-select:none;user-select:none;overscroll-behavior:none}
 .img-gallery.open{display:flex}
 .img-gallery .gallery-img{max-width:100vw;max-height:100dvh;width:auto;height:auto;object-fit:contain;object-position:center center;transform-origin:center center;pointer-events:none}
 .gallery-back,.desc-reader-back,.path-reader-back{position:absolute;top:max(.5rem,env(safe-area-inset-top));left:max(.5rem,env(safe-area-inset-left));z-index:3;box-sizing:border-box;width:2.75rem;height:2.75rem;min-width:2.75rem;min-height:2.75rem;display:flex;align-items:center;justify-content:center;padding:0;background:rgba(20,20,24,.82);color:#fff;border:1px solid rgba(255,255,255,.35);border-radius:8px;cursor:pointer;touch-action:manipulation;font-size:1.375rem;line-height:1}
 .gallery-title,.img-focus-title{position:absolute;top:max(.5rem,env(safe-area-inset-top));left:calc(max(.5rem,env(safe-area-inset-left)) + 3.25rem);right:calc(max(.5rem,env(safe-area-inset-right)) + 3.25rem);z-index:2;pointer-events:auto;box-sizing:border-box;display:block;min-width:0;max-height:2.5em;margin:0;padding:8px 10px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-family:inherit;font-size:clamp(.8125rem,3.5vw,1rem);font-weight:600;line-height:1.25;text-align:center;color:#fff;background:rgba(0,0,0,.45);border:0;border-radius:8px;cursor:pointer;touch-action:manipulation;-webkit-appearance:none;appearance:none;-webkit-user-select:none;user-select:none}
 .gallery-title.expanded,.img-focus-title.expanded{white-space:normal;overflow:visible;text-overflow:clip;max-height:none;overflow-wrap:anywhere}
 .gallery-zoom,.desc-reader-zoom,.path-reader-zoom{position:absolute;bottom:max(16px,env(safe-area-inset-bottom));left:50%;transform:translateX(-50%);z-index:3;display:flex;align-items:center;gap:8px;background:rgba(0,0,0,.5);border:1px solid rgba(255,255,255,.2);border-radius:8px;padding:6px 12px;touch-action:manipulation}
 .gallery-zoom-btn,.desc-reader-zoom-btn,.path-reader-zoom-btn{width:2.25rem;height:2.25rem;min-width:2.25rem;min-height:2.25rem;border:1px solid rgba(255,255,255,.3);background:transparent;color:#fff;border-radius:6px;cursor:pointer;font-size:1.25rem;line-height:1;touch-action:manipulation}
 .desc-reader,.path-reader{display:none;position:fixed;inset:0;top:0;left:0;right:0;bottom:0;width:100vw;width:100dvw;height:100vh;height:100dvh;height:100svh;z-index:10050;background:var(--bg);color:var(--text);flex-direction:column;box-sizing:border-box;padding:max(52px,calc(env(safe-area-inset-top) + 8px)) max(16px,env(safe-area-inset-right)) env(safe-area-inset-bottom) max(16px,env(safe-area-inset-left));touch-action:manipulation;overscroll-behavior:none}
 .desc-reader.open,.path-reader.open{display:flex}
 .desc-reader-text,.path-reader-text{flex:1 1 auto;min-height:0;overflow-y:auto;-webkit-overflow-scrolling:touch;font-size:clamp(1.125rem,4.8vw,1.375rem);line-height:1.7;max-width:65ch;margin:0 auto;width:100%;touch-action:pan-y;padding-bottom:56px}
 .desc-reader-text h2,.path-reader-text h2{margin:0 0 .6rem;font-size:clamp(1.25rem,5vw,1.625rem);color:var(--text)}
 .desc-reader-text p,.path-reader-text p{margin:0}
 .path-reader-text,.path-reader-text p{overflow-wrap:anywhere;word-break:break-word;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
 body.gallery-open,body.desc-reader-open,body.path-reader-open{overflow:hidden}
GALLERYCSS
  if [ "$MODE" != portable ]; then
    cat <<'FOCUSCSS'
 .img-focus-backdrop,.desc-focus-backdrop,.path-focus-backdrop{display:none;position:fixed;inset:0;z-index:870;background:rgba(0,0,0,.72);align-items:center;justify-content:center;padding:clamp(12px,3vw,32px);overflow:hidden;overscroll-behavior:none}
 .desc-focus-backdrop,.path-focus-backdrop{z-index:10050}
 .desc-focus-zoom,.path-focus-zoom{z-index:10051}
 .img-focus-backdrop{touch-action:none}
 .desc-focus-backdrop,.path-focus-backdrop{touch-action:manipulation}
 .img-focus-backdrop.open,.desc-focus-backdrop.open,.path-focus-backdrop.open{display:flex}
 .img-focus-img{max-width:min(92vw,1400px);max-height:min(88vh,900px);width:auto;height:auto;object-fit:contain;object-position:center center;cursor:zoom-out;transform-origin:center center;-webkit-user-select:none;user-select:none}
 .img-focus-zoom,.desc-focus-zoom,.path-focus-zoom{position:fixed;bottom:max(16px,env(safe-area-inset-bottom));left:50%;transform:translateX(-50%);z-index:871;display:flex;align-items:center;gap:8px;background:rgba(0,0,0,.5);border:1px solid rgba(255,255,255,.2);border-radius:8px;padding:6px 12px}
 .img-focus-zoom-btn,.desc-focus-zoom-btn,.path-focus-zoom-btn{width:2.25rem;height:2.25rem;border:1px solid rgba(255,255,255,.3);background:transparent;color:#fff;border-radius:6px;cursor:pointer;font-size:1.25rem;line-height:1}
 .img-focus-zoom input[type=range]{width:min(40vw,180px);accent-color:var(--accent-instrument)}
 .desc-focus-box,.path-focus-box{background:var(--bg-card);color:var(--text);border:1px solid var(--border);border-radius:10px;max-width:min(42rem,90vw);max-height:min(80vh,820px);overflow:hidden;display:flex;flex-direction:column;padding:clamp(16px,2.5vw,28px);box-shadow:0 12px 48px rgba(0,0,0,.4);cursor:pointer}
 .desc-focus-text,.path-focus-text{overflow-y:auto;font-size:1.125rem;line-height:1.7;max-height:min(72vh,760px);touch-action:pan-y}
 .desc-focus-text h2,.path-focus-text h2{margin:0 0 .6rem;font-size:1.25em;color:var(--text)}
 .desc-focus-text p,.path-focus-text p{margin:0}
 .path-focus-text,.path-focus-text p{overflow-wrap:anywhere;word-break:break-word;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
 body.img-focus-open,body.desc-focus-open,body.path-focus-open{overflow:hidden}
FOCUSCSS
  fi
  cat <<'HTML'
 .summary-panel{width:100%;max-width:100%;min-width:0;overflow:hidden;border-radius:6px;border:1px solid var(--border);margin:clamp(4px,0.6vw,8px) 0;padding:clamp(8px,1.1vw,14px) clamp(10px,1.2vw,16px);background:var(--bg);max-height:8.2em}
 .summary-panel .desc{font-style:normal;font-size:.9375rem;line-height:1.55;color:var(--text);margin:0;overflow-wrap:break-word;word-break:normal;hyphens:none;white-space:normal;max-width:100%}
 .entry.highlight .summary-panel{width:100%;max-width:100%;overflow:visible;overflow-wrap:break-word;background:var(--bg);max-height:none;flex:none}
 .entry.highlight .summary-panel .desc,.entry.highlight .desc{min-height:8em;max-height:none;overflow:visible;font-size:clamp(1rem,4.5vw,1.25rem);max-width:65ch;margin-left:auto;margin-right:auto;margin-bottom:.75rem;line-height:1.65;overflow-wrap:break-word;word-break:normal;hyphens:none;white-space:normal;text-align:left}
 .path{font-size:.8125rem;color:var(--text-muted);margin:.35rem 0 .15rem;overflow-wrap:anywhere}
 .path code{overflow-wrap:anywhere;word-break:break-word}
 .entry.highlight .path,.entry.highlight .path code,.entry.highlight .path .folder{font-size:clamp(.875rem,3.8vw,1.0625rem);color:var(--text-muted)}
 .desc{font-style:italic;color:var(--text-muted);margin:.2rem 0;overflow-wrap:break-word;word-break:normal;min-width:0}
 .entry:not(.highlight) .summary-panel .desc,.entry:not(.highlight) .desc{overflow:hidden}
 .entry.selected:not(.highlight) .summary-panel{max-height:none;overflow:visible}
 .entry.selected:not(.highlight) .summary-panel .desc,.entry.selected:not(.highlight) .desc{max-height:7.2em;overflow-y:auto;-webkit-overflow-scrolling:touch;touch-action:pan-y;overscroll-behavior:contain}
 .entry.selected:not(.highlight) .path{max-height:6em;overflow-y:auto;-webkit-overflow-scrolling:touch;touch-action:pan-y;overscroll-behavior:contain}
 code{background:var(--bg-surface);padding:.05rem .3rem;border-radius:3px;font-size:.82rem;word-break:break-all;color:var(--text-muted)}
 .folder{color:var(--accent-gear);text-decoration:underline;font-size:.82rem;white-space:nowrap}
 .patches{margin:.35rem 0;font-size:.86rem}
 .patches>summary{cursor:pointer;color:var(--accent-instrument);font-weight:600}
 .patches .grp{margin:.2rem 0 .2rem 1rem}
 .patches .grp>summary{cursor:pointer;color:var(--text-muted);font-weight:600}
 .patchlist{margin:.2rem 0 .4rem 1.4rem;padding-left:1rem;columns:2;column-gap:1.5rem}
 .patchlist li{break-inside:avoid;list-style:disc;color:var(--text-muted)}
 .patches.nopatch{color:var(--text-muted);font-style:italic;margin-left:.2rem;opacity:.6}
 .entry.highlight details.patches{max-height:none;overflow:visible}
 #kwbar{display:flex;flex-wrap:wrap;gap:.45rem;margin:.5rem 0;max-width:100%;box-sizing:border-box}
 .kw{cursor:pointer;border:1px solid var(--accent-instrument-bg);background:var(--accent-instrument-bg);border-radius:14px;padding:.375rem .625rem;font-size:.875rem;color:var(--accent-instrument);min-height:2.25rem;touch-action:manipulation;-webkit-touch-callout:none;-webkit-user-select:none;user-select:none}
 .kw:hover{border-color:var(--accent-instrument)} .kw.active{background:var(--accent-instrument-active);color:#1a1008;border-color:var(--accent-instrument)}
 .kw.disabled{color:var(--text-muted);background:transparent;border-color:var(--border);cursor:not-allowed;opacity:.5}
 .kw.clear{background:rgba(180,40,40,0.2);border-color:#c03040;color:#ff9090}
 .kwstatus{font-size:.9375rem;color:var(--accent-instrument);font-weight:600;min-height:1.1em}
 .kw.patch,.kw[data-cat="patch"]{border-color:var(--accent-patch-bg);background:var(--accent-patch-bg);color:var(--accent-patch)}
 .kw.patch:hover,.kw[data-cat="patch"]:hover{border-color:var(--accent-patch)}
 .kw.patch.active,.kw[data-cat="patch"].active{background:var(--accent-patch-active);color:#082422;border-color:var(--accent-patch)}
 .top,.bottom{background:var(--accent-instrument);color:#1a1008;padding:.4rem .7rem;border-radius:4px;text-decoration:none;border:1px solid var(--accent-instrument)}
 .top{position:fixed;bottom:1rem;right:1rem}
 .bottom{position:fixed;top:1rem;right:1rem}
 .mode-switch{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;max-width:100%}
 .mode-btn{background:var(--bg-card);border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:0 12px;font-size:.875rem;cursor:pointer;min-height:2.25rem;touch-action:manipulation;display:inline-flex;align-items:center;justify-content:center;line-height:1;text-align:center}
 .mode-btn.active{background:var(--accent-instrument-bg);color:var(--accent-instrument);border-color:var(--accent-instrument)}
 .entry.dim{order:999;opacity:.25;pointer-events:none}
 .card-actions{display:flex;gap:clamp(4px,0.8vw,8px);padding:clamp(4px,0.6vw,6px) 0 0 0;margin-top:auto}
 .search-link{display:inline-flex;align-items:center;gap:3px;padding:clamp(6px,0.8vw,8px) clamp(8px,1.2vw,12px);border-radius:4px;font-size:.9375rem;text-decoration:none;border:1px solid var(--border);color:var(--text-muted);background:var(--bg);transition:color 0.15s,border-color 0.15s;white-space:nowrap;touch-action:manipulation;min-height:2.25rem}
 .search-link:hover{color:var(--text);border-color:var(--text-muted)}
 .search-popup-btn{display:inline-flex;align-items:center;gap:4px;padding:clamp(6px,0.8vw,8px) clamp(10px,1.5vw,14px);border-radius:4px;font-size:.9375rem;border:1px solid var(--border);color:var(--text-muted);background:var(--bg);cursor:pointer;touch-action:manipulation;min-height:2.25rem;transition:color 0.15s,border-color 0.15s}
 .search-popup-btn:hover{color:var(--text);border-color:var(--text-muted)}
 .card-actions--noart .search-popup-btn{font-size:.8125rem;padding:clamp(5px,0.8vw,8px) clamp(10px,2vw,16px);min-height:2.25rem}
 .search-modal-backdrop{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:860;align-items:center;justify-content:center;padding:clamp(8px,3vw,24px)}
 .search-modal-backdrop.open{display:flex}
 body.search-modal-open{overflow:hidden}
 body.search-modal-open .search-modal-backdrop.open{align-items:flex-end}
HTML
  cat <<'CHOSENPREVIEWCSS'
 body.chosen-preview-open{overflow:hidden}
 body.chosen-preview-open:not(.hl-open)::before{content:"";position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:830;pointer-events:none}
 body.chosen-preview-open.search-modal-open:not(.hl-open) .search-modal-backdrop{background:transparent;pointer-events:none;z-index:860}
 body.search-modal-open:not(.hl-open) .search-modal{pointer-events:auto;position:relative;z-index:1}
 body.chosen-preview-open:not(.hl-open) .entry:not(.selected):not(.highlight){opacity:.28;filter:saturate(.4);pointer-events:none}
 body.chosen-preview-open .entry.selected:not(.highlight){position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);z-index:840;box-sizing:border-box;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:auto;display:grid;grid-template-columns:auto minmax(0,1fr);grid-auto-rows:auto;align-content:start;align-items:start;justify-items:stretch;width:min(86vw,70rem);height:auto;min-height:min(52vh,26.25rem);max-width:min(86vw,70rem);max-height:min(88vh,53.75rem);margin:0;padding:3.5rem .875rem .75rem .625rem;box-shadow:0 18px 56px rgba(0,0,0,.5);background:var(--bg-card);background-image:none;opacity:1;filter:none;isolation:isolate}
 body.chosen-preview-open .entry.selected.hit:not(.highlight),body.chosen-preview-open .entry.selected.fav-rec:not(.highlight){background:var(--bg-card);opacity:1;filter:none}
 .entry.highlight .card-chrome-start,body.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-start{display:flex;position:absolute;top:max(var(--card-chrome-inset),env(safe-area-inset-top));left:max(var(--card-chrome-inset),env(safe-area-inset-left));gap:var(--card-chrome-gap);z-index:841;align-items:center}
 .entry.highlight .card-chrome-end,body.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-end{display:flex;position:absolute;top:max(var(--card-chrome-inset),env(safe-area-inset-top));right:max(var(--card-chrome-inset),env(safe-area-inset-right));gap:var(--card-chrome-gap);z-index:841;align-items:center}
 .entry.highlight .card-chrome-start>*,.entry.highlight .card-chrome-end>*,body.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-start>*,body.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-end>*{position:static;top:auto;left:auto;right:auto;bottom:auto;margin:0}
 body.chosen-preview-open .entry.selected:not(.highlight) .preview-back{display:flex;z-index:841}
 body.chosen-preview-open .entry.selected:not(.highlight) .fav-btn{z-index:841}
 body.chosen-preview-open .entry.selected:not(.highlight) .fs-btn{z-index:841;display:flex}
 body.chosen-preview-open .entry.selected:not(.highlight) .hl-body{display:contents}
 body.chosen-preview-open .entry.selected:not(.highlight) .cover{grid-column:1;grid-row:1;align-self:start;justify-self:start;flex:none;position:static;width:auto;height:10rem;max-height:10rem;max-width:min(38vw,22.5rem);min-height:6.875rem;margin:0 14px 0 0;overflow:hidden;display:flex;align-items:center;justify-content:flex-start}
 body.chosen-preview-open .entry.selected:not(.highlight) .cover img{width:auto;height:auto;max-width:100%;max-height:10rem;object-fit:contain;object-position:left center;transform:none}
 body.chosen-preview-open .entry.selected:not(.highlight) .lib-name{grid-column:2;grid-row:1;align-self:center;margin:0;padding-right:calc(var(--card-chrome-btn) + var(--card-chrome-gap));min-width:0;white-space:normal;overflow-wrap:break-word;word-break:normal}
 body.chosen-preview-open .entry.selected:not(.highlight) .lib-notes{display:contents}
 body.chosen-preview-open .entry.selected:not(.highlight) .note-balloon{grid-column:2;grid-row:1;align-self:center;justify-self:end;display:inline-flex;align-items:center;justify-content:center;width:2.75rem;height:2.75rem;min-width:2.75rem;min-height:2.75rem;background:var(--bg-surface);color:var(--text-muted);border:1px solid var(--border);border-radius:8px;cursor:pointer;touch-action:manipulation;font-size:1.125rem;line-height:1}
 body.chosen-preview-open .entry.selected:not(.highlight) .note-text.has-note{display:block;grid-column:1/-1;position:static;min-height:3.2em;max-height:none;overflow:visible;overflow-x:hidden;white-space:pre-wrap;overflow-wrap:break-word;word-break:normal}
 body.chosen-preview-open .entry.selected:not(.highlight) .note-pop{position:absolute;left:auto;right:calc(var(--card-chrome-inset) + var(--card-chrome-btn) + var(--card-chrome-gap));top:calc(var(--card-chrome-inset) + var(--card-chrome-btn) + var(--card-chrome-gap));z-index:845}
 body.chosen-preview-open .entry.selected:not(.highlight) .noart{grid-column:1/-1;position:static}
 body.chosen-preview-open .entry.selected:not(.highlight) .summary-panel{grid-column:1/-1;position:static;z-index:auto;float:none;flex:1 1 auto;flex-shrink:1;margin:10px 0 0;padding:clamp(8px,1.1vw,14px) clamp(10px,1.2vw,16px);min-height:calc(1.65em * 3 + 1.6em);max-height:min(14em,calc(36vh - 2.5em));overflow:hidden;overflow-x:hidden;overflow-y:hidden}
 body.chosen-preview-open .entry.selected:not(.highlight) .summary-panel .desc,body.chosen-preview-open .entry.selected:not(.highlight) .desc{position:static;z-index:auto;float:none;margin:0;max-height:100%;min-height:calc(1.65em * 3);line-height:1.65;overflow:visible;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;white-space:normal;overflow-wrap:break-word;word-break:normal;hyphens:none}
 body.chosen-preview-open .entry.selected:not(.highlight) .path{grid-column:1/-1;position:static;z-index:auto;float:none;flex:0 0 auto;flex-shrink:0;margin:10px 0 0;min-height:2.5em;max-height:none;overflow:visible;overflow-x:hidden;overflow-y:visible;white-space:normal;overflow-wrap:break-word;word-break:break-word}
 body.chosen-preview-open .entry.selected:not(.highlight) .path code{white-space:normal;overflow-wrap:break-word;word-break:break-word}
 body.chosen-preview-open .entry.selected:not(.highlight) details.patches,body.chosen-preview-open .entry.selected:not(.highlight) .patches{grid-column:1/-1;position:static;flex-shrink:0;max-height:none;overflow:visible;margin-top:8px}
 body.chosen-preview-open .entry.selected:not(.highlight) .card-actions{grid-column:1/-1;position:sticky;bottom:0;z-index:2;flex-shrink:0;margin-top:8px;background:var(--bg-card);padding-right:0;padding-top:6px;padding-bottom:4px}
 body.chosen-preview-open:not([data-focus="search"]) .entry.selected:not(.highlight){z-index:10000}
 body.search-modal-open[data-focus="search"] #searchModal{z-index:10000;isolation:isolate;transform:translate3d(0,0,0);-webkit-transform:translate3d(0,0,0)}
 body.search-modal-open[data-focus="search"] .search-modal{z-index:10001;pointer-events:auto;isolation:isolate;transform:translate3d(0,0,0);-webkit-transform:translate3d(0,0,0)}
 body.search-modal-open[data-focus="search"].chosen-preview-open .entry.selected:not(.highlight){z-index:100;-webkit-overflow-scrolling:auto}
 body.search-modal-open[data-focus="search"].chosen-preview-open .entry.selected:not(.highlight) .preview-back,
 body.search-modal-open[data-focus="search"].chosen-preview-open .entry.selected:not(.highlight) .fav-btn,
 body.search-modal-open[data-focus="search"].chosen-preview-open .entry.selected:not(.highlight) .note-balloon,
 body.search-modal-open[data-focus="search"].chosen-preview-open .entry.selected:not(.highlight) .fs-btn,
 body.search-modal-open[data-focus="search"].chosen-preview-open .entry.selected:not(.highlight) .card-actions{z-index:1}
 body.search-modal-open[data-focus="preview"] #searchModal{z-index:500;transform:none;-webkit-transform:none}
 body.search-modal-open[data-focus="preview"].chosen-preview-open .entry.selected:not(.highlight){z-index:10000;isolation:isolate}
 @media (hover:hover) and (pointer:fine){
  body.chosen-preview-open .entry.selected:not(.highlight) .cover img:hover,body.chosen-preview-open .entry.selected:not(.highlight) .cover:hover img{transform:none}
 }
 /* 16:9 landscape (incl. 640×360, 800×450, 1024×576) */
 @media (min-aspect-ratio: 16/10) and (max-aspect-ratio: 21/9){
  body.chosen-preview-open .entry.selected:not(.highlight){width:min(86vw,1120px);max-height:min(88vh,780px);height:auto}
 }
 /* 16:10 (e.g. 1280×800, 1920×1200) — later rule wins overlap with 16:9 at 16/10 */
 @media (min-aspect-ratio: 15/10) and (max-aspect-ratio: 17/10){
  body.chosen-preview-open .entry.selected:not(.highlight){width:min(86vw,1120px);max-height:min(88vh,840px);height:auto}
 }
 /* 4:3 landscape (VGA 640×480, SVGA 800×600, XGA 1024×768) */
 @media (min-aspect-ratio: 5/4) and (max-aspect-ratio: 3/2){
  body.chosen-preview-open .entry.selected:not(.highlight){width:min(84vw,980px);max-height:min(88vh,820px);height:auto}
 }
 /* Mobile/portrait/portable expanded preview: stack image → name → desc → path → patches → Search */
 body.chosen-preview-open .entry.selected:not(.highlight) .cover,
 body.chosen-preview-open .entry.selected:not(.highlight) .lib-name,
 body.chosen-preview-open .entry.selected:not(.highlight) .note-text,
 body.chosen-preview-open .entry.selected:not(.highlight) .noart,
 body.chosen-preview-open .entry.selected:not(.highlight) .summary-panel,
 body.chosen-preview-open .entry.selected:not(.highlight) .path,
 body.chosen-preview-open .entry.selected:not(.highlight) details.patches,
 body.chosen-preview-open .entry.selected:not(.highlight) .patches,
 body.chosen-preview-open .entry.selected:not(.highlight) .card-actions{position:static}
 /* 3:4 and 9:16 portrait — name under image, notes beside heart; room at bottom for Search */
 @media (orientation:portrait),(max-aspect-ratio: 1/1){
  body.chosen-preview-open .entry.selected.is-hidden:not(.highlight){display:flex!important}
  body.chosen-preview-open .entry.selected:not(.highlight){width:min(94vw,560px);max-height:min(92dvh,100%);height:auto;top:50%;display:flex;flex-direction:column;align-items:stretch;justify-content:flex-start;gap:10px;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;grid-template-columns:none}
  body.chosen-preview-open.search-modal-open .entry.selected:not(.highlight){top:42%}
  body.chosen-preview-open .entry.selected:not(.highlight) .hl-body{display:flex;flex-direction:column;align-items:stretch;gap:10px;min-width:0;overflow:visible;flex:0 0 auto}
  body.chosen-preview-open .entry.selected:not(.highlight) .cover{flex:none;align-self:center;justify-self:center;justify-content:center;display:flex;align-items:center;width:auto;height:auto;max-height:min(28vh,200px);max-width:min(86vw,360px);min-height:0;margin:0 auto;margin-inline:auto;overflow:hidden;float:none}
  body.chosen-preview-open .entry.selected:not(.highlight) .cover img{max-height:min(28vh,200px);max-width:100%;object-position:center center}
  body.chosen-preview-open .entry.selected:not(.highlight) .lib-name{align-self:stretch;width:100%;max-width:100%;margin:0;padding-inline:12px;box-sizing:border-box;text-align:center;overflow-wrap:break-word;word-break:break-word;white-space:normal;overflow:visible}
  body.chosen-preview-open .entry.selected:not(.highlight) .lib-notes{display:contents}
  body.chosen-preview-open .entry.selected:not(.highlight) .note-balloon{position:absolute;top:var(--card-chrome-inset);left:calc(var(--card-chrome-inset) + var(--card-chrome-btn) + var(--card-chrome-gap) + var(--card-chrome-btn) + var(--card-chrome-gap));right:auto;bottom:auto;z-index:841;margin:0}
  body.chosen-preview-open .entry.selected:not(.highlight) .note-text.has-note{display:block;margin:0;max-height:none;overflow:visible;flex-shrink:0}
  body.chosen-preview-open .entry.selected:not(.highlight) .note-pop{position:absolute;left:var(--card-chrome-inset);right:auto;top:calc(var(--card-chrome-inset) + var(--card-chrome-btn) + var(--card-chrome-gap))}
  body.chosen-preview-open .entry.selected:not(.highlight) .noart{margin:0;overflow:visible;flex-shrink:0}
  body.chosen-preview-open .entry.selected:not(.highlight) .summary-panel{float:none;flex:none;flex-shrink:0;margin:0;max-height:none;min-height:calc(1.65em * 3 + 1.6em);overflow:visible}
  body.chosen-preview-open .entry.selected:not(.highlight) .summary-panel .desc,body.chosen-preview-open .entry.selected:not(.highlight) .desc{float:none;margin:0;max-height:none;min-height:calc(1.65em * 3);line-height:1.65;overflow:visible;white-space:normal;overflow-wrap:break-word;word-break:normal;hyphens:none}
  body.chosen-preview-open .entry.selected:not(.highlight) .path{float:none;flex:none;flex-shrink:0;margin:0;min-height:0;max-height:none;overflow:visible;white-space:normal;overflow-wrap:break-word;word-break:break-word}
  body.chosen-preview-open .entry.selected:not(.highlight) details.patches,body.chosen-preview-open .entry.selected:not(.highlight) .patches{flex:none;flex-shrink:0;max-height:none;overflow:visible;margin:0}
  body.chosen-preview-open .entry.selected:not(.highlight) .card-actions{z-index:auto;flex:none;flex-shrink:0;margin:0;overflow:visible;padding-top:0;padding-bottom:0}
 }
 /* Phone/portable: momentum-scroll compositing can paint the fixed preview over #searchModal. */
 @media (max-width:899px),(hover:none) and (pointer:coarse){
  body.chosen-preview-open .entry.selected.is-hidden:not(.highlight){display:flex!important}
  body.chosen-preview-open .entry.selected:not(.highlight){left:0;right:0;top:4dvh;bottom:auto;transform:none;margin:0 auto;display:flex;flex-direction:column;align-items:stretch;justify-content:flex-start;gap:10px;max-height:min(92dvh,100%);height:auto;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;grid-template-columns:none}
  body.chosen-preview-open.search-modal-open .entry.selected:not(.highlight){top:8px;bottom:auto;margin:8px auto auto;max-height:min(92dvh,100%)}
  body.chosen-preview-open .entry.selected:not(.highlight) .hl-body{display:flex;flex-direction:column;align-items:stretch;gap:10px;min-width:0;overflow:visible;flex:0 0 auto}
  body.chosen-preview-open .entry.selected:not(.highlight) .cover{flex:none;align-self:center;justify-self:center;justify-content:center;display:flex;align-items:center;width:auto;height:auto;max-height:min(28vh,200px);max-width:min(86vw,360px);min-height:0;margin:0 auto;margin-inline:auto;overflow:hidden;float:none}
  body.chosen-preview-open .entry.selected:not(.highlight) .cover img{max-height:min(28vh,200px);max-width:100%;object-position:center center}
  body.chosen-preview-open .entry.selected:not(.highlight) .lib-name{align-self:stretch;width:100%;max-width:100%;margin:0;padding-inline:12px;box-sizing:border-box;text-align:center;overflow-wrap:break-word;word-break:break-word;white-space:normal;overflow:visible}
  body.chosen-preview-open .entry.selected:not(.highlight) .lib-notes{display:contents}
  body.chosen-preview-open .entry.selected:not(.highlight) .note-balloon{position:absolute;top:var(--card-chrome-inset);left:calc(var(--card-chrome-inset) + var(--card-chrome-btn) + var(--card-chrome-gap) + var(--card-chrome-btn) + var(--card-chrome-gap));right:auto;bottom:auto;z-index:841;margin:0}
  body.chosen-preview-open .entry.selected:not(.highlight) .note-text.has-note{display:block;margin:0;max-height:none;overflow:visible;flex-shrink:0}
  body.chosen-preview-open .entry.selected:not(.highlight) .note-pop{position:absolute;left:var(--card-chrome-inset);right:auto;top:calc(var(--card-chrome-inset) + var(--card-chrome-btn) + var(--card-chrome-gap))}
  body.chosen-preview-open .entry.selected:not(.highlight) .noart{margin:0;overflow:visible;flex-shrink:0}
  body.chosen-preview-open .entry.selected:not(.highlight) .summary-panel{float:none;flex:none;flex-shrink:0;margin:0;max-height:none;min-height:calc(1.65em * 3 + 1.6em);overflow:visible}
  body.chosen-preview-open .entry.selected:not(.highlight) .summary-panel .desc,body.chosen-preview-open .entry.selected:not(.highlight) .desc{float:none;margin:0;max-height:none;min-height:calc(1.65em * 3);line-height:1.65;overflow:visible;white-space:normal;overflow-wrap:break-word;word-break:normal;hyphens:none}
  body.chosen-preview-open .entry.selected:not(.highlight) .path{float:none;flex:none;flex-shrink:0;margin:0;min-height:0;max-height:none;overflow:visible;white-space:normal;overflow-wrap:break-word;word-break:break-word}
  body.chosen-preview-open .entry.selected:not(.highlight) details.patches,body.chosen-preview-open .entry.selected:not(.highlight) .patches{flex:none;flex-shrink:0;max-height:none;overflow:visible;margin:0}
  body.chosen-preview-open .entry.selected:not(.highlight) .card-actions{z-index:auto;flex:none;flex-shrink:0;margin:0;overflow:visible;padding-top:0;padding-bottom:0}
  body.chosen-preview-open:not([data-focus="search"]) .entry.selected:not(.highlight){z-index:10000}
  body.search-modal-open[data-focus="search"] #searchModal{z-index:10000;isolation:isolate;transform:translate3d(0,0,0);-webkit-transform:translate3d(0,0,0)}
  body.search-modal-open[data-focus="search"] .search-modal{z-index:10001;pointer-events:auto;isolation:isolate;transform:translate3d(0,0,0);-webkit-transform:translate3d(0,0,0)}
  body.search-modal-open[data-focus="search"].chosen-preview-open .entry.selected:not(.highlight){z-index:100;-webkit-overflow-scrolling:touch;transform:none;-webkit-transform:none}
  body.search-modal-open[data-focus="preview"] #searchModal{z-index:500;transform:none;-webkit-transform:none}
  body.search-modal-open[data-focus="preview"].chosen-preview-open .entry.selected:not(.highlight){z-index:10000;isolation:isolate}
 }
 body.chosen-preview-open.desc-reader-open .entry.selected:not(.highlight),
 body.chosen-preview-open.path-reader-open .entry.selected:not(.highlight),
 body.chosen-preview-open.desc-focus-open .entry.selected:not(.highlight),
 body.chosen-preview-open.path-focus-open .entry.selected:not(.highlight){z-index:840;pointer-events:none}
CHOSENPREVIEWCSS
  if [ "$MODE" = portable ]; then
    cat <<'PORTABLEPREVIEWCSS'
 @media (orientation:portrait){
  .catalog-body,.loc-group{--cat-cols:1fr;grid-template-columns:1fr}
  body.search-mode .catalog-body,body.search-mode .loc-group{--cat-cols:1fr;grid-template-columns:1fr}
 }
 @media (orientation:landscape){
  .catalog-body,.loc-group{--cat-cols:repeat(var(--cat-land-cols,3),minmax(0,1fr));grid-template-columns:repeat(var(--cat-land-cols,3),minmax(0,1fr))}
  body.search-mode .catalog-body,body.search-mode .loc-group{--cat-cols:repeat(var(--cat-land-cols,3),minmax(0,1fr));grid-template-columns:repeat(var(--cat-land-cols,3),minmax(0,1fr))}
 }
 body.chosen-preview-open .entry.selected.is-hidden:not(.highlight){display:flex!important}
 body.chosen-preview-open .entry.selected:not(.highlight){display:flex;flex-direction:column;align-items:stretch;justify-content:flex-start;gap:10px;max-height:min(92dvh,100%);height:auto;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;grid-template-columns:none}
 body.chosen-preview-open .entry.selected:not(.highlight) .hl-body{display:flex;flex-direction:column;align-items:stretch;gap:10px;min-width:0;overflow:visible;flex:0 0 auto}
 body.chosen-preview-open .entry.selected:not(.highlight) .cover,body.chosen-preview-open .entry.selected:not(.highlight) .lib-name,body.chosen-preview-open .entry.selected:not(.highlight) .note-text,body.chosen-preview-open .entry.selected:not(.highlight) .noart,body.chosen-preview-open .entry.selected:not(.highlight) .summary-panel,body.chosen-preview-open .entry.selected:not(.highlight) .path,body.chosen-preview-open .entry.selected:not(.highlight) details.patches,body.chosen-preview-open .entry.selected:not(.highlight) .patches,body.chosen-preview-open .entry.selected:not(.highlight) .card-actions{position:static}
 body.chosen-preview-open .entry.selected:not(.highlight) .cover{flex:none;align-self:center;justify-self:center;justify-content:center;display:flex;align-items:center;width:auto;height:auto;max-height:min(28vh,200px);max-width:min(86vw,360px);min-height:0;margin:0 auto;margin-inline:auto;overflow:hidden;float:none}
 body.chosen-preview-open .entry.selected:not(.highlight) .cover img{max-height:min(28vh,200px);max-width:100%;object-position:center center}
 body.chosen-preview-open .entry.selected:not(.highlight) .lib-name{align-self:stretch;width:100%;max-width:100%;margin:0;padding-inline:12px;box-sizing:border-box;text-align:center;overflow-wrap:break-word;word-break:break-word;white-space:normal;overflow:visible}
 body.chosen-preview-open .entry.selected:not(.highlight) .lib-notes{display:contents}
 body.chosen-preview-open .entry.selected:not(.highlight) .note-balloon{position:absolute;top:var(--card-chrome-inset);left:calc(var(--card-chrome-inset) + var(--card-chrome-btn) + var(--card-chrome-gap) + var(--card-chrome-btn) + var(--card-chrome-gap));right:auto;bottom:auto;z-index:841;margin:0}
 body.chosen-preview-open .entry.selected:not(.highlight) .note-text.has-note{display:block;margin:0;max-height:none;overflow:visible;flex-shrink:0}
 body.chosen-preview-open .entry.selected:not(.highlight) .note-pop{position:absolute;left:var(--card-chrome-inset);right:auto;top:calc(var(--card-chrome-inset) + var(--card-chrome-btn) + var(--card-chrome-gap))}
 body.chosen-preview-open .entry.selected:not(.highlight) .noart{margin:0;overflow:visible;flex-shrink:0}
 body.chosen-preview-open .entry.selected:not(.highlight) .summary-panel{float:none;flex:none;flex-shrink:0;margin:0;max-height:none;min-height:calc(1.65em * 3 + 1.6em);overflow:visible}
 body.chosen-preview-open .entry.selected:not(.highlight) .summary-panel .desc,body.chosen-preview-open .entry.selected:not(.highlight) .desc{float:none;margin:0;max-height:none;min-height:calc(1.65em * 3);line-height:1.65;overflow:visible;white-space:normal;overflow-wrap:break-word;word-break:normal;hyphens:none}
 body.chosen-preview-open .entry.selected:not(.highlight) .path{float:none;flex:none;flex-shrink:0;margin:0;min-height:0;max-height:none;overflow:visible;white-space:normal;overflow-wrap:break-word;word-break:break-word}
 body.chosen-preview-open .entry.selected:not(.highlight) details.patches,body.chosen-preview-open .entry.selected:not(.highlight) .patches{flex:none;flex-shrink:0;max-height:none;overflow:visible;margin:0}
 body.chosen-preview-open .entry.selected:not(.highlight) .card-actions{z-index:auto;flex:none;flex-shrink:0;margin:0;overflow:visible;padding-top:0;padding-bottom:0}
PORTABLEPREVIEWCSS
  fi
  cat <<'HTML'
 .search-modal{background:var(--bg-surface);border:1px solid var(--border);border-radius:10px;padding:clamp(16px,3vw,28px);max-width:min(640px,92vw);width:100%;position:relative;box-shadow:0 8px 32px rgba(0,0,0,0.5)}
 .search-modal-close{position:absolute;top:clamp(8px,1.5vw,12px);right:clamp(8px,1.5vw,12px);background:none;border:none;color:var(--text-muted);font-size:1.125rem;cursor:pointer;line-height:1;padding:4px 6px;border-radius:4px;touch-action:manipulation;min-width:2rem;min-height:2rem}
 .search-modal-close:hover{color:var(--text);background:var(--bg-card)}
 .search-modal-title{font-size:1.0625rem;font-weight:600;color:var(--text);padding-right:32px;margin-bottom:6px;word-break:break-word}
 .search-modal-subtitle{font-size:.8125rem;color:var(--text-muted);margin-bottom:clamp(12px,2vw,18px)}
 .search-modal-btns{display:flex;gap:clamp(10px,2.2vw,20px);flex-wrap:wrap}
 .search-modal-link{flex:1 1 auto;min-width:6.875rem;display:flex;align-items:center;justify-content:center;gap:6px;padding:clamp(10px,1.8vw,16px) clamp(12px,2.5vw,20px);border-radius:7px;font-size:.9375rem;font-weight:500;text-decoration:none;border:1px solid var(--border);color:var(--text);background:var(--bg-card);cursor:pointer;touch-action:manipulation;min-height:3rem;transition:background 0.15s,border-color 0.15s,color 0.15s}
 .search-modal-link.yt:hover{background:rgba(255,64,64,0.12);border-color:#ff4040;color:#ff5555}
 .search-modal-link.web:hover{background:var(--accent-instrument-bg);border-color:var(--accent-instrument);color:var(--accent-instrument)}
 .search-modal-link.img:hover{background:var(--accent-gear-bg);border-color:var(--accent-gear);color:var(--accent-gear)}
 .search-modal-hint{font-size:.75rem;color:var(--text-muted);text-align:center;margin-top:clamp(8px,1.2vw,12px);opacity:0.7}
 .card-search-embed{display:none;grid-column:1/-1;flex:1 1 auto;min-height:0;flex-direction:column;background:var(--bg);color:var(--text);border:1px solid var(--border);border-radius:8px;overflow:hidden;isolation:isolate}
 body.card-embed-open .card-search-embed{display:flex}
 body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight){display:flex;flex-direction:column;align-items:stretch;height:min(88vh,860px);max-height:min(88vh,860px);overflow:hidden}
 body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .cover,
 body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .lib-name,
 body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .lib-notes,
 body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .note-text,
 body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .noart,
 body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .summary-panel,
 body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .path,
 body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) details.patches,
 body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .patches,
 body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .card-actions,
 body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .hl-body{display:none!important}
 body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .card-search-embed{display:flex;flex:1 1 auto;min-height:0;margin-top:8px}
 .card-search-chrome{display:flex;align-items:center;gap:var(--card-chrome-gap);flex-shrink:0;padding:.5rem .625rem;background:var(--bg-surface);border-bottom:1px solid var(--border);color:var(--text)}
 .card-search-chrome button{box-sizing:border-box;min-width:2.75rem;min-height:2.75rem;padding:0 12px;border:1px solid var(--border);border-radius:8px;background:var(--bg-card);color:var(--text);font:inherit;cursor:pointer;touch-action:manipulation}
 .card-search-chrome button:hover{border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 .card-search-chrome button:disabled{opacity:.35;pointer-events:none}
 .card-search-hint{position:absolute;z-index:6;left:50%;top:.5rem;transform:translateX(-50%) translateY(-6px);max-width:min(26rem,calc(100% - 1.5rem));box-sizing:border-box;padding:.625rem .75rem .625rem .875rem;border:1px solid var(--border);border-radius:10px;background:var(--bg-surface);color:var(--text);box-shadow:0 10px 28px rgba(0,0,0,.38);display:none;align-items:center;gap:.5rem;opacity:0;pointer-events:none;transition:opacity .2s,transform .2s}
 .card-search-hint.is-on{display:flex;opacity:1;pointer-events:auto;transform:translateX(-50%) translateY(0)}
 .card-search-hint-text{margin:0;flex:1 1 auto;min-width:0;font-size:.8125rem;line-height:1.35;color:var(--text)}
 .card-search-hint-text strong{color:var(--accent-instrument);font-weight:700}
 .card-search-hint-x{flex:0 0 auto;box-sizing:border-box;width:2rem;height:2rem;min-width:2rem;min-height:2rem;padding:0;border:1px solid var(--border);border-radius:8px;background:var(--bg-card);color:var(--text-muted);font:inherit;font-size:1.05rem;line-height:1;cursor:pointer;touch-action:manipulation}
 .card-search-hint-x:hover{border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 .card-search-title{flex:1 1 auto;min-width:0;font-size:.9375rem;color:var(--text-muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
 .card-search-stage{position:relative;flex:1 1 auto;min-height:min(42vh,320px);background:var(--bg);display:flex;flex-direction:column;min-height:0}
 .card-search-frame{display:block;width:100%;height:100%;border:0;background:var(--bg);pointer-events:auto;flex:1 1 auto;min-height:0}
 .card-search-frame.is-hidden{display:none!important}
 .card-yt-comments{display:none;flex:1 1 auto;min-height:0;width:100%;border:0;border-top:1px solid var(--border);background:var(--bg-card);pointer-events:auto}
 .card-yt-comments-strip{display:flex;flex:1 1 auto;align-items:stretch;justify-content:flex-start;flex-direction:column;gap:0;padding:0;text-align:left;background:var(--bg-card);color:var(--text);min-height:0;overflow:auto;-webkit-overflow-scrolling:touch}
 .card-yt-comments-strip p{margin:0;padding:12px 14px;color:var(--text-muted)}
 .card-yt-comments-strip button{min-height:2.75rem;padding:0 16px;border:1px solid var(--accent-instrument);border-radius:8px;background:var(--accent-instrument-bg);color:var(--accent-instrument);font:inherit;cursor:pointer;touch-action:manipulation}
 .card-yt-list{display:flex;flex-direction:column;gap:8px;min-height:0;padding:8px;box-sizing:border-box}
 .card-yt-row{display:flex;align-items:flex-start;gap:10px;width:100%;box-sizing:border-box;margin:0;padding:10px;border:1px solid var(--border);border-radius:8px;background:var(--bg);color:var(--text);font:inherit;cursor:pointer;text-align:left;touch-action:manipulation;min-height:0;overflow:hidden;flex:0 0 auto}
 .card-yt-row.is-active{background:var(--accent-instrument-bg);border-color:var(--accent-instrument)}
 .card-yt-row img{width:4.5rem;height:2.5rem;object-fit:cover;border-radius:4px;flex:0 0 auto;background:var(--bg-surface);margin-top:1px}
 .card-yt-row-title{flex:1 1 auto;min-width:0;max-width:100%;font-size:.92em;line-height:1.35;color:var(--text);overflow-wrap:anywhere;word-break:break-word;white-space:normal;display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:4;overflow:hidden;hyphens:auto}
 .card-search-stage.yt-split .card-search-frame{flex:0 0 auto;height:min(42vh,48%);min-height:180px;max-height:52%;position:relative;inset:auto}
 .card-search-stage.yt-split .card-yt-comments{display:flex;flex:1 1 auto;min-height:0;flex-direction:column}
 .card-search-stage.yt-wide{flex-direction:row;align-items:stretch}
 .card-search-stage.yt-wide .card-search-frame{position:relative;inset:auto;flex:1 1 55%;width:auto;height:100%;max-height:none;min-height:0}
 .card-search-stage.yt-wide .card-yt-comments{display:flex;flex:1 1 45%;min-width:14rem;max-width:min(22rem,46%);border-top:0;border-left:1px solid var(--border)}
 .card-search-stage.yt-wide .card-yt-row-title{-webkit-line-clamp:5}
 .card-search-reader{display:none;flex:1 1 auto;min-height:0;overflow:auto;-webkit-overflow-scrolling:touch;background:var(--bg);color:var(--text)}
 .card-search-reader.open{display:flex;flex-direction:column}
 .card-search-status{display:flex;flex:1 1 auto;align-items:center;justify-content:center;flex-direction:column;gap:12px;padding:24px;text-align:center;color:var(--text-muted)}
 .card-search-status p{margin:0;max-width:40ch}
 .card-search-status button,.card-search-article button{min-height:2.75rem;padding:0 16px;border:1px solid var(--accent-instrument);border-radius:8px;background:var(--accent-instrument-bg);color:var(--accent-instrument);font:inherit;cursor:pointer;touch-action:manipulation}
 .card-search-results{display:flex;flex-direction:column;margin:0;padding:0}
 .card-search-row{display:block;width:100%;box-sizing:border-box;text-align:left;padding:12px 14px;border:0;border-bottom:1px solid var(--border);background:transparent;color:var(--text);font:inherit;cursor:pointer;touch-action:manipulation}
 .card-search-row:hover,.card-search-row:focus-visible{background:var(--bg-card);outline:none}
 .card-search-row-title{display:block;font-weight:600;color:var(--accent-instrument);word-break:break-word}
 .card-search-row-snip{display:block;margin-top:4px;font-size:.92em;color:var(--text-muted);word-break:break-word}
 .card-search-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(7.375rem,1fr));gap:8px;padding:10px}
 .card-search-tile{aspect-ratio:1;margin:0;padding:0;border:1px solid var(--border);border-radius:8px;overflow:hidden;background:var(--bg-card);cursor:pointer;touch-action:manipulation}
 .card-search-tile img{display:block;width:100%;height:100%;object-fit:cover}
 .card-search-article{padding:16px;display:flex;flex-direction:column;gap:12px}
 .card-search-article h3{margin:0;font-size:1.125rem;color:var(--text)}
 .card-search-article p{margin:0;color:var(--text-muted);line-height:1.45}
 .card-img-exit{display:none;position:absolute;right:10px;bottom:10px;z-index:4;box-sizing:border-box;min-width:2.75rem;min-height:2.75rem;padding:0 14px;border:1px solid var(--border);border-radius:8px;background:var(--bg-surface);color:var(--text);font:inherit;cursor:pointer;touch-action:manipulation;box-shadow:0 4px 16px rgba(0,0,0,.35)}
 .card-search-img-view.open ~ .card-img-exit{display:flex;align-items:center;justify-content:center}
 .card-img-exit:hover{border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 .card-search-img-view{display:none;position:absolute;inset:0;z-index:3;align-items:center;justify-content:center;background:var(--bg)}
 .card-search-img-view.open{display:flex}
 .card-search-img-view img{max-width:100%;max-height:100%;object-fit:contain;cursor:pointer}
 .card-search-fallback{display:none;position:absolute;inset:0;align-items:center;justify-content:center;flex-direction:column;gap:12px;padding:24px;text-align:center;background:var(--bg-card);color:var(--text)}
 .card-search-fallback.open{display:flex}
 .card-search-fallback p{margin:0;max-width:36ch;color:var(--text-muted)}
 .card-search-fallback button{min-height:2.75rem;padding:0 16px;border:1px solid var(--accent-instrument);border-radius:8px;background:var(--accent-instrument-bg);color:var(--accent-instrument);font:inherit;cursor:pointer;touch-action:manipulation}

 .card-google-cse{flex:1 1 auto;min-height:0;width:100%;overflow:auto;-webkit-overflow-scrolling:touch;padding:8px 10px;box-sizing:border-box;background:var(--bg)}
 .card-google-cse .gsc-control-cse{background:transparent!important;border:0!important;padding:0!important}
 .card-google-frame{display:block;width:100%;height:100%;border:0;background:#fff;flex:1 1 auto;min-height:0}
 .card-search-stage:has(> .card-google-frame:not(.is-hidden)){padding:0;gap:0}
 .card-search-stage > .card-google-frame{margin:0}
 .card-google-fallback{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;padding:24px;text-align:center;min-height:12rem}
 .card-google-fallback p{margin:0;max-width:40ch;color:var(--text-muted)}
 .card-google-fallback button{min-height:2.75rem;padding:0 16px;border:1px solid var(--accent-instrument);border-radius:8px;background:var(--accent-instrument-bg);color:var(--accent-instrument);font:inherit;cursor:pointer;touch-action:manipulation}
 .card-yt-blocked{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:0;max-width:min(36rem,96%);width:100%;padding:8px;box-sizing:border-box}
 .card-yt-blocked-thumb{position:relative;display:block;padding:0;border:1px solid var(--border);border-radius:10px;overflow:hidden;background:var(--bg);cursor:pointer;touch-action:manipulation;max-width:100%;width:min(36rem,92vw)}
 .card-yt-blocked-thumb img{display:block;width:100%;max-width:100%;height:auto;aspect-ratio:16/9;object-fit:cover}
 .card-yt-blocked-play{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,.3);pointer-events:none;transition:background .15s}
 .card-yt-blocked-thumb:hover .card-yt-blocked-play,.card-yt-blocked-thumb:focus-visible .card-yt-blocked-play{background:rgba(0,0,0,.42)}
 .card-yt-blocked-play svg{width:clamp(3.25rem,14vw,4.75rem);height:clamp(3.25rem,14vw,4.75rem);color:#fff;filter:drop-shadow(0 4px 14px rgba(0,0,0,.5))}
 .card-yt-blocked-bare{display:inline-flex;align-items:center;justify-content:center;min-width:min(22rem,86vw);min-height:min(12rem,28vh);padding:0;border:1px solid var(--border);border-radius:10px;background:var(--bg-card);color:var(--text);cursor:pointer;touch-action:manipulation}
 .card-yt-blocked-bare svg{width:clamp(3.25rem,14vw,4.75rem);height:clamp(3.25rem,14vw,4.75rem);color:var(--accent-instrument)}
 .card-yt-blocked-img{display:block;width:100%;max-width:min(36rem,92vw);height:auto;aspect-ratio:16/9;object-fit:cover;border-radius:8px;margin-bottom:4px}
 .card-yt-blocked-msg{margin:4px 0 6px;font-size:.875rem;color:var(--text-muted);text-align:center;max-width:30ch}
 .card-yt-blocked-retry{display:inline-flex;align-items:center;gap:.3em;margin-top:2px;padding:0 12px;min-height:2.25rem;border:1px solid var(--accent-instrument);border-radius:8px;background:var(--accent-instrument-bg);color:var(--accent-instrument);font:inherit;font-size:.875rem;cursor:pointer;touch-action:manipulation}
 .card-yt-blocked-retry:hover{background:var(--accent-instrument);color:var(--bg)}
 .card-yt-list-toggle{flex:0 0 auto;display:flex;align-items:center;justify-content:center;padding:4px 8px;border:0;border-bottom:1px solid var(--border);background:var(--bg-surface);color:var(--text-muted);font:inherit;font-size:.875rem;cursor:pointer;touch-action:manipulation;min-height:2rem;width:100%}
 .card-yt-list-toggle:hover{color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 .card-search-stage.yt-list-collapsed.yt-wide .card-yt-comments{min-width:2rem;flex:0 0 2rem;overflow:hidden}
 .card-search-stage.yt-list-collapsed.yt-wide .card-yt-comments-strip{display:none!important}
 .card-search-stage.yt-list-collapsed.yt-wide .card-yt-list-toggle{height:100%;border-bottom:0;border-right:1px solid var(--border);writing-mode:vertical-rl}
 .card-search-stage.yt-list-collapsed.yt-split .card-yt-comments-strip{display:none!important}
 /* Bug2-fix: constrain blocked-state fallback to the frame area so #cardYtComments stays visible */
 .card-search-stage.yt-split .card-search-fallback{bottom:auto;height:min(42vh,48%);min-height:180px;max-height:52%;}
 .card-search-stage.yt-wide .card-search-fallback{right:auto;width:55%;}
 .card-search-switch{display:none;position:absolute;left:10px;right:10px;bottom:max(10px,4%);z-index:5;align-items:center;justify-content:space-evenly;gap:8px;height:clamp(3.25rem,9vh,4.25rem);max-height:33%;padding:6px 14px;border:1px solid var(--border);border-radius:14px;background:color-mix(in srgb,var(--bg-surface) 88%,transparent);box-shadow:0 10px 28px rgba(0,0,0,.32);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px)}
 body.card-embed-open .card-search-switch{display:flex}
 .card-search-switch-btn{flex:1 1 0;max-width:5.75rem;min-width:2.75rem;min-height:2.75rem;display:flex;align-items:center;justify-content:center;margin:0;padding:0;border:1px solid transparent;border-radius:10px;background:transparent;color:var(--text-muted);cursor:pointer;touch-action:manipulation}
 .card-search-switch-btn svg{width:1.375rem;height:1.375rem;display:block}
 .card-search-switch-btn:hover{color:var(--text);background:var(--bg-card)}
 .card-search-switch-btn.is-active{color:var(--accent-instrument);background:var(--accent-instrument-bg);border-color:var(--accent-instrument)}
 body.card-embed-open.card-switch-bar-hidden .card-search-switch{display:none!important}
 body.card-embed-open .card-search-reader.open{padding-bottom:84px}
 body.card-embed-open.card-switch-bar-hidden .card-search-reader.open{padding-bottom:12px}
 body.card-embed-open .card-img-exit{bottom:calc(12px + clamp(52px,9vh,68px));z-index:6}
 body.card-embed-open.card-switch-bar-hidden .card-img-exit{bottom:12px}
 .card-search-switch-toggle{flex:0 0 auto;min-width:2.75rem;padding:0;display:inline-flex;align-items:center;justify-content:center}
 .card-search-switch-toggle svg{width:1.25rem;height:1.25rem;display:block}
 .card-search-switch-toggle[aria-pressed="false"]{color:var(--text-muted)}
 .card-search-switch-toggle[aria-pressed="true"]{color:var(--accent-instrument);border-color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 .card-search-popup{flex:0 0 auto;white-space:nowrap}
 .card-search-fs{flex:0 0 auto;padding:0;min-width:2.75rem;min-height:2.75rem;display:inline-flex;align-items:center;justify-content:center;font-size:1.125rem}
 .card-search-fs[aria-pressed="true"]{color:var(--accent-instrument);border-color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 @media (min-width:900px) and (orientation:landscape){.search-modal{max-width:min(92vw,720px)}}
 @media (min-width:600px) and (orientation:portrait){.search-modal{max-width:min(92vw,640px)}}
 @media (max-width:899px) and (orientation:landscape){.search-modal{max-width:min(92vw,720px)}.search-modal-backdrop{align-items:center;justify-content:center;padding:clamp(8px,3vw,24px)}}
 @media (max-width:599px) and (orientation:portrait){.search-modal{border-radius:12px 12px 0 0;margin-top:auto;margin-bottom:0;max-width:100%}.search-modal-backdrop{align-items:flex-end;padding:0}}
 @media(max-width:320px){.card-actions{flex-direction:column}}
 .search-chrome{width:100%;max-width:100%;box-sizing:border-box}
 .search-col{display:none;position:relative;min-width:0;max-width:100%;width:100%}
 .search-strip-anchor{position:relative;min-width:0;width:100%;max-width:100%}
 body.search-mode .search-chrome{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);grid-template-rows:none;gap:8px;align-items:start;justify-content:stretch;position:sticky;top:0;z-index:200;background:var(--bg-surface);padding-top:max(.5rem,env(safe-area-inset-top,0px));padding-left:max(.75rem,calc(env(safe-area-inset-left,0px) + .5rem));padding-right:max(1rem,calc(env(safe-area-inset-right,0px) + .75rem));padding-bottom:10px;width:100%;max-width:100%;min-width:0;box-sizing:border-box;overflow-x:clip}
 body.search-mode:not(.kw-open) .search-chrome{position:sticky;top:0;z-index:200}
 body.search-mode .search-col{display:flex;flex-direction:column;min-width:0;max-width:100%;justify-self:start;overflow:hidden}
 body.search-mode .filter-wrap{position:relative;top:auto;z-index:auto;width:100%;max-width:100%;min-width:0;padding-left:0;padding-right:0;justify-self:end;overflow:hidden}
 /* Search always left, Keywords always right — never stacked mid-screen.
    Fallback columns only; JS applySplit applies saved edge sizes and must win. */
 body.search-mode.kw-open:not(.search-chrome-collapsed) .search-chrome{grid-template-columns:minmax(0,1fr) .625rem minmax(0,1fr)}
 body.search-mode:not(.kw-open):not(.search-chrome-collapsed) .search-chrome{grid-template-columns:minmax(0,1fr) 0 minmax(0,max-content)}
 body.search-mode.kw-open.search-chrome-collapsed .search-chrome{grid-template-columns:minmax(0,max-content) 0 minmax(0,1fr)}
 body.search-mode .search-col,body.search-mode .filter-wrap{width:auto;max-width:100%;min-width:0}
 body.search-mode.menus-collapsed .search-chrome{grid-template-columns:minmax(0,max-content) minmax(0,1fr) minmax(0,max-content);justify-content:stretch;align-items:start;gap:0}
 body.search-mode.menus-collapsed .search-col{width:auto;max-width:100%;min-width:0;flex:0 1 auto;justify-self:start}
 body.search-mode.menus-collapsed .filter-wrap{width:auto;max-width:100%;min-width:0;flex:0 1 auto;justify-self:end}
 body.search-mode.kw-open:not(.search-chrome-collapsed) .search-strip input{flex:1 1 8rem;min-width:0}
 /* Collapsed toolbar: borderless Search (left) / Keywords (right). */
 body.search-mode.search-chrome-collapsed .search-strip{border:none;background:transparent;padding:0;min-width:0;width:auto}
 body.search-mode.search-chrome-collapsed .search-strip-hide{border:none;background:transparent;box-shadow:none;border-radius:0;padding:.5rem .25rem;color:var(--text-muted);font-weight:600}
 body.search-mode.search-chrome-collapsed .search-strip-hide:hover{color:var(--accent-instrument);border:none;background:transparent}
 body.search-mode .filter-wrap:not(.open) .filter-toggle{border:none;background:transparent;box-shadow:none;width:auto;max-width:100%;min-width:0;flex:0 1 auto;padding:.5rem max(.5rem,env(safe-area-inset-right,0px)) .5rem .35rem;margin-right:0;color:var(--text-muted);font-weight:600;justify-content:flex-end;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;box-sizing:border-box}
 body.search-mode .filter-wrap:not(.open) .filter-toggle .toggle-arrow{display:none}
 body.search-mode .filter-wrap:not(.open) .filter-top{justify-content:flex-end;border:none;padding:0;min-width:0;max-width:100%;overflow:visible}
 body.search-mode .filter-wrap:not(.open){width:auto;max-width:calc(100% - .25rem);min-width:0;justify-self:end;flex:0 1 auto;overflow:hidden;padding-right:max(.25rem,env(safe-area-inset-right,0px));box-sizing:border-box}
 body.search-mode .filter-wrap:not(.open) .filter-panel{display:none!important}

 body.search-mode .search-chrome>.search-col,body.search-mode .search-chrome>.filter-wrap{position:relative;z-index:auto}
 /* Fullscreen Search: Back arrow top-left. */
 .ac-fs-back{box-sizing:border-box;flex:0 0 auto;min-width:2.75rem;min-height:2.75rem;margin:0;padding:0;border:1px solid var(--border);border-radius:8px;background:var(--bg-card);color:var(--text);font:inherit;font-size:1.375rem;line-height:1;cursor:pointer;touch-action:manipulation;display:none;align-items:center;justify-content:center}
 body.ac-fs-open .ac-fs-back{display:inline-flex}
 .ac-fs-back:hover{border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 .search-ac-shell.ac-fs .ac-fs-bar{display:flex;align-items:center;gap:.5rem;flex-wrap:nowrap;width:100%;max-width:100%;min-width:0;box-sizing:border-box;overflow:visible}
 body.ac-fs-open .search-strip-fs{display:inline-flex!important}
 .search-split{display:none;box-sizing:border-box;position:relative;z-index:3;margin:0;padding:0;border:0;background:transparent;touch-action:none;-webkit-user-select:none;user-select:none;-webkit-tap-highlight-color:transparent}
 body.search-mode .search-chrome.search-split-lr>.search-split{display:block;width:.625rem;min-width:.625rem;max-width:.625rem;align-self:stretch;cursor:col-resize}
 body.search-mode .search-chrome.search-split-lr>.search-split[aria-hidden="true"]{display:block;width:0;min-width:0;max-width:0;margin:0;padding:0;border:0;overflow:hidden;visibility:hidden;pointer-events:none}
 body.search-mode .search-chrome.search-split-ud>.search-split{display:block;width:100%;height:.625rem;min-height:.625rem;max-height:.625rem;cursor:row-resize}
 .search-split::before{content:"";position:absolute;background:var(--border);border-radius:2px;pointer-events:none}
 body.search-mode .search-chrome.search-split-lr>.search-split::before{top:18%;bottom:18%;left:3px;width:4px}
 body.search-mode .search-chrome.search-split-ud>.search-split::before{left:28%;right:28%;top:3px;height:4px}
 .search-split:hover::before,.search-split:focus-visible::before,body.search-mode .search-chrome.search-split-dragging>.search-split::before{background:var(--accent-instrument)}
 body.search-mode .search-chrome.search-split-lr{gap:0;align-items:stretch}
 body.search-mode .search-chrome.search-split-ud{gap:0}
 body.search-mode .search-chrome.search-split-lr .search-col,body.search-mode .search-chrome.search-split-lr .filter-wrap{min-width:0;max-width:100%}
 body.search-mode .search-chrome.search-split-lr .search-strip input{min-width:0;flex:1 1 8rem}
 body.search-mode .search-chrome.search-split-lr .filter-wrap:not(.open) .filter-top{flex-wrap:nowrap;overflow:hidden;min-width:0}
 body.search-mode .search-chrome.search-split-lr .filter-wrap:not(.open) .layout-presets{flex-wrap:nowrap;overflow:visible;min-width:0}
 body.search-mode .search-chrome.search-split-lr .filter-wrap:not(.open){min-width:0}
 body.search-mode .search-chrome.search-split-ud .search-col,body.search-mode .search-chrome.search-split-ud .filter-wrap{min-height:0;max-height:100%}
 body.search-mode .search-chrome.search-split-ud .filter-wrap{overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch}
 body.search-mode .search-chrome.search-split-ud .filter-wrap.open .filter-panel{max-height:none}
 .search-chrome.search-split-dragging{-webkit-user-select:none;user-select:none}
 .search-height{display:none;box-sizing:border-box;position:absolute;z-index:4;left:0;right:0;bottom:0;width:100%;height:.625rem;min-height:.625rem;max-height:.625rem;margin:0;padding:0;border:0;background:transparent;cursor:row-resize;touch-action:none;-webkit-user-select:none;user-select:none;-webkit-tap-highlight-color:transparent}
 body.search-mode .search-chrome>.search-height{display:block}
 body.search-mode:not(.kw-open) .search-chrome>.search-height{display:none}
 .search-height::before{content:"";position:absolute;left:28%;right:28%;top:3px;height:4px;background:var(--border);border-radius:2px;pointer-events:none}
 .search-height:hover::before,.search-height:focus-visible::before,body.search-mode .search-chrome.search-height-dragging>.search-height::before{background:var(--accent-instrument)}
 .search-chrome.search-height-dragging{-webkit-user-select:none;user-select:none}
 body.search-mode .search-chrome.search-height-set{overflow-x:clip;overflow-y:visible;align-items:stretch}
 body.search-mode .search-chrome.search-height-set .search-col,body.search-mode .search-chrome.search-height-set .filter-wrap{min-height:0;max-height:100%}
 body.search-mode .search-col,body.search-mode .search-strip-anchor{overflow:visible}
 body.search-mode .search-chrome.search-height-set .filter-wrap{overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch}
 body.search-mode .search-chrome.search-height-set .filter-wrap.open .filter-panel{max-height:none}
 body.search-mode:not(.layout-edit) .search-split,body.search-mode:not(.layout-edit) .search-height{pointer-events:none;cursor:default}
 body.search-mode:not(.layout-edit) .search-split::before,body.search-mode:not(.layout-edit) .search-height::before{opacity:0}
 .search-split::after,.search-height::after,.ac-height::after,.ac-width::after,.kw-shade-height::after{content:"";position:absolute;pointer-events:none}
 body.layout-edit .search-split::after,body.layout-edit .search-height::after,body.layout-edit .ac-height::after,body.layout-edit .ac-width::after,body.layout-edit .kw-shade-height::after{pointer-events:auto}
 body.search-mode .search-chrome.search-split-lr>.search-split::after{top:0;bottom:0;left:-17px;right:-17px}
 body.search-mode .search-chrome.search-split-ud>.search-split::after{left:0;right:0;top:-17px;bottom:-17px}
 .search-height::after,.ac-height::after,.kw-shade-height::after{left:0;right:0;top:-17px;bottom:-17px}
 .ac-width::after{top:0;bottom:0;left:-17px;right:-17px}
 body.layout-edit.search-mode .search-chrome.search-height-set{overflow-x:clip;overflow-y:visible}
 body.layout-edit.search-mode .search-chrome.search-height-set .search-col{min-height:0;overflow:visible}
 body.layout-edit.search-mode .search-chrome.search-height-set .filter-wrap{min-height:0;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch}
 .search-ac-shell{position:absolute;top:100%;left:0;right:0;z-index:260;display:none;width:100%;max-width:100%;box-sizing:border-box;pointer-events:auto}
 .search-ac-shell:has(.search-autocomplete.open),.search-ac-shell.open{display:block}
 .search-ac-shell.ac-fixed{position:fixed;right:auto;z-index:260;max-width:none;overflow:visible;box-shadow:0 10px 28px rgba(0,0,0,.28)}
 /* History clear: cloud popover inside Search dropdown chrome. */
 .ac-history-wrap{position:relative;flex:0 0 auto;margin-left:auto;z-index:5;min-width:0}
 .ac-history-btn{box-sizing:border-box;flex:0 0 auto;min-height:2.25rem;min-width:2.25rem;height:2.25rem;padding:0 .5rem;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text-muted);font:inherit;font-size:.875rem;font-weight:600;font-style:normal;letter-spacing:0;cursor:pointer;touch-action:manipulation;white-space:nowrap;display:inline-flex;align-items:center;justify-content:center;line-height:1}
 .ac-history-btn:hover,.ac-history-btn[aria-expanded="true"]{border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg);font-weight:600}
 .ac-history-cloud{position:fixed;z-index:420;box-sizing:border-box;min-width:11rem;max-width:min(20rem,calc(100vw - 1.5rem - env(safe-area-inset-left,0px) - env(safe-area-inset-right,0px)));padding:.75rem .875rem .625rem;border:1px solid var(--border);border-radius:1.35rem;background:var(--bg-card);color:var(--text);box-shadow:0 12px 32px rgba(0,0,0,.38);display:flex;flex-direction:column;gap:.55rem}
 .ac-history-cloud[hidden]{display:none!important}
 .ac-history-cloud::after{content:"";position:absolute;width:.7rem;height:.7rem;background:var(--bg-card);transform:rotate(45deg);pointer-events:none}
 .ac-history-cloud.cloud-below::after{top:-.38rem;left:var(--cloud-tail-x,.75rem);border-left:1px solid var(--border);border-top:1px solid var(--border);border-right:0;border-bottom:0}
 .ac-history-cloud.cloud-above::after{bottom:-.38rem;left:var(--cloud-tail-x,.75rem);border-right:1px solid var(--border);border-bottom:1px solid var(--border);border-left:0;border-top:0}
 .ac-history-ask{margin:0;font-size:.875rem;line-height:1.35;color:var(--text);max-width:100%}
 .ac-history-picks{display:flex;flex-direction:column;gap:.28rem;max-width:100%}
 .ac-history-picks label{display:flex;align-items:center;gap:.45rem;margin:0;font-size:.8125rem;line-height:1.3;color:var(--text);cursor:pointer;min-height:1.75rem}
 .ac-history-picks input{flex:0 0 auto;margin:0;accent-color:var(--accent-instrument)}
 .ac-history-picks .ac-hist-count{margin-left:auto;color:var(--text-muted);font-variant-numeric:tabular-nums}
 .ac-history-search,.ac-history-all{box-sizing:border-box;min-height:2.75rem;padding:0 .7rem;border:1px solid var(--border);border-radius:999px;background:var(--bg-surface);color:var(--text);font:inherit;font-size:.8125rem;cursor:pointer;touch-action:manipulation}
 .ac-history-all{margin-right:auto}
 .ac-history-search:hover,.ac-history-all:hover{border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 .ac-history-actions{display:flex;align-items:center;justify-content:flex-end;gap:.45rem}
 .ac-history-yes,.ac-history-no{box-sizing:border-box;min-width:2.75rem;min-height:2.75rem;padding:0;border:1px solid var(--border);border-radius:999px;background:var(--bg-surface);color:var(--text);font:inherit;font-size:1.125rem;line-height:1;cursor:pointer;touch-action:manipulation;display:inline-flex;align-items:center;justify-content:center}
 .ac-history-yes{color:var(--accent-instrument);border-color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 .ac-history-yes:hover{background:var(--accent-instrument);color:var(--bg-card)}
 .ac-history-no:hover{border-color:#c03040;color:#ff9090;background:rgba(180,40,40,0.18)}
 .search-ac-shell.open .ac-fs-bar,.search-ac-shell:has(.search-autocomplete.open) .ac-fs-bar,.search-ac-shell.ac-fs .ac-fs-bar{display:flex;align-items:center;gap:.5rem;flex-wrap:wrap;width:100%;max-width:100%;min-width:0;box-sizing:border-box;overflow:visible}
 .search-ac-shell:not(.ac-fs) .ac-fs-bar{padding:.375rem .5rem;padding-left:max(.5rem,env(safe-area-inset-left,0px));padding-right:max(.5rem,env(safe-area-inset-right,0px));border-bottom:1px solid var(--border)}
 .ac-fs-bar{display:none;flex:0 0 auto;align-items:center;gap:.5rem;padding:.5rem .75rem;padding-top:max(.5rem,env(safe-area-inset-top,0px));padding-right:max(.75rem,env(safe-area-inset-right,0px));padding-bottom:.5rem;padding-left:max(.75rem,env(safe-area-inset-left,0px));border-bottom:1px solid var(--border);background:var(--bg-surface);z-index:2;box-sizing:border-box;width:100%;max-width:100%;min-width:0;overflow:visible}
 .search-ac-shell.ac-fs{position:fixed;z-index:280;display:flex!important;flex-direction:column;background:var(--bg-surface);overflow:hidden;box-shadow:none;max-width:none;touch-action:manipulation;-webkit-overflow-scrolling:auto}
 .search-ac-shell.ac-fs .ac-fs-bar{display:flex;flex:0 0 auto}
 .ac-fs-close{box-sizing:border-box;min-height:2.75rem;padding:0 1rem;border:1px solid var(--border);border-radius:8px;background:var(--bg-card);color:var(--text);font:inherit;font-size:1rem;cursor:pointer;touch-action:manipulation;white-space:nowrap}
 .ac-fs-close:hover{border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 .search-ac-shell.ac-fs .search-autocomplete,.search-ac-shell.ac-fs .search-autocomplete.open{position:relative!important;inset:auto!important;flex:1 1 0!important;min-height:0!important;max-height:none!important;height:auto!important;overflow-x:hidden!important;overflow-y:scroll!important;-webkit-overflow-scrolling:touch;touch-action:pan-y!important;overscroll-behavior-y:auto;overscroll-behavior-x:none;border:0;width:100%;font-size:1em;pointer-events:auto}
 .search-ac-shell.ac-fs .ac-item,.search-ac-shell.ac-fs .ac-group-label{touch-action:pan-y}
 body.ac-fs-open{overflow:hidden;overscroll-behavior:none}
 body.ac-fs-open .search-ac-shell.ac-fs{pointer-events:auto}
 .search-ac-shell.ac-fs .ac-item{min-height:2.75rem;font-size:1rem;padding:.625rem 1rem}
 .search-ac-shell.ac-fs>.ac-width{display:none!important}
 body:not(.layout-edit) .search-ac-shell.ac-fs>.ac-height{display:none!important}
 body.display-fs.layout-edit .search-ac-shell.ac-fs>.ac-height{display:block!important}
 .ac-height,.kw-shade-height{display:none;box-sizing:border-box;position:absolute;z-index:4;left:0;right:0;bottom:0;width:100%;height:.625rem;min-height:.625rem;max-height:.625rem;margin:0;padding:0;border:0;background:transparent;cursor:row-resize;touch-action:none;-webkit-user-select:none;user-select:none;-webkit-tap-highlight-color:transparent}
 .ac-width{display:none;box-sizing:border-box;position:absolute;z-index:5;top:0;right:0;bottom:0;width:.625rem;min-width:.625rem;max-width:.625rem;height:auto;margin:0;padding:0;border:0;background:transparent;cursor:col-resize;touch-action:none;-webkit-user-select:none;user-select:none;-webkit-tap-highlight-color:transparent}
 .search-ac-shell:has(.search-autocomplete.open)>.ac-height,.search-ac-shell.open>.ac-height{display:block}
 .search-ac-shell:has(.search-autocomplete.open)>.ac-width,.search-ac-shell.open>.ac-width{display:block}
 body.search-mode.kw-open .search-ac-shell>.ac-width,body:not(.search-mode) .search-ac-shell>.ac-width{display:none!important}
 body.search-mode:not(.kw-open) .search-ac-shell.open:not(.ac-fs)>.ac-height,body.search-mode:not(.kw-open) .search-ac-shell:has(.search-autocomplete.open):not(.ac-fs)>.ac-height{right:.625rem;width:auto}
 body:not(.search-mode) .filter-wrap.open>.kw-shade-height{display:block}
 body.search-mode:not(.display-upper):not(.display-fs) .kw-shade-height,body.search-mode .search-chrome.search-split-ud .kw-shade-height{display:none}
 body.search-mode.display-upper .filter-wrap.open>.kw-shade-height,body.search-mode.display-fs .filter-wrap.open>.kw-shade-height{display:block}
 .ac-height::before,.kw-shade-height::before{content:"";position:absolute;left:28%;right:28%;top:3px;height:4px;background:var(--border);border-radius:2px;pointer-events:none}
 .ac-width::before{content:"";position:absolute;top:28%;bottom:28%;left:3px;width:4px;background:var(--border);border-radius:2px;pointer-events:none}
 .ac-height:hover::before,.ac-height:focus-visible::before,.search-ac-shell.ac-height-dragging>.ac-height::before,.kw-shade-height:hover::before,.kw-shade-height:focus-visible::before,.filter-wrap.kw-shade-dragging>.kw-shade-height::before,.ac-width:hover::before,.ac-width:focus-visible::before,.search-ac-shell.ac-width-dragging>.ac-width::before{background:var(--accent-instrument)}
 .search-ac-shell.ac-height-dragging,.search-ac-shell.ac-width-dragging,.filter-wrap.kw-shade-dragging{-webkit-user-select:none;user-select:none}
 body.layout-edit .search-autocomplete.open{padding-bottom:.625rem;padding-right:.625rem}
 .filter-wrap.kw-shade-height-set{overflow:hidden;display:flex;flex-direction:column}
 .filter-wrap.kw-shade-height-set .filter-top{flex:0 0 auto}
 .filter-wrap.kw-shade-height-set .filter-panel{flex:1 1 auto;min-height:0;max-height:none;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch}
 body.layout-edit #kwbar,
 .filter-wrap.kw-shade-height-set #kwbar,
 body.search-mode.layout-edit #kwbar,
 body.search-mode .search-chrome.search-height-set #kwbar{max-height:none!important;overflow:visible}
 .filter-wrap.kw-shade-dragging .filter-panel{transition:none}
 body:not(.layout-edit) .ac-height,body:not(.layout-edit) .ac-width,body:not(.layout-edit) .kw-shade-height{pointer-events:none;cursor:default}
 body:not(.layout-edit) .ac-height::before,body:not(.layout-edit) .ac-width::before,body:not(.layout-edit) .kw-shade-height::before{opacity:0}
 .search-strip{display:none;position:relative;min-height:2.75rem;height:auto;background:var(--bg-surface);border-bottom:1px solid var(--border);padding:0 .5rem;align-items:center;gap:.5rem;flex-wrap:wrap;box-sizing:border-box;width:100%;max-width:100%}
 .search-mode .search-strip{display:flex}
 .search-strip input{flex:1;min-width:0;background:transparent;border:none;outline:none;color:var(--text);font-size:1rem;caret-color:var(--accent-instrument);min-height:2.75rem}
 .search-strip input::placeholder{color:var(--text-muted)}
 .search-strip-clear{flex-shrink:0;background:transparent;border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:0 12px;font-size:.9375rem;cursor:pointer;min-height:2.75rem;touch-action:manipulation;display:inline-flex;align-items:center;justify-content:center;line-height:1;text-align:center}
 .search-strip-clear:hover{color:var(--accent-instrument);border-color:var(--accent-instrument)}
 .search-strip-hide{flex-shrink:0;background:transparent;border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:6px 12px;font-size:.9375rem;cursor:pointer;min-height:2.75rem;touch-action:manipulation;white-space:nowrap}
 .search-strip-hide:hover{color:var(--accent-instrument);border-color:var(--accent-instrument)}
 .kw-strip-hide{flex-shrink:0;background:transparent;border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:6px 12px;font-size:.9375rem;cursor:pointer;min-height:2.75rem;touch-action:manipulation;white-space:nowrap}
 .kw-strip-hide:hover{color:var(--accent-instrument);border-color:var(--accent-instrument)}
 body:not(.display-sides) .kw-strip-hide{display:none!important}
 .search-strip-fs{display:inline-flex;flex-shrink:0;box-sizing:border-box;background:var(--bg-card);border:1px solid var(--border);color:var(--text);border-radius:8px;padding:0;font-size:1rem;cursor:pointer;min-height:2.25rem;min-width:2.25rem;touch-action:manipulation;line-height:1;align-items:center;justify-content:center}
 .search-strip-fs:hover,.search-strip-fs[aria-pressed="true"]{color:var(--accent-instrument);border-color:var(--accent-instrument)}
 body.catalog-portable .search-strip-fs,.search-strip-fs.is-mobile{display:inline-flex}
 @media(max-width:899px){.search-strip-fs{display:inline-flex}}
 body.ac-fs-open .search-strip-hide{display:none!important}
 /* Row 2: search strip as direct child of ac-shell (below Row 1 bar) */
 body.ac-fs-open .search-ac-shell.ac-fs>.search-strip{display:flex;flex:0 0 auto;min-width:0;width:100%;max-width:100%;margin:0;padding:.375rem max(.75rem,env(safe-area-inset-right,0px)) .375rem max(.75rem,env(safe-area-inset-left,0px));border:0;border-bottom:1px solid var(--border);background:var(--bg-surface);flex-wrap:wrap;align-items:center;gap:.5rem;box-sizing:border-box;overflow:visible}
 body.ac-fs-open .search-ac-shell.ac-fs>.search-strip input{flex:1 1 auto;min-width:0;width:auto}
 body.ac-fs-open .search-ac-shell.ac-fs>.search-strip .search-strip-clear,
 body.ac-fs-open .search-ac-shell.ac-fs>.search-strip .search-strip-fs{flex:0 0 auto;position:static;max-width:100%}
 body.search-mode:not(.kw-open) #searchCol,body.search-mode:not(.kw-open) #acShell{
  font-size:calc(var(--ui-base) * var(--search-ui-scale,1));
 }
 body.search-mode:not(.kw-open) #searchCol :is(.search-strip input,.search-strip-clear,.search-strip-hide,.search-strip-fs,.ui-scale-step,.ui-scale-readout,.tap-add-btn),
 body.search-mode:not(.kw-open) #acShell :is(.ac-item,.ac-item .ac-note,.ac-item .ac-count,.ac-group-label,.ac-fs-close){
  font-size:1em;
 }
 body.search-mode:not(.kw-open) #searchCol :is(.search-strip,.search-strip input,.search-strip-clear,.search-strip-hide,.search-strip-fs,.ui-scale-step,.ui-scale-readout),
 body.search-mode:not(.kw-open) #acShell :is(.ac-item,.ac-fs-close){
  min-height:2.75em;
 }
 body.search-mode:not(.kw-open) #searchCol .search-strip-fs{min-width:2.75em}
 .search-only-scale{display:none;flex:0 0 auto;position:relative;z-index:6;min-width:0}
 body.search-mode:not(.kw-open):not(.search-chrome-collapsed):not(.ac-fs-open) .search-only-scale{display:flex}
 body.ac-fs-open .search-only-scale{display:none!important}
 .search-only-scale .ui-scale-step,.search-only-scale .ui-scale-readout{min-height:2.75em}
 .tap-add-btn{flex-shrink:0;box-sizing:border-box;min-height:2.75rem;background:transparent;border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:0 12px;font-size:.9375rem;cursor:pointer;touch-action:manipulation;white-space:nowrap}
 .tap-add-btn[aria-pressed="true"]{background:var(--accent-instrument-bg);color:var(--accent-instrument);border-color:var(--accent-instrument);font-weight:600}
 body:not(.search-mode) .tap-add-btn{display:none}
 .clear-miss-btn,.layout-edit-btn,.layout-default-btn,.layout-presets-btn,.ui-scale-step,.ui-scale-readout{min-height:2.75rem}
 .mode-btn.clear-all{border-color:#c03040;color:#ff9090;background:rgba(180,40,40,0.2)}
 body.search-extras-collapsed .search-autocomplete,body.search-extras-collapsed .search-active-pills,body.search-chrome-collapsed .search-autocomplete,body.search-chrome-collapsed .search-active-pills,body.search-extras-collapsed .search-ac-shell,body.search-chrome-collapsed .search-ac-shell{display:none!important}
 body.search-chrome-collapsed .search-ac-shell.ac-fs,body.search-extras-collapsed .search-ac-shell.ac-fs{display:flex!important}
 body.search-chrome-collapsed .search-ac-shell.ac-fs .search-autocomplete,body.search-extras-collapsed .search-ac-shell.ac-fs .search-autocomplete{display:block!important}
 body.search-chrome-collapsed .search-strip input,
 body.search-chrome-collapsed .search-strip-clear,
 body.search-chrome-collapsed .search-strip-fs,
 body.search-chrome-collapsed .search-only-scale{display:none!important}
 body.search-chrome-collapsed .search-strip{flex-wrap:nowrap;gap:.5rem;border-bottom:none;padding-left:0;padding-right:0;min-width:0;width:auto}
 .filter-wrap:not(.open)>.filter-top .clear-miss-btn,
 .filter-wrap:not(.open)>.filter-top .layout-edit-btn,
 .filter-wrap:not(.open)>.layout-presets,
 .filter-wrap:not(.open)>.filter-kw-tools{display:none!important}
 .filter-wrap:not(.open)>.filter-top{padding-bottom:0}
 .filter-wrap:not(.open) .filter-toggle{flex:0 1 auto;width:auto;max-width:100%;min-width:0}
 .filter-kw-tools{display:flex;align-items:center;flex-wrap:wrap;gap:6px;width:100%;max-width:100%;box-sizing:border-box;padding:0 0 .5rem;min-width:0;flex:0 0 auto;position:relative;z-index:5}
 .filter-wrap.open>.filter-kw-tools{display:flex}
 .filter-wrap:not(.open)>.filter-kw-tools{display:none!important}
 .filter-kw-tools .layout-presets{padding:0;width:auto;flex:1 1 auto}
 .filter-kw-tools .clear-miss-btn,.filter-kw-tools .layout-edit-btn,.filter-kw-tools .layout-default-btn{flex:0 0 auto}
 .search-autocomplete{position:relative;top:auto;left:auto;right:auto;background:var(--bg-surface);border:1px solid var(--border);border-top:none;z-index:2;max-height:calc(100dvh - env(safe-area-inset-bottom,0px) - 6.5rem);overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;touch-action:pan-y;overscroll-behavior:contain;display:none;max-width:100%;width:100%;box-sizing:border-box;font-size:1rem}
 .search-autocomplete.open{display:block}
.search-autocomplete{scrollbar-width:none!important;-ms-overflow-style:none!important}
.search-autocomplete::-webkit-scrollbar{display:none!important;width:0!important;height:0!important}
.ac-scroll-stripe{position:absolute;top:0;right:3px;width:12px;z-index:12;display:none;pointer-events:none;touch-action:none;-webkit-user-select:none;user-select:none;box-sizing:border-box}
.ac-scroll-stripe[hidden]{display:none!important}
.search-ac-shell.has-ac-overflow>.ac-scroll-stripe:not([hidden]){display:block;pointer-events:auto}
.ac-scroll-thumb{position:absolute;right:1px;width:3px;min-height:1.15rem;border-radius:999px;background:var(--accent-instrument);opacity:.4;box-shadow:0 0 0 1px var(--border);cursor:grab;touch-action:none;transform-origin:right center;transition:width .14s ease,opacity .14s ease,transform .14s ease}
.search-ac-shell.has-ac-overflow>.ac-scroll-stripe:hover .ac-scroll-thumb,.search-ac-shell.has-ac-overflow>.ac-scroll-stripe.is-dragging .ac-scroll-thumb{width:7px;opacity:.92;transform:scaleY(1.08);cursor:grabbing}
.hover-scroll-stripe{position:absolute;top:4px;right:3px;bottom:4px;width:12px;z-index:28;display:none;pointer-events:none;touch-action:none;-webkit-user-select:none;user-select:none;box-sizing:border-box}
.hover-scroll-stripe[hidden]{display:none!important}
.hover-scroll-host.has-hover-overflow>.hover-scroll-stripe:not([hidden]){display:block;pointer-events:auto}
.hover-scroll-thumb{position:absolute;right:1px;width:3px;min-height:1.15rem;border-radius:999px;background:var(--accent-instrument);opacity:.4;box-shadow:0 0 0 1px var(--border);cursor:grab;touch-action:none;transform-origin:right center;transition:width .14s ease,opacity .14s ease,transform .14s ease}
.hover-scroll-host.has-hover-overflow>.hover-scroll-stripe:hover .hover-scroll-thumb,.hover-scroll-host.has-hover-overflow>.hover-scroll-stripe.is-dragging .hover-scroll-thumb{width:7px;opacity:.92;transform:scaleY(1.08);cursor:grabbing}
#catalogMain>.hover-scroll-stripe{z-index:8;top:4px}
#catalogMainHoverStripe.hover-scroll-fixed{position:fixed!important;z-index:24;width:12px;margin:0;display:none;pointer-events:none}
body.has-hover-overflow-content #catalogMainHoverStripe.hover-scroll-fixed:not([hidden]){display:block;pointer-events:auto}
body.has-hover-overflow-content.is-content-hover #catalogMainHoverStripe .hover-scroll-thumb,#catalogMainHoverStripe.hover-scroll-fixed:hover .hover-scroll-thumb,#catalogMainHoverStripe.hover-scroll-fixed.is-dragging .hover-scroll-thumb{width:7px;opacity:.92;transform:scaleY(1.08);cursor:grabbing}
#catalogIndex>.hover-scroll-stripe{top:var(--index-bar-h,2.75rem);z-index:10}
#cardMinDock{position:fixed}
#cardMinDock .card-min-save{pointer-events:auto;position:absolute;right:.75rem;bottom:max(.85rem,env(safe-area-inset-bottom));display:inline-flex;align-items:center;justify-content:center;min-height:2.85rem;padding:0 .8rem;border:1px solid var(--accent-instrument);border-radius:999px;background:var(--bg-card);color:var(--accent-instrument);font:inherit;font-size:.9rem;font-weight:650;cursor:pointer;touch-action:manipulation;box-shadow:0 8px 28px rgba(0,0,0,.38);z-index:1}
body.display-middle #cardMinDock .card-min-save,body.display-sides #cardMinDock .card-min-save{right:auto;left:calc(50% + (var(--card-min-stack-w,0px) / 2) + .45rem)}
#cardMinSavePop{position:absolute;bottom:calc(100% + .45rem);left:50%;transform:translateX(-50%);z-index:10041;min-width:14rem;padding:.55rem;border:1px solid var(--border);border-radius:8px;background:var(--bg-surface);box-shadow:0 10px 28px rgba(0,0,0,.4);pointer-events:auto}
#cardMinSavePop[hidden]{display:none!important}
#cardMinSaveName{width:100%;box-sizing:border-box;min-height:2.25rem;margin:0 0 .4rem;padding:.3rem .5rem;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text);font:inherit}
#cardMinSaveGo{width:100%;min-height:2.25rem;border:1px solid var(--accent-instrument);border-radius:6px;background:var(--accent-instrument-bg);color:var(--accent-instrument);font:inherit;cursor:pointer}
.entry>.cover>img,.entry .cover>img{display:block;visibility:visible;max-width:100%;min-height:4.5rem;height:auto}
.search-autocomplete .ac-item.ac-session .ac-count,.search-autocomplete .ac-item.ac-combo .ac-count,.search-autocomplete .ac-item.ac-cardhit .ac-count{color:var(--text-muted)}
body.display-sides #catalogMain,body.display-sides #catalogIndex{position:relative}
 .search-autocomplete.ac-height-set,.search-autocomplete.ac-height-dragging{max-height:none}
 .search-autocomplete .ac-item{padding:10px clamp(8px,2vw,20px);cursor:pointer;font-size:1rem;color:var(--text);display:flex;justify-content:space-between;min-height:2.75rem;align-items:center;gap:8px}
 .search-autocomplete .ac-item:hover{background:var(--bg-card)}
 .search-autocomplete .ac-item .ac-label{display:flex;align-items:center;gap:8px;min-width:0;flex:1}
 .search-autocomplete .ac-item.ac-lib{align-items:flex-start;height:auto;white-space:normal}
 .search-autocomplete .ac-item.ac-lib .ac-label{display:block;white-space:normal;overflow-wrap:anywhere;word-break:break-word;align-self:center;line-height:1.3}
 .search-autocomplete .ac-item.ac-lib .ac-lib-mark{flex:0 0 auto;align-self:center;color:var(--text-muted);font-variant-numeric:tabular-nums;letter-spacing:.02em}
.kw-combo-save{flex:0 0 auto;box-sizing:border-box;min-height:2.25rem;padding:0 .8rem;border:1px solid var(--accent-instrument);border-radius:999px;background:var(--bg-card);color:var(--accent-instrument);font:inherit;font-size:.9rem;font-weight:650;cursor:pointer;touch-action:manipulation}
.kw-combo-save[hidden]{display:none!important}
.kw-combo-save-pop{min-width:14rem;padding:.55rem;border:1px solid var(--border);border-radius:8px;background:var(--bg-surface);box-shadow:0 10px 28px rgba(0,0,0,.4)}
.kw-combo-save-pop[hidden]{display:none!important}
#kwComboSaveName{width:100%;box-sizing:border-box;min-height:2.25rem;margin:0 0 .4rem;padding:.3rem .5rem;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text);font:inherit}
#kwComboSaveGo{width:100%;min-height:2.25rem;border:1px solid var(--accent-instrument);border-radius:6px;background:var(--accent-instrument-bg);color:var(--accent-instrument);font:inherit;cursor:pointer}
 .search-autocomplete .ac-item .ac-note{flex-shrink:0;font-size:1rem;line-height:1}
 .search-autocomplete .ac-item .ac-count{color:var(--text-muted);font-size:.85em;flex-shrink:0}
 .search-active-pills{display:none;flex-wrap:wrap;gap:6px;padding:clamp(4px,.5vw,8px) clamp(8px,2vw,20px);background:var(--bg-surface);border-bottom:1px solid var(--border);position:relative;max-width:100%;width:100%;box-sizing:border-box}
 .search-mode .search-active-pills{display:flex;align-items:center}
 body.search-mode:not(.kw-open) .search-active-pills{display:none!important}
 .pill-tag{background:var(--accent-instrument-bg);color:var(--accent-instrument);border:1px solid var(--accent-instrument);border-radius:12px;padding:.125rem .125rem .125rem .625rem;font-size:.9375rem;cursor:default;display:flex;align-items:center;gap:0;-webkit-user-select:none;user-select:none;min-height:2.25rem}
 .pill-tag.patch{background:var(--accent-patch-bg);color:var(--accent-patch);border-color:var(--accent-patch)}
 .pill-tag.patch .pill-x{color:var(--accent-patch)}
 .pill-tag .pill-label{padding-right:2px}
 .pill-tag .pill-x{opacity:1;display:inline-flex;align-items:center;justify-content:center;min-width:2.25rem;min-height:2.25rem;margin:0;padding:0;border:0;background:transparent;color:var(--accent-instrument);font-size:1.25rem;font-weight:700;line-height:1;cursor:pointer;touch-action:manipulation;-webkit-touch-callout:none;border-radius:10px}
 .pill-tag .pill-x:hover{background:rgba(255,144,144,0.18);color:#ff9090}
 .cat-switch{display:flex;flex-wrap:wrap;align-items:center;align-content:flex-start;gap:clamp(4px,0.8vw,8px);margin-bottom:clamp(6px,1.2vw,10px);width:100%;max-width:100%;min-width:0;height:auto;overflow:visible;box-sizing:border-box}.cat-switch-lead{display:inline-flex;flex-wrap:nowrap;align-items:center;gap:clamp(4px,0.8vw,8px);flex:0 0 auto}.cat-switch .tap-add-btn,.cat-switch .mode-btn.clear-all{flex:0 0 auto;min-height:2.25rem;align-self:center}
 .cat-btn{background:var(--bg-card);border:1px solid var(--border);color:var(--text-muted);border-radius:6px;padding:8px 14px;font-size:.9375rem;cursor:pointer;min-height:2.25rem;flex:0 0 auto;touch-action:manipulation;white-space:nowrap;transition:background 0.15s,color 0.15s}
 .cat-btn.active{background:var(--accent-instrument-bg);color:var(--accent-instrument);border-color:var(--accent-instrument);font-weight:600}
 .cat-btn[data-cat="patch"].active{background:var(--accent-patch-bg);color:var(--accent-patch);border-color:var(--accent-patch)}
 @media(max-width:899px){body{font-size:1rem}.entry h3{font-size:clamp(1rem,1.15em,1.375rem)}.kw{min-height:2.75rem;font-size:.9375rem;padding:.5rem .875rem}.cat-btn,.mode-btn,.tap-add-btn,.clear-miss-btn,.layout-edit-btn,.layout-presets-btn,.ui-scale-step,.ui-scale-readout,.search-strip-clear,.search-strip-hide,.search-strip-fs,.mode-btn.clear-all{min-height:2.75rem;font-size:.9375rem}.filter-toggle{font-size:.9375rem;min-height:2.75rem}.theme-picker{font-size:.9375rem;min-height:2.25rem}.path,.path code,.path .folder{font-size:.875rem}.summary-panel .desc,.desc{font-size:1rem}.search-popup-btn,.search-link{min-height:2.75rem;font-size:.9375rem}.pill-tag{font-size:.9375rem;min-height:2.75rem}.index{font-size:1rem}}
 @media(orientation:portrait){.filter-panel,body.display-sides #filterWrap .filter-panel,body.display-sides.display-middle #filterWrap .filter-panel{flex-direction:column!important;flex-wrap:nowrap!important;align-items:stretch;max-width:100%;min-width:0;overflow-x:hidden}.cat-switch,#kwbar,.mode-switch{flex-wrap:wrap!important;max-width:100%;min-width:0;width:100%;box-sizing:border-box;overflow-x:hidden}.cat-switch{overflow-y:visible;-webkit-overflow-scrolling:touch;align-content:flex-start}.cat-switch-lead{display:flex!important;flex-wrap:wrap!important;max-width:100%;min-width:0;flex:0 1 auto}.filter-panel>#kwbar,body.display-sides #kwbar,body.display-sides.display-middle #kwbar{overflow-x:hidden!important;overflow-y:auto!important;align-content:flex-start;min-width:0}body:not(.layout-edit) .filter-wrap:not(.kw-shade-height-set) #kwbar{overflow-x:hidden;overflow-y:auto;max-height:none}.entry.highlight .cover,.entry.highlight .cover img{max-height:min(38dvh,100%)}}
 @media(max-width:899px) and (orientation:landscape){body.search-mode.kw-open .search-strip input{flex:1 1 8rem;min-width:0}}.entry.highlight .cover,.entry.highlight .cover img{max-height:min(32dvh,100%)}#kwbar{flex-wrap:wrap;max-width:100%;min-width:0;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;align-content:flex-start}.cat-switch{flex-wrap:wrap;overflow:visible;max-width:100%;height:auto}}
 @media(min-width:900px){.entry.highlight .cover,.entry.highlight .cover img{max-width:100%;max-height:min(70dvh,calc(100dvh - 12em));width:auto;height:auto;object-fit:contain;object-position:center center}.entry.highlight .cover img{width:auto;height:auto;max-width:100%;max-height:min(70dvh,calc(100dvh - 12em));object-fit:contain}.entry.highlight .summary-panel .desc{font-size:1.125rem}}
 .search-autocomplete .ac-group-label{padding:4px clamp(8px,2vw,20px) 2px;font-size:.75em;font-weight:700;color:var(--accent-gear);text-transform:uppercase;letter-spacing:.05em}
 .search-autocomplete .ac-group-label[data-cat="patch"]{color:var(--accent-patch)}
 .search-autocomplete .ac-item[data-cat="patch"] .ac-label{color:var(--accent-patch)}
 .search-autocomplete .ac-group-label.ac-fav-label{color:var(--accent-instrument)}
 .search-autocomplete .ac-item.fav-rec{opacity:.72;filter:saturate(.75);background:rgba(0,0,0,.12);box-shadow:inset 0 0 24px rgba(0,0,0,.16);border-left:3px dashed var(--accent-gear)}
 .search-autocomplete .ac-item.fav-rec:hover{opacity:1;filter:none}
 /* ====== KW Fullscreen + Dual Fullscreen system ====== */
 .kw-fs-btn{display:inline-flex;box-sizing:border-box;min-width:2.25rem;min-height:2.25rem;padding:0;border:1px solid var(--border);border-radius:8px;background:var(--bg-card);color:var(--text);font:inherit;font-size:1rem;cursor:pointer;touch-action:manipulation;align-items:center;justify-content:center;flex:0 0 auto}
 body.search-mode .kw-fs-btn{display:inline-flex}
 .kw-fs-btn:hover,.kw-fs-btn[aria-pressed="true"]{border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 .kw-fs-back{display:none;box-sizing:border-box;min-width:2.25rem;min-height:2.25rem;padding:0 .625rem;border:1px solid var(--border);border-radius:8px;background:var(--bg-card);color:var(--text);font:inherit;cursor:pointer;touch-action:manipulation;align-items:center;gap:.25rem;flex:0 0 auto;white-space:nowrap;font-size:.9375rem}
 body.kw-fs-open .kw-fs-back{display:inline-flex}
 .fs-mode-nav{display:none;align-items:center;gap:4px;flex:0 1 auto;min-width:0}
 body.ac-fs-open .ac-fs-bar .fs-mode-nav,body.kw-fs-open .filter-top .fs-mode-nav{display:inline-flex}
 .fs-mode-nav .mode-btn{min-height:2.25rem;padding:0 .7rem}
 body.kw-fs-open .filter-kw-tools{display:none!important}
 body.kw-fs-open .kw-fs-btn{display:none!important}
 body.kw-fs-open .filter-panel>.mode-switch{display:none!important}
 body.kw-fs-open .filter-top{flex-wrap:nowrap}
 body.kw-fs-open .filter-wrap .filter-top .filter-toggle{flex:0 1 auto!important;max-width:12rem}
 body.kw-fs-open .filter-top .fs-mode-nav{margin-right:auto}
 body.ac-fs-open .search-ac-shell.ac-fs{display:grid!important;grid-template-columns:auto minmax(0,1fr);grid-template-rows:auto minmax(0,1fr);align-items:stretch}
 body.ac-fs-open .search-ac-shell.ac-fs .ac-fs-bar{grid-column:1;grid-row:1;width:auto;max-width:100%;padding:.35rem .4rem}
 body.ac-fs-open .search-ac-shell.ac-fs>.search-strip{grid-column:2;grid-row:1;min-width:0}
 body.ac-fs-open .search-ac-shell.ac-fs>.search-strip .search-strip-fs{display:none!important}
 body.ac-fs-open .search-ac-shell.ac-fs>.search-autocomplete,body.ac-fs-open .search-ac-shell.ac-fs>#acList{grid-column:1/-1;grid-row:2;min-height:0}
 .kw-companion-btn,.ac-companion-btn{display:none;box-sizing:border-box;min-width:2.25rem;min-height:2.25rem;padding:0 .625rem;border:1px solid var(--border);border-radius:8px;background:var(--bg-card);color:var(--text);font:inherit;font-size:.9375rem;cursor:pointer;touch-action:manipulation;align-items:center;justify-content:center;flex:0 0 auto;white-space:nowrap}
 .kw-companion-btn:hover,.ac-companion-btn:hover,.kw-companion-btn[aria-pressed="true"],.ac-companion-btn[aria-pressed="true"]{border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 body.ac-fs-open .kw-companion-btn{display:inline-flex}
 .filter-wrap .ac-companion-btn{display:inline-flex}
 body.search-mode .ac-companion-btn,body.kw-fs-open .ac-companion-btn{display:inline-flex}
 .fs-stripe-wrap{display:none;position:relative;align-items:center;margin-left:auto;flex:0 0 auto}
 body.ac-fs-open .fs-stripe-wrap,body.kw-fs-open .fs-stripe-wrap{display:flex}
 .fs-stripe-trigger{box-sizing:border-box;min-width:2rem;min-height:2.25rem;padding:0;border:1px solid var(--border);border-radius:8px;background:var(--bg-card);color:var(--text-muted);font:inherit;font-size:1.1rem;cursor:pointer;touch-action:manipulation;display:flex;align-items:center;justify-content:center;flex:0 0 auto;position:relative;z-index:2}
 .fs-stripe-trigger:hover{color:var(--accent-instrument);border-color:var(--accent-instrument)}
 .fs-stripe-panel{position:absolute;right:100%;top:50%;transform:translateY(-50%);display:flex;flex-direction:row;align-items:center;gap:6px;padding:5px 0;background:var(--bg-surface);border:1px solid var(--border);border-radius:8px 0 0 8px;border-right:none;max-width:0;overflow:hidden;transition:max-width .18s ease,padding .18s ease;white-space:nowrap;z-index:1;pointer-events:none}
 .fs-stripe-panel.stripe-open{max-width:min(80vw,320px);padding:5px 8px;pointer-events:auto}
 .fs-snap-btn,.fs-pin-btn{box-sizing:border-box;min-width:2.25rem;min-height:2.25rem;padding:0 .625rem;border:1px solid var(--border);border-radius:8px;background:var(--bg-card);color:var(--text);font:inherit;font-size:.875rem;cursor:pointer;touch-action:manipulation;display:inline-flex;align-items:center;justify-content:center;white-space:nowrap;flex-shrink:0}
 .fs-snap-btn:hover,.fs-pin-btn:hover,.fs-pin-btn[aria-pressed="true"]{border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 /* Stripe scale buttons (single fullscreen only, shown via CSS) */
 .fs-stripe-scale{display:none;align-items:center;gap:2px;flex-shrink:0}
 body.ac-fs-open:not(.dual-fs-open) .fs-stripe-scale.for-ac{display:flex}
 body.kw-fs-open:not(.dual-fs-open) .fs-stripe-scale.for-kw{display:flex}
 .fs-stripe-scale-btn{box-sizing:border-box;min-width:2rem;min-height:2rem;padding:0;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text);font:inherit;font-size:.9375rem;cursor:pointer;touch-action:manipulation;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0}
 .fs-stripe-scale-btn:hover{border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 /* Search FS secondary ctx bar — collapsed into stripe; toggle + bar always hidden in FS */
 .ac-ctx-toggle{display:none}
 .ac-ctx-arrow{display:none}
 .ac-ctx-bar{display:none!important}
 .ac-ctx-row{display:flex;flex-wrap:wrap;align-items:center;gap:.375rem;padding:.375rem max(.75rem,env(safe-area-inset-right,0px)) .375rem max(.75rem,env(safe-area-inset-left,0px));box-sizing:border-box;width:100%;min-width:0;overflow:visible}
 /* KW ctx: separator below filter-kw-tools when in KW fullscreen */
 body.kw-fs-open .filter-kw-tools{border-bottom:1px solid var(--border);padding-bottom:.5rem;margin-bottom:.25rem}
 /* Narrow panels in dual-fs portrait: single-column adaptive layout */
 @media(orientation:portrait){
  body.dual-fs-open.dual-kw-narrow #kwbar{flex-direction:column;align-items:stretch}
  body.dual-fs-open.dual-kw-narrow .kw{width:100%;box-sizing:border-box;white-space:normal;word-break:break-word;overflow-wrap:break-word;hyphens:auto}
  body.dual-fs-open.dual-ac-narrow .search-autocomplete .ac-item{flex-direction:column;align-items:flex-start;gap:4px}
  /* Syllable-aware wrap for keyword pills in dual-fs portrait */
  body.dual-fs-open #kwbar .kw{word-break:break-word;overflow-wrap:break-word;hyphens:auto;white-space:normal}
 }
 body.kw-fs-open{overflow:hidden;overscroll-behavior:none}
 body.kw-fs-open .filter-wrap{position:fixed!important;inset:0!important;z-index:282!important;display:flex!important;flex-direction:column!important;max-height:none!important;overflow:hidden!important;background:var(--bg-surface);padding:env(safe-area-inset-top,0px) env(safe-area-inset-right,0px) env(safe-area-inset-bottom,0px) env(safe-area-inset-left,0px);pointer-events:auto!important}
 body.kw-fs-open .filter-wrap .filter-top{flex:0 0 auto!important;display:flex!important;flex-wrap:wrap!important;align-items:center;gap:.375rem;padding:.5rem max(.625rem,env(safe-area-inset-right,0px)) .5rem max(.625rem,env(safe-area-inset-left,0px));border-bottom:1px solid var(--border);background:var(--bg-surface);overflow:visible;position:relative;z-index:2;min-height:0}
 body.kw-fs-open .filter-wrap .filter-top .filter-toggle{flex:1 1 auto!important;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
 body.kw-fs-open .filter-wrap .filter-panel{flex:1 1 auto!important;min-height:0!important;max-height:none!important;overflow-y:auto!important;-webkit-overflow-scrolling:touch!important;overscroll-behavior:contain;display:block!important}
 body.dual-fs-open .search-ac-shell.ac-fs{width:var(--dual-fs-lw,50%)!important;right:auto!important}
 body.dual-fs-open .filter-wrap{left:var(--dual-fs-lw,50%)!important;width:calc(100% - var(--dual-fs-lw,50%))!important;right:0!important}
 .dual-fs-sep{display:none;position:fixed;top:0;bottom:0;z-index:290;width:6px;transform:translateX(-50%);cursor:col-resize;touch-action:none;-webkit-user-select:none;user-select:none;background:var(--border);transition:background .15s}
 body.dual-fs-open .dual-fs-sep{display:block}
 body.dual-fs-open .dual-fs-sep:hover,.dual-fs-sep.sep-dragging{background:var(--accent-instrument)}
 .dual-fs-sep.sep-pinned{cursor:default!important}
 .dual-fs-sep.sep-pinned:hover{background:var(--border)}
 .dual-fs-sep-pin{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:1.875rem;height:1.875rem;border:1px solid var(--border);border-radius:50%;background:var(--bg-card);color:var(--text-muted);cursor:pointer;touch-action:manipulation;display:flex;align-items:center;justify-content:center;font-size:.875rem}
 .dual-fs-sep-pin:hover,.dual-fs-sep-pin[aria-pressed="true"],.dual-fs-sep.sep-pinned .dual-fs-sep-pin{border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 @media(max-width:899px){
  /* Fix 4: mobile — scroll/slide expanded search+keywords menus that overflow screen */
  body.search-mode:not(.layout-edit) .search-chrome:not(.search-height-set){max-height:100dvh;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;overscroll-behavior:contain}
  /* When kw-open, restore sticky so the chrome stays at the top of the viewport */
  body.search-mode.kw-open:not(.layout-edit) .search-chrome:not(.search-height-set){position:sticky;top:0;z-index:200}
 }
/* === Scroll-collapse toolbar (IntersectionObserver-driven) === */
.search-ac-shell.ac-fs.toolbar-scroll-collapsed>.search-strip{
  display:none!important;
}
.search-ac-shell.ac-fs.toolbar-scroll-collapsed .fs-stripe-wrap{
  display:none!important;
}
body.kw-fs-open .filter-wrap.toolbar-scroll-collapsed .fs-stripe-wrap,
body.kw-fs-open .filter-wrap.toolbar-scroll-collapsed .kw-fs-btn{
  display:none!important;
}
body:not(.ac-fs-open) .search-ac-shell.toolbar-scroll-collapsed>.search-strip{
  display:flex!important;
}

 .hdr-menu-btns{display:flex;align-items:center;gap:4px;flex:0 0 auto;margin-left:.35rem}
 .hdr-menu-btn{box-sizing:border-box;min-width:2.25rem;min-height:2.25rem;padding:0 .5rem;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text-muted);font:inherit;font-size:.875rem;font-weight:600;cursor:pointer;touch-action:manipulation;line-height:1;display:inline-flex;align-items:center;justify-content:center;text-align:center}
 .hdr-menu-btn.is-on{background:var(--accent-instrument-bg);color:var(--accent-instrument);border-color:var(--accent-instrument)}
 .hdr-menu-btn[aria-pressed="false"]{opacity:.72}
 .search-strip{position:relative}
 .search-strip-more{flex:0 0 auto;min-width:2.25rem;min-height:2.25rem;padding:0 .45rem;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text);font:inherit;cursor:pointer;margin-left:auto}
 .search-strip-more-pop{position:absolute;right:.5rem;top:calc(100% + 4px);z-index:260;min-width:12rem;display:flex;flex-direction:column;gap:.35rem;padding:.5rem;background:var(--bg-surface);border:1px solid var(--border);border-radius:8px;box-shadow:0 12px 28px rgba(0,0,0,.38)}
 .search-strip-more-pop[hidden]{display:none!important}
 .search-strip-more-pop button{min-height:2.25rem;text-align:left;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text);padding:.35rem .6rem;cursor:pointer;font:inherit}
 .catalog-index-embed{box-sizing:border-box;min-height:2.25rem;padding:0 .55rem;border:1px solid var(--border);border-radius:8px;background:var(--bg-surface);color:var(--text);font:inherit;font-size:.75rem;cursor:pointer;margin-left:auto}
 .catalog-index-embed[aria-pressed="true"]{background:var(--accent-instrument-bg);color:var(--accent-instrument);border-color:var(--accent-instrument)}

 body.display-upper .catalog-header+p,body.display-upper .catalog-header+p+p{display:none}
 body.display-upper.search-mode .search-chrome{height:auto!important;max-height:min(68dvh,50rem);margin-bottom:.35rem}
 body.display-upper .catalog-index{margin-top:.35rem}
 body.display-upper:not(.layout-edit) #searchChrome{min-height:0}
 body.display-upper.search-chrome-collapsed .search-strip-hide{display:none!important}
 .search-strip-hide{display:none!important} /* fix-hdr: toolbar 🔍 is sole toggle — strip button redundant */
 body.display-sides #kwStripHide{display:none!important}
 body.display-fs.ac-fs-open .search-strip-clear,
 body.display-fs.ac-fs-open .search-strip-fs,
 body.display-fs.ac-fs-open .search-strip-more{display:inline-flex!important}
 body.display-fs.ac-fs-open .search-only-scale{display:flex!important}
 body.display-fs.ac-fs-open .search-ac-shell.ac-fs>.search-strip{display:flex!important;flex-wrap:wrap;align-items:center}
 body.display-fs .search-ac-shell.ac-fs.toolbar-scroll-collapsed>.search-strip{display:flex!important}
 body.display-upper .search-strip-clear,body.display-upper .search-strip-fs,body.display-upper .search-strip-more{display:inline-flex!important}
 body.display-sides:not(.search-chrome-collapsed) .search-strip-clear,
 body.display-sides:not(.search-chrome-collapsed) .search-strip-fs,
 body.display-sides:not(.search-chrome-collapsed) .search-strip-more{display:inline-flex!important}
 body.display-sides:not(.search-chrome-collapsed) .search-only-scale{display:flex!important}
 body.display-sides.search-chrome-collapsed .search-strip-more{display:none!important}
 .display-switch{display:flex;align-items:center;gap:4px;flex:0 0 auto;margin-left:.5rem}
 .display-btn{box-sizing:border-box;min-height:2.25rem;padding:0 .65rem;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text-muted);font:inherit;font-size:.8125rem;cursor:pointer;touch-action:manipulation;display:inline-flex;align-items:center;justify-content:center;line-height:1;text-align:center}
 .ui-btn-center,.display-btn,.clear-miss-btn,.layout-edit-btn,.layout-default-btn,.layout-presets-btn,.layout-presets-tab,.hdr-menu-btn,.search-strip-clear,.search-strip-hide,.search-strip-fs,.search-strip-more,.mode-btn,.cat-btn,.tap-add-btn,.ui-scale-step,.ui-scale-readout,.ac-history-btn,.catalog-index-embed,.layout-restore-defaults,.layout-presets-save>button,.kw-strip-hide,.kw-fs-btn,.fs-stripe-scale-btn,.fs-snap-btn,.fs-stripe-trigger,.card-min-save{display:inline-flex;align-items:center;justify-content:center;line-height:1;text-align:center}
 .search-strip-clear,.mode-btn,.cat-btn,.tap-add-btn{padding-top:0;padding-bottom:0}
 .display-btn[data-display="middle"]{align-items:center!important;justify-content:center!important;line-height:1}
 .display-btn.is-active{background:var(--accent-instrument-bg);color:var(--accent-instrument);border-color:var(--accent-instrument);font-weight:600}
 @media(max-width:899px){.display-btn.display-desktop-only{display:none!important}.display-btn[data-display='sides'],.display-btn[data-display='middle']{display:inline-flex!important}}
 .catalog-main{width:100%;max-width:100%;min-width:0}
 @media(min-width:900px){
  body.display-sides{max-width:none;width:100%;margin:0;padding:0;height:100dvh;overflow:hidden;display:grid;grid-template-columns:var(--sides-lw,22vw) minmax(0,1fr) var(--sides-rw,26vw);grid-template-rows:auto minmax(0,1fr) var(--card-min-dock-h,0px);column-gap:var(--sides-pane-gap,6px);row-gap:0;align-items:stretch}
  body.display-sides.search-chrome-collapsed{grid-template-columns:minmax(0,1fr) var(--sides-rw,26vw)}
  body.display-sides.kw-chrome-collapsed{grid-template-columns:var(--sides-lw,22vw) minmax(0,1fr)}
  body.display-sides.search-chrome-collapsed.kw-chrome-collapsed{grid-template-columns:minmax(0,1fr)}
  body.display-sides .catalog-header{grid-column:1/-1;grid-row:1;padding:.4rem .75rem;margin:0;border-bottom:1px solid var(--border);background:var(--bg-surface);z-index:30}
  body.display-sides .catalog-header+p,body.display-sides .catalog-header+p+p{display:none}
  body.display-sides #searchChrome{grid-column:1;grid-row:2;height:100%;min-height:0;max-width:none;width:100%;overflow:hidden;display:flex!important;flex-direction:column;position:relative!important;top:auto!important;z-index:5;background:var(--bg-surface);border-right:1px solid var(--border);border-bottom:1px solid var(--border);padding:0;align-items:stretch;align-self:stretch;box-sizing:border-box}
  body.display-sides.search-chrome-collapsed #searchChrome{display:none!important;width:0!important;min-width:0!important;max-width:0!important;overflow:hidden!important;border:0!important;padding:0!important}
  body.display-sides.search-chrome-collapsed .search-strip-hide,body.display-sides.search-chrome-collapsed #searchChrome .search-strip{display:none!important}
  body.display-sides.search-chrome-collapsed #searchSplit{display:none!important}
  body.display-sides.kw-chrome-collapsed #filterWrap{display:none!important;width:0!important;min-width:0!important;max-width:0!important;overflow:hidden!important;border:0!important;padding:0!important;height:0!important}
  body.display-sides.kw-chrome-collapsed .kw-strip-hide,body.display-sides.kw-chrome-collapsed #filterWrap .filter-top,body.display-sides.kw-chrome-collapsed .filter-toggle{display:none!important}
  body.display-sides.kw-chrome-collapsed #dualFsSep{display:none!important}
  body.display-sides #searchCol{flex:1;min-height:0;display:flex!important;flex-direction:column;overflow:hidden;width:100%;max-width:none}
  body.display-sides .search-strip{display:flex!important;flex:0 0 auto}
  body.display-sides #acFsBar,body.display-sides .ac-fs-bar,body.display-sides .kw-fs-back,body.display-sides .ac-fs-back,body.display-sides .ac-companion-btn,body.display-sides .kw-companion-btn,body.display-sides .fs-stripe-wrap,body.display-sides .fs-mode-nav{display:none!important}
 body.display-sides .kw-fs-btn,body.display-sides .search-strip-fs{display:inline-flex!important}
  body.display-sides #searchCol .search-strip-anchor{flex:1;min-height:0;display:flex;flex-direction:column;overflow:hidden}
  body.display-sides #filterWrap{grid-column:3;grid-row:2;height:100%;min-height:0;overflow:hidden;position:relative!important;inset:auto!important;z-index:5!important;width:100%!important;max-width:none!important;border-left:1px solid var(--border);border-bottom:0;padding:0;display:flex!important;flex-direction:column!important;background:var(--bg-surface);align-self:stretch}
  body.display-sides #catalogMain{grid-column:2;grid-row:2;min-width:0;min-height:0;height:100%;align-self:stretch;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;touch-action:pan-y;padding:0 0 2rem;background:var(--bg-surface);border:1px solid var(--border);border-top:0;box-sizing:border-box}
  body.display-sides #catalogMain{position:relative;display:flex;flex-direction:column;align-items:stretch}
  body.display-sides #catalogMain .catalog-body,body.display-sides #catalogMain .entry,body.display-sides #catalogMain .path,body.display-sides #catalogMain .path code{min-width:0;max-width:100%;overflow-wrap:anywhere;word-break:break-word}
  body.display-sides #catalogMain .path .folder{white-space:normal;overflow-wrap:anywhere}
  body.display-sides #catalogMain .catalog-body{padding-left:1rem;padding-right:1rem}
  body.display-sides > p,body.display-sides #searchHeight,body.display-sides .search-height{display:none!important}
  body.display-sides:not(.layout-edit) #kwShadeHeight{display:none!important}
  body.display-sides.layout-edit #kwShadeHeight{display:block!important;position:absolute;left:0;right:0;bottom:0;z-index:6}
  body.display-sides #filterWrap{height:100%!important;max-height:none!important;align-self:stretch}
  body.display-sides #filterWrap.open .filter-panel,body.display-sides #filterWrap.kw-shade-height-set.open .filter-panel{display:flex!important;flex-direction:column;flex:1 1 auto!important;min-height:0!important;max-height:none!important}
  body.display-sides #filterWrap .filter-top,body.display-sides #filterWrap .filter-kw-tools,body.display-sides #filterWrap .mode-switch,body.display-sides #filterWrap .cat-switch,body.display-sides #filterWrap .kwstatus{flex:0 0 auto}
  body.display-sides #filterWrap .cat-switch{flex-wrap:wrap!important;overflow:visible;height:auto;min-width:0;width:100%;align-content:flex-start}
  body.display-sides #kwbar{flex:1 1 auto!important;min-height:0;max-height:none!important;overflow-x:hidden!important;overflow-y:auto!important;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;touch-action:pan-y;align-content:flex-start;flex-wrap:wrap}
  body.display-sides #catalogMain{padding-top:0}
  body.display-sides .index,body.display-sides #catalogIndexList{columns:none!important;column-width:auto!important;column-count:1!important;column-fill:auto!important}
  body.display-sides #catalogIndex{position:sticky;top:0;z-index:12;box-sizing:border-box;width:auto;max-width:100%;margin:var(--sides-pane-gap,6px);display:flex;flex-direction:column;height:var(--sides-index-h,min(48dvh,28rem));max-height:min(70dvh,40rem);min-height:0;flex-shrink:0;overflow:hidden;border:1px solid var(--border);border-radius:0 0 10px 10px;background:var(--bg-surface);box-shadow:0 10px 24px rgba(0,0,0,.32)}
  body.display-sides #catalogIndex #indexHeight{display:none;box-sizing:border-box;position:absolute;z-index:22;left:0;right:0;bottom:0;width:100%;height:.75rem;margin:0;padding:0;border:0;background:transparent;cursor:ns-resize;touch-action:none;-webkit-user-select:none;user-select:none}
  body.display-sides #catalogIndex #indexHeight::before{content:"";position:absolute;left:28%;right:28%;top:3px;height:4px;background:var(--border);border-radius:2px;pointer-events:none}
  body.display-sides.layout-edit:not(.mode-layout-pinned) #catalogIndex #indexHeight{display:block!important;pointer-events:auto!important}
  body.display-sides #catalogIndex .catalog-index-head{flex:0 0 auto;margin:0;padding:.45rem .7rem;cursor:default;border-bottom:1px solid var(--border);user-select:none;min-width:0;position:relative;z-index:12}
  body.display-sides #catalogIndex .catalog-index-title{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  body.display-sides #catalogIndex.is-collapsed{height:auto!important;max-height:none}
  body.display-sides #catalogIndex.is-collapsed .catalog-index-head{border-bottom:0}
  body.display-sides #catalogIndex:not(.is-collapsed) .index,body.display-sides #catalogIndex:not(.is-collapsed) #catalogIndexList{display:grid!important;grid-template-columns:repeat(auto-fill,minmax(min(12rem,100%),1fr));grid-auto-flow:row;align-items:start;align-content:start;grid-auto-rows:min-content;flex:1 1 auto;min-height:0;width:100%;max-width:100%;box-sizing:border-box;margin:0;padding:.4rem .7rem .75rem;overflow-x:hidden!important;overflow-y:auto!important;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;touch-action:pan-y;columns:none!important;column-width:auto!important;column-count:1!important;column-fill:auto!important;list-style:none;padding-left:.95rem;gap:.15rem 1rem}
  body.display-sides #catalogIndex.is-collapsed .index,body.display-sides #catalogIndex.is-collapsed #catalogIndexList{display:none!important;height:0!important;min-height:0!important;overflow:hidden!important;padding:0!important;border:0!important}
  body.display-sides #catalogIndex .index li{display:flex!important;align-items:flex-start;gap:.3em;box-sizing:border-box;margin:.12rem 0;padding:0;max-width:100%;min-width:0;min-height:1.4em;line-height:1.35;overflow:hidden;isolation:isolate;position:relative;z-index:0;white-space:normal;overflow-wrap:anywhere;word-break:break-word;list-style:none}
  body.display-sides #catalogIndex .index li::before{content:"•";flex:0 0 auto;width:.7em;line-height:1.35;color:var(--text);pointer-events:none}
  body.display-sides #catalogIndex .index a{flex:1 1 auto;min-width:0;max-width:100%;overflow:hidden;white-space:normal;overflow-wrap:anywhere;word-break:break-word;display:block;-webkit-line-clamp:unset;line-clamp:unset;max-height:calc(1.35em * var(--index-name-lines,2));line-height:1.35;vertical-align:top}
  body.display-sides #catalogIndex.is-embedded{position:static!important;height:auto!important;max-height:none!important;box-shadow:none;border-radius:8px}
  body.display-sides #catalogIndex.is-embedded:not(.is-collapsed) .index,body.display-sides #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList{height:auto!important;max-height:none!important;overflow:visible!important;flex:0 0 auto}
  body.display-sides #catalogIndex.is-embedded #indexHeight{display:none!important}
  body.display-sides.layout-edit #catalogIndex .index,body.display-sides.layout-edit #catalogIndex #catalogIndexList{padding-bottom:1.05rem}
  body.display-sides #catalogIndex #catalogIndexList::-webkit-scrollbar{width:3px}  body.display-sides #catalogIndex #catalogIndexList::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}  body.display-sides #catalogIndex #catalogIndexList{scrollbar-width:thin} /* fix-DS: thin inner scrollbar so it doesn't double up with catalogMain scrollbar */
/* fix-SB: no scrollbar chrome — content still scrollable */*::-webkit-scrollbar{display:none!important}*{scrollbar-width:none!important;-ms-overflow-style:none!important}
  body.display-sides a.bottom,body.display-sides a.top{display:inline-flex!important;align-items:center;justify-content:center;position:sticky!important;z-index:26;float:none;clear:none;align-self:flex-end;flex:0 0 auto;box-sizing:border-box;margin-right:.6rem}
  #catalogJumpStack{display:none}
  body.display-sides #catalogJumpStack{position:fixed;z-index:40;display:flex;flex-direction:column;align-items:flex-end;gap:.35rem;pointer-events:auto}
  body.display-sides #catalogJumpStack>a.top,body.display-sides #catalogJumpStack>a.bottom{position:relative!important;top:auto!important;bottom:auto!important;margin:0!important;pointer-events:auto;z-index:40}
  body.display-sides #filterWrap.open .filter-panel,body.display-sides #filterWrap.kw-shade-height-set.open .filter-panel{position:static!important;max-height:none!important;flex:1 1 auto;min-height:0;overflow-y:auto!important;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;touch-action:pan-y;width:auto!important;box-shadow:none;border:0}
  body.display-sides #kwbar{flex:1 1 auto!important;min-height:0;max-height:none!important;overflow-x:hidden!important;overflow-y:auto!important;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;touch-action:pan-y;align-content:flex-start;flex-wrap:wrap}
  body.display-sides #acShell,body.display-sides #acShell.open{position:relative!important;inset:auto!important;width:auto!important;flex:1 1 0%!important;min-height:0!important;max-height:none;overflow:hidden!important;display:flex!important;flex-direction:column!important;box-shadow:none;border:0}body.display-sides #acList.search-autocomplete,body.display-sides #acList.search-autocomplete.open{position:relative!important;inset:auto!important;width:auto!important;flex:1 1 0%!important;min-height:0!important;max-height:none!important;overflow-x:hidden!important;overflow-y:auto!important;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;touch-action:pan-y;box-shadow:none;border:0;scrollbar-width:none!important;-ms-overflow-style:none!important}
  body.display-sides.kw-fs-open #filterWrap,body.display-sides.ac-fs-open #acShell.ac-fs{position:relative!important;inset:auto!important;width:auto!important;height:auto!important}
  body.display-sides #searchSplit,body.display-sides #dualFsSep{display:none}
  body.display-sides.layout-edit #searchSplit,body.display-sides.layout-edit #dualFsSep{display:block!important;position:fixed!important;z-index:80!important;width:12px!important;min-width:12px!important;max-width:12px!important;transform:none!important;margin:0;padding:0;cursor:col-resize;pointer-events:auto!important}
  body.display-sides:not(.layout-edit) #searchSplit,body.display-sides:not(.layout-edit) #dualFsSep{display:none!important}
  body.display-sides.search-chrome-collapsed.layout-edit #searchSplit{display:none!important}
  body.display-sides.kw-chrome-collapsed.layout-edit #dualFsSep{display:none!important}
  body.display-sides.sides-pinned #searchSplit,body.display-sides.sides-pinned #dualFsSep,body.mode-layout-pinned #searchSplit,body.mode-layout-pinned #dualFsSep,body.mode-layout-pinned #indexHeight{cursor:default!important;pointer-events:none!important}
  body.display-sides #dualFsSep .dual-fs-sep-pin,body #fsSepPinBtn{display:none!important}
 }
 body.display-upper .catalog-header{position:sticky;top:0;z-index:320;background:var(--bg-surface)}
 body.display-upper.search-mode .search-chrome{position:sticky;top:var(--cat-header-h,3.5rem);z-index:220;overflow:hidden!important;align-items:stretch;background:var(--bg-surface);grid-template-rows:minmax(0,1fr)}
 body.display-upper.search-mode .search-col{display:flex;flex-direction:column;min-height:0;max-height:100%;overflow:hidden}
 body.display-upper.search-mode #filterWrap,body.display-upper.search-mode #filterWrap.open{min-height:0;max-height:100%;overflow:hidden}
 body.display-upper.search-mode #acShell,body.display-upper.search-mode #acShell.open,body.display-upper.search-mode #acList,body.display-upper.search-mode #acList.open{position:relative!important;inset:auto!important;flex:1 1 auto;min-height:0;overflow:auto!important}
 body.display-upper.search-mode #filterWrap.open .filter-panel,body.display-upper.search-mode #kwbar{overflow:auto!important}
 body.display-upper.pick-mode .search-chrome{position:sticky;top:var(--cat-header-h,3.5rem);z-index:220;overflow:hidden!important;background:var(--bg-surface)}
 body.display-upper.pick-mode #filterWrap,body.display-upper.pick-mode #filterWrap.open{min-height:0;max-height:100%;overflow:hidden}
 body.display-upper.pick-mode #filterWrap.open .filter-panel,body.display-upper.pick-mode #kwbar{overflow:auto!important}
 body.pick-mode:not(.display-sides) .filter-wrap{position:relative;top:auto;z-index:auto;width:100%;max-width:100%;min-width:0}
 body.layout-edit:not(.mode-layout-pinned) .ac-height,body.layout-edit:not(.mode-layout-pinned) .ac-width,body.layout-edit:not(.mode-layout-pinned) .kw-shade-height,body.layout-edit:not(.mode-layout-pinned) .search-height,body.layout-edit:not(.mode-layout-pinned) .search-split,body.layout-edit:not(.mode-layout-pinned) #indexHeight{pointer-events:auto!important;z-index:80}
 body.layout-edit:not(.mode-layout-pinned) .ac-height::before,body.layout-edit:not(.mode-layout-pinned) .ac-width::before,body.layout-edit:not(.mode-layout-pinned) .kw-shade-height::before,body.layout-edit:not(.mode-layout-pinned) .search-height::before{opacity:1}
 body.display-sides:not(.kw-open):not(.kw-chrome-collapsed){grid-template-columns:var(--sides-lw,22vw) minmax(0,1fr) max-content}
 body.display-sides.search-chrome-collapsed:not(.kw-open):not(.kw-chrome-collapsed){grid-template-columns:minmax(0,1fr) max-content}
 body.display-sides:not(.kw-open):not(.kw-chrome-collapsed) #filterWrap{width:auto!important;min-width:0;height:auto!important;max-height:none!important;align-self:start;overflow:visible}
 body.display-sides.kw-chrome-collapsed{grid-template-columns:var(--sides-lw,22vw) minmax(0,1fr)}
 body.display-sides.search-chrome-collapsed.kw-chrome-collapsed{grid-template-columns:minmax(0,1fr)}
 body.display-sides.kw-chrome-collapsed #filterWrap{display:none!important;width:0!important;min-width:0!important;max-width:0!important;overflow:hidden!important;border:0!important;padding:0!important;height:0!important}
 body.display-fs:not(.kw-fs-open) #filterWrap{position:relative!important;inset:auto!important;height:auto!important;max-height:none!important;width:auto!important}
 body.display-upper .fs-stripe-wrap,body.display-upper .fs-mode-nav,body.display-fs .fs-mode-nav{display:none!important}
 body.display-upper .search-strip-fs,body.display-upper .kw-fs-btn{display:inline-flex!important}
 body.display-upper .ac-companion-btn,body.display-upper .kw-companion-btn{display:none!important}
 body.display-upper #catalogIndex,body.display-fs #catalogIndex{position:static;height:auto;max-height:none;overflow:visible;border:0;box-shadow:none;display:block}
 body.display-upper #catalogIndex .index,body.display-upper #catalogIndex #catalogIndexList,body.display-fs #catalogIndex .index,body.display-fs #catalogIndex #catalogIndexList{column-width:clamp(14rem,28vw,18rem)!important;column-count:3!important;column-fill:balance!important;height:auto!important;max-height:none!important;overflow:visible!important}
 body.display-fs:not(.dual-fs-open) #dualFsSep{display:none!important}
 body.display-fs.kw-fs-open .filter-kw-tools{display:flex!important;flex-wrap:wrap;gap:.35rem}
 body.display-fs.kw-fs-open .filter-panel>.mode-switch{display:flex!important;flex-wrap:wrap}
 body.display-fs.ac-fs-open #acShell.ac-fs{height:var(--fs-ac-h,calc(100dvh - var(--cat-header-h,3.5rem)))!important;max-height:var(--fs-ac-h,none);bottom:auto!important}
 body.display-fs.kw-fs-open #filterWrap{height:var(--fs-kw-h,calc(100dvh - var(--cat-header-h,3.5rem)))!important;max-height:var(--fs-kw-h,none);bottom:auto!important}
 .filter-top #layoutEditBtn,.filter-top #modePinBtn{flex:0 0 auto;display:inline-flex!important}
 .filter-wrap:not(.open)>.filter-top #layoutEditBtn,.filter-wrap:not(.open)>.filter-top #modePinBtn{display:inline-flex!important}
 body.mode-layout-pinned.layout-edit .search-split,body.mode-layout-pinned.layout-edit .search-height,body.mode-layout-pinned.layout-edit .ac-height,body.mode-layout-pinned.layout-edit .kw-shade-height,body.mode-layout-pinned.layout-edit #searchSplit,body.mode-layout-pinned.layout-edit #dualFsSep,body.mode-layout-pinned.layout-edit #indexHeight{cursor:default!important;pointer-events:none!important}
 body.display-fs .catalog-header{position:relative;z-index:300;background:var(--bg-surface)}
 body.display-fs.kw-fs-open #filterWrap{top:var(--cat-header-h,3.5rem)!important;height:calc(100dvh - var(--cat-header-h,3.5rem))!important;bottom:0!important}
 body.display-fs.ac-fs-open #acShell.ac-fs{top:var(--cat-header-h,3.5rem)!important;height:calc(100dvh - var(--cat-header-h,3.5rem))!important}
 body.display-fs.dual-fs-open #dualFsSep{top:var(--cat-header-h,3.5rem)!important}
 .fs-stripe-panel:not(.stripe-open){visibility:hidden!important;pointer-events:none!important;max-width:0!important;padding:0!important}
/* fix-UPPER-SEP: Upper portrait — sticky menus, scrollable catalog below (no grid override) */
@media(orientation:portrait){
  body.display-upper.search-mode .search-chrome{max-height:var(--upper-portrait-menu-h,45dvh)!important;overflow:hidden!important}
  body.display-upper #catalogMain{margin-top:.35rem}
}
/* fix-DESK-CHROME: layout tools centered in header; 4 layout scopes; no Lock */
.catalog-header{display:grid!important;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);align-items:center;column-gap:.5rem;row-gap:.35rem;min-width:0;position:relative}
.catalog-header h1{grid-column:1;grid-row:1;justify-self:start;z-index:1;min-width:0;max-width:100%;margin:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.hdr-cluster{grid-column:2;grid-row:1;justify-self:center;display:flex;align-items:center;gap:.5rem;flex-wrap:nowrap;min-width:0;max-width:100%;position:relative;z-index:2}
.catalog-header::after{content:'';grid-column:3;grid-row:1}
.hdr-layout-btns{display:flex;align-items:center;gap:4px;flex:0 1 auto;margin-left:0;min-width:0}
.catalog-header #clearMissBtn,.hdr-cluster>#clearMissBtn{flex:0 0 auto;display:inline-flex;align-items:center;justify-content:center;min-height:2.25rem;position:relative;z-index:2}
body.display-sides .catalog-header #clearMissBtn,body.display-sides.display-middle .catalog-header #clearMissBtn{display:inline-flex!important}
.hdr-end{margin-left:0;display:flex;align-items:center;gap:.5rem;min-width:0;flex:0 0 auto}
.catalog-header .hdr-menu-btns,.hdr-cluster .hdr-menu-btns{margin-left:0;flex:0 0 auto}
.hdr-layout-btns .layout-presets{width:auto;max-width:none;padding:0;flex-wrap:nowrap;gap:4px}
.hdr-layout-btns .layout-edit-btn,.hdr-layout-btns .layout-presets-btn,.hdr-layout-btns .ui-scale-step,.hdr-layout-btns .ui-scale-readout,.catalog-header #clearMissBtn{min-height:2.25rem}
#hdrSearchBtn{font-weight:600;font-size:.875rem}
.filter-panel>.mode-switch{display:none!important}
@media(orientation:portrait){.catalog-header{grid-template-rows:auto auto}.catalog-header h1{grid-column:1/-1;grid-row:1;max-width:100%}.hdr-cluster{grid-column:2;grid-row:2;flex-wrap:wrap;justify-content:center}.catalog-header::after{grid-column:3;grid-row:2}}
#modePinBtn,.mode-pin-btn{display:none!important}
#layoutDefaultBtn{display:none!important}
.search-only-scale,#searchOnlyScale,#searchStripMore,#searchStripMorePop{display:none!important}
.catalog-header .theme-picker{margin-left:0}
#searchStrip .ac-history-wrap{display:inline-flex;flex:0 0 auto;align-items:center;margin:0}
.layout-presets-tabs{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.layout-presets-tab{font-size:.75rem;line-height:1.15;min-height:2.5rem}
.layout-presets-pop{min-width:min(340px,calc(100vw - 16px));max-width:min(480px,calc(100vw - 16px))}
.layout-restore-defaults{display:block;width:100%;box-sizing:border-box;min-height:2.25rem;margin:0 0 8px;padding:0 .625rem;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text);font:inherit;cursor:pointer;touch-action:manipulation}
.layout-restore-defaults:hover{border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg)}
/* fix-SIDES-ONLY: Upper and Full removed — Sides handles all orientations */
.display-btn[data-display="upper"],.display-btn[data-display="fs"]{display:none!important}
/* fix-NO-FS: leftover Full-mode chrome — Sides is the only display */
.search-strip-fs,.kw-fs-btn,.ac-fs-back,.kw-fs-back,.ac-companion-btn,.kw-companion-btn,.fs-stripe-wrap,
body.display-sides .search-strip-fs,body.display-sides .kw-fs-btn,
body.display-sides:not(.search-chrome-collapsed) .search-strip-fs,
body.display-upper .search-strip-fs,body.display-upper .kw-fs-btn,
body.display-fs .search-strip-fs{display:none!important}
/* fix-MOBILE-SIDES: single-column Sides on mobile */
@media(max-width:899px){
  body.display-sides{display:flex!important;flex-direction:column!important;height:100dvh;overflow:hidden}
  body.display-sides .catalog-header{flex:0 0 auto;position:sticky;top:0;z-index:320;background:var(--bg-surface)}
  body.display-sides #searchChrome{flex:0 0 auto;height:auto!important;max-height:min(38dvh,20rem)!important;overflow:hidden!important;border-right:0!important;display:flex!important;flex-direction:column!important}body.display-sides #searchCol,body.display-sides #searchCol .search-strip-anchor{flex:1 1 auto;min-height:0;display:flex;flex-direction:column;overflow:hidden;max-height:100%}
  body.display-sides #filterWrap{position:fixed!important;right:0;top:var(--cat-header-h,3.5rem);bottom:0;width:min(88vw,22rem)!important;max-width:100vw!important;z-index:310;transform:translateX(110%);transition:transform 0.28s cubic-bezier(0.4,0,0.2,1);border-left:1px solid var(--border)!important;background:var(--bg-surface);height:auto!important;max-height:none!important;overflow-y:auto!important;padding:0;box-shadow:-4px 0 12px rgba(0,0,0,0.35)}
  body.display-sides.kw-open #filterWrap{transform:translateX(0)!important}
  body.display-sides #catalogMain{flex:1 1 auto;min-height:0;overflow-y:auto!important;overflow-x:hidden;padding:0 0 2rem}
  body.display-sides #searchSplit,body.display-sides #dualFsSep{display:none!important}
  body.display-sides #catalogIndex{position:static!important;height:auto!important;max-height:min(32dvh,16rem)!important;overflow:hidden!important;display:flex!important;flex-direction:column}
  body.display-sides #catalogIndex:not(.is-collapsed) #catalogIndexList{display:grid!important;grid-template-columns:repeat(auto-fill,minmax(min(10.5rem,100%),1fr));grid-auto-flow:row;flex:1 1 auto;min-height:0;overflow-y:auto!important;columns:none!important;column-count:1!important;list-style:none;padding:.35rem .6rem .6rem .85rem;gap:.2rem .75rem}
  body.display-sides #catalogIndex .index li{display:flex!important;align-items:flex-start;gap:.3em;min-height:1.35em;line-height:1.35;overflow:hidden;isolation:isolate;position:relative;white-space:normal;overflow-wrap:anywhere}
  body.display-sides a.top,body.display-sides a.bottom{right:auto}
}

/* fix-MOBILE-PROGRESS: desktop chrome that fits a phone — never 3 panes */
@media(max-width:899px),(hover:none) and (pointer:coarse){
  body .search-strip-fs,body .kw-fs-btn,
  body.display-sides .search-strip-fs,body.display-sides .kw-fs-btn,
  body.display-sides:not(.search-chrome-collapsed) .search-strip-fs,
  body.catalog-portable .search-strip-fs{display:inline-flex!important}
  body.kw-fs-open .kw-fs-btn,body.ac-fs-open .search-ac-shell.ac-fs>.search-strip .search-strip-fs{display:none!important}
  body.ac-fs-open .ac-fs-back,body.kw-fs-open .kw-fs-back{display:inline-flex!important}
  body .ac-companion-btn,body .kw-companion-btn,body .fs-stripe-wrap,body .fs-mode-nav,
  body.ac-fs-open .kw-companion-btn,body.kw-fs-open .ac-companion-btn,
  body.ac-fs-open .fs-stripe-wrap,body.kw-fs-open .fs-stripe-wrap{display:none!important}
  body.display-sides #searchSplit,body.display-sides #dualFsSep,body.dual-fs-open #dualFsSep{display:none!important}
  body.display-sides.display-middle{
    display:flex!important;flex-direction:column!important;
    grid-template-columns:none!important;grid-template-rows:none!important
  }
  body.display-sides.display-middle .catalog-header{flex:0 0 auto;position:sticky;top:0;z-index:320}
  body.display-sides.display-middle #searchChrome{
    flex:0 1 auto;width:100%!important;max-height:min(32dvh,15rem)!important;
    border-right:0!important;border-bottom:1px solid var(--border)!important
  }
  body.display-sides.display-middle #filterWrap,
  body.display-sides.display-middle.kw-open #filterWrap{
    position:relative!important;inset:auto!important;right:auto!important;top:auto!important;bottom:auto!important;
    transform:none!important;width:100%!important;max-width:100%!important;
    max-height:min(32dvh,15rem)!important;flex:0 1 auto;z-index:6!important;
    box-shadow:none!important;border-left:0!important;border-top:1px solid var(--border)!important
  }
  body.display-sides.display-middle.kw-chrome-collapsed #filterWrap,
  body.display-sides.display-middle:not(.kw-open) #filterWrap{display:none!important}
  body.display-sides.display-middle.search-chrome-collapsed #searchChrome{display:none!important}
  body.display-sides.display-middle #catalogMain{flex:1 1 auto;min-height:0;width:100%!important}
  body.kw-fs-open:not(.dual-fs-open) #filterWrap,
  body.display-sides.kw-fs-open:not(.dual-fs-open) #filterWrap,
  body.display-sides.display-middle.kw-fs-open:not(.dual-fs-open) #filterWrap{
    position:fixed!important;top:var(--cat-header-h,3.5rem)!important;left:0!important;right:0!important;bottom:0!important;
    width:100%!important;max-width:none!important;max-height:none!important;height:auto!important;
    transform:none!important;z-index:340!important;box-shadow:none!important;overflow:auto!important
  }
  body.ac-fs-open:not(.dual-fs-open) #acShell.ac-fs,
  body.display-sides.ac-fs-open:not(.dual-fs-open) #acShell.ac-fs{
    position:fixed!important;top:var(--cat-header-h,3.5rem)!important;left:0!important;right:0!important;bottom:0!important;
    width:100%!important;max-width:none!important;height:auto!important;max-height:none!important;z-index:340!important
  }
}
@media(max-width:899px) and (orientation:portrait),(hover:none) and (pointer:coarse) and (orientation:portrait){
  body.dual-fs-open #acShell.ac-fs,body.display-sides.dual-fs-open #acShell.ac-fs{
    position:fixed!important;top:var(--cat-header-h,3.5rem)!important;left:0!important;right:0!important;bottom:50%!important;
    width:100%!important;height:auto!important;max-height:none!important;z-index:340!important
  }
  body.dual-fs-open #filterWrap,body.display-sides.dual-fs-open #filterWrap{
    position:fixed!important;top:50%!important;left:0!important;right:0!important;bottom:0!important;
    width:100%!important;max-width:none!important;transform:none!important;z-index:341!important;box-shadow:none!important
  }
}
@media(max-width:899px) and (orientation:landscape),(hover:none) and (pointer:coarse) and (orientation:landscape){
  body.dual-fs-open #acShell.ac-fs,body.display-sides.dual-fs-open #acShell.ac-fs{
    position:fixed!important;top:var(--cat-header-h,3.5rem)!important;left:0!important;right:50%!important;bottom:0!important;
    width:auto!important;height:auto!important;z-index:340!important
  }
  body.dual-fs-open #filterWrap,body.display-sides.dual-fs-open #filterWrap{
    position:fixed!important;top:var(--cat-header-h,3.5rem)!important;left:50%!important;right:0!important;bottom:0!important;
    width:auto!important;max-width:none!important;transform:none!important;z-index:341!important;box-shadow:none!important
  }
}

.hdr-more-btn,.hdr-more-pop,.kw-strip-more,.kw-strip-more-pop{display:none}
/* fix-MOBILE-PIN-SHEET: phone-only pin sheet + toolbar overflow */
@media(max-width:899px),(hover:none) and (pointer:coarse){
  body .hdr-more-btn,body .kw-strip-more{display:inline-flex!important;flex:0 0 auto;align-items:center;justify-content:center;min-width:2.75rem;min-height:2.75rem;padding:0 .45rem;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text);font:inherit;cursor:pointer}
  body .hdr-cluster .hdr-layout-btns,body .catalog-header .theme-picker,
  body .catalog-header #clearMissBtn,body.display-sides .catalog-header #clearMissBtn,
  body.display-sides.display-middle .catalog-header #clearMissBtn{display:none!important}
  body .hdr-more-pop .theme-picker{display:block!important;width:100%;max-width:none;min-height:2.75rem;margin:0}
  body .hdr-more-pop,body .kw-strip-more-pop,body #searchStripMorePop{
    position:absolute;z-index:360;display:flex;flex-direction:column;gap:.35rem;min-width:min(18rem,calc(100vw - 1.5rem));
    padding:.5rem;background:var(--bg-surface);border:1px solid var(--border);border-radius:8px;box-shadow:0 12px 28px rgba(0,0,0,.38)
  }
  body .hdr-more-pop{top:calc(100% + 4px);right:0;left:auto}
  body .kw-strip-more-pop{top:calc(100% + 4px);right:.35rem}
  body #searchStripMorePop{right:.35rem;top:calc(100% + 4px);left:auto}
  body .hdr-more-pop[hidden],body .kw-strip-more-pop[hidden],body #searchStripMorePop[hidden]{display:none!important}
  body .hdr-more-pop button,body .kw-strip-more-pop button,body #searchStripMorePop button{
    min-height:2.75rem;text-align:left;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text);padding:.35rem .6rem;cursor:pointer;font:inherit
  }
  body .hdr-cluster{flex-wrap:wrap;overflow:visible;position:relative;justify-content:center}
  body #searchStripMore{display:inline-flex!important;margin-left:auto}
  body .search-strip .search-strip-clear,body .search-strip #searchHistoryWrap,body .search-strip .search-only-scale,body #searchOnlyScale{display:none!important}
  body .filter-top{position:relative;flex-wrap:nowrap;gap:.35rem}
  body .filter-kw-tools{display:none!important}
  body #cardMinDock.card-min-phone{
    flex-direction:column;justify-content:flex-end;align-items:stretch;padding:0;overflow:visible;pointer-events:none;left:0!important;width:100%!important
  }
  body #cardMinDock.card-min-phone .card-min-sheet{
    pointer-events:auto;display:flex;flex-direction:column;min-width:0;max-height:min(58dvh,28rem);
    background:var(--bg-surface);border-top:1px solid var(--border);border-radius:14px 14px 0 0;
    box-shadow:0 -10px 32px rgba(0,0,0,.4);padding:.15rem .7rem max(.55rem,env(safe-area-inset-bottom))
  }
  body #cardMinDock.card-min-phone .card-min-sheet-bar{display:flex;align-items:center;gap:.45rem;min-height:2.85rem;flex:0 0 auto}
  body #cardMinDock.card-min-phone .card-min-sheet-handle{
    flex:1 1 auto;min-width:0;min-height:2.75rem;display:inline-flex;align-items:center;justify-content:center;gap:.45rem;
    border:1px solid var(--border);border-radius:999px;background:var(--bg-card);color:var(--text);font:inherit;font-weight:650;cursor:pointer
  }
  body #cardMinDock.card-min-phone .card-min-sheet-grip{width:2.2rem;height:.28rem;border-radius:999px;background:var(--border)}
  body #cardMinDock.card-min-phone .card-min-save{position:static!important;left:auto!important;right:auto!important;bottom:auto!important;top:auto!important;flex:0 0 auto;box-shadow:none}
  body #cardMinDock.card-min-phone .card-min-stack{display:none!important}
  body #cardMinDock.card-min-phone:not(.is-sheet-open) .card-min-list{display:none}
  body #cardMinDock.card-min-phone.is-sheet-open .card-min-list{
    display:flex;flex-direction:column;gap:.4rem;overflow-y:auto;-webkit-overflow-scrolling:touch;min-height:0;padding:.15rem 0 .35rem
  }
  body #cardMinDock.card-min-phone .card-min-pill{max-width:none!important;width:100%;flex:0 0 auto}
  body #cardMinDock.card-min-phone #cardMinSavePop{left:auto;right:.7rem;transform:none;bottom:calc(100% + .4rem)}
  body.has-card-min-dock #catalogMain{padding-bottom:calc(var(--card-min-dock-h,3.25rem) + .5rem)}
}
/* fix-PORTRAIT-SIDES: desktop portrait A/B — stacked menus left or right, content the other side */
body.display-sides:not(.sides-orient-portrait) .layout-presets-tabs{display:none!important}
@media(min-width:900px) and (orientation:portrait){
  body.display-sides{
    grid-template-columns:var(--portrait-lw,38%) minmax(0,1fr)!important;
    grid-template-rows:auto minmax(0,var(--portrait-menu-h,1fr)) minmax(0,1fr)!important
  }
  body.display-sides.sides-portrait-flip{
    grid-template-columns:minmax(0,1fr) var(--portrait-lw,38%)!important
  }
  body.display-sides.search-chrome-collapsed:not(.kw-chrome-collapsed),
  body.display-sides.kw-chrome-collapsed:not(.search-chrome-collapsed){
    grid-template-rows:auto minmax(0,1fr)!important
  }
  body.display-sides.search-chrome-collapsed.kw-chrome-collapsed,
  body.display-sides.sides-portrait-flip.search-chrome-collapsed.kw-chrome-collapsed{
    grid-template-columns:minmax(0,1fr)!important;
    grid-template-rows:auto minmax(0,1fr)!important
  }
  body.display-sides .catalog-header{grid-column:1/-1;grid-row:1}
  body.display-sides #searchChrome{
    grid-column:1!important;grid-row:2!important;
    height:auto!important;max-height:none!important;min-height:0;
    border-right:1px solid var(--border)!important;border-left:0!important;
    border-bottom:1px solid var(--border)!important;overflow:hidden!important
  }
  body.display-sides #filterWrap{
    grid-column:1!important;grid-row:3!important;
    height:100%!important;max-height:none!important;min-height:0;align-self:stretch;
    border-left:0!important;border-right:1px solid var(--border)!important;
    overflow:hidden!important
  }
  body.display-sides #catalogMain{
    grid-column:2!important;grid-row:2/-1!important;
    min-height:0;height:100%;align-self:stretch;overflow-y:auto!important;overflow-x:hidden;padding:0 0 2rem
  }
  body.display-sides.sides-portrait-flip #searchChrome{
    grid-column:2!important;
    border-right:0!important;border-left:1px solid var(--border)!important
  }
  body.display-sides.sides-portrait-flip #filterWrap{
    grid-column:2!important;
    border-right:0!important;border-left:1px solid var(--border)!important
  }
  body.display-sides.sides-portrait-flip #catalogMain{grid-column:1!important}
  body.display-sides.search-chrome-collapsed #filterWrap{grid-row:2/-1!important;border-bottom:0!important}
  body.display-sides.kw-chrome-collapsed #searchChrome{grid-row:2/-1!important;border-bottom:0!important}
  body.display-sides.search-chrome-collapsed.kw-chrome-collapsed,
  body.display-sides.sides-portrait-flip.search-chrome-collapsed.kw-chrome-collapsed{
    grid-template-columns:minmax(0,1fr)!important;
    grid-template-rows:auto minmax(0,1fr)!important
  }
  body.display-sides.search-chrome-collapsed.kw-chrome-collapsed #catalogMain{grid-column:1/-1!important;grid-row:2!important}
  body.display-sides.layout-edit #searchSplit{
    width:auto!important;min-width:0!important;max-width:none!important;
    height:12px!important;cursor:ns-resize!important
  }
  body.display-sides.layout-edit #dualFsSep{cursor:ew-resize!important}
  body.display-sides.search-chrome-collapsed.layout-edit #searchSplit,
  body.display-sides.kw-chrome-collapsed.layout-edit #searchSplit{display:none!important}
  body.display-sides.kw-chrome-collapsed.layout-edit:not(.search-chrome-collapsed) #dualFsSep,
  body.display-sides.search-chrome-collapsed.layout-edit:not(.kw-chrome-collapsed) #dualFsSep{display:block!important}
  body.display-sides.search-chrome-collapsed.kw-chrome-collapsed.layout-edit #dualFsSep{display:none!important}
  body.display-sides #filterWrap.open .filter-panel{max-height:none!important;flex:1 1 auto;min-height:0;overflow-y:auto!important}
  body.display-sides a.top,body.display-sides.sides-portrait-flip a.top,body.display-sides a.bottom,body.display-sides.sides-portrait-flip a.bottom{right:auto}
  body.display-sides.layout-edit #dualFsSep::before,body.display-sides.layout-edit #searchSplit::before{
    content:'';display:block;
    background:var(--border,rgba(128,128,128,0.5));border-radius:2px;
    opacity:.6;transition:opacity .15s;position:absolute;top:50%;left:50%;transform:translate(-50%,-50%)
  }
  body.display-sides.layout-edit #dualFsSep::before{width:2px;height:24px}
  body.display-sides.layout-edit #searchSplit::before{width:24px;height:2px}
  body.display-sides.layout-edit #dualFsSep:hover::before,body.display-sides.layout-edit #searchSplit:hover::before{opacity:1}
}
/* fix-STREAM: toolbar-only open/close; unified search pills; remove redundant mode nav */
.search-strip-hide{display:none!important}
.filter-top .fs-mode-nav{display:none!important}
.mode-switch .mode-btn[data-mode="pick"],.mode-switch .mode-btn[data-mode="search"]{display:none!important}
/* fix-FULL-MODE-COMPACT
/* fix-STREAM: toolbar-only open/close; unified search pills; remove redundant mode nav */
.search-strip-hide{display:none!important}
.filter-top .fs-mode-nav{display:none!important}
.mode-switch .mode-btn[data-mode="pick"],.mode-switch .mode-btn[data-mode="search"]{display:none!important}

/* ── UPPER MODE: cap Index height to prevent void ──────────────────────────*/
body.display-upper #catalogIndex{max-height:min(28dvh,16rem)!important;overflow-y:auto!important;-webkit-overflow-scrolling:touch!important;border:1px solid var(--border);border-radius:0 0 8px 8px;margin-bottom:.5rem}
body.display-upper #catalogIndex.is-collapsed{max-height:none!important;overflow:visible!important}
body.display-upper #catalogIndex .index,body.display-upper #catalogIndex #catalogIndexList{max-height:none!important;overflow:visible!important}
/* ── SIDES MODE: remove gap above first card ─────────────────────────────── */
body.display-sides #catalogMain{padding-top:0!important}
body.display-sides #catalogMain .catalog-body{padding-top:.5rem!important}
.catalog-doc-note{margin:1rem 0 .35rem;padding:0;border:1px solid var(--border);border-radius:8px;background:var(--bg-surface);width:100%;max-width:100%;min-width:0;box-sizing:border-box;overflow-wrap:anywhere;word-break:break-word}
.catalog-doc-note-toggle{display:flex;align-items:center;gap:.45rem;width:100%;min-height:2.25rem;padding:.35rem .7rem;border:0;border-radius:8px;background:transparent;color:var(--text-muted);font:inherit;font-size:.875rem;font-weight:600;cursor:pointer;text-align:left;touch-action:manipulation}
.catalog-doc-note-toggle:hover{color:var(--accent-instrument);background:var(--accent-instrument-bg)}
.catalog-doc-note-toggle .toggle-arrow{display:inline-block;transition:transform .2s}
.catalog-doc-note.is-collapsed .catalog-doc-note-toggle .toggle-arrow{transform:rotate(-90deg)}
.catalog-doc-note-body{padding:.1rem .75rem .65rem;color:var(--text-muted);font-size:.875rem}
.catalog-doc-note-body p{display:block!important;margin:.35rem 0}
.catalog-doc-note.is-collapsed .catalog-doc-note-body{display:none}
body.display-sides #catalogMain .catalog-index,
body.display-sides #catalogMain .catalog-body,
body.display-sides #catalogMain .catalog-doc-note{align-self:stretch;width:auto;max-width:none;min-width:0;box-sizing:border-box}
body.display-sides #catalogMain .catalog-doc-note{margin:.75rem 0 1.25rem;flex:0 0 auto;overflow-wrap:anywhere;word-break:break-word}
body.display-sides #catalogMain .catalog-doc-note-body,
body.display-sides #catalogMain .catalog-doc-note-body p{max-width:100%;overflow-wrap:anywhere;word-break:break-word}
/* fix-SIDES-PANE: equal bottoms + tiny gutter that never collapses to 0 */
@media(min-width:900px){
  body.display-sides.search-chrome-collapsed:not(.kw-chrome-collapsed) #catalogMain{grid-column:1}
  body.display-sides.search-chrome-collapsed:not(.kw-chrome-collapsed) #filterWrap{grid-column:2}
  body.display-sides.search-chrome-collapsed.kw-chrome-collapsed #catalogMain{grid-column:1}
  body.display-sides.search-chrome-collapsed:not(.kw-open):not(.kw-chrome-collapsed) #catalogMain{grid-column:1}
  body.display-sides.search-chrome-collapsed:not(.kw-open):not(.kw-chrome-collapsed) #filterWrap{grid-column:2}
  body.display-sides #catalogMain,body.display-sides #searchChrome,body.display-sides.kw-open #filterWrap{height:100%;min-height:0;align-self:stretch}
  body.display-sides.kw-open:not(.kw-chrome-collapsed) #filterWrap{height:100%!important;max-height:none!important;align-self:stretch!important;margin-bottom:0!important;border-bottom:0!important;padding-bottom:0!important}
  body.display-sides.kw-open:not(.kw-chrome-collapsed) #filterWrap .filter-panel,body.display-sides.kw-open:not(.kw-chrome-collapsed) #filterWrap.open .filter-panel{display:flex!important;flex-direction:column!important;flex:1 1 auto!important;min-height:0!important;max-height:none!important;padding-bottom:0!important;margin-bottom:0!important}
  body.display-sides.kw-open:not(.kw-chrome-collapsed) #kwbar{flex:1 1 auto!important;min-height:0!important;margin-bottom:0!important;padding-bottom:0!important}
  body.display-sides.kw-open:not(.kw-chrome-collapsed) #kwstatus,body.display-sides.kw-open:not(.kw-chrome-collapsed) .kwstatus{margin:0!important;padding-bottom:max(.15rem,env(safe-area-inset-bottom,0px))!important}

  body.display-sides #catalogIndex:not(.is-embedded){width:auto;max-width:100%;margin:var(--sides-pane-gap,6px);flex-shrink:0}
}
@media(min-width:900px) and (orientation:portrait){
  body.display-sides{column-gap:var(--sides-pane-gap,6px)!important;row-gap:0!important}
  body.display-sides:not(.search-chrome-collapsed):not(.kw-chrome-collapsed) #searchChrome{margin-bottom:var(--sides-pane-gap,6px)!important}
  body.display-sides.kw-chrome-collapsed #searchChrome{margin-bottom:0!important}
  body.display-sides #catalogMain{height:100%!important;align-self:stretch!important}
}
/* fix-MIDDLE: Search | Keywords on top, catalog full-width below */
.display-btn[data-display="middle"]{display:inline-flex!important;align-items:center;justify-content:center;line-height:1}
body.display-sides.display-middle{
  display:grid!important;
  flex-direction:unset!important;
  grid-template-columns:minmax(0,var(--middle-lw,1fr)) minmax(0,var(--middle-rw,1fr))!important;
  grid-template-rows:auto var(--middle-menu-h,38dvh) minmax(0,1fr) var(--card-min-dock-h,0px)!important;
  column-gap:var(--sides-pane-gap,6px)!important;
  row-gap:0!important;
  height:100dvh;overflow:hidden;align-items:stretch
}
body.display-sides.display-middle.search-chrome-collapsed:not(.kw-chrome-collapsed),
body.display-sides.display-middle.kw-chrome-collapsed:not(.search-chrome-collapsed){
  grid-template-columns:minmax(0,1fr)!important
}
body.display-sides.display-middle.search-chrome-collapsed.kw-chrome-collapsed{
  grid-template-columns:minmax(0,1fr)!important;
  grid-template-rows:auto minmax(0,1fr)!important
}
body.display-sides.display-middle .catalog-header{grid-column:1/-1!important;grid-row:1!important}
body.display-sides.display-middle #searchChrome{
  grid-column:1!important;grid-row:2!important;
  height:100%!important;max-height:none!important;min-height:0;width:100%!important;
  border-right:1px solid var(--border)!important;border-bottom:1px solid var(--border)!important;border-left:0!important;
  overflow:hidden!important;position:relative!important;inset:auto!important;transform:none!important;
  display:flex!important;flex-direction:column!important;flex:unset!important;z-index:5
}
body.display-sides.display-middle.search-chrome-collapsed #searchChrome{display:none!important}
body.display-sides.display-middle #filterWrap{
  grid-column:2!important;grid-row:2!important;
  position:relative!important;inset:auto!important;right:auto!important;top:auto!important;bottom:auto!important;
  transform:none!important;width:100%!important;max-width:none!important;
  height:100%!important;max-height:none!important;z-index:5!important;
  box-shadow:none!important;border-left:1px solid var(--border)!important;border-right:0!important;
  overflow:hidden!important;display:flex!important;flex-direction:column!important
}
body.display-sides.display-middle.kw-open #filterWrap{transform:none!important}
body.display-sides.display-middle.kw-chrome-collapsed #filterWrap{display:none!important}
body.display-sides.display-middle.search-chrome-collapsed #filterWrap{grid-column:1/-1!important}
body.display-sides.display-middle.kw-chrome-collapsed #searchChrome{grid-column:1/-1!important}
body.display-sides.display-middle #catalogMain{
  grid-column:1/-1!important;grid-row:3!important;
  min-height:0;height:auto!important;align-self:stretch;
  overflow-y:auto!important;overflow-x:hidden;padding:0 0 2rem
}
body.display-sides.display-middle.search-chrome-collapsed.kw-chrome-collapsed #catalogMain{grid-column:1/-1!important;grid-row:2!important}
body.display-sides.display-middle #filterWrap.open .filter-panel,
body.display-sides.display-middle #filterWrap .filter-panel{
  display:flex!important;flex-direction:column;flex:1 1 auto!important;min-height:0!important;max-height:none!important;
  position:static!important;width:auto!important;box-shadow:none
}
body.display-sides.display-middle #kwbar{flex:1 1 auto!important;min-height:0;overflow-y:auto!important;-webkit-overflow-scrolling:touch}
body.display-sides.display-middle.layout-edit #searchSplit,
body.display-sides.display-middle.layout-edit #dualFsSep{display:block!important;pointer-events:auto!important;z-index:80!important}
body.display-sides.display-middle.layout-edit #searchSplit{
  cursor:ns-resize!important;width:auto!important;min-width:0!important;max-width:none!important;height:12px!important;min-height:12px!important;max-height:12px!important
}
body.display-sides.display-middle.layout-edit #dualFsSep{
  cursor:ew-resize!important;width:12px!important;min-width:12px!important;max-width:12px!important;height:auto!important
}
body.display-sides.display-middle.layout-edit #searchSplit::before,
body.display-sides.display-middle.layout-edit #dualFsSep::before{
  content:'';display:block;background:var(--border,rgba(128,128,128,0.5));border-radius:2px;
  opacity:.7;position:absolute;top:50%;left:50%;transform:translate(-50%,-50%)
}
body.display-sides.display-middle.layout-edit #searchSplit::before{width:28px;height:2px}
body.display-sides.display-middle.layout-edit #dualFsSep::before{width:2px;height:28px}
body.display-sides.display-middle.mode-layout-pinned.layout-edit #searchSplit,
body.display-sides.display-middle.mode-layout-pinned.layout-edit #dualFsSep,
body.display-sides.display-middle.sides-pinned.layout-edit #searchSplit,
body.display-sides.display-middle.sides-pinned.layout-edit #dualFsSep{cursor:default!important;pointer-events:none!important}
body.display-sides.display-middle.sides-portrait-flip #searchChrome{grid-column:1!important;grid-row:2!important}
body.display-sides.display-middle.sides-portrait-flip #filterWrap{grid-column:2!important;grid-row:2!important}
body.display-sides.display-middle.sides-portrait-flip #catalogMain{grid-column:1/-1!important;grid-row:3!important}
@media(max-width:899px){
  body.display-sides.display-middle{display:grid!important;flex-direction:unset!important}
  body.display-sides.display-middle #searchChrome{max-height:none!important;height:100%!important;overflow:hidden!important}
  body.display-sides.display-middle #filterWrap{
    position:relative!important;right:auto;top:auto;bottom:auto;left:auto;
    transform:none!important;width:100%!important;max-width:none!important;
    z-index:5!important;box-shadow:none!important;height:100%!important
  }
  body.display-sides.display-middle.kw-open #filterWrap{transform:none!important}
  body.display-sides.display-middle #catalogMain{flex:unset!important}
}
@media(min-width:900px) and (orientation:portrait){
  body.display-sides.display-middle{
    grid-template-columns:minmax(0,var(--middle-lw,1fr)) minmax(0,var(--middle-rw,1fr))!important;
    grid-template-rows:auto var(--middle-menu-h,38dvh) minmax(0,1fr)!important
  }
  body.display-sides.display-middle #searchChrome{grid-column:1!important;grid-row:2!important}
  body.display-sides.display-middle #filterWrap{grid-column:2!important;grid-row:2!important}
  body.display-sides.display-middle #catalogMain{grid-column:1/-1!important;grid-row:3!important}
}
@media(max-width:899px){.display-btn[data-display='middle']{display:inline-flex!important}}
#portraitFlipBtn[hidden]{display:none!important}
</style></head><body class="search-mode">
<div class="catalog-header"><h1 id="top">Kontakt Library</h1><div class="hdr-cluster" id="hdrCluster"><div class="hdr-layout-btns" id="hdrLayoutBtns" role="toolbar" aria-label="Layout controls"></div><button type="button" class="clear-miss-btn" id="clearMissBtn" aria-pressed="false" title="When leaving the image gallery on a library outside the current Search hits, clear Search." onclick="event.preventDefault();event.stopPropagation();toggleClearOnMiss()">Clear on miss</button><div class="hdr-menu-btns" id="hdrMenuBtns" role="toolbar" aria-label="Search and Keywords"><button type="button" class="hdr-menu-btn is-on" id="hdrSearchBtn" aria-pressed="true" title="Search" aria-label="Search" onclick="event.preventDefault();event.stopPropagation();toggleHdrSearch()">S</button><button type="button" class="hdr-menu-btn is-on" id="hdrKwBtn" aria-pressed="true" title="Keywords" aria-label="Keywords" onclick="event.preventDefault();event.stopPropagation();toggleHdrKw()">K</button></div><button type="button" class="hdr-more-btn" id="hdrMoreBtn" aria-expanded="false" aria-haspopup="true" title="More header controls" onclick="event.preventDefault();event.stopPropagation();toggleHdrMore()">&#x22EF;</button><div class="hdr-more-pop" id="hdrMorePop" hidden></div><div class="display-switch" id="displaySwitch" role="tablist" aria-label="Display layout"><button type="button" class="display-btn is-active" data-display="upper" onclick="event.preventDefault();event.stopPropagation();setDisplayMode('upper')">Upper</button><button type="button" class="display-btn display-desktop-only" data-display="sides" onclick="event.preventDefault();event.stopPropagation();setDisplayMode('sides',{pick:true})">Sides</button><button type="button" class="display-btn" data-display="middle" title="Middle: Search and Keywords on top, catalog below" onclick="event.preventDefault();event.stopPropagation();setDisplayMode('middle',{pick:true})">Middle</button><button type="button" class="display-btn" data-display="fs" onclick="event.preventDefault();event.stopPropagation();setDisplayMode('fs')">Full</button></div><select id="themePicker" class="theme-picker" onchange="setTheme(this.value)" onclick="event.stopPropagation()"><optgroup label="— Dark —"><option value="desert">Desert Dusk</option><option value="studio">Night Studio</option><option value="smoked">Smoked Glass</option><option value="autumn-ember">Autumn Ember</option><option value="tropical-night">Tropical Night</option><option value="spring-rain">Spring Rain</option><option value="deep-winter">Deep Winter</option></optgroup><optgroup label="— Light —"><option value="sandstorm">Sand Storm</option><option value="bleached">Bleached</option><option value="spring-bloom">Spring Bloom</option><option value="summer-beach">Summer Beach</option><option value="harvest">Harvest</option><option value="arctic">Arctic</option></optgroup><optgroup label="— High Contrast —"><option value="hc-dark">HC Dark</option><option value="hc-light">HC Light</option></optgroup></select></div></div></div>
HTML
  echo '<div class="search-chrome" id="searchChrome"><div class="search-col" id="searchCol"><div class="search-strip-anchor"><div class="search-strip" id="searchStrip"><input id="searchInput" type="text" placeholder="Search libraries..." autocomplete="off"><button type="button" class="search-strip-hide" onclick="toggleSearchChrome()" aria-expanded="true">Hide Search</button><button type="button" class="search-strip-clear" onclick="clearAllFilters()">Clear</button><button type="button" class="search-strip-fs" id="searchStripFs" onclick="toggleAcFullscreen()" aria-pressed="false" aria-label="Fullscreen search" title="Fullscreen search">&#x26F6;</button><div class="ui-scale search-only-scale" id="searchOnlyScale"><button type="button" class="ui-scale-step" id="searchOnlyScaleDown" aria-label="Smaller Search">−</button><button type="button" class="ui-scale-readout" id="searchOnlyScaleReadout" aria-expanded="false" aria-haspopup="true" title="Search scale">100%</button><button type="button" class="ui-scale-step" id="searchOnlyScaleUp" aria-label="Larger Search">+</button><div class="ui-scale-pop" id="searchOnlyScalePop" hidden></div></div><button type="button" class="search-strip-more" id="searchStripMore" aria-expanded="false" aria-haspopup="true" title="More search controls" onclick="event.preventDefault();event.stopPropagation();toggleSearchStripMore()">&#x22EF;</button><div class="search-strip-more-pop" id="searchStripMorePop" hidden></div></div><div class="search-ac-shell" id="acShell"><div class="ac-fs-bar" id="acFsBar"><button type="button" class="ac-fs-back" id="acFsBack" aria-label="Exit fullscreen" title="Exit fullscreen" onclick="event.preventDefault();event.stopPropagation();setAcFullscreen(false)">&#x2190;</button><div class="fs-mode-nav" id="acFsModeNav" role="navigation" aria-label="Mode"><button type="button" class="mode-btn" data-mode="pick" onclick="event.preventDefault();event.stopPropagation();setMode(&#x27;pick&#x27;)">Pick</button><button type="button" class="mode-btn" data-mode="search" onclick="event.preventDefault();event.stopPropagation();setMode(&#x27;search&#x27;)">Search</button></div><button type="button" class="kw-companion-btn" id="kwCompanionBtn" aria-label="Keywords side-by-side" aria-pressed="false" title="Keywords" onclick="event.preventDefault();event.stopPropagation();toggleKwFsCompanion()">K</button><div class="fs-stripe-wrap"><button type="button" class="fs-stripe-trigger" id="acStripeTrigger" aria-label="Expand controls" title="Expand controls" onclick="event.preventDefault();event.stopPropagation();toggleFsStripe(&#x27;ac&#x27;)">&#x203a;</button><div class="fs-stripe-panel" id="acFsStripePanel"><button type="button" class="fs-snap-btn" id="acSnapBtn" style="display:none" aria-label="Snap 50/50" title="Snap 50/50" onclick="event.preventDefault();event.stopPropagation();snapDualFsTo50()">&#x229e; 50/50</button><button type="button" class="fs-pin-btn" id="fsSepPinBtn" style="display:none" aria-label="Lock separator" aria-pressed="false" title="Lock separator" onclick="event.preventDefault();event.stopPropagation();toggleDualFsPin()">&#x1F4CC;</button><div class="ac-history-wrap" id="searchHistoryWrap"><button type="button" class="ac-history-btn" id="searchHistory" aria-haspopup="dialog" aria-expanded="false" aria-controls="historyCloud" title="History">H</button><div class="ac-history-cloud" id="historyCloud" hidden role="dialog" aria-label="Erase history"><p class="ac-history-ask">Erase history</p><div class="ac-history-picks" id="historyPicks"></div><div class="ac-history-actions"><button type="button" class="ac-history-search" id="historySearchAll" title="Select all search history (not saved sessions or saved combinations)">All search</button><button type="button" class="ac-history-all" id="historyAll" title="Select all, including saved sessions and saved combinations">All</button><button type="button" class="ac-history-yes" id="historyYes" aria-label="Erase selected" title="Erase">&#x2713;</button><button type="button" class="ac-history-no" id="historyNo" aria-label="Cancel" title="Keep">&#x2715;</button></div></div></div><div class="fs-stripe-scale for-ac" aria-label="Scale"><button type="button" class="fs-stripe-scale-btn" aria-label="Smaller search" title="Smaller search" onclick="event.preventDefault();event.stopPropagation();if(typeof stepSearchOnlyUiScale===&#x27;function&#x27;)stepSearchOnlyUiScale(-1)">&#x2212;</button><button type="button" class="fs-stripe-scale-btn" aria-label="Larger search" title="Larger search" onclick="event.preventDefault();event.stopPropagation();if(typeof stepSearchOnlyUiScale===&#x27;function&#x27;)stepSearchOnlyUiScale(1)">+</button></div></div></div></div><div class="ac-ctx-bar" id="acCtxBar"></div><div class="search-autocomplete" id="acList"></div><div class="ac-scroll-stripe" id="acScrollStripe" hidden><div class="ac-scroll-thumb" id="acScrollThumb"></div></div><button type="button" class="ac-height" id="acHeight" aria-label="Resize search suggestions" aria-orientation="horizontal" tabindex="-1"></button><button type="button" class="ac-width" id="acWidth" aria-label="Resize search suggestions width" aria-orientation="vertical" tabindex="-1"></button></div></div><div class="search-active-pills" id="searchPills"></div></div>'
  echo '<button type="button" class="search-split" id="searchSplit" aria-label="Resize Search and Keywords" aria-orientation="vertical" tabindex="-1"></button>'
  echo '<div class="dual-fs-sep" id="dualFsSep" role="separator" aria-label="Drag to resize panels"><button type="button" class="dual-fs-sep-pin" id="dualFsSepPin" aria-label="Lock separator" aria-pressed="false" title="Lock separator" onclick="event.preventDefault();event.stopPropagation();toggleDualFsPin()">&#x1F4CC;</button></div>'
echo '<div class="filter-wrap" id="filterWrap"><div class="filter-top" id="filterTop"><button type="button" class="kw-fs-back" id="kwFsBack" aria-label="Exit fullscreen Keywords" title="Exit fullscreen" onclick="event.preventDefault();event.stopPropagation();toggleKwFullscreen()">&#x2190;</button><button class="filter-toggle" id="filterToggle" onclick="toggleFilter()" aria-expanded="false"><span class="toggle-arrow">&#9660;</span> Keywords</button><button type="button" class="kw-strip-hide" id="kwStripHide" onclick="event.preventDefault();event.stopPropagation();toggleKwChrome()" aria-expanded="true">Hide Keywords</button><div class="fs-mode-nav" id="kwFsModeNav" role="navigation" aria-label="Mode"><button type="button" class="mode-btn" data-mode="pick" onclick="event.preventDefault();event.stopPropagation();setMode(&#x27;pick&#x27;)">Pick</button><button type="button" class="mode-btn" data-mode="search" onclick="event.preventDefault();event.stopPropagation();setMode(&#x27;search&#x27;)">Search</button></div><button type="button" class="ac-companion-btn" id="acCompanionBtn" aria-label="Search side-by-side" aria-pressed="false" title="Search" onclick="event.preventDefault();event.stopPropagation();toggleAcFsCompanion()">&#x1F50D;</button><button type="button" class="kw-strip-more" id="kwStripMore" aria-expanded="false" aria-haspopup="true" title="More keyword controls" onclick="event.preventDefault();event.stopPropagation();toggleKwStripMore()">&#x22EF;</button><div class="kw-strip-more-pop" id="kwStripMorePop" hidden></div><button type="button" class="kw-fs-btn" id="kwStripFs" aria-pressed="false" aria-label="Fullscreen Keywords" title="Fullscreen Keywords" onclick="event.preventDefault();event.stopPropagation();toggleKwFullscreen()">&#x26F6;</button><div class="fs-stripe-wrap"><button type="button" class="fs-stripe-trigger" id="kwStripeTrigger" aria-label="Expand controls" title="Expand controls" onclick="event.preventDefault();event.stopPropagation();toggleFsStripe(&#x27;kw&#x27;)">&#x203a;</button><div class="fs-stripe-panel" id="kwFsStripePanel"><button type="button" class="fs-snap-btn" id="kwSnapBtn" style="display:none" aria-label="Snap 50/50" title="Snap 50/50" onclick="event.preventDefault();event.stopPropagation();snapDualFsTo50()">&#x229e; 50/50</button><div class="fs-stripe-scale for-kw" aria-label="Scale"><button type="button" class="fs-stripe-scale-btn" aria-label="Smaller UI" title="Smaller UI" onclick="event.preventDefault();event.stopPropagation();if(typeof stepUiScale===&#x27;function&#x27;)stepUiScale(-1)">&#x2212;</button><button type="button" class="fs-stripe-scale-btn" aria-label="Larger UI" title="Larger UI" onclick="event.preventDefault();event.stopPropagation();if(typeof stepUiScale===&#x27;function&#x27;)stepUiScale(1)">+</button></div></div></div></div><div class="filter-panel" id="filterPanel"><div class="filter-kw-tools" id="filterKwTools"><button type="button" class="layout-edit-btn" id="layoutEditBtn" aria-pressed="false" title="Show drag edges to resize Search, Keywords, Index, and menu height" onclick="event.preventDefault();event.stopPropagation();toggleLayoutEdit()">Customize</button><button type="button" class="layout-default-btn" id="layoutDefaultBtn" title="Reset layout sizes to defaults." onclick="event.preventDefault();event.stopPropagation();resetLayoutDefaults()">Default</button><div class="layout-presets" id="layoutPresets"><button type="button" class="layout-presets-btn" id="layoutPresetsBtn" aria-expanded="false" aria-haspopup="true" title="Save and apply named menu layouts">Layouts</button><div class="layout-presets-pop" id="layoutPresetsPop" hidden><div class="layout-presets-tabs" role="tablist" aria-label="Layout store"><button type="button" class="layout-presets-tab" id="layoutTabKeywords" data-layout-scope="keywords" role="tab" aria-selected="true">Search + Keywords</button><button type="button" class="layout-presets-tab" id="layoutTabSearch" data-layout-scope="search" role="tab" aria-selected="false">Search</button></div><p class="layout-presets-store" id="layoutPresetsStoreLabel">Search + Keywords</p><div class="layout-presets-list" id="layoutPresetsList"></div><div class="layout-presets-save"><input id="layoutPresetsName" type="text" maxlength="40" placeholder="Name (e.g. Studio)" autocomplete="off"><button type="button" id="layoutPresetsSave">Save Keywords layout</button><button type="button" id="layoutPresetsUpdate">Update Keywords layout</button><p class="layout-presets-flash" id="layoutPresetsFlash" aria-live="polite"></p></div></div><div class="ui-scale" id="uiScale"><button type="button" class="ui-scale-step" id="uiScaleDown" aria-label="Smaller UI">−</button><button type="button" class="ui-scale-readout" id="uiScaleReadout" aria-expanded="false" aria-haspopup="true" title="Interface scale">100%</button><button type="button" class="ui-scale-step" id="uiScaleUp" aria-label="Larger UI">+</button><div class="ui-scale-pop" id="uiScalePop" hidden></div></div></div></div><div class="mode-switch"><button class="mode-btn" data-mode="pick" onclick="setMode(this.dataset.mode)">Pick</button><button class="mode-btn active" data-mode="search" onclick="setMode(this.dataset.mode)">Search</button></div><div class="cat-switch" id="catSwitch"><span class="cat-switch-lead"><button type="button" class="tap-add-btn" id="tapAddBtnPanel" aria-pressed="false" onclick="toggleTapToAdd()">Tap to add</button><button type="button" class="mode-btn clear-all" onclick="clearAllFilters()">Clear</button></span><button class="cat-btn active" data-cat="all" onclick="setCat(this.dataset.cat)">All</button><button class="cat-btn" data-cat="instrument" onclick="setCat(this.dataset.cat)">Instrument</button><button class="cat-btn" data-cat="brand" onclick="setCat(this.dataset.cat)">Brand</button><button class="cat-btn" data-cat="model" onclick="setCat(this.dataset.cat)">Model</button><button class="cat-btn" data-cat="vibe" onclick="setCat(this.dataset.cat)">Vibe</button><button class="cat-btn" data-cat="patch" onclick="setCat(this.dataset.cat)">Patch</button></div><div id="kwbar" lang="en"></div><p id="kwstatus" class="kwstatus"></p></div><button type="button" class="kw-shade-height" id="kwShadeHeight" aria-label="Resize Keywords height" aria-orientation="horizontal" tabindex="-1"></button></div><button type="button" class="search-height" id="searchHeight" aria-label="Resize Search height" aria-orientation="horizontal" tabindex="-1"></button></div>'
  echo '<div class="catalog-index is-collapsed" id="catalogIndex"><div class="catalog-index-head"><button type="button" class="catalog-index-toggle" id="catalogIndexToggle" aria-label="Expand index" aria-expanded="false" title="Expand index" onclick="event.preventDefault();event.stopPropagation();toggleCatalogIndex()"><span class="toggle-arrow">&#9660;</span></button><h2 class="catalog-index-title">Index (alphabetical)</h2><button type="button" class="catalog-index-embed" id="catalogIndexEmbed" aria-pressed="false" title="Embed index above the catalog cards" onclick="event.preventDefault();event.stopPropagation();toggleIndexEmbed()">Embed</button></div><ul class="index" id="catalogIndexList">'
  python3 -c 'import sys,re,html
p=sys.argv[1]
lines=[ln for ln in open(p,encoding="utf-8",errors="replace") if ln.strip()]
def key(line):
    m=re.search(r"<a[^>]*>(.*)</a>",line)
    t=html.unescape(m.group(1) if m else line)
    return t.casefold()
seen=set()
for line in sorted(lines,key=key):
    if line in seen: continue
    seen.add(line)
    sys.stdout.write(line if line.endswith("\n") else line+"\n")
' "$IDX"
  echo '</ul></div>'
  echo '<div class="catalog-body">'
  echo '<div class="fav-recs-label">Favorites</div>'
  cat "$BODY"
  echo '</div>'
  echo '<aside class="catalog-doc-note is-collapsed" id="catalogDocNote"><button type="button" class="catalog-doc-note-toggle" id="catalogDocNoteToggle" aria-expanded="false" aria-controls="catalogDocNoteBody" title="Show document text" onclick="event.preventDefault();event.stopPropagation();toggleCatalogDocNote()"><span class="toggle-arrow">&#9660;</span> About / Document</button><div class="catalog-doc-note-body" id="catalogDocNoteBody">'
  printf '<p>generated: %s</p>\n' "$(e "$(date)")"
  if [ "$MODE" = portable ]; then
    printf '<p>Portable snapshot (banners embedded; phone-safe). Registered Kontakt libraries; click a name to jump. <b>Update:</b> on desktop re-run <code>build-kontakt-catalog-html.sh both</code> and re-transfer this file.</p>\n'
  else
    printf '<p>Registered Kontakt libraries (from komplete.db3). Click a name to jump; [open folder] opens the library in Dolphin.</p>\n'
  fi
  echo '</div></aside>'
  echo '<a class="bottom" href="#catalogBottom">&darr; bottom</a><a class="top" href="#top">&uarr; top</a>'
  cat <<'MODAL'
<div id="hlBackdrop" class="hl-backdrop" onclick="clearHighlight()"></div>
<div id="imgGallery" class="img-gallery" aria-hidden="true">
  <button type="button" class="gallery-back" aria-label="Back" onclick="closeGallery();event.stopPropagation()">&#x2190;</button>
  <button type="button" class="gallery-fav" aria-label="Favorite" aria-pressed="false" onclick="event.preventDefault();event.stopPropagation();toggleFav(this)">&#x2661;</button>
  <button type="button" class="gallery-title" hidden aria-expanded="false" onclick="event.preventDefault();event.stopPropagation();toggleOverlayTitle(this)"></button>
  <img class="gallery-img" alt="">
  <div class="gallery-zoom" onclick="event.stopPropagation()">
    <button type="button" class="gallery-zoom-btn" aria-label="Zoom out" onclick="nudgeImgFocusScale(-0.15)">−</button>
    <button type="button" class="gallery-zoom-btn" aria-label="Zoom in" onclick="nudgeImgFocusScale(0.15)">+</button>
  </div>
</div>
<div id="descReader" class="desc-reader" aria-hidden="true">
  <button type="button" class="desc-reader-back" aria-label="Back" onclick="closeDescReader();event.stopPropagation()">&#x2190;</button>
  <div class="desc-reader-text"></div>
  <div class="desc-reader-zoom" onclick="event.stopPropagation()">
    <button type="button" class="desc-reader-zoom-btn" aria-label="Smaller text" onclick="nudgeDescFocusSize(-2)">−</button>
    <button type="button" class="desc-reader-zoom-btn" aria-label="Larger text" onclick="nudgeDescFocusSize(2)">+</button>
  </div>
</div>
<div id="pathReader" class="path-reader" aria-hidden="true">
  <button type="button" class="path-reader-back" aria-label="Back" onclick="closePathReader();event.stopPropagation()">&#x2190;</button>
  <div class="path-reader-text"></div>
  <div class="path-reader-zoom" onclick="event.stopPropagation()">
    <button type="button" class="path-reader-zoom-btn" aria-label="Smaller text" onclick="nudgePathFocusSize(-2)">−</button>
    <button type="button" class="path-reader-zoom-btn" aria-label="Larger text" onclick="nudgePathFocusSize(2)">+</button>
  </div>
</div>
MODAL
  if [ "$MODE" != portable ]; then
    cat <<'FOCUSHTML'
<div id="imgFocus" class="img-focus-backdrop" onclick="if(event.target===this)closeImgFocus()">
  <button type="button" class="img-focus-fav" aria-label="Favorite" aria-pressed="false" onclick="event.preventDefault();event.stopPropagation();toggleFav(this)">&#x2661;</button>
  <button type="button" class="img-focus-title" hidden aria-expanded="false" onclick="event.preventDefault();event.stopPropagation();toggleOverlayTitle(this)"></button>
  <img class="img-focus-img" alt="">
  <div class="img-focus-zoom" onclick="event.stopPropagation()">
    <button type="button" class="img-focus-zoom-btn" aria-label="Zoom out" onclick="nudgeImgFocusScale(-0.15)">−</button>
    <input id="imgFocusScale" type="range" min="0.5" max="3" step="0.05" value="1" aria-label="Image scale">
    <button type="button" class="img-focus-zoom-btn" aria-label="Zoom in" onclick="nudgeImgFocusScale(0.15)">+</button>
  </div>
</div>
<div id="descFocus" class="desc-focus-backdrop" onclick="if(event.target===this)closeDescFocus()">
  <div class="desc-focus-box" onclick="closeDescFocus();event.stopPropagation()">
    <div class="desc-focus-text"></div>
  </div>
  <div class="desc-focus-zoom" onclick="event.stopPropagation()">
    <button type="button" class="desc-focus-zoom-btn" aria-label="Smaller text" onclick="nudgeDescFocusSize(-2)">−</button>
    <button type="button" class="desc-focus-zoom-btn" aria-label="Larger text" onclick="nudgeDescFocusSize(2)">+</button>
  </div>
</div>
<div id="pathFocus" class="path-focus-backdrop" onclick="if(event.target===this)closePathFocus()">
  <div class="path-focus-box" onclick="closePathFocus();event.stopPropagation()">
    <div class="path-focus-text"></div>
  </div>
  <div class="path-focus-zoom" onclick="event.stopPropagation()">
    <button type="button" class="path-focus-zoom-btn" aria-label="Smaller text" onclick="nudgePathFocusSize(-2)">−</button>
    <button type="button" class="path-focus-zoom-btn" aria-label="Larger text" onclick="nudgePathFocusSize(2)">+</button>
  </div>
</div>
FOCUSHTML
  fi
  cat <<'MODAL'
<div id="searchModal" class="search-modal-backdrop" onclick="if(event.target===this)closeSearchModal()">
  <div class="search-modal">
    <button class="search-modal-close" onclick="closeSearchModal()">&#x2715;</button>
    <div class="search-modal-title" id="searchModalTitle"></div>
    <div class="search-modal-subtitle">Open search in a new window:</div>
    <div class="search-modal-btns">
      <a id="searchModalYT" class="search-modal-link yt" href="#" target="_blank" rel="noopener noreferrer" onclick="openPopup(this,'yt');event.preventDefault();event.stopPropagation();return false;">
        &#x25B6; YouTube
      </a>
      <a id="searchModalWeb" class="search-modal-link web" href="#" target="_blank" rel="noopener noreferrer" onclick="openPopup(this,'web');event.preventDefault();event.stopPropagation();return false;">
        &#x1F50D; Web Search
      </a>
      <a id="searchModalImg" class="search-modal-link img" href="#" target="_blank" rel="noopener noreferrer" onclick="openPopup(this,'img');event.preventDefault();event.stopPropagation();return false;">
        &#x1F5BC; Images
      </a>
    </div>
    <div class="search-modal-hint">Opens as a resizable popup window</div>
  </div>
</div>
<div id="cardSearchEmbed" class="card-search-embed" hidden>
  <div class="card-search-chrome">
    <button type="button" class="card-search-back" aria-label="Back" onclick="event.preventDefault();event.stopPropagation();cardSearchBack()">&#x2190;</button>
    <button type="button" class="card-search-reload" aria-label="Reload" onclick="event.preventDefault();event.stopPropagation();cardSearchReload()">&#x21BB;</button>
    <button type="button" class="card-search-iframe-back" aria-label="Back one step" title="Back one step in page" onclick="event.preventDefault();event.stopPropagation();cardSearchIframeBack()">&#x21BA;</button>
    <span class="card-search-title" id="cardSearchTitle">Search</span>
    <button type="button" class="card-search-switch-toggle" id="cardSearchSwitchToggle" aria-label="Hide mode bar" aria-pressed="true" title="Hide mode bar" onclick="event.preventDefault();event.stopPropagation();cardSearchToggleSwitchBar()">
      <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.2" y="15.2" width="17.6" height="4.4" rx="1.4" fill="none" stroke="currentColor" stroke-width="1.6"/><rect x="5" y="16.6" width="3.2" height="1.6" rx=".4" fill="currentColor"/><rect x="10.4" y="16.6" width="3.2" height="1.6" rx=".4" fill="currentColor"/><rect x="15.8" y="16.6" width="3.2" height="1.6" rx=".4" fill="currentColor"/><path d="M6 5.5h12M6 9h12M6 12.5h8" fill="none" stroke="currentColor" stroke-width="1.45" stroke-linecap="round"/></svg>
    </button>
    <button type="button" class="card-search-popup" onclick="event.preventDefault();event.stopPropagation();cardSearchOpenPopup()">Open in popup</button>
    <button type="button" class="card-search-fs" id="cardSearchFsBtn" aria-label="Fullscreen" aria-pressed="false" title="Fullscreen" onclick="event.preventDefault();event.stopPropagation();cardSearchToggleFullscreen()">&#x2922;</button>
  </div>
  <div class="card-search-stage" id="cardSearchStage">
    <div class="card-search-hint" id="cardSearchHint" hidden role="status" aria-live="polite">
      <p class="card-search-hint-text">If this embed doesn&rsquo;t work, use <strong>Open in popup</strong>.</p>
      <button type="button" class="card-search-hint-x" aria-label="Dismiss" onclick="event.preventDefault();event.stopPropagation();cardSearchDismissEmbedHint()">×</button>
    </div>
    <iframe class="card-search-frame" id="cardSearchFrame" title="Library search" allowfullscreen referrerpolicy="strict-origin-when-cross-origin" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen"></iframe>
    <div class="card-yt-comments" id="cardYtComments">
      <button type="button" class="card-yt-list-toggle" id="cardYtListToggle" aria-label="Hide video list" title="Collapse list" onclick="event.preventDefault();event.stopPropagation();cardToggleYtList()">&#x2039;</button>
      <div class="card-yt-comments-strip" id="cardYtCommentsStrip">
        <div class="card-yt-list" id="cardYtList"></div>
      </div>
    </div>
    <div class="card-search-reader" id="cardSearchReader" hidden></div>
    <div class="card-search-img-view" id="cardSearchImgView">
      <img id="cardSearchImgFit" alt="" onclick="event.preventDefault();event.stopPropagation();cardSearchExitImage()">
    </div>
    <button type="button" class="card-img-exit" id="cardSearchImgExit" onclick="event.preventDefault();event.stopPropagation();cardSearchExitImage()">Exit</button>
    <div class="card-search-fallback" id="cardSearchFallback">
      <p>This search cannot be embedded here.</p>
      <button type="button" onclick="event.preventDefault();event.stopPropagation();cardSearchOpenPopup()">Open in popup</button>
    </div>
    <div class="card-search-switch" id="cardSearchSwitch" role="toolbar" aria-label="Search mode">
      <button type="button" class="card-search-switch-btn" data-mode="yt" aria-label="YouTube" aria-pressed="false" onclick="event.preventDefault();event.stopPropagation();cardSearchSwitch('yt')">
        <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="2.2" y="5.2" width="19.6" height="13.6" rx="3.2" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M10 9.1v5.8L15.4 12z" fill="currentColor"/></svg>
      </button>
      <button type="button" class="card-search-switch-btn" data-mode="web" aria-label="Web Search" aria-pressed="false" onclick="event.preventDefault();event.stopPropagation();cardSearchSwitch('web')">
        <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8.1" fill="none" stroke="currentColor" stroke-width="1.6"/><ellipse cx="12" cy="12" rx="3.3" ry="8.1" fill="none" stroke="currentColor" stroke-width="1.35"/><path d="M4.1 12h15.8M6.4 8.1h11.2M6.4 15.9h11.2" fill="none" stroke="currentColor" stroke-width="1.3"/></svg>
      </button>
      <button type="button" class="card-search-switch-btn" data-mode="img" aria-label="Image Search" aria-pressed="false" onclick="event.preventDefault();event.stopPropagation();cardSearchSwitch('img')">
        <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.1" y="5.2" width="17.8" height="13.6" rx="2.4" fill="none" stroke="currentColor" stroke-width="1.6"/><circle cx="8.5" cy="9.6" r="1.45" fill="currentColor"/><path d="M4.7 16.3l4.5-4.3 3.1 2.9 2.5-2.3 4.5 3.7" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>
      </button>
    </div>
  </div>
</div>
MODAL
  cat <<'JS'
<script>
JS
  if [ "$MODE" = portable ]; then echo 'var CATALOG_PORTABLE=true;window.CATALOG_PORTABLE=true;document.body.classList.add("catalog-portable");'; else echo 'var CATALOG_PORTABLE=false;window.CATALOG_PORTABLE=false;'; fi
echo 'var CATALOG_NS="kontakt";window.CATALOG_NS="kontakt";';
  cat <<'JS'
function cardSearchPopupLabel(){
  return window.CATALOG_PORTABLE?'Popup':'Open in popup';
}
function cardSearchApplyPopupLabels(){
  var lab=cardSearchPopupLabel();
  document.querySelectorAll('.card-search-popup').forEach(function(b){b.textContent=lab;});
  var fb=document.querySelector('#cardSearchFallback > button');
  if(fb&&/popup/i.test(fb.textContent||''))fb.textContent=lab;
  var hint=document.querySelector('.card-search-hint-text strong');
  if(hint)hint.textContent=lab;
}
cardSearchApplyPopupLabels();
function syncSearchHideBtn(){
  var collapsed=document.body.classList.contains('search-chrome-collapsed');
  document.querySelectorAll('.search-strip-hide').forEach(function(b){
    b.textContent=collapsed?'Search':'Hide Search';
    b.setAttribute('aria-expanded',collapsed?'false':'true');
    b.setAttribute('aria-label',collapsed?'Search':'Hide Search');
  });
  var w=document.getElementById('filterWrap');
  var t=document.getElementById('filterToggle');
  var kwOpen=!!(w&&w.classList.contains('open'));
  document.body.classList.toggle('kw-open',kwOpen);
  document.body.classList.toggle('menus-collapsed',!!collapsed&&!kwOpen);
  if(t)t.setAttribute('aria-expanded',kwOpen?'true':'false');
  if(window.syncLayoutStoreUi)window.syncLayoutStoreUi();
  if(window.syncSearchSplit)window.syncSearchSplit();
  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
}
function toggleFilter(){
  var w=document.getElementById('filterWrap'),a=document.querySelector('.toggle-arrow');
  if(!w)return;
  if(document.body.classList.contains('display-sides')){
    if(typeof toggleKwChrome==='function')toggleKwChrome();
    if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
    return;
  }
  var ac=document.getElementById('acList');
  var keepAc=!!(ac&&ac.classList.contains('open'));
  var fromKwFs=document.body.classList.contains('kw-fs-open')||(typeof kwFsWanted!=='undefined'&&kwFsWanted);
  var wasOpen=w.classList.contains('open');
  if(fromKwFs&&wasOpen){
    if(typeof window.setKwFullscreen==='function')window.setKwFullscreen(false);
    else document.body.classList.remove('kw-fs-open');
    w.classList.add('open');
    document.body.classList.add('kw-open');
    if(a)a.textContent='▲';
  }else{
    w.classList.toggle('open');
    if(a)a.textContent=w.classList.contains('open')?'▲':'▼';
    try{localStorage.setItem('catalog-kw-open-'+(window.CATALOG_NS||'catalog'),w.classList.contains('open')?'1':'0');}catch(e){} // fix-KW-save
  }
  var open=w.classList.contains('open');
  syncSearchHideBtn();
  if(open&&typeof window.restoreFilterUi==='function')window.restoreFilterUi();
  if(keepAc&&ac)ac.classList.add('open');
  if(typeof window.applyActiveLayoutStore==='function'){
    window.applyActiveLayoutStore();
    requestAnimationFrame(function(){window.applyActiveLayoutStore();});
  }else if(window.syncSearchSplit)window.syncSearchSplit();
}
function collapseSearchMenu(){
  if(typeof snapshotCurrentLayoutBucket==='function'){snapshotCurrentLayoutBucket();lastLayoutBucket='pending';}
  acFsWanted=false;
  if(typeof parkSearchStrip==='function')parkSearchStrip();
  if(typeof window.hideSearchAc==='function')window.hideSearchAc();
  else{
    var ac=document.getElementById('acList');
    if(ac){ac.classList.remove('open');ac.innerHTML='';}
    var si=document.getElementById('searchInput');
    if(si)si.blur();
  }
  document.body.classList.add('search-chrome-collapsed','search-extras-collapsed');
  syncSearchHideBtn();
  if(typeof applySidesCols==='function')applySidesCols();

}
window.collapseSearchMenu=collapseSearchMenu;
function expandSearchMenu(){
  if(typeof snapshotCurrentLayoutBucket==='function'){snapshotCurrentLayoutBucket();lastLayoutBucket='pending';}
  acFsWanted=false;
  if(typeof parkSearchStrip==='function')parkSearchStrip();
  if(typeof syncAcFsBtn==='function')syncAcFsBtn();
  document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed');
  syncSearchHideBtn();
  if(typeof applySidesCols==='function')applySidesCols();
  if(typeof window.applyActiveLayoutStore==='function'){
    window.applyActiveLayoutStore();
    requestAnimationFrame(function(){window.applyActiveLayoutStore();});
  }else if(typeof window.restoreSearchUi==='function')window.restoreSearchUi();
  var si=document.getElementById('searchInput');
  if(si&&!document.body.classList.contains('ac-fs-open'))setTimeout(function(){si.focus();},50);
}
function toggleSearchChrome(){
  if(document.body.classList.contains('search-chrome-collapsed')) expandSearchMenu();
  else collapseSearchMenu();
}

function syncKwHideBtn(){
  var hidden=document.body.classList.contains('kw-chrome-collapsed');
  document.querySelectorAll('.kw-strip-hide').forEach(function(b){
    b.textContent=hidden?'Keywords':'Hide Keywords';
    b.setAttribute('aria-expanded',hidden?'false':'true');
    b.setAttribute('aria-label',hidden?'Keywords':'Hide Keywords');
  });
}
function collapseKwMenu(){
  if(typeof snapshotCurrentLayoutBucket==='function'){snapshotCurrentLayoutBucket();lastLayoutBucket='pending';}
  var w=document.getElementById('filterWrap');
  if(w)w.classList.remove('open');
  document.body.classList.remove('kw-open');
  document.body.classList.add('kw-chrome-collapsed');
  if(typeof kwFsWanted!=='undefined')kwFsWanted=false;
  document.body.classList.remove('kw-fs-open');
  if(typeof syncKwHideBtn==='function')syncKwHideBtn();
  if(typeof syncSearchHideBtn==='function')syncSearchHideBtn();
  if(typeof applySidesCols==='function')applySidesCols();
  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();

}
function expandKwMenu(){
  if(typeof snapshotCurrentLayoutBucket==='function'){snapshotCurrentLayoutBucket();lastLayoutBucket='pending';}
  document.body.classList.remove('kw-chrome-collapsed');
  var w=document.getElementById('filterWrap');
  if(w)w.classList.add('open');
  document.body.classList.add('kw-open');
  var a=document.querySelector('#filterToggle .toggle-arrow')||document.querySelector('.toggle-arrow');
  if(a)a.textContent='▲';
  if(typeof syncKwHideBtn==='function')syncKwHideBtn();
  if(typeof syncSearchHideBtn==='function')syncSearchHideBtn();
  if(typeof applySidesCols==='function')applySidesCols();
  if(typeof window.restoreFilterUi==='function')window.restoreFilterUi();
}
function toggleKwChrome(){
  if(!document.body.classList.contains('display-sides')){
    if(typeof toggleFilter==='function')toggleFilter();
    return;
  }
  if(document.body.classList.contains('kw-chrome-collapsed')) expandKwMenu();
  else collapseKwMenu();
}
function forceCatalogIndexClosed(reason){
  var ix=document.getElementById('catalogIndex');
  if(!ix)return;
  ix.classList.add('is-collapsed');
  ix.dataset.dockAuto='';
  ix.dataset.dockPin='';
  if(typeof syncIndexToggleUi==='function')syncIndexToggleUi(ix);

}
function resetIndexDock(){
  var ix=document.getElementById('catalogIndex');
  var il=document.getElementById('catalogIndexList')||(ix&&ix.querySelector('ul.index'));
  if(!ix)return;
  ix.classList.add('is-collapsed');
  ix.dataset.dockAuto='';
  ix.dataset.dockPin='';
  ix.dataset.goingTop='';
  try{delete ix.dataset.ixFitInner;}catch(err){ix.dataset.ixFitInner='';}
  if(typeof syncIndexToggleUi==='function')syncIndexToggleUi(ix);
  if(il)il.scrollTop=0;
  var cm=document.getElementById('catalogMain');
  if(cm)cm.scrollTop=0;
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();

}
window.forceCatalogIndexClosed=forceCatalogIndexClosed;
window.syncKwHideBtn=syncKwHideBtn;
window.collapseKwMenu=collapseKwMenu;
window.expandKwMenu=expandKwMenu;
window.toggleKwChrome=toggleKwChrome;
window.resetIndexDock=resetIndexDock;

function syncHdrMenuBtns(){
  var searchOn=!document.body.classList.contains('search-chrome-collapsed');
  var fw=document.getElementById('filterWrap');
  var kwOn=!document.body.classList.contains('kw-chrome-collapsed')&&!!(fw&&fw.classList.contains('open'));
  var sb=document.getElementById('hdrSearchBtn');
  var kb=document.getElementById('hdrKwBtn');
  if(sb){sb.classList.toggle('is-on',searchOn);sb.setAttribute('aria-pressed',searchOn?'true':'false');sb.title=searchOn?'Hide Search':'Show Search';}
  if(kb){kb.classList.toggle('is-on',kwOn);kb.setAttribute('aria-pressed',kwOn?'true':'false');kb.title=kwOn?'Hide Keywords':'Show Keywords';}
}
function toggleHdrSearch(){
  if(typeof toggleSearchChrome==='function')toggleSearchChrome();
  else if(document.body.classList.contains('search-chrome-collapsed')){if(typeof expandSearchMenu==='function')expandSearchMenu();}
  else if(typeof collapseSearchMenu==='function')collapseSearchMenu();
  syncHdrMenuBtns();
}
function toggleHdrKw(){
  if(document.body.classList.contains('display-sides')){
    if(typeof toggleKwChrome==='function')toggleKwChrome();
  }else if(typeof toggleFilter==='function'){
    var w=document.getElementById('filterWrap');
    if(document.body.classList.contains('kw-chrome-collapsed')&&typeof expandKwMenu==='function')expandKwMenu();
    else toggleFilter();
  }
  syncHdrMenuBtns();
}
function syncIndexEmbedBtn(){
  var ix=document.getElementById('catalogIndex');
  var btn=document.getElementById('catalogIndexEmbed');
  if(!btn)return;
  var on=!!(ix&&ix.classList.contains('is-embedded'));
  var sides=document.body.classList.contains('display-sides');
  btn.hidden=!sides;
  btn.setAttribute('aria-pressed',on?'true':'false');
  btn.textContent=on?'Window':'Embed';
  btn.title=on?'Show Index as a scrollable dock window':'Embed Index above the catalog cards';
}
function toggleIndexEmbed(){
  var ix=document.getElementById('catalogIndex');
  if(!ix||!document.body.classList.contains('display-sides'))return;
  var on=ix.classList.toggle('is-embedded');
  if(typeof writeModeSlot==='function')writeModeSlot({indexEmbed:on},'sides');
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  syncIndexEmbedBtn();
  var cm=document.getElementById('catalogMain');
  if(on&&cm)cm.scrollTop=0;
}
function toggleSearchStripMore(){
  var pop=document.getElementById('searchStripMorePop');
  var btn=document.getElementById('searchStripMore');
  if(!pop||!btn)return;
  var open=pop.hasAttribute('hidden');
  if(open){
    pop.innerHTML='';
    function add(label,fn){var b=document.createElement('button');b.type='button';b.textContent=label;b.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();pop.setAttribute('hidden','');btn.setAttribute('aria-expanded','false');fn();});pop.appendChild(b);}
    add('Smaller Search',function(){if(typeof stepSearchOnlyUiScale==='function')stepSearchOnlyUiScale(-1);});
    add('Larger Search',function(){if(typeof stepSearchOnlyUiScale==='function')stepSearchOnlyUiScale(1);});
    if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
      add('Clear search',function(){if(typeof clearAllFilters==='function')clearAllFilters();});
      add('History',function(){var h=document.getElementById('searchHistory');if(h)h.click();});
    }
    pop.removeAttribute('hidden');
    btn.setAttribute('aria-expanded','true');
  }else{
    pop.setAttribute('hidden','');
    btn.setAttribute('aria-expanded','false');
  }
}
window.syncHdrMenuBtns=syncHdrMenuBtns;
window.toggleHdrSearch=toggleHdrSearch;
window.toggleHdrKw=toggleHdrKw;
window.syncIndexEmbedBtn=syncIndexEmbedBtn;
window.toggleIndexEmbed=toggleIndexEmbed;
window.toggleSearchStripMore=toggleSearchStripMore;

function closePhoneOverflowPops(except){
  [['hdrMorePop','hdrMoreBtn'],['kwStripMorePop','kwStripMore'],['searchStripMorePop','searchStripMore']].forEach(function(pair){
    if(except&&pair[0]===except)return;
    var p=document.getElementById(pair[0]);var b=document.getElementById(pair[1]);
    if(p)p.setAttribute('hidden','');
    if(b)b.setAttribute('aria-expanded','false');
  });
}
function phoneMoreAdd(pop,label,fn){
  var b=document.createElement('button');b.type='button';b.textContent=label;
  b.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();closePhoneOverflowPops();fn();});
  pop.appendChild(b);
}
function toggleHdrMore(){
  if(!(typeof isPhoneViewport==='function'&&isPhoneViewport()))return;
  var pop=document.getElementById('hdrMorePop');var btn=document.getElementById('hdrMoreBtn');
  if(!pop||!btn)return;
  var open=pop.hasAttribute('hidden');
  closePhoneOverflowPops('hdrMorePop');
  if(!open){pop.setAttribute('hidden','');btn.setAttribute('aria-expanded','false');return;}
  pop.innerHTML='';
  phoneMoreAdd(pop,'Clear on miss',function(){var x=document.getElementById('clearMissBtn');if(x)x.click();});
  phoneMoreAdd(pop,'Customize',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();});
  phoneMoreAdd(pop,'Layouts',function(){var x=document.getElementById('layoutPresetsBtn');if(x)x.click();});
  phoneMoreAdd(pop,'Smaller UI',function(){if(typeof stepUiScale==='function')stepUiScale(-1);});
  phoneMoreAdd(pop,'Larger UI',function(){if(typeof stepUiScale==='function')stepUiScale(1);});
  var sel=document.getElementById('themePicker');
  if(sel){
    var lab=document.createElement('label');lab.textContent='Theme';lab.style.fontSize='.85rem';
    var clone=sel.cloneNode(true);clone.id='hdrMoreTheme';clone.className='theme-picker';
    clone.value=sel.value;
    clone.addEventListener('change',function(){if(typeof setTheme==='function')setTheme(clone.value);sel.value=clone.value;});
    pop.appendChild(lab);pop.appendChild(clone);
  }
  pop.removeAttribute('hidden');btn.setAttribute('aria-expanded','true');
}
function toggleKwStripMore(){
  if(!(typeof isPhoneViewport==='function'&&isPhoneViewport()))return;
  var pop=document.getElementById('kwStripMorePop');var btn=document.getElementById('kwStripMore');
  if(!pop||!btn)return;
  var open=pop.hasAttribute('hidden');
  closePhoneOverflowPops('kwStripMorePop');
  if(!open){pop.setAttribute('hidden','');btn.setAttribute('aria-expanded','false');return;}
  pop.innerHTML='';
  phoneMoreAdd(pop,'Customize',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();});
  phoneMoreAdd(pop,'Layouts',function(){var x=document.getElementById('layoutPresetsBtn');if(x)x.click();});
  phoneMoreAdd(pop,'Smaller UI',function(){if(typeof stepUiScale==='function')stepUiScale(-1);});
  phoneMoreAdd(pop,'Larger UI',function(){if(typeof stepUiScale==='function')stepUiScale(1);});
  phoneMoreAdd(pop,'Tap to add',function(){if(typeof toggleTapToAdd==='function')toggleTapToAdd();});
  phoneMoreAdd(pop,'Clear keywords',function(){if(typeof clearAllFilters==='function')clearAllFilters();});
  pop.removeAttribute('hidden');btn.setAttribute('aria-expanded','true');
}
window.toggleHdrMore=toggleHdrMore;
window.toggleKwStripMore=toggleKwStripMore;
document.addEventListener('click',function(e){
  if(!(typeof isPhoneViewport==='function'&&isPhoneViewport()))return;
  var t=e.target;
  if(t&&t.closest&&t.closest('#hdrMoreBtn,#hdrMorePop,#kwStripMore,#kwStripMorePop,#searchStripMore,#searchStripMorePop'))return;
  closePhoneOverflowPops();
});
document.addEventListener('click',function(e){
  var pop=document.getElementById('searchStripMorePop');
  var btn=document.getElementById('searchStripMore');
  if(!pop||pop.hasAttribute('hidden'))return;
  if(btn&&(btn===e.target||btn.contains(e.target)))return;
  if(pop.contains(e.target))return;
  pop.setAttribute('hidden','');
  if(btn)btn.setAttribute('aria-expanded','false');
});
function syncLayoutEditBtn(){
  var on=document.body.classList.contains('layout-edit');
  document.querySelectorAll('#layoutEditBtn,.layout-edit-btn:not(#modePinBtn)').forEach(function(b){
    if(b.id==='modePinBtn')return;
    b.textContent=on?'Done':'Customize';
    b.setAttribute('aria-pressed',on?'true':'false');
    b.title=on?'Finish arranging UI edges':'Show drag edges to resize Search, Keywords, Index, and menu height';
    b.setAttribute('aria-label',on?'Done arranging':'Customize layout');
  });
  if(typeof syncModeLockBtn==='function')syncModeLockBtn();
}
function toggleLayoutEdit(){
  var was=document.body.classList.contains('layout-edit');
  document.body.classList.toggle('layout-edit');
  if(was&&typeof persistAllLiveLayouts==='function')persistAllLiveLayouts();
  syncLayoutEditBtn();
  if(window.syncSearchSplit)window.syncSearchSplit();
  if(typeof applyAll==='function')applyAll();
  if(typeof applySidesCols==='function')applySidesCols();
  if(typeof applyFsChromeSize==='function')applyFsChromeSize();
  if(typeof placeSidesHandles==='function')placeSidesHandles();
  if(typeof bindIndexHeight==='function')bindIndexHeight();

}
window.toggleLayoutEdit=toggleLayoutEdit;
window.syncLayoutEditBtn=syncLayoutEditBtn;
function setTheme(t){document.documentElement.setAttribute('data-theme',t);localStorage.setItem('catalog-theme',t);if(typeof window.syncCardSearchTheme==='function')window.syncCardSearchTheme();}
(function(){var t=localStorage.getItem('catalog-theme')||'desert';document.documentElement.setAttribute('data-theme',t);var p=document.getElementById('themePicker');if(p)p.value=t;})();
var LIGHT_THEMES={sandstorm:1,bleached:1,'spring-bloom':1,'summer-beach':1,harvest:1,arctic:1,'hc-light':1};
var cardSearchState={type:'',popupUrl:'',embedUrl:'',history:[],query:'',view:'',urls:{}};
var searchModalFromPreview=false;
function catalogThemeName(){return document.documentElement.getAttribute('data-theme')||localStorage.getItem('catalog-theme')||'desert';}
function catalogThemeIsDark(){return !LIGHT_THEMES[catalogThemeName()];}
function catalogThemeCss(){
  var cs=getComputedStyle(document.documentElement);
  function v(n){return (cs.getPropertyValue(n)||'').trim();}
  return {bg:v('--bg'),surface:v('--bg-surface'),card:v('--bg-card'),text:v('--text'),muted:v('--text-muted'),border:v('--border'),accent:v('--accent-instrument')};
}
function queryFromSearchUrl(url){
  try{
    var u=new URL(url,location.href);
    return u.searchParams.get('search_query')||u.searchParams.get('q')||'';
  }catch(err){return '';}
}
function cardSearchEsc(s){
  return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function cardSearchQuery(popupUrl,fallback){
  var q=queryFromSearchUrl(popupUrl);
  if(q)return q;
  return String(fallback||'').replace(/^\s+|\s+$/g,'');
}
function cardSearchYtIdFromUrl(popupUrl){
  try{
    var u=new URL(popupUrl,location.href);
    var host=(u.hostname||'').toLowerCase();
    if(host==='youtu.be'||host==='www.youtu.be'){
      var id=(u.pathname||'').replace(/^\//,'').split('/')[0];
      if(id&&!/embed/.test(id))return id;
    }
    if(/youtube\.com$/.test(host)||/youtube-nocookie\.com$/.test(host)){
      var vid=u.searchParams.get('v');
      if(vid)return vid;
      var emb=(u.pathname||'').match(/^\/embed\/([^/?]+)/);
      if(emb&&emb[1]&&emb[1]!=='videoseries')return emb[1];
    }
    var m=String(popupUrl||'').match(/[?&]v=([A-Za-z0-9_-]{6,})/);
    if(m)return m[1];
  }catch(err){}
  return '';
}
function cardSearchYtPlayUrl(id,host,opts){
  if(!id)return '';
  id=String(id).replace(/^\s+|\s+$/g,'');
  if(!/^[A-Za-z0-9_-]{6,}$/.test(id))return '';
  if(/^(videoseries|results|search)$/i.test(id))return '';
  host=String(host||cardSearchState._ytHost||'youtube');
  opts=opts||{};
  // Invidious: open-source YT frontend, no Referer restriction — works from file:// too.
  if(host==='invidious'){
    var instances=cardSearchState._invInstances||['yewtu.be','invidious.nerdvpn.de','inv.nadeko.net','yt.artemislena.eu'];
    var idx=Number(cardSearchState._invInstanceIdx)||0;
    var inst=instances[idx%instances.length]||'yewtu.be';
    return 'https://'+inst+'/embed/'+encodeURIComponent(id)+'?autoplay='+(opts.autoplay?1:0)+'&quality=auto&listen=0&iv_load_policy=3';
  }
  // Error 153 = missing HTTP Referer (Google YT terms). Prefer www.youtube.com.
  if(host!=='nocookie')host='youtube';
  var origin=(location.origin&&location.origin!=='null')?location.origin:'';
  var q='rel=0&modestbranding=1&playsinline=1&enablejsapi=1';
  if(opts.autoplay)q+='&autoplay=1';
  if(origin){
    q+='&origin='+encodeURIComponent(origin);
    q+='&widget_referrer='+encodeURIComponent(origin+'/');
  }
  var base=host==='nocookie'?'https://www.youtube-nocookie.com/embed/':'https://www.youtube.com/embed/';
  return base+encodeURIComponent(id)+'?'+q;
}
function cardSearchYtEmbedUrl(popupUrl,query,id){
  if(id)return cardSearchYtPlayUrl(id);
  var from=cardSearchYtIdFromUrl(popupUrl);
  if(from)return cardSearchYtPlayUrl(from);
  return '';
}
function cardSearchYtIsBadEmbedUrl(url){
  var s=String(url||'');
  if(!s||s==='about:blank')return true;
  if(/listType=search|\/results\?|\/watch\?|\/embed\/videoseries/i.test(s))return true;
  var isYt=/(?:youtube(?:-nocookie)?\.com)\/embed\/[A-Za-z0-9_-]{6,}/.test(s);
  var isInv=/(?:yewtu\.be|invidious\.nerdvpn\.de|inv\.nadeko\.net|yt\.artemislena\.eu)\/embed\/[A-Za-z0-9_-]{6,}/.test(s);
  if(!isYt&&!isInv)return true;
  return false;
}
function catalogSearchExtra(){return (window.CATALOG_NS==='ds')?'decent sampler':'kontakt';}
function catalogFileHint(){return (window.CATALOG_NS==='ds')?'dspreset':'nki';}
function stripCatalogExtra(s){
  return String(s||'').replace(/\s+decent\s+sampler(?:\s+library)?\s*$/i,'').replace(/\s+kontakt(?:\s+library)?\s*$/i,'').replace(/\s+vst(?:\s+instrument)?\s*$/i,'').replace(/^\s+|\s+$/g,'');
}
function libraryDisplayName(){
  return String(cardSearchState.name||stripCatalogExtra(cardSearchState.query||'')||'').replace(/^\s+|\s+$/g,'');
}
function libraryNameTokens(){
  var stop={the:1,and:1,for:1,from:1,with:1,this:1,that:1,a:1,an:1,of:1,to:1,in:1,on:1,by:1,or:1,is:1,at:1,as:1,vs:1,http:1,https:1,www:1,com:1,org:1,net:1,search:1,query:1,results:1,vst:1,instrument:1,library:1,kontakt:1,decent:1,sampler:1,free:1,plus:1,edition:1,vol:1,volume:1,nki:1,dspreset:1};
  var name=libraryDisplayName().toLowerCase().replace(/[^a-z0-9]+/g,' ');
  return name.split(' ').filter(function(w){return w.length>2&&!stop[w];});
}
function libraryQueryVariants(){
  var name=libraryDisplayName();
  var extra=catalogSearchExtra();
  var hint=catalogFileHint();
  var out=[];
  function add(s){
    s=String(s||'').replace(/^\s+|\s+$/g,'');
    if(!s)return;
    var key=s.toLowerCase();
    if(out.some(function(x){return x.toLowerCase()===key;}))return;
    out.push(s);
  }
  if(name){
    add('"'+name+'" '+extra);
    add('"'+name+'" sample library');
    add('"'+name+'" '+hint);
    add(name+' '+extra+' sample library');
    add(name+' '+extra);
  }
  return out;
}
function librarySearchTokens(){return libraryNameTokens();}
function scoreSearchHay(text,tokens){
  var hay=String(text||'').toLowerCase();
  var score=0,hits=0;
  (tokens||[]).forEach(function(t){
    if(hay.indexOf(t)>=0){hits++;score+=t.length>=4?3:1;}
  });
  return {score:score,hits:hits};
}
function libraryProductContext(hay){
  return /kontakt|decent\s*sampler|sample\s*library|\bnki\b|\bdspreset\b|nks|native\s*instruments|vst|plugin|preset|gumroad|itch\.io|patch\s*library|instrument\s*library|walkthrough|manual|gui|cover\s*art/.test(String(hay||'').toLowerCase());
}
function isLibraryRelevantHit(hay,opts){
  opts=opts||{};
  hay=String(hay||'').toLowerCase();
  if(!hay)return false;
  if(/cia\.gov|reading room|soviet activities|arctic and antarctic|histolog|microscope|patholog|anatomy atlas|tire\b|tyre\b/.test(hay))return false;
  var name=libraryDisplayName().toLowerCase();
  var toks=libraryNameTokens();
  if(!toks.length&&!name)return false;
  var nameHit=!!(name&&hay.indexOf(name)>=0);
  var sc=scoreSearchHay(hay,toks);
  var need=toks.length<=1?1:toks.length;
  // Require ALL distinctive name tokens in title/snippet/url — blocks CIA/arctic for "Cloud Supply"
  if(!(nameHit||sc.hits>=need))return false;
  if(opts.requireProduct===false)return true;
  if(libraryProductContext(hay))return true;
  if(nameHit&&toks.length>=2)return true;
  if(/wikipedia\.org|wikimedia\.org|commons\.wikimedia|cia\.gov/.test(hay)&&!libraryProductContext(hay))return false;
  return nameHit&&sc.hits>=need;
}
function fetchJsonTimeout(url,ms){
  var ctrl=new AbortController();
  var t=setTimeout(function(){try{ctrl.abort();}catch(err){}},ms||5000);
  return fetch(url,{mode:'cors',signal:ctrl.signal}).then(function(r){
    if(!r.ok)throw new Error('HTTP '+r.status);
    return r.json();
  }).finally(function(){clearTimeout(t);});
}
function parsePipedVideos(data){
  var items=(data&&data.items)||[];
  var out=[];
  items.forEach(function(it){
    if(!it||(it.type&&it.type!=='stream'))return;
    var id='';
    var u=String(it.url||it.id||'');
    var m=u.match(/[?&]v=([A-Za-z0-9_-]{6,})/)||u.match(/\/watch\/([A-Za-z0-9_-]{6,})/)||u.match(/^([A-Za-z0-9_-]{6,})$/);
    if(m)id=m[1];
    if(!id&&it.id&&/^[A-Za-z0-9_-]{6,}$/.test(it.id))id=it.id;
    if(!id)return;
    out.push({id:id,title:it.title||id,thumb:'https://i.ytimg.com/vi/'+id+'/hqdefault.jpg',author:it.uploaderName||''});
  });
  return out;
}
function parseInvidiousVideos(data){
  var items=Array.isArray(data)?data:(data&&data.videos)||[];
  var out=[];
  items.forEach(function(it){
    if(!it||(it.type&&it.type!=='video'))return;
    var id=it.videoId||'';
    if(!id)return;
    out.push({id:id,title:it.title||id,thumb:'https://i.ytimg.com/vi/'+id+'/hqdefault.jpg',author:it.author||''});
  });
  return out;
}
function rankSearchItems(items,textFn,opts){
  opts=opts||{};
  var tokens=libraryNameTokens();
  var name=libraryDisplayName().toLowerCase();
  return (items||[]).map(function(it){
    var hay=textFn?textFn(it):((it.title||'')+' '+(it.snippet||'')+' '+(it.author||'')+' '+(it.url||''));
    var sc=scoreSearchHay(hay,tokens);
    var nameHit=name&&String(hay).toLowerCase().indexOf(name)>=0?1:0;
    var prod=libraryProductContext(hay)?1:0;
    it._hay=hay;
    it._score=sc.score+(nameHit?8:0)+(prod?10:0);
    it._hits=sc.hits;
    it._nameHits=nameHit?Math.max(1,sc.hits):sc.hits;
    it._relevant=isLibraryRelevantHit(hay,opts);
    return it;
  }).filter(function(it){return !!it._relevant;}).sort(function(a,b){return (b._score-a._score)||(b._nameHits-a._nameHits)||(b._hits-a._hits);});
}
function cardSearchEnsureYtFrame(){
  var old=document.getElementById('cardSearchFrame');
  var parent=old?old.parentNode:null;
  if(!parent)return null;
  var frame=document.createElement('iframe');
  frame.className='card-search-frame';
  frame.id='cardSearchFrame';
  frame.title='Library search';
  frame.setAttribute('allowfullscreen','');
  frame.setAttribute('referrerpolicy','strict-origin-when-cross-origin');
  frame.setAttribute('allow','accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen; web-share');
  try{frame.referrerPolicy='strict-origin-when-cross-origin';}catch(err){}
  try{frame.allowFullscreen=true;}catch(err){}
  parent.replaceChild(frame,old);
  return frame;
}
function cardSearchYtCanEmbedHere(){
  try{
    if(location.protocol==='file:')return false;
    if(!location.origin||location.origin==='null')return false;
  }catch(err){return false;}
  return true;
}
function cardSearchEnsureYtApi(cb){
  if(window.YT&&YT.Player){if(cb)cb();return;}
  var q=window._catalogYtApiQ||(window._catalogYtApiQ=[]);
  if(cb)q.push(cb);
  var prev=window.onYouTubeIframeAPIReady;
  window.onYouTubeIframeAPIReady=function(){
    try{if(typeof prev==='function')prev();}catch(err){}
    var cbs=window._catalogYtApiQ||[];
    window._catalogYtApiQ=[];
    cbs.forEach(function(fn){try{fn();}catch(err){}});
  };
  if(document.getElementById('catalogYtIframeApi'))return;
  var s=document.createElement('script');
  s.id='catalogYtIframeApi';
  s.src='https://www.youtube.com/iframe_api';
  s.async=true;
  document.head.appendChild(s);
}
function cardSearchClearYtWatchdog(){
  if(cardSearchState&&cardSearchState._ytWatch){
    try{clearTimeout(cardSearchState._ytWatch);}catch(err){}
    cardSearchState._ytWatch=null;
  }
}
function cardSearchArmYtApiWatchdog(id){
  cardSearchClearYtWatchdog();
  cardSearchState._ytWatch=setTimeout(function(){
    if(!(cardSearchState&&cardSearchState.type==='yt'))return;
    if(cardSearchState.ytId!==id)return;
    if(cardSearchState._ytReady)return;
    // API never reached onReady — hide broken player, show thumbnail CTA.
    cardSearchYtTryNext('error 153');
  },5000);
}
function setCardYtFrame(id,host,opts){
  opts=opts||{};
  var url=cardSearchYtPlayUrl(id,host,opts);
  if(!url||cardSearchYtIsBadEmbedUrl(url))return false;
  var useInvidious=String(host||'').toLowerCase()==='invidious';
  if(!cardSearchYtCanEmbedHere()&&!useInvidious){
    cardSearchState.ytId=id;
    cardSearchState.embedUrl=url;
    cardSearchState.popupUrl=cardSearchState.popupUrl||('https://www.youtube.com/watch?v='+encodeURIComponent(id));
    showCardSearchFrame(false);
    cardSearchShowYtBlocked('file:// or null origin — YouTube needs HTTP(S) Referer');
    return true;
  }
  cardSearchClearYtWatchdog();
  if(cardSearchState._ytPlayer){
    try{cardSearchState._ytPlayer.destroy();}catch(err){}
    cardSearchState._ytPlayer=null;
  }
  var frame=cardSearchEnsureYtFrame();
  var fallback=document.getElementById('cardSearchFallback');
  if(!frame)return false;
  if(fallback)fallback.classList.remove('open');
  cardSearchState.ytId=id;
  var hostNorm=String(host||cardSearchState._ytHost||'youtube');
  cardSearchState._ytHost=hostNorm==='nocookie'?'nocookie':(hostNorm==='invidious'?'invidious':'youtube');
  cardSearchState.embedUrl=url;
  if(!(opts&&opts.noHist)&&typeof cardSearchHistPush==='function')cardSearchHistPush({kind:'yt',type:'yt',view:'yt',ytId:id,embedUrl:url,host:cardSearchState._ytHost});
  else if(!(opts&&opts.noHist))cardSearchState.history=(cardSearchState.history||[]).concat([url]);
  cardSearchState._ytReady=false;
  frame.classList.remove('is-hidden');
  frame.style.display='';
  frame.setAttribute('referrerpolicy','strict-origin-when-cross-origin');
  try{frame.referrerPolicy='strict-origin-when-cross-origin';}catch(err){}
  showCardSearchFrame(true);
  function mountPlain(){
    var f=document.getElementById('cardSearchFrame')||frame;
    if(!f)return;
    f.src=url;
  }
  function mountApi(){
    try{
      if(!(window.YT&&YT.Player)){mountPlain();return;}
      if(cardSearchState._ytPlayer){
        try{cardSearchState._ytPlayer.destroy();}catch(err){}
        cardSearchState._ytPlayer=null;
      }
      var f=cardSearchEnsureYtFrame();
      if(!f){mountPlain();return;}
      f.removeAttribute('src');
      f.setAttribute('referrerpolicy','strict-origin-when-cross-origin');
      try{f.referrerPolicy='strict-origin-when-cross-origin';}catch(err){}
      var origin=(location.origin&&location.origin!=='null')?location.origin:undefined;
      cardSearchState._ytPlayer=new YT.Player(f,{
        host:cardSearchState._ytHost==='nocookie'?'https://www.youtube-nocookie.com':'https://www.youtube.com',
        videoId:id,
        playerVars:{rel:0,modestbranding:1,playsinline:1,enablejsapi:1,origin:origin,autoplay:opts.autoplay?1:0},
        events:{
          onReady:function(ev){cardSearchState._ytReady=true;cardSearchClearYtWatchdog();if(opts.autoplay){try{ev.target.playVideo();}catch(err){}}},
          onError:function(ev){
            var code=ev&&ev.data;
            if(code===153||code===150||code===101||code===100||code===2||code===5){
              if(cardSearchState&&cardSearchState.type==='yt')cardSearchYtTryNext('error '+code);
            }
          }
        }
      });
      cardSearchArmYtApiWatchdog(id);
    }catch(err){mountPlain();}
  }
  mountPlain();
  if(!useInvidious)cardSearchEnsureYtApi(function(){});
  return true;
}

function cardSearchYtTryNext(reason){
  var items=cardSearchState.ytItems||[];
  var cur=cardSearchState.ytId||'';
  var tried=cardSearchState._ytTried||{};
  var hostTried=cardSearchState._ytHostTried||{};
  var why=String(reason||'');
  cardSearchClearYtWatchdog();
  // Error 153 is Referer/policy — cycling videos keeps a broken Napaka 153 player.
  // One host swap, then thumbnail + Open in popup (same path as header).
  if(cur&&(/\b153\b|file:\/\/|null origin|watchdog|config/i.test(why))){
    var curHost=cardSearchState._ytHost||'youtube';
    var alt=curHost==='youtube'?'nocookie':'youtube';
    var hk=cur+'@'+alt;
    if(/\b153\b|watchdog|config/i.test(why)&&!hostTried[hk]&&!/file:\/\/|null origin/i.test(why)){
      hostTried[hk]=1;
      cardSearchState._ytHostTried=hostTried;
      // Prefer IFrame API path via setCardYtFrame; if still fails, blocked UI.
      if(setCardYtFrame(cur,alt)){
        renderCardYtList(items,cur);
        return true;
      }
    }
    showCardSearchFrame(false);
    cardSearchShowYtBlocked(why||'error 153');
    return false;
  }
  if(cur&&(/150|101/i.test(why))){
    var curHost2=cardSearchState._ytHost||'youtube';
    var alt2=curHost2==='youtube'?'nocookie':'youtube';
    var hk2=cur+'@'+alt2;
    if(!hostTried[hk2]){
      hostTried[hk2]=1;
      cardSearchState._ytHostTried=hostTried;
      if(setCardYtFrame(cur,alt2)){
        renderCardYtList(items,cur);
        return true;
      }
    }
  }
  if(cur)tried[cur]=1;
  cardSearchState._ytTried=tried;
  cardSearchState._ytHostTried=hostTried;
  for(var i=0;i<items.length;i++){
    var it=items[i];
    if(!it||!it.id||tried[it.id])continue;
    cardSearchState._ytHost='youtube';
    if(setCardYtFrame(it.id,'youtube')){
      renderCardYtList(items,it.id);
      return true;
    }
    tried[it.id]=1;
  }
  showCardSearchFrame(false);
  cardSearchShowYtBlocked(reason);
  return false;
}
(function(){
  if(window._ytErrBound)return;
  window._ytErrBound=1;
  window.addEventListener('message',function(e){
    try{
      var host=String((e&&e.origin)||'');
      if(host.indexOf('youtube.com')<0&&host.indexOf('youtube-nocookie.com')<0)return;
      var data=e.data;
      if(typeof data==='string'){
        try{data=JSON.parse(data);}catch(err){return;}
      }
      if(!data||typeof data!=='object')return;
      var code=null;
      if(data.event==='onError')code=data.info;
      else if(data.info&&typeof data.info==='object'&&data.info.event==='onError')code=data.info.info;
      if(code==null)return;
      code=Number(code);
      if(code===153||code===150||code===101||code===100||code===2||code===5){
        if(cardSearchState&&cardSearchState.type==='yt')cardSearchYtTryNext('error '+code);
      }
    }catch(err){}
  });
})();
function renderCardYtList(items,activeId){
  var list=document.getElementById('cardYtList');
  if(!list)return;
  if(!items||!items.length){
    list.innerHTML='<p>No embeddable videos for this library. Open YouTube in a popup.</p><button type="button" onclick="event.preventDefault();event.stopPropagation();cardSearchOpenPopup()">'+cardSearchPopupLabel()+'</button>';
    return;
  }
  var html='<div class="card-yt-list">';
  items.forEach(function(it,i){
    html+='<button type="button" class="card-yt-row'+(it.id===activeId?' is-active':'')+'" data-i="'+i+'" onclick="event.preventDefault();event.stopPropagation();cardSearchPlayYt('+i+')">';
    html+='<img src="'+cardSearchEsc(it.thumb)+'" alt="">';
    html+='<span class="card-yt-row-title">'+cardSearchEsc(it.title||it.id)+'</span></button>';
  });
  html+='</div>';
  list.innerHTML=html;
}
window.cardSearchPlayYt=function(i){
  var items=cardSearchState.ytItems||[];
  var it=items[i];
  if(!it||!it.id)return;
  cardSearchState._ytHost='youtube';
  cardSearchState._ytHostTried={};
  setCardYtFrame(it.id,'youtube');
  renderCardYtList(items,it.id);
};
function loadCardYtSearch(query){
  var q=query||cardSearchState.query||cardSearchState.name||'';
  var extra=catalogSearchExtra();
  if(q&&q.toLowerCase().indexOf(extra)<0)q=q+' '+extra;
  cardSearchState.view='yt';
  // Bug1-fix: clear manual-play flag so finish() may set the initial video.
  // If user clicks play while the fetch is in flight, finish() will see _ytManualPlay=true
  // and skip the non-autoplay setCardYtFrame that would otherwise kill the playing video.
  cardSearchState._ytManualPlay=false;
  var list=document.getElementById('cardYtList');
  if(list)list.innerHTML='<p>Finding videos…</p>';
  var known=cardSearchYtIdFromUrl(cardSearchState.popupUrl);
  var apis=[
    {kind:'piped',url:'https://pipedapi.ducks.party/search?q='+encodeURIComponent(q)+'&filter=videos'},
    {kind:'piped',url:'https://api.piped.private.coffee/search?q='+encodeURIComponent(q)+'&filter=videos'},
    {kind:'piped',url:'https://pipedapi.adminforge.de/search?q='+encodeURIComponent(q)+'&filter=videos'},
    {kind:'piped',url:'https://pipedapi.reallyaweso.me/search?q='+encodeURIComponent(q)+'&filter=videos'},
    {kind:'invidious',url:'https://inv.nadeko.net/api/v1/search?q='+encodeURIComponent(q)+'&type=video'},
    {kind:'invidious',url:'https://invidious.nerdvpn.de/api/v1/search?q='+encodeURIComponent(q)+'&type=video'}
  ];
  function finish(items){
    var ranked=rankSearchItems(items,function(it){return (it.title||'')+' '+(it.author||'');},{requireProduct:false});
    ranked=(ranked.length?ranked:(items||[])).filter(function(it){
      return it&&it.id&&cardSearchYtPlayUrl(it.id)&&!cardSearchYtIsBadEmbedUrl(cardSearchYtPlayUrl(it.id));
    }).slice(0,12);
    cardSearchState.ytItems=ranked;
    cardSearchState._ytTried={};
    cardSearchState._ytHostTried={};
    cardSearchState._ytPlayRetried=0;
    cardSearchState._ytHost='youtube';
    if(!ranked.length){
      showCardSearchFrame(false);
      renderCardYtList([]);
      cardSearchShowStatus('No embeddable YouTube videos for “'+(cardSearchState.name||q||'this library')+'”. Open the full search in a popup.');
      return;
    }
    var pick=ranked[0];
    if(known){
      var hit=ranked.filter(function(it){return it.id===known;})[0];
      if(hit)pick=hit;
    }
    // Bug1-fix: if user already triggered manual play (autoplay) don't overwrite the
    // live iframe with a fresh non-autoplaying one from the async search result.
    if(!cardSearchState._ytManualPlay){
      if(!setCardYtFrame(pick.id,'youtube'))cardSearchYtTryNext('bad id');
    }
    renderCardYtList(ranked,cardSearchState.ytId||pick.id);
    syncCardSearchLayout();
  }
  function tryAt(i){
    if(i>=apis.length){finish([]);return;}
    fetchJsonTimeout(apis[i].url,5000).then(function(data){
      var vids=apis[i].kind==='piped'?parsePipedVideos(data):parseInvidiousVideos(data);
      if(vids.length)finish(vids);
      else tryAt(i+1);
    }).catch(function(){tryAt(i+1);});
  }
  tryAt(0);
}
function cardSearchEnableBack(){
  var back=document.querySelector('#cardSearchEmbed .card-search-back');
  if(back){back.disabled=false;back.removeAttribute('disabled');}
  var step=document.querySelector('#cardSearchEmbed .card-search-iframe-back');
  if(step){
    var n=(cardSearchState&&cardSearchState.history||[]).length;
    var frame=document.getElementById('cardSearchFrame');
    var frameOn=!!(frame&&!frame.classList.contains('is-hidden')&&(frame.getAttribute('src')||''));
    var can=n>1||!!(cardSearchState&&(cardSearchState.view==='article'||cardSearchState.view==='image'||(cardSearchState.type==='yt'&&(cardSearchState.ytId||frameOn))));
    step.disabled=!can;
    if(can)step.removeAttribute('disabled');
    else step.setAttribute('disabled','');
  }
}
function cardSearchHistEq(a,b){
  if(a===b)return true;
  if(!a||!b)return false;
  if(typeof a==='string'||typeof b==='string')return String(a)===String(b);
  return (a.kind||'')===(b.kind||'')&&(a.view||'')===(b.view||'')&&(a.ytId||'')===(b.ytId||'')&&(a.embedUrl||'')===(b.embedUrl||'')&&a.i===b.i;
}
function cardSearchHistPush(snap){
  if(!cardSearchState.history)cardSearchState.history=[];
  var last=cardSearchState.history[cardSearchState.history.length-1];
  if(last&&cardSearchHistEq(last,snap))return;
  cardSearchState.history.push(snap);
  if(cardSearchState.history.length>40)cardSearchState.history.shift();
  cardSearchEnableBack();
}
function cardSearchApplyHist(snap){
  if(snap==null)return;
  if(typeof snap==='string'){
    if(snap==='results'){if(typeof cardSearchShowWebResults==='function')cardSearchShowWebResults();return;}
    if(snap==='grid'){if(window.cardSearchExitImage)window.cardSearchExitImage();return;}
    if(snap==='article'||snap==='image'||snap==='yt')return;
    var frame=document.getElementById('cardSearchFrame');
    cardSearchState.embedUrl=snap;
    if(frame){frame.src=snap;frame.classList.remove('is-hidden');}
    if(typeof showCardSearchFrame==='function')showCardSearchFrame(true);
    return;
  }
  var kind=snap.kind||snap.view||'';
  if(kind==='root'||kind==='yt-list'||kind==='grid'&&snap.type==='img'){
    if((cardSearchState.type==='yt'||kind==='yt-list'||kind==='root'&&cardSearchState.type==='yt')&&kind!=='grid'){
      if(typeof showCardSearchFrame==='function')showCardSearchFrame(false);
      if(typeof renderCardYtList==='function')renderCardYtList(cardSearchState.ytItems||[],'');
      cardSearchState.view='yt';
      return;
    }
  }
  if(kind==='yt'||snap.ytId){
    setCardYtFrame(snap.ytId,snap.host||'youtube',{noHist:1});
    if(typeof renderCardYtList==='function')renderCardYtList(cardSearchState.ytItems||[],snap.ytId);
    return;
  }
  if(kind==='article'||snap.view==='article'){
    var _p=cardSearchHistPush;cardSearchHistPush=function(){};
    try{if(typeof window.cardSearchOpenWebRow==='function')window.cardSearchOpenWebRow(snap.i);}finally{cardSearchHistPush=_p;}
    return;
  }
  if(kind==='results'||snap.view==='results'){
    if(typeof cardSearchShowWebResults==='function')cardSearchShowWebResults();
    return;
  }
  if(kind==='image'||snap.view==='image'){
    var _q=cardSearchHistPush;cardSearchHistPush=function(){};
    try{if(typeof window.cardSearchOpenImage==='function')window.cardSearchOpenImage(snap.i);}finally{cardSearchHistPush=_q;}
    return;
  }
  if(kind==='grid'||snap.view==='grid'){
    if(window.cardSearchExitImage)window.cardSearchExitImage();
  }
}

function cardSearchHost(){
  var host=document.getElementById('cardSearchEmbed');
  if(!host)return null;
  if(!document.getElementById('cardSearchPark')){
    var p=document.createElement('div');
    p.id='cardSearchPark';
    p.hidden=true;
    document.body.appendChild(p);
  }
  return {host:host,park:document.getElementById('cardSearchPark')};
}
function cardSearchReaderEl(){return document.getElementById('cardSearchReader');}
function showCardSearchReader(on){
  var reader=cardSearchReaderEl();
  if(!reader)return;
  reader.hidden=!on;
  reader.classList.toggle('open',!!on);
  if(!on)reader.innerHTML='';
}
function showCardSearchFrame(on){
  var frame=document.getElementById('cardSearchFrame');
  if(!frame)return;
  frame.classList.toggle('is-hidden',!on);
  if(!on){frame.removeAttribute('src');frame.src='about:blank';}
}
function resetCardSearchChrome(){
  var host=document.getElementById('cardSearchEmbed');
  var stage=document.getElementById('cardSearchStage');
  var imgView=document.getElementById('cardSearchImgView');
  var img=document.getElementById('cardSearchImgFit');
  var text=document.getElementById('cardYtCommentsText');
  if(host)host.classList.remove('is-img');
  if(stage){stage.classList.remove('yt-split','yt-wide');}
  if(imgView)imgView.classList.remove('open');
  if(img){img.removeAttribute('src');img.alt='';}
  if(text)text.textContent='Comments stay on YouTube.';
  showCardSearchReader(false);
  showCardSearchFrame(false);
}
function closeCardSearchEmbed(){
  cardSearchClearEmbedHint();
  var wrap=cardSearchHost();
  var fallback=document.getElementById('cardSearchFallback');
  if(fallback)fallback.classList.remove('open');
  resetCardSearchChrome();
  if(wrap&&wrap.host){
    wrap.host.hidden=true;
    if(wrap.park&&wrap.host.parentNode!==wrap.park)wrap.park.appendChild(wrap.host);
  }
  document.body.classList.remove('card-embed-open');
  cardSearchState={type:'',popupUrl:'',embedUrl:'',history:[],query:'',view:'',urls:{}};
  paintCardSearchSwitch();
}
window.closeCardSearchEmbed=closeCardSearchEmbed;
function cardSearchShowYtBlocked(reason){
  var fallback=document.getElementById('cardSearchFallback');
  var frame=document.getElementById('cardSearchFrame');
  var thumb='';
  var items=cardSearchState.ytItems||[];
  var cur=cardSearchState.ytId||'';
  for(var i=0;i<items.length;i++){
    if(items[i]&&items[i].id===cur&&items[i].thumb){thumb=items[i].thumb;break;}
  }
  if(!thumb&&items[0]&&items[0].thumb)thumb=items[0].thumb;
  if(frame){frame.classList.add('is-hidden');frame.removeAttribute('src');frame.style.display='none';}
  if(fallback){
    fallback.classList.add('open');
    var play='<svg viewBox="0 0 64 64" aria-hidden="true"><circle cx="32" cy="32" r="29" fill="rgba(0,0,0,.55)" stroke="currentColor" stroke-width="2"/><path d="M27 20.5v23L46 32z" fill="currentColor"/></svg>';
    var html='<div class="card-yt-blocked">';
    if(reason==='all-instances-tried'){
      if(thumb)html+='<img class="card-yt-blocked-img" src="'+cardSearchEsc(thumb)+'" alt="">';
      html+='<p class="card-yt-blocked-msg">All video sources tried. Use <strong>Open in popup</strong> above to watch.</p>';
      html+='<button type="button" class="card-yt-blocked-retry" aria-label="Try again" title="Try again" onclick="event.preventDefault();event.stopPropagation();cardSearchPlayYtFallback()">&#x21BA; Try again</button>';
    }else if(thumb){
      html+='<button type="button" class="card-yt-blocked-thumb" aria-label="Play video" title="Play" onclick="event.preventDefault();event.stopPropagation();cardSearchPlayYtFallback()">';
      html+='<img src="'+cardSearchEsc(thumb)+'" alt="">';
      html+='<span class="card-yt-blocked-play" aria-hidden="true">'+play+'</span></button>';
    }else{
      html+='<button type="button" class="card-yt-blocked-bare" aria-label="Play video" title="Play" onclick="event.preventDefault();event.stopPropagation();cardSearchPlayYtFallback()">'+play+'</button>';
    }
    html+='</div>';
    fallback.innerHTML=html;
  }else{
    cardSearchShowStatus('YouTube blocked in-card'+(reason?(' ('+reason+')'):'')+'. Use Open in popup from the header if needed.',false);
  }
}
window.cardSearchPlayYtFallback=function(){
  // Bug1-fix: mark that the user manually triggered playback so the pending
  // loadCardYtSearch async finish() does not overwrite the autoplaying iframe.
  cardSearchState._ytManualPlay=true;
  var id=cardSearchState.ytId||'';
  if(!id){
    var items=cardSearchState.ytItems||[];
    if(items[0]&&items[0].id)id=items[0].id;
  }
  // Play overlay: always retry in-card embed (same slot). Never auto-open popup.
  if(!id){
    cardSearchShowYtBlocked('no video id');
    return;
  }
  if(!cardSearchYtCanEmbedHere()){
    // file:// or null origin — YouTube embed blocked. Try Invidious instead
    // (open-source frontend, no Referer restriction, works from file://).
    cardSearchState._invInstances=['yewtu.be','invidious.nerdvpn.de','inv.nadeko.net','yt.artemislena.eu'];
    cardSearchState._invInstanceIdx=0;
    cardSearchState._ytHostTried={};
    cardSearchState._ytHost='invidious';
    if(!setCardYtFrame(id,'invidious',{autoplay:1})){
      cardSearchOpenPopup();
    }
    return;
  }
  cardSearchState._ytHostTried={};
  cardSearchState._ytHost='youtube';
  if(!setCardYtFrame(id,'youtube',{autoplay:1})){
    cardSearchShowYtBlocked('could not load embed');
  }
};
function cardSearchShowStatus(msg,showPopup){
  var reader=cardSearchReaderEl();
  if(!reader)return;
  showCardSearchReader(true);
  var html='<div class="card-search-status"><p>'+cardSearchEsc(msg)+'</p>';
  if(showPopup!==false)html+='<button type="button" onclick="event.preventDefault();event.stopPropagation();cardSearchOpenPopup()">'+cardSearchPopupLabel()+'</button>';
  html+='</div>';
  reader.innerHTML=html;
}
function flattenDdgTopics(topics,out){
  out=out||[];
  (topics||[]).forEach(function(t){
    if(!t)return;
    if(t.Topics)flattenDdgTopics(t.Topics,out);
    else if(t.FirstURL&&t.Text)out.push({url:t.FirstURL,title:String(t.Text).split(' - ')[0],snippet:t.Text});
  });
  return out;
}
function cardSearchRenderWeb(data){
  var reader=cardSearchReaderEl();
  if(!reader)return;
  var rows=flattenDdgTopics((data&&data.RelatedTopics)||[]);
  flattenDdgTopics((data&&data.Results)||[],rows);
  var abstract=data&&data.Abstract?String(data.Abstract):'';
  var absUrl=data&&data.AbstractURL?String(data.AbstractURL):'';
  var absTitle=(data&&(data.Heading||data.AbstractSource))||cardSearchState.query||'Result';
  if(abstract){
    rows.unshift({url:absUrl,title:absTitle,snippet:abstract,text:abstract,kind:'abstract'});
  }
  rows=rankSearchItems(rows,function(r){return (r.title||'')+' '+(r.snippet||'')+' '+(r.url||'');}).filter(function(r){
    var hay=((r.title||'')+' '+(r.snippet||'')+' '+(r.url||'')).toLowerCase();
    if(/duckduckgo|about duck|cia\.gov|soviet activities|arctic and antarctic/.test(hay))return false;
    return true;
  }).slice(0,16);
  cardSearchState.results=rows;
  cardSearchState.view='results';
  if(!rows.length){
    cardSearchShowStatus('No library-related web results for “'+(cardSearchState.name||cardSearchState.query||'this library')+'”. Open the full search in a popup if you want broader hits.');
    return;
  }
  showCardSearchReader(true);
  var html='<div class="card-search-results">';
  rows.forEach(function(r,i){
    html+='<button type="button" class="card-search-row" data-i="'+i+'" onclick="event.preventDefault();event.stopPropagation();cardSearchOpenWebRow('+i+')">';
    html+='<span class="card-search-row-title">'+cardSearchEsc(r.title||r.url||'Result')+'</span>';
    if(r.snippet)html+='<span class="card-search-row-snip">'+cardSearchEsc(r.snippet)+'</span>';
    html+='</button>';
  });
  html+='</div>';
  reader.innerHTML=html;
}
window.cardSearchOpenWebRow=function(i){
  var rows=cardSearchState.results||[];
  var row=rows[i];
  if(!row)return;
  var reader=cardSearchReaderEl();
  if(!reader)return;
  cardSearchState._openRow=row;
  cardSearchState.view='article';
  if(typeof cardSearchHistPush==='function')cardSearchHistPush({kind:'article',view:'article',type:cardSearchState.type||'web',i:i});
  else cardSearchState.history=['results','article'];
  var body=row.text||row.snippet||'';
  var msg=(row.text||row.kind==='abstract')?'':'This page cannot be shown inside the card.';
  var html='<div class="card-search-article"><h3>'+cardSearchEsc(row.title||'Result')+'</h3>';
  if(body)html+='<p>'+cardSearchEsc(body)+'</p>';
  if(msg)html+='<p>'+cardSearchEsc(msg)+'</p>';
  if(row.url)html+='<button type="button" onclick="event.preventDefault();event.stopPropagation();cardSearchOpenRowPopup()">Open</button>';
  html+='</div>';
  reader.innerHTML=html;
};
window.cardSearchOpenRowPopup=function(){
  var row=cardSearchState._openRow;
  if(row&&row.url)window.cardSearchOpenUrlPopup(row.url);
  else window.cardSearchOpenPopup();
};
function cardSearchShowWebResults(){
  if(cardSearchState._webData)cardSearchRenderWeb(cardSearchState._webData);
  else loadCardWebSearch(cardSearchState.query);
}
function cardSearchDdgHasRows(data){
  if(!data)return false;
  if(data.Abstract)return true;
  function count(topics){
    var n=0;
    (topics||[]).forEach(function(t){
      if(!t)return;
      if(t.Topics)n+=count(t.Topics);
      else if(t.FirstURL&&t.Text)n++;
    });
    return n;
  }
  return count(data.RelatedTopics)+count(data.Results)>0;
}
function fetchCardDdg(q){
  return fetch('https://api.duckduckgo.com/?q='+encodeURIComponent(q)+'&format=json&no_html=1&skip_disambig=1',{mode:'cors'}).then(function(r){
    if(!r.ok)throw new Error('HTTP '+r.status);
    return r.json();
  });
}
function wikiSnippetText(s){
  return String(s||'').replace(/<[^>]+>/g,' ').replace(/&quot;/g,'"').replace(/&#039;/g,"'").replace(/&amp;/g,'&').replace(/\s+/g,' ').replace(/^ | $/g,'');
}
function fetchCardWiki(q){
  var search='https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch='+encodeURIComponent(q)+'&srlimit=12&utf8=&format=json&origin=*';
  var open='https://en.wikipedia.org/w/api.php?action=opensearch&search='+encodeURIComponent(q)+'&limit=10&format=json&origin=*';
  return Promise.all([
    fetch(search,{mode:'cors'}).then(function(r){if(!r.ok)throw new Error('HTTP '+r.status);return r.json();}).catch(function(){return {};}),
    fetch(open,{mode:'cors'}).then(function(r){if(!r.ok)throw new Error('HTTP '+r.status);return r.json();}).catch(function(){return [];})
  ]).then(function(pair){
    var data=pair[0]||{};
    var os=pair[1]||[];
    var titles=os[1]||[];
    var descs=os[2]||[];
    if(!data.query)data.query={};
    if(!data.query.search)data.query.search=[];
    titles.forEach(function(t,i){
      if(data.query.search.some(function(h){return h.title===t;}))return;
      data.query.search.push({title:t, snippet:descs[i]||''});
    });
    return data;
  });
}
function wikiSearchToTopics(data){
  var hits=((data&&data.query&&data.query.search)||[]).map(function(h){
    var title=h.title||'Result';
    var snip=wikiSnippetText(h.snippet);
    return {FirstURL:'https://en.wikipedia.org/wiki/'+encodeURIComponent(title.replace(/ /g,'_')), Text:snip?(title+' - '+snip):title};
  });
  return {RelatedTopics:hits, Results:[], Abstract:'', Heading:''};
}
function fetchCardArchive(q){
  var url='https://archive.org/advancedsearch.php?q='+encodeURIComponent(q)+'&fl[]=identifier,title,description&rows=8&page=1&output=json';
  return fetchJsonTimeout(url,5000).then(function(d){
    var docs=((d&&d.response&&d.response.docs)||[]).map(function(doc){
      var title=doc.title||doc.identifier||'Archive';
      var snip=Array.isArray(doc.description)?doc.description[0]:(doc.description||'');
      if(typeof snip!=='string')snip='';
      return {FirstURL:'https://archive.org/details/'+encodeURIComponent(doc.identifier||''),Text:snip?(title+' - '+snip):title};
    });
    return {RelatedTopics:docs,Results:[],Abstract:'',Heading:''};
  });
}

function cardGoogleQuery(){
  var name=libraryDisplayName();
  var extra=catalogSearchExtra();
  var q=(name?(name+' '+extra):String(cardSearchState.query||'')).replace(/^\s+|\s+$/g,'');
  return q||extra;
}
function cardGooglePopupUrl(mode){
  var q=cardGoogleQuery();
  if(mode==='img')return 'https://www.google.com/search?tbm=isch&q='+encodeURIComponent(q);
  return 'https://www.google.com/search?q='+encodeURIComponent(q);
}
function cardGoogleEmbedUrl(mode){
  // Undocumented but widely used: igu=1 allows Search UI in a cross-origin iframe (no XFO).
  // udm=14 = Web results (skips AI Overview empty band); udm=2 = Images. nfpr=1 skips interstitial.
  // Official CSE needs a Programmable Search cx id; optional via window.CATALOG_GOOGLE_CSE_CX.
  var q=cardGoogleQuery();
  if(mode==='img')return 'https://www.google.com/search?igu=1&udm=2&tbm=isch&nfpr=1&hl=en&q='+encodeURIComponent(q);
  return 'https://www.google.com/search?igu=1&udm=14&nfpr=1&hl=en&q='+encodeURIComponent(q);
}
function cardGoogleCseCx(){
  try{
    if(window.CATALOG_GOOGLE_CSE_CX)return String(window.CATALOG_GOOGLE_CSE_CX);
    var ls=localStorage.getItem('catalog-google-cse-cx');
    if(ls)return String(ls);
  }catch(err){}
  return '';
}
function cardSearchShowGoogleFallback(mode,msg){
  var reader=cardSearchReaderEl();
  if(!reader)return;
  showCardSearchFrame(false);
  showCardSearchReader(true);
  var note=msg||('Google could not be embedded here. Open the full '+(mode==='img'?'image ':'')+'search in a popup.');
  reader.innerHTML='<div class="card-google-fallback"><p>'+cardSearchEsc(note)+'</p><button type="button" onclick="event.preventDefault();event.stopPropagation();cardSearchOpenPopup()">'+cardSearchPopupLabel()+'</button></div>';
}
function cardSearchMountGoogleIframe(mode){
  var frame=cardSearchEnsureYtFrame();
  var fallback=document.getElementById('cardSearchFallback');
  if(!frame){cardSearchShowGoogleFallback(mode);return false;}
  if(fallback)fallback.classList.remove('open');
  showCardSearchReader(false);
  var url=cardGoogleEmbedUrl(mode);
  cardSearchState.embedUrl=url;
  cardSearchState.popupUrl=cardGooglePopupUrl(mode);
  // No footer strip — header Open in popup already covers opening Google.
  frame.classList.remove('is-hidden');
  frame.classList.add('card-google-frame');
  frame.style.display='';
  frame.title=mode==='img'?'Google Images':'Google Search';
  frame.removeAttribute('allow');
  frame.setAttribute('referrerpolicy','strict-origin-when-cross-origin');
  try{frame.referrerPolicy='strict-origin-when-cross-origin';}catch(err){}
  frame.src=url;
  showCardSearchFrame(true);
  return true;
}
function cardSearchMountGoogleCse(mode){
  var cx=cardGoogleCseCx();
  if(!cx)return false;
  var reader=cardSearchReaderEl();
  if(!reader)return false;
  showCardSearchFrame(false);
  showCardSearchReader(true);
  var q=cardGoogleQuery();
  cardSearchState.popupUrl=cardGooglePopupUrl(mode);
  reader.innerHTML='<div class="card-google-cse" id="cardGoogleCse"><div id="cardGoogleCseHost"></div></div>';
  function render(){
    try{
      if(!(window.google&&google.search&&google.search.cse&&google.search.cse.element))return false;
      var host=document.getElementById('cardGoogleCseHost');
      if(!host)return false;
      host.innerHTML='';
      var attrs={enableImageSearch:true};
      if(mode==='img'){attrs.defaultToImageSearch=true;attrs.disableWebSearch=true;}
      google.search.cse.element.render({div:host,tag:'searchresults-only',gname:'cardGoogle',attributes:attrs});
      var el=google.search.cse.element.getElement('cardGoogle');
      if(el&&el.execute)el.execute(q);
      return true;
    }catch(err){return false;}
  }
  if(window.google&&google.search&&google.search.cse){render();return true;}
  var prev=window.__gcse;
  window.__gcse={parsetags:'explicit',callback:function(){render();}};
  var s=document.createElement('script');
  s.async=true;
  s.src='https://cse.google.com/cse.js?cx='+encodeURIComponent(cx);
  s.onerror=function(){cardSearchMountGoogleIframe(mode)||cardSearchShowGoogleFallback(mode);};
  document.head.appendChild(s);
  setTimeout(function(){
    if(!(window.google&&google.search&&google.search.cse)){
      if(prev)window.__gcse=prev;
      cardSearchMountGoogleIframe(mode)||cardSearchShowGoogleFallback(mode);
    }
  },4000);
  return true;
}
function loadCardGoogleSearch(mode){
  mode=mode==='img'?'img':'web';
  cardSearchState.view=mode==='img'?'grid':'results';
  if(typeof cardSearchHistPush==='function')cardSearchHistPush({kind:'root',view:cardSearchState.view,type:cardSearchState.type});
  else cardSearchState.history=[cardSearchState.view];
  cardSearchState.type=mode==='img'?'img':'web';
  cardSearchState.popupUrl=cardGooglePopupUrl(mode);
  var imgView=document.getElementById('cardSearchImgView');
  if(imgView)imgView.classList.remove('open');
  if(cardGoogleCseCx()&&cardSearchMountGoogleCse(mode))return;
  if(!cardSearchMountGoogleIframe(mode))cardSearchShowGoogleFallback(mode);
}

function loadCardWebSearch(query){
  loadCardGoogleSearch('web');
}
function cardSearchRenderImages(items){
  var reader=cardSearchReaderEl();
  if(!reader)return;
  cardSearchState.images=items||[];
  cardSearchState.view='grid';
  if(typeof cardSearchHistPush==='function')cardSearchHistPush({kind:'grid',view:'grid',type:'img'});
  else cardSearchState.history=['grid'];
  if(!items||!items.length){
    cardSearchShowStatus('No library-related images for “'+(cardSearchState.name||cardSearchState.query||'this library')+'”. Open the full image search in a popup if you want broader hits.');
    return;
  }
  showCardSearchReader(true);
  var html='<div class="card-search-grid">';
  items.forEach(function(it,i){
    html+='<button type="button" class="card-search-tile" data-i="'+i+'" onclick="event.preventDefault();event.stopPropagation();cardSearchOpenImage('+i+')">';
    html+='<img src="'+cardSearchEsc(it.thumb||it.url)+'" alt="'+cardSearchEsc(it.title||'')+'">';
    html+='</button>';
  });
  html+='</div>';
  reader.innerHTML=html;
}
window.cardSearchOpenImage=function(i){
  var items=cardSearchState.images||[];
  var it=typeof i==='number'?items[i]:null;
  var src=it? (it.url||it.thumb): (typeof i==='string'?i:'');
  var alt=it&&it.title?it.title:'';
  var view=document.getElementById('cardSearchImgView');
  var img=document.getElementById('cardSearchImgFit');
  if(!view||!img||!src)return;
  img.src=src;
  img.alt=alt;
  view.classList.add('open');
  cardSearchState.view='image';
  if(typeof cardSearchHistPush==='function')cardSearchHistPush({kind:'image',view:'image',type:'img',i:i,src:src});
  else cardSearchState.history=['grid','image'];
};
function loadCardImageSearch(query){
  loadCardGoogleSearch('img');
}
function collectSearchUrls(extra){
  extra=extra||{};
  var modal=document.getElementById('searchModal');
  var card=document.querySelector('.entry.selected')||lastViewedEntry;
  var btn=card&&card.querySelector?card.querySelector('.search-popup-btn'):null;
  var prev=cardSearchState.urls||{};
  return {
    yt:extra.yt||prev.yt||(modal&&modal._ytUrl)||(btn&&btn.dataset.yt)||'',
    web:extra.web||prev.web||(modal&&modal._webUrl)||(btn&&btn.dataset.web)||'',
    img:extra.img||prev.img||(modal&&modal._imgUrl)||(btn&&btn.dataset.img)||''
  };
}
function cardSearchUrlFor(type,urls){
  urls=urls||collectSearchUrls();
  if(type==='yt')return urls.yt||'';
  if(type==='img')return urls.img||'';
  return urls.web||'';
}
function cardSearchSwitchBarKey(){
  return 'catalog-embed-switch-bar-'+(window.CATALOG_NS||'catalog');
}
function cardSearchSwitchBarVisible(){
  try{
    var v=localStorage.getItem(cardSearchSwitchBarKey());
    if(v==='0'||v==='hidden')return false;
  }catch(err){}
  return true;
}
function syncCardSearchSwitchBar(){
  var show=cardSearchSwitchBarVisible();
  document.body.classList.toggle('card-switch-bar-hidden',!show);
  var btn=document.getElementById('cardSearchSwitchToggle');
  if(btn){
    btn.setAttribute('aria-pressed',show?'true':'false');
    var label=show?'Hide mode bar':'Show mode bar';
    btn.setAttribute('aria-label',label);
    btn.title=label;
  }
}
window.cardSearchToggleSwitchBar=function(){
  var show=!cardSearchSwitchBarVisible();
  try{localStorage.setItem(cardSearchSwitchBarKey(),show?'1':'0');}catch(err){}
  syncCardSearchSwitchBar();
};
function paintCardSearchSwitch(){
  var bar=document.getElementById('cardSearchSwitch');
  if(!bar)return;
  bar.querySelectorAll('[data-mode]').forEach(function(b){
    var on=!!cardSearchState.type&&b.getAttribute('data-mode')===cardSearchState.type;
    b.classList.toggle('is-active',on);
    b.setAttribute('aria-pressed',on?'true':'false');
  });
  syncCardSearchSwitchBar();
}
window.cardSearchSwitch=function(type){
  if(!type||!document.body.classList.contains('card-embed-open'))return;
  if(type===cardSearchState.type)return;
  var url=cardSearchUrlFor(type);
  if(!url)return;
  openCardSearchEmbed(type,url);
};
function cardSearchClearEmbedHint(){
  if(window._cardSearchHintT){try{clearTimeout(window._cardSearchHintT);}catch(err){} window._cardSearchHintT=null;}
  var el=document.getElementById('cardSearchHint');
  if(el){el.classList.remove('is-on');el.hidden=true;}
}
function cardSearchShowEmbedHint(){
  var el=document.getElementById('cardSearchHint');
  if(!el)return;
  cardSearchClearEmbedHint();
  el.hidden=false;
  el.classList.add('is-on');
  window._cardSearchHintT=setTimeout(function(){cardSearchClearEmbedHint();},5000);
}
window.cardSearchDismissEmbedHint=function(){
  cardSearchClearEmbedHint();
};
(function sortCatalogIndexList(){
  var list=document.getElementById('catalogIndexList');
  if(!list)return;
  var items=[].slice.call(list.querySelectorAll(':scope > li'));
  if(!items.length)return;
  items.sort(function(a,b){
    var ta=(a.textContent||'').trim();
    var tb=(b.textContent||'').trim();
    return ta.localeCompare(tb,undefined,{sensitivity:'base'});
  });
  items.forEach(function(li){list.appendChild(li);});
})();
window.toggleCatalogIndex=function(){
  var box=document.getElementById('catalogIndex');
  if(!box)return;
  var collapsed=box.classList.toggle('is-collapsed');

  var btn=document.getElementById('catalogIndexToggle');
  if(btn){
    btn.setAttribute('aria-expanded',collapsed?'false':'true');
    btn.setAttribute('aria-label',collapsed?'Expand index':'Collapse index');
    btn.title=collapsed?'Expand index':'Collapse index';
  }
  if(document.body.classList.contains('display-sides')){
    box.dataset.dockAuto='';
    box.dataset.dockPin=collapsed?'':'1';
    if(typeof writeModeSlot==='function')writeModeSlot({indexCollapsed:!!collapsed},'sides');
  }
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
};
function openCardSearchEmbed(type,popupUrl){
  var card=document.querySelector('.entry.selected')||lastViewedEntry;
  var wrap=cardSearchHost();
  if(!card||!wrap||!wrap.host||!popupUrl)return false;
  var urls=collectSearchUrls();
  if(type==='yt')urls.yt=popupUrl;
  else if(type==='img')urls.img=popupUrl;
  else urls.web=popupUrl;
  var name=(card.getAttribute('data-name')||'')||((document.getElementById('searchModalTitle')||{}).textContent||'');
  var query=cardSearchQuery(popupUrl,name);
  cardSearchState={type:type||'',popupUrl:popupUrl,embedUrl:'',history:[],query:query,name:name,view:'',results:[],images:[],_webData:null,urls:urls};
  if(wrap.host.parentNode!==card)card.appendChild(wrap.host);
  wrap.host.hidden=false;
  document.body.classList.add('card-embed-open');
  if(typeof window.parkSearchBehindOverlay==='function')window.parkSearchBehindOverlay();
  wrap.host.classList.toggle('is-img',type==='img');
  var title=document.getElementById('cardSearchTitle');
  if(title)title.textContent=type==='yt'?'YouTube':(type==='img'?'Images':'Web Search');
  var fallback=document.getElementById('cardSearchFallback');
  if(fallback)fallback.classList.remove('open');
  var imgView=document.getElementById('cardSearchImgView');
  if(imgView)imgView.classList.remove('open');
  cardSearchEnableBack();
  if(type==='yt'){
    showCardSearchReader(false);
    cardSearchState.ytItems=[];
    cardSearchState.ytId='';
    cardSearchState._ytTried={};
    cardSearchState._ytHostTried={};
    cardSearchState._ytHost='youtube';
    var known=cardSearchYtIdFromUrl(popupUrl);
    if(known)setCardYtFrame(known,'youtube');
    else showCardSearchFrame(false);
    loadCardYtSearch(query);
  }else if(type==='img'){
    showCardSearchFrame(false);
    loadCardImageSearch(query);
  }else{
    showCardSearchFrame(false);
    loadCardWebSearch(query);
  }
  paintCardSearchSwitch();
  syncCardSearchLayout();
  cardSearchShowEmbedHint();
  return true;
}
window.cardSearchBack=function(){
  var frame=document.getElementById('cardSearchFrame');
  if(typeof closeCardSearchEmbed==='function')closeCardSearchEmbed();
};
window.cardSearchReload=function(){
  cardSearchEnableBack();
  var frame=document.getElementById('cardSearchFrame');
  if(cardSearchState.type==='yt'){
    // Reload the currently visible YT page; fall back to root only when no embedUrl
    if(cardSearchState.embedUrl&&frame&&!frame.classList.contains('is-hidden')){
      frame.src=cardSearchState.embedUrl;
    }else{
      loadCardYtSearch(cardSearchState.query);
    }
    return;
  }
  if(cardSearchState.type==='img'){
    window.cardSearchExitImage();
    loadCardImageSearch(cardSearchState.query);
    return;
  }
  // web: reload the article iframe if visible, else reload results from scratch
  if(cardSearchState.view==='article'&&frame&&!frame.classList.contains('is-hidden')&&cardSearchState.embedUrl){
    frame.src=cardSearchState.embedUrl;
    return;
  }
  loadCardWebSearch(cardSearchState.query);
};
window.cardSearchOpenPopup=function(){
  var url=cardSearchState.popupUrl;
  if(!url)return;
  var type=cardSearchState.type||'web';
  var modal=document.getElementById('searchModal');
  if(modal){
    if(type==='yt')modal._ytUrl=url;
    else if(type==='img')modal._imgUrl=url;
    else modal._webUrl=url;
  }
  window._cardSearchForcePopup=true;
  window.openPopup({href:url},type);
};
window.cardSearchOpenUrlPopup=function(url){
  if(!url){window.cardSearchOpenPopup();return;}
  var type=cardSearchState.type||'web';
  var modal=document.getElementById('searchModal');
  if(modal){
    if(type==='yt')modal._ytUrl=url;
    else if(type==='img')modal._imgUrl=url;
    else modal._webUrl=url;
  }
  window._cardSearchForcePopup=true;
  window.openPopup({href:url},type);
};
window.cardSearchToggleFullscreen=function(){
  var host=document.getElementById('cardSearchEmbed');
  if(!host)return;
  var fsEl=document.fullscreenElement||document.webkitFullscreenElement||null;
  if(fsEl===host){
    if(document.exitFullscreen)document.exitFullscreen();
    else if(document.webkitExitFullscreen)document.webkitExitFullscreen();
  }else{
    if(host.requestFullscreen)host.requestFullscreen();
    else if(host.webkitRequestFullscreen)host.webkitRequestFullscreen(Element.ALLOW_KEYBOARD_INPUT||1);
  }
};
(function(){
  function _syncCardFsBtn(){
    var btn=document.getElementById('cardSearchFsBtn');
    if(!btn)return;
    var host=document.getElementById('cardSearchEmbed');
    var active=!!(host&&(document.fullscreenElement===host||document.webkitFullscreenElement===host));
    btn.setAttribute('aria-pressed',active?'true':'false');
    btn.title=active?'Exit fullscreen':'Fullscreen';
    btn.setAttribute('aria-label',active?'Exit fullscreen':'Fullscreen');
  }
  document.addEventListener('fullscreenchange',_syncCardFsBtn);
  document.addEventListener('webkitfullscreenchange',_syncCardFsBtn);
})();
window.syncCardSearchTheme=function(){
  if(!document.body.classList.contains('card-embed-open')||!cardSearchState.popupUrl)return;
  if(cardSearchState.type==='yt'){
    var next=cardSearchYtEmbedUrl(cardSearchState.popupUrl,cardSearchState.query);
    if(next===cardSearchState.embedUrl)return;
    cardSearchState.embedUrl=next;
    if(typeof cardSearchHistPush==='function')cardSearchHistPush({kind:'yt',type:'yt',view:'yt',ytId:cardSearchState.ytId,embedUrl:next,host:cardSearchState._ytHost});
    else cardSearchState.history=[next];
    var frame=document.getElementById('cardSearchFrame');
    if(frame)frame.src=next;
  }
  syncCardSearchLayout();
};
window.shouldEmbedCardSearch=function(){
  return document.body.classList.contains('chosen-preview-open')&&!document.body.classList.contains('hl-open')&&!window._cardSearchForcePopup;
};
function cardSearchIsLandscape(){
  try{
    if(window.matchMedia&&window.matchMedia('(orientation: landscape)').matches)return true;
  }catch(err){}
  return window.innerWidth>window.innerHeight;
}
function fillYtCommentsStrip(){
  var text=document.getElementById('cardYtCommentsText');
  var q=cardSearchState.query||queryFromSearchUrl(cardSearchState.popupUrl)||'';
  if(text)text.textContent=q?('Comments for “'+q+'” stay on YouTube.'):'Comments stay on YouTube.';
}
function syncCardSearchLayout(){
  var host=document.getElementById('cardSearchEmbed');
  var stage=document.getElementById('cardSearchStage');
  if(host)host.classList.toggle('is-img',cardSearchState.type==='img');
  if(!stage)return;
  var yt=cardSearchState.type==='yt'&&document.body.classList.contains('card-embed-open');
  var land=cardSearchIsLandscape();
  stage.classList.toggle('yt-split',!!(yt&&!land));
  stage.classList.toggle('yt-wide',!!(yt&&land));
  if(yt){fillYtCommentsStrip();cardRestoreYtListState();}
}
var _YT_LIST_KEY='catalog-yt-list-hidden-'+(window.CATALOG_NS||'catalog');
function cardApplyYtListState(hidden){
  var stage=document.getElementById('cardSearchStage');
  var btn=document.getElementById('cardYtListToggle');
  if(stage)stage.classList.toggle('yt-list-collapsed',!!hidden);
  if(btn){
    btn.setAttribute('aria-label',hidden?'Show video list':'Hide video list');
    btn.title=hidden?'Expand list':'Collapse list';
    btn.textContent=hidden?'\u203a':'\u2039';
  }
}
window.cardToggleYtList=function(){
  var stage=document.getElementById('cardSearchStage');
  var hidden=stage&&stage.classList.contains('yt-list-collapsed');
  var next=!hidden;
  try{localStorage.setItem(_YT_LIST_KEY,next?'1':'');}catch(err){}
  cardApplyYtListState(next);
};
function cardRestoreYtListState(){
  var saved='';
  try{saved=localStorage.getItem(_YT_LIST_KEY)||'';}catch(err){}
  cardApplyYtListState(!!saved);
}
window.cardSearchIframeBack=function(){
  var frame=document.getElementById('cardSearchFrame');
  if(!cardSearchState.history)cardSearchState.history=[];
  if(cardSearchState.history.length>1){
    cardSearchState.history.pop();
    var prev=cardSearchState.history[cardSearchState.history.length-1];
    if(typeof cardSearchApplyHist==='function')cardSearchApplyHist(prev);
    else if(typeof prev==='string'&&frame){cardSearchState.embedUrl=prev;frame.src=prev;}
    cardSearchEnableBack();
    return;
  }
  if(frame&&!frame.classList.contains('is-hidden')&&frame.contentWindow){
    try{
      if(frame.contentWindow.history&&frame.contentWindow.history.length>1){
        frame.contentWindow.history.back();
        cardSearchEnableBack();
        return;
      }
    }catch(err){}
  }
  if(cardSearchState.type==='yt'){
    if(typeof showCardSearchFrame==='function')showCardSearchFrame(false);
    if(typeof renderCardYtList==='function')renderCardYtList(cardSearchState.ytItems||[],'');
    cardSearchEnableBack();
    return;
  }
  if(cardSearchState.type==='img'){
    if(window.cardSearchExitImage)window.cardSearchExitImage();
    cardSearchEnableBack();
    return;
  }
  if(typeof cardSearchShowWebResults==='function')cardSearchShowWebResults();
  cardSearchEnableBack();
};
window.syncCardSearchLayout=syncCardSearchLayout;
window.cardSearchExitImage=function(){
  var view=document.getElementById('cardSearchImgView');
  var img=document.getElementById('cardSearchImgFit');
  if(view)view.classList.remove('open');
  if(img){img.removeAttribute('src');img.alt='';}
  cardSearchState.view='grid';
  if(cardSearchState.history&&cardSearchState.history.length){
    var _last=cardSearchState.history[cardSearchState.history.length-1];
    var _isImg=_last==='image'||(_last&&(_last.kind==='image'||_last.view==='image'));
    if(_isImg)cardSearchState.history.pop();
  }
};
(function(){
  function onOrient(){if(typeof window.syncCardSearchLayout==='function')window.syncCardSearchLayout();}
  window.addEventListener('orientationchange',onOrient);
  window.addEventListener('resize',onOrient);
  if(window.visualViewport)window.visualViewport.addEventListener('resize',onOrient);
  try{
    var mq=window.matchMedia('(orientation: landscape)');
    if(mq.addEventListener)mq.addEventListener('change',onOrient);
    else if(mq.addListener)mq.addListener(onOrient);
  }catch(err){}
})();

var FAV_KEY='catalog-fav-'+(window.CATALOG_NS||'catalog');
var NOTES_KEY='catalog-notes-'+(window.CATALOG_NS||'catalog');
var SEARCH_COMMIT_KEY='catalog-search-commits-'+(window.CATALOG_NS||'catalog');
function lsGet(key,fallback){
  try{
    var raw=localStorage.getItem(key);
    if(raw==null||raw==='')return fallback;
    var v=JSON.parse(raw);
    return v==null?fallback:v;
  }catch(err){return fallback;}
}
function lsSet(key,val){try{localStorage.setItem(key,JSON.stringify(val));}catch(err){}}
var favSet={};
(function(){var arr=lsGet(FAV_KEY,[]);if(Array.isArray(arr))arr.forEach(function(n){if(n)favSet[n]=1;});})();
var searchCommitCounts=lsGet(SEARCH_COMMIT_KEY,{});
if(!searchCommitCounts||typeof searchCommitCounts!=='object'||Array.isArray(searchCommitCounts))searchCommitCounts={};
var PIN_SESS_KEY='catalog-pin-sessions-'+(window.CATALOG_NS||'catalog');
var KW_COMBO_KEY='catalog-kw-combos-'+(window.CATALOG_NS||'catalog');
var CARD_HIT_KEY='catalog-card-hits-'+(window.CATALOG_NS||'catalog');
var RECENT_KW_KEY='catalog-recent-kws-'+(window.CATALOG_NS||'catalog');
var PIN_SESS_MAX=12;
var KW_COMBO_MAX=12;
var KW_COMBO_AUTO_MAX=10;
var pinSessionStore=lsGet(PIN_SESS_KEY,{sessions:[],recent:[]});
if(!pinSessionStore||typeof pinSessionStore!=='object')pinSessionStore={sessions:[],recent:[]};
if(!Array.isArray(pinSessionStore.sessions))pinSessionStore.sessions=[];
if(!Array.isArray(pinSessionStore.recent))pinSessionStore.recent=[];
var kwComboStore=lsGet(KW_COMBO_KEY,[]);
if(!Array.isArray(kwComboStore))kwComboStore=[];
var cardHitStore=lsGet(CARD_HIT_KEY,{});
if(!cardHitStore||typeof cardHitStore!=='object'||Array.isArray(cardHitStore))cardHitStore={};
var recentKwStore=lsGet(RECENT_KW_KEY,[]);
if(!Array.isArray(recentKwStore))recentKwStore=[];
function persistPinSessions(){lsSet(PIN_SESS_KEY,{sessions:pinSessionStore.sessions.slice(0,PIN_SESS_MAX),recent:(pinSessionStore.recent||[]).slice(0,6)});}
function kwComboKey(pills){return (pills||[]).map(function(x){return String(x).toLowerCase();}).sort().join('\u001f');}
function kwSavedCombos(){return (kwComboStore||[]).filter(function(o){return o&&o.saved;});}
function kwAutoCombos(){return (kwComboStore||[]).filter(function(o){return o&&!o.saved;});}
function persistKwCombos(){
  var maxS=typeof KW_COMBO_MAX==='number'?KW_COMBO_MAX:12;
  var maxA=typeof KW_COMBO_AUTO_MAX==='number'?KW_COMBO_AUTO_MAX:10;
  var saved=kwSavedCombos().slice().sort(function(a,b){return (b.usedAt||b.savedAt||b.t||0)-(a.usedAt||a.savedAt||a.t||0);}).slice(0,maxS);
  var auto=kwAutoCombos().slice(0,maxA);
  kwComboStore=saved.concat(auto);
  lsSet(KW_COMBO_KEY,kwComboStore);
}

function persistCardHits(){
  var keys=Object.keys(cardHitStore||{});
  if(keys.length>80){
    keys.sort(function(a,b){var A=cardHitStore[a]||{},B=cardHitStore[b]||{};return (B.n||0)-(A.n||0)||(B.t||0)-(A.t||0);});
    var keep={};keys.slice(0,80).forEach(function(k){keep[k]=cardHitStore[k];});
    cardHitStore=keep;
  }
  lsSet(CARD_HIT_KEY,cardHitStore);
}
function persistRecentKws(){lsSet(RECENT_KW_KEY,recentKwStore.slice(0,10));}
function isLibraryNameQuery(text){
  var t=String(text||'').replace(/^\s+|\s+$/g,'').toLowerCase();
  if(!t)return false;
  if(typeof searchMeta!=='undefined'&&searchMeta[t]&&searchMeta[t].isLibName)return true;
  try{
    if(typeof entries!=='undefined'){
      for(var i=0;i<entries.length;i++){
        var n=(typeof entryName==='function'?entryName(entries[i]):(entries[i].getAttribute&&entries[i].getAttribute('data-name')))||'';
        if(String(n).toLowerCase()===t)return true;
      }
    }
  }catch(err){}
  return false;
}
function recordRecentKeyword(text){
  var t=String(text||'').replace(/^\s+|\s+$/g,'');
  if(!t||isLibraryNameQuery(t))return;
  recentKwStore=recentKwStore.filter(function(x){return String(x).toLowerCase()!==t.toLowerCase();});
  recentKwStore.unshift(t);
  persistRecentKws();
}
function snapshotKwCombo(){
  var pills=(typeof searchKeywords!=='undefined'&&searchKeywords&&searchKeywords.length)?searchKeywords.slice():[];
  if(!pills.length)return;
  var key=typeof kwComboKey==='function'?kwComboKey(pills):pills.map(function(x){return String(x).toLowerCase();}).sort().join('\u001f');
  kwComboStore=kwComboStore.filter(function(o){return o&&(o.saved||o.key!==key);});
  kwComboStore.unshift({key:key,pills:pills.slice(),t:Date.now(),saved:0});
  persistKwCombos();
}
function recordCardHit(el){
  if(!el)return;
  var id=el.id||'';
  var name=(typeof entryName==='function'?entryName(el):(el.getAttribute&&el.getAttribute('data-name')))||'';
  if(!id&&!name)return;
  var k=id||name;
  var cur=cardHitStore[k]||{id:id,name:name,n:0,t:0};
  cur.id=id||cur.id;cur.name=name||cur.name;cur.n=(cur.n||0)+1;cur.t=Date.now();
  cardHitStore[k]=cur;
  persistCardHits();
}
function pinTinKindOf(item){
  if(!item)return 'preview';
  if(item.kind==='highlight'||item.mode==='highlight')return 'highlight';
  return 'preview';
}
function snapshotPinSessionCards(){
  var max=typeof cardMinCap==='function'?cardMinCap():(typeof CARD_MIN_MAX==='number'?CARD_MIN_MAX:9);
  var cards=[];
  var seen={};
  function add(it){
    if(!it||!it.id)return;
    var kind=pinTinKindOf(it);
    var k=String(it.id)+'|'+kind;
    if(seen[k])return;
    seen[k]=1;
    cards.push({id:it.id,mode:it.mode||kind,kind:kind,name:it.name||''});
  }
  (typeof cardMinDockItems!=='undefined'?cardMinDockItems:[]).forEach(add);
  var front=typeof cardMinExpanded==='function'?cardMinExpanded():null;
  if(front&&front.id){
    add({
      id:front.id,
      mode:typeof cardMinMode==='function'?cardMinMode(front):'preview',
      kind:typeof cardMinTinKind==='function'?cardMinTinKind(front):'preview',
      name:typeof cardMinShortName==='function'?cardMinShortName(front):''
    });
  }
  if(cards.length>max)cards=cards.slice(-max);
  return cards;
}
function pinFrontIntoDock(){
  var front=typeof cardMinExpanded==='function'?cardMinExpanded():null;
  if(!front||!front.id)return;
  var kind=typeof cardMinTinKind==='function'?cardMinTinKind(front):'preview';
  if(typeof cardMinIndex==='function'&&cardMinIndex(front.id,kind)>=0)return;
  var rec={id:front.id,mode:typeof cardMinMode==='function'?cardMinMode(front):'preview',kind:kind,name:typeof cardMinShortName==='function'?cardMinShortName(front):''};
  var max=typeof cardMinCap==='function'?cardMinCap():(typeof CARD_MIN_MAX==='number'?CARD_MIN_MAX:9);
  if(cardMinDockItems.length>=max){
    var drop=cardMinDockItems[0];
    if(drop)cardMinClose(drop.id,true,drop.kind||(drop.mode==='highlight'?'highlight':'preview'));
  }
  cardMinDockItems.push(rec);
  if(typeof cardMinRender==='function')cardMinRender();
}
function pinSessionId(){return 's'+Date.now().toString(36)+Math.floor(Math.random()*1e4).toString(36);}
window.savePinSession=function(name){
  name=String(name||'').replace(/^\s+|\s+$/g,'');
  if(!name)return false;
  if(typeof pinFrontIntoDock==='function')pinFrontIntoDock();
  var cards=snapshotPinSessionCards();
  if(!cards.length)return false;
  var front=typeof cardMinExpanded==='function'?cardMinExpanded():null;
  var rec={id:pinSessionId(),name:name,savedAt:Date.now(),usedAt:Date.now(),cards:cards,frontId:front&&front.id||(cards[cards.length-1]&&cards[cards.length-1].id)||'',frontKind:front?cardMinTinKind(front):(cards[cards.length-1]&&(cards[cards.length-1].kind||cards[cards.length-1].mode))||'preview'};
  var exist=-1;
  pinSessionStore.sessions.forEach(function(s,i){if(s&&String(s.name).toLowerCase()===name.toLowerCase())exist=i;});
  if(exist>=0){rec.id=pinSessionStore.sessions[exist].id;pinSessionStore.sessions[exist]=rec;}
  else{
    if(pinSessionStore.sessions.length>=PIN_SESS_MAX){
      pinSessionStore.sessions.sort(function(a,b){return (a.usedAt||a.savedAt||0)-(b.usedAt||b.savedAt||0);});
      pinSessionStore.sessions.shift();
    }
    pinSessionStore.sessions.push(rec);
  }
  touchPinSession(rec.id);
  persistPinSessions();

  return true;
};
function touchPinSession(id){
  pinSessionStore.recent=(pinSessionStore.recent||[]).filter(function(x){return x!==id;});
  pinSessionStore.recent.unshift(id);
  pinSessionStore.recent=pinSessionStore.recent.slice(0,6);
  pinSessionStore.sessions.forEach(function(s){if(s&&s.id===id)s.usedAt=Date.now();});
}
window.restorePinSession=function(id,ev){
  if(ev&&ev.stopPropagation){ev.preventDefault();ev.stopPropagation();}
  id=String(id||'');
  if(!id)return;
  if(window._pinSessLock===id)return;
  window._pinSessLock=id;
  setTimeout(function(){if(window._pinSessLock===id)window._pinSessLock='';},400);
  var sess=null;
  (pinSessionStore.sessions||[]).forEach(function(s){if(s&&s.id===id)sess=s;});
  if(!sess||!sess.cards)return;
  touchPinSession(id);persistPinSessions();
  if(typeof hideSearchAc==='function')hideSearchAc();
  var ac=document.getElementById('acList');
  if(ac){ac.classList.remove('open');ac.innerHTML='';}
  var cur=typeof cardMinExpanded==='function'?cardMinExpanded():null;
  if(cur){
    if(document.body.classList.contains('hl-open')||(cur.classList&&cur.classList.contains('highlight'))){
      if(typeof closeOverlay==='function')closeOverlay({skipScroll:true});
    }else if(document.body.classList.contains('chosen-preview-open')&&typeof closeChosenPreview==='function'){
      closeChosenPreview({skipJumpExit:true,skipDismiss:true,keepMedia:true});
    }
  }
  cardMinDockItems=[];
  sess.cards.forEach(function(c){
    if(!c||!c.id)return;
    cardMinDockItems.push({id:c.id,mode:c.mode||c.kind||'preview',kind:c.kind||(c.mode==='highlight'?'highlight':'preview'),name:c.name||''});
  });
  var maxDock=typeof cardMinCap==='function'?cardMinCap():(typeof CARD_MIN_MAX==='number'?CARD_MIN_MAX:9);
  while(cardMinDockItems.length>maxDock)cardMinDockItems.shift();
  var frontId=sess.frontId||(sess.cards[sess.cards.length-1]&&sess.cards[sess.cards.length-1].id);
  var frontKind=sess.frontKind||'preview';
  var inDock=false;
  cardMinDockItems.forEach(function(c){if(c&&c.id===frontId&&pinTinKindOf(c)===frontKind)inDock=true;});
  if(frontId&&!inDock){
    cardMinDockItems.push({id:frontId,mode:frontKind,kind:frontKind,name:''});
    var max=typeof cardMinCap==='function'?cardMinCap():(typeof CARD_MIN_MAX==='number'?CARD_MIN_MAX:9);
    if(cardMinDockItems.length>max)cardMinDockItems.shift();
  }
  if(typeof cardMinRender==='function')cardMinRender();
  setTimeout(function(){
    var dock=document.getElementById('cardMinDock');
    if(dock&&cardMinDockItems.length)dock.classList.add('is-on');
    if(typeof cardMinPlace==='function')cardMinPlace();
  },0);
};
(function(){
  if(window._pinSessAcBind)return;
  window._pinSessAcBind=1;
  document.addEventListener('pointerdown',function(e){
    var row=e.target&&e.target.closest&&e.target.closest('.ac-item');
    if(!row)return;
    window._acItemPointer=1;
    if(!row.classList.contains('ac-session'))return;
    var id=row.getAttribute('data-sid');
    if(!id){
      var m=String(row.getAttribute('onclick')||'').match(/restorePinSession\('([^']+)'/);
      id=m&&m[1];
    }
    if(id&&typeof restorePinSession==='function')restorePinSession(id,e);
  },true);
  document.addEventListener('mousedown',function(e){
    if(e.target&&e.target.closest&&e.target.closest('#acList .ac-item,.search-autocomplete .ac-item'))e.preventDefault();
  },true);
  document.addEventListener('pointerup',function(){
    setTimeout(function(){window._acItemPointer=0;},250);
  },true);
})();
window.deletePinSession=function(id){
  pinSessionStore.sessions=(pinSessionStore.sessions||[]).filter(function(s){return s&&s.id!==id;});
  pinSessionStore.recent=(pinSessionStore.recent||[]).filter(function(x){return x!==id;});
  persistPinSessions();
};
window.applyKwCombo=function(key,ev){
  if(ev&&ev.stopPropagation){ev.preventDefault();ev.stopPropagation();}
  var hit=null;
  (kwComboStore||[]).forEach(function(o){if(o&&(o.key===key||o.id===key))hit=o;});
  if(!hit||!hit.pills)return;
  if(hit.saved){hit.usedAt=Date.now();if(typeof persistKwCombos==='function')persistKwCombos();}
  if(typeof hideSearchAc==='function')hideSearchAc();
  var ac=document.getElementById('acList');
  if(ac){ac.classList.remove('open');ac.innerHTML='';}
  if(typeof setMode==='function')setMode('search');
  searchKeywords=hit.pills.slice();
  if(typeof renderPills==='function')renderPills();
  if(typeof applySearch==='function')applySearch();
  if(typeof renderKwBar==='function')renderKwBar();
};
window.saveKwCombo=function(name){
  name=String(name||'').replace(/^\s+|\s+$/g,'');
  var pills=(typeof searchKeywords!=='undefined'&&searchKeywords)?searchKeywords.slice():[];
  if(!pills.length)return false;
  if(!name)name=pills.join(' + ');
  var key=typeof kwComboKey==='function'?kwComboKey(pills):pills.map(function(x){return String(x).toLowerCase();}).sort().join('\u001f');
  var rec={id:'c'+Date.now().toString(36)+Math.floor(Math.random()*1e4).toString(36),key:key,pills:pills.slice(),name:name,saved:1,savedAt:Date.now(),usedAt:Date.now(),t:Date.now()};
  var exist=-1;
  kwComboStore.forEach(function(o,i){if(o&&o.saved&&(o.key===key||String(o.name||'').toLowerCase()===name.toLowerCase()))exist=i;});
  if(exist>=0){rec.id=kwComboStore[exist].id||rec.id;kwComboStore[exist]=rec;}
  else{
    var maxS=typeof KW_COMBO_MAX==='number'?KW_COMBO_MAX:12;
    var saved=kwSavedCombos();
    if(saved.length>=maxS){
      saved.sort(function(a,b){return (a.usedAt||a.savedAt||a.t||0)-(b.usedAt||b.savedAt||b.t||0);});
      var drop=saved[0];
      kwComboStore=kwComboStore.filter(function(o){return o!==drop;});
    }
    kwComboStore.unshift(rec);
  }
  kwComboStore=kwComboStore.filter(function(o){return !(o&&!o.saved&&o.key===key);});
  persistKwCombos();
  return true;
};
function defaultKwComboName(){return ((typeof searchKeywords!=='undefined'&&searchKeywords)?searchKeywords:[]).join(' + ');}
function placeKwComboSavePop(){
  var pop=document.getElementById('kwComboSavePop'),btn=document.getElementById('kwComboSave');
  if(!pop||!btn)return;
  var br=btn.getBoundingClientRect();
  pop.style.position='fixed';pop.style.zIndex='10050';
  var w=Math.max(224,pop.getBoundingClientRect().width||224);
  var left=Math.max(8,Math.min((window.innerWidth||800)-w-8,br.right-w));
  var top=br.bottom+6;
  if(top+148>(window.innerHeight||800))top=Math.max(8,br.top-148);
  pop.style.left=Math.round(left)+'px';pop.style.top=Math.round(top)+'px';
}
function parkKwComboSave(){
  var strip=document.getElementById('searchStrip');
  var pills=document.getElementById('searchPills');
  var btn=document.getElementById('kwComboSave');
  if(!btn){
    btn=document.createElement('button');
    btn.type='button';btn.id='kwComboSave';btn.className='kw-combo-save';
    btn.textContent='Save';
    btn.setAttribute('aria-label','Save keyword combination');
    btn.title='Save current pills as a named combination';
    document.body.appendChild(btn);
  }
  var pop=document.getElementById('kwComboSavePop');
  if(!pop){
    pop=document.createElement('div');
    pop.id='kwComboSavePop';pop.hidden=true;pop.className='kw-combo-save-pop';
    pop.innerHTML='<input id="kwComboSaveName" type="text" maxlength="40" placeholder="Combination name" autocomplete="off"><button type="button" id="kwComboSaveGo">Save combination</button>';
    document.body.appendChild(pop);
  }
  var n=(typeof searchKeywords!=='undefined'&&searchKeywords)?searchKeywords.length:0;
  btn.hidden=n<1;
  if(n<1){pop.hidden=true;return;}
  var pillsOn=false;
  if(pills){
    var cs=getComputedStyle(pills);
    pillsOn=cs.display!=='none'&&cs.visibility!=='hidden'&&pills.offsetParent!==null;
  }
  var host=pillsOn?pills:strip;
  if(host&&btn.parentElement!==host)host.appendChild(btn);
}
window.openKwComboSave=function(ev){
  if(ev&&ev.stopPropagation){ev.preventDefault();ev.stopPropagation();}
  if(!(typeof searchKeywords!=='undefined'&&searchKeywords&&searchKeywords.length))return;
  if(typeof parkKwComboSave==='function')parkKwComboSave();
  var pop=document.getElementById('kwComboSavePop'),inp=document.getElementById('kwComboSaveName');
  if(!pop||!inp)return;
  pop.hidden=!pop.hidden;
  if(!pop.hidden){
    inp.value=defaultKwComboName().slice(0,40);
    placeKwComboSavePop();
    try{inp.focus();inp.select();}catch(err){}
  }
};
window.openCardHit=function(id){
  var el=id&&document.getElementById(id);
  if(!el)return;
  if(typeof openChosenPreview==='function')openChosenPreview(el);
};
function catalogHistMatch(label,q){
  if(!q)return true;
  return String(label||'').toLowerCase().indexOf(q)>=0;
}
function catalogAcHistoryHtml(q){
  var html='',q=String(q||'').toLowerCase();
  function jsStr(s){return String(s||'').replace(/\\/g,'\\\\').replace(/'/g,"\\'");}
  function htmlStr(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
  var gqHist=typeof acGroupQuery==='function'?acGroupQuery(q):'';
  var sessions=(pinSessionStore.sessions||[]).slice().sort(function(a,b){return (b.usedAt||b.savedAt||0)-(a.usedAt||a.savedAt||0);}).filter(function(s){return s&&(gqHist==='session'||catalogHistMatch(s.name,q));});
  var saved=sessions.slice(0,PIN_SESS_MAX);
  if(saved.length){
    html+='<div class="ac-group-label" data-cat="session">Saved sessions</div>';
    saved.forEach(function(s){
      html+='<div class="ac-item ac-session" data-cat="session" data-sid="'+htmlStr(s.id)+'" onclick="restorePinSession(\''+jsStr(s.id)+'\',event)"><span class="ac-label">'+htmlStr(s.name||'Session')+'</span><span class="ac-count">'+(s.cards&&s.cards.length||0)+'</span></div>';
    });
  }
  if((pinSessionStore.sessions||[]).length>6){
    var recentIds=pinSessionStore.recent||[];
    var savedIds={};saved.forEach(function(s){savedIds[s.id]=1;});
    var rec=[];
    recentIds.forEach(function(id){
      var s=null;(pinSessionStore.sessions||[]).forEach(function(x){if(x&&x.id===id)s=x;});
      if(s&&catalogHistMatch(s.name,q)&&rec.length<6)rec.push(s);
    });
    if(rec.length){
      html+='<div class="ac-group-label" data-cat="session">Recent sessions</div>';
      rec.forEach(function(s){
        html+='<div class="ac-item ac-session" data-cat="session" data-sid="'+htmlStr(s.id)+'" onclick="restorePinSession(\''+jsStr(s.id)+'\',event)"><span class="ac-label">'+htmlStr(s.name||'Session')+'</span><span class="ac-count">'+(s.cards&&s.cards.length||0)+'</span></div>';
      });
    }
  }
  var savedC=(typeof kwSavedCombos==='function'?kwSavedCombos():[]).filter(function(o){return o&&(catalogHistMatch(o.name,q)||catalogHistMatch((o.pills||[]).join(' + '),q));}).sort(function(a,b){return (b.usedAt||b.savedAt||b.t||0)-(a.usedAt||a.savedAt||a.t||0);}).slice(0,typeof KW_COMBO_MAX==='number'?KW_COMBO_MAX:12);
  if(savedC.length){
    html+='<div class="ac-group-label" data-cat="combo">Saved combinations</div>';
    savedC.forEach(function(o){
      var lab=o.name||(o.pills||[]).join(' + ');
      html+='<div class="ac-item ac-combo ac-combo-saved" data-cat="combo" onclick="applyKwCombo(\''+jsStr(o.id||o.key)+'\',event)"><span class="ac-label">'+htmlStr(lab)+'</span><span class="ac-count">'+(o.pills&&o.pills.length||0)+'</span></div>';
    });
  }
  var combos=(typeof kwAutoCombos==='function'?kwAutoCombos():(kwComboStore||[])).filter(function(o){return o&&!o.saved&&catalogHistMatch((o.pills||[]).join(' + '),q);}).slice(0,10);
  if(combos.length){
    html+='<div class="ac-group-label" data-cat="combo">Keyword combos</div>';
    combos.forEach(function(o){
      var lab=(o.pills||[]).join(' + ');
      html+='<div class="ac-item ac-combo" data-cat="combo" onclick="applyKwCombo(\''+jsStr(o.key)+'\',event)"><span class="ac-label">'+htmlStr(lab)+'</span></div>';
    });
  }
  var hits=Object.keys(cardHitStore||{}).map(function(k){return cardHitStore[k];}).filter(function(o){return o&&catalogHistMatch(o.name||o.id,q);}).sort(function(a,b){return (b.n||0)-(a.n||0)||(b.t||0)-(a.t||0);}).slice(0,10);
  if(hits.length){
    html+='<div class="ac-group-label" data-cat="card">Top card hits</div>';
    hits.forEach(function(o){
      html+='<div class="ac-item ac-cardhit ac-lib" data-cat="card" data-lib="1" onclick="openCardHit(\''+jsStr(o.id)+'\')"><span class="ac-label">'+htmlStr(o.name||o.id)+'</span><span class="ac-lib-mark" title="Full library name">[-]</span><span class="ac-count">'+(o.n||1)+'</span></div>';
    });
  }
  var recK=(recentKwStore||[]).filter(function(t){return catalogHistMatch(t,q);}).slice(0,10);
  if(recK.length){
    html+='<div class="ac-group-label" data-cat="recent">Recent keywords</div>';
    recK.forEach(function(t){
      html+='<div class="ac-item" data-cat="recent" onclick="pickAc(\''+jsStr(t)+'\')"><span class="ac-label">'+htmlStr(t)+'</span></div>';
    });
  }
  return html;
}
window.catalogAcHistoryHtml=catalogAcHistoryHtml;
(function bindKwComboSave(){
  if(window.__kwComboSaveBound)return;
  window.__kwComboSaveBound=1;
  document.addEventListener('click',function(e){
    var t=e.target;
    if(!t||!t.closest)return;
    if(t.closest('#kwComboSave,.kw-combo-save')){
      e.preventDefault();e.stopPropagation();
      if(typeof openKwComboSave==='function')openKwComboSave(e);
      return;
    }
    if(t.closest('#kwComboSaveGo')){
      e.preventDefault();e.stopPropagation();
      var inp=document.getElementById('kwComboSaveName');
      var nm=inp?inp.value:'';
      if(typeof saveKwCombo==='function'&&saveKwCombo(nm)){
        var p=document.getElementById('kwComboSavePop');if(p)p.hidden=true;
        if(typeof showAc==='function')showAc((typeof searchInput!=='undefined'&&searchInput&&searchInput.value||'').trim().toLowerCase(),{force:true});
      }
      return;
    }
    var pop=document.getElementById('kwComboSavePop');
    if(pop&&!pop.hidden&&!t.closest('#kwComboSavePop,#kwComboSave,.kw-combo-save'))pop.hidden=true;
  });
})();

var notesMap=lsGet(NOTES_KEY,{});

if(!notesMap||typeof notesMap!=='object'||Array.isArray(notesMap))notesMap={};
function entryName(el){return (el&&el.getAttribute&&el.getAttribute('data-name'))||'';}
function persistFavs(){lsSet(FAV_KEY,Object.keys(favSet));}
function persistNotes(){lsSet(NOTES_KEY,notesMap);}
function currentFocusEntry(){
  try{
    if(typeof galleryHits==='function'&&typeof galleryIndex==='number'){
      var hits=galleryHits();
      if((document.body.classList.contains('gallery-open')||document.body.classList.contains('img-focus-open'))&&hits[galleryIndex])return hits[galleryIndex];
    }
  }catch(err){}
  return document.querySelector('.entry.highlight')||document.querySelector('.entry.selected');
}
function paintFavBtn(btn,fav){
  if(!btn)return;
  btn.classList.toggle('on',!!fav);
  btn.setAttribute('aria-pressed',fav?'true':'false');
  btn.setAttribute('aria-label',fav?'Unfavorite':'Favorite');
  btn.textContent=fav?'\u2665':'\u2661';
}
function syncEntryMeta(el){
  if(!el)return;
  var name=entryName(el);
  var fav=!!favSet[name];
  var note=String(notesMap[name]||'').replace(/^\s+|\s+$/g,'');
  el.classList.toggle('is-fav',fav);
  paintFavBtn(el.querySelector('.fav-btn'),fav);
  var badge=el.querySelector('.un-badge');
  if(badge){badge.hidden=!note;badge.classList.toggle('has-note',!!note);}
  var nt=el.querySelector('.note-text');
  if(nt){nt.textContent=note;nt.hidden=!note;nt.classList.toggle('has-note',!!note);}
}
function syncAllMeta(){document.querySelectorAll('.entry').forEach(syncEntryMeta);if(typeof window.syncChromeFavs==='function')window.syncChromeFavs();}
window.syncChromeFavs=function(el){
  el=el||currentFocusEntry();
  var fav=!!(el&&favSet[entryName(el)]);
  document.querySelectorAll('.gallery-fav,.img-focus-fav').forEach(function(b){paintFavBtn(b,fav);});
};
window.toggleFav=function(src){
  var el=(src&&src.closest)?src.closest('.entry'):null;
  if(!el)el=currentFocusEntry();
  var name=entryName(el);
  if(!name)return;
  if(favSet[name])delete favSet[name];else favSet[name]=1;
  persistFavs();
  syncEntryMeta(el);
  window.syncChromeFavs(el);
  if(document.body.classList.contains('search-mode')&&typeof window.applySearch==='function')window.applySearch();
  if(typeof window.showAc==='function'&&!document.body.classList.contains('search-extras-collapsed')){
    var ac=document.getElementById('acList');
    if(ac&&ac.classList.contains('open')){
      var si=document.getElementById('searchInput');
      window.showAc(si?si.value.trim().toLowerCase():'',{force:true});
    }
  }
};
window.closeAllNotePops=function(){
  document.querySelectorAll('.note-pop').forEach(function(p){p.hidden=true;p.classList.remove('open');});
};
window.openNotePop=function(btn){
  var wrap=btn&&btn.closest?btn.closest('.lib-notes'):null;
  var el=btn&&btn.closest?btn.closest('.entry'):null;
  if(!wrap)return;
  window.closeAllNotePops();
  var pop=wrap.querySelector('.note-pop');
  var ta=wrap.querySelector('.note-ta');
  if(ta)ta.value=notesMap[entryName(el)]||'';
  if(pop){pop.hidden=false;pop.classList.add('open');}
  if(ta)try{ta.focus();}catch(err){}
};
window.cancelNotePop=function(btn){
  var pop=btn&&btn.closest?btn.closest('.note-pop'):null;
  if(pop){pop.hidden=true;pop.classList.remove('open');}
};
window.saveNotePop=function(btn){
  var wrap=btn&&btn.closest?btn.closest('.lib-notes'):null;
  var el=btn&&btn.closest?btn.closest('.entry'):null;
  var name=entryName(el);
  var ta=wrap&&wrap.querySelector('.note-ta');
  if(!name)return;
  var val=ta?String(ta.value||'').replace(/^\s+|\s+$/g,''):'';
  if(val)notesMap[name]=val;else delete notesMap[name];
  persistNotes();
  syncEntryMeta(el);
  window.cancelNotePop(btn);
  if(document.body.classList.contains('search-mode')&&typeof window.applySearch==='function')window.applySearch();
};
syncAllMeta();

JS
  printf 'var KW_CATS=%s;\n' "$KW_CATS_JS"
  cat <<'JS'
(function(){
 var entries=[].slice.call(document.querySelectorAll('.entry'));
 var idx=[].slice.call(document.querySelectorAll('.index li'));
 function entryForIdx(li){var a=li.querySelector('a[href^="#"]');return a?document.getElementById(a.getAttribute('href').slice(1)):null;}
 function kws(el){return (el.getAttribute('data-kw')||'').split(/\s+/).filter(Boolean);}
 function others(el){return (el.getAttribute('data-other')||'').split(/\s+/).filter(Boolean);}
 function patches(el){return (el.getAttribute('data-patch')||'').split(/\s+/).filter(Boolean);}
 function elName(el){return el.getAttribute('data-name')||'';}
 function elNameLc(el){return elName(el).toLowerCase();}
 var sel=[], bar=document.getElementById('kwbar'), st=document.getElementById('kwstatus');
 var PATCH_STOP={a:1,an:1,the:1,and:1,or:1,of:1,to:1,in:1,on:1,at:1,by:1,for:1,from:1,with:1,into:1,onto:1,upon:1,as:1,vs:1,via:1,is:1,it:1,its:1,this:1,that:1,these:1,those:1,be:1,was:1,were:1,are:1,not:1,no:1,nor:1,but:1,so:1,if:1,then:1,than:1,your:1,my:1,our:1,their:1,you:1,we:1,they:1,he:1,she:1,them:1,us:1,me:1,vol:1,version:1,ver:1,rev:1,patch:1,patches:1,preset:1,presets:1,nki:1,nkm:1,nkr:1,dspreset:1,ds:1,wav:1,ogg:1,flac:1,mp3:1,midi:1,kit:1,bank:1,inst:1,lib:1,demo:1,free:1,edition:1,ed:1,unpack:1,unpacked:1,mac:1,win:1,windows:1,linux:1,v1:1,v2:1,v3:1,v4:1,v5:1,v6:1,v7:1,v8:1,v9:1,default:1,init:1,user:1,multi:1,mic:1,mics:1};
 function usefulPatchToken(k){
   k=String(k||'').toLowerCase();
   if(!k||k.length<3||PATCH_STOP[k])return false;
   if(/^[0-9]{1,2}$/.test(k))return false;
   return true;
 }
 var PATCH_SET={}, patchCounts={};
 entries.forEach(function(el){patches(el).forEach(function(k){if(!usefulPatchToken(k))return;PATCH_SET[k]=1;patchCounts[k]=(patchCounts[k]||0)+1;});});
 var ALL=(function(){var s={};entries.forEach(function(el){kws(el).forEach(function(k){s[k]=1;});});return Object.keys(s).sort();})();
 function matchesSel(el){return sel.length>0&&sel.every(function(k){return pillMatch(el,k);});}
 function matching(){return entries.filter(matchesSel);}
 /* --- category filter --- */
 var activeCat='all';
 function kwCat(k){if(KW_CATS[k])return KW_CATS[k];if(PATCH_SET[k])return 'patch';return 'other';}
 function isPatchKw(k){
   k=String(k||'').toLowerCase();
   if(kwCounts[k])return false;
   if(PATCH_SET[k])return true;
   return entries.some(function(el){return patchNames(el).indexOf(k)>=0;});
 }
 function kwTone(k,asPatch){return (asPatch||isPatchKw(k))?' patch':'';}
 function catTokens(el){return kws(el).concat(others(el));}
 function catMatch(el){
   var ks=catTokens(el);
   if(activeCat==='all'||activeCat==='other')return true;
   if(activeCat==='patch')return parseInt(el.getAttribute('data-patch-count')||'0',10)>0||patches(el).length>0;
   return ks.some(function(k){return KW_CATS[k]===activeCat;});
 }
 var CAT_ORDER=['instrument','brand','model','vibe','patch'];
 var CAT_LABEL={instrument:'Instrument',brand:'Brand',model:'Model',vibe:'Vibe',patch:'Patch'};
 var PATCH_BAR_CAP=30;
 window.setCat=function(cat){if(cat==='other')cat='all';activeCat=cat;document.querySelectorAll('.cat-btn').forEach(function(b){b.classList.toggle('active',b.dataset.cat===cat);});if(currentMode==='search')applySearch();else render();requestAnimationFrame(function(){requestAnimationFrame(function(){if(typeof jumpAcList==='function')jumpAcList(typeof typedQuery==='function'?typedQuery():((typeof searchInput!=='undefined'&&searchInput&&searchInput.value)||'').trim().toLowerCase(),{jumpCat:cat});});});};
 /* --- mode switcher --- */
 var currentMode='search';
var DATA_MODE_KEY='catalog-data-mode-'+(window.CATALOG_NS||'catalog');
window.DATA_MODE_KEY=DATA_MODE_KEY;
function isPickMode(m){m=m==null?currentMode:m;return m==='pick'||m==='shade';}
function normalizeDataMode(m){if(m==='shade'||m==='pick')return'pick';if(m==='hide')return'search';return'search';}
window.isPickMode=isPickMode;
window.normalizeDataMode=normalizeDataMode;
window.getCurrentMode=function(){return currentMode;};
window.getSel=function(){return (sel||[]).slice();};
 var TAP_ADD_KEY='catalog-tap-to-add';
 var tapToAdd=false;
 try{tapToAdd=localStorage.getItem(TAP_ADD_KEY)==='1';}catch(err){}
 var CLEAR_MISS_KEY='catalog-clear-on-miss';
 var clearOnMiss=false;
 try{clearOnMiss=localStorage.getItem(CLEAR_MISS_KEY)==='1';}catch(err){}
 var gallerySearchSnap=null;
 var pendingRestoreSearchHits=false;
 function syncTapToAddBtns(){
   document.querySelectorAll('.tap-add-btn').forEach(function(b){
     b.setAttribute('aria-pressed',tapToAdd?'true':'false');
     b.classList.toggle('on',tapToAdd);
   });
   document.body.classList.toggle('tap-to-add',!!(tapToAdd&&currentMode==='search'));
 }
 function syncClearOnMissBtns(){
   document.querySelectorAll('.clear-miss-btn').forEach(function(b){
     b.setAttribute('aria-pressed',clearOnMiss?'true':'false');
     b.classList.toggle('on',clearOnMiss);
   });
 }
 window.toggleTapToAdd=function(){
   tapToAdd=!tapToAdd;
   try{localStorage.setItem(TAP_ADD_KEY,tapToAdd?'1':'0');}catch(err){}
   syncTapToAddBtns();
 };
 window.toggleClearOnMiss=function(){
   clearOnMiss=!clearOnMiss;
   try{localStorage.setItem(CLEAR_MISS_KEY,clearOnMiss?'1':'0');}catch(err){}
   syncClearOnMissBtns();
 };
 function snapHitList(snap){
   if(!snap)return [];
   if(Object.prototype.toString.call(snap)==='[object Array]')return snap;
   return snap.hits||[];
 }
 function snapHasEntry(list,el){
   if(!list||!el)return false;
   if(list.indexOf(el)>=0)return true;
   var id=el.id;
   if(id&&list.some(function(h){return h&&h.id===id;}))return true;
   if(gallerySearchSnap&&gallerySearchSnap.ids&&id&&gallerySearchSnap.ids.indexOf(id)>=0)return true;
   return false;
 }
 window.snapContainsEntry=function(el){return snapHasEntry(snapHitList(gallerySearchSnap),el);};
 function searchFiltersOn(){
   return currentMode==='search'&&(searchKeywords.length>0||!!typedQuery());
 }
 function hideNonHitEntry(el){
   if(!el)return;
   el.classList.add('is-hidden');
   el.classList.remove('hit','dim');
   el.style.display='none';
 }
 window.searchFiltersOn=searchFiltersOn;
 window.rehideSearchNonHits=function(extra){
   if(currentMode!=='search'||!searchFiltersOn())return;
   var hits=currentHits();
   var bannerOn=document.body.classList.contains('gallery-open')||document.body.classList.contains('img-focus-open')||document.body.classList.contains('hl-open')||document.body.classList.contains('chosen-preview-open');
   entries.forEach(function(el){
     if(hits.indexOf(el)>=0)return;
     if(bannerOn&&(el.classList.contains('highlight')||(document.body.classList.contains('chosen-preview-open')&&el.classList.contains('selected')))){
       el.classList.add('is-hidden');
       el.classList.remove('hit','dim');
       return;
     }
     hideNonHitEntry(el);
     if(el.classList.contains('selected')&&!el.classList.contains('highlight'))el.classList.remove('selected');
   });
   if(extra&&hits.indexOf(extra)<0&&!extra.classList.contains('highlight')&&!(document.body.classList.contains('chosen-preview-open')&&extra.classList.contains('selected'))){
     hideNonHitEntry(extra);
     extra.classList.remove('selected');
     if(lastViewedEntry===extra&&!bannerOn)lastViewedEntry=null;
   }
   syncLocGroups();
 };
 window.hasGallerySearchSnap=function(){return snapHitList(gallerySearchSnap).length>0;};
 window.ensureGallerySearchSnap=function(){
   if(window._galleryExitLock)return;
   if(window.hasGallerySearchSnap())return;
   window.captureGallerySearchSnap();
 };
 window.captureGallerySearchSnap=function(){
   if(window._galleryExitLock)return;
   if(window.hasGallerySearchSnap())return;
   if(currentMode!=='search'){gallerySearchSnap=null;pendingRestoreSearchHits=false;return;}
   if(!searchKeywords.length&&!typedQuery()){gallerySearchSnap=null;pendingRestoreSearchHits=false;return;}
   var hits=currentHits();
   if(!hits.length){gallerySearchSnap=null;pendingRestoreSearchHits=false;return;}
   gallerySearchSnap={hits:hits.slice(),ids:hits.map(function(h){return h&&h.id;}),q:typedQuery(),pills:searchKeywords.slice()};
   pendingRestoreSearchHits=false;
 };
 window.consumeGallerySearchExit=function(last){
   if(window._galleryExitHandled){
     if(currentMode==='search')applySearch();
     if(window._galleryExitHandled.miss&&!window._galleryExitHandled.cleared&&typeof window.rehideSearchNonHits==='function')window.rehideSearchNonHits(last);
     return;
   }
   var snap=gallerySearchSnap;
   gallerySearchSnap=null;
   window._galleryExitLock=true;
   var list=snapHitList(snap);
   var filtersOn=searchFiltersOn();
   if(!filtersOn&&!list.length){
     window._galleryExitHandled={miss:false,cleared:false};
     pendingRestoreSearchHits=false;
     if(currentMode==='search')applySearch();
     return;
   }
   var isHit=!!last&&list.length&&snapHasEntry(list,last);
   window._galleryExitHandled={miss:!!(last&&!isHit&&(filtersOn||list.length)),cleared:false};
   if(!last||isHit){
     pendingRestoreSearchHits=false;
     if(currentMode==='search')applySearch();
     if(typeof window.rehideSearchNonHits==='function')window.rehideSearchNonHits(last);
     return;
   }
   if(clearOnMiss){
     window._galleryExitHandled.cleared=true;
     pendingRestoreSearchHits=false;
     searchKeywords=[];
     if(searchInput)searchInput.value='';
     if(acList){acList.classList.remove('open');acList.innerHTML='';}
     renderPills();
     if(currentMode==='search')applySearch();
     else render();
     return;
   }
   pendingRestoreSearchHits=true;
   if(currentMode==='search')applySearch();
   if(typeof window.rehideSearchNonHits==='function')window.rehideSearchNonHits(last);
 };
 window.shouldRestoreSearchHits=function(){return !!pendingRestoreSearchHits;};
 window.restoreSearchHitsAfterMiss=function(){
   if(!pendingRestoreSearchHits)return;
   pendingRestoreSearchHits=false;
   clearSelect();
   lastViewedEntry=null;
   if(currentMode!=='search')window.setMode('search');
   else applySearch();
   if(typeof window.rehideSearchNonHits==='function')window.rehideSearchNonHits();
   var hits=currentHits();
   if(hits.length){
     try{hits[0].scrollIntoView({behavior:'smooth',block:'nearest'});}
     catch(err){try{hits[0].scrollIntoView(true);}catch(err2){}}
   }
 };
 var searchKeywords=[];
 var searchMeta={};
 var kwCounts={};entries.forEach(function(el){kws(el).forEach(function(k){kwCounts[k]=(kwCounts[k]||0)+1;});});
 var otherCounts={}, untaggedNames={}, nameLabel={};
 entries.forEach(function(el){
   others(el).forEach(function(k){otherCounts[k]=(otherCounts[k]||0)+1;});
   var classified=kws(el), nm=elNameLc(el);
   if(!nm||KW_CATS[nm])return;
   searchMeta[nm]={isLibName:1,untagged:classified.length===0?1:0};
   nameLabel[nm]=elName(el);
   if(classified.length===0)untaggedNames[nm]=1;
   if(others(el).indexOf(nm)<0)otherCounts[nm]=(otherCounts[nm]||0)+1;
 });
 var allKws=(function(){
   var seen={}, list=[];
   Object.keys(kwCounts).forEach(function(k){seen[k]=1;list.push({k:k,c:kwCounts[k],untagged:0,isLibName:0,label:k,cat:kwCat(k)});});
   Object.keys(patchCounts).forEach(function(k){
     if(seen[k])return; seen[k]=1;
     list.push({k:k,c:patchCounts[k],untagged:0,isLibName:0,label:k,cat:'patch'});
   });
   return list.sort(function(a,b){return b.c-a.c||(a.k<b.k?-1:a.k>b.k?1:0);});
 })();
 function renderKwBar(){
   var hideZero=currentMode==='search';
   var active=currentMode==='search'?searchKeywords:sel;
   var hits=currentHits();
   var counts={};
   hits.forEach(function(el){kws(el).forEach(function(k){if(active.indexOf(k)<0)counts[k]=(counts[k]||0)+1;});});
   bar.innerHTML='';
   var activeKws=currentMode==='search'?searchKeywords:sel;
   activeKws.forEach(function(k){
     var asPatch=activeCat==='patch'||isPatchKw(k);
     var b=document.createElement('button');b.className='kw active on'+kwTone(k,asPatch);b.setAttribute('data-cat',asPatch?'patch':kwCat(k));b.setAttribute('data-kw',k);if(asPatch)b.setAttribute('data-src','patch');b.textContent=k+' \u2715';
     b.onclick=function(ev){if(typeof window.removeSearchKw==='function')window.removeSearchKw(k);else{sel=sel.filter(function(x){return x!==k;});render();}}; // fix-P: always removeSearchKw
     if(currentMode!=='search'&&activeCat!=='all'&&(asPatch?'patch':kwCat(k))!==activeCat){b.style.opacity='0.3';b.style.pointerEvents='none';}
     bar.appendChild(b);
   });
   if(activeCat==='patch'){
     var pcounts={};
     hits.forEach(function(el){patches(el).forEach(function(k){if(active.indexOf(k)<0&&usefulPatchToken(k))pcounts[k]=(pcounts[k]||0)+1;});});
     Object.keys(pcounts).sort(function(a,b){return (pcounts[b]-pcounts[a])||(a<b?-1:a>b?1:0);}).slice(0,PATCH_BAR_CAP).forEach(function(k){
       var c=pcounts[k]||0;if(hideZero&&c<1)return;
       var b=document.createElement('button');b.className='kw'+(c>0?'':' disabled')+' patch';b.setAttribute('data-cat','patch');b.setAttribute('data-src','patch');b.setAttribute('data-kw',k);b.textContent=k+' ('+c+')';
       if(c>0)b.onclick=function(ev){if(typeof setMode==='function')setMode('search');if(typeof window.addSearchKw==='function'){window.addSearchKw(k);return;}sel.push(k);render();}; else b.disabled=true; // fix-P: pills work in search
       bar.appendChild(b);
     });
   }else{
     ALL.forEach(function(k){if(active.indexOf(k)>=0)return;var c=counts[k]||0;if(hideZero&&c<1)return;var b=document.createElement('button');
       b.className='kw'+(c>0?'':' disabled')+kwTone(k,false);b.setAttribute('data-cat',kwCat(k));b.setAttribute('data-kw',k);b.textContent=k+' ('+c+')';
       if(c>0)b.onclick=function(ev){if(typeof setMode==='function')setMode('search');if(typeof window.addSearchKw==='function'){window.addSearchKw(k);return;}sel.push(k);render();}; else b.disabled=true; // fix-P: pills work in search
       if(currentMode!=='search'&&activeCat!=='all'&&kwCat(k)!==activeCat){b.style.opacity='0.3';b.style.pointerEvents='none';}bar.appendChild(b);});
   }
   if(activeKws.length>0){var cl=document.createElement('button');cl.className='kw clear';cl.textContent='Clear';cl.onclick=function(){window.clearAllFilters();};bar.appendChild(cl);} // fix-C: only when tags active
   if(currentMode==='search'){
     if(searchKeywords.length)st.textContent=hits.length+' match(es) for: '+searchKeywords.join(' + '); else st.textContent='';
   }else if(sel.length)st.textContent=matching().length+' match(es) for: '+sel.join(' + '); else st.textContent='';
 }
 function filtersActive(){
   if(activeCat!=='all')return true;
   if(currentMode==='search')return searchKeywords.length>0||!!typedQuery();
   return sel.length>0;
 }
 function syncLocGroups(){
   var on=filtersActive();
   document.querySelectorAll('.loc-group').forEach(function(group){
     var hide=on&&group.querySelectorAll('.entry:not(.is-hidden)').length===0;
     group.classList.toggle('is-hidden',hide);
     group.hidden=hide;
   });
 }
 function render(){
   if(currentMode!=='search'){
   document.body.classList.remove('search-empty-recs');
   entries.forEach(function(el){var catOk=catMatch(el);var kwMatch=matchesSel(el);var show=catOk&&(sel.length===0||kwMatch);el.classList.toggle('hit',sel.length>0&&kwMatch&&catOk);el.classList.toggle('dim',!show);el.classList.toggle('is-hidden',!show);el.classList.remove('fav-rec');el.style.display=show?'':'none';});
   idx.forEach(function(li){var el=entryForIdx(li)||li;var catOk=catMatch(el);var kwMatch=matchesSel(el);var show=catOk&&(sel.length===0||kwMatch);li.classList.toggle('hit',sel.length>0&&kwMatch&&catOk);li.style.display=show?'':'none';});
   }
   renderKwBar();
   syncLocGroups();
   if(currentMode!=='search')syncHighlight();
 }
 window.setMode=function(mode){
   if(window._searchPopupGuard)return;
if(mode==='hide')mode='search';
if(typeof normalizeDataMode==='function')mode=normalizeDataMode(mode);
else if(mode==='shade'||mode==='pick')mode='pick';
if(currentMode==='hide')currentMode='search';
if(currentMode==='shade')currentMode='pick';

   if(mode==='search'&&currentMode==='search'){
     // Search pill while already in Search: bring Search chrome up correctly (do not exit Search).
     document.querySelectorAll('.mode-btn').forEach(function(b){b.classList.toggle('active',b.dataset.mode==='search');});
     document.body.classList.add('search-mode');
     if(typeof expandSearchMenu==='function')expandSearchMenu();
     else{
       document.body.classList.remove('search-extras-collapsed','search-chrome-collapsed');
       if(window.syncSearchHideBtn)window.syncSearchHideBtn();
     }
     try{window.scrollTo(0,0);}catch(err){}
     var chrome=document.getElementById('searchChrome');
     try{window.scrollTo(0,0);}catch(err){}
     if(typeof window.restoreSearchUi==='function')window.restoreSearchUi();
     if(typeof window.applyActiveLayoutStore==='function')window.applyActiveLayoutStore();
     setTimeout(function(){var si=document.getElementById('searchInput');if(si&&!document.body.classList.contains('ac-fs-open'))si.focus();},50);
     if((document.body.classList.contains('kw-fs-open')||(typeof kwFsWanted!=='undefined'&&kwFsWanted))&&!document.body.classList.contains('display-fs')&&typeof window.setAcFullscreen==='function'&&!document.body.classList.contains('ac-fs-open'))window.setAcFullscreen(true);
     if(typeof window.updateDualState==='function')window.updateDualState();
     syncTapToAddBtns();
     return;
   }
   currentMode=mode;
document.querySelectorAll('.mode-btn').forEach(function(b){var bm=b.dataset.mode;b.classList.toggle('active',bm===mode||((mode==='pick'||mode==='shade')&&(bm==='pick'||bm==='shade')));});
document.body.classList.toggle('search-mode',mode==='search');
document.body.classList.toggle('pick-mode',mode==='pick');
try{localStorage.setItem(DATA_MODE_KEY,mode==='pick'?'pick':'search');}catch(err){}

   document.body.classList.remove('search-extras-collapsed','search-chrome-collapsed');if(window.syncSearchHideBtn)window.syncSearchHideBtn();
   if(typeof window.applyActiveLayoutStore==='function')window.applyActiveLayoutStore();
   if(mode==='search'){renderPills();applySearch();if(typeof window.restoreSearchUi==='function')window.restoreSearchUi();setTimeout(function(){var si=document.getElementById('searchInput');if(si&&!document.body.classList.contains('ac-fs-open'))si.focus();},50);}
   else{entries.forEach(function(el){el.style.display='';el.classList.remove('dim','is-hidden','fav-rec');});document.body.classList.remove('search-empty-recs');render();
     if(typeof acFsWanted!=='undefined')acFsWanted=false;
     document.body.classList.remove('ac-fs-open','dual-fs-open');
     if(typeof parkSearchStrip==='function')parkSearchStrip();
     if(typeof placeAcShell==='function')placeAcShell();
   }
   if(mode==='search'&&(document.body.classList.contains('kw-fs-open')||(typeof kwFsWanted!=='undefined'&&kwFsWanted))&&!document.body.classList.contains('display-fs')&&typeof window.setAcFullscreen==='function'&&!document.body.classList.contains('ac-fs-open'))window.setAcFullscreen(true);
   if(typeof window.updateDualState==='function')window.updateDualState();
   syncTapToAddBtns();};
/* --- search mode --- */
 var searchInput=document.getElementById('searchInput'),acList=document.getElementById('acList');
 function jsStr(s){return String(s).replace(/\\/g,'\\\\').replace(/'/g,"\\'");}
 function htmlStr(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
 function sortOther(arr){return arr.slice().sort(function(a,b){if(b.c!==a.c)return b.c-a.c;return a.k<b.k?-1:a.k>b.k?1:0;});}
 function acNoteIcon(o){
   var name=o.label||'';
   var k=o.k||'';
   var has=false;
   if(name&&notesMap[name])has=true;
   if(!has){
     entries.some(function(el){
       var n=elName(el);
       if((n===name||elNameLc(el)===k)&&notesMap[n]){has=true;return true;}
       return false;
     });
   }
   return has?'<span class="ac-note" title="User notes" aria-label="User notes">\uD83D\uDCAC</span>':'';
 }
 function acRowIsLib(o,cat,force){
  if(force)return true;
  if(!o)return false;
  cat=cat||o.cat||'';
  if(cat==='session'||cat==='combo'||cat==='recent'||cat==='combo-save')return false;
  if(o.isLibName||cat==='lib'||cat==='card')return true;
  var lab=String(o.label||o.k||'');
  return typeof isLibraryNameQuery==='function'&&isLibraryNameQuery(lab);
}
function acLibItemHtml(o,cat,onclick,opts){
  opts=opts||{};
  var lib=acRowIsLib(o,cat,opts.forceLib);
  var extra=opts.extra?(' '+opts.extra):'';
  var fav=(o&&(o.isFav||(o.label&&typeof favSet!=='undefined'&&favSet[o.label])))?' fav-rec':'';
  var cls='ac-item'+fav+(lib?' ac-lib':'')+extra;
  var mark=lib?'<span class="ac-lib-mark" title="Full library name">[-]</span>':'';
  var count=(opts.count==null||opts.count==='')?'':(' <span class="ac-count">'+opts.count+'</span>');
  var note=(opts.note&&typeof acNoteIcon==='function')?acNoteIcon(o):'';
  return '<div class="'+cls+'" data-cat="'+cat+'"'+(lib?' data-lib="1"':'')+' onclick="'+onclick+'"><span class="ac-label">'+htmlStr((o&&(o.label||o.k))||'')+note+'</span>'+mark+count+'</div>';
}
function suggestLibNames(q,lim,all){
  var ql=String(q||'').toLowerCase();
  if(!ql&&!all)return [];
  var list=[],seen={};
  function add(k,lab){
    lab=lab||k;
    var kk=String(k||'').toLowerCase();
    if(!kk||seen[kk])return;
    if(!all&&ql&&String(lab).toLowerCase().indexOf(ql)<0&&kk.indexOf(ql)<0)return;
    seen[kk]=1;
    list.push({k:kk,c:1,isLibName:1,label:lab,cat:'lib'});
  }
  try{Object.keys(nameLabel||{}).forEach(function(k){add(k,nameLabel[k]);});}catch(err){}
  try{
    if(typeof entries!=='undefined')entries.forEach(function(el){
      var n=(typeof entryName==='function'?entryName(el):(el.getAttribute&&el.getAttribute('data-name')))||'';
      if(n)add(n,n);
    });
  }catch(err2){}
  list.sort(function(a,b){return String(a.label||'').localeCompare(String(b.label||''));});
  return list.slice(0,lim||24);
}
function libAcHtml(list){
  if(!list||!list.length)return '';
  var html='<div class="ac-group-label" data-cat="lib">Libraries</div>';
  list.forEach(function(o){html+=acLibItemHtml(o,'lib',"pickAc('"+jsStr(o.label||o.k)+"')",{note:1,forceLib:1});});
  return html;
}
function acHtml(list,cap,hint){
   var groups={};CAT_ORDER.forEach(function(c){groups[c]=[];});
   list.forEach(function(o){var c=o.cat||kwCat(o.k);if(groups[c])groups[c].push(o);});
   if(groups.patch)groups.patch=sortOther(groups.patch);
   var picked={};CAT_ORDER.forEach(function(c){picked[c]=[];});
   var perCat=hint?10:8;
   if(hint){
     CAT_ORDER.forEach(function(c){picked[c]=groups[c].slice(0,perCat);});
   }else{
     var used=0,lim=cap||100;
     CAT_ORDER.forEach(function(c){
       var n=Math.min(perCat,groups[c].length);
       for(var i=0;i<n;i++){picked[c].push(groups[c][i]);used++;}
     });
     CAT_ORDER.forEach(function(c){for(var i=picked[c].length;i<groups[c].length&&used<lim;i++){picked[c].push(groups[c][i]);used++;}});
   }
   var html='';
   CAT_ORDER.forEach(function(c){
     if(!picked[c].length)return;
     html+='<div class="ac-group-label" data-cat="'+c+'">'+CAT_LABEL[c]+'</div>';
     picked[c].forEach(function(o){
       html+=acLibItemHtml(o,c,"pickAc('"+jsStr(o.label||o.k)+"')",{note:1,count:o.c});
     });
   });
   return html;}
 function patchNames(el){
   if(el._patchNames)return el._patchNames;
   el._patchNames=[].slice.call(el.querySelectorAll('.patches li')).map(function(li){return (li.textContent||'').replace(/^\s+|\s+$/g,'').toLowerCase();}).filter(Boolean);
   return el._patchNames;
 }
 function typedQuery(){return searchInput?searchInput.value.trim().toLowerCase():'';}
 function typedMatch(el,q){
   if(!q)return true;
   if(elNameLc(el).indexOf(q)>=0)return true;
   if((el.getAttribute('data-kw')||'').toLowerCase().indexOf(q)>=0)return true;
   if((el.getAttribute('data-other')||'').toLowerCase().indexOf(q)>=0)return true;
   if((el.getAttribute('data-patch')||'').toLowerCase().indexOf(q)>=0)return true;
   return patchNames(el).some(function(n){return n.indexOf(q)>=0;});
 }
 function currentHits(){
   if(currentMode==='search'){
     var q=typedQuery();
     return entries.filter(function(el){
       if(!catMatch(el))return false;
       if(q&&!typedMatch(el,q))return false;
       if(searchKeywords.length===0)return true;
       return searchKeywords.every(function(k){return pillMatch(el,k);});
     });
   }
   return entries.filter(function(el){
     if(!catMatch(el))return false;
     if(sel.length===0)return true;
     return matchesSel(el);
   });
 }
 function isSearchHit(el){return !!el&&currentHits().indexOf(el)>=0;}
 window.currentHits=currentHits;
 window.isSearchHit=isSearchHit;
 function suggestFromHits(){
   var hits=currentHits(),active=currentMode==='search'?searchKeywords:sel;
   return allKws.filter(function(o){
     if(active.indexOf(o.k)>=0)return false;
     return hits.some(function(el){return pillMatch(el,o.k);});
   }).map(function(o){
     var c=0;hits.forEach(function(el){if(pillMatch(el,o.k))c++;});
     return {k:o.k,c:c,untagged:o.untagged,isLibName:o.isLibName,label:o.label,cat:o.cat||kwCat(o.k)};
   }).filter(function(o){return o.c>0;});
 }
 function suggestPatchNames(q,hits,lim){
   if(!q||q.length<2)return [];
   var seen={},list=[];
   hits.forEach(function(el){
     patchNames(el).forEach(function(n){
       if(n.indexOf(q)<0)return;
       if(seen[n]){seen[n].c++;return;}
       var o={k:n,c:1,untagged:0,isLibName:0,label:n,cat:'patch'};
       seen[n]=o;list.push(o);
     });
   });
   list.sort(function(a,b){return b.c-a.c||(a.k<b.k?-1:a.k>b.k?1:0);});
   return list.slice(0,lim||16);
 }
 function persistSearchCommits(){
   var keys=Object.keys(searchCommitCounts||{});
   if(keys.length>80){
     keys.sort(function(a,b){return (searchCommitCounts[b]||0)-(searchCommitCounts[a]||0);});
     var keep={};
     keys.slice(0,80).forEach(function(k){keep[k]=searchCommitCounts[k];});
     searchCommitCounts=keep;
   }
   lsSet(SEARCH_COMMIT_KEY,searchCommitCounts);
 }
 function commitSearchTokens(text){
   text=String(text||'').trim();
   if(!text)return;
   if(typeof isLibraryNameQuery==='function'&&isLibraryNameQuery(text))return;
   var low=text.toLowerCase();
   var seen={};
   low.split(/[\s,;/|]+/).forEach(function(t){
     t=String(t||'').replace(/^[^\w]+|[^\w]+$/g,'').toLowerCase();
     if(!t||seen[t]||t.length<3)return;
     if(typeof isLibraryNameQuery==='function'&&isLibraryNameQuery(t))return;
     if(typeof PATCH_STOP!=='undefined'&&PATCH_STOP[t])return;
     if(typeof usefulPatchToken==='function'&&!usefulPatchToken(t)&&!(typeof kwCounts!=='undefined'&&kwCounts[t]))return;
     seen[t]=1;
     searchCommitCounts[t]=(searchCommitCounts[t]||0)+1;
   });
   persistSearchCommits();
   if(typeof recordRecentKeyword==='function')recordRecentKeyword(text);
 }
 function favEntries(){
   var seen={},list=[];
   entries.forEach(function(el){
     var name=entryName(el)||elName(el);
     if(!name||!favSet[name]||seen[name])return;
     if(typeof catMatch==='function'&&!catMatch(el))return;
     seen[name]=1;
     list.push(el);
   });
   return list;
 }
 function suggestFavs(){
   return favEntries().map(function(el){
     var name=entryName(el)||elName(el);
     return {k:(typeof elNameLc==='function'?elNameLc(el):name.toLowerCase()),c:1,isFav:1,isLibName:1,label:name,cat:'fav'};
   }).sort(function(a,b){return (a.label||a.k)<(b.label||b.k)?-1:(a.label||a.k)>(b.label||b.k)?1:0;});
 }
 function suggestRankedKws(favEls,skipNames){
   var favHits={},skip={};
   (skipNames||[]).forEach(function(n){if(n)skip[String(n).toLowerCase()]=1;});
   (favEls||[]).forEach(function(el){
     var seen={};
     function add(k){
       k=String(k||'').toLowerCase();
       if(!k||seen[k]||skip[k])return;
       seen[k]=1;
       favHits[k]=(favHits[k]||0)+1;
     }
     kws(el).forEach(add);
     others(el).forEach(add);
     patches(el).forEach(function(k){
       if(typeof usefulPatchToken==='function'&&!usefulPatchToken(k))return;
       add(k);
     });
   });
   var keys={};
   Object.keys(favHits).forEach(function(k){keys[k]=1;});
   Object.keys(searchCommitCounts||{}).forEach(function(k){if(k&&!skip[k])keys[k]=1;});
   return Object.keys(keys).map(function(k){
     var fh=favHits[k]||0,sc=searchCommitCounts[k]||0;
     return {k:k,c:Math.max(sc,fh),favHits:fh,searchCommits:sc,isFav:fh>0,label:k,cat:kwCat(k)};
   }).sort(function(a,b){
     var am=Math.max(a.searchCommits,a.favHits),bm=Math.max(b.searchCommits,b.favHits);
     if(bm!==am)return bm-am;
     var ao=a.searchCommits+a.favHits-am,bo=b.searchCommits+b.favHits-bm;
     if(bo!==ao)return bo-ao;
     return a.k<b.k?-1:a.k>b.k?1:0;
   }).slice(0,24);
 }
 function favAcHtml(names,kws){
   var html='';
   var favNames=names||[];
   var favOnly=(kws||[]).filter(function(o){return o&&o.favHits>0;});
   var commitOnly=(kws||[]).filter(function(o){return o&&o.searchCommits>0&&!(o.favHits>0);});
   if(favNames.length||favOnly.length){
     html+='<div class="ac-group-label ac-fav-label" data-cat="fav">Favorites</div>';
     favNames.forEach(function(o){
       html+=acLibItemHtml(o,'fav',"pickAc('"+jsStr(o.label||o.k)+"')",{note:1,extra:'fav-rec',forceLib:1});
     });
     favOnly.forEach(function(o){
       html+='<div class="ac-item fav-rec" data-cat="'+(o.cat||'other')+'" onclick="pickAc(\''+jsStr(o.label||o.k)+'\')"><span class="ac-label">'+htmlStr(o.label||o.k)+'</span> <span class="ac-count">'+o.c+'</span></div>';
     });
   }
   if(commitOnly.length){
     html+='<div class="ac-group-label">Searched keywords</div>';
     commitOnly.forEach(function(o){
       html+='<div class="ac-item" data-cat="'+(o.cat||'other')+'" onclick="pickAc(\''+jsStr(o.label||o.k)+'\')"><span class="ac-label">'+htmlStr(o.label||o.k)+'</span> <span class="ac-count">'+o.c+'</span></div>';
     });
   }
   return html;
 }
 /* ac-cat-jump */
function acScrollRoot(){
  var ac=document.getElementById('acList');
  var sh=document.getElementById('acShell');
  if(ac&&ac.classList.contains('open')&&ac.scrollHeight>ac.clientHeight+2)return ac;
  if(sh&&sh.scrollHeight>sh.clientHeight+2)return sh;
  return ac;
}
function acGroupLabelEl(cat){
  var ac=document.getElementById('acList');
  if(!ac||!cat)return null;
  cat=String(cat);
  var hit=ac.querySelector('.ac-group-label[data-cat="'+cat.replace(/"/g,'')+'"]');
  if(hit)return hit;
  var map={instrument:'instrument',brand:'brand',model:'model',vibe:'vibe',patch:'patch',fav:'favorites',lib:'libraries',other:'other',session:'saved sessions',combo:'keyword combos'};
  var want=(map[cat]||cat).toLowerCase();
  var labels=ac.querySelectorAll('.ac-group-label');
  for(var i=0;i<labels.length;i++){
    if(String(labels[i].textContent||'').replace(/^\s+|\s+$/g,'').toLowerCase()===want)return labels[i];
  }
  return null;
}
function scrollAcGroupToTop(label){
  var sc=acScrollRoot();
  if(!sc||!label)return false;
  var lr=label.getBoundingClientRect();
  var sr=sc.getBoundingClientRect();
  var next=sc.scrollTop+(lr.top-sr.top);
  var max=Math.max(0,sc.scrollHeight-sc.clientHeight);
  sc.scrollTop=Math.max(0,Math.min(max,next));
  if(window.syncAcScrollStripe)window.syncAcScrollStripe();
  return true;
}
function categoryForLibraryQuery(q){
  q=String(q||'').toLowerCase();
  if(!q||q.length<2)return '';
  var best=null,score=0;
  try{
    if(typeof entries!=='undefined')entries.forEach(function(el){
      var n=String((typeof entryName==='function'?entryName(el):'')||(el.getAttribute&&el.getAttribute('data-name'))||'').toLowerCase();
      if(!n)return;
      var s=0;
      if(n===q)s=4;
      else if(n.indexOf(q)===0)s=3;
      else if(q.length>=3&&n.indexOf(q)>=0)s=2;
      if(s>score){score=s;best=el;}
    });
  }catch(err){}
  if(!best||score<2)return '';
  var ks=typeof catTokens==='function'?catTokens(best):[];
  var order=(typeof CAT_ORDER!=='undefined'&&CAT_ORDER)?CAT_ORDER:['instrument','brand','model','vibe','patch'];
  for(var i=0;i<order.length;i++){
    var c=order[i];
    if(ks.some(function(k){return (typeof KW_CATS!=='undefined'&&KW_CATS[k]===c)||(typeof kwCat==='function'&&kwCat(k)===c);}))return c;
  }
  return 'lib';
}
function matchingAcLibGroup(q){
  var ac=document.getElementById('acList');
  if(!ac||!q)return null;
  q=String(q).toLowerCase();
  var items=ac.querySelectorAll('.ac-item.ac-lib');
  var best=null,score=0;
  for(var i=0;i<items.length;i++){
    var lab=(items[i].querySelector('.ac-label')||items[i]).textContent||'';
    lab=lab.replace(/^\s+|\s+$/g,'').toLowerCase();
    var s=0;
    if(lab===q)s=4;
    else if(lab.indexOf(q)===0)s=3;
    else if(q.length>=3&&lab.indexOf(q)>=0)s=2;
    if(s>score){score=s;best=items[i];}
  }
  if(!best||score<2)return null;
  var cat=best.getAttribute('data-cat')||'';
  if(cat){
    var byCat=acGroupLabelEl(cat);
    if(byCat)return byCat;
  }
  var el=best.previousElementSibling;
  while(el&&!el.classList.contains('ac-group-label'))el=el.previousElementSibling;
  return el;
}

function acGroupQuery(q){
  q=String(q||'').toLowerCase().replace(/^\s+|\s+$/g,'');
  if(!q||q.length<2)return '';
  var names=[
    {cat:'instrument',keys:['instrument']},
    {cat:'brand',keys:['brand']},
    {cat:'model',keys:['model']},
    {cat:'vibe',keys:['vibe']},
    {cat:'patch',keys:['patch']},
    {cat:'lib',keys:['libraries','library','lib']},
    {cat:'fav',keys:['favorites','favourite','favorite','fav']},
    {cat:'session',keys:['saved sessions','sessions','session']},
    {cat:'combo',keys:['saved combinations','combinations','combination','combos','combo']}
  ];
  var best='',score=0;
  names.forEach(function(n){
    n.keys.forEach(function(k){
      var s=0;
      if(k===q)s=6;
      else if(k.indexOf(q)===0)s=5;
      else if(q.length>=3&&k.indexOf(q)>=0)s=3;
      if(s>score){score=s;best=n.cat;}
    });
  });
  return score>=5?best:'';
}
function fillAcGroupQuery(q,list){
  list=list?list.slice():[];
  var gq=typeof acGroupQuery==='function'?acGroupQuery(q):'';
  if(!gq||typeof CAT_ORDER==='undefined'||CAT_ORDER.indexOf(gq)<0)return list;
  var src=(typeof allKws!=='undefined'&&allKws)?allKws:[];
  src.forEach(function(o){
    if(!o||!o.k)return;
    var c=o.cat||(typeof kwCat==='function'?kwCat(o.k):'');
    if(c!==gq)return;
    if(list.some(function(x){return x&&x.k===o.k;}))return;
    list.push({k:o.k,c:o.c||0,label:o.label||o.k,cat:c,untagged:o.untagged,isLibName:o.isLibName});
  });
  return list;
}
function matchingAcGroupLabel(q){
  var gq=typeof acGroupQuery==='function'?acGroupQuery(q):'';
  if(gq&&typeof acGroupLabelEl==='function'){
    var by=acGroupLabelEl(gq);
    if(by)return by;
  }
  var ac=document.getElementById('acList');
  if(!ac||!q)return null;
  q=String(q).toLowerCase().replace(/^\s+|\s+$/g,'');
  var labels=ac.querySelectorAll('.ac-group-label');
  var best=null,score=0;
  for(var i=0;i<labels.length;i++){
    var el=labels[i];
    var cat=String(el.getAttribute('data-cat')||'').toLowerCase();
    var lab=String(el.textContent||'').replace(/^\s+|\s+$/g,'').toLowerCase();
    var head=lab.split(/\s+[·•|]/)[0];
    var s=0;
    if(cat===q||lab===q||head===q)s=6;
    else if(cat.indexOf(q)===0||lab.indexOf(q)===0||head.indexOf(q)===0)s=5;
    if(s>score){score=s;best=el;}
  }
  return score>=5?best:null;
}
function jumpAcList(q,opts){
  opts=opts||{};
  var ac=document.getElementById('acList');
  if(!ac||!ac.classList.contains('open'))return;
  var cat='';
  var label=null;
  var path='';
  var libCat='';
  q=String(q||'').toLowerCase();
  if(q){
    libCat=typeof categoryForLibraryQuery==='function'?categoryForLibraryQuery(q):'';
    label=typeof matchingAcGroupLabel==='function'?matchingAcGroupLabel(q):null;
    if(label)path='group';
    if(!label){
      cat=libCat;
      if(cat)label=acGroupLabelEl(cat);
      if(label)path='libCat';
    }
    if(!label){label=matchingAcLibGroup(q);if(label)path='libItem';}
  }
  if(!label){
    cat=opts.jumpCat||(typeof activeCat!=='undefined'?activeCat:'');
    if(cat&&cat!=='all'&&cat!=='other'){label=acGroupLabelEl(cat);if(label)path='jumpCat';}
  }
  if(!label&&(opts.jumpCat==='all'||cat==='all')){
    var sc0=acScrollRoot();
    if(sc0)sc0.scrollTop=0;
    return;
  }
  if(!label)return;
  scrollAcGroupToTop(label);
}
window.jumpAcList=jumpAcList;
window.scrollAcGroupToTop=scrollAcGroupToTop;
window.acGroupLabelEl=acGroupLabelEl;
function showAc(q,opts){
   opts=opts||{};
   if(document.body.classList.contains('search-extras-collapsed')){if(acList){acList.classList.remove('open');acList.innerHTML='';}return;}
   if(typeof overlayCoversSearch==='function'&&overlayCoversSearch()){if(acList){acList.classList.remove('open');acList.innerHTML='';}if(typeof window.hideSearchAc==='function')window.hideSearchAc();return;}
   var src=suggestFromHits();
   var list=q?src.filter(function(o){return o.k.indexOf(q)>=0||(o.label&&o.label.toLowerCase().indexOf(q)>=0);}):src;
   if(typeof fillAcGroupQuery==='function')list=fillAcGroupQuery(q,list);
   if(q&&q.length>=2){
     suggestPatchNames(q,currentHits(),32).forEach(function(o){
       if(!list.some(function(x){return x.k===o.k;}))list.push(o);
     });
   }
   var favEls=favEntries();
   var favs=suggestFavs();
   var ranked=suggestRankedKws(favEls,favs.map(function(o){return o.label||o.k;}));
   if(q){
     favs=favs.filter(function(o){return ((o.label||o.k||'').toLowerCase()).indexOf(q)>=0;});
     ranked=ranked.filter(function(o){return ((o.label||o.k||'').toLowerCase()).indexOf(q)>=0;});
     favs.forEach(function(o){
       var hit=list.filter(function(x){return (x.label||x.k)===o.label||x.k===o.k;})[0];
       if(hit)hit.isFav=1;
     });
   }
   var histHtml=typeof catalogAcHistoryHtml==='function'?catalogAcHistoryHtml(q):'';
   var libHtml=(q&&typeof libAcHtml==='function')?libAcHtml(typeof suggestLibNames==='function'?suggestLibNames(q,24,typeof acGroupQuery==='function'&&acGroupQuery(q)==='lib'):[]):'';
   var mainHtml=acHtml(list,100,!q);
   var favHtml=favAcHtml(favs,ranked);
   var hasMain=mainHtml.length>0;
   var hasCommits=(ranked||[]).some(function(o){return o&&o.searchCommits>0;});
   // Never open the dropdown solely to dump favorite suggestions.
   if(!q&&!hasMain&&!hasCommits&&!histHtml&&!opts.force){
     if(acList){acList.innerHTML='';acList.classList.remove('open');}
     if(window.syncSearchSplit)window.syncSearchSplit();
     return;
   }
   var html=(histHtml||'')+(libHtml||'')+((hasMain||hasCommits||!!q||opts.force)?(favHtml+mainHtml):'');
   acList.innerHTML=html;acList.classList.toggle('open',html.length>0);if(window.syncAcScrollStripe)window.syncAcScrollStripe();
   if(window.syncSearchSplit)window.syncSearchSplit();
   requestAnimationFrame(function(){requestAnimationFrame(function(){if(typeof jumpAcList==='function')jumpAcList(q,opts);if(window.syncAcScrollStripe)window.syncAcScrollStripe();});});
 }
 window.showAc=showAc;
 /* ac-scroll-stripe */
(function(){
  var bound=false,drag=null,raf=0;
  function gid(id){return document.getElementById(id);}
  function ensure(){
    var sh=gid('acShell'),ac=gid('acList');
    if(!sh||!ac)return null;
    var st=gid('acScrollStripe');
    if(!st){
      st=document.createElement('div');
      st.id='acScrollStripe';
      st.className='ac-scroll-stripe';
      st.hidden=true;
      var th0=document.createElement('div');
      th0.id='acScrollThumb';
      th0.className='ac-scroll-thumb';
      st.appendChild(th0);
      sh.appendChild(st);
    }
    var th=gid('acScrollThumb')||st.querySelector('.ac-scroll-thumb');
    return {sh:sh,ac:ac,st:st,th:th};
  }
  function scroller(ac,sh){
    if(ac&&ac.classList.contains('open')&&ac.scrollHeight>ac.clientHeight+2)return ac;
    if(sh&&sh.scrollHeight>sh.clientHeight+2)return sh;
    return ac;
  }
  function sync(){
    var n=ensure();
    if(!n)return;
    var ac=n.ac,sh=n.sh,st=n.st,th=n.th;
    var open=ac.classList.contains('open')&&ac.childNodes.length;
    var sc=scroller(ac,sh);
    var max=sc?Math.max(0,sc.scrollHeight-sc.clientHeight):0;
    var show=!!(open&&max>2);
    sh.classList.toggle('has-ac-overflow',show);
    st.hidden=!show;
    if(!show){st.classList.remove('is-dragging');return;}
    var gap=4;
    var top=ac.offsetTop;
    var trackH=Math.max(16,ac.clientHeight-gap*2);
    st.style.top=(top+gap)+'px';
    st.style.height=trackH+'px';
    var thumbH=Math.max(22,Math.round((sc.clientHeight/Math.max(1,sc.scrollHeight))*trackH));
    if(thumbH>trackH)thumbH=trackH;
    var range=Math.max(1,trackH-thumbH);
    th.style.height=thumbH+'px';
    th.style.top=Math.round((sc.scrollTop/Math.max(1,max))*range)+'px';
  }
  function schedule(){
    if(raf)cancelAnimationFrame(raf);
    raf=requestAnimationFrame(function(){
      raf=requestAnimationFrame(function(){raf=0;sync();});
    });
  }
  function yToScroll(sc,st,clientY){
    var r=st.getBoundingClientRect();
    var th=gid('acScrollThumb');
    var thH=th?th.offsetHeight:22;
    var y=clientY-r.top-thH/2;
    var range=Math.max(1,r.height-thH);
    var ratio=Math.max(0,Math.min(1,y/range));
    sc.scrollTop=ratio*Math.max(1,sc.scrollHeight-sc.clientHeight);
  }
  function bind(){
    var n=ensure();
    if(!n||bound)return;
    bound=true;
    n.ac.addEventListener('scroll',schedule,{passive:true});
    n.sh.addEventListener('scroll',schedule,{passive:true});
    n.st.addEventListener('pointerdown',function(e){
      var n2=ensure();
      if(!n2||n2.st.hidden)return;
      var sc=scroller(n2.ac,n2.sh);
      if(!sc)return;
      e.preventDefault();
      e.stopPropagation();
      n2.st.classList.add('is-dragging');
      try{n2.st.setPointerCapture(e.pointerId);}catch(err){}
      drag={sc:sc,st:n2.st,id:e.pointerId};
      yToScroll(sc,n2.st,e.clientY);
      schedule();
    });
    n.st.addEventListener('pointermove',function(e){
      if(!drag||e.pointerId!==drag.id)return;
      yToScroll(drag.sc,drag.st,e.clientY);
    });
    function end(e){
      if(!drag||(e&&e.pointerId!==drag.id))return;
      drag.st.classList.remove('is-dragging');
      try{drag.st.releasePointerCapture(drag.id);}catch(err){}
      drag=null;
      schedule();
    }
    n.st.addEventListener('pointerup',end);
    n.st.addEventListener('pointercancel',end);
    if(typeof ResizeObserver!=='undefined'){
      var ro=new ResizeObserver(schedule);
      ro.observe(n.ac);ro.observe(n.sh);
    }
    var mo=new MutationObserver(schedule);
    mo.observe(n.ac,{childList:true,subtree:true,attributes:true,attributeFilter:['class']});
    if(document.body){
      var mb=new MutationObserver(schedule);
      mb.observe(document.body,{attributes:true,attributeFilter:['class','style']});
    }
    window.addEventListener('resize',schedule);
  }
  function boot(){bind();schedule();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);
  else boot();
  window.syncAcScrollStripe=schedule;
})();

/* hover-scroll-stripe: Content + Index */
(function(){
  function bindStripe(hostId, scrollId, mark){
    var drag=null,raf=0,bound=false;
    function host(){return document.getElementById(hostId);}
    function scroller(){return document.getElementById(scrollId)||host();}
    function ensure(){
      var h=host(),sc=scroller();
      if(!h||!sc)return null;
      h.classList.add('hover-scroll-host');
      var st=document.getElementById(hostId+'HoverStripe')||h.querySelector(':scope > .hover-scroll-stripe');
      var parkBody=mark==='content';
      if(!st){
        st=document.createElement('div');
        st.className='hover-scroll-stripe';
        st.id=hostId+'HoverStripe';
        st.hidden=true;
        var th=document.createElement('div');
        th.className='hover-scroll-thumb';
        st.appendChild(th);
      }
      if(parkBody){
        st.classList.add('hover-scroll-fixed');
        if(st.parentNode!==document.body)document.body.appendChild(st);
      }else if(st.parentNode!==h){
        h.appendChild(st);
      }
      return {h:h,sc:sc,st:st,th:st.querySelector('.hover-scroll-thumb')};
    }
    function sync(){
      var n=ensure();
      if(!n)return;
      var sc=n.sc,max=Math.max(0,sc.scrollHeight-sc.clientHeight);
      var show=max>8;
      n.h.classList.toggle('has-hover-overflow',show);
      if(mark==='content')document.body.classList.toggle('has-hover-overflow-content',show);
      n.st.hidden=!show;
      if(!show){n.st.classList.remove('is-dragging');return;}
      if(mark==='content'){
        var mr0=sc.getBoundingClientRect();
        n.st.style.top=Math.round(mr0.top+4)+'px';
        n.st.style.left=Math.round(Math.max(0,mr0.right-15))+'px';
        n.st.style.height=Math.round(Math.max(16,mr0.height-8))+'px';
        n.st.style.right='auto';
        n.st.style.bottom='auto';
        n.st.style.width='12px';
      }
      var trackH=Math.max(16,n.st.clientHeight||(sc.clientHeight-8));
      var thumbH=Math.max(22,Math.round((sc.clientHeight/Math.max(1,sc.scrollHeight))*trackH));
      if(thumbH>trackH)thumbH=trackH;
      var range=Math.max(1,trackH-thumbH);
      n.th.style.height=thumbH+'px';
      n.th.style.top=Math.round((sc.scrollTop/Math.max(1,max))*range)+'px';
    }
    function schedule(){
      if(raf)cancelAnimationFrame(raf);
      raf=requestAnimationFrame(function(){raf=0;sync();});
    }
    function yToScroll(sc,st,clientY){
      var r=st.getBoundingClientRect();
      var th=st.querySelector('.hover-scroll-thumb');
      var thH=th?th.offsetHeight:22;
      var y=clientY-r.top-thH/2;
      var range=Math.max(1,r.height-thH);
      sc.scrollTop=Math.max(0,Math.min(1,y/range))*Math.max(1,sc.scrollHeight-sc.clientHeight);
    }
    function bind(){
      var n=ensure();
      if(!n){
        if(document.documentElement&&!window['_hsObs_'+mark]){
          try{
            window['_hsObs_'+mark]=new MutationObserver(function(){if(!bound)bind();schedule();});
            window['_hsObs_'+mark].observe(document.documentElement,{childList:true,subtree:true});
          }catch(err){}
        }
        return;
      }
      if(bound){schedule();return;}
      bound=true;
      if(mark==='content'&&n.h&&!n.h.dataset.hsHoverBound){
        n.h.dataset.hsHoverBound='1';
        n.h.addEventListener('pointerenter',function(){document.body.classList.add('is-content-hover');});
        n.h.addEventListener('pointerleave',function(){if(!drag)document.body.classList.remove('is-content-hover');});
      }
      n.sc.addEventListener('scroll',schedule,{passive:true});
      n.st.addEventListener('pointerdown',function(e){
        var n2=ensure();
        if(!n2||n2.st.hidden)return;
        e.preventDefault();e.stopPropagation();
        n2.st.classList.add('is-dragging');
        try{n2.st.setPointerCapture(e.pointerId);}catch(err){}
        drag={sc:n2.sc,st:n2.st,id:e.pointerId};
        yToScroll(n2.sc,n2.st,e.clientY);
        schedule();
      });
      n.st.addEventListener('pointermove',function(e){
        if(!drag||e.pointerId!==drag.id)return;
        yToScroll(drag.sc,drag.st,e.clientY);
      });
      function end(e){
        if(!drag||(e&&e.pointerId!==drag.id))return;
        drag.st.classList.remove('is-dragging');
        try{drag.st.releasePointerCapture(drag.id);}catch(err){}
        drag=null;schedule();
      }
      n.st.addEventListener('pointerup',end);
      n.st.addEventListener('pointercancel',end);
      if(typeof ResizeObserver!=='undefined'){
        var ro=new ResizeObserver(schedule);
        ro.observe(n.sc);ro.observe(n.h);
      }
      window.addEventListener('resize',schedule);
      if(document.body){
        try{new MutationObserver(function(){if(!bound)bind();schedule();}).observe(document.body,{childList:true,subtree:true});}catch(err){}
      }
    }
    function boot(){bind();schedule();}
    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);
    else boot();
    window['bindHover_'+mark]=bind;
    return schedule;
  }
  window.syncMainHoverStripe=bindStripe('catalogMain','catalogMain','content');
  window.bindMainHoverStripe=window.bindHover_content||function(){if(window.syncMainHoverStripe)window.syncMainHoverStripe();};
  window.syncIndexHoverStripe=bindStripe('catalogIndex','catalogIndexList','index');
})();

searchInput.addEventListener('input',function(){
   var q=searchInput.value.trim().toLowerCase();
   showAc(q);
   applySearch();
 });
searchInput.addEventListener('focus',function(){if(document.body.classList.contains('search-extras-collapsed'))return;if(typeof overlayCoversSearch==='function'&&overlayCoversSearch()){searchInput.blur();return;}showAc(searchInput.value.trim().toLowerCase());});
// Fix 5: collapse dropdown when focus leaves search field AND #acShell (standard combobox behaviour)
searchInput.addEventListener('focusout',function(e){
  var sh=document.getElementById('acShell');
  var rt=e.relatedTarget;
  // If focus moved somewhere inside acShell (e.g. history button, scrollbar), keep open
  if(rt&&sh&&(sh===rt||sh.contains(rt)))return;
  var ac=document.getElementById('acList');
  if(!ac||!ac.classList.contains('open'))return;
  // Small delay so click/tap on an ac-item fires first (pickAc will close it properly)
  setTimeout(function(){
    if(document.activeElement===searchInput)return;
    var sh2=document.getElementById('acShell');
    if(sh2&&(sh2===document.activeElement||sh2.contains(document.activeElement)))return;
    var acL=document.getElementById('acList');
    if(window._acItemPointer)return;
    if(acL){acL.classList.remove('open');acL.innerHTML='';}
    if(window.syncSearchSplit)window.syncSearchSplit();
  },100);
});
searchInput.addEventListener('keydown',function(e){
   if(e.key==='Enter'){
     commitSearchTokens(searchInput.value);
     if(acList)acList.classList.remove('open');
     applySearch();
   }
 });
 function isRemainingHitKw(kw){
   if(!kw)return false;
   return currentHits().some(function(el){return pillMatch(el,kw);});
 }
window.pickAc=function(text){
if(!searchInput)return;
searchInput.value=text||'';
if(!(typeof isLibraryNameQuery==='function'&&isLibraryNameQuery(text)))commitSearchTokens(text);
else{
  var el=null;
  try{if(typeof entries!=='undefined')entries.forEach(function(e){if(!el&&String((typeof entryName==='function'?entryName(e):'')||'').toLowerCase()===String(text||'').toLowerCase())el=e;});}catch(err){}
  if(el&&typeof recordCardHit==='function')recordCardHit(el);
}
if(acList){acList.classList.remove('open');acList.innerHTML='';}
if(window.CATALOG_PORTABLE||(window.matchMedia&&window.matchMedia('(max-width:899px)').matches)){
  searchInput.blur();
  if(typeof window.hideSearchAc==='function')window.hideSearchAc();
}
applySearch();
};
 window.addSearchKw=function(kw){
   var remain=typeof isRemainingHitKw==='function'?isRemainingHitKw(kw):true;
   if(!kw||searchKeywords.indexOf(kw)>=0)return;
   if(!remain)return;
   searchKeywords.push(kw);renderPills();applySearch();if(typeof recordRecentKeyword==='function')recordRecentKeyword(kw);if(typeof snapshotKwCombo==='function')snapshotKwCombo();
   if(typeof renderKwBar==='function')renderKwBar();
   if(searchInput)searchInput.value='';if(acList)acList.classList.remove('open');};
 window.removeSearchKw=function(kw){searchKeywords=searchKeywords.filter(function(k){return k!==kw;});renderPills();applySearch();};
 function renderPills(){var keep=document.getElementById('kwComboSave');if(keep)document.body.appendChild(keep);var html=searchKeywords.map(function(k){var cls='pill-tag'+(isPatchKw(k)?' patch':'');return '<span class="'+cls+'"><span class="pill-label">'+htmlStr(k)+'</span><button type="button" class="pill-x" aria-label="Remove '+htmlStr(k)+'" onclick="event.preventDefault();event.stopPropagation();removeSearchKw(\''+jsStr(k)+'\')">\u00d7</button></span>';}).join('');document.querySelectorAll('#searchPills,.search-active-pills').forEach(function(c){c.innerHTML=html;});if(typeof parkKwComboSave==='function')parkKwComboSave();}
 window.restoreFilterUi=function(){
   renderKwBar();
   renderPills();
   syncTapToAddBtns();
   document.querySelectorAll('.cat-btn').forEach(function(b){b.classList.toggle('active',b.dataset.cat===activeCat);});
 };
 window.restoreSearchUi=function(){
   renderPills();
   renderKwBar();
   syncTapToAddBtns();
   if(window.syncSearchSplit)window.syncSearchSplit();
 };
(function(){
var drag=null,hdrag=null,adrag=null,sdrag=null,wdrag=null;
function splitGap(){return Math.max(8,Math.round(0.625*rem()));}
var KEYH='catalog-search-split-h-'+(window.CATALOG_NS||'catalog');
var KEYV='catalog-search-split-v-'+(window.CATALOG_NS||'catalog');
var KEYCH='catalog-search-split-c-h-'+(window.CATALOG_NS||'catalog');
var KEYCV='catalog-search-split-c-v-'+(window.CATALOG_NS||'catalog');
var KEYHT='catalog-search-height-'+(window.CATALOG_NS||'catalog');
var KEYAC='catalog-search-ac-height-'+(window.CATALOG_NS||'catalog');
var KEYACSO='catalog-search-only-ac-height-'+(window.CATALOG_NS||'catalog');
var KEYACWSO='catalog-search-only-ac-width-'+(window.CATALOG_NS||'catalog');
var KEYSH='catalog-keywords-shade-height-'+(window.CATALOG_NS||'catalog');
function rem(){return parseFloat(getComputedStyle(document.documentElement).fontSize)||16;}
function searchOnlyRem(){
  var el=document.getElementById('searchCol')||document.getElementById('acShell');
  var n=el?parseFloat(getComputedStyle(el).fontSize):NaN;
  if(isFinite(n)&&n>0)return n;
  return rem();
}
function layoutRem(){return searchOnlyStore()?searchOnlyRem():rem();}
function chrome(){return document.getElementById('searchChrome');}
function splitBtn(){return document.getElementById('searchSplit');}
function heightBtn(){return document.getElementById('searchHeight');}
function acListEl(){return document.getElementById('acList');}
function acBtn(){return document.getElementById('acHeight');}
function acWBtn(){return document.getElementById('acWidth');}
function acShell(){return document.getElementById('acShell');}
function shadeBtn(){return document.getElementById('kwShadeHeight');}
function col(){return document.getElementById('searchCol');}
function wrap(){return document.getElementById('filterWrap');}
function sideBySide(){return true;}
function viewH(){return (window.visualViewport&&window.visualViewport.height)||window.innerHeight;}
function viewW(){return (window.visualViewport&&window.visualViewport.width)||window.innerWidth||0;}
function splitOn(){
  return document.body.classList.contains('search-mode');
}
function splitExpanded(){
  var w=wrap();
  return !!(w&&w.classList.contains('open'));
}
function searchOnlyStore(){
  return document.body.classList.contains('search-mode')&&!splitExpanded();
}
function acStoreKey(){return searchOnlyStore()?KEYACSO:KEYAC;}
function splitRatioKey(axis){
  if(splitExpanded())return axis==='h'?KEYH:KEYV;
  return axis==='h'?KEYCH:KEYCV;
}
function heightOn(){return document.body.classList.contains('search-mode')&&splitExpanded();}
function layoutEdit(){return document.body.classList.contains('layout-edit');}
function acOpen(){var ac=acListEl();return !!(ac&&ac.classList.contains('open'));}
function shadeOn(){var w=wrap();if(!w||!w.classList.contains('open'))return false;if(document.body.classList.contains('display-sides'))return false;if(document.body.classList.contains('display-upper')||document.body.classList.contains('display-fs'))return true;return !document.body.classList.contains('search-mode');}
function readRatio(axis){
  try{
    var n=parseFloat(localStorage.getItem(splitRatioKey(axis)));
    return (isFinite(n)&&n>0&&n<1)?n:null;
  }catch(err){return null;}
}
function writeRatio(axis,ratio){
  try{localStorage.setItem(splitRatioKey(axis),String(ratio));}catch(err){}
  if(typeof writeModeSlot==='function'){var p={};p[axis==='h'?'splitH':'splitV']=String(ratio);writeModeSlot(p);}
}
function measureRowMin(row){
  if(!row)return 0;
  var cs=getComputedStyle(row);
  if(cs.display==='none'||cs.visibility==='hidden')return 0;
  var prevWrap=row.style.flexWrap,prevW=row.style.width,prevMin=row.style.minWidth;
  row.style.flexWrap='nowrap';
  row.style.width='max-content';
  row.style.minWidth='max-content';
  var w=Math.max(row.scrollWidth||0,row.getBoundingClientRect().width||0);
  row.style.flexWrap=prevWrap;
  row.style.width=prevW;
  row.style.minWidth=prevMin;
  return w;
}
function collapsedSearchMin(){
  var r=searchOnlyStore()?searchOnlyRem():rem();
  return Math.max(measureRowMin(document.getElementById('searchStrip')),10*r);
}
function collapsedKwMin(){
  var w=wrap(),r=rem();
  if(!w)return 6*r;
  if(!w.classList.contains('open'))return Math.max(measureRowMin(w.querySelector('.filter-top')),4*r);
  return Math.max(measureRowMin(w.querySelector('.filter-top')),measureRowMin(w.querySelector('.filter-kw-tools')),measureRowMin(w.querySelector('.layout-presets')),6*r);
}
function collapsedSearchMinH(){
  var r=searchOnlyStore()?searchOnlyRem():rem(),c=col(),strip=document.getElementById('searchStrip');
  var h=0;
  if(strip)h=strip.getBoundingClientRect().height;
  if(c&&document.body.classList.contains('search-chrome-collapsed'))h=Math.max(h,c.getBoundingClientRect().height);
  return Math.max(h,2.75*r);
}
function collapsedKwMinH(){
  var w=wrap(),r=rem();
  if(!w)return 2.75*r;
  var h=0,ft=w.querySelector('.filter-top');
  if(ft)h+=ft.getBoundingClientRect().height;
  if(w.classList.contains('open')){
    var tools=w.querySelector('.filter-kw-tools'),lp=w.querySelector('.layout-presets');
    if(tools)h+=tools.getBoundingClientRect().height;
    else if(lp)h+=lp.getBoundingClientRect().height;
  }
  return Math.max(h,2.75*r);
}
function currentHorizMins(avail){
  if(!splitExpanded()){
    var a=collapsedSearchMin(),b=collapsedKwMin();
    if(a+b>avail){var s=avail/Math.max(1,a+b);a*=s;b*=s;}
    return {a:a,b:b};
  }
  return horizMins(avail);
}
function currentVertMins(avail){
  if(!splitExpanded()){
    var a=collapsedSearchMinH(),b=collapsedKwMinH();
    if(a+b>avail){var s=avail/Math.max(1,a+b);a*=s;b*=s;}
    return {a:a,b:b};
  }
  return vertMins(avail);
}
function heightStoreKey(){return KEYHT+'-l';}
function readHeightRatio(){
  try{
    var n=parseFloat(localStorage.getItem(KEYHT+'-l'));
    if(isFinite(n)&&n>0&&n<1)return n;
    // Preserve older portrait-saved chrome heights after always-LR chrome.
    n=parseFloat(localStorage.getItem(KEYHT+'-p'));
    return (isFinite(n)&&n>0&&n<1)?n:null;
  }catch(err){return null;}
}
function writeHeightRatio(ratio){
  try{localStorage.setItem(KEYHT+'-l',String(ratio));}catch(err){}
  if(typeof writeModeSlot==='function')writeModeSlot({chromeH:String(ratio)});
}
function clampRatio(ratio,aMin,bMin,avail,fallback){
  if(!(avail>0))return (ratio!=null&&isFinite(ratio))?ratio:(fallback||0.5);
  var minR=aMin/avail,maxR=1-(bMin/avail);
  if(!(minR<maxR)){
    // Mins cannot both fit — scale proportionally; still prefer a saved ratio if present.
    if(ratio!=null&&isFinite(ratio))return Math.max(0.02,Math.min(0.98,ratio));
    return aMin/(aMin+bMin);
  }
  if(ratio!=null&&isFinite(ratio)){
    // User-defined size wins: only clamp to keep both panes on-screen.
    if(ratio<minR)return minR;
    if(ratio>maxR)return maxR;
    return ratio;
  }
  var def=fallback!=null?fallback:0.55;
  if(def<minR)def=minR;if(def>maxR)def=maxR;
  return def;
}
function contentW(el){
  var r=el.getBoundingClientRect(),s=getComputedStyle(el);
  return Math.max(0,r.width-(parseFloat(s.paddingLeft)||0)-(parseFloat(s.paddingRight)||0));
}
function contentH(el){
  var r=el.getBoundingClientRect(),s=getComputedStyle(el);
  return Math.max(0,r.height-(parseFloat(s.paddingTop)||0)-(parseFloat(s.paddingBottom)||0));
}
function horizMins(avail){
  // Keep controls usable on-screen; do not invent large default pane floors.
  var r=rem();
  var a=Math.max(collapsedSearchMin(),Math.min(10*r,avail*0.2));
  var b=Math.max(collapsedKwMin(),Math.min(8.25*r,avail*0.2));
  if(a+b>avail){var s=avail/Math.max(1,a+b);a*=s;b*=s;}
  return {a:a,b:b};
}
function vertBudget(){
  var el=chrome(),top=el?el.getBoundingClientRect().top:0;
  var vh=viewH();
  var cap=Math.max(10*rem(),vh-top-1.5*rem());
  if(el&&el.classList.contains('search-height-set')){
    var inner=contentH(el);
    if(inner>8)return Math.min(cap,inner);
  }
  return cap;
}
function heightMin(){
  var el=chrome();
  if(!el)return 72;
  var s=getComputedStyle(el);
  var pad=(parseFloat(s.paddingTop)||0)+(parseFloat(s.paddingBottom)||0);
  var collapsed=document.body.classList.contains('search-chrome-collapsed');
  var strip=document.getElementById('searchStrip');
  var searchNeed=Math.max(2.75*rem(),(strip&&(strip.offsetHeight||strip.scrollHeight))||2.75*rem());
  if(!collapsed){
    var pills=document.getElementById('searchPills');
    if(pills){
      var pd=getComputedStyle(pills);
      if(pd.display!=='none'&&pd.visibility!=='hidden')searchNeed+=pills.offsetHeight||0;
    }
  }
  var w=wrap();
  var kwNeed=0;
  if(w){
    var ft=w.querySelector('.filter-top');
    kwNeed+=(ft&&(ft.scrollHeight||ft.offsetHeight))||2.75*rem();
    var lp=w.querySelector('.layout-presets');
    if(lp)kwNeed+=lp.offsetHeight||0;
    if(w.classList.contains('open')&&!collapsed){
      var ms=w.querySelector('.mode-switch');
      var cs=w.querySelector('.cat-switch');
      kwNeed+=(ms&&(ms.offsetHeight||ms.scrollHeight))||0;
      kwNeed+=(cs&&(cs.scrollHeight||cs.offsetHeight))||0;
    }
  }
  var need=searchNeed;
  if(w&&w.classList.contains('open')&&!collapsed){
    if(sideBySide())need=Math.max(searchNeed,kwNeed);
    else need=searchNeed+splitGap()+kwNeed;
  }else if(w){
    if(sideBySide())need=Math.max(searchNeed,kwNeed);
    else need=searchNeed+kwNeed;
  }
  return Math.max(4*rem(),need+pad);
}
function heightMax(){
  var el=chrome(),raw=el?el.getBoundingClientRect().top:0;
  var top=Math.max(0,raw);
  var vh=viewH();
  return Math.max(4*rem(),vh-top-1.5*rem());
}
function heightBounds(){
  var min=heightMin(),max=heightMax();
  if(max<4*rem())max=4*rem();
  if(min>max)min=max;
  return {min:min,max:max};
}
function setChromeHeight(el,h){
  el.style.height=Math.round(h)+'px';
  el.style.maxHeight=Math.round(h)+'px';
  el.classList.add('search-height-set');
}
function clearHeight(el){
  if(!el)return;
  el.style.removeProperty('height');
  el.style.removeProperty('max-height');
  el.classList.remove('search-height-set','search-height-dragging');
}
function applyHeight(){
  var el=chrome(),b=heightBtn();
  if(!el)return;
  if(document.body.classList.contains('display-sides')||document.body.classList.contains('display-fs')){
    clearHeight(el);
    if(b)b.setAttribute('aria-hidden','true');
    return;
  }
  if(!heightOn()){
    clearHeight(el);
    if(b)b.setAttribute('aria-hidden','true');
    return;
  }
  if(b){
    b.removeAttribute('aria-hidden');
    b.setAttribute('aria-orientation','horizontal');
  }
  var stored=readHeightRatio();
  if(stored==null&&document.body.classList.contains('display-upper'))stored=0.48;
  if(stored==null){
    if(!hdrag){
      var cur=el.getBoundingClientRect().height;
      var bds0=heightBounds();
      if(layoutEdit()&&cur>bds0.max)setChromeHeight(el,bds0.max);
      else if(layoutEdit()&&cur<bds0.min)setChromeHeight(el,bds0.min);
      else if(!layoutEdit()&&!el.classList.contains('search-height-set'))clearHeight(el);
    }
    return;
  }
  var h=stored*viewH();
  var bds=heightBounds();
  if(stored<0.05||stored>0.99||!(bds.min<=bds.max)){
    clearHeight(el);
    return;
  }
  if(h<bds.min||h>bds.max)h=Math.max(bds.min,Math.min(bds.max,h));
  setChromeHeight(el,h);
}
function persistHeight(){
  var el=chrome();
  if(!el||!heightOn())return;
  var vh=viewH();
  if(!(vh>0))return;
  var h=el.getBoundingClientRect().height;
  if(h>8)writeHeightRatio(h/vh);
}
function onHeightDown(e){
  var b=heightBtn(),el=chrome();
  if(!b||!el||!heightOn()||!layoutEdit())return;
  if(typeof modeLayoutPinned==='function'&&modeLayoutPinned())return;
  if(e.button!=null&&e.button!==0)return;
  e.preventDefault();e.stopPropagation();
  hdrag={start:e.clientY,startH:el.getBoundingClientRect().height,el:el,id:e.pointerId};
  el.classList.add('search-height-dragging');
  try{b.setPointerCapture(e.pointerId);}catch(err){}
}
function onHeightMove(e){
  if(!hdrag)return;
  if(e.pointerId!=null&&hdrag.id!=null&&e.pointerId!==hdrag.id)return;
  e.preventDefault();
  var bds=heightBounds();
  var h=hdrag.startH+(e.clientY-hdrag.start);
  h=Math.max(bds.min,Math.min(bds.max,h));
  setChromeHeight(hdrag.el,h);
  applySplit();
}
function onHeightUp(e){
  if(!hdrag)return;
  if(e&&e.pointerId!=null&&hdrag.id!=null&&e.pointerId!==hdrag.id)return;
  persistHeight();
  hdrag.el.classList.remove('search-height-dragging');
  try{heightBtn().releasePointerCapture(hdrag.id);}catch(err){}
  hdrag=null;
  applySplit();
}
function vertMins(avail){
  var r=rem(),a=4.5*r,b=9.25*r;
  a=Math.min(a,avail*0.45);b=Math.min(b,avail*0.55);
  if(a+b>avail){var s=avail/Math.max(1,a+b);a*=s;b*=s;}
  return {a:Math.max(3.25*r,a),b:Math.max(5.5*r,b)};
}
function clearSplit(el){
  el.style.removeProperty('grid-template-columns');
  el.style.removeProperty('grid-template-rows');
  el.classList.remove('search-split-lr','search-split-ud','search-split-dragging');
  var b=splitBtn();
  if(b){b.setAttribute('aria-hidden','true');b.setAttribute('aria-orientation','vertical');}
}
function bothMenusOpen(){
  return !document.body.classList.contains('search-chrome-collapsed')&&splitExpanded();
}
function applySplit(){
  if(document.body.classList.contains('display-sides')||document.body.classList.contains('display-fs')){
    var el=chrome();
    if(el)clearSplit(el);

    return;
  }
  var el=chrome(),b=splitBtn();
  if(!el||!b)return;
  if(!splitOn()){clearSplit(el);return;}
  // Always left|right: Search stays top-left, Keywords top-right (never stacked).
  el.classList.add('search-split-lr');
  el.classList.remove('search-split-ud');
  b.setAttribute('aria-orientation','vertical');
  el.style.removeProperty('grid-template-rows');
  var searchCollapsed=document.body.classList.contains('search-chrome-collapsed');
  var kwOpen=splitExpanded();
  var bothOpen=bothMenusOpen();
  if(!bothOpen){
    // Temporary solo/collapsed chrome layout only — never persist these sizes over saved edges.
    b.setAttribute('aria-hidden','true');
    if(searchCollapsed&&!kwOpen){
      // Search left + Keywords right; hidden split track is the flexible spacer.
      el.style.gridTemplateColumns='minmax(0,max-content) minmax(0,1fr) minmax(0,max-content)';
      return;
    }
    if(searchCollapsed&&kwOpen){
      el.style.gridTemplateColumns='minmax(0,max-content) 0px minmax(0,1fr)';
      return;
    }
    // Search alone may occupy full top chrome width; Keywords control stays top-right.
    el.style.gridTemplateColumns='minmax(0,1fr) 0px minmax(0,max-content)';
    return;
  }
  // Both open: restore user-saved together split (KEYH); do not invent a default ratio.
  b.removeAttribute('aria-hidden');
  var gap=splitGap();
  var avail=Math.max(0,contentW(el)-gap);
  var stored=readRatio('h');
  if(stored==null||!isFinite(stored)){
    el.style.gridTemplateColumns='minmax(0,1fr) '+gap+'px minmax(0,1fr)';
    return;
  }
  // Prefer saved ratio, but never shove Keywords / Search off-screen.
  var mins=currentHorizMins(avail);
  var ratio=clampRatio(stored,mins.a,mins.b,avail,null);
  var a=Math.round(avail*ratio);
  el.style.gridTemplateColumns=a+'px '+gap+'px '+(avail-a)+'px';
}
function persist(){
  var el=chrome(),c=col(),w=wrap();
  if(!el||!c||!w||!splitOn()||!bothMenusOpen())return;
  var lr=el.classList.contains('search-split-lr');
  var a=lr?c.getBoundingClientRect().width:c.getBoundingClientRect().height;
  var b=lr?w.getBoundingClientRect().width:w.getBoundingClientRect().height;
  if(a+b>8)writeRatio(lr?'h':'v',a/(a+b));
}
function onDown(e){
  var b=splitBtn(),el=chrome(),c=col();
  if(!b||!el||!c||!splitOn()||!layoutEdit()||!bothMenusOpen())return;
  if(e.button!=null&&e.button!==0)return;
  e.preventDefault();e.stopPropagation();
  var lr=el.classList.contains('search-split-lr');
  drag={lr:lr,start:lr?e.clientX:e.clientY,startA:lr?c.getBoundingClientRect().width:c.getBoundingClientRect().height,el:el,id:e.pointerId};
  el.classList.add('search-split-dragging');
  try{b.setPointerCapture(e.pointerId);}catch(err){}
}
function onMove(e){
  if(!drag)return;
  if(e.pointerId!=null&&drag.id!=null&&e.pointerId!==drag.id)return;
  e.preventDefault();
  var a=drag.startA+((drag.lr?e.clientX:e.clientY)-drag.start);
  if(drag.lr){
    var avail=Math.max(0,contentW(drag.el)-splitGap());
    var mins=currentHorizMins(avail);
    a=Math.max(mins.a,Math.min(avail-mins.b,a));
    drag.el.style.gridTemplateColumns=Math.round(a)+'px '+splitGap()+'px '+Math.round(avail-a)+'px';
  }else{
    var budget=Math.max(0,vertBudget()-splitGap());
    var mins=currentVertMins(budget);
    a=Math.max(mins.a,Math.min(budget-mins.b,a));
    drag.el.style.gridTemplateColumns='1fr';
    drag.el.style.gridTemplateRows=Math.round(a)+'px '+splitGap()+'px '+Math.round(budget-a)+'px';
  }
}
function onUp(e){
  if(!drag)return;
  if(e&&e.pointerId!=null&&drag.id!=null&&e.pointerId!==drag.id)return;
  persist();
  drag.el.classList.remove('search-split-dragging');
  try{splitBtn().releasePointerCapture(drag.id);}catch(err){}
  drag=null;
}
function readExtraRatio(key){
  try{
    var n=parseFloat(localStorage.getItem(key));
    return (isFinite(n)&&n>0&&n<1)?n:null;
  }catch(err){return null;}
}
function writeExtraRatio(key,ratio){
  try{localStorage.setItem(key,String(ratio));}catch(err){}
  if(typeof writeModeSlot==='function'){if(key===KEYAC||key===KEYACSO)writeModeSlot({acH:String(ratio)});if(key===KEYSH)writeModeSlot({kwH:String(ratio)});}
}
function readSearchOnlyPx(key,viewportFn){
  try{
    var n=parseFloat(localStorage.getItem(key));
    if(!isFinite(n)||n<=0)return null;
    if(n<1)return n*(viewportFn?viewportFn():viewH());
    return n*searchOnlyRem();
  }catch(err){return null;}
}
function writeSearchOnlyRem(key,px){
  var r=searchOnlyRem();
  if(!(r>0)||!(px>0))return;
  try{localStorage.setItem(key,String(px/r));}catch(err){}
}
var acFsWanted=false;
function acFsAvailable(){return true;}
function acCapDropdownHeight(){
  if(window.CATALOG_PORTABLE)return true;
  try{return window.matchMedia('(max-width:899px)').matches;}catch(err){return false;}
}
function acFullscreen(){return !!acFsWanted;}
function parkSearchStrip(){
  var strip=document.getElementById('searchStrip');
  var sh=acShell();
  var anchor=document.querySelector('.search-strip-anchor');
  if(!strip)return;
  if(acFsWanted){
    // Park strip as Row 2: direct child of acShell, before the AC list
    if(sh&&strip.parentNode!==sh){
      var acL=sh.querySelector('.search-autocomplete');
      if(acL)sh.insertBefore(strip,acL);
      else sh.appendChild(strip);
    }
  }else if(anchor&&strip.parentNode!==anchor){
    if(sh)anchor.insertBefore(strip,sh);
    else anchor.appendChild(strip);
  }
}
function syncAcFsBtn(){
  var btn=document.getElementById('searchStripFs');
  if(!btn)return;
  var on=acFullscreen();
  var show=acFsAvailable();
  btn.hidden=!show;
  btn.classList.toggle('is-mobile',show);
  btn.setAttribute('aria-pressed',on?'true':'false');
  btn.setAttribute('aria-label',on?'Exit fullscreen search':'Fullscreen search');
  btn.title=on?'Exit fullscreen':'Fullscreen search';
}
function setAcFullscreen(on){
  acFsWanted=!!on&&acFsAvailable();
  parkSearchStrip();
  syncAcFsBtn();
  if(acFsWanted){
    var ac=acListEl(),sh=acShell();
    if(ac)ac.classList.add('open');
    if(sh)sh.classList.add('open');
  }
  if(typeof applyAcHeight==='function')applyAcHeight();
  else if(typeof placeAcShell==='function')placeAcShell();
}
function toggleAcFullscreen(){setAcFullscreen(!acFsWanted);}
window.toggleAcFullscreen=toggleAcFullscreen;
window.setAcFullscreen=setAcFullscreen;

function acWidthOn(){return !acFullscreen()&&searchOnlyStore();}
function viewBox(){
  var vv=window.visualViewport;
  if(vv)return {left:vv.offsetLeft,top:vv.offsetTop,right:vv.offsetLeft+vv.width,bottom:vv.offsetTop+vv.height,width:vv.width,height:vv.height};
  var w=window.innerWidth||document.documentElement.clientWidth||0;
  var h=viewH();
  return {left:0,top:0,right:w,bottom:h,width:w,height:h};
}
function safeInset(side){
  var n=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--safe-'+side));
  return isFinite(n)?n:0;
}
function clearAcShellPos(sh){
  if(!sh)return;
  sh.classList.remove('ac-fixed','ac-fs','toolbar-scroll-collapsed');
  document.body.classList.remove('ac-fs-open');
  ['top','left','right','bottom','width','height','max-width','max-height'].forEach(function(p){sh.style.removeProperty(p);});
}
function placeAcShell(){
  var sh=acShell();
  if(!sh)return;
  syncAcFsBtn();
  parkSearchStrip();
  if(acFsWanted){
    var acKeep=acListEl();
    if(acKeep)acKeep.classList.add('open');
    sh.classList.add('open');
  }
  if(!acOpen()){clearAcShellPos(sh);syncAcWidthBtn();return;}
  var box=viewBox();
  var r=layoutRem();
  if(acFullscreen()){
    sh.classList.add('ac-fixed','ac-fs');
    document.body.classList.add('ac-fs-open');
    var top=box.top,left=box.left,width=box.width,height=box.height;
    if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
      var hdr=document.querySelector('.catalog-header');
      if(hdr)top=Math.max(top,hdr.getBoundingClientRect().bottom);
      height=Math.max(80,box.bottom-top);
    }
    sh.style.top=Math.round(top)+'px';
    sh.style.left=Math.round(left)+'px';
    sh.style.right='auto';
    sh.style.bottom='auto';
    sh.style.width=Math.round(width)+'px';
    sh.style.height=Math.round(height)+'px';
    sh.style.maxWidth='none';
    sh.style.maxHeight=Math.round(height)+'px';
    syncAcWidthBtn();
    return;
  }
  sh.classList.remove('ac-fs');
  document.body.classList.remove('ac-fs-open');
  var sides=document.body.classList.contains('display-sides');
  var combined=sides||(document.body.classList.contains('search-mode')&&document.body.classList.contains('kw-open')&&!document.body.classList.contains('search-chrome-collapsed')&&!document.body.classList.contains('kw-fs-open')&&!document.body.classList.contains('display-fs'));
  if(combined){
    clearAcShellPos(sh);
    var acIn=acListEl();
    if(acIn&&typeof clearAcBox==='function')clearAcBox(acIn);
    sh.classList.add('open');
    syncAcWidthBtn();
    return;
  }
  var strip=document.getElementById('searchStrip')||document.getElementById('searchCol');
  if(!strip)return;
  var br=strip.getBoundingClientRect();
  var sl=safeInset('left'),sr=safeInset('right'),sb=safeInset('bottom');
  var pad=Math.max(0.375*r,6);
  var alignMin=Math.min(br.width||0,8*r)||8*r;
  var left=Math.min(Math.max(br.left,box.left+sl),Math.max(box.left+sl,box.right-sr-alignMin));
  var fieldW=Math.min(br.width||alignMin,box.right-sr-left);
  if(fieldW<alignMin){left=Math.max(box.left+sl,box.right-sr-alignMin);fieldW=Math.min(alignMin,box.right-sr-left);}
  var maxW=Math.max(alignMin,box.right-sr-left);
  var minW=Math.min(8*r,maxW);
  var width=fieldW;
  if(acWidthOn()){
    if(wdrag&&wdrag.w!=null)width=wdrag.w;
    else{
      var storedW=readSearchOnlyPx(KEYACWSO,viewW);
      if(storedW!=null)width=storedW;
    }
    width=Math.max(minW,Math.min(maxW,width));
  }
  var top=Math.max(box.top,br.bottom);
  var maxH=Math.max(2.75*r,box.bottom-sb-pad-top);
  if(acCapDropdownHeight())maxH=Math.min(maxH,Math.max(6*r,0.5*box.height));
  sh.classList.add('ac-fixed');
  sh.style.top=Math.round(top)+'px';
  sh.style.left=Math.round(left)+'px';
  sh.style.right='auto';
  sh.style.bottom='auto';
  sh.style.width=Math.round(Math.max(0,width))+'px';
  sh.style.maxWidth=sh.style.width;
  sh.style.height='auto';
  sh.style.maxHeight=Math.round(maxH)+'px';
  syncAcWidthBtn();
}
function hideSearchAc(){
  acFsWanted=false;
  parkSearchStrip();
  syncAcFsBtn();
  var ac=acListEl();
  if(ac){ac.classList.remove('open');ac.innerHTML='';}
  var si=document.getElementById('searchInput');
  if(si)si.blur();
  clearAcShellPos(acShell());
  if(window.syncSearchSplit)window.syncSearchSplit();
}
window.hideSearchAc=hideSearchAc;
function acBounds(){
  placeAcShell();
  var ac=acListEl();
  var strip=document.getElementById('searchStrip');
  var top=(ac&&ac.getBoundingClientRect().top)||(strip&&strip.getBoundingClientRect().bottom)||0;
  var box=viewBox();
  var r=layoutRem();
  var sb=safeInset('bottom');
  var pad=Math.max(0.375*r,6);
  var maxH=Math.max(2.75*r,box.bottom-sb-pad-Math.max(0,top));
  if(acFullscreen())maxH=Math.max(2.75*r,box.height-sb-pad);
  var minH=Math.min(Math.max(2.75*r,4*r),maxH);
  return {min:minH,max:maxH};
}
function setAcBox(ac,h){
  ac.style.height=Math.round(h)+'px';
  ac.style.maxHeight=Math.round(h)+'px';
  ac.classList.add('ac-height-set');
}
function clearAcBox(ac){
  if(!ac)return;
  ac.style.removeProperty('height');
  ac.style.removeProperty('max-height');
  ac.classList.remove('ac-height-set','ac-height-dragging');
  var sh=acShell();
  if(sh)sh.classList.remove('ac-height-dragging');
}
function syncAcWidthBtn(){
  var b=acWBtn();
  if(!b)return;
  if(!acOpen()||!acWidthOn()){
    b.setAttribute('aria-hidden','true');
    return;
  }
  b.removeAttribute('aria-hidden');
  b.setAttribute('aria-orientation','vertical');
}
function acWidthBounds(){
  var box=viewBox();
  var r=layoutRem();
  var sl=safeInset('left'),sr=safeInset('right');
  var strip=document.getElementById('searchStrip')||document.getElementById('searchCol');
  var br=strip?strip.getBoundingClientRect():{left:box.left+sl,width:8*r};
  var alignMin=Math.min(br.width||0,8*r)||8*r;
  var left=Math.min(Math.max(br.left,box.left+sl),Math.max(box.left+sl,box.right-sr-alignMin));
  var maxW=Math.max(alignMin,box.right-sr-left);
  var minW=Math.min(8*r,maxW);
  return {left:left,min:minW,max:maxW};
}
function persistAcWidth(){
  var sh=acShell();
  if(!sh||!acOpen()||!acWidthOn())return;
  var vw=viewW();
  if(!(vw>0))return;
  var w=sh.getBoundingClientRect().width;
  if(w>8)writeSearchOnlyRem(KEYACWSO,w);
}
function onAcWDown(e){
  var b=acWBtn(),sh=acShell();
  if(!b||!sh||!acOpen()||!layoutEdit()||!acWidthOn())return;
  if(e.button!=null&&e.button!==0)return;
  e.preventDefault();e.stopPropagation();
  var w=sh.getBoundingClientRect().width;
  wdrag={start:e.clientX,startW:w,w:w,id:e.pointerId};
  sh.classList.add('ac-width-dragging');
  try{b.setPointerCapture(e.pointerId);}catch(err){}
}
function onAcWMove(e){
  if(!wdrag)return;
  if(e.pointerId!=null&&wdrag.id!=null&&e.pointerId!==wdrag.id)return;
  e.preventDefault();
  var bds=acWidthBounds();
  var w=wdrag.startW+(e.clientX-wdrag.start);
  w=Math.max(bds.min,Math.min(bds.max,w));
  wdrag.w=w;
  placeAcShell();
}
function onAcWUp(e){
  if(!wdrag)return;
  if(e&&e.pointerId!=null&&wdrag.id!=null&&e.pointerId!==wdrag.id)return;
  persistAcWidth();
  var sh=acShell();
  if(sh)sh.classList.remove('ac-width-dragging');
  try{acWBtn().releasePointerCapture(wdrag.id);}catch(err){}
  wdrag=null;
  placeAcShell();
}
function applyAcHeight(){
  var ac=acListEl(),b=acBtn(),sh=acShell();
  if(sh)sh.classList.toggle('open',acOpen());
  placeAcShell();
  var combined=document.body.classList.contains('display-sides')||(document.body.classList.contains('search-mode')&&document.body.classList.contains('kw-open')&&!document.body.classList.contains('search-chrome-collapsed')&&!document.body.classList.contains('kw-fs-open')&&!document.body.classList.contains('display-fs')&&!acFullscreen());
  if(combined){
    if(ac&&!adrag)clearAcBox(ac);
    if(b)b.setAttribute('aria-hidden','true');
    syncAcWidthBtn();
    return;
  }
  if(!ac||!acOpen()){
    if(ac&&!adrag)clearAcBox(ac);
    if(b)b.setAttribute('aria-hidden','true');
    syncAcWidthBtn();
    return;
  }
  if(acFullscreen()){
    if(!adrag){
      // Keep #acList as the only scrollport; size it to shell minus Row 1 bar and Row 2 strip.
      clearAcBox(ac);
      var bar=document.getElementById('acFsBar');
      var strip2=document.getElementById('searchStrip');
      var shEl=sh||acShell();
      var shBox=shEl&&shEl.getBoundingClientRect();
      var shH=(shBox&&shBox.height)||viewBox().height||0;
      var chromeTop=shBox?shBox.top:0,chromeBot=shBox?shBox.top:0,chromeSet=false;
      [bar,strip2&&strip2.parentNode===shEl?strip2:null].forEach(function(el){
        if(!el)return;
        var er=el.getBoundingClientRect();
        if(er.height<1)return;
        if(!chromeSet){chromeTop=er.top;chromeBot=er.bottom;chromeSet=true;}
        else{chromeTop=Math.min(chromeTop,er.top);chromeBot=Math.max(chromeBot,er.bottom);}
      });
      var chromeH=chromeSet?Math.max(0,chromeBot-chromeTop):0;
      var h=Math.max(96,Math.floor(shH-chromeH));
      ac.style.height=h+'px';
      ac.style.maxHeight=h+'px';
      ac.style.overflowY='scroll';
      ac.style.touchAction='pan-y';
      try{ac.style.webkitOverflowScrolling='touch';}catch(err){}
    }
    if(b)b.setAttribute('aria-hidden','true');
    syncAcWidthBtn();
    return;
  }
  if(b){
    b.removeAttribute('aria-hidden');
    b.setAttribute('aria-orientation','horizontal');
  }
  syncAcWidthBtn();
  var bds=acBounds();
  var h;
  if(searchOnlyStore()){
    h=readSearchOnlyPx(KEYACSO,viewH);
    if(h==null||!(bds.min<=bds.max)){
      if(!adrag)clearAcBox(ac);
      return;
    }
  }else{
    var stored=readExtraRatio(KEYAC);
    if(stored==null||stored<0.04||stored>0.99||!(bds.min<=bds.max)){
      if(!adrag)clearAcBox(ac);
      return;
    }
    h=stored*viewH();
  }
  if(h<bds.min||h>bds.max)h=Math.max(bds.min,Math.min(bds.max,h));
  setAcBox(ac,h);
}
function persistAcHeight(){
  var ac=acListEl();
  if(!ac||!acOpen())return;
  var vh=viewH();
  if(!(vh>0))return;
  var h=ac.getBoundingClientRect().height;
  if(!(h>8))return;
  if(searchOnlyStore())writeSearchOnlyRem(KEYACSO,h);
  else writeExtraRatio(KEYAC,h/vh);
}
function onAcDown(e){
  var b=acBtn(),ac=acListEl();
  if(!b||!ac||!acOpen()||!layoutEdit())return;
  if(typeof modeLayoutPinned==='function'&&modeLayoutPinned())return;
  if(acFullscreen()&&!document.body.classList.contains('display-fs'))return;
  if(e.button!=null&&e.button!==0)return;
  e.preventDefault();e.stopPropagation();
  adrag={start:e.clientY,startH:ac.getBoundingClientRect().height,ac:ac,id:e.pointerId};
  ac.classList.add('ac-height-dragging');
  var sh=acShell();
  if(sh)sh.classList.add('ac-height-dragging');
  try{b.setPointerCapture(e.pointerId);}catch(err){}
}
function onAcMove(e){
  if(!adrag)return;
  if(e.pointerId!=null&&adrag.id!=null&&e.pointerId!==adrag.id)return;
  e.preventDefault();
  var bds=acBounds();
  var h=adrag.startH+(e.clientY-adrag.start);
  h=Math.max(bds.min,Math.min(bds.max,h));
  setAcBox(adrag.ac,h);
}
function onAcUp(e){
  if(!adrag)return;
  if(e&&e.pointerId!=null&&adrag.id!=null&&e.pointerId!==adrag.id)return;
  persistAcHeight();
  adrag.ac.classList.remove('ac-height-dragging');
  var sh=acShell();
  if(sh)sh.classList.remove('ac-height-dragging');
  try{acBtn().releasePointerCapture(adrag.id);}catch(err){}
  adrag=null;
}
function shadeMin(){
  var w=wrap();
  if(!w)return 168;
  var ft=w.querySelector('.filter-top');
  var need=(ft&&(ft.scrollHeight||ft.offsetHeight))||2.75*rem();
  var lp=w.querySelector('.layout-presets');
  if(lp)need+=lp.offsetHeight||0;
  var ms=w.querySelector('.mode-switch');
  var cs=w.querySelector('.cat-switch');
  need+=(ms&&(ms.offsetHeight||ms.scrollHeight))||0;
  need+=(cs&&(cs.offsetHeight||cs.scrollHeight))||2.5*rem();
  need+=3*rem();
  var s=getComputedStyle(w);
  need+=(parseFloat(s.paddingTop)||0)+(parseFloat(s.paddingBottom)||0);
  return Math.max(10.5*rem(),need);
}
function shadeMax(){
  var w=wrap(),raw=w?w.getBoundingClientRect().top:0;
  var top=Math.max(0,raw);
  var vh=viewH();
  return Math.max(10.5*rem(),vh-top-1.5*rem());
}
function shadeBounds(){
  var min=shadeMin(),max=shadeMax();
  if(max<10.5*rem())max=10.5*rem();
  if(min>max)min=max;
  return {min:min,max:max};
}
function setShadeBox(w,h){
  w.style.height=Math.round(h)+'px';
  w.style.maxHeight=Math.round(h)+'px';
  w.classList.add('kw-shade-height-set');
}
function clearShadeBox(w){
  if(!w)return;
  w.style.removeProperty('height');
  w.style.removeProperty('max-height');
  w.classList.remove('kw-shade-height-set','kw-shade-dragging');
}
function applyShadeHeight(){
  var w=wrap(),b=shadeBtn();
  if(!w)return;
  if(document.body.classList.contains('display-sides')&&!(typeof layoutEdit==='function'&&layoutEdit())){
    if(typeof clearShadeBox==='function')clearShadeBox(w);
    if(b)b.setAttribute('aria-hidden','true');
    return;
  }
  if(!shadeOn()){
    clearShadeBox(w);
    if(b)b.setAttribute('aria-hidden','true');
    return;
  }
  if(b){
    b.removeAttribute('aria-hidden');
    b.setAttribute('aria-orientation','horizontal');
  }
  var stored=readExtraRatio(KEYSH);
  if(stored==null){
    if(!sdrag){
      var cur=w.getBoundingClientRect().height;
      var bds0=shadeBounds();
      if(layoutEdit()&&cur>bds0.max)setShadeBox(w,bds0.max);
      else if(layoutEdit()&&cur<bds0.min)setShadeBox(w,bds0.min);
      else if(!layoutEdit()&&!w.classList.contains('kw-shade-height-set'))clearShadeBox(w);
    }
    return;
  }
  var h=stored*viewH();
  var bds=shadeBounds();
  if(stored<0.08||stored>0.99||!(bds.min<=bds.max)){
    if(!sdrag)clearShadeBox(w);
    return;
  }
  if(h<bds.min||h>bds.max)h=Math.max(bds.min,Math.min(bds.max,h));
  setShadeBox(w,h);
}
function persistShadeHeight(){
  var w=wrap();
  if(!w||!shadeOn())return;
  var vh=viewH();
  if(!(vh>0))return;
  var h=w.getBoundingClientRect().height;
  if(h>8)writeExtraRatio(KEYSH,h/vh);
}
function onShadeDown(e){
  var b=shadeBtn(),w=wrap();
  if(!b||!w||!shadeOn()||!layoutEdit())return;
  if(typeof modeLayoutPinned==='function'&&modeLayoutPinned())return;
  if(e.button!=null&&e.button!==0)return;
  e.preventDefault();e.stopPropagation();
  sdrag={start:e.clientY,startH:w.getBoundingClientRect().height,w:w,id:e.pointerId};
  w.classList.add('kw-shade-dragging');
  try{b.setPointerCapture(e.pointerId);}catch(err){}
}
function onShadeMove(e){
  if(!sdrag)return;
  if(e.pointerId!=null&&sdrag.id!=null&&e.pointerId!==sdrag.id)return;
  e.preventDefault();
  var bds=shadeBounds();
  var h=sdrag.startH+(e.clientY-sdrag.start);
  h=Math.max(bds.min,Math.min(bds.max,h));
  setShadeBox(sdrag.w,h);
}
function onShadeUp(e){
  if(!sdrag)return;
  if(e&&e.pointerId!=null&&sdrag.id!=null&&e.pointerId!==sdrag.id)return;
  persistShadeHeight();
  sdrag.w.classList.remove('kw-shade-dragging');
  try{shadeBtn().releasePointerCapture(sdrag.id);}catch(err){}
  sdrag=null;
}
function applyAll(){
  applyHeight();
  applySplit();
  applyAcHeight();
  applyShadeHeight();
}
function init(){
  var b=splitBtn();
  if(b){
    b.addEventListener('pointerdown',onDown);
    b.addEventListener('pointermove',onMove);
    b.addEventListener('pointerup',onUp);
    b.addEventListener('pointercancel',onUp);
    b.addEventListener('lostpointercapture',function(){if(drag)onUp({pointerId:drag.id});});
  }
  var hb=heightBtn();
  if(hb){
    hb.addEventListener('pointerdown',onHeightDown);
    hb.addEventListener('pointermove',onHeightMove);
    hb.addEventListener('pointerup',onHeightUp);
    hb.addEventListener('pointercancel',onHeightUp);
    hb.addEventListener('lostpointercapture',function(){if(hdrag)onHeightUp({pointerId:hdrag.id});});
  }
  var ab=acBtn();
  if(ab){
    ab.addEventListener('pointerdown',onAcDown);
    ab.addEventListener('pointermove',onAcMove);
    ab.addEventListener('pointerup',onAcUp);
    ab.addEventListener('pointercancel',onAcUp);
    ab.addEventListener('lostpointercapture',function(){if(adrag)onAcUp({pointerId:adrag.id});});
  }
  var wb=acWBtn();
  if(wb){
    wb.addEventListener('pointerdown',onAcWDown);
    wb.addEventListener('pointermove',onAcWMove);
    wb.addEventListener('pointerup',onAcWUp);
    wb.addEventListener('pointercancel',onAcWUp);
    wb.addEventListener('lostpointercapture',function(){if(wdrag)onAcWUp({pointerId:wdrag.id});});
  }
  var sb=shadeBtn();
  if(sb){
    sb.addEventListener('pointerdown',onShadeDown);
    sb.addEventListener('pointermove',onShadeMove);
    sb.addEventListener('pointerup',onShadeUp);
    sb.addEventListener('pointercancel',onShadeUp);
    sb.addEventListener('lostpointercapture',function(){if(sdrag)onShadeUp({pointerId:sdrag.id});});
  }
  window.addEventListener('resize',applyAll);
  window.addEventListener('scroll',placeAcShell,{passive:true});
  if(window.visualViewport){
    window.visualViewport.addEventListener('resize',applyAll);
    window.visualViewport.addEventListener('scroll',placeAcShell);
  }
  syncAcFsBtn();
  document.addEventListener('pointerdown',function(e){
    if(!acOpen())return;
    if(e.target.closest&&e.target.closest('#acShell,#searchInput,.search-strip,.search-chrome,#filterWrap,.filter-toggle'))return;
    hideSearchAc();
  });
  if(window.matchMedia){
    var mq=window.matchMedia('(orientation: landscape)');
    if(mq.addEventListener)mq.addEventListener('change',applyAll);
    else if(mq.addListener)mq.addListener(applyAll);
  }
  applyAll();
  if(window.syncLayoutEditBtn)window.syncLayoutEditBtn();
}
var KEYMAP='catalog-layouts-'+(window.CATALOG_NS||'catalog');
var KEYLAST='catalog-layouts-last-'+(window.CATALOG_NS||'catalog');
var KEYMAPSO='catalog-layouts-search-only-'+(window.CATALOG_NS||'catalog');
var KEYLASTSO='catalog-layouts-search-only-last-'+(window.CATALOG_NS||'catalog');
var LAYOUT_SCOPE_DEFS=[
  {id:'sck',label:'Search+Content+Key'},
  {id:'sc',label:'Search+Content'},
  {id:'ck',label:'Content+Key'},
  {id:'c',label:'Content'}
];
var layoutUiScope=null;
function layoutScopeMeta(id){id=normalizeLayoutScope(id);for(var i=0;i<LAYOUT_SCOPE_DEFS.length;i++)if(LAYOUT_SCOPE_DEFS[i].id===id)return LAYOUT_SCOPE_DEFS[i];return LAYOUT_SCOPE_DEFS[0];}
function chromeSearchOpen(){return !document.body.classList.contains('search-chrome-collapsed');}
function chromeKwOpen(){return !document.body.classList.contains('kw-chrome-collapsed')&&document.body.classList.contains('kw-open');}
function liveLayoutScopeId(){var s=chromeSearchOpen(),k=chromeKwOpen();if(s&&k)return'sck';if(s)return'sc';if(k)return'ck';return'c';}
function normalizeLayoutScope(id){if(id==='search'||id===true)return'sc';if(id==='keywords'||id==='together'||id===false)return'sck';if(id==='sck'||id==='sc'||id==='ck'||id==='c')return id;return liveLayoutScopeId();}
function coerceScope(so){return normalizeLayoutScope(so);}
function applyLayoutChrome(id){
  id=normalizeLayoutScope(id);
  var wantS=(id==='sck'||id==='sc');
  var wantK=(id==='sck'||id==='ck');
  document.body.classList.toggle('search-chrome-collapsed',!wantS);
  document.body.classList.toggle('search-extras-collapsed',!wantS);
  document.body.classList.toggle('kw-chrome-collapsed',!wantK);
  var fw=document.getElementById('filterWrap');
  if(wantK){document.body.classList.add('kw-open');if(fw)fw.classList.add('open');}
  else{document.body.classList.remove('kw-open');if(fw)fw.classList.remove('open');}
  if(typeof applySidesCols==='function')applySidesCols();
  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
  if(typeof syncSearchHideBtn==='function')syncSearchHideBtn();
}
function defaultLayoutScope(){return liveLayoutScopeId();}
function activeLayoutScope(){
  if(layoutUiScope!=='sck'&&layoutUiScope!=='sc'&&layoutUiScope!=='ck'&&layoutUiScope!=='c')layoutUiScope=defaultLayoutScope();
  return layoutUiScope;
}
function layoutScopeSo(scope){return coerceScope(scope||activeLayoutScope())==='sc';}
function layoutScopeLabel(so){return layoutScopeMeta(so).label;}
function layoutMapKeyFor(so){
  var ns=window.CATALOG_NS||'catalog';
  var o=(typeof layoutOrientId==='function')?layoutOrientId():((typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides())?'portrait':'wide');
  if(o==='middle')return 'catalog-layouts-middle-'+coerceScope(so)+'-'+ns;
  if(o==='wide')return 'catalog-layouts-wide-'+ns;
  var flip=document.body.classList.contains('sides-portrait-flip')?'B':'A';
  var id=coerceScope(so);
  return 'catalog-layouts-portrait-'+flip+'-'+id+'-'+ns;
}
function layoutLastKeyFor(so){
  var ns=window.CATALOG_NS||'catalog';
  var o=(typeof layoutOrientId==='function')?layoutOrientId():((typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides())?'portrait':'wide');
  if(o==='middle')return 'catalog-layouts-middle-'+coerceScope(so)+'-last-'+ns;
  if(o==='wide')return 'catalog-layouts-wide-last-'+ns;
  var flip=document.body.classList.contains('sides-portrait-flip')?'B':'A';
  var id=coerceScope(so);
  return 'catalog-layouts-portrait-'+flip+'-'+id+'-last-'+ns;
}
function layoutMapKey(){return layoutMapKeyFor(activeLayoutScope());}
function layoutLastKey(){return layoutLastKeyFor(activeLayoutScope());}

function persistAllLiveLayouts(){
  try{if(typeof persist==='function')persist();}catch(err){}
  try{if(typeof persistHeight==='function')persistHeight();}catch(err){}
  try{if(typeof persistAcHeight==='function')persistAcHeight();}catch(err){}
  try{if(typeof persistAcWidth==='function')persistAcWidth();}catch(err){}
  try{if(typeof persistShadeHeight==='function')persistShadeHeight();}catch(err){}
  try{if(typeof snapshotLiveToMode==='function')snapshotLiveToMode();}catch(err){}
  try{
    if(typeof displayIsMiddle==='function'&&displayIsMiddle()&&typeof writeMiddleLayout==='function'){
      var ml=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-lw'),10)||0;
      var mh=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-menu-h'),10)||0;
      writeMiddleLayout(ml,mh);
    }
  }catch(err){}
}
function clearLiveLayoutKeys(so){
  try{
    if(so){
      localStorage.removeItem(KEYCH);localStorage.removeItem(KEYCV);
      localStorage.removeItem(KEYACSO);localStorage.removeItem(KEYACWSO);
      localStorage.removeItem(SEARCH_ONLY_UI_SCALE_KEY);
      setLastLayoutNameFor(true,'');
    }else{
      localStorage.removeItem(KEYH);localStorage.removeItem(KEYV);
      localStorage.removeItem(KEYHT+'-l');localStorage.removeItem(KEYHT+'-p');
      localStorage.removeItem(KEYAC);localStorage.removeItem(KEYSH);
      setLastLayoutNameFor(false,'');
    }
  }catch(err){}
}
function resetLayoutDefaults(scope){
  var so=coerceScope(scope||activeLayoutScope());
  applyLayoutChrome(so);
  clearLiveLayoutKeys(so==='sc');
  if(so!=='sc')clearLiveLayoutKeys(false);
  if(so){
    try{document.documentElement.style.setProperty('--search-ui-scale','1');document.documentElement.setAttribute('data-search-ui-scale','100');}catch(err){}
  }
  var el=typeof chrome==='function'?chrome():null;
  var w=typeof wrap==='function'?wrap():null;
  var sh=typeof acShell==='function'?acShell():null;
  if(el&&typeof clearHeight==='function')clearHeight(el);
  if(w&&typeof clearShadeBox==='function')clearShadeBox(w);
  if(sh){
    sh.classList.remove('ac-height-set','ac-width-set','ac-height-dragging','ac-width-dragging');
    sh.style.height='';sh.style.maxHeight='';sh.style.width='';sh.style.maxWidth='';
  }
  if(typeof applyAll==='function')applyAll();
  else if(window.syncSearchSplit)window.syncSearchSplit();
  try{
    document.body.style.removeProperty('--sides-lw');
    document.body.style.removeProperty('--sides-rw');
    document.body.style.removeProperty('--sides-index-h');
    document.documentElement.style.removeProperty('--portrait-lw');
    document.documentElement.style.removeProperty('--portrait-rw');
    document.documentElement.style.removeProperty('--portrait-menu-h');
    localStorage.removeItem('catalog-portrait-menu-h');
    localStorage.removeItem('catalog-portrait-lw');
    localStorage.removeItem('catalog-portrait-rw');
    try{
      localStorage.removeItem(typeof middleLwKey==='function'?middleLwKey():('catalog-middle-lw-'+(window.CATALOG_NS||'catalog')));
      localStorage.removeItem(typeof middleMhKey==='function'?middleMhKey():('catalog-middle-menu-h-'+(window.CATALOG_NS||'catalog')));
      localStorage.removeItem('catalog-middle-lw');
      localStorage.removeItem('catalog-middle-menu-h');
    }catch(eMid){}
    document.documentElement.style.removeProperty('--middle-lw');
    document.documentElement.style.removeProperty('--middle-rw');
    document.documentElement.style.removeProperty('--middle-menu-h');
    try{localStorage.removeItem('catalog-sides-portrait-flip-'+(window.CATALOG_NS||'catalog'));}catch(eFlip){}
    document.body.classList.remove('sides-portrait-flip');
  }catch(err){}
  if(typeof applySidesCols==='function')applySidesCols();
  return true;
}
window.persistAllLiveLayouts=persistAllLiveLayouts;
window.resetLayoutDefaults=resetLayoutDefaults;

function snapshotLayout(so){
  var id=coerceScope(so==null?activeLayoutScope():so);
  var lw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0;
  var rw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-rw'),10)||0;
  var ih=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-index-h'),10)||0;
  var ix=document.getElementById('catalogIndex');
  return {
    kind:id,
    lw:lw||undefined,rw:rw||undefined,indexH:ih||undefined,
    indexEmbed:!!(ix&&ix.classList.contains('is-embedded')),
    indexCollapsed:!!(ix&&ix.classList.contains('is-collapsed')),
    searchCollapsed:!chromeSearchOpen(),
    kwCollapsed:!chromeKwOpen(),
    ch:localStorage.getItem(KEYCH),
    cv:localStorage.getItem(KEYCV),
    acso:localStorage.getItem(KEYACSO),
    acw:localStorage.getItem(KEYACWSO),
    h:localStorage.getItem(KEYH),
    v:localStorage.getItem(KEYV),
    htL:localStorage.getItem(KEYHT+'-l'),
    htP:localStorage.getItem(KEYHT+'-p'),
    ac:localStorage.getItem(KEYAC),
    sh:localStorage.getItem(KEYSH),
    scale:typeof currentUiScale==='function'?currentUiScale():undefined,
    mlw:parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-lw'),10)||undefined,
    mmh:parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-menu-h'),10)||undefined
  };
}
function writeSnapKey(k,v){
  if(v==null||v==='')localStorage.removeItem(k);
  else localStorage.setItem(k,String(v));
}
function applySnapshot(snap,so){
  if(!snap)return;
  var id=coerceScope(so!=null?so:(snap.kind==='search-only'?'sc':(snap.kind==='together'?'sck':snap.kind)));
  applyLayoutChrome(id);
  writeSnapKey(KEYCH,snap.ch);writeSnapKey(KEYCV,snap.cv);
  writeSnapKey(KEYACSO,snap.acso||snap.ac);writeSnapKey(KEYACWSO,snap.acw);
  writeSnapKey(KEYH,snap.h);writeSnapKey(KEYV,snap.v);
  writeSnapKey(KEYHT+'-l',snap.htL);writeSnapKey(KEYHT+'-p',snap.htP);
  writeSnapKey(KEYAC,snap.ac);writeSnapKey(KEYSH,snap.sh);
  try{
    if(snap.lw)document.body.style.setProperty('--sides-lw',parseInt(snap.lw,10)+'px');
    if(snap.rw)document.body.style.setProperty('--sides-rw',parseInt(snap.rw,10)+'px');
    if(snap.indexH)document.body.style.setProperty('--sides-index-h',parseInt(snap.indexH,10)+'px');
    if(snap.mlw)document.documentElement.style.setProperty('--middle-lw',parseInt(snap.mlw,10)+'px');
    if(snap.mmh)document.documentElement.style.setProperty('--middle-menu-h',parseInt(snap.mmh,10)+'px');
    if((snap.mlw||snap.mmh)&&typeof writeMiddleLayout==='function')writeMiddleLayout(snap.mlw,snap.mmh);
    var ix=document.getElementById('catalogIndex');
    if(ix){
      if(typeof snap.indexEmbed==='boolean')ix.classList.toggle('is-embedded',!!snap.indexEmbed);
      ix.classList.add('is-collapsed');

      if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();
    }
  }catch(err){}
  if(typeof applyAll==='function')applyAll();
  if(typeof applySidesCols==='function')applySidesCols();
  if(typeof snapshotLiveToMode==='function')snapshotLiveToMode();
}
function readLayoutsFor(so){
  try{
    var o=JSON.parse(localStorage.getItem(layoutMapKeyFor(so))||'{}');
    return (o&&typeof o==='object'&&!Array.isArray(o))?o:{};
  }catch(err){return {};}
}
function writeLayoutsFor(so,map){try{localStorage.setItem(layoutMapKeyFor(so),JSON.stringify(map));}catch(err){}}
function readLayouts(){return readLayoutsFor(activeLayoutScope());}
function writeLayouts(map){writeLayoutsFor(activeLayoutScope(),map);}
function lastLayoutNameFor(so){try{return localStorage.getItem(layoutLastKeyFor(so))||'';}catch(err){return '';}}
function setLastLayoutNameFor(so,n){try{if(n)localStorage.setItem(layoutLastKeyFor(so),n);else localStorage.removeItem(layoutLastKeyFor(so));}catch(err){}}
function lastLayoutName(){return lastLayoutNameFor(activeLayoutScope());}
function setLastLayoutName(n){setLastLayoutNameFor(activeLayoutScope(),n);}
function syncLayoutScopeUi(){
  var id=activeLayoutScope();
  var meta=layoutScopeMeta(id);
  var btn=document.getElementById('layoutPresetsBtn');
  if(btn){
    btn.textContent='Layouts';
    btn.title='Save and apply menu-set sizes for '+meta.label;
  }
  var inp=document.getElementById('layoutPresetsName');
  if(inp)inp.placeholder='Name (e.g. Studio)';
  var save=document.getElementById('layoutPresetsSave');
  var upd=document.getElementById('layoutPresetsUpdate');
  if(save)save.textContent='Save '+meta.label;
  if(upd)upd.textContent='Update '+meta.label;
  document.querySelectorAll('.layout-presets-tab').forEach(function(t){
    var on=normalizeLayoutScope(t.getAttribute('data-layout-scope'))===id;
    t.classList.toggle('is-active',on);
    t.setAttribute('aria-selected',on?'true':'false');
  });
  var lab=document.getElementById('layoutPresetsStoreLabel');
  var wide=(typeof layoutOrientId==='function'?layoutOrientId():'')==='wide';
  if(lab)lab.textContent=wide?'Widescreen':meta.label;
  if(typeof syncPortraitFlipBtn==='function')syncPortraitFlipBtn();
  var rb=document.getElementById('layoutRestoreDefaults');
  if(rb)rb.textContent='Restore '+meta.label+' defaults';
  var pop=document.getElementById('layoutPresetsPop');
  if(pop&&!pop.hidden)renderLayoutList();
}
function syncLayoutStoreUi(){
  layoutUiScope=defaultLayoutScope();
  syncLayoutScopeUi();
}
window.syncLayoutStoreUi=syncLayoutStoreUi;
function setLayoutUiScope(scope){
  layoutUiScope=normalizeLayoutScope(scope);
  var inp=document.getElementById('layoutPresetsName');
  if(inp)inp.value=lastLayoutNameFor(layoutUiScope);
  syncLayoutScopeUi();
}
function readNamedMap(so){
  return readLayoutsFor(!!so);
}
function readLastNamed(so){
  return lastLayoutNameFor(!!so);
}
function uniqueLayoutName(base,so){
  if(so==null)so=activeLayoutScope();
  so=coerceScope(so);
  var map=readLayoutsFor(so);
  var lab=layoutScopeMeta(so).label;
  base=String(base||lab).replace(/^\s+|\s+$/g,'').slice(0,32)||lab;
  if(!map[base])return base;
  var i=2,n;
  do{n=base+' '+i;i++;}while(map[n]);
  return n.slice(0,40);
}
function applyActiveLayoutStore(){
  syncLayoutStoreUi();
  if(typeof applyModeSlot==='function')applyModeSlot(typeof currentDisplay!=='undefined'?currentDisplay:'upper');
  applyAll();
  if(typeof applySidesCols==='function')applySidesCols();
  if(typeof applyFsChromeSize==='function')applyFsChromeSize();

}
window.applyActiveLayoutStore=applyActiveLayoutStore;
function closeLayoutPop(){
  var pop=document.getElementById('layoutPresetsPop');
  var btn=document.getElementById('layoutPresetsBtn');
  if(pop){pop.hidden=true;pop.classList.remove('open');}
  if(btn)btn.setAttribute('aria-expanded','false');
}
function placeLayoutPop(){
  var pop=document.getElementById('layoutPresetsPop');
  var btn=document.getElementById('layoutPresetsBtn');
  if(!pop||!btn||pop.hidden)return;
  var vv=window.visualViewport;
  var vh=vv?vv.height:((window.innerHeight)||0);
  var topOff=vv?vv.offsetTop:0;
  var leftOff=vv?vv.offsetLeft:0;
  var br=btn.getBoundingClientRect();
  var pad=8;
  var below=vh-(br.bottom-topOff)-pad;
  var above=(br.top-topOff)-pad;
  var maxH=Math.min(420,Math.max(180,Math.max(below,above)));
  var width=Math.min(420,Math.max(260,(vv?vv.width:window.innerWidth)-pad*2));
  var left=Math.min(Math.max(pad+leftOff,br.left),leftOff+(vv?vv.width:window.innerWidth)-width-pad);
  pop.style.position='fixed';
  pop.style.left=Math.round(left)+'px';
  pop.style.width=Math.round(width)+'px';
  pop.style.maxHeight=Math.round(maxH)+'px';
  if(below>=180||below>=above){
    pop.style.top=Math.round(br.bottom+4)+'px';
    pop.style.bottom='auto';
  }else{
    pop.style.top='auto';
    pop.style.bottom=Math.round((vv?vv.height+vv.offsetTop:window.innerHeight)-br.top+4)+'px';
  }
}
function renderLayoutList(){
  var list=document.getElementById('layoutPresetsList');
  if(!list)return;
  var so=activeLayoutScope();
  var map=readLayoutsFor(so);
  var names=Object.keys(map).sort(function(a,b){return a.localeCompare(b);});
  var last=lastLayoutNameFor(so);
  var html='';
  if(!names.length){list.innerHTML='<p class="layout-presets-empty" style="margin:0 0 6px;color:var(--text-muted);font-size:.9em">No saved '+layoutScopeMeta(so).label+' layouts yet.</p>';return;}
  names.forEach(function(n){
    var label=n;
    html+='<div class="layout-presets-item"><button type="button" class="layout-presets-item-name'+(n===last?' is-active':'')+'" data-name="'+n.replace(/"/g,'&quot;')+'">'+label.replace(/&/g,'&amp;').replace(/</g,'&lt;')+'</button><button type="button" class="layout-presets-item-del" data-del="'+n.replace(/"/g,'&quot;')+'" aria-label="Delete '+n.replace(/"/g,'&quot;')+'">✕</button></div>';
  });
  list.innerHTML=html;
}
function flashLayoutSaveFeedback(kind){
  var save=document.getElementById('layoutPresetsSave');
  var upd=document.getElementById('layoutPresetsUpdate');
  var flash=document.getElementById('layoutPresetsFlash');
  var btn=kind==='update'?upd:save;
  var msg=kind==='update'?'Updated':'Saved';
  if(btn){
    btn.classList.add('is-pressed','is-flash');
    var prev=btn.getAttribute('data-label')||btn.textContent;
    btn.setAttribute('data-label',prev);
    btn.textContent=msg;
    clearTimeout(btn._flashT);
    btn._flashT=setTimeout(function(){
      btn.classList.remove('is-pressed','is-flash');
      var restore=btn.getAttribute('data-label');
      if(restore)btn.textContent=restore;
      if(typeof syncLayoutScopeUi==='function')syncLayoutScopeUi();
    },1100);
  }
  if(flash){
    flash.textContent=msg;
    flash.classList.add('is-on');
    clearTimeout(flash._flashT);
    flash._flashT=setTimeout(function(){flash.classList.remove('is-on');flash.textContent='';},1100);
  }
}
function saveNamedLayout(name,overwrite){
  var so=activeLayoutScope();
  if(typeof persistAllLiveLayouts==='function')persistAllLiveLayouts();
  else if(so&&searchOnlyStore()){
    persistAcHeight();
    persistAcWidth();
  }
  name=String(name||'').replace(/^\s+|\s+$/g,'').slice(0,40);
  if(!name)name=uniqueLayoutName(layoutScopeMeta(so).label,so);
  else if(!overwrite&&readLayoutsFor(so)[name]&&name!==lastLayoutNameFor(so))name=uniqueLayoutName(name,so);
  var map=readLayoutsFor(so);
  map[name]=snapshotLayout(so);
  writeLayoutsFor(so,map);
  setLastLayoutNameFor(so,name);
  var inp=document.getElementById('layoutPresetsName');
  if(inp)inp.value=name;
  renderLayoutList();
  return true;
}
function applyNamedLayout(name){
  var so=activeLayoutScope();
  var map=readLayoutsFor(so);
  if(!map[name])return;
  applySnapshot(map[name],so);
  setLastLayoutNameFor(so,name);
  renderLayoutList();
}
function deleteNamedLayout(name){
  var so=activeLayoutScope();
  var map=readLayoutsFor(so);
  delete map[name];
  writeLayoutsFor(so,map);
  if(lastLayoutNameFor(so)===name)setLastLayoutNameFor(so,'');
  renderLayoutList();
}
function openLayoutPop(){
  if(typeof closeSearchOnlyScalePop==="function")closeSearchOnlyScalePop();
  closeUiScalePop();
  layoutUiScope=defaultLayoutScope();
  var pop=document.getElementById('layoutPresetsPop');
  var btn=document.getElementById('layoutPresetsBtn');
  if(!pop||!btn)return;
  if(typeof ensurePortraitFlipBtn==='function')ensurePortraitFlipBtn();
  else if(typeof syncPortraitFlipBtn==='function')syncPortraitFlipBtn();
  syncLayoutScopeUi();
  renderLayoutList();
  pop.hidden=false;
  pop.classList.add('open');
  btn.setAttribute('aria-expanded','true');
  placeLayoutPop();
  var inp=document.getElementById('layoutPresetsName');
  if(inp)inp.value=lastLayoutName()||inp.value||'';
}
var UI_SCALE_STEPS=[50,67,75,80,90,100,110,125,133,140,150,175,200,250,300];
var UI_SCALE_KEY='catalog-ui-scale-'+(window.CATALOG_NS==='kontakt'?'kontakt':'ds');
var SEARCH_ONLY_UI_SCALE_KEY='catalog-search-only-ui-scale-'+(window.CATALOG_NS==='kontakt'?'kontakt':'ds');
function readSavedSearchOnlyUiScale(){
  try{
    var n=parseInt(localStorage.getItem(SEARCH_ONLY_UI_SCALE_KEY)||'',10);
    if(UI_SCALE_STEPS.indexOf(n)>=0)return n;
  }catch(err){}
  return null;
}
function currentSearchOnlyUiScale(){
  var attr=parseInt(document.documentElement.getAttribute('data-search-ui-scale')||'',10);
  if(UI_SCALE_STEPS.indexOf(attr)>=0)return attr;
  var raw=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--search-ui-scale'));
  if(isFinite(raw)&&raw>0){
    var pct=Math.round(raw*100);
    if(UI_SCALE_STEPS.indexOf(pct)>=0)return pct;
  }
  var saved=readSavedSearchOnlyUiScale();
  if(saved!=null)return saved;
  return 100;
}
function syncSearchOnlyScaleUi(pct){
  if(pct==null||UI_SCALE_STEPS.indexOf(pct)<0)pct=currentSearchOnlyUiScale();
  var read=document.getElementById('searchOnlyScaleReadout');
  if(read){
    read.textContent=pct+'%';
    read.title='Search scale';
  }
  var dn=document.getElementById('searchOnlyScaleDown');
  var up=document.getElementById('searchOnlyScaleUp');
  if(dn)dn.disabled=pct<=UI_SCALE_STEPS[0];
  if(up)up.disabled=pct>=UI_SCALE_STEPS[UI_SCALE_STEPS.length-1];
  document.querySelectorAll('#searchOnlyScalePop .ui-scale-choice').forEach(function(b){
    b.classList.toggle('is-active',parseInt(b.getAttribute('data-scale'),10)===pct);
  });
}
function applySearchOnlyUiScaleCss(pct){
  if(UI_SCALE_STEPS.indexOf(pct)<0)pct=100;
  document.documentElement.style.setProperty('--search-ui-scale',String(pct/100));
  document.documentElement.setAttribute('data-search-ui-scale',String(pct));
  // Readout must follow the value just applied (not stale localStorage).
  syncSearchOnlyScaleUi(pct);
}
function refreshSearchOnlyLayout(){
  if(typeof applyAcHeight==='function'){
    applyAcHeight();
    requestAnimationFrame(function(){if(typeof applyAcHeight==='function')applyAcHeight();});
  }else if(window.syncSearchSplit)window.syncSearchSplit();
}
function setSearchOnlyUiScale(pct,persist){
  if(UI_SCALE_STEPS.indexOf(pct)<0)return;
  if(persist){
    try{localStorage.setItem(SEARCH_ONLY_UI_SCALE_KEY,String(pct));}catch(err){}
  }
  applySearchOnlyUiScaleCss(pct);
  refreshSearchOnlyLayout();
}
function closeSearchOnlyScalePop(){
  var pop=document.getElementById('searchOnlyScalePop');
  var btn=document.getElementById('searchOnlyScaleReadout');
  if(pop){pop.hidden=true;pop.classList.remove('open');}
  if(btn)btn.setAttribute('aria-expanded','false');
}
function placeSearchOnlyScalePop(){
  var pop=document.getElementById('searchOnlyScalePop');
  var btn=document.getElementById('searchOnlyScaleReadout');
  if(!pop||!btn||pop.hidden)return;
  var vv=window.visualViewport;
  var vh=vv?vv.height:((window.innerHeight)||0);
  var topOff=vv?vv.offsetTop:0;
  var leftOff=vv?vv.offsetLeft:0;
  var br=btn.getBoundingClientRect();
  var pad=8;
  var below=vh-(br.bottom-topOff)-pad;
  var above=(br.top-topOff)-pad;
  var maxH=Math.min(360,Math.max(120,Math.max(below,above)));
  var width=Math.min(220,Math.max(140,(vv?vv.width:window.innerWidth)-pad*2));
  var left=Math.min(Math.max(pad+leftOff,br.left),leftOff+(vv?vv.width:window.innerWidth)-width-pad);
  pop.style.position='fixed';
  pop.style.left=Math.round(left)+'px';
  pop.style.width=Math.round(width)+'px';
  pop.style.maxHeight=Math.round(maxH)+'px';
  if(below>=140||below>=above){
    pop.style.top=Math.round(br.bottom+4)+'px';
    pop.style.bottom='auto';
  }else{
    pop.style.top='auto';
    pop.style.bottom=Math.round((vv?vv.height+vv.offsetTop:window.innerHeight)-br.top+4)+'px';
  }
}
function renderSearchOnlyScaleList(){
  var pop=document.getElementById('searchOnlyScalePop');
  if(!pop)return;
  var cur=currentSearchOnlyUiScale();
  var html='';
  UI_SCALE_STEPS.forEach(function(n){
    html+='<button type="button" class="ui-scale-choice'+(n===cur?' is-active':'')+'" data-scale="'+n+'">'+n+'%</button>';
  });
  pop.innerHTML=html;
}
function openSearchOnlyScalePop(){
  if(typeof closeUiScalePop==='function')closeUiScalePop();
  if(typeof closeLayoutPop==='function')closeLayoutPop();
  var pop=document.getElementById('searchOnlyScalePop');
  var btn=document.getElementById('searchOnlyScaleReadout');
  if(!pop||!btn)return;
  renderSearchOnlyScaleList();
  pop.hidden=false;
  pop.classList.add('open');
  btn.setAttribute('aria-expanded','true');
  placeSearchOnlyScalePop();
}
function stepSearchOnlyUiScale(dir){
  var cur=currentSearchOnlyUiScale();
  var i=UI_SCALE_STEPS.indexOf(cur);
  if(i<0)i=UI_SCALE_STEPS.indexOf(100);
  var n=UI_SCALE_STEPS[Math.max(0,Math.min(UI_SCALE_STEPS.length-1,i+dir))];
  setSearchOnlyUiScale(n,true);
}
function nearestSearchOnlyStep(pct){
  var best=UI_SCALE_STEPS[0],d=Math.abs(pct-best);
  UI_SCALE_STEPS.forEach(function(n){
    var dd=Math.abs(pct-n);
    if(dd<d){best=n;d=dd;}
  });
  return best;
}
function searchOnlyPinchDist(a,b){
  var dx=a.clientX-b.clientX,dy=a.clientY-b.clientY;
  return Math.sqrt(dx*dx+dy*dy);
}
function searchOnlyPinchOn(el){
  return !!(el&&el.closest&&el.closest('#searchCol,#acShell,#searchStrip,#acList,#acFsBar'));
}
var searchOnlyPinch=null;
function onSearchOnlyPinchStart(e){
  if(!searchOnlyStore()||document.body.classList.contains('ac-fs-open')||!e.touches||e.touches.length!==2){searchOnlyPinch=null;return;}
  if(!searchOnlyPinchOn(e.target)&&!(e.touches[0]&&searchOnlyPinchOn(document.elementFromPoint(e.touches[0].clientX,e.touches[0].clientY))))return;
  var d=searchOnlyPinchDist(e.touches[0],e.touches[1]);
  if(!(d>8))return;
  searchOnlyPinch={start:d,pct:currentSearchOnlyUiScale()};
}
function onSearchOnlyPinchMove(e){
  if(!searchOnlyPinch||!e.touches||e.touches.length!==2)return;
  var d=searchOnlyPinchDist(e.touches[0],e.touches[1]);
  if(!(searchOnlyPinch.start>0)||!(d>0))return;
  e.preventDefault();
  var n=nearestSearchOnlyStep(searchOnlyPinch.pct*(d/searchOnlyPinch.start));
  if(n!==currentSearchOnlyUiScale())setSearchOnlyUiScale(n,true);
}
function onSearchOnlyPinchEnd(e){
  if(!e.touches||e.touches.length<2)searchOnlyPinch=null;
}
function initSearchOnlyPinch(){
  if(document.documentElement.dataset.searchPinchBound)return;
  document.documentElement.dataset.searchPinchBound='1';
  document.addEventListener('touchstart',onSearchOnlyPinchStart,{passive:true,capture:true});
  document.addEventListener('touchmove',onSearchOnlyPinchMove,{passive:false,capture:true});
  document.addEventListener('touchend',onSearchOnlyPinchEnd,{passive:true,capture:true});
  document.addEventListener('touchcancel',onSearchOnlyPinchEnd,{passive:true,capture:true});
}
function initSearchOnlyUiScale(){
  applySearchOnlyUiScaleCss(currentSearchOnlyUiScale());
  syncSearchOnlyScaleUi();
  initSearchOnlyPinch();
  var down=document.getElementById('searchOnlyScaleDown');
  var up=document.getElementById('searchOnlyScaleUp');
  var read=document.getElementById('searchOnlyScaleReadout');
  var pop=document.getElementById('searchOnlyScalePop');
  if(down)down.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();stepSearchOnlyUiScale(-1);});
  if(up)up.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();stepSearchOnlyUiScale(1);});
  if(read)read.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    if(pop&&!pop.hidden)closeSearchOnlyScalePop();
    else openSearchOnlyScalePop();
  });
  if(pop)pop.addEventListener('click',function(e){
    var b=e.target.closest&&e.target.closest('[data-scale]');
    if(!b)return;
    e.preventDefault();e.stopPropagation();
    setSearchOnlyUiScale(parseInt(b.getAttribute('data-scale'),10),true);
    closeSearchOnlyScalePop();
  });
  document.addEventListener('click',function(e){
    if(!pop||pop.hidden)return;
    if(e.target.closest&&e.target.closest('#searchOnlyScale,#searchOnlyScalePop'))return;
    closeSearchOnlyScalePop();
  });
  window.addEventListener('resize',placeSearchOnlyScalePop);
  if(window.visualViewport)window.visualViewport.addEventListener('resize',placeSearchOnlyScalePop);
  window.syncSearchOnlyScaleUi=syncSearchOnlyScaleUi;
}
function readSavedUiScale(){
  try{
    var n=parseInt(localStorage.getItem(UI_SCALE_KEY)||'',10);
    if(UI_SCALE_STEPS.indexOf(n)>=0)return n;
  }catch(err){}
  return null;
}
function currentUiScale(){
  var saved=readSavedUiScale();
  if(saved!=null)return saved;
  var raw=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--ui-scale'));
  if(isFinite(raw)&&raw>0){
    var pct=Math.round(raw*100);
    if(UI_SCALE_STEPS.indexOf(pct)>=0)return pct;
  }
  return 100;
}
function landColsForScale(pct){
  if(pct>=200)return 1;
  if(pct>=150)return 2;
  return 3;
}
function applyUiScaleCss(pct){
  if(UI_SCALE_STEPS.indexOf(pct)<0)pct=100;
  var root=document.documentElement;
  root.style.setProperty('--ui-scale',String(pct/100));
  root.setAttribute('data-ui-scale',String(pct));
  root.style.setProperty('--cat-land-cols',String(landColsForScale(pct)));
  var read=document.getElementById('uiScaleReadout');
  if(read)read.textContent=pct+'%';
  var dn=document.getElementById('uiScaleDown');
  var up=document.getElementById('uiScaleUp');
  if(dn)dn.disabled=pct<=UI_SCALE_STEPS[0];
  if(up)up.disabled=pct>=UI_SCALE_STEPS[UI_SCALE_STEPS.length-1];
  document.querySelectorAll('#uiScalePop .ui-scale-choice').forEach(function(b){
    b.classList.toggle('is-active',parseInt(b.getAttribute('data-scale'),10)===pct);
  });
}
function reapplyLayoutAfterScale(){
  applyActiveLayoutStore();
}
function setUiScale(pct,persist){
  if(UI_SCALE_STEPS.indexOf(pct)<0)return;
  applyUiScaleCss(pct);
  if(persist){
    try{localStorage.setItem(UI_SCALE_KEY,String(pct));}catch(err){}
  }
  reapplyLayoutAfterScale();
  requestAnimationFrame(function(){reapplyLayoutAfterScale();});
}
function closeUiScalePop(){
  var pop=document.getElementById('uiScalePop');
  var btn=document.getElementById('uiScaleReadout');
  if(pop){pop.hidden=true;pop.classList.remove('open');}
  if(btn)btn.setAttribute('aria-expanded','false');
}
function placeUiScalePop(){
  var pop=document.getElementById('uiScalePop');
  var btn=document.getElementById('uiScaleReadout');
  if(!pop||!btn||pop.hidden)return;
  var vv=window.visualViewport;
  var vh=vv?vv.height:((window.innerHeight)||0);
  var topOff=vv?vv.offsetTop:0;
  var leftOff=vv?vv.offsetLeft:0;
  var br=btn.getBoundingClientRect();
  var pad=8;
  var below=vh-(br.bottom-topOff)-pad;
  var above=(br.top-topOff)-pad;
  var maxH=Math.min(360,Math.max(120,Math.max(below,above)));
  var width=Math.min(220,Math.max(140,(vv?vv.width:window.innerWidth)-pad*2));
  var left=Math.min(Math.max(pad+leftOff,br.left),leftOff+(vv?vv.width:window.innerWidth)-width-pad);
  pop.style.position='fixed';
  pop.style.left=Math.round(left)+'px';
  pop.style.width=Math.round(width)+'px';
  pop.style.maxHeight=Math.round(maxH)+'px';
  if(below>=140||below>=above){
    pop.style.top=Math.round(br.bottom+4)+'px';
    pop.style.bottom='auto';
  }else{
    pop.style.top='auto';
    pop.style.bottom=Math.round((vv?vv.height+vv.offsetTop:window.innerHeight)-br.top+4)+'px';
  }
}
function renderUiScaleList(){
  var pop=document.getElementById('uiScalePop');
  if(!pop)return;
  var cur=currentUiScale();
  var html='';
  UI_SCALE_STEPS.forEach(function(n){
    html+='<button type="button" class="ui-scale-choice'+(n===cur?' is-active':'')+'" data-scale="'+n+'">'+n+'%</button>';
  });
  pop.innerHTML=html;
}
function openUiScalePop(){
  if(typeof closeSearchOnlyScalePop==="function")closeSearchOnlyScalePop();
  closeLayoutPop();
  var pop=document.getElementById('uiScalePop');
  var btn=document.getElementById('uiScaleReadout');
  if(!pop||!btn)return;
  renderUiScaleList();
  pop.hidden=false;
  pop.classList.add('open');
  btn.setAttribute('aria-expanded','true');
  placeUiScalePop();
}
function stepUiScale(dir){
  var cur=currentUiScale();
  var i=UI_SCALE_STEPS.indexOf(cur);
  if(i<0)i=UI_SCALE_STEPS.indexOf(100);
  var n=UI_SCALE_STEPS[Math.max(0,Math.min(UI_SCALE_STEPS.length-1,i+dir))];
  setUiScale(n,true);
}
function initUiScale(){
  applyUiScaleCss(currentUiScale());
  var down=document.getElementById('uiScaleDown');
  var up=document.getElementById('uiScaleUp');
  var read=document.getElementById('uiScaleReadout');
  var pop=document.getElementById('uiScalePop');
  if(down)down.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();stepUiScale(-1);});
  if(up)up.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();stepUiScale(1);});
  if(read)read.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    if(pop&&!pop.hidden)closeUiScalePop();
    else openUiScalePop();
  });
  if(pop)pop.addEventListener('click',function(e){
    var b=e.target.closest&&e.target.closest('[data-scale]');
    if(!b)return;
    e.preventDefault();e.stopPropagation();
    setUiScale(parseInt(b.getAttribute('data-scale'),10),true);
    closeUiScalePop();
  });
  document.addEventListener('click',function(e){
    if(!pop||pop.hidden)return;
    if(e.target.closest&&e.target.closest('#uiScale,#uiScalePop'))return;
    closeUiScalePop();
  });
  window.addEventListener('resize',placeUiScalePop);
  if(window.visualViewport)window.visualViewport.addEventListener('resize',placeUiScalePop);
}
function initLayoutPresets(){
  var btn=document.getElementById('layoutPresetsBtn');
  var pop=document.getElementById('layoutPresetsPop');
  var save=document.getElementById('layoutPresetsSave');
  var upd=document.getElementById('layoutPresetsUpdate');
  var list=document.getElementById('layoutPresetsList');
  if(btn)btn.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    if(pop&&!pop.hidden)closeLayoutPop();
    else openLayoutPop();
  });
  document.querySelectorAll('.layout-presets-tab').forEach(function(tab){
    tab.addEventListener('click',function(e){
      e.preventDefault();e.stopPropagation();
      setLayoutUiScope(tab.getAttribute('data-layout-scope'));
    });
  });
  if(save)save.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    save.classList.add('is-pressed');
    var inp=document.getElementById('layoutPresetsName');
    saveNamedLayout(inp&&inp.value);
    flashLayoutSaveFeedback('save');
  });
  if(upd)upd.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    upd.classList.add('is-pressed');
    var inp=document.getElementById('layoutPresetsName');
    var n=(inp&&inp.value.replace(/^\s+|\s+$/g,''))||lastLayoutName();
    saveNamedLayout(n,true);
    flashLayoutSaveFeedback('update');
  });
  if(list)list.addEventListener('click',function(e){
    var del=e.target.closest&&e.target.closest('[data-del]');
    if(del){e.preventDefault();e.stopPropagation();deleteNamedLayout(del.getAttribute('data-del'));return;}
    var nameBtn=e.target.closest&&e.target.closest('[data-name]');
    if(nameBtn){e.preventDefault();e.stopPropagation();applyNamedLayout(nameBtn.getAttribute('data-name'));}
  });
  document.addEventListener('click',function(e){
    if(!pop||pop.hidden)return;
    if(e.target.closest&&e.target.closest('#layoutPresets,#layoutPresetsPop,.layout-presets'))return;
    closeLayoutPop();
  });
  window.addEventListener('resize',placeLayoutPop);
  if(window.visualViewport)window.visualViewport.addEventListener('resize',placeLayoutPop);
  syncLayoutStoreUi();
}
window.syncSearchSplit=applyAll;
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){init();initLayoutPresets();initUiScale();initSearchOnlyUiScale();});
else {init();initLayoutPresets();initUiScale();initSearchOnlyUiScale();}
})();
 function pillMatch(el,k){
   var name=elNameLc(el);
   var nameNorm=name.replace(/[^a-z0-9]+/g,' ').replace(/^\s+|\s+$/g,'');
   if(kws(el).indexOf(k)>=0||others(el).indexOf(k)>=0||patches(el).indexOf(k)>=0)return true;
   if(name===k||nameNorm===k)return true;
   if(patchNames(el).indexOf(k)>=0)return true;
   if(k.length>=2&&patchNames(el).some(function(n){return n.indexOf(k)>=0;}))return true;
   return false;
 }
 function applySearch(){
   var grid=document.querySelector('.catalog-body');
   var hasPills=searchKeywords.length>0;
   var typed=searchInput?searchInput.value.trim():'';
   var typedLc=typed.toLowerCase();
   if(grid)grid.style.display='';
   entries.forEach(function(el){
     var kwMatch=!hasPills||searchKeywords.every(function(k){return pillMatch(el,k);});
     var qMatch=!typedLc||typedMatch(el,typedLc);
     var show=kwMatch&&catMatch(el)&&qMatch;
     el.style.display=show?'':'none';
     el.classList.toggle('is-hidden',!show);
     el.classList.toggle('hit',(hasPills||!!typedLc)&&show);
     el.classList.remove('dim','fav-rec');
   });
   idx.forEach(function(li){
     var el=entryForIdx(li);
     var kwMatch=el&&(!hasPills||searchKeywords.every(function(k){return pillMatch(el,k);}));
     var qMatch=el&&(!typedLc||typedMatch(el,typedLc));
     var show=!!el&&kwMatch&&catMatch(el)&&qMatch;
     li.classList.toggle('hit',(hasPills||!!typedLc)&&show);
     li.style.display=show?'':'none';
   });
   document.body.classList.remove('search-empty-recs');
   syncHighlight();
   renderKwBar();
   syncLocGroups();
   if(!document.body.classList.contains('search-extras-collapsed')&&acList&&(acList.classList.contains('open')||(searchInput&&document.activeElement===searchInput))){
     showAc(searchInput?searchInput.value.trim().toLowerCase():'');
   }
 }
 window.applySearch=applySearch;
 function closeSearchExtras(){
   if(acList){acList.classList.remove('open');acList.innerHTML='';}
   document.body.classList.add('search-extras-collapsed','search-chrome-collapsed');
   if(window.syncSearchHideBtn)window.syncSearchHideBtn();
 }
 window.closeSearchExtras=closeSearchExtras;
 window.showSearchExtras=function(){document.body.classList.remove('search-extras-collapsed','search-chrome-collapsed');if(window.syncSearchHideBtn)window.syncSearchHideBtn();if(window.restoreSearchUi)window.restoreSearchUi();};
function historyCloudEl(){return document.getElementById('historyCloud');}
function parkHistoryCloud(){
  var wrap=document.getElementById('searchHistoryWrap');
  var strip=document.getElementById('searchStrip');
  var clr=strip&&strip.querySelector('.search-strip-clear');
  if(wrap&&strip&&wrap.parentElement!==strip){
    if(clr&&clr.nextSibling)strip.insertBefore(wrap,clr.nextSibling);
    else strip.appendChild(wrap);
  }
  var cloud=historyCloudEl();
  if(cloud&&cloud.parentNode!==document.body)document.body.appendChild(cloud);
  return cloud;
}
function historyBtnEl(){return document.getElementById('searchHistory');}
function hideHistoryCloud(){
  var cloud=historyCloudEl(),btn=historyBtnEl();
  if(cloud){cloud.hidden=true;cloud.classList.remove('cloud-above','cloud-below');}
  if(btn)btn.setAttribute('aria-expanded','false');
}
function placeHistoryCloud(){
  var cloud=historyCloudEl(),btn=historyBtnEl();
  if(!cloud||cloud.hidden)return;
  if(!btn){cloud.style.left='12px';cloud.style.top='72px';return;}
  var br=btn.getBoundingClientRect();
  var pad=8;
  var vv=window.visualViewport;
  var safeL=(vv?vv.offsetLeft:0)+pad;
  var safeT=(vv?vv.offsetTop:0)+pad;
  var vw=(vv?vv.width:window.innerWidth)||window.innerWidth;
  var vh=(vv?vv.height:window.innerHeight)||window.innerHeight;
  var safeR=safeL+vw-pad;
  var safeB=safeT+vh-pad;
  cloud.style.left='0px';cloud.style.top='0px';
  var cr=cloud.getBoundingClientRect();
  var w=cr.width||180,h=cr.height||72;
  var left=br.right-w;
  if(left<safeL)left=safeL;
  if(left+w>safeR)left=Math.max(safeL,safeR-w);
  var below=br.bottom+10;
  var above=br.top-10-h;
  var top,placeBelow;
  if(below+h<=safeB||above<safeT){top=Math.min(below,Math.max(safeT,safeB-h));placeBelow=true;}
  else{top=Math.max(safeT,above);placeBelow=false;}
  cloud.style.left=Math.round(left)+'px';
  cloud.style.top=Math.round(top)+'px';
  cloud.classList.toggle('cloud-below',placeBelow);
  cloud.classList.toggle('cloud-above',!placeBelow);
  var tail=Math.max(12,Math.min(w-12,(br.left+br.width/2)-left-6));
  cloud.style.setProperty('--cloud-tail-x',Math.round(tail)+'px');
}
function historyPickBuckets(){
  var picks=document.getElementById('historyPicks'),out={};
  if(!picks)return out;
  picks.querySelectorAll('input[type="checkbox"][data-hist]').forEach(function(cb){if(cb.checked)out[cb.getAttribute('data-hist')]=1;});
  return out;
}
function renderHistoryPicks(){
  var el=document.getElementById('historyPicks');
  if(!el)return;
  var sessN=(pinSessionStore&&pinSessionStore.sessions||[]).length;
  var recN=(pinSessionStore&&pinSessionStore.recent||[]).length;
  var sessLab='Saved sessions'+(recN?' \u00b7 '+recN+' recent':'');
  var rows=[
    {id:'commits',label:'Searched keywords',n:Object.keys(searchCommitCounts||{}).length,on:1},
    {id:'recent',label:'Recent keywords',n:(recentKwStore||[]).length,on:1},
    {id:'combos',label:'Keyword combos',n:(typeof kwAutoCombos==='function'?kwAutoCombos():(kwComboStore||[])).length,on:1},
    {id:'cards',label:'Card hits',n:Object.keys(cardHitStore||{}).length,on:1},
    {id:'savedCombos',label:'Saved combinations',n:(typeof kwSavedCombos==='function'?kwSavedCombos():[]).length,on:0},
    {id:'sessions',label:sessLab,n:sessN,on:0}
  ];
  el.innerHTML=rows.map(function(r){return '<label><input type="checkbox" data-hist="'+r.id+'"'+(r.on?' checked':'')+'> <span>'+r.label+'</span> <span class="ac-hist-count">'+r.n+'</span></label>';}).join('');
}
function showHistoryCloud(){
  var cloud=historyCloudEl(),btn=historyBtnEl();
  cloud=parkHistoryCloud()||cloud;
  if(!cloud)return;
  if(typeof renderHistoryPicks==='function')renderHistoryPicks();
  cloud.hidden=false;
  window.__histIgnoreUntil=Date.now()+800;
  if(btn)btn.setAttribute('aria-expanded','true');
  placeHistoryCloud();
}
window.clearSearchHistoryData=function(opts){
  opts=opts||{};
  var buckets=opts.buckets||(typeof historyPickBuckets==='function'?historyPickBuckets():{});
  var keys=Object.keys(buckets||{}).filter(function(k){return buckets[k];});
  if(!keys.length){
    hideHistoryCloud();
    return;
  }
  if(buckets.commits){
    searchCommitCounts={};
    if(typeof persistSearchCommits==='function')persistSearchCommits();
    else if(typeof lsSet==='function'&&typeof SEARCH_COMMIT_KEY!=='undefined')lsSet(SEARCH_COMMIT_KEY,{});
  }
  if(buckets.recent){
    recentKwStore=[];
    if(typeof persistRecentKws==='function')persistRecentKws();
  }
  if(buckets.combos&&buckets.savedCombos){
    kwComboStore=[];
    if(typeof persistKwCombos==='function')persistKwCombos();
  }else if(buckets.combos){
    kwComboStore=(kwComboStore||[]).filter(function(o){return o&&o.saved;});
    if(typeof persistKwCombos==='function')persistKwCombos();
  }else if(buckets.savedCombos){
    kwComboStore=(kwComboStore||[]).filter(function(o){return o&&!o.saved;});
    if(typeof persistKwCombos==='function')persistKwCombos();
  }
  if(buckets.cards){
    cardHitStore={};
    if(typeof persistCardHits==='function')persistCardHits();
  }
  if(buckets.sessions){
    pinSessionStore={sessions:[],recent:[]};
    if(typeof persistPinSessions==='function')persistPinSessions();
  }
  hideHistoryCloud();
  try{
    if(typeof showAc==='function'){
      var q=(typeof searchInput!=='undefined'&&searchInput)?searchInput.value.trim().toLowerCase():'';
      var ac=document.getElementById('acList');
      if(ac&&(ac.classList.contains('open')||(searchInput&&document.activeElement===searchInput)))showAc(q,{force:true});
    }
  }catch(err){}
};
window.showHistoryCloud=showHistoryCloud;
window.hideHistoryCloud=hideHistoryCloud;
window.placeHistoryCloud=placeHistoryCloud;
window.parkHistoryCloud=parkHistoryCloud;
(function bindHistoryCloud(){
  if(typeof parkHistoryCloud==='function')parkHistoryCloud();
  var btn=historyBtnEl(),yes=document.getElementById('historyYes'),no=document.getElementById('historyNo'),all=document.getElementById('historyAll'),searchAll=document.getElementById('historySearchAll'),cloud=historyCloudEl();
  if(btn)btn.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    if(cloud&&!cloud.hidden)hideHistoryCloud();else showHistoryCloud();
  });
  if(searchAll)searchAll.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    var picks=document.getElementById('historyPicks');
    if(picks)picks.querySelectorAll('input[type="checkbox"][data-hist]').forEach(function(cb){var h=cb.getAttribute('data-hist');cb.checked=h!=='sessions'&&h!=='savedCombos';});
  });
  if(all)all.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    var picks=document.getElementById('historyPicks');
    if(picks)picks.querySelectorAll('input[type="checkbox"][data-hist]').forEach(function(cb){cb.checked=true;});
  });
  if(yes)yes.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();window.clearSearchHistoryData();});
  if(no)no.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();hideHistoryCloud();});
  document.addEventListener('pointerdown',function(e){
    if(!cloud||cloud.hidden)return;
    if(window.__histIgnoreUntil&&Date.now()<window.__histIgnoreUntil)return;
    if(e.target.closest&&(e.target.closest('#historyCloud')||e.target.closest('#searchHistory')||e.target.closest('#searchHistoryWrap')))return;
    hideHistoryCloud();
  },true);
  window.addEventListener('resize',function(){if(cloud&&!cloud.hidden)placeHistoryCloud();},{passive:true});
  if(window.visualViewport)window.visualViewport.addEventListener('resize',function(){if(cloud&&!cloud.hidden)placeHistoryCloud();},{passive:true});
})();
 window.clearAllFilters=function(){
   if(typeof hideHistoryCloud==='function')hideHistoryCloud();
   recentKwStore=[];
   if(typeof persistRecentKws==='function')persistRecentKws();
   searchCommitCounts={};
   if(typeof persistSearchCommits==='function')persistSearchCommits();
   else if(typeof lsSet==='function'&&typeof SEARCH_COMMIT_KEY!=='undefined')lsSet(SEARCH_COMMIT_KEY,{});
   sel=[];
   searchKeywords=[];
   activeCat='all';
   document.querySelectorAll('.cat-btn').forEach(function(b){b.classList.toggle('active',b.dataset.cat==='all');});
   document.querySelectorAll('.kw.on,.kw.active').forEach(function(b){if(!b.classList.contains('clear'))b.classList.remove('on','active');});
   if(searchInput)searchInput.value='';
   if(acList){acList.classList.remove('open');acList.innerHTML='';}
   renderPills();
   document.body.classList.remove('search-extras-collapsed','search-chrome-collapsed');if(window.syncSearchHideBtn)window.syncSearchHideBtn();
   clearHighlight();
   var grid=document.querySelector('.catalog-body');
   if(grid)grid.style.display='';
   if(currentMode==='search'){applySearch();render();}
   else render();
   try{
     var acOpen=document.getElementById('acList');
     if(acOpen&&acOpen.classList.contains('open')&&typeof showAc==='function'){
       var cq=(typeof searchInput!=='undefined'&&searchInput)?searchInput.value.trim().toLowerCase():'';
       showAc(cq,{force:true});
     }
   }catch(err){}
 };
 window.exitSearchUi=function(){
   closeSearchExtras();
   if(searchInput)searchInput.blur();
 };
 if(bar){
   bar.addEventListener('click',function(e){
     var btn=e.target.closest('.kw');
     if(!btn||btn.classList.contains('clear'))return;
     var k=(btn.getAttribute('data-kw')||'').trim();
     var on=btn.classList.contains('active')||btn.classList.contains('on');
     e.preventDefault();
     e.stopPropagation();
     if(typeof e.stopImmediatePropagation==='function')e.stopImmediatePropagation();
     if(!k||btn.classList.contains('disabled'))return;
     if(on){if(typeof window.removeSearchKw==='function')window.removeSearchKw(k);else{sel=sel.filter(function(x){return x!==k;});if(typeof render==='function')render();}}
     else if(typeof window.addSearchKw==='function')window.addSearchKw(k);
     else{if(sel.indexOf(k)<0)sel.push(k);if(typeof render==='function')render();}
   },true);
 }
 syncTapToAddBtns();
 syncClearOnMissBtns();
 render();
})();
function shownHits(){
  if(typeof window.currentHits==='function')return window.currentHits();
  return [];
}
function entryIsShown(el){
  if(!el)return false;
  if(el.classList.contains('is-hidden'))return false;
  if(el.style.display==='none')return false;
  if(el.classList.contains('dim'))return false;
  return true;
}
function markSelected(el){
  document.querySelectorAll('.entry.selected').forEach(function(e){if(e!==el)e.classList.remove('selected');});
  document.querySelectorAll('.index li.selected').forEach(function(li){li.classList.remove('selected');});
  if(!el)return;
  el.classList.add('selected');
  var id=el.id;
  if(!id)return;
  var a=document.querySelector('.index a[href="#'+id+'"]');
  if(a&&a.parentElement)a.parentElement.classList.add('selected');
}
function clearSelect(){
  closeChosenPreview({skipJumpExit:true});
  document.querySelectorAll('.entry.selected').forEach(function(e){e.classList.remove('selected');});
  document.querySelectorAll('.index li.selected').forEach(function(li){li.classList.remove('selected');});
}
var lastViewedEntry=null;
var focusReturn='grid';
function setFocusReturn(closeTo, el){
  if(closeTo==='overlay'||closeTo==='grid'||closeTo==='preview'){focusReturn=closeTo;return;}
  if(el&&el.classList.contains('highlight')){focusReturn='overlay';return;}
  if(document.body.classList.contains('chosen-preview-open')&&el&&el.classList.contains('selected')){focusReturn='preview';return;}
  focusReturn='grid';
}
function finishTextFocus(keepClosed){
  if(keepClosed)return;
  var sel=lastViewedEntry||document.querySelector('.entry.selected');
  if(focusReturn==='overlay'){
    if(sel&&!sel.classList.contains('highlight'))openOverlay(sel);
    return;
  }
  if(focusReturn==='preview'&&sel&&!document.body.classList.contains('chosen-preview-open'))openChosenPreview(sel);
}
function rememberViewed(el){
  if(!el)return;
  lastViewedEntry=el;
  markSelected(el);
}
function scrollViewedIntoGrid(el){
  el=el||lastViewedEntry||document.querySelector('.entry.selected');
  if(!el)return;
  rememberViewed(el);
  try{el.scrollIntoView({behavior:'smooth',block:'center',inline:'nearest'});}
  catch(err){try{el.scrollIntoView({block:'center'});}catch(err2){el.scrollIntoView(true);}}
}
function gridCovered(){
  var b=document.body.classList;
  return b.contains('hl-open')||b.contains('chosen-preview-open')||!!document.querySelector('.entry.highlight')||overlayFocusOpen();
}
function revealLastViewed(){
  if(gridCovered())return;
  scrollViewedIntoGrid();
}
function selectEntry(el){
  if(window._searchPopupGuard)return;
  if(!el){clearSelect();lastViewedEntry=null;return;}
  closeChosenPreview({skipJumpExit:true});
  closeOverlay({skipScroll:true});
  rememberViewed(el);
  scrollViewedIntoGrid(el);
}
function unpinSelectedForPreview(){
  if(previewPh&&previewPh.parentNode)previewPh.parentNode.removeChild(previewPh);
  previewPh=null;
}
function pinSelectedForPreview(card){
  if(!card||card.classList.contains('highlight'))return;
  if(previewPh&&previewPh.parentNode&&previewPh.nextSibling===card)return;
  unpinSelectedForPreview();
  if(!overlayHoldsGridSlot(card))return;
  var ph=document.createElement('div');
  ph.className='hl-ph search-sel-ph';
  ph.setAttribute('aria-hidden','true');
  ph.style.width=card.offsetWidth+'px';
  ph.style.minHeight=card.offsetHeight+'px';
  if(card.parentNode)card.parentNode.insertBefore(ph,card);
  previewPh=ph;
}
function openChosenPreview(el){
  if(!el)return;
  if(typeof recordCardHit==='function')recordCardHit(el);
  parkSearchBehindOverlay();
  var fromFullscreen=el.classList.contains('highlight')||document.body.classList.contains('hl-open');
  if(!document.body.classList.contains('chosen-preview-open')){
    jumpOrigin=fromFullscreen?'preview-from-fullscreen':null;
  }
  if(typeof closeCardSearchEmbed==='function'){
    if(el&&window.cardMinMediaOwnerId===el.id){/* keep parked media for this card */}
    else if(window.cardMinMediaOwnerId&&typeof cardMinPauseMedia==='function')cardMinPauseMedia();
    else closeCardSearchEmbed();
  }
  closeOverlay({skipScroll:true});
  rememberViewed(el);
  pinSelectedForPreview(el);
  document.body.classList.add('chosen-preview-open');
  setOverlayFocus('preview');
}
function setOverlayFocus(which){
  if(which==='search'||which==='preview')document.body.setAttribute('data-focus',which);
  else document.body.removeAttribute('data-focus');
}
function closeChosenPreview(opts){
  opts=opts||{};
  var last=lastViewedEntry||document.querySelector('.entry.selected');
  var origin=jumpOrigin;
  var jumpExit=!opts.skipJumpExit&&origin==='search';
  if(!opts.skipJumpExit)jumpOrigin=null;
  var modal=document.getElementById('searchModal');
  if(modal)modal.classList.remove('open');
  document.body.classList.remove('search-modal-open');
  if(!opts.skipDismiss&&typeof cardMinDismissOpen==='function')cardMinDismissOpen();
  var keepMedia=!!opts.keepMedia;
  if(!keepMedia){
    var curEl=document.querySelector('.entry.highlight')||(document.body.classList.contains('chosen-preview-open')?document.querySelector('.entry.selected'):null);
    if(window.cardMinMediaOwnerId&&curEl&&window.cardMinMediaOwnerId!==curEl.id)keepMedia=true;
  }
  if(!keepMedia&&typeof closeCardSearchEmbed==='function')closeCardSearchEmbed();
  document.body.classList.remove('chosen-preview-open');
  setOverlayFocus(null);
  unpinSelectedForPreview();
  collapseOversizedGridPatches();
  if(!opts.skipJumpExit&&origin==='preview-from-fullscreen'&&last){
    openOverlay(last);
    return;
  }
  if(jumpExit){
    if(typeof window.consumeGallerySearchExit==='function')window.consumeGallerySearchExit(last);
    finishGallerySearchExit(last);
    return;
  }
  if(typeof window.rehideSearchNonHits==='function')window.rehideSearchNonHits(last);
  if(typeof reviveEntryCovers==='function')reviveEntryCovers('after-preview');
}
var previewPh=null;
function overlayHoldsGridSlot(el){
  if(!el)return false;
  if(typeof window.searchFiltersOn==='function'&&window.searchFiltersOn()){
    if(typeof window.hasGallerySearchSnap==='function'&&window.hasGallerySearchSnap()&&typeof window.snapContainsEntry==='function')
      return window.snapContainsEntry(el);
    if(typeof window.isSearchHit==='function')return window.isSearchHit(el);
    return false;
  }
  return !el.classList.contains('is-hidden')&&el.style.display!=='none';
}
function placeHighlight(el){
  document.querySelectorAll('.hl-ph').forEach(function(ph){if(ph.parentNode)ph.parentNode.removeChild(ph);});
  document.querySelectorAll('.entry.highlight').forEach(function(e){if(e!==el)e.classList.remove('highlight');});
  if(overlayHoldsGridSlot(el)&&el.parentNode){
    var ph=document.createElement('div');
    ph.className='hl-ph';
    ph.setAttribute('aria-hidden','true');
    ph.style.width=Math.max(0,el.offsetWidth)+'px';
    ph.style.minHeight=Math.max(0,el.offsetHeight)+'px';
    el.parentNode.insertBefore(ph,el);
  }
  el.classList.add('highlight');
}
function openOverlay(el){
  if(!el)return;
  parkSearchBehindOverlay();
  if(!document.body.classList.contains('hl-open')&&typeof window.ensureGallerySearchSnap==='function')window.ensureGallerySearchSnap();
  revealEntryForView(el);
  if(document.body.classList.contains('search-modal-open'))closeSearchModal();
  closeChosenPreview({skipJumpExit:true});
  rememberViewed(el);
  if(el.classList.contains('highlight')){
    var bd=document.getElementById('hlBackdrop');
    if(bd)bd.classList.add('open');
    document.body.classList.add('hl-open');
    syncViewportLock();
    return;
  }
  closeOverlay({skipScroll:true});
  rememberViewed(el);
  placeHighlight(el);
  var backdrop=document.getElementById('hlBackdrop');
  if(backdrop)backdrop.classList.add('open');
  document.body.classList.add('hl-open');
  syncViewportLock();
}
var GRID_PATCH_OVERLAY_MIN=12;
function entryPatchCount(entry){
  if(!entry)return 0;
  var n=parseInt(entry.getAttribute('data-patch-count')||'',10);
  if(!isNaN(n)&&n>=0)return n;
  var d=entry.querySelector('details.patches');
  if(!d){entry.setAttribute('data-patch-count','0');return 0;}
  n=parseInt(d.getAttribute('data-patch-count')||'',10);
  if(isNaN(n)||n<0)n=d.querySelectorAll('li').length;
  entry.setAttribute('data-patch-count',String(n));
  return n;
}
function gridPatchHeightCap(){
  var vh=window.innerHeight||document.documentElement.clientHeight||0;
  var ch=0;
  var chrome=document.getElementById('searchChrome');
  if(chrome){
    var st=window.getComputedStyle(chrome);
    if(document.body.classList.contains('search-mode')||st.position==='sticky'||st.position==='fixed')
      ch=chrome.getBoundingClientRect().height||0;
  }
  var cap=Math.min(Math.max(vh-ch,0),vh*0.9);
  if(!(cap>0))cap=vh*0.85;
  return cap;
}
function patchesOverflowGrid(entry){
  if(!entry||entry.classList.contains('highlight'))return false;
  if(keepPatchesInPlace(entry))return false;
  if(entryPatchCount(entry)>=GRID_PATCH_OVERLAY_MIN)return true;
  var h=entry.getBoundingClientRect().height;
  var vh=window.innerHeight||document.documentElement.clientHeight||0;
  return h>gridPatchHeightCap()||h>vh*0.85;
}
function keepPatchesInPlace(entry){
  if(document.body.classList.contains('search-mode'))return true;
  if(document.body.classList.contains('chosen-preview-open'))return true;
  return false;
}
var patchPromoteLock=null;
function promotePatchesToOverlay(entry, details){
  if(!entry||patchPromoteLock===entry)return;
  if(keepPatchesInPlace(entry))return;
  patchPromoteLock=entry;
  var root=details&&details.classList.contains('patches')?details:entry.querySelector('details.patches');
  if(root)root.open=false;
  selectEntry(entry);
  openOverlay(entry);
  var p=entry.querySelector('details.patches');
  if(p)p.open=true;
  setTimeout(function(){if(patchPromoteLock===entry)patchPromoteLock=null;},0);
}
function collapseOversizedGridPatches(){
  document.querySelectorAll('.entry details.patches[open]').forEach(function(d){
    var e=d.closest('.entry');
    if(!e||e.classList.contains('highlight'))return;
    if(patchesOverflowGrid(e))d.open=false;
  });
}
function closeOverlay(opts){
  opts=opts||{};
  var last=document.querySelector('.entry.highlight')||lastViewedEntry||document.querySelector('.entry.selected');
  var wasOpen=!!(document.body.classList.contains('hl-open')||document.querySelector('.entry.highlight')||document.body.classList.contains('gallery-open')||document.body.classList.contains('img-focus-open'));
  if(typeof window.closeAllNotePops==='function')window.closeAllNotePops();
  closeGallery(true);
  closeDescReader(true);
  closePathReader(true);
  closeImgFocus(true);
  closeDescFocus(true);
  closePathFocus(true);
  if(wasOpen&&!opts.skipScroll&&typeof window.consumeGallerySearchExit==='function')window.consumeGallerySearchExit(last);
  document.querySelectorAll('.hl-ph').forEach(function(ph){if(ph.parentNode)ph.parentNode.removeChild(ph);});
  document.querySelectorAll('.entry.highlight').forEach(function(e){e.classList.remove('highlight');});
  collapseOversizedGridPatches();
  var bd=document.getElementById('hlBackdrop');
  if(bd)bd.classList.remove('open');
  document.body.classList.remove('hl-open');
  syncViewportLock();
  if(last)rememberViewed(last);
  if(wasOpen&&!opts.skipScroll)finishGallerySearchExit(last);
  else{
    window._galleryExitLock=false;
    window._galleryExitHandled=null;
  }
  if(!opts.skipScroll)jumpOrigin=null;
  if(typeof reviveEntryCovers==='function')reviveEntryCovers('after-overlay');
}
function switchOverlayTo(el){
  if(!el)return;
  revealEntryForView(el);
  rememberViewed(el);
  if(el.classList.contains('highlight'))return;
  collapseOversizedGridPatches();
  placeHighlight(el);
  var backdrop=document.getElementById('hlBackdrop');
  if(backdrop)backdrop.classList.add('open');
  document.body.classList.add('hl-open');
  syncViewportLock();
}
function clearHighlight(){closeOverlay();}

var CARD_MIN_MAX=9;
var CARD_MIN_PHONE_MAX=24;
function cardMinCap(){
  if(typeof isPhoneViewport==='function'&&isPhoneViewport())return CARD_MIN_PHONE_MAX;
  return typeof CARD_MIN_MAX==='number'?CARD_MIN_MAX:9;
}
var cardMinDockItems=[];
function cardMinExpanded(){
  var hl=document.querySelector('.entry.highlight');
  if(hl)return hl;
  if(document.body.classList.contains('chosen-preview-open'))return document.querySelector('.entry.selected');
  return null;
}
function cardMinMode(el){
  if(el&&el.classList.contains('highlight'))return 'highlight';
  if(document.body.classList.contains('hl-open'))return 'highlight';
  return 'preview';
}
function cardMinShortName(el){
  var n=(el&&(el.getAttribute('data-name')||((el.querySelector('.lib-name')||{}).textContent||'')))||'Library';
  n=String(n).replace(/\s+/g,' ').trim();
  if(n.length>28)n=n.slice(0,26)+'\u2026';
  return n;
}
function cardMinCoverSrc(el){
  var img=el&&(el.querySelector(':scope > .cover > img')||el.querySelector('.cover > img'));
  if(!img)return '';
  return img.getAttribute('data-cover-src')||img.getAttribute('src')||'';
}
function reviveEntryCovers(phase){
  var revived=0,boxFix=0;
  document.querySelectorAll('.entry .cover').forEach(function(box){
    var img=box.querySelector(':scope > img')||box.querySelector('img');
    if(!img)return;
    var src=img.getAttribute('src')||'';
    var pin=img.getAttribute('data-cover-src')||'';
    if(src&&src!=='about:blank'&&!pin){img.setAttribute('data-cover-src',src);pin=src;}
    if((!src||src==='about:blank'||!(img.complete&&img.naturalWidth>0))&&pin){
      img.src=pin;revived++;
    }
    var br=box.getBoundingClientRect();
    if(br.height<8||box.style.height==='0px'||img.style.height==='0px'||img.style.display==='none'){
      box.style.removeProperty('height');box.style.removeProperty('min-height');box.style.removeProperty('max-height');box.style.removeProperty('display');box.style.removeProperty('flex');
      img.style.removeProperty('height');img.style.removeProperty('width');img.style.removeProperty('display');img.style.removeProperty('max-height');
      img.style.visibility='visible';
      boxFix++;
    }
  });

}
window.reviveEntryCovers=reviveEntryCovers;

function cardMinTinKind(el,mode){
  if(mode==='highlight')return 'highlight';
  if(mode==='preview'||mode==='embed')return 'preview';
  if(el&&el.classList.contains('highlight'))return 'highlight';
  if(document.body.classList.contains('hl-open')&&el&&(el.classList.contains('highlight')||el===document.querySelector('.entry.highlight')))return 'highlight';
  if(document.body.classList.contains('hl-open')&&!document.body.classList.contains('chosen-preview-open'))return 'highlight';
  return 'preview';
}
function cardMinIndex(id,kind){
  kind=kind||'preview';
  for(var i=0;i<cardMinDockItems.length;i++){
    var it=cardMinDockItems[i];
    if(it.id===id&&(it.kind||(it.mode==='highlight'?'highlight':'preview'))===kind)return i;
  }
  return -1;
}
function cardMinDismissOpen(){
  var el=cardMinExpanded();
  if(!el||!el.id)return;
  cardMinClose(el.id,true,cardMinTinKind(el));
}
function cardMinYtCmd(fn){
  var f=document.getElementById('cardSearchFrame');
  if(f&&f.contentWindow){
    try{f.contentWindow.postMessage(JSON.stringify({event:'command',func:fn,args:[]}),'*');}catch(err){}
  }
  var yt=window.cardSearchState&&cardSearchState._ytPlayer;
  if(yt&&typeof yt[fn]==='function'){try{yt[fn]();}catch(err){}}
}
function cardMinMediaPlaying(){
  var f=document.getElementById('cardSearchFrame');
  if(!f)return false;
  var src=f.getAttribute('src')||'';
  if(!src||src==='about:blank')return false;
  if(f.classList.contains('is-hidden'))return false;
  return !!(document.body.classList.contains('card-embed-open')||(window.cardSearchState&&(cardSearchState.ytId||cardSearchState.embedUrl||src)));
}
function cardMinPauseMedia(){cardMinYtCmd('pauseVideo');}
function cardMinPlayMedia(){cardMinYtCmd('playVideo');}
function cardMinParkMedia(id){
  window.cardMinMediaOwnerId=id||'';
  if(!id||!cardMinMediaPlaying())return;
  var slot=document.querySelector('#cardMinDock .card-min-pill[data-card-min-id="'+id+'"][data-card-min-kind="preview"] .card-min-media');
  var host=document.getElementById('cardSearchEmbed');
  if(!slot||!host)return;
  host.hidden=false;
  slot.appendChild(host);
  cardMinPlayMedia();
}
function cardMinRestoreMedia(id){
  var host=document.getElementById('cardSearchEmbed');
  var card=id&&document.getElementById(id);
  if(!host)return;
  if(window.cardMinMediaOwnerId===id&&card){
    host.hidden=false;
    document.body.classList.add('card-embed-open');
    if(host.parentElement!==card)card.appendChild(host);
    cardMinPlayMedia();
  }else{
    cardMinPauseMedia();
  }
}
function cardMinClose(id,fromOpen,kind){
  if(!id)return;
  var i=(kind!=null&&kind!=='')?cardMinIndex(id,kind):cardMinIndex(id,cardMinTinKind(cardMinExpanded()));
  if(i<0&&(kind==null||kind==='')){
    for(var j=0;j<cardMinDockItems.length;j++)if(cardMinDockItems[j].id===id){i=j;break;}
  }
  var closedKind=(i>=0)?(cardMinDockItems[i].kind||(cardMinDockItems[i].mode==='highlight'?'highlight':'preview')):(kind||'preview');
  var wasOwner=window.cardMinMediaOwnerId===id&&closedKind==='preview';
  if(wasOwner){
    var stillPreview=false;
    for(var k=0;k<cardMinDockItems.length;k++){
      if(k===i)continue;
      var it=cardMinDockItems[k];
      if(it.id===id&&(it.kind||(it.mode==='highlight'?'highlight':'preview'))==='preview')stillPreview=true;
    }
    if(!stillPreview){
      window.cardMinMediaOwnerId='';
      if(typeof closeCardSearchEmbed==='function')closeCardSearchEmbed();
    }
  }
  if(i>=0)cardMinDockItems.splice(i,1);
  var cur=cardMinExpanded();
  if(cur&&cur.id===id&&!fromOpen){
    if(document.body.classList.contains('hl-open')||cur.classList.contains('highlight'))closeOverlay({skipScroll:true});
    else if(document.body.classList.contains('chosen-preview-open'))closeChosenPreview({skipJumpExit:true,skipDismiss:true,keepMedia:true});
  }
  cardMinRender();
}
function cardMinEnsureBtn(entry){
  if(!entry)return;
  var end=entry.querySelector('.card-chrome-end');
  if(!end||end.querySelector('.hl-min'))return;
  var b=document.createElement('button');
  b.type='button';
  b.className='hl-min';
  b.setAttribute('aria-label','Minimize');
  b.setAttribute('title','Minimize');
  b.innerHTML='&#x2212;';
  var close=end.querySelector('.hl-close');
  if(close)end.insertBefore(b,close);else end.appendChild(b);
}
function cardMinEnsureAllBtns(){document.querySelectorAll('.entry').forEach(cardMinEnsureBtn);}
function cardMinEnsureDock(){
  var d=document.getElementById('cardMinDock');
  if(d)return d;
  d=document.createElement('div');
  d.id='cardMinDock';
  d.setAttribute('role','toolbar');
  d.setAttribute('aria-label','Minimized library cards');
  document.body.appendChild(d);
  return d;
}
function cardMinRemPx(){
  var n=parseFloat(getComputedStyle(document.documentElement).fontSize||'16');
  return n>0?n:16;
}
function cardMinGapPx(){
  var d=document.getElementById('cardMinDock');
  var row=d&&d.querySelector('.card-min-row');
  var cs=getComputedStyle(row||d||document.body);
  var g=parseFloat(cs.columnGap||cs.gap||'0');
  return g>0?g:Math.round(.45*cardMinRemPx());
}
function cardMinInnerWidth(){
  var d=document.getElementById('cardMinDock');
  var main=document.getElementById('catalogMain');
  var w=0;
  if(d){
    var r=d.getBoundingClientRect();
    var cs=getComputedStyle(d);
    var pl=parseFloat(cs.paddingLeft)||0,pr=parseFloat(cs.paddingRight)||0;
    w=Math.max(0,r.width-pl-pr);
  }
  if(w<40&&main)w=main.getBoundingClientRect().width;
  if(w<40)w=window.innerWidth||360;
  return w;
}
function cardMinRowAvailWidth(){
  var d=document.getElementById('cardMinDock');
  if(d){
    var dr=d.getBoundingClientRect();
    if(dr.width>40)return Math.max(80,dr.width-16);
  }
  var main=document.getElementById('catalogMain');
  if(main){
    var mr=main.getBoundingClientRect();
    if(mr.width>40)return Math.max(80,mr.width-16);
  }
  var vw=window.innerWidth||360;
  return Math.max(80,vw-24);
}
function cardMinSaveReserve(){
  var sav=document.getElementById('cardMinDockSave');
  if(!sav||sav.hidden)return 0;
  var w=72;
  var r=sav.getBoundingClientRect();
  if(r.width>8)w=r.width;
  return 2*(w+Math.round(.45*cardMinRemPx()));
}
function cardMinMaxPerRow(n){
  if(n==null||n==='')n=(typeof cardMinDockItems!=='undefined'&&cardMinDockItems)?cardMinDockItems.length:0;
  n=n|0;
  var rem=cardMinRemPx();
  var gap=cardMinGapPx();
  var saveW=0;
  var sav=document.getElementById('cardMinDockSave');
  if(sav&&!sav.hidden){
    var sr0=sav.getBoundingClientRect();
    saveW=(sr0.width>8?sr0.width:72)+Math.round(.55*rem);
  }
  var inner=Math.max(80,cardMinRowAvailWidth()-saveW);
  function fit(minW){return Math.floor((inner+gap)/Math.max(1,minW+gap));}
  var widthCap=fit(8.75*rem);
  if(widthCap>=5)widthCap=5;
  else if(widthCap>=4)widthCap=4;
  else widthCap=Math.min(3,Math.max(1,fit(4.6*rem)));
  var countCap=n>=7?5:Math.min(3,Math.max(1,n||1));
  var cap=Math.min(widthCap,countCap);
  if(n>0)cap=Math.min(cap,n);
  return Math.max(1,cap);
}
function cardMinPyramidCounts(n,maxPerRow){
  n=n|0;
  maxPerRow=Math.max(1,Math.min(5,maxPerRow|0||5));
  if(n<7&&maxPerRow>3)maxPerRow=3;
  if(n<=0)return [];
  var rows=[],left=n;
  while(left>0){
    var take=Math.min(maxPerRow,left);
    rows.push(take);
    left-=take;
  }
  if(rows.length>=3&&rows[rows.length-1]===1){
    for(var i=rows.length-2;i>=1;i--){
      if(rows[i]-1>=rows[i+1]+1){rows[i]--;rows[rows.length-1]++;break;}
    }
  }
  return rows;
}
function cardMinRectsOverlap(a,b,pad){
  if(!a||!b)return false;
  pad=pad||0;
  return !(a.right<b.left-pad||a.left>b.right+pad||a.bottom<b.top-pad||a.top>b.bottom+pad);
}
function cardMinLayoutRows(){
  var d=document.getElementById('cardMinDock');
  if(!d)return;
  var stack=d.querySelector('.card-min-stack');
  if(!stack)return;
  var pills=Array.prototype.slice.call(stack.querySelectorAll('.card-min-pill'));
  var n=pills.length;
  var rem=cardMinRemPx();
  var gap=cardMinGapPx();
  var saveRes=typeof cardMinSaveReserve==='function'?cardMinSaveReserve():0;
  var per=typeof cardMinMaxPerRow==='function'?cardMinMaxPerRow(n):Math.min(3,Math.max(1,n||1));
  function apply(perNow,pillCap){
    var counts=cardMinPyramidCounts(n,perNow);
    d.setAttribute('data-card-min-per',String(perNow));
    d.style.setProperty('--card-min-per-row',String(perNow));
    pills.forEach(function(p){stack.appendChild(p);});
    Array.prototype.slice.call(stack.querySelectorAll('.card-min-row')).forEach(function(row){
      if(row.parentNode)row.parentNode.removeChild(row);
    });
    var i=0;
    counts.forEach(function(c,ri){
      var row=document.createElement('div');
      row.className='card-min-row';
      row.setAttribute('data-card-min-row',String(ri));
      for(var k=0;k<c&&i<pills.length;k++,i++){
        var pill=pills[i];
        pill.setAttribute('data-card-min-slot',k===0?'left':(k===c-1?'right':'middle'));
        row.appendChild(pill);
      }
      stack.appendChild(row);
    });
    var rowN=Math.max(1,counts[0]||1);
    var inner=Math.max(80,cardMinRowAvailWidth()-saveRes);
    var pillMax=Math.min(pillCap,Math.floor((inner-gap*Math.max(0,rowN-1))/rowN));
    pillMax=Math.max(72,pillMax);
    d.style.setProperty('--card-min-pill-max',pillMax+'px');
    return counts;
  }
  var cap=Math.round(14.5*rem);
  apply(per,cap);
  var sav=document.getElementById('cardMinDockSave');
  var saveW=72;
  if(sav&&!sav.hidden){
    var sbb=sav.getBoundingClientRect();
    if(sbb.width>8)saveW=sbb.width;
  }
  var need=saveW+gap+8;
  function overflowRight(){
    var sr=stack.getBoundingClientRect();
    var vw=window.innerWidth||0;
    return sr.width>8&&sr.right+need>vw;
  }
  if(overflowRight()&&per>4){per=4;apply(per,cap);}
  if(overflowRight()&&per>3){per=3;apply(per,cap);}
  if(overflowRight()){
    var sr=stack.getBoundingClientRect();
    var vw=window.innerWidth||0;
    var room=Math.max(80,vw-need-(sr.left>0?sr.left:8));
    var bottom=stack.querySelector('.card-min-row');
    var rowN=bottom?Math.max(1,bottom.querySelectorAll('.card-min-pill').length):1;
    var shrink=Math.max(72,Math.floor((room-gap*Math.max(0,rowN-1))/rowN));
    apply(per,Math.min(cap,shrink));
  }
}
function cardMinPlaceSave(){
  var d=document.getElementById('cardMinDock');
  var sav=document.getElementById('cardMinDockSave');
  if(!d||!sav)return;
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    sav.style.removeProperty('left');sav.style.removeProperty('right');
    sav.style.removeProperty('bottom');sav.style.removeProperty('top');
    return;
  }
  sav.style.removeProperty('left');
  sav.style.removeProperty('right');
  sav.style.removeProperty('bottom');
  sav.style.removeProperty('top');
  if(sav.hidden){
    d.style.setProperty('--card-min-stack-w','0px');
    return;
  }
  var middle=document.body.classList.contains('display-middle');
  var stack=d.querySelector('.card-min-stack');
  var sr=stack?stack.getBoundingClientRect():null;
  var dr=d.getBoundingClientRect();
  var gap=Math.round(.45*cardMinRemPx());
  var saveW=sav.getBoundingClientRect().width||72;
  var saveH=sav.getBoundingClientRect().height||46;
  d.style.setProperty('--card-min-stack-w',sr&&sr.width>8?Math.round(sr.width)+'px':'0px');
  function chromeRects(){
    var out=[];
    ['catalogJumpStack','searchHistory','filterWrap'].forEach(function(id){
      var el=document.getElementById(id);
      if(!el)return;
      var cs=getComputedStyle(el);
      if(cs.display==='none'||cs.visibility==='hidden')return;
      var r=el.getBoundingClientRect();
      if(r.width>4&&r.height>4)out.push(r);
    });
    return out;
  }
  function hits(){
    var sb=sav.getBoundingClientRect();
    var hit=false;
    Array.prototype.forEach.call(d.querySelectorAll('.card-min-pill'),function(p){
      var r=p.getBoundingClientRect();
      if(r.width<4||r.height<4)return;
      if(cardMinRectsOverlap(sb,r,4))hit=true;
    });
    chromeRects().forEach(function(r){
      if(cardMinRectsOverlap(sb,r,4))hit=true;
    });
    return hit;
  }
  function setLeft(px){
    sav.style.right='auto';
    sav.style.left=Math.round(px)+'px';
  }
  function setRightCss(){
    sav.style.left='auto';
    sav.style.right='.75rem';
  }
  function liftAbove(){
    if(sr&&sr.width>8){
      var gapY=Math.max(gap,6);
      var wantB=sr.top-gapY;
      var cssB=dr.bottom-wantB;
      sav.style.bottom=Math.round(Math.max(0,cssB))+'px';
      var liftLeft=sr.right-saveW-dr.left;
      if(liftLeft<8)liftLeft=8;
      if(liftLeft+saveW>dr.width-8)liftLeft=Math.max(8,dr.width-saveW-8);
      setLeft(liftLeft);
    }else{
      sav.style.bottom=Math.round(saveH+gap)+'px';
    }
  }
  if(sr&&sr.width>8){
    var leftBeside=sr.right+gap-dr.left;
    var fitsRight=leftBeside+saveW<=dr.width-8;
    var leftOf=sr.left-gap-saveW-dr.left;
    var fitsLeft=leftOf>=8;
    if(fitsRight)setLeft(leftBeside);
    else if(fitsLeft)setLeft(leftOf);
    else liftAbove();
  }else setRightCss();
  if(hits())liftAbove();
}
window.cardMinPyramidCounts=cardMinPyramidCounts;
window.cardMinMaxPerRow=cardMinMaxPerRow;
window.cardMinLayoutRows=cardMinLayoutRows;
window.cardMinPlaceSave=cardMinPlaceSave;
function cardMinFitMenusForPins(){
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    var n=(typeof cardMinDockItems!=='undefined'&&cardMinDockItems)?cardMinDockItems.length:0;
    var root=document.documentElement;var body=document.body;
    if(!n){root.style.setProperty('--card-min-dock-h','0px');body.classList.remove('has-card-min-dock');return;}
    body.classList.add('has-card-min-dock');
    var d=document.getElementById('cardMinDock');
    var h=d?Math.ceil(d.getBoundingClientRect().height):0;
    root.style.setProperty('--card-min-dock-h',(h>8?h:52)+'px');
    return;
  }
  if(window._cardMinFitting)return;
  var n=(typeof cardMinDockItems!=='undefined'&&cardMinDockItems)?cardMinDockItems.length:0;
  var root=document.documentElement;
  var body=document.body;
  if(!n){
    root.style.setProperty('--card-min-dock-h','0px');
    body.classList.remove('has-card-min-dock');
    return;
  }
  window._cardMinFitting=1;
  body.classList.add('has-card-min-dock');
  try{
    var rem=cardMinRemPx();
    var gap=cardMinGapPx();
    var pill=Math.round(8.75*rem);
    var minPer=Math.max(1,Math.ceil(n/5));
    var countCap=n>=7?5:Math.min(3,Math.max(1,n));
    var wantPer=Math.max(minPer,Math.min(countCap,n));
    var wantW=wantPer*pill+(Math.max(0,wantPer-1)*gap)+16;
    var middle=body.classList.contains('display-middle');
    var sides=body.classList.contains('display-sides');
    var vw=window.innerWidth||1200;
    var paneGap=parseFloat(getComputedStyle(root).getPropertyValue('--sides-pane-gap'))||6;
    var lw=0,rw=0;
    if(sides&&!middle&&!(typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides())){
      var minL=240,minR=260;
      var o=typeof readSidesCols==='function'?readSidesCols():{lw:0,rw:0};
      lw=o.lw||Math.round(vw*0.22);
      rw=o.rw||Math.round(vw*0.26);
      var searchHid=body.classList.contains('search-chrome-collapsed');
      var kwHid=body.classList.contains('kw-chrome-collapsed');
      function contentW(L,R){return vw-(searchHid?0:L)-(kwHid?0:R)-2*paneGap;}
      var cw=contentW(lw,rw);
      if(cw<wantW){
        var need=wantW-cw;
        var canL=searchHid?0:Math.max(0,lw-minL);
        var canR=kwHid?0:Math.max(0,rw-minR);
        var take=Math.min(need,canL+canR);
        if(take>0){
          var dl=Math.round(take*(canL/(canL+canR||1)));
          var dr=take-dl;
          lw-=dl;rw-=dr;
          if(typeof writeSidesCols==='function')writeSidesCols(lw,rw);
          if(typeof applySidesCols==='function')applySidesCols();
        }
      }
    }
    if(middle&&typeof clampMiddleMh==='function'){
      var d=typeof middleLayoutDefaults==='function'?middleLayoutDefaults():null;
      var rowH=Math.round(2.85*rem)+gap;
      var rows=Math.min(5,Math.max(1,Math.ceil(n/Math.max(1,wantPer))));
      var band=rows*rowH+Math.round(.5*rem);
      if(d){
        var cur=parseInt(getComputedStyle(root).getPropertyValue('--middle-menu-h'),10)||d.menuH;
        var next=clampMiddleMh(cur-band,d);
        if(next<cur&&typeof writeMiddleLayout==='function'){
          writeMiddleLayout(null,next);
          if(typeof applyMiddleLayout==='function')applyMiddleLayout();
        }
      }
    }
    var per=typeof cardMinMaxPerRow==='function'?cardMinMaxPerRow(n):wantPer;
    var rows2=Math.min(5,Math.max(1,Math.ceil(n/Math.max(1,per))));
    var h=rows2*(Math.round(2.85*rem)+gap)+Math.round(.5*rem);
    root.style.setProperty('--card-min-dock-h',h+'px');
  }finally{
    window._cardMinFitting=0;
  }
}
function cardMinPlace(){
  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
  var d=document.getElementById('cardMinDock');
  if(!d)return;
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    d.classList.add('card-min-phone');
    d.style.left='0';d.style.width='100%';d.style.bottom='0';
    if(typeof cardMinFitMenusForPins==='function')cardMinFitMenusForPins();
    var sheet=d.querySelector('.card-min-sheet');
    var sh=sheet?Math.ceil(sheet.getBoundingClientRect().height):Math.ceil(d.getBoundingClientRect().height);
    if(sh>8)document.documentElement.style.setProperty('--card-min-dock-h',sh+'px');
    return;
  }
  if(typeof cardMinFitMenusForPins==='function')cardMinFitMenusForPins();
  var main=document.getElementById('catalogMain');
  var r=main?main.getBoundingClientRect():null;
  if(r&&r.width>40){
    d.style.left=Math.round(r.left)+'px';
    d.style.width=Math.round(r.width)+'px';
    d.style.bottom='0';
  }else{
    d.style.left='0';
    d.style.width='100%';
    d.style.bottom='0';
  }
  if(typeof cardMinLayoutRows==='function')cardMinLayoutRows();
  if(typeof cardMinPlaceSave==='function')cardMinPlaceSave();
  var stack=d.querySelector('.card-min-stack');
  if(stack){
    var sh=Math.ceil(stack.getBoundingClientRect().height+12);
    if(sh>8)document.documentElement.style.setProperty('--card-min-dock-h',sh+'px');
  }
}
function cardMinRender(){
  var d=cardMinEnsureDock();
  var cur=cardMinExpanded();
  var curId=cur&&cur.id;
  d.classList.toggle('is-on',cardMinDockItems.length>0);
  var hold=document.getElementById('cardSearchEmbed');
  var park=document.getElementById('cardSearchPark');
  if(hold&&park&&hold.closest('#cardMinDock')&&hold.parentNode!==park)park.appendChild(hold);
  d.innerHTML='';
  var stack=document.createElement('div');
  stack.className='card-min-stack';
  cardMinDockItems.forEach(function(item,idx){
    var el=document.getElementById(item.id);
    var itemKind=item.kind||(item.mode==='highlight'?'highlight':'preview');
    var curKind=cur?cardMinTinKind(cur):'';
    var playing=window.cardMinMediaOwnerId===item.id&&itemKind==='preview';
    var pill=document.createElement('div');
    pill.className='card-min-pill'+(item.id===curId&&itemKind===curKind?' is-front':'')+(playing?' is-playing':'');
    pill.setAttribute('data-card-min-id',item.id);
    pill.setAttribute('data-card-min-kind',item.kind||(item.mode==='highlight'?'highlight':'preview'));
    pill.setAttribute('data-card-min-slot',idx===0?'left':(idx===cardMinDockItems.length-1&&cardMinDockItems.length>1?'right':'middle'));
    if(cardMinDockItems.length===3)pill.setAttribute('data-card-min-slot',idx===0?'left':(idx===1?'middle':'right'));
    var open=document.createElement('button');
    open.type='button';
    open.className='card-min-open';
    open.setAttribute('aria-pressed',item.id===curId&&itemKind===curKind?'true':'false');
    open.setAttribute('aria-label',(el?cardMinShortName(el):(item.name||'Library'))+(itemKind==='highlight'?' fullscreen':' embed')+' (restore)');
    var src=el?cardMinCoverSrc(el):'';
    if(src){
      var im=document.createElement('img');
      im.alt='';
      im.src=src;
      open.appendChild(im);
    }
    var sp=document.createElement('span');
    sp.className='card-min-name';
    sp.textContent=el?cardMinShortName(el):(item.name||'Library');
    open.appendChild(sp);
    pill.appendChild(open);
    var media=document.createElement('span');
    media.className='card-min-media';
    media.setAttribute('aria-hidden','true');
    pill.appendChild(media);
    var xb=document.createElement('button');
    xb.type='button';
    xb.className='card-min-close';
    xb.setAttribute('aria-label','Close pinned card');
    xb.setAttribute('title','Close');
    xb.innerHTML='\u00d7';
    pill.appendChild(xb);
    stack.appendChild(pill);
  });
  d.appendChild(stack);
  if(window.cardMinMediaOwnerId&&typeof cardMinParkMedia==='function'){
    var host=document.getElementById('cardSearchEmbed');
    var slot=d.querySelector('.card-min-pill[data-card-min-id="'+window.cardMinMediaOwnerId+'"][data-card-min-kind="preview"] .card-min-media');
    if(host&&slot&&!slot.contains(host)&&!cardMinExpanded())slot.appendChild(host);
  }
  var sav=document.createElement('button');
  sav.type='button';
  sav.className='card-min-save';
  sav.id='cardMinDockSave';
  sav.hidden=cardMinDockItems.length===0;
  sav.textContent='Save';
  sav.setAttribute('aria-label','Save pinned session');
  sav.title='Save pinned cards as a named session';
  d.appendChild(sav);
  var pop=document.getElementById('cardMinSavePop');
  if(!pop){
    pop=document.createElement('div');
    pop.id='cardMinSavePop';
    pop.hidden=true;
    pop.innerHTML='<input id="cardMinSaveName" type="text" maxlength="40" placeholder="Session name" autocomplete="off"><button type="button" id="cardMinSaveGo">Save session</button>';
    d.appendChild(pop);
  }else d.appendChild(pop);
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    d.classList.add('card-min-phone');
    var sheetOpen=document.body.classList.contains('card-min-sheet-open');
    d.classList.toggle('is-sheet-open',sheetOpen);
    var sheet=document.createElement('div');sheet.className='card-min-sheet';
    var bar=document.createElement('div');bar.className='card-min-sheet-bar';
    var handle=document.createElement('button');handle.type='button';handle.className='card-min-sheet-handle';handle.id='cardMinSheetHandle';
    handle.setAttribute('aria-expanded',sheetOpen?'true':'false');
    var nPin=cardMinDockItems.length;
    handle.innerHTML='<span class="card-min-sheet-grip" aria-hidden="true"></span><span class="card-min-sheet-label">'+(nPin||0)+' '+(nPin===1?'pin':'pins')+'</span>';
    bar.appendChild(handle);
    if(sav.parentNode)sav.parentNode.removeChild(sav);
    bar.appendChild(sav);
    var list=document.createElement('div');list.className='card-min-list';list.id='cardMinList';
    if(stack.parentNode)stack.parentNode.removeChild(stack);
    while(stack.firstChild)list.appendChild(stack.firstChild);
    sheet.appendChild(bar);sheet.appendChild(list);
    d.insertBefore(sheet,d.firstChild);
    if(pop.parentNode)d.appendChild(pop);
  }else{
    d.classList.remove('card-min-phone','is-sheet-open');
  }
  cardMinPlace();
}
function minimizeExpandedCard(entry){
  entry=entry||cardMinExpanded();
  if(!entry||!entry.id)return;
  var mode=cardMinMode(entry);
  var kind=cardMinTinKind(entry,mode);
  var i=cardMinIndex(entry.id,kind);
  var rec={id:entry.id,mode:mode,kind:kind,name:cardMinShortName(entry)};
  var evicted=null;
  if(i>=0){cardMinDockItems[i].mode=mode;cardMinDockItems[i].kind=kind;cardMinDockItems[i].name=rec.name;}
  else{
    if(cardMinDockItems.length>=(typeof cardMinCap==='function'?cardMinCap():CARD_MIN_MAX)){
      var drop=cardMinDockItems[0];
      evicted=drop&&drop.id||null;
      if(drop)cardMinClose(drop.id,false,drop.kind||(drop.mode==='highlight'?'highlight':'preview'));
    }
    cardMinDockItems.push(rec);
  }
  var keep=typeof cardMinMediaPlaying==='function'&&cardMinMediaPlaying();
  if(window.cardMinMediaOwnerId&&window.cardMinMediaOwnerId!==entry.id&&typeof cardMinPauseMedia==='function')cardMinPauseMedia();
  if(document.body.classList.contains('hl-open')||entry.classList.contains('highlight'))closeOverlay({skipScroll:true});
  else if(document.body.classList.contains('chosen-preview-open'))closeChosenPreview({skipJumpExit:true,skipDismiss:true,keepMedia:keep});
  cardMinRender();
  if(keep&&kind==='preview'&&typeof cardMinParkMedia==='function')cardMinParkMedia(entry.id);
}
function cardMinRestore(id,kind){
  var i=cardMinIndex(id,kind||'preview');
  if(i<0){for(var j=0;j<cardMinDockItems.length;j++)if(cardMinDockItems[j].id===id){i=j;break;}}
  if(i<0)return;
  var item=cardMinDockItems[i];
  var el=document.getElementById(item.id);
  if(!el){cardMinDockItems.splice(i,1);cardMinRender();return;}
  var cur=cardMinExpanded();
  var wantKind=item.kind||(item.mode==='highlight'?'highlight':'preview');
  if(cur){
    var ck=cardMinTinKind(cur);
    if(cur!==el||ck!==wantKind){
      var ci=cardMinIndex(cur.id,ck);
      if(ci>=0){cardMinDockItems[ci].mode=cardMinMode(cur);cardMinDockItems[ci].kind=ck;}
      if(document.body.classList.contains('hl-open')||cur.classList.contains('highlight'))closeOverlay({skipScroll:true});
      else if(document.body.classList.contains('chosen-preview-open'))closeChosenPreview({skipJumpExit:true,skipDismiss:true,keepMedia:true});
    }
  }
  if(wantKind==='highlight'||item.mode==='highlight')openOverlay(el);
  else openChosenPreview(el);
  if(wantKind!=='highlight'&&typeof cardMinRestoreMedia==='function')cardMinRestoreMedia(id);
  cardMinRender();
}
function cardMinActivate(id,kind){
  var cur=cardMinExpanded();
  var ck=cur?cardMinTinKind(cur):'';
  if(cur&&cur.id===id&&ck===(kind||ck)){minimizeExpandedCard(cur);return;}
  cardMinRestore(id,kind);
}
function cardMinTabNext(){
  var n=cardMinDockItems.length;
  if(!n)return;
  var cur=cardMinExpanded();
  var idx=cur?cardMinIndex(cur.id,cardMinTinKind(cur)):-1;
  var next=(idx<0)?0:((idx+1)%n);
  var it=cardMinDockItems[next];
  cardMinRestore(it.id,it.kind||(it.mode==='highlight'?'highlight':'preview'));
}
function cardMinField(t){
  if(!t)return false;
  if(t.isContentEditable)return true;
  var tag=(t.tagName||'').toLowerCase();
  if(tag==='textarea'||tag==='select')return true;
  if(tag==='input'){
    var ty=(t.type||'').toLowerCase();
    if(ty==='button'||ty==='submit'||ty==='checkbox'||ty==='radio'||ty==='range'||ty==='file'||ty==='hidden')return false;
    return true;
  }
  return !!(t.closest&&t.closest('textarea,select,[contenteditable="true"]'));
}
function cardMinShouldTakeTab(t){
  if(!cardMinDockItems.length)return false;
  if(cardMinField(t))return false;
  if(t&&t.closest&&t.closest('#searchInput,#acList,#acShell,.search-ac-shell,#searchChrome,.search-chrome,#filterWrap,#kwbar,.filter-wrap,.note-pop,.note-ta,textarea,select,[contenteditable="true"]'))return false;
  if(t&&t.closest&&t.closest('input')&&cardMinField(t.closest('input')))return false;
  if(cardMinExpanded())return true;
  if(t&&t.closest&&t.closest('#catalogMain,#cardMinDock,.catalog-body'))return true;
  if(!t||t===document.body||t===document.documentElement)return true;
  return false;
}
function cardMinOnOverlayOpen(el){
  if(el)cardMinEnsureBtn(el);
  cardMinRender();
}
window.minimizeExpandedCard=minimizeExpandedCard;
window.cardMinDismissOpen=cardMinDismissOpen;
window.cardMinClose=cardMinClose;
window.cardMinOnOverlayOpen=cardMinOnOverlayOpen;
window.cardMinActivate=cardMinActivate;
window.cardMinTabNext=cardMinTabNext;
(function initCardMinDock(){
  if(window._cardMinDockInit)return;
  window._cardMinDockInit=true;
  function boot(){
    cardMinEnsureAllBtns();
    cardMinEnsureDock();
    cardMinRender();
    var main=document.getElementById('catalogMain');
    if(main){
      main.addEventListener('scroll',cardMinPlace,{passive:true});
      if(window.ResizeObserver)try{new ResizeObserver(cardMinPlace).observe(main);}catch(err){}
    }
    window.addEventListener('resize',cardMinPlace);
    if(window.visualViewport){
      window.visualViewport.addEventListener('resize',cardMinPlace);
      window.visualViewport.addEventListener('scroll',cardMinPlace);
    }
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);
  else boot();
  function pinCovers(){if(typeof reviveEntryCovers==='function')reviveEntryCovers('boot');}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',pinCovers);
  else pinCovers();
  document.addEventListener('keydown',function(e){
    if(e.key!=='Tab'||e.shiftKey||e.altKey||e.ctrlKey||e.metaKey)return;
    if(!cardMinShouldTakeTab(e.target))return;
    e.preventDefault();
    cardMinTabNext();
  },true);
  document.addEventListener('click',function(e){
    if(e.target.closest&&e.target.closest('.preview-back'))cardMinDismissOpen();
  },true);
  var _ch=clearHighlight;
  clearHighlight=function(){cardMinDismissOpen();return _ch.apply(this,arguments);};
  window.clearHighlight=clearHighlight;
  if(typeof openChosenPreview==='function'){
    var _ocp=openChosenPreview;
    openChosenPreview=function(el){var r=_ocp.apply(this,arguments);cardMinOnOverlayOpen(el);return r;};
    window.openChosenPreview=openChosenPreview;
  }
  if(typeof openOverlay==='function'){
    var _oo=openOverlay;
    openOverlay=function(el){var r=_oo.apply(this,arguments);cardMinOnOverlayOpen(el);return r;};
    window.openOverlay=openOverlay;
  }
})();
function isPhoneViewport(){
  try{
    return window.matchMedia('(max-width:899px)').matches
      || window.matchMedia('(hover:none) and (pointer:coarse)').matches;
  }catch(err){return false;}
}
function useMobileFocus(){return !!window.CATALOG_PORTABLE||isPhoneViewport();}
function galleryHits(){
  var list=typeof window.currentHits==='function'?window.currentHits():shownHits();
  return list.filter(function(el){return el.querySelector('.cover img');});
}
var galleryIndex=0;
var imgFocusSwiped=false;
var overlayPinching=false;
var skipSwipeAfterPinch=false;
var skipBannerSwipeClick=false;
var jumpOrigin=null;
var bannerLongPressFired=false;
var bannerLongPressTimer=null;
var bannerLongPressEntry=null;
var bannerLongPressStart=null;
var BANNER_LONGPRESS_MS=450;
var BANNER_LONGPRESS_MOVE=8;
var VIEWPORT_BASE='width=device-width, initial-scale=1, viewport-fit=cover';
var VIEWPORT_LOCKED=VIEWPORT_BASE+', maximum-scale=1, user-scalable=no';
function overlayFocusOpen(){
  var b=document.body.classList;
  return b.contains('gallery-open')||b.contains('img-focus-open')||b.contains('desc-focus-open')||b.contains('desc-reader-open')||b.contains('path-focus-open')||b.contains('path-reader-open');
}
function overlayCoversSearch(){
  var b=document.body.classList;
  if(overlayFocusOpen()||b.contains('hl-open')||b.contains('search-modal-open'))return true;
  if(b.contains('display-sides'))return false;
  return b.contains('chosen-preview-open')||b.contains('card-embed-open')||!!document.querySelector('.entry.highlight');
}
function parkSearchBehindOverlay(){
  if(typeof window.hideSearchAc==='function')window.hideSearchAc();
}
window.overlayCoversSearch=overlayCoversSearch;
window.parkSearchBehindOverlay=parkSearchBehindOverlay;
var overlayScrollY=0;
function overlayStageOpen(){
  var b=document.body.classList;
  return overlayFocusOpen()||b.contains('hl-open')||!!document.querySelector('.entry.highlight');
}
function syncViewportLock(){
  var m=document.getElementById('catalogViewport')||document.querySelector('meta[name="viewport"]');
  var on=overlayStageOpen();
  if(m)m.setAttribute('content',on?VIEWPORT_LOCKED:VIEWPORT_BASE);
  var root=document.documentElement;
  if(on){
    if(!root.classList.contains('overlay-fs')){
      overlayScrollY=window.scrollY||window.pageYOffset||0;
      root.classList.add('overlay-fs');
      document.body.classList.add('overlay-fs');
      document.body.style.top=(-overlayScrollY)+'px';
    }
  }else if(root.classList.contains('overlay-fs')){
    root.classList.remove('overlay-fs');
    document.body.classList.remove('overlay-fs');
    document.body.style.removeProperty('top');
    try{window.scrollTo(0,overlayScrollY);}catch(err){}
  }
}
function touchDist(a,b){
  var dx=b.clientX-a.clientX, dy=b.clientY-a.clientY;
  return Math.sqrt(dx*dx+dy*dy);
}
function focusedBannerImg(){
  if(document.body.classList.contains('gallery-open'))
    return document.querySelector('#imgGallery .gallery-img');
  if(document.body.classList.contains('img-focus-open'))
    return document.querySelector('#imgFocus .img-focus-img');
  return null;
}
function focusedDescText(){
  if(document.body.classList.contains('desc-focus-open'))
    return document.querySelector('#descFocus .desc-focus-text');
  if(document.body.classList.contains('desc-reader-open'))
    return document.querySelector('#descReader .desc-reader-text');
  return null;
}
function fillDescBox(box,el){
  if(!box)return;
  box.innerHTML='';
  if(!el)return;
  var nameEl=el.querySelector('h3.lib-name,h3,.lib-name');
  var descEl=el.querySelector('.summary-panel .desc');
  if(nameEl&&nameEl.textContent){
    var h=document.createElement('h2');
    h.textContent=nameEl.textContent;
    box.appendChild(h);
  }
  var p=document.createElement('p');
  p.textContent=descEl?descEl.textContent:'';
  box.appendChild(p);
}
function fillPathBox(box,el){
  if(!box)return;
  box.innerHTML='';
  if(!el)return;
  var nameEl=el.querySelector('h3.lib-name,h3,.lib-name');
  if(nameEl&&nameEl.textContent){
    var h=document.createElement('h2');
    h.textContent=nameEl.textContent;
    box.appendChild(h);
  }
  var pathEl=el.querySelector('.path');
  var code=pathEl?pathEl.querySelector('code'):null;
  var p=document.createElement('p');
  p.textContent=code?code.textContent:(pathEl?pathEl.textContent.replace(/^\s*(path|open):\s*/i,'').replace(/\s*\[open folder\]\s*$/i,'').replace(/^\s+|\s+$/g,''):'');
  box.appendChild(p);
}
function setOverlayTitle(el){
  var name=el?entryName(el):'';
  document.querySelectorAll('.gallery-title,.img-focus-title').forEach(function(t){
    t.textContent=name;
    t.classList.remove('expanded');
    t.setAttribute('aria-expanded','false');
    t.hidden=!name;
  });
}
function toggleOverlayTitle(t){
  if(!t)return;
  var exp=t.classList.toggle('expanded');
  t.setAttribute('aria-expanded',exp?'true':'false');
}
function showGallerySlide(idx){
  var hits=galleryHits();
  if(!hits.length)return;
  idx=((idx%hits.length)+hits.length)%hits.length;
  galleryIndex=idx;
  var el=hits[idx];
  var srcImg=el.querySelector('.cover img');
  var gimg=document.querySelector('#imgGallery .gallery-img');
  if(gimg&&srcImg){gimg.src=srcImg.src;gimg.alt=srcImg.alt||'';}
  setImgFocusScale(1);
  rememberViewed(el);
  if(document.querySelector('.entry.highlight')||document.body.classList.contains('hl-open')){
    switchOverlayTo(el);
  }
  if(typeof window.syncChromeFavs==='function')window.syncChromeFavs(el);
  setOverlayTitle(el);
}
function openGallery(el){
  var gal=document.getElementById('imgGallery');
  if(!gal||!el)return;
  parkSearchBehindOverlay();
  if(!el.querySelector('.cover img'))return;
  if(!document.body.classList.contains('gallery-open')&&typeof window.ensureGallerySearchSnap==='function')window.ensureGallerySearchSnap();
  var hits=galleryHits();
  var idx=hits.indexOf(el);
  gal.classList.add('open');
  gal.setAttribute('aria-hidden','false');
  document.body.classList.add('gallery-open');
  setImgFocusScale(1);
  syncViewportLock();
  if(idx>=0){
    galleryIndex=idx;
    showGallerySlide(idx);
  }else{
    showBannerEntry(el);
  }
}
function revealEntryForView(el){
  if(!el)return;
  var searchOn=document.body.classList.contains('search-mode');
  var knownHit=false;
  if(typeof window.hasGallerySearchSnap==='function'&&window.hasGallerySearchSnap()&&typeof window.snapContainsEntry==='function')
    knownHit=window.snapContainsEntry(el);
  else if(typeof window.isSearchHit==='function')
    knownHit=window.isSearchHit(el);
  if(searchOn&&!knownHit)return;
  el.classList.remove('is-hidden','dim');
  el.style.display='';
  var group=el.closest('.loc-group');
  if(group){
    group.classList.remove('is-hidden');
    group.hidden=false;
  }
}
function exitBannerToFullscreen(el){
  el=el||lastViewedEntry||document.querySelector('.entry.selected');
  if(!el){revealLastViewed();return;}
  rememberViewed(el);
  revealEntryForView(el);
  if(el.classList.contains('highlight'))return;
  openOverlay(el);
}
function setJumpOrigin(origin){
  if(!jumpOrigin&&origin)jumpOrigin=origin;
}
function finishGallerySearchExit(last){
  last=last||lastViewedEntry||document.querySelector('.entry.selected');
  if(last)rememberViewed(last);
  if(typeof window.shouldRestoreSearchHits==='function'&&window.shouldRestoreSearchHits()){
    if(typeof window.restoreSearchHitsAfterMiss==='function')window.restoreSearchHitsAfterMiss();
    window._galleryExitLock=false;
    window._galleryExitHandled=null;
    return;
  }
  var handled=window._galleryExitHandled;
  var missExit=handled&&handled.miss&&!handled.cleared;
  if(missExit){
    if(typeof window.rehideSearchNonHits==='function')window.rehideSearchNonHits(last);
    if(last)last.classList.remove('selected');
    if(lastViewedEntry===last)lastViewedEntry=null;
  }else if(last){
    scrollViewedIntoGrid(last);
  }
  window._galleryExitLock=false;
  window._galleryExitHandled=null;
}
function exitJumpSession(last){
  var origin=jumpOrigin;
  last=last||lastViewedEntry||document.querySelector('.entry.selected');
  if(origin==='gallery-from-expand'){
    jumpOrigin=null;
    if(last)openChosenPreview(last);
    jumpOrigin='search';
    return;
  }
  jumpOrigin=null;
  if(origin==='search'){
    finishGallerySearchExit(last);
    return;
  }
  if(origin==='fullscreen'||origin==='gallery-from-fullscreen'){
    exitBannerToFullscreen(last);
    return;
  }
  if(document.body.classList.contains('hl-open')||(last&&last.classList.contains('highlight'))){
    exitBannerToFullscreen(last);
    return;
  }
  finishGallerySearchExit(last);
}
function closeGallery(keepClosed){
  var gal=document.getElementById('imgGallery');
  if(!gal||!gal.classList.contains('open'))return;
  var last=lastViewedEntry||document.querySelector('.entry.selected');
  gal.classList.remove('open');
  gal.setAttribute('aria-hidden','true');
  document.body.classList.remove('gallery-open');
  var gimg=document.querySelector('#imgGallery .gallery-img');
  if(gimg){gimg.style.transform='';gimg.removeAttribute('src');gimg.alt='';}
  setOverlayTitle(null);
  imgFocusScale=1;
  syncViewportLock();
  if(last)rememberViewed(last);
  if(keepClosed)return;
  if(typeof window.consumeGallerySearchExit==='function')window.consumeGallerySearchExit(last);
  exitJumpSession(last);
}
function showBannerEntry(el){
  if(!el)return false;
  var srcImg=el.querySelector('.cover img');
  if(!srcImg)return false;
  if(typeof window.ensureGallerySearchSnap==='function')window.ensureGallerySearchSnap();
  rememberViewed(el);
  if(document.body.classList.contains('chosen-preview-open')){
    openChosenPreview(el);
    if(typeof window.syncChromeFavs==='function')window.syncChromeFavs(el);
    return true;
  }
  revealEntryForView(el);
  var hits=galleryHits();
  var i=hits.indexOf(el);
  if(i>=0)galleryIndex=i;
  var keepOverlay=document.body.classList.contains('hl-open')||!!document.querySelector('.entry.highlight')||jumpOrigin==='fullscreen'||jumpOrigin==='gallery-from-fullscreen';
  if(keepOverlay&&!el.classList.contains('highlight'))switchOverlayTo(el);
  if(document.body.classList.contains('gallery-open')){
    var gimg=document.querySelector('#imgGallery .gallery-img');
    if(gimg){gimg.src=srcImg.src;gimg.alt=srcImg.alt||'';}
  }
  if(document.body.classList.contains('img-focus-open')){
    var img=document.querySelector('#imgFocus .img-focus-img');
    if(img){img.src=srcImg.src;img.alt=srcImg.alt||'';}
  }
  setImgFocusScale(1);
  if(typeof window.syncChromeFavs==='function')window.syncChromeFavs(el);
  setOverlayTitle(el);
  return true;
}
function currentBannerEntry(){
  return lastViewedEntry
    || document.querySelector('.entry.highlight')
    || document.querySelector('.entry.selected')
    || galleryHits()[galleryIndex]
    || null;
}
function alphaGalleryHits(){
  if(alphaGalleryHits._list)return alphaGalleryHits._list;
  var seen={},list=[];
  document.querySelectorAll('.index a[href^="#"]').forEach(function(a){
    var id=(a.getAttribute('href')||'').replace(/^#/,'');
    if(!id||id==='top'||seen[id])return;
    var el=document.getElementById(id);
    if(!el||!el.classList.contains('entry')||!el.querySelector('.cover img'))return;
    seen[id]=1;
    list.push(el);
  });
  document.querySelectorAll('.entry').forEach(function(el){
    if(!el.id||seen[el.id]||!el.querySelector('.cover img'))return;
    seen[el.id]=1;
    list.push(el);
  });
  alphaGalleryHits._list=list;
  return list;
}
function bannerList(mode){
  if(mode==='alpha')return alphaGalleryHits();
  return galleryHits();
}
function stepInBannerList(list,dir){
  if(!list||!list.length)return null;
  dir=dir<0?-1:1;
  var cur=currentBannerEntry();
  var i=list.indexOf(cur);
  if(i>=0)return list[((i+dir)%list.length+list.length)%list.length];
  var alpha=alphaGalleryHits();
  var ai=cur?alpha.indexOf(cur):-1;
  if(ai<0)return list[dir>0?0:list.length-1];
  for(var n=1;n<=alpha.length;n++){
    var el=alpha[((ai+n*dir)%alpha.length+alpha.length)%alpha.length];
    if(list.indexOf(el)>=0)return el;
  }
  return list[0];
}
function galleryStep(dir){
  return stepBannerGallery(dir,'hits');
}
function imgFocusStep(dir){
  return stepBannerGallery(dir,'hits');
}
function bannerJumpOpen(){
  var b=document.body.classList;
  return b.contains('gallery-open')||b.contains('img-focus-open')||b.contains('hl-open')||b.contains('chosen-preview-open');
}
function stepBannerGallery(dir, mode){
  if(!bannerJumpOpen())return false;
  if(document.body.classList.contains('chosen-preview-open'))setJumpOrigin('search');
  else if(document.body.classList.contains('hl-open')&&!document.body.classList.contains('gallery-open')&&!document.body.classList.contains('img-focus-open'))setJumpOrigin('fullscreen');
  return showBannerEntry(stepInBannerList(bannerList(mode||'hits'),dir));
}
function bannerAxisPortrait(){
  try{return window.matchMedia('(orientation: portrait)').matches;}
  catch(err){return (window.innerHeight||0)>=(window.innerWidth||0);}
}
function bannerSwipeNav(dx,dy){
  var adx=Math.abs(dx),ady=Math.abs(dy);
  if(adx<40&&ady<40)return null;
  var horiz=adx>=ady;
  if(horiz&&adx<40)return null;
  if(!horiz&&ady<40)return null;
  var dir=horiz?(dx<0?1:-1):(dy<0?1:-1);
  var portrait=bannerAxisPortrait();
  return {dir:dir,mode:portrait?(horiz?'alpha':'hits'):(horiz?'hits':'alpha')};
}
function bannerNavKey(e){
  if(!e||e.altKey||e.ctrlKey||e.metaKey)return false;
  var portrait=bannerAxisPortrait();
  var dir=0,mode=null;
  if(e.key==='ArrowRight'){dir=1;mode=portrait?'alpha':'hits';}
  else if(e.key==='ArrowLeft'){dir=-1;mode=portrait?'alpha':'hits';}
  else if(e.key==='ArrowDown'){dir=1;mode=portrait?'hits':'alpha';}
  else if(e.key==='ArrowUp'){dir=-1;mode=portrait?'hits':'alpha';}
  else return false;
  var t=e.target;
  if(t&&(t.tagName==='TEXTAREA'||t.isContentEditable||(t.tagName==='INPUT'&&t.type!=='range'&&t.type!=='button')))return false;
  if(!stepBannerGallery(dir,mode))return false;
  e.preventDefault();
  return true;
}
function openDescReader(el, closeTo){
  var reader=document.getElementById('descReader');
  if(!reader||!el)return;
  parkSearchBehindOverlay();
  setFocusReturn(closeTo, el);
  fillDescBox(reader.querySelector('.desc-reader-text'),el);
  rememberViewed(el);
  reader.classList.add('open');
  reader.setAttribute('aria-hidden','false');
  document.body.classList.add('desc-reader-open');
  setDescFocusSize(18);
  syncViewportLock();
  var sc=reader.querySelector('.desc-reader-text');
  if(sc)sc.scrollTop=0;
}
function closeDescReader(keepClosed){
  var reader=document.getElementById('descReader');
  if(!reader||!reader.classList.contains('open'))return;
  reader.classList.remove('open');
  reader.setAttribute('aria-hidden','true');
  document.body.classList.remove('desc-reader-open');
  var box=reader.querySelector('.desc-reader-text');
  if(box){box.innerHTML='';box.style.fontSize='';}
  descFocusPx=18;
  syncViewportLock();
  finishTextFocus(keepClosed);
}
var imgFocusScale=1;
function setImgFocusScale(v){
  imgFocusScale=Math.min(3,Math.max(0.5,v));
  var img=focusedBannerImg();
  if(img){
    img.style.transform='scale('+imgFocusScale+')';
    img.style.transformOrigin='center center';
  }
  var sl=document.getElementById('imgFocusScale');
  if(sl)sl.value=String(imgFocusScale);
}
function nudgeImgFocusScale(d){setImgFocusScale(imgFocusScale+(d||0));}
function openImgFocus(el){
  var wrap=document.getElementById('imgFocus');
  if(!wrap||!el)return;
  parkSearchBehindOverlay();
  var srcImg=el.querySelector('.cover img');
  if(!srcImg||!srcImg.getAttribute('src'))return;
  var hits=galleryHits();
  var idx=hits.indexOf(el);
  if(idx>=0)galleryIndex=idx;
  if(!document.body.classList.contains('img-focus-open')&&typeof window.ensureGallerySearchSnap==='function')window.ensureGallerySearchSnap();
  rememberViewed(el);
  var img=wrap.querySelector('.img-focus-img');
  if(img){img.src=srcImg.src;img.alt=srcImg.alt||'';}
  setImgFocusScale(1);
  wrap.classList.add('open');
  document.body.classList.add('img-focus-open');
  syncViewportLock();
  if(typeof window.syncChromeFavs==='function')window.syncChromeFavs(el);
  setOverlayTitle(el);
}
function showImgFocusSlide(idx){
  var hits=galleryHits();
  if(!hits.length)return;
  idx=((idx%hits.length)+hits.length)%hits.length;
  galleryIndex=idx;
  var el=hits[idx];
  var srcImg=el.querySelector('.cover img');
  var img=document.querySelector('#imgFocus .img-focus-img');
  if(img&&srcImg){img.src=srcImg.src;img.alt=srcImg.alt||'';}
  setImgFocusScale(1);
  rememberViewed(el);
  if(document.querySelector('.entry.highlight')||document.body.classList.contains('hl-open')){
    switchOverlayTo(el);
  }
  if(typeof window.syncChromeFavs==='function')window.syncChromeFavs(el);
  setOverlayTitle(el);
}
function closeImgFocus(keepClosed){
  var wrap=document.getElementById('imgFocus');
  if(!wrap||!wrap.classList.contains('open'))return;
  var last=lastViewedEntry||document.querySelector('.entry.selected');
  wrap.classList.remove('open');
  document.body.classList.remove('img-focus-open');
  var img=wrap.querySelector('.img-focus-img');
  if(img){img.style.transform='scale(1)';img.removeAttribute('src');img.alt='';}
  setOverlayTitle(null);
  setImgFocusScale(1);
  syncViewportLock();
  if(last)rememberViewed(last);
  if(keepClosed)return;
  if(typeof window.consumeGallerySearchExit==='function')window.consumeGallerySearchExit(last);
  exitJumpSession(last);
}
var descFocusPx=18;
function setDescFocusSize(px){
  descFocusPx=Math.min(32,Math.max(14,px));
  var t=focusedDescText();
  if(t)t.style.fontSize=descFocusPx+'px';
}
function nudgeDescFocusSize(d){setDescFocusSize(descFocusPx+(d||0));}
function openDescFocus(el, closeTo){
  var wrap=document.getElementById('descFocus');
  if(!wrap||!el)return;
  parkSearchBehindOverlay();
  setFocusReturn(closeTo, el);
  fillDescBox(wrap.querySelector('.desc-focus-text'),el);
  rememberViewed(el);
  wrap.classList.add('open');
  document.body.classList.add('desc-focus-open');
  setDescFocusSize(18);
  syncViewportLock();
  var sc=wrap.querySelector('.desc-focus-text');
  if(sc)sc.scrollTop=0;
}
function closeDescFocus(keepClosed){
  var wrap=document.getElementById('descFocus');
  if(!wrap||!wrap.classList.contains('open'))return;
  wrap.classList.remove('open');
  document.body.classList.remove('desc-focus-open');
  var box=wrap.querySelector('.desc-focus-text');
  if(box){box.innerHTML='';box.style.fontSize='';}
  descFocusPx=18;
  syncViewportLock();
  finishTextFocus(keepClosed);
}
function focusedPathText(){
  if(document.body.classList.contains('path-focus-open'))
    return document.querySelector('#pathFocus .path-focus-text');
  if(document.body.classList.contains('path-reader-open'))
    return document.querySelector('#pathReader .path-reader-text');
  return null;
}
var pathFocusPx=18;
function setPathFocusSize(px){
  pathFocusPx=Math.min(32,Math.max(14,px));
  var t=focusedPathText();
  if(t)t.style.fontSize=pathFocusPx+'px';
}
function nudgePathFocusSize(d){setPathFocusSize(pathFocusPx+(d||0));}
function openPathReader(el, closeTo){
  var reader=document.getElementById('pathReader');
  if(!reader||!el)return;
  parkSearchBehindOverlay();
  setFocusReturn(closeTo, el);
  fillPathBox(reader.querySelector('.path-reader-text'),el);
  rememberViewed(el);
  reader.classList.add('open');
  reader.setAttribute('aria-hidden','false');
  document.body.classList.add('path-reader-open');
  setPathFocusSize(18);
  syncViewportLock();
  var sc=reader.querySelector('.path-reader-text');
  if(sc)sc.scrollTop=0;
}
function closePathReader(keepClosed){
  var reader=document.getElementById('pathReader');
  if(!reader||!reader.classList.contains('open'))return;
  reader.classList.remove('open');
  reader.setAttribute('aria-hidden','true');
  document.body.classList.remove('path-reader-open');
  var box=reader.querySelector('.path-reader-text');
  if(box){box.innerHTML='';box.style.fontSize='';}
  pathFocusPx=18;
  syncViewportLock();
  finishTextFocus(keepClosed);
}
function openPathFocus(el, closeTo){
  var wrap=document.getElementById('pathFocus');
  if(!wrap||!el)return;
  parkSearchBehindOverlay();
  setFocusReturn(closeTo, el);
  fillPathBox(wrap.querySelector('.path-focus-text'),el);
  rememberViewed(el);
  wrap.classList.add('open');
  document.body.classList.add('path-focus-open');
  setPathFocusSize(18);
  syncViewportLock();
  var sc=wrap.querySelector('.path-focus-text');
  if(sc)sc.scrollTop=0;
}
function closePathFocus(keepClosed){
  var wrap=document.getElementById('pathFocus');
  if(!wrap||!wrap.classList.contains('open'))return;
  wrap.classList.remove('open');
  document.body.classList.remove('path-focus-open');
  var box=wrap.querySelector('.path-focus-text');
  if(box){box.innerHTML='';box.style.fontSize='';}
  pathFocusPx=18;
  syncViewportLock();
  finishTextFocus(keepClosed);
}
function activatePath(entry){
  if(!entry)return;
  if(typeof closeSearchModal==='function')closeSearchModal();
  rememberViewed(entry);
  if(entry.classList.contains('highlight')){
    if(useMobileFocus())openPathReader(entry,'overlay');
    else openPathFocus(entry,'overlay');
    return;
  }
  var closeTo=(document.body.classList.contains('chosen-preview-open')&&entry.classList.contains('selected'))?'preview':'grid';
  markSelected(entry);
  rememberViewed(entry);
  if(useMobileFocus())openPathReader(entry,closeTo);
  else openPathFocus(entry,closeTo);
}
function clearBannerLongPress(){
  if(bannerLongPressTimer){clearTimeout(bannerLongPressTimer);bannerLongPressTimer=null;}
  bannerLongPressEntry=null;
  bannerLongPressStart=null;
}
function openBannerGallery(entry){
  if(!entry)return;
  if(typeof closeSearchModal==='function')closeSearchModal();
  if(document.body.classList.contains('chosen-preview-open')||entry.classList.contains('chosen')){
    jumpOrigin='gallery-from-expand';
    document.body.classList.remove('chosen-preview-open');
    setOverlayFocus(null);
    unpinSelectedForPreview();
  }else if(entry.classList.contains('highlight')||document.body.classList.contains('hl-open')){
    jumpOrigin='gallery-from-fullscreen';
  }else{
    setJumpOrigin('search');
  }
  if(useMobileFocus())openGallery(entry);
  else openImgFocus(entry);
}
function activateCover(entry){
  if(!entry)return;
  if(skipBannerSwipeClick){skipBannerSwipeClick=false;return;}
  if(bannerLongPressFired){bannerLongPressFired=false;return;}
  if(typeof closeSearchModal==='function')closeSearchModal();
  if(entry.classList.contains('highlight')||document.body.classList.contains('hl-open')||
     entry.classList.contains('chosen')||document.body.classList.contains('chosen-preview-open')){
    openBannerGallery(entry);
    return;
  }
  openOverlay(entry);
}
function activateDesc(entry){
  if(!entry)return;
  if(typeof closeSearchModal==='function')closeSearchModal();
  rememberViewed(entry);
  if(entry.classList.contains('highlight')){
    if(useMobileFocus())openDescReader(entry,'overlay');
    else openDescFocus(entry,'overlay');
    return;
  }
  var closeTo=(document.body.classList.contains('chosen-preview-open')&&entry.classList.contains('selected'))?'preview':'grid';
  markSelected(entry);
  rememberViewed(entry);
  if(useMobileFocus())openDescReader(entry,closeTo);
  else openDescFocus(entry,closeTo);
}
function syncHighlight(){
  var hits=typeof window.currentHits==='function'?window.currentHits():shownHits();
  var keep=lastViewedEntry;
  var bannerOn=document.body.classList.contains('gallery-open')||document.body.classList.contains('img-focus-open')||document.body.classList.contains('hl-open')||document.body.classList.contains('chosen-preview-open');
  var selEl=document.querySelector('.entry.selected');
  if(selEl&&hits.indexOf(selEl)<0&&selEl!==keep&&!(bannerOn&&(selEl.classList.contains('highlight')||selEl.classList.contains('selected')))){
    selEl.classList.remove('selected');
  }
  var hl=document.querySelector('.entry.highlight');
  if(hl&&hits.indexOf(hl)<0){
    hl.classList.add('is-hidden');
    hl.classList.remove('hit','dim');
    if(!bannerOn){
      hl.classList.remove('highlight');
      hl.style.display='none';
    }
  }
  if(document.body.classList.contains('gallery-open')&&!galleryHits().length)closeGallery(true);
}
window.openOverlay=openOverlay;
window.selectEntry=selectEntry;
window.openChosenPreview=openChosenPreview;
window.closeChosenPreview=closeChosenPreview;
window.setOverlayFocus=setOverlayFocus;
document.addEventListener('pointerdown',function(e){
  if(!document.body.classList.contains('search-modal-open'))return;
  if(e.target.closest&&e.target.closest('.search-modal,#searchModal')){
    if(e.target.id==='searchModal'||e.target.classList.contains('search-modal-backdrop'))return;
    setOverlayFocus('search');
    return;
  }
  if(document.body.classList.contains('chosen-preview-open')&&e.target.closest&&e.target.closest('.entry.selected')&&!e.target.closest('.preview-back')){
    setOverlayFocus('preview');
  }
},true);
document.addEventListener('click',function(e){
  var sum=e.target.closest&&e.target.closest('summary');
  if(!sum)return;
  var details=sum.parentNode;
  if(!details||details.tagName!=='DETAILS'||!details.classList.contains('patches'))return;
  var entry=details.closest('.entry');
  if(!entry||entry.classList.contains('highlight'))return;
  if(details.open)return;
  if(keepPatchesInPlace(entry))return;
  if(entryPatchCount(entry)>=GRID_PATCH_OVERLAY_MIN){
    e.preventDefault();
    e.stopPropagation();
    promotePatchesToOverlay(entry, details);
  }
},true);
document.addEventListener('toggle',function(e){
  var details=e.target;
  if(!details||details.tagName!=='DETAILS'||!details.open)return;
  if(!details.classList.contains('patches')&&!details.classList.contains('grp'))return;
  var entry=details.closest('.entry');
  if(!entry||entry.classList.contains('highlight'))return;
  if(keepPatchesInPlace(entry))return;
  if(patchesOverflowGrid(entry)){
    var root=entry.querySelector('details.patches')||details;
    promotePatchesToOverlay(entry, root);
  }
},true);
document.querySelectorAll('.entry').forEach(function(el){entryPatchCount(el);});
window.clearHighlight=clearHighlight;
window.closeOverlay=closeOverlay;
window.closeGallery=closeGallery;
window.closeDescReader=closeDescReader;
window.closePathReader=closePathReader;
window.closeImgFocus=closeImgFocus;
window.closeDescFocus=closeDescFocus;
window.closePathFocus=closePathFocus;
window.nudgeImgFocusScale=nudgeImgFocusScale;
window.nudgeDescFocusSize=nudgeDescFocusSize;
window.nudgePathFocusSize=nudgePathFocusSize;
window.openSearchModal = function(btn) {
  var card = btn.closest && btn.closest('.entry');
  if(card&&typeof recordCardHit==='function')recordCardHit(card);
  var overlayOn=!!(document.body.classList.contains('hl-open')||(card&&card.classList.contains('highlight')));
  searchModalFromPreview=false;
  if(card){
    markSelected(card);
    rememberViewed(card);
    if(!overlayOn && document.body.classList.contains('chosen-preview-open')){
      searchModalFromPreview=true;
      if(typeof closeCardSearchEmbed==='function')closeCardSearchEmbed();
      document.body.classList.remove('chosen-preview-open');
      setOverlayFocus(null);
      unpinSelectedForPreview();
    }
  }
  var modal = document.getElementById('searchModal');
  document.getElementById('searchModalTitle').textContent = btn.dataset.name || '';
  document.getElementById('searchModalYT').href = btn.dataset.yt || '#';
  document.getElementById('searchModalWeb').href = btn.dataset.web || '#';
  document.getElementById('searchModalImg').href = btn.dataset.img || '#';
  modal.classList.add('open');
  document.body.classList.add('search-modal-open');
  setOverlayFocus('search');
  modal._ytUrl = btn.dataset.yt;
  modal._webUrl = btn.dataset.web;
  modal._imgUrl = btn.dataset.img;
};
window.closeSearchModal = function() {
  var modal=document.getElementById('searchModal');
  if(modal)modal.classList.remove('open');
  document.body.classList.remove('search-modal-open');
  var restore=searchModalFromPreview;
  searchModalFromPreview=false;
  if(restore && !document.body.classList.contains('card-embed-open') && !document.body.classList.contains('hl-open')){
    var card=document.querySelector('.entry.selected')||lastViewedEntry;
    if(card)openChosenPreview(card);
    else setOverlayFocus(null);
    return;
  }
  if(document.body.classList.contains('chosen-preview-open')&&!document.body.classList.contains('hl-open'))
    setOverlayFocus('preview');
  else
    setOverlayFocus(null);
};
window.openPopup = function(link, type) {
  window._searchPopupGuard = true;
  var modal = document.getElementById('searchModal');
  var url = (link && link.href) || '';
  if(!url || url.slice(-1)==='#' ){
    url = '';
    if(modal){
      if(type==='yt') url = modal._ytUrl || '';
      else if(type==='web') url = modal._webUrl || '';
      else if(type==='img') url = modal._imgUrl || '';
    }
  }
  if(!url && typeof cardSearchUrlFor==='function') url = cardSearchUrlFor(type);
  if(!window._cardSearchForcePopup && url && !document.body.classList.contains('hl-open')){
    var card=document.querySelector('.entry.selected')||lastViewedEntry;
    if(card && typeof openChosenPreview==='function' && !document.body.classList.contains('chosen-preview-open')){
      searchModalFromPreview=false;
      openChosenPreview(card);
    }
  }
  if(url && typeof window.shouldEmbedCardSearch==='function' && window.shouldEmbedCardSearch()){
    window._cardSearchForcePopup=false;
    if(typeof openCardSearchEmbed==='function' && openCardSearchEmbed(type,url)){
      searchModalFromPreview=false;
      setTimeout(function(){
        closeSearchModal();
        setTimeout(function(){ window._searchPopupGuard = false; }, 400);
      }, 0);
      return;
    }
  }
  window._cardSearchForcePopup=false;
  var sw = window.screen.availWidth, sh = window.screen.availHeight;
  var w = Math.min(920, Math.round(sw * 0.85));
  var h = Math.min(680, Math.round(sh * 0.82));
  var left = Math.round((sw - w) / 2);
  var top = Math.round((sh - h) / 6);
  var features = 'width='+w+',height='+h+',left='+left+',top='+top+',resizable=yes,scrollbars=yes,toolbar=yes,menubar=no,location=yes';
  if(url){
    var win = window.open(url, 'catalogSearch_'+type, features);
    if (!win) {
      window.open(url, '_blank', 'noopener,noreferrer');
    }
  }
  setTimeout(function(){
    closeSearchModal();
    setTimeout(function(){ window._searchPopupGuard = false; }, 400);
  }, 0);
};
document.addEventListener('click', function(e) {
  if(!window._searchPopupGuard)return;
  e.preventDefault();
  e.stopPropagation();
}, true);
document.addEventListener('pointerdown', function(e) {
  if(!window._searchPopupGuard)return;
  e.preventDefault();
  e.stopPropagation();
}, true);
document.addEventListener('keydown', function(e) {
  if(bannerNavKey(e))return;
  if (e.key !== 'Escape') return;
  var ac=document.getElementById('acList');
  var acOpen=ac&&ac.classList.contains('open');
  var searchUi=e.target.closest&&e.target.closest('#searchInput,#acList,#searchStrip,.search-chrome,.search-col,.search-split,.search-height,.ac-height,.ac-width,.kw-shade-height,.search-ac-shell,.search-autocomplete,.search-active-pills,#filterWrap');
  var modal=document.getElementById('searchModal');
  var modalOpen=modal&&modal.classList.contains('open');
  if(modalOpen){
    closeSearchModal();
    e.preventDefault();
    return;
  }
  if(acOpen){
    if(typeof window.hideSearchAc==='function')window.hideSearchAc();
    else ac.classList.remove('open');
    e.preventDefault();
    return;
  }
  if(document.body.classList.contains('img-focus-open')){
    closeImgFocus();
    e.preventDefault();
    return;
  }
  if(document.body.classList.contains('desc-focus-open')){
    closeDescFocus();
    e.preventDefault();
    return;
  }
  if(document.body.classList.contains('path-focus-open')){
    closePathFocus();
    e.preventDefault();
    return;
  }
  if(document.body.classList.contains('gallery-open')){
    closeGallery();
    e.preventDefault();
    return;
  }
  if(document.body.classList.contains('desc-reader-open')){
    closeDescReader();
    e.preventDefault();
    return;
  }
  if(document.body.classList.contains('path-reader-open')){
    closePathReader();
    e.preventDefault();
    return;
  }
  var notePop=document.querySelector('.note-pop.open');
  if(notePop){
    if(typeof window.closeAllNotePops==='function')window.closeAllNotePops();
    e.preventDefault();
    return;
  }
  if(document.querySelector('.entry.highlight')){
    cardMinDismissOpen();
    closeOverlay();
    e.preventDefault();
    return;
  }
  if(document.body.classList.contains('card-embed-open')){
    closeCardSearchEmbed();
    e.preventDefault();
    return;
  }
  if(document.body.classList.contains('chosen-preview-open')){
    cardMinDismissOpen();
    closeChosenPreview();
    e.preventDefault();
    return;
  }
  if(searchUi){
    if(typeof window.exitSearchUi==='function')window.exitSearchUi();
    if(e.target&&e.target.blur)e.target.blur();
    e.preventDefault();
    return;
  }
  if(document.querySelector('.entry.selected')){
    clearSelect();
    e.preventDefault();
    return;
  }
});
function entryFromHash(){
  var id=(location.hash||'').replace(/^#/,'');
  if(!id||id==='top')return null;
  var el=document.getElementById(id);
  return (el&&el.classList.contains('entry'))?el:null;
}
function highlightFromHash(){
  var el=entryFromHash();
  if(el)selectEntry(el);
}
document.addEventListener('click', function(e) {
  if(document.body.classList.contains('gallery-open')){
    if(e.target.closest('.gallery-back')){closeGallery();e.preventDefault();return;}
    if(e.target.closest('.gallery-fav,.fav-btn,.gallery-zoom,.gallery-title')){e.preventDefault();return;}
    return;
  }
  if(document.body.classList.contains('desc-reader-open')){
    if(e.target.closest('.desc-reader-back')){closeDescReader();e.preventDefault();return;}
    if(e.target.closest('.desc-reader-zoom')){e.preventDefault();return;}
    return;
  }
  if(document.body.classList.contains('path-reader-open')){
    if(e.target.closest('.path-reader-back')){closePathReader();e.preventDefault();return;}
    if(e.target.closest('.path-reader-zoom')){e.preventDefault();return;}
    return;
  }
  if(document.body.classList.contains('img-focus-open')){
    if(e.target.closest('#imgFocusScale,.img-focus-zoom,.img-focus-fav,.fav-btn,.img-focus-title')) return;
    if(imgFocusSwiped){imgFocusSwiped=false;e.preventDefault();return;}
    if(e.target.closest('.img-focus-img')||(e.target.id==='imgFocus')){closeImgFocus();e.preventDefault();return;}
    return;
  }
  if(e.target.closest('#imgFocusScale,.img-focus-zoom,.desc-focus-zoom,.path-focus-zoom')) return;
  if(e.target.closest('#cardMinDock')){
    var x=e.target.closest('.card-min-close');
    if(x){
      var xp=x.closest('.card-min-pill');
      if(xp)cardMinClose(xp.getAttribute('data-card-min-id'),false,xp.getAttribute('data-card-min-kind')||'preview');
      e.preventDefault();e.stopPropagation();return;
    }
    if(e.target.closest('#cardMinSheetHandle,.card-min-sheet-handle')){
      document.body.classList.toggle('card-min-sheet-open');
      var dock=document.getElementById('cardMinDock');
      if(dock)dock.classList.toggle('is-sheet-open',document.body.classList.contains('card-min-sheet-open'));
      var hh=document.getElementById('cardMinSheetHandle');
      if(hh)hh.setAttribute('aria-expanded',document.body.classList.contains('card-min-sheet-open')?'true':'false');
      if(typeof cardMinPlace==='function')cardMinPlace();
      e.preventDefault();e.stopPropagation();return;
    }
    if(e.target.closest('#cardMinDockSave,.card-min-save')){
      e.preventDefault();e.stopPropagation();
      var pop=document.getElementById('cardMinSavePop');
      if(pop){
        pop.hidden=!pop.hidden;
        var inp=document.getElementById('cardMinSaveName');
        if(!pop.hidden&&inp)inp.focus();
      }
      return;
    }
    if(e.target.closest('#cardMinSaveGo')){
      e.preventDefault();e.stopPropagation();
      var inp2=document.getElementById('cardMinSaveName');
      var nm=inp2?inp2.value:'';
      if(typeof savePinSession==='function'&&savePinSession(nm)){
        var p2=document.getElementById('cardMinSavePop');if(p2)p2.hidden=true;
        if(typeof showAc==='function')showAc((searchInput&&searchInput.value||'').trim().toLowerCase(),{force:true});
      }
      return;
    }
    var pill=e.target.closest('.card-min-pill');
    if(pill){cardMinActivate(pill.getAttribute('data-card-min-id'),pill.getAttribute('data-card-min-kind')||'preview');e.preventDefault();e.stopPropagation();return;}
    e.stopPropagation();return;
  }
  if(e.target.closest('.hl-min')){var minE=e.target.closest('.entry');if(minE)minimizeExpandedCard(minE);e.preventDefault();e.stopPropagation();return;}
  if(e.target.closest('.preview-back')){closeChosenPreview();e.preventDefault();e.stopPropagation();return;}
  if(e.target.closest('.hl-close')){closeOverlay();e.preventDefault();return;}
  if(e.target.closest('.fs-btn')){
    var fsEntry=e.target.closest('.entry');
    if(fsEntry)openOverlay(fsEntry);
    e.preventDefault();
    e.stopPropagation();
    return;
  }
  if(window._searchPopupGuard || e.target.closest('#searchModal,.search-modal,.search-modal-link,.search-modal-btns')){
    if(window._searchPopupGuard){e.preventDefault();return;}
    if(e.target.closest('.search-modal-link,.search-modal-btns,.search-modal-close,.search-modal')) return;
  }
  if(document.body.classList.contains('search-modal-open')&&!document.body.classList.contains('hl-open')){
    if(e.target.closest('.search-modal')) return;
    if(!e.target.closest('.entry.selected')){
      closeSearchModal();
      e.preventDefault();
      return;
    }
  }
  if(document.body.classList.contains('chosen-preview-open')&&!document.body.classList.contains('hl-open')){
    if(e.target.closest('#searchModal,.search-modal,.search-modal-link,#cardMinDock,.search-chrome,.search-ac-shell,.search-autocomplete,#acList,#acShell,#historyCloud,.ac-item,.ac-history-cloud')) return;
    if(!e.target.closest('.entry.selected,#cardMinDock')){
      if(document.body.classList.contains('card-embed-open')){closeCardSearchEmbed();e.preventDefault();return;}
      cardMinDismissOpen();
      closeChosenPreview();
      e.preventDefault();
      return;
    }
  }
  var idxLink=e.target.closest&&e.target.closest('.index a[href^="#"]');
  if(idxLink){
    var id=(idxLink.getAttribute('href')||'').replace(/^#/,'');
    var el=id?document.getElementById(id):null;
    if(el&&el.classList.contains('entry'))selectEntry(el);
    return;
  }
  if(e.target.closest('#searchModal,#cardMinDock,.card-min-pill,.card-search-embed,.search-chrome,.search-split,.search-height,.ac-height,.ac-width,.kw-shade-height,.search-ac-shell,.filter-wrap,.search-strip,.search-autocomplete,.search-active-pills,.top,.tap-add-btn,.clear-miss-btn,.layout-edit-btn,#kwbar,.kw,.mode-switch,.cat-switch,.fav-btn,.note-pop,.note-balloon,.preview-back,.hl-min')) return;
  if(!(e.target.closest&&e.target.closest('.note-pop,.note-balloon'))&&typeof window.closeAllNotePops==='function')window.closeAllNotePops();
  var entry=e.target.closest('.entry');
  if(entry){
    if(e.target.closest('a,.hl-close,.hl-min,.preview-back,.kw,input,select,textarea,summary,.patches,.search-popup-btn,.search-link,.fav-btn,.note-balloon,.note-pop,.un-badge,.note-save,.note-cancel,.fs-btn,.card-search-embed,#cardMinDock')) return;
    if(e.target.closest('.cover')){activateCover(entry);return;}
    if(e.target.closest('.summary-panel .desc')){activateDesc(entry);return;}
    if(e.target.closest('.path')){activatePath(entry);return;}
    if(e.target.closest('h3,.lib-name')){openChosenPreview(entry);return;}
    if(entry.classList.contains('highlight'))return;
    if(e.target.closest('button')) return;
    if(document.body.classList.contains('chosen-preview-open')&&entry.classList.contains('selected'))return;
    selectEntry(entry);
    return;
  }
  if(document.querySelector('.entry.highlight'))return;
  if(document.body.classList.contains('chosen-preview-open')){
    if(document.body.classList.contains('card-embed-open')){closeCardSearchEmbed();return;}
    closeChosenPreview();
    return;
  }
  clearSelect();
});
window.addEventListener('hashchange', highlightFromHash);
(function initGalleryPointer(){
  var gal=document.getElementById('imgGallery');
  if(!gal)return;
  var sx=0,sy=0,tracking=false,pinchDist0=0,pinchScale0=1;
  gal.addEventListener('pointerdown',function(e){
    if(e.target.closest('.gallery-back,.gallery-fav,.fav-btn,.gallery-zoom,.gallery-title'))return;
    if(overlayPinching)return;
    tracking=true;
    sx=e.clientX;sy=e.clientY;
    try{gal.setPointerCapture(e.pointerId);}catch(err){}
  });
  gal.addEventListener('pointermove',function(e){
    if(!tracking||overlayPinching)return;
    e.preventDefault();
  });
  gal.addEventListener('pointerup',function(e){
    if(!tracking)return;
    tracking=false;
    if(overlayPinching||skipSwipeAfterPinch){skipSwipeAfterPinch=false;return;}
    var nav=bannerSwipeNav(e.clientX-sx,e.clientY-sy);
    if(!nav)return;
    stepBannerGallery(nav.dir,nav.mode);
  });
  gal.addEventListener('pointercancel',function(){tracking=false;});
  gal.addEventListener('touchstart',function(e){
    if(e.target.closest('.gallery-back,.gallery-fav,.fav-btn,.gallery-zoom,.gallery-title'))return;
    if(e.touches.length>=2){
      overlayPinching=true;
      skipSwipeAfterPinch=true;
      tracking=false;
      pinchDist0=touchDist(e.touches[0],e.touches[1]);
      pinchScale0=imgFocusScale;
      e.preventDefault();
    }
  },{passive:false});
  gal.addEventListener('touchmove',function(e){
    e.preventDefault();
    if(overlayPinching&&e.touches.length>=2&&pinchDist0>0){
      setImgFocusScale(pinchScale0*(touchDist(e.touches[0],e.touches[1])/pinchDist0));
    }
  },{passive:false});
  gal.addEventListener('touchend',function(e){
    if(e.touches.length<2)overlayPinching=false;
  });
  gal.addEventListener('touchcancel',function(){overlayPinching=false;});
})();
(function initBannerLongPress(){
  function coverEntry(t){
    if(!t||!t.closest)return null;
    if(t.closest('.fs-btn,.hl-close,.hl-min,.preview-back,.fav-btn,#cardMinDock'))return null;
    var cover=t.closest('.entry .cover');
    return cover?cover.closest('.entry'):null;
  }
  document.addEventListener('pointerdown',function(e){
    if(document.body.classList.contains('gallery-open')||document.body.classList.contains('img-focus-open'))return;
    var entry=coverEntry(e.target);
    if(!entry)return;
    clearBannerLongPress();
    bannerLongPressFired=false;
    bannerLongPressEntry=entry;
    bannerLongPressStart={x:e.clientX,y:e.clientY};
    bannerLongPressTimer=setTimeout(function(){
      bannerLongPressTimer=null;
      var el=bannerLongPressEntry;
      if(!el)return;
      bannerLongPressFired=true;
      skipBannerSwipeClick=true;
      openBannerGallery(el);
    },BANNER_LONGPRESS_MS);
  },true);
  document.addEventListener('pointermove',function(e){
    if(!bannerLongPressStart)return;
    if(Math.abs(e.clientX-bannerLongPressStart.x)>BANNER_LONGPRESS_MOVE||Math.abs(e.clientY-bannerLongPressStart.y)>BANNER_LONGPRESS_MOVE)clearBannerLongPress();
  },true);
  document.addEventListener('pointerup',clearBannerLongPress,true);
  document.addEventListener('pointercancel',clearBannerLongPress,true);
  document.addEventListener('touchstart',function(e){
    if(document.body.classList.contains('gallery-open')||document.body.classList.contains('img-focus-open'))return;
    if(!e.touches||!e.touches.length)return;
    var entry=coverEntry(e.target);
    if(!entry)return;
    if(bannerLongPressTimer)return;
    clearBannerLongPress();
    bannerLongPressFired=false;
    bannerLongPressEntry=entry;
    bannerLongPressStart={x:e.touches[0].clientX,y:e.touches[0].clientY};
    bannerLongPressTimer=setTimeout(function(){
      bannerLongPressTimer=null;
      var el=bannerLongPressEntry;
      if(!el)return;
      bannerLongPressFired=true;
      skipBannerSwipeClick=true;
      openBannerGallery(el);
    },BANNER_LONGPRESS_MS);
  },{capture:true,passive:true});
  document.addEventListener('touchmove',function(e){
    if(!bannerLongPressStart||!e.touches||!e.touches.length)return;
    if(Math.abs(e.touches[0].clientX-bannerLongPressStart.x)>BANNER_LONGPRESS_MOVE||Math.abs(e.touches[0].clientY-bannerLongPressStart.y)>BANNER_LONGPRESS_MOVE)clearBannerLongPress();
  },{capture:true,passive:true});
  document.addEventListener('touchend',clearBannerLongPress,true);
  document.addEventListener('touchcancel',clearBannerLongPress,true);
  document.addEventListener('contextmenu',function(e){
    if(!(bannerLongPressFired||bannerLongPressTimer||skipBannerSwipeClick))return;
    if(e.target.closest&&e.target.closest('.entry .cover'))e.preventDefault();
  },true);
  document.addEventListener('click',function(e){
    if(!bannerLongPressFired)return;
    bannerLongPressFired=false;
    skipBannerSwipeClick=false;
    e.preventDefault();
    e.stopPropagation();
  },true);
})();
(function initHighlightBannerSwipe(){
  var sx=0,sy=0,tracking=false;
  function jumpCover(t){
    if(!t||!t.closest)return false;
    if(document.body.classList.contains('gallery-open')||document.body.classList.contains('img-focus-open'))return false;
    if(document.body.classList.contains('hl-open')&&t.closest('.entry.highlight .cover'))return true;
    if(document.body.classList.contains('chosen-preview-open')&&t.closest('.entry.selected .cover'))return true;
    return false;
  }
  document.addEventListener('pointerdown',function(e){
    if(!jumpCover(e.target))return;
    tracking=true;
    sx=e.clientX;sy=e.clientY;
  },true);
  document.addEventListener('pointerup',function(e){
    if(!tracking)return;
    tracking=false;
    if(!(document.body.classList.contains('hl-open')||document.body.classList.contains('chosen-preview-open')))return;
    if(document.body.classList.contains('gallery-open')||document.body.classList.contains('img-focus-open'))return;
    var nav=bannerSwipeNav(e.clientX-sx,e.clientY-sy);
    if(!nav)return;
    skipBannerSwipeClick=true;
    e.preventDefault();
    stepBannerGallery(nav.dir,nav.mode);
  },true);
  document.addEventListener('pointercancel',function(){tracking=false;},true);
})();
(function initImgFocusPointer(){
  var wrap=document.getElementById('imgFocus');
  if(!wrap)return;
  var sx=0,sy=0,tracking=false,pinchDist0=0,pinchScale0=1;
  wrap.addEventListener('pointerdown',function(e){
    if(e.target.closest('#imgFocusScale,.img-focus-zoom,.img-focus-fav,.fav-btn,.img-focus-title'))return;
    if(overlayPinching)return;
    tracking=true;imgFocusSwiped=false;
    sx=e.clientX;sy=e.clientY;
    try{wrap.setPointerCapture(e.pointerId);}catch(err){}
  });
  wrap.addEventListener('pointermove',function(e){
    if(!tracking||overlayPinching)return;
    e.preventDefault();
  });
  wrap.addEventListener('pointerup',function(e){
    if(!tracking)return;
    tracking=false;
    if(overlayPinching||skipSwipeAfterPinch){skipSwipeAfterPinch=false;imgFocusSwiped=false;return;}
    var nav=bannerSwipeNav(e.clientX-sx,e.clientY-sy);
    if(!nav)return;
    imgFocusSwiped=true;
    stepBannerGallery(nav.dir,nav.mode);
  });
  wrap.addEventListener('pointercancel',function(){tracking=false;});
  wrap.addEventListener('touchstart',function(e){
    if(e.target.closest('#imgFocusScale,.img-focus-zoom,.img-focus-fav,.fav-btn,.img-focus-title'))return;
    if(e.touches.length>=2){
      overlayPinching=true;
      skipSwipeAfterPinch=true;
      tracking=false;
      pinchDist0=touchDist(e.touches[0],e.touches[1]);
      pinchScale0=imgFocusScale;
      e.preventDefault();
    }
  },{passive:false});
  wrap.addEventListener('touchmove',function(e){
    e.preventDefault();
    if(overlayPinching&&e.touches.length>=2&&pinchDist0>0){
      setImgFocusScale(pinchScale0*(touchDist(e.touches[0],e.touches[1])/pinchDist0));
    }
  },{passive:false});
  wrap.addEventListener('touchend',function(e){
    if(e.touches.length<2)overlayPinching=false;
  });
  wrap.addEventListener('touchcancel',function(){overlayPinching=false;});
})();
function bindDescPinch(root){
  if(!root)return;
  var pinchDist0=0,pinchSize0=18;
  root.addEventListener('touchstart',function(e){
    if(e.target.closest('.desc-reader-back,.desc-reader-zoom,.desc-focus-zoom,.path-reader-back,.path-reader-zoom,.path-focus-zoom'))return;
    if(e.touches.length>=2){
      overlayPinching=true;
      pinchDist0=touchDist(e.touches[0],e.touches[1]);
      pinchSize0=descFocusPx;
      e.preventDefault();
    }
  },{passive:false});
  root.addEventListener('touchmove',function(e){
    if(e.touches.length>=2){
      e.preventDefault();
      if(pinchDist0>0)setDescFocusSize(pinchSize0*(touchDist(e.touches[0],e.touches[1])/pinchDist0));
    }
  },{passive:false});
  root.addEventListener('touchend',function(e){
    if(e.touches.length<2)overlayPinching=false;
  });
  root.addEventListener('touchcancel',function(){overlayPinching=false;});
}
bindDescPinch(document.getElementById('descReader'));
bindDescPinch(document.getElementById('descFocus'));
function bindPathPinch(root){
  if(!root)return;
  var pinchDist0=0,pinchSize0=18;
  root.addEventListener('touchstart',function(e){
    if(e.target.closest('.path-reader-back,.path-reader-zoom,.path-focus-zoom'))return;
    if(e.touches.length>=2){
      overlayPinching=true;
      pinchDist0=touchDist(e.touches[0],e.touches[1]);
      pinchSize0=pathFocusPx;
      e.preventDefault();
    }
  },{passive:false});
  root.addEventListener('touchmove',function(e){
    if(e.touches.length>=2){
      e.preventDefault();
      if(pinchDist0>0)setPathFocusSize(pinchSize0*(touchDist(e.touches[0],e.touches[1])/pinchDist0));
    }
  },{passive:false});
  root.addEventListener('touchend',function(e){
    if(e.touches.length<2)overlayPinching=false;
  });
  root.addEventListener('touchcancel',function(){overlayPinching=false;});
}
bindPathPinch(document.getElementById('pathReader'));
bindPathPinch(document.getElementById('pathFocus'));
document.addEventListener('input',function(e){
  if(e.target&&e.target.id==='imgFocusScale')setImgFocusScale(parseFloat(e.target.value)||1);
});
document.addEventListener('touchmove',function(e){
  var b=document.body.classList;
  // Never lock scrolling inside fullscreen Search suggestions.
  if(b.contains('ac-fs-open')&&e.target&&e.target.closest&&e.target.closest('#acList,.search-autocomplete,.search-ac-shell.ac-fs'))return;
  if(b.contains('gallery-open')||b.contains('img-focus-open')){
    e.preventDefault();
    return;
  }
  if((b.contains('desc-focus-open')||b.contains('desc-reader-open')||b.contains('path-focus-open')||b.contains('path-reader-open'))&&e.touches&&e.touches.length>1){
    e.preventDefault();
  }
},{passive:false});
['gesturestart','gesturechange','gestureend'].forEach(function(ev){
  document.addEventListener(ev,function(e){
    if(overlayFocusOpen())e.preventDefault();
  },{passive:false});
});
document.addEventListener('wheel',function(e){
  var b=document.body.classList;
  if(b.contains('gallery-open')||b.contains('img-focus-open')){
    e.preventDefault();
    if(e.ctrlKey)setImgFocusScale(imgFocusScale+(e.deltaY<0?0.1:-0.1));
    return;
  }
  if((b.contains('path-focus-open')||b.contains('path-reader-open'))&&e.ctrlKey){
    e.preventDefault();
    setPathFocusSize(pathFocusPx+(e.deltaY<0?2:-2));
    return;
  }
  if((b.contains('desc-focus-open')||b.contains('desc-reader-open'))&&e.ctrlKey){
    e.preventDefault();
    setDescFocusSize(descFocusPx+(e.deltaY<0?2:-2));
  }
},{passive:false});

// ===================================================================
// KW Fullscreen + Dual Fullscreen system
// ===================================================================
(function(){
var _ns=window.CATALOG_NS||'catalog';
var _RATIO_KEY='catalog-fullscreen-split-ratio-'+_ns;
var _PIN_KEY='catalog-fullscreen-split-pinned-'+_ns;
var kwFsWanted=false;
var dualRatio=0.5;
var dualPinned=false;

try{
  var _r=parseFloat(localStorage.getItem(_RATIO_KEY));
  if(isFinite(_r)&&_r>=0.1&&_r<=0.9)dualRatio=_r;
  dualPinned=localStorage.getItem(_PIN_KEY)==='1';
}catch(err){}

function saveRatio(r){dualRatio=r;try{localStorage.setItem(_RATIO_KEY,String(r));}catch(err){}}
function savePin(p){dualPinned=p;try{localStorage.setItem(_PIN_KEY,p?'1':'');}catch(err){}}
function isDualFs(){return document.body.classList.contains('dual-fs-open');}
function isAcFs(){return document.body.classList.contains('ac-fs-open');}

function applyDualLayout(){
  var sep=document.getElementById('dualFsSep');
  if(!isDualFs()||(document.body.classList.contains('display-sides')&&!(typeof isPhoneViewport==='function'&&isPhoneViewport()))){
    document.documentElement.style.removeProperty('--dual-fs-lw');
    if(sep&&!document.body.classList.contains('display-sides'))sep.removeAttribute('style');
    syncNarrowPanels();
    return;
  }
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    if(sep)sep.style.display='none';
    syncNarrowPanels();
    return;
  }
  var vw=window.innerWidth||1200;
  var lw=Math.round(vw*dualRatio);
  var sh=document.getElementById('acShell');
  if(sh){var r=sh.getBoundingClientRect();if(r.width>40)lw=Math.round(r.right);}
  document.documentElement.style.setProperty('--dual-fs-lw',lw+'px');
  if(sep){
    var hdr=document.querySelector('.catalog-header');
    var top=hdr?Math.round(hdr.getBoundingClientRect().bottom):0;
    sep.style.cssText='position:fixed;top:'+top+'px;bottom:0;left:'+lw+'px;width:10px;height:auto;z-index:290;margin:0;transform:translateX(-50%);';
  }
  syncNarrowPanels();
}
function syncDualButtons(){
  var dual=isDualFs();
  var kBtn=document.getElementById('kwCompanionBtn');
  var aBtn=document.getElementById('acCompanionBtn');
  if(kBtn){kBtn.setAttribute('aria-pressed',dual?'true':'false');kBtn.title=dual?'Close Keywords':'Keywords side-by-side';}
  if(aBtn){aBtn.setAttribute('aria-pressed',dual?'true':'false');aBtn.title=dual?'Close Search':'Search side-by-side';}
  var showDual=dual?'':'none';
  document.querySelectorAll('.fs-snap-btn').forEach(function(b){b.style.display=showDual;});
  document.querySelectorAll('.fs-pin-btn').forEach(function(b){b.style.display=showDual;});
}
function syncKwFsBtn(){
  var btn=document.getElementById('kwStripFs');
  if(!btn)return;
  btn.setAttribute('aria-pressed',kwFsWanted?'true':'false');
  btn.setAttribute('aria-label',kwFsWanted?'Exit fullscreen Keywords':'Fullscreen Keywords');
  btn.title=kwFsWanted?'Exit fullscreen':'Fullscreen Keywords';
}
function syncSepPin(){
  var sep=document.getElementById('dualFsSep');
  if(sep)sep.classList.toggle('sep-pinned',dualPinned);
  var pin=document.getElementById('dualFsSepPin');
  if(pin)pin.setAttribute('aria-pressed',dualPinned?'true':'false');
}
function updateDualState(){
  if(document.body.classList.contains('kw-fs-open'))kwFsWanted=true;
  var acOn=isAcFs()||(typeof acFsWanted!=='undefined'&&!!acFsWanted);
  var dual=!!(acOn&&(kwFsWanted||document.body.classList.contains('kw-fs-open')));
  document.body.classList.toggle('dual-fs-open',dual);
  applyDualLayout();syncDualButtons();syncSepPin();
}
window.updateDualState=updateDualState;
function setKwFullscreen(on){
  kwFsWanted=!!on;
  var w=document.getElementById('filterWrap');
  if(kwFsWanted){
    document.body.classList.add('kw-fs-open');
    if(w&&!w.classList.contains('open')){
      w.classList.add('open');document.body.classList.add('kw-open');
      var arr=w.querySelector('.toggle-arrow');if(arr)arr.textContent='\u25b2';
      var ft=document.getElementById('filterToggle');if(ft)ft.setAttribute('aria-expanded','true');
    }
  }else{
    document.body.classList.remove('kw-fs-open');
    var panel=document.getElementById('kwFsStripePanel');var trig=document.getElementById('kwStripeTrigger');
    if(panel)panel.classList.remove('stripe-open');
    if(trig){trig.textContent='\u203a';trig.title='Expand controls';}
    if(w)w.classList.remove('toolbar-scroll-collapsed');
  }
  updateDualState();syncKwFsBtn();
  if(typeof placeAcShell==='function')placeAcShell();
}
window.setKwFullscreen=setKwFullscreen;
window.toggleKwFullscreen=function(){setKwFullscreen(!kwFsWanted);};
window.toggleKwFsCompanion=function(){
  if(document.body.classList.contains('display-sides'))return;
  if(!document.body.classList.contains('display-fs'))return;
  setKwFullscreen(!kwFsWanted);

};
window.toggleAcFsCompanion=function(){
  if(document.body.classList.contains('display-sides'))return;
  if(!document.body.classList.contains('display-fs'))return;

  var wantFs=!!(document.body.classList.contains('kw-fs-open')||kwFsWanted);
  if(wantFs&&isAcFs()){
    if(typeof window.setAcFullscreen==='function')window.setAcFullscreen(false);
    return;
  }
  if(typeof currentMode!=='undefined'&&currentMode!=='search'&&typeof window.setMode==='function'){
    window.setMode('search');
  }
  document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed');
  if(typeof syncSearchHideBtn==='function')syncSearchHideBtn();
  var ac=document.getElementById('acList');
  var sh=document.getElementById('acShell');
  if(ac)ac.classList.add('open');
  if(sh)sh.classList.add('open');
  try{if(typeof showAc==='function')showAc(((document.getElementById('searchInput')||{}).value||'').trim().toLowerCase(),{force:true});}catch(err){}
  if(wantFs){
    if(typeof applySearch==='function')try{applySearch();}catch(err){}
    if(ac)ac.classList.add('open');
    if(sh)sh.classList.add('open');
    if(typeof window.setAcFullscreen==='function')window.setAcFullscreen(true);
    var si=document.getElementById('searchInput');
    if(si)try{si.blur();}catch(err){}
  }else{
    if(typeof applySearch==='function')try{applySearch();}catch(err){}
    if(typeof applyAcHeight==='function')applyAcHeight();
    else if(typeof placeAcShell==='function')placeAcShell();
  }
};
window.snapDualFsTo50=function(){
  saveRatio(0.5);if(dualPinned)savePin(false);applyDualLayout();syncSepPin();
  ['acFsStripePanel','kwFsStripePanel'].forEach(function(id){var p=document.getElementById(id);if(p)p.classList.remove('stripe-open');});
  var at=document.getElementById('acStripeTrigger');if(at)at.textContent='\u203a';
  var kt=document.getElementById('kwStripeTrigger');if(kt)kt.textContent='\u203a';
};
window.toggleDualFsPin=function(){
  if(document.body.classList.contains('display-sides')){
    if(typeof toggleModeLock==='function')toggleModeLock();
    return;
  }
  savePin(!dualPinned);
  syncSepPin();
};

// --- ctx-bar toggle (Search FS secondary controls) ---
window.toggleAcCtxBar=function(){
  var portrait=window.matchMedia('(orientation:portrait)').matches;
  var tog=document.getElementById('acCtxToggle');
  if(portrait){
    var open=document.body.classList.toggle('ac-ctx-open');
    if(tog)tog.setAttribute('aria-expanded',open?'true':'false');
  }else{
    var collapsed=document.body.classList.toggle('ac-ctx-collapsed');
    if(tog)tog.setAttribute('aria-expanded',collapsed?'false':'true');
  }
};

// --- Narrow panels in dual-fs portrait ---
function syncNarrowPanels(){
  if(!isDualFs()){document.body.classList.remove('dual-ac-narrow','dual-kw-narrow');return;}
  var vw=window.innerWidth;
  var lw=Math.round(vw*dualRatio);
  var clamp=Math.max(160,Math.round(0.15*vw));
  document.body.classList.toggle('dual-ac-narrow',lw<=clamp+40);
  document.body.classList.toggle('dual-kw-narrow',(vw-lw)<=clamp+40);
}
window.toggleFsStripe=function(which){
  var panelId=which==='ac'?'acFsStripePanel':'kwFsStripePanel';
  var trigId=which==='ac'?'acStripeTrigger':'kwStripeTrigger';
  var panel=document.getElementById(panelId);var trig=document.getElementById(trigId);
  if(!panel)return;
  var open=panel.classList.toggle('stripe-open');
  if(trig){trig.textContent=open?'\u2039':'\u203a';trig.title=open?'Collapse':'Expand controls';}
};
(function bindSepDrag(){
  var sep=document.getElementById('dualFsSep');if(!sep)return;
  var active=false,dragId=null;
  sep.addEventListener('pointerdown',function(e){
    if(dualPinned||!isDualFs())return;
    active=true;dragId=e.pointerId;sep.setPointerCapture(e.pointerId);sep.classList.add('sep-dragging');
    e.preventDefault();e.stopPropagation();
  });
  sep.addEventListener('pointermove',function(e){
    if(!active||e.pointerId!==dragId)return;
    var vw=window.innerWidth;
    var minPx=Math.max(160,Math.round(0.15*vw)),maxPx=Math.min(vw-160,Math.round(0.85*vw));
    var x=Math.max(minPx,Math.min(maxPx,e.clientX));
    dualRatio=x/vw;document.documentElement.style.setProperty('--dual-fs-lw',Math.round(x)+'px');sep.style.left=Math.round(x)+'px';if(typeof syncNarrowPanels==='function')syncNarrowPanels();
  });
  function onUp(e){if(!active||(e&&e.pointerId!=null&&e.pointerId!==dragId))return;active=false;sep.classList.remove('sep-dragging');saveRatio(dualRatio);}
  sep.addEventListener('pointerup',onUp);sep.addEventListener('pointercancel',onUp);sep.addEventListener('lostpointercapture',onUp);
})();
(function bindEdgeSwipe(){
  var EDGE=24,sx=null,sy=null,st=null;
  document.addEventListener('pointerdown',function(e){
    if(e.pointerType==='mouse')return;
    if(!isAcFs()&&!kwFsWanted)return;
    if(isAcFs()&&kwFsWanted)return;
    var vw=window.innerWidth;
    if(e.clientX<=EDGE||e.clientX>=vw-EDGE){sx=e.clientX;sy=e.clientY;st=Date.now();}
  },{passive:true});
  document.addEventListener('pointerup',function(e){
    if(sx===null)return;
    var dx=e.clientX-sx,dy=e.clientY-sy,dt=Date.now()-st;sx=null;
    if(dt>700||Math.abs(dy)>Math.abs(dx)*2||Math.abs(dx)<28)return;
    var vw=window.innerWidth,fromLeft=sx<=EDGE,fromRight=(sx>=vw-EDGE);
    if(fromRight&&isAcFs()&&!kwFsWanted)setKwFullscreen(true);
    else if(fromLeft&&kwFsWanted&&!isAcFs())if(typeof setAcFullscreen==='function')setAcFullscreen(true);
  },{passive:true});
})();
(function patchAcFs(){
  var _orig=window.setAcFullscreen;if(!_orig)return;
  window.setAcFullscreen=function(on){
    var keepKw=(!on)&&(kwFsWanted||document.body.classList.contains('kw-fs-open'));
    var fw=document.getElementById('filterWrap');
    var kwCollapsed=keepKw&&!(document.body.classList.contains('kw-open')||(fw&&fw.classList.contains('open')));
    _orig(on);
    updateDualState();
    syncKwFsBtn();
    if(keepKw){
      setKwFullscreen(true);
    }
    if(typeof placeAcShell==='function')placeAcShell();
  };
  window.toggleAcFullscreen=function(){window.setAcFullscreen(!isAcFs());};
})();
window.addEventListener('resize',applyDualLayout,{passive:true});
if(window.visualViewport)window.visualViewport.addEventListener('resize',applyDualLayout,{passive:true});
syncKwFsBtn();syncDualButtons();syncSepPin();
})();

// === Scroll-collapse toolbar (scroll event on content container) ===
(function bindScrollCollapse(){
  var COLLAPSE_AT=40,RESTORE_AT=10;

  function onAcScroll(){
    var ac=document.getElementById('acList');
    var sh=typeof acShell==='function'?acShell():document.getElementById('acShell');
    if(!ac||!sh)return;
    if(!sh.classList.contains('ac-fs')){sh.classList.remove('toolbar-scroll-collapsed');return;}
    var y=ac.scrollTop;
    if(y>COLLAPSE_AT)sh.classList.add('toolbar-scroll-collapsed');
    else if(y<=RESTORE_AT)sh.classList.remove('toolbar-scroll-collapsed');
  }

  function onKwScroll(){
    var fp=document.getElementById('filterPanel');
    var fw=document.getElementById('filterWrap');
    if(!fp||!fw)return;
    if(!document.body.classList.contains('kw-fs-open')){fw.classList.remove('toolbar-scroll-collapsed');return;}
    var y=fp.scrollTop;
    if(y>COLLAPSE_AT)fw.classList.add('toolbar-scroll-collapsed');
    else if(y<=RESTORE_AT)fw.classList.remove('toolbar-scroll-collapsed');
  }

  var acEl=document.getElementById('acList');
  if(acEl)acEl.addEventListener('scroll',onAcScroll,{passive:true});
  var fpEl=document.getElementById('filterPanel');
  if(fpEl)fpEl.addEventListener('scroll',onKwScroll,{passive:true});
})();

var DISPLAY_KEY='catalog-display-mode-'+(window.CATALOG_NS||'catalog');
var currentDisplay='upper';
var lastNonFsDisplay='upper';

function leaveFullscreenDisplay(){
  setDisplayMode('upper');
}
window.leaveFullscreenDisplay=leaveFullscreenDisplay;
function displayIsDesktop(){return !!(window.matchMedia&&window.matchMedia('(min-width:900px)').matches);}
function catalogDocNoteKey(){return 'catalog-doc-note-open-'+(window.CATALOG_NS||'catalog');}
function collectCatalogIntroParas(){
  var hdr=document.querySelector('.catalog-header');
  var out=[];
  if(!hdr)return out;
  var n=hdr.nextElementSibling;
  while(n&&n.tagName==='P'){out.push(n);n=n.nextElementSibling;}
  return out;
}
function applyCatalogDocNoteOpen(open){
  var el=document.getElementById('catalogDocNote');
  if(!el)return;
  el.classList.toggle('is-collapsed',!open);
  var btn=document.getElementById('catalogDocNoteToggle');
  if(btn){btn.setAttribute('aria-expanded',open?'true':'false');btn.setAttribute('title',open?'Hide document text':'Show document text');}
}
function toggleCatalogDocNote(){
  var el=document.getElementById('catalogDocNote');
  if(!el)return;
  var open=el.classList.contains('is-collapsed');
  applyCatalogDocNoteOpen(open);
  try{localStorage.setItem(catalogDocNoteKey(),open?'1':'0');}catch(err){}
  
}
window.toggleCatalogDocNote=toggleCatalogDocNote;
function ensureCatalogDocNote(){
  var note=document.getElementById('catalogDocNote');
  var paras=collectCatalogIntroParas();
  if(!note){
    if(!paras.length)return null;
    note=document.createElement('aside');
    note.id='catalogDocNote';
    note.className='catalog-doc-note is-collapsed';
    note.innerHTML='<button type="button" class="catalog-doc-note-toggle" id="catalogDocNoteToggle" aria-expanded="false" aria-controls="catalogDocNoteBody" title="Show document text" onclick="event.preventDefault();event.stopPropagation();toggleCatalogDocNote()"><span class="toggle-arrow">&#9660;</span> About / Document</button><div class="catalog-doc-note-body" id="catalogDocNoteBody"></div>';
  }
  var body=document.getElementById('catalogDocNoteBody');
  if(!body){
    body=document.createElement('div');
    body.id='catalogDocNoteBody';
    body.className='catalog-doc-note-body';
    note.appendChild(body);
  }
  paras.forEach(function(p){p.removeAttribute('style');if(p.parentNode!==body)body.appendChild(p);});
  if(!body.childElementCount)return null;
  var saved=null;try{saved=localStorage.getItem(catalogDocNoteKey());}catch(err){}
  applyCatalogDocNoteOpen(saved==='1');
  return note;
}
function parkCatalogDocNote(host){
  var note=ensureCatalogDocNote();
  if(!note)return;
  var w=host||document.getElementById('catalogMain');
  if(!w){
    var cb=document.querySelector('.catalog-body');
    if(cb&&cb.parentNode){if(cb.nextSibling)cb.parentNode.insertBefore(note,cb.nextSibling);else cb.parentNode.appendChild(note);}
    return;
  }
  var top=null;
  try{top=w.querySelector(':scope > a.top');}catch(err){top=null;}
  if(!top)top=w.querySelector('a.top');
  if(note.parentNode!==w||(top&&note.nextElementSibling!==top)||(!top&&w.lastElementChild!==note)){
    if(top)w.insertBefore(note,top);else w.appendChild(note);
  }
  
}
function syncBottomBelowIndex(){
  var ix=document.getElementById('catalogIndex');
  var head=ix&&ix.querySelector('.catalog-index-head');
  var h=head?Math.round(head.getBoundingClientRect().height):0;
  if(h<24)h=44;
  document.documentElement.style.setProperty('--index-bar-h',h+'px');
}
function placeCatalogJumpStack(){
  var stack=document.getElementById('catalogJumpStack');
  var main=document.getElementById('catalogMain');
  if(!stack)return;
  if(!document.body.classList.contains('display-sides')||!main){
    stack.style.cssText='';
  }else{
    var r=main.getBoundingClientRect();
    var right=Math.max(6,Math.round((window.innerWidth||0)-r.right)+10);
    var bottom=Math.max(6,Math.round((window.innerHeight||0)-r.bottom)+12);
    stack.style.right=right+'px';
    stack.style.bottom=bottom+'px';
    stack.style.left='auto';
    stack.style.top='auto';
  }
}
function ensureCatalogMain(){
  var w=document.getElementById('catalogMain');
  if(!w){
    var ix=document.getElementById('catalogIndex');
    var cb=document.querySelector('.catalog-body');
    if(!ix||!cb)return;
    w=document.createElement('div');
    w.id='catalogMain';
    w.className='catalog-main';
    ix.parentNode.insertBefore(w,ix);
    w.appendChild(ix);
    w.appendChild(cb);
    var top=document.querySelector('a.top');
    if(top&&top.parentNode===w.parentNode)w.appendChild(top);
  }
  parkCatalogDocNote(w);
  var bot=document.querySelector('a.bottom');
  if(!bot){
    bot=document.createElement('a');
    bot.className='bottom';
    bot.href='#catalogBottom';
    bot.textContent='\u2193 bottom';
  }
  var topBtn=document.querySelector('a.top');
  var stack=document.getElementById('catalogJumpStack');
  if(!stack){
    stack=document.createElement('div');
    stack.id='catalogJumpStack';
  }
  if(stack.parentNode!==document.body)document.body.appendChild(stack);
  if(topBtn&&topBtn.parentNode!==stack)stack.appendChild(topBtn);
  if(bot.parentNode!==stack)stack.appendChild(bot);
  if(topBtn&&bot.previousElementSibling!==topBtn)stack.insertBefore(topBtn,bot);
  var oldHold=document.getElementById('catalogBottomJump');
  if(oldHold&&oldHold!==stack&&!oldHold.firstElementChild)oldHold.remove();
  if(typeof syncBottomBelowIndex==='function')syncBottomBelowIndex();
  if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();
  if(typeof window.bindMainHoverStripe==='function')window.bindMainHoverStripe();
  else if(typeof window.syncMainHoverStripe==='function')window.syncMainHoverStripe();
  if(typeof reviveEntryCovers==='function')reviveEntryCovers();
  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
  if(typeof bindCatalogTop==='function')bindCatalogTop();
}
var SIDES_KEY='catalog-sides-cols-'+(window.CATALOG_NS||'catalog');
var sidesPinned=false;
try{sidesPinned=localStorage.getItem(SIDES_KEY+'-pin')==='1';}catch(err){}

var MODE_LAYOUT_KEY='catalog-layout-'+(window.CATALOG_NS||'catalog');
function liveLayoutKey(suffix){return suffix+(window.CATALOG_NS||'catalog');}
function displayModeSlot(){
  var m=typeof currentDisplay!=='undefined'?currentDisplay:'upper';
  if(m==='middle')m='sides';
  if(m!=='upper'&&m!=='sides'&&m!=='fs')m='upper';
  return m;
}
function emptyModeLayout(){return {upper:{},sides:{},fs:{}};}
function readModeLayoutStore(){
  try{
    var o=JSON.parse(localStorage.getItem(MODE_LAYOUT_KEY)||'null');
    if(o&&typeof o==='object'&&!Array.isArray(o)){
      return {
        upper:o.upper&&typeof o.upper==='object'?o.upper:{},
        sides:o.sides&&typeof o.sides==='object'?o.sides:{},
        fs:o.fs&&typeof o.fs==='object'?o.fs:{}
      };
    }
  }catch(err){}
  var store=emptyModeLayout();
  try{
    var sc=JSON.parse(localStorage.getItem(SIDES_KEY)||'null');
    if(sc&&sc.lw&&sc.rw){store.sides.lw=sc.lw;store.sides.rw=sc.rw;}
    if(localStorage.getItem(SIDES_KEY+'-pin')==='1')store.sides.pinned=true;
  }catch(err){}
  try{
    var ac=localStorage.getItem(liveLayoutKey('catalog-search-ac-height-'));
    var sh=localStorage.getItem(liveLayoutKey('catalog-keywords-shade-height-'));
    var h=localStorage.getItem(liveLayoutKey('catalog-search-split-h-'));
    var v=localStorage.getItem(liveLayoutKey('catalog-search-split-v-'));
    var ht=localStorage.getItem(liveLayoutKey('catalog-search-height-')+'-l');
    if(ac)store.upper.acH=ac;
    if(sh)store.upper.kwH=sh;
    if(h)store.upper.splitH=h;
    if(v)store.upper.splitV=v;
    if(ht)store.upper.chromeH=ht;
  }catch(err){}
  return store;
}
function writeModeLayoutStore(store){
  try{localStorage.setItem(MODE_LAYOUT_KEY,JSON.stringify(store));}catch(err){}
}
function readModeSlot(mode){
  var s=readModeLayoutStore();
  return s[mode||displayModeSlot()]||{};
}
function writeModeSlot(patch,mode){
  mode=mode||displayModeSlot();
  var s=readModeLayoutStore();
  var cur=s[mode]||{};
  Object.keys(patch||{}).forEach(function(k){cur[k]=patch[k];});
  s[mode]=cur;
  writeModeLayoutStore(s);
  return cur;
}
function modeLayoutPinned(){return false;}
function snapshotLiveToMode(mode){
  mode=mode||displayModeSlot();
  if(mode==='middle')mode='sides';
  var patch={};
  try{
    if(mode==='sides'){
      var lw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0;
      var rw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-rw'),10)||0;
      if(lw)patch.lw=lw;
      if(rw)patch.rw=rw;
      var ih=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-index-h'),10)||0;
      if(!ih){var ixEl=document.getElementById('catalogIndex');if(ixEl&&!ixEl.classList.contains('is-collapsed'))ih=Math.round(ixEl.getBoundingClientRect().height);}
      if(ih>40)patch.indexH=ih;
      var ixSnap=document.getElementById('catalogIndex');
      if(ixSnap){patch.indexEmbed=ixSnap.classList.contains('is-embedded');patch.indexCollapsed=ixSnap.classList.contains('is-collapsed');}
      patch.pinned=!!sidesPinned;
      if(typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle')){
        var mlwS=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-lw'),10)||0;
        var mmhS=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-menu-h'),10)||0;
        if(mlwS>40)patch.middleLw=mlwS;
        if(mmhS>40)patch.middleMh=mmhS;
      }
    }else if(mode==='fs'){
      patch.menu=document.body.classList.contains('kw-fs-open')&&!document.body.classList.contains('ac-fs-open')?'keywords':(document.body.classList.contains('ac-fs-open')&&!document.body.classList.contains('kw-fs-open')?'search':'both');
      var acVar=getComputedStyle(document.documentElement).getPropertyValue('--fs-ac-h').trim();
      var kwVar=getComputedStyle(document.documentElement).getPropertyValue('--fs-kw-h').trim();
      var avail=Math.max(160,(window.innerHeight||800)-56);
      if(acVar&&acVar.indexOf('px')>0)patch.acH=String(parseFloat(acVar)/avail);
      if(kwVar&&kwVar.indexOf('px')>0)patch.kwH=String(parseFloat(kwVar)/avail);
    }else{
      try{patch.chromeH=localStorage.getItem(liveLayoutKey('catalog-search-height-')+'-l')||undefined;}catch(err){}
      try{patch.splitH=localStorage.getItem(liveLayoutKey('catalog-search-split-h-'))||undefined;}catch(err){}
      try{patch.splitV=localStorage.getItem(liveLayoutKey('catalog-search-split-v-'))||undefined;}catch(err){}
      try{patch.acH=localStorage.getItem(liveLayoutKey('catalog-search-ac-height-'))||undefined;}catch(err){}
      try{patch.kwH=localStorage.getItem(liveLayoutKey('catalog-keywords-shade-height-'))||undefined;}catch(err){}
    }
  }catch(err){}
  writeModeSlot(patch,mode);
  return patch;
}
function applyModeSlot(mode){
  mode=mode||displayModeSlot();
  if(mode==='middle')mode='sides';
  var slot=readModeSlot(mode);
  try{
    function setOrClear(key,val){
      if(val==null||val==='')return;
      localStorage.setItem(key,String(val));
    }
    if(mode==='sides'){
      if(slot.lw&&slot.rw)localStorage.setItem(SIDES_KEY,JSON.stringify({lw:slot.lw,rw:slot.rw}));
      try{
        if(slot.middleLw)localStorage.setItem(typeof middleLwKey==='function'?middleLwKey():liveLayoutKey('catalog-middle-lw-'),parseInt(slot.middleLw,10)+'px');
        if(slot.middleMh)localStorage.setItem(typeof middleMhKey==='function'?middleMhKey():liveLayoutKey('catalog-middle-menu-h-'),parseInt(slot.middleMh,10)+'px');
      }catch(eM){}
      if(slot.indexH)document.body.style.setProperty('--sides-index-h',parseInt(slot.indexH,10)+'px');
      var ixSlot=document.getElementById('catalogIndex');
      if(ixSlot){
        if(typeof slot.indexEmbed==='boolean')ixSlot.classList.toggle('is-embedded',!!slot.indexEmbed);
        ixSlot.classList.add('is-collapsed');
        if(typeof syncIndexToggleUi==='function')syncIndexToggleUi(ixSlot);

        if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();
      }
      if(typeof slot.pinned==='boolean'){
        sidesPinned=!!slot.pinned;
        localStorage.setItem(SIDES_KEY+'-pin',sidesPinned?'1':'0');
      }
    }else if(mode==='fs'){

    }else{
      setOrClear(liveLayoutKey('catalog-search-height-')+'-l', slot.chromeH);
      setOrClear(liveLayoutKey('catalog-search-split-h-'), slot.splitH);
      setOrClear(liveLayoutKey('catalog-search-split-v-'), slot.splitV);
      setOrClear(liveLayoutKey('catalog-search-ac-height-'), slot.acH);
      setOrClear(liveLayoutKey('catalog-keywords-shade-height-'), slot.kwH);
    }
  }catch(err){}
  document.body.classList.toggle('mode-layout-pinned',!!slot.pinned||(mode==='sides'&&!!sidesPinned));
  var pin=document.getElementById('modePinBtn');
  if(pin)pin.setAttribute('aria-pressed',(slot.pinned||(mode==='sides'&&sidesPinned))?'true':'false');
}
function applyFsChromeSize(){
  var hdr=document.querySelector('.catalog-header');
  if(hdr)document.documentElement.style.setProperty('--cat-header-h',Math.round(hdr.getBoundingClientRect().bottom)+'px');
  var root=document.documentElement;
  if(!document.body.classList.contains('display-fs')){
    root.style.removeProperty('--fs-ac-h');
    root.style.removeProperty('--fs-kw-h');
    return;
  }
  var slot=readModeSlot('fs');
  var top=hdr?hdr.getBoundingClientRect().bottom:56;
  var avail=Math.max(160,(window.innerHeight||800)-top);
  function px(frac){
    var n=parseFloat(frac);
    if(!isFinite(n))return avail;
    if(n>0&&n<=1)return Math.max(160,Math.min(avail,Math.round(n*avail)));
    return Math.max(160,Math.min(avail,Math.round(n)));
  }
  root.style.setProperty('--fs-ac-h',px(slot.acH||1)+'px');
  root.style.setProperty('--fs-kw-h',px(slot.kwH||1)+'px');
}
function ensureLayoutChromeBtns(){
  var hdr=document.querySelector('.catalog-header');
  var host=document.getElementById('hdrLayoutBtns')||document.getElementById('filterTop');
  if(!host)return;
  var cluster=document.getElementById('hdrCluster');
  if(!cluster&&hdr){
    cluster=document.createElement('div');
    cluster.id='hdrCluster';cluster.className='hdr-cluster';
    var after=hdr.querySelector('h1');
    if(after&&after.nextSibling)hdr.insertBefore(cluster,after.nextSibling);
    else hdr.appendChild(cluster);
  }
  if(cluster&&host&&host.parentElement!==cluster){
    if(cluster.firstChild)cluster.insertBefore(host,cluster.firstChild);else cluster.appendChild(host);
  }
  var wrap=cluster||hdr;
  var end=document.getElementById('hdrEnd');
  if(!end&&wrap){
    end=document.createElement('div');
    end.id='hdrEnd';end.className='hdr-end';
    var menu=document.getElementById('hdrMenuBtns');
    var sw=document.getElementById('displaySwitch');
    var th=document.getElementById('themePicker');
    if(menu){wrap.insertBefore(end,menu);end.appendChild(menu);if(sw)end.appendChild(sw);if(th)end.appendChild(th);}
  }
  var miss=document.getElementById('clearMissBtn');
  if(miss&&wrap){
    var before=end||document.getElementById('hdrMenuBtns');
    if(before){if(miss.parentElement!==wrap||miss.nextElementSibling!==before)wrap.insertBefore(miss,before);}
    else if(miss.parentElement!==wrap)wrap.appendChild(miss);
  }
  var cs=document.getElementById('catSwitch');
  var tap=document.getElementById('tapAddBtnPanel');
  var clrBtn=document.querySelector('#filterPanel .mode-btn.clear-all,.cat-switch .mode-btn.clear-all,.mode-btn.clear-all');
  if(cs&&tap&&clrBtn&&clrBtn.id!=='clearMissBtn'){
    var lead=cs.querySelector('.cat-switch-lead');
    if(!lead){lead=document.createElement('span');lead.className='cat-switch-lead';}
    if(lead.parentElement!==cs||cs.firstElementChild!==lead)cs.insertBefore(lead,cs.firstChild);
    if(tap.parentElement!==lead)lead.appendChild(tap);
    if(clrBtn.parentElement!==lead)lead.appendChild(clrBtn);
    if(tap.nextElementSibling!==clrBtn)lead.insertBefore(tap,clrBtn);
  }
  var edit=document.getElementById('layoutEditBtn');
  if(edit&&edit.parentElement!==host)host.appendChild(edit);
  var pin=document.getElementById('modePinBtn');
  if(pin)pin.hidden=true;
  ['uiScale','layoutPresets'].forEach(function(id){
    var el=document.getElementById(id);
    if(el&&el.parentElement!==host)host.appendChild(el);
  });
  var def=document.getElementById('layoutDefaultBtn');
  if(def)def.hidden=true;
  var strip=document.getElementById('searchStrip');
  var hist=document.getElementById('searchHistoryWrap');
  var clr=strip&&strip.querySelector('.search-strip-clear');
  if(strip&&hist&&clr&&hist.parentElement!==strip){
    if(clr.nextSibling)strip.insertBefore(hist,clr.nextSibling);
    else strip.appendChild(hist);
  }
  var tabs=document.querySelector('.layout-presets-tabs');
  if(tabs&&tabs.getAttribute('data-four-scopes')!=='1'){
    tabs.setAttribute('data-four-scopes','1');
    tabs.innerHTML='';
    LAYOUT_SCOPE_DEFS.forEach(function(d){
      var tb=document.createElement('button');
      tb.type='button';tb.className='layout-presets-tab';
      tb.setAttribute('data-layout-scope',d.id);tb.setAttribute('role','tab');
      tb.textContent=d.label;
      tb.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();setLayoutUiScope(d.id);});
      tabs.appendChild(tb);
    });
  }
  var pop=document.getElementById('layoutPresetsPop');
  if(pop&&!document.getElementById('layoutRestoreDefaults')){
    var rb=document.createElement('button');
    rb.type='button';rb.id='layoutRestoreDefaults';rb.className='layout-restore-defaults';
    rb.textContent='Restore default positions';
    rb.addEventListener('click',function(e){
      e.preventDefault();e.stopPropagation();
      if(typeof resetLayoutDefaults==='function')resetLayoutDefaults(activeLayoutScope());
      if(typeof closeLayoutPop==='function')closeLayoutPop();
    });
    var saveRow=pop.querySelector('.layout-presets-save');
    if(saveRow)pop.insertBefore(rb,saveRow);else pop.appendChild(rb);
  }else{
    var exist=document.getElementById('layoutRestoreDefaults');
    if(exist&&!exist.dataset.scopeBound){
      exist.dataset.scopeBound='1';
      exist.addEventListener('click',function(e){
        e.preventDefault();e.stopPropagation();
        if(typeof resetLayoutDefaults==='function')resetLayoutDefaults(activeLayoutScope());
        if(typeof closeLayoutPop==='function')closeLayoutPop();
      });
    }
  }
  if(typeof syncLayoutEditBtn==='function')syncLayoutEditBtn();
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    if(!document.getElementById('hdrMoreBtn')){
      var cluster=document.getElementById('hdrCluster');
      var sw=document.getElementById('displaySwitch');
      if(cluster&&sw){
        var hb=document.createElement('button');hb.type='button';hb.className='hdr-more-btn';hb.id='hdrMoreBtn';
        hb.setAttribute('aria-expanded','false');hb.innerHTML='&#x22EF;';
        hb.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();toggleHdrMore();});
        var hp=document.createElement('div');hp.className='hdr-more-pop';hp.id='hdrMorePop';hp.hidden=true;
        cluster.insertBefore(hb,sw);cluster.insertBefore(hp,sw);
      }
    }
    if(!document.getElementById('kwStripMore')){
      var fs=document.getElementById('kwStripFs');var top=document.getElementById('filterTop');
      if(fs&&top){
        var kb=document.createElement('button');kb.type='button';kb.className='kw-strip-more';kb.id='kwStripMore';
        kb.setAttribute('aria-expanded','false');kb.innerHTML='&#x22EF;';
        kb.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();toggleKwStripMore();});
        var kp=document.createElement('div');kp.className='kw-strip-more-pop';kp.id='kwStripMorePop';kp.hidden=true;
        top.insertBefore(kb,fs);top.insertBefore(kp,fs);
      }
    }
  }
}
function bindFsModeHandles(){
  function start(e,which){
    if(!document.body.classList.contains('display-fs'))return;
    if(!document.body.classList.contains('layout-edit'))return;
    if(modeLayoutPinned())return;
    if(e.button!=null&&e.button!==0)return;
    e.preventDefault();e.stopPropagation();
    var hdr=document.querySelector('.catalog-header');
    var top=hdr?hdr.getBoundingClientRect().bottom:56;
    var avail=Math.max(160,(window.innerHeight||800)-top);
    var cur=parseInt(getComputedStyle(document.documentElement).getPropertyValue(which==='ac'?'--fs-ac-h':'--fs-kw-h'),10)||avail;
    var drag={which:which,y:e.clientY,h:cur,avail:avail,id:e.pointerId};
    function move(ev){
      if(!drag)return;
      var h=Math.max(160,Math.min(drag.avail,drag.h+(ev.clientY-drag.y)));
      document.documentElement.style.setProperty(drag.which==='ac'?'--fs-ac-h':'--fs-kw-h',h+'px');
    }
    function up(){
      if(!drag)return;
      var h=parseInt(getComputedStyle(document.documentElement).getPropertyValue(drag.which==='ac'?'--fs-ac-h':'--fs-kw-h'),10)||0;
      var patch={};
      if(drag.which==='ac')patch.acH=String(h/drag.avail);
      else patch.kwH=String(h/drag.avail);
      writeModeSlot(patch,'fs');
      drag=null;
      document.removeEventListener('pointermove',move);
      document.removeEventListener('pointerup',up);

    }
    document.addEventListener('pointermove',move);
    document.addEventListener('pointerup',up);
    try{e.currentTarget.setPointerCapture(e.pointerId);}catch(err){}
  }
  var ac=document.getElementById('acHeight');
  var kw=document.getElementById('kwShadeHeight');
  if(ac&&!ac.dataset.fsModeBound){ac.dataset.fsModeBound='1';ac.addEventListener('pointerdown',function(e){if(document.body.classList.contains('display-fs'))start(e,'ac');});}
  if(kw&&!kw.dataset.fsModeBound){kw.dataset.fsModeBound='1';kw.addEventListener('pointerdown',function(e){if(document.body.classList.contains('display-fs'))start(e,'kw');});}
}
window.readModeSlot=readModeSlot;
window.writeModeSlot=writeModeSlot;
window.applyModeSlot=applyModeSlot;
window.snapshotLiveToMode=snapshotLiveToMode;

function syncModeLockBtn(){
  var on=typeof modeLayoutPinned==='function'&&modeLayoutPinned();
  var b=document.getElementById('modePinBtn');
  if(b){
    b.textContent=on?'Unlock':'Lock';
    b.title=on?'Unlock this display mode to resize again':'Lock current sizes for this display mode';
    b.setAttribute('aria-label',b.title);
    b.setAttribute('aria-pressed',on?'true':'false');
  }
  ['dualFsSepPin','fsSepPinBtn'].forEach(function(id){var el=document.getElementById(id);if(el){el.hidden=true;el.setAttribute('aria-hidden','true');}});
}
function toggleModeLock(){
  var on=!modeLayoutPinned();
  if(on&&typeof snapshotLiveToMode==='function')snapshotLiveToMode();
  writeModeSlot({pinned:on});
  if(displayModeSlot()==='sides'){
    sidesPinned=on;
    try{localStorage.setItem(SIDES_KEY+'-pin',on?'1':'0');}catch(err){}
    if(typeof syncSidesPin==='function')syncSidesPin();
  }
  document.body.classList.toggle('mode-layout-pinned',on);
  syncModeLockBtn();
  if(typeof placeSidesHandles==='function')placeSidesHandles();

}
window.syncModeLockBtn=syncModeLockBtn;
window.toggleModeLock=toggleModeLock;

function syncSidesPin(){
  document.body.classList.toggle('sides-pinned',!!sidesPinned);
  var sep=document.getElementById('dualFsSep');
  var pin=document.getElementById('dualFsSepPin');
  if(sep)sep.classList.toggle('sep-pinned',!!sidesPinned);
  if(pin)pin.setAttribute('aria-pressed',sidesPinned?'true':'false');
}
function readSidesCols(){
  try{var o=JSON.parse(localStorage.getItem(SIDES_KEY)||'null');if(o&&o.lw&&o.rw)return o;}catch(err){}
  return {lw:0,rw:0};
}
function writeSidesCols(lw,rw){
  if(sidesPinned)return;
  try{localStorage.setItem(SIDES_KEY,JSON.stringify({lw:lw,rw:rw}));}catch(err){}
  if(typeof writeModeSlot==='function')writeModeSlot({lw:lw,rw:rw},'sides');
  if(typeof snapshotCurrentLayoutBucket==='function')snapshotCurrentLayoutBucket('wide');
}
var lastLayoutBucket=null;
function layoutOrientId(){
  if(typeof displayIsMiddle==='function'?displayIsMiddle():(document.body&&document.body.classList.contains('display-middle')))return 'middle';
  return (typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides())?'portrait':'wide';
}
function layoutBucketId(){
  var o=layoutOrientId();
  if(o==='middle')return 'middle-'+((typeof liveLayoutScopeId==='function')?liveLayoutScopeId():'sck');
  if(o!=='portrait')return 'wide';
  var flip=document.body.classList.contains('sides-portrait-flip')?'B':'A';
  var g=(typeof liveLayoutScopeId==='function')?liveLayoutScopeId():'sck';
  return 'portrait-'+flip+'-'+g;
}
function sidesBuckets(){
  var s=(typeof readModeSlot==='function'?readModeSlot('sides'):{})||{};
  var b=(s.buckets&&typeof s.buckets==='object')?Object.assign({},s.buckets):{};
  if(!b.wide){
    var lw=s.lw,rw=s.rw;
    if(!lw||!rw){
      try{var o=JSON.parse(localStorage.getItem(SIDES_KEY)||'null');if(o&&o.lw&&o.rw){lw=o.lw;rw=o.rw;}}catch(eB){}
    }
    if(lw||rw)b.wide={lw:lw,rw:rw,indexH:s.indexH,indexCollapsed:s.indexCollapsed,indexEmbed:s.indexEmbed};
  }
  return b;
}
function snapshotCurrentLayoutBucket(id){
  id=id||lastLayoutBucket||layoutBucketId();
  if(!id||id==='pending')return;
  var ix=document.getElementById('catalogIndex');
  var searchHid=document.body.classList.contains('search-chrome-collapsed');
  var kwHid=document.body.classList.contains('kw-chrome-collapsed');
  var patch={
    indexCollapsed:!!(ix&&ix.classList.contains('is-collapsed')),
    indexEmbed:!!(ix&&ix.classList.contains('is-embedded'))
  };
  var ih=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-index-h'),10)||0;
  if(ih>40)patch.indexH=ih;
  if(id==='wide'){
    var lw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0;
    var rw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-rw'),10)||0;
    if(!searchHid&&lw>40)patch.lw=lw;
    if(!kwHid&&rw>40)patch.rw=rw;
  }else if(String(id).indexOf('middle-')===0){
    var mlw=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-lw'),10)||0;
    var mmh=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-menu-h'),10)||0;
    if(mlw>40)patch.mlw=mlw;
    if(mmh>40)patch.mmh=mmh;
  }else{
    var plw=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--portrait-lw'),10)||0;
    var pmh=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--portrait-menu-h'),10)||0;
    if(plw>40)patch.plw=plw;
    if(pmh>40)patch.pmh=pmh;
    patch.flip=id.indexOf('-B-')>=0;
  }
  var buckets=sidesBuckets();
  buckets[id]=Object.assign({},buckets[id]||{},patch);
  var out={buckets:buckets};
  if(id==='wide'){
    if(patch.lw)out.lw=patch.lw;
    if(patch.rw)out.rw=patch.rw;
    try{if(patch.lw&&patch.rw)localStorage.setItem(SIDES_KEY,JSON.stringify({lw:patch.lw,rw:patch.rw}));}catch(eW){}
  }else if(String(id).indexOf('middle-')===0){
    if(patch.mlw)out.middleLw=patch.mlw;
    if(patch.mmh)out.middleMh=patch.mmh;
  }
  if(typeof writeModeSlot==='function')writeModeSlot(out,'sides');
}
function applyLayoutBucket(id){
  id=id||layoutBucketId();
  if(!id||id==='pending')return;
  var b=sidesBuckets()[id]||{};
  var ix=document.getElementById('catalogIndex');
  if(id==='wide'){
    if(b.lw)document.body.style.setProperty('--sides-lw',parseInt(b.lw,10)+'px');
    if(b.rw)document.body.style.setProperty('--sides-rw',parseInt(b.rw,10)+'px');
  }else if(String(id).indexOf('middle-')===0){
    if(b.mlw)document.documentElement.style.setProperty('--middle-lw',parseInt(b.mlw,10)+'px');
    if(b.mmh)document.documentElement.style.setProperty('--middle-menu-h',parseInt(b.mmh,10)+'px');
    if(b.mlw){
      var dMid=typeof middleLayoutDefaults==='function'?middleLayoutDefaults():{availW:window.innerWidth||900,minR:148};
      document.documentElement.style.setProperty('--middle-rw',Math.max(dMid.minR||148,(dMid.availW||window.innerWidth)-parseInt(b.mlw,10))+'px');
    }
  }else{
    var d=typeof portraitSidesDefaults==='function'?portraitSidesDefaults():null;
    var lw=b.plw,mh=b.pmh;
    if(d&&typeof clampPortraitTravel==='function'){
      lw=clampPortraitTravel(lw||d.stackW,d.stackW,d.availW);
      mh=clampPortraitTravel(mh||d.searchH,d.searchH,d.availH);
    }
    if(lw)document.documentElement.style.setProperty('--portrait-lw',parseInt(lw,10)+'px');
    if(mh)document.documentElement.style.setProperty('--portrait-menu-h',parseInt(mh,10)+'px');
    if(d&&lw)document.documentElement.style.setProperty('--portrait-rw',Math.max(80,d.availW-parseInt(lw,10))+'px');
  }
  if(b.indexH)document.body.style.setProperty('--sides-index-h',parseInt(b.indexH,10)+'px');
  if(ix){
    ix.classList.add('is-collapsed');if(typeof syncIndexToggleUi==='function')syncIndexToggleUi(ix);
    if(typeof b.indexEmbed==='boolean'){ix.classList.toggle('is-embedded',!!b.indexEmbed);if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();}

  }
}
function syncLayoutBucket(){
  var next=layoutBucketId();
  if(lastLayoutBucket&&lastLayoutBucket!=='pending'&&lastLayoutBucket!==next)snapshotCurrentLayoutBucket(lastLayoutBucket);
  if(lastLayoutBucket!==next)applyLayoutBucket(next);
  lastLayoutBucket=next;
}
window.layoutOrientId=layoutOrientId;
window.layoutBucketId=layoutBucketId;
window.snapshotCurrentLayoutBucket=snapshotCurrentLayoutBucket;
window.syncLayoutBucket=syncLayoutBucket;

// fix-PORTRAIT-SEP: portrait A/B helpers (drag lives in bindSidesDrag; Customize + ±30% clamp)
(function(){
  var PORTRAIT_TRAVEL=0.30;
  var PORTRAIT_STACK_FRAC=0.38;
  var PORTRAIT_SEARCH_FRAC=0.50;
  function isPortraitDesktopSides(){return !!(window.matchMedia&&window.matchMedia('(min-width:900px)').matches&&window.matchMedia('(orientation:portrait)').matches);}
  function portraitFlipKey(){return 'catalog-sides-portrait-flip-'+(window.CATALOG_NS||'catalog');}
  function portraitFlipScope(){return (typeof liveLayoutScopeId==='function')?liveLayoutScopeId():'sck';}
  function readPortraitFlipMap(){
    try{
      var raw=localStorage.getItem(portraitFlipKey());
      if(!raw)return {};
      if(raw==='1'||raw==='0'){var on=raw==='1';return {sck:on,sc:on,ck:on,c:on};}
      var o=JSON.parse(raw);
      return (o&&typeof o==='object'&&!Array.isArray(o))?o:{};
    }catch(err){return {};}
  }
  function portraitFlipOn(scope){
    try{
      var raw=localStorage.getItem(portraitFlipKey());
      if(!raw)return false;
      if(raw==='1'||raw==='0')return raw==='1';
      var o=JSON.parse(raw);
      if(o&&typeof o==='object'&&!Array.isArray(o))return !!o[scope||portraitFlipScope()];
    }catch(err){}
    return false;
  }
  function writePortraitFlip(on){
    try{localStorage.setItem(portraitFlipKey(),on?'1':'0');}catch(err){}
  }
  function portraitSidesDefaults(){
    var hdr=document.querySelector('.catalog-header');
    var top=hdr?Math.round(hdr.getBoundingClientRect().height):56;
    var availW=Math.max(320,window.innerWidth||900);
    var availH=Math.max(240,(window.innerHeight||1200)-top);
    return {stackW:Math.round(availW*PORTRAIT_STACK_FRAC),searchH:Math.round(availH*PORTRAIT_SEARCH_FRAC),availW:availW,availH:availH};
  }
  function clampPortraitTravel(val,def,track){
    var lo=def-PORTRAIT_TRAVEL*track;
    var hi=def+PORTRAIT_TRAVEL*track;
    if(lo<80)lo=80;
    if(hi>track-80)hi=Math.max(lo,track-80);
    val=Number(val);
    if(!isFinite(val))val=def;
    return Math.round(Math.max(lo,Math.min(hi,val)));
  }
  function parsePortraitStored(key,fallback){
    try{
      var v=localStorage.getItem(key);
      if(!v)return fallback;
      var n=parseInt(v,10);
      return (isFinite(n)&&n>0)?n:fallback;
    }catch(err){return fallback;}
  }
    function syncPortraitFlipBtn(){
    var fb=document.getElementById('portraitFlipBtn');
    if(!fb)return;
    var on=portraitFlipOn();
    var show=!!(document.body.classList.contains('display-sides')&&isPortraitDesktopSides()&&!(typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle')));
    fb.textContent=on?'Portrait: menus right':'Portrait: menus left';
    fb.setAttribute('aria-pressed',on?'true':'false');
    fb.title='Desktop portrait Sides: put Search/Keywords on the left or right of Content';
    fb.hidden=!show;
    fb.setAttribute('aria-hidden',show?'false':'true');
  }
  function ensurePortraitFlipBtn(){
    var pop=document.getElementById('layoutPresetsPop');
    if(!pop)return;
    var fb=document.getElementById('portraitFlipBtn');
    if(!fb){
      fb=document.createElement('button');
      fb.type='button';fb.id='portraitFlipBtn';fb.className='layout-restore-defaults';
      fb.addEventListener('click',function(e){
        e.preventDefault();e.stopPropagation();
        togglePortraitSidesFlip();
      });
      var rb=document.getElementById('layoutRestoreDefaults');
      if(rb)rb.insertAdjacentElement('afterend',fb);
      else pop.appendChild(fb);
    }
    syncPortraitFlipBtn();
  }
  function togglePortraitSidesFlip(){
    if(typeof snapshotCurrentLayoutBucket==='function'){snapshotCurrentLayoutBucket();lastLayoutBucket='pending';}
    writePortraitFlip(!portraitFlipOn());
    applyPortraitSides();
    if(typeof placeSidesHandles==='function')placeSidesHandles();
    
  }
  function placePortraitSidesHandles(){
    var split=document.getElementById('searchSplit');
    var sep=document.getElementById('dualFsSep');
    var ch=document.getElementById('searchChrome');
    var fw=document.getElementById('filterWrap');
    var hdr=document.querySelector('.catalog-header');
    var top=hdr?Math.round(hdr.getBoundingClientRect().bottom):62;
    var hidden=document.body.classList.contains('search-chrome-collapsed');
    var kwHid=document.body.classList.contains('kw-chrome-collapsed');
    var editing=document.body.classList.contains('layout-edit');
    var flip=document.body.classList.contains('sides-portrait-flip');
    var both=!hidden&&!kwHid;
    function applyBar(el,props){
      if(!el)return;
      el.removeAttribute('style');
      Object.keys(props).forEach(function(k){el.style.setProperty(k,props[k],'important');});
    }
    if(split&&ch&&editing&&both){
      var r=ch.getBoundingClientRect();
      applyBar(split,{position:'fixed',display:'block',left:Math.round(r.left)+'px',width:Math.round(r.width)+'px',top:Math.round(r.bottom+(parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sides-pane-gap'))||6)/2-6)+'px',height:'12px','min-width':'0','max-width':'none','min-height':'12px','max-height':'12px',bottom:'auto','z-index':'80',margin:'0',transform:'none','pointer-events':'auto',cursor:'ns-resize'});
    }else if(split){split.removeAttribute('style');}
    var stack=(!hidden&&ch)?ch:(!kwHid&&fw)?fw:null;
    if(sep&&stack&&editing&&(!hidden||!kwHid)){
      var r2=stack.getBoundingClientRect();
      var paneGap=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sides-pane-gap'))||6;var x=flip?Math.round(r2.left-paneGap/2-6):Math.round(r2.right+paneGap/2-6);
      applyBar(sep,{position:'fixed',display:'block',top:top+'px',bottom:'0',left:x+'px',width:'12px','min-width':'12px','max-width':'12px',height:'auto','z-index':'80',margin:'0',transform:'none','pointer-events':'auto',cursor:'ew-resize'});
    }else if(sep&&!document.body.classList.contains('dual-fs-open')){sep.removeAttribute('style');}
  }
  function applyPortraitSides(){
    var sides=document.body.classList.contains('display-sides');
    if(typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle')){
      document.body.classList.remove('sides-portrait-flip');
      if(typeof syncPortraitFlipBtn==='function')syncPortraitFlipBtn();
      return;
    }
    var portrait=isPortraitDesktopSides();
    var flip=sides&&portrait&&portraitFlipOn();
    document.body.classList.toggle('sides-portrait-flip',flip);
    ensurePortraitFlipBtn();
    if(!sides||!portrait){
      syncPortraitFlipBtn();
      return;
    }
    var d=portraitSidesDefaults();
    var id=(typeof layoutBucketId==='function')?layoutBucketId():('portrait-'+(flip?'B':'A')+'-sck');
    var b=(typeof sidesBuckets==='function'?sidesBuckets()[id]:null)||{};
    var lw=clampPortraitTravel(b.plw||parsePortraitStored('catalog-portrait-lw',d.stackW),d.stackW,d.availW);
    var mh=clampPortraitTravel(b.pmh||parsePortraitStored('catalog-portrait-menu-h',d.searchH),d.searchH,d.availH);
    document.documentElement.style.setProperty('--portrait-lw',lw+'px');
    document.documentElement.style.setProperty('--portrait-menu-h',mh+'px');
    document.documentElement.style.setProperty('--portrait-rw',Math.max(80,d.availW-lw)+'px');
    syncPortraitFlipBtn();
    
  }
  window.portraitFlipOn=portraitFlipOn;
  window.isPortraitDesktopSides=isPortraitDesktopSides;
  window.portraitSidesDefaults=portraitSidesDefaults;
  window.clampPortraitTravel=clampPortraitTravel;
  window.applyPortraitSides=applyPortraitSides;
  window.placePortraitSidesHandles=placePortraitSidesHandles;
  window.togglePortraitSidesFlip=togglePortraitSidesFlip;
  window.ensurePortraitFlipBtn=ensurePortraitFlipBtn;
  window.syncPortraitFlipBtn=syncPortraitFlipBtn;
    try{applyPortraitSides();if(typeof placeSidesHandles==='function')placeSidesHandles();}catch(err){}
  if(window.matchMedia){
    var mqP=window.matchMedia('(orientation: portrait)');
    var mqD=window.matchMedia('(min-width:900px)');
    function onQ(){if(typeof applySidesCols==='function')applySidesCols();}
    if(mqP.addEventListener){mqP.addEventListener('change',onQ);mqD.addEventListener('change',onQ);}
    else if(mqP.addListener){mqP.addListener(onQ);mqD.addListener(onQ);}
  }
})();
function displayPickKey(orient){
  var ns=window.CATALOG_NS||'catalog';
  if(orient)return 'catalog-display-pick-'+ns+'-'+orient;
  return 'catalog-display-pick-'+ns;
}
function displayOrientId(){
  try{
    if(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches)return 'portrait';
  }catch(err){}
  return 'landscape';
}
function displayModeOrientKey(orient){
  orient=orient||displayOrientId();
  return 'catalog-display-mode-'+(window.CATALOG_NS||'catalog')+'-'+orient;
}
function defaultDisplayForOrient(orient){
  orient=orient||displayOrientId();
  return orient==='portrait'?'middle':'sides';
}
function normalizeDisplayMode(m){
  if(m==='middle'||m==='sides')return m;
  if(m==='upper'||m==='fs')return 'sides';
  return '';
}
function readDisplayOrientPick(orient){
  orient=orient||displayOrientId();
  try{
    var flag=localStorage.getItem(displayPickKey(orient));
    var stored=normalizeDisplayMode(localStorage.getItem(displayModeOrientKey(orient))||'');
    if(flag==='1'&&stored)return stored;
    var asMode=normalizeDisplayMode(flag);
    if(asMode)return asMode;
  }catch(err){}
  return null;
}
function writeDisplayOrientPick(mode,orient){
  orient=orient||displayOrientId();
  mode=normalizeDisplayMode(mode)||defaultDisplayForOrient(orient);
  try{
    localStorage.setItem(displayPickKey(orient),'1');
    localStorage.setItem(displayModeOrientKey(orient),mode);
    localStorage.setItem(displayPickKey(),'1');
  }catch(err){}
  
}
function resolveDisplayForOrient(orient){
  orient=orient||displayOrientId();
  var picked=readDisplayOrientPick(orient);
  if(picked)return picked;
  return defaultDisplayForOrient(orient);
}
var lastDisplayOrient=null;
function syncDisplayForOrientation(){
  var o=displayOrientId();
  if(lastDisplayOrient==null){lastDisplayOrient=o;return;}
  if(o===lastDisplayOrient)return;
  var next=resolveDisplayForOrient(o);
  lastDisplayOrient=o;
  
  if(typeof setDisplayMode==='function')setDisplayMode(next);
}
function displayIsMiddle(){return !!(document.body&&document.body.classList.contains('display-middle'));}
window.displayIsMiddle=displayIsMiddle;
window.displayPickKey=displayPickKey;
window.displayOrientId=displayOrientId;
window.displayModeOrientKey=displayModeOrientKey;
window.defaultDisplayForOrient=defaultDisplayForOrient;
window.readDisplayOrientPick=readDisplayOrientPick;
window.writeDisplayOrientPick=writeDisplayOrientPick;
window.resolveDisplayForOrient=resolveDisplayForOrient;
window.syncDisplayForOrientation=syncDisplayForOrientation;
function middleLayoutDefaults(){
  var hdr=document.querySelector('.catalog-header');
  var top=hdr?Math.round(hdr.getBoundingClientRect().height):56;
  var availW=Math.max(280,window.innerWidth||900);
  var availH=Math.max(220,(window.innerHeight||800)-top);
  var minL=Math.max(148,Math.min(220,Math.round(availW*0.24)));
  var minR=Math.max(148,Math.min(220,Math.round(availW*0.24)));
  var minH=Math.max(132,Math.min(200,Math.round(availH*0.20)));
  var minC=Math.max(120,Math.min(200,Math.round(availH*0.18)));
  return {menuH:Math.round(availH*0.38),lw:Math.round(availW*0.5),availW:availW,availH:availH,minL:minL,minR:minR,minH:minH,minC:minC};
}
function middleLwKey(){return (typeof liveLayoutKey==='function'?liveLayoutKey('catalog-middle-lw-'):('catalog-middle-lw-'+(window.CATALOG_NS||'catalog')));}
function middleMhKey(){return (typeof liveLayoutKey==='function'?liveLayoutKey('catalog-middle-menu-h-'):('catalog-middle-menu-h-'+(window.CATALOG_NS||'catalog')));}
function parseMiddleStored(key,fallback){
  try{
    var v=localStorage.getItem(key);
    if(!v){
      if(key===middleLwKey())v=localStorage.getItem('catalog-middle-lw');
      else if(key===middleMhKey())v=localStorage.getItem('catalog-middle-menu-h');
    }
    if(!v)return fallback;
    var n=parseInt(v,10);
    return (isFinite(n)&&n>0)?n:fallback;
  }catch(err){return fallback;}
}
function clampMiddleLw(val,d){
  d=d||middleLayoutDefaults();
  val=Number(val);if(!isFinite(val))val=d.lw;
  return Math.round(Math.max(d.minL,Math.min(d.availW-d.minR,val)));
}
function clampMiddleMh(val,d){
  d=d||middleLayoutDefaults();
  val=Number(val);if(!isFinite(val))val=d.menuH;
  return Math.round(Math.max(d.minH,Math.min(d.availH-d.minC,val)));
}
function writeMiddleLayout(lw,mh){
  if(typeof sidesPinned!=='undefined'&&sidesPinned)return;
  if(typeof modeLayoutPinned==='function'&&modeLayoutPinned())return;
  var d=middleLayoutDefaults();
  if(lw!=null)lw=clampMiddleLw(lw,d);
  if(mh!=null)mh=clampMiddleMh(mh,d);
  try{
    if(lw!=null)localStorage.setItem(middleLwKey(),lw+'px');
    if(mh!=null)localStorage.setItem(middleMhKey(),mh+'px');
  }catch(err){}
  var patch={};
  if(lw!=null)patch.middleLw=lw;
  if(mh!=null)patch.middleMh=mh;
  if(Object.keys(patch).length&&typeof writeModeSlot==='function')writeModeSlot(patch,'sides');
  if(typeof snapshotCurrentLayoutBucket==='function'&&displayIsMiddle()){
    var bid=(typeof layoutBucketId==='function')?layoutBucketId():'middle-sck';
    snapshotCurrentLayoutBucket(bid);
  }
  
}
function applyMiddleLayout(){
  if(!displayIsMiddle())return;
  document.body.classList.remove('sides-portrait-flip');
  var d=middleLayoutDefaults();
  var slot=(typeof readModeSlot==='function'?readModeSlot('sides'):{})||{};
  var bid=(typeof layoutBucketId==='function')?layoutBucketId():'middle-sck';
  var buck=(typeof sidesBuckets==='function'&&sidesBuckets()[bid])||{};
  var lw=buck.mlw||slot.middleLw||parseMiddleStored(middleLwKey(),d.lw);
  var mh=buck.mmh||slot.middleMh||parseMiddleStored(middleMhKey(),d.menuH);
  lw=clampMiddleLw(lw,d);
  mh=clampMiddleMh(mh,d);
  document.documentElement.style.setProperty('--middle-menu-h',mh+'px');
  document.documentElement.style.setProperty('--middle-lw',lw+'px');
  document.documentElement.style.setProperty('--middle-rw',Math.max(d.minR,d.availW-lw)+'px');
  var fw=document.getElementById('filterWrap');
  if(fw&&!document.body.classList.contains('kw-chrome-collapsed')){
    fw.classList.add('open');document.body.classList.add('kw-open');
  }
  
}
function placeMiddleHandles(){
  var split=document.getElementById('searchSplit');
  var sep=document.getElementById('dualFsSep');
  var ch=document.getElementById('searchChrome');
  var fw=document.getElementById('filterWrap');
  var editing=document.body.classList.contains('layout-edit');
  var pinned=!!(typeof sidesPinned!=='undefined'&&sidesPinned)||(typeof modeLayoutPinned==='function'&&modeLayoutPinned())||document.body.classList.contains('mode-layout-pinned')||document.body.classList.contains('sides-pinned');
  var hidden=document.body.classList.contains('search-chrome-collapsed');
  var kwHid=document.body.classList.contains('kw-chrome-collapsed');
  if(pinned)editing=false;
  function applyBar(el,props){
    if(!el)return;
    el.removeAttribute('style');
    Object.keys(props).forEach(function(k){el.style.setProperty(k,props[k],'important');});
  }
  if(split&&ch&&fw&&editing&&!hidden&&!kwHid){
    var r=ch.getBoundingClientRect();
    var r2=fw.getBoundingClientRect();
    var left=Math.min(r.left,r2.left);
    var right=Math.max(r.right,r2.right);
    var top=Math.max(r.bottom,r2.bottom);
    applyBar(split,{position:'fixed',display:'block',left:Math.round(left)+'px',width:Math.round(right-left)+'px',top:Math.round(top-6)+'px',height:'12px','min-width':'0','max-width':'none','min-height':'12px','max-height':'12px',bottom:'auto','z-index':'80',margin:'0',transform:'none','pointer-events':'auto',cursor:'ns-resize'});
  }else if(split){split.removeAttribute('style');}
  if(sep&&ch&&fw&&editing&&!hidden&&!kwHid){
    var a=ch.getBoundingClientRect();
    var b=fw.getBoundingClientRect();
    var x=Math.round((a.right+b.left)/2-6);
    var top2=Math.min(a.top,b.top);
    var bot=Math.max(a.bottom,b.bottom);
    applyBar(sep,{position:'fixed',display:'block',left:x+'px',top:Math.round(top2)+'px',height:Math.round(bot-top2)+'px',width:'12px','min-width':'12px','max-width':'12px',bottom:'auto','z-index':'80',margin:'0',transform:'none','pointer-events':'auto',cursor:'ew-resize'});
  }else if(sep&&!document.body.classList.contains('dual-fs-open')){sep.removeAttribute('style');}
}
window.middleLayoutDefaults=middleLayoutDefaults;
window.applyMiddleLayout=applyMiddleLayout;
window.placeMiddleHandles=placeMiddleHandles;
window.writeMiddleLayout=writeMiddleLayout;
window.middleLwKey=middleLwKey;
window.middleMhKey=middleMhKey;
window.clampMiddleLw=clampMiddleLw;
window.clampMiddleMh=clampMiddleMh;
function applySidesCols(){
  var hdr=document.querySelector('.catalog-header');
  if(hdr)document.documentElement.style.setProperty('--cat-header-h',Math.round(hdr.getBoundingClientRect().bottom)+'px');
  if(!document.body.classList.contains('display-sides')){
    document.body.style.removeProperty('--sides-lw');
    document.body.style.removeProperty('--sides-rw');
    document.body.style.removeProperty('--sides-index-h');
    document.body.classList.remove('kw-chrome-collapsed');
    ['searchSplit','dualFsSep'].forEach(function(id){var el=document.getElementById(id);if(el)el.removeAttribute('style');});
    if(typeof clearChromeInlineLeftovers==='function')clearChromeInlineLeftovers();
    if(typeof applyUpperContain==='function')applyUpperContain();
    if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
    if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();

    return;
  }
  if(typeof clearChromeInlineLeftovers==='function')clearChromeInlineLeftovers();
  var middle=typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle');
  var portrait=typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides();
  document.body.classList.toggle('sides-orient-portrait',!!portrait&&!middle);
  if(middle){
    document.body.classList.remove('sides-portrait-flip');
    if(typeof applyMiddleLayout==='function')applyMiddleLayout();
  }else if(portrait){
    var flipOn=typeof window.portraitFlipOn==='function'?window.portraitFlipOn():document.body.classList.contains('sides-portrait-flip');
    document.body.classList.toggle('sides-portrait-flip',!!flipOn);
  }else{
    document.body.classList.remove('sides-portrait-flip');
  }
  if(typeof syncLayoutBucket==='function')syncLayoutBucket();
  var vw=window.innerWidth||1200;
  var minL=240,minR=260,minC=280;
  var o=readSidesCols();
  var lw=o.lw||Math.round(vw*0.22);
  var rw=o.rw||Math.round(vw*0.26);
  if(middle){
    /* middle uses --middle-* ; keep widescreen --sides-lw/--sides-rw intact */
  }else if(portrait){
    /* portrait uses --portrait-* buckets; do not overwrite widescreen --sides-lw/--sides-rw */
  }else if(document.body.classList.contains('search-chrome-collapsed')){
    document.body.style.setProperty('--sides-lw','0px');
  }else{
    lw=Math.max(minL,Math.min(lw,vw-minR-minC-2*(parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sides-pane-gap'))||6)));
    document.body.style.setProperty('--sides-lw',lw+'px');
  }
  if(typeof applySidesIndexH==='function')applySidesIndexH();
  if(portrait){
  }else if(document.body.classList.contains('kw-chrome-collapsed')){
    document.body.style.setProperty('--sides-rw','0px');
  }else if(!document.body.classList.contains('kw-open')){
    document.body.style.removeProperty('--sides-rw');
  }else{
    rw=Math.max(minR,Math.min(rw,vw-minL-minC-2*(parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sides-pane-gap'))||6)));
    document.body.style.setProperty('--sides-rw',rw+'px');
  }
  if(typeof applyPortraitSides==='function')applyPortraitSides();
  placeSidesHandles();
  syncSidesPin();
  if(typeof applyUpperContain==='function')applyUpperContain();
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();

  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();

}
function placeSidesHandles(){
  if(!document.body.classList.contains('display-sides'))return;
  if(typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle')){
    if(typeof placeMiddleHandles==='function')placeMiddleHandles();
    return;
  }
  if(typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides()){
    if(typeof placePortraitSidesHandles==='function')placePortraitSidesHandles();
    return;
  }
  var split=document.getElementById('searchSplit');
  var sep=document.getElementById('dualFsSep');
  var ch=document.getElementById('searchChrome');
  var fw=document.getElementById('filterWrap');
  var hdr=document.querySelector('.catalog-header');
  var top=hdr?Math.round(hdr.getBoundingClientRect().bottom):62;
  var hidden=document.body.classList.contains('search-chrome-collapsed');
  var kwHid=document.body.classList.contains('kw-chrome-collapsed');
  var editing=document.body.classList.contains('layout-edit');
  if(split&&ch&&!hidden&&editing){
    var r=ch.getBoundingClientRect();
    split.style.cssText='position:fixed;top:'+top+'px;bottom:0;left:'+Math.round(r.right+(parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sides-pane-gap'))||6)/2-6)+'px;width:12px;min-width:12px;max-width:12px;height:auto;z-index:80;margin:0;transform:none;pointer-events:auto;';
  }else if(split){split.removeAttribute('style');}
  if(sep&&fw&&editing&&!kwHid){
    var r2=fw.getBoundingClientRect();
    sep.style.cssText='position:fixed;top:'+top+'px;bottom:0;left:'+Math.round(r2.left-(parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sides-pane-gap'))||6)/2-6)+'px;width:12px;min-width:12px;max-width:12px;height:auto;z-index:80;margin:0;transform:none;pointer-events:auto;';
  }else if(sep&&!document.body.classList.contains('dual-fs-open')){sep.removeAttribute('style');}
}
(function bindSidesDrag(){
  var drag=null;
  function onDown(e,which){
    if(!document.body.classList.contains('display-sides'))return;
    if(!document.body.classList.contains('layout-edit'))return;
    if(sidesPinned||(typeof modeLayoutPinned==='function'&&modeLayoutPinned()))return;
    if(e.pointerType==='mouse'&&e.button!=null&&e.button!==0)return;
    e.preventDefault();e.stopPropagation();
    if(typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle')){
      var dM=typeof middleLayoutDefaults==='function'?middleLayoutDefaults():null;
      if(!dM)return;
      var rootM=document.documentElement;
      var mlw=parseInt(getComputedStyle(rootM).getPropertyValue('--middle-lw'),10)||dM.lw;
      var mmh=parseInt(getComputedStyle(rootM).getPropertyValue('--middle-menu-h'),10)||dM.menuH;
      var tM=e.currentTarget||e.target;
      drag={middle:true,which:which,x:e.clientX,y:e.clientY,lw:mlw,mh:mmh,def:dM,id:e.pointerId};
      try{if(tM&&tM.setPointerCapture)tM.setPointerCapture(e.pointerId);}catch(err){}
      return;
    }
    if(typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides()){
      var d=typeof portraitSidesDefaults==='function'?portraitSidesDefaults():null;
      if(!d)return;
      var root=document.documentElement;
      var plw=parseInt(getComputedStyle(root).getPropertyValue('--portrait-lw'),10)||d.stackW;
      var pmh=parseInt(getComputedStyle(root).getPropertyValue('--portrait-menu-h'),10)||d.searchH;
      var tP=e.currentTarget||e.target;
      drag={portrait:true,which:which,x:e.clientX,y:e.clientY,lw:plw,mh:pmh,flip:document.body.classList.contains('sides-portrait-flip'),def:d,id:e.pointerId};
      try{if(tP&&tP.setPointerCapture)tP.setPointerCapture(e.pointerId);}catch(err){}

      return;
    }
    var vw=window.innerWidth||1200;
    var t=e.currentTarget||e.target;
    drag={which:which,x:e.clientX,lw:parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||Math.round(vw*0.22),rw:parseInt(getComputedStyle(document.body).getPropertyValue('--sides-rw'),10)||Math.round(vw*0.26),id:e.pointerId};
    try{if(t&&t.setPointerCapture)t.setPointerCapture(e.pointerId);}catch(err){}

  }
  function onMove(e){
    if(!drag)return;
    if(drag.middle){
      var dM=drag.def;
      if(drag.which==='split'){
        var mhM=clampMiddleMh(drag.mh+(e.clientY-drag.y),dM);
        document.documentElement.style.setProperty('--middle-menu-h',mhM+'px');
      }else{
        var nlwM=clampMiddleLw(drag.lw+(e.clientX-drag.x),dM);
        document.documentElement.style.setProperty('--middle-lw',nlwM+'px');
        document.documentElement.style.setProperty('--middle-rw',Math.max(dM.minR,dM.availW-nlwM)+'px');
      }
      if(typeof placeSidesHandles==='function')placeSidesHandles();
      return;
    }
    if(drag.portrait){
      var clamp=window.clampPortraitTravel||function(v){return v;};
      if(drag.which==='split'){
        var mh=clamp(drag.mh+(e.clientY-drag.y),drag.def.searchH,drag.def.availH);
        document.documentElement.style.setProperty('--portrait-menu-h',mh+'px');
        try{localStorage.setItem('catalog-portrait-menu-h',mh+'px');}catch(ex){}
      }else{
        var dx=e.clientX-drag.x;
        var nlw=clamp(drag.flip?drag.lw-dx:drag.lw+dx,drag.def.stackW,drag.def.availW);
        document.documentElement.style.setProperty('--portrait-lw',nlw+'px');
        document.documentElement.style.setProperty('--portrait-rw',Math.max(80,drag.def.availW-nlw)+'px');
        try{localStorage.setItem('catalog-portrait-lw',nlw+'px');localStorage.setItem('catalog-portrait-rw',Math.max(0,drag.def.availW-nlw)+'px');}catch(ex){}
      }
      placeSidesHandles();
      return;
    }
    var vw=window.innerWidth||1200;
    var minL=240,minR=260,minC=280;
    if(drag.which==='split'){
      var lw=Math.max(minL,Math.min(vw-minR-minC-2*(parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sides-pane-gap'))||6),drag.lw+(e.clientX-drag.x)));
      document.body.style.setProperty('--sides-lw',lw+'px');
    }else{
      var rw=Math.max(minR,Math.min(vw-minL-minC-2*(parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sides-pane-gap'))||6),drag.rw-(e.clientX-drag.x)));
      document.body.style.setProperty('--sides-rw',rw+'px');
    }
    placeSidesHandles();
  }
  function onUp(e){
    if(!drag)return;
    if(drag.middle){
      var mlwU=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-lw'),10)||0;
      var mmhU=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-menu-h'),10)||0;
      if(typeof writeMiddleLayout==='function')writeMiddleLayout(mlwU,mmhU);
      drag=null;

      return;
    }
    if(drag.portrait){
      var plw=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--portrait-lw'),10)||0;
      var pmh=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--portrait-menu-h'),10)||0;
      var whichP=drag.which;
      try{
        localStorage.setItem('catalog-portrait-lw',plw+'px');
        localStorage.setItem('catalog-portrait-menu-h',pmh+'px');
        localStorage.setItem('catalog-portrait-rw',Math.max(0,(window.innerWidth||0)-plw)+'px');
        if(typeof snapshotCurrentLayoutBucket==='function')snapshotCurrentLayoutBucket();
      }catch(ex){}
      drag=null;

      return;
    }
    var lw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0;
    var rw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-rw'),10)||0;
    var which=drag.which,dx=e&&e.clientX!=null?(e.clientX-drag.x):0;
    writeSidesCols(lw,rw);
    drag=null;

  }
  function bind(el,which){
    if(!el||el.dataset.sidesDragBound)return;
    el.dataset.sidesDragBound='1';
    el.addEventListener('pointerdown',function(e){if(e.target&&e.target.closest&&e.target.closest('#dualFsSepPin'))return;onDown(e,which);});
  }
  bind(document.getElementById('searchSplit'),'split');
  bind(document.getElementById('dualFsSep'),'sep');
  document.addEventListener('pointermove',onMove);
  document.addEventListener('pointerup',onUp);
  document.addEventListener('pointercancel',onUp);
})();

function applySidesIndexH(){
  if(!document.body.classList.contains('display-sides')){
    document.body.style.removeProperty('--sides-index-h');
    return;
  }
  var slot=typeof readModeSlot==='function'?readModeSlot('sides'):{};
  var h=parseInt(slot&&slot.indexH,10);
  if(h>40)document.body.style.setProperty('--sides-index-h',h+'px');
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
}
function ensureIndexHeightHandle(){
  var ix=document.getElementById('catalogIndex');
  if(!ix)return null;
  var h=document.getElementById('indexHeight');
  if(!h){
    h=document.createElement('button');
    h.type='button';
    h.id='indexHeight';
    h.className='index-height';
    h.setAttribute('aria-label','Drag the bottom edge to resize Index height');
    h.setAttribute('aria-orientation','horizontal');
    h.tabIndex=-1;
    ix.appendChild(h);
  }
  return h;
}
function bindIndexHeight(){
  var h=ensureIndexHeightHandle();
  if(!h||h.dataset.indexHBound)return;
  h.dataset.indexHBound='1';
  var drag=null;
  h.addEventListener('pointerdown',function(e){
    if(!document.body.classList.contains('display-sides'))return;
    if(!document.body.classList.contains('layout-edit'))return;
    if(sidesPinned||(typeof modeLayoutPinned==='function'&&modeLayoutPinned()))return;
    if(e.pointerType==='mouse'&&e.button!=null&&e.button!==0)return;
    e.preventDefault();e.stopPropagation();
    var ix=document.getElementById('catalogIndex');
    if(!ix||ix.classList.contains('is-collapsed'))return;
    var cur=Math.round(ix.getBoundingClientRect().height);
    drag={y:e.clientY,h:cur,id:e.pointerId};
    try{h.setPointerCapture(e.pointerId);}catch(err){}

  });
  function move(e){
    if(!drag)return;
    var max=Math.round(Math.min(window.innerHeight*0.7,640));
    var nh=Math.max(72,Math.min(max,drag.h+(e.clientY-drag.y)));
    document.body.style.setProperty('--sides-index-h',nh+'px');
  }
  function up(e){
    if(!drag)return;
    var nh=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-index-h'),10)||0;
    drag=null;
    if(nh>40&&typeof writeModeSlot==='function')writeModeSlot({indexH:nh},'sides');
    if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();

  }
  document.addEventListener('pointermove',move);
  document.addEventListener('pointerup',up);
  document.addEventListener('pointercancel',up);
}
window.applySidesIndexH=applySidesIndexH;
window.ensureIndexHeightHandle=ensureIndexHeightHandle;
window.bindIndexHeight=bindIndexHeight;

function syncIndexToggleUi(box){
  if(!box)box=document.getElementById('catalogIndex');
  var btn=document.getElementById('catalogIndexToggle');
  if(!box||!btn)return;
  var collapsed=box.classList.contains('is-collapsed');
  btn.setAttribute('aria-expanded',collapsed?'false':'true');
  btn.setAttribute('aria-label',collapsed?'Expand index':'Collapse index');
  btn.title=collapsed?'Expand index':'Collapse index';
}
function syncIndexDock(){
  var ix=document.getElementById('catalogIndex');
  var cm=document.getElementById('catalogMain');
  if(!ix||!cm)return;
  if(!document.body.classList.contains('display-sides')){
    ix.dataset.dockAuto='';
    return;
  }
  if(ix.dataset.goingTop==='1'&&cm.scrollTop<=12)ix.dataset.goingTop='';
}
function bindIndexDock(){
  var cm=document.getElementById('catalogMain');
  var ix=document.getElementById('catalogIndex');
  if(!cm||!ix)return;
  if(!cm.dataset.indexDockBound){
    cm.dataset.indexDockBound='1';
    cm.addEventListener('scroll',syncIndexDock,{passive:true});
  }
  if(!ix.dataset.indexHeadBound){
    ix.dataset.indexHeadBound='1';
    var head=ix.querySelector('.catalog-index-head');
    /* Index opens only via #catalogIndexToggle */
  }
}
function bindCatalogTop(){
  function goTop(e,topEl){
    if(!document.body.classList.contains('display-sides'))return;
    if(e){e.preventDefault();e.stopPropagation();}
    var cm=document.getElementById('catalogMain');
    var ix=document.getElementById('catalogIndex');
    var ixColBefore=!!(ix&&ix.classList.contains('is-collapsed'));
    var searchBefore=document.body.classList.contains('search-chrome-collapsed');
    var kwBefore=document.body.classList.contains('kw-chrome-collapsed');
    var kwOpenBefore=document.body.classList.contains('kw-open');
    if(ix)ix.dataset.goingTop='1';
    if(cm){try{cm.scrollTo({top:cm.scrollTop,behavior:'instant'});}catch(err){cm.scrollTop=cm.scrollTop;}try{cm.scrollTo({top:0,behavior:'smooth'});}catch(err){cm.scrollTop=0;}}
  }
  function goBot(e){
    if(!document.body.classList.contains('display-sides'))return;
    if(e){e.preventDefault();e.stopPropagation();}
    var cm=document.getElementById('catalogMain');
    var ix=document.getElementById('catalogIndex');
    var ixColBefore=!!(ix&&ix.classList.contains('is-collapsed'));
    var searchBefore=document.body.classList.contains('search-chrome-collapsed');
    var kwBefore=document.body.classList.contains('kw-chrome-collapsed');
    if(cm){try{cm.scrollTo({top:cm.scrollTop,behavior:'instant'});}catch(err){cm.scrollTop=cm.scrollTop;}try{cm.scrollTo({top:cm.scrollHeight,behavior:'smooth'});}catch(err){cm.scrollTop=cm.scrollHeight;}}
  }
  var stack=document.getElementById('catalogJumpStack');
  if(stack&&!stack.dataset.sidesJumpBound){
    stack.dataset.sidesJumpBound='1';
    stack.addEventListener('click',function(e){
      var t=e.target&&e.target.closest&&e.target.closest('a.top,a.bottom');
      if(!t)return;
      if(t.classList.contains('top'))goTop(e,t);
      else goBot(e);
    },true);
  }
  var top=document.querySelector('a.top');
  if(top&&!top.dataset.sidesTopBound&&!(stack&&stack.contains(top))){
    top.dataset.sidesTopBound='1';
    top.addEventListener('click',function(e){goTop(e,top);});
  }
  var bot=document.querySelector('a.bottom');
  if(bot&&!bot.dataset.sidesBotBound&&!(stack&&stack.contains(bot))){
    bot.dataset.sidesBotBound='1';
    bot.addEventListener('click',function(e){goBot(e);});
  }
}

function applyIndexScrollFit(){
  var ix=document.getElementById('catalogIndex');
  var il=document.getElementById('catalogIndexList')||(ix&&ix.querySelector('ul.index'));
  if(!ix||!il)return;
  if(ix.dataset.ixFitting==='1')return;
  if(!document.body.classList.contains('display-sides')||ix.classList.contains('is-collapsed')||ix.classList.contains('is-embedded')){
    ['height','max-height','columns','column-width','column-count','column-fill','display','grid-template-columns'].forEach(function(p){il.style.removeProperty(p);});
    try{delete ix.dataset.ixFitInner;}catch(err){ix.dataset.ixFitInner='';}

    if(typeof syncBottomBelowIndex==='function')syncBottomBelowIndex();
    if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();
    return;
  }
  var head=ix.querySelector('.catalog-index-head');
  var hh=head?Math.round(head.getBoundingClientRect().height):0;
  var inner=Math.max(48,Math.round(ix.clientHeight-hh));
  if((ix.dataset.ixFitInner||'')===String(inner)&&il.style.height===inner+'px'){
    if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();
    if(typeof syncBottomBelowIndex==='function')syncBottomBelowIndex();
    return;
  }
  ix.dataset.ixFitting='1';
  il.style.setProperty('columns','none');
  il.style.setProperty('column-width','auto');
  il.style.setProperty('column-count','1');
  il.style.removeProperty('column-fill');
  il.style.height=inner+'px';
  il.style.maxHeight=inner+'px';
  ix.dataset.ixFitInner=String(inner);
  if(!il.dataset.ixWheelBound){
    il.dataset.ixWheelBound='1';
    il.addEventListener('wheel',function(e){
      if(!document.body.classList.contains('display-sides'))return;
      var max=il.scrollHeight-il.clientHeight;
      if(max<=1)return;
      var atTop=il.scrollTop<=0&&e.deltaY<0;
      var atBot=il.scrollTop>=max-1&&e.deltaY>0;
      if(!atTop&&!atBot)e.stopPropagation();
    },{passive:true});
  }
  ix.dataset.ixFitting='';

  if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();
  if(typeof syncBottomBelowIndex==='function')syncBottomBelowIndex();
}
window.applyIndexScrollFit=applyIndexScrollFit;
function clearChromeInlineLeftovers(){
  var ch=document.getElementById('searchChrome');
  var had=ch?((ch.getAttribute('style')||'')+''):'';
  if(ch){
    ch.style.removeProperty('grid-template-columns');
    ch.style.removeProperty('grid-template-rows');
    ch.style.removeProperty('height');
    ch.style.removeProperty('max-height');
    if(!document.body.classList.contains('display-upper')){
      ch.classList.remove('search-split-lr','search-split-ud','search-split-dragging','search-height-set');
    }
  }
  var fw=document.getElementById('filterWrap');
  if(fw&&!document.body.classList.contains('display-fs')){
    fw.style.removeProperty('height');
    fw.style.removeProperty('max-height');
  }
  ['acShell','kwbar','filterPanel'].forEach(function(id){
    var el=document.getElementById(id);
    if(el&&!document.body.classList.contains('display-upper'))el.style.removeProperty('max-height');
  });
  var split=document.getElementById('searchSplit');
  var sep=document.getElementById('dualFsSep');
  if(!document.body.classList.contains('display-sides')){
    if(split)split.removeAttribute('style');
    if(sep&&!document.body.classList.contains('dual-fs-open'))sep.removeAttribute('style');
  }
}
function applyUpperContain(){
  var sh=document.getElementById('acShell');
  var kw=document.getElementById('kwbar');
  var panel=document.getElementById('filterPanel')||document.querySelector('#filterWrap .filter-panel');
  var ch=document.getElementById('searchChrome');
  function clr(el){if(el)el.style.removeProperty('max-height');}
  if(!document.body.classList.contains('display-upper')||!ch){clr(sh);clr(kw);clr(panel);return;}
  var bottom=ch.getBoundingClientRect().bottom;
  function cap(el){if(!el)return;el.style.setProperty('max-height',Math.max(72,Math.round(bottom-el.getBoundingClientRect().top))+'px','important');}
  cap(sh);cap(panel);cap(kw);
  if(!document.body.classList.contains('layout-edit')){ch.style.removeProperty('height');ch.style.maxHeight='min(46dvh,32rem)';}
}
function placeMenusForDisplay(mode){
  var ch=document.getElementById('searchChrome');
  var fw=document.getElementById('filterWrap');
  var main=document.getElementById('catalogMain');
  var split=document.getElementById('searchSplit');
  var sep=document.getElementById('dualFsSep');
  var ht=document.getElementById('searchHeight');
  if(!ch||!fw)return;
  var body=document.body;
  var col=document.getElementById('searchCol');
  if(mode==='sides'){
    if(fw.parentElement!==body)body.insertBefore(fw, main||null);
    if(split&&split.parentElement!==body)body.insertBefore(split, fw);
    if(sep&&sep.parentElement!==body)body.insertBefore(sep, fw);
    if(ht&&ht.parentElement!==ch)ch.appendChild(ht);
  }else if(mode==='fs'){
    if(fw.parentElement!==body)body.insertBefore(fw, main||null);
    if(split){
      if(col&&split.parentElement!==ch){if(col.nextSibling)ch.insertBefore(split,col.nextSibling);else ch.appendChild(split);}
    }
    if(sep&&sep.parentElement!==body)body.insertBefore(sep, main||fw);
    if(ht&&ht.parentElement!==ch)ch.appendChild(ht);
  }else{
    if(fw.parentElement!==ch)ch.appendChild(fw);
    if(split){
      if(col&&(split.parentElement!==ch||split.previousElementSibling!==col)){
        if(col.nextSibling)ch.insertBefore(split,col.nextSibling);
        else ch.insertBefore(split,fw);
      }else if(!col&&split.parentElement!==ch)ch.insertBefore(split,fw);
    }
    if(ht&&ht.parentElement!==ch)ch.appendChild(ht);
    if(sep&&sep.parentElement!==body)body.insertBefore(sep, main||ch.nextSibling);
  }

}
function syncDisplayBtns(){
  document.querySelectorAll('.display-btn').forEach(function(b){
    var on=b.getAttribute('data-display')===currentDisplay;
    b.classList.toggle('is-active',on);
    b.setAttribute('aria-pressed',on?'true':'false');
  });
}
function setDisplayMode(mode,opts){
  opts=opts||{};
  if(mode!=='upper'&&mode!=='sides'&&mode!=='fs'&&mode!=='middle')mode='sides';
  if(mode==='upper'||mode==='fs')mode='sides';
  var persistDisplay=mode;
  if(opts.pick){
    try{
      if(typeof writeDisplayOrientPick==='function')writeDisplayOrientPick(persistDisplay);
      else localStorage.setItem(typeof displayPickKey==='function'?displayPickKey():('catalog-display-pick-'+(window.CATALOG_NS||'catalog')),'1');
    }catch(err){}
  }
  if(mode==='middle')mode='sides';
  try{lastDisplayOrient=typeof displayOrientId==='function'?displayOrientId():lastDisplayOrient;}catch(err){}
  // fix-SIDES-ONLY: Sides works on all viewports via CSS — no mobile coercion
  var prev=typeof currentDisplay!=='undefined'?currentDisplay:'';
  var already=prev===mode;
  if(prev&&prev!=='fs')lastNonFsDisplay=prev;
  if(mode==='sides'){
    var wasCol=document.body.classList.contains('search-chrome-collapsed');
    var wasKw=document.body.classList.contains('kw-chrome-collapsed');
    var ixPre=document.getElementById('catalogIndex');
    var ilPre=document.getElementById('catalogIndexList');
    document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed','kw-chrome-collapsed');
    var fwPre=document.getElementById('filterWrap');
    if(fwPre){if(displayIsDesktop()){fwPre.classList.add('open');document.body.classList.add('kw-open');}else{fwPre.classList.remove('open');document.body.classList.remove('kw-open');}}
    var aPre=document.querySelector('#filterToggle .toggle-arrow')||document.querySelector('.toggle-arrow');
    if(aPre)aPre.textContent='▲';
    if(typeof syncSearchHideBtn==='function')syncSearchHideBtn();
    if(typeof syncKwHideBtn==='function')syncKwHideBtn();
    if(typeof resetIndexDock==='function')resetIndexDock();
    if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
    if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();

  }else{
    document.body.classList.remove('kw-chrome-collapsed');
  }
  if(prev&&prev!==mode&&typeof snapshotLiveToMode==='function')snapshotLiveToMode(prev);
  currentDisplay=typeof persistDisplay!=='undefined'?persistDisplay:mode;
  try{localStorage.setItem(DISPLAY_KEY,currentDisplay);}catch(err){}
  document.body.classList.remove('display-upper','display-sides','display-fs','display-middle');
  document.body.classList.add('display-'+mode);
  if(currentDisplay==='middle'){
    document.body.classList.add('display-middle');
    var fwMid=document.getElementById('filterWrap');
    if(fwMid){fwMid.classList.add('open');document.body.classList.add('kw-open');}
    document.body.classList.remove('kw-chrome-collapsed');
  }
  ensureCatalogMain();
  placeMenusForDisplay(mode);
  if(typeof ensureLayoutChromeBtns==='function')ensureLayoutChromeBtns();
  // fix-IDX-embed: embed index in upper/fs (prevent floating window); leave sides alone
  (function(){var idx=document.getElementById('catalogIndex');if(!idx)return;if(mode!=='sides')idx.classList.add('is-embedded');else idx.classList.remove('is-embedded');})();
  if(typeof bindFsModeHandles==='function')bindFsModeHandles();
  if(typeof applyModeSlot==='function')applyModeSlot(mode);
  if(mode==='sides'){
    if(typeof acFsWanted!=='undefined')acFsWanted=false;
    if(typeof kwFsWanted!=='undefined')kwFsWanted=false;
    document.body.classList.remove('ac-fs-open','kw-fs-open','dual-fs-open');
    var _acs=document.getElementById('acShell');if(_acs)_acs.classList.remove('ac-fs');
    var _sfs=document.getElementById('searchStripFs');if(_sfs){_sfs.setAttribute('aria-pressed','false');_sfs.setAttribute('aria-label','Fullscreen search');}
    var fw=document.getElementById('filterWrap');
    if(fw){
      if(displayIsDesktop()){fw.classList.add('open');document.body.classList.add('kw-open');}
      else{fw.classList.remove('open');document.body.classList.remove('kw-open');}
      if(typeof clearShadeBox==='function')clearShadeBox(fw);
      fw.style.removeProperty('height');fw.style.removeProperty('max-height');
    }
    if(typeof bindIndexDock==='function')bindIndexDock();
    if(typeof bindIndexHeight==='function')bindIndexHeight();
    if(typeof bindCatalogTop==='function')bindCatalogTop();
    document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed');
    var ac=document.getElementById('acList'),sh=document.getElementById('acShell');
    if(ac)ac.classList.add('open');
    if(sh){sh.classList.add('open');sh.classList.remove('ac-fs','ac-fixed');}
    if(typeof parkSearchStrip==='function')parkSearchStrip();
    try{if(typeof showAc==='function')showAc(((document.getElementById('searchInput')||{}).value||'').trim().toLowerCase(),{force:true});}catch(err){}
    if(typeof placeAcShell==='function')placeAcShell();
  }else if(mode==='fs'){
    var menu=opts.menu||'both'; // fix-FS: compact bar always shows both panels
    document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed','kw-chrome-collapsed');
    if(menu==='both'){
      if(typeof window.setAcFullscreen==='function')window.setAcFullscreen(true);
      if(typeof window.setKwFullscreen==='function')window.setKwFullscreen(true);
    }else if(menu==='search'){
      document.body.classList.remove('dual-fs-open');
      if(typeof kwFsWanted!=='undefined')kwFsWanted=false;
      if(typeof window.setKwFullscreen==='function')window.setKwFullscreen(false);
      document.body.classList.remove('kw-fs-open');
      var fwEx=document.getElementById('filterWrap');
      if(fwEx){fwEx.classList.remove('open');document.body.classList.remove('kw-open');}
      if(typeof window.setAcFullscreen==='function')window.setAcFullscreen(true);
    }else{
      document.body.classList.remove('dual-fs-open');
      if(typeof acFsWanted!=='undefined')acFsWanted=false;
      if(typeof window.setAcFullscreen==='function')window.setAcFullscreen(false);
      document.body.classList.remove('ac-fs-open');
      var shEx=document.getElementById('acShell');
      if(shEx)shEx.classList.remove('ac-fs','ac-fixed');
      if(typeof window.setKwFullscreen==='function')window.setKwFullscreen(true);
    }
    if(typeof placeMenusForDisplay==='function')placeMenusForDisplay('fs');
  }else{
    if(typeof window.setKwFullscreen==='function')window.setKwFullscreen(false);
    if(typeof window.setAcFullscreen==='function')window.setAcFullscreen(false);
    document.body.classList.remove('dual-fs-open');
    if(typeof parkSearchStrip==='function')parkSearchStrip();
    if(typeof placeAcShell==='function')placeAcShell();
  }
  if(typeof clearChromeInlineLeftovers==='function')clearChromeInlineLeftovers();
  var hdrFix=document.querySelector('.catalog-header');
  if(hdrFix)document.documentElement.style.setProperty('--cat-header-h',Math.round(hdrFix.getBoundingClientRect().bottom)+'px');
  if(typeof applySidesCols==='function')applySidesCols();
  if(typeof applyAll==='function')applyAll();
  if(typeof applyFsChromeSize==='function')applyFsChromeSize();
  if(typeof placeMenusForDisplay==='function')placeMenusForDisplay(mode);
  try{window.scrollTo(0,0);}catch(err){}
  if(typeof applyUpperContain==='function')applyUpperContain();
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();

  syncDisplayBtns();
  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns(); // fix-A: sync header btn state on every mode change
  if(typeof cardMinPlace==='function')try{cardMinPlace();}catch(err){}

}
window.setDisplayMode=setDisplayMode;
window.toggleKwFullscreen=function(){
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    if(typeof setKwFullscreen==='function')setKwFullscreen(!kwFsWanted);
    return;
  }
  if(typeof expandKwMenu==='function')expandKwMenu();
};
window.toggleAcFullscreen=function(){
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    if(typeof setAcFullscreen==='function')setAcFullscreen(!(typeof acFsWanted!=='undefined'&&acFsWanted));
    return;
  }
  if(typeof expandSearchMenu==='function')expandSearchMenu();
};
(function(){
  var m=(typeof resolveDisplayForOrient==='function')?resolveDisplayForOrient():((window.matchMedia&&window.matchMedia('(orientation:portrait)').matches)?'middle':'sides');
  if(m!=='upper'&&m!=='sides'&&m!=='fs'&&m!=='middle')m='sides';
  if(m==='upper'||m==='fs')m='sides';
  // Landscape defaults to Sides, portrait to Middle. Explicit picks are stored per orientation.
  setDisplayMode(m);
  if(typeof forceCatalogIndexClosed==='function')forceCatalogIndexClosed('boot');
  try{lastDisplayOrient=typeof displayOrientId==='function'?displayOrientId():lastDisplayOrient;}catch(err){}

  // fix-KW-default: restore or default-open Keywords on load
  (function(){var fw=document.getElementById('filterWrap');if(!fw)return;var key='catalog-kw-open-'+(window.CATALOG_NS||'catalog');var saved;try{saved=localStorage.getItem(key);}catch(e){}var shouldOpen=(saved===null)?true:(saved==='1');if(shouldOpen&&!fw.classList.contains('open')&&typeof currentDisplay!=='undefined'&&currentDisplay!=='sides'&&currentDisplay!=='middle'){if(typeof toggleFilter==='function')toggleFilter();}})();
  var _dm='search';
  try{_dm=typeof normalizeDataMode==='function'?normalizeDataMode(localStorage.getItem(window.DATA_MODE_KEY||('catalog-data-mode-'+(window.CATALOG_NS||'catalog')))||'search'):'search';}catch(err){_dm='search';}
  if(_dm!=='pick')_dm='search';
  if(typeof window.setMode==='function')window.setMode(_dm);

  window.addEventListener('resize',function(){
    if(!displayIsDesktop()){
      document.body.classList.remove('dual-fs-open');
      if(typeof kwFsWanted!=='undefined'&&currentDisplay!=='fs')kwFsWanted=false;
      if(typeof clearChromeInlineLeftovers==='function')clearChromeInlineLeftovers();
    if(typeof applyUpperContain==='function')applyUpperContain();
      // Sides handles all orientations via CSS — no mode coercion on resize
    }
    if(typeof applySidesCols==='function')applySidesCols();
    if(currentDisplay==='fs'&&typeof applyDualLayout==='function')applyDualLayout();
    if(typeof syncDisplayForOrientation==='function')syncDisplayForOrientation();
  },{passive:true});
  // Orientation change applies that orientation's default (or saved pick). Width-only resizes do not coerce.
  window.addEventListener('orientationchange',function(){setTimeout(function(){if(typeof syncDisplayForOrientation==='function')syncDisplayForOrientation();},0);});
  if(window.matchMedia){
    var mqOrient=window.matchMedia('(orientation: portrait)');
    function onOrientMq(){if(typeof syncDisplayForOrientation==='function')syncDisplayForOrientation();}
    if(mqOrient.addEventListener)mqOrient.addEventListener('change',onOrientMq);
    else if(mqOrient.addListener)mqOrient.addListener(onOrientMq);
  }

  var _tle=window.toggleLayoutEdit;
  if(typeof _tle==='function'){
    window.toggleLayoutEdit=function(){ _tle(); if(typeof applySidesCols==='function')applySidesCols(); };
  }
  var _tsc=window.toggleSearchChrome;
  if(typeof _tsc==='function'){
    window.toggleSearchChrome=function(){ _tsc(); if(typeof applySidesCols==='function')applySidesCols(); };
  }
  var _tf=window.toggleFilter;
  if(typeof _tf==='function'){
    window.toggleFilter=function(){
      var w=document.getElementById('filterWrap');
      if(document.body.classList.contains('display-sides')&&document.body.classList.contains('kw-chrome-collapsed')){
        if(typeof expandKwMenu==='function'){expandKwMenu();return;}
      }
      if(document.body.classList.contains('display-sides')&&w&&w.classList.contains('open')&&!document.body.classList.contains('kw-fs-open')){
        if(typeof collapseKwMenu==='function'){collapseKwMenu();return;}
      }
      _tf.apply(this,arguments);
      if(typeof applySidesCols==='function')applySidesCols();
    };
  }
})();

</script>
JS
  echo '</body></html>'
} > "$OUT"
rm -f "$IDX" "$BODY"

echo "KONTAKT CATALOG ($MODE): $OUT"
echo "libraries: $N   thumbs: $(ls "$THUMBS" 2>/dev/null | wc -l)   (magick: $HAVE_MAGICK)"
[ "$MODE" = portable ] && echo "size: $(du -h "$OUT" 2>/dev/null | cut -f1)"
echo "done."
