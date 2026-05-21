package sarcoma

import "github.com/gin-gonic/gin"

type ArticlesAPI interface {
	ListArticles(c *gin.Context)
	CreateArticle(c *gin.Context)
	GetArticle(c *gin.Context)
	UpdateArticle(c *gin.Context)
	DeleteArticle(c *gin.Context)
	UpdateArticleStatus(c *gin.Context)
}

type implArticlesAPI struct {
	store *Store
}

func NewArticlesAPI(store *Store) ArticlesAPI {
	return &implArticlesAPI{store: store}
}
