FROM golang:1.25-alpine AS build

WORKDIR /app
COPY go.mod ./
COPY cmd/ cmd/
RUN go test ./...
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o /sarcoma-fasttrack-api ./cmd/sarcoma-fasttrack-api

FROM scratch

COPY --from=build /sarcoma-fasttrack-api /sarcoma-fasttrack-api

ENV PORT=8000
EXPOSE 8000
ENTRYPOINT ["/sarcoma-fasttrack-api"]
