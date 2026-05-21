package sarcoma

import (
	"net/http"
	"sort"

	"github.com/gin-gonic/gin"
)

func (api *implUsersAPI) ListUsers(c *gin.Context) {
	api.store.mu.RLock()
	defer api.store.mu.RUnlock()
	result := make([]UserRead, 0, len(api.store.users))
	for _, user := range api.store.users {
		result = append(result, api.store.userRead(user))
	}
	sort.Slice(result, func(i, j int) bool { return result[i].ID < result[j].ID })
	c.JSON(http.StatusOK, result)
}

func (api *implUsersAPI) CreateUser(c *gin.Context) {
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

type validationError struct {
	status  int
	message string
}

func createUserLocked(store *Store, payload UserCreate) (storedUser, *validationError) {
	if _, exists := store.usersByEmail[payload.Email]; exists {
		return storedUser{}, &validationError{status: http.StatusBadRequest, message: "Email already registered"}
	}
	if payload.Role == RoleDoctor && payload.OrganizationID != nil {
		if _, found := store.organizations[*payload.OrganizationID]; !found {
			return storedUser{}, &validationError{status: http.StatusBadRequest, message: "Organization not found"}
		}
	}

	id := store.nextUserID
	store.nextUserID++
	salt := randomHex(8)
	fhirID := strPtr(store.randomFHIRID("prac"))
	user := storedUser{
		ID:           id,
		Email:        payload.Email,
		Role:         payload.Role,
		Salt:         salt,
		PasswordHash: hashPassword(payload.Password, salt),
		IsActive:     true,
	}
	if payload.Role == RoleDoctor || payload.Role == RoleSpecialist {
		user.FhirID = fhirID
		store.doctors[id] = storedDoctor{
			ID:             id,
			OrganizationID: payload.OrganizationID,
			FhirID:         fhirID,
		}
	}
	store.users[id] = user
	store.usersByEmail[user.Email] = id
	return user, nil
}
