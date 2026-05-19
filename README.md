# Sarcom FastTrack Go API

Gin-based WebAPI replacing the original Python backend for the Sarcom FastTrack project. The API keeps the endpoints expected by the frontend, serves `/openapi`, and can run either with an in-memory store or a MongoDB-backed snapshot store like the lecture exercises.

## Runtime

Use the root `mise.toml`:

```bash
cd ..
mise install
cd WAC-BE
```

The API listens on `http://localhost:8000` by default.

```bash
mise exec -- go mod tidy
mise exec -- go test ./...
SARCOMA_API_PORT=8000 mise exec -- go run ./cmd/sarcoma-api-service
```

Seeded users:

| email | password | role |
| --- | --- | --- |
| `admin@admin.com` | `admin` | `admin` |
| `doctor@sft.local` | `doctor` | `doctor` |
| `specialist@sft.local` | `specialist` | `specialist` |

Seed data also includes doctor `19`, organizations `14` and `15`, patient `1`, and report `1`.

## Persistence

By default the API uses an in-memory store, which is useful for tests and local smoke checks.

MongoDB mode is enabled by either `SARCOMA_API_STORE=mongo` or `SARCOMA_API_MONGODB_URI`:

```bash
SARCOMA_API_STORE=mongo \
SARCOMA_API_MONGODB_URI='mongodb://admin:admin@localhost:27017/?authSource=admin' \
SARCOMA_API_MONGODB_DATABASE=sarcoma-fasttrack \
SARCOMA_API_MONGODB_COLLECTION=state \
mise exec -- go run ./cmd/sarcoma-api-service
```

The store is persisted as a single Mongo snapshot document. On first startup with an empty collection, seed data is written automatically.

For Kubernetes startup, the API retries Mongo-backed initialization until `SARCOMA_API_STARTUP_TIMEOUT_SECONDS` expires. The default startup timeout is `60` seconds and the retry delay is controlled by `SARCOMA_API_MONGODB_STARTUP_RETRY_SECONDS` with default `2`.

## Endpoints

Auth:

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/logout`

Core resources:

- `GET|POST /api/v1/patients`
- `GET|PUT|DELETE /api/v1/patients/{id}`
- `GET /api/v1/patients/{id}/name`
- `GET|POST /api/v1/reports`
- `GET|PUT|DELETE /api/v1/reports/{id}`
- `PATCH /api/v1/reports/{id}/status`
- `PATCH /api/v1/reports/{id}/feedback`
- `GET /api/v1/reports/{id}/classification`
- `POST /api/v1/reports/{id}/reclassify`
- `GET|POST /api/v1/organizations`
- `GET|PUT|DELETE /api/v1/organizations/{id}`
- `GET /api/v1/organizations/{id}/name`
- `GET|POST /api/v1/users`

Utility:

- `GET /health/db`
- `GET /openapi`

## Tests

```bash
mise exec -- go test ./...
```

Coverage includes authentication, protected routes, role-filtered reports, patient/report workflows, CRUD routes, and store snapshot persistence.

Runtime smoke from the frontend project:

```bash
cd ../WAC-FE
API_BASE=http://127.0.0.1:8000 mise exec -- npm run test:functional
```

## Docker

Single API image:

```bash
docker build -t sarcoma-fasttrack-api .
docker run --rm -p 8000:8000 sarcoma-fasttrack-api
```

API + MongoDB:

```bash
docker compose up --build
```

If a previously created local Mongo volume has different credentials, reset it with `docker compose down -v` before starting the stack again.

The exercise-style compose file with Mongo Express is also available:

```bash
docker compose -f deployments/docker-compose/compose.yaml up --build
```

Mongo Express is exposed on `http://localhost:8081` in that deployment.

## CI and Images

The GitHub Actions workflow in `.github/workflows/docker-publish.yml` runs `go test ./...` for pull requests and pushes Docker Hub images on `main` and `v1*` tags.

Published tags include developer tags such as `main.20260505.0148` for Flux image automation and semver release tags such as `1.0.0` for the WAC production overlay.

## Kubernetes

Kustomize manifests are under `deployments/kustomize`:

```bash
kubectl kustomize deployments/kustomize/install
kubectl kustomize deployments/kustomize/with-mongo
kubectl kustomize deployments/kustomize/components/with-gateway-api
```

Use `with-mongo` for a complete API + MongoDB deployment. The install manifest exposes the API service on Kubernetes port `80`, keeps the Go process on container port `8000`, and includes a Swagger UI sidecar exposed through `sarcoma-fasttrack-openapi-ui`. The optional `with-gateway-api` component adds the production HTTPRoute paths used by the root GitOps overlay.
