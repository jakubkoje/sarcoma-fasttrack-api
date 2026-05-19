package sarcoma

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

func (api *implAuthAPI) Login(c *gin.Context) {
	var payload LoginRequest
	if !bindJSON(c, &payload) {
		return
	}
	user, ok := api.store.authenticate(payload.Email, payload.Password)
	if !ok {
		writeError(c, http.StatusUnauthorized, "Invalid credentials")
		return
	}
	c.JSON(http.StatusOK, TokenResponse{
		AccessToken: api.store.createAccessToken(user.Email),
		UserRole:    user.Role,
		TokenType:   "bearer",
	})
}

func (api *implAuthAPI) Register(c *gin.Context) {
	var payload UserCreate
	if !bindJSON(c, &payload) {
		return
	}
	api.store.mu.Lock()
	defer api.store.mu.Unlock()

	user, err := createUserLocked(api.store, payload)
	if err != nil {
		writeError(c, err.status, err.message)
		return
	}
	if !persistOrError(c, api.store) {
		return
	}
	c.JSON(http.StatusCreated, api.store.userRead(user))
}

func (api *implAuthAPI) Logout(c *gin.Context) {
	c.Status(http.StatusNoContent)
}
