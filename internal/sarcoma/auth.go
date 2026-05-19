package sarcoma

import (
	"crypto/hmac"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/base64"
	"encoding/hex"
	"errors"
	"fmt"
	"strconv"
	"strings"
	"time"
)

func hashPassword(password string, salt string) string {
	sum := sha256.Sum256([]byte(salt + ":" + password))
	return hex.EncodeToString(sum[:])
}

func verifyPassword(password string, salt string, expectedHash string) bool {
	actualHash := hashPassword(password, salt)
	return subtle.ConstantTimeCompare([]byte(actualHash), []byte(expectedHash)) == 1
}

func (s *Store) createAccessToken(email string) string {
	expiresAt := time.Now().UTC().Add(time.Hour).Unix()
	payload := fmt.Sprintf("%s|%d", email, expiresAt)
	signature := s.sign(payload)
	return base64.RawURLEncoding.EncodeToString([]byte(payload)) + "." + signature
}

func (s *Store) verifyAccessToken(token string) (string, error) {
	parts := strings.Split(token, ".")
	if len(parts) != 2 {
		return "", errors.New("invalid token")
	}
	payloadBytes, err := base64.RawURLEncoding.DecodeString(parts[0])
	if err != nil {
		return "", errors.New("invalid token")
	}
	payload := string(payloadBytes)
	if !hmac.Equal([]byte(s.sign(payload)), []byte(parts[1])) {
		return "", errors.New("invalid token")
	}
	payloadParts := strings.Split(payload, "|")
	if len(payloadParts) != 2 {
		return "", errors.New("invalid token")
	}
	expiresAt, err := strconv.ParseInt(payloadParts[1], 10, 64)
	if err != nil || time.Now().UTC().Unix() > expiresAt {
		return "", errors.New("token expired")
	}
	return payloadParts[0], nil
}

func (s *Store) sign(payload string) string {
	mac := hmac.New(sha256.New, s.secret)
	mac.Write([]byte(payload))
	return base64.RawURLEncoding.EncodeToString(mac.Sum(nil))
}
