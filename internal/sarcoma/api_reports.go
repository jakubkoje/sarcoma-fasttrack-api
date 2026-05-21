package sarcoma

import "github.com/gin-gonic/gin"

type ReportsAPI interface {
	ListReports(c *gin.Context)
	CreateReport(c *gin.Context)
	GetReport(c *gin.Context)
	UpdateReport(c *gin.Context)
	DeleteReport(c *gin.Context)
	UpdateReportStatus(c *gin.Context)
	UpdateReportFeedback(c *gin.Context)
	GetClassification(c *gin.Context)
	Reclassify(c *gin.Context)
}

type implReportsAPI struct {
	store *Store
}

func NewReportsAPI(store *Store) ReportsAPI {
	return &implReportsAPI{store: store}
}
