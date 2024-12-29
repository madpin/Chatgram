# data/models.py
from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, Table, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

# Association table for the many-to-many relationship between Personas and Users
persona_access = Table(
    "persona_access",
    Base.metadata,
    Column("persona_id", Integer, ForeignKey("personas.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
)


class User(Base):
    """Represents a user of the system."""

    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)

    personas = relationship(
        "Personas", secondary=persona_access, back_populates="allowed_users"
    )
    chat_instances = relationship("ChatInstance", back_populates="user")

    # Performance considerations:
    # - `username` is indexed for faster lookups.


class ChatInstance(Base):
    """Represents a unique chat session."""

    __tablename__ = "chat_instances"
    id = Column(String, primary_key=True)  # Consider using UUID
    persona_id = Column(Integer, ForeignKey("personas.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())

    persona = relationship("Personas")
    user = relationship("User")
    messages = relationship("Message", back_populates="chat_instance")

    # Performance considerations:
    # - `persona_id` and `user_id` are foreign keys with indexes for faster lookups.


class ChatbotConfig(Base):
    """Represents configuration settings for a chatbot."""

    __tablename__ = "chatbot_configs"
    id = Column(Integer, primary_key=True)
    persona_id = Column(Integer, ForeignKey("personas.id"))
    system_message = Column(String)
    model = Column(String)
    tokens = Column(Integer)
    temperature = Column(Float)
    presence_penalty = Column(Float)
    max_messages = Column(Integer)
    max_tokens = Column(Integer)
    max_chars = Column(Integer)

    persona = relationship("Personas", back_populates="chatbot_config")

    # Performance considerations:
    # - `persona_id` is a foreign key with an index for faster lookups.


class Personas(Base):
    """Represents a persona configuration."""

    __tablename__ = "personas"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    allowed_users = relationship(
        "User", secondary=persona_access, back_populates="personas"
    )
    chatbot_config = relationship(
        "ChatbotConfig", uselist=False, back_populates="persona"
    )
    chat_instances = relationship("ChatInstance", back_populates="persona")

    # Performance considerations:
    # - `name` is indexed for faster lookups.


class Message(Base):
    """Represents a message in the chat history."""

    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    chat_instance_id = Column(String, ForeignKey("chat_instances.id"))
    message = Column(String)
    response = Column(String)
    token_count = Column(Integer)
    role = Column(String)
    user = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    extra_info = Column(JSON)

    chat_instance = relationship("ChatInstance", back_populates="messages")

    # Performance considerations:
    # - `chat_instance_id` is a foreign key with an index for faster lookups.
    # - `created_at` is indexed for faster ordering of messages.
