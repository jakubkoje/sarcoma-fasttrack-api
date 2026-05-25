package sarcoma

import (
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
)

const currentUserKey = "current_user"

func AuthMiddleware(store *Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		token, ok := applicationToken(c)
		if !ok {
			writeError(c, http.StatusUnauthorized, "Missing bearer token")
			c.Abort()
			return
		}
		email, err := store.verifyAccessToken(token)
		if err != nil {
			writeError(c, http.StatusUnauthorized, "Invalid bearer token")
			c.Abort()
			return
		}
		user, ok := store.userByEmail(email)
		if !ok || !user.IsActive {
			writeError(c, http.StatusUnauthorized, "Invalid user")
			c.Abort()
			return
		}
		c.Set(currentUserKey, user)
		c.Next()
	}
}

func applicationToken(c *gin.Context) (string, bool) {
	if token := strings.TrimSpace(c.GetHeader("X-Sarcoma-Token")); token != "" {
		return strings.TrimPrefix(token, "Bearer "), true
	}

	header := strings.TrimSpace(c.GetHeader("Authorization"))
	if header == "" || !strings.HasPrefix(header, "Bearer ") {
		return "", false
	}
	return strings.TrimSpace(strings.TrimPrefix(header, "Bearer ")), true
}

func currentUser(c *gin.Context) (storedUser, bool) {
	value, ok := c.Get(currentUserKey)
	if !ok {
		return storedUser{}, false
	}
	user, ok := value.(storedUser)
	return user, ok
}

func hasRole(user storedUser, roles ...UserRole) bool {
	for _, role := range roles {
		if user.Role == role {
			return true
		}
	}
	return false
}

func requireRole(c *gin.Context, roles ...UserRole) (storedUser, bool) {
	user, ok := currentUser(c)
	if !ok {
		writeError(c, http.StatusUnauthorized, "Missing authenticated user")
		return storedUser{}, false
	}
	if !hasRole(user, roles...) {
		writeError(c, http.StatusForbidden, "Forbidden for role "+string(user.Role))
		return user, false
	}
	return user, true
}

func writeError(c *gin.Context, status int, message string) {
	c.JSON(status, gin.H{"detail": message, "message": message, "status": status})
}

func bindJSON(c *gin.Context, target interface{}) bool {
	if err := c.ShouldBindJSON(target); err != nil {
		writeError(c, http.StatusBadRequest, "Invalid request body: "+err.Error())
		return false
	}
	return true
}

func persistOrError(c *gin.Context, store *Store) bool {
	if err := store.persistLocked(); err != nil {
		writeError(c, http.StatusInternalServerError, "Cannot persist state: "+err.Error())
		return false
	}
	return true
}
