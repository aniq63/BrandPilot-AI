from datetime import datetime, timezone

from sqlalchemy import (
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    JSON
)


from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship
)


class Base(DeclarativeBase):
    pass