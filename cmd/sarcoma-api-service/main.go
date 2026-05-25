package main

import (
	"context"
	"log"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"

	"github.com/jakubkoje/sarcomfasttrack-be/api"
	"github.com/jakubkoje/sarcomfasttrack-be/internal/sarcoma"
)

func main() {
	port := getenv("SARCOMA_API_PORT", "8000")
	environment := os.Getenv("SARCOMA_API_ENVIRONMENT")
	if strings.EqualFold(environment, "production") {
		gin.SetMode(gin.ReleaseMode)
	}

	startupCtx, startupCancel := context.WithTimeout(context.Background(), envDurationSeconds("SARCOMA_API_STARTUP_TIMEOUT_SECONDS", 60))
	defer startupCancel()
	store, err := sarcoma.NewStoreFromEnv(startupCtx)
	if err != nil {
		log.Fatal(err)
	}
	defer func() {
		closeCtx, closeCancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer closeCancel()
		if err := store.Close(closeCtx); err != nil {
			log.Printf("cannot close store: %v", err)
		}
	}()
	storeKind := "memory"
	if os.Getenv("SARCOMA_API_STORE") == "mongo" || os.Getenv("SARCOMA_API_MONGODB_URI") != "" {
		storeKind = "mongo"
	}

	engine := gin.New()
	engine.Use(gin.Recovery())
	engine.Use(cors.New(cors.Config{
		AllowOrigins:     []string{"*"},
		AllowMethods:     []string{"GET", "PUT", "POST", "DELETE", "PATCH", "OPTIONS"},
		AllowHeaders:     []string{"Origin", "Authorization", "X-Sarcoma-Token", "Content-Type"},
		AllowCredentials: false,
		MaxAge:           12 * time.Hour,
	}))

	engine.GET("/", func(c *gin.Context) {
		c.JSON(200, gin.H{"name": "Sarcom FastTrack API", "openapi": "/openapi"})
	})
	engine.GET("/health/db", func(c *gin.Context) {
		if err := store.Ping(c.Request.Context()); err != nil {
			c.JSON(503, gin.H{"status": "error", "store": storeKind, "detail": err.Error()})
			return
		}
		c.JSON(200, gin.H{"status": "ok", "store": storeKind})
	})
	engine.GET("/openapi", api.HandleOpenAPI)

	handleFunctions := sarcoma.ApiHandleFunctions{
		AuthAPI:          sarcoma.NewAuthAPI(store),
		PatientsAPI:      sarcoma.NewPatientsAPI(store),
		ReportsAPI:       sarcoma.NewReportsAPI(store),
		OrganizationsAPI: sarcoma.NewOrganizationsAPI(store),
		UsersAPI:         sarcoma.NewUsersAPI(store),
		ArticlesAPI:      sarcoma.NewArticlesAPI(store),
		AuthMiddleware:   sarcoma.AuthMiddleware(store),
	}
	sarcoma.NewRouterWithGinEngine(engine, handleFunctions)

	serverAddr := ":" + port
	log.Printf("Sarcom FastTrack API listening on %s", serverAddr)
	if err := engine.Run(serverAddr); err != nil && err != context.Canceled {
		log.Fatal(err)
	}
}

func getenv(key string, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}

func envDurationSeconds(key string, fallback int) time.Duration {
	value := getenv(key, "")
	if value == "" {
		return time.Duration(fallback) * time.Second
	}
	seconds, err := strconv.Atoi(value)
	if err != nil || seconds <= 0 {
		return time.Duration(fallback) * time.Second
	}
	return time.Duration(seconds) * time.Second
}
