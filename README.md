# SISEMA — Sistem Informasi Senat Mahasiswa UISI

This project is an assignment for the MPPL (Manejemen Proyek Perangkat Lunak/Software Project Management) course.

## Tech Stack

- Frontend: React
- Backend: FastAPI
- Database: PostgreSQL
- ORM: SQlModel
- Database Migration: Alembic
- Authentication: PyJWT

## Application Access

- FastAPI: `http://localhost:8000/`
- FastAPI API Docs: `http://localhost:8000/docs`
- React: `http://localhost:5173/`

## Development Setup

Requirements:
- uv >= 0.11.16, < 1.0.0
- bun >= 1.3.14, < 2.0.0
- postgresql >= 17.11, < 18.00

1. Clone the repo

	```bash
	git clone https://github.com/mab-eric313/sisema.git
	cd sisema
	```

2. Initialize virtual environment and Install backend dependencies

	```bash
	cd backend
	uv sync
	```

3. Install frontend dependencies

	```bash
	cd ../frontend
	bun install
	```

4. Create env file

	Use your test editor to create `.env` file
	```bash
	# development | production
	FASTAPI_ENV=development

	PROJECT_NAME="FastAPI-React"
	SECRET_KEY=changethis

	POSTGRES_PASSWORD=changethis
	DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@localhost:5432/app

	FIRST_SUPERUSER=admin@example.com
	FIRST_SUPERUSER_PASSWORD=changethis

	# Email / SMTP
	SMTP_PORT=587
	SMTP_HOST=smtp.gmail.com
	SMTP_USER=info@example.com
	SMTP_PASSWORD=changethis

	# Sender
	EMAILS_FROM_EMAIL=info@example.com
	EMAILS_FROM_NAME=
	```

5. Run migration

	```bash
	cd ../backend
	bash scripts/prestart.sh
	```

5. Run the project

	Open two terminal

	- Backend

	```bash
	cd backend
	uv run fastapi dev
	```

	- Frontend

	```bash
	cd frontend
	bun run dev
	```
