package sarcoma

import (
	"context"
	"errors"
	"fmt"
	"os"
	"strconv"
	"time"

	"go.mongodb.org/mongo-driver/v2/bson"
	"go.mongodb.org/mongo-driver/v2/mongo"
	"go.mongodb.org/mongo-driver/v2/mongo/options"
	"go.mongodb.org/mongo-driver/v2/mongo/readpref"
)

const defaultSnapshotID = "sarcoma-fasttrack"

type MongoConfig struct {
	URI        string
	Database   string
	Collection string
	SnapshotID string
	Timeout    time.Duration
}

type MongoPersistence struct {
	client     *mongo.Client
	collection *mongo.Collection
	snapshotID string
	timeout    time.Duration
}

func MongoConfigFromEnv() MongoConfig {
	timeoutSeconds, _ := strconv.Atoi(envOr("SARCOMA_API_MONGODB_TIMEOUT_SECONDS", "5"))
	if timeoutSeconds <= 0 {
		timeoutSeconds = 5
	}
	return MongoConfig{
		URI:        envOr("SARCOMA_API_MONGODB_URI", "mongodb://localhost:27017"),
		Database:   envOr("SARCOMA_API_MONGODB_DATABASE", "sarcoma-fasttrack"),
		Collection: envOr("SARCOMA_API_MONGODB_COLLECTION", "state"),
		SnapshotID: envOr("SARCOMA_API_MONGODB_SNAPSHOT_ID", defaultSnapshotID),
		Timeout:    time.Duration(timeoutSeconds) * time.Second,
	}
}

func NewMongoPersistence(ctx context.Context, cfg MongoConfig) (*MongoPersistence, error) {
	if cfg.Timeout <= 0 {
		cfg.Timeout = 5 * time.Second
	}
	if cfg.SnapshotID == "" {
		cfg.SnapshotID = defaultSnapshotID
	}
	client, err := mongo.Connect(options.Client().ApplyURI(cfg.URI).SetConnectTimeout(cfg.Timeout))
	if err != nil {
		return nil, err
	}
	persistence := &MongoPersistence{
		client:     client,
		collection: client.Database(cfg.Database).Collection(cfg.Collection),
		snapshotID: cfg.SnapshotID,
		timeout:    cfg.Timeout,
	}
	if err := persistence.Ping(ctx); err != nil {
		_ = client.Disconnect(context.Background())
		return nil, err
	}
	return persistence, nil
}

func NewStoreFromEnv(ctx context.Context) (*Store, error) {
	if os.Getenv("SARCOMA_API_STORE") != "mongo" && os.Getenv("SARCOMA_API_MONGODB_URI") == "" {
		return NewStore(), nil
	}

	retrySeconds, _ := strconv.Atoi(envOr("SARCOMA_API_MONGODB_STARTUP_RETRY_SECONDS", "2"))
	if retrySeconds <= 0 {
		retrySeconds = 2
	}
	retryDelay := time.Duration(retrySeconds) * time.Second
	cfg := MongoConfigFromEnv()
	var lastErr error

	for {
		persistence, err := NewMongoPersistence(ctx, cfg)
		if err == nil {
			store, storeErr := NewStoreWithPersistence(ctx, persistence)
			if storeErr == nil {
				return store, nil
			}
			_ = persistence.Close(context.Background())
			lastErr = storeErr
		} else {
			lastErr = err
		}

		select {
		case <-ctx.Done():
			if lastErr != nil {
				return nil, fmt.Errorf("mongo store startup failed: %w", lastErr)
			}
			return nil, ctx.Err()
		case <-time.After(retryDelay):
		}
	}
}

func (p *MongoPersistence) Load(ctx context.Context) (*StoreSnapshot, error) {
	ctx, cancel := p.withTimeout(ctx)
	defer cancel()

	var snapshot StoreSnapshot
	err := p.collection.FindOne(ctx, bson.M{"_id": p.snapshotID}).Decode(&snapshot)
	if errors.Is(err, mongo.ErrNoDocuments) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	return &snapshot, nil
}

func (p *MongoPersistence) Save(ctx context.Context, snapshot StoreSnapshot) error {
	ctx, cancel := p.withTimeout(ctx)
	defer cancel()

	snapshot.ID = p.snapshotID
	if _, err := p.collection.DeleteOne(ctx, bson.M{"_id": p.snapshotID}); err != nil {
		return err
	}
	_, err := p.collection.InsertOne(ctx, snapshot)
	return err
}

func (p *MongoPersistence) Ping(ctx context.Context) error {
	ctx, cancel := p.withTimeout(ctx)
	defer cancel()
	return p.client.Ping(ctx, readpref.Primary())
}

func (p *MongoPersistence) Close(ctx context.Context) error {
	return p.client.Disconnect(ctx)
}

func (p *MongoPersistence) withTimeout(ctx context.Context) (context.Context, context.CancelFunc) {
	if _, ok := ctx.Deadline(); ok {
		return context.WithCancel(ctx)
	}
	return context.WithTimeout(ctx, p.timeout)
}

func envOr(key string, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}
