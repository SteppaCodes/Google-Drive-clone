# Contributing to Lore

Thank you for your interest in contributing to Lore!

## Prerequisites
- Python 3.12+
- PostgreSQL (recommended) or SQLite (for quick development)

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/The-17/Lore.git
   cd Lore
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables:**
   ```bash
   cp .env.example .env
   ```

5. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Run tests:**
   ```bash
   python manage.py test
   ```

## Development Workflow
- **Branch Naming:** Use descriptive prefixes like `feature/`, `bugfix/`, or `docs/` (e.g., `feature/folder-sharing`).
- **Commit Messages:** Write clear, imperative commit messages.
- **Pull Requests:** Open a PR against the `main` branch. Ensure CI passes and request a review.

## Code Style
We use `ruff` for linting and formatting, and `mypy` for static type checking.
- Run `ruff check .` to check for linting errors.
- Run `mypy .` to check types.

## Testing Requirements
- All tests must pass before a PR can be merged.
- New features must include appropriate test coverage.

## Project Structure Overview
- `apps/accounts/`: User authentication, registration, and profiles.
- `apps/files/`: File management, uploading, and metadata.
- `apps/folders/`: Folder structure and organization.
- `apps/common/`: Shared utilities, base models, and helpers.
- `lore/`: Django project configuration and settings.
