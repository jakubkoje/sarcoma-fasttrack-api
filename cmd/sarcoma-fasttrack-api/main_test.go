package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestMessageEndpoint(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/api/message", nil)
	res := httptest.NewRecorder()

	routes().ServeHTTP(res, req)

	if res.Code != http.StatusOK {
		t.Fatalf("expected status 200, got %d", res.Code)
	}

	var body messageResponse
	if err := json.NewDecoder(res.Body).Decode(&body); err != nil {
		t.Fatalf("decode response: %v", err)
	}
	if body.Message == "" || body.Service != "sarcoma-fasttrack-api" {
		t.Fatalf("unexpected body: %+v", body)
	}
}

func TestOpenAPIEndpoint(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/openapi", nil)
	res := httptest.NewRecorder()

	routes().ServeHTTP(res, req)

	if res.Code != http.StatusOK {
		t.Fatalf("expected status 200, got %d", res.Code)
	}
	if got := res.Body.String(); !contains(got, "/api/message:") {
		t.Fatalf("openapi does not include /api/message: %s", got)
	}
}

func contains(value string, needle string) bool {
	for i := 0; i+len(needle) <= len(value); i++ {
		if value[i:i+len(needle)] == needle {
			return true
		}
	}
	return false
}
