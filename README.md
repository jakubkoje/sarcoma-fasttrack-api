# Sarcoma FastTrack API

Minimal Go API for the early WAC deployment points.

## Run

```bash
go test ./...
go run ./cmd/sarcoma-fasttrack-api
```

Endpoints:

- `GET /health`
- `GET /api/message`
- `GET /openapi`

## Image

```bash
docker build -t jakubkoje/sarcoma-fasttrack-api:1.0.0 .
```

Create/push a `v1.0.0` release later so CI publishes `1.0.0`, then bump the GitOps `components/version-release` tag when needed.
