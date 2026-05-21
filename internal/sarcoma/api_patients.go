package sarcoma

import "github.com/gin-gonic/gin"

type PatientsAPI interface {
	ListPatients(c *gin.Context)
	CreatePatient(c *gin.Context)
	GetPatient(c *gin.Context)
	UpdatePatient(c *gin.Context)
	DeletePatient(c *gin.Context)
	GetPatientName(c *gin.Context)
}

type implPatientsAPI struct {
	store *Store
}

func NewPatientsAPI(store *Store) PatientsAPI {
	return &implPatientsAPI{store: store}
}
