# Database Seeder Setup

This directory contains scripts to seed the PostgreSQL database with sample data integrated with FHIR.

## Docker Compose Setup

### Quick Start

1. **Start PostgreSQL database:**
   ```bash
   docker-compose -f docker-compose.db.yml up -d postgres
   ```

2. **Wait for database to be ready** (healthcheck will ensure it's ready)

3. **Run the seeder:**
   ```bash
   docker-compose -f docker-compose.db.yml --profile seeder up seeder
   ```

   Or run it manually:
   ```bash
   docker-compose -f docker-compose.db.yml run --rm seeder
   ```

### Manual Setup

If you want to run the seeder manually without Docker:

1. **Ensure your database is running and accessible**
2. **Set environment variables:**
   ```bash
   export DB_HOST=localhost
   export DB_PORT=5433
   export DB_NAME=sarcomfasttrack
   export DB_USER=sarcomfasttrack
   export DB_PASSWORD=sarcomfasttrack
   export FHIR_ENABLED=true
   export FHIR_SERVER_URL=http://localhost:32783/csp/healthshare/demo/fhir/r4
   export FHIR_SERVER_USER=_SYSTEM
   export FHIR_SERVER_PASSWORD=ISCDEMO
   ```

3. **Run the seeder:**
   ```bash
   python scripts/seed_database.py
   ```

## What Gets Seeded

The seeder creates:

### Organizations (3)
- Fakultní nemocnice Brno
- Nemocnice u sv. Anny v Brně
- VZP - Všeobecná zdravotní pojišťovna

### Users (4)
- 2 Doctors (with FHIR Practitioner resources)
- 1 Practitioner (with FHIR Practitioner resource)
- 1 Coordinator (no FHIR resource)

### Patients (3)
- Jan Novák
- Marie Svobodová
- Petr Dvořák

### Reports (2)
- Sample medical reports with clinical data

## FHIR Integration

The seeder automatically:
- Creates FHIR resources for all organizations, practitioners, patients, and reports
- Links them properly using references
- Stores FHIR IDs in the database
- Falls back gracefully if FHIR is disabled or unavailable

## Environment Variables

Key environment variables for the seeder:

- `DB_HOST` - PostgreSQL host (default: postgres in Docker)
- `DB_PORT` - PostgreSQL port (default: 5432)
- `DB_NAME` - Database name (default: sarcomfasttrack)
- `DB_USER` - Database user (default: sarcomfasttrack)
- `DB_PASSWORD` - Database password (default: sarcomfasttrack)
- `FHIR_ENABLED` - Enable/disable FHIR integration (default: true)
- `FHIR_SERVER_URL` - FHIR server URL
- `FHIR_SERVER_USER` - FHIR server username
- `FHIR_SERVER_PASSWORD` - FHIR server password

## Cleanup

To remove the database and start fresh:

```bash
docker-compose -f docker-compose.db.yml down -v
```

This will remove the PostgreSQL container and all data volumes.

## Troubleshooting

### FHIR Connection Issues

If FHIR uploads fail, the seeder will continue but log warnings. Check:
- FHIR server is accessible
- FHIR credentials are correct
- `FHIR_ENABLED=true` is set

### Database Connection Issues

Check:
- PostgreSQL container is running: `docker ps`
- Database credentials match in environment variables
- Port is not already in use (default: 5433)

### Permission Issues

Make sure the script has proper permissions:
```bash
chmod +x scripts/seed_database.py
```
