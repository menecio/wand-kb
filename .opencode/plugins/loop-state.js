// State machine for the multi-agent pipeline.
// Enforces phase ordering by deriving state from .tasks/ and blocking
// illegal tool calls before they execute.

import fs from "node:fs"
import path from "node:path"

function latestTaskDir(directory) {
  const tasksDir = path.join(directory, ".tasks")
  if (!fs.existsSync(tasksDir)) return null
  const dirs = fs
    .readdirSync(tasksDir, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name)
    .sort()
  if (dirs.length === 0) return null
  return path.join(tasksDir, dirs[dirs.length - 1])
}

function allVerdictsPass(taskDir) {
  if (!taskDir) return false
  const reportsDir = path.join(taskDir, "reports")
  if (!fs.existsSync(reportsDir)) return false
  const files = fs.readdirSync(reportsDir)
  const logicReports = files.filter((f) => /^verify-.*-logic\.md$/.test(f))
  if (logicReports.length === 0) return false
  for (const f of logicReports) {
    const content = fs.readFileSync(path.join(reportsDir, f), "utf8")
    if (!/VERDICT:\s*PASS/i.test(content)) return false
  }
  const visualReports = files.filter((f) => /^verify-.*-visual\.md$/.test(f))
  for (const f of visualReports) {
    const content = fs.readFileSync(path.join(reportsDir, f), "utf8")
    if (!/VERDICT:\s*PASS/i.test(content)) return false
  }
  return true
}

function readState(directory) {
  const taskDir = latestTaskDir(directory)
  if (!taskDir) {
    return { taskDir: null, briefExists: false, briefConfirmed: false, hasTests: false, hasImpl: false, allVerdictsPass: false }
  }
  const briefPath = path.join(taskDir, "brief.md")
  const logPath = path.join(taskDir, "log.md")
  const reportsDir = path.join(taskDir, "reports")

  let briefConfirmed = false
  if (fs.existsSync(logPath)) {
    const log = fs.readFileSync(logPath, "utf8")
    briefConfirmed = /brief v1 confirmed by user/i.test(log)
  }

  let hasTests = false
  let hasImpl = false
  if (fs.existsSync(reportsDir)) {
    const files = fs.readdirSync(reportsDir)
    hasTests = files.some((f) => /^tests-.*\.md$/.test(f))
    hasImpl = files.some((f) => /^impl-.*\.md$/.test(f))
  }

  return {
    taskDir,
    briefExists: fs.existsSync(briefPath),
    briefConfirmed,
    hasTests,
    hasImpl,
    allVerdictsPass: allVerdictsPass(taskDir),
  }
}

function relPath(directory, filePath) {
  if (!filePath) return null
  if (path.isAbsolute(filePath)) {
    return path.relative(directory, filePath)
  }
  return filePath
}

function isSafePath(rel) {
  if (!rel) return false
  const normalized = rel.replace(/\\/g, "/")
  const safePrefixes = [
    ".tasks/",
    "docs/adr/",
    ".opencode/",
  ]
  const safeExact = [
    "pyproject.toml",
  ]
  const safePatterns = [
    /^tests\//,
    /\/tests\//,
    /^test\//,
    /\/test\//,
    /\/__tests__\//,
    /(^|\/)conftest\.py$/,
    /(^|\/)test_[^/]*\.py$/,
    /(^|\/)[^/]*_test\.py$/,
    /(^|\/)[^/]*\.test\.(ts|tsx|js|jsx)$/,
    /(^|\/)[^/]*\.spec\.(ts|tsx|js|jsx)$/,
    /^e2e\//,
    /\/e2e\//,
    /playwright\.config\.[^/]+$/,
    /(^|\/)package\.json$/,
    /(^|\/)\.gitignore$/,
  ]
  if (safePrefixes.some((p) => normalized.startsWith(p))) return true
  if (safeExact.includes(normalized)) return true
  if (safePatterns.some((re) => re.test(normalized))) return true
  return false
}

export const LoopStateMachine = async ({ directory }) => {
  return {
    "tool.execute.before": async (input, output) => {
      const state = readState(directory)

      // Gate delegations (task tool)
      if (input.tool === "task") {
        const subagent = output.args?.subagent_type
        if (subagent === "issue-creator" && !state.briefExists) {
          throw new Error("LOOP-STATE: brief.md must exist before issue-creator (Phase 1)")
        }
        if (subagent === "test-writer" && !state.briefConfirmed) {
          throw new Error("LOOP-STATE: brief must be confirmed before test-writer (Phase 1)")
        }
        if (subagent === "implementer" && !state.hasTests) {
          throw new Error("LOOP-STATE: tests must exist before implementer (Phase 3)")
        }
        if (subagent === "logic-verifier" && !state.hasImpl) {
          throw new Error("LOOP-STATE: implementation must exist before logic-verifier (Phase 4)")
        }
        if (subagent === "visual-verifier" && !state.hasImpl) {
          throw new Error("LOOP-STATE: implementation must exist before visual-verifier (Phase 4)")
        }
        if (subagent === "pr-creator" && !state.allVerdictsPass) {
          throw new Error("LOOP-STATE: all verification verdicts must be PASS before pr-creator (Phase 7)")
        }
        if (subagent === "playwright-setup" && !state.briefExists) {
          throw new Error("LOOP-STATE: brief must exist before playwright-setup (Phase 1)")
        }
      }

      // Gate file writes when no tests exist yet
      if (input.tool === "write" || input.tool === "edit" || input.tool === "apply_patch") {
        if (!state.hasTests) {
          const rel = relPath(directory, output.args?.filePath || output.args?.path || output.args?.file)
          if (!isSafePath(rel)) {
            throw new Error("LOOP-STATE: cannot write code files before tests exist (Phase 3). Only .tasks/, docs/adr/, tests, e2e, config files allowed.")
          }
        }
      }
    },
  }
}

export default LoopStateMachine