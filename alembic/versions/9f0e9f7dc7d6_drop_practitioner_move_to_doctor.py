"""Drop practitioners, move references to doctors

Revision ID: 9f0e9f7dc7d6
Revises: 30cfc686db50
Create Date: 2025-12-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9f0e9f7dc7d6"
down_revision: Union[str, Sequence[str], None] = "30cfc686db50"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Move practitioner references to doctors and drop practitioners table."""
    conn = op.get_bind()

    # Ensure doctor_id exists on reports
    op.execute("ALTER TABLE reports ADD COLUMN IF NOT EXISTS doctor_id INTEGER")

    # Create doctors for any practitioner users that don't have a doctor record
    conn.execute(
        sa.text(
            """
            INSERT INTO doctors (fhir_id, user_id, organization_id, family_name, given_name, phone, email, specialty_code, role_code)
            SELECT p.fhir_id, p.user_id, NULL, p.family_name, p.given_name, p.phone, p.email, NULL, NULL
            FROM practitioners p
            WHERE NOT EXISTS (
                SELECT 1 FROM doctors d WHERE d.user_id = p.user_id
            )
            """
        )
    )

    # Move report links to doctors based on matching practitioner.user_id -> doctor.user_id
    conn.execute(
        sa.text(
            """
            UPDATE reports r
            SET doctor_id = d.id
            FROM practitioners p
            JOIN doctors d ON d.user_id = p.user_id
            WHERE r.practitioner_id = p.id
            """
        )
    )

    # Drop old FK and column, add new FK
    op.execute(
        "DO $$ BEGIN "
        "IF EXISTS (SELECT 1 FROM information_schema.table_constraints "
        "WHERE constraint_name = 'reports_practitioner_id_fkey' AND table_name = 'reports') THEN "
        "ALTER TABLE reports DROP CONSTRAINT reports_practitioner_id_fkey; "
        "END IF; END $$;"
    )
    op.create_foreign_key(
        "reports_doctor_id_fkey", "reports", "doctors", ["doctor_id"], ["id"]
    )
    op.drop_column("reports", "practitioner_id")

    # Drop practitioners table
    op.drop_table("practitioners")

    # Doctor link on reports should be required
    op.alter_column("reports", "doctor_id", nullable=False)


def downgrade() -> None:
    """Recreate practitioners and practitioner links (best-effort)."""
    conn = op.get_bind()

    op.add_column(
        "reports", sa.Column("practitioner_id", sa.Integer(), nullable=True)
    )

    op.create_table(
        "practitioners",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fhir_id", sa.String(), unique=True, nullable=True),
        sa.Column("user_id", sa.Integer(), unique=True, nullable=False),
        sa.Column("identifier_ico", sa.String(), nullable=True),
        sa.Column("family_name", sa.String(), nullable=True),
        sa.Column("given_name", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("address_line", sa.String(), nullable=True),
        sa.Column("address_city", sa.String(), nullable=True),
        sa.Column("address_postal_code", sa.String(), nullable=True),
        sa.Column("address_country", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )

    # Recreate practitioners from doctors (best-effort, without address/ico)
    conn.execute(
        sa.text(
            """
            INSERT INTO practitioners (fhir_id, user_id, family_name, given_name, phone, email)
            SELECT d.fhir_id, d.user_id, d.family_name, d.given_name, d.phone, d.email
            FROM doctors d
            WHERE NOT EXISTS (
                SELECT 1 FROM practitioners p WHERE p.user_id = d.user_id
            )
            """
        )
    )

    # Re-link reports to practitioners
    conn.execute(
        sa.text(
            """
            UPDATE reports r
            SET practitioner_id = p.id
            FROM doctors d
            JOIN practitioners p ON p.user_id = d.user_id
            WHERE r.doctor_id = d.id
            """
        )
    )

    op.drop_constraint("reports_doctor_id_fkey", "reports", type_="foreignkey")
    op.create_foreign_key(
        "reports_practitioner_id_fkey",
        "reports",
        "practitioners",
        ["practitioner_id"],
        ["id"],
    )
    op.alter_column("reports", "practitioner_id", nullable=False)
    op.drop_column("reports", "doctor_id")
