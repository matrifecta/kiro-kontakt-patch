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
    | grep -viE '^[[:space:]]*(the story|story|usage|faq|included formats|release notes|date:|by:|created by:|profile:|version)' \
    | grep -viE 'decentsampler.com|pianobook.co.uk|hyperlink|requires kontakt|drag the|\.dslibrary' \
    | sed '/^[[:space:]]*$/d' | tr '\n' ' ' | sed 's/  */ /g; s/^ //')
  case "$(printf '%s' "$txt" | tr 'A-Z' 'a-z')" in *"your full name"*|*"your sample pack"*|*"new feature one"*|*"[1.x]"*|*"lorem ipsum"*) return 0;; esac
  printf '%s' "$txt" | grep -oE '^.{0,300}([.!?]|$)' | head -1 | sed 's/[[:space:]]*$//'; }

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

# curated gear/rack terms to look for in the DESCRIPTION text (specific, low false-positive).
# tokens use lowercase; multi-char models kept as single tokens.
GEAR="808 909 707 606 727 cr-78 cr78 tr-808 tr-909 linndrum juno jupiter moog minimoog \
mellotron rhodes wurlitzer prophet oberheim korg roland yamaha dx7 casio sh-101 ms-20 \
op-1 volca arp emu fairlight ppg synclavier hammond leslie optigan chamberlin \
steinway broadwood ensoniq dfam ibanez casiotone digitech tx81z selmer"
classify_desc(){ local d; d=$(printf '%s' "${1:-}" | tr 'A-Z' 'a-z'); local o=""
  for k in $GEAR; do case "$d" in *"$k"*) o="$o $k";; esac; done; printf '%s' "${o# }"; }

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
  printf '  <img class="cover" src="data:%s;base64,%s" alt="%s">\n' "$mime" "$b64" "$(e "$name")"
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

# ---- one entry per LIBRARY ----  args: display_name  library_dir  loadable_path(for open:)
entry(){ local name="$1" libdir="$2" openp="$3"
  N=$((N+1)); local id="item-$N"
  local d; d=$(desc_for "$libdir")
  local kw; kw=$(classify "$name $d")   # name + desc both feed instrument tags
  local gkw; gkw=$(classify_desc "$d")  # desc feeds gear/brand tags (purple)
  local allkw; allkw=$(printf '%s %s' "$kw" "$gkw" | sed 's/^ //;s/ $//')
  printf '<li data-kw="%s"><a href="#%s">%s</a></li>\n' "$(e "$allkw")" "$id" "$(e "$name")" >> "$IDX"
  {
    printf '<div class="entry" id="%s" data-kw="%s" data-gear="%s">\n' "$id" "$(e "$allkw")" "$(e "$gkw")"
    printf '  <h3>%s</h3>\n' "$(e "$name")"
    [ -n "$d" ] && printf '  <p class="desc">%s</p>\n' "$(e "$d")"
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
    if [ "$MODE" = portable ]; then
      printf '  <div class="path"><b>open:</b> <code>%s</code></div>\n' "$(e "$openp")"
    else
      local url; url="file://$(printf '%s' "$libdir" | sed 's/ /%20/g')"
      printf '  <div class="path"><b>open:</b> <code>%s</code> &nbsp;<a class="folder" href="%s">[open folder]</a></div>\n' "$(e "$openp")" "$(e "$url")"
    fi
    emit_patches "$libdir"
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
<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>DecentSampler Library Catalog</title>
<style>
 body{font-family:system-ui,Segoe UI,Roboto,sans-serif;max-width:1000px;margin:2rem auto;padding:0 1rem;line-height:1.4;color:#111}
 h1{margin-bottom:.2rem} h2{margin-top:2rem;border-bottom:2px solid #ddd;padding-bottom:.2rem}
 .index{column-width:260px;column-gap:2rem;font-size:.9rem;padding-left:1.2rem}
 .index li{break-inside:avoid;margin:.15rem 0;list-style:disc;overflow-wrap:break-word;word-break:normal}
 .index a{color:#2563eb;text-decoration:underline;overflow-wrap:break-word} .index li.hit{background:#fff7cc;border-radius:3px}
 .entry{border-top:1px solid #eee;padding:.6rem 0} .entry h3{margin:.2rem 0}
 .entry.hit{background:#fff7cc;border-left:4px solid #f59e0b;padding-left:.6rem}
 .desc{font-style:italic;color:#444;margin:.2rem 0}
 .cover{max-height:150px;border:1px solid #ccc;border-radius:4px;margin:.3rem 0;display:block}
 code{background:#f4f4f4;padding:.05rem .3rem;border-radius:3px;font-size:.82rem;word-break:break-all}
 .folder{color:#059669;text-decoration:underline;font-size:.82rem;white-space:nowrap}
 details.patches{margin:.3rem 0;font-size:.86rem} details.patches summary{cursor:pointer;color:#7c3aed;font-weight:600}
 .grp{margin:.3rem 0 .1rem;font-weight:600;color:#555} details.patches ul{margin:.1rem 0 .3rem 1rem}
 .nopatch{font-size:.82rem;color:#999}
 #kwbar{display:flex;flex-wrap:wrap;gap:.35rem;margin:.5rem 0}
 .kw{cursor:pointer;border:1px solid #cbd5e1;background:#f8fafc;border-radius:14px;padding:.2rem .6rem;font-size:.8rem}
 .kw:hover{background:#eef2ff} .kw.active{background:#2563eb;color:#fff;border-color:#2563eb}
 .kw.disabled{color:#bbb;background:#f3f4f6;border-color:#e5e7eb;cursor:not-allowed;opacity:.6}
 .kw.clear{background:#fee2e2;border-color:#fca5a5} .kwstatus{font-size:.85rem;color:#2563eb;font-weight:600;min-height:1.1em}
 .kw.gear{border-color:#a855f7;color:#7c3aed} .kw.gear.active{background:#7c3aed;color:#fff;border-color:#7c3aed}
 .noart{font-size:.85rem;color:#999;margin:.2rem 0} .viewart{color:#059669;text-decoration:underline;font-weight:600}
 .top{position:fixed;bottom:1rem;right:1rem;background:#2563eb;color:#fff;padding:.4rem .7rem;border-radius:4px;text-decoration:none}
</style></head><body>
<h1 id="top">DecentSampler Library Catalog</h1>
HTML
printf '<p>generated: %s. Library-level; expand a library to see its patches (grouped by subfolder).</p>\n' "$(e "$(date)")"
if [ "$MODE" = portable ]; then printf '<p>Portable snapshot (images embedded; phone-safe). <b>Update:</b> desktop <code>build-ds-catalog-html.sh both</code>.</p>\n'
else printf '<p><b>Added libraries?</b> Re-run <code>build-ds-catalog-html.sh both</code>.</p>\n'; fi
echo '<h2>Filter by type</h2><div id="kwbar"></div><p id="kwstatus" class="kwstatus"></p>'
echo '<h2>Index (alphabetical)</h2><ul class="index">'; sort -f "$IDX" | uniq; echo '</ul>'
cat "$BODY"
echo '<a class="top" href="#top">&uarr; top</a>'
cat <<'JS'
<script>
(function(){var entries=[].slice.call(document.querySelectorAll('.entry')),idx=[].slice.call(document.querySelectorAll('.index li'));
function kws(el){return (el.getAttribute('data-kw')||'').split(/\s+/).filter(Boolean);}
var sel=[],bar=document.getElementById('kwbar'),st=document.getElementById('kwstatus');
// gear keywords (from descriptions) get a distinct color
var GEAR={};entries.forEach(function(el){(el.getAttribute('data-gear')||'').split(/\s+/).filter(Boolean).forEach(function(k){GEAR[k]=1;});});
var ALL=(function(){var s={};entries.forEach(function(el){kws(el).forEach(function(k){s[k]=1;});});return Object.keys(s).sort();})();
function ms(el){var s=kws(el);return sel.length>0&&sel.every(function(k){return s.indexOf(k)>=0;});}
function matching(){return entries.filter(ms);}
function render(){entries.forEach(function(el){el.classList.toggle('hit',ms(el));});idx.forEach(function(el){el.classList.toggle('hit',ms(el));});
var base=sel.length?matching():entries,counts={};base.forEach(function(el){kws(el).forEach(function(k){if(sel.indexOf(k)<0)counts[k]=(counts[k]||0)+1;});});
bar.innerHTML='';sel.forEach(function(k){var b=document.createElement('button');b.className='kw active'+(GEAR[k]?' gear':'');b.textContent=k+' \u2715';b.onclick=function(){sel=sel.filter(function(x){return x!==k;});render();};bar.appendChild(b);});
ALL.forEach(function(k){if(sel.indexOf(k)>=0)return;var c=counts[k]||0;var b=document.createElement('button');b.className='kw'+(c>0?'':' disabled')+(GEAR[k]?' gear':'');b.textContent=k+' ('+c+')';if(c>0)b.onclick=function(){sel.push(k);render();};else b.disabled=true;bar.appendChild(b);});
if(sel.length){var cl=document.createElement('button');cl.className='kw clear';cl.textContent='Clear';cl.onclick=function(){sel=[];render();};bar.appendChild(cl);st.textContent=matching().length+' match(es) for: '+sel.join(' + ');}else st.textContent='';}
render();})();
</script>
JS
echo '</body></html>'
} > "$OUT"
rm -f "$IDX" "$BODY"
echo "DS CATALOG ($MODE): $OUT"
echo "libraries: $N"
[ "$MODE" = portable ] && echo "size: $(du -h "$OUT" 2>/dev/null | cut -f1)"
echo "done."
