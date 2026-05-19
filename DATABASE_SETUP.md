# Database Setup with Docker Compose

This guide explains how to set up and seed the PostgreSQL database using Docker Compose.

## Quick Start

### 1. Start PostgreSQL Database

```bash
make db-up
```

Or manually:
```bash
docker-compose -f docker-compose.db.yml up -d postgres
```

The database will be available at:
- **Host**: `localhost`
- **Port**: `5433` (to avoid conflicts with other PostgreSQL instances)
- **Database**: `sarcomfasttrack`
- **User**: `sarcomfasttrack`
- **Password**: `sarcomfasttrack`

### 2. Seed Database

```bash
make db-seed
```

Or manually:
```bash
docker-compose -f docker-compose.db.yml --profile seeder up seeder
```

### 3. Reset Database (Fresh Start)

To completely reset the database and reseed:

```bash
make db-reset
```

Or manually:
```bash
docker-compose -f docker-compose.db.yml down -v
docker-compose -f docker-compose.db.yml up -d postgres
# Wait for database to be ready, then:
docker-compose -f docker-compose.db.yml --profile seeder up seeder
```

## What Gets Seeded

The seeder creates sample data for testing:

### Organizations (3)
1. **Fakultní nemocnice Brno** - Healthcare provider
2. **Nemocnice u sv. Anny v Brně** - Healthcare provider  
3. **VZP - Všeobecná zdravotní pojišťovna** - Insurance company

### Users (4)
1. **doktor.novak@fnbrno.cz** - Doctor (password: `doctor123`)
2. **doktor.svoboda@fnbrno.cz** - Doctor (password: `doctor123`)
3. **praktik.kovarik@lekarna.cz** - Practitioner (password: `practitioner123`)
4. **koordinator@system.cz** - Coordinator (password: `coordinator123`)

### Patients (3)
1. **Jan Novák** - Born 1985-01-01
2. **Marie Svobodová** - Born 1990-02-02
3. **Petr Dvořák** - Born 1988-03-03

### Reports (2)
- Sample medical reports with clinical data (anamnesis, imaging, histology, etc.)

## FHIR Integration

All seeded data automatically creates corresponding FHIR resources:

- **Organizations** → FHIR Organization resources
- **Doctors/Practitioners** → FHIR Practitioner resources + PractitionerRole
- **Patients** → FHIR Patient resources
- **Reports** → FHIR ServiceRequest resources with custom extensions

### FHIR Configuration

The seeder respects the `FHIR_ENABLED` environment variable. Set it to `false` to disable FHIR integration:

```bash
export FHIR_ENABLED=false
make db-seed
```

By default, it tries to connect to:
- `FHIR_SERVER_URL`: `http://host.docker.internal:32783/csp/healthshare/demo/fhir/r4`
- `FHIR_SERVER_USER`: `_SYSTEM`
- `FHIR_SERVER_PASSWORD`: `ISCDEMO`

You can override these via environment variables or `.env` file.

## Environment Variables

### Database Connection

```bash
# Database (defaults shown)
DB_HOST=postgres
DB_PORT=5432
DB_NAME=sarcomfasttrack
DB_USER=sarcomfasttrack
DB_PASSWORD=sarcomfasttrack
```

### FHIR Server Configuration

```bash
FHIR_ENABLED=true
FHIR_SERVER_URL=http://host.docker.internal:32783/csp/healthshare/demo/fhir/r4
FHIR_SERVER_USER=_SYSTEM
FHIR_SERVER_PASSWORD=ISCDEMO
```

### Seeder Configuration

Control what gets seeded and how:

```bash
# Enable/disable seeding specific entities (default: true for all)
SEED_ORGANIZATIONS=true
SEED_USERS=true
SEED_PATIENTS=true
SEED_REPORTS=true

# Overwrite existing data (default: false)
SEED_OVERWRITE=false

# Optional: Use custom seed data from JSON file
SEED_DATA_FILE=/path/to/custom_seed_data.json
```

**Production Usage Examples:**

```bash
# Seed only organizations (useful for production setup)
SEED_ORGANIZATIONS=true SEED_USERS=false SEED_PATIENTS=false SEED_REPORTS=false python scripts/seed_database.py

# Seed with custom data file
SEED_DATA_FILE=/path/to/production_seed_data.json python scripts/seed_database.py

# Skip seeding if data already exists (default behavior)
# Just run: python scripts/seed_database.py
```

## Manual Seeding

If you prefer to run the seeder manually (outside Docker):

```bash
# Set environment variables
export DB_HOST=localhost
export DB_PORT=5433
export DB_NAME=sarcomfasttrack
export DB_USER=sarcomfasttrack
export DB_PASSWORD=sarcomfasttrack
export FHIR_ENABLED=true
export FHIR_SERVER_URL=http://localhost:32783/csp/healthshare/demo/fhir/r4
export FHIR_SERVER_USER=_SYSTEM
export FHIR_SERVER_PASSWORD=ISCDEMO

# Run seeder
python scripts/seed_database.py
```

## Connecting Your Application

Update your application's `.env` file to connect to the Docker database:

```bash
DB_HOST=localhost
DB_PORT=5433
DB_NAME=sarcomfasttrack
DB_USER=sarcomfasttrack
DB_PASSWORD=sarcomfasttrack
```

## Troubleshooting

### Database Connection Failed

- Check if PostgreSQL container is running: `docker ps`
- Verify port 5433 is not in use
- Check logs: `docker-compose -f docker-compose.db.yml logs postgres`

### FHIR Upload Failed

- Verify FHIR server is accessible
- Check FHIR credentials are correct
- The seeder will continue even if FHIR uploads fail (with warnings)
- Set `FHIR_ENABLED=false` to skip FHIR entirely

### Seeder Script Errors

- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check database tables exist (seeder creates them automatically)
- Review logs: `docker-compose -f docker-compose.db.yml logs seeder`

## Cleanup

Stop and remove everything:

```bash
make db-down
```

Or remove with volumes (deletes all data):

```bash
docker-compose -f docker-compose.db.yml down -v
```

## Database Access

You can access the database directly:

```bash
docker exec -it sarcomfasttrack-postgres psql -U sarcomfasttrack -d sarcomfasttrack
```

Or connect from your local machine:

```bash
psql -h localhost -p 5433 -U sarcomfasttrack -d sarcomfasttrack
```
