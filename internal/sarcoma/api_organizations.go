package sarcoma

import "github.com/gin-gonic/gin"

type OrganizationsAPI interface {
	ListOrganizations(c *gin.Context)
	CreateOrganization(c *gin.Context)
	GetOrganization(c *gin.Context)
	UpdateOrganization(c *gin.Context)
	DeleteOrganization(c *gin.Context)
	GetOrganizationName(c *gin.Context)
}

type implOrganizationsAPI struct {
	store *Store
}

func NewOrganizationsAPI(store *Store) OrganizationsAPI {
	return &implOrganizationsAPI{store: store}
}
