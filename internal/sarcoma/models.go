package sarcoma

import "time"

type UserRole string

const (
	RoleAdmin       UserRole = "admin"
	RoleDoctor      UserRole = "doctor"
	RoleSpecialist  UserRole = "specialist"
	RoleCoordinator UserRole = "coordinator"
)

type ReportStatus string

const (
	StatusDraft     ReportStatus = "DRAFT"
	StatusActive    ReportStatus = "ACTIVE"
	StatusSubmitted ReportStatus = "SUBMITTED"
	StatusSent      ReportStatus = "SENT"
	StatusDone      ReportStatus = "DONE"
	StatusError     ReportStatus = "ERROR"
	StatusCancelled ReportStatus = "CANCELLED"
)

func (s ReportStatus) Czech() string {
	switch s {
	case StatusDraft:
		return "Draft"
	case StatusActive:
		return "Active"
	case StatusSubmitted:
		return "Submitted"
	case StatusSent:
		return "Sent"
	case StatusDone:
		return "Done"
	case StatusError:
		return "Error"
	case StatusCancelled:
		return "Cancelled"
	default:
		return string(s)
	}
}

func (s ReportStatus) IsValid() bool {
	switch s {
	case StatusDraft, StatusActive, StatusSubmitted, StatusSent, StatusDone, StatusError, StatusCancelled:
		return true
	}
	return false
}

type ArticleStatus string

const (
	ArticleDraft     ArticleStatus = "DRAFT"
	ArticlePublished ArticleStatus = "PUBLISHED"
	ArticleArchived  ArticleStatus = "ARCHIVED"
)

func (s ArticleStatus) IsValid() bool {
	switch s {
	case ArticleDraft, ArticlePublished, ArticleArchived:
		return true
	}
	return false
}

type LoginRequest struct {
	Email    string `json:"email" binding:"required"`
	Password string `json:"password" binding:"required"`
}

type TokenResponse struct {
	AccessToken string   `json:"access_token"`
	UserRole    UserRole `json:"user_role"`
	TokenType   string   `json:"token_type"`
}

type UserCreate struct {
	Email          string   `json:"email" binding:"required"`
	Password       string   `json:"password" binding:"required"`
	Role           UserRole `json:"role" binding:"required"`
	OrganizationID *int     `json:"organization_id,omitempty"`
}

type UserRead struct {
	ID       int      `json:"id"`
	Email    string   `json:"email"`
	IsActive bool     `json:"is_active"`
	Role     UserRole `json:"role"`
	FhirID   *string  `json:"fhir_id,omitempty"`
}

type PatientCreate struct {
	FhirID                 *string `json:"fhir_id,omitempty"`
	FirstName              string  `json:"first_name" binding:"required"`
	LastName               string  `json:"last_name" binding:"required"`
	Address                string  `json:"address" binding:"required"`
	BirthNumber            string  `json:"birth_number" binding:"required"`
	Phone                  string  `json:"phone" binding:"required"`
	Email                  *string `json:"email,omitempty"`
	ManagingOrgID          *int    `json:"managing_org_id,omitempty"`
	IdentifierRC           *string `json:"identifier_rc,omitempty"`
	InsuranceCompanyCode   *string `json:"insurance_company_code,omitempty"`
	AddressCity            *string `json:"address_city,omitempty"`
	AddressPostalCode      *string `json:"address_postal_code,omitempty"`
	AddressCountry         *string `json:"address_country,omitempty"`
	BirthDate              *string `json:"birth_date,omitempty"`
	Gender                 *string `json:"gender,omitempty"`
	ManagingOrganizationID *int    `json:"managing_organization_id,omitempty"`
}

type PatientUpdate struct {
	FhirID                 *string `json:"fhir_id,omitempty"`
	FirstName              *string `json:"first_name,omitempty"`
	LastName               *string `json:"last_name,omitempty"`
	Address                *string `json:"address,omitempty"`
	BirthNumber            *string `json:"birth_number,omitempty"`
	Phone                  *string `json:"phone,omitempty"`
	Email                  *string `json:"email,omitempty"`
	ManagingOrgID          *int    `json:"managing_org_id,omitempty"`
	IdentifierRC           *string `json:"identifier_rc,omitempty"`
	InsuranceCompanyCode   *string `json:"insurance_company_code,omitempty"`
	AddressCity            *string `json:"address_city,omitempty"`
	AddressPostalCode      *string `json:"address_postal_code,omitempty"`
	AddressCountry         *string `json:"address_country,omitempty"`
	BirthDate              *string `json:"birth_date,omitempty"`
	Gender                 *string `json:"gender,omitempty"`
	ManagingOrganizationID *int    `json:"managing_organization_id,omitempty"`
}

type PatientRead struct {
	ID                     int     `json:"id"`
	FhirID                 string  `json:"fhir_id"`
	FirstName              *string `json:"first_name,omitempty"`
	LastName               *string `json:"last_name,omitempty"`
	Address                *string `json:"address,omitempty"`
	BirthNumber            *string `json:"birth_number,omitempty"`
	Phone                  *string `json:"phone,omitempty"`
	Email                  *string `json:"email,omitempty"`
	ManagingOrgID          *int    `json:"managing_org_id,omitempty"`
	IdentifierRC           *string `json:"identifier_rc,omitempty"`
	InsuranceCompanyCode   *string `json:"insurance_company_code,omitempty"`
	AddressText            *string `json:"address_text,omitempty"`
	AddressCity            *string `json:"address_city,omitempty"`
	AddressPostalCode      *string `json:"address_postal_code,omitempty"`
	AddressCountry         *string `json:"address_country,omitempty"`
	FamilyName             *string `json:"family_name,omitempty"`
	GivenName              *string `json:"given_name,omitempty"`
	BirthDate              *string `json:"birth_date,omitempty"`
	Gender                 *string `json:"gender,omitempty"`
	ManagingOrganizationID *int    `json:"managing_organization_id,omitempty"`
}

type OrganizationCreate struct {
	FhirID            *string `json:"fhir_id,omitempty"`
	Name              string  `json:"name" binding:"required"`
	TypeCode          string  `json:"type_code" binding:"required"`
	Address           string  `json:"address" binding:"required"`
	Contact           string  `json:"contact" binding:"required"`
	ICO               *string `json:"ico,omitempty"`
	DIC               *string `json:"dic,omitempty"`
	Email             *string `json:"email,omitempty"`
	AddressCity       *string `json:"address_city,omitempty"`
	AddressPostalCode *string `json:"address_postal_code,omitempty"`
	AddressCountry    *string `json:"address_country,omitempty"`
	Capacity          *int    `json:"capacity,omitempty"`
	Region            *string `json:"region,omitempty"`
	CatchmentArea     *string `json:"catchment_area,omitempty"`
}

type OrganizationUpdate struct {
	FhirID            *string `json:"fhir_id,omitempty"`
	Name              *string `json:"name,omitempty"`
	TypeCode          *string `json:"type_code,omitempty"`
	Address           *string `json:"address,omitempty"`
	Contact           *string `json:"contact,omitempty"`
	ICO               *string `json:"ico,omitempty"`
	DIC               *string `json:"dic,omitempty"`
	Email             *string `json:"email,omitempty"`
	AddressCity       *string `json:"address_city,omitempty"`
	AddressPostalCode *string `json:"address_postal_code,omitempty"`
	AddressCountry    *string `json:"address_country,omitempty"`
	Capacity          *int    `json:"capacity,omitempty"`
	Region            *string `json:"region,omitempty"`
	CatchmentArea     *string `json:"catchment_area,omitempty"`
}

type OrganizationRead struct {
	ID                int     `json:"id"`
	FhirID            string  `json:"fhir_id"`
	Name              *string `json:"name,omitempty"`
	TypeCode          *string `json:"type_code,omitempty"`
	Address           *string `json:"address,omitempty"`
	Contact           *string `json:"contact,omitempty"`
	ICO               *string `json:"ico,omitempty"`
	DIC               *string `json:"dic,omitempty"`
	Email             *string `json:"email,omitempty"`
	AddressCity       *string `json:"address_city,omitempty"`
	AddressPostalCode *string `json:"address_postal_code,omitempty"`
	AddressCountry    *string `json:"address_country,omitempty"`
	Capacity          *int    `json:"capacity,omitempty"`
	Region            *string `json:"region,omitempty"`
	CatchmentArea     *string `json:"catchment_area,omitempty"`
}

type ReportCreate struct {
	FhirID                   *string       `json:"fhir_id,omitempty"`
	PatientID                int           `json:"patient_id" binding:"required"`
	DoctorID                 int           `json:"doctor_id" binding:"required"`
	TargetOrganizationID     int           `json:"target_organization_id" binding:"required"`
	Status                   *ReportStatus `json:"status,omitempty"`
	IsNewPatient             *bool         `json:"is_new_patient,omitempty"`
	AnyImagingPerformed      *bool         `json:"any_imaging_performed,omitempty"`
	AdditionalImagingPlanned *bool         `json:"additional_imaging_planned,omitempty"`
	AdditionalImagingNote    *string       `json:"additional_imaging_note,omitempty"`
	Anamnesis                *string       `json:"anamnesis,omitempty"`
	MKN10Code                *string       `json:"mkn10_code,omitempty"`
	FamilyHistory            *string       `json:"family_history,omitempty"`
	AnticoagulantMedication  *bool         `json:"anticoagulant_medication,omitempty"`
	AnticoagulantDetail      *string       `json:"anticoagulant_detail,omitempty"`
	HistologyPerformed       *bool         `json:"histology_performed,omitempty"`
	HistologyDate            *string       `json:"histology_date,omitempty"`
	HistologyResult          *string       `json:"histology_result,omitempty"`
	Summary                  *string       `json:"summary,omitempty"`
	FeedbackSpecialist       *string       `json:"feedback_specialist,omitempty"`
	AttachmentPath           *string       `json:"attachment_path,omitempty"`
	Note                     *string       `json:"note,omitempty"`
}

type ReportUpdate struct {
	FhirID                   *string       `json:"fhir_id,omitempty"`
	PatientID                *int          `json:"patient_id,omitempty"`
	DoctorID                 *int          `json:"doctor_id,omitempty"`
	TargetOrganizationID     *int          `json:"target_organization_id,omitempty"`
	Status                   *ReportStatus `json:"status,omitempty"`
	IsNewPatient             *bool         `json:"is_new_patient,omitempty"`
	AnyImagingPerformed      *bool         `json:"any_imaging_performed,omitempty"`
	AdditionalImagingPlanned *bool         `json:"additional_imaging_planned,omitempty"`
	AdditionalImagingNote    *string       `json:"additional_imaging_note,omitempty"`
	Anamnesis                *string       `json:"anamnesis,omitempty"`
	MKN10Code                *string       `json:"mkn10_code,omitempty"`
	FamilyHistory            *string       `json:"family_history,omitempty"`
	AnticoagulantMedication  *bool         `json:"anticoagulant_medication,omitempty"`
	AnticoagulantDetail      *string       `json:"anticoagulant_detail,omitempty"`
	HistologyPerformed       *bool         `json:"histology_performed,omitempty"`
	HistologyDate            *string       `json:"histology_date,omitempty"`
	HistologyResult          *string       `json:"histology_result,omitempty"`
	Summary                  *string       `json:"summary,omitempty"`
	FeedbackSpecialist       *string       `json:"feedback_specialist,omitempty"`
	AttachmentPath           *string       `json:"attachment_path,omitempty"`
	Note                     *string       `json:"note,omitempty"`
}

type ReportStatusUpdate struct {
	Status ReportStatus `json:"status" binding:"required"`
}

type ReportFeedbackUpdate struct {
	FeedbackSpecialist string `json:"feedback_specialist" binding:"required"`
}

type ReportRead struct {
	ID                       int          `json:"id"`
	FhirID                   string       `json:"fhir_id,omitempty"`
	PatientID                int          `json:"patient_id"`
	DoctorID                 int          `json:"doctor_id"`
	TargetOrganizationID     int          `json:"target_organization_id"`
	Status                   ReportStatus `json:"status"`
	StatusCZ                 string       `json:"status_cz"`
	AuthoredOn               *time.Time   `json:"authored_on,omitempty"`
	Note                     *string      `json:"note,omitempty"`
	FeedbackSpecialist       *string      `json:"feedback_specialist,omitempty"`
	MKN10Code                *string      `json:"mkn10_code,omitempty"`
	IsNewPatient             *bool        `json:"is_new_patient,omitempty"`
	AnyImagingPerformed      *bool        `json:"any_imaging_performed,omitempty"`
	AdditionalImagingPlanned *bool        `json:"additional_imaging_planned,omitempty"`
	AdditionalImagingNote    *string      `json:"additional_imaging_note,omitempty"`
	Anamnesis                *string      `json:"anamnesis,omitempty"`
	FamilyHistory            *string      `json:"family_history,omitempty"`
	AnticoagulantMedication  *bool        `json:"anticoagulant_medication,omitempty"`
	AnticoagulantDetail      *string      `json:"anticoagulant_detail,omitempty"`
	HistologyPerformed       *bool        `json:"histology_performed,omitempty"`
	HistologyDate            *string      `json:"histology_date,omitempty"`
	HistologyResult          *string      `json:"histology_result,omitempty"`
	Summary                  *string      `json:"summary,omitempty"`
	AttachmentPath           *string      `json:"attachment_path,omitempty"`
	CreatedAt                time.Time    `json:"created_at"`
	UpdatedAt                time.Time    `json:"updated_at"`
	Specialist               *string      `json:"specialist,omitempty"`
	SpecialistConfidence     *float64     `json:"specialist_confidence,omitempty"`
	Severity                 *string      `json:"severity,omitempty"`
	SeverityCode             *int         `json:"severity_code,omitempty"`
	SeverityConfidence       *float64     `json:"severity_confidence,omitempty"`
	OverallConfidence        *float64     `json:"overall_confidence,omitempty"`
}

type ArticleCreate struct {
	Title            string  `json:"title" binding:"required"`
	Summary          string  `json:"summary" binding:"required"`
	Body             string  `json:"body" binding:"required"`
	Category         *string `json:"category,omitempty"`
	ImageURL         *string `json:"image_url,omitempty"`
	AuthorName       *string `json:"author_name,omitempty"`
	AuthorAvatarURL  *string `json:"author_avatar_url,omitempty"`
	ReadTimeMinutes  *int    `json:"read_time_minutes,omitempty"`
}

type ArticleUpdate struct {
	Title            *string `json:"title,omitempty"`
	Summary          *string `json:"summary,omitempty"`
	Body             *string `json:"body,omitempty"`
	Category         *string `json:"category,omitempty"`
	ImageURL         *string `json:"image_url,omitempty"`
	AuthorName       *string `json:"author_name,omitempty"`
	AuthorAvatarURL  *string `json:"author_avatar_url,omitempty"`
	ReadTimeMinutes  *int    `json:"read_time_minutes,omitempty"`
}

type ArticleStatusUpdate struct {
	Status ArticleStatus `json:"status" binding:"required"`
}

type ArticleRead struct {
	ID              int           `json:"id"`
	Title           string        `json:"title"`
	Summary         string        `json:"summary"`
	Body            string        `json:"body"`
	Category        *string       `json:"category,omitempty"`
	ImageURL        *string       `json:"image_url,omitempty"`
	AuthorID        int           `json:"author_id"`
	AuthorName      *string       `json:"author_name,omitempty"`
	AuthorAvatarURL *string       `json:"author_avatar_url,omitempty"`
	ReadTimeMinutes *int          `json:"read_time_minutes,omitempty"`
	Status          ArticleStatus `json:"status"`
	PublishedAt     *time.Time    `json:"published_at,omitempty"`
	CreatedAt       time.Time     `json:"created_at"`
	UpdatedAt       time.Time     `json:"updated_at"`
}
