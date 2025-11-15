from sqlalchemy import CheckConstraint, Column, DateTime, Float, Integer, String, Enum, ForeignKey
from db.database import Base
import enum

class status(enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    done = "done"
    failed = "failed"


class label(enum.Enum):
    signature = "signature"
    stamp = "stamp"
    qr_code = "qr_code"


class Document(Base):
    __tablename__ = "document"
    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    pages_count = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, nullable=False)
    status = Column(Enum(status), nullable=False)


class Page(Base):
    __tablename__ = "page"
    id = Column(Integer, primary_key=True)
    document_id = Column(ForeignKey("document.id"))
    page_index = Column(Integer, nullable=False)
    image_path = Column(String, nullable=False)
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    processed_at = Column(DateTime, nullable=False)


class Detection(Base):
    __tablename__ = "detection"
    page_id = Column(ForeignKey("page.id"))
    label = Column(Enum(label), nullable=False)
    x_min = Column(Float, nullable=False)
    y_min = Column(Float, nullable=False)
    x_max = Column(Float, nullable=False)
    y_max = Column(Float, nullable=False)
    confidence = Column(Float, CheckConstraint("confidence >= 0 and confidence <= 1"), name="confidence_range")
    