# Flaggit — Cable Flag Label Printer
### AV · Film · Broadcast

---

## What Is Flaggit?

Flaggit is a purpose-built mobile web application for printing cable flag labels on a thermal label printer, designed specifically for the fast-paced demands of live events, film production, and broadcast environments. It runs entirely on a GL.iNet travel router, meaning it requires **no internet connection, no cloud service, and no app installation** — crew members connect to the router's WiFi and open the web UI on any phone or tablet.

A "flag label" is a strip of gaffer tape or label stock that wraps around a cable, with the two sticky halves meeting back-to-back to form a flag that hangs free. Flaggit prints these with large, bold, rotated text optimized for quick identification from a distance — essential when tracing cables in a dark studio, packed snake box, or live stage.

---

## Marketing Summary

> **Label your cables in seconds, not minutes.**
>
> Flaggit eliminates the marker-and-tape ritual. Build a full cable run — Main and Backup, numbered 1 through 24, in three taps — queue it, and print. Labels come out perfectly sized, boldly typed, and consistently formatted every time. No laptop required. No app to install. Just join the WiFi and go.
>
> Built for A1s, video engineers, riggers, and anyone who's ever squinted at a hand-scrawled cable label in the dark.

---

## Hardware Setup

| Component | Details |
|---|---|
| Router | GL.iNet (any model running OpenWrt) |
| Router IP | `192.168.100.1` |
| SSH access | `ssh gli` (alias for `root@192.168.100.1`) |
| SSH key | `~/.ssh/id_rsa` |
| Web UI | `http://192.168.100.1:9000/` |
| Printer | Thermal label printer, TCP/IP at `192.168.100.101:9100` |
| Printer protocol | ESC/POS raster |
| Tape widths supported | 40 mm, 58 mm, 80 mm |

### Key Files on Router

| File | Purpose |
|---|---|
| `/root/gafflabel.html` | Entire frontend — single HTML file, loaded into memory at server start |
| `/root/combined.py` | Python HTTP server on port 9000; handles all requests and label rendering |
| `/etc/gafflabel/font.ttc` | Helvetica TTC with 6 faces: 0=Regular, 1=Bold, 2=Italic, 3=Bold Italic, 4=Light, 5=Light Italic |

### Local Backups (Development Machine)

| File | Purpose |
|---|---|
| `~/Desktop/flaggit.html` | Exact copy of live router frontend |
| `~/Desktop/flaggit-combined.py` | Exact copy of live combined.py |

---

## Architecture

### Server (`combined.py`)

A pure Python HTTP server running on port 9000. At startup it reads `gafflabel.html` once into memory and serves it for all `GET /` requests. Label print jobs arrive as `POST /print` with a JSON body.

**Important:** The server must be restarted after any edit to `gafflabel.html`. The file is only read at startup.

**Restart command:**
```bash
kill $(netstat -tlnp 2>/dev/null | grep :9000 | awk '{print $NF}' | cut -d/ -f1) 2>/dev/null
sleep 1
python3 -u /root/combined.py > /tmp/server.log 2>&1 &
```

### Label Rendering (`make_label_perp`)

All labels use **perp mode** — text is rendered horizontally in Pillow, then rotated 90° clockwise so it runs along the length of the tape. The tape is treated as a vertical canvas where the top is the fold/cable side and the bottom is the free end of the flag.

**Tape constants (40mm tape):**
- `W = 320` px — full tape width (8.42 px/mm)
- `SAFE_W = 270` px — safe text area (leaving margin each side)
- `TEXT_MARGIN = 10` px — always-on margin, independent of cable pad

**Layout formula (fold → free end):**
```
fold edge → BASE_PAD → label_padding → [text] → BASE_GAP + label_padding → [MB tag] → [show_name] → END_PAD
```

Where:
- `BASE_PAD = 10 + cable_pad` — fold-side offset (grows with cable diameter)
- `BASE_GAP = 8` — minimum gap between text and MB tag
- `END_PAD = 10` — free-end margin
- `label_padding` is added symmetrically: once before text, once in the gap after text

**Font sizing:**
```python
slider_frac = max(0.0, min(1.0, (max_half_px - 200) / 300))
max_h_by_slider = max(10, int(max_total_h * (0.10 + 0.90 * slider_frac)))
```
The slider value (`max_half_px`, range 200–500) maps linearly: 200 = 10% tape fill, 500 = 100% tape fill.

**Two-line sizing caps:**
- Line 1: `min(int(max_total_h * 0.62), max_h_by_slider)`
- Line 2: `min(int(max_total_h * 0.30), line1_font_size)`

**MB tag sizing:**
- Always uses `fit_font('BACKUP', SAFE_W, SAFE_W, 0)` — MAIN and BACKUP render at identical scale for consistency
- Positioned horizontally at the free end

**Show Name sizing:**
- `fit_font(show_name, SAFE_W, int(SAFE_W * 0.55), 0)` — slightly smaller than MB tag
- Invert mode: black rectangle drawn first, then white text on top

### Print Job Format

`POST /print` with JSON body:
```json
{
  "labels": [
    {
      "line1": "A",
      "line2": null,
      "font_size": 430,
      "label_padding": 0,
      "cable_pad": 100,
      "bold": false,
      "perp_mode": true,
      "perp_text": "MAIN",
      "show_name": "ROCK SHOW",
      "show_name_invert": false
    }
  ],
  "sep": 200
}
```

Each label is rendered as a PNG via Pillow, converted to ESC/POS raster format, and sent to the printer via TCP socket on port 9100.

### Frontend (`gafflabel.html`)

A single self-contained HTML file. No build step, no external dependencies at runtime (fonts loaded from Google Fonts at startup). All JavaScript is inline. State is managed in plain JS variables with localStorage persistence.

**Fonts loaded:**
- `Share Tech Mono` — UI monospace (queue text, labels, codes)
- `Barlow Condensed` — display font (preview flag text, buttons, headers)

---

## Feature Reference

### Label Modes

Four modes arranged in a 4×1 row at the top of the Build tab.

#### Alpha
Generates a sequence of single letters or custom letter ranges.
- **Methods:** Range (A → H) or Manual (comma-separated list)
- **Range validation:** Start/end auto-corrected so end is never less than start. Blank end = single label.
- Fields: `alpha-method`, `alpha-from`, `alpha-to`, `alpha-manual`

#### Numeric
Generates a sequence of numbers with optional zero-padding.
- Fields: start number, end number, zero-pad width
- **Range validation:** Spinner arrows clamp immediately; keyboard edits wait for blur.
- Blank end = single label.

#### Alphanumeric
Combines a text prefix with a numeric or alpha suffix.
- Fields: prefix, separator, series type (numeric or alpha), range fields
- Examples: `A-1` through `A-8`, `CAM-A` through `CAM-D`

#### Two-Line
Prints a fixed Line 1 with a variable Line 2 series.
- Line 1 is static across all labels in the series
- Line 2 uses numeric, alpha, or alphanumeric series
- Line 1 renders ~62% of tape height; Line 2 ~30%

---

### Per-Label Settings

All settings are **snapshotted at add-time** — each queue item remembers its own values independently.

| Setting | UI Element | Values | Notes |
|---|---|---|---|
| Text Size | Slider | 200–500 (internal) | Displayed in mm; maps to 10%–100% tape fill |
| Label Padding | Slider | 0–60 px | Added equally to BOTH sides of text block |
| Cable Size | Dropdown | Small / Medium / Large | Adds offset to fold side to clear cable diameter |
| MB Tag | Toggle + text | MAIN / BACKUP (or custom) | Horizontal band at free end of flag |
| Show Name | Toggle + text + Invert | Any string | Outermost band; invert = white text on black box |

**Cable Size values (cable_pad):**
| Size | Value | Suitable For |
|---|---|---|
| Small | 50 px | XLR, Ethernet, Coax |
| Medium | 100 px (default) | Edison, True1 |
| Large | 200 px | Soca, Camlock, Snake |

---

### Preview

A live DOM-based flag preview renders on the Build tab as you adjust settings. It mirrors the server layout exactly:
- Uses CSS `writing-mode: vertical-lr` for rotated text
- `translateX(8px)` nudge compensates for Barlow Condensed's built-in bearing offset
- Flag body height grows naturally with content — no fixed height
- Cable rendered as a rounded dark bar at the top
- Show name preview shrinks font in a loop until text fits single line within flag width
- Show name invert: black background with 8px horizontal margin, white text

The preview updates live on every slider move, input change, mode switch, and setting toggle.

---

### Queue

The queue collects labels before printing. Labels are added individually or as full series (e.g., "Add A–H as MAIN + BACKUP" adds 16 items at once).

**Queue item data stored per label:**
- `line1`, `line2`, `twoLine` — label text
- `fontSize`, `labelPadding`, `cablePad` — rendering settings
- `mbType` ('main' / 'back' / null), `mbText` — MB tag
- `showName`, `showNameInvert` — show name
- `bold` — bold flag
- `formSnapshot` — full form state for preset restoration (mode, all series fields, copies)
- `printedAt` — timestamp added when item moves to history

**Queue actions:**
| Action | How |
|---|---|
| Add label(s) | "Add to Queue" floating button (Build tab) |
| Select item | Tap row (amber highlight) |
| Select all | "All" button in toolbar |
| Deselect all | "None" button |
| Delete selected | "Delete" button |
| Clear entire queue | "Clear All" button |
| Print all | "Print" FAB at bottom |
| Print selected only | "Print Selected" amber button (appears when items highlighted) |
| Preview inline | Eye (👁) button — expands flag preview below that row |
| Load preset | ↩ button — restores all settings to Build tab without printing |

---

### Print Flow

1. User taps Print (all) or Print Selected
2. App builds JSON payload from queue items
3. `POST /print` to `http://{ip}:{port}/print`
4. Server renders each label as PNG via Pillow
5. Server sends ESC/POS raster to printer via TCP
6. On success: printed items move to **Print History** section
7. Queue is cleared of printed items
8. State auto-saves to localStorage

---

### Print History

After printing, labels are archived in a "Print History" section at the bottom of the Print Queue tab — they are not deleted.

**History features:**
- Each item shows label text, ✓ checkmark, and print timestamp
- Tap to select (same amber highlight pattern as queue)
- Eye button opens inline flag preview (identical to queue preview)
- **Re-Add Selected** button appears when items are highlighted — moves them back into the active queue
- **Clear history** button wipes the log
- Maximum 50 items (oldest drop off automatically)
- History persists across sessions via localStorage

---

### Persistence (localStorage)

The app auto-saves and auto-restores state on every change.

| Key | Content |
|---|---|
| `flaggit-queue` | Full queue array as JSON |
| `flaggit-printed` | Print history array (last 50) as JSON |
| `flaggit-theme` | `'light'` or `'dark'` |
| Settings (IP, port, width, cut) | Saved by `saveSettings()` / `loadSettings()` |

**Before-unload guard:** If the queue is non-empty and the user attempts to close or refresh the page, the browser shows a "Leave site?" confirmation dialog.

---

### Inline Flag Preview

Queue and history items each have an eye icon (👁) button that expands an inline preview panel directly below that row — like an accordion. Closing one automatically closes any other open preview. The preview is rendered using `drawQueueFlag(item)`, which reads directly from the stored item data (not global form state), so it always reflects what will actually print.

---

### Load Preset (↩)

The ↩ button on any queue item restores the full form state to the Build tab:
- Switches to the correct label mode
- Restores all series fields (range start/end, method, prefix, separator, etc.)
- Restores sliders, cable size, copies
- Restores MB toggle, MB text, MB type
- Restores Show Name toggle, text, and invert state
- Switches to the Build tab and updates the preview

This lets you quickly replicate a label set with minor modifications without starting over.

---

### Theme System

Light/dark toggle in the header (🌙/☀️). Persisted to localStorage.

**CSS architecture:**
- Dark mode: default `:root` variables
- Light mode: `html.light` class on `<html>` element overrides variables
- All colors reference CSS variables — no hardcoded values in components
- Key variables: `--bg`, `--surf`, `--surf2`, `--surf3`, `--border`, `--border2`, `--amber`, `--amber2`, `--amber-dim`, `--amber-bg`, `--hdr-bg`, `--tabs-bg`
- Input fields: amber-tinted bg (`#181408` dark / `#fffbf0` light) with amber border
- Flag preview canvas always stays dark (even in light mode) for accurate label preview

---

### Printer Status

The header shows live printer status (ONLINE / OFFLINE / UNKNOWN) with a colored dot.

- **Auto-ping on load:** Silent status check fires immediately at page open
- **Manual test:** "Test Connection" button on Settings tab
- Status updates automatically after every print attempt

---

### Settings

| Setting | Notes |
|---|---|
| Printer IP | Default `192.168.100.101` |
| Printer Port | Default `9100` |
| Tape Width | 40 / 58 / 80 mm |
| Cut Between Labels | Toggle — inserts a cut command between each label |

---

### Range Validation

Both alpha and numeric ranges are validated to prevent illegal sequences:

- **Alpha (Range mode):** Validated on blur. If start > end after edit, the other field snaps to match. Blank end = single label.
- **Numeric:** Spinner arrows (↑↓) trigger immediate clamping. Keyboard edits wait for blur to avoid clamping mid-deletion (e.g., deleting a digit from "100" temporarily shows "10" — don't clamp yet).
- Same logic applies in Alphanumeric and Two-Line series fields.

---

## Development Workflow

### Apply Changes to Router

```bash
# 1. Edit ~/Desktop/flaggit.html locally

# 2. Upload
ssh gli "cat > /root/gafflabel.html" < ~/Desktop/flaggit.html

# 3. Restart server
ssh gli "kill \$(netstat -tlnp 2>/dev/null | grep :9000 | awk '{print \$NF}' | cut -d/ -f1) 2>/dev/null; sleep 1; python3 -u /root/combined.py > /tmp/server.log 2>&1 &"

# 4. Test in browser (hard refresh)

# 5. Sync backups
ssh gli "cat /root/gafflabel.html" > ~/Desktop/flaggit.html
ssh gli "cat /root/combined.py" > ~/Desktop/flaggit-combined.py
```

### Patch Script Pattern (for server-side edits)

```bash
ssh gli "cat > /tmp/patch.py" << 'PYEOF'
# Python patch script here
PYEOF
ssh gli "python3 /tmp/patch.py"
# Then restart server
```

### View Server Logs

```bash
ssh gli "tail -f /tmp/server.log"
```

---

## Key Implementation Details (for Claude)

These are non-obvious details that are critical for maintaining correctness:

### Preview ↔ Server Parity
The frontend `drawFlag()` preview and server `make_label_perp()` must use the **same slider_frac formula**:
```
slider_frac = (fontSize - 200) / (500 - 200)
```
Any change to font sizing in one must be mirrored in the other.

### Label Padding is Symmetric
`label_padding` is added to **both** sides of the text block — before text (fold side gap) AND in the gap between text and MB tag (free end side). Both the server layout and the preview `padTop`/`gapToTag` calculations must include it.

### TEXT_MARGIN is Independent of Cable Pad
`max_total_h = W - 2 * TEXT_MARGIN` (always 10px each side). The cable pad only affects the fold-side offset, not the available text height. This was a critical bug fix — early versions used `BASE_PAD` for text height which made text tiny at large cable sizes.

### Server Loads HTML Once
`gafflabel.html` is read into memory at server startup. Editing the file has no effect until the server is restarted. Always restart after uploading.

### Queue Item formSnapshot
Every queue item stores a `formSnapshot` — the full form state at the moment of adding. This is what the ↩ (load preset) button restores. It includes: `mode`, `copies`, `alphaMethod`, `alphaFrom`, `alphaTo`, `alphaManual`, `numStart`, `numEnd`, `numPad`, `anPrefix`, `anSep`, `anStype`, `anNumStart`, `anNumEnd`, `anNumPad`, `anAlphaFrom`, `anAlphaTo`, `tlLine1`, `tlStype`, `tlNumStart`, `tlNumEnd`, `tlNumPad`, `tlAlphaFrom`, `tlAlphaTo`, `tlAnPrefix`, `tlAnStart`, `tlAnEnd`.

### Preview Panel ID Sharing
Queue and history preview panels share the same DOM element IDs (`qp-scene`, `qp-line1`, etc.) because only one can be open at a time — opening a queue preview closes any history preview and vice versa. `qpOpenIdx` tracks queue open state; `qpOpenPrintedIdx` tracks history open state.

### MB Tag Scale
MAIN and BACKUP are always rendered at the same font size — sized to fit "BACKUP" (the longer word) — so tags are visually consistent across labels in a set.

### Barlow Condensed Centering Nudge
CSS `writing-mode: vertical-lr` combined with Barlow Condensed's bearing creates an optical misalignment. A `translateX(8px)` is applied to the main text element in the preview to compensate. This is preview-only; the server centers mathematically in PIL.

### localStorage Keys
- `flaggit-queue` — active queue
- `flaggit-printed` — print history (max 50)
- `flaggit-theme` — `'light'` or `'dark'`
- `flaggit-settings` — IP, port, tape width, cut toggle

---

## File Size and Dependencies

| Dependency | How Used |
|---|---|
| Python 3 | Server runtime |
| Pillow (PIL) | Label image rendering |
| Google Fonts (Barlow Condensed, Share Tech Mono) | Loaded at page open; requires internet on first visit, then cached |
| No npm, no build tools, no frameworks | Pure HTML/CSS/JS |

---

*Flaggit — Built for the truck. Ready for anything.*
