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
KW_CATS_JS='{"piano":"instrument","keys":"instrument","organ":"instrument","harmonium":"instrument","celeste":"instrument","harpsichord":"instrument","clavinova":"model","wurlitzer":"instrument","choir":"instrument","vocal":"instrument","voice":"instrument","strings":"instrument","string":"instrument","violin":"instrument","cello":"instrument","viola":"instrument","domra":"instrument","guitar":"instrument","bass":"instrument","bassoon":"instrument","harp":"instrument","mandolin":"instrument","lute":"instrument","flute":"instrument","recorder":"instrument","ocarina":"instrument","whistle":"instrument","woodwind":"instrument","reed":"instrument","clarinet":"instrument","oboe":"instrument","drum":"instrument","drums":"instrument","percussion":"instrument","kalimba":"instrument","bell":"instrument","bells":"instrument","glock":"instrument","chimes":"instrument","bodhran":"instrument","tabla":"instrument","tablas":"instrument","xylophone":"instrument","marimba":"instrument","synth":"instrument","pad":"instrument","bowed":"instrument","accordion":"instrument","saxophone":"instrument","harmonica":"instrument","melodica":"instrument","bagpipe":"instrument","didgeridoo":"instrument","flutina":"instrument","ukulele":"instrument","autoharp":"instrument","lapsteel":"instrument","dobro":"instrument","hurdy":"instrument","lyre":"instrument","erhu":"instrument","kantele":"instrument","gusli":"instrument","bandola":"instrument","guitarron":"instrument","jaw":"instrument","tongue":"instrument","bowl":"instrument","cajon":"instrument","djembe":"instrument","udu":"instrument","clave":"instrument","brass":"instrument","horn":"instrument","gamelan":"instrument","orchestra":"instrument","guitarist":"instrument","mellotron":"instrument","rhodes":"instrument","hammond":"instrument","optigan":"instrument","chamberlin":"instrument","fairlight":"instrument","synclavier":"instrument","gretsch":"brand","moog":"brand","oberheim":"brand","korg":"brand","roland":"brand","yamaha":"brand","casio":"brand","arp":"brand","emu":"brand","ppg":"brand","steinway":"brand","broadwood":"brand","ensoniq":"brand","ibanez":"brand","digitech":"brand","selmer":"brand","stradivari":"brand","amati":"brand","guarneri":"brand","808":"model","909":"model","707":"model","606":"model","727":"model","cr-78":"model","cr78":"model","tr-808":"model","tr-909":"model","linndrum":"model","juno":"model","jupiter":"model","minimoog":"model","prophet":"model","dx7":"model","sh-101":"model","ms-20":"model","op-1":"model","volca":"model","leslie":"model","dfam":"model","casiotone":"model","tx81z":"model","drone":"vibe","ambient":"vibe","texture":"vibe","noise":"vibe","fx":"vibe","fm":"vibe","granular":"vibe","glitch":"vibe","lofi":"vibe","vintage":"vibe","cinematic":"vibe","orchestral":"vibe","ethereal":"vibe","atmospheric":"vibe","hybrid":"vibe","world":"vibe","analog":"vibe","soul":"vibe"}'

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
<title>Kontakt Library Catalog</title>
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
 html{--hl-backdrop:rgba(0,0,0,.55);--hl-shadow:0 12px 48px rgba(0,0,0,.45);--accent-patch:#3ecfbf;--accent-patch-bg:rgba(62,207,191,0.18);--accent-patch-active:#7eefe4;--catalog-max:1800px;--ui-base:16px;--ui-scale:1;--search-ui-scale:1;--cat-land-cols:3;--card-chrome-inset:.5rem;--card-chrome-btn:2.75rem;--card-chrome-gap:.5rem;--safe-top:env(safe-area-inset-top,0px);--safe-right:env(safe-area-inset-right,0px);--safe-bottom:env(safe-area-inset-bottom,0px);--safe-left:env(safe-area-inset-left,0px);font-size:calc(var(--ui-base) * var(--ui-scale))}
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
 .clear-miss-btn{flex-shrink:0;box-sizing:border-box;min-height:2.25rem;background:transparent;border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:0 .625rem;font-size:.875rem;cursor:pointer;touch-action:manipulation;white-space:nowrap}
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
 .filter-wrap.open .filter-panel{max-height:calc(100dvh - 24px);overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;padding:clamp(6px,1vw,12px) clamp(8px,1.5vw,16px)}
 body.layout-edit .filter-panel{transition:none}
 body.layout-edit .filter-wrap.open .filter-panel,
 .filter-wrap.kw-shade-height-set.open .filter-panel{max-height:none}
 .toggle-arrow{display:inline-block;transition:transform 0.3s}
 .filter-wrap.open .toggle-arrow{transform:rotate(180deg)}
 .theme-picker{margin-left:0;background:var(--bg-card);color:var(--text-muted);border:1px solid var(--border);border-radius:4px;padding:.25rem .5rem;font-size:.9375rem;cursor:pointer;min-height:2.25rem;max-width:100%}
 .index{column-width:clamp(14rem,28vw,18rem);column-gap:clamp(1rem,2.5vw,2rem);font-size:.9rem}
 .index li{break-inside:avoid;margin:.1rem 0}
 .index a{color:var(--accent-instrument);text-decoration:underline} .index li.hit{background:var(--accent-instrument-bg);border-radius:3px}
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
 .card-chrome-start>.preview-back,.card-chrome-start>.fav-btn,.card-chrome-end>.fs-btn,.card-chrome-end>.hl-close{flex:0 0 auto}
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
 body:is(.hl-open,.gallery-open,.img-focus-open,.desc-reader-open,.path-reader-open,.desc-focus-open,.path-focus-open,.chosen-preview-open,.card-embed-open) .top{visibility:hidden!important;pointer-events:none!important}
 body:is(.hl-open,.gallery-open,.img-focus-open,.desc-reader-open,.path-reader-open,.desc-focus-open,.path-focus-open,.chosen-preview-open,.card-embed-open) :is(.search-chrome,.filter-wrap,.search-ac-shell,.layout-presets-pop,.ui-scale-pop){pointer-events:none!important;z-index:1!important}
 .hl-close{display:none}
 .entry.highlight .hl-close{display:flex;position:absolute;top:max(var(--card-chrome-inset),env(safe-area-inset-top));right:max(var(--card-chrome-inset),env(safe-area-inset-right));z-index:5;width:var(--card-chrome-btn);height:var(--card-chrome-btn);min-width:var(--card-chrome-btn);min-height:var(--card-chrome-btn);font-size:1.375rem;align-items:center;justify-content:center;background:var(--bg-surface);color:var(--text);border:1px solid var(--border);border-radius:8px;cursor:pointer;touch-action:manipulation;line-height:1;padding:0}
 .entry.highlight .hl-close:hover{color:var(--accent-instrument);border-color:var(--accent-instrument)}
 .entry.highlight{position:fixed;inset:0;top:0;left:0;right:0;bottom:0;width:100vw;width:100dvw;height:100vh;height:100dvh;height:100svh;max-width:none;max-height:none;z-index:860;display:flex;flex-direction:column;overflow:hidden;padding:max(52px,calc(env(safe-area-inset-top) + 8px)) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left);box-sizing:border-box;grid-column:unset;transform:none;border-radius:0;outline:2px solid var(--accent-instrument);outline-offset:-2px;background:var(--bg-card);border:1px solid var(--border);box-shadow:var(--hl-shadow)}
 .hl-body{min-width:0}
 .entry.highlight .hl-body{flex:1 1 auto;min-height:0;overflow-y:auto;-webkit-overflow-scrolling:touch;padding:12px 16px 24px}
 .cover{flex-shrink:0;width:100%;max-width:100%;max-height:clamp(7.5rem,18vw,12.5rem);margin:.3rem 0;display:flex;align-items:center;justify-content:center;overflow:hidden;border:1px solid var(--border);border-radius:4px;background:var(--bg-surface);box-sizing:border-box;cursor:pointer}
 .cover img{width:auto;height:auto;max-width:100%;max-height:clamp(7.5rem,18vw,12.5rem);object-fit:contain;object-position:center center;display:block}
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
 .top{position:fixed;bottom:1rem;right:1rem;background:var(--accent-instrument);color:#1a1008;padding:.4rem .7rem;border-radius:4px;text-decoration:none;border:1px solid var(--accent-instrument)}
 .mode-switch{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;max-width:100%}
 .mode-btn{background:var(--bg-card);border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:6px 12px;font-size:.875rem;cursor:pointer;min-height:2.25rem;touch-action:manipulation}
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
 body.search-mode .filter-wrap:not(.open) .filter-top{justify-content:flex-end;border:none;padding:0;min-width:0;max-width:100%;overflow:hidden}
 body.search-mode .filter-wrap:not(.open){width:auto;max-width:calc(100% - .25rem);min-width:0;justify-self:end;flex:0 1 auto;overflow:hidden;padding-right:max(.25rem,env(safe-area-inset-right,0px));box-sizing:border-box}
 body.search-mode .filter-wrap:not(.open) .filter-panel{display:none!important}

 body.search-mode .search-chrome>.search-col,body.search-mode .search-chrome>.filter-wrap{position:relative;z-index:auto}
 /* Fullscreen Search: Back arrow top-left. */
 .ac-fs-back{box-sizing:border-box;flex:0 0 auto;min-width:2.75rem;min-height:2.75rem;margin:0;padding:0;border:1px solid var(--border);border-radius:8px;background:var(--bg-card);color:var(--text);font:inherit;font-size:1.375rem;line-height:1;cursor:pointer;touch-action:manipulation;display:none;align-items:center;justify-content:center}
 body.ac-fs-open .ac-fs-back{display:inline-flex}
 .ac-fs-back:hover{border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 .search-ac-shell.ac-fs .ac-fs-bar{display:flex;align-items:center;gap:.5rem;flex-wrap:nowrap;width:100%;max-width:100%;min-width:0;box-sizing:border-box;overflow:visible}
 body.ac-fs-open .search-strip-fs{display:none!important}
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
 .ac-history-btn{box-sizing:border-box;flex:0 0 auto;min-height:2.75rem;padding:0 .75rem;border:1px solid var(--border);border-radius:8px;background:var(--bg-card);color:var(--text);font:inherit;font-size:.9375rem;font-weight:600;cursor:pointer;touch-action:manipulation;white-space:nowrap}
 .ac-history-btn:hover,.ac-history-btn[aria-expanded="true"]{border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 .ac-history-cloud{position:fixed;z-index:320;box-sizing:border-box;min-width:11rem;max-width:min(16rem,calc(100vw - 1.5rem - env(safe-area-inset-left,0px) - env(safe-area-inset-right,0px)));padding:.75rem .875rem .625rem;border:1px solid var(--border);border-radius:1.35rem;background:var(--bg-card);color:var(--text);box-shadow:0 12px 32px rgba(0,0,0,.38);display:flex;flex-direction:column;gap:.55rem}
 .ac-history-cloud[hidden]{display:none!important}
 .ac-history-cloud::after{content:"";position:absolute;width:.7rem;height:.7rem;background:var(--bg-card);transform:rotate(45deg);pointer-events:none}
 .ac-history-cloud.cloud-below::after{top:-.38rem;left:var(--cloud-tail-x,.75rem);border-left:1px solid var(--border);border-top:1px solid var(--border);border-right:0;border-bottom:0}
 .ac-history-cloud.cloud-above::after{bottom:-.38rem;left:var(--cloud-tail-x,.75rem);border-right:1px solid var(--border);border-bottom:1px solid var(--border);border-left:0;border-top:0}
 .ac-history-ask{margin:0;font-size:.875rem;line-height:1.35;color:var(--text);max-width:100%}
 .ac-history-actions{display:flex;align-items:center;justify-content:flex-end;gap:.45rem}
 .ac-history-yes,.ac-history-no{box-sizing:border-box;min-width:2.75rem;min-height:2.75rem;padding:0;border:1px solid var(--border);border-radius:999px;background:var(--bg-surface);color:var(--text);font:inherit;font-size:1.125rem;line-height:1;cursor:pointer;touch-action:manipulation;display:inline-flex;align-items:center;justify-content:center}
 .ac-history-yes{color:var(--accent-instrument);border-color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 .ac-history-yes:hover{background:var(--accent-instrument);color:var(--bg-card)}
 .ac-history-no:hover{border-color:#c03040;color:#ff9090;background:rgba(180,40,40,0.18)}
 .search-ac-shell.open .ac-fs-bar,.search-ac-shell:has(.search-autocomplete.open) .ac-fs-bar,.search-ac-shell.ac-fs .ac-fs-bar{display:flex;align-items:center;gap:.5rem;flex-wrap:nowrap;width:100%;max-width:100%;min-width:0;box-sizing:border-box;overflow:visible}
 .search-ac-shell:not(.ac-fs) .ac-fs-bar{padding:.375rem .5rem;padding-left:max(.5rem,env(safe-area-inset-left,0px));padding-right:max(.5rem,env(safe-area-inset-right,0px));border-bottom:1px solid var(--border)}
 .ac-fs-bar{display:none;flex:0 0 auto;align-items:center;gap:.5rem;padding:.5rem .75rem;padding-top:max(.5rem,env(safe-area-inset-top,0px));padding-right:max(.75rem,env(safe-area-inset-right,0px));padding-bottom:.5rem;padding-left:max(.75rem,env(safe-area-inset-left,0px));border-bottom:1px solid var(--border);background:var(--bg-surface);z-index:2;box-sizing:border-box;width:100%;max-width:100%;min-width:0;overflow:visible}
 .search-ac-shell.ac-fs{position:fixed;z-index:280;display:flex!important;flex-direction:column;background:var(--bg-surface);overflow:hidden;box-shadow:none;max-width:none;touch-action:manipulation;-webkit-overflow-scrolling:auto}
 .search-ac-shell.ac-fs .ac-fs-bar{display:flex;flex:0 0 auto}
 .ac-fs-close{box-sizing:border-box;min-height:2.75rem;padding:0 1rem;border:1px solid var(--border);border-radius:8px;background:var(--bg-card);color:var(--text);font:inherit;font-size:1rem;cursor:pointer;touch-action:manipulation;white-space:nowrap}
 .ac-fs-close:hover{border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 .search-ac-shell.ac-fs .search-autocomplete,.search-ac-shell.ac-fs .search-autocomplete.open{flex:1 1 0!important;min-height:0!important;max-height:none!important;height:auto!important;overflow-x:hidden!important;overflow-y:scroll!important;-webkit-overflow-scrolling:touch;touch-action:pan-y!important;overscroll-behavior-y:auto;overscroll-behavior-x:none;border:0;width:100%;font-size:1em;pointer-events:auto}
 .search-ac-shell.ac-fs .ac-item,.search-ac-shell.ac-fs .ac-group-label{touch-action:pan-y}
 body.ac-fs-open{overflow:hidden;overscroll-behavior:none}
 body.ac-fs-open .search-ac-shell.ac-fs{pointer-events:auto}
 .search-ac-shell.ac-fs .ac-item{min-height:2.75rem;font-size:1rem;padding:.625rem 1rem}
 .search-ac-shell.ac-fs>.ac-height,.search-ac-shell.ac-fs>.ac-width{display:none!important}
 .ac-height,.kw-shade-height{display:none;box-sizing:border-box;position:absolute;z-index:4;left:0;right:0;bottom:0;width:100%;height:.625rem;min-height:.625rem;max-height:.625rem;margin:0;padding:0;border:0;background:transparent;cursor:row-resize;touch-action:none;-webkit-user-select:none;user-select:none;-webkit-tap-highlight-color:transparent}
 .ac-width{display:none;box-sizing:border-box;position:absolute;z-index:5;top:0;right:0;bottom:0;width:.625rem;min-width:.625rem;max-width:.625rem;height:auto;margin:0;padding:0;border:0;background:transparent;cursor:col-resize;touch-action:none;-webkit-user-select:none;user-select:none;-webkit-tap-highlight-color:transparent}
 .search-ac-shell:has(.search-autocomplete.open)>.ac-height,.search-ac-shell.open>.ac-height{display:block}
 .search-ac-shell:has(.search-autocomplete.open)>.ac-width,.search-ac-shell.open>.ac-width{display:block}
 body.search-mode.kw-open .search-ac-shell>.ac-width,body:not(.search-mode) .search-ac-shell>.ac-width{display:none!important}
 body.search-mode:not(.kw-open) .search-ac-shell.open:not(.ac-fs)>.ac-height,body.search-mode:not(.kw-open) .search-ac-shell:has(.search-autocomplete.open):not(.ac-fs)>.ac-height{right:.625rem;width:auto}
 body:not(.search-mode) .filter-wrap.open>.kw-shade-height{display:block}
 body.search-mode .kw-shade-height,body.search-mode .search-chrome.search-split-ud .kw-shade-height{display:none}
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
 .search-strip-clear{flex-shrink:0;background:transparent;border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:6px 12px;font-size:.9375rem;cursor:pointer;min-height:2.75rem;touch-action:manipulation}
 .search-strip-clear:hover{color:var(--accent-instrument);border-color:var(--accent-instrument)}
 .search-strip-hide{flex-shrink:0;background:transparent;border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:6px 12px;font-size:.9375rem;cursor:pointer;min-height:2.75rem;touch-action:manipulation;white-space:nowrap}
 .search-strip-hide:hover{color:var(--accent-instrument);border-color:var(--accent-instrument)}
 .search-strip-fs{display:none;flex-shrink:0;box-sizing:border-box;background:transparent;border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:6px 10px;font-size:1rem;cursor:pointer;min-height:2.75rem;min-width:2.75rem;touch-action:manipulation;line-height:1;align-items:center;justify-content:center}
 .search-strip-fs:hover,.search-strip-fs[aria-pressed="true"]{color:var(--accent-instrument);border-color:var(--accent-instrument)}
 body.catalog-portable .search-strip-fs,.search-strip-fs.is-mobile{display:inline-flex}
 @media(max-width:899px){.search-strip-fs{display:inline-flex}}
 body.ac-fs-open .search-strip-hide{display:none!important}
 body.ac-fs-open .search-ac-shell.ac-fs .search-strip{display:flex;flex:1 1 auto;min-width:0;width:auto;max-width:100%;margin:0;padding:0;border:0;background:transparent;flex-wrap:nowrap;align-items:center;gap:.5rem;box-sizing:border-box;overflow:visible}
 body.ac-fs-open .search-ac-shell.ac-fs .search-strip input{flex:1 1 auto;min-width:0;width:auto}
 body.ac-fs-open .search-ac-shell.ac-fs .search-strip-clear,
 body.ac-fs-open .search-ac-shell.ac-fs .search-strip-fs{flex:0 0 auto;position:static;max-width:100%}
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
 .search-autocomplete.ac-height-set,.search-autocomplete.ac-height-dragging{max-height:none}
 .search-autocomplete .ac-item{padding:10px clamp(8px,2vw,20px);cursor:pointer;font-size:1rem;color:var(--text);display:flex;justify-content:space-between;min-height:2.75rem;align-items:center;gap:8px}
 .search-autocomplete .ac-item:hover{background:var(--bg-card)}
 .search-autocomplete .ac-item .ac-label{display:flex;align-items:center;gap:8px;min-width:0;flex:1}
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
 .cat-switch{display:flex;flex-wrap:wrap;gap:clamp(4px,0.8vw,8px);margin-bottom:clamp(6px,1.2vw,10px);max-width:100%;box-sizing:border-box}
 .cat-btn{background:var(--bg-card);border:1px solid var(--border);color:var(--text-muted);border-radius:6px;padding:8px 14px;font-size:.9375rem;cursor:pointer;min-height:2.25rem;touch-action:manipulation;white-space:nowrap;transition:background 0.15s,color 0.15s}
 .cat-btn.active{background:var(--accent-instrument-bg);color:var(--accent-instrument);border-color:var(--accent-instrument);font-weight:600}
 .cat-btn[data-cat="patch"].active{background:var(--accent-patch-bg);color:var(--accent-patch);border-color:var(--accent-patch)}
 @media(max-width:899px){body{font-size:1rem}.entry h3{font-size:clamp(1rem,1.15em,1.375rem)}.kw{min-height:2.75rem;font-size:.9375rem;padding:.5rem .875rem}.cat-btn,.mode-btn,.tap-add-btn,.clear-miss-btn,.layout-edit-btn,.layout-presets-btn,.ui-scale-step,.ui-scale-readout,.search-strip-clear,.search-strip-hide,.search-strip-fs,.mode-btn.clear-all{min-height:2.75rem;font-size:.9375rem}.filter-toggle{font-size:.9375rem;min-height:2.75rem}.theme-picker{font-size:.9375rem;min-height:2.25rem}.path,.path code,.path .folder{font-size:.875rem}.summary-panel .desc,.desc{font-size:1rem}.search-popup-btn,.search-link{min-height:2.75rem;font-size:.9375rem}.pill-tag{font-size:.9375rem;min-height:2.75rem}.index{font-size:1rem}}
 @media(orientation:portrait){.filter-panel,.cat-switch,#kwbar,.mode-switch{flex-wrap:wrap;max-width:100%;overflow-x:hidden}.cat-switch{overflow-y:auto;-webkit-overflow-scrolling:touch}body:not(.layout-edit) .filter-wrap:not(.kw-shade-height-set) #kwbar{overflow:visible;max-height:none}.entry.highlight .cover,.entry.highlight .cover img{max-height:min(38dvh,100%)}}
 @media(max-width:899px) and (orientation:landscape){body.search-mode.kw-open .search-strip input{flex:1 1 8rem;min-width:0}}.entry.highlight .cover,.entry.highlight .cover img{max-height:min(32dvh,100%)}#kwbar{flex-wrap:wrap;max-width:100%;overflow-x:auto;overflow-y:hidden;-webkit-overflow-scrolling:touch}.cat-switch{flex-wrap:nowrap;overflow-x:auto;max-width:100%;-webkit-overflow-scrolling:touch}}
 @media(min-width:900px){.entry.highlight .cover,.entry.highlight .cover img{max-width:100%;max-height:min(70dvh,calc(100dvh - 12em));width:auto;height:auto;object-fit:contain;object-position:center center}.entry.highlight .cover img{width:auto;height:auto;max-width:100%;max-height:min(70dvh,calc(100dvh - 12em));object-fit:contain}.entry.highlight .summary-panel .desc{font-size:1.125rem}}
 .search-autocomplete .ac-group-label{padding:4px clamp(8px,2vw,20px) 2px;font-size:.75em;font-weight:700;color:var(--accent-gear);text-transform:uppercase;letter-spacing:.05em}
 .search-autocomplete .ac-group-label[data-cat="patch"]{color:var(--accent-patch)}
 .search-autocomplete .ac-item[data-cat="patch"] .ac-label{color:var(--accent-patch)}
 .search-autocomplete .ac-group-label.ac-fav-label{color:var(--accent-instrument)}
 .search-autocomplete .ac-item.fav-rec{opacity:.72;filter:saturate(.75);background:rgba(0,0,0,.12);box-shadow:inset 0 0 24px rgba(0,0,0,.16);border-left:3px dashed var(--accent-gear)}
 .search-autocomplete .ac-item.fav-rec:hover{opacity:1;filter:none}
</style></head><body>
<div class="catalog-header"><h1 id="top">Kontakt Library Catalog</h1><select id="themePicker" class="theme-picker" onchange="setTheme(this.value)" onclick="event.stopPropagation()"><optgroup label="— Dark —"><option value="desert">Desert Dusk</option><option value="studio">Night Studio</option><option value="smoked">Smoked Glass</option><option value="autumn-ember">Autumn Ember</option><option value="tropical-night">Tropical Night</option><option value="spring-rain">Spring Rain</option><option value="deep-winter">Deep Winter</option></optgroup><optgroup label="— Light —"><option value="sandstorm">Sand Storm</option><option value="bleached">Bleached</option><option value="spring-bloom">Spring Bloom</option><option value="summer-beach">Summer Beach</option><option value="harvest">Harvest</option><option value="arctic">Arctic</option></optgroup><optgroup label="— High Contrast —"><option value="hc-dark">HC Dark</option><option value="hc-light">HC Light</option></optgroup></select></div>
HTML
  printf '<p>generated: %s</p>\n' "$(e "$(date)")"
  if [ "$MODE" = portable ]; then
    printf '<p>Portable snapshot (banners embedded; phone-safe). Registered Kontakt libraries; click a name to jump. <b>Update:</b> on desktop re-run <code>build-kontakt-catalog-html.sh both</code> and re-transfer this file.</p>\n'
  else
    printf '<p>Registered Kontakt libraries (from komplete.db3). Click a name to jump; [open folder] opens the library in Dolphin. <b>Added libraries?</b> Re-run <code>build-kontakt-catalog-html.sh both</code>.</p>\n'
  fi
  echo '<div class="search-chrome" id="searchChrome"><div class="search-col" id="searchCol"><div class="search-strip-anchor"><div class="search-strip" id="searchStrip"><input id="searchInput" type="text" placeholder="Search libraries..." autocomplete="off"><button type="button" class="search-strip-hide" onclick="toggleSearchChrome()" aria-expanded="true">Hide search</button><button type="button" class="search-strip-clear" onclick="clearAllFilters()">Clear</button><button type="button" class="search-strip-fs" id="searchStripFs" onclick="toggleAcFullscreen()" aria-pressed="false" aria-label="Fullscreen search" title="Fullscreen search">&#x26F6;</button><div class="ui-scale search-only-scale" id="searchOnlyScale"><button type="button" class="ui-scale-step" id="searchOnlyScaleDown" aria-label="Smaller Search">−</button><button type="button" class="ui-scale-readout" id="searchOnlyScaleReadout" aria-expanded="false" aria-haspopup="true" title="Search scale">100%</button><button type="button" class="ui-scale-step" id="searchOnlyScaleUp" aria-label="Larger Search">+</button><div class="ui-scale-pop" id="searchOnlyScalePop" hidden></div></div></div><div class="search-ac-shell" id="acShell"><div class="ac-fs-bar" id="acFsBar"><button type="button" class="ac-fs-back" id="acFsBack" aria-label="Back" title="Back" onclick="event.preventDefault();event.stopPropagation();setAcFullscreen(false)">&#x2190;</button><div class="ac-history-wrap" id="searchHistoryWrap"><button type="button" class="ac-history-btn" id="searchHistory" aria-haspopup="dialog" aria-expanded="false" aria-controls="historyCloud" title="History">History</button><div class="ac-history-cloud" id="historyCloud" hidden role="dialog" aria-label="Clear search history"><p class="ac-history-ask">Clear search history?</p><div class="ac-history-actions"><button type="button" class="ac-history-yes" id="historyYes" aria-label="Yes, clear history" title="Clear">&#x2713;</button><button type="button" class="ac-history-no" id="historyNo" aria-label="No, keep history" title="Keep">&#x2715;</button></div></div></div></div><div class="search-autocomplete" id="acList"></div><button type="button" class="ac-height" id="acHeight" aria-label="Resize search suggestions" aria-orientation="horizontal" tabindex="-1"></button><button type="button" class="ac-width" id="acWidth" aria-label="Resize search suggestions width" aria-orientation="vertical" tabindex="-1"></button></div></div><div class="search-active-pills" id="searchPills"></div></div>'
  echo '<button type="button" class="search-split" id="searchSplit" aria-label="Resize Search and Keywords" aria-orientation="vertical" tabindex="-1"></button>'
  echo '<div class="filter-wrap" id="filterWrap"><div class="filter-top"><button class="filter-toggle" id="filterToggle" onclick="toggleFilter()" aria-expanded="false"><span class="toggle-arrow">&#9660;</span> Keywords</button></div><div class="filter-panel" id="filterPanel"><div class="filter-kw-tools" id="filterKwTools"><button type="button" class="clear-miss-btn" id="clearMissBtn" aria-pressed="false" title="When leaving the image gallery on a library outside the current Search hits, clear Search." onclick="event.preventDefault();event.stopPropagation();toggleClearOnMiss()">Clear on miss</button><button type="button" class="layout-edit-btn" id="layoutEditBtn" aria-pressed="false" title="Drag menu edges to resize. Lock when finished." onclick="event.preventDefault();event.stopPropagation();toggleLayoutEdit()">Edit layout</button><button type="button" class="layout-default-btn" id="layoutDefaultBtn" title="Reset layout sizes to defaults." onclick="event.preventDefault();event.stopPropagation();resetLayoutDefaults()">Default</button><div class="layout-presets" id="layoutPresets"><button type="button" class="layout-presets-btn" id="layoutPresetsBtn" aria-expanded="false" aria-haspopup="true" title="Save and apply named menu layouts">Layouts</button><div class="layout-presets-pop" id="layoutPresetsPop" hidden><div class="layout-presets-tabs" role="tablist" aria-label="Layout store"><button type="button" class="layout-presets-tab" id="layoutTabKeywords" data-layout-scope="keywords" role="tab" aria-selected="true">Search + Keywords</button><button type="button" class="layout-presets-tab" id="layoutTabSearch" data-layout-scope="search" role="tab" aria-selected="false">Search</button></div><p class="layout-presets-store" id="layoutPresetsStoreLabel">Search + Keywords</p><div class="layout-presets-list" id="layoutPresetsList"></div><div class="layout-presets-save"><input id="layoutPresetsName" type="text" maxlength="40" placeholder="Name (e.g. Studio)" autocomplete="off"><button type="button" id="layoutPresetsSave">Save Keywords layout</button><button type="button" id="layoutPresetsUpdate">Update Keywords layout</button><p class="layout-presets-flash" id="layoutPresetsFlash" aria-live="polite"></p></div></div><div class="ui-scale" id="uiScale"><button type="button" class="ui-scale-step" id="uiScaleDown" aria-label="Smaller UI">−</button><button type="button" class="ui-scale-readout" id="uiScaleReadout" aria-expanded="false" aria-haspopup="true" title="Interface scale">100%</button><button type="button" class="ui-scale-step" id="uiScaleUp" aria-label="Larger UI">+</button><div class="ui-scale-pop" id="uiScalePop" hidden></div></div></div></div><div class="mode-switch"><button class="mode-btn active" data-mode="shade" onclick="setMode(this.dataset.mode)">Shade</button><button class="mode-btn" data-mode="search" onclick="setMode(this.dataset.mode)">Search</button><button type="button" class="tap-add-btn" id="tapAddBtnPanel" aria-pressed="false" onclick="toggleTapToAdd()">Tap to add</button><button type="button" class="mode-btn clear-all" onclick="clearAllFilters()">Clear</button></div><div class="cat-switch" id="catSwitch"><button class="cat-btn active" data-cat="all" onclick="setCat(this.dataset.cat)">All</button><button class="cat-btn" data-cat="instrument" onclick="setCat(this.dataset.cat)">Instrument</button><button class="cat-btn" data-cat="brand" onclick="setCat(this.dataset.cat)">Brand</button><button class="cat-btn" data-cat="model" onclick="setCat(this.dataset.cat)">Model</button><button class="cat-btn" data-cat="vibe" onclick="setCat(this.dataset.cat)">Vibe</button><button class="cat-btn" data-cat="patch" onclick="setCat(this.dataset.cat)">Patch</button></div><div id="kwbar"></div><p id="kwstatus" class="kwstatus"></p></div><button type="button" class="kw-shade-height" id="kwShadeHeight" aria-label="Resize Keywords height" aria-orientation="horizontal" tabindex="-1"></button></div><button type="button" class="search-height" id="searchHeight" aria-label="Resize Search height" aria-orientation="horizontal" tabindex="-1"></button></div>'
  echo '<h2>Index (alphabetical)</h2><ul class="index">'
  sort -f "$IDX" | uniq
  echo '</ul>'
  echo '<div class="catalog-body">'
  echo '<div class="fav-recs-label">Favorites</div>'
  cat "$BODY"
  echo '</div>'
  echo '<a class="top" href="#top">&uarr; top</a>'
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
    <span class="card-search-title" id="cardSearchTitle">Search</span>
    <button type="button" class="card-search-switch-toggle" id="cardSearchSwitchToggle" aria-label="Hide mode bar" aria-pressed="true" title="Hide mode bar" onclick="event.preventDefault();event.stopPropagation();cardSearchToggleSwitchBar()">
      <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.2" y="15.2" width="17.6" height="4.4" rx="1.4" fill="none" stroke="currentColor" stroke-width="1.6"/><rect x="5" y="16.6" width="3.2" height="1.6" rx=".4" fill="currentColor"/><rect x="10.4" y="16.6" width="3.2" height="1.6" rx=".4" fill="currentColor"/><rect x="15.8" y="16.6" width="3.2" height="1.6" rx=".4" fill="currentColor"/><path d="M6 5.5h12M6 9h12M6 12.5h8" fill="none" stroke="currentColor" stroke-width="1.45" stroke-linecap="round"/></svg>
    </button>
    <button type="button" class="card-search-popup" onclick="event.preventDefault();event.stopPropagation();cardSearchOpenPopup()">Open in popup</button>
  </div>
  <div class="card-search-stage" id="cardSearchStage">
    <div class="card-search-hint" id="cardSearchHint" hidden role="status" aria-live="polite">
      <p class="card-search-hint-text">If this embed doesn&rsquo;t work, use <strong>Open in popup</strong>.</p>
      <button type="button" class="card-search-hint-x" aria-label="Dismiss" onclick="event.preventDefault();event.stopPropagation();cardSearchDismissEmbedHint()">×</button>
    </div>
    <iframe class="card-search-frame" id="cardSearchFrame" title="Library search" allowfullscreen referrerpolicy="strict-origin-when-cross-origin" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen"></iframe>
    <div class="card-yt-comments" id="cardYtComments">
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
    b.textContent=collapsed?'Search':'Hide search';
    b.setAttribute('aria-expanded',collapsed?'false':'true');
    b.setAttribute('aria-label',collapsed?'Search':'Hide search');
  });
  var w=document.getElementById('filterWrap');
  var t=document.getElementById('filterToggle');
  var kwOpen=!!(w&&w.classList.contains('open'));
  document.body.classList.toggle('kw-open',kwOpen);
  document.body.classList.toggle('menus-collapsed',!!collapsed&&!kwOpen);
  if(t)t.setAttribute('aria-expanded',kwOpen?'true':'false');
  if(window.syncLayoutStoreUi)window.syncLayoutStoreUi();
  if(window.syncSearchSplit)window.syncSearchSplit();
}
function toggleFilter(){
  var w=document.getElementById('filterWrap'),a=document.querySelector('.toggle-arrow');
  if(!w)return;
  var ac=document.getElementById('acList');
  var keepAc=!!(ac&&ac.classList.contains('open'));
  w.classList.toggle('open');
  var open=w.classList.contains('open');
  if(a)a.textContent=open?'▲':'▼';
  syncSearchHideBtn();
  if(open&&typeof window.restoreFilterUi==='function')window.restoreFilterUi();
  if(keepAc&&ac)ac.classList.add('open');
  if(typeof window.applyActiveLayoutStore==='function'){
    window.applyActiveLayoutStore();
    requestAnimationFrame(function(){window.applyActiveLayoutStore();});
  }else if(window.syncSearchSplit)window.syncSearchSplit();
}
function collapseSearchMenu(){
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
}
window.collapseSearchMenu=collapseSearchMenu;
function expandSearchMenu(){
  acFsWanted=false;
  if(typeof parkSearchStrip==='function')parkSearchStrip();
  if(typeof syncAcFsBtn==='function')syncAcFsBtn();
  document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed');
  syncSearchHideBtn();
  if(typeof window.applyActiveLayoutStore==='function'){
    window.applyActiveLayoutStore();
    requestAnimationFrame(function(){window.applyActiveLayoutStore();});
  }else if(typeof window.restoreSearchUi==='function')window.restoreSearchUi();
  var si=document.getElementById('searchInput');
  if(si)setTimeout(function(){si.focus();},50);
}
function toggleSearchChrome(){
  if(document.body.classList.contains('search-chrome-collapsed')) expandSearchMenu();
  else collapseSearchMenu();
}
function syncLayoutEditBtn(){
  var on=document.body.classList.contains('layout-edit');
  document.querySelectorAll('.layout-edit-btn').forEach(function(b){
    b.textContent=on?'Lock layout':'Edit layout';
    b.setAttribute('aria-pressed',on?'true':'false');
  });
}
function toggleLayoutEdit(){
  var was=document.body.classList.contains('layout-edit');
  document.body.classList.toggle('layout-edit');
  if(was&&typeof persistAllLiveLayouts==='function')persistAllLiveLayouts();
  syncLayoutEditBtn();
  if(window.syncSearchSplit)window.syncSearchSplit();
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
  // Error 153 = missing HTTP Referer (Google YT terms). Prefer www.youtube.com; keep meta/iframe referrerpolicy.
  host=String(host||cardSearchState._ytHost||'youtube');
  if(host!=='nocookie')host='youtube';
  opts=opts||{};
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
  if(!/(?:youtube(?:-nocookie)?\.com)\/embed\/[A-Za-z0-9_-]{6,}/.test(s))return true;
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
  if(!cardSearchYtCanEmbedHere()){
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
  cardSearchState._ytHost=String(host||cardSearchState._ytHost||'youtube')==='nocookie'?'nocookie':'youtube';
  cardSearchState.embedUrl=url;
  cardSearchState.history=[url];
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
  // Prefer IFrame API when already available (reliable onError for 153).
  // Otherwise plain embed + postMessage; preload API for the next play.
  if(window.YT&&YT.Player)mountApi();
  else{
    mountPlain();
    cardSearchEnsureYtApi(function(){});
  }
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
    if(!setCardYtFrame(pick.id,'youtube'))cardSearchYtTryNext('bad id');
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
    if(thumb){
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
    cardSearchShowYtBlocked('file:// or null origin — YouTube needs HTTP(S) Referer');
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
  cardSearchState.history=['results','article'];
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
  cardSearchState.history=[cardSearchState.view];
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
  cardSearchState.history=['grid'];
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
  cardSearchState.history=['grid','image'];
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
  var imgView=document.getElementById('cardSearchImgView');
  if(imgView&&imgView.classList.contains('open')){
    window.cardSearchExitImage();
    return;
  }
  if(cardSearchState.type!=='yt'&&cardSearchState.view==='article'){
    cardSearchShowWebResults();
    return;
  }
  var frame=document.getElementById('cardSearchFrame');
  if(frame&&cardSearchState.type==='yt'&&!frame.classList.contains('is-hidden')){
    try{
      if(frame.contentWindow&&frame.contentWindow.history&&frame.contentWindow.history.length>1){
        frame.contentWindow.history.back();
        return;
      }
    }catch(err){}
    if(cardSearchState.history.length>1){
      cardSearchState.history.pop();
      var url=cardSearchState.history[cardSearchState.history.length-1];
      cardSearchState.embedUrl=url;
      frame.src=url;
      cardSearchEnableBack();
      return;
    }
  }
  closeCardSearchEmbed();
};
window.cardSearchReload=function(){
  cardSearchEnableBack();
  if(cardSearchState.type==='yt'){
    loadCardYtSearch(cardSearchState.query);
    return;
  }
  if(cardSearchState.type==='img'){
    window.cardSearchExitImage();
    loadCardImageSearch(cardSearchState.query);
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
window.syncCardSearchTheme=function(){
  if(!document.body.classList.contains('card-embed-open')||!cardSearchState.popupUrl)return;
  if(cardSearchState.type==='yt'){
    var next=cardSearchYtEmbedUrl(cardSearchState.popupUrl,cardSearchState.query);
    if(next===cardSearchState.embedUrl)return;
    cardSearchState.embedUrl=next;
    cardSearchState.history=[next];
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
  if(yt)fillYtCommentsStrip();
}
window.syncCardSearchLayout=syncCardSearchLayout;
window.cardSearchExitImage=function(){
  var view=document.getElementById('cardSearchImgView');
  var img=document.getElementById('cardSearchImgFit');
  if(view)view.classList.remove('open');
  if(img){img.removeAttribute('src');img.alt='';}
  cardSearchState.view='grid';
  cardSearchState.history=['grid'];
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
 window.setCat=function(cat){if(cat==='other')cat='all';activeCat=cat;document.querySelectorAll('.cat-btn').forEach(function(b){b.classList.toggle('active',b.dataset.cat===cat);});if(currentMode==='search')applySearch();else render();};
 /* --- mode switcher --- */
 var currentMode='shade';
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
     b.onclick=function(){if(currentMode==='search')window.removeSearchKw(k);else{sel=sel.filter(function(x){return x!==k;});render();}};
     if(currentMode!=='search'&&activeCat!=='all'&&(asPatch?'patch':kwCat(k))!==activeCat){b.style.opacity='0.3';b.style.pointerEvents='none';}
     bar.appendChild(b);
   });
   if(activeCat==='patch'){
     var pcounts={};
     hits.forEach(function(el){patches(el).forEach(function(k){if(active.indexOf(k)<0&&usefulPatchToken(k))pcounts[k]=(pcounts[k]||0)+1;});});
     Object.keys(pcounts).sort(function(a,b){return (pcounts[b]-pcounts[a])||(a<b?-1:a>b?1:0);}).slice(0,PATCH_BAR_CAP).forEach(function(k){
       var c=pcounts[k]||0;if(hideZero&&c<1)return;
       var b=document.createElement('button');b.className='kw'+(c>0?'':' disabled')+' patch';b.setAttribute('data-cat','patch');b.setAttribute('data-src','patch');b.setAttribute('data-kw',k);b.textContent=k+' ('+c+')';
       if(c>0)b.onclick=function(){if(currentMode==='search')return;sel.push(k);render();};else b.disabled=true;
       bar.appendChild(b);
     });
   }else{
     ALL.forEach(function(k){if(active.indexOf(k)>=0)return;var c=counts[k]||0;if(hideZero&&c<1)return;var b=document.createElement('button');
       b.className='kw'+(c>0?'':' disabled')+kwTone(k,false);b.setAttribute('data-cat',kwCat(k));b.setAttribute('data-kw',k);b.textContent=k+' ('+c+')';
       if(c>0)b.onclick=function(){if(currentMode==='search')return;sel.push(k);render();};else b.disabled=true;
       if(currentMode!=='search'&&activeCat!=='all'&&kwCat(k)!==activeCat){b.style.opacity='0.3';b.style.pointerEvents='none';}bar.appendChild(b);});
   }
   var cl=document.createElement('button');cl.className='kw clear';cl.textContent='Clear';
   cl.onclick=function(){window.clearAllFilters();};bar.appendChild(cl);
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
   if(mode==='hide')mode='shade';
   if(currentMode==='hide')currentMode='shade';
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
     if(chrome&&chrome.scrollIntoView)try{chrome.scrollIntoView({block:'start'});}catch(err){}
     if(typeof window.restoreSearchUi==='function')window.restoreSearchUi();
     if(typeof window.applyActiveLayoutStore==='function')window.applyActiveLayoutStore();
     setTimeout(function(){var si=document.getElementById('searchInput');if(si)si.focus();},50);
     syncTapToAddBtns();
     return;
   }
   currentMode=mode;
   document.querySelectorAll('.mode-btn').forEach(function(b){b.classList.toggle('active',b.dataset.mode===mode);});
   document.body.classList.toggle('search-mode',mode==='search');
   document.body.classList.remove('search-extras-collapsed','search-chrome-collapsed');if(window.syncSearchHideBtn)window.syncSearchHideBtn();
   if(typeof window.applyActiveLayoutStore==='function')window.applyActiveLayoutStore();
   if(mode==='search'){renderPills();applySearch();if(typeof window.restoreSearchUi==='function')window.restoreSearchUi();setTimeout(function(){var si=document.getElementById('searchInput');if(si)si.focus();},50);}
   else{entries.forEach(function(el){el.style.display='';el.classList.remove('dim','is-hidden','fav-rec');});document.body.classList.remove('search-empty-recs');render();}
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
 function acHtml(list,cap,hint){
   var groups={};CAT_ORDER.forEach(function(c){groups[c]=[];});
   list.forEach(function(o){var c=o.cat||kwCat(o.k);if(groups[c])groups[c].push(o);});
   if(groups.patch)groups.patch=sortOther(groups.patch);
   var picked={};CAT_ORDER.forEach(function(c){picked[c]=[];});
   if(hint){
     CAT_ORDER.forEach(function(c){picked[c]=groups[c].slice(0,2);});
   }else{
     var used=0,lim=cap||9999;
     CAT_ORDER.forEach(function(c){if(groups[c].length){picked[c].push(groups[c][0]);used++;}});
     CAT_ORDER.forEach(function(c){for(var i=1;i<groups[c].length&&used<lim;i++){picked[c].push(groups[c][i]);used++;}});
   }
   var html='';
   CAT_ORDER.forEach(function(c){
     if(!picked[c].length)return;
     html+='<div class="ac-group-label" data-cat="'+c+'">'+CAT_LABEL[c]+'</div>';
     picked[c].forEach(function(o){
       html+='<div class="ac-item'+(o.isFav||(o.label&&favSet[o.label])?' fav-rec':'')+'" data-cat="'+c+'" onclick="pickAc(\''+jsStr(o.label||o.k)+'\')"><span class="ac-label">'+htmlStr(o.label||o.k)+acNoteIcon(o)+'</span> <span class="ac-count">'+o.c+'</span></div>';
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
   text=String(text||'').trim().toLowerCase();
   if(!text)return;
   var seen={};
   text.split(/[\s,;/|]+/).forEach(function(t){
     t=String(t||'').replace(/^[^\w]+|[^\w]+$/g,'').toLowerCase();
     if(!t||seen[t]||t.length<3)return;
     if(typeof PATCH_STOP!=='undefined'&&PATCH_STOP[t])return;
     if(typeof usefulPatchToken==='function'&&!usefulPatchToken(t)&&!(typeof kwCounts!=='undefined'&&kwCounts[t]))return;
     seen[t]=1;
     searchCommitCounts[t]=(searchCommitCounts[t]||0)+1;
   });
   persistSearchCommits();
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
     html+='<div class="ac-group-label ac-fav-label">Favorites</div>';
     favNames.forEach(function(o){
       html+='<div class="ac-item fav-rec" data-cat="fav" onclick="pickAc(\''+jsStr(o.label||o.k)+'\')"><span class="ac-label">'+htmlStr(o.label||o.k)+acNoteIcon(o)+'</span></div>';
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
 function showAc(q,opts){
   opts=opts||{};
   if(document.body.classList.contains('search-extras-collapsed')){if(acList){acList.classList.remove('open');acList.innerHTML='';}return;}
   if(typeof overlayCoversSearch==='function'&&overlayCoversSearch()){if(acList){acList.classList.remove('open');acList.innerHTML='';}if(typeof window.hideSearchAc==='function')window.hideSearchAc();return;}
   var src=suggestFromHits();
   var list=q?src.filter(function(o){return o.k.indexOf(q)>=0||(o.label&&o.label.toLowerCase().indexOf(q)>=0);}):src;
   if(q&&q.length>=2){
     suggestPatchNames(q,currentHits(),16).forEach(function(o){
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
   var mainHtml=acHtml(list,40,!q);
   var favHtml=favAcHtml(favs,ranked);
   var hasMain=mainHtml.length>0;
   var hasCommits=(ranked||[]).some(function(o){return o&&o.searchCommits>0;});
   // Never open the dropdown solely to dump favorite suggestions.
   if(!q&&!hasMain&&!hasCommits&&!opts.force){
     if(acList){acList.innerHTML='';acList.classList.remove('open');}
     if(window.syncSearchSplit)window.syncSearchSplit();
     return;
   }
   var html=(hasMain||hasCommits||!!q||opts.force)?(favHtml+mainHtml):'';
   acList.innerHTML=html;acList.classList.toggle('open',html.length>0);
   if(window.syncSearchSplit)window.syncSearchSplit();
 }
 window.showAc=showAc;
 searchInput.addEventListener('input',function(){
   var q=searchInput.value.trim().toLowerCase();
   showAc(q);
   applySearch();
 });
 searchInput.addEventListener('focus',function(){if(document.body.classList.contains('search-extras-collapsed'))return;if(typeof overlayCoversSearch==='function'&&overlayCoversSearch()){searchInput.blur();return;}showAc(searchInput.value.trim().toLowerCase());});
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
commitSearchTokens(text);
if(acList){acList.classList.remove('open');acList.innerHTML='';}
if(window.CATALOG_PORTABLE||(window.matchMedia&&window.matchMedia('(max-width:899px)').matches)){
  searchInput.blur();
  if(typeof window.hideSearchAc==='function')window.hideSearchAc();
}
applySearch();
};
 window.addSearchKw=function(kw){
   if(!kw||searchKeywords.indexOf(kw)>=0)return;
   if(!isRemainingHitKw(kw))return;
   searchKeywords.push(kw);renderPills();applySearch();
   searchInput.value='';acList.classList.remove('open');};
 window.removeSearchKw=function(kw){searchKeywords=searchKeywords.filter(function(k){return k!==kw;});renderPills();applySearch();};
 function renderPills(){var html=searchKeywords.map(function(k){var cls='pill-tag'+(isPatchKw(k)?' patch':'');return '<span class="'+cls+'"><span class="pill-label">'+htmlStr(k)+'</span><button type="button" class="pill-x" aria-label="Remove '+htmlStr(k)+'" onclick="event.preventDefault();event.stopPropagation();removeSearchKw(\''+jsStr(k)+'\')">\u00d7</button></span>';}).join('');document.querySelectorAll('#searchPills,.search-active-pills').forEach(function(c){c.innerHTML=html;});}
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
function shadeOn(){var w=wrap();return !!(w&&w.classList.contains('open')&&!document.body.classList.contains('search-mode'));}
function readRatio(axis){
  try{
    var n=parseFloat(localStorage.getItem(splitRatioKey(axis)));
    return (isFinite(n)&&n>0&&n<1)?n:null;
  }catch(err){return null;}
}
function writeRatio(axis,ratio){
  try{localStorage.setItem(splitRatioKey(axis),String(ratio));}catch(err){}
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
      kwNeed+=Math.min((cs&&(cs.scrollHeight||cs.offsetHeight))||0,3.25*rem());
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
function acFsAvailable(){
  if(window.CATALOG_PORTABLE)return true;
  try{return window.matchMedia('(max-width:899px)').matches;}catch(err){return false;}
}
function acFullscreen(){return !!acFsWanted;}
function parkSearchStrip(){
  var strip=document.getElementById('searchStrip');
  var bar=document.getElementById('acFsBar');
  var sh=acShell();
  var anchor=document.querySelector('.search-strip-anchor');
  var back=document.getElementById('acFsBack');
  if(!strip)return;
  if(acFsWanted){
    if(bar&&strip.parentNode!==bar){
      var hist=document.getElementById('searchHistoryWrap');
      if(hist&&hist.parentNode===bar)bar.insertBefore(strip,hist);
      else if(back&&back.parentNode===bar)bar.insertBefore(strip,back.nextSibling);
      else bar.appendChild(strip);
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
  sh.classList.remove('ac-fixed','ac-fs');
  document.body.classList.remove('ac-fs-open');
  ['top','left','right','bottom','width','height','max-width','max-height'].forEach(function(p){sh.style.removeProperty(p);});
}
function placeAcShell(){
  var sh=acShell();
  if(!sh)return;
  syncAcFsBtn();
  parkSearchStrip();
  if(!acOpen()){clearAcShellPos(sh);syncAcWidthBtn();return;}
  var box=viewBox();
  var r=layoutRem();
  if(acFullscreen()){
    sh.classList.add('ac-fixed','ac-fs');
    document.body.classList.add('ac-fs-open');
    sh.style.top=Math.round(box.top)+'px';
    sh.style.left=Math.round(box.left)+'px';
    sh.style.right='auto';
    sh.style.bottom='auto';
    sh.style.width=Math.round(box.width)+'px';
    sh.style.height=Math.round(box.height)+'px';
    sh.style.maxWidth='none';
    sh.style.maxHeight=Math.round(box.height)+'px';
    syncAcWidthBtn();
    return;
  }
  sh.classList.remove('ac-fs');
  document.body.classList.remove('ac-fs-open');
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
  if(acFsAvailable())maxH=Math.min(maxH,Math.max(6*r,0.5*box.height));
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
  if(!ac||!acOpen()){
    if(ac&&!adrag)clearAcBox(ac);
    if(b)b.setAttribute('aria-hidden','true');
    syncAcWidthBtn();
    return;
  }
  if(acFullscreen()){
    if(!adrag){
      // Keep #acList as the only scrollport; size it to shell minus chrome so it always scrolls.
      clearAcBox(ac);
      var bar=document.getElementById('acFsBar');
      var shEl=sh||acShell();
      var shH=(shEl&&shEl.getBoundingClientRect().height)||viewBox().height||0;
      var barH=(bar&&bar.getBoundingClientRect().height)||0;
      var h=Math.max(96,Math.floor(shH-barH));
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
  if(!b||!ac||!acOpen()||!layoutEdit()||acFullscreen())return;
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
  need+=(ms&&(ms.offsetHeight||ms.scrollHeight))||2.5*rem();
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
var layoutUiScope=null;
function defaultLayoutScope(){return searchOnlyStore()?'search':'keywords';}
function activeLayoutScope(){
  if(layoutUiScope!=='search'&&layoutUiScope!=='keywords')layoutUiScope=defaultLayoutScope();
  return layoutUiScope;
}
function layoutScopeSo(scope){return (scope||activeLayoutScope())==='search';}
function layoutScopeLabel(so){return so?'Search':'Search + Keywords';}
function layoutMapKeyFor(so){return so?KEYMAPSO:KEYMAP;}
function layoutLastKeyFor(so){return so?KEYLASTSO:KEYLAST;}
function layoutMapKey(){return layoutMapKeyFor(layoutScopeSo());}
function layoutLastKey(){return layoutLastKeyFor(layoutScopeSo());}

function persistAllLiveLayouts(){
  try{if(typeof persist==='function')persist();}catch(err){}
  try{if(typeof persistHeight==='function')persistHeight();}catch(err){}
  try{if(typeof persistAcHeight==='function')persistAcHeight();}catch(err){}
  try{if(typeof persistAcWidth==='function')persistAcWidth();}catch(err){}
  try{if(typeof persistShadeHeight==='function')persistShadeHeight();}catch(err){}
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
function resetLayoutDefaults(){
  var so=searchOnlyStore();
  clearLiveLayoutKeys(so);
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
  return true;
}
window.persistAllLiveLayouts=persistAllLiveLayouts;
window.resetLayoutDefaults=resetLayoutDefaults;

function snapshotLayout(so){
  if(so==null)so=searchOnlyStore();
  if(so){
    return {
      kind:'search-only',
      ch:localStorage.getItem(KEYCH),
      cv:localStorage.getItem(KEYCV),
      ac:localStorage.getItem(KEYACSO),
      acw:localStorage.getItem(KEYACWSO)
    };
  }
  return {
    kind:'together',
    h:localStorage.getItem(KEYH),
    v:localStorage.getItem(KEYV),
    htL:localStorage.getItem(KEYHT+'-l'),
    htP:localStorage.getItem(KEYHT+'-p'),
    ac:localStorage.getItem(KEYAC),
    sh:localStorage.getItem(KEYSH),
    scale:currentUiScale()
  };
}
function writeSnapKey(k,v){
  if(v==null||v==='')localStorage.removeItem(k);
  else localStorage.setItem(k,String(v));
}
function applySnapshot(snap,so){
  if(!snap)return;
  if(so==null)so=snap.kind==='search-only';
  if(so){
    writeSnapKey(KEYCH,snap.ch);writeSnapKey(KEYCV,snap.cv);
    writeSnapKey(KEYACSO,snap.ac);writeSnapKey(KEYACWSO,snap.acw);
  }else{
    writeSnapKey(KEYH,snap.h);writeSnapKey(KEYV,snap.v);
    writeSnapKey(KEYHT+'-l',snap.htL);writeSnapKey(KEYHT+'-p',snap.htP);
    writeSnapKey(KEYAC,snap.ac);writeSnapKey(KEYSH,snap.sh);
  }
  applyAll();
}
function readLayoutsFor(so){
  try{
    var o=JSON.parse(localStorage.getItem(layoutMapKeyFor(so))||'{}');
    return (o&&typeof o==='object'&&!Array.isArray(o))?o:{};
  }catch(err){return {};}
}
function writeLayoutsFor(so,map){try{localStorage.setItem(layoutMapKeyFor(so),JSON.stringify(map));}catch(err){}}
function readLayouts(){return readLayoutsFor(layoutScopeSo());}
function writeLayouts(map){writeLayoutsFor(layoutScopeSo(),map);}
function lastLayoutNameFor(so){try{return localStorage.getItem(layoutLastKeyFor(so))||'';}catch(err){return '';}}
function setLastLayoutNameFor(so,n){try{if(n)localStorage.setItem(layoutLastKeyFor(so),n);else localStorage.removeItem(layoutLastKeyFor(so));}catch(err){}}
function lastLayoutName(){return lastLayoutNameFor(layoutScopeSo());}
function setLastLayoutName(n){setLastLayoutNameFor(layoutScopeSo(),n);}
function syncLayoutScopeUi(){
  var so=layoutScopeSo();
  var btn=document.getElementById('layoutPresetsBtn');
  if(btn){
    btn.textContent='Layouts';
    btn.title='Save and apply Search + Keywords or independent Search layouts';
  }
  var inp=document.getElementById('layoutPresetsName');
  if(inp)inp.placeholder=so?'Name (e.g. Slim)':'Name (e.g. Studio)';
  var save=document.getElementById('layoutPresetsSave');
  var upd=document.getElementById('layoutPresetsUpdate');
  if(save)save.textContent=so?'Save Search layout':'Save Keywords layout';
  if(upd)upd.textContent=so?'Update Search layout':'Update Keywords layout';
  document.querySelectorAll('.layout-presets-tab').forEach(function(t){
    var on=t.getAttribute('data-layout-scope')===activeLayoutScope();
    t.classList.toggle('is-active',on);
    t.setAttribute('aria-selected',on?'true':'false');
  });
  var lab=document.getElementById('layoutPresetsStoreLabel');
  if(lab)lab.textContent=layoutScopeLabel(so);
  var pop=document.getElementById('layoutPresetsPop');
  if(pop&&!pop.hidden)renderLayoutList();
}
function syncLayoutStoreUi(){
  layoutUiScope=defaultLayoutScope();
  syncLayoutScopeUi();
}
window.syncLayoutStoreUi=syncLayoutStoreUi;
function setLayoutUiScope(scope){
  layoutUiScope=scope==='search'?'search':'keywords';
  var so=layoutScopeSo();
  var inp=document.getElementById('layoutPresetsName');
  if(inp)inp.value=lastLayoutNameFor(so);
  syncLayoutScopeUi();
}
function readNamedMap(so){
  return readLayoutsFor(!!so);
}
function readLastNamed(so){
  return lastLayoutNameFor(!!so);
}
function uniqueLayoutName(base,so){
  if(so==null)so=layoutScopeSo();
  var map=readLayoutsFor(so);
  base=String(base||(so?'Search':'Keywords')).replace(/^\s+|\s+$/g,'').slice(0,32)||(so?'Search':'Keywords');
  if(!map[base])return base;
  var i=2,n;
  do{n=base+' '+i;i++;}while(map[n]);
  return n.slice(0,40);
}
function applyActiveLayoutStore(){
  syncLayoutStoreUi();
  var so=searchOnlyStore();
  var last=readLastNamed(so);
  if(last){
    var map=readNamedMap(so);
    if(map[last]){applySnapshot(map[last],so);return;}
  }
  applyAll();
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
  var so=layoutScopeSo();
  var map=readLayoutsFor(so);
  var names=Object.keys(map).sort(function(a,b){return a.localeCompare(b);});
  var last=lastLayoutNameFor(so);
  var html='';
  if(!names.length){list.innerHTML='<p class="layout-presets-empty" style="margin:0 0 6px;color:var(--text-muted);font-size:.9em">'+(so?'No saved Search layouts yet.':'No saved Search + Keywords layouts yet.')+'</p>';return;}
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
  var so=layoutScopeSo();
  if(typeof persistAllLiveLayouts==='function')persistAllLiveLayouts();
  else if(so&&searchOnlyStore()){
    persistAcHeight();
    persistAcWidth();
  }
  name=String(name||'').replace(/^\s+|\s+$/g,'').slice(0,40);
  if(!name)name=uniqueLayoutName(so?'Search':'Keywords',so);
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
  var so=layoutScopeSo();
  var map=readLayoutsFor(so);
  if(!map[name])return;
  applySnapshot(map[name],so);
  setLastLayoutNameFor(so,name);
  renderLayoutList();
}
function deleteNamedLayout(name){
  var so=layoutScopeSo();
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
function historyBtnEl(){return document.getElementById('searchHistory');}
function hideHistoryCloud(){
  var cloud=historyCloudEl(),btn=historyBtnEl();
  if(cloud){cloud.hidden=true;cloud.classList.remove('cloud-above','cloud-below');}
  if(btn)btn.setAttribute('aria-expanded','false');
}
function placeHistoryCloud(){
  var cloud=historyCloudEl(),btn=historyBtnEl();
  if(!cloud||!btn||cloud.hidden)return;
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
function showHistoryCloud(){
  var cloud=historyCloudEl(),btn=historyBtnEl();
  if(!cloud||!btn)return;
  cloud.hidden=false;
  btn.setAttribute('aria-expanded','true');
  placeHistoryCloud();
}
window.clearSearchHistoryData=function(){
  searchKeywords=[];
  if(typeof searchInput!=='undefined'&&searchInput)searchInput.value='';
  searchCommitCounts={};
  if(typeof lsSet==='function'&&typeof SEARCH_COMMIT_KEY!=='undefined')lsSet(SEARCH_COMMIT_KEY,{});
  if(typeof renderPills==='function')renderPills();
  if(typeof applySearch==='function'&&currentMode==='search'){applySearch();if(typeof render==='function')render();}
  else if(typeof render==='function')render();
  hideHistoryCloud();
  try{
    if(typeof showAc==='function'){
      var q=(typeof searchInput!=='undefined'&&searchInput)?searchInput.value.trim().toLowerCase():'';
      var ac=document.getElementById('acList');
      if(ac&&(ac.classList.contains('open')||(searchInput&&document.activeElement===searchInput)))showAc(q,{force:true});
    }
  }catch(err){}
};
(function bindHistoryCloud(){
  var btn=historyBtnEl(),yes=document.getElementById('historyYes'),no=document.getElementById('historyNo'),cloud=historyCloudEl();
  if(btn)btn.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    if(cloud&&!cloud.hidden)hideHistoryCloud();else showHistoryCloud();
  });
  if(yes)yes.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();window.clearSearchHistoryData();});
  if(no)no.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();hideHistoryCloud();});
  document.addEventListener('pointerdown',function(e){
    if(!cloud||cloud.hidden)return;
    if(e.target.closest&&(e.target.closest('#historyCloud')||e.target.closest('#searchHistory')))return;
    hideHistoryCloud();
  },true);
  window.addEventListener('resize',function(){if(cloud&&!cloud.hidden)placeHistoryCloud();},{passive:true});
  if(window.visualViewport)window.visualViewport.addEventListener('resize',function(){if(cloud&&!cloud.hidden)placeHistoryCloud();},{passive:true});
})();
 window.clearAllFilters=function(){
   if(typeof hideHistoryCloud==='function')hideHistoryCloud();
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
 };
 window.exitSearchUi=function(){
   closeSearchExtras();
   if(searchInput)searchInput.blur();
   if(currentMode==='search')window.setMode('shade');
 };
 if(bar){
   bar.addEventListener('click',function(e){
     var btn=e.target.closest('.kw');
     if(!btn||btn.classList.contains('clear'))return;
     if(currentMode!=='search')return;
     e.preventDefault();
     e.stopPropagation();
     if(typeof e.stopImmediatePropagation==='function')e.stopImmediatePropagation();
     if(e.ctrlKey||e.metaKey||tapToAdd){
       var k=(btn.getAttribute('data-kw')||'').trim();
       if(k&&!btn.classList.contains('disabled')&&isRemainingHitKw(k))window.addSearchKw(k);
     }
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
  parkSearchBehindOverlay();
  var fromFullscreen=el.classList.contains('highlight')||document.body.classList.contains('hl-open');
  if(!document.body.classList.contains('chosen-preview-open')){
    jumpOrigin=fromFullscreen?'preview-from-fullscreen':null;
  }
  if(typeof closeCardSearchEmbed==='function')closeCardSearchEmbed();
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
  if(typeof closeCardSearchEmbed==='function')closeCardSearchEmbed();
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
  return overlayFocusOpen()||b.contains('hl-open')||b.contains('chosen-preview-open')||b.contains('card-embed-open')||b.contains('search-modal-open')||!!document.querySelector('.entry.highlight');
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
    if(e.target.closest('#searchModal,.search-modal,.search-modal-link')) return;
    if(!e.target.closest('.entry.selected')){
      if(document.body.classList.contains('card-embed-open')){closeCardSearchEmbed();e.preventDefault();return;}
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
  if(e.target.closest('#searchModal,.card-search-embed,.search-chrome,.search-split,.search-height,.ac-height,.ac-width,.kw-shade-height,.search-ac-shell,.filter-wrap,.search-strip,.search-autocomplete,.search-active-pills,.top,.tap-add-btn,.clear-miss-btn,.layout-edit-btn,#kwbar,.kw,.mode-switch,.cat-switch,.fav-btn,.note-pop,.note-balloon,.preview-back')) return;
  if(!(e.target.closest&&e.target.closest('.note-pop,.note-balloon'))&&typeof window.closeAllNotePops==='function')window.closeAllNotePops();
  var entry=e.target.closest('.entry');
  if(entry){
    if(e.target.closest('a,.hl-close,.preview-back,.kw,input,select,textarea,summary,.patches,.search-popup-btn,.search-link,.fav-btn,.note-balloon,.note-pop,.un-badge,.note-save,.note-cancel,.fs-btn,.card-search-embed')) return;
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
    if(t.closest('.fs-btn,.hl-close,.preview-back,.fav-btn'))return null;
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

</script>
JS
  echo '</body></html>'
} > "$OUT"
rm -f "$IDX" "$BODY"

echo "KONTAKT CATALOG ($MODE): $OUT"
echo "libraries: $N   thumbs: $(ls "$THUMBS" 2>/dev/null | wc -l)   (magick: $HAVE_MAGICK)"
[ "$MODE" = portable ] && echo "size: $(du -h "$OUT" 2>/dev/null | cut -f1)"
echo "done."
