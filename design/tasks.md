## Project Brief
- Project type: Multi-page web frontend (landing, admin, submissions, student home, student profile)
- Industry and audience: Student developer learning platform (college/university users and admins)
- Current request: Improve dark mode so it is not monochrome; avoid AI-blue accents
- Constraints: Keep SVG-only icons, preserve existing layout and interactions

## Research Findings
- 2025-2026 dark UI trend direction supports warm non-blue accents with layered dark surfaces.
- Recommended accent families: Ember/Amber (#FF8A5B, #F6C85F), Emerald support (#34D399), optional Rose for highlights.
- Practical dark foundations: background around #101117, surfaces around #1A1D26/#232835, primary text around #F5F7FA.
- Accessibility guardrails: 4.5:1 for normal text, 3:1 for large text and non-text UI indicators.
- Caution: keep saturated accents limited to key actions and highlights to avoid visual fatigue.
- Additional 2026 dev-theme insights: developers prefer deeper near-black foundations, subtle layer stepping, restrained accents, and terminal-like semantic cues.
- Best practice for dev-heavy UI: one CTA accent, one success accent, one rare premium accent; avoid broad neon fills on large surfaces.

## Chosen Palette
- Dark background: #0D1110
- Dark surface: #18201E
- Elevated surface: #24302D
- Text primary: #F3F6F2
- Text secondary: #B7C2BB
- Primary accent (CTA/buttons): #2EC4B6
- Support accent (success/highlights): #9FE870
- Premium accent (rare elements): #C9883D

## Generated Palette Options
- Option A: Rose Peach
	- Dark background: #0F111A
	- Dark surface: #191D2A
	- Elevated surface: #242A39
	- Text primary: #F8F4EF
	- Text secondary: #CDBFB1
	- Primary accent: #FF6B8A
	- Secondary accent: #FFB38A
	- Support accent: #F59E0B
- Option B: Emerald Copper
	- Dark background: #0D1110
	- Dark surface: #18201E
	- Elevated surface: #24302D
	- Text primary: #F3F6F2
	- Text secondary: #B7C2BB
	- Primary accent: #2EC4B6
	- Secondary accent: #C9883D
	- Support accent: #9FE870
	- Accent usage rule: #2EC4B6 for buttons and CTA, #9FE870 for success/highlights, #C9883D for rare premium details only
- Option C: Graphite Terminal Mint (darker)
	- Dark background: #090B10
	- Dark surface: #121722
	- Elevated surface: #1A2231
	- Text primary: #EAF0FF
	- Text secondary: #9CA8C0
	- Primary accent: #4DD4A8
	- Success accent: #33C37A
	- Premium accent: #D3A85F
- Option D: Obsidian Ember (darker)
	- Dark background: #0B0908
	- Dark surface: #171211
	- Elevated surface: #211A18
	- Text primary: #F4ECE8
	- Text secondary: #B5AAA3
	- Primary accent: #FF7A45
	- Success accent: #6FCF97
	- Premium accent: #E6B86A

## Chosen Typography
- Existing typography retained for consistency across current pages.
- Font stack remains Inter/system sans across the frontend.

## Design Decisions Log
- 2026-04-02: Added persistent light/dark toggle to all frontend pages using localStorage key devela-theme.
- 2026-04-02: Replaced emoji/symbol icon usages with inline SVG icons (lock, close, success, sync, arrows).
- 2026-04-02: Reworked dark theme from grayscale/blue-tinted style to a warm colorful non-blue palette.
- 2026-04-02: Updated dark interactive states (active nav, buttons, hover states, toggles) to use warm accents.
- 2026-04-02: Generated two additional non-blue dark palette options (Rose Peach, Emerald Copper) for next iteration.
- 2026-04-02: User selected Version B accent usage constraints: avoid overusing green; #2EC4B6 for CTA/buttons, #9FE870 for success/highlights, #C9883D as rare premium accent.
- 2026-04-03: Applied Version B (Emerald Copper) across all Frontend pages with constrained accent mapping.
- 2026-04-03: Brainstormed darker developer-first palette variants emphasizing deeper backgrounds and restrained accents.
- 2026-04-03: Recommended adding a fourth admin action card for Use Cases CSV upload in the Use Case column (before assignment in mobile flow), with explicit helper text for required columns: Topic, Objective, Key Concepts, Output.
- 2026-04-05: Drafted implementation-ready downtime/maintenance page design spec aligned to current DevElan visual language (light grid, rounded glass card, deep navy/cyan + dark mode emerald-copper tokens, restrained ambient motion, single CTA).

## Export History
- 2026-04-02: Exported direct HTML/CSS updates across Frontend pages (no separate token file yet).
- 2026-04-03: Applied Version B tokens and dark-mode accent rules in index/admin/form/user_home/user_profile.

## Downtime/Maintenance Page Spec
- Layout concept: center-focused single card over ambient grid with one supporting decorative shape layer; no secondary panels.
- Content hierarchy: status label -> H1 outage/maintenance message -> one-sentence clarification -> optional ETA/info chip -> one primary CTA.
- Token mapping: light mode uses #1E3A8A and #00D4FF accents over #E2E8F0/#FFFFFF surfaces; dark mode uses #2EC4B6 CTA accent, #9FE870 status/success, #C9883D optional premium divider or chip edge on #0D1110/#18201E surfaces.
- Motion profile: three low-amplitude ambient animations only (status pulse, slow grid drift, shape float) with reduced-motion fallback to near-static.
- Accessibility guardrails: maintain WCAG AA contrast (4.5:1 text, 3:1 UI components), keep focus-visible states high-contrast, avoid flashing/rapid movement.
