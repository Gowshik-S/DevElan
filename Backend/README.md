# FastAPI Backend

## Setup

1. Open a terminal in this folder:
   - `cd Backend`
2. Create a virtual environment:
   - `python -m venv .venv`
3. Activate the virtual environment:
   - PowerShell: `.\.venv\Scripts\Activate.ps1`
   - Command Prompt: `.\.venv\Scripts\activate.bat`
4. Install dependencies:
   - `pip install -r requirements.txt`
5. Configure environment variables:
   - `copy .env.example .env`
   - Update `DATABASE_URL` for your PostgreSQL instance.

## Database

- This backend targets PostgreSQL.
- Tables are created automatically on app startup.
- Seed data is inserted on first startup:
  - Admin: register no `ADMIN001`, password `Admin@123`
  - Student: register no `STU001`, password `Student@123`
  - Demo use case: `EL-01`
   - Note: the demo student is not auto-assigned to a use case.

## Run

Start the development server:

- `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`

Open these URLs:

- API root: http://127.0.0.1:8000/
- Health check: http://127.0.0.1:8000/api/v1/health
- Swagger docs: http://127.0.0.1:8000/docs

## Frontend-Aligned API Groups

- Auth: `/api/v1/auth/login`, `/api/v1/auth/logout`
- Profile: `/api/v1/profile/get`, `/api/v1/profile/update`
- Use case: `/api/v1/usecase/list`, `/api/v1/usecase/get/{use_case_id}`
- Student submission: `/api/v1/submission/repo-link`, `/api/v1/submission/video-upload` (meeting), `/api/v1/submission/demo-video-upload` (optional demo), `/api/v1/submission/get`
- Admin submissions: `/api/v1/submissions/list`, `/api/v1/submissions/get/{submission_id}`, `/api/v1/submissions/update-status`
- Admin tools: `/api/v1/admin/users/create`, `/api/v1/admin/users/bulk-import`, `/api/v1/admin/usecase/assign`
- Video stream: `/api/v1/video/stream/{video_id}`

## Use Case List Response

- `GET /api/v1/usecase/list` returns an object:
   - `items`: assigned use cases for student, all use cases for admin.
   - `message`: optional no-task message for students with no assignment.
- No-assignment message:
   - `No task assigned yet. Stay ready — your next challenge is coming.`
