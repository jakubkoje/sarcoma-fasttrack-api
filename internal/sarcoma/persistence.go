package sarcoma

import "context"

type StoreSnapshot struct {
	ID            string             `bson:"_id" json:"id"`
	Version       int                `bson:"version" json:"version"`
	NextUserID    int                `bson:"next_user_id" json:"next_user_id"`
	NextPatientID int                `bson:"next_patient_id" json:"next_patient_id"`
	NextOrgID     int                `bson:"next_org_id" json:"next_org_id"`
	NextReportID  int                `bson:"next_report_id" json:"next_report_id"`
	Users         []storedUser       `bson:"users" json:"users"`
	Doctors       []storedDoctor     `bson:"doctors" json:"doctors"`
	Patients      []PatientRead      `bson:"patients" json:"patients"`
	Organizations []OrganizationRead `bson:"organizations" json:"organizations"`
	Reports       []ReportRead       `bson:"reports" json:"reports"`
}

type Persistence interface {
	Load(ctx context.Context) (*StoreSnapshot, error)
	Save(ctx context.Context, snapshot StoreSnapshot) error
	Ping(ctx context.Context) error
	Close(ctx context.Context) error
}

type memoryPersistence struct {
	snapshot *StoreSnapshot
}

func newMemoryPersistence(snapshot *StoreSnapshot) *memoryPersistence {
	return &memoryPersistence{snapshot: snapshot}
}

func (p *memoryPersistence) Load(context.Context) (*StoreSnapshot, error) {
	if p.snapshot == nil {
		return nil, nil
	}
	copied := *p.snapshot
	return &copied, nil
}

func (p *memoryPersistence) Save(_ context.Context, snapshot StoreSnapshot) error {
	copied := snapshot
	p.snapshot = &copied
	return nil
}

func (p *memoryPersistence) Ping(context.Context) error {
	return nil
}

func (p *memoryPersistence) Close(context.Context) error {
	return nil
}
