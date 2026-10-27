# 0010. Frontend: React + TypeScript + Vite + shadcn/ui

- Status: Proposed
- Date: 2026-10-27
- Context: The UI is planned for a later phase but the stack must be frozen now so scaffolding and proxy/CORS decisions stay consistent. The frontend needs type safety, fast dev iteration, and accessible, composable components without building a design system from scratch.
- Decision: Use React with TypeScript, Vite as the build/dev tool, and shadcn/ui (Radix + Tailwind) for components.
- Alternatives considered:
  - Vue 3 / Svelte — rejected because the team's familiarity and ecosystem alignment favor React; component libraries and tooling are more abundant.
  - Create React App — rejected because it is deprecated/slower and lacks Vite's dev performance.
  - Plain CSS / custom components — rejected because shadcn/ui provides accessible, themeable primitives that accelerate UI work without a heavy runtime dependency.
- Consequences: Type-safe, fast frontend development with reusable accessible components. Trade-off: frontend is not yet implemented (Phase 1 only scaffolds `frontend/` placeholder); shadcn/ui requires Tailwind setup and component ownership/maintenance.