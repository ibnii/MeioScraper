---
name: Novelin
description: A local reading desk for choosing and exporting accessible novel chapters.
colors:
  paper: "#F2EBDD"
  paper-raised: "#FBF6EC"
  paper-deep: "#E8DDC9"
  ink: "#241E18"
  ink-soft: "#6B5F52"
  ink-faint: "#746655"
  rule: "#D6C8B4"
  rule-strong: "#B9A88F"
  terracotta: "#B24A2E"
  terracotta-deep: "#8C3520"
  terracotta-soft: "#F0D9CC"
  moss: "#3E6B4F"
  moss-soft: "#DFE9DF"
  rust: "#9B5A2E"
  rust-deep: "#854A24"
  rust-soft: "#F2E0D1"
  highlight: "rgba(255, 255, 255, 0.22)"
  reader-sepia-bg: "#F3E7D3"
  reader-sepia-text: "#3A2E22"
  reader-sepia-rule: "#D8C6AA"
  reader-sepia-raised: "#E4D3BA"
  reader-night-bg: "#1C1916"
  reader-night-text: "#E9DFD1"
  reader-night-muted: "#B3A797"
  reader-night-rule: "#3A322A"
  reader-night-accent: "#E09A78"
  reader-night-raised: "#332C24"
  night-paper: "#1C1916"
  night-paper-raised: "#26211C"
  night-paper-deep: "#14110F"
  night-ink: "#E9DFD1"
  night-ink-soft: "#B3A797"
  night-ink-faint: "#9A8D7D"
  night-rule: "#3A322A"
  night-rule-strong: "#574B3E"
  night-terracotta: "#D97F5F"
  night-terracotta-deep: "#E8A98C"
  night-terracotta-soft: "rgba(217, 127, 95, 0.16)"
  night-moss: "#9BC4A8"
  night-moss-soft: "rgba(90, 134, 107, 0.18)"
  night-rust: "#C98A63"
  night-rust-deep: "#E0A67C"
  night-rust-soft: "rgba(185, 121, 74, 0.16)"
  night-shell: "#14110F"
typography:
  display:
    fontFamily: "Spectral, Georgia, 'Times New Roman', serif"
    fontSize: "clamp(2.7rem, 4.6vw, 4.4rem)"
    fontWeight: 600
    lineHeight: 0.98
    letterSpacing: "-0.04em"
  headline:
    fontFamily: "Spectral, Georgia, 'Times New Roman', serif"
    fontSize: "clamp(2rem, 3.8vw, 3.2rem)"
    fontWeight: 600
    lineHeight: 1.02
    letterSpacing: "-0.035em"
  title:
    fontFamily: "Spectral, Georgia, 'Times New Roman', serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "-0.025em"
  body:
    fontFamily: "'Public Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.65
  reader:
    fontFamily: "Spectral, Georgia, 'Times New Roman', serif"
    fontSize: "1.08rem"
    fontWeight: 400
    lineHeight: 1.85
  label:
    fontFamily: "'Public Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "0.75rem"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0.09em"
rounded:
  xs: "3px"
  sm: "2px"
  md: "4px"
  pill: "999px"
spacing:
  xs: "6px"
  sm: "10px"
  md: "16px"
  lg: "24px"
  xl: "38px"
  section: "48px"
components:
  button-primary:
    backgroundColor: "{colors.terracotta}"
    textColor: "{colors.paper-raised}"
    rounded: "{rounded.md}"
    padding: "0 18px"
    height: "48px"
  button-primary-hover:
    backgroundColor: "{colors.terracotta-deep}"
    textColor: "{colors.paper-raised}"
    rounded: "{rounded.md}"
    padding: "0 18px"
    height: "48px"
  button-ghost:
    backgroundColor: "{colors.paper-raised}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "0 18px"
    height: "48px"
  input:
    backgroundColor: "{colors.paper-raised}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "13px 15px"
    height: "48px"
  chip-free:
    backgroundColor: "{colors.moss-soft}"
    textColor: "{colors.moss}"
    rounded: "{rounded.sm}"
    padding: "3px 6px"
  chip-locked:
    backgroundColor: "{colors.rust-soft}"
    textColor: "{colors.rust-deep}"
    rounded: "{rounded.sm}"
    padding: "3px 6px"
  panel:
    backgroundColor: "{colors.paper-raised}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "22px"
---

# Design System: Novelin

## Overview

**Creative North Star: "The Reading Desk"**

Novelin is a working surface that borrows the calm of a reading desk rather than the chrome of a dashboard. The page ground is unbleached paper; the top bar is a cloth-bound spine in deep ink; terracotta is the single editorial accent, used for the primary action, selection, and progress. Everything else is carried by hairlines, tabular numerals, and two type voices.

The system is restrained on purpose. Operate surfaces earn familiarity: controls look like controls, the chapter ledger reads like a ledger, and the signature move is a printed check stamp that appears when a chapter has been set into the file. The world never turns a button into a book or a table into a newspaper.

**Key Characteristics:**
- Warm paper ground with a deep ink shell and one terracotta accent.
- Spectral for titles and reading voice; Public Sans for controls, labels, and data.
- Hairline rules instead of cards inside cards.
- Printed state marks: free/locked chips and a green stamp for downloaded chapters.
- A measured galley gauge, not a progress ring.
- A focused reader in Kertas, Sepia, or Malam, with a printed drop cap on the first prose paragraph.
- A warm dark mode that keeps the ink shell and lightens terracotta instead of inverting the palette.

## Colors

The palette is a pinned warm editorial world. The ink header is the committed field; paper and terracotta do the rest.

### Primary
- **Terracotta** (#B24A2E): the primary action, selected rows, active format, and progress fill. It should own less than a fifth of any screen.
- **Deep Terracotta** (#8C3520): hover and accent text on paper; the second line of the opening headline.

### Secondary
- **Moss** (#3E6B4F) on **Moss Wash** (#DFE9DF): a free chapter and a completed download.
- **Rust** (#9B5A2E) on **Rust Wash** (#F2E0D1): a locked chapter or a failed event. Text uses **Deep Rust** (#854A24) for contrast.

### Neutral
- **Paper** (#F2EBDD): the page field.
- **Raised Paper** (#FBF6EC): panels, inputs, and chips.
- **Deep Paper** (#E8DDC9): skeleton blocks and inactive wells.
- **Ink** (#241E18): body text and the top bar.
- **Soft Ink** (#6B5F52): secondary text.
- **Faint Ink** (#746655): dates, hints, and disabled labels. Never lighter than this on paper.
- **Rule** (#D6C8B4) and **Strong Rule** (#B9A88F): hairlines and input borders.

**The One Accent Rule.** Terracotta marks action and selection only. It is not a decorative wash, a heading color for every section, or a border on every card.

**The Printed State Rule.** Status is always text plus shape, never color alone: `Gratis`, `1 koin`, a lock glyph, a check stamp, or a dash.

### Reader Themes
- **Kertas:** Raised Paper (#FBF6EC) ground with Ink (#241E18) text; the default.
- **Sepia:** #F3E7D3 ground with #3A2E22 text; rules #D8C6AA.
- **Malam:** #1C1916 ground with #E9DFD1 text; muted #B3A797; accent #E09A78. A warm dark, never blue-black.

### Dark Mode

The dark theme keeps the same roles rather than inverting the light hierarchy. The shell remains darker than the page (#14110F vs #1C1916), the page raises to #26211C, and ink becomes warm #E9DFD1. Terracotta lightens to #D97F5F with #26211C text; moss and rust lighten into state colors. The toggle lives in the top bar, stores `novelin:theme`, and is applied before first paint. The reader defaults to Malam in dark mode when the reader has no saved theme.

**The Dark Shell Rule.** The shell is always darker than the page. Dark mode is not an inversion of the light theme; it is the same hierarchy with a warm dark ground.

## Typography

**Display Font:** Spectral (with Georgia and Times New Roman fallbacks), self-hosted.
**Body Font:** Public Sans (with the platform sans stack), self-hosted.

**Character:** Spectral provides the literary voice without the costume of a display serif; Public Sans keeps dense chapter data quiet and legible. The pairing is editorial, not nostalgic.

### Hierarchy
- **Display** (600, clamp 2.7–4.4rem, 0.98 line-height): the opening thesis only.
- **Headline** (600, clamp 2–3.2rem, 1.02): the novel title.
- **Title** (600, 1.5rem, 1.15): the "Berkas" panel and section headings.
- **Body** (400, 1rem, 1.65): the lede and synopsis, held to roughly 62ch.
- **Label** (600, 0.75rem, 0.09em tracking, uppercase): field labels, source links, and format legends.

**The Two Voices Rule.** Spectral never sets a button, a chapter title in the ledger, a date, or a badge. Public Sans never sets the page thesis or the novel title.

## Layout

The shell is a 1320px maximum grid with a fluid workspace and a 360px export rail, separated by 48px. The rail is sticky at 88px from the top. Below 1120px the rail narrows to 324px; below 980px the layout becomes one column, the rail moves into flow, and a fixed mobile dock carries the selected count, a format selector, an "Opsi" jump to the export panel, and the download action.

The opening viewport is a two-column reading desk: thesis and ruled URL field on the left, a colophon-like export panel on the right. Once a novel is loaded, the thesis and examples collapse, the URL form remains as a compact source bar, and the novel header becomes the first content block. The chapter ledger shows 80 rows at a time, with a measured "load more" action rather than an infinite scroll.

Spacing follows a tight-groups, generous-separation rhythm: 10px inside a row, 16px between controls, 26–38px between major blocks, 48px for the opening section.

## Elevation & Depth

Depth is mostly tonal and linear. Hairlines divide the ledger; paper-raised panels sit one value above the ground. The only soft shadows are the export panel and the cover, both offset downward with a wide negative-spread blur. There are no hard offset shadows, no glass, and no glow.

### Shadow Vocabulary
- **Panel lift** (`0 22px 48px -30px rgba(36, 30, 24, 0.45), 0 2px 6px rgba(36, 30, 24, 0.06)`): the sticky export panel and the cover image.
- **Toast lift** (same value): transient status messages.

**The Flat-By-Default Rule.** Surfaces are flat at rest. Elevation appears only on the export panel and the cover; a row never floats.

## Shapes

Corners are small and printed: 2px for chips, checkboxes, and stamps; 4px for buttons, inputs, and panels; a pill only for the job progress bar. Rules are 1px; the top bar carries a single terracotta bottom rule. No large rounded cards, no colored side stripes.

## Components

### Buttons
- **Shape:** 4px radius, 48px minimum height.
- **Primary:** terracotta field, raised-paper text, 18px horizontal padding, a soft inset highlight and a downward shadow. Hover deepens to deep terracotta; active shifts down 1px.
- **Ghost:** raised-paper field with a strong-rule border; hover moves to deep paper.
- **Disabled:** full-opacity Deep Paper field with a Soft Ink label (4.6:1 on Deep Paper), no shadow, no hover change. The label states the missing prerequisite ("Pilih chapter dulu").

### Chips
- **Style:** 2px radius, uppercase 0.7rem label, wash background. Free uses moss; locked uses rust and carries a 10px lock glyph.
- **State:** the chip never responds to hover; it is data, not a control.

### Cards / Containers
- **Corner Style:** 4px for the export panel; no card inside a card.
- **Background:** raised paper on the paper ground.
- **Shadow Strategy:** panel lift only.
- **Border:** 1px strong rule.
- **Internal Padding:** 22px.

### Inputs / Fields
- **Style:** raised-paper field, 1px strong rule with a darker bottom edge, 4px radius.
- **Focus:** terracotta border plus a 2px 20% terracotta halo.
- **Disabled:** inherited muted text and a dashed checkbox box for locked rows.

### Navigation
- **Style:** a deep ink top bar with a cream wordmark, a theme toggle, and a tracked uppercase source link. There is no multi-page navigation; the only route is the reading desk and its source link.
- **Mobile:** the note hides; the wordmark, theme toggle, and source link remain.

### Theme Toggle
A small outlined control in the top bar: moon + "Gelap" in light mode, sun + "Terang" in dark mode. `aria-pressed` reflects dark mode; the preference lives in `novelin:theme` and is applied inline before first paint.

### Chapter Ledger (signature component)
A five-part row: checkbox, zero-padded index, title/date/chip, a labelled "Baca" button, and a state stamp. The Baca button opens the reader directly to that chapter; the rest of the row toggles selection. Selected rows take a near-paper terracotta tint (9% alpha); the filled checkbox and gauge carry the selection, keeping the accent below a fifth of the screen. Completed rows take a moss wash and a circled check stamp that arrives with a 240ms press. Locked checkboxes are dashed, disabled, and never selectable without a user cookie.

### Galley Gauge
A 14px horizontal rail with a terracotta fill and ten printed tick divisions. It reports selection out of available chapters before a run and processed-out-of-total during a run. It is never a progress ring.

### Export Panel
A sticky colophon: selection count, gauge, format segmented control, cover switch, advanced options, primary download action, and a live job section with a progress bar, the latest eight events, and a save link. The cancel action disappears once the job is terminal; a disabled action never lingers beside a finished result.

### Mobile Dock
A fixed ink bar below 980px: selected count, an "Opsi" link that jumps to the colophon, a compact EPUB/TXT/JSON selector, and the primary download action. It exists so format can be chosen from the ledger, not 5,000px below it.

### Reader Page
A focused reading route at `/read/<slug>/<index>`, opened from a ledger row or "Mulai baca". The page fills the viewport on both mobile and desktop, with the reading body as the only scroll container and a centered 66ch measure inside. Prev/next navigate in place with `history.pushState`; opening the URL directly fetches the novel first.

- **Type:** Spectral at 0.98/1.08/1.2rem, 1.85 line-height, 66ch measure.
- **Drop cap:** the first prose paragraph of 80+ characters gets a 3.3em terracotta drop cap; chapter labels and short lines are skipped.
- **Controls:** A−/A+, Kertas/Sepia/Malam theme buttons, source link, close; footer has previous, position, next.
- **State:** a locked chapter shows a lock mark, the coin label, and an inline cookie field. It is not fetched without a cookie.
- **Motion:** the page opens without a staged entrance; progress is a 3px rail tied to scroll position.
- **Immersive:** clicking the reading canvas hides the header, footer, and progress rail without resizing the full-viewport page. Clicking again or pressing `F` restores the chrome. Links, buttons, form fields, and text selection are exempt.

**The Quiet Canvas Rule.** The reading surface itself is the immersive control. Chrome never auto-hides while scrolling, and a click on a link or a text selection never toggles it.

### Recommendation List
A text-only dashboard ledger, not a card grid. Rows pair a Spectral title (1.05rem) with a right-aligned muted slug (0.72rem) over a hairline; hover raises the paper and turns the title terracotta. Clicking loads that novel and the list disappears into the working view. No covers, no thumbnails, no carousel.

## Do's and Don'ts

### Do:
- **Do** keep the page ground paper and the top bar ink; the contrast is the shell.
- **Do** use the printed stamp for completed chapters and a dash for skipped ones.
- **Do** keep the chapter ledger at 80 rows per page and preserve selection across filters.
- **Do** keep the selected-row wash near paper; let the filled box and stamp carry state.
- **Do** keep the reader at a 66ch measure and put the drop cap on the first long prose paragraph.
- **Do** keep the shell darker than the page in both themes and lighten terracotta for dark mode.
- **Do** keep dashboard recommendations as a text ledger; no covers or card grid.
- **Do** let the reading canvas toggle immersive chrome, while leaving links, buttons, and text selection alone.
- **Do** state the reason for a disabled action in the action label.

### Don't:
- **Don't** introduce a second accent color for decoration; moss and rust are state colors only.
- **Don't** replace hairlines with nested rounded cards or colored left borders.
- **Don't** use a progress ring, sparkline, or hero metric in place of the chapter data.
- **Don't** lighten secondary text below Faint Ink (#746655) on paper.
- **Don't** bypass or imply bypass of a locked chapter; the gate is product truth.
