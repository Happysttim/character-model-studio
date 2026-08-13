# 09 — UI Design System

## Direction

**Warm glassmorphism with high visibility.**

The product should feel like a crafted desktop creative tool, not an AI chatbot, admin dashboard, or template SaaS page.

## Surface hierarchy

Use four visible depth levels:

1. **Window backdrop** — warm neutral Mica/Acrylic or deterministic warm fallback.
2. **Primary work surface** — large translucent pane with restrained border.
3. **Secondary glass pane** — contextual controls/metadata.
4. **Floating transient surface** — menus, tooltips, small selectors.

Do not wrap every text group in a card.

## Windows backdrop

On supported Windows 11 builds, the app may use DWM system backdrop attributes through Python `ctypes` in `platform/windows/dwm.py`.

Fallback must be a warm opaque/translucent painted background when unsupported.

The UI must remain legible without the OS backdrop effect.

## Warm palette tokens

The implementation may tune exact values after visual testing, but use this family as the baseline:

```text
CanvasWarm      #F5E6D7   light warm cream canvas
CanvasWarmAlt   #E7C8AF   warm apricot navigation surface
GlassBase       rgba(255, 250, 244, 0.62)
GlassRaised     rgba(255, 252, 248, 0.70)
GlassStrong     rgba(255, 248, 240, 0.80)
BorderSoft      rgba(143, 79, 50, 0.22)
BorderFocus     rgba(255, 181, 122, 0.65)
TextPrimary     #3E241B
TextSecondary   #633C2E
TextMuted       #876657
Amber           #F2A65A
Apricot         #FFBE88
Coral           #E97B67
Terracotta      #C96A4B
Cream           #FFE4CB
Success         #9CCB9A
Warning         #E6B86C
Danger          #E57464
Info            #A9BED1
```

The palette is intentionally not monochrome. Status colors remain muted enough to coexist with warm accents.

The desktop shell uses an app-owned frameless title bar with visible minimize, maximize/restore, and close controls. The main workspace surface has no corner radius; secondary and floating controls retain the smaller contextual radii defined below.

## Gradients

Gradients are allowed as subtle environmental lighting, not as the identity of every button/card.

Good:

- one soft amber/terracotta radial glow behind the main workspace;
- a slight warm vertical tonal shift in the backdrop.

Bad:

- purple-to-blue gradient on every panel;
- neon mesh gradients;
- gradients used instead of hierarchy.

## Glass treatment

Primary glass panes should generally use:

- low-to-medium opacity;
- 1 px soft border;
- limited highlight edge;
- moderate radius;
- backdrop/system blur where available;
- minimal shadow, primarily for separation.

Avoid stacking multiple heavy blurs that destroy GPU/UI performance.

## Corner radii

Use a small family, not one universal radius:

- 6 px: compact inputs/small controls;
- 10 px: buttons/menus;
- 14 px: secondary glass panes;
- 18 px: major workspace panels;

Pills are reserved for true tags/status indicators/toggles where shape communicates meaning.

## Typography

Use a Windows-appropriate sans-serif system stack through Qt fonts. Prioritize readable Korean and Latin text.

- body text: regular/medium;
- section titles: semibold;
- avoid oversized marketing headings inside the application;
- avoid all-caps except short states such as `REC`.

## Buttons

Primary action:

- warm amber/apricot emphasis;
- high text contrast;
- restrained glow only on hover/focus if any.

Secondary action:

- glass surface + border.

Danger action:

- muted coral/red treatment; do not make the whole app red.

## Anti-AI-template acceptance rule

A screen fails visual review if three or more of the following are present:

- hero-sized heading with empty space;
- 3–6 equal KPI cards across the top;
- generic sparkle/AI icon as a central motif;
- blue/purple gradient identity;
- every control is a pill;
- icon-only navigation with no persistent labels;
- all panels use identical 16–24 px rounding;
- arbitrary glow around every surface;
- excessive empty dashboard space;
- chat-composer visual language where no chat exists;
- placeholder charts or metrics not required by the product.

## Focus and accessibility

- keyboard focus must be visible;
- selected state must differ by more than slight transparency;
- important controls may not rely on color alone;
- text over glass must preserve contrast under bright wallpapers by using an appropriate base/tint/fallback.
