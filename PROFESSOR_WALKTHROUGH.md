# Professor & Academic Reviewer Walkthrough Guide

Dear Professor / Evaluator,

Welcome to the **NORAY AI Operating System** evaluation workspace.

---

## ⚡ Quick Evaluation Steps (2 Minutes)

1. **Launch the Demo Application**:
   ```bash
   cd academic_demo
   pip install -r requirements.txt
   streamlit run streamlit_app.py
   ```
2. **Review RAG Principles**:
   - Navigate to page **`3_RAG_Pipeline`** to inspect the mathematical formulation of Reciprocal Rank Fusion (RRF), cross-encoder reranking, and context compression.
3. **Test Retrieval & Query Answering**:
   - Navigate to **`2_Ask`** to test streaming query formulation, citation citations, and confidence scores.
4. **Verify Automated Unit Tests**:
   ```bash
   python -m pytest tests/ -v
   ```
   *Expected outcome*: 96/96 test modules passing.

Thank you for reviewing our project!
