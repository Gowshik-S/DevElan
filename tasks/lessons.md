# Lessons Learned

- Seed routines must be idempotent against custom credential changes: locate existing accounts by multiple stable identifiers (register number, email, role) before insert, otherwise startup can crash on unique constraints.
- Frontend API clients should not rely on one hard-coded host; include localhost/127.0.0.1 fallback and provide same-origin frontend serving via backend to avoid browser context fetch failures.
- Admin bulk-import pipelines must support headerless CSV and real-world column aliases (e.g., "PROBLEM STATEMENT NUMBER") or uploads silently fail with zero mapped/imported rows.
- Bulk import UX must never show failure count alone; always return and render per-row identity plus reason so admins can act on failed records immediately.
- Dynamic task pages should not ship with realistic hardcoded defaults (e.g., EL-01) because empty API states can look like assigned tasks; use neutral placeholders and explicit empty-state rendering.
- Upload success overlays in admin flows should auto-hide on a short timer and pair summaries with row-level failure lists to prevent blocked or ambiguous states.
- After layout/theme edits, re-verify critical admin result panels still render row-level outcomes; payload correctness alone is insufficient if the UI regresses to count-only summaries.
- Every visual success/failure overlay in admin flows must have deterministic auto-dismiss with timer reset on repeat actions; otherwise repeated sync attempts can leave cards permanently blocked.
- Avoid global `overflow: hidden` on `body` for dashboard-style pages; use scrollable page flow with `min-height: 100vh` and reserve overflow locks for temporary modal/intro states only.
- When catalog and assignment are separate uploads, always preserve/import canonical use-case code (`ID`) and never auto-create fallback description records during mapping-only sync; missing codes must be explicit failures.
- For use-case catalog files, header aliases must include practical variants (`THE OBJECTIVE`, `problem_number`, `problem_id`, `expected_output`, plain `id`) or imports can appear successful while leaving stale placeholder records in student views.
- When users ask for a page to be hosted separately, avoid adding backend route integration or backend-dependent links; keep it a standalone static artifact.
- If a user specifies light-only mode, remove all dark-mode tokens/toggles and avoid dual-theme scaffolding.
- API root fallback lists must be environment-aware: never include localhost fallbacks on hosted origins, or users will see misleading production errors and hit unreachable local endpoints.
- If the user explicitly asks to remove localhost completely, remove all localhost/127 references from frontend source and error paths, not just runtime fallbacks.
- If a user escalates from roadmap language ("2-4 weeks") to an explicit "implement this" request, switch immediately to an additive production-safe implementation path instead of proposing only guidance.
- For upload stalls that happen to all users at the same early percentage, always check edge proxy/CDN body-size limits (e.g., Cloudflare) and add adaptive chunk sizing around HTTP 413.
