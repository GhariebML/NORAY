# Troubleshooting

## Ollama Cannot Be Reached
- **Symptom:** AI Gateway falls back repeatedly or First Run Wizard fails to download models.
- **Fix:** Ensure the Ollama background service is running. On Windows, check the System Tray. On macOS, check the menu bar. Verify `http://localhost:11434` responds.

## Qdrant Connection Refused
- **Symptom:** `Qdrant not reachable on localhost:6333` during `database_init.py`.
- **Fix:** Ensure Docker Compose is running. Run `docker-compose ps` to verify the Qdrant container is healthy.

## Next.js Build Failures
- **Symptom:** `npm run build` fails with ESLint or TypeScript errors.
- **Fix:** Run `npm run lint` and fix any type errors. If SWC compiler fails on Windows, ensure `@next/swc-win32-x64-msvc` is installed.

## Port Conflicts (5432)
- **Symptom:** Docker Compose cannot start PostgreSQL.
- **Fix:** You likely have a native PostgreSQL installation running on port 5432. Stop the local service or change `POSTGRES_PORT` in `.env` and `docker-compose.yml`.
