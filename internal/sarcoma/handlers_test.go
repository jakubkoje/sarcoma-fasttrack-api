package sarcoma

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
)

func TestAPIWorkflow(t *testing.T) {
	router := testRouter()
	token := loginToken(t, router, "admin@admin.com", "admin")

	patient := requestJSON[PatientRead](t, router, http.MethodPost, "/api/v1/patients", token, `{
		"first_name": "Marie",
		"last_name": "Dvořáková",
		"address": "Náměstí 789, Ostrava",
		"birth_number": "880303/9012",
		"phone": "+420555666777",
		"email": "marie.dvorakova@example.test"
	}`, http.StatusCreated)
	if patient.ID == 0 || patient.FhirID == "" {
		t.Fatalf("created patient is incomplete: %+v", patient)
	}

	report := requestJSON[ReportRead](t, router, http.MethodPost, "/api/v1/reports", token, `{
		"patient_id": `+itoa(patient.ID)+`,
		"doctor_id": 19,
		"target_organization_id": 14,
		"status": "DRAFT",
		"anamnesis": "Suspektní ložisko měkkých tkání",
		"note": "MRI: ložisko 4 cm"
	}`, http.StatusCreated)
	if report.Status != StatusDraft || report.PatientID != patient.ID {
		t.Fatalf("unexpected report response: %+v", report)
	}
	if report.Severity == nil || *report.Severity == "" {
		t.Fatalf("expected demo classification in report: %+v", report)
	}

	updated := requestJSON[ReportRead](t, router, http.MethodPatch, "/api/v1/reports/"+itoa(report.ID)+"/status", token, `{"status":"ACTIVE"}`, http.StatusOK)
	if updated.Status != StatusActive || updated.StatusCZ != StatusActive.Czech() {
		t.Fatalf("status was not updated: %+v", updated)
	}

	feedback := requestJSON[ReportRead](t, router, http.MethodPatch, "/api/v1/reports/"+itoa(report.ID)+"/feedback", token, `{"feedback_specialist":"Doplnit staging."}`, http.StatusOK)
	if feedback.FeedbackSpecialist == nil || *feedback.FeedbackSpecialist != "Doplnit staging." {
		t.Fatalf("feedback was not updated: %+v", feedback)
	}

	name := requestJSON[struct {
		Name string `json:"name"`
	}](t, router, http.MethodGet, "/api/v1/patients/"+itoa(patient.ID)+"/name", token, ``, http.StatusOK)
	if name.Name != "Marie Dvořáková" {
		t.Fatalf("unexpected patient name payload: %+v", name)
	}
}

func TestProtectedRoutesRequireBearerToken(t *testing.T) {
	router := testRouter()
	recorder := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodGet, "/api/v1/reports", nil)
	router.ServeHTTP(recorder, req)
	if recorder.Code != http.StatusUnauthorized {
		t.Fatalf("expected 401, got %d: %s", recorder.Code, recorder.Body.String())
	}
}

func TestDoctorOnlySeesOwnReports(t *testing.T) {
	router := testRouter()
	token := loginToken(t, router, "doctor@sft.local", "doctor")
	reports := requestJSON[[]ReportRead](t, router, http.MethodGet, "/api/v1/reports", token, ``, http.StatusOK)
	if len(reports) == 0 {
		t.Fatal("expected seeded doctor report")
	}
	for _, report := range reports {
		if report.DoctorID != 19 {
			t.Fatalf("doctor received report owned by another doctor: %+v", report)
		}
	}
}

func testRouter() *gin.Engine {
	return testRouterWithStore(NewStore())
}

func testRouterWithStore(store *Store) *gin.Engine {
	gin.SetMode(gin.TestMode)
	router := gin.New()
	NewRouterWithGinEngine(router, ApiHandleFunctions{
		AuthAPI:          NewAuthAPI(store),
		PatientsAPI:      NewPatientsAPI(store),
		ReportsAPI:       NewReportsAPI(store),
		OrganizationsAPI: NewOrganizationsAPI(store),
		UsersAPI:         NewUsersAPI(store),
		ArticlesAPI:      NewArticlesAPI(store),
		AuthMiddleware:   AuthMiddleware(store),
	})
	return router
}

func loginToken(t *testing.T, router *gin.Engine, email string, password string) string {
	t.Helper()
	response := requestJSON[TokenResponse](t, router, http.MethodPost, "/api/v1/auth/login", "", `{"email":"`+email+`","password":"`+password+`"}`, http.StatusOK)
	if response.AccessToken == "" {
		t.Fatal("login returned empty token")
	}
	return response.AccessToken
}

func requestJSON[T any](t *testing.T, router *gin.Engine, method string, path string, token string, body string, expectedStatus int) T {
	t.Helper()
	var reader *bytes.Reader
	if body == "" {
		reader = bytes.NewReader(nil)
	} else {
		reader = bytes.NewReader([]byte(body))
	}
	recorder := httptest.NewRecorder()
	req := httptest.NewRequest(method, path, reader)
	if body != "" {
		req.Header.Set("Content-Type", "application/json")
	}
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	router.ServeHTTP(recorder, req)
	if recorder.Code != expectedStatus {
		t.Fatalf("%s %s expected %d, got %d: %s", method, path, expectedStatus, recorder.Code, recorder.Body.String())
	}
	var decoded T
	if recorder.Body.Len() == 0 {
		return decoded
	}
	if err := json.Unmarshal(recorder.Body.Bytes(), &decoded); err != nil {
		t.Fatalf("cannot decode response %q: %v", recorder.Body.String(), err)
	}
	return decoded
}

func itoa(value int) string {
	if value == 0 {
		return "0"
	}
	digits := []byte{}
	for value > 0 {
		digits = append([]byte{byte('0' + value%10)}, digits...)
		value /= 10
	}
	return string(digits)
}
