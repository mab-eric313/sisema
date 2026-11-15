#! /usr/bin/env bash

set -e
set -x

cd backend
FASTAPI_ENV=development uv run python -c "import main; import json; print(json.dumps(main.app.openapi()))" > ../openapi.json
cd ..
mv openapi.json frontend/
cd frontend
bunx @hey-api/openapi-ts -i ./openapi.json -o ./src/client
# bun run --filter frontend generate-client
bun run lint
