package sarcoma

import (
	"net/http"
	"sort"
	"strconv"

	"github.com/gin-gonic/gin"
)

func (api *implPatientsAPI) ListPatients(c *gin.Context) {
	api.store.mu.RLock()
	defer api.store.mu.RUnlock()

	result := make([]PatientRead, 0, len(api.store.patients))
	for _, patient := range api.store.patients {
		result = append(result, patient.PatientRead)
	}
	sort.Slice(result, func(i, j int) bool { return result[i].ID < result[j].ID })
	c.JSON(http.StatusOK, result)
}

func (api *implPatientsAPI) CreatePatient(c *gin.Context) {
	var payload PatientCreate
	if !bindJSON(c, &payload) {
		return
	}

	api.store.mu.Lock()
	defer api.store.mu.Unlock()

	id := api.store.nextPatientID
	api.store.nextPatientID++
	fhirID := api.store.randomFHIRID("pat")
	if payload.FhirID != nil && *payload.FhirID != "" {
		fhirID = *payload.FhirID
	}
	managingOrgID := payload.ManagingOrgID
	if managingOrgID == nil {
		managingOrgID = payload.ManagingOrganizationID
	}
	patient := PatientRead{
		ID:                     id,
		FhirID:                 fhirID,
		FirstName:              strPtr(payload.FirstName),
		LastName:               strPtr(payload.LastName),
		Address:                strPtr(payload.Address),
		BirthNumber:            strPtr(payload.BirthNumber),
		Phone:                  strPtr(payload.Phone),
		Email:                  payload.Email,
		ManagingOrgID:          managingOrgID,
		IdentifierRC:           stringOr(payload.IdentifierRC, payload.BirthNumber),
		InsuranceCompanyCode:   payload.InsuranceCompanyCode,
		AddressText:            strPtr(payload.Address),
		AddressCity:            payload.AddressCity,
		AddressPostalCode:      payload.AddressPostalCode,
		AddressCountry:         payload.AddressCountry,
		FamilyName:             strPtr(payload.LastName),
		GivenName:              strPtr(payload.FirstName),
		BirthDate:              payload.BirthDate,
		Gender:                 payload.Gender,
		ManagingOrganizationID: managingOrgID,
	}
	api.store.patients[id] = storedPatient{PatientRead: patient}
	if !persistOrError(c, api.store) {
		return
	}
	c.JSON(http.StatusCreated, patient)
}

func (api *implPatientsAPI) GetPatient(c *gin.Context) {
	id, ok := intParam(c, "patientId")
	if !ok {
		return
	}
	api.store.mu.RLock()
	defer api.store.mu.RUnlock()
	patient, found := api.store.patients[id]
	if !found {
		writeError(c, http.StatusNotFound, "Patient not found")
		return
	}
	c.JSON(http.StatusOK, patient.PatientRead)
}

func (api *implPatientsAPI) UpdatePatient(c *gin.Context) {
	id, ok := intParam(c, "patientId")
	if !ok {
		return
	}
	var payload PatientUpdate
	if !bindJSON(c, &payload) {
		return
	}

	api.store.mu.Lock()
	defer api.store.mu.Unlock()
	patient, found := api.store.patients[id]
	if !found {
		writeError(c, http.StatusNotFound, "Patient not found")
		return
	}
	if payload.FhirID != nil {
		patient.FhirID = *payload.FhirID
	}
	if payload.FirstName != nil {
		patient.FirstName = payload.FirstName
		patient.GivenName = payload.FirstName
	}
	if payload.LastName != nil {
		patient.LastName = payload.LastName
		patient.FamilyName = payload.LastName
	}
	if payload.Address != nil {
		patient.Address = payload.Address
		patient.AddressText = payload.Address
	}
	if payload.BirthNumber != nil {
		patient.BirthNumber = payload.BirthNumber
		patient.IdentifierRC = payload.BirthNumber
	}
	if payload.Phone != nil {
		patient.Phone = payload.Phone
	}
	if payload.Email != nil {
		patient.Email = payload.Email
	}
	if payload.ManagingOrgID != nil {
		patient.ManagingOrgID = payload.ManagingOrgID
		patient.ManagingOrganizationID = payload.ManagingOrgID
	}
	if payload.ManagingOrganizationID != nil {
		patient.ManagingOrgID = payload.ManagingOrganizationID
		patient.ManagingOrganizationID = payload.ManagingOrganizationID
	}
	if payload.IdentifierRC != nil {
		patient.IdentifierRC = payload.IdentifierRC
	}
	if payload.InsuranceCompanyCode != nil {
		patient.InsuranceCompanyCode = payload.InsuranceCompanyCode
	}
	if payload.AddressCity != nil {
		patient.AddressCity = payload.AddressCity
	}
	if payload.AddressPostalCode != nil {
		patient.AddressPostalCode = payload.AddressPostalCode
	}
	if payload.AddressCountry != nil {
		patient.AddressCountry = payload.AddressCountry
	}
	if payload.BirthDate != nil {
		patient.BirthDate = payload.BirthDate
	}
	if payload.Gender != nil {
		patient.Gender = payload.Gender
	}
	api.store.patients[id] = patient
	if !persistOrError(c, api.store) {
		return
	}
	c.JSON(http.StatusOK, patient.PatientRead)
}

func (api *implPatientsAPI) DeletePatient(c *gin.Context) {
	id, ok := intParam(c, "patientId")
	if !ok {
		return
	}
	api.store.mu.Lock()
	defer api.store.mu.Unlock()
	if _, found := api.store.patients[id]; !found {
		writeError(c, http.StatusNotFound, "Patient not found")
		return
	}
	delete(api.store.patients, id)
	if !persistOrError(c, api.store) {
		return
	}
	c.Status(http.StatusNoContent)
}

func (api *implPatientsAPI) GetPatientName(c *gin.Context) {
	id, ok := intParam(c, "patientId")
	if !ok {
		return
	}
	api.store.mu.RLock()
	defer api.store.mu.RUnlock()
	patient, found := api.store.patients[id]
	if !found {
		writeError(c, http.StatusNotFound, "Patient not found")
		return
	}
	nameParts := []string{}
	if patient.FirstName != nil {
		nameParts = append(nameParts, *patient.FirstName)
	} else if patient.GivenName != nil {
		nameParts = append(nameParts, *patient.GivenName)
	}
	if patient.LastName != nil {
		nameParts = append(nameParts, *patient.LastName)
	} else if patient.FamilyName != nil {
		nameParts = append(nameParts, *patient.FamilyName)
	}
	if len(nameParts) == 0 {
		writeError(c, http.StatusNotFound, "Patient name not found")
		return
	}
	c.JSON(http.StatusOK, gin.H{"patient_id": id, "name": joinName(nameParts)})
}

func intParam(c *gin.Context, key string) (int, bool) {
	id, err := strconv.Atoi(c.Param(key))
	if err != nil {
		writeError(c, http.StatusBadRequest, "Invalid "+key)
		return 0, false
	}
	return id, true
}

func joinName(parts []string) string {
	result := ""
	for _, part := range parts {
		if part == "" {
			continue
		}
		if result != "" {
			result += " "
		}
		result += part
	}
	return result
}

func stringOr(value *string, fallback string) *string {
	if value != nil {
		return value
	}
	return strPtr(fallback)
}
