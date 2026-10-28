# 0021. Orchestrator executes subagent roles in-session (harness limitation)

- Status: Proposed
- Date: 2026-10-28
- Context: The repository's pipeline (AGENTS.md §2, `.opencode/README.md`)
  mandates separate subagent sessions for issue-creator, test-writer,
  implementer, logic-verifier, visual-verifier and adr-writer, coordinated by
  an orchestrator with pointer-based handoffs. The task "delete an uploaded
  document from the frontend" was started in the LM Studio Bionic harness,
  where the orchestrator session cannot spawn or control other sessions: the
  `session_control.*` bionic tools are unavailable in this session and no MCP
  agent servers are configured. The escalation protocol was followed and the
  user was offered (a) enabling session control, (b) manually opened subagent
  sessions, or (c) executing each role in-session. The user chose (c)
  explicitly.
- Decision: For this task (and future tasks in this harness unless session
  control becomes available), the orchestrator session executes each pipeline
  phase itself, one role at a time, while preserving the invariants that make
  the pipeline auditable: strict phase order (tests before implementation),
  role-based file permissions applied procedurally (tests written only in the
  test-writer step, implementation only in the implementer step, verifiers
  read-only), separate Conventional Commits per role, and the append-only
  `.tasks/` evidence trail with per-role reports.
- Alternatives considered:
  - Block the pipeline until the harness gains session-control support —
    rejected because the user explicitly approved in-session execution and the
    work has real value now.
  - Weaken the evidence trail (skip per-role reports) — rejected because the
    audit trail is the pipeline's source of truth and remains cheap to keep.
- Consequences: Context separation between roles is lost (the same model sees
  both tests and implementation), which weakens the TDD-independence guarantee
  the multi-agent setup provides; mitigations are to keep the test-first
  commit ordering and run verifiers against the diff/evidence rather than
  memory. The role table in AGENTS.md remains the target state when the
  harness supports real delegation.
