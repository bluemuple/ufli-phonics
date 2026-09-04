#!/bin/sh
S="/private/tmp/claude-501/-Users-moonleon-Documents-Phonics-program/ba225789-6bc1-495c-aaae-e99ed5e027cb/scratchpad"
D="/Users/moonleon/Documents/Phonics program/UFLI_AUS_pptx_downloads"
for f in "$D"/*.pptx; do
  id=$(basename "$f" | cut -d'_' -f1)
  out="$S/build/json/$id.json"
  [ -s "$out" ] && continue
  python3 "$S/build/parse_pptx.py" "$f" "$out" "$S/build/out/assets" 2>&1 | tail -1
done
echo PARSE_DONE
