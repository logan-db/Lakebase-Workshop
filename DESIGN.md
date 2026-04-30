---
name: Lakebase Lab Console
description: Hands-on workshop console for exploring Databricks Lakebase Autoscaling
colors:
  ember-orange: "#ff6b35"
  ember-hover: "#ff8055"
  signal-blue: "#3b82f6"
  deep-violet: "#8b5cf6"
  live-teal: "#14b8a6"
  clear-green: "#22c55e"
  caution-amber: "#f59e0b"
  alert-red: "#ef4444"
  night-surface: "#0f1117"
  night-card: "#1a1d2b"
  night-inset: "#12141c"
  night-elevated: "#2a2e3f"
  night-sidebar: "#0d0f16"
  night-text: "#eef0f6"
  night-text-secondary: "#9ba3bf"
  night-text-muted: "#636d88"
  day-surface: "#f5f6fa"
  day-card: "#ffffff"
  day-text: "#1a1d2b"
  day-text-secondary: "#4b5268"
typography:
  display:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "26px"
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: "-0.6px"
  title:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "15px"
    fontWeight: 700
    lineHeight: 1.4
    letterSpacing: "-0.2px"
  body:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "13px"
    fontWeight: 500
    lineHeight: 1.6
  label:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "10px"
    fontWeight: 700
    lineHeight: 1.4
    letterSpacing: "1.2px"
  mono:
    fontFamily: "'JetBrains Mono', 'Fira Code', 'SF Mono', monospace"
    fontSize: "12px"
    fontWeight: 500
    lineHeight: 1.7
rounded:
  sm: "6px"
  md: "8px"
  lg: "10px"
  xl: "14px"
  xxl: "18px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  xxl: "44px"
components:
  button-primary:
    backgroundColor: "{colors.ember-orange}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "9px 18px"
  button-primary-hover:
    backgroundColor: "{colors.ember-hover}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "9px 18px"
  button-secondary:
    backgroundColor: "{colors.night-elevated}"
    textColor: "{colors.night-text}"
    rounded: "{rounded.md}"
    padding: "9px 18px"
  card:
    backgroundColor: "{colors.night-card}"
    rounded: "{rounded.xl}"
    padding: "24px"
  input:
    backgroundColor: "{colors.night-inset}"
    textColor: "{colors.night-text}"
    rounded: "{rounded.md}"
    padding: "10px 14px"
  badge:
    rounded: "{rounded.sm}"
    padding: "3px 10px"
  nav-item:
    textColor: "{colors.night-text-secondary}"
    rounded: "{rounded.md}"
    padding: "9px 22px"
  nav-item-active:
    backgroundColor: "rgba(255, 107, 53, 0.10)"
    textColor: "{colors.ember-orange}"
    rounded: "{rounded.md}"
    padding: "9px 22px"
---

# Design System: Lakebase Lab Console

## 1. Overview

**Creative North Star: "The Workshop Bench"**

This is a tool built for doing, not watching. Every surface is a workbench where engineers explore Lakebase through direct interaction. The design communicates competence through clarity and energy through purposeful color. It feels like a capable instrument built by people who use their own tools daily.

The aesthetic sits between a modern observability console and a well-organized IDE. Spacious enough to breathe, dense enough to be useful. Dark by default because the primary audience works on laptops in conference rooms and hotel ballrooms during workshops. Light mode exists for bright environments and preference.

The system explicitly rejects enterprise-heavy dashboards with dense gray panels and walls of data. It also rejects the generic SaaS clone aesthetic where every product converges on the same muted palette, identical card grids, and safe typographic choices. This console has its own identity: an ember-orange accent that runs hot against cool blue-gray surfaces.

**Key Characteristics:**
- Data and system state front and center, UI chrome recedes
- Orange accent used with restraint to mark primary actions and active states
- Monospace type for all data values, creating a clear visual channel for "this is real data"
- Ambient depth through subtle shadows and border shifts, never heavy drop shadows
- Dual-theme support (dark default, light available) with full token parity

## 2. Colors

A cool-neutral foundation with a single warm accent that earns its presence through restraint.

### Primary
- **Ember Orange** (#ff6b35): The signature. Active nav states, primary buttons, accent glows, metric highlights. Never decorative. Appears on less than 15% of any screen.

### Secondary
- **Signal Blue** (#3b82f6): Informational badges, notebook links, read-operation indicators. The calm counterpoint to orange.
- **Deep Violet** (#8b5cf6): System-level messages, agent memory system role, rare emphasis.
- **Live Teal** (#14b8a6): Compute gauges, scale-to-zero indicators, the "alive" color for active infrastructure.

### Semantic
- **Clear Green** (#22c55e): Connected, healthy, success. Pulse animation on connection dot.
- **Caution Amber** (#f59e0b): Scaling states, warnings, attention-needed.
- **Alert Red** (#ef4444): Disconnected, errors, destructive actions.

### Neutral
- **Night Surface** (#0f1117): Primary dark background. Tinted blue-black, never pure.
- **Night Card** (#1a1d2b): Card and container background. One step above the surface.
- **Night Inset** (#12141c): Recessed areas (code blocks, chart backgrounds, input fields). Darker than the card.
- **Night Sidebar** (#0d0f16): Sidebar background, the deepest surface.
- **Night Text** (#eef0f6): Primary text in dark mode. Warm-tinted white.
- **Night Text Secondary** (#9ba3bf): Descriptions, secondary information.
- **Night Text Muted** (#636d88): Labels, placeholders, inactive elements.

Light mode mirrors the hierarchy with Day Surface (#f5f6fa), Day Card (#ffffff), Day Text (#1a1d2b), and a slightly deeper Ember Orange (#e85d2a) for better contrast on white.

**The Tinted Neutral Rule.** No pure black (#000) or pure white (#fff) anywhere. Every neutral carries a subtle blue tint toward the brand hue. This prevents the clinical feel of pure grays.

**The Ember Restraint Rule.** Ember Orange is used on primary buttons, active nav states, and accent glows only. If orange appears on more than 15% of a screen, it has lost its signal value.

## 3. Typography

**Display Font:** Inter (with system fallbacks)
**Mono Font:** JetBrains Mono (with Fira Code, SF Mono fallbacks)

**Character:** Inter's geometric precision and wide weight range (400-800) create hierarchy through weight contrast alone. JetBrains Mono provides a distinct visual channel that immediately signals "this is data" or "this is code." The pairing is technical but never cold.

### Hierarchy
- **Display** (800, 26px, line-height 1.2, tracking -0.6px): Page titles only. One per screen. The heaviest weight in the system.
- **Title** (700, 15px, line-height 1.4, tracking -0.2px): Card headers, section titles. Tight tracking adds density.
- **Body** (500, 13px, line-height 1.6): Navigation labels, descriptions, form labels, general content. Medium weight prevents the washed-out feel of 400.
- **Label** (700, 10px, line-height 1.4, tracking 1.2px, uppercase): Section labels, table headers, metric labels, badge text. Always uppercase with wide tracking.
- **Mono** (500-800, 12px, line-height 1.7): All data values, code blocks, connection strings, metric numbers. Weight varies: 500 for code, 600-800 for metric values.

**The Data Channel Rule.** If a value came from the database or API, it renders in JetBrains Mono. If it's UI chrome, it renders in Inter. This visual separation is absolute and never crossed.

## 4. Elevation

Ambient and atmospheric. Shadows exist to create a soft sense of layering, not to lift elements off the page. The system relies primarily on background color steps for hierarchy (surface → card → elevated → inset), with shadows providing gentle ambience.

### Shadow Vocabulary
- **Ambient Low** (`0 1px 3px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.2)`): Default card resting state. Barely perceptible.
- **Ambient Mid** (`0 4px 16px rgba(0,0,0,0.35)`): Hover lift on action cards, dropdown panels.
- **Ambient High** (`0 8px 32px rgba(0,0,0,0.4)`): Toasts, modals, floating elements.
- **Accent Glow** (`0 0 24px rgba(255, 107, 53, 0.15)`): Primary button resting glow. Ember orange bleed into the surrounding surface.

Light mode dramatically reduces shadow opacity (0.06/0.08/0.1) to prevent muddy appearance on white backgrounds.

**The Flat-at-Rest Rule.** Surfaces are flat at rest. Shadows intensify as a response to interaction (hover lifts cards, focus glows inputs). If it's not interactive, it doesn't cast a shadow.

## 5. Components

### Buttons
Tactile and confident. Every press should feel like flipping a switch.

- **Shape:** Gently curved edges (8px radius)
- **Primary:** Ember Orange gradient (135deg, #ff6b35 → #ff8c55), white text, 600 weight, 13px. Resting glow from accent-glow shadow. Padding 9px 18px.
- **Hover:** Lighter gradient (#ff8055 → #ffa070), stronger glow, 1px upward lift via translateY(-1px).
- **Active:** Snaps back to translateY(0) on press.
- **Disabled:** 40% opacity, no glow, no cursor.
- **Secondary:** Night Elevated background (#2a2e3f), border 1px solid border-light, primary text color. Hover darkens background and sharpens border.
- **Danger:** Red-tinted transparent background (rgba(239,68,68,0.15)), red text and border.
- **Small/XS variants:** Reduced padding (6px 14px / 4px 10px), smaller radius (7px / 6px).

### Cards / Containers
- **Corner Style:** Generously curved (14px radius)
- **Background:** Night Card (#1a1d2b) on dark, white on light
- **Shadow:** Ambient Low at rest
- **Border:** 1px solid rgba(255,255,255,0.06). Lightens to border-light on hover.
- **Internal Padding:** 24px

### Inputs / Fields
- **Style:** Inset background (#12141c), 1px solid border-light, 8px radius
- **Focus:** Border shifts to Ember Orange, 3px glow ring in accent-dim
- **Range inputs:** Custom-styled thumb with Ember Orange and accent glow

### Navigation
- **Sidebar:** Fixed 260px, Night Sidebar background, full viewport height
- **Nav items:** 13px, 500 weight, Night Text Secondary. 8px radius, 9px 22px padding.
- **Hover:** Background shifts to bg-hover, text brightens to primary
- **Active:** Ember Orange text, accent-dim background, 3px orange left indicator bar
- **Section labels:** 10px, 700 weight, uppercase, 1.2px tracking, muted color
- **Mobile (< 768px):** Sidebar collapses to 60px icon-only strip

### Badges
- **Shape:** Compact pills (6px radius, 3px 10px padding, 11px text)
- **Variants:** Color-coded by role — success/warning/danger/info/accent/purple/teal. Each uses its dim background + solid text color.

### Metric Cards
- **Layout:** Centered content, icon above value above label
- **Value:** 26px, 800 weight, JetBrains Mono, Ember Orange color, -1px tracking
- **Label:** 10px uppercase, muted, 0.8px tracking
- **Hover:** Border lightens, background shifts to card-hover, subtle gradient line appears at top

### Data Tables
- **Headers:** 10px uppercase, muted, 600 weight, 0.8px tracking, bottom border
- **Cells:** 13px, 11px padding, subtle bottom border
- **Hover:** Faint row highlight (rgba(255,255,255,0.02))
- **Data Channel enforcement:** Use `.td-mono` / `.td-mono-sm` / `.td-mono-xs` / `.td-mono-bold` on all cells containing data values (IDs, counts, timestamps, sizes). Never inline `fontFamily: 'var(--font-mono)'`.

### Alert Banners
- **Structure:** `.alert-banner` + `.alert-banner-danger` wrapper. Flex row with icon, message `<p>`, and optional dismiss button.
- **Danger variant:** `var(--danger-dim)` background, `rgba(239,68,68,0.3)` border, danger text.
- **Pattern:** Replaces the legacy `<div className="card" style={{ borderColor: ... }}>` error banner. All pages use this component.

### Utility Classes
Reusable layout and typography utilities to eliminate inline styles:

- **`.grid-2col`** — Two-column grid (1fr 1fr), 16px gap, 16px bottom margin. Collapses to single column at 768px.
- **`.metrics-row-2` / `.metrics-row-4` / `.metrics-row-5`** — Column count variants for `.metrics-row`. All collapse to 2 columns at 768px.
- **`.empty-state-compact`** — 20px padding variant of `.empty-state` for inline use within cards.
- **`.section-subheader`** — 11px uppercase label (600 weight, 0.8px tracking, muted color, 8px bottom margin).
- **`.list-item-card`** — Reusable card container: 18px padding, bg-secondary background, 1px border, standard radius.
- **`.btn-row`** — Flex row with 8px gap, vertically centered. For button groups and badge rows.
- **`.running-config`** — Flex row summary bar (14px padding, bg-secondary, 24px gap, 13px text, wrapping).
- **`.form-inset`** — Inset form container: 18px padding, bg-secondary, 1px border, standard radius.
- **`.form-select`** — Standalone select element styling (matches form-group select but works outside form context).
- **`.slider-labels`** — Flex split row for range slider min/max labels (10px mono, muted).
- **`.cu-gauge-labels`** — Flex split row for gauge/progress bar labels.
- **`.spike-preset-desc`** — Tiny description text for preset buttons (10px, muted).

### Chat Messages (Agent Memory)
- **User:** Ember Orange gradient bubble, white text, right-aligned, rounded bottom-right corner flattened
- **Assistant:** Card background with border, left-aligned, rounded bottom-left corner flattened
- **System:** Purple-dim background, centered, smaller text

## 6. Accessibility

### Focus Visible
All interactive elements show a 2px Ember Orange outline on `:focus-visible` (keyboard navigation only, not mouse clicks):
- `.btn`, `.quick-action-card`, `.tab-btn`, `.spike-preset-btn`, `.theme-toggle` — 2px offset
- `.sidebar-nav li a` — -2px offset (inward, to stay within the sidebar boundary)

### Reduced Motion
A `@media (prefers-reduced-motion: reduce)` query suppresses all animations and transitions globally. This covers the refresh spinner (`spin`), toast entrance, hover lifts, and all `transition` properties. Users who prefer reduced motion see instant state changes.

### Aria Labels
All interactive elements (buttons, toggles, refresh controls) include `aria-label` attributes describing their purpose. Data badges include `title` attributes for tooltip context.

## 7. Do's and Don'ts

### Do:
- **Do** use Ember Orange exclusively for primary actions, active states, and metric highlights. Its rarity is its power.
- **Do** render all data values (row counts, CU numbers, connection strings, timestamps) in JetBrains Mono. The data channel is sacred.
- **Do** use background color steps (surface → card → elevated → inset) as the primary depth mechanism. Shadows are seasoning, not structure.
- **Do** keep body text at 13px / 500 weight. This density feels professional without straining readability.
- **Do** tint every neutral toward blue. The Night Surface family (#0f1117 → #2a2e3f) carries a consistent cool undertone that unifies the palette.
- **Do** provide full dark/light theme parity. Every token has a light-mode counterpart.
- **Do** use the 0.2s cubic-bezier(0.4, 0, 0.2, 1) easing for all state transitions. Consistent motion rhythm.
- **Do** use the utility CSS classes (`.alert-banner`, `.grid-2col`, `.list-item-card`, `.btn-row`, `.td-mono`, `.form-inset`, `.form-select`, etc.) instead of inline styles for recurring layout patterns.
- **Do** respect `prefers-reduced-motion`. All animations and transitions are suppressed when the user requests it.

### Don't:
- **Don't** build enterprise-heavy layouts with dense gray panels, walls of tiny data, and cluttered toolbars. This should breathe. (PRODUCT.md: "dense, cluttered, gray corporate UIs")
- **Don't** fall into the generic SaaS dashboard clone: safe muted palettes, identical card grids, and typographic choices that could belong to any product. This console has its own identity. (PRODUCT.md: "the Stripe/Linear clone aesthetic")
- **Don't** use pure black (#000000) or pure white (#ffffff). Every neutral is tinted.
- **Don't** use gradient text (`background-clip: text` with gradients). Emphasis comes from weight and size.
- **Don't** use glassmorphism or heavy backdrop-filter decoratively. The one allowed blur is the toast notification.
- **Don't** nest cards inside cards. If content needs sub-grouping, use inset backgrounds or subtle borders.
- **Don't** use bounce or elastic easing curves. Ease-out with the standard cubic-bezier only.
- **Don't** use border-left or border-right greater than 1px as a colored accent stripe, except the 3px active nav indicator which is an intentional signature element.
- **Don't** use em dashes in UI copy. Use commas, colons, or periods.
- **Don't** create metric cards with the "big number, small label, gradient accent" hero-metric template. The current metric cards are intentionally restrained: number + label, no decorative gradients on the values themselves.
