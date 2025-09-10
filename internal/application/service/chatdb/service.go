package chatdb

import (
	"context"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/Tencent/WeKnora/internal/logger"
	"github.com/Tencent/WeKnora/internal/types"
	"github.com/minio/minio-go/v7"
	"github.com/minio/minio-go/v7/pkg/credentials"
	"gorm.io/gorm"
)

// ChatDBService provides chat database operations
type ChatDBService struct {
	db                *gorm.DB
	minioClient       *minio.Client
	publicMinioClient *minio.Client
	bucketName        string
}

// NewChatDBService creates a new ChatDBService instance
func NewChatDBService(db *gorm.DB) (*ChatDBService, error) {
	// Initialize MinIO client
	minioEndpoint := os.Getenv("MINIO_ENDPOINT")
	minioAccessKey := os.Getenv("MINIO_ACCESS_KEY_ID")
	minioSecretKey := os.Getenv("MINIO_SECRET_ACCESS_KEY")
	minioBucketName := os.Getenv("MINIO_BUCKET_NAME")

	if minioEndpoint == "" || minioAccessKey == "" || minioSecretKey == "" || minioBucketName == "" {
		return nil, fmt.Errorf("MinIO configuration incomplete: missing required environment variables")
	}

	// Create MinIO client
	minioClient, err := minio.New(minioEndpoint, &minio.Options{
		Creds:  credentials.NewStaticV4(minioAccessKey, minioSecretKey, ""),
		Secure: false, // Set to true if using HTTPS
	})
	if err != nil {
		return nil, fmt.Errorf("failed to initialize MinIO client: %w", err)
	}

	// Store public endpoint for presigned URL generation
	var publicMinioClient *minio.Client
	publicEndpoint := os.Getenv("MINIO_PUBLIC_ENDPOINT")
	if publicEndpoint != "" {
		// Parse the public endpoint to extract host:port
		var publicHost string
		var publicSecure bool

		if strings.HasPrefix(publicEndpoint, "https://") {
			publicHost = strings.TrimPrefix(publicEndpoint, "https://")
			publicSecure = true
		} else if strings.HasPrefix(publicEndpoint, "http://") {
			publicHost = strings.TrimPrefix(publicEndpoint, "http://")
			publicSecure = false
		} else {
			publicHost = publicEndpoint
			publicSecure = false
		}

		// Create a client with public endpoint for presigned URL generation
		publicMinioClient, err = minio.New(publicHost, &minio.Options{
			Creds:  credentials.NewStaticV4(minioAccessKey, minioSecretKey, ""),
			Secure: publicSecure,
		})
		if err != nil {
			return nil, fmt.Errorf("failed to initialize public MinIO client: %w", err)
		}
	}

	// Check if bucket exists
	ctx := context.Background()
	exists, err := minioClient.BucketExists(ctx, minioBucketName)
	if err != nil {
		return nil, fmt.Errorf("failed to check MinIO bucket existence: %w", err)
	}

	if !exists {
		// Create bucket if it doesn't exist
		err = minioClient.MakeBucket(ctx, minioBucketName, minio.MakeBucketOptions{})
		if err != nil {
			return nil, fmt.Errorf("failed to create MinIO bucket: %w", err)
		}
		logger.GetLogger(ctx).Infof("Created MinIO bucket: %s", minioBucketName)
	} else {
		logger.GetLogger(ctx).Infof("MinIO bucket exists: %s", minioBucketName)
	}

	return &ChatDBService{
		db:                db,
		minioClient:       minioClient,
		publicMinioClient: publicMinioClient,
		bucketName:        minioBucketName,
	}, nil
}

// GetChatRecordByID retrieves a chat record by ID and generates presigned URLs for images
func (s *ChatDBService) GetChatRecordByID(ctx context.Context, recordID int) (*types.ChatLog, error) {
	logger.GetLogger(ctx).Infof("Retrieving chat record with ID: %d", recordID)

	// Query the database for the chat record
	var chatLog types.ChatLog
	err := s.db.WithContext(ctx).Where("id = ?", recordID).First(&chatLog).Error
	if err != nil {
		if err == gorm.ErrRecordNotFound {
			logger.GetLogger(ctx).Warnf("Chat record not found with ID: %d", recordID)
			return nil, fmt.Errorf("chat record not found")
		}
		logger.GetLogger(ctx).Errorf("Failed to query chat record: %v", err)
		return nil, fmt.Errorf("failed to query chat record: %w", err)
	}

	// Check if the record contains image references (support both single and multiple images)
	imageRefs := chatLog.LogData.GetImageReferences()
	if len(imageRefs) > 0 {
		imageURLs := make(map[string]string)

		for refKey, imageRef := range imageRefs {
			if imageRef == nil || (imageRef.ObjectName == "" && imageRef.Key == "") {
				continue
			}

			// Determine the object name (prefer ObjectName, fallback to Key)
			objectName := imageRef.ObjectName
			if objectName == "" {
				objectName = imageRef.Key
			}

			// Determine the bucket name (prefer from imageRef, fallback to service default)
			bucketName := imageRef.Bucket
			if bucketName == "" {
				bucketName = s.bucketName
			}

			logger.GetLogger(ctx).Infof("Generating presigned URL for image '%s': bucket=%s, object=%s", refKey, bucketName, objectName)

			// Generate URL for image access
			// For public buckets, use direct URL; for private buckets, use presigned URL
			publicEndpoint := os.Getenv("MINIO_PUBLIC_ENDPOINT")
			if publicEndpoint != "" {
				// Use direct URL for public bucket
				imageURL := fmt.Sprintf("%s/%s/%s", publicEndpoint, bucketName, objectName)
				imageURLs[refKey] = imageURL
				logger.GetLogger(ctx).Infof("Generated direct URL for image '%s': %s", refKey, objectName)
			} else {
				// Fallback to presigned URL for private bucket
				presignedURL, err := s.minioClient.PresignedGetObject(ctx, bucketName, objectName, 12*time.Hour, nil)
				if err != nil {
					logger.GetLogger(ctx).Errorf("Failed to generate presigned URL for image '%s': %v", refKey, err)
					imageURLs[refKey] = ""
				} else {
					imageURLs[refKey] = presignedURL.String()
					logger.GetLogger(ctx).Infof("Generated presigned URL for image '%s': %s", refKey, objectName)
				}
			}
		}

		// Set all image URLs in the log data
		if len(imageURLs) > 0 {
			chatLog.LogData.SetImageURLs(imageURLs)
		}

		// For backward compatibility, also set single image URL if there's only one image
		if len(imageURLs) == 1 {
			for _, url := range imageURLs {
				chatLog.LogData.SetImageURL(url)
				break
			}
		}
	}

	logger.GetLogger(ctx).Infof("Successfully retrieved chat record: ID=%d, ConversationID=%s", chatLog.ID, chatLog.ConversationID)
	return &chatLog, nil
}

// GetAllChatRecords retrieves all chat records with pagination
func (s *ChatDBService) GetAllChatRecords(ctx context.Context, limit, offset int) ([]*types.ChatLog, int64, error) {
	logger.GetLogger(ctx).Infof("Retrieving all chat records with limit: %d, offset: %d", limit, offset)

	var chatLogs []*types.ChatLog
	var total int64

	// Get total count
	err := s.db.WithContext(ctx).Model(&types.ChatLog{}).Count(&total).Error
	if err != nil {
		logger.GetLogger(ctx).Errorf("Failed to count chat records: %v", err)
		return nil, 0, fmt.Errorf("failed to count chat records: %w", err)
	}

	// Get records with pagination
	err = s.db.WithContext(ctx).Order("created_at DESC").Limit(limit).Offset(offset).Find(&chatLogs).Error
	if err != nil {
		logger.GetLogger(ctx).Errorf("Failed to query chat records: %v", err)
		return nil, 0, fmt.Errorf("failed to query chat records: %w", err)
	}

	logger.GetLogger(ctx).Infof("Successfully retrieved %d chat records, total: %d", len(chatLogs), total)
	return chatLogs, total, nil
}

// SaveChatRecord saves a new chat record to the database
func (s *ChatDBService) SaveChatRecord(ctx context.Context, userID, conversationID, sessionID string, logData types.ChatLogData) (*types.ChatLog, error) {
	logger.GetLogger(ctx).Infof("Saving chat record: UserID=%s, ConversationID=%s, SessionID=%s", userID, conversationID, sessionID)

	chatLog := &types.ChatLog{
		UserID:         userID,
		ConversationID: conversationID,
		SessionID:      &sessionID,
		LogData:        logData,
	}

	err := s.db.WithContext(ctx).Create(chatLog).Error
	if err != nil {
		logger.GetLogger(ctx).Errorf("Failed to save chat record: %v", err)
		return nil, fmt.Errorf("failed to save chat record: %w", err)
	}

	logger.GetLogger(ctx).Infof("Successfully saved chat record with ID: %d", chatLog.ID)
	return chatLog, nil
}
