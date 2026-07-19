import time
import sys
import psutil
from noray.gateway.providers.local import LocalProvider
from noray.rag.local_embeddings import LocalEmbeddings

def run_benchmark():
    print("=== Local LLM & Embedding Benchmark ===")
    
    # Measure memory before
    mem_before = psutil.virtual_memory().used
    
    print("\n1. Testing Local Embeddings...")
    start_time = time.time()
    try:
        embeddings_model = LocalEmbeddings()
        vec = embeddings_model.embed_text("This is a test document for generating vector embeddings.")
        emb_latency = time.time() - start_time
        print(f"✓ Embeddings Generated! Vector Size: {len(vec)}")
        print(f"  Latency: {emb_latency:.2f} seconds")
    except Exception as e:
        print(f"✗ Embeddings failed: {e}")

    print("\n2. Testing Local LLM Inference (Ollama)...")
    start_time = time.time()
    try:
        provider = LocalProvider()
        response, meta = provider.generate("Explain the theory of relativity in two short sentences.")
        llm_latency = time.time() - start_time
        print(f"✓ LLM Inference Successful!")
        print(f"  Response: {response}")
        print(f"  Latency: {llm_latency:.2f} seconds")
    except Exception as e:
        print(f"✗ LLM inference failed: {e}")

    # Measure memory after
    mem_after = psutil.virtual_memory().used
    diff_mb = (mem_after - mem_before) / (1024 * 1024)
    print(f"\nMemory Delta during Benchmark: {diff_mb:.2f} MB")

if __name__ == "__main__":
    run_benchmark()
