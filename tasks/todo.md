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
