from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


# =======================
# USER TABLE
# =======================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String, unique=True, index=True, nullable=False)

    password = Column(String, nullable=False)

    # Relationship → One user can have many files
    files = relationship(
        "File",
        back_populates="owner",
        cascade="all, delete"
    )


# =======================
# FILE METADATA TABLE
# =======================

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)

    filename = Column(String, nullable=False)

    size = Column(Integer)

    upload_time = Column(DateTime, default=datetime.utcnow)

    # ⭐ NEW FIELDS
    is_deleted = Column(Boolean, default=False)   # Trash system
    folder = Column(String, default="root")       # Folder system
    shared = Column(Boolean, default=False)       # Share feature

    owner_id = Column(Integer, ForeignKey("users.id"))

    # Relationship → File belongs to one user
    owner = relationship("User", back_populates="files")