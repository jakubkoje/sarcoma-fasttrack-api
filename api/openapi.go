package api

import (
	_ "embed"
	"net/http"

	"github.com/gin-gonic/gin"
)

//go:embed sarcoma.openapi.yaml
var openapiSpec []byte

func HandleOpenAPI(c *gin.Context) {
	c.Data(http.StatusOK, "application/yaml; charset=utf-8", openapiSpec)
}
