package sarcoma

import (
	"net/http"
	"sort"

	"github.com/gin-gonic/gin"
)

func (api *implOrganizationsAPI) ListOrganizations(c *gin.Context) {
	api.store.mu.RLock()
	defer api.store.mu.RUnlock()
	result := make([]OrganizationRead, 0, len(api.store.organizations))
	for _, organization := range api.store.organizations {
		result = append(result, organization.OrganizationRead)
	}
	sort.Slice(result, func(i, j int) bool { return result[i].ID < result[j].ID })
	c.JSON(http.StatusOK, result)
}

func (api *implOrganizationsAPI) CreateOrganization(c *gin.Context) {
	if _, ok := requireRole(c, RoleAdmin); !ok {
		return
	}
	var payload OrganizationCreate
	if !bindJSON(c, &payload) {
		return
	}
	if payload.Capacity != nil && *payload.Capacity < 0 {
		writeError(c, http.StatusBadRequest, "Capacity must be non-negative")
		return
	}
	api.store.mu.Lock()
	defer api.store.mu.Unlock()
	id := api.store.nextOrgID
	api.store.nextOrgID++
	fhirID := api.store.randomFHIRID("org")
	if payload.FhirID != nil && *payload.FhirID != "" {
		fhirID = *payload.FhirID
	}
	organization := OrganizationRead{
		ID:                id,
		FhirID:            fhirID,
		Name:              strPtr(payload.Name),
		TypeCode:          strPtr(payload.TypeCode),
		Address:           strPtr(payload.Address),
		Contact:           strPtr(payload.Contact),
		ICO:               payload.ICO,
		DIC:               payload.DIC,
		Email:             payload.Email,
		AddressCity:       payload.AddressCity,
		AddressPostalCode: payload.AddressPostalCode,
		AddressCountry:    payload.AddressCountry,
		Capacity:          payload.Capacity,
		Region:            payload.Region,
		CatchmentArea:     payload.CatchmentArea,
	}
	api.store.organizations[id] = storedOrganization{OrganizationRead: organization}
	if !persistOrError(c, api.store) {
		return
	}
	c.JSON(http.StatusCreated, organization)
}

func (api *implOrganizationsAPI) GetOrganization(c *gin.Context) {
	id, ok := intParam(c, "organizationId")
	if !ok {
		return
	}
	api.store.mu.RLock()
	defer api.store.mu.RUnlock()
	organization, found := api.store.organizations[id]
	if !found {
		writeError(c, http.StatusNotFound, "Organization not found")
		return
	}
	c.JSON(http.StatusOK, organization.OrganizationRead)
}

func (api *implOrganizationsAPI) UpdateOrganization(c *gin.Context) {
	id, ok := intParam(c, "organizationId")
	if !ok {
		return
	}
	if _, ok := requireRole(c, RoleAdmin); !ok {
		return
	}
	var payload OrganizationUpdate
	if !bindJSON(c, &payload) {
		return
	}
	if payload.Capacity != nil && *payload.Capacity < 0 {
		writeError(c, http.StatusBadRequest, "Capacity must be non-negative")
		return
	}
	api.store.mu.Lock()
	defer api.store.mu.Unlock()
	organization, found := api.store.organizations[id]
	if !found {
		writeError(c, http.StatusNotFound, "Organization not found")
		return
	}
	if payload.FhirID != nil {
		organization.FhirID = *payload.FhirID
	}
	if payload.Name != nil {
		organization.Name = payload.Name
	}
	if payload.TypeCode != nil {
		organization.TypeCode = payload.TypeCode
	}
	if payload.Address != nil {
		organization.Address = payload.Address
	}
	if payload.Contact != nil {
		organization.Contact = payload.Contact
	}
	if payload.ICO != nil {
		organization.ICO = payload.ICO
	}
	if payload.DIC != nil {
		organization.DIC = payload.DIC
	}
	if payload.Email != nil {
		organization.Email = payload.Email
	}
	if payload.AddressCity != nil {
		organization.AddressCity = payload.AddressCity
	}
	if payload.AddressPostalCode != nil {
		organization.AddressPostalCode = payload.AddressPostalCode
	}
	if payload.AddressCountry != nil {
		organization.AddressCountry = payload.AddressCountry
	}
	if payload.Capacity != nil {
		organization.Capacity = payload.Capacity
	}
	if payload.Region != nil {
		organization.Region = payload.Region
	}
	if payload.CatchmentArea != nil {
		organization.CatchmentArea = payload.CatchmentArea
	}
	api.store.organizations[id] = organization
	if !persistOrError(c, api.store) {
		return
	}
	c.JSON(http.StatusOK, organization.OrganizationRead)
}

func (api *implOrganizationsAPI) DeleteOrganization(c *gin.Context) {
	id, ok := intParam(c, "organizationId")
	if !ok {
		return
	}
	if _, ok := requireRole(c, RoleAdmin); !ok {
		return
	}
	api.store.mu.Lock()
	defer api.store.mu.Unlock()
	if _, found := api.store.organizations[id]; !found {
		writeError(c, http.StatusNotFound, "Organization not found")
		return
	}
	delete(api.store.organizations, id)
	if !persistOrError(c, api.store) {
		return
	}
	c.Status(http.StatusNoContent)
}

func (api *implOrganizationsAPI) GetOrganizationName(c *gin.Context) {
	id, ok := intParam(c, "organizationId")
	if !ok {
		return
	}
	api.store.mu.RLock()
	defer api.store.mu.RUnlock()
	organization, found := api.store.organizations[id]
	if !found {
		writeError(c, http.StatusNotFound, "Organization not found")
		return
	}
	if organization.Name == nil || *organization.Name == "" {
		writeError(c, http.StatusNotFound, "Organization name not found")
		return
	}
	c.JSON(http.StatusOK, gin.H{"organization_id": id, "name": *organization.Name})
}
