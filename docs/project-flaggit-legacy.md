---
name: Flaggit label printer project
description: GL.iNet router label app; SSH alias `gli`; files at /root/gafflabel.html + /root/combined.py; server must be restarted after edits
type: project
---

# Flaggit — Label Printing App on GL.iNet Router

## Access
- Router SSH alias: `gli` (resolves to root@192.168.100.1)
- Web UI: http://192.168.100.1:9000/
- SSH key: ~/.ssh/id_rsa

## Key Files on Router
- `/root/flaggit.html` — the entire frontend (single HTML file, served in-memory by flaggit-combined.py)
- `/root/flaggit-combined.py` — Python server on port 9000; handles HTTP serving and label printing via ESC/POS over TCP
- `/etc/gafflabel/font.ttc` — Helvetica TTC with 6 faces: 0=Regular, 1=Bold, 2=Italic, 3=Bold Italic, 4=Light, 5=Light Italic

## Local Backup Files (Desktop)
- `~/Desktop/flaggit.html` — exact copy of the live router file
- `~/Desktop/flaggit-combined.py` — exact copy of the live combined.py
- `~/Desktop/FLAGGIT_README.md` — full feature + architecture documentation

## Architecture
- combined.py loads gafflabel.html once at startup into memory
- **Must restart the server after editing gafflabel.html** for changes to take effect
- Restart command: `kill $(netstat -tlnp 2>/dev/null | grep :9000 | awk '{print $NF}' | cut -d/ -f1) 2>/dev/null; sleep 1; python3 -u /root/flaggit-combined.py > /tmp/server.log 2>&1 &`
- Label printing: browser builds a print queue, sends JSON per label to server, server renders PNG via Pillow and sends ESC/POS raster to printer

## Apply Changes Workflow
1. Edit `~/Desktop/flaggit.html` locally
2. Upload: `ssh gli "cat > /root/flaggit.html" < ~/Desktop/flaggit.html`
3. Restart server (command above)
4. Test via browser hard-refresh
5. Sync backups: `ssh gli "cat /root/gafflabel.html" > ~/Desktop/flaggit.html && ssh gli "cat /root/combined.py" > ~/Desktop/flaggit-combined.py`

## All Labels Use Rotated (Perp) Mode
- All 4 modes (Alpha, Numeric, Alphanumeric, Two-Line) send `perp_mode: true`
- Text rotated 90° along tape length; main text fills tape width; M/B tag at free end horizontal

## Per-Label Settings (all snapshotted at add-time)
- `font_size` — Text Size slider (200-500px mapped to 10%-100% tape fill via slider_frac)
- `label_padding` — added equally to BOTH sides of text (fold and free-end gap)
- `cable_pad` — Cable Size dropdown: Small=50, Medium=100 (default), Large=200
- `bold` — bold flag (no UI toggle currently)
- `perp_text` — MB tag text (MAIN/BACKUP); horizontal at free end
- `show_name` — optional per-label show/event name; outermost position at free end
- `show_name_invert` — black background + white text for show name

## Server: make_label_perp layout
- `BASE_PAD = 10 + cable_pad` — fold-side offset
- `TEXT_MARGIN = 10` — text height constraint (independent of cable_pad)
- `slider_frac = (max_half_px - 200) / 300` — maps slider to font height (10%→100% of tape)
- `max_h1 = min(max_total_h, max_h_by_slider)` — font height capped by slider AND tape width
- Layout: `fold → BASE_PAD → label_padding → text → BASE_GAP+label_padding → [MB tag →] [show_name →] END_PAD`
- Tag sizing: `fit_font('BACKUP', SAFE_W, SAFE_W, 0)` — MAIN/BACKUP always same scale
- Show name: `fit_font(show_name, SAFE_W, int(SAFE_W*0.55), 0)` — slightly smaller; invert = black rect + white text
- Line2 font capped at: `min(int(max_total_h * 0.30), line1_font_size)`
- Offsets: OFFSET_N=-25, OFFSET_F=+25 for centering on each flag half

## Cable Size (per-label)
- Small (XLR, Ethernet, Coax): cable_pad=50
- Medium (Edison, True1): cable_pad=100 (default)
- Large (Soca, Camlock, Snake): cable_pad=200

## Frontend Features
- **4 modes in 4x1 row**: Alpha, Numeric, Alphanumeric, Two-Line
- **Range validation**: `clampRange()` on onblur for alpha; `clampIfSpinner(event,...)` on oninput for numeric spinners only (keyboard edits wait for blur); blank end = single-item series
- **Queue**: single-tap selects (amber highlight); eye button expands inline flag preview below row (accordion); ↩ button loads preset back to build tab with full `formSnapshot`
- **Inline queue preview**: `qpOpenIdx` tracks open queue item; `qpOpenPrintedIdx` tracks open history item; only one open at a time; share same DOM IDs (`qp-scene`, `qp-line1`, etc.); `drawQueueFlag(item)` reads item data directly (not global state)
- **loadPreset**: restores mode, all series fields, copies, sliders, MB, show name, invert; switches to Build tab
- **Preview**: `drawFlag()` scales text with slider; `translateX(8px)` nudge for Barlow Condensed centering; natural height from content
- **Show Name**: per-label toggle + text + Invert (black bg/white text); preview fits single line with font-shrink loop
- **Light/Dark mode**: 🌙/☀️ button in header; persisted via localStorage `flaggit-theme`; `html.light` class on `<html>`; cards/tiles white, page background warm tan, flag canvas stays dark

## CSS Theme System
- Dark mode: default `:root` variables (bg=#0a0a0a, surf=#161616, etc.)
- Light mode: `html.light` overrides (bg=#f0ece2, surf/#card=#fff, hdr-bg=#fff8ee, tabs-bg=#f5f1e8)
- `--hdr-bg` and `--tabs-bg` are CSS variables so light mode overrides them cleanly
- Input fields: amber-tinted bg (#181408 dark / #fffbf0 light) with amber border
- Tab badge: light mode uses `#c07800` bg + white text for contrast (dark amber on black was unreadable)
- Counters use `system-ui,-apple-system,'Segoe UI',sans-serif` font (not Barlow Condensed) for digit readability

## Queue System
- **State**: `let queue = []; let selected = new Set(); let qpOpenIdx = -1;`
- **Print Selected**: amber "Print Selected (N)" button appears in toolbar when items highlighted; `printQueue()` already handles `selected.size > 0 ? queue.filter(...) : queue`
- **Multi-select**: tap to highlight, All/None/Delete toolbar buttons
- **Sticky Add to Queue**: floating outlined amber button above Print FAB; visible only on Build tab; controlled by `switchTab()`
- **Print FAB**: always shows on Build + Queue tabs; hidden on Settings; disabled when queue empty

## Print History
- After print success, items move to `printed[]` array with timestamp (`printedAt`)
- Capped at 50 items (oldest dropped)
- Rendered below queue list with ✓ checkmark and time
- **Selection**: tap to select (amber highlight); `printedSelected = new Set()`
- **Re-Add Selected**: "↩ Re-Add Selected (N)" button appears; moves items back to queue, removes from history
- **Preview**: eye button works on history items same as queue items (`togglePrintedPreview`)
- **Clear history**: wipes `printed[]` entirely

## Persistence (localStorage)
- `flaggit-queue` — active queue (auto-saved on every `renderQueue()` call)
- `flaggit-printed` — print history (max 50, auto-saved)
- `flaggit-theme` — light/dark preference
- Settings saved separately by `saveSettings()` / `loadSettings()`
- `restoreState()` called at init before `renderQueue()`
- **Before-unload guard**: `window.addEventListener('beforeunload', ...)` prompts if queue non-empty

## Auto-Ping on Load
- Silent fetch to `http://{ip}:{port}/` with 4s timeout, `mode:'no-cors'`
- Updates header status dot (ONLINE/OFFLINE) without toast or button disruption
- Fires in anonymous async IIFE at page init

## Settings Page
- Printer IP, port, tape width (40/58/80mm), Cut Between Labels

## Floating Action Buttons (FAB area)
- Both buttons in `.fab-wrap` (fixed position, bottom of screen, hidden on Settings)
- **Add to Queue** (top): outlined amber, hidden on Queue/Settings tabs
- **Print** (bottom): solid amber, disabled when queue empty; count badge uses system-ui font, white on black, font-weight:600
- Body padding: `calc(136px + var(--safe-bottom))` to clear both buttons

## Planned Features (not yet built)
- **Regular Label mode**: same tape/printer, but single-sided — no flag doubling. The label just prints once, not mirrored/folded. Preview and print flow stay the same. Queue items should visually distinguish FLAG vs LABEL type (badge or style difference on each queue row). Server-side: `make_label_perp` already renders one half; label mode would skip the second half / sep / mirror step.

## Physical Hardware (Future)

A purpose-built physical Flaggit device is planned (replacing the
GL.iNet router + Star printer + phone configuration with a single
integrated unit). When that hardware design begins, follow the
standards in repo-root `CLAUDE.md` → "PHYSICAL / INDUSTRIAL DESIGN
STANDARDS" section, with full design vocabulary in
`patent/industrial-design.md`.

Quick reference for Flaggit specifically:
- Black anodized chassis, amber `#ffb300` as the only accent (matches
  the existing software UI)
- Barlow Condensed and Share Tech Mono on any silkscreen labels
- Status display (if included) follows the Dockcase data card pattern:
  printer status, queue depth, paper level, network state
- Service connectors gold-finished where visible
- Tactile buttons with engraved markings — the device will be used in
  low-light AV environments
