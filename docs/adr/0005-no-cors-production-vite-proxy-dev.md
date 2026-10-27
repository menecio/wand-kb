# 0005. No CORS in production; Vite proxy in dev

- Status: Proposed
- Date: 2026-10-27
- Context: In production FastAPI serves the built frontend from the same origin, so cross-origin requests never occur. In development the Vite dev server can proxy `/api` to the backend, keeping the browser on one origin. Enabling CORS would add configuration and a broader attack surface for no benefit.
- Decision: Do not enable CORS. Use a Vite dev-server proxy to the backend in development; serve the production frontend build from FastAPI in production.
- Alternatives considered:
  - Enable CORS with permissive origins — rejected because it is unnecessary for same-origin deployment and risks misconfiguration/credential leakage.
  - Enable CORS restricted to localhost — rejected because the Vite proxy already removes the need and keeps the setup simpler and more secure.
- Consequences: Cleaner security posture and less config. Trade-off: frontend dev setup must configure the proxy; any future separate-origin deployment requires revisiting this decision via a new ADR.