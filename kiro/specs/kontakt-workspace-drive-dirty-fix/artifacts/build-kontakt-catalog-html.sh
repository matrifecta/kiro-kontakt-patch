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
    out_rows.append((alias,lp))
out_rows.sort(key=lambda r: r[0].lower())
with open(out,'w') as f:
    for alias,lp in out_rows:
        f.write(f"{alias}\t{lp}\n")
PY
rm -f "$DBTMP"

KEYWORDS="piano keys organ strings violin viola cello guitar bass harp choir vocal voice \
flute reed brass horn drums drum percussion bells gamelan tabla kalimba \
synth pad ambient cinematic orchestral world lofi analog"
classify(){ local w; w=$(printf '%s' "${1:-}" | tr 'A-Z' 'a-z' | tr -c 'a-z0-9' ' '); local o=""
  for k in $KEYWORDS; do case " $w " in *" $k "*) o="$o $k";; esac; done; printf '%s' "${o# }"; }

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
    | grep -viE '^[[:space:]]*(the story|story|usage|faq|installation|install|included|release notes|date:|by:|created by:|version|copyright|license|www\.|http)' \
    | sed '/^[[:space:]]*$/d' | tr '\n' ' ' | sed 's/  */ /g; s/^ //')
  case "$(printf '%s' "$txt" | tr 'A-Z' 'a-z')" in *"your full name"*|*"your sample pack"*|*"lorem ipsum"*) return 0;; esac
  printf '%s' "$txt" | grep -oE '^.{0,300}([.!?]|$)' | head -1 | sed 's/[[:space:]]*$//'; }

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
  printf '  <img class="cover" src="data:%s;base64,%s" alt="%s">\n' "$mime" "$b64" "$(e "$name")"
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
  printf '  <details class="patches"><summary>Patches (%s)</summary>\n' "$total"

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
  local name="$1" path="$2"
  N=$((N+1)); local id; id=$(anchor "$N")
  local kw; kw=$(classify "$name")
  printf '<li data-kw="%s"><a href="#%s">%s</a></li>\n' "$(e "$kw")" "$id" "$(e "$name")" >> "$IDX"
  {
    printf '<div class="entry" id="%s" data-kw="%s">\n' "$id" "$(e "$kw")"
    printf '  <h3>%s</h3>\n' "$(e "$name")"
    local dsc; dsc=$(desc_for "$path"); [ -n "$dsc" ] && printf '  <p class="desc">%s</p>\n' "$(e "$dsc")"
    local b; b=$(banner_for "$name")
    [ -n "$b" ] && [ -f "$b" ] && emit_img "$b" "$name"
    if [ "$MODE" = portable ]; then
      printf '  <div class="path"><b>path:</b> <code>%s</code></div>\n' "$(e "$path")"
    else
      local url; url="file://$(printf '%s' "$path" | sed 's/ /%20/g')"
      printf '  <div class="path"><b>path:</b> <code>%s</code> &nbsp;<a class="folder" href="%s">[open folder]</a></div>\n' "$(e "$path")" "$(e "$url")"
    fi
    emit_patches "$path"
    printf '</div>\n'
  } >> "$BODY"
}

while IFS=$'\t' read -r alias path; do [ -z "$alias" ] && continue; entry "$alias" "$path"; done < "$LIBLIST"
rm -f "$LIBLIST"

{
  cat <<'HTML'
<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>Kontakt Library Catalog</title>
<style>
 body{font-family:system-ui,Segoe UI,Roboto,sans-serif;max-width:1000px;margin:2rem auto;padding:0 1rem;line-height:1.4;color:#111}
 h1{margin-bottom:.2rem} h2{margin-top:2rem;border-bottom:2px solid #ddd;padding-bottom:.2rem}
 .index{columns:3;column-gap:2rem;font-size:.9rem} .index li{break-inside:avoid;margin:.1rem 0}
 .index a{color:#2563eb;text-decoration:underline} .index li.hit{background:#fff7cc;border-radius:3px}
 .entry{border-top:1px solid #eee;padding:.6rem 0} .entry h3{margin:.2rem 0}
 .entry.hit{background:#fff7cc;border-left:4px solid #f59e0b;padding-left:.6rem}
 .cover{max-height:150px;border:1px solid #ccc;border-radius:4px;margin:.3rem 0;display:block}
 .desc{font-style:italic;color:#444;margin:.2rem 0}
 code{background:#f4f4f4;padding:.05rem .3rem;border-radius:3px;font-size:.82rem;word-break:break-all}
 .folder{color:#059669;text-decoration:underline;font-size:.82rem;white-space:nowrap}
 .patches{margin:.35rem 0;font-size:.86rem}
 .patches>summary{cursor:pointer;color:#2563eb;font-weight:600}
 .patches .grp{margin:.2rem 0 .2rem 1rem}
 .patches .grp>summary{cursor:pointer;color:#374151;font-weight:600}
 .patchlist{margin:.2rem 0 .4rem 1.4rem;padding-left:1rem;columns:2;column-gap:1.5rem}
 .patchlist li{break-inside:avoid;list-style:disc;color:#111}
 .patches.nopatch{color:#888;font-style:italic;margin-left:.2rem}
 #kwbar{display:flex;flex-wrap:wrap;gap:.35rem;margin:.5rem 0}
 .kw{cursor:pointer;border:1px solid #cbd5e1;background:#f8fafc;border-radius:14px;padding:.2rem .6rem;font-size:.8rem}
 .kw:hover{background:#eef2ff} .kw.active{background:#2563eb;color:#fff;border-color:#2563eb}
 .kw.disabled{color:#bbb;background:#f3f4f6;border-color:#e5e7eb;cursor:not-allowed;opacity:.6}
 .kw.clear{background:#fee2e2;border-color:#fca5a5}
 .kwstatus{font-size:.85rem;color:#2563eb;font-weight:600;min-height:1.1em}
 .top{position:fixed;bottom:1rem;right:1rem;background:#2563eb;color:#fff;padding:.4rem .7rem;border-radius:4px;text-decoration:none}
</style></head><body>
<h1 id="top">Kontakt Library Catalog</h1>
HTML
  printf '<p>generated: %s</p>\n' "$(e "$(date)")"
  if [ "$MODE" = portable ]; then
    printf '<p>Portable snapshot (banners embedded; phone-safe). Registered Kontakt libraries; click a name to jump. <b>Update:</b> on desktop re-run <code>build-kontakt-catalog-html.sh both</code> and re-transfer this file.</p>\n'
  else
    printf '<p>Registered Kontakt libraries (from komplete.db3). Click a name to jump; [open folder] opens the library in Dolphin. <b>Added libraries?</b> Re-run <code>build-kontakt-catalog-html.sh both</code>.</p>\n'
  fi
  echo '<h2>Filter by type</h2><div id="kwbar"></div><p id="kwstatus" class="kwstatus"></p>'
  echo '<h2>Index (alphabetical)</h2><ul class="index">'
  sort -f "$IDX" | uniq
  echo '</ul>'
  cat "$BODY"
  echo '<a class="top" href="#top">&uarr; top</a>'
  cat <<'JS'
<script>
(function(){
 var entries=[].slice.call(document.querySelectorAll('.entry'));
 var idx=[].slice.call(document.querySelectorAll('.index li'));
 function kws(el){return (el.getAttribute('data-kw')||'').split(/\s+/).filter(Boolean);}
 var sel=[], bar=document.getElementById('kwbar'), st=document.getElementById('kwstatus');
 var ALL=(function(){var s={};entries.forEach(function(el){kws(el).forEach(function(k){s[k]=1;});});return Object.keys(s).sort();})();
 function matchesSel(el){var s=kws(el);return sel.length>0&&sel.every(function(k){return s.indexOf(k)>=0;});}
 function matching(){return entries.filter(matchesSel);}
 function render(){
   entries.forEach(function(el){el.classList.toggle('hit',matchesSel(el));});
   idx.forEach(function(el){el.classList.toggle('hit',matchesSel(el));});
   var base=sel.length?matching():entries, counts={};
   base.forEach(function(el){kws(el).forEach(function(k){if(sel.indexOf(k)<0)counts[k]=(counts[k]||0)+1;});});
   bar.innerHTML='';
   sel.forEach(function(k){var b=document.createElement('button');b.className='kw active';b.textContent=k+' \u2715';
     b.onclick=function(){sel=sel.filter(function(x){return x!==k;});render();};bar.appendChild(b);});
   ALL.forEach(function(k){if(sel.indexOf(k)>=0)return;var c=counts[k]||0;var b=document.createElement('button');
     b.className='kw'+(c>0?'':' disabled');b.textContent=k+' ('+c+')';
     if(c>0)b.onclick=function(){sel.push(k);render();};else b.disabled=true;bar.appendChild(b);});
   if(sel.length){var cl=document.createElement('button');cl.className='kw clear';cl.textContent='Clear';
     cl.onclick=function(){sel=[];render();};bar.appendChild(cl);
     st.textContent=matching().length+' match(es) for: '+sel.join(' + ');} else st.textContent='';
 }
 render();
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
