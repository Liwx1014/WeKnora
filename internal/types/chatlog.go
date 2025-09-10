package types

import (
	"database/sql/driver"
	"encoding/json"
	"time"
)

// ChatLog represents a record in the chat_service.logs table
type ChatLog struct {
	ID             int64           `json:"id" gorm:"column:id;primaryKey;autoIncrement"`
	ConversationID string          `json:"conversation_id" gorm:"column:conversation_id;type:uuid;not null"`
	UserID         string          `json:"user_id" gorm:"column:user_id;type:varchar(255);not null"`
	SessionID      *string         `json:"session_id" gorm:"column:session_id;type:varchar(255)"`
	LogData        ChatLogData     `json:"log_data" gorm:"column:log_data;type:jsonb;not null"`
	CreatedAt      time.Time       `json:"created_at" gorm:"column:created_at;default:CURRENT_TIMESTAMP"`
}

// TableName specifies the table name for ChatLog
func (ChatLog) TableName() string {
	return "chat_service.logs"
}

// ChatLogData represents the JSON data stored in the log_data column
type ChatLogData map[string]interface{}

// Value implements the driver.Valuer interface for GORM
func (c ChatLogData) Value() (driver.Value, error) {
	if c == nil {
		return nil, nil
	}
	return json.Marshal(c)
}

// Scan implements the sql.Scanner interface for GORM
func (c *ChatLogData) Scan(value interface{}) error {
	if value == nil {
		return nil
	}
	
	switch v := value.(type) {
	case []byte:
		return json.Unmarshal(v, c)
	case string:
		return json.Unmarshal([]byte(v), c)
	default:
		return nil
	}
}

// ImageReference represents the structure of image reference in log_data
type ImageReference struct {
	Bucket     string `json:"bucket"`
	ObjectName string `json:"object_name"`
	Key        string `json:"key"` // Alternative field name used in Python script
}

// GetImageReference extracts image reference from ChatLogData (legacy single image support)
func (c ChatLogData) GetImageReference() *ImageReference {
	if imageRef, ok := c["image_ref"]; ok {
		if refMap, ok := imageRef.(map[string]interface{}); ok {
			ref := &ImageReference{}
			if bucket, ok := refMap["bucket"].(string); ok {
				ref.Bucket = bucket
			}
			if objectName, ok := refMap["object_name"].(string); ok {
				ref.ObjectName = objectName
			}
			if key, ok := refMap["key"].(string); ok {
				ref.Key = key
				ref.ObjectName = key // Use key as object_name if object_name is not set
			}
			return ref
		}
	}
	return nil
}

// GetImageReferences extracts multiple image references from ChatLogData
func (c ChatLogData) GetImageReferences() map[string]*ImageReference {
	result := make(map[string]*ImageReference)
	
	// Check for image_refs field (multiple images)
	if imageRefs, ok := c["image_refs"]; ok {
		if refsMap, ok := imageRefs.(map[string]interface{}); ok {
			for refKey, refValue := range refsMap {
				if refMap, ok := refValue.(map[string]interface{}); ok {
					ref := &ImageReference{}
					if bucket, ok := refMap["bucket"].(string); ok {
						ref.Bucket = bucket
					}
					if objectName, ok := refMap["object_name"].(string); ok {
						ref.ObjectName = objectName
					}
					if key, ok := refMap["key"].(string); ok {
						ref.Key = key
						if ref.ObjectName == "" {
							ref.ObjectName = key // Use key as object_name if object_name is not set
						}
					}
					if ref.ObjectName != "" || ref.Key != "" {
						result[refKey] = ref
					}
				}
			}
		}
	}
	
	// Fallback to single image_ref for backward compatibility
	if len(result) == 0 {
		if singleRef := c.GetImageReference(); singleRef != nil {
			result["image"] = singleRef
		}
	}
	
	return result
}

// SetImageURL sets the image URL in ChatLogData (legacy single image support)
func (c ChatLogData) SetImageURL(url string) {
	c["image_url"] = url
}

// SetImageURLs sets multiple image URLs in ChatLogData
func (c ChatLogData) SetImageURLs(urls map[string]string) {
	if c["image_urls"] == nil {
		c["image_urls"] = make(map[string]interface{})
	}
	imageURLsMap, ok := c["image_urls"].(map[string]interface{})
	if !ok {
		c["image_urls"] = make(map[string]interface{})
		imageURLsMap = c["image_urls"].(map[string]interface{})
	}
	for key, url := range urls {
		// 生成前端ImageGallery组件期望的字段名格式
		imageURLsMap[key+"_image_url"] = url
	}
}