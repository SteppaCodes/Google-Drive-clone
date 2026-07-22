# Contributing to Lore

Thank you for your interest in contributing to **Lore** — the Artifact Plane for Humans and AI Agents!

---

## 1. Code of Conduct

We aim to build an open, welcoming, and inclusive community. Please treat all contributors with respect.

---

## 2. Development Workflow

### Prerequisites
* **Python**: 3.12+
* **Framework**: Django 5.x + Django Ninja
* **Linters**: `ruff` for code formatting and linting

### Local Development Setup
1. Fork and clone the repository:
   ```bash
   git clone https://github.com/YourUsername/Lore.git
   cd Lore
   ```
2. Create virtual environment and install dependencies:
   ```bash
   python3 -m venv env
   source env/bin/activate
   pip install -r requirements.txt
   ```
3. Set up environment:
   ```bash
   cp .env.example .env
   python manage.py migrate
   ```
4. Create feature branch:
   ```bash
   git checkout -b feat/your-feature-name
   ```

---

## 3. Coding Standards & Guardrails

* **Additive-first**: Prefer extending existing logic rather than swapping out core authentication or scoping stack components.
* **Preserve Behavior**: Verify existing unit tests pass before making pull requests.
* **Explicit Error Context**: Always handle errors explicitly with context in responses or logs.

---

## 4. Running Unit Tests

Run Django test suite:
```bash
python manage.py test apps.artifacts --noinput
```

Ensure all tests pass cleanly before submitting a Pull Request.

---

## 5. Submitting Pull Requests

1. Push your feature branch to your fork:
   ```bash
   git push origin feat/your-feature-name
   ```
2. Open a Pull Request against `main`.
3. Provide a clear description of changes, motivation, and verification steps in your PR body.
