FROM golang:1.25 AS build

WORKDIR /app

COPY go.mod go.sum* ./
RUN go mod download

COPY api/ api/
COPY cmd/ cmd/
COPY internal/ internal/

RUN go test ./...
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o /sarcoma-api ./cmd/sarcoma-api-service

FROM scratch

LABEL org.opencontainers.image.title="Sarcom FastTrack API"
LABEL org.opencontainers.image.description="Go WebAPI for Sarcom FastTrack"

ENV SARCOMA_API_ENVIRONMENT=production
ENV SARCOMA_API_PORT=8000

COPY --from=build /sarcoma-api /sarcoma-api

EXPOSE 8000
ENTRYPOINT ["/sarcoma-api"]
