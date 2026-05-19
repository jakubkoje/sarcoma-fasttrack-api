package sarcoma

import "github.com/gin-gonic/gin"

type AuthAPI interface {
	Login(c *gin.Context)
	Register(c *gin.Context)
	Logout(c *gin.Context)
}

type implAuthAPI struct {
	store *Store
}

func NewAuthAPI(store *Store) AuthAPI {
	return &implAuthAPI{store: store}
}
