from sqlalchemy import select, desc

from app.database.connection import (
    engine,
    SessionLocal
)

from app.database.models import (
    Base
)


# =====================================
# CREATE TABLES
# =====================================

def initialize_database():

    Base.metadata.create_all(bind=engine)

    print("Database tables created successfully!")