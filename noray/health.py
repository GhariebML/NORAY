import socket
import subprocess
import sys

from noray.config import settings


def is_port_open(host: str, port: str) -> bool:
    try:
        with socket.create_connection((host, int(port)), timeout=1):
            return True
    except OSError:
        return False

class RecoveryManager:
    def __init__(self):
        self.issues = []
        self.recovered = []

    def check_command(self, cmd: list, name: str, recovery: str):
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            print(f"[OK] {name} is installed.")
        except (FileNotFoundError, subprocess.CalledProcessError):
            print(f"[ERR] {name} is MISSING.")
            self.issues.append(f"{name} is missing. {recovery}")

    def attempt_docker_recovery(self, service: str):
        print(f"[RECOVERY] Attempting to start {service} via docker-compose...")
        try:
            res = subprocess.run(["docker-compose", "up", "-d", service], capture_output=True, text=True)
            if res.returncode == 0:
                print(f"[RECOVERY] Successfully started {service}.")
                self.recovered.append(f"Restarted {service} via Docker.")
                return True
            else:
                print(f"[RECOVERY] Failed to start {service}: {res.stderr.strip()}")
                return False
        except FileNotFoundError:
            print("[RECOVERY] docker-compose not found.")
            return False

    def check_service(self, host: str, port: str, name: str, docker_service: str = None):
        if is_port_open(host, port):
            print(f"[OK] {name} is running on {host}:{port}.")
        else:
            print(f"[WARN] {name} is NOT running on {host}:{port}.")
            if docker_service and self.attempt_docker_recovery(docker_service):
                if is_port_open(host, port):
                    print(f"[OK] {name} recovered and running on {host}:{port}.")
                    return
            self.issues.append(f"{name} is unreachable on {host}:{port}.")

    def ensure_directories(self):
        from noray.config import APPLICATIONS_DIR, DATA_DIR, SCHOLARSHIP_REPORTS_DIR, UPSILL_REPORTS_DIR
        dirs = [DATA_DIR, APPLICATIONS_DIR, UPSILL_REPORTS_DIR, SCHOLARSHIP_REPORTS_DIR]
        for d in dirs:
            if not d.exists():
                print(f"[RECOVERY] Creating missing directory: {d}")
                d.mkdir(parents=True, exist_ok=True)
                self.recovered.append(f"Created missing directory {d.name}")

    def run_migrations(self):
        from alembic import command
        from alembic.config import Config

        from noray.config import PROJECT_ROOT
        try:
            print("[RECOVERY] Running database migrations...")
            alembic_cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
            command.upgrade(alembic_cfg, "head")
            self.recovered.append("Applied pending database migrations.")
        except Exception as e:
            self.issues.append(f"Failed to run database migrations: {e}")

    def run_checks(self):
        print("\n--- NORAY Health & Recovery Manager ---")

        self.ensure_directories()

        # Software checks
        self.check_command(["python", "--version"], "Python", "Install Python 3.10+ and ensure it is in PATH.")
        self.check_command(["node", "--version"], "Node.js", "Install Node.js 18+")
        self.check_command(["npm", "--version"], "npm", "npm is required to run the frontend.")

        # Services checks
        self.check_service(settings.POSTGRES_HOST, settings.POSTGRES_PORT, "PostgreSQL", "postgres")
        self.check_service(settings.QDRANT_HOST, settings.QDRANT_PORT, "Qdrant", "qdrant")
        self.check_service(settings.REDIS_HOST, settings.REDIS_PORT, "Redis", "redis")

        # Migrations
        self.run_migrations()

        # AI check
        ollama_url = settings.OLLAMA_BASE_URL
        ollama_host = ollama_url.split("://")[-1].split(":")[0]
        ollama_port = ollama_url.split(":")[-1].split("/")[0] if ":" in ollama_url.split("://")[-1] else "80"
        self.check_service(ollama_host, ollama_port, "Ollama")

        if self.recovered:
            print("\n[INFO] The following automatic recoveries were performed:")
            for rec in self.recovered:
                print(f"  + {rec}")

        if self.issues:
            print("\n[FAILED] Health check failed with the following unrecoverable issues:")
            for issue in self.issues:
                print(f"  - {issue}")
            sys.exit(1)
        else:
            print("\n[SUCCESS] All systems operational. NORAY is ready.")

if __name__ == "__main__":
    manager = RecoveryManager()
    manager.run_checks()
