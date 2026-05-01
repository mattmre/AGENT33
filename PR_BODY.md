# Add design system + UI kit (control plane)

## What

Adds a self-contained AGENT-33 design system under `design-system/` plus one
upstream rename in `frontend/src/components/`.

The design system is the source of truth for new screens, prototypes, decks,
and marketing material that should look and feel like AGENT-33. It was
reverse-engineered from this repo — `frontend/src/styles.css` (~7,800 lines)
and the React components under `frontend/src/components/`.

## Why

Today there is no Figma file, no formal style guide, no logo SVG, and no icon
system. Brand decisions live entirely inside the cockpit's CSS. That makes it
hard to:

1. Build any new surface that isn't the cockpit.
2. Onboard a designer or contractor without making them read 7,800 lines of CSS.
3. Keep voice / type / spacing consistent when AI tools generate UI.

This PR is the first crack at a portable artifact that fixes all three.

## What's inside

```
design-system/
├── README.md                  Brand voice, content rules, visual foundations,
│                              iconography, manifest. Read this first.
├── SKILL.md                   Manifest so Claude Code can consume the folder.
├── colors_and_type.css        All design tokens as CSS vars. Drop into any
│                              page to get the AGENT-33 look.
│
├── assets/                    Brand mark + wordmark.
│   ├── logo-orb.html          Canonical CSS-rendered logo orb (with pulse).
│   └── wordmark.svg           Space Grotesk wordmark mock.
│
├── preview/                   18 design-system foundation cards.
│                              Type, colors (5 palettes), radii, shadows,
│                              spacing, buttons, inputs, badges, cards,
│                              health states, logo orb.
│
└── ui_kits/control-plane/     Cockpit recreation + 13 reference surfaces.
    ├── index.html             Interactive React cockpit (open in a browser).
    ├── _kit.css               Shared "sharp / chamfered" aesthetic for every
    │                          standalone reference page.
    ├── Topbar.jsx
    ├── Sidebar.jsx
    ├── Dashboard.jsx
    ├── OperationCard.jsx
    ├── ActivityPanel.jsx
    ├── App.jsx
    ├── AuthPanel.html
    ├── HealthPanel.html
    ├── HealthPanelFull.html
    ├── PermissionModeControl.html
    ├── SafetyGateIndicator.html
    ├── GlobalSearch.html
    ├── DomainPanel.html
    ├── WorkflowGraph.html
    ├── WorkspaceTaskBoard.html
    ├── ShipyardLaneScaffold.html
    ├── ArtifactReviewDrawer.html
    ├── ExplanationView.html
    └── ObservationStream.html
```

## Aesthetic decision

The original cockpit leaned on neumorphic shadows (4-direction inset/outset).
After comparing it to the product's actual register — operator-grade, naval /
industrial vocabulary, `instrument-panel-like` per the source comments — the
design-system pages were rebuilt around a **sharp / chamfered system**:

- 10px chamfered corners on panels via `clip-path`.
- 4px chamfer on buttons.
- 1px hairline gradient strokes via `::before` + mask.
- 2px coloured left rule for status tinting (lanes, tasks, gates, events).
- No `border-radius` anywhere except chamfer cuts.

The legacy neumorphic tokens are preserved in `colors_and_type.css` for
source-faithful recreation, but `README.md` directs new work to the sharp
system. See any page in `design-system/ui_kits/control-plane/` for examples.

## Vocabulary change

The source `ShipyardLaneScaffold` referred to `BridgeSpace-style lanes`. In
keeping with AGENT-33's naval / industrial register, this PR renames the
workspace concept to **Drydock** across the design system and the one upstream
component (1-line copy edit, no behavioural change):

- `frontend/src/components/ShipyardLaneScaffold.tsx`
  - `BridgeSpace-style lanes` → `Drydock-style lanes`

## How to view

```bash
# From repo root after merging:
open design-system/ui_kits/control-plane/index.html       # cockpit
open design-system/ui_kits/control-plane/AuthPanel.html   # any standalone page
open design-system/preview/buttons.html                   # any foundation card
```

No build step. No npm install. Plain HTML + CSS + a couple of React/Babel
script tags loaded from unpkg.

## Caveats

- **No formal logo.** The orb is the only mark; a real logotype hasn't been
  commissioned. Flagged in `design-system/README.md`.
- **No icon system.** Lucide is suggested as a substitute (1.5px stroke,
  currentColor) but unconfirmed.
- **Fonts not bundled.** Space Grotesk + IBM Plex Mono load from Google Fonts.
  Local hosting is recommended for production.
- **No marketing surface, deck template, or social card system.** Everything
  here is built around the in-product cockpit.

## Next steps (suggested follow-ups)

- Commission a real logotype.
- Decide on Lucide vs a proprietary icon set.
- Bundle `.woff2` files for offline-safe type.
- Add a marketing / deck surface if AGENT-33 ever needs one.
