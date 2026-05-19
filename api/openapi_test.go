package api

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/gin-gonic/gin"
)

func TestHandleOpenAPI(t *testing.T) {
	gin.SetMode(gin.TestMode)
	router := gin.New()
	router.GET("/openapi", HandleOpenAPI)

	recorder := httptest.NewRecorder()
	request := httptest.NewRequest(http.MethodGet, "/openapi", nil)
	router.ServeHTTP(recorder, request)

	if recorder.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", recorder.Code)
	}
	contentType := recorder.Header().Get("Content-Type")
	if !strings.Contains(contentType, "application/yaml") {
		t.Fatalf("expected application/yaml content type, got %q", contentType)
	}

	spec := recorder.Body.String()
	required := []string{
		"openapi: 3.0.3",
		"/api/v1/auth/login:",
		"/api/v1/reports/{reportId}/classification:",
		"/health/db:",
		"operationId: login",
		"bearerAuth:",
		"components:",
		"schemas:",
		"responses:",
	}
	for _, needle := range required {
		if !strings.Contains(spec, needle) {
			t.Fatalf("OpenAPI spec does not contain %q", needle)
		}
	}

	assertEveryOperationHasResponses(t, spec)
}

func assertEveryOperationHasResponses(t *testing.T, spec string) {
	t.Helper()
	methods := map[string]bool{
		"get": true, "post": true, "put": true, "patch": true, "delete": true,
	}
	lines := strings.Split(spec, "\n")
	for index, line := range lines {
		trimmed := strings.TrimSpace(line)
		method := strings.TrimSuffix(trimmed, ":")
		if !strings.HasPrefix(line, "    ") || strings.HasPrefix(line, "      ") || !methods[method] {
			continue
		}

		hasResponses := false
		for next := index + 1; next < len(lines); next++ {
			nextLine := lines[next]
			if strings.HasPrefix(nextLine, "    ") && !strings.HasPrefix(nextLine, "      ") {
				break
			}
			if strings.TrimSpace(nextLine) == "responses:" {
				hasResponses = true
				break
			}
		}
		if !hasResponses {
			t.Fatalf("OpenAPI operation %s on line %d has no responses block", method, index+1)
		}
	}
}
