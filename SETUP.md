# NORAY Setup Guide

Complete setup instructions for NORAY — AI Career & Scholarship Operating System.

## Prerequisites

- **Python 3.10+** (3.12+ recommended)
- **Claude Code** (CLI) — [install guide](https://docs.anthropic.com/en/docs/claude-code/overview)
- **Bun** (for Danish job search CLI tools) — [bun.sh](https://bun.sh)
- **LaTeX** with `lualatex` and `xelatex`:
  - Windows: [MiKTeX](https://miktex.org/download) — install for all users
  - macOS/Linux: [TeX Live](https://tug.org/texlive/)
  - The CV compiles with `lualatex` (moderncv); the cover letter compiles with `xelatex` (cover.cls requires fontspec)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/GhariebML/NORAY.git
cd NORAY
```

### 2. Install Python dependencies

```bash
# Install in development mode
pip install -e ".[dev]"

# Or install just the package
pip install -e .
```

This installs all dependencies: `pydantic>=2.0`, `fastapi`, `uvicorn`, `httpx`, `pdfplumber`, `PyMuPDF`, `python-docx`, `pytesseract`, `Pillow`, and test dependencies.

### 3. Install Danish job search tools (optional)

```bash
cd .agents/skills/jobbank-search/cli && bun install && cd ../../../..
cd .agents/skills/jobdanmark-search/cli && bun install && cd ../../../..
cd .agents/skills/jobindex-search/cli && bun install && cd ../../../..
cd .agents/skills/jobnet-search/cli && bun install && cd ../../../..
```

These are only needed for the Danish job market. The core NORAY functionality works without them.

### 4. Set up your profile

```bash
claude
# Inside Claude Code:
/setup
```

`/setup` offers three paths:
- **Path A**: Read your `documents/` folder (CV PDF, LinkedIn export, diplomas, etc.)
- **Path B**: Import a single CV pasted in chat
- **Path C**: Walk through an interview

### 5. Verify installation

```bash
# Run all tests
python -m pytest tests/ -v

# Start the API server
uvicorn NORAY.api.app:app --reload --port 8000
# Visit http://localhost:8000/docs
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NORAY_PROFILE_PATH` | Path to career_profile.json | `./career_profile.json` |
| `NORAY_LLM_PROVIDER` | LLM provider for generation | `anthropic` |
| `NORAY_LLM_MODEL` | Model to use | `claude-3-5-sonnet-20241022` |
| `NORAY_API_HOST` | API server host | `0.0.0.0` |
| `NORAY_API_PORT` | API server port | `8000` |

### Profile Location

The canonical profile is stored at `career_profile.json` in the project root. All agents read from this file. The profile store module (`NORAY/shared/profile_store.py`) handles:
- Loading and saving with atomic writes
- Automatic backups before each save
- Merge with intelligent deduplication
- Diff tracking between versions
- Export to legacy skill files (backward compatibility)

### LaTeX Setup

NORAY requires two LaTeX engines:
- **`lualatex`** for CV compilation (moderncv template)
- **`xelatex`** for cover letter compilation (cover.cls with fontspec)

Verify both are available:
```bash
lualatex --version
xelatex --version
```

On Windows with MiKTeX, ensure both are in your PATH. MiKTeX may prompt to install missing packages on first run — allow this.

### GitHub Import

For `/import_github`, set a GitHub personal access token:
```bash
export GITHUB_TOKEN=ghp_your_token_here
```

The token needs `public_repo` and `read:user` scopes.

## Project Structure

```
NORAY/
├── career_profile.json         # Your canonical profile
├── NORAY/                     # Python package
│   ├── shared/                 # Core models & utilities
│   ├── profile_engine/         # Multi-source profile import
│   ├── career_agent/           # Job search & applications
│   ├── scholarship_agent/      # Scholarship search & docs
│   ├── upskill_agent/          # Skill gap & roadmap
│   ├── dashboard/              # Tracking & analytics
│   └── api/                    # REST API
├── .claude/commands/           # 16 Claude Code commands
├── tests/                      # 233 tests
├── cv/                         # CV LaTeX templates
├── cover_letters/              # Cover letter templates
├── documents/                  # Your source materials
│   ├── cv/                     # Master CV files
│   ├── linkedin/               # LinkedIn exports
│   ├── diplomas/               # Degree certificates
│   ├── certificates/           # Professional certificates
│   └── references/             # Reference letters
└── docs/                       # Additional documentation
```

## Troubleshooting

### LaTeX compilation fails

- **fontawesome5 error**: Use `lualatex`, not `pdflatex`. MiKTeX sometimes defaults to pdflatex.
- **fontspec error**: Cover letters need `xelatex`, not `lualatex` or `pdflatex`.
- **Missing packages**: MiKTeX should auto-install. If not, run `mpm --install` for the missing package.

### Tests fail

- **Import errors**: Run `pip install -e ".[dev]"` to ensure all dependencies are installed.
- **Permission errors on Windows**: Close any programs that might lock `.pytest_cache/`.
- **Deprecation warnings**: These are non-breaking. The tests still pass.

### API server won't start

- **Port in use**: Change port with `uvicorn NORAY.api.app:app --port 8001`.
- **Missing module**: Ensure the package is installed: `pip install -e .`.

### Profile import fails

- **PDF parsing**: Requires `pdfplumber` and `PyMuPDF`. Both are installed with the package.
- **OCR for certificates**: Requires `pytesseract` and Tesseract OCR installed on your system.
- **GitHub API**: Requires `GITHUB_TOKEN` environment variable.

## Development

### Running tests

```bash
# All tests
python -m pytest tests/ -v

# Specific module
python -m pytest tests/test_profile_engine.py -v

# With coverage
python -m pytest tests/ --cov=NORAY --cov-report=html

# Quick summary
python -m pytest tests/ -q
```

### Adding new tests

Tests are organized by module:
- `tests/test_profile_engine.py` — Profile models, store, importers
- `tests/test_career_agent.py` — Job search, ATS, CV, cover letter, interview
- `tests/test_scholarship_agent.py` — Scholarship search, eligibility, SOP, docs
- `tests/test_upskill_agent.py` — Gap analysis, roadmap, resources
- `tests/test_dashboard.py` — Tracker, analytics
- `tests/test_api.py` — REST API endpoints

### Code style

- Python 3.10+ with type hints
- Pydantic v2 for data validation
- Dataclasses for internal models
- Docstrings on all public functions
- No external state in tests (use fixtures and tempfile)
