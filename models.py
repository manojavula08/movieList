from sqlalchemy import Column, String, Boolean, Integer
from database import Base

class Movie(Base):
    __tablename__ = "movietable"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    year = Column(Integer)
    description = Column(String)
    rating = Column(Integer)
    ranking = Column(Integer)
    review = Column(String)
    img_url = Column(String)
