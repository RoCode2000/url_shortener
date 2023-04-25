from sqlalchemy import Boolean, Column, Integer, String
from database import Base


class UrlMapping(Base):
    __tablename__ = "url_mappings"

    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String, index=True)
    short_url_key = Column(String, index=True, unique=True)
    short_url = Column(String, index=True, unique=True)
    clicks = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
