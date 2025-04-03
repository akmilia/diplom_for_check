"""
fix_migration

Revision ID: 1a3921867d9b
Revises: 05285ed603d5
Create Date: 2025-04-04 00:42:13.945890

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '1a3921867d9b'
down_revision: str | None = '05285ed603d5'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    create_schedule_view()
    create_users_view()
    create_subjects_view()


def downgrade() -> None:
    drop_schedule_view()
    drop_users_view()
    drop_subjects_view()


view_schedule_query = """
SELECT s.idschedule,
    s."time",
    sub.name AS subject_name,
    u.surname || ' ' || u.name || ' ' || u.paternity AS teacher,
    c.idcabinet AS cabinet,
    g.name AS group_nam,
        CASE
            WHEN s.day_of_week = 1 THEN 'Понедельник'::text
            WHEN s.day_of_week = 2 THEN 'Вторник'::text
            WHEN s.day_of_week = 3 THEN 'Среда'::text
            WHEN s.day_of_week = 4 THEN 'Четверг'::text
            WHEN s.day_of_week = 5 THEN 'Пятница'::text
            WHEN s.day_of_week = 6 THEN 'Суббота'::text
            WHEN s.day_of_week = 7 THEN 'Воскресенье'::text
            ELSE NULL::text
        END AS day_of_week
FROM schedule s
     JOIN subjects sub ON s.subjects_idsubjects = sub.idsubjects
     JOIN users u ON s.users_idusers = u.idusers
     JOIN cabinets c ON s.cabinets_idcabinet = c.idcabinet
     LEFT JOIN groups g ON s.groups_idgroup = g.idgroups;
"""

def create_schedule_view():
    op.execute(f"""
    CREATE OR REPLACE VIEW scheduleshow AS
    {view_schedule_query}
    """)

def drop_schedule_view():
    op.execute("DROP VIEW IF EXISTS scheduleshow") 

view_users_query = """
SELECT u.idusers,
    u.login,
    u.password,
    (((u.surname::text || ' '::text) || u.name::text) || ' '::text) || u.paternity::text AS full_name,
    r.idroles,
    r.name AS user_role
FROM users u
     JOIN roles r ON u.roles_idroles = r.idroles;
"""

def create_users_view():
    op.execute(f"""
    CREATE OR REPLACE VIEW usersshow AS
    {view_users_query}
    """)

def drop_users_view():
    op.execute("DROP VIEW IF EXISTS usersshow")  

view_subjects_query = """
 SELECT s.idsubjects AS subject_id,
    s.name AS subject_name,
    s.description,
    t.id AS type_id,
    t.type AS type_name
FROM subjects s
     JOIN types_subjects st ON s.idsubjects = st.subjects_idsubjects
     JOIN types t ON st.types_id = t.id;
"""

def create_subjects_view():
    op.execute(f"""
    CREATE OR REPLACE VIEW subjectsshow AS
    {view_subjects_query}
    """)

def drop_subjects_view():
    op.execute("DROP VIEW IF EXISTS subjectsshow")