# Flaggit
## Professional Cable Flag Label Printing for AV, Film & Broadcast

---

### Stop Writing on Tape. Start Printing Flags.

Flaggit is the cable labeling tool built for the people who actually pull cable. It runs on a pocket-sized router that lives in your kit — no internet, no app store, no laptop required. Your whole crew joins the WiFi, opens a browser, and starts printing in under a minute.

Labels come out bold, clean, and consistent every time. Main and Backup sets. Full numbered runs. Custom show names. Exactly sized for the cable you're wrapping. The days of squinting at marker-scrawled tape under stage lights are over.

Built for A1s, video engineers, riggers, system techs, and anyone who's ever labeled 48 channels by hand and regretted it.

---

### What It Does

**Label Generation**
- Generate full label series in seconds — Alpha (A–H), Numeric (1–48), Alphanumeric (CAM-A–CAM-D), or Two-Line
- Set start and end of any sequence; the app builds the full run automatically
- Blank end field = single label, no extra steps
- Print multiple copies of any series with one tap

**Label Customization**
- Text Size slider — from subtle to enormous, scaled precisely to tape width
- Cable Size presets — Small (XLR, Ethernet, Coax), Medium (Edison, True1), Large (Soca, Camlock, Snake) — adjusts fold clearance for the cable you're actually wrapping
- Label Padding — controls breathing room on both sides of text for clean flag proportions
- Main/Backup tagging — add a MAIN or BACKUP horizontal band to the free end of every flag in a set
- Show Name / Event Name — optional outermost band with full invert mode (white text on black) for show or venue identification
- Every setting is saved per label — mix cable sizes, text sizes, and show names freely within a single queue

**Queue Management**
- Build a queue of any size before sending to print
- Tap any item to select it (amber highlight); multi-select as many as you need
- Print the full queue or selected items only
- Delete selected items or clear the entire queue
- Eye button on each item expands an inline flag preview — exactly what will print, right in the list
- Load Preset button (↩) on any item — restores every setting back to the Build tab for quick duplication or modification

**Printing**
- One tap to send the full queue to the printer
- Print Selected — highlighted items only, leave the rest in queue
- Labels removed from queue after successful print and moved to history
- Printer status shown live in the header (Online / Offline / Unknown)
- Auto-ping checks printer connectivity the moment the page loads

**Print History**
- Every printed label is archived with a timestamp — nothing disappears
- Tap history items to select; Re-Add Selected puts them straight back in the active queue for reprints
- Preview works on history items too — confirm what you're re-adding before you do
- Holds up to 50 labels; clear history manually when done

**Session Persistence**
- Queue and print history survive page refresh, tab close, and accidental navigation
- Everything restores automatically when you reopen the app
- Browser warns you before closing if your queue isn't empty
- Theme preference remembered between sessions

**Interface**
- Live flag preview on the Build tab — updates instantly as you type and adjust sliders
- Sticky "Add to Queue" button always visible at the bottom of the Build tab — no scrolling
- Floating Print button always accessible from anywhere in the app
- Light and Dark mode — one tap toggle, full theme switch
- Designed for mobile-first touchscreen use; works on any phone, tablet, or laptop browser
- No installation, no app store, no account

---

---

# Release Notes — Flaggit v1.0

*Initial documented release — April 2026*

---

## Core Label Engine

- Four label modes: **Alpha**, **Numeric**, **Alphanumeric**, **Two-Line**
- Series generation from range (A→H, 1→48) or manual entry
- Blank end field treated as single-label series
- Range auto-correction: end field never allowed to fall below start; alpha waits for blur, numeric responds to spinner arrows immediately without interrupting keyboard edits
- Multiple copies per series
- All label settings snapshotted independently at add-time — each queue item remembers its own configuration

## Label Layout (Perp Mode)

- All labels print in rotated (perpendicular) orientation — text runs along tape length for maximum readability wrapped around a cable
- Text sized by slider: 200–500 internal range maps linearly to 10%–100% of tape width fill
- Label padding applied symmetrically to both sides of text block (fold gap and free-end gap)
- Cable Size preset adjusts fold-side offset for cable diameter clearance:
  - Small (XLR, Ethernet, Coax)
  - Medium (Edison, True1) — default
  - Large (Soca, Camlock, Snake)
- Main/Backup tag: horizontal band at flag free end; MAIN and BACKUP always printed at identical scale (sized to fit "BACKUP") for visual consistency across sets
- Show Name: optional outermost band; scales to single line; Invert option (white text on black background box with white border)

## Live Preview

- DOM-based flag preview renders in real time on the Build tab
- Mirrors server layout exactly — same slider_frac formula, same symmetric padding, same MB and Show Name positioning
- Flag body height grows naturally with content; cable bar renders at top
- Show name preview font-shrinks in a loop to guarantee single-line fit
- Preview updates on every input, slider move, mode switch, and toggle

## Queue System

- Add individual labels or full series (Main + Backup adds both sets in one tap)
- Tap to select (amber highlight); multi-select support
- Toolbar: All, None, Delete Selected, Clear All
- Print Selected button appears dynamically when items are highlighted
- Eye button on each item: inline accordion preview expands below the row; one open at a time
- Load Preset (↩): restores complete form state including mode, all series fields, sliders, cable size, MB config, and show name — without printing

## Print Flow

- Full queue or selected-only print
- Server renders each label as PNG via Pillow, transmits ESC/POS raster to thermal printer over TCP
- Printed items archived to history on success; queue cleared of sent items
- Toast notification confirms print count

## Print History

- Labels move to Print History after successful print with timestamp
- Tap to select; Re-Add Selected returns items to active queue
- Preview (eye button) works on history items identically to queue items
- Clear history button
- 50-item maximum; oldest entries dropped automatically

## Persistence

- Queue and print history auto-save to localStorage on every change
- Full restore on page load — survives refresh, tab close, accidental navigation
- Before-unload browser warning when queue is non-empty
- Theme (light/dark) persisted to localStorage
- Printer settings (IP, port, tape width, cut) persisted to localStorage

## Interface & UX

- **4×1 label mode selector** — all four modes visible without scrolling
- **Sticky Add to Queue button** — floats above Print FAB, visible only on Build tab, no scrolling required
- **Floating Print FAB** — always accessible on Build and Queue tabs; disabled and grayed when queue empty
- **Tab renamed** to "Print Queue" for clarity
- **Queue count badge** — system-ui font, medium weight, high contrast; light mode uses white text on amber for readability
- **Print FAB counter** — system-ui font, white text on black pill
- **Light / Dark mode toggle** — full theme switch; flag preview canvas always dark regardless of theme
- **Input field styling** — amber-tinted background and border to visually distinguish editable fields
- **Auto-ping on load** — silent printer connectivity check updates status dot in header immediately
- **Inline queue preview** — expands below list item (not a modal/sheet); opening one closes any other

## Settings

- Printer IP address
- Printer port
- Tape width (40 / 58 / 80 mm)
- Cut between labels toggle

---

*Flaggit runs on a GL.iNet router. No internet required after initial font load. No app installation. Any browser, any device on the local network.*
