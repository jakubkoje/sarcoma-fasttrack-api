package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"time"
)

type messageResponse struct {
	Message string `json:"message"`
	Service string `json:"service"`
	Time    string `json:"time"`
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = os.Getenv("SARCOMA_FASTTRACK_API_PORT")
	}
	if port == "" {
		port = "8000"
	}

	server := &http.Server{
		Addr:              ":" + port,
		Handler:           routes(),
		ReadHeaderTimeout: 5 * time.Second,
	}

	log.Printf("sarcoma-fasttrack-api listening on :%s", port)
	if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatal(err)
	}
}

func routes() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", jsonHandler(func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{
			"status":  "ok",
			"service": "sarcoma-fasttrack-api",
		})
	}))
	mux.HandleFunc("/api/message", jsonHandler(func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, messageResponse{
			Message: "Dummy backend communication works",
			Service: "sarcoma-fasttrack-api",
			Time:    time.Now().UTC().Format(time.RFC3339),
		})
	}))
	mux.HandleFunc("/openapi", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/yaml")
		_, _ = w.Write([]byte(openAPI))
	})
	return cors(mux)
}

func jsonHandler(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		next(w, r)
	}
}

func cors(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		next.ServeHTTP(w, r)
	})
}

func writeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(payload)
}

const openAPI = `openapi: 3.0.3
info:
  title: Sarcoma FastTrack API
  version: 1.0.0
paths:
  /health:
    get:
      responses:
        "200":
          description: API health
  /api/message:
    get:
      responses:
        "200":
          description: Dummy frontend-backend message
`
