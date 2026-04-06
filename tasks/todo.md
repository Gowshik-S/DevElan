# FastAPI Backend Initialization

## Context Map

### Files to Create
- Backend/requirements.txt (Python dependencies)
- Backend/app/__init__.py (package marker)
- Backend/app/main.py (FastAPI app entrypoint)
- Backend/app/api/__init__.py (API package marker)
- Backend/app/api/router.py (top-level API router)
- Backend/app/api/routes/__init__.py (routes package marker)
- Backend/app/api/routes/health.py (health endpoint)
- Backend/README.md (setup and run instructions)

### Dependencies
- fastapi
- uvicorn

### Risks
- [x] Breaking changes to existing API surface (none expected; folder is empty)
- [x] Configuration changes required (minimal; install deps and run uvicorn)

## Plan

- [x] Scaffold FastAPI package and route structure
- [x] Add dependency and startup docs
- [x] Validate files for syntax/editor errors
- [x] Add implementation review notes

## Review

- Implemented a new FastAPI app entrypoint with CORS and API router mounting.
- Added versioned health endpoint at /api/v1/health and root endpoint at /.
- Added dependency manifest and backend setup/run documentation.
- Verified with workspace diagnostics: no errors reported in Backend.

## Research Plan (2025-2026 Dark UI, Non-Blue Accents)

- [ ] Web best-practices scan for dark dashboard and edtech color trends
- [ ] Failure and pitfalls scan for saturation, eye strain, and accessibility regressions
- [ ] Alternatives and tradeoffs scan across non-blue accent families
- [ ] Codebase cross-reference for current palette constraints in Frontend
- [ ] Security/performance and accessibility audit for contrast and usability impacts
- [ ] Community pulse scan to validate what is currently shipping in production tools

## Backend Implementation Plan (Frontend Parity)

- [x] Phase 1: Add configuration, PostgreSQL session, models, and app data initialization
- [x] Phase 2: Add JWT auth + role dependencies and profile/usecase endpoints
- [x] Phase 3: Add submission/video/admin endpoints with file and bulk-upload handling
- [x] Phase 4: Wire routers, update dependencies/docs, and run diagnostics

### Backend Implementation Review (2026-04-02)

- Implemented full frontend-aligned API surface under `/api/v1` for auth, profile, usecase, submission, submissions, admin, and video.
- Added SQLAlchemy models for users, use cases, assignments, submissions, and video assets.
- Added PostgreSQL configuration, JWT auth helpers, role guards, upload storage service, and CSV/XLSX parsing utilities.
- Wired startup initialization for auto table creation + seed data and upload directory setup.
- Verified workspace diagnostics report zero errors and runtime import check succeeds (`routes 22`, `ready`).

## Frontend Wiring Plan (2026-04-03)

- [x] Wire `index.html` login to `/api/v1/auth/login` and session storage
- [x] Wire `user_home.html` use-case fetch and submission uploads
- [x] Wire `user_profile.html` profile fetch/update with auth guard
- [x] Wire `admin.html` create user + bulk import + assignment sync
- [x] Wire `form.html` submissions list/search/video stream + admin guard
- [x] Validate browser/runtime behavior and update review notes

### Frontend Wiring Review (2026-04-03)

- Connected landing login modal to live `/api/v1/auth/login`, persisting token/role/user id in local storage.
- Added authenticated API integration for student home (`/usecase/list`, `/usecase/get/{id}`, `/submission/repo-link`, `/submission/video-upload`, `/submission/get`).
- Added profile bootstrap/update integration via `/profile/get` and `/profile/update`.
- Added admin management integrations for single-user creation, bulk user upload, and use-case assignment sync.
- Replaced mock submissions viewer data with live `/submissions/list` rendering and authenticated video streaming from `/video/stream/{video_id}`.
- Added logout handlers across pages and session guards for protected/admin-only screens.

## Research Findings (Dark UI, 2025-2026)

- [x] Best-practice scan complete: current major systems emphasize tokenized dark layers and contrast-aware roles
- [x] Pitfalls scan complete: saturated accents on near-black reduce readability and perceived sharpness
- [x] Alternatives/tradeoffs complete: warm amber/coral, emerald/mint, and magenta/rose are viable non-blue accent families
- [x] Codebase cross-reference complete: Frontend dark theme already uses orange/amber/mint accents and layered dark surfaces
- [x] Security/performance review complete: WCAG AA text/non-text contrast thresholds confirmed
- [x] Community pulse complete (partial): framework/design-system sources resolved; several trend blogs blocked by extraction/anti-bot

### Bottlenecks

- Missing `docs/` directory prevents internal-doc verification against implementation
- Trend-editorial sources had retrieval limits; recommendations are anchored primarily to standards and design-system sources
- Existing frontend includes heavy translucency/blur usage, which can reduce contrast clarity in some states

## Use Case CSV Upload Plan (2026-04-03)

- [x] Add backend response schema for use case CSV import results
- [x] Add admin endpoint to upsert use cases from Topic/Objectives CSV
- [x] Add a dedicated upload box in admin panel for use case CSV import
- [x] Validate end-to-end upload flow against running backend
- [x] Add review notes and mark completion

### Use Case CSV Upload Review (2026-04-03)

- Added `UseCaseImportResponse` schema with `created_count`, `updated_count`, and row-level failures.
- Added admin endpoint `POST /api/v1/admin/usecase/import` that reads Topic/Objectives CSV rows and performs overwrite-style upserts by topic.
- Added a dedicated upload card in `Frontend/admin.html` with CSV-only validation and success/failure feedback.
- Verified API behavior with live requests: first upload created two use cases, second upload updated the same two use cases.

### Primary Sources

- WCAG 2.2 Understanding: Contrast Minimum and Non-text Contrast (W3C, 2026 updates)
- Apple Human Interface Guidelines: Dark Mode
- Material Design 3 Color System (May 2025 updates)
- IBM Carbon Color documentation (updated March 2026)
- Radix Colors and Tailwind Colors documentation (2026)
- NN/g dark mode research and pitfalls articles

## Assignment Failure UI Plan (2026-04-03)

- [x] Include assignment row identifiers in backend failure payload
- [x] Show failed assignment reasons directly in admin UI
- [x] Auto-reset assignment success overlay after 5 seconds
- [x] Verify response payload and UI wiring behavior

### Assignment Failure UI Review (2026-04-03)

- Added backend-side `identifier` for assignment failures using register number and use-case code.
- Added `Failed Assignments` panel in admin use-case assignment card to list row-wise reasons.
- Updated overlays to auto-hide after 5 seconds so cards become interactive again.
- Verified assignment API response now includes reasons and identifiers for failed rows.

## Assignment Mapping Visibility Fix (2026-04-03)

- [x] Confirm backend assignment API payload includes detailed failure rows
- [x] Add failed-row rendering in admin assignment card
- [x] Include mapped identifiers in assignment response and render mapped list
- [x] Validate editor diagnostics and summarize outcome

### Assignment Mapping Visibility Review (2026-04-03)

- Verified `POST /api/v1/admin/usecase/assign` already returns row-level failure reasons; UI previously only displayed counts.
- Added a `Failed Assignments` list showing `Row`, optional `register | use_case` identifier, and reason.
- Added backend `mapped_identifiers` in assignment sync response and rendered `Mapped Assignments` list in admin UI.
- Confirmed no new Python diagnostics after schema and route updates.

## Frontend Scroll Unlock Fix (2026-04-03)

- [x] Identify pages with `overflow: hidden` and fixed viewport clamps
- [x] Enable normal vertical scroll on impacted frontend pages
- [x] Remove grid/main viewport max-height clamps that clip content
- [x] Validate diagnostics and confirm no functional regressions

### Frontend Scroll Unlock Review (2026-04-03)

- Updated body layout styles in admin, student home, profile, submissions, and landing pages to allow vertical scrolling.
- Replaced fixed `height: 100vh` + `overflow: hidden` with `min-height: 100vh` and `overflow-y: auto`.
- Removed `max-height: calc(100vh - 100px)` from admin and student home main grids so cards are not clipped at normal zoom.
- Updated profile page main alignment to `flex-start` to avoid centered overflow clipping on shorter viewport heights.

## Use-Case Catalog Quality Fix (2026-04-03)

- [x] Diagnose why synced use cases show placeholder content
- [x] Make use-case import honor CSV `ID` / code columns
- [x] Prevent assignment sync from creating placeholder use cases when code is missing
- [x] Validate backend diagnostics for updated import/sync flow

### Use-Case Catalog Quality Review (2026-04-03)

- Root cause: use-case import ignored `ID` in `EL_Use_Cases.csv`, while assignment sync created missing codes with fallback text (`Imported via assignment sync`).
- Updated `/admin/usecase/import` to read and normalize code from `ID`/code-style columns and upsert by code first.
- Updated `/admin/usecase/assign` creation path to fail with actionable error when code is missing from catalog and row lacks title/objective.
- Added code normalization for numeric/variant formats (`53`, `53.0`, `EL53`, `EL-53`) to prevent mismatches.
- Expanded CSV alias support for common header variants (`THE OBJECTIVE`, `problem_id`, `problem_number`, `expected_output`, `id`) in both import and assignment sync paths.

## Video Role Refactor Plan (2026-04-05)

- [x] Add backend meeting/demo asset classification without DB migration
- [x] Keep backward compatibility by mapping legacy `video_id` to meeting video
- [x] Add optional demo upload API while keeping meeting upload mandatory for completion
- [x] Update student page with separate meeting and demo upload sections
- [x] Update admin submissions page to show/watch meeting and demo videos independently
- [x] Run route and UI smoke checks; record implementation review

### Video Role Refactor Review (2026-04-05)

- Reworked submission video selection to classify by stored filename prefix (`demo_`) so all legacy uploads remain meeting videos by default.
- Added `POST /api/v1/submission/demo-video-upload` and kept existing `POST /api/v1/submission/video-upload` as meeting upload.
- Updated student/admin response schemas with `meeting_video_id` and `demo_video_id` while preserving `video_id` as meeting-compatible legacy field.
- Updated student UI with mandatory meeting upload and optional demo upload card; status remains completion-safe only when meeting is present.
- Updated admin submissions table to show separate Watch controls for meeting and demo videos.
- Verified with an end-to-end TestClient smoke script: demo-only keeps status `in-progress`; meeting upload transitions to `submitted`; admin/student payload IDs align.

## Downtime Page Plan (2026-04-05)

- [x] Design minimalist animated downtime layout aligned with existing DevElan styles
- [x] Create `Frontend/downtime.html` with responsive and reduced-motion support
- [x] Keep page standalone with no backend route integration
- [x] Validate route render and basic page behavior
- [x] Add implementation review notes

### Downtime Page Review (2026-04-05)

- Added a new minimalist animated maintenance page at `Frontend/downtime.html` using the existing DevElan visual system (grid background, glass card, blue/cyan accents, light-only mode).
- Implemented restrained motion with three purposeful animations: grid drift, ambient shape float, and status pulse.
- Added accessibility support with `prefers-reduced-motion` handling and clear readable countdown typography.
- Updated page to show only `Under Maintenance` with ETA `20 min` and a live countdown timer.
- Removed backend-dependent links and retained the page as a separate static hostable artifact.

## Upload Resilience Research Plan (2026-04-05)

- [x] Boot scan: checked docs folder (missing), tasks notes, code paths, and diagnostics
- [x] Web best practices: resumable/chunked strategy patterns used across large providers
- [x] Web pitfalls/failure analysis: duplicates, stale sessions, integrity drift, retry storms
- [x] Web alternatives/tradeoffs: custom chunks vs tus vs direct-to-object-storage multipart
- [x] Docs/code cross-reference: map recommendations to current FastAPI + vanilla JS implementation
- [x] Security/performance audit: auth, integrity checks, storage pressure, and timeout behavior

### Upload Resilience Bottleneck Hypothesis

- Current bottleneck is one-shot multipart upload to app server; any mid-stream interruption restarts from byte zero and increases user drop-off on unstable networks.

### Upload Resilience Findings Summary

- Current implementation confirms one-shot XHR upload to `/api/v1/submission/video-upload` with frontend progress only, but no resumable upload session, no offset reconciliation, and no chunk commit protocol.
- Highest-confidence near-term path is a phased rollout: immediate retry/idempotency hardening on current API, then custom chunked sessions or tus, then direct-to-object-storage multipart at scale.
- Core reliability controls identified: per-upload idempotency key, server-tracked upload session with offset/status endpoint, chunk checksum verification, retry with exponential backoff + jitter, and explicit session expiration/garbage collection.
- Operational risk hotspots to control early: duplicate submission rows/assets, orphaned temp parts, stale session takeover, and integrity mismatches between client-side file metadata and committed object bytes.

## Resumable Upload Implementation Plan (2026-04-05)

- [x] Add backend schemas for resumable upload start/status/chunk/complete responses
- [x] Implement backend resumable session storage and chunk append service with byte-offset validation
- [x] Add authenticated submission routes for resumable start, status, chunk upload, complete, and cancel
- [x] Wire `Frontend/user_home.html` meeting/demo upload flows to chunked resumable API with real last-byte resume
- [x] Preserve existing upload endpoints for backward compatibility and validate no regression in submission status logic
- [x] Run focused smoke checks for resumed upload behavior and add implementation review notes

### Resumable Upload Implementation Review (2026-04-05)

- Added resumable session schemas and response contracts for start, status, chunk, and cancel flows.
- Implemented `app/services/resumable_upload_service.py` with deterministic upload IDs, byte-offset validation, resumable session persistence, and completion finalization into standard upload storage.
- Added authenticated submission routes:
	- `POST /api/v1/submission/resumable/start`
	- `GET /api/v1/submission/resumable/{upload_id}/status`
	- `PUT /api/v1/submission/resumable/{upload_id}/chunk`
	- `POST /api/v1/submission/resumable/{upload_id}/complete`
	- `DELETE /api/v1/submission/resumable/{upload_id}`
- Kept legacy one-shot upload endpoints unchanged for backward compatibility.
- Updated `Frontend/user_home.html` meeting/demo upload actions to use chunked resumable API with deterministic upload keys, server-offset reconciliation, per-chunk retries, and cancel/offline abort handling.
- Tuned chunk strategy for edge proxies (including Cloudflare Tunnel free): default chunk is now 512 KB with adaptive downshift on HTTP 413 response.
- Added adaptive throughput tuning: chunk size now scales up to 2 MB after stable chunk streaks and scales down to 64 KB on gateway or transport instability.
- Verified via OpenAPI route smoke test and end-to-end chunked resume script (`start -> chunk -> start(resume) -> chunk -> complete`) returning success.

## Admin Video Streaming Playback Plan (2026-04-06)

- [x] Add backend short-lived stream-token endpoint for authorized video playback
- [x] Update backend video stream route to accept stream token query auth for HTML5 video element requests
- [x] Replace admin modal blob download flow with direct stream URL playback so browser can range-buffer
- [x] Validate route behavior and page render markers with smoke checks
- [x] Add implementation review notes

### Admin Video Streaming Playback Review (2026-04-06)

- Added `GET /api/v1/video/stream-token/{video_id}` to issue short-lived stream tokens after normal authorization and access checks.
- Updated `GET /api/v1/video/stream/{video_id}` to accept short-lived stream token query auth (`st`) for HTML5 video playback requests while preserving bearer-header support.
- Reworked admin submissions modal playback to avoid `response.blob()` and object URL buffering; playback now uses direct stream URL with token query so the browser can range-buffer and start quickly.
- Verified smoke markers in rendered `/submissions` page: stream-token call present, blob buffering removed, direct stream URL path present.
- Verified range behavior end-to-end with a generated video asset: stream request returns `206`, `accept-ranges: bytes`, and `content-range` header for partial content delivery.

## User Video Replacement Plan (2026-04-06)

- [x] Allow meeting/demo uploads to replace prior video records of the same type
- [x] Prevent UI lock after prior upload so users can upload replacement files immediately
- [x] Keep submission status logic stable while replacing assets
- [x] Validate replacement behavior for both meeting and demo uploads with smoke checks

### User Video Replacement Review (2026-04-06)

- Added backend replacement handling in submission routes so uploading a new meeting/demo video removes previous same-kind asset records for the same submission and cleans up replaced files on disk.
- Applied replacement handling to both one-shot and resumable completion paths, preserving existing route contracts.
- Updated student upload UI to keep upload controls available after prior uploads, including explicit replace guidance and dynamic button labels (`Upload` -> `Replace`).
- Replaced persistent success overlays with short-lived overlays so cards are no longer blocked after successful upload.
- Verified replacement with end-to-end tests:
	- meeting replace: second upload leaves exactly one meeting asset (`meeting_two.mp4`)
	- demo replace: second upload leaves exactly one demo asset (`demo_two.mp4`) and meeting asset remains intact.

## Demo Upload Progress Parity (2026-04-06)

- [x] Add live progress widget in demo upload section (percent, MB, speed, ETA)
- [x] Wire demo upload callback to update progress and status text continuously
- [x] Keep demo progress reset/show/hide and completion behavior consistent with meeting upload
- [x] Validate rendered page markers for demo progress UI and callback wiring

### Demo Upload Progress Parity Review (2026-04-06)

- Added a dedicated progress panel in the demo card and connected it to resumable upload progress updates.
- Demo upload now displays `Uploading X% (uploaded/total MB) • speed MB/s` and ETA while uploading.
- Added demo progress lifecycle helpers (`reset/show/hide/complete`) and invoked them on file selection, upload start, success, and failure paths.
- Verified via render checks that demo progress markup, functions, and live callback wiring are present.

## Admin Evaluation + Alignment Plan (2026-04-06)

- [x] Add backend submission-evaluation persistence for accepted/rejected decision and admin feedback
- [x] Expose evaluation fields in submissions list/detail payloads for admin UI rendering
- [x] Add per-student evaluation controls (decision + feedback + save) in admin submissions page
- [x] Improve alignment/responsive behavior in admin management and submissions pages
- [x] Run focused smoke checks and record implementation review notes

### Admin Evaluation + Alignment Review (2026-04-06)

- Added a new `submission_evaluations` persistence model with one-to-one linkage to submissions, storing `decision` (`pending|accepted|rejected`) and optional `feedback`.
- Added `PATCH /api/v1/submissions/update-evaluation` and extended submissions list/detail payloads with `evaluation_decision` and `admin_feedback`.
- Updated admin submissions UI (`Frontend/form.html`) with per-student evaluation controls: decision dropdown, feedback textarea, and save action.
- Improved alignment/responsiveness for both admin pages by adding centered max-width layout, mobile/tablet header wrapping, and table horizontal-scroll strategy for narrow viewports.
- Verified with smoke checks:
	- OpenAPI route presence for update-evaluation.
	- Render markers for evaluation UI elements in `/submissions`.
	- End-to-end API flow: admin login -> update evaluation -> list payload contains persisted decision and feedback.

## Submissions Sort + Compact Repo Link Plan (2026-04-06)

- [x] Add sort control in submissions page with default latest-upload behavior
- [x] Add name/register number sort options for admin submissions list
- [x] Render repo link as a compact control while keeping new-tab navigation
- [x] Validate rendered page markers for sort wiring and repo-link behavior

### Submissions Sort + Compact Repo Link Review (2026-04-06)

- Added a toolbar sort dropdown with options: `Latest Upload` (default), `Name (A-Z)`, and `Register No (A-Z)`.
- Preserved existing upload-time ordering by default by keeping API response order untouched for `Latest Upload`.
- Added client-side sort helpers for name/register options and wired immediate re-render on sort changes.
- Updated repository link rendering to a compact `Open Repo` chip with `target="_blank"` and `rel="noopener noreferrer"`.
- Verified render markers confirm sort controls, sort functions, compact repo-link class, and new-tab behavior.

## Submission Evaluation Mail Workflow Plan (2026-04-06)

- [x] Convert mail service into reusable Graph API helper wired to backend settings
- [x] Add backend mail-state persistence and API endpoint for evaluation mail sending
- [x] Implement first-send acceptance mail and repeat-send feedback mail with send-anyway confirmation flow
- [x] Add row-level send-mail button in admin submissions evaluation cell
- [x] Validate route + UI behavior with focused smoke checks and add review notes

### Submission Evaluation Mail Workflow Review (2026-04-06)

- Replaced the ad-hoc `mail.py` script with a reusable `send_submission_mail()` helper using Microsoft Graph app credentials from settings.
- Added new mail state persistence table (`submission_mail_notifications`) to track send count and mail type without altering existing evaluation table columns.
- Added `POST /api/v1/submissions/send-evaluation-mail`:
	- First send (`mail_sent_count == 0`) sends acceptance-style mail.
	- Repeat send without `send_anyway` returns `needs_confirmation=true` and message `Mail already sent once. Send anyway?`.
	- Repeat send with `send_anyway=true` sends feedback-style mail (or generic received message if feedback is empty).
- Updated submissions list payload with `mail_sent_count` and `last_mail_type`.
- Added a row-level `Send Acceptance Mail / Send Feedback Mail` button in admin submissions evaluation cell and wired confirmation flow in UI.
- Send-mail action now auto-saves current decision and feedback before dispatch, so mail content uses latest edits even if `Save` was not clicked separately.
- Verified with smoke checks:
	- Endpoint registration marker present in OpenAPI.
	- End-to-end sequence: first send success -> second send confirmation required -> forced resend success.
	- List payload reflects incremented `mail_sent_count`.
	- `/submissions` render includes mail button and API wiring markers.

## Polished Mail Templates + History Tooltip (2026-04-06)

- [x] Add formal, separate accepted/rejected first-mail templates
- [x] Expose last mail sent timestamp in submissions API payloads
- [x] Add row-level mail history tooltip showing last sent type and timestamp
- [x] Keep tooltip state synced after each send action
- [x] Validate template selection and tooltip markers with smoke checks

### Polished Mail Templates + History Tooltip Review (2026-04-06)

- Upgraded first-send templates in backend to formal accepted/rejected variants with professional wording.
- Added `last_mail_sent_at` to submission list/detail and send-mail response schemas.
- Updated submissions route item builder and send-mail endpoint responses to include `last_mail_sent_at`.
- Added `Mail History` tooltip chip per row in admin submissions page with title content:
	- Mail Sent Count
	- Last Mail Type
	- Last Sent Time
- Tooltip content now updates after each successful send using returned response fields.
- Verified via mocked mail smoke tests that accepted and rejected first-send templates are selected correctly and that `last_mail_sent_at` is populated.
