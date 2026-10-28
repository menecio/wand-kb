# 0022. Hard delete of a document across all stores

- Status: Proposed
- Date: 2026-10-28
- Context: Users must be able to delete an uploaded document from the
  Documents view. A document exists in three stores: the uploaded file (and its
  storage folder) under `data/uploads/<document_id>/`, the registry entry in
  `data/registry.json`, and its chunks/embeddings in the Qdrant collection
  (`knowledge_base`, payload field `document_id`). Deleting only some of them
  would leave either a dead registry row, an orphaned file, or — worse —
  chunks that keep contributing to query answers and citations for a document
  the user believes is gone. The app is single-user with no authentication
  (ADR-0004), and the user explicitly requested that "the file from the
  filesystem and its data used to solve the queries" be deleted.
- Decision: Deleting a document performs a HARD delete across all three stores
  in a single request: remove the storage folder, remove the registry entry,
  and delete all Qdrant points whose payload `document_id` matches. If any
  store removal fails (e.g. Qdrant unreachable), the delete request fails and
  the document remains fully intact in all stores — no partial deletion.
  There is no soft-delete status, no tombstone, and no undo.
- Alternatives considered:
  - Soft delete via a `DELETED` registry status flag (keep file and vectors,
    filter them out of queries) — rejected because the user explicitly wants
    the file and data gone from the filesystem, and it adds a dead status to
    every consumer of the registry/Qdrant data.
  - Tombstone/audit-trail retention (record the deletion, defer physical
    removal to a background sweep) — rejected because this is a single-user
    prototype with no audit consumer; it adds migration and storage complexity
    with no benefit and keeps orphaned vectors temporarily.
  - Best-effort partial deletion (delete whatever succeeds, report the rest) —
    rejected because it silently leaves orphaned vectors that would still
    surface in answers for a deleted document, which violates the core
    requirement.
- Consequences: Deletion is irreversible; nothing can be recovered after a
  successful delete. The backend must expose a delete-points-by-filter method
  on `QdrantClient`. Tests must cover all three stores and the
  fail-without-partial-state guarantee. Future features (e.g. re-upload of the
  same file) must not rely on deleted documents lingering anywhere.
