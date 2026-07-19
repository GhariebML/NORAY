# Contributing to NORAY

We welcome contributions! To get started:

1. **Fork the repository** and clone it locally.
2. Run the environment bootstrap script (`./setup.sh` or `.\setup.ps1`).
3. Ensure you have Docker running (`docker-compose up -d`) to spin up local testing databases.
4. **Create a branch** for your feature (`git checkout -b feature/amazing-feature`).
5. Run the linters and tests before committing:
   ```bash
   make lint
   make test
   ```
6. **Submit a Pull Request**.

## Code Style
- We use `ruff` for Python linting and formatting. Line length is set to 120.
- For frontend, we use Next.js ESLint defaults and Prettier.

## Adding New AI Providers
To add a new LLM provider to the AI Gateway:
1. Create `noray/gateway/providers/yourprovider.py`.
2. Implement the `BaseLLMProvider` interface.
3. Register it in `noray/gateway/facade.py`.
