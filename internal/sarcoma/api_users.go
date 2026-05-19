package sarcoma

import "github.com/gin-gonic/gin"

type UsersAPI interface {
	ListUsers(c *gin.Context)
	CreateUser(c *gin.Context)
}

type implUsersAPI struct {
	store *Store
}

func NewUsersAPI(store *Store) UsersAPI {
	return &implUsersAPI{store: store}
}
