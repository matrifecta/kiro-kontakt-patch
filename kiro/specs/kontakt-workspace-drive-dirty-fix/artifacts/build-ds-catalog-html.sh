#!/usr/bin/env bash
# build-ds-catalog-html.sh
# DecentSampler catalog, LIBRARY-level with nested collapsible patch groups.
# Each library (a .dsbundle, or a folder containing .dspreset files) is one entry with: cover, description
# (readme, junk-filtered), keyword tags, [open folder] (desktop), and a collapsible list of its patches
# (.dspreset) grouped by subfolder. Modes: desktop | portable | both.
set -u
ART_DIR="/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts"
MODE="${1:-desktop}"
if [ "$MODE" = both ]; then bash "$0" desktop && bash "$0" portable; exit $?; fi
if [ "$MODE" = portable ]; then OUT="$ART_DIR/DS-CATALOG-portable.html"; else OUT="$ART_DIR/DS-CATALOG.html"; fi
THUMBS="$ART_DIR/catalog-thumbs"; MANUAL="$ART_DIR/covers-manual"; OVERRIDES="$ART_DIR/cover-overrides.tsv"
IDX="$ART_DIR/.idx.tmp"; BODY="$ART_DIR/.body.tmp"
HOME_LIB="$HOME/.config/DecentSampler/Sample Libraries"
BTRFS="/mnt/btrfs_disk/DS Libraries"; WDB="/mnt/wd_black/DS Libraries"
mkdir -p "$MANUAL"; rm -rf "$THUMBS"; mkdir -p "$THUMBS"; : > "$IDX"; : > "$BODY"
HAVE_MAGICK=0; { command -v magick >/dev/null 2>&1 || command -v convert >/dev/null 2>&1; } && HAVE_MAGICK=1
N=0
esc(){ sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g'; }
e(){ printf '%s' "$1" | esc; }
eattr(){ printf '%s' "$1" | sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g' -e 's/"/\&quot;/g'; }
slug(){ echo "$1" | tr -c 'A-Za-z0-9._-' '_' | cut -c1-70; }

override_cover(){ [ -f "$OVERRIDES" ] || return 0; local want="$1" n p
  while IFS=$'\t' read -r n p; do [ "$n" = "$want" ] || continue; [ -f "$p" ] && { printf '%s' "$p"; return 0; }; done < "$OVERRIDES"; }
# view-artwork URL override: cover-view-urls.tsv  <entry name><TAB><https url to the image/page>
VIEWURLS="$ART_DIR/cover-view-urls.tsv"
view_url(){ [ -f "$VIEWURLS" ] || return 0; local want="$1" n u
  while IFS=$'\t' read -r n u; do case "$n" in \#*) continue;; esac; [ "$n" = "$want" ] || continue; [ -n "$u" ] && { printf '%s' "$u"; return 0; }; done < "$VIEWURLS"; }

# return cover image candidates in priority order; caller iterates until emit_cover succeeds.
# tier1=named cover/bg/artwork, tier2=Images/Resources dirs (largest first), tier3=rest (largest first).
# Extra exclusions: sprite|filmstrip|_anim catch UI animation strips missed by name alone.
primary_images(){ local d="$1" all
  all=$(find "$d" -maxdepth 3 -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.gif' -o -iname '*.bmp' -o -iname '*.webp' \) 2>/dev/null \
        | grep -viE '/__MACOSX/|/\._' | grep -viE 'knob|dial|fader|slider|button|hover|switch|led|arrow|sprite|filmstrip|_anim')
  printf '%s\n' "$all" | grep -iE 'background|cover|artwork|(^|/)bg[_.-]|_bg\.'
  printf '%s\n' "$all" | grep -iE '/(Images|Image|Resources|Samples)/' | while IFS= read -r f; do
    printf '%s\t%s\n' "$(stat -c%s "$f" 2>/dev/null||echo 0)" "$f"; done | sort -rn | cut -f2-
  printf '%s\n' "$all" | grep -viE '/(Images|Image|Resources|Samples)/' | \
    grep -viE 'background|cover|artwork|(^|/)bg[_.-]|_bg\.' | while IFS= read -r f; do
    printf '%s\t%s\n' "$(stat -c%s "$f" 2>/dev/null||echo 0)" "$f"; done | sort -rn | cut -f2-
}

desc_for(){ local d="$1" rf raw txt
  rf=$(find "$d" -maxdepth 2 -type f \( -iname 'readme*' -o -iname 'read me*' -o -iname '*description*' -o -iname 'about*' -o -iname 'info*.txt' \) 2>/dev/null | grep -viE '/__MACOSX/|/\._' | head -1)
  [ -z "$rf" ] && return 0
  case "$(file -b --mime-type "$rf" 2>/dev/null)" in text/*|application/rtf) : ;; *) return 0 ;; esac
  raw=$(tr -d '\000' < "$rf" 2>/dev/null)
  if printf '%s' "$raw" | head -c 6 | grep -q '{\\rtf'; then
    txt=$(printf '%s' "$raw" | sed -e 's/\\par[d]*/\n/g' -e 's/{\\[^ }]*//g' -e 's/\\[a-zA-Z]*[0-9]*//g' -e 's/[{}]//g')
  else txt="$raw"; fi
  txt=$(printf '%s\n' "$txt" | sed 's/\r$//' \
    | grep -viE '^[[:space:]]*[-=_*#]{3,}[[:space:]]*$' \
    | grep -viE '^[[:space:]]*(the story|story|usage|faq|included formats|release notes|date:|by:|created by:|profile:|version|contents|table of contents|version history|readme file|changelog|copyright|license)' \
    | grep -viE 'decentsampler.com|pianobook.co.uk|hyperlink|requires kontakt|drag the|\.dslibrary' \
    | grep -viE '/mnt/|/home/|file://|[A-Za-z]:[\\/]' \
    | sed '/^[[:space:]]*$/d' | tr '\n' ' ' | sed 's/  */ /g; s/^ //')
  case "$(printf '%s' "$txt" | tr 'A-Z' 'a-z')" in *"your full name"*|*"your sample pack"*|*"new feature one"*|*"[1.x]"*|*"lorem ipsum"*) return 0;; esac
  printf '%s' "$txt" | cut -c1-2500 | sed 's/[[:space:]]*$//'; }

# 1–5 sentence catalog blurb. Same cleaner as Kontakt; fallback is product + tags.
desc_blurb(){
  local name="${1:-}" text="${2:-}" kw="${3:-}" product="${4:-Decent Sampler library}"
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

KEYWORDS="piano keys organ harmonium celeste harpsichord clavinova wurlitzer choir vocal voice \
strings violin cello viola domra guitar bass bassoon harp mandolin lute \
flute recorder ocarina whistle woodwind reed clarinet oboe \
drum percussion kalimba bell glock chimes bodhran tabla xylophone marimba \
synth pad drone ambient texture noise fx bowed \
accordion saxophone harmonica melodica bagpipe didgeridoo flutina \
ukulele autoharp lapsteel dobro hurdy lyre erhu kantele gusli bandola guitarron jaw \
tongue bowl cajon djembe udu clave \
fm granular glitch lofi vintage cinematic orchestral ethereal atmospheric hybrid \
gretsch"
classify(){ local w; w=$(printf '%s' "${1:-}" | tr 'A-Z' 'a-z' | tr -c 'a-z0-9' ' '); local o=""
  for k in $KEYWORDS; do case " $w " in *" $k "*) o="$o $k";; esac; done; printf '%s' "${o# }"; }

# searchable tokens from the library display name (All other / Search). not shown as .kw buttons.
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

# curated gear/rack terms to look for in the DESCRIPTION text (specific, low false-positive).
# tokens use lowercase; multi-char models kept as single tokens.
GEAR="808 909 707 606 727 cr-78 cr78 tr-808 tr-909 linndrum juno jupiter moog minimoog \
mellotron rhodes wurlitzer prophet oberheim korg roland yamaha dx7 casio sh-101 ms-20 \
op-1 volca arp emu fairlight ppg synclavier hammond leslie optigan chamberlin \
steinway broadwood ensoniq dfam ibanez casiotone digitech tx81z selmer"
classify_desc(){ local d; d=$(printf '%s' "${1:-}" | tr 'A-Z' 'a-z'); local o=""
  for k in $GEAR; do case "$d" in *"$k"*) o="$o $k";; esac; done; printf '%s' "${o# }"; }

# ---- category map for keyword buttons (emitted as JS object at build time) ----
KW_CATS_JS='{"piano":"instrument","keys":"instrument","organ":"instrument","harmonium":"instrument","celeste":"instrument","harpsichord":"instrument","clavinova":"model","wurlitzer":"instrument","choir":"instrument","vocal":"instrument","voice":"instrument","strings":"instrument","string":"instrument","violin":"instrument","cello":"instrument","viola":"instrument","domra":"instrument","guitar":"instrument","bass":"instrument","bassoon":"instrument","harp":"instrument","mandolin":"instrument","lute":"instrument","flute":"instrument","recorder":"instrument","ocarina":"instrument","whistle":"instrument","woodwind":"instrument","reed":"instrument","clarinet":"instrument","oboe":"instrument","drum":"instrument","drums":"instrument","percussion":"instrument","kalimba":"instrument","bell":"instrument","bells":"instrument","glock":"instrument","chimes":"instrument","bodhran":"instrument","tabla":"instrument","tablas":"instrument","xylophone":"instrument","marimba":"instrument","synth":"instrument","pad":"instrument","bowed":"instrument","accordion":"instrument","saxophone":"instrument","harmonica":"instrument","melodica":"instrument","bagpipe":"instrument","didgeridoo":"instrument","flutina":"instrument","ukulele":"instrument","autoharp":"instrument","lapsteel":"instrument","dobro":"instrument","hurdy":"instrument","lyre":"instrument","erhu":"instrument","kantele":"instrument","gusli":"instrument","bandola":"instrument","guitarron":"instrument","jaw":"instrument","tongue":"instrument","bowl":"instrument","cajon":"instrument","djembe":"instrument","udu":"instrument","clave":"instrument","brass":"instrument","horn":"instrument","gamelan":"instrument","orchestra":"instrument","guitarist":"instrument","mellotron":"instrument","rhodes":"instrument","hammond":"instrument","optigan":"instrument","chamberlin":"instrument","fairlight":"instrument","synclavier":"instrument","gretsch":"brand","moog":"brand","oberheim":"brand","korg":"brand","roland":"brand","yamaha":"brand","casio":"brand","arp":"brand","emu":"brand","ppg":"brand","steinway":"brand","broadwood":"brand","ensoniq":"brand","ibanez":"brand","digitech":"brand","selmer":"brand","stradivari":"brand","amati":"brand","guarneri":"brand","808":"model","909":"model","707":"model","606":"model","727":"model","cr-78":"model","cr78":"model","tr-808":"model","tr-909":"model","linndrum":"model","juno":"model","jupiter":"model","minimoog":"model","prophet":"model","dx7":"model","sh-101":"model","ms-20":"model","op-1":"model","volca":"model","leslie":"model","dfam":"model","casiotone":"model","tx81z":"model","drone":"vibe","ambient":"vibe","texture":"vibe","noise":"vibe","fx":"vibe","fm":"vibe","granular":"vibe","glitch":"vibe","lofi":"vibe","vintage":"vibe","cinematic":"vibe","orchestral":"vibe","ethereal":"vibe","atmospheric":"vibe","hybrid":"vibe","world":"vibe","analog":"vibe","soul":"vibe"}'

# returns 0 and prints an <img> if the source is a USABLE image; returns 1 if degenerate so the
# caller can try the next candidate. Rejects: <16px dims, sprite strips (h>w*5), unreadable.
# Flattens alpha to white before JPEG conversion; uses correct MIME type if fallback is needed.
emit_cover(){ local src="$1" name="$2"
  if [ "$HAVE_MAGICK" -eq 1 ]; then
    local dim w ht; dim=$(magick identify -format '%w %h' "$src"[0] 2>/dev/null || identify -format '%w %h' "$src"[0] 2>/dev/null)
    w=${dim%% *}; ht=${dim##* }
    case "$w$ht" in ''|*[!0-9]*) return 1;; esac   # couldn't read dims -> unusable
    [ "$w" -ge 16 ] 2>/dev/null && [ "$ht" -ge 16 ] 2>/dev/null || return 1
    [ "$ht" -gt $((w * 5)) ] 2>/dev/null && return 1   # sprite / filmstrip: would render as vertical line
  fi
  local h q; if [ "$MODE" = portable ]; then h=110; q=70; else h=160; q=85; fi
  local b64="" mime="image/jpeg"
  if [ "$HAVE_MAGICK" -eq 1 ]; then local s="$THUMBS/.m_$N.jpg"
    { magick "$src" -background white -flatten -resize x$h -quality $q "$s" 2>/dev/null || \
      convert "$src" -background white -flatten -resize x$h -quality $q "$s" 2>/dev/null; }
    [ -f "$s" ] && b64=$(base64 -w0 "$s") && rm -f "$s"; fi
  if [ -z "$b64" ]; then
    b64=$(base64 -w0 "$src" 2>/dev/null)
    mime=$(file --mime-type -b "$src" 2>/dev/null); [ -z "$mime" ] && mime="image/png"
  fi
  [ -z "$b64" ] && return 1
  printf '  <div class="cover"><img src="data:%s;base64,%s" alt="%s"></div>\n' "$mime" "$b64" "$(e "$name")"
  return 0; }

# list patches (.dspreset) under a library dir, grouped by their immediate subfolder relative to the lib dir
emit_patches(){ local libdir="$1"
  local list; list=$(find "$libdir" -maxdepth 4 -iname '*.dspreset' 2>/dev/null | grep -viE '/__MACOSX/|/\._' | sort -f)
  [ -z "$list" ] && { printf '  <div class="nopatch"><i>no .dspreset patches found</i></div>\n'; return; }
  local count; count=$(printf '%s\n' "$list" | grep -c .)
  printf '  <details class="patches"><summary>%s patch(es)</summary>\n' "$count"
  # group by relative subdir (dir path minus libdir); "" = root of library
  local prevgrp="__none__"
  printf '%s\n' "$list" | while IFS= read -r p; do
    local rel="${p#$libdir/}"; local grp; grp=$(dirname "$rel"); [ "$grp" = "." ] && grp="(root)"
    if [ "$grp" != "$prevgrp" ]; then
      [ "$prevgrp" != "__none__" ] && printf '    </ul>\n'
      printf '    <div class="grp">%s</div><ul>\n' "$(e "$grp")"; prevgrp="$grp"
    fi
    printf '      <li>%s</li>\n' "$(e "$(basename "$p" .dspreset)")"
  done
    printf '    </ul>\n  </details>\n'; }

# collect .dspreset filenames (without extension) as patch/preset name list for a library
# uses a while-read loop instead of xargs to safely handle apostrophes/spaces in filenames
patch_names(){ local libdir="$1"
  find "$libdir" -maxdepth 4 -name '*.dspreset' 2>/dev/null \
    | while IFS= read -r f; do basename "$f" .dspreset; done \
    | tr '\n' ' '; }

# ---- one entry per LIBRARY ----  args: display_name  library_dir  loadable_path(for open:)
entry(){ local name="$1" libdir="$2" openp="$3"
  N=$((N+1)); local id="item-$N"
  local d; d=$(desc_for "$libdir")
  local kw; kw=$(classify "$name $d $(patch_names "$libdir")")   # name + desc + preset names feed instrument tags
  local gkw; gkw=$(classify_desc "$d")  # desc feeds gear/brand tags (purple)
  local allkw; allkw=$(printf '%s %s' "$kw" "$gkw" | sed 's/^ //;s/ $//')
  local dsc; dsc=$(desc_blurb "$name" "$d" "$allkw" "Decent Sampler library")
  local ntoks; ntoks=$(name_tokens "$name")
  local other; other=$(other_from_name "$allkw" "$ntoks")
  local enc; enc=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote_plus(sys.argv[1]))" "$name" 2>/dev/null || printf '%s' "$name" | sed 's/ /+/g; s/&/%26/g; s/"/%22/g')
  local yturl weburl imgurl
  yturl=$(printf 'https://www.youtube.com/results?search_query=%s+decent+sampler' "$enc")
  weburl=$(printf 'https://www.google.com/search?q=%s+vst+instrument' "$enc")
  imgurl=$(printf 'https://www.google.com/search?tbm=isch&q=%s+decent+sampler' "$enc")
  printf '<li data-kw="%s"><a href="#%s">%s</a></li>\n' "$(e "$allkw")" "$id" "$(e "$name")" >> "$IDX"
  {
    printf '<div class="entry" id="%s" data-kw="%s" data-gear="%s" data-name="%s" data-other="%s">\n' "$id" "$(e "$allkw")" "$(e "$gkw")" "$(eattr "$name")" "$(e "$other")"
    printf '  <h3>%s</h3>\n' "$(e "$name")"
    local shown=0
    # iterate candidates: manual override first, then auto-detected (deduped); stop on first usable image
    while IFS= read -r prim; do
      [ -z "$prim" ] && continue; [ -f "$prim" ] || continue
      emit_cover "$prim" "$name" && { shown=1; break; }
    done < <({ oc=$(override_cover "$name"); [ -n "$oc" ] && printf '%s\n' "$oc"
               primary_images "$libdir"; } | awk '!seen[$0]++')
    if [ "$shown" -eq 0 ]; then
      local vu; vu=$(view_url "$name")
      if [ -z "$vu" ]; then
        # auto: web-search link (never 404s) so you can find/open the artwork
        local q; q=$(printf '%s decent sampler' "$name" | sed 's/ /+/g; s/&/%26/g')
        vu="https://www.google.com/search?q=$q&tbm=isch"
      fi
      printf '  <div class="noart"><i>no artwork</i> &nbsp;<a class="viewart" href="%s" target="_blank" rel="noopener">[find artwork &#8599;]</a></div>\n' "$(e "$vu")"
    fi
    printf '  <div class="summary-panel">\n'
    printf '    <p class="desc">%s</p>\n' "$(e "$dsc")"
    printf '    <button type="button" class="summary-google" onclick="openSearchModal(this);event.stopPropagation()" data-yt="%s" data-web="%s" data-img="%s" data-name="%s">Search on Google</button>\n' "$(e "$yturl")" "$(e "$weburl")" "$(e "$imgurl")" "$(e "$name")"
    printf '  </div>\n'
    if [ "$MODE" = portable ]; then
      printf '  <div class="path"><b>open:</b> <code>%s</code></div>\n' "$(e "$openp")"
    else
      local url; url="file://$(printf '%s' "$libdir" | sed 's/ /%20/g')"
      printf '  <div class="path"><b>open:</b> <code>%s</code> &nbsp;<a class="folder" href="%s">[open folder]</a></div>\n' "$(e "$openp")" "$(e "$url")"
    fi
    emit_patches "$libdir"
    local act_cls="card-actions"; [ "$shown" -eq 0 ] && act_cls="card-actions card-actions--noart"
    printf '  <div class="%s">\n' "$act_cls"
    printf '    <button class="search-link search-popup-btn" onclick="openSearchModal(this);event.stopPropagation()" data-yt="%s" data-web="%s" data-img="%s" data-name="%s">&#x1F50D; Search</button>\n' "$(e "$yturl")" "$(e "$weburl")" "$(e "$imgurl")" "$(e "$name")"
    printf '  </div>\n'
    printf '</div>\n'
  } >> "$BODY"; }

# enumerate LIBRARIES in a root: each .dsbundle is a library; plus each top-level folder that (recursively)
# contains .dspreset files but is NOT inside a .dsbundle. Dedup so a folder isn't listed twice.
list_libraries(){ local root="$1"
  # .dsbundle libraries
  find "$root" -maxdepth 6 -iname '*.dsbundle' -type d 2>/dev/null | grep -viE '/__MACOSX/|/\._|/_kiro_nonds_trash_' | while read -r b; do
    printf '%s\t%s\t%s\n' "$(basename "$b" .dsbundle)" "$b" "$b"
  done
  # loose-preset libraries: top-level dirs under root that contain .dspreset (not within a .dsbundle)
  find "$root" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | grep -viE '/__MACOSX/|/_kiro_nonds_trash_' | while read -r d; do
    # skip if this top dir IS a dsbundle (already handled) 
    case "$d" in *.dsbundle) continue;; esac
    # does it contain any .dspreset NOT inside a .dsbundle?
    local hit; hit=$(find "$d" -maxdepth 4 -iname '*.dspreset' 2>/dev/null | grep -viE '/__MACOSX/|/\._|\.dsbundle/' | head -1)
    [ -z "$hit" ] && continue
    printf '%s\t%s\t%s\n' "$(basename "$d")" "$d" "$hit"
  done
}

section(){ printf '<h2>%s</h2>\n' "$(e "$1")" >> "$BODY"; }

section "1. Via SAMPLE STORE (DS default folder)"
printf '<p>Folder: <code>%s</code></p>\n' "$(e "$HOME_LIB")" >> "$BODY"
while IFS=$'\t' read -r nm dir openp; do [ -z "$nm" ] && continue; entry "$nm" "$dir" "$openp"; done < <(list_libraries "$HOME_LIB" | sort -f | uniq)

do_drive(){ section "$1"
  printf '<p>FILE BROWSER &rarr; <b>%s</b> &rarr; <code>DS Libraries</code>. Root: <code>%s</code></p>\n' "$(e "$3")" "$(e "$2")" >> "$BODY"
  [ -d "$2" ] || { printf '<p><i>(drive not present)</i></p>\n' >> "$BODY"; return; }
  while IFS=$'\t' read -r nm dir openp; do [ -z "$nm" ] && continue; entry "$nm" "$dir" "$openp"; done < <(list_libraries "$2" | sort -f | uniq)
}
do_drive "2. Via FILE BROWSER - BTRFS drive" "$BTRFS" "btrfs"
do_drive "3. Via FILE BROWSER - WD_BLACK drive" "$WDB" "wd_black"

# ---- assemble ----
{
cat <<'HTML'
<!DOCTYPE html><html lang="en" data-theme="desert"><head><meta charset="utf-8"><title>DecentSampler Library Catalog</title>
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
 html{--hl-backdrop:rgba(0,0,0,.55);--hl-shadow:0 12px 48px rgba(0,0,0,.45)}
 *{box-sizing:border-box}
 body{font-family:system-ui,Segoe UI,Roboto,sans-serif;max-width:1800px;margin:0 auto;padding:clamp(8px,2vw,32px);line-height:1.5;color:var(--text);background:var(--bg);font-size:clamp(12px,1.2vw,16px)}
 h1{margin-bottom:.2rem;color:var(--text)} h2{margin-top:2rem;border-bottom:2px solid var(--border);padding-bottom:.2rem;color:var(--text-muted)}
 .filter-wrap{position:sticky;top:0;z-index:100;background:var(--bg-surface);border-bottom:1px solid var(--border)}
 .filter-toggle{width:100%;height:32px;background:transparent;border:none;cursor:pointer;color:var(--text-muted);font-size:clamp(11px,1vw,13px);text-align:left;padding:0 clamp(8px,1.5vw,16px);display:flex;align-items:center;gap:6px;user-select:none}
 .filter-panel{overflow:hidden;max-height:0;transition:max-height 0.3s ease,padding 0.3s ease;padding:0 clamp(8px,1.5vw,16px)}
 .filter-wrap.open .filter-panel{max-height:360px;padding:clamp(6px,1vw,12px) clamp(8px,1.5vw,16px)}
 .toggle-arrow{display:inline-block;transition:transform 0.3s}
 .filter-wrap.open .toggle-arrow{transform:rotate(180deg)}
 .theme-picker{margin-left:auto;background:var(--bg-card);color:var(--text-muted);border:1px solid var(--border);border-radius:4px;padding:2px 6px;font-size:clamp(10px,.9vw,12px);cursor:pointer}
 .index{column-width:260px;column-gap:2rem;font-size:.9rem;padding-left:1.2rem}
 .index li{break-inside:avoid;margin:.15rem 0;list-style:disc;overflow-wrap:break-word;word-break:normal}
 .index a{color:var(--accent-instrument);text-decoration:underline;overflow-wrap:break-word} .index li.hit{background:var(--accent-instrument-bg);border-radius:3px}
 .catalog-body{display:grid;grid-template-columns:repeat(auto-fill,minmax(clamp(200px,22vw,280px),1fr));gap:1rem;align-items:start;margin-top:1rem}
 .catalog-body>h2,.catalog-body>p{grid-column:1/-1}
 .entry{background:var(--bg-card);border:1px solid var(--border);border-radius:8px;padding:.8rem;transition:border-color .2s;display:flex;flex-direction:column;height:auto;min-height:0;overflow:hidden;order:0}
 .entry:hover{border-color:var(--accent-instrument)} .entry h3{margin:.2rem 0;color:var(--text);word-wrap:break-word;overflow-wrap:break-word;word-break:normal;hyphens:none;white-space:normal;min-width:0}
 .entry.hit{background:var(--accent-instrument-bg);border-left:4px solid var(--accent-gear);padding-left:.6rem}
 .hl-backdrop{display:none;position:fixed;inset:0;z-index:400;background:var(--hl-backdrop)}
 .hl-backdrop.open{display:block}
 .hl-ph{visibility:hidden;pointer-events:none}
 body.hl-open{overflow:hidden}
 body.hl-open .filter-wrap{z-index:410}
 body.hl-open .search-strip{z-index:412}
 body.hl-open .search-autocomplete,body.hl-open .search-active-pills{z-index:411}
 .entry.highlight{position:fixed;z-index:401;left:50%;top:50%;transform:translate(-50%,-50%);width:min(800px,92vw);height:min(600px,88vh);grid-column:auto;outline:2px solid var(--accent-instrument);outline-offset:2px;overflow:auto;display:flex;flex-direction:column;background:var(--bg-card);border:1px solid var(--border);box-shadow:var(--hl-shadow);padding:clamp(12px,1.5vw,20px)}
 .cover{flex-shrink:0;width:100%;max-width:min(100%,280px);max-height:160px;margin:.3rem 0;display:flex;align-items:center;justify-content:center;overflow:hidden;border:1px solid var(--border);border-radius:4px;background:var(--bg-surface);box-sizing:border-box}
 .cover img{width:100%;height:auto;max-width:100%;max-height:160px;object-fit:contain;object-position:center;display:block}
 .entry.highlight .cover{flex:0 1 auto;width:100%;max-width:100%;height:auto;max-height:min(35%,280px);margin:.3rem 0}
 .entry.highlight .cover img{width:100%;height:auto;max-width:100%;max-height:100%;object-fit:contain;object-position:center}
 .summary-panel{width:100%;max-width:100%;min-width:0;overflow:hidden;border-radius:6px;border:1px solid var(--border);margin:clamp(4px,0.6vw,8px) 0;padding:clamp(8px,1.1vw,14px) clamp(10px,1.2vw,16px);background:var(--bg);max-height:8.2em}
 .summary-panel .desc{font-style:normal;font-size:clamp(12px,1.15vw,15px);line-height:1.55;color:var(--text);margin:0 0 .5rem 0;overflow-wrap:break-word;word-break:normal;hyphens:none;white-space:normal;max-width:100%}
 .summary-google{display:inline-block;background:none;border:none;padding:0;color:var(--text-muted);font-size:clamp(10px,0.9vw,12px);text-decoration:underline;cursor:pointer;touch-action:manipulation}
 .summary-google:hover{color:var(--accent-instrument)}
 .entry.highlight .summary-panel,.entry.highlight .desc{min-height:calc(1.65em * 3);flex:1 1 auto;overflow-y:auto;-webkit-overflow-scrolling:touch}
 .entry.highlight .summary-panel{width:100%;max-width:100%;overflow-wrap:break-word;background:var(--bg);max-height:none}
 .entry.highlight .summary-panel .desc{max-width:65ch;margin-left:auto;margin-right:auto;margin-bottom:.75rem;line-height:1.65;overflow-wrap:break-word;word-break:normal;hyphens:none;white-space:normal;text-align:left}
 @media (min-width:900px) and (orientation:landscape){.entry.highlight{width:min(800px,92vw);height:min(600px,88vh)}.entry.highlight .cover{max-height:min(42%,280px)}}
 @media (min-width:600px) and (orientation:portrait){.entry.highlight{width:min(640px,92vw);height:min(72vh,800px)}.entry.highlight .cover{max-height:min(38%,240px)}}
 @media (max-width:899px) and (orientation:landscape){.entry.highlight{width:min(92vw,800px);height:min(88vh,480px)}.entry.highlight .cover{max-height:min(22vh,120px)}.summary-panel .desc,.entry.highlight .summary-panel .desc,.desc{font-size:clamp(16px,4.2vw,18px);line-height:1.55}.entry.highlight .summary-panel .desc,.entry.highlight .desc{line-height:1.65}.path,.path code,.path .folder,.entry.highlight .path,.entry.highlight .path code{font-size:clamp(14px,3.6vw,16px);color:var(--text-muted)}}
 @media (max-width:599px) and (orientation:portrait){.entry.highlight{width:min(94vw,640px);height:min(82vh,720px)}.entry.highlight .cover{max-height:min(28vh,180px)}.summary-panel .desc,.entry.highlight .summary-panel .desc,.desc{font-size:clamp(16px,4.2vw,18px);line-height:1.55}.entry.highlight .summary-panel .desc,.entry.highlight .desc{line-height:1.65}.path,.path code,.path .folder,.entry.highlight .path,.entry.highlight .path code{font-size:clamp(14px,3.6vw,16px);color:var(--text-muted)}}
 .path{font-size:clamp(10px,0.85vw,12px);color:var(--text-muted);margin:.35rem 0 .15rem;overflow-wrap:anywhere}
 .desc{font-style:italic;color:var(--text-muted);margin:.2rem 0;overflow-wrap:break-word;word-break:normal;min-width:0}
 code{background:var(--bg-surface);padding:.05rem .3rem;border-radius:3px;font-size:.82rem;word-break:break-all;color:var(--text-muted)}
 .folder{color:var(--accent-gear);text-decoration:underline;font-size:.82rem;white-space:nowrap}
 details.patches{margin:.3rem 0;font-size:.86rem} details.patches summary{cursor:pointer;color:var(--accent-gear);font-weight:600}
 .grp{margin:.3rem 0 .1rem;font-weight:600;color:var(--text-muted)} details.patches ul{margin:.1rem 0 .3rem 1rem}
 .nopatch{font-size:.82rem;color:var(--text-muted);opacity:.6}
 #kwbar{display:flex;flex-wrap:wrap;gap:.35rem;margin:.5rem 0}
 .kw{cursor:pointer;border:1px solid var(--accent-instrument-bg);background:var(--accent-instrument-bg);border-radius:14px;padding:clamp(2px,.3vw,4px) clamp(4px,.6vw,8px);font-size:clamp(9px,.9vw,12px);color:var(--accent-instrument);min-height:32px;touch-action:manipulation}
 .kw:hover{border-color:var(--accent-instrument)} .kw.active{background:var(--accent-instrument-active);color:#1a1008;border-color:var(--accent-instrument)}
 .kw.disabled{color:var(--text-muted);background:transparent;border-color:var(--border);cursor:not-allowed;opacity:.5}
 .kw.clear{background:rgba(180,40,40,0.2);border-color:#c03040;color:#ff9090}
 .kwstatus{font-size:.85rem;color:var(--accent-instrument);font-weight:600;min-height:1.1em}
 .kw.gear{border-color:var(--accent-gear-bg);background:var(--accent-gear-bg);color:var(--accent-gear)}
 .kw.gear:hover{border-color:var(--accent-gear)} .kw.gear.active{background:var(--accent-gear-active);color:#1a1008;border-color:var(--accent-gear)}
 .noart{font-size:.85rem;color:var(--text-muted);margin:.2rem 0} .viewart{color:var(--accent-gear);text-decoration:underline;font-weight:600}
 .top{position:fixed;bottom:1rem;right:1rem;background:var(--accent-instrument);color:#1a1008;padding:.4rem .7rem;border-radius:4px;text-decoration:none;border:1px solid var(--accent-instrument)}
 .mode-switch{display:flex;gap:4px;margin-bottom:8px}
 .mode-btn{background:var(--bg-card);border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:3px 10px;font-size:clamp(10px,.9vw,12px);cursor:pointer}
 .mode-btn.active{background:var(--accent-instrument-bg);color:var(--accent-instrument);border-color:var(--accent-instrument)}
 .entry.dim{order:999;opacity:.25;pointer-events:none}
 .card-actions{display:flex;gap:clamp(4px,0.8vw,8px);padding:clamp(4px,0.6vw,6px) 0 0 0;margin-top:auto}
 .search-link{display:inline-flex;align-items:center;gap:3px;padding:clamp(3px,0.5vw,5px) clamp(6px,1.2vw,10px);border-radius:4px;font-size:clamp(9px,0.85vw,11px);text-decoration:none;border:1px solid var(--border);color:var(--text-muted);background:var(--bg);transition:color 0.15s,border-color 0.15s;white-space:nowrap;touch-action:manipulation;min-height:28px}
 .search-link:hover{color:var(--text);border-color:var(--text-muted)}
 .search-popup-btn{display:inline-flex;align-items:center;gap:4px;padding:clamp(3px,0.5vw,5px) clamp(8px,1.5vw,12px);border-radius:4px;font-size:clamp(9px,0.85vw,11px);border:1px solid var(--border);color:var(--text-muted);background:var(--bg);cursor:pointer;touch-action:manipulation;min-height:28px;transition:color 0.15s,border-color 0.15s}
 .search-popup-btn:hover{color:var(--text);border-color:var(--text-muted)}
 .card-actions--noart .search-popup-btn{font-size:clamp(11px,1vw,13px);padding:clamp(5px,0.8vw,8px) clamp(10px,2vw,16px);min-height:36px}
 .search-modal-backdrop{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:500;align-items:center;justify-content:center;padding:clamp(8px,3vw,24px)}
 .search-modal-backdrop.open{display:flex}
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
 .search-strip{display:none;position:fixed;top:0;left:0;right:0;height:36px;background:var(--bg-surface);border-bottom:1px solid var(--border);z-index:200;padding:0 clamp(8px,2vw,20px);align-items:center;gap:8px}
 .search-mode .search-strip{display:flex}
 .search-strip input{flex:1;background:transparent;border:none;outline:none;color:var(--text);font-size:clamp(12px,1.1vw,14px);caret-color:var(--accent-instrument)}
 .search-strip input::placeholder{color:var(--text-muted)}
 .search-strip-clear{flex-shrink:0;background:transparent;border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:3px 10px;font-size:clamp(10px,.9vw,12px);cursor:pointer}
 .search-strip-clear:hover{color:var(--accent-instrument);border-color:var(--accent-instrument)}
 .mode-btn.clear-all{border-color:#c03040;color:#ff9090;background:rgba(180,40,40,0.2)}
 body.search-extras-collapsed .search-autocomplete,body.search-extras-collapsed .search-active-pills{display:none!important}
 .search-autocomplete{position:fixed;top:36px;left:0;right:0;background:var(--bg-surface);border-bottom:1px solid var(--border);z-index:199;max-height:280px;overflow-y:auto;display:none}
 .search-autocomplete.open{display:block}
 .search-autocomplete .ac-item{padding:6px clamp(8px,2vw,20px);cursor:pointer;font-size:clamp(11px,1vw,13px);color:var(--text);display:flex;justify-content:space-between}
 .search-autocomplete .ac-item:hover{background:var(--bg-card)}
 .search-autocomplete .ac-item .ac-count{color:var(--text-muted);font-size:.85em}
 .search-active-pills{display:none;flex-wrap:wrap;gap:4px;padding:clamp(4px,.5vw,8px) clamp(8px,2vw,20px);background:var(--bg-surface);border-bottom:1px solid var(--border);position:fixed;top:36px;left:0;right:0;z-index:198}
 .search-mode .search-active-pills{display:flex}
 .pill-tag{background:var(--accent-instrument-bg);color:var(--accent-instrument);border:1px solid var(--accent-instrument);border-radius:12px;padding:2px 8px;font-size:clamp(9px,.85vw,11px);cursor:pointer;display:flex;align-items:center;gap:4px}
 .pill-tag .pill-x{opacity:.7}
 .pill-tag:hover .pill-x{opacity:1}
 body.search-mode .filter-wrap{top:36px}
 .cat-switch{display:flex;flex-wrap:wrap;gap:clamp(3px,0.8vw,6px);margin-bottom:clamp(6px,1.2vw,10px)}
 .cat-btn{background:var(--bg-card);border:1px solid var(--border);color:var(--text-muted);border-radius:6px;padding:clamp(5px,1.2vw,8px) clamp(10px,2.5vw,18px);font-size:clamp(11px,1.1vw,14px);cursor:pointer;min-height:36px;touch-action:manipulation;white-space:nowrap;transition:background 0.15s,color 0.15s}
 .cat-btn.active{background:var(--accent-instrument-bg);color:var(--accent-instrument);border-color:var(--accent-instrument);font-weight:600}
 @media(max-width:400px){.cat-switch{flex-wrap:nowrap;overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;padding-bottom:4px}.cat-switch::-webkit-scrollbar{display:none}}
 .search-autocomplete .ac-group-label{padding:4px clamp(8px,2vw,20px) 2px;font-size:.75em;font-weight:700;color:var(--accent-gear);text-transform:uppercase;letter-spacing:.05em}
</style></head><body>
<h1 id="top">DecentSampler Library Catalog</h1>
HTML
printf '<p>generated: %s. Library-level; expand a library to see its patches (grouped by subfolder).</p>\n' "$(e "$(date)")"
if [ "$MODE" = portable ]; then printf '<p>Portable snapshot (images embedded; phone-safe). <b>Update:</b> desktop <code>build-ds-catalog-html.sh both</code>.</p>\n'
else printf '<p><b>Added libraries?</b> Re-run <code>build-ds-catalog-html.sh both</code>.</p>\n'; fi
echo '<div class="search-strip" id="searchStrip"><input id="searchInput" type="text" placeholder="Search libraries..." autocomplete="off"><button type="button" class="search-strip-clear" onclick="clearAllFilters()">Clear</button></div><div class="search-autocomplete" id="acList"></div><div class="search-active-pills" id="searchPills"></div>'
echo '<div class="filter-wrap" id="filterWrap"><button class="filter-toggle" id="filterToggle" onclick="toggleFilter()"><span class="toggle-arrow">&#9660;</span> Keywords<select id="themePicker" class="theme-picker" onchange="setTheme(this.value)" onclick="event.stopPropagation()"><optgroup label="— Dark —"><option value="desert">Desert Dusk</option><option value="studio">Night Studio</option><option value="smoked">Smoked Glass</option><option value="autumn-ember">Autumn Ember</option><option value="tropical-night">Tropical Night</option><option value="spring-rain">Spring Rain</option><option value="deep-winter">Deep Winter</option></optgroup><optgroup label="— Light —"><option value="sandstorm">Sand Storm</option><option value="bleached">Bleached</option><option value="spring-bloom">Spring Bloom</option><option value="summer-beach">Summer Beach</option><option value="harvest">Harvest</option><option value="arctic">Arctic</option></optgroup><optgroup label="— High Contrast —"><option value="hc-dark">HC Dark</option><option value="hc-light">HC Light</option></optgroup></select></button><div class="filter-panel" id="filterPanel"><div class="mode-switch"><button class="mode-btn active" data-mode="shade" onclick="setMode(this.dataset.mode)">Shade</button><button class="mode-btn" data-mode="search" onclick="setMode(this.dataset.mode)">Search</button><button type="button" class="mode-btn clear-all" onclick="clearAllFilters()">Clear</button></div><div class="cat-switch" id="catSwitch"><button class="cat-btn active" data-cat="all" onclick="setCat(this.dataset.cat)">All</button><button class="cat-btn" data-cat="instrument" onclick="setCat(this.dataset.cat)">Instrument</button><button class="cat-btn" data-cat="brand" onclick="setCat(this.dataset.cat)">Brand</button><button class="cat-btn" data-cat="model" onclick="setCat(this.dataset.cat)">Model</button><button class="cat-btn" data-cat="vibe" onclick="setCat(this.dataset.cat)">Vibe</button><button class="cat-btn" data-cat="other" onclick="setCat(this.dataset.cat)">All other</button></div><div id="kwbar"></div><p id="kwstatus" class="kwstatus"></p></div></div>'
echo '<h2>Index (alphabetical)</h2><ul class="index">'; sort -f "$IDX" | uniq; echo '</ul>'
echo '<div class="catalog-body">'
cat "$BODY"
echo '</div>'
echo '<a class="top" href="#top">&uarr; top</a>'
cat <<'MODAL'
<div id="hlBackdrop" class="hl-backdrop" onclick="clearHighlight()"></div>
<div id="searchModal" class="search-modal-backdrop" onclick="if(event.target===this)closeSearchModal()">
  <div class="search-modal">
    <button class="search-modal-close" onclick="closeSearchModal()">&#x2715;</button>
    <div class="search-modal-title" id="searchModalTitle"></div>
    <div class="search-modal-subtitle">Open search in a new window:</div>
    <div class="search-modal-btns">
      <a id="searchModalYT" class="search-modal-link yt" href="#" target="_blank" rel="noopener noreferrer" onclick="openPopup(this,'yt');return false;">
        &#x25B6; YouTube
      </a>
      <a id="searchModalWeb" class="search-modal-link web" href="#" target="_blank" rel="noopener noreferrer" onclick="openPopup(this,'web');return false;">
        &#x1F50D; Web Search
      </a>
      <a id="searchModalImg" class="search-modal-link img" href="#" target="_blank" rel="noopener noreferrer" onclick="openPopup(this,'img');return false;">
        &#x1F5BC; Images
      </a>
    </div>
    <div class="search-modal-hint">Opens as a resizable popup window</div>
  </div>
</div>
MODAL
cat <<'JS'
<script>
function toggleFilter(){
  var w=document.getElementById('filterWrap'),a=document.querySelector('.toggle-arrow');
  w.classList.toggle('open');
  var open=w.classList.contains('open');
  if(a)a.textContent=open?'▲':'▼';
  if(!open){if(window.closeSearchExtras)window.closeSearchExtras();}
  else if(window.showSearchExtras)window.showSearchExtras();
}
function setTheme(t){document.documentElement.setAttribute('data-theme',t);localStorage.setItem('catalog-theme',t);}
(function(){var t=localStorage.getItem('catalog-theme')||'desert';document.documentElement.setAttribute('data-theme',t);var p=document.getElementById('themePicker');if(p)p.value=t;})();
JS
printf 'var KW_CATS=%s;\n' "$KW_CATS_JS"
cat <<'JS'
(function(){
var entries=[].slice.call(document.querySelectorAll('.entry')),idx=[].slice.call(document.querySelectorAll('.index li'));
function entryForIdx(li){var a=li.querySelector('a[href^="#"]');return a?document.getElementById(a.getAttribute('href').slice(1)):null;}
function kws(el){return (el.getAttribute('data-kw')||'').split(/\s+/).filter(Boolean);}
function others(el){return (el.getAttribute('data-other')||'').split(/\s+/).filter(Boolean);}
function elName(el){return el.getAttribute('data-name')||'';}
function elNameLc(el){return elName(el).toLowerCase();}
var sel=[],bar=document.getElementById('kwbar'),st=document.getElementById('kwstatus');
// gear keywords (from descriptions) get a distinct color
var GEAR={};entries.forEach(function(el){(el.getAttribute('data-gear')||'').split(/\s+/).filter(Boolean).forEach(function(k){GEAR[k]=1;});});
var ALL=(function(){var s={};entries.forEach(function(el){kws(el).forEach(function(k){s[k]=1;});});return Object.keys(s).sort();})();
function ms(el){var s=kws(el);return sel.length>0&&sel.every(function(k){return s.indexOf(k)>=0;});}
function matching(){return entries.filter(ms);}
/* --- category filter --- */
var activeCat='all';
function kwCat(k){return KW_CATS[k]||'other';}
function catTokens(el){return kws(el).concat(others(el));}
function catMatch(el){
var ks=catTokens(el);
if(activeCat==='all')return true;
if(activeCat==='other'){
if(ks.some(function(k){return !KW_CATS[k];}))return true;
return kws(el).length===0&&!!elName(el);
}
return ks.some(function(k){return KW_CATS[k]===activeCat;});
}
var CAT_ORDER=['instrument','brand','model','vibe','other'];
var CAT_LABEL={instrument:'Instrument',brand:'Brand',model:'Model',vibe:'Vibe',other:'All other'};
window.setCat=function(cat){activeCat=cat;document.querySelectorAll('.cat-btn').forEach(function(b){b.classList.toggle('active',b.dataset.cat===cat);});if(currentMode==='search')applySearch();else render();};
/* --- mode switcher --- */
var currentMode='shade';
var searchKeywords=[];
var searchMeta={};
var kwCounts={};entries.forEach(function(el){kws(el).forEach(function(k){kwCounts[k]=(kwCounts[k]||0)+1;});});
var otherCounts={},untaggedNames={},nameLabel={};
entries.forEach(function(el){
others(el).forEach(function(k){otherCounts[k]=(otherCounts[k]||0)+1;});
var classified=kws(el),nm=elNameLc(el);
if(!nm||KW_CATS[nm])return;
searchMeta[nm]={isLibName:1,untagged:classified.length===0?1:0};
nameLabel[nm]=elName(el);
if(classified.length===0)untaggedNames[nm]=1;
if(others(el).indexOf(nm)<0)otherCounts[nm]=(otherCounts[nm]||0)+1;
});
var allKws=(function(){
var seen={},list=[];
Object.keys(kwCounts).forEach(function(k){seen[k]=1;list.push({k:k,c:kwCounts[k],untagged:0,isLibName:0,label:k});});
Object.keys(otherCounts).forEach(function(k){
if(seen[k])return;seen[k]=1;
list.push({k:k,c:otherCounts[k],untagged:untaggedNames[k]?1:0,isLibName:searchMeta[k]&&searchMeta[k].isLibName?1:0,label:nameLabel[k]||k});
});
return list.sort(function(a,b){
if(kwCat(a.k)==='other'&&kwCat(b.k)==='other'){
if(b.c!==a.c)return b.c-a.c;
return a.k<b.k?-1:a.k>b.k?1:0;
}
return b.c-a.c||(a.k<b.k?-1:a.k>b.k?1:0);
});
})();
function renderKwBar(){
var hideZero=currentMode==='search';
var active=currentMode==='search'?searchKeywords:sel;
var hits=currentHits();
var counts={};
hits.forEach(function(el){kws(el).forEach(function(k){if(active.indexOf(k)<0)counts[k]=(counts[k]||0)+1;});});
bar.innerHTML='';
if(currentMode!=='search'){
sel.forEach(function(k){var b=document.createElement('button');b.className='kw active on'+(GEAR[k]?' gear':'');b.setAttribute('data-cat',kwCat(k));b.setAttribute('data-kw',k);b.textContent=k+' \u2715';b.onclick=function(){sel=sel.filter(function(x){return x!==k;});render();};if(activeCat!=='all'&&kwCat(k)!==activeCat){b.style.opacity='0.3';b.style.pointerEvents='none';}bar.appendChild(b);});
}
ALL.forEach(function(k){if(active.indexOf(k)>=0)return;var c=counts[k]||0;if(hideZero&&c<1)return;var b=document.createElement('button');b.className='kw'+(c>0?'':' disabled')+(GEAR[k]?' gear':'');b.setAttribute('data-cat',kwCat(k));b.setAttribute('data-kw',k);b.textContent=k+' ('+c+')';if(c>0)b.onclick=function(){if(currentMode==='search')return;sel.push(k);render();};else b.disabled=true;if(currentMode!=='search'&&activeCat!=='all'&&kwCat(k)!==activeCat){b.style.opacity='0.3';b.style.pointerEvents='none';}bar.appendChild(b);});
var cl=document.createElement('button');cl.className='kw clear';cl.textContent='Clear';cl.onclick=function(){window.clearAllFilters();};bar.appendChild(cl);
if(currentMode==='search'){if(searchKeywords.length)st.textContent=hits.length+' match(es) for: '+searchKeywords.join(' + ');else st.textContent='';}
else if(sel.length)st.textContent=matching().length+' match(es) for: '+sel.join(' + ');else st.textContent='';
}
function render(){
if(currentMode!=='search'){
entries.forEach(function(el){var catOk=catMatch(el);var kwMatch=ms(el);var show=catOk&&(sel.length===0||kwMatch);el.classList.toggle('hit',sel.length>0&&kwMatch&&catOk);el.classList.toggle('dim',!show);el.style.display=show?'':'none';});
idx.forEach(function(li){var el=entryForIdx(li)||li;var catOk=catMatch(el);var kwMatch=ms(el);var show=catOk&&(sel.length===0||kwMatch);li.classList.toggle('hit',sel.length>0&&kwMatch&&catOk);li.style.display=show?'':'none';});
}
renderKwBar();
if(currentMode!=='search')syncHighlight();}
window.setMode=function(mode){
if(mode==='hide')mode='shade';
if(currentMode==='hide')currentMode='shade';
if(mode==='search'&&currentMode==='search'){
currentMode='shade';
document.querySelectorAll('.mode-btn').forEach(function(b){b.classList.toggle('active',b.dataset.mode==='shade');});
document.body.classList.remove('search-mode','search-extras-collapsed');
if(searchInput)searchInput.blur();
if(acList){acList.classList.remove('open');acList.innerHTML='';}
entries.forEach(function(el){el.style.display='';el.classList.remove('dim');});
render();
return;
}
currentMode=mode;
document.querySelectorAll('.mode-btn').forEach(function(b){b.classList.toggle('active',b.dataset.mode===mode);});
document.body.classList.toggle('search-mode',mode==='search');
document.body.classList.remove('search-extras-collapsed');
if(mode==='search'){searchKeywords=[];if(searchInput)searchInput.value='';renderPills();applySearch();setTimeout(function(){document.getElementById('searchInput').focus();},50);}
else{entries.forEach(function(el){el.style.display='';el.classList.remove('dim');});render();}};
/* --- search mode --- */
var searchInput=document.getElementById('searchInput'),acList=document.getElementById('acList');
function jsStr(s){return String(s).replace(/\\/g,'\\\\').replace(/'/g,"\\'");}
function htmlStr(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function sortOther(arr){return arr.slice().sort(function(a,b){if(b.c!==a.c)return b.c-a.c;return a.k<b.k?-1:a.k>b.k?1:0;});}
function acHtml(list,cap,hint){
var groups={};CAT_ORDER.forEach(function(c){groups[c]=[];});
list.forEach(function(o){var c=kwCat(o.k);if(groups[c])groups[c].push(o);});
groups.other=sortOther(groups.other);
var picked={};CAT_ORDER.forEach(function(c){picked[c]=[];});
if(hint){
CAT_ORDER.forEach(function(c){
if(c==='other'){
var untagged=groups[c].filter(function(o){return o.untagged;});
var rest=groups[c].filter(function(o){return !o.untagged;});
picked[c]=untagged.concat(rest).slice(0,2);
}else picked[c]=groups[c].slice(0,2);
});
}else{
var used=0,lim=cap||9999;
var nameHits=groups.other.filter(function(o){return o.isLibName||o.untagged;});
var otherRest=groups.other.filter(function(o){return !o.isLibName&&!o.untagged;});
groups.other=nameHits.concat(otherRest);
CAT_ORDER.forEach(function(c){if(groups[c].length){picked[c].push(groups[c][0]);used++;}});
CAT_ORDER.forEach(function(c){for(var i=1;i<groups[c].length&&used<lim;i++){picked[c].push(groups[c][i]);used++;}});
nameHits.forEach(function(o){if(picked.other.indexOf(o)<0)picked.other.push(o);});
}
var html='';
CAT_ORDER.forEach(function(c){
if(!picked[c].length)return;
html+='<div class="ac-group-label">'+CAT_LABEL[c]+'</div>';
picked[c].forEach(function(o){
html+='<div class="ac-item" onclick="addSearchKw(\''+jsStr(o.k)+'\')">'+htmlStr(o.label||o.k)+' <span class="ac-count">'+o.c+'</span></div>';
});
});
return html;}
function currentHits(){
if(currentMode==='search'){
return entries.filter(function(el){
if(!catMatch(el))return false;
if(searchKeywords.length===0)return true;
return searchKeywords.every(function(k){return pillMatch(el,k);});
});
}
return entries.filter(function(el){
if(!catMatch(el))return false;
if(sel.length===0)return true;
return ms(el);
});
}
function suggestFromHits(){
var hits=currentHits(),active=currentMode==='search'?searchKeywords:sel;
return allKws.filter(function(o){
if(active.indexOf(o.k)>=0)return false;
return hits.some(function(el){return pillMatch(el,o.k);});
}).map(function(o){
var c=0;hits.forEach(function(el){if(pillMatch(el,o.k))c++;});
return {k:o.k,c:c,untagged:o.untagged,isLibName:o.isLibName,label:o.label};
}).filter(function(o){return o.c>0;});
}
function showAc(q){var src=suggestFromHits();var list=q?src.filter(function(o){return o.k.indexOf(q)>=0||(o.label&&o.label.toLowerCase().indexOf(q)>=0);}):src;var html=acHtml(list,40,!q);acList.innerHTML=html;acList.classList.toggle('open',html.length>0);}
searchInput.addEventListener('input',function(){
var q=searchInput.value.trim().toLowerCase();
showAc(q);
if(!q&&searchKeywords.length===0)applySearch();
});
searchInput.addEventListener('focus',function(){showAc(searchInput.value.trim().toLowerCase());});
searchInput.addEventListener('keydown',function(e){
if(e.key==='Enter'){var q=searchInput.value.trim().toLowerCase();var src=suggestFromHits();var m=src.find(function(o){return o.k===q||(o.label&&o.label.toLowerCase()===q);});if(m)addSearchKw(m.k);}
});
function isRemainingHitKw(kw){
if(!kw)return false;
return currentHits().some(function(el){return pillMatch(el,kw);});
}
window.addSearchKw=function(kw){
if(!kw||searchKeywords.indexOf(kw)>=0)return;
if(!isRemainingHitKw(kw))return;
searchKeywords.push(kw);renderPills();applySearch();
searchInput.value='';acList.classList.remove('open');};
window.removeSearchKw=function(kw){searchKeywords=searchKeywords.filter(function(k){return k!==kw;});renderPills();applySearch();};
function renderPills(){var c=document.getElementById('searchPills');c.innerHTML=searchKeywords.map(function(k){return '<span class="pill-tag" onclick="removeSearchKw(\''+jsStr(k)+'\')">'+htmlStr(k)+' <span class="pill-x">\u00d7</span></span>';}).join('');}
function pillMatch(el,k){
var name=elNameLc(el);
var nameNorm=name.replace(/[^a-z0-9]+/g,' ').replace(/^\s+|\s+$/g,'');
if(kws(el).indexOf(k)>=0||others(el).indexOf(k)>=0)return true;
if(name===k||nameNorm===k)return true;
return false;
}
function applySearch(){
var grid=document.querySelector('.catalog-body');
var hasPills=searchKeywords.length>0;
var typed=searchInput?searchInput.value.trim():'';
if(grid)grid.style.display='';
entries.forEach(function(el){
var kwMatch=!hasPills||searchKeywords.every(function(k){return pillMatch(el,k);});
var show=kwMatch&&catMatch(el);
el.style.display=show?'':'none';
el.classList.toggle('hit',hasPills&&show);
el.classList.remove('dim');
});
idx.forEach(function(li){
var el=entryForIdx(li);
var kwMatch=el&&(!hasPills||searchKeywords.every(function(k){return pillMatch(el,k);}));
var show=!!el&&kwMatch&&catMatch(el);
li.classList.toggle('hit',hasPills&&show);
li.style.display=show?'':'none';
});
if(!hasPills&&!typed)clearHighlight();
else syncHighlight();
renderKwBar();
if(acList&&(acList.classList.contains('open')||(searchInput&&document.activeElement===searchInput))){
showAc(searchInput?searchInput.value.trim().toLowerCase():'');
}
}
function closeSearchExtras(){
if(acList){acList.classList.remove('open');acList.innerHTML='';}
document.body.classList.add('search-extras-collapsed');
}
window.closeSearchExtras=closeSearchExtras;
window.showSearchExtras=function(){document.body.classList.remove('search-extras-collapsed');};
window.clearAllFilters=function(){
sel=[];
searchKeywords=[];
activeCat='all';
document.querySelectorAll('.cat-btn').forEach(function(b){b.classList.toggle('active',b.dataset.cat==='all');});
document.querySelectorAll('.kw.on,.kw.active').forEach(function(b){if(!b.classList.contains('clear'))b.classList.remove('on','active');});
if(searchInput)searchInput.value='';
if(acList){acList.classList.remove('open');acList.innerHTML='';}
renderPills();
document.body.classList.remove('search-extras-collapsed');
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
var w=document.getElementById('filterWrap'),a=document.querySelector('.toggle-arrow');
if(w)w.classList.remove('open');
if(a)a.textContent='▼';
};
if(bar){
bar.addEventListener('click',function(e){
var btn=e.target.closest('.kw');
if(!btn||btn.classList.contains('clear'))return;
if(currentMode!=='search')return;
e.preventDefault();
e.stopPropagation();
if(typeof e.stopImmediatePropagation==='function')e.stopImmediatePropagation();
if(e.ctrlKey||e.metaKey){
var k=(btn.getAttribute('data-kw')||'').trim();
if(k&&!btn.classList.contains('disabled')&&isRemainingHitKw(k))window.addSearchKw(k);
}
},true);
}
render();
})();
function highlightEntry(el){
  if(!el){clearHighlight();return;}
  var cur=document.querySelector('.entry.highlight');
  if(cur===el){
    var bd=document.getElementById('hlBackdrop');
    if(bd)bd.classList.add('open');
    document.body.classList.add('hl-open');
    return;
  }
  clearHighlight();
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
function clearHighlight(){
  document.querySelectorAll('.hl-ph').forEach(function(ph){if(ph.parentNode)ph.parentNode.removeChild(ph);});
  document.querySelectorAll('.entry.highlight').forEach(function(e){e.classList.remove('highlight');});
  var bd=document.getElementById('hlBackdrop');
  if(bd)bd.classList.remove('open');
  document.body.classList.remove('hl-open');
}
function toggleHighlight(el){
  if(!el){clearHighlight();return;}
  if(el.classList.contains('highlight'))clearHighlight();
  else highlightEntry(el);
}
function entryIsShown(el){
  if(!el)return false;
  if(el.style.display==='none')return false;
  if(el.classList.contains('dim'))return false;
  return true;
}
function syncHighlight(){
  var hits=[].slice.call(document.querySelectorAll('.entry')).filter(entryIsShown);
  var cur=document.querySelector('.entry.highlight');
  if(hits.length===0){clearHighlight();return;}
  if(cur&&hits.indexOf(cur)<0){clearHighlight();cur=null;}
  if(hits.length===1){highlightEntry(hits[0]);return;}
}
window.openSearchModal = function(btn) {
  var card = btn.closest && btn.closest('.entry');
  if(card) highlightEntry(card);
  var modal = document.getElementById('searchModal');
  document.getElementById('searchModalTitle').textContent = btn.dataset.name || '';
  document.getElementById('searchModalYT').href = btn.dataset.yt || '#';
  document.getElementById('searchModalWeb').href = btn.dataset.web || '#';
  document.getElementById('searchModalImg').href = btn.dataset.img || '#';
  modal.classList.add('open');
  modal._ytUrl = btn.dataset.yt;
  modal._webUrl = btn.dataset.web;
  modal._imgUrl = btn.dataset.img;
};
window.closeSearchModal = function() {
  document.getElementById('searchModal').classList.remove('open');
};
window.openPopup = function(link, type) {
  var url = link.href;
  var sw = window.screen.availWidth, sh = window.screen.availHeight;
  var w = Math.min(920, Math.round(sw * 0.85));
  var h = Math.min(680, Math.round(sh * 0.82));
  var left = Math.round((sw - w) / 2);
  var top = Math.round((sh - h) / 6);
  var features = 'width='+w+',height='+h+',left='+left+',top='+top+',resizable=yes,scrollbars=yes,toolbar=yes,menubar=no,location=yes';
  var win = window.open(url, 'catalogSearch_'+type, features);
  if (!win) {
    window.open(url, '_blank', 'noopener,noreferrer');
  }
  closeSearchModal();
};
document.addEventListener('keydown', function(e) {
  if (e.key !== 'Escape') return;
  var ac=document.getElementById('acList');
  var acOpen=ac&&ac.classList.contains('open');
  var searchUi=e.target.closest&&e.target.closest('#searchInput,#acList,#searchStrip,.search-autocomplete,.search-active-pills,#filterWrap');
  var modal=document.getElementById('searchModal');
  var modalOpen=modal&&modal.classList.contains('open');
  if(acOpen){
    ac.classList.remove('open');
    e.preventDefault();
    return;
  }
  if(searchUi){
    if(typeof window.exitSearchUi==='function')window.exitSearchUi();
    if(e.target&&e.target.blur)e.target.blur();
    e.preventDefault();
    return;
  }
  if(document.querySelector('.entry.highlight')){
    clearHighlight();
    e.preventDefault();
    return;
  }
  if(modalOpen){
    closeSearchModal();
    e.preventDefault();
  }
});
document.addEventListener('click', function(e) {
  if(e.target.closest('#searchModal,.filter-wrap,.search-strip,.search-autocomplete,.search-active-pills,.top,.index')) return;
  var entry=e.target.closest('.entry');
  if(entry){
    if(e.target.closest('a,button,.kw,input,select,textarea,summary')) return;
    toggleHighlight(entry);
    return;
  }
  clearHighlight();
});
</script>
JS
echo '</body></html>'
} > "$OUT"
rm -f "$IDX" "$BODY"
echo "DS CATALOG ($MODE): $OUT"
echo "libraries: $N"
[ "$MODE" = portable ] && echo "size: $(du -h "$OUT" 2>/dev/null | cut -f1)"
echo "done."
