# 0017. Local shadcn-style Button and Textarea instead of full shadcn/ui adoption

- Status: Proposed
- Date: 2026-10-28
- Context: ADR 0010 proposed React + TypeScript + Vite + shadcn/ui (Radix + Tailwind), status still Proposed. The Phase 5 frontend was implemented with plain CSS and local components. The 2026-10-28 frontend audit requires replacing the raw native `<button>`/`<textarea>` with shadcn Button and Textarea (§10, §17), while the same brief's constraints demand keeping components local and simple with no new abstraction layers. Adopting real shadcn/ui now would introduce Tailwind, Radix, class-variance-authority, and tailwind-merge as a parallel styling system used by only two components in an otherwise plain-CSS, token-driven app.
- Decision: Implement `frontend/src/components/ui/Button.tsx` and `Textarea.tsx` as local components that mirror the shadcn/ui component contract (forwardRef, `variant` and `size` props with the shadcn variant names, `data-slot` attributes, same accessibility and disabled semantics), styled exclusively with the §15 design-token CSS in `index.css`. Use them for every action button and the question textarea. This partially supersedes ADR 0010; the rest of the component inventory stays local per the Phase 5 spec §16 ("shadcn/ui covers Button and Textarea; the rest may remain local and simple").
- Alternatives considered:
  - Full shadcn/ui adoption (Tailwind + Radix + CVA) — rejected: adds a second styling system and runtime dependencies for two components, violating the brief's "keep components local and simple" constraint and the repo's YAGNI rule.
  - Keep raw native elements — rejected: the audit explicitly requires replacing them (§10/§17 conformance).
  - Hand-rolled bespoke components without the shadcn API shape — rejected: loses the familiar component contract and variant vocabulary the brief references.
- Consequences: The UI gains the shadcn Button/Textarea usage pattern and API without the Tailwind toolchain; styling stays in one token-driven stylesheet. Trade-off: the components are owned locally (not pulled from the shadcn registry), so future shadcn registry updates must be ported by hand.
