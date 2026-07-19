# Development Guide

## Workflow

1. **Start Local Services**
   ```bash
   make dev-db
   ```
2. **Start Backend**
   ```bash
   make dev-backend
   ```
3. **Start Frontend**
   ```bash
   make dev-frontend
   ```
   Or use `make dev` to start both backend and frontend together.

## Database Migrations

If you make changes to the SQLAlchemy models in `noray/models/`:
1. Generate an alembic migration (once alembic is configured).
2. Or simply restart the backend if relying on `Base.metadata.create_all()` in development.

## Testing

Run Python backend tests:
```bash
make test
```

Run frontend tests:
```bash
cd frontend
npm run test
```
