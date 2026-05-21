package sarcoma

import (
	"net/http"
	"sort"
	"time"

	"github.com/gin-gonic/gin"
)

func (api *implReportsAPI) ListReports(c *gin.Context) {
	user, _ := currentUser(c)
	api.store.mu.RLock()
	defer api.store.mu.RUnlock()

	result := make([]ReportRead, 0, len(api.store.reports))
	for _, report := range api.store.reports {
		if user.Role == RoleSpecialist && report.Status == StatusDraft {
			continue
		}
		if user.Role == RoleDoctor && report.DoctorID != user.ID {
			continue
		}
		report.StatusCZ = report.Status.Czech()
		result = append(result, report.ReportRead)
	}
	sort.Slice(result, func(i, j int) bool { return result[i].ID < result[j].ID })
	c.JSON(http.StatusOK, result)
}

func (api *implReportsAPI) CreateReport(c *gin.Context) {
	user, ok := requireRole(c, RoleDoctor, RoleAdmin)
	if !ok {
		return
	}
	var payload ReportCreate
	if !bindJSON(c, &payload) {
		return
	}
	if payload.Status != nil && !payload.Status.IsValid() {
		writeError(c, http.StatusBadRequest, "Invalid status: "+string(*payload.Status))
		return
	}
	api.store.mu.Lock()
	defer api.store.mu.Unlock()
	if _, found := api.store.patients[payload.PatientID]; !found {
		writeError(c, http.StatusNotFound, "Patient not found")
		return
	}
	if _, found := api.store.doctors[payload.DoctorID]; !found {
		writeError(c, http.StatusNotFound, "Doctor not found")
		return
	}
	if _, found := api.store.organizations[payload.TargetOrganizationID]; !found {
		writeError(c, http.StatusNotFound, "Organization not found")
		return
	}
	if user.Role == RoleDoctor && payload.DoctorID != user.ID {
		writeError(c, http.StatusForbidden, "Doctor can only create referrals attributed to themselves")
		return
	}
	status := StatusDraft
	if payload.Status != nil {
		status = *payload.Status
	}
	now := time.Now().UTC()
	id := api.store.nextReportID
	api.store.nextReportID++
	fhirID := api.store.randomFHIRID("rep")
	if payload.FhirID != nil && *payload.FhirID != "" {
		fhirID = *payload.FhirID
	}
	report := ReportRead{
		ID:                       id,
		FhirID:                   fhirID,
		PatientID:                payload.PatientID,
		DoctorID:                 payload.DoctorID,
		TargetOrganizationID:     payload.TargetOrganizationID,
		Status:                   status,
		StatusCZ:                 status.Czech(),
		AuthoredOn:               &now,
		Note:                     payload.Note,
		FeedbackSpecialist:       payload.FeedbackSpecialist,
		MKN10Code:                payload.MKN10Code,
		IsNewPatient:             payload.IsNewPatient,
		AnyImagingPerformed:      payload.AnyImagingPerformed,
		AdditionalImagingPlanned: payload.AdditionalImagingPlanned,
		AdditionalImagingNote:    payload.AdditionalImagingNote,
		Anamnesis:                payload.Anamnesis,
		FamilyHistory:            payload.FamilyHistory,
		AnticoagulantMedication:  payload.AnticoagulantMedication,
		AnticoagulantDetail:      payload.AnticoagulantDetail,
		HistologyPerformed:       payload.HistologyPerformed,
		HistologyDate:            payload.HistologyDate,
		HistologyResult:          payload.HistologyResult,
		Summary:                  payload.Summary,
		AttachmentPath:           payload.AttachmentPath,
		CreatedAt:                now,
		UpdatedAt:                now,
	}
	applyDemoClassification(&report)
	api.store.reports[id] = storedReport{ReportRead: report}
	if !persistOrError(c, api.store) {
		return
	}
	c.JSON(http.StatusCreated, report)
}

func (api *implReportsAPI) GetReport(c *gin.Context) {
	id, ok := intParam(c, "reportId")
	if !ok {
		return
	}
	api.store.mu.RLock()
	defer api.store.mu.RUnlock()
	report, found := api.store.reports[id]
	if !found {
		writeError(c, http.StatusNotFound, "Report not found")
		return
	}
	report.StatusCZ = report.Status.Czech()
	c.JSON(http.StatusOK, report.ReportRead)
}

func (api *implReportsAPI) UpdateReport(c *gin.Context) {
	id, ok := intParam(c, "reportId")
	if !ok {
		return
	}
	user, ok := currentUser(c)
	if !ok {
		writeError(c, http.StatusUnauthorized, "Missing authenticated user")
		return
	}
	var payload ReportUpdate
	if !bindJSON(c, &payload) {
		return
	}
	if payload.Status != nil && !payload.Status.IsValid() {
		writeError(c, http.StatusBadRequest, "Invalid status: "+string(*payload.Status))
		return
	}
	api.store.mu.Lock()
	defer api.store.mu.Unlock()
	report, found := api.store.reports[id]
	if !found {
		writeError(c, http.StatusNotFound, "Report not found")
		return
	}
	switch user.Role {
	case RoleAdmin:
	case RoleDoctor:
		if report.DoctorID != user.ID {
			writeError(c, http.StatusForbidden, "Doctor can only edit own referrals")
			return
		}
		if report.Status != StatusDraft {
			writeError(c, http.StatusConflict, "Referral can only be edited while in DRAFT")
			return
		}
		if payload.Status != nil && *payload.Status != StatusDraft {
			writeError(c, http.StatusForbidden, "Use PATCH /status to change referral status")
			return
		}
	default:
		writeError(c, http.StatusForbidden, "Forbidden for role "+string(user.Role))
		return
	}
	if payload.PatientID != nil {
		if _, found := api.store.patients[*payload.PatientID]; !found {
			writeError(c, http.StatusNotFound, "Patient not found")
			return
		}
		report.PatientID = *payload.PatientID
	}
	if payload.DoctorID != nil {
		if _, found := api.store.doctors[*payload.DoctorID]; !found {
			writeError(c, http.StatusNotFound, "Doctor not found")
			return
		}
		report.DoctorID = *payload.DoctorID
	}
	if payload.TargetOrganizationID != nil {
		if _, found := api.store.organizations[*payload.TargetOrganizationID]; !found {
			writeError(c, http.StatusNotFound, "Organization not found")
			return
		}
		report.TargetOrganizationID = *payload.TargetOrganizationID
	}
	applyReportUpdate(&report.ReportRead, payload)
	report.UpdatedAt = time.Now().UTC()
	report.StatusCZ = report.Status.Czech()
	api.store.reports[id] = report
	if !persistOrError(c, api.store) {
		return
	}
	c.JSON(http.StatusOK, report.ReportRead)
}

func (api *implReportsAPI) DeleteReport(c *gin.Context) {
	id, ok := intParam(c, "reportId")
	if !ok {
		return
	}
	user, ok := currentUser(c)
	if !ok {
		writeError(c, http.StatusUnauthorized, "Missing authenticated user")
		return
	}
	api.store.mu.Lock()
	defer api.store.mu.Unlock()
	report, found := api.store.reports[id]
	if !found {
		writeError(c, http.StatusNotFound, "Report not found")
		return
	}
	switch user.Role {
	case RoleAdmin:
	case RoleDoctor:
		if report.DoctorID != user.ID {
			writeError(c, http.StatusForbidden, "Doctor can only delete own referrals")
			return
		}
		if report.Status != StatusDraft && report.Status != StatusCancelled {
			writeError(c, http.StatusConflict, "Referral can only be deleted while in DRAFT or CANCELLED")
			return
		}
	default:
		writeError(c, http.StatusForbidden, "Forbidden for role "+string(user.Role))
		return
	}
	delete(api.store.reports, id)
	if !persistOrError(c, api.store) {
		return
	}
	c.Status(http.StatusNoContent)
}

func (api *implReportsAPI) UpdateReportStatus(c *gin.Context) {
	id, ok := intParam(c, "reportId")
	if !ok {
		return
	}
	user, ok := currentUser(c)
	if !ok {
		writeError(c, http.StatusUnauthorized, "Missing authenticated user")
		return
	}
	var payload ReportStatusUpdate
	if !bindJSON(c, &payload) {
		return
	}
	if !payload.Status.IsValid() {
		writeError(c, http.StatusBadRequest, "Invalid status: "+string(payload.Status))
		return
	}
	api.store.mu.Lock()
	defer api.store.mu.Unlock()
	report, found := api.store.reports[id]
	if !found {
		writeError(c, http.StatusNotFound, "Report not found")
		return
	}
	if err := authorizeStatusTransition(user, report.ReportRead, payload.Status); err != "" {
		writeError(c, http.StatusForbidden, err)
		return
	}
	report.Status = payload.Status
	report.StatusCZ = payload.Status.Czech()
	now := time.Now().UTC()
	report.UpdatedAt = now
	api.store.reports[id] = report
	if !persistOrError(c, api.store) {
		return
	}
	c.JSON(http.StatusOK, report.ReportRead)
}

func (api *implReportsAPI) UpdateReportFeedback(c *gin.Context) {
	id, ok := intParam(c, "reportId")
	if !ok {
		return
	}
	if _, ok := requireRole(c, RoleSpecialist, RoleAdmin); !ok {
		return
	}
	var payload ReportFeedbackUpdate
	if !bindJSON(c, &payload) {
		return
	}
	api.store.mu.Lock()
	defer api.store.mu.Unlock()
	report, found := api.store.reports[id]
	if !found {
		writeError(c, http.StatusNotFound, "Report not found")
		return
	}
	report.FeedbackSpecialist = strPtr(payload.FeedbackSpecialist)
	report.UpdatedAt = time.Now().UTC()
	api.store.reports[id] = report
	if !persistOrError(c, api.store) {
		return
	}
	c.JSON(http.StatusOK, report.ReportRead)
}

func authorizeStatusTransition(user storedUser, report ReportRead, target ReportStatus) string {
	if report.Status == StatusCancelled {
		return "Referral is cancelled and cannot transition further"
	}
	if target == report.Status {
		return ""
	}
	switch user.Role {
	case RoleAdmin:
		return ""
	case RoleDoctor:
		if report.DoctorID != user.ID {
			return "Doctor can only change status of own referrals"
		}
		switch report.Status {
		case StatusDraft:
			if target == StatusActive || target == StatusCancelled {
				return ""
			}
		case StatusActive:
			if target == StatusCancelled {
				return ""
			}
		}
		return "Doctor cannot move referral from " + string(report.Status) + " to " + string(target)
	case RoleSpecialist:
		if report.Status == StatusDraft {
			return "Specialist cannot act on a DRAFT referral"
		}
		switch target {
		case StatusActive, StatusSubmitted, StatusSent, StatusDone, StatusError, StatusCancelled:
			return ""
		}
		return "Specialist cannot move referral to " + string(target)
	}
	return "Forbidden for role " + string(user.Role)
}

func (api *implReportsAPI) GetClassification(c *gin.Context) {
	id, ok := intParam(c, "reportId")
	if !ok {
		return
	}
	api.store.mu.RLock()
	defer api.store.mu.RUnlock()
	report, found := api.store.reports[id]
	if !found {
		writeError(c, http.StatusNotFound, "Report not found")
		return
	}
	c.JSON(http.StatusOK, classificationPayload(report.ReportRead))
}

func (api *implReportsAPI) Reclassify(c *gin.Context) {
	id, ok := intParam(c, "reportId")
	if !ok {
		return
	}
	api.store.mu.Lock()
	defer api.store.mu.Unlock()
	report, found := api.store.reports[id]
	if !found {
		writeError(c, http.StatusNotFound, "Report not found")
		return
	}
	applyDemoClassification(&report.ReportRead)
	report.UpdatedAt = time.Now().UTC()
	api.store.reports[id] = report
	if !persistOrError(c, api.store) {
		return
	}
	c.JSON(http.StatusOK, classificationPayload(report.ReportRead))
}

func applyReportUpdate(report *ReportRead, payload ReportUpdate) {
	if payload.FhirID != nil {
		report.FhirID = *payload.FhirID
	}
	if payload.Status != nil {
		report.Status = *payload.Status
	}
	if payload.IsNewPatient != nil {
		report.IsNewPatient = payload.IsNewPatient
	}
	if payload.AnyImagingPerformed != nil {
		report.AnyImagingPerformed = payload.AnyImagingPerformed
	}
	if payload.AdditionalImagingPlanned != nil {
		report.AdditionalImagingPlanned = payload.AdditionalImagingPlanned
	}
	if payload.AdditionalImagingNote != nil {
		report.AdditionalImagingNote = payload.AdditionalImagingNote
	}
	if payload.Anamnesis != nil {
		report.Anamnesis = payload.Anamnesis
	}
	if payload.MKN10Code != nil {
		report.MKN10Code = payload.MKN10Code
	}
	if payload.FamilyHistory != nil {
		report.FamilyHistory = payload.FamilyHistory
	}
	if payload.AnticoagulantMedication != nil {
		report.AnticoagulantMedication = payload.AnticoagulantMedication
	}
	if payload.AnticoagulantDetail != nil {
		report.AnticoagulantDetail = payload.AnticoagulantDetail
	}
	if payload.HistologyPerformed != nil {
		report.HistologyPerformed = payload.HistologyPerformed
	}
	if payload.HistologyDate != nil {
		report.HistologyDate = payload.HistologyDate
	}
	if payload.HistologyResult != nil {
		report.HistologyResult = payload.HistologyResult
	}
	if payload.Summary != nil {
		report.Summary = payload.Summary
	}
	if payload.FeedbackSpecialist != nil {
		report.FeedbackSpecialist = payload.FeedbackSpecialist
	}
	if payload.AttachmentPath != nil {
		report.AttachmentPath = payload.AttachmentPath
	}
	if payload.Note != nil {
		report.Note = payload.Note
	}
}

func applyDemoClassification(report *ReportRead) {
	severityCode := (report.ID % 3) + 1
	confidence := 0.76 + float64(report.ID%20)/100
	report.SeverityCode = &severityCode
	report.Severity = strPtr(string(rune('0' + severityCode)))
	report.SeverityConfidence = &confidence
	report.OverallConfidence = &confidence
	report.Specialist = strPtr([]string{"Oncologist", "Surgeon", "Radiotherapist"}[report.ID%3])
	report.SpecialistConfidence = &confidence
}

func classificationPayload(report ReportRead) gin.H {
	return gin.H{
		"specialist":            report.Specialist,
		"specialist_confidence": report.SpecialistConfidence,
		"severity":              report.Severity,
		"severity_code":         report.SeverityCode,
		"severity_confidence":   report.SeverityConfidence,
		"overall_confidence":    report.OverallConfidence,
	}
}
