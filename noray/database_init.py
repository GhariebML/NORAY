import sys
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from noray.database import Base, engine, is_port_open
from noray.config import QDRANT_HOST, QDRANT_PORT

def init_relational_db():
    print("Initializing relational database (Alembic)...")
    try:
        from alembic.config import Config
        from alembic import command
        from noray.config import settings, PROJECT_ROOT
        
        if settings.ENVIRONMENT.lower() == "development":
            alembic_cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
            command.upgrade(alembic_cfg, "head")
            print("[OK] Relational database schema upgraded successfully (Development).")
        else:
            print("[OK] Skipping automatic migration in Production. Verify manually.")
            
    except Exception as e:
        print(f"[ERROR] Failed to initialize relational database: {e}", file=sys.stderr)

def init_vector_db():
    print("Initializing vector database (Qdrant)...")
    if not is_port_open(QDRANT_HOST, QDRANT_PORT):
        print(f"[WARN] Qdrant not reachable on {QDRANT_HOST}:{QDRANT_PORT}. Skipping vector DB init.")
        return

    try:
        client = QdrantClient(host=QDRANT_HOST, port=int(QDRANT_PORT))
        collections = [c.name for c in client.get_collections().collections]
        
        # We need a collection for user documents. 384 is typical for all-MiniLM-L6-v2
        collection_name = "user_documents"
        if collection_name not in collections:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
            print(f"[OK] Created Qdrant collection: {collection_name}")
        else:
            print(f"[OK] Qdrant collection {collection_name} already exists.")
    except Exception as e:
        print(f"[ERROR] Failed to initialize Qdrant: {e}", file=sys.stderr)

def seed_data():
    print("Seeding initial development data...")
    # Add any required initial seeds here
    print("[OK] Seeding complete.")

if __name__ == "__main__":
    print("--- NORAY Database Initialization ---")
    init_relational_db()
    init_vector_db()
    seed_data()
    print("-------------------------------------")
