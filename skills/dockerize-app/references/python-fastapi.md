# Python and FastAPI images

- Derive the Python version from `requires-python`, runtime files, CI, or existing images.
- Use the repository's package manager and lockfile. Do not silently migrate pip, Poetry, Pipenv, or uv.
- Install dependencies before copying changing application source.
- Keep compilers and development headers out of the runtime stage where practical.
- Run FastAPI through the repository's documented ASGI server and import path.
- Use exec-form commands such as `uvicorn module:app --host 0.0.0.0 --port 8000` only when the module and application object exist.
- Do not add multiple workers without considering CPU, memory, connection pools, graceful shutdown, and application state.
- Keep Alembic migrations as an explicit deployment operation. Do not run them in every web-container startup.
- Ensure the runtime user can read application files and write only to documented temporary or persistent paths.
- Prefer an orchestrator health check calling an existing lightweight endpoint. Do not invent a health endpoint in deployment configuration.
