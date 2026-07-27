# Evaluator Quick-Start Guide

This guide enables academic evaluators and reviewers to launch and test the **NORAY** system within 3 minutes.

---

## ⚡ Option 1: Academic Streamlit Demo (Recommended for Evaluation)

The Streamlit interface requires minimal dependencies and provides a clean evaluation interface.

```bash
# 1. Navigate to academic demo directory
cd academic_demo

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch Streamlit
streamlit run streamlit_app.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your browser.

---

## 🐳 Option 2: Full Production Docker

To test the multi-service system (Next.js, FastAPI, PostgreSQL, Qdrant, Redis):

```bash
# Launch all containers via Docker Compose
docker-compose up --build -d
```
Access points:
- Next.js Workspace UI: `http://localhost:3000`
- FastAPI REST Docs: `http://localhost:8001/docs`

---

## 🧪 Option 3: Run Automated Test Suite

To verify system health programmatically:

```bash
# Run full Pytest test suite
python -m pytest tests/ -v
```
Expectation: **96 passed**.
