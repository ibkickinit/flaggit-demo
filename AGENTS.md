# AGENTS.md — Flaggit

Canonical agent-context file for this repo. Read this before touching code.
Global rules live in the vault at `/_PROJECTS/Claude/coding-standards.md`;
project orientation lives at `/_PROJECTS/Flaggit/00-index.md`.

---

## What this is

Cable-flag label printing app for AV / film / broadcast. A single-file HTML UI
generates label series (alpha, numeric, alphanumeric, two-line), queues them, and
posts them to a Python relay that rasterises each flag with Pillow and writes raw
bytes to a thermal printer.

**Status:** functional and deployed. PAUSED for feature work; active design work is
the multi-printer port (see *Printer port* below).

## Source of truth

**The copy deployed on the GL.iNet router is canonical.** This repo is a snapshot
taken from the Dropbox vault working copies, which were themselves migrated from
Desktop on 2026-05-06 and have **never been diff-verified against the router**
(`00-index.md` migration checkbox is still open).

Before changing anything: sync down from the router and diff. Before deploying:
push up to the router and restart the service.

Known suspected drift: `flaggit-combined.py` here has `PRINTER_IP = 192.168.100.101`,
while the UI's default relay address is `192.168.8.100`. Confirm both against the
router before trusting either.

## Architecture

```
browser (phone)                GL.iNet router                    printer
┌──────────────┐   POST /print  ┌──────────────────────┐  TCP 9100  ┌──────────┐
│ flaggit.html │ ─────────────▶ │ flaggit-combined.py  │ ─────────▶ │ TSP143IV │
│  queue + UI  │ ◀───────────── │  :9000  also serves  │            │   -UE    │
└──────────────┘   200 OK       │  the HTML itself     │            └──────────┘
                                └──────────────────────┘
```

The relay serves the UI **and** bridges to the printer, so the app is same-origin
with its own API — no CORS or mixed-content problem in normal use.

- Relay listens on `:9000`, printer socket is raw TCP `:9100`
- Rasterisation: Pillow renders a PIL image → `build_raster()` emits Star `ESC * r`
- `ESC * r E 1` between labels = feed and cut

### Print API

```
POST /print
{ "labels": [ { "line1": str,
                "line2": str?,
                "font_size": int,        # 200..500, slider units (see geometry)
                "label_padding": int,    # dots
                "cable_pad": int,        # dots, fold-side offset
                "bold": bool,
                "dominance": "l1"|"equal"|"l2",
                "perp_mode": true,
                "perp_text": str?,       # MAIN / BACKUP band
                "show_name": str?,
                "show_name_invert": bool? } ],
  "sep": 200 }
```

## Files

| File | Role |
|---|---|
| `flaggit.html` | Real UI. Talks to the relay. Deployed to `/root/flaggit.html`. |
| `index.html` | Demo UI — print is simulated. Refactored: printer profiles, mm geometry, one renderer. No longer byte-identical to the vault's `flaggit-demo.html`. Named `index.html` so GitHub Pages serves it. |
| `flaggit-combined.py` | Relay server: HTTP on :9000, Pillow rasteriser, Star raster encoder, TCP to printer. |
| `README.md` | Full feature and implementation reference, including a "Key Implementation Details" section documenting preview↔server parity. |
| `docs/MARKETING.md` | Positioning copy and v1.0 release notes. |
| `docs/project-flaggit-legacy.md` | Earlier project notes from the monorepo era. Includes "Planned Features (not yet built)". |

Font on the router: `/etc/gafflabel/font.ttc` (Barlow Condensed; index 0 regular,
index 1 bold). The `gafflabel` name is legacy — it is also still the localStorage
settings key. Do not rename either without migrating.

## Geometry model

The flag is printed as **two mirrored halves** separated by a blank gap, so that
after wrapping the cable and folding, the text reads from both sides.

```
H = HALF_H * 2 + sep

HALF_H = BASE_PAD + label_padding + text_tape_len
       + (BASE_GAP + label_padding + tag_tape_len)   if perp_text
       + (SN_GAP + sn_tape_len)                      if show_name
       + END_PAD
```

`sep` (default 200 dots ≈ 25 mm) is the cable-wrap allowance in the middle.
`cable_pad` is an *additional* fold-side offset folded into `BASE_PAD`.

| Constant | Value | Meaning |
|---|---|---|
| `W` | 320 dots | Tape width. 320 dots ÷ 8 dots/mm = 40 mm. |
| `SAFE_W` | 270 dots | Usable width used by the horizontal layout and tag fitting. |
| `max_total_h` | `W - 2*10` = 300 dots | Height budget in perp mode (37.5 mm). |
| `BASE_PAD` | `10 + cable_pad` | Fold-side offset. |
| `END_PAD` | 10 dots | Free end always this far from the paper end. |
| `BASE_GAP` | 8 dots | Text→tag gap before `label_padding`. |
| `LINE_GAP` | 8 dots | Between line1 and line2. |
| cable wrap | `π × diameter / 2` | The old 50 / 100 / 200 dot presets are exactly half-circumferences of 4 / 8 / 16 mm cable, within 0.5%. Each printed face of a fold-over flag wraps half the way round, so this is the physically right quantity, and the UI control is the diameter. |
| `SN_GAP` | 6 dots | Before the show-name band. |
| `PERP_W` | 48 dots | Width of the perpendicular tag strip (horizontal layout only). |
| `OFFSET_N` / `OFFSET_F` | -25 / +25 | Opposite nudges on the two halves so they align once folded. Also compensates Barlow Condensed centring. |
| dominance ratios | 0.62 / 0.46 / 0.30 | Share of tape width for line1 vs line2 (`l1` / `equal` / `l2`). |
| slider mapping | `(font_size-200)/300` → `0.10 + 0.90*frac` | Fraction of `max_total_h` used for glyph height. |

**Preview↔server parity is deliberate and load-bearing.** `drawFlag()` in the HTML
reproduces this maths against a 200 px scene where `scale = 200/320`. The dominance
ratios and the slider mapping are duplicated verbatim in both places. **Change one,
change the other**, or the preview lies.

## Known issues

Verified by reading the code. Demo-only items do not affect the deployed app.

**Real app and relay**
1. Geometry maths is duplicated between `drawFlag()` and `drawQueueFlag()` in the
   HTML (~90 lines each, ~95% identical) and again in the Python. Three copies.
2. All dot-based constants assume 8 dots/mm. Any printer at a different dpi breaks
   silently. Geometry should be stored in mm and converted at the raster boundary.
3. `cfg-width` (40/58/80 mm) is persisted to localStorage and **read by nothing**.
   The preview hardcodes 320 dots.
4. Selection state is keyed by array index over a mutating array. `removeItem()`
   fixes `qpOpenIdx` but not `selected`, so deleting an item silently re-points
   selections above it. Items already carry an `id` — key on that.
5. Text Size readout shows `font_size / 8.42` mm, which does not match what the
   preview renders (430 reads "51 mm", renders ≈30 mm; 200 reads "24 mm", renders
   ≈3.8 mm). It also labels an em size as if it were cap height.
6. `make_label()` (horizontal text) is dead on the current path — the UI always
   sets `perp_mode: true`. **Keep it:** it is the layout the Brother port needs.
7. Relay has `Access-Control-Allow-Origin: *` and no auth, so any page in the
   browser can print. Acceptable on a closed show network; know that it is true.
8. Relay reads the HTML once at import — UI changes need a service restart.
9. `PRINTER_IP` / `PRINTER_PORT` / `PORT` / paths are module-level literals with no
   config file or env override.
10. Settings panel markup has one unclosed `<div class="card">`.

**Demo (`index.html`) — refactored, these are now fixed there but still live in
`flaggit.html` and the relay.** The demo is the reference implementation for the
port; `flaggit.html` has not been touched because the router copy is canonical and
unverified.

Fixed in the demo:
- One `renderFlag()` replaces `drawFlag` + `drawQueueFlag`. Geometry maths exists
  once. `buildSpecFromState()` makes the build panel's implicit read of live state
  explicit; `specFromQueueItem()` does the same for a queue row.
- `PRINTER_PROFILES` holds every printer-specific number. The preview scene scales
  to `printableWidthMm`, so a Brother flag actually looks narrower than a Star one.
- Geometry is stored in mm; `mmToDots()` is the only conversion. Values reproduce
  the relay's dot constants exactly at 203 dpi.
- Selection is keyed on `item.id`. Deleting an earlier row no longer re-points a
  selection at a different label.
- Text Size reports real cap height in mm from the active profile, and shows both
  line heights when the width is split (`6.4 / 3.1mm`) so the unreadable second
  line is visible rather than hidden behind one number.
- Narrow media stacks two lines **along the feed** at full height instead of
  splitting the width. `tlDominance` keeps the user's intent; the renderer decides
  what is achievable, so switching back to wide media restores their choice.
- State lives in one `appState` object, exposed on `window` for field debugging
  from a phone console.
- Dead code removed: `toggleCut`/`toggleBold`, `showQueuePreview`/
  `closeQueuePreview`, the `qp-sheet` bottom-sheet CSS, `.flag-tape`, the dead
  `hdr-ip` writes that made `saveSettings()` throw on every call.
- Unclosed `<div class="card">` closed. `cfg-width` replaced by the profile select.
- Queue text is escaped before `innerHTML`. Legacy localStorage items are migrated
  (ids assigned, dot geometry converted and snapped to a cable preset).
- Print history is no longer hidden when the queue empties.
- Settings said "StarWebPRNT" / port 80. It is `ESC * r` raster over TCP 9100 to
  the relay on :9000. Corrected.

Still open in the demo:
- No N-up imposition for `layout: 'sheet'` profiles; Rollo 4 in only warns. Under
  the rule above this should become a user-selectable layout, not a Rollo-only
  mode: offer flag and sheet layouts wherever the media can carry them.
- `brother-24` now *defaults* to stacked, because side by side gives 6.4 / 3.1 mm
  where stacking gives 9.7 mm on both. Both remain available to the user.
- Wrap-around (text repeated along the cable, no flag) is not implemented. It is
  the fourth viable layout and the most durable one for permanent install work.
- Only one face is drawn in the preview, deliberately: the author asked for an
  illustration of where the cable sits and the blank leader before the text, not
  a 3D fold. The hatched `.flag-wrap-zone` band does that. The relay still prints
  two mirrored halves separated by `sep`, which the preview does not show.

## Audience — this ships to the public

Flaggit is not a personal tool. It is intended for other AV / film / broadcast
techs, not just its author's kit. Two things follow:

- **Defaults have to be right without explanation**, because most users will
  never read any of this.
- **The profile table is a public-facing abstraction.** It will grow. Adding a
  printer must stay a matter of adding a row.

The transport matrix matters more for the same reason: Android Chrome can drive
a USB printer directly over WebUSB with nothing installed, iOS cannot do USB at
all, and the router bridge is the only path that covers every phone and every
printer. Not everyone will carry a router, so no single transport is sufficient.

## Never let the printer decide for the user

**Offer every layout the hardware can physically do, show what each one costs,
and let the user choose.** A profile supplies a *default*, never a restriction.

This is a correction of an earlier design in this repo. The demo originally had
`allowTwoLineSideBySide`, a per-profile flag that *disabled* the dominance
buttons on narrow media — the printer deciding on the user's behalf. That is
exactly wrong for a public tool: 9.9 mm split across two lines is a bad idea,
not an impossible one, and someone printing a two-character label may want it.

It is now `defaultTwoLineLayout`, a starting point, with a user-facing
SIDE BY SIDE / STACKED control. Dominance greys out only when STACKED is chosen,
because dominance is genuinely meaningless then — a consequence of the user's
own choice, never of the printer's. Warnings state the cost ("Side by side puts
the second line at 1.7 mm — stacked would give 3.5 mm on both") instead of
removing the option.

Apply the same rule to anything added later: Rollo sheet vs flag layouts, N-up,
wrap-around vs fold. Offer all viable options per printer.

## JS baseline — ES6+, settled

Global standards default to ES5 for constrained single-file device apps,
explicitly naming GL.iNet routers. The author has confirmed ES6+ for this repo:
the UI runs in mobile Safari / Chrome, not on the router itself, and the code is
already ES6+ throughout. Not an oversight, and not to be "corrected" later.

## Printer port (active design work)

Porting off 40 mm linerless, which is a scarce medium: high-tack industrial
adhesive and the silicone release coat that makes linerless possible trade off
against each other, so the grade needed barely exists.

| Target | dpi | Printable width | Transport |
|---|---|---|---|
| Star TSP143IV-UE, 40 mm linerless | 203 | 320 dots / 40 mm (verify — `SAFE_W` implies 270) | TCP 9100 ✔ shipping |
| Brother PT-P710BT, 24 mm TZe-FX | 180 | **128 dots / 18.1 mm** | USB, or BT Classic SPP |
| Brother PT-P710BT, 18 mm | 180 | 112 dots / 15.8 mm | as above |
| Brother PT-P710BT, 12 mm | 180 | 70 dots / 9.9 mm | as above |
| Rollo X1040, 2" die-cut | 203 | 406 dots / 50.8 mm | USB, WiFi, AirPrint/IPP |
| Rollo X1040, 4" die-cut | 203 | 812 dots / 104 mm | as above |

Brother printable widths are from the official Raster Command Reference tape table
(PT-E550W/P750W/P710BT). The 128-pin head is narrower than 24 mm tape, so ~3 mm on
each edge is unprintable. Other Brother facts that constrain design: minimum tape
fed per print is 24.5 mm regardless of content (so auto-cutting every label wastes
~38% of a cassette; chain printing recovers ~60% more labels), and `ESC i A`
"cut each N labels" is **not** supported on the P710BT, so the app must compose the
chained strip itself. Use **TZe-FX** flexible-ID tape, not standard TZe — Brother
specifies it for wrapping cables *and* for sticking to itself as a flag.

Rollo is gap-sensing die-cut, not truly continuous, so variable-length flags do not
port; a fixed "universal wrap" geometry does. Rollo is also direct thermal, which
fades with heat and UV — scope it as show-duration, not season-long.

**The port is smaller than it looks.** The pipeline is already
`PIL image → 1-bit → encoder → transport`, and only the last two steps are
Star-specific. `build_raster()` is the single Star-coupled function, and
`make_label()` already implements the horizontal layout the narrow Brother tape
wants. The work is: extract a printer-profile object, move geometry from dots to
mm, collapse the duplicated renderers, and add `build_raster_brother()` /
`build_raster_rollo()` plus a transport interface.

Transport notes: Android Chrome can drive USB printers directly via WebUSB over
OTG (no app, no bridge). iOS cannot — Safari does not implement WebUSB on any
platform and WebKit's position is "opposed". The router already being the app host
plus print bridge is the only path that covers every phone and every printer.

## Gotchas

- **Router is canonical.** Sync before editing, deploy after.
- **Relay restart required** after changing the HTML.
- **`gafflabel` legacy naming** in the font path and the localStorage settings key.
- **HTML-entity rule** from global standards applies when pushing HTML through the
  GitHub *API* (raw unicode gets mangled in the JSON round-trip). This repo was
  pushed with plain `git`, which is byte-exact, so the files hold raw unicode
  (`·`, `→`, `✓`, emoji) intentionally.
- **Duplicated element IDs** (`qp-scene`, `qp-body`, `qp-line1`) are emitted in two
  template literals in `renderQueue()`. It works only because one preview panel is
  ever open.
- `.dropboxignore` deliberately does **not** exclude `.git/` — that is the
  cross-machine transport in this vault's model.

## Checks before any push

Per global standards, nothing ships without a clean syntax check:

```sh
python3 -c "import ast,sys; ast.parse(open('flaggit-combined.py').read())"
# extract the <script> block from each HTML and:  node --check
```
