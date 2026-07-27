# CI/CD Workflows with GitHub Actions

This guide describes how to configure **GitHub Actions** workflows for the **NORAY** repository to automate test runs and container image compilation checks.

---

## 🧪 Testing Workflow (`.github/workflows/test.yml`)

This workflow automatically executes the backend test suite and checks the frontend build on every pull request or push to the `main` branch.

Create the file `.github/workflows/test.yml`:

```yaml
name: NORAY CI/CD Build & Test

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run Pytest suite
        run: |
          python -m pytest tests/ -v

  frontend-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies & Build
        run: |
          cd frontend
          npm ci
          npm run build
```

---

## 🐳 Docker Build check Workflow (`.github/workflows/docker.yml`)

To verify Dockerfile compile statuses:

Create the file `.github/workflows/docker.yml`:

```yaml
name: Verify Docker Builds

on:
  push:
    branches: [ main ]

jobs:
  build-images:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Test build Backend Image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./Dockerfile
          push: false

      - name: Test build Frontend Image
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          file: ./frontend/Dockerfile
          push: false
```
