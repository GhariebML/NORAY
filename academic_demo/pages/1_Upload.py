import streamlit as st
from academic_demo.components.utils import inject_custom_styles, render_header
from academic_demo.components.api import upload_file, list_documents, delete_document

# Page config
st.set_page_config(page_title="Upload Knowledge — NORAY OS", page_icon="📤", layout="wide")
inject_custom_styles()
render_header("Knowledge Base", "Ingest and auto-classify academic papers, career profiles, and general documents.")

col_upload, col_library = st.columns([1, 1])

with col_upload:
    st.markdown(
        """
        <div class="glass-card">
            <h3 style="color: #ffffff; margin-bottom: 15px;">📤 Upload New Document</h3>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Namespace selector
    namespaces = [
        ("general", "General Knowledge"),
        ("resumes", "Resumes & CVs"),
        ("papers", "Academic Papers"),
        ("code", "Source Code"),
        ("spreadsheets", "Spreadsheets (XLSX/CSV)"),
        ("presentations", "Presentations (PPTX)"),
    ]
    category = st.selectbox(
        "Target Namespace",
        options=[n[0] for n in namespaces],
        format_func=lambda x: next(n[1] for n in namespaces if n[0] == x)
    )
    
    uploaded_file = st.file_uploader(
        "Drag and drop your file here",
        type=["pdf", "docx", "txt", "md", "csv", "xlsx", "pptx", "png", "jpg", "jpeg"]
    )
    
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        filename = uploaded_file.name
        
        st.info(f"File '{filename}' loaded. Preparing to upload to category '{category}'...")
        
        if st.button("Index Document"):
            with st.spinner("Processing document (extracting, chunking, and embedding)..."):
                res = upload_file(file_bytes, filename, category)
                if "error" in res:
                    st.error(f"Ingestion failed: {res['error']}")
                else:
                    st.success(f"Successfully ingested '{res['filename']}'! Created {res['chunks_count']} chunks.")
                    st.balloons()
                    # Force reload library
                    st.rerun()

with col_library:
    st.markdown(
        """
        <div class="glass-card">
            <h3 style="color: #ffffff; margin-bottom: 15px;">📚 Document Library</h3>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    docs = list_documents()
    
    if not docs:
        st.info("No documents uploaded yet. Upload a file on the left to populate the knowledge base.")
    else:
        # Group by source to avoid listing multiple points/chunks
        unique_docs = {}
        for d in docs:
            payload = d.get("payload", {})
            source = payload.get("source", "Unknown Document")
            if source not in unique_docs:
                unique_docs[source] = {
                    "id": d.get("id"),
                    "source": source,
                    "category": payload.get("category", "general"),
                    "doc_type": payload.get("doc_type", "Document"),
                    "chunks_count": payload.get("chunks_count", 1),
                    "reading_time": payload.get("reading_time_min", 1),
                    "created_at": payload.get("created_at", "")
                }
        
        for name, doc in unique_docs.items():
            with st.expander(f"📄 {name} [{doc['doc_type']}]"):
                col_info, col_action = st.columns([3, 1])
                with col_info:
                    st.markdown(
                        f"""
                        - **Namespace**: `{doc['category']}`
                        - **Chunks**: {doc['chunks_count']} chunks indexed
                        - **Reading Time**: ~{doc['reading_time']} min
                        """
                    )
                with col_action:
                    if st.button("Delete File", key=f"del_{doc['id']}"):
                        with st.spinner("Deleting..."):
                            if delete_document(doc['id']):
                                st.success("Deleted document.")
                                st.rerun()
                            else:
                                st.error("Failed to delete document.")
