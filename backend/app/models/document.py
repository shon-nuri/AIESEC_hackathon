from sqlalchemy import CheckConstraint, Column, DateTime, Float, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base
from backend.app.enums import Status, Label


class Document(Base):
    __tablename__ = "document"
    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    pages_count = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, nullable=False)
    status = Column(Enum(Status), nullable=False)

    page = relationship("Page", back_populates="document", cascade="all, delete-orphan")


class Page(Base):
    __tablename__ = "page"
    id = Column(Integer, primary_key=True)
    document_id = Column(ForeignKey("document.id"))
    page_index = Column(Integer, nullable=False)
    image_path = Column(String, nullable=False)
    width = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    processed_at = Column(DateTime, nullable=True)

    document = relationship("Document", back_populates="page")
    detection = relationship("Detection", back_populates="page", cascade="all, delete-orphan")


class Detection(Base):
    __tablename__ = "detection"
    page_id = Column(ForeignKey("page.id"))
    label = Column(Enum(Label), nullable=False)
    x_min = Column(Float, nullable=False)
    y_min = Column(Float, nullable=False)
    x_max = Column(Float, nullable=False)
    y_max = Column(Float, nullable=False)
    confidence = Column(Float, CheckConstraint("confidence >= 0 and confidence <= 1"), name="confidence_range")

    page = relationship("Page", back_populates="detection")
