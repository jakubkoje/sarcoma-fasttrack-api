package sarcoma

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"sync"
	"time"
)

type storedUser struct {
	ID           int
	Email        string
	Role         UserRole
	Salt         string
	PasswordHash string
	IsActive     bool
	FhirID       *string
}

type storedDoctor struct {
	ID             int
	UserID         int
	OrganizationID *int
	FhirID         *string
}

type storedPatient struct {
	PatientRead
}

type storedOrganization struct {
	OrganizationRead
}

type storedReport struct {
	ReportRead
}

type storedArticle struct {
	ArticleRead
}

type Store struct {
	mu            sync.RWMutex
	nextUserID    int
	nextPatientID int
	nextOrgID     int
	nextReportID  int
	nextArticleID int
	users         map[int]storedUser
	usersByEmail  map[string]int
	doctors       map[int]storedDoctor
	patients      map[int]storedPatient
	organizations map[int]storedOrganization
	reports       map[int]storedReport
	articles      map[int]storedArticle
	secret        []byte
	persistence   Persistence
}

func NewStore() *Store {
	store := emptyStore(nil)
	store.seed()
	return store
}

func NewStoreWithPersistence(ctx context.Context, persistence Persistence) (*Store, error) {
	store := emptyStore(persistence)
	snapshot, err := persistence.Load(ctx)
	if err != nil {
		return nil, err
	}
	if snapshot != nil {
		store.applySnapshot(*snapshot)
		return store, nil
	}
	store.seed()
	if err := store.saveSnapshotLocked(ctx); err != nil {
		return nil, err
	}
	return store, nil
}

func emptyStore(persistence Persistence) *Store {
	return &Store{
		nextUserID:    20,
		nextPatientID: 2,
		nextOrgID:     16,
		nextReportID:  2,
		nextArticleID: 2,
		users:         map[int]storedUser{},
		usersByEmail:  map[string]int{},
		doctors:       map[int]storedDoctor{},
		patients:      map[int]storedPatient{},
		organizations: map[int]storedOrganization{},
		reports:       map[int]storedReport{},
		articles:      map[int]storedArticle{},
		secret:        []byte("sarcoma-fasttrack-local-dev-secret"),
		persistence:   persistence,
	}
}

func (s *Store) seed() {
	s.addSeedUser(1, "admin@admin.com", "admin", RoleAdmin, nil)
	s.addSeedUser(2, "specialist@sft.local", "specialist", RoleSpecialist, strPtr("prac-specialist-seed"))
	s.addSeedUser(3, "coordinator@sft.local", "coordinator", RoleCoordinator, strPtr("prac-coordinator-seed"))
	s.addSeedUser(19, "doctor@sft.local", "doctor", RoleDoctor, strPtr("prac-doctor-seed"))
	orgID := 14
	s.doctors[19] = storedDoctor{ID: 19, UserID: 19, OrganizationID: &orgID, FhirID: strPtr("prac-doctor-seed")}

	s.organizations[14] = storedOrganization{OrganizationRead: OrganizationRead{
		ID:            14,
		FhirID:        "org-mou",
		Name:          strPtr("Masarykův onkologický ústav"),
		TypeCode:      strPtr("prov"),
		Address:       strPtr("Žlutý kopec 7, Brno"),
		Contact:       strPtr("+420543131111"),
		Capacity:      intPtr(120),
		Region:        strPtr("Jihomoravský"),
		CatchmentArea: strPtr("Morava a Slezsko"),
	}}
	s.organizations[15] = storedOrganization{OrganizationRead: OrganizationRead{
		ID:            15,
		FhirID:        "org-fn-motol",
		Name:          strPtr("FN Motol"),
		TypeCode:      strPtr("prov"),
		Address:       strPtr("V Úvalu 84, Praha"),
		Contact:       strPtr("+420224431111"),
		Capacity:      intPtr(180),
		Region:        strPtr("Hlavní město Praha"),
		CatchmentArea: strPtr("Čechy"),
	}}
	s.patients[1] = storedPatient{PatientRead: PatientRead{
		ID:           1,
		FhirID:       "pat-seed",
		FirstName:    strPtr("Jan"),
		LastName:     strPtr("Novák"),
		GivenName:    strPtr("Jan"),
		FamilyName:   strPtr("Novák"),
		Address:      strPtr("Kounicova 1, Brno"),
		AddressText:  strPtr("Kounicova 1, Brno"),
		BirthNumber:  strPtr("800101/1234"),
		IdentifierRC: strPtr("800101/1234"),
		Phone:        strPtr("+420777111222"),
		Email:        strPtr("jan.novak@example.test"),
	}}
	now := time.Now().UTC()
	s.reports[1] = storedReport{ReportRead: ReportRead{
		ID:                       1,
		FhirID:                   "rep-seed",
		PatientID:                1,
		DoctorID:                 19,
		TargetOrganizationID:     14,
		Status:                   StatusDraft,
		StatusCZ:                 StatusDraft.Czech(),
		AuthoredOn:               &now,
		Note:                     strPtr("Sonografie: suspektní ložisko na pravém stehně."),
		IsNewPatient:             boolPtr(true),
		AnyImagingPerformed:      boolPtr(true),
		AdditionalImagingPlanned: boolPtr(false),
		Anamnesis:                strPtr("Rychle rostoucí měkkotkáňová rezistence."),
		MKN10Code:                strPtr("C49.2"),
		CreatedAt:                now,
		UpdatedAt:                now,
		Severity:                 strPtr("2"),
	}}
	publishedAt := now
	s.articles[1] = storedArticle{ArticleRead: ArticleRead{
		ID:              1,
		Title:           "Diagnostika sarkomu pro praktické lékaře",
		Summary:         "Stručný přehled klíčových diagnostických kroků a kdy odeslat pacienta do specializovaného centra.",
		Body:            "## Úvod\n\nU každého rychle rostoucího ložiska v měkkých tkáních zvažte sarkom.\n\n## Co odeslat\n\n- MR vyšetření postižené oblasti\n- Kompletní anamnézu a foto léze\n- Kontakt na pacienta\n\n## Kdy odeslat\n\nNeprodleně při jakémkoliv podezření — biopsii vždy plánuje specializované centrum.",
		Category:        strPtr("Diagnostika"),
		ImageURL:        strPtr("https://images.unsplash.com/photo-1559757175-5700dde675bc?w=800&q=80"),
		AuthorID:        3,
		AuthorName:      strPtr("MUDr. Koordinátor"),
		AuthorAvatarURL: strPtr("https://ui-avatars.com/api/?name=Koordinator&background=9333ea&color=fff"),
		ReadTimeMinutes: intPtr(6),
		Status:          ArticlePublished,
		PublishedAt:     &publishedAt,
		CreatedAt:       now,
		UpdatedAt:       now,
	}}
}

func (s *Store) Ping(ctx context.Context) error {
	if s.persistence == nil {
		return nil
	}
	return s.persistence.Ping(ctx)
}

func (s *Store) Close(ctx context.Context) error {
	if s.persistence == nil {
		return nil
	}
	return s.persistence.Close(ctx)
}

func (s *Store) saveSnapshotLocked(ctx context.Context) error {
	if s.persistence == nil {
		return nil
	}
	return s.persistence.Save(ctx, s.snapshotLocked())
}

func (s *Store) persistLocked() error {
	if s.persistence == nil {
		return nil
	}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	return s.saveSnapshotLocked(ctx)
}

func (s *Store) snapshotLocked() StoreSnapshot {
	snapshot := StoreSnapshot{
		Version:       1,
		NextUserID:    s.nextUserID,
		NextPatientID: s.nextPatientID,
		NextOrgID:     s.nextOrgID,
		NextReportID:  s.nextReportID,
		NextArticleID: s.nextArticleID,
		Users:         make([]storedUser, 0, len(s.users)),
		Doctors:       make([]storedDoctor, 0, len(s.doctors)),
		Patients:      make([]PatientRead, 0, len(s.patients)),
		Organizations: make([]OrganizationRead, 0, len(s.organizations)),
		Reports:       make([]ReportRead, 0, len(s.reports)),
		Articles:      make([]ArticleRead, 0, len(s.articles)),
	}
	for _, user := range s.users {
		snapshot.Users = append(snapshot.Users, user)
	}
	for _, doctor := range s.doctors {
		snapshot.Doctors = append(snapshot.Doctors, doctor)
	}
	for _, patient := range s.patients {
		snapshot.Patients = append(snapshot.Patients, patient.PatientRead)
	}
	for _, organization := range s.organizations {
		snapshot.Organizations = append(snapshot.Organizations, organization.OrganizationRead)
	}
	for _, report := range s.reports {
		snapshot.Reports = append(snapshot.Reports, report.ReportRead)
	}
	for _, article := range s.articles {
		snapshot.Articles = append(snapshot.Articles, article.ArticleRead)
	}
	return snapshot
}

func (s *Store) applySnapshot(snapshot StoreSnapshot) {
	s.nextUserID = snapshot.NextUserID
	s.nextPatientID = snapshot.NextPatientID
	s.nextOrgID = snapshot.NextOrgID
	s.nextReportID = snapshot.NextReportID
	s.nextArticleID = snapshot.NextArticleID
	if s.nextArticleID == 0 {
		s.nextArticleID = 2
	}
	s.users = map[int]storedUser{}
	s.usersByEmail = map[string]int{}
	s.doctors = map[int]storedDoctor{}
	s.patients = map[int]storedPatient{}
	s.organizations = map[int]storedOrganization{}
	s.reports = map[int]storedReport{}
	s.articles = map[int]storedArticle{}

	for _, user := range snapshot.Users {
		s.users[user.ID] = user
		s.usersByEmail[user.Email] = user.ID
	}
	for _, doctor := range snapshot.Doctors {
		s.doctors[doctor.ID] = doctor
	}
	for _, patient := range snapshot.Patients {
		s.patients[patient.ID] = storedPatient{PatientRead: patient}
	}
	for _, organization := range snapshot.Organizations {
		s.organizations[organization.ID] = storedOrganization{OrganizationRead: organization}
	}
	for _, report := range snapshot.Reports {
		s.reports[report.ID] = storedReport{ReportRead: report}
	}
	for _, article := range snapshot.Articles {
		s.articles[article.ID] = storedArticle{ArticleRead: article}
	}
}

func (s *Store) addSeedUser(id int, email string, password string, role UserRole, fhirID *string) {
	salt := randomHex(8)
	s.users[id] = storedUser{
		ID:           id,
		Email:        email,
		Role:         role,
		Salt:         salt,
		PasswordHash: hashPassword(password, salt),
		IsActive:     true,
		FhirID:       fhirID,
	}
	s.usersByEmail[email] = id
}

func (s *Store) userRead(user storedUser) UserRead {
	return UserRead{
		ID:       user.ID,
		Email:    user.Email,
		IsActive: user.IsActive,
		Role:     user.Role,
		FhirID:   user.FhirID,
	}
}

func (s *Store) authenticate(email string, password string) (storedUser, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	id, ok := s.usersByEmail[email]
	if !ok {
		return storedUser{}, false
	}
	user := s.users[id]
	return user, user.IsActive && verifyPassword(password, user.Salt, user.PasswordHash)
}

func (s *Store) userByEmail(email string) (storedUser, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	id, ok := s.usersByEmail[email]
	if !ok {
		return storedUser{}, false
	}
	return s.users[id], true
}

func (s *Store) randomFHIRID(prefix string) string {
	return fmt.Sprintf("%s-%s", prefix, randomHex(16))
}

func randomHex(bytes int) string {
	buffer := make([]byte, bytes)
	if _, err := rand.Read(buffer); err != nil {
		panic(err)
	}
	return hex.EncodeToString(buffer)
}

func strPtr(value string) *string {
	return &value
}

func boolPtr(value bool) *bool {
	return &value
}

func intPtr(value int) *int {
	return &value
}
