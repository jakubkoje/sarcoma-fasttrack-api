package sarcoma

import (
	"net/http"
	"sort"
	"time"

	"github.com/gin-gonic/gin"
)

func (api *implArticlesAPI) ListArticles(c *gin.Context) {
	user, _ := currentUser(c)
	api.store.mu.RLock()
	defer api.store.mu.RUnlock()
	result := make([]ArticleRead, 0, len(api.store.articles))
	for _, article := range api.store.articles {
		if !canViewArticle(user, article.ArticleRead) {
			continue
		}
		result = append(result, article.ArticleRead)
	}
	sort.Slice(result, func(i, j int) bool {
		return result[i].ID > result[j].ID
	})
	c.JSON(http.StatusOK, result)
}

func (api *implArticlesAPI) GetArticle(c *gin.Context) {
	id, ok := intParam(c, "articleId")
	if !ok {
		return
	}
	user, _ := currentUser(c)
	api.store.mu.RLock()
	defer api.store.mu.RUnlock()
	article, found := api.store.articles[id]
	if !found {
		writeError(c, http.StatusNotFound, "Article not found")
		return
	}
	if !canViewArticle(user, article.ArticleRead) {
		writeError(c, http.StatusNotFound, "Article not found")
		return
	}
	c.JSON(http.StatusOK, article.ArticleRead)
}

func (api *implArticlesAPI) CreateArticle(c *gin.Context) {
	user, ok := requireRole(c, RoleCoordinator, RoleAdmin)
	if !ok {
		return
	}
	var payload ArticleCreate
	if !bindJSON(c, &payload) {
		return
	}
	if payload.ReadTimeMinutes != nil && *payload.ReadTimeMinutes < 0 {
		writeError(c, http.StatusBadRequest, "read_time_minutes must be non-negative")
		return
	}
	api.store.mu.Lock()
	defer api.store.mu.Unlock()
	now := time.Now().UTC()
	id := api.store.nextArticleID
	api.store.nextArticleID++
	article := ArticleRead{
		ID:              id,
		Title:           payload.Title,
		Summary:         payload.Summary,
		Body:            payload.Body,
		Category:        payload.Category,
		ImageURL:        payload.ImageURL,
		AuthorID:        user.ID,
		AuthorName:      payload.AuthorName,
		AuthorAvatarURL: payload.AuthorAvatarURL,
		ReadTimeMinutes: payload.ReadTimeMinutes,
		Status:          ArticleDraft,
		CreatedAt:       now,
		UpdatedAt:       now,
	}
	api.store.articles[id] = storedArticle{ArticleRead: article}
	if !persistOrError(c, api.store) {
		return
	}
	c.JSON(http.StatusCreated, article)
}

func (api *implArticlesAPI) UpdateArticle(c *gin.Context) {
	id, ok := intParam(c, "articleId")
	if !ok {
		return
	}
	user, ok := requireRole(c, RoleCoordinator, RoleAdmin)
	if !ok {
		return
	}
	var payload ArticleUpdate
	if !bindJSON(c, &payload) {
		return
	}
	if payload.ReadTimeMinutes != nil && *payload.ReadTimeMinutes < 0 {
		writeError(c, http.StatusBadRequest, "read_time_minutes must be non-negative")
		return
	}
	api.store.mu.Lock()
	defer api.store.mu.Unlock()
	article, found := api.store.articles[id]
	if !found {
		writeError(c, http.StatusNotFound, "Article not found")
		return
	}
	if user.Role == RoleCoordinator && article.AuthorID != user.ID {
		writeError(c, http.StatusForbidden, "Coordinator can only edit own articles")
		return
	}
	if payload.Title != nil {
		article.Title = *payload.Title
	}
	if payload.Summary != nil {
		article.Summary = *payload.Summary
	}
	if payload.Body != nil {
		article.Body = *payload.Body
	}
	if payload.Category != nil {
		article.Category = payload.Category
	}
	if payload.ImageURL != nil {
		article.ImageURL = payload.ImageURL
	}
	if payload.AuthorName != nil {
		article.AuthorName = payload.AuthorName
	}
	if payload.AuthorAvatarURL != nil {
		article.AuthorAvatarURL = payload.AuthorAvatarURL
	}
	if payload.ReadTimeMinutes != nil {
		article.ReadTimeMinutes = payload.ReadTimeMinutes
	}
	article.UpdatedAt = time.Now().UTC()
	api.store.articles[id] = article
	if !persistOrError(c, api.store) {
		return
	}
	c.JSON(http.StatusOK, article.ArticleRead)
}

func (api *implArticlesAPI) DeleteArticle(c *gin.Context) {
	id, ok := intParam(c, "articleId")
	if !ok {
		return
	}
	user, ok := requireRole(c, RoleCoordinator, RoleAdmin)
	if !ok {
		return
	}
	api.store.mu.Lock()
	defer api.store.mu.Unlock()
	article, found := api.store.articles[id]
	if !found {
		writeError(c, http.StatusNotFound, "Article not found")
		return
	}
	if user.Role == RoleCoordinator && article.AuthorID != user.ID {
		writeError(c, http.StatusForbidden, "Coordinator can only delete own articles")
		return
	}
	delete(api.store.articles, id)
	if !persistOrError(c, api.store) {
		return
	}
	c.Status(http.StatusNoContent)
}

func (api *implArticlesAPI) UpdateArticleStatus(c *gin.Context) {
	id, ok := intParam(c, "articleId")
	if !ok {
		return
	}
	user, ok := requireRole(c, RoleCoordinator, RoleAdmin)
	if !ok {
		return
	}
	var payload ArticleStatusUpdate
	if !bindJSON(c, &payload) {
		return
	}
	if !payload.Status.IsValid() {
		writeError(c, http.StatusBadRequest, "Invalid status: "+string(payload.Status))
		return
	}
	api.store.mu.Lock()
	defer api.store.mu.Unlock()
	article, found := api.store.articles[id]
	if !found {
		writeError(c, http.StatusNotFound, "Article not found")
		return
	}
	if user.Role == RoleCoordinator && article.AuthorID != user.ID {
		writeError(c, http.StatusForbidden, "Coordinator can only change status of own articles")
		return
	}
	now := time.Now().UTC()
	if payload.Status == ArticlePublished && article.Status != ArticlePublished {
		article.PublishedAt = &now
	}
	article.Status = payload.Status
	article.UpdatedAt = now
	api.store.articles[id] = article
	if !persistOrError(c, api.store) {
		return
	}
	c.JSON(http.StatusOK, article.ArticleRead)
}

func canViewArticle(user storedUser, article ArticleRead) bool {
	if article.Status == ArticlePublished {
		return true
	}
	if user.Role == RoleAdmin {
		return true
	}
	if user.Role == RoleCoordinator && article.AuthorID == user.ID {
		return true
	}
	return false
}
