$env:ENVIRONMENT = "test"
$env:OLLAMA_BASE_URL = "http://localhost:11434"
$env:POSTGRES_HOST = "localhost"

# Run tests
pytest tests/ -v
