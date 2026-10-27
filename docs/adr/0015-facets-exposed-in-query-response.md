# 0015. Expose the facet breakdown in the public QueryResponse

- Status: Accepted
- Date: 2026-10-27
- Context: The `Facet` schema exists but is unused in generation, so the per-question facet decomposition (description, status, citation ids, associated gap) is invisible to clients and evaluators. The requirement that completeness/partiality/insufficiency be "reflected in the structured contract" and the need for evaluation inspectability (per-case observation of facets, gaps, and suggestions) demand that this breakdown be part of the public response.
- Decision: Add a `facets` field to the public `QueryResponse` returned by `/api/query`, exposing the per-facet breakdown (description, status, citation ids, associated gap). This contract addition (D3) makes the three primary paths (complete / partial / insufficient) and the identified gaps programmatically inspectable without a separate endpoint.
- Alternatives considered:
  - Keeping facets internal only — rejected because the contract would not reflect completeness or partiality, failing the "reflected in the structured contract" requirement and losing evaluation inspectability.
  - Logging facets only — rejected because logs are not part of the API contract and the eval runner needs programmatic access to assert facet statuses.
  - Exposing full model reasoning/chain-of-thought — rejected because it is unnecessary and risks leaking internal prompt details; only the facet breakdown is justified.
  - A separate endpoint for facets — rejected because it fragments the query result and complicates clients; facets belong with the answer they describe.
- Consequences: A richer, justified public contract that enables per-facet assertions in tests and evaluation. Trade-off: larger responses and a requirement to keep the public `facets` shape in sync with the generation schema and IR-1..IR-6.