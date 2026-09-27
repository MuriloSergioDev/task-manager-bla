# Design system

The frontend's design system is deliberately small: **design tokens**, a
**component layer** built on them, and **Storybook** to document both. It
uses no component library. The components are home-made on Tailwind CSS v4.

Storybook is the visual reference (`cd frontend && npm run storybook`, then
open http://localhost:6006). This document covers the rules behind it.

## Layers

| Layer | Where | What it owns |
|---|---|---|
| Tokens | `src/styles/tokens.css` | Every visual value: colour, type scale, radius, widths, elevation, motion |
| Components | `src/components/ui/` | Generic, domain-free UI built only from tokens, imported via `components/ui/index.ts` |
| Patterns | Next to their feature (`DateStub`, `Wordmark`) | Domain-aware pieces that still follow the system. Their stories sit under "Patterns" |
| Features | `src/features/*` | Composition and behaviour; no new visual values |

Tailwind v4 reads the `@theme` block in `tokens.css` and generates utilities
from it: `--color-ink` becomes `bg-ink`, `text-ink` and `border-ink`;
`--text-label` becomes `text-label`; `--radius-sheet` becomes
`rounded-sheet`.

## Rules

1. **No one-off values.** Components use token utilities, never `text-[13px]`
   or `#5e6b66`. The only allowed arbitrary values are layout or selector
   syntax, and each has a comment:
   - `max-h-[92dvh]` on the dialog panel
   - the task row's grid template in `taskListLayout.ts`
   - `has-[:focus-visible]`

   Check with `grep -rnE "[a-z]-\[" frontend/src --include=*.tsx`.
2. **Colour means something.** Neutrals do the layout work, and each accent
   has one job:
   - `progress` (indigo): in progress, keyboard focus
   - `done` (green): done, success
   - `late` (brick): overdue, errors, destructive actions

   The primary button is `ink`, not an accent.
3. **Text meets WCAG AA.** All text is at least 4.5:1 on every surface.
   `muted` is the lightest colour allowed for text. `faint` is for non-text
   only (icons, spinners, disabled states) and is at least 3:1.
4. **Radius follows hierarchy:** `segment` (5px) sits inside `control` (6px),
   which sits inside `sheet` (10px).
5. **Flat surfaces.** Borders separate things; only dialogs get a shadow
   (`shadow-dialog`).
6. **Motion answers the user.** The only animations are dialogs appearing,
   and `prefers-reduced-motion` turns them off.

## Naming

Tokens are named by **role**, not by value or hue: `muted`, not `grey-500`;
`text-label`, not `text-13`. A new value needs a role that no existing token
covers. If you can't name the role, the existing scale probably already
covers it.

Type roles that always go with a line height or tracking include it (Tailwind's
`--text-<name>--line-height` and `--text-<name>--letter-spacing`), so a call
site can't pair them wrongly. Tailwind's built-in `text-sm`, `text-lg`,
`text-xl` and `text-2xl` are used as they are.

## Adding a token

1. Add it to `tokens.css` in the right group, with a trailing comment saying
   what it's for. The comment appears on Storybook's Foundations page, which
   is generated from this file.
2. For a colour used as text, check contrast against `paper`, `sheet` and
   `wash`. The a11y panel flags failures in any story that uses it.
3. Use it through its utility (`text-<name>`, `bg-<name>` and so on).

## Adding a component

1. Put it in `src/components/ui/` if it's generic, or next to its feature if
   it knows about tasks. Style it with token utilities only.
2. Keep variants to a small union prop (`variant`, `size`, `tone`) with
   JSDoc; the JSDoc becomes the description in Storybook's props table.
   Accept `className` only for spacing around the component, not to restyle it.
3. Export it from `components/ui/index.ts`.
4. Add `Component.stories.tsx` next to it, covering every variant and state,
   including error, disabled and loading where they apply. Components that
   need auth or server data stay out of Storybook; their design pieces are
   what get stories.
5. Check the story's accessibility panel shows no violations.

## Verifying a change

- `npm run lint` (fails on warnings), `npm run build` (strict TypeScript),
  then `npm run build-storybook && npm run test:storybook`, which runs axe and
  checks for console errors on every story.
- For refactors that shouldn't change the look, run
  `npm run test:visual:baseline` before the change and `npm run test:visual`
  after it. Any differing pixel fails, so every difference must be explained.
  The token migration was checked this way, and its screens at two widths
  came out pixel-identical. See [ai-development.md §9e](ai-development.md).
