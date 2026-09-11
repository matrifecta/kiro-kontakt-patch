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
THUMBS="$ART_DIR/kontakt-thumbs"
IDX="$ART_DIR/.kidx.tmp"; BODY="$ART_DIR/.kbody.tmp"
DB_SRC="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/komplete.db3"
NIIMG="/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/image"
LIBLIST="$ART_DIR/.klibs.tmp"

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
name_tokens(){ local raw t o=""
  raw=$(printf '%s' "${1:-}" | tr 'A-Z' 'a-z' | tr -c 'a-z0-9' ' ')
  for t in $raw; do
    [ "${#t}" -lt 2 ] && continue
    case "$t" in [0-9]|[0-9][0-9]) continue ;; esac   # drop useless 1-2 digit numbers; keep 808-style
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
  local nki_list="$ART_DIR/.knki.$N.tmp"; : > "$nki_list"
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
  local groups="$ART_DIR/.kgrp.$N.tmp"; : > "$groups"
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
  local ptoks; ptoks=$(uniq_tokens "$(name_tokens "$pnames")")
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
    printf '  <button type="button" class="hl-close" aria-label="Close" onclick="clearHighlight();event.stopPropagation()">&#x2715;</button>\n'
    printf '  <button type="button" class="preview-back" aria-label="Back" onclick="event.preventDefault();event.stopPropagation();closeChosenPreview()">&#x2190;</button>\n'
    printf '  <button type="button" class="fs-btn" aria-label="Open fullscreen" onclick="event.preventDefault();event.stopPropagation();openOverlay(this.parentNode)">&#x26F6;</button>\n'
    printf '  <button type="button" class="fav-btn" aria-label="Favorite" aria-pressed="false" onclick="event.preventDefault();event.stopPropagation();toggleFav(this)">&#x2661;</button>\n'
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
  local tmp="$ART_DIR/.kloc.$key.tmp"
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
<!DOCTYPE html><html lang="en" data-theme="desert"><head><meta charset="utf-8">
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
 html{--hl-backdrop:rgba(0,0,0,.55);--hl-shadow:0 12px 48px rgba(0,0,0,.45);--accent-patch:#3ecfbf;--accent-patch-bg:rgba(62,207,191,0.18);--accent-patch-active:#7eefe4}
 *{box-sizing:border-box}
 html,body{min-height:100vh;min-height:100dvh}
 body{font-family:system-ui,Segoe UI,Roboto,sans-serif;max-width:1800px;margin:0 auto;padding:clamp(8px,2vw,32px);line-height:1.5;color:var(--text);background:var(--bg);font-size:clamp(14px,1.2vw,16px)}
 h1{margin-bottom:.2rem;color:var(--text);font-size:clamp(1.35rem,4.2vw,2rem)} h2{margin-top:2rem;border-bottom:2px solid var(--border);padding-bottom:.2rem;color:var(--text-muted);font-size:clamp(1.1rem,3.2vw,1.5rem)}
 .filter-wrap{position:sticky;top:0;z-index:210;background:var(--bg-surface);border-bottom:1px solid var(--border);box-sizing:border-box;width:100%;max-width:100vw;padding-left:env(safe-area-inset-left);padding-right:env(safe-area-inset-right)}
 .filter-toggle{width:100%;min-height:44px;height:auto;background:transparent;border:none;cursor:pointer;color:var(--text-muted);font-size:clamp(14px,1.2vw,16px);text-align:left;padding:8px clamp(8px,1.5vw,16px);display:flex;align-items:center;gap:6px;user-select:none}
 .filter-panel{overflow:hidden;max-height:0;transition:max-height 0.3s ease,padding 0.3s ease;padding:0 clamp(8px,1.5vw,16px);max-width:100%;box-sizing:border-box}
 .filter-wrap.open .filter-panel{max-height:min(70dvh,640px);overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;padding:clamp(6px,1vw,12px) clamp(8px,1.5vw,16px)}
 .toggle-arrow{display:inline-block;transition:transform 0.3s}
 .filter-wrap.open .toggle-arrow{transform:rotate(180deg)}
 .theme-picker{margin-left:auto;background:var(--bg-card);color:var(--text-muted);border:1px solid var(--border);border-radius:4px;padding:4px 8px;font-size:clamp(13px,.95vw,15px);cursor:pointer;min-height:36px}
 .index{columns:3;column-gap:2rem;font-size:.9rem} .index li{break-inside:avoid;margin:.1rem 0}
 .index a{color:var(--accent-instrument);text-decoration:underline} .index li.hit{background:var(--accent-instrument-bg);border-radius:3px}
 .catalog-body{--cat-cols:repeat(auto-fill,minmax(min(100%,clamp(200px,22vw,280px)),1fr));display:grid;grid-template-columns:var(--cat-cols);gap:1rem;align-items:start;margin-top:1rem}
 .catalog-body>h2,.catalog-body>p,.loc-group>h2,.loc-group>p,.loc-group>.loc-hint{grid-column:1/-1;order:-5}
 .loc-group{grid-column:1/-1;display:grid;grid-template-columns:var(--cat-cols);gap:inherit;align-items:start}
 .loc-group.is-hidden{display:none!important}
 .entry.is-hidden{display:none!important}
 .entry{background:var(--bg-card);border:1px solid var(--border);border-radius:8px;padding:.8rem;transition:border-color .2s;display:flex;flex-direction:column;height:auto;min-height:0;overflow:hidden;order:0;position:relative;max-width:100%;min-width:0}
 .entry:hover{border-color:var(--accent-instrument)} .entry h3,.entry .lib-name{margin:.2rem 0;color:var(--text);font-size:clamp(16px,1.6vw,22px);word-wrap:break-word;overflow-wrap:break-word;word-break:normal;hyphens:none;white-space:normal;min-width:0;cursor:pointer}
 .entry.hit{background:var(--accent-instrument-bg);border-left:4px solid var(--accent-gear);padding-left:.6rem}
 .entry.selected{outline:2px solid var(--accent-instrument);outline-offset:2px;border-color:var(--accent-instrument);box-shadow:0 0 0 4px var(--accent-instrument-bg);z-index:2}
 .preview-back{display:none;position:absolute;top:8px;left:8px;z-index:5;box-sizing:border-box;width:44px;height:44px;min-width:44px;min-height:44px;align-items:center;justify-content:center;padding:0;background:var(--bg-surface);color:var(--text);border:1px solid var(--border);border-radius:8px;cursor:pointer;touch-action:manipulation;font-size:22px;line-height:1}
 .preview-back:hover{color:var(--accent-instrument);border-color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 .fs-btn{display:none;position:absolute;top:8px;right:8px;left:auto;z-index:4;box-sizing:border-box;width:44px;height:44px;min-width:44px;min-height:44px;align-items:center;justify-content:center;padding:0;background:var(--bg-surface);color:var(--accent-instrument);border:1px solid var(--accent-instrument);border-radius:8px;cursor:pointer;touch-action:manipulation;font-size:20px;line-height:1}
 .entry.selected:not(.highlight) .fs-btn{display:flex}
 .entry.highlight .fs-btn{display:none!important}
 .entry.highlight .preview-back{display:none!important}
 .fs-btn:hover{color:var(--accent-instrument-active);border-color:var(--accent-instrument-active);background:var(--accent-instrument-bg)}
 .fav-btn{position:absolute;right:8px;bottom:8px;top:auto;left:auto;z-index:4;box-sizing:border-box;width:44px;height:44px;min-width:44px;min-height:44px;display:flex;align-items:center;justify-content:center;padding:0;background:var(--bg-surface);color:var(--text-muted);border:1px solid var(--border);border-radius:8px;cursor:pointer;touch-action:manipulation;font-size:20px;line-height:1}
 .fav-btn.on{color:var(--accent-gear);border-color:var(--accent-gear)}
 .fav-btn:hover{color:var(--accent-instrument);border-color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 .entry:not(.highlight) .card-actions{padding-right:52px}
 .entry.highlight .fav-btn{top:max(8px,env(safe-area-inset-top));left:max(8px,env(safe-area-inset-left));right:auto;bottom:auto}
 body.gallery-open .entry .fav-btn,body.img-focus-open .entry .fav-btn{visibility:hidden}
 .gallery-fav,.img-focus-fav{position:absolute;top:max(8px,env(safe-area-inset-top));right:max(8px,env(safe-area-inset-right));left:auto;bottom:auto;z-index:3;box-sizing:border-box;width:44px;height:44px;min-width:44px;min-height:44px;display:flex;align-items:center;justify-content:center;padding:0;background:rgba(20,20,24,.82);color:#fff;border:1px solid rgba(255,255,255,.35);border-radius:8px;cursor:pointer;touch-action:manipulation;font-size:20px;line-height:1}
 .gallery-fav.on,.img-focus-fav.on{color:#ffb0a0;border-color:#ffb0a0}
 .un-badge{display:none;position:absolute;top:8px;right:8px;z-index:3;width:28px;height:28px;min-width:28px;padding:0;align-items:center;justify-content:center;font-size:16px;font-weight:400;letter-spacing:0;line-height:1;background:var(--accent-instrument-bg);color:var(--accent-instrument);border:1px solid var(--accent-instrument);border-radius:6px;pointer-events:none}
 .un-badge.has-note{display:inline-flex}
 .entry.selected:not(.highlight) .un-badge{right:56px}
 .entry.highlight .un-badge{display:none!important}
 .lib-notes{position:relative;margin:.15rem 0 .35rem}
 .note-text{display:none;margin:.25rem 0;padding:.5rem .7rem;background:var(--bg-surface);border:1px dashed var(--border);border-radius:6px;color:var(--text);font-size:clamp(13px,1.1vw,15px);white-space:pre-wrap;overflow-wrap:anywhere}
 .entry.highlight .note-text.has-note{display:block}
 .note-balloon{display:none}
 .entry.highlight .note-balloon{display:inline-flex;align-items:center;justify-content:center;width:44px;height:44px;min-width:44px;min-height:44px;background:var(--bg-surface);color:var(--text-muted);border:1px solid var(--border);border-radius:8px;cursor:pointer;touch-action:manipulation;font-size:18px;line-height:1}
 .note-pop{display:none;position:absolute;z-index:6;left:0;top:48px;width:min(90vw,360px);max-width:min(90vw,360px);background:var(--bg-card);color:var(--text);border:1px solid var(--border);border-radius:8px;padding:10px;box-shadow:var(--hl-shadow)}
 .note-pop.open{display:block}
 .note-ta{width:100%;min-height:88px;resize:vertical;background:var(--bg);color:var(--text);border:1px solid var(--border);border-radius:6px;padding:8px;font:inherit}
 .note-pop-actions{display:flex;gap:8px;margin-top:8px;justify-content:flex-end}
 .note-save,.note-cancel{min-height:44px;min-width:72px;padding:0 14px;border-radius:6px;cursor:pointer;touch-action:manipulation;border:1px solid var(--border);background:var(--bg-surface);color:var(--text);font:inherit}
 .note-save{background:var(--accent-instrument-bg);color:var(--accent-instrument);border-color:var(--accent-instrument)}
 .fav-recs-label{display:none;grid-column:1/-1;order:-20;font-size:clamp(13px,.95vw,15px);color:var(--text-muted);letter-spacing:.06em;text-transform:uppercase;opacity:.9;padding:.35rem 0 .15rem;border-bottom:1px dashed var(--border);margin:0 0 .25rem}
 body.search-empty-recs .fav-recs-label{display:block}
 .entry.fav-rec{order:-1;opacity:.72;filter:saturate(.75);border-style:dashed;box-shadow:inset 0 0 40px rgba(0,0,0,.18)}
 .entry.highlight.fav-rec{opacity:1;filter:none;order:unset;border-style:solid;box-shadow:var(--hl-shadow)}
 .index li.selected{background:var(--accent-instrument-bg);border-radius:3px;box-shadow:inset 0 0 0 1px var(--accent-instrument)}
 .hl-backdrop{display:none;position:fixed;inset:0;z-index:400;background:var(--hl-backdrop)}
 .hl-backdrop.open{display:block}
 .hl-ph{visibility:hidden;pointer-events:none}
 body.hl-open{overflow:hidden}
 .hl-close{display:none}
 .entry.highlight .hl-close{display:flex;position:absolute;top:max(8px,env(safe-area-inset-top));right:max(8px,env(safe-area-inset-right));z-index:5;width:44px;height:44px;font-size:22px;align-items:center;justify-content:center;background:var(--bg-surface);color:var(--text);border:1px solid var(--border);border-radius:8px;cursor:pointer;touch-action:manipulation;line-height:1;padding:0}
 .entry.highlight .hl-close:hover{color:var(--accent-instrument);border-color:var(--accent-instrument)}
 .entry.highlight{position:fixed;inset:0;width:100vw;height:100vh;height:100dvh;max-width:none;max-height:none;z-index:401;display:flex;flex-direction:column;overflow:hidden;padding:max(52px,calc(env(safe-area-inset-top) + 8px)) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left);box-sizing:border-box;grid-column:unset;left:auto;top:auto;transform:none;border-radius:0;outline:2px solid var(--accent-instrument);outline-offset:-2px;background:var(--bg-card);border:1px solid var(--border);box-shadow:var(--hl-shadow)}
 .hl-body{min-width:0}
 .entry.highlight .hl-body{flex:1 1 auto;min-height:0;overflow-y:auto;-webkit-overflow-scrolling:touch;padding:12px 16px 24px}
 .cover{flex-shrink:0;width:100%;max-width:min(100%,280px);max-height:160px;margin:.3rem 0;display:flex;align-items:center;justify-content:center;overflow:hidden;border:1px solid var(--border);border-radius:4px;background:var(--bg-surface);box-sizing:border-box;cursor:pointer}
 .cover img{width:auto;height:auto;max-width:100%;max-height:160px;object-fit:contain;object-position:center center;display:block}
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
 .entry.highlight h3,.entry.highlight .lib-name{text-align:center;width:100%;max-width:100%;overflow-wrap:break-word;word-break:break-word;white-space:normal;padding-inline:56px;box-sizing:border-box}
OVERLAYTITLECSS
  fi
  cat <<'GALLERYCSS'
 .entry.highlight .cover,.entry.highlight .cover img{cursor:pointer}
 .entry.highlight .summary-panel .desc,.summary-panel .desc{cursor:pointer}
 .path,.entry.highlight .path{cursor:pointer}
 .img-gallery{display:none;position:fixed;inset:0;z-index:870;background:#000;align-items:center;justify-content:center;touch-action:none;overflow:hidden;-webkit-user-select:none;user-select:none;overscroll-behavior:none}
 .img-gallery.open{display:flex}
 .img-gallery .gallery-img{max-width:100vw;max-height:100dvh;width:auto;height:auto;object-fit:contain;object-position:center center;transform-origin:center center;pointer-events:none}
 .gallery-back,.desc-reader-back,.path-reader-back{position:absolute;top:max(8px,env(safe-area-inset-top));left:max(8px,env(safe-area-inset-left));z-index:3;box-sizing:border-box;width:44px;height:44px;min-width:44px;min-height:44px;display:flex;align-items:center;justify-content:center;padding:0;background:rgba(20,20,24,.82);color:#fff;border:1px solid rgba(255,255,255,.35);border-radius:8px;cursor:pointer;touch-action:manipulation;font-size:22px;line-height:1}
 .gallery-title,.img-focus-title{position:absolute;top:max(8px,env(safe-area-inset-top));left:calc(max(8px,env(safe-area-inset-left)) + 52px);right:calc(max(8px,env(safe-area-inset-right)) + 52px);z-index:2;pointer-events:auto;box-sizing:border-box;display:block;min-width:0;max-height:2.5em;margin:0;padding:8px 10px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-family:inherit;font-size:clamp(13px,3.5vw,16px);font-weight:600;line-height:1.25;text-align:center;color:#fff;background:rgba(0,0,0,.45);border:0;border-radius:8px;cursor:pointer;touch-action:manipulation;-webkit-appearance:none;appearance:none;-webkit-user-select:none;user-select:none}
 .gallery-title.expanded,.img-focus-title.expanded{white-space:normal;overflow:visible;text-overflow:clip;max-height:none;overflow-wrap:anywhere}
 .gallery-zoom,.desc-reader-zoom,.path-reader-zoom{position:absolute;bottom:max(16px,env(safe-area-inset-bottom));left:50%;transform:translateX(-50%);z-index:3;display:flex;align-items:center;gap:8px;background:rgba(0,0,0,.5);border:1px solid rgba(255,255,255,.2);border-radius:8px;padding:6px 12px;touch-action:manipulation}
 .gallery-zoom-btn,.desc-reader-zoom-btn,.path-reader-zoom-btn{width:36px;height:36px;min-width:36px;min-height:36px;border:1px solid rgba(255,255,255,.3);background:transparent;color:#fff;border-radius:6px;cursor:pointer;font-size:20px;line-height:1;touch-action:manipulation}
 .desc-reader,.path-reader{display:none;position:fixed;inset:0;z-index:10050;background:var(--bg);color:var(--text);flex-direction:column;box-sizing:border-box;padding:max(52px,calc(env(safe-area-inset-top) + 8px)) max(16px,env(safe-area-inset-right)) env(safe-area-inset-bottom) max(16px,env(safe-area-inset-left));touch-action:manipulation;overscroll-behavior:none}
 .desc-reader.open,.path-reader.open{display:flex}
 .desc-reader-text,.path-reader-text{flex:1 1 auto;min-height:0;overflow-y:auto;-webkit-overflow-scrolling:touch;font-size:clamp(18px,4.8vw,22px);line-height:1.7;max-width:65ch;margin:0 auto;width:100%;touch-action:pan-y;padding-bottom:56px}
 .desc-reader-text h2,.path-reader-text h2{margin:0 0 .6rem;font-size:clamp(20px,5vw,26px);color:var(--text)}
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
 .img-focus-zoom-btn,.desc-focus-zoom-btn,.path-focus-zoom-btn{width:36px;height:36px;border:1px solid rgba(255,255,255,.3);background:transparent;color:#fff;border-radius:6px;cursor:pointer;font-size:20px;line-height:1}
 .img-focus-zoom input[type=range]{width:min(40vw,180px);accent-color:var(--accent-instrument)}
 .desc-focus-box,.path-focus-box{background:var(--bg-card);color:var(--text);border:1px solid var(--border);border-radius:10px;max-width:min(42rem,90vw);max-height:min(80vh,820px);overflow:hidden;display:flex;flex-direction:column;padding:clamp(16px,2.5vw,28px);box-shadow:0 12px 48px rgba(0,0,0,.4);cursor:pointer}
 .desc-focus-text,.path-focus-text{overflow-y:auto;font-size:18px;line-height:1.7;max-height:min(72vh,760px);touch-action:pan-y}
 .desc-focus-text h2,.path-focus-text h2{margin:0 0 .6rem;font-size:1.25em;color:var(--text)}
 .desc-focus-text p,.path-focus-text p{margin:0}
 .path-focus-text,.path-focus-text p{overflow-wrap:anywhere;word-break:break-word;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
 body.img-focus-open,body.desc-focus-open,body.path-focus-open{overflow:hidden}
FOCUSCSS
  fi
  cat <<'HTML'
 .summary-panel{width:100%;max-width:100%;min-width:0;overflow:hidden;border-radius:6px;border:1px solid var(--border);margin:clamp(4px,0.6vw,8px) 0;padding:clamp(8px,1.1vw,14px) clamp(10px,1.2vw,16px);background:var(--bg);max-height:8.2em}
 .summary-panel .desc{font-style:normal;font-size:clamp(13px,1.15vw,16px);line-height:1.55;color:var(--text);margin:0;overflow-wrap:break-word;word-break:normal;hyphens:none;white-space:normal;max-width:100%}
 .entry.highlight .summary-panel{width:100%;max-width:100%;overflow:visible;overflow-wrap:break-word;background:var(--bg);max-height:none;flex:none}
 .entry.highlight .summary-panel .desc,.entry.highlight .desc{min-height:8em;max-height:none;overflow:visible;font-size:clamp(16px,4.5vw,20px);max-width:65ch;margin-left:auto;margin-right:auto;margin-bottom:.75rem;line-height:1.65;overflow-wrap:break-word;word-break:normal;hyphens:none;white-space:normal;text-align:left}
 .path{font-size:clamp(12px,0.9vw,14px);color:var(--text-muted);margin:.35rem 0 .15rem;overflow-wrap:anywhere}
 .path code{overflow-wrap:anywhere;word-break:break-word}
 .entry.highlight .path,.entry.highlight .path code,.entry.highlight .path .folder{font-size:clamp(14px,3.8vw,17px);color:var(--text-muted)}
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
 .kw{cursor:pointer;border:1px solid var(--accent-instrument-bg);background:var(--accent-instrument-bg);border-radius:14px;padding:6px 10px;font-size:clamp(12px,.95vw,14px);color:var(--accent-instrument);min-height:36px;touch-action:manipulation;-webkit-touch-callout:none;-webkit-user-select:none;user-select:none}
 .kw:hover{border-color:var(--accent-instrument)} .kw.active{background:var(--accent-instrument-active);color:#1a1008;border-color:var(--accent-instrument)}
 .kw.disabled{color:var(--text-muted);background:transparent;border-color:var(--border);cursor:not-allowed;opacity:.5}
 .kw.clear{background:rgba(180,40,40,0.2);border-color:#c03040;color:#ff9090}
 .kwstatus{font-size:clamp(14px,1vw,16px);color:var(--accent-instrument);font-weight:600;min-height:1.1em}
 .kw.patch,.kw[data-cat="patch"]{border-color:var(--accent-patch-bg);background:var(--accent-patch-bg);color:var(--accent-patch)}
 .kw.patch:hover,.kw[data-cat="patch"]:hover{border-color:var(--accent-patch)}
 .kw.patch.active,.kw[data-cat="patch"].active{background:var(--accent-patch-active);color:#082422;border-color:var(--accent-patch)}
 .top{position:fixed;bottom:1rem;right:1rem;background:var(--accent-instrument);color:#1a1008;padding:.4rem .7rem;border-radius:4px;text-decoration:none;border:1px solid var(--accent-instrument)}
 .mode-switch{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;max-width:100%}
 .mode-btn{background:var(--bg-card);border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:6px 12px;font-size:clamp(12px,.95vw,14px);cursor:pointer;min-height:36px;touch-action:manipulation}
 .mode-btn.active{background:var(--accent-instrument-bg);color:var(--accent-instrument);border-color:var(--accent-instrument)}
 .entry.dim{order:999;opacity:.25;pointer-events:none}
 .card-actions{display:flex;gap:clamp(4px,0.8vw,8px);padding:clamp(4px,0.6vw,6px) 0 0 0;margin-top:auto}
 .search-link{display:inline-flex;align-items:center;gap:3px;padding:clamp(6px,0.8vw,8px) clamp(8px,1.2vw,12px);border-radius:4px;font-size:clamp(13px,1vw,15px);text-decoration:none;border:1px solid var(--border);color:var(--text-muted);background:var(--bg);transition:color 0.15s,border-color 0.15s;white-space:nowrap;touch-action:manipulation;min-height:36px}
 .search-link:hover{color:var(--text);border-color:var(--text-muted)}
 .search-popup-btn{display:inline-flex;align-items:center;gap:4px;padding:clamp(6px,0.8vw,8px) clamp(10px,1.5vw,14px);border-radius:4px;font-size:clamp(13px,1vw,15px);border:1px solid var(--border);color:var(--text-muted);background:var(--bg);cursor:pointer;touch-action:manipulation;min-height:36px;transition:color 0.15s,border-color 0.15s}
 .search-popup-btn:hover{color:var(--text);border-color:var(--text-muted)}
 .card-actions--noart .search-popup-btn{font-size:clamp(11px,1vw,13px);padding:clamp(5px,0.8vw,8px) clamp(10px,2vw,16px);min-height:36px}
 .search-modal-backdrop{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:860;align-items:center;justify-content:center;padding:clamp(8px,3vw,24px)}
 .search-modal-backdrop.open{display:flex}
 body.search-modal-open .search-modal-backdrop.open{align-items:flex-end}
HTML
  cat <<'CHOSENPREVIEWCSS'
 body.chosen-preview-open{overflow:hidden}
 body.chosen-preview-open:not(.hl-open)::before{content:"";position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:830;pointer-events:none}
 body.chosen-preview-open:not(.hl-open) .search-modal-backdrop,body.search-modal-open:not(.hl-open) .search-modal-backdrop{background:transparent;pointer-events:none;z-index:860}
 body.search-modal-open:not(.hl-open) .search-modal{pointer-events:auto;position:relative;z-index:1}
 body.chosen-preview-open:not(.hl-open) .entry:not(.selected):not(.highlight){opacity:.28;filter:saturate(.4);pointer-events:none}
 body.chosen-preview-open .entry.selected:not(.highlight){position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);z-index:840;box-sizing:border-box;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:auto;display:grid;grid-template-columns:auto minmax(0,1fr);grid-auto-rows:auto;align-content:start;align-items:start;justify-items:stretch;width:min(86vw,1120px);height:auto;min-height:min(52vh,420px);max-width:min(86vw,1120px);max-height:min(88vh,860px);margin:0;padding:56px 14px 12px 10px;box-shadow:0 18px 56px rgba(0,0,0,.5)}
 body.chosen-preview-open .entry.selected:not(.highlight) .preview-back{display:flex;z-index:841}
 body.chosen-preview-open .entry.selected:not(.highlight) .fav-btn{top:8px;left:56px;right:auto;bottom:auto;z-index:841}
 body.chosen-preview-open .entry.selected:not(.highlight) .fs-btn{z-index:841;display:flex}
 body.chosen-preview-open .entry.selected:not(.highlight) .hl-body{display:contents}
 body.chosen-preview-open .entry.selected:not(.highlight) .cover{grid-column:1;grid-row:1;align-self:start;justify-self:start;flex:none;position:static;width:auto;height:160px;max-height:160px;max-width:min(38vw,360px);min-height:110px;margin:0 14px 0 0;overflow:hidden;display:flex;align-items:center;justify-content:flex-start}
 body.chosen-preview-open .entry.selected:not(.highlight) .cover img{width:auto;height:auto;max-width:100%;max-height:160px;object-fit:contain;object-position:left center;transform:none}
 body.chosen-preview-open .entry.selected:not(.highlight) .lib-name{grid-column:2;grid-row:1;align-self:center;margin:0;padding-right:52px;min-width:0;white-space:normal;overflow-wrap:break-word;word-break:normal}
 body.chosen-preview-open .entry.selected:not(.highlight) .lib-notes{display:contents}
 body.chosen-preview-open .entry.selected:not(.highlight) .note-balloon{grid-column:2;grid-row:1;align-self:center;justify-self:end;display:inline-flex;align-items:center;justify-content:center;width:44px;height:44px;min-width:44px;min-height:44px;background:var(--bg-surface);color:var(--text-muted);border:1px solid var(--border);border-radius:8px;cursor:pointer;touch-action:manipulation;font-size:18px;line-height:1}
 body.chosen-preview-open .entry.selected:not(.highlight) .note-text.has-note{display:block;grid-column:1/-1;position:static;min-height:3.2em;max-height:none;overflow:visible;overflow-x:hidden;white-space:pre-wrap;overflow-wrap:break-word;word-break:normal}
 body.chosen-preview-open .entry.selected:not(.highlight) .note-pop{position:absolute;left:auto;right:56px;top:56px;z-index:845}
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
  body.chosen-preview-open .entry.selected:not(.highlight){width:min(94vw,560px);max-height:min(92dvh,100%);height:auto;top:50%;display:flex;flex-direction:column;align-items:stretch;justify-content:flex-start;gap:10px;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;grid-template-columns:none}
  body.chosen-preview-open.search-modal-open .entry.selected:not(.highlight){top:42%}
  body.chosen-preview-open .entry.selected:not(.highlight) .hl-body{display:flex;flex-direction:column;align-items:stretch;gap:10px;min-width:0;overflow:visible;flex:0 0 auto}
  body.chosen-preview-open .entry.selected:not(.highlight) .cover{flex:none;align-self:center;justify-self:center;justify-content:center;display:flex;align-items:center;width:auto;height:auto;max-height:min(28vh,200px);max-width:min(86vw,360px);min-height:0;margin:0 auto;margin-inline:auto;overflow:hidden;float:none}
  body.chosen-preview-open .entry.selected:not(.highlight) .cover img{max-height:min(28vh,200px);max-width:100%;object-position:center center}
  body.chosen-preview-open .entry.selected:not(.highlight) .lib-name{align-self:stretch;width:100%;max-width:100%;margin:0;padding-inline:12px;box-sizing:border-box;text-align:center;overflow-wrap:break-word;word-break:break-word;white-space:normal;overflow:visible}
  body.chosen-preview-open .entry.selected:not(.highlight) .lib-notes{display:contents}
  body.chosen-preview-open .entry.selected:not(.highlight) .note-balloon{position:absolute;top:8px;left:104px;right:auto;bottom:auto;z-index:841;margin:0}
  body.chosen-preview-open .entry.selected:not(.highlight) .note-text.has-note{display:block;margin:0;max-height:none;overflow:visible;flex-shrink:0}
  body.chosen-preview-open .entry.selected:not(.highlight) .note-pop{position:absolute;left:8px;right:auto;top:56px}
  body.chosen-preview-open .entry.selected:not(.highlight) .noart{margin:0;overflow:visible;flex-shrink:0}
  body.chosen-preview-open .entry.selected:not(.highlight) .summary-panel{float:none;flex:none;flex-shrink:0;margin:0;max-height:none;min-height:calc(1.65em * 3 + 1.6em);overflow:visible}
  body.chosen-preview-open .entry.selected:not(.highlight) .summary-panel .desc,body.chosen-preview-open .entry.selected:not(.highlight) .desc{float:none;margin:0;max-height:none;min-height:calc(1.65em * 3);line-height:1.65;overflow:visible;white-space:normal;overflow-wrap:break-word;word-break:normal;hyphens:none}
  body.chosen-preview-open .entry.selected:not(.highlight) .path{float:none;flex:none;flex-shrink:0;margin:0;min-height:0;max-height:none;overflow:visible;white-space:normal;overflow-wrap:break-word;word-break:break-word}
  body.chosen-preview-open .entry.selected:not(.highlight) details.patches,body.chosen-preview-open .entry.selected:not(.highlight) .patches{flex:none;flex-shrink:0;max-height:none;overflow:visible;margin:0}
  body.chosen-preview-open .entry.selected:not(.highlight) .card-actions{z-index:auto;flex:none;flex-shrink:0;margin:0;overflow:visible;padding-top:0;padding-bottom:0}
 }
 /* Phone/portable: momentum-scroll compositing can paint the fixed preview over #searchModal. */
 @media (max-width:899px),(hover:none) and (pointer:coarse){
  body.chosen-preview-open .entry.selected:not(.highlight){left:0;right:0;top:4dvh;bottom:auto;transform:none;margin:0 auto;display:flex;flex-direction:column;align-items:stretch;justify-content:flex-start;gap:10px;max-height:min(92dvh,100%);height:auto;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;grid-template-columns:none}
  body.chosen-preview-open.search-modal-open .entry.selected:not(.highlight){top:8px;bottom:auto;margin:8px auto auto;max-height:min(92dvh,100%)}
  body.chosen-preview-open .entry.selected:not(.highlight) .hl-body{display:flex;flex-direction:column;align-items:stretch;gap:10px;min-width:0;overflow:visible;flex:0 0 auto}
  body.chosen-preview-open .entry.selected:not(.highlight) .cover{flex:none;align-self:center;justify-self:center;justify-content:center;display:flex;align-items:center;width:auto;height:auto;max-height:min(28vh,200px);max-width:min(86vw,360px);min-height:0;margin:0 auto;margin-inline:auto;overflow:hidden;float:none}
  body.chosen-preview-open .entry.selected:not(.highlight) .cover img{max-height:min(28vh,200px);max-width:100%;object-position:center center}
  body.chosen-preview-open .entry.selected:not(.highlight) .lib-name{align-self:stretch;width:100%;max-width:100%;margin:0;padding-inline:12px;box-sizing:border-box;text-align:center;overflow-wrap:break-word;word-break:break-word;white-space:normal;overflow:visible}
  body.chosen-preview-open .entry.selected:not(.highlight) .lib-notes{display:contents}
  body.chosen-preview-open .entry.selected:not(.highlight) .note-balloon{position:absolute;top:8px;left:104px;right:auto;bottom:auto;z-index:841;margin:0}
  body.chosen-preview-open .entry.selected:not(.highlight) .note-text.has-note{display:block;margin:0;max-height:none;overflow:visible;flex-shrink:0}
  body.chosen-preview-open .entry.selected:not(.highlight) .note-pop{position:absolute;left:8px;right:auto;top:56px}
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
 body.chosen-preview-open .entry.selected:not(.highlight){display:flex;flex-direction:column;align-items:stretch;justify-content:flex-start;gap:10px;max-height:min(92dvh,100%);height:auto;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;grid-template-columns:none}
 body.chosen-preview-open .entry.selected:not(.highlight) .hl-body{display:flex;flex-direction:column;align-items:stretch;gap:10px;min-width:0;overflow:visible;flex:0 0 auto}
 body.chosen-preview-open .entry.selected:not(.highlight) .cover,body.chosen-preview-open .entry.selected:not(.highlight) .lib-name,body.chosen-preview-open .entry.selected:not(.highlight) .note-text,body.chosen-preview-open .entry.selected:not(.highlight) .noart,body.chosen-preview-open .entry.selected:not(.highlight) .summary-panel,body.chosen-preview-open .entry.selected:not(.highlight) .path,body.chosen-preview-open .entry.selected:not(.highlight) details.patches,body.chosen-preview-open .entry.selected:not(.highlight) .patches,body.chosen-preview-open .entry.selected:not(.highlight) .card-actions{position:static}
 body.chosen-preview-open .entry.selected:not(.highlight) .cover{flex:none;align-self:center;justify-self:center;justify-content:center;display:flex;align-items:center;width:auto;height:auto;max-height:min(28vh,200px);max-width:min(86vw,360px);min-height:0;margin:0 auto;margin-inline:auto;overflow:hidden;float:none}
 body.chosen-preview-open .entry.selected:not(.highlight) .cover img{max-height:min(28vh,200px);max-width:100%;object-position:center center}
 body.chosen-preview-open .entry.selected:not(.highlight) .lib-name{align-self:stretch;width:100%;max-width:100%;margin:0;padding-inline:12px;box-sizing:border-box;text-align:center;overflow-wrap:break-word;word-break:break-word;white-space:normal;overflow:visible}
 body.chosen-preview-open .entry.selected:not(.highlight) .lib-notes{display:contents}
 body.chosen-preview-open .entry.selected:not(.highlight) .note-balloon{position:absolute;top:8px;left:104px;right:auto;bottom:auto;z-index:841;margin:0}
 body.chosen-preview-open .entry.selected:not(.highlight) .note-text.has-note{display:block;margin:0;max-height:none;overflow:visible;flex-shrink:0}
 body.chosen-preview-open .entry.selected:not(.highlight) .note-pop{position:absolute;left:8px;right:auto;top:56px}
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
 .search-modal-close{position:absolute;top:clamp(8px,1.5vw,12px);right:clamp(8px,1.5vw,12px);background:none;border:none;color:var(--text-muted);font-size:18px;cursor:pointer;line-height:1;padding:4px 6px;border-radius:4px;touch-action:manipulation;min-width:32px;min-height:32px}
 .search-modal-close:hover{color:var(--text);background:var(--bg-card)}
 .search-modal-title{font-size:clamp(13px,1.4vw,17px);font-weight:600;color:var(--text);padding-right:32px;margin-bottom:6px;word-break:break-word}
 .search-modal-subtitle{font-size:clamp(11px,1vw,13px);color:var(--text-muted);margin-bottom:clamp(12px,2vw,18px)}
 .search-modal-btns{display:flex;gap:clamp(10px,2.2vw,20px);flex-wrap:wrap}
 .search-modal-link{flex:1 1 auto;min-width:110px;display:flex;align-items:center;justify-content:center;gap:6px;padding:clamp(10px,1.8vw,16px) clamp(12px,2.5vw,20px);border-radius:7px;font-size:clamp(13px,1.2vw,15px);font-weight:500;text-decoration:none;border:1px solid var(--border);color:var(--text);background:var(--bg-card);cursor:pointer;touch-action:manipulation;min-height:48px;transition:background 0.15s,border-color 0.15s,color 0.15s}
 .search-modal-link.yt:hover{background:rgba(255,64,64,0.12);border-color:#ff4040;color:#ff5555}
 .search-modal-link.web:hover{background:var(--accent-instrument-bg);border-color:var(--accent-instrument);color:var(--accent-instrument)}
 .search-modal-link.img:hover{background:var(--accent-gear-bg);border-color:var(--accent-gear);color:var(--accent-gear)}
 .search-modal-hint{font-size:clamp(9px,0.85vw,11px);color:var(--text-muted);text-align:center;margin-top:clamp(8px,1.2vw,12px);opacity:0.7}
 @media (min-width:900px) and (orientation:landscape){.search-modal{max-width:min(92vw,720px)}}
 @media (min-width:600px) and (orientation:portrait){.search-modal{max-width:min(92vw,640px)}}
 @media (max-width:899px) and (orientation:landscape){.search-modal{max-width:min(92vw,720px)}.search-modal-backdrop{align-items:center;justify-content:center;padding:clamp(8px,3vw,24px)}}
 @media (max-width:599px) and (orientation:portrait){.search-modal{border-radius:12px 12px 0 0;margin-top:auto;margin-bottom:0;max-width:100%}.search-modal-backdrop{align-items:flex-end;padding:0}}
 @media(max-width:320px){.card-actions{flex-direction:column}}
 .search-chrome{width:100%;max-width:100%;box-sizing:border-box}
 .search-col{display:none;position:relative;min-width:0;max-width:100%;width:100%}
 .search-strip-anchor{position:relative;min-width:0;width:100%;max-width:100%}
 body.search-mode .search-chrome{display:grid;grid-template-columns:1fr;gap:8px;align-items:start;position:sticky;top:0;z-index:200;background:var(--bg-surface);padding-top:env(safe-area-inset-top);padding-left:env(safe-area-inset-left);padding-right:env(safe-area-inset-right);width:100%;max-width:100%;box-sizing:border-box}
 body.search-mode .search-col{display:flex;flex-direction:column;min-width:0;max-width:100%}
 body.search-mode .filter-wrap{position:relative;top:auto;z-index:auto;width:100%;max-width:100%;padding-left:0;padding-right:0}
 @media(min-width:900px){body.search-mode .search-chrome{grid-template-columns:1fr 1fr}}
 @media(min-width:700px) and (orientation:landscape){body.search-mode .search-chrome{grid-template-columns:minmax(20rem,1.6fr) minmax(14rem,1fr)}body.search-mode .search-col{min-width:min(100%,20rem)}body.search-mode .search-strip input{flex:1 1 12rem;min-width:12rem}}
 @media(max-width:899px) and (orientation:portrait){body.search-mode .search-chrome{grid-template-columns:1fr}}
 .search-strip{display:none;position:relative;min-height:44px;height:auto;background:var(--bg-surface);border-bottom:1px solid var(--border);padding:0 8px;align-items:center;gap:8px;flex-wrap:wrap;box-sizing:border-box;width:100%;max-width:100%}
 .search-mode .search-strip{display:flex}
 .search-strip input{flex:1;min-width:0;background:transparent;border:none;outline:none;color:var(--text);font-size:clamp(16px,1.1vw,16px);caret-color:var(--accent-instrument);min-height:44px}
 .search-strip input::placeholder{color:var(--text-muted)}
 .search-strip-clear{flex-shrink:0;background:transparent;border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:6px 12px;font-size:clamp(14px,.95vw,16px);cursor:pointer;min-height:44px;touch-action:manipulation}
 .search-strip-clear:hover{color:var(--accent-instrument);border-color:var(--accent-instrument)}
 .search-strip-hide{flex-shrink:0;background:transparent;border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:6px 12px;font-size:clamp(14px,.95vw,16px);cursor:pointer;min-height:44px;touch-action:manipulation;white-space:nowrap}
 .search-strip-hide:hover{color:var(--accent-instrument);border-color:var(--accent-instrument)}
 .tap-add-btn{flex-shrink:0;box-sizing:border-box;min-height:44px;background:transparent;border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:0 12px;font-size:clamp(14px,.95vw,16px);cursor:pointer;touch-action:manipulation;white-space:nowrap}
 .tap-add-btn[aria-pressed="true"]{background:var(--accent-instrument-bg);color:var(--accent-instrument);border-color:var(--accent-instrument);font-weight:600}
 body:not(.search-mode) .tap-add-btn{display:none}
 .mode-btn.clear-all{border-color:#c03040;color:#ff9090;background:rgba(180,40,40,0.2)}
 body.search-extras-collapsed .search-autocomplete,body.search-extras-collapsed .search-active-pills,body.search-chrome-collapsed .search-autocomplete,body.search-chrome-collapsed .search-active-pills{display:none!important}
 body.search-chrome-collapsed .search-strip input,body.search-chrome-collapsed .search-strip-clear{display:none!important}
 .search-autocomplete{position:absolute;top:100%;left:0;right:0;background:var(--bg-surface);border:1px solid var(--border);border-top:none;z-index:2;max-height:min(40dvh,280px);overflow-y:auto;display:none;max-width:100%;width:100%;box-sizing:border-box}
 .search-autocomplete.open{display:block}
 .search-autocomplete .ac-item{padding:10px clamp(8px,2vw,20px);cursor:pointer;font-size:clamp(14px,1.1vw,16px);color:var(--text);display:flex;justify-content:space-between;min-height:44px;align-items:center;gap:8px}
 .search-autocomplete .ac-item:hover{background:var(--bg-card)}
 .search-autocomplete .ac-item .ac-label{display:flex;align-items:center;gap:8px;min-width:0;flex:1}
 .search-autocomplete .ac-item .ac-note{flex-shrink:0;font-size:16px;line-height:1}
 .search-autocomplete .ac-item .ac-count{color:var(--text-muted);font-size:.85em;flex-shrink:0}
 .search-active-pills{display:none;flex-wrap:wrap;gap:6px;padding:clamp(4px,.5vw,8px) clamp(8px,2vw,20px);background:var(--bg-surface);border-bottom:1px solid var(--border);position:relative;max-width:100%;width:100%;box-sizing:border-box}
 .search-mode .search-active-pills{display:flex;align-items:center}
 .pill-tag{background:var(--accent-instrument-bg);color:var(--accent-instrument);border:1px solid var(--accent-instrument);border-radius:12px;padding:2px 2px 2px 10px;font-size:clamp(13px,.95vw,15px);cursor:default;display:flex;align-items:center;gap:0;-webkit-user-select:none;user-select:none;min-height:36px}
 .pill-tag.patch{background:var(--accent-patch-bg);color:var(--accent-patch);border-color:var(--accent-patch)}
 .pill-tag.patch .pill-x{color:var(--accent-patch)}
 .pill-tag .pill-label{padding-right:2px}
 .pill-tag .pill-x{opacity:1;display:inline-flex;align-items:center;justify-content:center;min-width:36px;min-height:36px;margin:0;padding:0;border:0;background:transparent;color:var(--accent-instrument);font-size:20px;font-weight:700;line-height:1;cursor:pointer;touch-action:manipulation;-webkit-touch-callout:none;border-radius:10px}
 .pill-tag .pill-x:hover{background:rgba(255,144,144,0.18);color:#ff9090}
 .cat-switch{display:flex;flex-wrap:wrap;gap:clamp(4px,0.8vw,8px);margin-bottom:clamp(6px,1.2vw,10px);max-width:100%;box-sizing:border-box}
 .cat-btn{background:var(--bg-card);border:1px solid var(--border);color:var(--text-muted);border-radius:6px;padding:8px 14px;font-size:clamp(13px,1.1vw,15px);cursor:pointer;min-height:36px;touch-action:manipulation;white-space:nowrap;transition:background 0.15s,color 0.15s}
 .cat-btn.active{background:var(--accent-instrument-bg);color:var(--accent-instrument);border-color:var(--accent-instrument);font-weight:600}
 .cat-btn[data-cat="patch"].active{background:var(--accent-patch-bg);color:var(--accent-patch);border-color:var(--accent-patch)}
 @media(max-width:899px){body{font-size:clamp(16px,4vw,18px)}.entry h3{font-size:clamp(16px,4.5vw,22px)}.kw{min-height:44px;font-size:clamp(14px,3.8vw,17px);padding:8px 14px}.cat-btn,.mode-btn,.tap-add-btn,.search-strip-clear,.search-strip-hide,.mode-btn.clear-all{min-height:44px;font-size:clamp(14px,3.6vw,16px)}.filter-toggle{font-size:clamp(14px,3.6vw,16px);min-height:44px}.theme-picker{font-size:clamp(14px,3.4vw,16px);min-height:36px}.path,.path code,.path .folder{font-size:clamp(14px,3.8vw,17px)}.summary-panel .desc,.desc{font-size:clamp(16px,4.5vw,20px)}.search-popup-btn,.search-link{min-height:44px;font-size:clamp(14px,3.6vw,16px)}.pill-tag{font-size:clamp(14px,3.6vw,16px);min-height:44px}.index{columns:1;font-size:1rem}}
 @media(orientation:portrait){.filter-panel,.cat-switch,#kwbar,.mode-switch{flex-wrap:wrap;max-width:100%;overflow-x:hidden}.cat-switch,#kwbar{overflow-y:auto;-webkit-overflow-scrolling:touch}#kwbar{max-height:min(42dvh,360px)}.catalog-body{--cat-cols:minmax(0,1fr);grid-template-columns:var(--cat-cols)}.entry{max-width:100%}.entry.highlight .cover,.entry.highlight .cover img{max-height:min(38dvh,100%)}}
 @media(max-width:899px) and (orientation:landscape){body.search-mode .search-chrome{grid-template-columns:minmax(18rem,1.75fr) minmax(0,1fr)}body.search-mode .search-col{min-width:min(100%,18rem)}body.search-mode .search-strip input{flex:1 1 12rem;min-width:12rem}.entry.highlight .cover,.entry.highlight .cover img{max-height:min(32dvh,100%)}#kwbar{flex-wrap:wrap;max-width:100%;overflow-x:auto;overflow-y:hidden;-webkit-overflow-scrolling:touch}.cat-switch{flex-wrap:nowrap;overflow-x:auto;max-width:100%;-webkit-overflow-scrolling:touch}.catalog-body{--cat-cols:repeat(auto-fill,minmax(min(100%,220px),1fr));grid-template-columns:var(--cat-cols)}}
 @media(min-width:900px){.entry.highlight .cover,.entry.highlight .cover img{max-width:100%;max-height:min(70dvh,calc(100dvh - 12em));width:auto;height:auto;object-fit:contain;object-position:center center}.entry.highlight .cover img{width:auto;height:auto;max-width:100%;max-height:min(70dvh,calc(100dvh - 12em));object-fit:contain}.entry.highlight .summary-panel .desc{font-size:clamp(16px,1.3vw,20px)}}
 .search-autocomplete .ac-group-label{padding:4px clamp(8px,2vw,20px) 2px;font-size:.75em;font-weight:700;color:var(--accent-gear);text-transform:uppercase;letter-spacing:.05em}
 .search-autocomplete .ac-group-label[data-cat="patch"]{color:var(--accent-patch)}
 .search-autocomplete .ac-item[data-cat="patch"] .ac-label{color:var(--accent-patch)}
</style></head><body>
<h1 id="top">Kontakt Library Catalog</h1>
HTML
  printf '<p>generated: %s</p>\n' "$(e "$(date)")"
  if [ "$MODE" = portable ]; then
    printf '<p>Portable snapshot (banners embedded; phone-safe). Registered Kontakt libraries; click a name to jump. <b>Update:</b> on desktop re-run <code>build-kontakt-catalog-html.sh both</code> and re-transfer this file.</p>\n'
  else
    printf '<p>Registered Kontakt libraries (from komplete.db3). Click a name to jump; [open folder] opens the library in Dolphin. <b>Added libraries?</b> Re-run <code>build-kontakt-catalog-html.sh both</code>.</p>\n'
  fi
  echo '<div class="search-chrome" id="searchChrome"><div class="search-col" id="searchCol"><div class="search-strip-anchor"><div class="search-strip" id="searchStrip"><input id="searchInput" type="text" placeholder="Search libraries..." autocomplete="off"><button type="button" class="search-strip-hide" onclick="toggleSearchChrome()" aria-expanded="true">Hide search</button><button type="button" class="search-strip-clear" onclick="clearAllFilters()">Clear</button></div><div class="search-autocomplete" id="acList"></div></div><div class="search-active-pills" id="searchPills"></div></div>'
  echo '<div class="filter-wrap" id="filterWrap"><button class="filter-toggle" id="filterToggle" onclick="toggleFilter()" aria-expanded="false"><span class="toggle-arrow">&#9660;</span> Keywords<select id="themePicker" class="theme-picker" onchange="setTheme(this.value)" onclick="event.stopPropagation()"><optgroup label="— Dark —"><option value="desert">Desert Dusk</option><option value="studio">Night Studio</option><option value="smoked">Smoked Glass</option><option value="autumn-ember">Autumn Ember</option><option value="tropical-night">Tropical Night</option><option value="spring-rain">Spring Rain</option><option value="deep-winter">Deep Winter</option></optgroup><optgroup label="— Light —"><option value="sandstorm">Sand Storm</option><option value="bleached">Bleached</option><option value="spring-bloom">Spring Bloom</option><option value="summer-beach">Summer Beach</option><option value="harvest">Harvest</option><option value="arctic">Arctic</option></optgroup><optgroup label="— High Contrast —"><option value="hc-dark">HC Dark</option><option value="hc-light">HC Light</option></optgroup></select></button><div class="filter-panel" id="filterPanel"><div class="mode-switch"><button class="mode-btn active" data-mode="shade" onclick="setMode(this.dataset.mode)">Shade</button><button class="mode-btn" data-mode="search" onclick="setMode(this.dataset.mode)">Search</button><button type="button" class="tap-add-btn" id="tapAddBtnPanel" aria-pressed="false" onclick="toggleTapToAdd()">Tap to add</button><button type="button" class="mode-btn clear-all" onclick="clearAllFilters()">Clear</button></div><div class="cat-switch" id="catSwitch"><button class="cat-btn active" data-cat="all" onclick="setCat(this.dataset.cat)">All</button><button class="cat-btn" data-cat="instrument" onclick="setCat(this.dataset.cat)">Instrument</button><button class="cat-btn" data-cat="brand" onclick="setCat(this.dataset.cat)">Brand</button><button class="cat-btn" data-cat="model" onclick="setCat(this.dataset.cat)">Model</button><button class="cat-btn" data-cat="vibe" onclick="setCat(this.dataset.cat)">Vibe</button><button class="cat-btn" data-cat="patch" onclick="setCat(this.dataset.cat)">Patch</button></div><div id="kwbar"></div><p id="kwstatus" class="kwstatus"></p></div></div></div>'
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
MODAL
  cat <<'JS'
<script>
JS
  if [ "$MODE" = portable ]; then echo 'var CATALOG_PORTABLE=true;window.CATALOG_PORTABLE=true;'; else echo 'var CATALOG_PORTABLE=false;window.CATALOG_PORTABLE=false;'; fi
echo 'var CATALOG_NS="kontakt";window.CATALOG_NS="kontakt";';
  cat <<'JS'
function syncSearchHideBtn(){
  var collapsed=document.body.classList.contains('search-chrome-collapsed');
  document.querySelectorAll('.search-strip-hide').forEach(function(b){
    b.textContent=collapsed?'Show search':'Hide search';
    b.setAttribute('aria-expanded',collapsed?'false':'true');
  });
  var w=document.getElementById('filterWrap');
  var t=document.getElementById('filterToggle');
  if(t)t.setAttribute('aria-expanded',w&&w.classList.contains('open')?'true':'false');
}
function toggleFilter(){
  var w=document.getElementById('filterWrap'),a=document.querySelector('.toggle-arrow');
  if(!w)return;
  w.classList.toggle('open');
  var open=w.classList.contains('open');
  if(a)a.textContent=open?'▲':'▼';
  syncSearchHideBtn();
  if(open&&typeof window.restoreFilterUi==='function')window.restoreFilterUi();
}
function collapseSearchMenu(){
  document.body.classList.add('search-chrome-collapsed','search-extras-collapsed');
  var ac=document.getElementById('acList');
  if(ac){ac.classList.remove('open');ac.innerHTML='';}
  var si=document.getElementById('searchInput');
  if(si)si.blur();
  syncSearchHideBtn();
}
function expandSearchMenu(){
  document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed');
  syncSearchHideBtn();
  if(typeof window.restoreSearchUi==='function')window.restoreSearchUi();
  var si=document.getElementById('searchInput');
  if(si)setTimeout(function(){si.focus();},50);
}
function toggleSearchChrome(){
  if(document.body.classList.contains('search-chrome-collapsed')) expandSearchMenu();
  else collapseSearchMenu();
}
function setTheme(t){document.documentElement.setAttribute('data-theme',t);localStorage.setItem('catalog-theme',t);}
(function(){var t=localStorage.getItem('catalog-theme')||'desert';document.documentElement.setAttribute('data-theme',t);var p=document.getElementById('themePicker');if(p)p.value=t;})();

var FAV_KEY='catalog-fav-'+(window.CATALOG_NS||'catalog');
var NOTES_KEY='catalog-notes-'+(window.CATALOG_NS||'catalog');
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
 var PATCH_SET={}, patchCounts={};
 entries.forEach(function(el){patches(el).forEach(function(k){PATCH_SET[k]=1;patchCounts[k]=(patchCounts[k]||0)+1;});});
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
   if(activeCat==='patch')return patches(el).length>0;
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
 function syncTapToAddBtns(){
   document.querySelectorAll('.tap-add-btn').forEach(function(b){
     b.setAttribute('aria-pressed',tapToAdd?'true':'false');
     b.classList.toggle('on',tapToAdd);
   });
   document.body.classList.toggle('tap-to-add',!!(tapToAdd&&currentMode==='search'));
 }
 window.toggleTapToAdd=function(){
   tapToAdd=!tapToAdd;
   try{localStorage.setItem(TAP_ADD_KEY,tapToAdd?'1':'0');}catch(err){}
   syncTapToAddBtns();
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
     hits.forEach(function(el){patches(el).forEach(function(k){if(active.indexOf(k)<0)pcounts[k]=(pcounts[k]||0)+1;});});
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
     currentMode='shade';
     document.querySelectorAll('.mode-btn').forEach(function(b){b.classList.toggle('active',b.dataset.mode==='shade');});
     document.body.classList.remove('search-mode','search-extras-collapsed','search-chrome-collapsed');if(window.syncSearchHideBtn)window.syncSearchHideBtn();
     if(searchInput)searchInput.blur();
     if(acList){acList.classList.remove('open');acList.innerHTML='';}
     entries.forEach(function(el){el.style.display='';el.classList.remove('dim','is-hidden','fav-rec');});
     document.body.classList.remove('search-empty-recs');
     render();
     syncTapToAddBtns();
     return;
   }
   currentMode=mode;
   document.querySelectorAll('.mode-btn').forEach(function(b){b.classList.toggle('active',b.dataset.mode===mode);});
   document.body.classList.toggle('search-mode',mode==='search');
   document.body.classList.remove('search-extras-collapsed','search-chrome-collapsed');if(window.syncSearchHideBtn)window.syncSearchHideBtn();
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
       html+='<div class="ac-item" data-cat="'+c+'" onclick="pickAc(\''+jsStr(o.label||o.k)+'\')"><span class="ac-label">'+htmlStr(o.label||o.k)+acNoteIcon(o)+'</span> <span class="ac-count">'+o.c+'</span></div>';
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
 function showAc(q){
   if(document.body.classList.contains('search-extras-collapsed')){if(acList){acList.classList.remove('open');acList.innerHTML='';}return;}
   var src=suggestFromHits();
   var list=q?src.filter(function(o){return o.k.indexOf(q)>=0||(o.label&&o.label.toLowerCase().indexOf(q)>=0);}):src;
   if(q&&q.length>=2){
     suggestPatchNames(q,currentHits(),16).forEach(function(o){
       if(!list.some(function(x){return x.k===o.k;}))list.push(o);
     });
   }
   var html=acHtml(list,40,!q);
   acList.innerHTML=html;acList.classList.toggle('open',html.length>0);
 }
 searchInput.addEventListener('input',function(){
   var q=searchInput.value.trim().toLowerCase();
   showAc(q);
   applySearch();
 });
 searchInput.addEventListener('focus',function(){if(document.body.classList.contains('search-extras-collapsed'))return;showAc(searchInput.value.trim().toLowerCase());});
 searchInput.addEventListener('keydown',function(e){
   if(e.key==='Enter'){
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
   if(acList){acList.classList.remove('open');acList.innerHTML='';}
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
 };
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
   var emptySearch=!hasPills&&!typed;
   if(grid)grid.style.display='';
   entries.forEach(function(el){
     var kwMatch=!hasPills||searchKeywords.every(function(k){return pillMatch(el,k);});
     var qMatch=!typedLc||typedMatch(el,typedLc);
     var show=kwMatch&&catMatch(el)&&qMatch;
     el.style.display=show?'':'none';
     el.classList.toggle('is-hidden',!show);
     el.classList.toggle('hit',(hasPills||!!typedLc)&&show);
     el.classList.remove('dim');
     el.classList.toggle('fav-rec',!!(emptySearch&&show&&el.classList.contains('is-fav')));
   });
   idx.forEach(function(li){
     var el=entryForIdx(li);
     var kwMatch=el&&(!hasPills||searchKeywords.every(function(k){return pillMatch(el,k);}));
     var qMatch=el&&(!typedLc||typedMatch(el,typedLc));
     var show=!!el&&kwMatch&&catMatch(el)&&qMatch;
     li.classList.toggle('hit',(hasPills||!!typedLc)&&show);
     li.style.display=show?'':'none';
   });
   var anyRec=emptySearch&&entries.some(function(el){return el.classList.contains('fav-rec');});
   document.body.classList.toggle('search-empty-recs',!!anyRec);
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
 window.clearAllFilters=function(){
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
 render();
})();
function shownHits(){
  return [].slice.call(document.querySelectorAll('.entry')).filter(entryIsShown);
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
  closeChosenPreview();
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
  closeChosenPreview();
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
  if(el.classList.contains('highlight')||document.body.classList.contains('hl-open')){
    rememberViewed(el);
    return;
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
function closeChosenPreview(){
  var modal=document.getElementById('searchModal');
  if(modal)modal.classList.remove('open');
  document.body.classList.remove('search-modal-open');
  document.body.classList.remove('chosen-preview-open');
  setOverlayFocus(null);
  unpinSelectedForPreview();
  collapseOversizedGridPatches();
}
var previewPh=null;
function openOverlay(el){
  if(!el)return;
  if(document.body.classList.contains('search-modal-open'))closeSearchModal();
  closeChosenPreview();
  rememberViewed(el);
  if(el.classList.contains('highlight')){
    var bd=document.getElementById('hlBackdrop');
    if(bd)bd.classList.add('open');
    document.body.classList.add('hl-open');
    return;
  }
  closeOverlay({skipScroll:true});
  rememberViewed(el);
  var ph=document.createElement('div');
  ph.className='hl-ph';
  ph.setAttribute('aria-hidden','true');
  ph.style.width=el.offsetWidth+'px';
  ph.style.minHeight=el.offsetHeight+'px';
  el.parentNode.insertBefore(ph,el);
  el.classList.add('highlight');
  var backdrop=document.getElementById('hlBackdrop');
  if(backdrop)backdrop.classList.add('open');
  document.body.classList.add('hl-open');
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
  document.querySelectorAll('.hl-ph').forEach(function(ph){if(ph.parentNode)ph.parentNode.removeChild(ph);});
  document.querySelectorAll('.entry.highlight').forEach(function(e){e.classList.remove('highlight');});
  collapseOversizedGridPatches();
  var bd=document.getElementById('hlBackdrop');
  if(bd)bd.classList.remove('open');
  document.body.classList.remove('hl-open');
  syncViewportLock();
  if(last)rememberViewed(last);
  if(wasOpen&&!opts.skipScroll)scrollViewedIntoGrid(last);
}
function switchOverlayTo(el){
  if(!el)return;
  rememberViewed(el);
  if(el.classList.contains('highlight'))return;
  document.querySelectorAll('.hl-ph').forEach(function(ph){if(ph.parentNode)ph.parentNode.removeChild(ph);});
  document.querySelectorAll('.entry.highlight').forEach(function(e){e.classList.remove('highlight');});
  collapseOversizedGridPatches();
  var ph=document.createElement('div');
  ph.className='hl-ph';
  ph.setAttribute('aria-hidden','true');
  ph.style.width=el.offsetWidth+'px';
  ph.style.minHeight=el.offsetHeight+'px';
  el.parentNode.insertBefore(ph,el);
  el.classList.add('highlight');
  var backdrop=document.getElementById('hlBackdrop');
  if(backdrop)backdrop.classList.add('open');
  document.body.classList.add('hl-open');
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
  return shownHits().filter(function(el){return el.querySelector('.cover img');});
}
var galleryIndex=0;
var imgFocusSwiped=false;
var overlayPinching=false;
var skipSwipeAfterPinch=false;
var VIEWPORT_BASE='width=device-width, initial-scale=1, viewport-fit=cover';
var VIEWPORT_LOCKED=VIEWPORT_BASE+', maximum-scale=1, user-scalable=no';
function overlayFocusOpen(){
  var b=document.body.classList;
  return b.contains('gallery-open')||b.contains('img-focus-open')||b.contains('desc-focus-open')||b.contains('desc-reader-open')||b.contains('path-focus-open')||b.contains('path-reader-open');
}
function syncViewportLock(){
  var m=document.getElementById('catalogViewport')||document.querySelector('meta[name="viewport"]');
  if(!m)return;
  m.setAttribute('content', overlayFocusOpen()?VIEWPORT_LOCKED:VIEWPORT_BASE);
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
  var hits=galleryHits();
  var idx=hits.indexOf(el);
  if(idx<0)return;
  galleryIndex=idx;
  showGallerySlide(idx);
  gal.classList.add('open');
  gal.setAttribute('aria-hidden','false');
  document.body.classList.add('gallery-open');
  setImgFocusScale(1);
  syncViewportLock();
}
function closeGallery(keepClosed){
  var gal=document.getElementById('imgGallery');
  if(!gal||!gal.classList.contains('open'))return;
  var last=null;
  try{last=galleryHits()[galleryIndex];}catch(err){}
  last=last||lastViewedEntry||document.querySelector('.entry.selected');
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
  var sel=last||document.querySelector('.entry.selected');
  if(sel&&!sel.classList.contains('highlight'))openOverlay(sel);
  else revealLastViewed();
}
function galleryStep(dir){
  showGallerySlide(galleryIndex+(dir||1));
}
function openDescReader(el, closeTo){
  var reader=document.getElementById('descReader');
  if(!reader||!el)return;
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
  var srcImg=el.querySelector('.cover img');
  if(!srcImg||!srcImg.getAttribute('src'))return;
  var hits=galleryHits();
  var idx=hits.indexOf(el);
  if(idx>=0)galleryIndex=idx;
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
function closeImgFocus(){
  var wrap=document.getElementById('imgFocus');
  if(!wrap||!wrap.classList.contains('open'))return;
  var last=null;
  try{last=galleryHits()[galleryIndex];}catch(err){}
  last=last||lastViewedEntry||document.querySelector('.entry.selected');
  wrap.classList.remove('open');
  document.body.classList.remove('img-focus-open');
  var img=wrap.querySelector('.img-focus-img');
  if(img){img.style.transform='scale(1)';img.removeAttribute('src');img.alt='';}
  setOverlayTitle(null);
  setImgFocusScale(1);
  syncViewportLock();
  if(last)rememberViewed(last);
  revealLastViewed();
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
function activateCover(entry){
  if(!entry)return;
  if(entry.classList.contains('highlight')){
    if(typeof closeSearchModal==='function')closeSearchModal();
    if(useMobileFocus())openGallery(entry);
    else openImgFocus(entry);
    return;
  }
  if(document.body.classList.contains('chosen-preview-open')&&entry.classList.contains('selected')){
    openOverlay(entry);
    return;
  }
  if(document.body.classList.contains('search-mode')){
    openChosenPreview(entry);
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
  var hits=shownHits();
  var selEl=document.querySelector('.entry.selected');
  if(selEl&&hits.indexOf(selEl)<0)clearSelect();
  var hl=document.querySelector('.entry.highlight');
  if(hl&&hits.indexOf(hl)<0)closeOverlay();
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
  if(card){
    if(overlayOn){
      markSelected(card);
      rememberViewed(card);
    } else {
      openChosenPreview(card);
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
  if (e.key !== 'Escape') return;
  var ac=document.getElementById('acList');
  var acOpen=ac&&ac.classList.contains('open');
  var searchUi=e.target.closest&&e.target.closest('#searchInput,#acList,#searchStrip,.search-chrome,.search-col,.search-autocomplete,.search-active-pills,#filterWrap');
  var modal=document.getElementById('searchModal');
  var modalOpen=modal&&modal.classList.contains('open');
  if(modalOpen){
    closeSearchModal();
    e.preventDefault();
    return;
  }
  if(acOpen){
    ac.classList.remove('open');
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
  if(e.target.closest('#searchModal,.search-chrome,.filter-wrap,.search-strip,.search-autocomplete,.search-active-pills,.top,.tap-add-btn,#kwbar,.kw,.mode-switch,.cat-switch,.fav-btn,.note-pop,.note-balloon,.preview-back')) return;
  if(!(e.target.closest&&e.target.closest('.note-pop,.note-balloon'))&&typeof window.closeAllNotePops==='function')window.closeAllNotePops();
  var entry=e.target.closest('.entry');
  if(entry){
    if(e.target.closest('a,.hl-close,.preview-back,.kw,input,select,textarea,summary,.patches,.search-popup-btn,.search-link,.fav-btn,.note-balloon,.note-pop,.un-badge,.note-save,.note-cancel,.fs-btn')) return;
    if(e.target.closest('.cover')){activateCover(entry);return;}
    if(e.target.closest('.summary-panel .desc')){activateDesc(entry);return;}
    if(e.target.closest('.path')){activatePath(entry);return;}
    if(entry.classList.contains('highlight'))return;
    if(e.target.closest('h3,.lib-name')){openChosenPreview(entry);return;}
    if(e.target.closest('button')) return;
    if(document.body.classList.contains('chosen-preview-open')&&entry.classList.contains('selected'))return;
    selectEntry(entry);
    return;
  }
  if(document.querySelector('.entry.highlight'))return;
  if(document.body.classList.contains('chosen-preview-open')){closeChosenPreview();return;}
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
    var dx=e.clientX-sx,dy=e.clientY-sy;
    var adx=Math.abs(dx),ady=Math.abs(dy);
    if(adx<40&&ady<40)return;
    var forward=(adx>=ady)?(dx<0):(dy<0);
    galleryStep(forward?1:-1);
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
    var dx=e.clientX-sx,dy=e.clientY-sy;
    var adx=Math.abs(dx),ady=Math.abs(dy);
    if(adx<40&&ady<40)return;
    imgFocusSwiped=true;
    var forward=(adx>=ady)?(dx<0):(dy<0);
    showImgFocusSlide(galleryIndex+(forward?1:-1));
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
