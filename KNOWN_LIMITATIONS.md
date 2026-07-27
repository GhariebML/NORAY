# Known Limitations & Mitigation Protocols

This document records the current known limits of **NORAY OS v1.0.0** and the built-in mitigation protocols implemented in the system.

---

## 📋 Limitations & Mitigation Table

| Limitation | Technical Reason | Mitigation Protocol |
|---|---|---|
| **Local LLM Memory Requirements** | Running local Ollama models (`qwen2.5-coder:7b`) requires 8GB+ RAM. | Automated failover probes switch to cloud Gemini/DeepSeek APIs if local RAM/VRAM is constrained. |
| **Complex Table Formatting in PDFs** | PDF parsers can struggle with borderless complex multi-column tables. | Clean preprocessing regex normalizes paragraphs prior to semantic chunking. |
| **Qdrant Storage Locking** | Simultaneous process access to local Qdrant SQLite files can trigger portalocker errors. | Thread-safe Singleton connection manager prevents concurrent lock contention. |
