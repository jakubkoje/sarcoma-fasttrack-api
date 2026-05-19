package sarcoma

import (
	"context"
	"net/http"
	"testing"
)

func TestStorePersistenceRoundTrip(t *testing.T) {
	persistence := newMemoryPersistence(nil)
	store, err := NewStoreWithPersistence(context.Background(), persistence)
	if err != nil {
		t.Fatalf("cannot create persistent store: %v", err)
	}
	router := testRouterWithStore(store)
	token := loginToken(t, router, "admin@admin.com", "admin")

	patient := requestJSON[PatientRead](t, router, http.MethodPost, "/api/v1/patients", token, `{
		"first_name": "Persist",
		"last_name": "Patient",
		"address": "Persistence 1",
		"birth_number": "660606/6666",
		"phone": "+420666666666"
	}`, http.StatusCreated)
	if persistence.snapshot == nil {
		t.Fatal("expected write path to save a snapshot")
	}

	loaded, err := NewStoreWithPersistence(context.Background(), persistence)
	if err != nil {
		t.Fatalf("cannot load persistent store: %v", err)
	}
	loaded.mu.RLock()
	defer loaded.mu.RUnlock()
	restored, ok := loaded.patients[patient.ID]
	if !ok {
		t.Fatalf("patient %d was not restored from snapshot", patient.ID)
	}
	if restored.FirstName == nil || *restored.FirstName != "Persist" {
		t.Fatalf("restored patient is wrong: %+v", restored.PatientRead)
	}
	if loaded.nextPatientID <= patient.ID {
		t.Fatalf("next patient id was not restored correctly: got %d, patient %d", loaded.nextPatientID, patient.ID)
	}
}
