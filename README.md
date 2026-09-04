# UFLI Foundations — interactive slides & teacher guides (Australian edition)

Personal study site for teaching phonics at home. Open **`index.html`** (double-click) — everything works offline.
Online: <https://bluemuple.github.io/ufli-phonics/>

## Folders

| Folder | What it is |
|---|---|
| `decks/` | One interactive HTML lesson per deck (A–J, 1–128, incl. 77 AUS / 80 AUS), converted from the UFLI Toolbox (AUS) PowerPoints |
| `guide/` | Teacher's guide (교사용 지도서) per lesson, in the UFLI manual layout, with example-word popups. Print → PDF works |
| `assets/` | Images and letter-formation GIFs extracted from the PowerPoints (shared, de-duplicated) |
| `shared/` | Player CSS/JS, grapheme database (`graphemes.js`), guide CSS/JS |
| `fonts/` | Century Gothic, copied from Microsoft Office for local use only (not published to GitHub) |
| `_build/` | The Python pipeline, plus everything needed to rebuild **without** the PowerPoint files |

## Keyboard (slides)

| Key | Action |
|---|---|
| `→` / `←` | Next (reveals hidden items first) / previous |
| `↓` / `↑` | Skip a whole slide |
| `F` | Full screen |
| `N` | Teacher notes + lesson plan panel |
| `M` | Step menu |
| `D` | **Details mode** on/off |
| `H` | Hint: how many sounds this grapheme has |
| `S` | Read aloud |
| `E` | Example words for the grapheme |
| `A` / `R` | Reveal all / reset the slide |
| `G` | Go to a slide number |
| `?` | All shortcuts |

**Details mode ON** — on Visual Drill cards `→` first shows the example-word popup, then moves on; in the
Auditory Drill helper `→` steps grapheme → its example words → next grapheme.

Click any word or sentence to hear it. On the "Spell a sentence" and "Spell" helper slides the 🔊 button
plays the sentence/word **without revealing it** (for dictation).

## Text-to-speech

Clicks call the Supabase edge function `tts` (Google Neural2 `en-AU-Neural2-A`, the NZ/AU female voice).
If that call fails, the Mac's built-in voice (Karen) is used automatically.
Free tier: 1 million characters per month for Neural2 voices — far beyond normal home use.

## Rebuilding (no PowerPoint files needed)

```bash
cd "$HOME/Documents/Phonics program/UFLI_HTML" && python3 _build/build_all.py .
```

`_build/json/` holds all 150 parsed decks (slide text, geometry, animations), `_build/content/` the extracted
lesson content, `_build/plans/*.py` the lesson-plan data. Edit a plan, run the command above, done.
The downloaded PowerPoints were deleted on 2026-09-05; their URLs are kept in `_build/pptx_urls.txt` (`id|url`).

## Publishing

Double-click `publish_to_github.command`, or:

```bash
cd "$HOME/Documents/Phonics program/UFLI_HTML" && git add -A && git commit -m "update" && git push
```

## Credit and scope

Slides, images and decodable passages come from the
[UFLI Foundations Toolbox, Australian edition](https://ufli.education.ufl.edu/foundations/toolbox-aus/),
© University of Florida Literacy Institute, used and adapted under UFLI's terms (free for educational use with
attribution; not for sale or commercial use).

Teacher-guide text for lessons **116, 118–122, 77 AUS and 80 AUS** comes from the manual. For every other lesson
the guide text (phonemic-awareness items, blending chains, concept scripts, spelling words, dictation sentences,
word lists) is a **reconstruction** in the UFLI format, not the official manual — each page says so in its footer.
Visual Drill graphemes, reading words, irregular words with their notes, sentences and passages are extracted
from the actual PowerPoints.
