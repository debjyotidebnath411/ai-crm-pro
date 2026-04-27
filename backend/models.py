from sqlalchemy import Column, Integer, String, Text
from database import Base

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)

    hcp_name = Column(String(255))
    interaction_type = Column(String(100))

    date = Column(String(20))
    time = Column(String(20))

    attendees = Column(Text)
    topics = Column(Text)

    materials = Column(Text)
    samples = Column(Text)

    sentiment = Column(String(50))
    outcomes = Column(Text)
    follow_up = Column(Text)