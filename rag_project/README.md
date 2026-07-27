# RAG Assistant — Simple Retrieval-Augmented Generation Project

A minimal, file-based RAG pipeline (no notebooks) that goes from raw
documents to a deployed Streamlit assistant:

```
documents -> preprocessing -> chunking -> vector representation ->
vector store -> context retrieval -> prompting -> Streamlit UI
```

## Project Structure

```
.
├── 01_documents.py             # Load raw .txt/.pdf files from documents/
├── 02_preprocessing.py         # Clean text (whitespace, control chars, hyphenation)
├── 03_chunking.py              # Word-based sliding-window chunking
├── 04_vector_representation.py # OpenAI embeddings (text-embedding-3-small)
├── 05_create_chroma_store.py   # Build/persist the Chroma vector store
├── 06_retrieve_context.py      # Query the vector store for relevant chunks
├── 07_prompting.py             # Build grounded prompt + call the LLM
├── streamlit_app.py            # Final UI tying everything together
├── _module_loader.py           # Helper to import numbered files (01_..., 02_...)
├── documents/                  # Source documents (sample .txt files included)
├── requirements.txt
├── .env.example                # Template for local API key — copy to .env
├── .streamlit/secrets.toml.example  # Template for Streamlit Cloud secrets
└── .gitignore
```

`_module_loader.py` exists because Python cannot `import 01_documents`
directly (module names can't start with a digit). Every step imports
the previous one via `load_module("0N_filename")` instead of a plain
`import` statement — this keeps the required numeric filenames exactly
as specified while still letting each file be run standalone or reused
by the next step.

## API Key Rule

**No real API key is ever written into any Python file.** The project
needs exactly one key — `OPENAI_API_KEY` — used for both embeddings
(step 4) and answer generation (step 7). It is read at runtime from:

- a local `.env` file (git-ignored — copy `.env.example` → `.env` and
  fill in your real key), **or**
- Streamlit Community Cloud's **Secrets** panel when deployed, which
  `streamlit_app.py` copies into the environment automatically.

`.gitignore` already excludes `.env` and `.streamlit/secrets.toml`, so
a real key can never be committed accidentally.

## Running Locally

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your API key
cp .env.example .env
# edit .env and paste your real OPENAI_API_KEY

# 4. (Optional) Run each pipeline step individually to see how it works
python 01_documents.py
python 02_preprocessing.py
python 03_chunking.py
python 04_vector_representation.py
python 05_create_chroma_store.py
python 06_retrieve_context.py "What is the remote work policy?"
python 07_prompting.py "What is the remote work policy?"

# 5. Launch the Streamlit app
streamlit run streamlit_app.py
```

The app auto-builds the vector store from `documents/` on first run.
Use your own documents by dropping `.txt` or `.pdf` files into
`documents/` and clicking **"Rebuild vector store"** in the sidebar.

## Deploying to Streamlit Community Cloud

1. Push this project to a **public GitHub repository**.
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Select your repo, branch, and set the main file to `streamlit_app.py`.
4. Before (or right after) deploying, open **App settings → Secrets**
   and add:
   ```toml
   OPENAI_API_KEY = "sk-your-real-key-here"
   ```
5. Deploy. The app reads the key from `st.secrets` automatically — no
   code change needed.

## Final Submission Checklist

Your submission must include all three of the following:

- [ ] **ZIP file** of the full project folder (excluding `.env`,
      `chroma_db/`, and `__pycache__/` — see `.gitignore` for the
      exact exclusion list). Example:
      ```bash
      zip -r rag_project_submission.zip . -x ".env" "chroma_db/*" "__pycache__/*" ".git/*"
      ```
- [ ] **GitHub repository link** — the public repo containing this
      exact structure, with `.env` and secrets never committed.
- [ ] **Deployed Streamlit app link** — the live `*.streamlit.app` URL
      from step "Deploying to Streamlit Community Cloud" above.

## Customization Notes

- **Chunk size/overlap**: edit `DEFAULT_CHUNK_SIZE` /
  `DEFAULT_CHUNK_OVERLAP` in `03_chunking.py`.
- **Number of retrieved chunks**: adjustable live in the Streamlit
  sidebar, or via `DEFAULT_TOP_K` in `06_retrieve_context.py`.
- **LLM model**: selectable in the Streamlit sidebar, or via
  `DEFAULT_MODEL` in `07_prompting.py`.
- **Swapping embedding/LLM providers**: only `04_vector_representation.py`
  and `07_prompting.py` talk to OpenAI directly — every other file
  depends on their functions, not on the OpenAI SDK, so switching
  providers only requires editing those two files.
