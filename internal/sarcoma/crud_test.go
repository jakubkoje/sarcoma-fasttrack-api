package sarcoma

import (
	"net/http"
	"testing"
)

func TestAuthRegisterLogoutAndCRUDRoutes(t *testing.T) {
	router := testRouter()

	createdUser := requestJSON[UserRead](t, router, http.MethodPost, "/api/v1/auth/register", "", `{
		"email": "coordinator@example.test",
		"password": "coordinator",
		"role": "coordinator"
	}`, http.StatusCreated)
	if createdUser.ID == 0 || createdUser.Role != RoleCoordinator {
		t.Fatalf("unexpected registered user: %+v", createdUser)
	}

	coordinatorToken := loginToken(t, router, "coordinator@example.test", "coordinator")
	requestJSON[struct{}](t, router, http.MethodPost, "/api/v1/auth/logout", coordinatorToken, ``, http.StatusNoContent)

	adminToken := loginToken(t, router, "admin@admin.com", "admin")
	organization := requestJSON[OrganizationRead](t, router, http.MethodPost, "/api/v1/organizations", adminToken, `{
		"name": "Test centrum",
		"type_code": "prov",
		"address": "Testovaci 1",
		"contact": "+420111222333",
		"email": "centrum@example.test"
	}`, http.StatusCreated)
	if organization.ID == 0 || organization.Name == nil || *organization.Name != "Test centrum" {
		t.Fatalf("unexpected organization: %+v", organization)
	}

	updatedOrganization := requestJSON[OrganizationRead](t, router, http.MethodPut, "/api/v1/organizations/"+itoa(organization.ID), adminToken, `{
		"name": "Test centrum updated"
	}`, http.StatusOK)
	if updatedOrganization.Name == nil || *updatedOrganization.Name != "Test centrum updated" {
		t.Fatalf("organization was not updated: %+v", updatedOrganization)
	}

	orgName := requestJSON[struct {
		Name string `json:"name"`
	}](t, router, http.MethodGet, "/api/v1/organizations/"+itoa(organization.ID)+"/name", adminToken, ``, http.StatusOK)
	if orgName.Name != "Test centrum updated" {
		t.Fatalf("unexpected organization name: %+v", orgName)
	}

	patient := requestJSON[PatientRead](t, router, http.MethodPost, "/api/v1/patients", adminToken, `{
		"first_name": "Petr",
		"last_name": "Test",
		"address": "Pacientska 2",
		"birth_number": "770707/7777",
		"phone": "+420777777777",
		"managing_organization_id": `+itoa(organization.ID)+`
	}`, http.StatusCreated)
	if patient.ManagingOrganizationID == nil || *patient.ManagingOrganizationID != organization.ID {
		t.Fatalf("patient organization was not persisted: %+v", patient)
	}

	updatedPatient := requestJSON[PatientRead](t, router, http.MethodPut, "/api/v1/patients/"+itoa(patient.ID), adminToken, `{
		"first_name": "Petra",
		"phone": "+420888888888"
	}`, http.StatusOK)
	if updatedPatient.FirstName == nil || *updatedPatient.FirstName != "Petra" {
		t.Fatalf("patient was not updated: %+v", updatedPatient)
	}

	requestJSON[struct{}](t, router, http.MethodDelete, "/api/v1/patients/"+itoa(patient.ID), adminToken, ``, http.StatusNoContent)
	requestJSON[struct{}](t, router, http.MethodGet, "/api/v1/patients/"+itoa(patient.ID), adminToken, ``, http.StatusNotFound)

	requestJSON[struct{}](t, router, http.MethodDelete, "/api/v1/organizations/"+itoa(organization.ID), adminToken, ``, http.StatusNoContent)
	requestJSON[struct{}](t, router, http.MethodGet, "/api/v1/organizations/"+itoa(organization.ID), adminToken, ``, http.StatusNotFound)
}
