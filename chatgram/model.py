from sqlalchemy import JSON, Column, DateTime, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///chatbot_v2.db")
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    chat_instance = Column(String)
    message = Column(String)
    response = Column(String)
    token_count = Column(Integer)
    role = Column(String)
    user = Column(String)
    persona = Column(String)
    created_at = Column(DateTime)
    extra_info = Column(JSON)


class Personas(Base):
    __tablename__ = "personas"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    first_system_message = Column(String)
    first_user_message = Column(String)
    chatbot = Column(JSON)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


Base.metadata.create_all(engine)
