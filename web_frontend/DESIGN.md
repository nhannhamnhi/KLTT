# Design System: Hệ Thống Kiểm Tra Vỉ Thuốc — PharmaScan HMI

**Project ID:** `3292800729238903661`
**Platform:** Web, Desktop-only (1920×1080 → 2560×2048 canvas)
**Device Type:** DESKTOP
**Color Mode:** DARK
**Source Screen:** `Monitoring Dashboard - PharmaScan HMI` (`d235bc4a8b90427a917a5563e5c4d2bd`)

---

## 1. Visual Theme & Atmosphere

This is a **mission-critical industrial monitoring dashboard** for pharmaceutical pill blister defect detection. The atmosphere is **dense, atmospheric, and utilitarian** — evoking a high-tech factory control room operating under low-light conditions.

The aesthetic follows **Industrial Cyber-Minimalism**:

- **Data-Dense & Purposeful:** Every pixel serves a function. The layout maximizes screen real estate to simultaneously display dual camera feeds, real-time statistics, and machine controls without scrolling.
- **Atmospheric Depth:** A "behind-the-glass" feel achieved through CRT-inspired scan lines (2% opacity repeating gradient overlay) and subtle electric cyan glows (`box-shadow: 0 0 10px rgba(0, 212, 255, 0.2)`) on active elements.
- **Urgency-Driven Contrast:** A deeply muted, monochromatic dark base is sharply interrupted by vivid neon signal colors — forcing the operator's eye immediately to defect statuses and critical alerts.
- **SCADA/HUD Heritage:** The interface draws from industrial SCADA panels and futuristic heads-up displays, prioritizing legibility, rapid cognition, and calm authority during high-velocity production runs.

All UI labels are rendered in **Vietnamese** to serve local factory operators.

---

## 2. Color Palette & Roles

### Core Backgrounds (Tonal Layering System)

| Descriptive Name | Hex Code | Functional Role |
|---|---|---|
| Abyssal Navy Black | `#0a0e1a` | Page canvas / application frame (Level 0 — Floor) |
| Deep Arctic Night | `#0e1417` | Surface base / overall surface color |
| Shadowed Teal-Black | `#080f12` | Deepest container / footer status bar background |
| Twilight Charcoal | `#161d1f` | Low-elevation container / toolbar header background |
| Dark Slate Teal | `#1a2123` | Mid-level container / standard surface cards |
| Frosted Obsidian | `#242b2e` | High-elevation container |
| Gunmetal Fog | `#2f3639` | Highest container / scrollbar thumb |
| Steel Shadow | `#333a3d` | Bright surface variant |

### Panel & Card Overrides (CSS Custom)

| Descriptive Name | Hex Code | Functional Role |
|---|---|---|
| Midnight Forge | `#111827` | Panel backgrounds (`.bg-panel`) — sidebar, card headers |
| Deep Blueprint | `#1a2035` | Card backgrounds (`.bg-card`) — inspection modules, controls |
| Ghost Border Blue | `#1e293b` | Container borders (`.border-panel`) — 1px structural separation |
| Industrial Vein Blue | `#1E3A5A` | Slider tracks / toolbar button borders — subtle interactive boundaries |

### Primary Accent (Cyan Family)

| Descriptive Name | Hex Code | Functional Role |
|---|---|---|
| Electric Cyan | `#00d4ff` | Primary container — action buttons ("KÍCH HOẠT"), active feed borders, mode badges |
| Frozen Lightning | `#3cd7ff` | Surface tint — active state glow, interactive highlights |
| Pale Ice Blue | `#a8e8ff` | Primary text variant — title text, branding highlights |
| Arctic Frost | `#b4ebff` | Primary fixed — soft accent for large surfaces |
| Sky Echo | `#0EA5E9` | Slider thumbs / slider fill — interactive control accent |

### Secondary Accent (Blue Family)

| Descriptive Name | Hex Code | Functional Role |
|---|---|---|
| Periwinkle Mist | `#adc6ff` | Secondary text / reset button text and borders |
| Royal Signal Blue | `#0566d9` | Secondary container — secondary interactive surfaces |
| Lavender Whisper | `#d8e2ff` | Secondary fixed — soft secondary backgrounds |

### Tertiary Accent (Amber/Gold Family)

| Descriptive Name | Hex Code | Functional Role |
|---|---|---|
| Warm Honey Glow | `#ffd9a1` | Tertiary text — warning-adjacent information |
| Molten Gold | `#feb528` | Tertiary container — amber alert badges, NG_L status indicator |
| Amber Flash | `#ffba3d` | Tertiary fixed dim — active warning highlights |

### Semantic Signal Colors

| Descriptive Name | Hex Code | Functional Role |
|---|---|---|
| Neon Phosphor Green | `#22c55e` | SUCCESS — "ĐẠT" (OK) result, connection dots, sensor active state |
| Deep Forest Green | `#166534` | Success badge background — result card fill for passing inspection |
| Pale Mint | `#86efac` | Success metadata — confidence/timestamp text on green badge |
| Vivid Alarm Red | `#ef4444` | DANGER — "LỖI NẶNG" (NG_H) result, FPS counter, failed count, defect bounding boxes |
| Soft Coral Error | `#ffb4ab` | Error text — error messages on dark backgrounds |
| Deep Crimson Void | `#93000a` | Error container — critical error badge backgrounds |
| Muted Slate | `#6b7280` | WAIT / IDLE — "CHỜ" state, disabled elements (referenced in design spec) |

### Text Hierarchy

| Descriptive Name | Hex Code | Functional Role |
|---|---|---|
| Frosted Silver | `#dde3e7` | Primary text — headings, body content, on-surface readouts |
| Cool Platinum Haze | `#bbc9cf` | Secondary text — labels, on-surface-variant, section headers |
| Weathered Steel | `#859398` | Outline / muted text — borders, disabled state, dividers |
| Smoke Signal | `#64748B` | Toolbar icon default state — inactive icon buttons |
| Deep Slate Border | `#3c494e` | Outline variant — subtle dividers, card separators |

---

## 3. Typography Rules

The system employs a **dual-typeface strategy** that separates human-readable UI from machine-read data:

### Inter — The Interface Voice

Used for all navigational, instructional, and categorical elements. Its neutral geometry provides calm authority.

| Token | Size | Weight | Line Height | Letter Spacing | Usage |
|---|---|---|---|---|---|
| `h2-label` | 24px | 600 (Semibold) | 32px | Normal | Section headings ("Điều chỉnh Camera") |
| `body-md` | 16px | 400 (Regular) | 24px | Normal | Standard body text, descriptions |
| `label-caps` | 11px | 700 (Bold) | 16px | 0.05em (Wide) | **UPPERCASE** section labels ("CAMERA GỐC", "TỔNG SỐ", "ĐĂNG NHẬP") — always uppercased |

### Roboto Mono — The Data Voice

Used exclusively for numerical readouts, timestamps, and machine-generated values. Its monospaced character ensures columns of rolling numbers never cause layout shifts.

| Token | Size | Weight | Line Height | Letter Spacing | Usage |
|---|---|---|---|---|---|
| `h1-data` | 32px | 700 (Bold) | 40px | -0.02em (Tight) | Large data display — stat counters ("45,021"), result badge text ("ĐẠT") |
| `data-lg` | 18px | 500 (Medium) | 24px | Normal | Mid-size data — clock display, secondary readouts |
| `data-sm` | 13px | 400 (Regular) | 16px | Normal | Small data — status bar values, confidence scores, slider values, connection pills |

### Font Loading

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Roboto+Mono:wght@400;500;700&display=swap" rel="stylesheet"/>
```

---

## 4. Component Stylings

### Buttons

- **Primary Action ("KÍCH HOẠT"):** Solid Electric Cyan (`#00d4ff`) background with deep teal-black text (`#00586b`). Gently softened corners (2px / `rounded-DEFAULT`). On hover: `brightness-110`. On press: `scale-95` with smooth 150ms transition. Emits a subtle 4px cyan glow on active state.
- **Secondary / Ghost ("TIẾP TỤC", "BĂNG TẢI"):** Transparent background with 1px Weathered Steel (`#859398`) border. Text in Frosted Silver (`#dde3e7`). On hover: fills with Surface Variant (`#2f3639`). Same press animation as primary.
- **Tertiary / Muted ("XI LANH 1/2"):** Transparent with 1px Outline Variant (`#3c494e`) border. Text in Cool Platinum Haze (`#bbc9cf`). Hover fills Surface Variant.
- **Login Button ("ĐĂNG NHẬP"):** Full-width, Surface Container (`#1a2123`) fill with Outline Variant border. Includes a lock icon (Material Symbols Outlined, 16px). Uppercase `label-caps` typography.
- **Toolbar Icon Buttons:** 60×40px, transparent fill, 1px Industrial Vein Blue (`#1E3A5A`) border, 6px radius. Default icon color: Smoke Signal (`#64748B`). Hover: icon and border transition to Sky Echo (`#0EA5E9`). Contains SVG icon (18px) + uppercase 10px label below.
- **Reset Button ("ĐẶT LẠI"):** Ghost style with Periwinkle Mist (`#adc6ff`) border and text. Hover: fills with `secondary/10` (10% opacity secondary).

### Cards & Containers

- **Standard Card:** Deep Blueprint (`#1a2035`) background, 1px Ghost Border Blue (`#1e293b`) border, gently softened corners (2px / `rounded-DEFAULT`). No drop shadows — depth is communicated purely through tonal layering.
- **Card Header Bar:** Midnight Forge (`#111827`) background, 1px bottom border matching card border. Contains `label-caps` section title + optional status dot.
- **Active / Highlighted Card (AI Feed):** Same as standard but with Electric Cyan (`#00d4ff`) border and cyan glow effect (`box-shadow: 0 0 10px rgba(0, 212, 255, 0.2)`).
- **Panel Container (Control Section):** Midnight Forge (`#111827`) fill — one tonal step lighter than the page canvas to create a recessed "control bay" feeling.

### Result Badge

A prominent, full-width status indicator card (180px height) centered in the right column:

| State | Vietnamese Label | Background | Border | Text Color | Glow Effect |
|---|---|---|---|---|---|
| OK / PASS | "ĐẠT" | Deep Forest Green (`#166534`) | Neon Green (`#22c55e`) | White | Green glow (`0 0 20px rgba(34,197,94,0.4)`) |
| WAIT / IDLE | "CHỜ" | Dark Gray (`#374151`) | Muted Gray (`#6b7280`) | Gray | None |
| NG_L (Light) | "LỖI NHẸ" | Deep Amber (`#92400e`) | Amber (`#f59e0b`) | White | Amber glow |
| NG_H (Heavy) | "LỖI NẶNG" | Deep Red (`#991b1b`) | Vivid Red (`#ef4444`) | White | Red pulsing glow |
| MISSING | "THIẾU" | Deep Purple (`#581c87`) | Purple (`#a855f7`) | White | Purple glow |

- Badge text uses `h1-data` at 64px size for maximum visibility
- Sub-line shows confidence + timestamp in `data-sm` with a muted success color (`#86efac`)
- Top accent bar: 100% width, 4px height, matching the border color

### Status Connection Pills (Header)

- Compact pill badges: Surface Container (`#1a2123`) background, 1px Outline Variant border, gently rounded corners
- Contains a 6px circular indicator dot + abbreviated label ("WS", "API", "PLC", "CAM")
- Active/Connected: Neon Phosphor Green (`#22c55e`) dot
- Disconnected: Vivid Alarm Red (`#ef4444`) dot
- Text: `data-sm` typography in Frosted Silver

### Sliders (Camera Adjustment)

- **Track:** Industrial Vein Blue (`#1E3A5A`) background, pill-shaped (`rounded-full`), 6px height
- **Fill:** Sky Echo (`#0EA5E9`) from left edge to thumb position
- **Thumb:** 16×16px circle, Sky Echo (`#0EA5E9`) fill, 2px Surface (`#0e1417`) border, subtle shadow
- **Label:** `data-sm` in Cool Platinum Haze, fixed 100px width
- **Value Display:** `data-sm` in Frosted Silver, fixed 40px width, right-aligned

### Stat Counters

- Vertical stack layout with horizontal `justify-between` alignment
- Label: `label-caps` uppercase in Cool Platinum Haze (`#bbc9cf`)
- Value: `h1-data` (32px bold monospace)
  - Total ("TỔNG SỐ"): White (`#ffffff`)
  - Passed ("ĐẠT"): Neon Green (`#22c55e`)
  - Failed ("LỖI"): Vivid Red (`#ef4444`)
- Separated by 1px Ghost Border Blue dividers

### Footer Status Bar

- Fixed bottom, 36px height, Abyssal container (`#080f12`) background, 1px top Outline Variant border
- Left section: `data-sm` status items separated by pipe `|` dividers in Cool Platinum Haze
  - Camera status, Model name, FPS (rendered in Vivid Red), PLC status
- Right section:
  - Mode badge ("TỰ ĐỘNG" / "THỦ CÔNG"): Pill-shaped, Electric Cyan border + 20% cyan bg fill, `label-caps` text
  - Sensor dots (S0, S1, S2): 6px green dots with `data-sm` labels
  - Digital clock: `data-lg` typography for prominent time display

### Scan Line Overlay (Global Effect)

A full-viewport fixed `div` (z-index: 9999, pointer-events: none) with:
```css
background: linear-gradient(
  to bottom,
  rgba(255,255,255,0), rgba(255,255,255,0) 50%,
  rgba(255,255,255,0.02) 50%, rgba(255,255,255,0.02)
);
background-size: 100% 4px;
```
This creates a subtle CRT scan-line texture across the entire UI at 2% opacity — reinforcing the industrial monitoring aesthetic without impeding readability.

---

## 5. Layout Principles

### Grid Architecture

- **Overall:** Full-viewport, no-scroll (`overflow-hidden`), fixed header (48px) + fixed footer (36px) + fluid main area
- **Main Split:** 75% left column (inspection area) / 25% right column (status & controls)
- **Gutters:** 12px between all adjacent elements
- **Outer Margins:** 20px horizontal padding on header, main content, and footer

### Spacing Scale (4px Baseline)

| Token | Value | Usage |
|---|---|---|
| `xs` | 4px | Tightest padding — icon gaps, pill internal |
| `sm` | 8px | Small padding — button internal, card header padding |
| `md` | 16px | Standard padding — card content, section gaps |
| `lg` | 24px | Large gaps — between slider rows |
| `xl` | 40px | Extra large — major section separation |
| `gutter` | 12px | Grid gutter — between all columns and rows |
| `margin` | 20px | Page margin — outer frame buffer |

### Vertical Zones (Top to Bottom)

1. **Header Zone (48px fixed):** Logo + toolbar + connection pills — always visible
2. **Inspection Zone (Main, ~66% height):** Dual 16:9 camera feeds side-by-side
3. **Adjustment Zone (Main, ~33% height):** Camera parameter sliders
4. **Right Panel (Full height):** Result badge → stat counters → machine controls
5. **Footer Zone (36px fixed):** Runtime telemetry bar — always visible

### Elevation Model

Depth through **Tonal Layering** only — no drop shadows:

| Level | Name | Background | Usage |
|---|---|---|---|
| 0 | Floor | `#0a0e1a` | Application canvas |
| 0.5 | Deepest | `#080f12` | Footer bar |
| 1 | Low | `#161d1f` | Header bar |
| 1.5 | Panel | `#111827` | Sidebar panels, card headers |
| 2 | Card | `#1a2035` | Content cards, modules |
| 3 | Container | `#1a2123` | Nested elements within cards |
| 4 | High | `#242b2e` | Elevated interactive areas |
| 5 | Overlay | Backdrop blur 20px | Modals, floating panels |

### Responsive Notes

This design is **NOT responsive** — it targets a fixed 1920×1080 industrial monitor. All elements use fixed or percentage-based widths within this constraint. The 75/25 column split is enforced via Tailwind's `w-3/4` and `w-1/4` utilities.

---

## 6. Icon System

- **Icon Library:** Google Material Symbols Outlined (variable weight 100-700, fill 0-1)
- **Toolbar Icons:** Custom inline SVGs, 18×18px, `stroke-width: 1.5`, no fill
- **Status Indicators:** Pure CSS 6×6px circles (`rounded-full`) — no icon dependency
- **Loading:** `font-size: 16px` for inline Material Symbols

```html
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
```

---

## 7. Motion & Interaction

| Element | Effect | Duration | Easing |
|---|---|---|---|
| Toolbar buttons | Color + border transition on hover | 150ms | `ease` (default Tailwind `transition-all`) |
| Action buttons | `scale(0.95)` on `:active` | 150ms | `ease` |
| Primary buttons | `brightness(1.1)` on hover | 150ms | `ease` |
| Result badge | Background color crossfade between states | 300ms | `ease-in-out` |
| Connection pills | Dot color change (green ↔ red) | Instant | — |
| Reset button | Background opacity fill on hover | 150ms | `ease` |
| Scan line overlay | Static — no animation | — | — |

---

## 8. Stitch Prompting Reference

When generating new screens in this project, include this block at the top of every prompt:

```
Use the design system from Project ID 3292800729238903661.
Maintain the dark industrial SCADA aesthetic with:
- Deep navy backgrounds (#0a0e1a, #111827, #1a2035)
- Electric Cyan (#00d4ff) as primary accent
- Inter for UI labels, Roboto Mono for data/numbers
- Tonal layering for depth (no drop shadows)
- CRT scan-line overlay effect
- All labels in Vietnamese
- label-caps (11px, bold, uppercase, 0.05em tracking) for section headers
- Ghost Border Blue (#1e293b) for all container borders
```

---

*Tạo bởi design-md skill — Nguồn: Stitch MCP Project `3292800729238903661`, Screen `d235bc4a8b90427a917a5563e5c4d2bd`*
*Cập nhật: 2026-05-07*
