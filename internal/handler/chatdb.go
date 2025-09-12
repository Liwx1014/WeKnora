package handler

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"

	"github.com/Tencent/WeKnora/internal/application/service/chatdb"
	"github.com/Tencent/WeKnora/internal/errors"
	"github.com/Tencent/WeKnora/internal/logger"
)

// ChatDBHandler handles HTTP requests related to ChatDB operations
type ChatDBHandler struct {
	chatDBService *chatdb.ChatDBService
}

// NewChatDBHandler creates a new ChatDB handler instance
func NewChatDBHandler(chatDBService *chatdb.ChatDBService) *ChatDBHandler {
	return &ChatDBHandler{
		chatDBService: chatDBService,
	}
}



// GetChatRecord handles the HTTP request to get a chat record by ID
// GET /api/v1/chatdb/record/:id
func (h *ChatDBHandler) GetChatRecord(c *gin.Context) {
	ctx := c.Request.Context()

	logger.Info(ctx, "Start getting chat record")

	// Get record ID from URL parameter
	recordIDStr := c.Param("id")
	if recordIDStr == "" {
		logger.Error(ctx, "Record ID is empty")
		c.Error(errors.NewBadRequestError("Record ID cannot be empty"))
		return
	}

	// Validate record ID is a number
	recordID, err := strconv.Atoi(recordIDStr)
	if err != nil {
		logger.Error(ctx, "Invalid record ID format", err)
		c.Error(errors.NewBadRequestError("Invalid record ID format"))
		return
	}

	logger.Infof(ctx, "Getting chat record with ID: %d", recordID)

	// Use ChatDBService to retrieve the record
	chatLog, err := h.chatDBService.GetChatRecordByID(ctx, recordID)
	if err != nil {
		logger.Error(ctx, "Failed to retrieve chat record", err)
		if err.Error() == "chat record not found" {
			c.Error(errors.NewNotFoundError("Chat record not found"))
		} else {
			c.Error(errors.NewInternalServerError("Failed to retrieve chat record"))
		}
		return
	}

	logger.Infof(ctx, "Successfully retrieved chat record, ID: %d, ConversationID: %s", chatLog.ID, chatLog.ConversationID)

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    chatLog,
	})
}

// GetAllChatRecords handles the HTTP request to get all chat records
// GET /api/v1/chatdb/records
func (h *ChatDBHandler) GetAllChatRecords(c *gin.Context) {
	ctx := c.Request.Context()

	logger.Info(ctx, "Start getting all chat records")

	// Parse pagination parameters
	limitStr := c.DefaultQuery("limit", "50")
	offsetStr := c.DefaultQuery("offset", "0")

	limit, err := strconv.Atoi(limitStr)
	if err != nil || limit <= 0 {
		limit = 50
	}
	if limit > 100 {
		limit = 100 // Maximum limit
	}

	offset, err := strconv.Atoi(offsetStr)
	if err != nil || offset < 0 {
		offset = 0
	}

	// Use ChatDBService to retrieve all records
	chatLogs, total, err := h.chatDBService.GetAllChatRecords(ctx, limit, offset)
	if err != nil {
		logger.Error(ctx, "Failed to retrieve all chat records", err)
		c.Error(errors.NewInternalServerError("Failed to retrieve all chat records"))
		return
	}

	logger.Infof(ctx, "Successfully retrieved %d chat records, total: %d", len(chatLogs), total)

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    chatLogs,
		"count":   len(chatLogs),
		"total":   total,
		"limit":   limit,
		"offset":  offset,
	})
}