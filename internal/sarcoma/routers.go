package sarcoma

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

type Route struct {
	Name        string
	Method      string
	Pattern     string
	HandlerFunc gin.HandlerFunc
	Protected   bool
}

type ApiHandleFunctions struct {
	AuthAPI          AuthAPI
	PatientsAPI      PatientsAPI
	ReportsAPI       ReportsAPI
	OrganizationsAPI OrganizationsAPI
	UsersAPI         UsersAPI
	AuthMiddleware   gin.HandlerFunc
}

func NewRouter(handleFunctions ApiHandleFunctions) *gin.Engine {
	return NewRouterWithGinEngine(gin.Default(), handleFunctions)
}

func NewRouterWithGinEngine(router *gin.Engine, handleFunctions ApiHandleFunctions) *gin.Engine {
	for _, route := range getRoutes(handleFunctions) {
		handler := route.HandlerFunc
		if handler == nil {
			handler = DefaultHandleFunc
		}
		handlers := []gin.HandlerFunc{handler}
		if route.Protected && handleFunctions.AuthMiddleware != nil {
			handlers = []gin.HandlerFunc{handleFunctions.AuthMiddleware, handler}
		}
		switch route.Method {
		case http.MethodGet:
			router.GET(route.Pattern, handlers...)
		case http.MethodPost:
			router.POST(route.Pattern, handlers...)
		case http.MethodPut:
			router.PUT(route.Pattern, handlers...)
		case http.MethodPatch:
			router.PATCH(route.Pattern, handlers...)
		case http.MethodDelete:
			router.DELETE(route.Pattern, handlers...)
		}
	}
	return router
}

func DefaultHandleFunc(c *gin.Context) {
	c.String(http.StatusNotImplemented, "501 not implemented")
}

func getRoutes(handleFunctions ApiHandleFunctions) []Route {
	return []Route{
		{"Login", http.MethodPost, "/api/v1/auth/login", handleFunctions.AuthAPI.Login, false},
		{"Register", http.MethodPost, "/api/v1/auth/register", handleFunctions.AuthAPI.Register, false},
		{"Logout", http.MethodPost, "/api/v1/auth/logout", handleFunctions.AuthAPI.Logout, true},
		{"ListUsers", http.MethodGet, "/api/v1/users", handleFunctions.UsersAPI.ListUsers, true},
		{"CreateUser", http.MethodPost, "/api/v1/users", handleFunctions.UsersAPI.CreateUser, false},

		{"ListPatients", http.MethodGet, "/api/v1/patients", handleFunctions.PatientsAPI.ListPatients, true},
		{"CreatePatient", http.MethodPost, "/api/v1/patients", handleFunctions.PatientsAPI.CreatePatient, true},
		{"GetPatient", http.MethodGet, "/api/v1/patients/:patientId", handleFunctions.PatientsAPI.GetPatient, true},
		{"UpdatePatient", http.MethodPut, "/api/v1/patients/:patientId", handleFunctions.PatientsAPI.UpdatePatient, true},
		{"DeletePatient", http.MethodDelete, "/api/v1/patients/:patientId", handleFunctions.PatientsAPI.DeletePatient, true},
		{"GetPatientName", http.MethodGet, "/api/v1/patients/:patientId/name", handleFunctions.PatientsAPI.GetPatientName, true},

		{"ListReports", http.MethodGet, "/api/v1/reports", handleFunctions.ReportsAPI.ListReports, true},
		{"CreateReport", http.MethodPost, "/api/v1/reports", handleFunctions.ReportsAPI.CreateReport, true},
		{"GetReport", http.MethodGet, "/api/v1/reports/:reportId", handleFunctions.ReportsAPI.GetReport, true},
		{"UpdateReport", http.MethodPut, "/api/v1/reports/:reportId", handleFunctions.ReportsAPI.UpdateReport, true},
		{"DeleteReport", http.MethodDelete, "/api/v1/reports/:reportId", handleFunctions.ReportsAPI.DeleteReport, true},
		{"UpdateReportStatus", http.MethodPatch, "/api/v1/reports/:reportId/status", handleFunctions.ReportsAPI.UpdateReportStatus, true},
		{"UpdateReportFeedback", http.MethodPatch, "/api/v1/reports/:reportId/feedback", handleFunctions.ReportsAPI.UpdateReportFeedback, true},
		{"GetClassification", http.MethodGet, "/api/v1/reports/:reportId/classification", handleFunctions.ReportsAPI.GetClassification, true},
		{"Reclassify", http.MethodPost, "/api/v1/reports/:reportId/reclassify", handleFunctions.ReportsAPI.Reclassify, true},

		{"ListOrganizations", http.MethodGet, "/api/v1/organizations", handleFunctions.OrganizationsAPI.ListOrganizations, true},
		{"CreateOrganization", http.MethodPost, "/api/v1/organizations", handleFunctions.OrganizationsAPI.CreateOrganization, true},
		{"GetOrganization", http.MethodGet, "/api/v1/organizations/:organizationId", handleFunctions.OrganizationsAPI.GetOrganization, true},
		{"UpdateOrganization", http.MethodPut, "/api/v1/organizations/:organizationId", handleFunctions.OrganizationsAPI.UpdateOrganization, true},
		{"DeleteOrganization", http.MethodDelete, "/api/v1/organizations/:organizationId", handleFunctions.OrganizationsAPI.DeleteOrganization, true},
		{"GetOrganizationName", http.MethodGet, "/api/v1/organizations/:organizationId/name", handleFunctions.OrganizationsAPI.GetOrganizationName, true},
	}
}
